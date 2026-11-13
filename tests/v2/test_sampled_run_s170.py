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


def plan_backend(tmp_path, tiny_model_dir, manifest, dataset_dir, run_id, backend, monkeypatch):
    if backend == "vllm":  # the vLLM env is not this process: plan and self-test see the same stand-in version set
        fake = {**s170.current_versions(), "vllm": "0.33.0-test"}
        monkeypatch.setattr(s170, "env_versions", lambda env: fake)
        monkeypatch.setattr(s170, "current_versions", lambda: fake)
    return s170.main(["plan", "--run-id", run_id, "--runs-dir", str(tmp_path / "runs"), "--purpose", "test",
                      "--dataset-dir", str(dataset_dir), "--model-key", "llama_primary", "--model-path", str(tiny_model_dir),
                      "--manifest", str(manifest), "--backend", backend, "--env", "physmon", "--n-samples", "1",
                      "--max-new-tokens", "6", "--shard-size", "3", "--batch-size", "3", "--dtype", "float32",
                      "--max-model-len", "512"])


def test_vllm_path_never_touches_cuda_in_the_parent_and_spawns(tmp_path, tiny_model_dir, manifest, dataset_dir,
                                                               monkeypatch):
    """Regression for jobs 444874-444879: CUDA initialised in the runner before vLLM forked its engine process."""

    import os

    import torch

    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "test-commit")
    assert plan_backend(tmp_path, tiny_model_dir, manifest, dataset_dir, "v1", "vllm", monkeypatch) == 0
    monkeypatch.delenv("VLLM_WORKER_MULTIPROC_METHOD", raising=False)

    def forbidden(*a, **k):
        raise AssertionError("torch.cuda used in the parent process of a vLLM run")

    monkeypatch.setattr(torch.cuda, "is_available", forbidden)
    monkeypatch.setattr(torch.cuda, "get_device_name", forbidden)
    monkeypatch.setattr(s170, "nvidia_smi_gpu", lambda: "FAKE H100")
    monkeypatch.setattr(s170, "libcuda_dirs", lambda: ["/fake/driver/lib"])
    seen = {}
    real_build = s170.build_backend

    def fake_build(spec, model_dir, device):
        seen["mp"] = os.environ.get("VLLM_WORKER_MULTIPROC_METHOD")
        return real_build({**spec, "backend": "hf"}, model_dir, "cpu")  # a CPU stand-in for the engine

    monkeypatch.setattr(s170, "build_backend", fake_build)
    try:
        code = s170.main(["work", "--run-id", "v1", "--runs-dir", str(tmp_path / "runs"), "--authorization-ref", "test",
                          "--queue-root", str(tmp_path / "queue" / "v1"), "--device", "cuda",
                          "--model-path", str(tiny_model_dir)])
    finally:
        os.environ.pop("VLLM_WORKER_MULTIPROC_METHOD", None)
    assert code == 0 and seen["mp"] == "spawn"
    records = [json.loads(line) for line in next((tmp_path / "queue" / "v1" / "results").glob("*.jsonl")).read_text().splitlines()]
    assert records and all(r["gpu_name"] == "FAKE H100" for r in records)


def _fake_canary(root, spec, records):
    import hashlib as _h

    (root / "results").mkdir(parents=True, exist_ok=True)
    (root / "done").mkdir(parents=True, exist_ok=True)
    for shard in spec["shards"]:
        path = root / "results" / f"{shard}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in records))
        (root / "done" / f"{shard}.json").write_text(json.dumps(
            {"records_sha256": _h.sha256(path.read_bytes()).hexdigest(), "n_record_errors": 0}))


