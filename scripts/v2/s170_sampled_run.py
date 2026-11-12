#!/usr/bin/env python3
"""Stage 15: sampled reasoning runs as a shared work queue (plan of record Sections 4.5, 5.1, 9; journal stage15).

Four subcommands:

* `plan`    (login node) freezes a run: the job list, k samples per job with a deterministic seed each, the model, backend,
            environment and expected package versions, the sampling defaults, the token budget, and the shards. Writes
            `data/v2/runs/<run_id>/spec.json` and `shards/*.jsonl`; these are committed before any job is submitted.
* `work`    (GPU job) runs from an immutable code snapshot. It exits at once if nothing is left, else self-tests (package
            versions, spec hash, every model file's SHA-256 against its manifest, a short generation), then claims shards
            from `/scratch/pabitra/physmon/queue/<run_id>/` until none is left or the time budget would be exceeded. The
            same `work` job may be submitted to several partitions: shards are claimed atomically, so nothing is duplicated.
* `collect` (login node) verifies that every shard is done and its records' hash matches, and writes
            `results/stage15/<run_id>/raw_records.jsonl` and `run_summary.json`.
* `status`  prints the queue's progress.

Records follow the v2 data contract (`RAW_RECORD_FIELDS`) plus the reasoning-v2 fields: completion status (outcome O3),
the three grading views, the dimension-checked relative error, the O2 semantic-recovery reading, thinking and token counts,
and the worker's provenance. A record that did not complete is never relabelled wrong.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract_v2 as rc2  # noqa: E402
from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.governance.v2_contract import missing_record_fields  # noqa: E402
from physmon.models import generation as gen  # noqa: E402
from physmon.runtime.workqueue import WorkQueue, sha256_file  # noqa: E402
from physmon.scoring import grading_views as gv  # noqa: E402
from physmon.utils.paths import expand_model_path, physmon_scratch_path  # noqa: E402

RUNS_DIR = "data/v2/runs"
RESULTS_DIR = "results/stage15"
REGISTRY = "docs/model_registry.yml"
MANIFESTS = "docs/model_manifests"
ENV_ROOTS = (Path.home() / ".conda" / "envs", Path("/scratch/pabitra/physmon/envs"))  # home envs, then scratch-hosted envs
PACKAGES = ("torch", "transformers", "vllm", "tokenizers")
EXIT_NOTHING_TO_DO, EXIT_NO_GPU, EXIT_ENV, EXIT_MODEL, EXIT_SPEC, EXIT_SMOKE = 0, 3, 10, 11, 12, 13


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def request_seed(seed_base: int, job_id: str, sample_index: int) -> int:
    return int(sha256_text(f"{seed_base}:{job_id}:{sample_index}")[:8], 16)


def queue_root(run_id: str, override: str | None = None) -> Path:
    return Path(override) if override else physmon_scratch_path("queue", run_id)


# --- plan -------------------------------------------------------------------------------------------------------------------

JOB_FIELDS = ("job_id", "structure_id", "instance", "cell_id", "structure_uuid", "template_cluster_id",
              "symbolic_program_hash", "prompt", "gold_value", "gold_unit", "domain", "level", "cue_semantic_role",
              "cue_numeric_value", "unit_type", "numeric_proximity", "digit_overlap", "cue_position", "isolation_condition",
              "expected_effect", "foils")


def jobs_from_dataset(dataset_dir: Path, keep: set[str] | None) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in (dataset_dir / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    jobs = []
    for r in rows:
        if keep is not None and f"{r['structure_id']}:{r['instance']}" not in keep:
            continue
        jobs.append({"job_id": f"{r['sample_id']}:no_cue", "structure_id": r["structure_id"], "instance": r["instance"],
                     "cell_id": "no_cue", "structure_uuid": r["structure_uuid"], "template_cluster_id": r["template_cluster_id"],
                     "symbolic_program_hash": r["symbolic_program_hash"], "prompt": r["problem"],
                     "gold_value": float(r["gold_answer"]["value"]), "gold_unit": r["answer_unit"], "domain": r.get("domain"),
                     "level": r.get("level"), "cue_semantic_role": None, "cue_numeric_value": None, "unit_type": None,
                     "numeric_proximity": None, "digit_overlap": None, "cue_position": None, "isolation_condition": None,
                     "expected_effect": None, "foils": {}})
    return jobs


def env_prefix(env_name: str) -> Path:
    """The directory of a named conda environment: under ~/.conda/envs, else under the scratch environment root."""

    for root in ENV_ROOTS:
        if (root / env_name / "bin" / "python").exists():
            return root / env_name
    raise SystemExit(f"no conda environment named {env_name} under {[str(r) for r in ENV_ROOTS]}")


@functools.lru_cache(maxsize=None)
def env_versions(env_name: str) -> dict[str, str | None]:
    """Package versions of a conda environment, read by running its own interpreter (never the user site)."""

    python = env_prefix(env_name) / "bin" / "python"
    code = ("import importlib, json, sys\nout={'python': sys.version.split()[0]}\n"
            f"for p in {list(PACKAGES)!r}:\n"
            "    try:\n        out[p]=importlib.import_module(p).__version__\n    except Exception:\n        out[p]=None\n"
            "print(json.dumps(out))")
    env = {**os.environ, "PYTHONNOUSERSITE": "1"}
    out = subprocess.run([str(python), "-c", code], capture_output=True, text=True, env=env, timeout=600, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def resolve(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def model_manifest(model_key: str, override: str | None = None) -> dict[str, Any]:
    path = Path(override) if override else REPO_ROOT / MANIFESTS / f"{model_key}.json"
    if not path.exists():
        raise SystemExit(f"no manifest for {model_key}: {path} (pin the model first)")
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_plan(args: argparse.Namespace) -> int:
    run_dir = resolve(args.runs_dir) / args.run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        print(f"Refusing to overwrite an existing run: {run_dir}", file=sys.stderr)
        return 2
    registry = yaml.safe_load((REPO_ROOT / REGISTRY).read_text(encoding="utf-8"))["models"][args.model_key]
    manifest = model_manifest(args.model_key, args.manifest)
    model_dir = Path(args.model_path or expand_model_path(registry["path"]))
    thinking = {"on": True, "off": False, "none": None}[args.thinking]
    family = "qwen3" if registry["name"].startswith("Qwen/Qwen3") else registry.get("family", "")
    if family == "qwen3" and thinking is None:
        print("Refusing: a Qwen3 model needs --thinking on or off (its template thinks by default).", file=sys.stderr)
        return 2
    if family != "qwen3" and thinking is not None:
        print(f"Refusing: --thinking {args.thinking} for a model without a thinking switch ({registry['name']}).",
              file=sys.stderr)
        return 2
    sampling = (gen.SamplingSpec(do_sample=False, temperature=1.0, top_p=1.0, top_k=0, source="greedy") if args.greedy
                else gen.sampling_from_generation_config(model_dir, thinking=thinking, family=family))
    keep = set(json.loads(Path(args.ids_file).read_text(encoding="utf-8"))) if args.ids_file else None
    dataset_dir = resolve(args.dataset_dir)
    if args.cells:
        cells_path = resolve(args.cells)
        jobs = [json.loads(line) for line in cells_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if keep is not None:
            jobs = [j for j in jobs if f"{j['structure_id']}:{j['instance']}" in keep]
        missing = [k for k in JOB_FIELDS if any(k not in j for j in jobs)]
        if missing:
            print(f"Refusing: cell rows lack the job fields {missing}", file=sys.stderr)
            return 2
    else:
        jobs = jobs_from_dataset(dataset_dir, keep)
    if args.max_jobs:
        jobs = jobs[: args.max_jobs]
    import transformers

    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
    prompt_lengths = []
    for job in jobs:
        user = rc2.user_turn(job["prompt"], job["gold_unit"] if not args.no_state_unit else None)
        prompt_lengths.append(len(gen.chat_prompt_ids(tokenizer, user, enable_thinking=thinking)[1]))
    max_prompt = max(prompt_lengths) if prompt_lengths else 0
    if args.backend == "vllm" and max_prompt + args.max_new_tokens > args.max_model_len:
        print(f"Refusing: longest prompt ({max_prompt} tokens) + max_new_tokens ({args.max_new_tokens}) exceeds "
              f"max_model_len ({args.max_model_len}); records would be cut below the declared budget.", file=sys.stderr)
        return 2
    pairs = [{**job, "sample_index": k, "seed": request_seed(args.seed, job["job_id"], k)}
             for job in jobs for k in range(args.sample_offset, args.sample_offset + args.n_samples)]
    pairs.sort(key=lambda p: (p["structure_id"], p["instance"], p["cell_id"], p["sample_index"]))
    shards: dict[str, list[dict[str, Any]]] = {}
    for i in range(0, len(pairs), args.shard_size):
        shards[f"shard_{i // args.shard_size:04d}"] = pairs[i:i + args.shard_size]
    (run_dir / "shards").mkdir(parents=True)
    shard_hashes = {}
    for name, rows in shards.items():
        path = run_dir / "shards" / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        shard_hashes[name] = sha256_file(path)
    versions = env_versions(args.env)
    if args.backend == "vllm" and not versions.get("vllm"):
        print(f"Refusing: backend vllm but environment {args.env} has no vllm", file=sys.stderr)
        return 2
    spec = {
        "run_id": args.run_id, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "purpose": args.purpose,
        "data_role": args.data_role, "phase_id": args.phase_id,
        "source": "role_cells" if args.cells else "dataset_base",
        "dataset_dir": args.cells if args.cells else args.dataset_dir,
        "dataset_files_sha256": ({Path(args.cells).name: sha256_file(resolve(args.cells))} if args.cells
                                 else {f: sha256_file(dataset_dir / f) for f in ("dataset.jsonl",)}),
        "ids_file": args.ids_file, "n_jobs": len(jobs), "n_samples": args.n_samples, "sample_offset": args.sample_offset,
        "n_pairs": len(pairs), "seed_base": args.seed, "model_key": args.model_key, "model_name": registry["name"],
        "model_path": registry["path"], "model_revision": manifest.get("revision"),
        "model_files": {f["path"]: {"sha256": f["sha256"], "size": f["size"]} for f in manifest["files"]},
        "backend": args.backend, "env": args.env, "env_prefix": str(env_prefix(args.env)), "env_expected": versions, "thinking": args.thinking, "family": family,
        "sampling": sampling.as_dict(), "max_new_tokens": args.max_new_tokens, "max_model_len": args.max_model_len,
        "batch_size": args.batch_size, "dtype": args.dtype, "state_unit": not args.no_state_unit,
        "max_prompt_tokens": max_prompt,
        "contract_version": rc2.CONTRACT_VERSION, "reasoning_contract_fingerprint": rc2.contract_fingerprint(),
        "scoring_contract_fingerprint": sc.contract_fingerprint(), "shards": shard_hashes, "shard_size": args.shard_size,
        "est_shard_s": args.est_shard_s,
    }
    (run_dir / "spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"run_dir": str(run_dir), "n_jobs": len(jobs), "n_pairs": len(pairs), "n_shards": len(shards),
                      "spec_sha256": sha256_file(run_dir / "spec.json"), "sampling": spec["sampling"],
                      "env_expected": versions}, indent=2))
    return 0


# --- work -------------------------------------------------------------------------------------------------------------------

def load_spec(run_id: str, runs_dir: str = RUNS_DIR) -> tuple[dict[str, Any], Path]:
    run_dir = resolve(runs_dir) / run_id
    return json.loads((run_dir / "spec.json").read_text(encoding="utf-8")), run_dir


def current_versions() -> dict[str, str | None]:
    import importlib

    out: dict[str, str | None] = {"python": platform.python_version()}
    for p in PACKAGES:
        try:
            out[p] = importlib.import_module(p).__version__
        except Exception:
            out[p] = None
    return out


def self_test(spec: dict[str, Any], run_dir: Path, model_dir: Path, *, expected_spec_sha: str | None,
              check_hashes: bool = True) -> tuple[int, dict[str, Any]]:
    """Package versions, spec and shard hashes, and every model file's SHA-256; (exit code, report)."""

    report: dict[str, Any] = {}
    spec_sha = sha256_file(run_dir / "spec.json")
    report["spec_sha256"] = spec_sha
    if expected_spec_sha and spec_sha != expected_spec_sha:
        return EXIT_SPEC, {**report, "error": f"spec hash {spec_sha} != expected {expected_spec_sha}"}
    for name, digest in spec["shards"].items():
        if sha256_file(run_dir / "shards" / f"{name}.jsonl") != digest:
            return EXIT_SPEC, {**report, "error": f"shard {name} hash mismatch"}
    versions = current_versions()
    report["versions"] = versions
    mismatched = {k: (versions.get(k), v) for k, v in spec["env_expected"].items() if versions.get(k) != v}
    if mismatched:
        return EXIT_ENV, {**report, "error": f"package versions differ from the plan: {mismatched}"}
    if check_hashes:
        bad = []
        for rel, meta in spec["model_files"].items():
            path = model_dir / rel
            if not path.exists() or path.stat().st_size != meta["size"] or sha256_file(path) != meta["sha256"]:
                bad.append(rel)
        if bad:
            return EXIT_MODEL, {**report, "error": f"model files differ from the manifest: {bad[:5]} ({len(bad)} files)"}
        report["model_files_verified"] = len(spec["model_files"])
    return 0, report


