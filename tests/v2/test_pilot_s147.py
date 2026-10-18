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


def test_the_runner_without_git_uses_the_submitters_commit_or_refuses(plan_dir, tiny_model_dir, tmp_path, monkeypatch):
    # Job 399511 failed because the node had no git. With no git on PATH the runner must not crash or record an empty
    # commit: it takes PHYSMON_SOURCE_COMMIT and says so, and it refuses without one.
    empty_bin = tmp_path / "empty_bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))
    monkeypatch.delenv("PHYSMON_SOURCE_COMMIT", raising=False)
    assert _run(plan_dir, tiny_model_dir, tmp_path, "g0", ("--authorization-ref", "TEST-ONLY")) == 8
    assert not (tmp_path / "g0").exists()
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "a" * 40)
    assert _run(plan_dir, tiny_model_dir, tmp_path, "g1", ("--authorization-ref", "TEST-ONLY")) == 0
    summary = json.loads((tmp_path / "g1" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["source_commit"] == "a" * 40 and "git unavailable" in summary["source_commit_from"]
    assert summary["git_status_short"] == "NOT AVAILABLE"
    assert all(r["source_commit"] == "a" * 40 for r in _jsonl(tmp_path / "g1" / "raw_records.jsonl"))


@pytest.mark.parametrize("error", [FileNotFoundError("git"), PermissionError(13, "Permission denied", "git")])
def test_git_that_cannot_be_executed_gives_an_empty_string_not_a_crash(error, monkeypatch):
    # Job 399530 died on gpunode6 with PermissionError from subprocess, not FileNotFoundError.
    def boom(*args, **kwargs):
        raise error

    monkeypatch.setattr(run_mod.subprocess, "run", boom)
    assert run_mod.git("rev-parse", "HEAD") == ""


def test_each_decoy_is_also_scored_under_the_no_cue_prompt_of_the_same_instantiation(plan_dir, tiny_model_dir, tmp_path):
    transformers = pytest.importorskip("transformers")
    sc = run_mod.sc
    vs = run_mod.vs
    assert _run(plan_dir, tiny_model_dir, tmp_path, "a1", ("--authorization-ref", "TEST-ONLY")) == 0
    # _run limits to 5 jobs, which already include a near-cue cell with a decoy; the anchor prompt comes from the full manifest.
    records = _jsonl(tmp_path / "a1" / "raw_records.jsonl")
    with_decoy = [r for r in records if r["alternative_scores"]]
    assert with_decoy and all(r["alternative_scores"]["decoy_under_anchor_prompt"] is not None for r in with_decoy)
    assert all(r["alternative_scores"] is None for r in records if r["cell_id"] in ("no_cue", "nonnumeric_extra"))
    jobs = [j for j in _jsonl(plan_dir / "job_manifest.jsonl") if j["model_key"] == "llama_primary"]
    anchors = {(j["structure_id"], j["instance"]): j["user_prompt"] for j in jobs if j["cell_id"] == "no_cue"}
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(tiny_model_dir), local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(str(tiny_model_dir), local_files_only=True)
    model.eval()
    fn = vs.make_hf_logprob_fn(model, "cpu")
    for record in with_decoy:
        anchor_prompt = vs.build_chat_prompt(tokenizer, sc.instruction_for("answer_line"),
                                             anchors[(record["structure_id"], record["instance"])])
        pair = vs.tokenize_pair(tokenizer, anchor_prompt, record["alternative_scores"]["decoy"]["text"])
        expected = vs.score_pair(fn, pair, "answer_line", record["alternative_scores"]["decoy"]["text"]).gold_logprob_raw
        stored = record["alternative_scores"]["decoy_under_anchor_prompt"]["logprob_raw"]
        assert stored == pytest.approx(expected, abs=1e-4)
        # A different prompt gives a different score, so the field is not a copy of the cue-prompt score.
        assert stored != record["alternative_scores"]["decoy"]["logprob_raw"]


def test_a_multi_wrapper_plan_has_unique_ids_unchanged_answer_line_ids_and_equivalent_targets(tmp_path, llama_tokenizer):
    sc = plan_mod.sc
    argv = sys.argv
    sys.argv = ["s147_plan", "--out-root", str(tmp_path), "--attempt-id", "w1", "--structures", "S06", "--models",
                "llama_primary", "--wrappers", "answer_line", "plain", "boxed", "json", "sentence", "decimal_plain",
                "scientific"]
    try:
        assert plan_mod.main() == 0
    finally:
        sys.argv = argv
    jobs = _jsonl(tmp_path / "w1" / "job_manifest.jsonl")
    plan = json.loads((tmp_path / "w1" / "plan.json").read_text(encoding="utf-8"))
    assert plan["wrapper_id"] == "multiple" and len(plan["wrapper_ids"]) == 7
    assert len({j["job_id"] for j in jobs}) == len(jobs)
    per_wrapper = {w: [j for j in jobs if j["wrapper_id"] == w] for w in plan["wrapper_ids"]}
    assert len({len(v) for v in per_wrapper.values()}) == 1 and len(jobs) == 7 * len(per_wrapper["plain"])
    assert all(j["job_id"] == f"llama_primary:{j['structure_id']}:{j['instance']}:{j['cell_id']}"
               for j in per_wrapper["answer_line"])  # answer_line ids carry no wrapper suffix
    assert all(j["job_id"].endswith(f":{j['wrapper_id']}") for w, rows in per_wrapper.items() if w != "answer_line"
               for j in rows)
    # Every wrapper encodes the same physical answer: parsing the gold string recovers the same value and unit.
    for wrapper, rows in per_wrapper.items():
        for job in rows:
            value, unit = sc.parse_target(wrapper, job["gold_text"])
            assert value == pytest.approx(float(f"{job['gold_value']:.4g}"), rel=1e-9)
            if job["decoy_text"]:
                assert sc.parse_target(wrapper, job["decoy_text"])[1] == unit
    audit = plan["cost"]["per_model"]["llama_primary"]["tokenizer_audit_by_wrapper"]
    assert set(audit) == set(plan["wrapper_ids"])
    assert all(a["duplicate_special_token"] == 0 for a in audit.values())


def test_the_runner_scores_and_parses_under_each_non_default_wrapper(tmp_path, llama_tokenizer, tiny_model_dir):
    plan_root = tmp_path / "plans"
    argv = sys.argv
    sys.argv = ["s147_plan", "--out-root", str(plan_root), "--attempt-id", "wp", "--structures", "S06", "--models",
                "llama_primary", "--wrappers", "boxed", "json"]
    try:
        assert plan_mod.main() == 0
    finally:
        sys.argv = argv
    jobs = _jsonl(plan_root / "wp" / "job_manifest.jsonl")
    assert {j["wrapper_id"] for j in jobs} == {"boxed", "json"}
    assert _run(plan_root / "wp", tiny_model_dir, tmp_path / "out", "w", ("--authorization-ref", "TEST-ONLY")) == 0
    records = _jsonl(tmp_path / "out" / "w" / "raw_records.jsonl")
    assert len(records) == 5 and {r["answer_wrapper_id"] for r in records} == {"boxed"}  # the first five jobs are boxed
    for record in records:
        assert record["status"] == "OK" and record["gold_text"].startswith("\\boxed{")
        assert set(RAW_RECORD_FIELDS) <= set(record)
        assert record["correctness"] in ("correct", "wrong", "UNPARSEABLE", "MULTIPLE_CANDIDATES", "EMPTY")


def test_the_planner_can_plan_the_second_structure_batch_from_its_own_manifest(tmp_path, llama_tokenizer):
    manifest = "data/v2/structures/v2/factor_cell_manifest.jsonl"
    argv = sys.argv
    sys.argv = ["s147_plan", "--out-root", str(tmp_path), "--attempt-id", "b1", "--structures", "S11", "S20", "--models",
                "llama_primary", "--manifest", manifest]
    try:
        assert plan_mod.main() == 0
    finally:
        sys.argv = argv
    plan = json.loads((tmp_path / "b1" / "plan.json").read_text(encoding="utf-8"))
    jobs = _jsonl(tmp_path / "b1" / "job_manifest.jsonl")
    assert plan["manifest"]["path"] == manifest and plan["authorized_to_run"] is False
    assert {j["structure_id"] for j in jobs} == {"S11", "S20"} and len({j["job_id"] for j in jobs}) == len(jobs) == plan["n_jobs"]
    rows = [json.loads(line) for line in (REPO_ROOT / manifest).read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(jobs) == sum(1 for r in rows if r["feasible"] and r["structure_id"] in ("S11", "S20"))
