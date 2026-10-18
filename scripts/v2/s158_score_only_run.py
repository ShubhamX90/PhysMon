#!/usr/bin/env python3
"""Stage 14.14 and 14.16: score the candidate strings of a plan on ONE model, without generation (requires an authorization reference).

For plans whose jobs are candidate strings to score under a prompt (`s154_numeral_presence_plan.py`, `s156_legacy_x03_plan.py`):
each job's `gold_text` is the candidate (the real answer is `true_gold_value`), scored under the job's prompt and wrapper with the
Stage 14.3 contract and the Stage 14.7 scorer. There is no generation, so `parsed_answer`, `parse_status` and `correctness` are
NOT_EVALUATED, never wrong and never zero. Raw records are written one line at a time and flushed; `--time-budget-s` stops the loop
cleanly and the summary counts the jobs not run. Log-probabilities are rounded to 4 decimals in the per-token list to keep the files
small; the raw sum is not rounded.

Provenance, the empty-attempt-directory rule, the authorization reference and the no-git fallback follow `s147_pilot_run.py`.

Plan reference: protocol section 5 row 4; card X03; journals J14.14-001 and J14.16-001.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import socket
import sys
import time
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.governance.v2_contract import missing_record_fields  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402
from physmon.utils.paths import expand_model_path  # noqa: E402

OUT_ROOT = "results/stage14/s158_score_only_run"
REGISTRY = "docs/model_registry.yml"
PASS_THROUGH = ("candidate_kind", "candidate_text", "candidate_matched_to", "candidate_role", "candidate_source_variant",
                "candidate_in_own_prompt", "candidate_numeral_in_prompt", "prompt_variant", "true_gold_value")


def _load_pilot_runner():
    spec = importlib.util.spec_from_file_location("s147_pilot_run", REPO_ROOT / "scripts/v2/s147_pilot_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_pilot_runner()


def make_record(job: dict, ctx: dict, logprobs, tokenizer) -> dict[str, Any]:
    started = time.time()
    wrapper = job["wrapper_id"]
    prompt = vs.build_chat_prompt(tokenizer, sc.instruction_for(wrapper), job["user_prompt"])
    status = "OK"
    scored = None
    if base.sha256_text(prompt) != job["formatted_prompt_sha256"]:
        status = "PROMPT_HASH_MISMATCH"
    else:
        scored = base.score_alternative(logprobs, tokenizer, prompt, job["gold_text"], wrapper)
        if scored["status"] != "OK":
            status = f"CANDIDATE_{scored['status']}"
    ok = scored is not None and status == "OK"
    record: dict[str, Any] = {
        "run_id": ctx["run_id"], "phase_id": "stage14_score_only", "exploratory_or_confirmatory": "exploratory",
        "structure_uuid": job["structure_uuid"], "template_cluster_id": job["template_cluster_id"],
        "symbolic_program_hash": job["symbolic_program_hash"], "cue_type": job["cue_semantic_role"],
        "cue_semantic_role": job["cue_semantic_role"], "cue_numeric_value": job["cue_numeric_value"], "unit_type": job["unit_type"],
        "numeric_proximity": job["numeric_proximity"], "digit_overlap": job["digit_overlap"], "cue_position": job["cue_position"],
        "isolation_condition": job["isolation_condition"], "model_id": ctx["model_name"], "model_commit": ctx["model_revision"],
        "tokenizer_commit": ctx["tokenizer_sha256"],
        "chat_template": base.sha256_text(str(getattr(tokenizer, "chat_template", "") or "")),
        "answer_wrapper_id": wrapper, "target_answer_ids": scored["target_ids"] if ok else None,
        "target_span_start": scored["span_start"] if ok else None, "target_span_end": scored["span_end"] if ok else None,
        "generated_answer_raw": None, "parsed_answer": None, "parse_status": "NOT_EVALUATED",
        "gold_logprob_raw": scored["logprob_raw"] if ok else None,
        "gold_logprob_per_token": [round(x, 4) for x in scored["logprob_per_token"]] if ok else None,
        "alternative_scores": None, "correctness": "NOT_EVALUATED", "seed": ctx["seed"], "dtype": ctx["dtype"],
        "wall_time": round(time.time() - started, 4), "artifact_checksum": None, "job_id": job["job_id"],
        "structure_id": job["structure_id"], "instance": job["instance"], "cell_id": job["cell_id"],
        "expected_effect": job["expected_effect"], "status": status, "contract_fingerprint": sc.contract_fingerprint(),
        "source_commit": ctx["source_commit"], "authorization_ref": ctx["authorization_ref"], "gold_text": job["gold_text"],
        "gold_value": job["gold_value"], "gold_unit": job["gold_unit"],
        **{k: job.get(k) for k in PASS_THROUGH},
    }
    missing = missing_record_fields(record)
    if missing:
        raise RuntimeError(f"record violates the v2 data contract; missing {missing}")
    record["artifact_checksum"] = base.sha256_text(json.dumps(record, sort_keys=True, default=str))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--model-key", required=True, choices=["qwen_primary", "llama_primary"])
    parser.add_argument("--authorization-ref", default="", help="Mandatory: cite the user's authorization record.")
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", default=None)
    parser.add_argument("--model-path", default=None, help="Override the registry path (tests only).")
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--time-budget-s", type=float, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.authorization_ref.strip():
        print("Refusing to run: --authorization-ref is required (the run has not been authorized by default).", file=sys.stderr)
        return 4
    import torch
    import transformers

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        print("Refusing to run: a CUDA device was requested but none is available.", file=sys.stderr)
        return 3
    plan_dir = Path(args.plan_dir)
    plan = json.loads((plan_dir / "plan.json").read_text(encoding="utf-8"))
    if plan["contract_fingerprint"] != sc.contract_fingerprint():
        print("Refusing to run: the plan was built under a different scoring contract.", file=sys.stderr)
        return 5
    sha = base.git("rev-parse", "HEAD")
    git_available = bool(sha)
    if not sha:
        sha = os.environ.get("PHYSMON_SOURCE_COMMIT", "")
    if not sha:
        print("Refusing to run: no git on this node and PHYSMON_SOURCE_COMMIT is not set (no provenance).", file=sys.stderr)
        return 8
    day = base.git("log", "-1", "--format=%cd", "--date=format:%Y%m%d") or time.strftime("%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}_{args.model_key}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    registry = yaml.safe_load((REPO_ROOT / REGISTRY).read_text(encoding="utf-8"))["models"][args.model_key]
    path = Path(args.model_path or expand_model_path(registry["path"]))
    dtype_name = args.dtype or ("bfloat16" if args.device.startswith("cuda") else "float32")
    torch.manual_seed(args.seed)
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=False)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        str(path), local_files_only=True, trust_remote_code=False, dtype=getattr(torch, dtype_name))
    model.to(args.device)
    model.eval()
    logprobs = vs.make_hf_logprob_fn(model, args.device)

    jobs = [json.loads(line) for line in (plan_dir / "job_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    jobs = [j for j in jobs if j["model_key"] == args.model_key][: args.max_jobs]
    ctx = {"run_id": attempt, "model_name": registry["name"], "model_revision": base.model_manifest_revision(args.model_key),
           "tokenizer_sha256": base.sha256_file(path / "tokenizer.json"), "dtype": dtype_name, "seed": args.seed,
           "source_commit": sha, "authorization_ref": args.authorization_ref}
    header = {"source_commit": sha, "source_commit_from": "git" if git_available else "PHYSMON_SOURCE_COMMIT (git unavailable)",
              "git_status_short": base.git("status", "--short").splitlines() if git_available else "NOT AVAILABLE",
              "host": socket.gethostname(), "device": args.device, "python": platform.python_version(), "torch": torch.__version__,
              "transformers": transformers.__version__, "contract_fingerprint": sc.contract_fingerprint(), "plan_stage": plan.get("stage"),
              "model_key": args.model_key, "model_path": str(path), "n_jobs_planned": len(jobs), "time_budget_s": args.time_budget_s,
              "authorization_ref": args.authorization_ref}
    print(json.dumps(header, indent=2), flush=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    started = time.time()
    n_run = 0
    with (out_dir / "raw_records.jsonl").open("w", encoding="utf-8") as handle:
        for job in jobs:
            if args.time_budget_s is not None and time.time() - started > args.time_budget_s:
                break
            record = make_record(job, ctx, logprobs, tokenizer)
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n")
            handle.flush()
            n_run += 1
            counts[record["status"]] = counts.get(record["status"], 0) + 1
    summary = {**header, "n_records": n_run, "n_jobs_not_run": len(jobs) - n_run, "status_counts": counts,
               "total_wall_time_s": round(time.time() - started, 2), "dtype": dtype_name, "seed": args.seed,
               "note": "score-only: no generation, no effect aggregated, no cell promoted to a result",
               "evidence_class": "exploratory; not paper-eligible", "data_role": "EXPLORATION",
               "records_sha256": base.sha256_file(out_dir / "raw_records.jsonl"), "plan_sha256": base.sha256_file(plan_dir / "plan.json")}
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_records", "n_jobs_not_run", "status_counts")}, indent=2))
    return 0 if n_run == len(jobs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