def make_record(pair: dict[str, Any], result: gen.GenResult, spec: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    thinking_expected = spec["thinking"] == "on"
    completion = rc2.assess(result.text, hit_token_limit=result.hit_limit, thinking_expected=thinking_expected)
    gold_value, gold_unit = float(pair["gold_value"]), pair["gold_unit"]
    views = gv.grade_all(completion.parsed, gold_value, gold_unit)
    recovery = rc2.recover_final(completion.answer_text) if completion.status != "COMPLETE" else None
    o2_parse = completion.parsed if completion.status == "COMPLETE" else (recovery.parsed if recovery else completion.parsed)
    o2_views = gv.grade_all(o2_parse, gold_value, gold_unit) if o2_parse.status == "PARSED" else None
    foils = gv.match_foils(views["value_in_gold_unit"], pair.get("foils") or {})
    record: dict[str, Any] = {
        "run_id": spec["run_id"], "phase_id": spec["phase_id"], "exploratory_or_confirmatory": "exploratory",
        "data_role": spec["data_role"], "structure_uuid": pair["structure_uuid"], "template_cluster_id": pair["template_cluster_id"],
        "symbolic_program_hash": pair["symbolic_program_hash"], "cue_type": pair["cue_semantic_role"],
        "cue_semantic_role": pair["cue_semantic_role"], "cue_numeric_value": pair["cue_numeric_value"],
        "unit_type": pair["unit_type"], "numeric_proximity": pair["numeric_proximity"], "digit_overlap": pair["digit_overlap"],
        "cue_position": pair["cue_position"], "isolation_condition": pair["isolation_condition"],
        "model_id": spec["model_name"], "model_commit": spec["model_revision"], "tokenizer_commit": ctx["tokenizer_sha256"],
        "chat_template": ctx["chat_template_sha256"], "answer_wrapper_id": f"{rc2.CONTRACT_VERSION}:final-line",
        "target_answer_ids": None, "target_span_start": None, "target_span_end": None,
        "generated_answer_raw": result.text,
        "parsed_answer": ({"value": completion.parsed.value, "unit": completion.parsed.unit}
                          if completion.status == "COMPLETE" else None),
        "parse_status": completion.status, "completion_status": completion.status, "gold_logprob_raw": None,
        "gold_logprob_per_token": None, "alternative_scores": None,
        "correctness": views["declared"], "correctness_rule": "declared (protocol 4b)",
        "grade_declared": views["declared"], "grade_convertible": views["convertible"], "grade_rel1pct": views["rel1pct"],
        "dimension_status": views["dimension_status"], "value_in_gold_unit": views["value_in_gold_unit"],
        "relative_error_dimchecked": views["relative_error_dimchecked"],
        "o2_source": "contract" if completion.status == "COMPLETE" else (recovery.status if recovery else "NONE"),
        "o2_semantic_correct": (o2_views["convertible"] if o2_views else "UNKNOWN"),
        "o2_recovered_value": o2_parse.value if (recovery and recovery.status == "RECOVERED") else None,
        "o2_recovered_unit": o2_parse.unit if (recovery and recovery.status == "RECOVERED") else None,
        "foil_match_class": foils["match_class"], "foil_matches": foils["matches"],
        "n_final_lines": completion.n_final_lines, "n_generated_tokens": result.n_new_tokens, "hit_token_limit": result.hit_limit,
        "finish_reason": result.finish_reason, "thinking_mode": spec["thinking"], "thinking_closed": completion.thinking_closed,
        "n_thinking_chars": len(completion.thinking_text), "n_answer_chars": len(completion.answer_text),
        "sample_index": pair["sample_index"], "seed": pair["seed"], "seed_scope": result.extra.get("seed_scope"),
        "sampling": spec["sampling"], "max_new_tokens": spec["max_new_tokens"], "backend": ctx["backend"],
        "dtype": spec["dtype"], "oom_fallback": result.oom_fallback, "wall_time": ctx["wall_per_record"],
        "artifact_checksum": None, "job_id": f"{pair['job_id']}:s{pair['sample_index']}", "structure_id": pair["structure_id"],
        "instance": pair["instance"], "cell_id": pair["cell_id"], "expected_effect": pair["expected_effect"],
        "domain": pair.get("domain"), "level": pair.get("level"), "gold_value": gold_value, "gold_unit": gold_unit,
        "unit_stated_in_prompt": spec["state_unit"], "status": "OK", "role": pair.get("role"),
        "contract_fingerprint": spec["scoring_contract_fingerprint"],
        "reasoning_contract_fingerprint": spec["reasoning_contract_fingerprint"], "source_commit": ctx["source_commit"],
        "authorization_ref": ctx["authorization_ref"], "shard": ctx["shard"], "worker_id": ctx["worker_id"],
        "slurm_job_id": ctx["slurm_job_id"], "partition": ctx["partition"], "gpu_name": ctx["gpu_name"],
    }
    missing = missing_record_fields(record)
    if missing:
        raise RuntimeError(f"record violates the v2 data contract; missing {missing}")
    record["artifact_checksum"] = sha256_text(json.dumps(record, sort_keys=True, default=str))
    return record


def save_raw(root: Path, shard: str, worker_id: str, rows: list[dict[str, Any]], results: list[gen.GenResult]) -> None:
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{shard}.{worker_id.replace(':', '_')}.{time.time_ns()}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row, res in zip(rows, results, strict=True):
            handle.write(json.dumps({"job_id": row["job_id"], "sample_index": row["sample_index"], "seed": row["seed"],
                                     "text": res.text, "n_new_tokens": res.n_new_tokens, "hit_limit": res.hit_limit,
                                     "finish_reason": res.finish_reason}, ensure_ascii=False) + "\n")


def safe_record(pair: dict[str, Any], result: gen.GenResult, spec: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """make_record, or an explicit RECORD_ERROR record with the raw text when scoring fails (never a silent drop)."""

    try:
        return make_record(pair, result, spec, ctx)
    except Exception as exc:  # the generation is kept; the record says why it could not be scored
        record = {name: None for name in ("structure_uuid", "template_cluster_id", "symbolic_program_hash")}
        record.update({"run_id": spec["run_id"], "status": "RECORD_ERROR", "error": repr(exc)[:500],
                       "job_id": f"{pair['job_id']}:s{pair['sample_index']}", "structure_id": pair.get("structure_id"),
                       "instance": pair.get("instance"), "cell_id": pair.get("cell_id"), "sample_index": pair.get("sample_index"),
                       "seed": pair.get("seed"), "generated_answer_raw": result.text, "n_generated_tokens": result.n_new_tokens,
                       "hit_token_limit": result.hit_limit, "completion_status": "RECORD_ERROR",
                       "grade_declared": "RECORD_ERROR", "source_commit": ctx.get("source_commit"), "shard": ctx.get("shard"),
                       "worker_id": ctx.get("worker_id"), "slurm_job_id": ctx.get("slurm_job_id")})
        return record


def build_backend(spec: dict[str, Any], model_dir: Path, device: str):
    import transformers

    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
    if spec["backend"] == "vllm":
        backend = gen.VLLMBackend(model_dir, dtype=spec["dtype"], max_model_len=spec["max_model_len"])
    else:
        import torch

        model = transformers.AutoModelForCausalLM.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False,
                                                                  dtype=getattr(torch, spec["dtype"]))
        model.to(device)
        model.eval()
        backend = gen.HFBackend(model, tokenizer, batch_size=spec["batch_size"])
    return tokenizer, backend


def gpu_name() -> str:
    try:
        import torch

        return torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
    except Exception:
        return "unknown"


def cmd_work(args: argparse.Namespace) -> int:
    spec, run_dir = load_spec(args.run_id, args.runs_dir)
    queue = WorkQueue(queue_root(args.run_id, args.queue_root), list(spec["shards"]), stale_after_s=args.stale_after_s)
    if not queue.unclaimed() and not (args.self_test_only or args.check_only):
        print(json.dumps({"event": "nothing_to_do", "status": queue.status()}), flush=True)
        return EXIT_NOTHING_TO_DO
    started = time.time()
    if (args.time_budget_s is not None and not args.self_test_only
            and args.time_budget_s < 1.25 * spec["est_shard_s"] + args.startup_allowance_s):
        print(json.dumps({"event": "budget_too_small", "budget_s": args.time_budget_s, "est_shard_s": spec["est_shard_s"]}),
              flush=True)
        return EXIT_NOTHING_TO_DO
    source_commit = os.environ.get("PHYSMON_SOURCE_COMMIT", "")
    if not source_commit:
        print("Refusing to run: PHYSMON_SOURCE_COMMIT is not set (jobs run from a snapshot of a pushed commit).", file=sys.stderr)
        return EXIT_SPEC
    if args.device.startswith("cuda") and not args.check_only:
        import torch

        if not torch.cuda.is_available():
            print("Refusing to run: a CUDA device was requested but none is available.", file=sys.stderr)
            return EXIT_NO_GPU
    model_dir = Path(args.model_path or expand_model_path(spec["model_path"]))
    code, report = self_test(spec, run_dir, model_dir, expected_spec_sha=args.expect_spec_sha256,
                             check_hashes=not args.skip_model_hash)
    header = {"event": "self_test", "code": code, "report": report, "host": socket.gethostname(),
              "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""), "partition": os.environ.get("SLURM_JOB_PARTITION", ""),
              "source_commit": source_commit, "elapsed_s": round(time.time() - started, 1)}
    print(json.dumps(header, default=str), flush=True)
    if code or args.check_only:
        return code
    tokenizer, backend = build_backend(spec, model_dir, args.device)
    ctx = {"tokenizer_sha256": sha256_file(model_dir / "tokenizer.json") if (model_dir / "tokenizer.json").exists() else None,
           "chat_template_sha256": sha256_text(str(getattr(tokenizer, "chat_template", "") or "")), "backend": backend.name,
           "source_commit": source_commit, "authorization_ref": args.authorization_ref, "worker_id": queue.worker_id,
           "slurm_job_id": queue.slurm_job_id, "partition": os.environ.get("SLURM_JOB_PARTITION", ""), "gpu_name": gpu_name()}
    enable_thinking = {"on": True, "off": False, "none": None}[spec["thinking"]]
    sampling = gen.SamplingSpec(**spec["sampling"])

    def requests_for(rows: list[dict[str, Any]]) -> list[gen.GenRequest]:
        reqs = []
        for row in rows:
            user = rc2.user_turn(row["prompt"], row["gold_unit"] if spec["state_unit"] else None)
            _, ids = gen.chat_prompt_ids(tokenizer, user, enable_thinking=enable_thinking)
            reqs.append(gen.GenRequest(f"{row['job_id']}:s{row['sample_index']}", ids, int(row["seed"])))
        return reqs

    first_shard = run_dir / "shards" / f"{sorted(spec['shards'])[0]}.jsonl"
    smoke_row = json.loads(first_shard.read_text(encoding="utf-8").splitlines()[0])
    smoke = backend.generate(requests_for([smoke_row]), 16, sampling)[0]
    print(json.dumps({"event": "smoke", "n_new_tokens": smoke.n_new_tokens, "text_head": smoke.text[:80]}), flush=True)
    if smoke.n_new_tokens < 1:
        return EXIT_SMOKE
    if args.self_test_only:
        print(json.dumps({"event": "self_test_only_done", "elapsed_s": round(time.time() - started, 1)}), flush=True)
        return 0
    shard_times: list[float] = []
    n_shards = n_records = 0
    while True:
        estimate = max(shard_times) if shard_times else spec["est_shard_s"]
        if args.time_budget_s and (time.time() - started) + 1.25 * estimate > args.time_budget_s:
            print(json.dumps({"event": "stop_time_budget", "elapsed_s": round(time.time() - started, 1),
                              "estimate_s": estimate}), flush=True)
            break
        shard = queue.claim_next()
        if shard is None:
            break
        rows = [json.loads(line) for line in (run_dir / "shards" / f"{shard}.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()]
        try:
            t0 = time.time()
            results = backend.generate(requests_for(rows), spec["max_new_tokens"], sampling)
            wall = time.time() - t0
            save_raw(queue.root, shard, queue.worker_id, rows, results)  # raw generations survive any scoring failure
            shard_ctx = {**ctx, "shard": shard, "wall_per_record": round(wall / max(len(rows), 1), 4)}
            records = [safe_record(row, res, spec, shard_ctx) for row, res in zip(rows, results, strict=True)]
            queue.complete(shard, records, {"wall_s": round(wall, 1), "tokens": sum(r.n_new_tokens for r in results),
                                            "partition": ctx["partition"], "gpu_name": ctx["gpu_name"],
                                            "n_record_errors": sum(r["status"] == "RECORD_ERROR" for r in records)})
        except BaseException:
            queue.release(shard)  # give the shard back so another worker can take it; then fail loudly
            raise
        shard_times.append(wall)
        n_shards += 1
        n_records += len(records)
        print(json.dumps({"event": "shard_done", "shard": shard, "n_records": len(records), "wall_s": round(wall, 1),
                          "tokens": sum(r.n_new_tokens for r in results), "queue": queue.status()}), flush=True)
        queue.log_worker({"n_shards": n_shards, "n_records": n_records, "last_shard": shard, "partition": ctx["partition"]})
    print(json.dumps({"event": "worker_done", "n_shards": n_shards, "n_records": n_records,
                      "elapsed_s": round(time.time() - started, 1), "queue": queue.status()}), flush=True)
    return 0


# --- collect / status -------------------------------------------------------------------------------------------------------

def cmd_collect(args: argparse.Namespace) -> int:
    spec, run_dir = load_spec(args.run_id, args.runs_dir)
    root = queue_root(args.run_id, args.queue_root)
    out_dir = resolve(args.results_dir) / args.run_id
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to overwrite: {out_dir}", file=sys.stderr)
        return 2
    missing, bad = [], []
    records: list[str] = []
    workers: dict[str, int] = {}
    for shard in sorted(spec["shards"]):
        done = root / "done" / f"{shard}.json"
        result = root / "results" / f"{shard}.jsonl"
        if not done.exists() or not result.exists():
            missing.append(shard)
            continue
        meta = json.loads(done.read_text(encoding="utf-8"))
        if sha256_file(result) != meta["records_sha256"]:
            bad.append(shard)
            continue
        lines = [line for line in result.read_text(encoding="utf-8").splitlines() if line.strip()]
        records.extend(lines)
        key = f"{meta.get('slurm_job_id')}@{meta.get('partition')}"
        workers[key] = workers.get(key, 0) + 1
    if bad:
        print(f"Refusing: shards whose records do not match their done marker: {bad}", file=sys.stderr)
        return 3
    if missing and not args.allow_partial:
        print(f"Refusing: {len(missing)} shards not done ({missing[:5]}...); use --allow-partial to collect what exists",
              file=sys.stderr)
        return 4
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = out_dir / "raw_records.jsonl"
    raw.write_text("".join(line + "\n" for line in records), encoding="utf-8")
    parsed = [json.loads(line) for line in records]

    def count(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in parsed:
            out[str(r.get(key))] = out.get(str(r.get(key)), 0) + 1
        return out

    summary = {"run_id": args.run_id, "spec_sha256": sha256_file(run_dir / "spec.json"),
               "n_records": len(parsed), "n_pairs_planned": spec["n_pairs"], "n_shards_missing": len(missing),
               "shards_missing": missing, "records_sha256": sha256_file(raw), "completion_status": count("completion_status"),
               "grade_declared": count("grade_declared"), "grade_convertible": count("grade_convertible"),
               "grade_rel1pct": count("grade_rel1pct"), "o2_semantic_correct": count("o2_semantic_correct"),
               "tokens_total": sum(int(r["n_generated_tokens"]) for r in parsed), "workers": workers,
               "data_role": spec["data_role"], "note": "raw records only; NOT_EVALUATED statuses are outcomes, never wrong"}
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_records", "n_pairs_planned", "n_shards_missing", "completion_status",
                                               "grade_declared")}, indent=2))
    return 0 if not missing else 1


