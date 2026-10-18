"""Tests for the Stage 14.13 reasoning contract and runner. A tiny random Llama model on CPU is used: no real checkpoint is
loaded, no GPU is used and nothing is submitted."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract as rc  # noqa: E402
from physmon.governance.v2_contract import RAW_RECORD_FIELDS  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_mod = _load("s147_pilot_plan_r", "scripts/v2/s147_pilot_plan.py")
run_mod = _load("s152_reasoning_run", "scripts/v2/s152_reasoning_run.py")


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# --- contract and parser (no model) -----------------------------------------------------------------------


def test_the_final_line_is_parsed_with_value_unit_and_printed_precision():
    text = "Step 1: a = F/m.\nStep 2: 3 / 0.5 = 6.\nFinal answer: 6.0 m/s²"
    result = rc.parse_final(text)
    assert result.parsed.status == "PARSED" and result.parsed.value == 6.0 and result.parsed.unit == "m/s^2"
    assert result.parsed.value_text == "6.0" and result.n_final_lines == 1


def test_markdown_and_trailing_period_are_tolerated_and_the_unit_is_normalised():
    parsed = rc.parse_final("Work...\n**Final answer: 0.0156 N·m.**").parsed
    assert parsed.status == "PARSED" and parsed.unit == "N*m" and parsed.value == pytest.approx(0.0156)


def test_repeated_identical_final_lines_are_one_answer_but_different_ones_are_a_status_of_their_own():
    same = rc.parse_final("Final answer: 5 m\nrecheck\nFinal answer: 5 m")
    assert same.parsed.status == "PARSED" and same.n_final_lines == 2
    different = rc.parse_final("Final answer: 5 m\nbut actually\nFinal answer: 6 m")
    assert different.parsed.status == "MULTIPLE_CANDIDATES" and different.n_final_lines == 2


def test_a_missing_final_line_is_unparseable_or_truncated_never_wrong_and_empty_is_empty():
    assert rc.parse_final("I think it is about 5 metres.").parsed.status == "UNPARSEABLE"
    assert rc.parse_final("Let me compute step by step and", hit_token_limit=True).parsed.status == "TRUNCATED"
    assert rc.parse_final("   \n", hit_token_limit=True).parsed.status == "EMPTY"
    assert vs.classify_answer(rc.parse_final("no final line", hit_token_limit=True).parsed, 5.0, "m") == "TRUNCATED"


def test_a_final_line_in_a_generation_that_hit_the_limit_is_still_parsed_but_a_mid_line_phrase_is_not_a_final_line():
    assert rc.parse_final("reasoning...\nFinal answer: 7 m", hit_token_limit=True).parsed.status == "PARSED"
    # The contract asks for the final result on its own last line; the phrase inside a sentence does not count.
    assert rc.parse_final("so the Final answer: 7 m is what I would say", hit_token_limit=True).parsed.status == "TRUNCATED"


def test_the_declared_correctness_rule_applies_to_the_reasoning_answer():
    parsed = rc.parse_final("Final answer: 2.18 m/s²").parsed
    assert vs.classify_answer(parsed, 2.1777777, "m/s^2") == "correct"
    assert vs.classify_answer(rc.parse_final("Final answer: 2.17 m/s²").parsed, 2.1777777, "m/s^2") == "wrong"


def test_the_reasoning_contract_has_its_own_fingerprint_and_leaves_the_scoring_contract_alone():
    from physmon.benchmark import scoring_contract as sc

    assert sc.contract_fingerprint() == "bb6bbec489ef185850a40c2d83955b4371a22b2343196135f2db885e6dabca81"
    assert len(rc.contract_fingerprint()) == 64 and rc.contract_fingerprint() != sc.contract_fingerprint()
    assert "Do not include reasoning" not in rc.INSTRUCTION and "step by step" in rc.INSTRUCTION
    assert rc.FINAL_LINE_FORMAT in rc.INSTRUCTION


# --- runner on a tiny random model ------------------------------------------------------------------------


@pytest.fixture(scope="module")
def plan_dir(tmp_path_factory, llama_tokenizer):
    base = tmp_path_factory.mktemp("s152plan")
    argv = sys.argv
    sys.argv = ["s147_plan", "--out-root", str(base), "--attempt-id", "p1", "--structures", "S06", "--models", "llama_primary",
                "--wrappers", "answer_line", "plain"]
    try:
        assert plan_mod.main() == 0
    finally:
        sys.argv = argv
    return base / "p1"


@pytest.fixture(scope="module")
def tiny_model_dir(tmp_path_factory, llama_tokenizer):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    config = transformers.LlamaConfig(vocab_size=len(llama_tokenizer), hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                                      num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=1024)
    directory = tmp_path_factory.mktemp("tiny_llama_r")
    transformers.LlamaForCausalLM(config).save_pretrained(str(directory))
    llama_tokenizer.save_pretrained(str(directory))
    return directory


def _run(plan_dir, model_dir, out_root, attempt, extra=()):
    argv = ["s152", "--plan-dir", str(plan_dir), "--model-key", "llama_primary", "--model-path", str(model_dir), "--device", "cpu",
            "--dtype", "float32", "--max-jobs", "3", "--max-new-tokens", "6", "--out-root", str(out_root), "--attempt-id", attempt, *extra]
    old = sys.argv
    sys.argv = argv
    try:
        return run_mod.main()
    finally:
        sys.argv = old


def test_the_runner_refuses_without_an_authorization_reference(plan_dir, tiny_model_dir, tmp_path):
    assert _run(plan_dir, tiny_model_dir, tmp_path, "r0") == 4 and not (tmp_path / "r0").exists()


def test_the_runner_writes_complete_records_with_null_log_probabilities_and_keeps_truncation_as_an_outcome(plan_dir, tiny_model_dir, tmp_path):
    assert _run(plan_dir, tiny_model_dir, tmp_path, "r1", ("--authorization-ref", "TEST-ONLY")) == 0
    records = _jsonl(tmp_path / "r1" / "raw_records.jsonl")
    summary = json.loads((tmp_path / "r1" / "run_summary.json").read_text(encoding="utf-8"))
    assert len(records) == 3 == summary["n_records"] and summary["n_jobs_not_run"] == 0
    jobs = [j for j in _jsonl(plan_dir / "job_manifest.jsonl") if j["wrapper_id"] == "answer_line"][:3]
    assert [r["job_id"] for r in records] == [f"{j['job_id']}:reasoning" for j in jobs]  # plain-wrapper jobs are not run
    for record in records:
        assert set(RAW_RECORD_FIELDS) <= set(record) and record["status"] == "OK"
        assert record["gold_logprob_raw"] is None and record["alternative_scores"] is None  # no teacher-forced score here
        assert record["answer_wrapper_id"] == f"reasoning:{rc.CONTRACT_VERSION}"
        assert record["reasoning_contract_fingerprint"] == rc.contract_fingerprint()
        assert record["n_generated_tokens"] <= 6 and record["hit_token_limit"] is True
        # A random model with a six-token budget writes no final line: TRUNCATED, never wrong.
        assert record["parse_status"] == "TRUNCATED" and record["correctness"] == "TRUNCATED" and record["parsed_answer"] is None
        assert record["artifact_checksum"]


def test_the_time_budget_stops_cleanly_counts_what_was_not_run_and_exits_non_zero(plan_dir, tiny_model_dir, tmp_path):
    assert _run(plan_dir, tiny_model_dir, tmp_path, "r2", ("--authorization-ref", "TEST-ONLY", "--time-budget-s", "0")) == 1
    summary = json.loads((tmp_path / "r2" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["n_records"] == 0 and summary["n_jobs_not_run"] == 3
    assert (tmp_path / "r2" / "raw_records.jsonl").read_text(encoding="utf-8") == ""


def test_the_runner_refuses_a_used_directory_and_leaves_its_contents(plan_dir, tiny_model_dir, tmp_path):
    used = tmp_path / "r3"
    used.mkdir()
    (used / "keep.txt").write_text("existing evidence", encoding="utf-8")
    assert _run(plan_dir, tiny_model_dir, tmp_path, "r3", ("--authorization-ref", "x")) == 2
    assert (used / "keep.txt").read_text(encoding="utf-8") == "existing evidence"


def test_greedy_generate_counted_reports_the_new_token_count_and_the_limit(tiny_model_dir, llama_tokenizer):
    transformers = pytest.importorskip("transformers")
    model = transformers.AutoModelForCausalLM.from_pretrained(str(tiny_model_dir), local_files_only=True).eval()
    prompt = vs.build_chat_prompt(llama_tokenizer, rc.INSTRUCTION, "What is 2 plus 2?")
    text, n_new, hit = vs.greedy_generate_counted(model, llama_tokenizer, prompt, 5)
    assert isinstance(text, str) and 1 <= n_new <= 5 and hit == (n_new >= 5)
    assert vs.greedy_generate(model, llama_tokenizer, prompt, 5) == text  # the plain helper is unchanged
