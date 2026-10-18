"""Tests for the Stage 14 artifact registry on a synthetic repository root."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("register_stage14", REPO_ROOT / "scripts/v2/register_stage14_artifacts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reg = _load()


def make_root(tmp_path: Path) -> Path:
    run = tmp_path / "results/stage14/s147_pilot_run/attempt_999_qwen_primary_bfloat16"
    run.mkdir(parents=True)
    (run / "raw_records.jsonl").write_text('{"a": 1}\n', encoding="utf-8")
    (run / "run_summary.json").write_text(json.dumps({
        "source_commit": "abc123", "authorization_ref": "ref-1", "dtype": "bfloat16", "model_key": "qwen_primary",
        "evidence_class": "exploratory; not paper-eligible"}), encoding="utf-8")
    plan = tmp_path / "results/stage14/s147_pilot_plan/attempt_20261016_d22a65d"
    plan.mkdir(parents=True)
    (plan / "plan.json").write_text(json.dumps({"source_commit": "d22a65d"}), encoding="utf-8")
    return tmp_path


def test_write_records_hashes_and_metadata_and_never_marks_anything_paper_eligible(tmp_path):
    root = make_root(tmp_path)
    new, problems = reg.write(root, root / reg.ARTIFACT_REGISTER)
    assert not problems and len(new) == 2
    run = next(e for e in new if e["kind"] == "pilot_run")
    assert run["source_commit"] == "abc123" and run["authorization_ref"] == "ref-1" and run["dtype"] == "bfloat16"
    assert set(run["files"]) == {"raw_records.jsonl", "run_summary.json"} and run["n_files"] == 2
    assert all(len(h) == 64 for h in run["files"].values())
    assert all(e["paper_eligible"] is False for e in new)
    plan = next(e for e in new if e["kind"] == "pilot_plan")
    assert plan["evidence_class"].startswith("derived or preparatory")  # no claim of run authority without a summary saying so


def test_verify_passes_on_an_unchanged_tree_and_fails_on_change_removal_and_additions(tmp_path):
    root = make_root(tmp_path)
    reg.write(root, root / reg.ARTIFACT_REGISTER)
    assert reg.verify(root, root / reg.ARTIFACT_REGISTER) == []
    run = root / "results/stage14/s147_pilot_run/attempt_999_qwen_primary_bfloat16"
    (run / "raw_records.jsonl").write_text('{"a": 2}\n', encoding="utf-8")
    assert any("file changed: raw_records.jsonl" in p for p in reg.verify(root, root / reg.ARTIFACT_REGISTER))
    (run / "raw_records.jsonl").write_text('{"a": 1}\n', encoding="utf-8")
    (run / "extra.txt").write_text("late", encoding="utf-8")
    assert any("unregistered file added: extra.txt" in p for p in reg.verify(root, root / reg.ARTIFACT_REGISTER))
    (run / "extra.txt").unlink()
    (run / "run_summary.json").unlink()
    assert any("file removed: run_summary.json" in p for p in reg.verify(root, root / reg.ARTIFACT_REGISTER))


def test_a_new_unregistered_artifact_directory_and_an_empty_register_are_errors(tmp_path):
    root = make_root(tmp_path)
    assert any("missing or empty" in p for p in reg.verify(root, root / reg.ARTIFACT_REGISTER))
    reg.write(root, root / reg.ARTIFACT_REGISTER)
    later = root / "results/stage14/s148_pilot_analysis/attempt_20261017_f8c4145"
    later.mkdir(parents=True)
    (later / "summary.json").write_text("{}", encoding="utf-8")
    assert any("not registered" in p for p in reg.verify(root, root / reg.ARTIFACT_REGISTER))


def test_write_appends_new_artifacts_and_refuses_when_a_registered_one_changed(tmp_path):
    root = make_root(tmp_path)
    reg.write(root, root / reg.ARTIFACT_REGISTER)
    before = (root / reg.ARTIFACT_REGISTER).read_text(encoding="utf-8")
    later = root / "results/stage14/s148_pilot_analysis/attempt_20261017_f8c4145"
    later.mkdir(parents=True)
    (later / "summary.json").write_text("{}", encoding="utf-8")
    new, problems = reg.write(root, root / reg.ARTIFACT_REGISTER)
    assert not problems and [e["kind"] for e in new] == ["pilot_analysis"]
    after = (root / reg.ARTIFACT_REGISTER).read_text(encoding="utf-8")
    assert after.startswith(before) and len(after.splitlines()) == 3  # existing lines untouched, one appended
    (root / "results/stage14/s147_pilot_plan/attempt_20261016_d22a65d/plan.json").write_text("{}", encoding="utf-8")
    new, problems = reg.write(root, root / reg.ARTIFACT_REGISTER)
    assert new == [] and any("file changed: plan.json" in p for p in problems)
    assert (root / reg.ARTIFACT_REGISTER).read_text(encoding="utf-8") == after  # a failed write changes nothing


def test_job_register_keeps_failed_and_cancelled_jobs_and_links_artifact_directories(tmp_path):
    root = make_root(tmp_path)
    text = ("JobIDRaw|JobName|Partition|State|Elapsed|ExitCode|NodeList|AllocTRES\n"
            "999|physmon_s14_pilot|gpu_h100_4|COMPLETED|00:09:15|0:0|gpunode6|billing=8\n"
            "998|physmon_s14_pilot|gpu_h100_4|FAILED|00:00:21|1:0|gpunode6|billing=8\n"
            "997|physmon_s14_smoke_rerun|gpu_h200_8|CANCELLED+|00:00:00|0:0|None assigned|\n")
    rows = reg.parse_sacct(text)
    assert len(rows) == 3 and rows[1]["State"] == "FAILED"
    added = reg.add_jobs(root, root / reg.JOB_REGISTER, ["999", "998", "997"], rows)
    assert [r["state"] for r in added] == ["COMPLETED", "FAILED", "CANCELLED+"]
    completed = added[0]
    assert completed["artifact_dirs"] == ["results/stage14/s147_pilot_run/attempt_999_qwen_primary_bfloat16"]
    assert added[1]["artifact_dirs"] == [] and added[2]["artifact_dirs"] == []  # no output directory exists
    again = reg.add_jobs(root, root / reg.JOB_REGISTER, ["999"], rows)
    assert again == [] and len((root / reg.JOB_REGISTER).read_text(encoding="utf-8").splitlines()) == 3


def test_main_verify_exits_non_zero_on_a_changed_file(tmp_path, monkeypatch, capsys):
    root = make_root(tmp_path)
    monkeypatch.setattr(sys, "argv", ["reg", "--write", "--root", str(root)])
    assert reg.main() == 0
    monkeypatch.setattr(sys, "argv", ["reg", "--verify", "--root", str(root)])
    assert reg.main() == 0
    (root / "results/stage14/s147_pilot_plan/attempt_20261016_d22a65d/plan.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["reg", "--verify", "--root", str(root)])
    assert reg.main() == 1
    assert "file changed: plan.json" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        monkeypatch.setattr(sys, "argv", ["reg"])
        reg.main()


def test_a_job_whose_output_directory_name_has_no_job_id_can_be_linked_explicitly(tmp_path):
    smoke = tmp_path / "results/infrastructure/model_smoke/attempt_20261017_gpu_h100"
    smoke.mkdir(parents=True)
    (smoke / "summary_gpu.json").write_text("{}", encoding="utf-8")
    rows = reg.parse_sacct("JobIDRaw|JobName|Partition|State|Elapsed|ExitCode|NodeList|AllocTRES\n"
                           "399217|physmon_s14_smoke_rerun|gpu_h100_4|COMPLETED|00:59:56|0:0|gpunode5|billing=8\n")
    added = reg.add_jobs(tmp_path, tmp_path / reg.JOB_REGISTER, ["399217"], rows)
    assert added[0]["artifact_dirs"] == ["results/infrastructure/model_smoke/attempt_20261017_gpu_h100"]
    new, problems = reg.write(tmp_path, tmp_path / reg.ARTIFACT_REGISTER)
    assert not problems and [e["kind"] for e in new] == ["model_smoke"]


def test_a_directory_of_a_job_that_is_still_running_is_not_registered_until_it_has_finished(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    running = root / "results/stage14/s152_reasoning_run/attempt_401357_qwen_primary_reasoning"
    running.mkdir(parents=True)
    (running / "raw_records.jsonl").write_text('{"partial": true}\n', encoding="utf-8")
    monkeypatch.setattr(reg, "live_jobs", lambda ids: {"401357"} & set(ids))
    new, problems = reg.write(root, root / reg.ARTIFACT_REGISTER)
    assert not problems and {e["path"].split("/")[-1] for e in new} == {"attempt_999_qwen_primary_bfloat16", "attempt_20261016_d22a65d"}
    assert not any("401357" in e["artifact_id"] for e in new)
    monkeypatch.setattr(reg, "live_jobs", lambda ids: set())  # the job has left the queue
    new, problems = reg.write(root, root / reg.ARTIFACT_REGISTER)
    assert not problems and [e["path"].split("/")[-1] for e in new] == ["attempt_401357_qwen_primary_reasoning"]


def test_job_id_is_read_from_the_attempt_name_and_a_failing_queue_is_an_error():
    assert reg.job_id_of(Path("x/attempt_401357_qwen_primary_reasoning")) == "401357"
    assert reg.job_id_of(Path("x/attempt_20261016_d22a65d")) is None  # a date and a commit, not a job id
    assert reg.job_id_of(Path("x/attempt_999_qwen")) is None
    assert reg.live_jobs([]) == set()
