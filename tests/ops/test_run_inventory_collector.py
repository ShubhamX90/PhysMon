"""Tests for the Sharanga run-inventory collector.

The collector is the evidence source for the Wave 0 run crosswalk, so its
failure modes matter more than its happy path: it must never invent a job
identity and never imply a run succeeded when accounting is unavailable.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "ops" / "collect_sharanga_run_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("collect_sharanga_run_inventory", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


collector = _load_module()


@pytest.mark.parametrize(
    ("filename", "job_id", "job_name", "stream"),
    [
        ("242828_physmon_s11_cuec_probe.out", "242828", "physmon_s11_cuec_probe", "out"),
        ("242828_physmon_s11_cuec_probe.err", "242828", "physmon_s11_cuec_probe", "err"),
        ("stage6_d2_qwen_242829.out", "242829", "stage6_d2_qwen", "out"),
        ("stage6_d2_qwen_242829.err", "242829", "stage6_d2_qwen", "err"),
    ],
)
def test_parse_log_name_handles_both_historical_conventions(filename, job_id, job_name, stream):
    assert collector.parse_log_name(filename) == (job_id, job_name, stream)


def test_parse_log_name_refuses_to_guess_an_unparseable_name():
    assert collector.parse_log_name("noconvention.out") == (None, None, None)
    assert collector.parse_log_name("not_a_slurm_log.txt") == (None, None, None)


def test_unparseable_logs_are_recorded_as_failures_not_dropped(tmp_path: Path):
    (tmp_path / "noconvention.out").write_text("x", encoding="utf-8")
    records = collector.build_inventory(tmp_path, {})
    assert len(records) == 1
    assert records[0]["job_id"] is None
    assert records[0]["job_id_source"] == "job_id_parse_failed"


def test_missing_accounting_never_implies_success(tmp_path: Path):
    (tmp_path / "242828_physmon_test.out").write_text("hello", encoding="utf-8")
    records = collector.build_inventory(tmp_path, {})
    record = records[0]
    assert record["accounting_status"] == "accounting_unavailable"
    assert record["terminal_state"] == "unknown"
    assert record["scientific_validity"] == "not_assessed_by_this_collector"


def test_accounting_state_is_joined_but_not_interpreted(tmp_path: Path):
    (tmp_path / "242828_physmon_test.out").write_text("hello", encoding="utf-8")
    sacct = {
        "242828": {
            "JobID": "242828",
            "JobName": "physmon_test",
            "Partition": "gpu_h100_4",
            "State": "COMPLETED",
            "Elapsed": "01:02:03",
            "ExitCode": "0:0",
            "Submit": "2026-06-20T10:00:00",
            "Start": "2026-06-20T10:01:00",
            "End": "2026-06-20T11:03:03",
            "ReqTRES": "cpu=8,gres/gpu=1",
            "NodeList": "gpunode5",
        }
    }
    record = collector.build_inventory(tmp_path, sacct)[0]
    assert record["terminal_state"] == "COMPLETED"
    assert record["partition"] == "gpu_h100_4"
    # A COMPLETED scheduler state must not be promoted to a scientific verdict.
    assert record["scientific_validity"] == "not_assessed_by_this_collector"


def test_stdout_and_stderr_are_grouped_into_one_job(tmp_path: Path):
    (tmp_path / "242828_physmon_test.out").write_text("out", encoding="utf-8")
    (tmp_path / "242828_physmon_test.err").write_text("err", encoding="utf-8")
    records = collector.build_inventory(tmp_path, {})
    assert len(records) == 1
    assert records[0]["stdout_path"].endswith("242828_physmon_test.out")
    assert records[0]["stderr_path"].endswith("242828_physmon_test.err")


def test_template_header_fields_are_extracted(tmp_path: Path):
    (tmp_path / "242828_physmon_test.out").write_text(
        "=== PhysMon Job Start ===\n"
        "Job ID:    242828\n"
        "Node:      gpunode5\n"
        "Script:    scripts/run_behavioural.py\n"
        "Args:      --model qwen_primary\n",
        encoding="utf-8",
    )
    header = collector.build_inventory(tmp_path, {})[0]["header"]
    assert header["script"] == "scripts/run_behavioural.py"
    assert header["args"] == "--model qwen_primary"
    assert header["node"] == "gpunode5"


def test_sacct_step_rows_are_folded_away(monkeypatch):
    class FakeRun:
        returncode = 0
        stderr = ""
        stdout = "\n".join(
            [
                "242828|physmon_test|gpu_h100_4|COMPLETED|01:00:00|0:0|s|s|e|cpu=8|gpunode5",
                "242828.batch|batch||COMPLETED|01:00:00|0:0|s|s|e||",
                "242828.extern|extern||COMPLETED|01:00:00|0:0|s|s|e||",
            ]
        )

    monkeypatch.setattr(collector.subprocess, "run", lambda *a, **k: FakeRun())
    rows = collector.collect_sacct("2026-05-01")
    assert list(rows) == ["242828"]


def test_output_is_jsonl_one_record_per_job(tmp_path: Path):
    (tmp_path / "242828_a.out").write_text("x", encoding="utf-8")
    (tmp_path / "242829_b.out").write_text("y", encoding="utf-8")
    records = collector.build_inventory(tmp_path, {})
    payload = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    assert len(payload.splitlines()) == 2