def test_a_gated_run_waits_for_its_canary_and_starts_after_it_passes(tmp_path, tiny_model_dir, manifest, dataset_dir,
                                                                     monkeypatch, capsys):
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "test-commit")
    assert plan_backend(tmp_path, tiny_model_dir, manifest, dataset_dir, "canary", "hf", monkeypatch) == 0
    assert plan_backend(tmp_path, tiny_model_dir, manifest, dataset_dir, "main", "hf", monkeypatch) == 0
    (tmp_path / "queue" / "main").mkdir(parents=True)
    (tmp_path / "queue" / "main" / "gate.json").write_text(json.dumps({"requires": ["canary"]}))
    assert work(tmp_path, tiny_model_dir, run_id="main") == 0
    assert '"gate_closed"' in capsys.readouterr().out and not list((tmp_path / "queue" / "main").glob("done/*.json"))
    spec = json.loads((tmp_path / "runs" / "canary" / "spec.json").read_text())
    good = {"job_id": "x", "status": "OK", "n_generated_tokens": 5, "finish_reason": "stop", "completion_status": "COMPLETE"}
    _fake_canary(tmp_path / "queue" / "canary", spec, [dict(good, completion_status="EMPTY", n_generated_tokens=0)])
    runs_dir = str(tmp_path / "runs")
    assert not s170.canary_verdict("canary", tmp_path / "queue" / "canary", runs_dir)[0]  # no tokens: closed
    _fake_canary(tmp_path / "queue" / "canary", spec, [dict(good, status="RECORD_ERROR")])
    assert not s170.canary_verdict("canary", tmp_path / "queue" / "canary", runs_dir)[0]
    _fake_canary(tmp_path / "queue" / "canary", spec, [dict(good, finish_reason="abort")])
    assert not s170.canary_verdict("canary", tmp_path / "queue" / "canary", runs_dir)[0]
    _fake_canary(tmp_path / "queue" / "canary", spec, [good, dict(good, completion_status="BUDGET_EXHAUSTED",
                                                                  finish_reason="length")])
    assert s170.canary_verdict("canary", tmp_path / "queue" / "canary", runs_dir)[0]
    assert work(tmp_path, tiny_model_dir, run_id="main") == 0
    assert len(list((tmp_path / "queue" / "main" / "done").glob("*.json"))) == len(
        json.loads((tmp_path / "runs" / "main" / "spec.json").read_text())["shards"])
    (tmp_path / "queue" / "canary" / "results" / f"{sorted(spec['shards'])[0]}.jsonl").write_text("tampered\n")
    assert not s170.canary_verdict("canary", tmp_path / "queue" / "canary", runs_dir)[0]  # checksum


def test_collect_refuses_a_sealed_run(tmp_path, tiny_model_dir, manifest, dataset_dir, monkeypatch, capsys):
    assert plan_backend(tmp_path, tiny_model_dir, manifest, dataset_dir, "sealed", "hf", monkeypatch) == 0
    (tmp_path / "runs" / "sealed" / "SEALED.json").write_text(json.dumps({"until": "G1 freeze", "reason": "test"}))
    args = ["collect", "--run-id", "sealed", "--runs-dir", str(tmp_path / "runs"), "--queue-root",
            str(tmp_path / "queue" / "sealed"), "--results-dir", str(tmp_path / "results")]
    assert s170.main(args) == 2 and "sealed until G1 freeze" in capsys.readouterr().err
    assert s170.main([*args, "--unseal-ref", "decision-log entry X"]) != 0  # unsealed, then refused as partial
    assert "sealed" not in capsys.readouterr().err


def test_an_abnormal_finish_becomes_an_error_record_not_an_outcome():
    from physmon.models.generation import GenResult

    pair = {"job_id": "S1-i0:no_cue", "sample_index": 0, "seed": 1, "structure_id": "S1", "instance": 0, "cell_id": "no_cue",
            "gold_value": 3.0, "gold_unit": "m"}
    record = s170.safe_record(pair, GenResult("x", "Final answer: 3 m", 5, False, "abort"), {"run_id": "r", "thinking": "none"},
                              {"source_commit": "c", "shard": "s", "worker_id": "w", "slurm_job_id": "1"})
    assert record["status"] == "RECORD_ERROR" and "abort" in record["error"] and record["generated_answer_raw"]


def test_c_compiler_guard_uses_a_working_compiler_and_refuses_without_one(tmp_path, monkeypatch):
    import shutil

    monkeypatch.delenv("CC", raising=False)
    found = s170.ensure_c_compiler()
    assert found["ok"] and s170._compiles(found["cc"])
    broken = tmp_path / "gcc"
    broken.write_text("#!/bin/sh\nexit 1\n")
    broken.chmod(0o755)
    monkeypatch.setattr(shutil, "which", lambda name: str(broken))
    monkeypatch.setattr(s170, "TOOLCHAIN_GCC", tmp_path / "missing" / "gcc")
    monkeypatch.delenv("CC", raising=False)
    assert s170.ensure_c_compiler() == {"ok": False, "cc": None, "tried": [str(broken), str(broken)]}


def test_libcuda_lookup_matches_tritons_rules(tmp_path, monkeypatch):
    monkeypatch.setattr(s170.subprocess, "run", lambda *a, **k: s170.subprocess.CompletedProcess(a, 0, "", ""))
    monkeypatch.setenv("LD_LIBRARY_PATH", str(tmp_path))
    assert s170.libcuda_dirs() == []
    (tmp_path / "libcuda.so.1").write_text("")
    assert s170.libcuda_dirs() == [str(tmp_path)]
