"""Tests for the Stage 14.14 and 14.16 score-only runner on a tiny random Llama model on CPU (no real checkpoint, no GPU, nothing submitted)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.governance.v2_contract import RAW_RECORD_FIELDS  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


presence_plan = _load("s154_plan_so", "scripts/v2/s154_numeral_presence_plan.py")
legacy_plan = _load("s156_plan_so", "scripts/v2/s156_legacy_x03_plan.py")
run_mod = _load("s158_run", "scripts/v2/s158_score_only_run.py")


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="module")
def plans(tmp_path_factory, llama_tokenizer):
    base = tmp_path_factory.mktemp("s158plans")
    argv = sys.argv
    try:
        sys.argv = ["s154", "--out-root", str(base), "--attempt-id", "pres", "--structures", "S06", "--models", "llama_primary"]
        assert presence_plan.main() == 0
        sys.argv = ["s156", "--out-root", str(base), "--attempt-id", "leg", "--models", "llama_primary", "--wrappers", "answer_line",
                    "--families", "CM_B_001"]
        assert legacy_plan.main() == 0
    finally:
        sys.argv = argv
    return {"presence": base / "pres", "legacy": base / "leg"}


@pytest.fixture(scope="module")
def tiny_model_dir(tmp_path_factory, llama_tokenizer):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    config = transformers.LlamaConfig(vocab_size=len(llama_tokenizer), hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                                      num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=1024)
    directory = tmp_path_factory.mktemp("tiny_llama_so")
    transformers.LlamaForCausalLM(config).save_pretrained(str(directory))
    llama_tokenizer.save_pretrained(str(directory))
    return directory


def _run(plan_dir, model_dir, out_root, attempt, extra=(), max_jobs="6"):
    argv = ["s158", "--plan-dir", str(plan_dir), "--model-key", "llama_primary", "--model-path", str(model_dir), "--device", "cpu",
            "--dtype", "float32", "--max-jobs", max_jobs, "--out-root", str(out_root), "--attempt-id", attempt, *extra]
    old = sys.argv
    sys.argv = argv
    try:
        return run_mod.main()
    finally:
        sys.argv = old


def test_the_runner_refuses_without_an_authorization_reference(plans, tiny_model_dir, tmp_path):
    assert _run(plans["presence"], tiny_model_dir, tmp_path, "r0") == 4 and not (tmp_path / "r0").exists()


@pytest.mark.parametrize("kind", ["presence", "legacy"])
def test_records_are_complete_have_no_generation_and_carry_the_candidate_fields(kind, plans, tiny_model_dir, tmp_path):
    assert _run(plans[kind], tiny_model_dir, tmp_path, "r1", ("--authorization-ref", "TEST-ONLY")) == 0
    records = _jsonl(tmp_path / "r1" / "raw_records.jsonl")
    summary = json.loads((tmp_path / "r1" / "run_summary.json").read_text(encoding="utf-8"))
    assert len(records) == 6 == summary["n_records"] and summary["n_jobs_not_run"] == 0 and summary["status_counts"] == {"OK": 6}
    for r in records:
        assert set(RAW_RECORD_FIELDS) <= set(r) and r["status"] == "OK"
        assert r["generated_answer_raw"] is None and r["parsed_answer"] is None
        assert r["parse_status"] == "NOT_EVALUATED" and r["correctness"] == "NOT_EVALUATED" and r["alternative_scores"] is None
        assert r["gold_logprob_raw"] < 0 and len(r["gold_logprob_per_token"]) == len(r["target_answer_ids"])
        assert r["candidate_kind"] in ("present", "absent_control", "gold", "cue_candidate") and r["candidate_text"] in r["gold_text"]
        assert r["target_span_end"] - r["target_span_start"] == len(r["target_answer_ids"])
        assert all(abs(x - round(x, 4)) < 1e-12 for x in r["gold_logprob_per_token"])


def test_the_stored_log_probability_equals_an_independent_recomputation(plans, tiny_model_dir, llama_tokenizer, tmp_path):
    transformers = pytest.importorskip("transformers")
    assert _run(plans["legacy"], tiny_model_dir, tmp_path, "r2", ("--authorization-ref", "TEST-ONLY"), max_jobs="4") == 0
    records = _jsonl(tmp_path / "r2" / "raw_records.jsonl")
    jobs = {j["job_id"]: j for j in _jsonl(plans["legacy"] / "job_manifest.jsonl")}
    model = transformers.AutoModelForCausalLM.from_pretrained(str(tiny_model_dir), local_files_only=True).eval()
    fn = vs.make_hf_logprob_fn(model, "cpu")
    for r in records:
        job = jobs[r["job_id"]]
        prompt = vs.build_chat_prompt(llama_tokenizer, sc.instruction_for(job["wrapper_id"]), job["user_prompt"])
        pair = vs.tokenize_pair(llama_tokenizer, prompt, job["gold_text"])
        expected = vs.score_pair(fn, pair, job["wrapper_id"], job["gold_text"]).gold_logprob_raw
        assert r["gold_logprob_raw"] == pytest.approx(expected, abs=1e-4)


def test_a_prompt_that_no_longer_matches_its_hash_is_a_recorded_status_not_a_score(plans, tiny_model_dir, tmp_path):
    plan = tmp_path / "tampered"
    plan.mkdir()
    jobs = _jsonl(plans["legacy"] / "job_manifest.jsonl")[:2]
    jobs[0]["formatted_prompt_sha256"] = "0" * 64
    (plan / "job_manifest.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs), encoding="utf-8")
    (plan / "plan.json").write_text((plans["legacy"] / "plan.json").read_text(encoding="utf-8"), encoding="utf-8")
    assert _run(plan, tiny_model_dir, tmp_path, "r3", ("--authorization-ref", "TEST-ONLY")) == 0
    records = _jsonl(tmp_path / "r3" / "raw_records.jsonl")
    assert records[0]["status"] == "PROMPT_HASH_MISMATCH" and records[0]["gold_logprob_raw"] is None
    assert records[1]["status"] == "OK" and records[1]["gold_logprob_raw"] is not None


def test_the_time_budget_stops_cleanly_and_a_used_directory_is_refused(plans, tiny_model_dir, tmp_path):
    assert _run(plans["presence"], tiny_model_dir, tmp_path, "r4", ("--authorization-ref", "TEST-ONLY", "--time-budget-s", "0")) == 1
    summary = json.loads((tmp_path / "r4" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["n_records"] == 0 and summary["n_jobs_not_run"] == 6
    used = tmp_path / "r5"
    used.mkdir()
    (used / "keep.txt").write_text("existing evidence", encoding="utf-8")
    assert _run(plans["presence"], tiny_model_dir, tmp_path, "r5", ("--authorization-ref", "x")) == 2
    assert (used / "keep.txt").read_text(encoding="utf-8") == "existing evidence"
