"""Tests for the Stage 14.7 pilot planner and runner. They use a tiny randomly initialised model on CPU: no real
checkpoint is loaded, no GPU is used, and nothing is submitted."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance.v2_contract import RAW_RECORD_FIELDS  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_mod = _load("s147_pilot_plan", "scripts/v2/s147_pilot_plan.py")
run_mod = _load("s147_pilot_run", "scripts/v2/s147_pilot_run.py")


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="module")
def plan_dir(tmp_path_factory, llama_tokenizer):
    base = tmp_path_factory.mktemp("s147plan")
    argv = sys.argv
    sys.argv = ["s147_plan", "--out-root", str(base), "--attempt-id", "p1", "--structures", "S06", "S10",
                "--models", "llama_primary"]
    try:
        assert plan_mod.main() == 0
    finally:
        sys.argv = argv
    return base / "p1"


def test_the_plan_is_a_dry_run_that_states_it_is_not_authorized(plan_dir):
    plan = json.loads((plan_dir / "plan.json").read_text(encoding="utf-8"))
    assert plan["authorized_to_run"] is False and plan["blockers"]
    assert plan["data_role"] == "EXPLORATION" and "not run" in plan["evidence_class"]
    assert "NOT ESTIMATED" in plan["cost"]["gpu_time_estimate"]
    assert plan["wrapper_id"] == "answer_line"
    jobs = _jsonl(plan_dir / "job_manifest.jsonl")
    manifest = [json.loads(line) for line in (REPO_ROOT / plan_mod.MANIFEST).read_text(
        encoding="utf-8").splitlines() if line.strip()]
    feasible = [r for r in manifest if r["feasible"] and r["structure_id"] in ("S06", "S10")]
    assert len(jobs) == len(feasible) == plan["n_jobs"]


def test_jobs_follow_the_contract_and_decoys_exist_only_for_numeric_cue_cells(plan_dir):
    jobs = _jsonl(plan_dir / "job_manifest.jsonl")
    assert {j["gold_tokenization_status"] for j in jobs} == {"OK"}
    assert {j["leading_special_tokens"] for j in jobs} == {1}  # Llama: BOS exactly once under the contract path
    for job in jobs:
        assert job["gold_text"].startswith("Answer: ")  # the scored string is the instructed format
        assert job["decoy_defined"] == (job["cell_id"] in plan_mod.DECOY_CELLS)
        assert (job["decoy_text"] is not None) == job["decoy_defined"]
        if job["decoy_defined"]:
            assert job["decoy_text"] != job["gold_text"] and job["decoy_tokenization_status"] == "OK"


def test_the_cost_summary_counts_passes_and_does_not_invent_a_gpu_time(plan_dir):
    plan = json.loads((plan_dir / "plan.json").read_text(encoding="utf-8"))
    per_model = plan["cost"]["per_model"]["llama_primary"]
    jobs = _jsonl(plan_dir / "job_manifest.jsonl")
    assert per_model["n_jobs"] == len(jobs)
    assert per_model["n_scoring_forward_passes"] == len(jobs) + sum(j["decoy_defined"] for j in jobs)
    assert per_model["max_generated_tokens"] == len(jobs) * plan_mod.MAX_NEW_TOKENS


def test_planner_refuses_to_reuse_an_attempt_directory(plan_dir, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["s147_plan", "--out-root", str(plan_dir.parent), "--attempt-id", "p1"])
    assert plan_mod.main() == 2


@pytest.fixture(scope="module")
def tiny_model_dir(tmp_path_factory, llama_tokenizer):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    config = transformers.LlamaConfig(vocab_size=len(llama_tokenizer), hidden_size=16, intermediate_size=32,
                                      num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
                                      max_position_embeddings=1024)
    directory = tmp_path_factory.mktemp("tiny_llama")
    transformers.LlamaForCausalLM(config).save_pretrained(str(directory))
    llama_tokenizer.save_pretrained(str(directory))
    return directory


def _run(plan_dir, tiny_model_dir, out_root, attempt, extra=()):
    argv = ["s147_run", "--plan-dir", str(plan_dir), "--model-key", "llama_primary", "--model-path",
            str(tiny_model_dir), "--device", "cpu", "--dtype", "float32", "--max-jobs", "5", "--max-new-tokens", "3",
            "--out-root", str(out_root), "--attempt-id", attempt, *extra]
    old = sys.argv
    sys.argv = argv
    try:
        return run_mod.main()
    finally:
        sys.argv = old


def test_the_runner_refuses_without_an_authorization_reference(plan_dir, tiny_model_dir, tmp_path):
    assert _run(plan_dir, tiny_model_dir, tmp_path, "r0") == 4
    assert not (tmp_path / "r0").exists()


def test_the_runner_writes_complete_raw_records_and_aggregates_nothing(plan_dir, tiny_model_dir, tmp_path):
    code = _run(plan_dir, tiny_model_dir, tmp_path, "r1", ("--authorization-ref", "TEST-ONLY-no-real-run"))
    assert code == 0
    records = _jsonl(tmp_path / "r1" / "raw_records.jsonl")
    summary = json.loads((tmp_path / "r1" / "run_summary.json").read_text(encoding="utf-8"))
    assert len(records) == 5 == summary["n_records"]
    for record in records:
        assert set(RAW_RECORD_FIELDS) <= set(record)
        assert record["status"] == "OK" and record["exploratory_or_confirmatory"] == "exploratory"
        assert record["authorization_ref"] == "TEST-ONLY-no-real-run"
        assert record["gold_logprob_raw"] is not None and record["gold_logprob_raw"] < 0
        assert len(record["gold_logprob_per_token"]) == len(record["target_answer_ids"])
        assert record["target_span_end"] - record["target_span_start"] == len(record["target_answer_ids"])
        # A random model's output does not parse; that is an outcome, never a wrong answer or a zero.
        assert record["correctness"] in ("correct", "wrong", "UNPARSEABLE", "MULTIPLE_CANDIDATES", "EMPTY")
        if record["parse_status"] != "PARSED":
            assert record["correctness"] == record["parse_status"] and record["parsed_answer"] is None
        assert record["artifact_checksum"]
    assert "effect" not in json.dumps(summary).replace("no effect", "")
    assert summary["note"].startswith("raw records only")


def test_the_runner_refuses_a_stale_contract_a_missing_gpu_and_a_used_directory(
        plan_dir, tiny_model_dir, tmp_path):
    stale = tmp_path / "stale_plan"
    stale.mkdir()
    plan = json.loads((plan_dir / "plan.json").read_text(encoding="utf-8"))
    plan = copy.deepcopy(plan)
    plan["contract_fingerprint"] = "0" * 64
    (stale / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (stale / "job_manifest.jsonl").write_text((plan_dir / "job_manifest.jsonl").read_text(encoding="utf-8"),
                                              encoding="utf-8")
    assert _run(stale, tiny_model_dir, tmp_path, "r2", ("--authorization-ref", "x")) == 5
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        old = sys.argv
        sys.argv = ["s147_run", "--plan-dir", str(plan_dir), "--model-key", "llama_primary", "--device", "cuda",
                    "--authorization-ref", "x", "--out-root", str(tmp_path), "--attempt-id", "r3"]
        try:
            assert run_mod.main() == 3
        finally:
            sys.argv = old
    used = tmp_path / "r4"
    used.mkdir()
    (used / "keep.txt").write_text("existing evidence", encoding="utf-8")
    assert _run(plan_dir, tiny_model_dir, tmp_path, "r4", ("--authorization-ref", "x")) == 2
    assert (used / "keep.txt").read_text(encoding="utf-8") == "existing evidence"
