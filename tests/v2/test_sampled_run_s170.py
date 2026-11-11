"""End-to-end test of the Stage 15 work-queue runner on a tiny random Llama model on CPU: plan, work, a late duplicate worker
that finds nothing to do, collect, and the self-test refusals. No real checkpoint, no GPU, nothing submitted."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract_v2 as rc2  # noqa: E402
from physmon.governance.v2_contract import RAW_RECORD_FIELDS  # noqa: E402


def _load():
    spec = importlib.util.spec_from_file_location("s170", REPO_ROOT / "scripts/v2/s170_sampled_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s170 = _load()


@pytest.fixture(scope="module")
def tiny_model_dir(tmp_path_factory, llama_tokenizer):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    config = transformers.LlamaConfig(vocab_size=len(llama_tokenizer), hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                                      num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=2048)
    directory = tmp_path_factory.mktemp("tiny_llama_s170")
    transformers.LlamaForCausalLM(config).save_pretrained(str(directory))
    llama_tokenizer.save_pretrained(str(directory))
    if not (directory / "generation_config.json").exists():
        (directory / "generation_config.json").write_text(json.dumps({"do_sample": True, "temperature": 0.6, "top_p": 0.9}))
    return directory


@pytest.fixture(scope="module")
def manifest(tmp_path_factory, tiny_model_dir):
    files = []
    for path in sorted(tiny_model_dir.iterdir()):
        if path.is_file():
            files.append({"path": path.name, "size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    out = tmp_path_factory.mktemp("manifest") / "tiny.json"
    out.write_text(json.dumps({"revision": "tiny-rev", "files": files}))
    return out


@pytest.fixture(scope="module")
def dataset_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("ds")
    rows = [{"sample_id": f"S11-i{i}", "structure_id": "S11", "instance": i, "structure_uuid": "u", "template_cluster_id": "V2C-S11",
             "symbolic_program_hash": "h", "problem": f"A car accelerates {i}.", "gold_answer": {"value": 40.8 + i, "unit": "m"},
             "answer_unit": "m", "domain": "mechanics", "level": "high_school"} for i in range(3)]
    (directory / "dataset.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return directory


def plan(tmp_path, tiny_model_dir, manifest, dataset_dir, run_id="t1"):
    return s170.main(["plan", "--run-id", run_id, "--runs-dir", str(tmp_path / "runs"), "--purpose", "test",
                      "--dataset-dir", str(dataset_dir), "--model-key", "llama_primary", "--model-path", str(tiny_model_dir),
                      "--manifest", str(manifest), "--backend", "hf", "--env", "physmon", "--n-samples", "2",
                      "--max-new-tokens", "6", "--shard-size", "2", "--batch-size", "2", "--dtype", "float32"])


def work(tmp_path, tiny_model_dir, run_id="t1", extra=()):
    return s170.main(["work", "--run-id", run_id, "--runs-dir", str(tmp_path / "runs"), "--authorization-ref", "test",
                      "--queue-root", str(tmp_path / "queue" / run_id), "--device", "cpu", "--model-path", str(tiny_model_dir),
                      *extra])


def test_plan_work_duplicate_collect(tmp_path, tiny_model_dir, manifest, dataset_dir, monkeypatch):
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "deadbeef")
    assert plan(tmp_path, tiny_model_dir, manifest, dataset_dir) == 0
    spec = json.loads((tmp_path / "runs" / "t1" / "spec.json").read_text())
    assert spec["n_pairs"] == 6 and len(spec["shards"]) == 3 and spec["contract_version"] == rc2.CONTRACT_VERSION
    assert spec["model_revision"] == "tiny-rev" and spec["env_expected"]["torch"]
    seeds = [json.loads(line)["seed"] for name in spec["shards"]
             for line in (tmp_path / "runs" / "t1" / "shards" / f"{name}.jsonl").read_text().splitlines()]
    assert len(set(seeds)) == 6
    assert plan(tmp_path, tiny_model_dir, manifest, dataset_dir) == 2  # never overwrites a frozen run

    assert work(tmp_path, tiny_model_dir) == 0
    assert work(tmp_path, tiny_model_dir) == 0  # a late duplicate job finds nothing to do and exits at once
    assert s170.main(["collect", "--run-id", "t1", "--runs-dir", str(tmp_path / "runs"),
                      "--queue-root", str(tmp_path / "queue" / "t1"), "--results-dir", str(tmp_path / "results")]) == 0
    records = [json.loads(line) for line in (tmp_path / "results" / "t1" / "raw_records.jsonl").read_text().splitlines()]
    assert len(records) == 6 and len({r["job_id"] for r in records}) == 6
    for r in records:
        assert not [f for f in RAW_RECORD_FIELDS if f not in r]
        assert r["completion_status"] in rc2.COMPLETION_STATUSES and r["thinking_mode"] == "none"
        assert r["grade_declared"] in ("correct", "wrong", *rc2.COMPLETION_STATUSES)
        if r["completion_status"] != "COMPLETE":
            assert r["grade_declared"] == r["completion_status"]  # never relabelled wrong
        assert r["source_commit"] == "deadbeef" and r["backend"] == "hf"
    summary = json.loads((tmp_path / "results" / "t1" / "run_summary.json").read_text())
    assert summary["n_records"] == 6 and summary["n_shards_missing"] == 0


def test_self_test_refuses_a_changed_spec_and_changed_packages(tmp_path, tiny_model_dir, manifest, dataset_dir, monkeypatch):
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "deadbeef")
    assert plan(tmp_path, tiny_model_dir, manifest, dataset_dir, run_id="t2") == 0
    assert work(tmp_path, tiny_model_dir, "t2", ("--expect-spec-sha256", "0" * 64)) == s170.EXIT_SPEC
    spec_path = tmp_path / "runs" / "t2" / "spec.json"
    spec = json.loads(spec_path.read_text())
    spec["env_expected"]["torch"] = "0.0.0"
    spec_path.write_text(json.dumps(spec))
    assert work(tmp_path, tiny_model_dir, "t2") == s170.EXIT_ENV
    assert not any((tmp_path / "queue" / "t2" / "claims").iterdir())  # a refused worker claims nothing


def test_collect_refuses_a_partial_queue(tmp_path, tiny_model_dir, manifest, dataset_dir, monkeypatch):
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "deadbeef")
    assert plan(tmp_path, tiny_model_dir, manifest, dataset_dir, run_id="t3") == 0
    assert s170.main(["collect", "--run-id", "t3", "--runs-dir", str(tmp_path / "runs"),
                      "--queue-root", str(tmp_path / "queue" / "t3"), "--results-dir", str(tmp_path / "results")]) == 4


def test_request_seeds_are_deterministic_and_distinct():
    assert s170.request_seed(1, "a", 0) == s170.request_seed(1, "a", 0)
    assert s170.request_seed(1, "a", 0) != s170.request_seed(1, "a", 1) != s170.request_seed(2, "a", 1)


def test_plan_refuses_a_thinking_switch_for_a_model_without_one(tmp_path, tiny_model_dir, manifest, dataset_dir):
    code = s170.main(["plan", "--run-id", "t4", "--runs-dir", str(tmp_path / "runs"), "--purpose", "test",
                      "--dataset-dir", str(dataset_dir), "--model-key", "llama_primary", "--model-path", str(tiny_model_dir),
                      "--manifest", str(manifest), "--backend", "hf", "--env", "physmon", "--n-samples", "1",
                      "--max-new-tokens", "6", "--thinking", "on"])
    assert code == 2 and not (tmp_path / "runs" / "t4" / "spec.json").exists()


def test_plan_refuses_a_budget_beyond_the_context_length(tmp_path, tiny_model_dir, manifest, dataset_dir, monkeypatch):
    monkeypatch.setattr(s170, "env_versions", lambda env: {"python": "x", "torch": "x", "transformers": "x",
                                                           "vllm": "0.33.0", "tokenizers": "x"})
    code = s170.main(["plan", "--run-id", "t5", "--runs-dir", str(tmp_path / "runs"), "--purpose", "test",
                      "--dataset-dir", str(dataset_dir), "--model-key", "llama_primary", "--model-path", str(tiny_model_dir),
                      "--manifest", str(manifest), "--backend", "vllm", "--env", "physmon", "--n-samples", "1",
                      "--max-new-tokens", "1000", "--max-model-len", "512"])
    assert code == 2 and not (tmp_path / "runs" / "t5" / "spec.json").exists()


def test_a_record_that_cannot_be_scored_becomes_an_explicit_error_record():
    from physmon.models.generation import GenResult

    pair = {"job_id": "S1-i0:no_cue", "sample_index": 0, "seed": 1, "structure_id": "S1", "instance": 0, "cell_id": "no_cue",
            "gold_value": "not a number", "gold_unit": "m"}
    spec = {"run_id": "r", "thinking": "none"}
    record = s170.safe_record(pair, GenResult("x", "Final answer: 3 m", 5, False, "stop"), spec,
                              {"source_commit": "c", "shard": "shard_0000", "worker_id": "w", "slurm_job_id": "1"})
    assert record["status"] == "RECORD_ERROR" and record["generated_answer_raw"] == "Final answer: 3 m"
    assert record["grade_declared"] == "RECORD_ERROR"