def cmd_status(args: argparse.Namespace) -> int:
    spec, _ = load_spec(args.run_id, args.runs_dir)
    queue = WorkQueue(queue_root(args.run_id, args.queue_root), list(spec["shards"]))
    print(json.dumps({"run_id": args.run_id, **queue.status()}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--run-id", required=True)
    p.add_argument("--runs-dir", default=RUNS_DIR)
    p.add_argument("--purpose", required=True)
    p.add_argument("--data-role", default="EXPLORATION")
    p.add_argument("--phase-id", default="stage15")
    p.add_argument("--dataset-dir", default="data/v2/dataset/v1")
    p.add_argument("--cells", default=None, help="a JSONL of runner-format job rows (role-by-value cells) instead of the "
                                                  "dataset's no-cue problems")
    p.add_argument("--ids-file", default=None)
    p.add_argument("--max-jobs", type=int, default=None)
    p.add_argument("--model-key", required=True)
    p.add_argument("--model-path", default=None, help="override the registry path (tests only)")
    p.add_argument("--manifest", default=None, help="override the manifest path (tests only)")
    p.add_argument("--backend", choices=["hf", "vllm"], required=True)
    p.add_argument("--env", required=True, help="conda environment the job runs in (physmon or physmon-vllm)")
    p.add_argument("--thinking", choices=["on", "off", "none"], default="none")
    p.add_argument("--n-samples", type=int, required=True)
    p.add_argument("--greedy", action="store_true", help="greedy decoding (backend parity runs only)")
    p.add_argument("--sample-offset", type=int, default=0)
    p.add_argument("--seed", type=int, default=20261112)
    p.add_argument("--max-new-tokens", type=int, required=True)
    p.add_argument("--max-model-len", type=int, default=16384)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--no-state-unit", action="store_true")
    p.add_argument("--shard-size", type=int, default=64)
    p.add_argument("--est-shard-s", type=float, default=1800.0)
    w = sub.add_parser("work")
    w.add_argument("--run-id", required=True)
    w.add_argument("--runs-dir", default=RUNS_DIR)
    w.add_argument("--authorization-ref", required=True)
    w.add_argument("--expect-spec-sha256", default=None)
    w.add_argument("--queue-root", default=None)
    w.add_argument("--time-budget-s", type=float, default=None)
    w.add_argument("--stale-after-s", type=float, default=900.0)
    w.add_argument("--startup-allowance-s", type=float, default=900.0, help="model hashing and loading before the first shard")
    w.add_argument("--device", default="cuda")
    w.add_argument("--model-path", default=None, help="override the registry path (tests only)")
    w.add_argument("--skip-model-hash", action="store_true", help="tests only")
    w.add_argument("--self-test-only", action="store_true")
    w.add_argument("--check-only", action="store_true",
                   help="versions, spec, shard and model-file hashes only; no model is loaded (login-node pre-flight)")
    c = sub.add_parser("collect")
    c.add_argument("--run-id", required=True)
    c.add_argument("--runs-dir", default=RUNS_DIR)
    c.add_argument("--queue-root", default=None)
    c.add_argument("--allow-partial", action="store_true")
    c.add_argument("--results-dir", default=RESULTS_DIR)
    s = sub.add_parser("status")
    s.add_argument("--run-id", required=True)
    s.add_argument("--runs-dir", default=RUNS_DIR)
    s.add_argument("--queue-root", default=None)
    args = parser.parse_args(argv)
    return {"plan": cmd_plan, "work": cmd_work, "collect": cmd_collect, "status": cmd_status}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
