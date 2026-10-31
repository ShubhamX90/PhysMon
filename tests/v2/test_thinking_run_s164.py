"""Tests for the Stage 14.20 thinking-model runner. A tiny random Llama model on CPU is used: no real checkpoint is loaded, no GPU is
used and nothing is submitted."""

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


def _load():
    spec = importlib.util.spec_from_file_location("s164", REPO_ROOT / "scripts/v2/s164_thinking_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_mod = _load()


def test_the_answer_is_the_text_after_the_last_closing_think_tag_and_a_phrase_inside_the_thinking_is_not_an_answer():
    text = "Let me try. Final answer: 5 m\nHmm, wait, that is wrong.\n</think>\nThe distance follows from v^2/(2 a).\nFinal answer: 40.8 m"
    parsed, thinking, answer, closed = run_mod.parse_thinking_output(text, hit_limit=False)
    assert closed and parsed.parsed.status == "PARSED" and parsed.parsed.value == pytest.approx(40.8) and "Final answer: 5 m" in thinking
    only_inside = run_mod.parse_thinking_output("Final answer: 5 m\nbut let me recheck.\n</think>\nI could not decide.", hit_limit=False)[0]
    assert only_inside.parsed.status == "UNPARSEABLE"


def test_thinking_that_never_closes_at_the_limit_is_truncated_and_an_untagged_direct_answer_is_parsed():
    assert run_mod.parse_thinking_output("long thinking without end", hit_limit=True)[0].parsed.status == "TRUNCATED"
    assert run_mod.parse_thinking_output("   ", hit_limit=True)[0].parsed.status == "EMPTY"
    direct = run_mod.parse_thinking_output("The answer.\nFinal answer: 3 m/s", hit_limit=False)[0]
    assert direct.parsed.status == "PARSED" and direct.parsed.unit == "m/s"
    closed_at_limit = run_mod.parse_thinking_output("thinking...\n</think>\nStill writing the solution", hit_limit=True)[0]
    assert closed_at_limit.parsed.status == "TRUNCATED"


def test_jobs_from_the_dataset_and_from_the_cell_manifest_carry_the_fields_the_record_needs():
    row = {"sample_id": "S11-i0", "structure_id": "S11", "instance": 0, "structure_uuid": "u", "template_cluster_id": "V2C-S11",
           "symbolic_program_hash": "h", "problem": "A car...", "gold_answer": {"value": 40.8, "unit": "m"}, "answer_unit": "m"}
    job = run_mod.jobs_from_dataset([row])[0]
    assert job["job_id"] == "S11-i0:no_cue" and job["cell_id"] == "no_cue" and job["cue_numeric_value"] is None and job["gold_unit"] == "m"
    assert run_mod.jobs_from_dataset([row], {"S11:1"}) == [] and len(run_mod.jobs_from_dataset([row], {"S11:0"})) == 1
    cell = {"structure_id": "S11", "instance": 1, "cell_id": "numeric_metadata", "feasible": True, "structure_uuid": "u",
            "template_cluster_id": "V2C-S11", "symbolic_program_hash": "h", "prompt": "p", "gold_value": 16.4, "gold_unit": "m",
            "cue_numeric_value": 21.0, "cue_semantic_role": "irrelevant", "expected_effect": "x"}
    infeasible = dict(cell, cell_id="far", feasible=False)
    other = dict(cell, instance=0)
    jobs = run_mod.jobs_from_manifest([cell, infeasible, other], None, None)
    assert [j["job_id"] for j in jobs] == ["S11-i1:numeric_metadata", "S11-i0:numeric_metadata"]
    assert [j["instance"] for j in run_mod.jobs_from_manifest([cell, other], ["numeric_metadata"], {"S11:1"})] == [1]
    assert run_mod.jobs_from_manifest([cell], ["far"], None) == []


@pytest.fixture(scope="module")
def tiny_model_dir(tmp_path_factory, llama_tokenizer):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    config = transformers.LlamaConfig(vocab_size=len(llama_tokenizer), hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                                      num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=1024)
    directory = tmp_path_factory.mktemp("tiny_llama_t")
    transformers.LlamaForCausalLM(config).save_pretrained(str(directory))
    llama_tokenizer.save_pretrained(str(directory))
    return directory


@pytest.fixture(scope="module")
def dataset_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("ds")
    rows = [{"sample_id": f"S11-i{i}", "structure_id": "S11", "instance": i, "structure_uuid": "u", "template_cluster_id": "V2C-S11",
             "symbolic_program_hash": "h", "problem": f"A car travels at {20 + i} m/s and brakes. How far does it go?",
             "gold_answer": {"value": 40.8 + i, "unit": "m"}, "answer_unit": "m"} for i in range(3)]
    (directory / "dataset.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return directory


def _run(dataset_dir, model_dir, out_root, attempt, extra=()):
    argv = ["s164", "--dataset-dir", str(dataset_dir), "--model-key", "llama_primary", "--model-path", str(model_dir), "--device", "cpu",
            "--dtype", "float32", "--max-new-tokens", "5", "--n-samples", "2", "--batch-size", "2", "--out-root", str(out_root),
            "--attempt-id", attempt, *extra]
    old = sys.argv
    sys.argv = argv
    try:
        return run_mod.main()
    finally:
        sys.argv = old


def test_the_runner_refuses_without_an_authorization_reference(dataset_dir, tiny_model_dir, tmp_path):
    assert _run(dataset_dir, tiny_model_dir, tmp_path, "r0") == 4 and not (tmp_path / "r0").exists()


def test_the_runner_writes_one_complete_record_per_job_and_sample_with_unique_ids_and_null_log_probabilities(dataset_dir, tiny_model_dir, tmp_path):
    assert _run(dataset_dir, tiny_model_dir, tmp_path, "r1", ("--authorization-ref", "TEST-ONLY")) == 0
    records = [json.loads(line) for line in (tmp_path / "r1" / "raw_records.jsonl").read_text(encoding="utf-8").splitlines()]
    summary = json.loads((tmp_path / "r1" / "run_summary.json").read_text(encoding="utf-8"))
    assert len(records) == 6 == summary["n_records"] and summary["n_records_not_run"] == 0
    assert len({r["job_id"] for r in records}) == 6 and {r["sample_index"] for r in records} == {0, 1}
    for r in records:
        assert set(RAW_RECORD_FIELDS) <= set(r) and r["status"] == "OK" and r["gold_logprob_raw"] is None
        assert r["answer_wrapper_id"] == f"thinking-v1:{rc.CONTRACT_VERSION}" and r["sampling"]["do_sample"] is True and r["batch_size"] == 2
        assert r["n_generated_tokens"] <= 5 and r["hit_token_limit"] is True and r["thinking_closed"] is False
        assert r["parse_status"] == "TRUNCATED" and r["correctness"] == "TRUNCATED" and r["model_commit"]
        assert r["artifact_checksum"]


def test_greedy_mode_the_time_budget_and_the_used_directory_rule(dataset_dir, tiny_model_dir, tmp_path):
    assert _run(dataset_dir, tiny_model_dir, tmp_path, "r2", ("--authorization-ref", "TEST-ONLY", "--greedy", "--max-jobs", "1")) == 0
    greedy = [json.loads(line) for line in (tmp_path / "r2" / "raw_records.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(greedy) == 2 and greedy[0]["sampling"]["do_sample"] is False and greedy[0]["generated_answer_raw"] == greedy[1]["generated_answer_raw"]
    assert _run(dataset_dir, tiny_model_dir, tmp_path, "r3", ("--authorization-ref", "TEST-ONLY", "--time-budget-s", "0")) == 1
    summary = json.loads((tmp_path / "r3" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["n_records"] == 0 and summary["n_records_not_run"] == 6
    used = tmp_path / "r4"
    used.mkdir()
    (used / "keep.txt").write_text("existing evidence", encoding="utf-8")
    assert _run(dataset_dir, tiny_model_dir, tmp_path, "r4", ("--authorization-ref", "x")) == 2
    assert (used / "keep.txt").read_text(encoding="utf-8") == "existing evidence"


def test_the_requested_unit_is_stated_in_the_user_turn_when_asked_and_superscripts_are_used():
    stated = run_mod.user_turn("A body accelerates.", "m/s^2")
    assert stated.endswith("Give the final answer in m/s\u00b2.") and stated.startswith(rc.INSTRUCTION) and "A body accelerates." in stated
    assert run_mod.user_turn("A body accelerates.") == f"{rc.INSTRUCTION}\n\nA body accelerates."


def test_records_carry_the_unit_convertible_label_the_unit_flag_and_the_oom_flag(dataset_dir, tiny_model_dir, tmp_path):
    assert _run(dataset_dir, tiny_model_dir, tmp_path, "r5", ("--authorization-ref", "TEST-ONLY", "--max-jobs", "1")) == 0
    first = [json.loads(line) for line in (tmp_path / "r5" / "raw_records.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(r["unit_stated_in_prompt"] is True and r["oom_fallback"] is False and r["correct_if_units_convertible"] == "TRUNCATED" for r in first)
    assert _run(dataset_dir, tiny_model_dir, tmp_path, "r6", ("--authorization-ref", "TEST-ONLY", "--max-jobs", "1", "--no-state-unit")) == 0
    second = [json.loads(line) for line in (tmp_path / "r6" / "raw_records.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(r["unit_stated_in_prompt"] is False for r in second)


def test_an_out_of_memory_batch_is_redone_one_sequence_at_a_time_and_flagged(monkeypatch):
    torch = pytest.importorskip("torch")
    calls = []

    def fake(model, tokenizer, prompts, max_new_tokens, sampling, seed):
        calls.append(len(prompts))
        if len(prompts) > 1:
            raise torch.cuda.OutOfMemoryError("simulated")
        return [(f"text for {prompts[0]}", 3, False)]

    monkeypatch.setattr(run_mod, "generate_batch", fake)
    outputs, fell_back = run_mod.generate_with_fallback(None, None, ["a", "b", "c"], 5, {"do_sample": False}, 1)
    assert fell_back is True and calls == [3, 1, 1, 1] and [o[0] for o in outputs] == ["text for a", "text for b", "text for c"]
    outputs, fell_back = run_mod.generate_with_fallback(None, None, ["a"], 5, {"do_sample": False}, 1)
    assert fell_back is False and len(outputs) == 1
