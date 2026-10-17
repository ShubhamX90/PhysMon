#!/usr/bin/env python3
"""Stage 14.7: run the pilot job manifest on ONE model (requires an explicit authorization reference).

This script is prepared but has not been run on any real checkpoint. It must not be launched unless the user has
authorized the run in the current task: `--authorization-ref` is mandatory and is recorded in every output.

For each job in `job_manifest.jsonl` (built by `s147_pilot_plan.py`) it scores the gold string and, where defined, the
decoy string under the Stage 14.3 scoring contract, generates greedily, parses the generation under the wrapper, and
writes one raw JSONL record with the v2 §9.1 fields. It writes no aggregate effect: raw records first, analysis later.
A failed tokenization, a prompt-hash mismatch, or an unparseable generation is a recorded status, never a zero.

Provenance printed at start: source commit, `git status --short`, host, device, package versions, contract fingerprint,
tokenizer file hashes. A non-empty attempt directory is refused.

Plan reference: protocol sections 2-4 and 7; v2 §9.1 (p.43), §8.4 (p.42).
"""

from __future__ import annotations

import argparse
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

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.governance.v2_contract import RAW_RECORD_FIELDS, missing_record_fields  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402
from physmon.utils.paths import expand_model_path  # noqa: E402

OUT_ROOT = "results/stage14/s147_pilot_run"
REGISTRY = "docs/model_registry.yml"


def git(*args: str) -> str:
    """Run git; an empty string if it fails or cannot be run (gpunode6: not found in job 399511, PermissionError in 399530)."""

    try:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                              check=False).stdout.strip()
    except OSError:  # FileNotFoundError, PermissionError (a PATH entry the job cannot execute), and similar
        return ""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def model_manifest_revision(model_key: str) -> str | None:
    path = REPO_ROOT / "docs/model_manifests" / f"{model_key}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("revision") or data.get("resolved_revision") or data.get("commit")


def score_alternative(logprobs, tokenizer, formatted_prompt: str, text: str | None, wrapper: str) -> dict | None:
    if text is None:
        return None
    pair = vs.tokenize_pair(tokenizer, formatted_prompt, text)
    record = vs.score_pair(logprobs, pair, wrapper, text)
    return {"text": text, "status": record.status, "logprob_raw": record.gold_logprob_raw,
            "logprob_per_token": record.gold_logprob_per_token, "target_ids": record.target_ids,
            "span_start": record.span_start, "span_end": record.span_end}


def make_record(job: dict, ctx: dict, logprobs, model, tokenizer) -> dict[str, Any]:
    started = time.time()
    wrapper = job["wrapper_id"]
    prompt = vs.build_chat_prompt(tokenizer, sc.instruction_for(wrapper), job["user_prompt"])
    status = "OK"
    if sha256_text(prompt) != job["formatted_prompt_sha256"]:
        status = "PROMPT_HASH_MISMATCH"
    gold = score_alternative(logprobs, tokenizer, prompt, job["gold_text"], wrapper) if status == "OK" else None
    decoy = score_alternative(logprobs, tokenizer, prompt, job["decoy_text"], wrapper) if status == "OK" else None
    # The same decoy string scored under the no-cue prompt of the same instantiation: the cue effect on the decoy is the
    # change from that score, not a comparison between two different strings (Stage 14.8, J14.8-003).
    decoy_anchor = None
    anchor_user_prompt = ctx.get("anchor_user_prompts", {}).get((job["structure_id"], job["instance"]))
    if status == "OK" and job["decoy_text"] is not None and anchor_user_prompt is not None:
        anchor_prompt = vs.build_chat_prompt(tokenizer, sc.instruction_for(wrapper), anchor_user_prompt)
        decoy_anchor = score_alternative(logprobs, tokenizer, anchor_prompt, job["decoy_text"], wrapper)
    generated, parsed, correctness = None, vs.ParsedOutput("NOT_EVALUATED"), "NOT_EVALUATED"
    rel_error, strict = None, "NOT_EVALUATED"
    if status == "OK" and gold is not None and gold["status"] == "OK":
        generated = vs.greedy_generate(model, tokenizer, prompt, ctx["max_new_tokens"])
        parsed = vs.parse_wrapped(wrapper, generated)
        correctness = vs.classify_answer(parsed, float(job["gold_value"]), job["gold_unit"])
        rel_error = vs.relative_error(parsed, float(job["gold_value"]))
        strict = vs.classify_answer(parsed, float(job["gold_value"]), job["gold_unit"], rel_tol=vs.STRICT_REL_TOL)
    elif status == "OK":
        status = f"GOLD_{gold['status']}" if gold else "NOT_EVALUATED"
    record: dict[str, Any] = {
        "run_id": ctx["run_id"], "phase_id": "stage14_pilot", "exploratory_or_confirmatory": "exploratory",
        "structure_uuid": job["structure_uuid"], "template_cluster_id": job["template_cluster_id"],
        "symbolic_program_hash": job["symbolic_program_hash"], "cue_type": job["cue_semantic_role"],
        "cue_semantic_role": job["cue_semantic_role"], "cue_numeric_value": job["cue_numeric_value"],
        "unit_type": job["unit_type"], "numeric_proximity": job["numeric_proximity"],
        "digit_overlap": job["digit_overlap"], "cue_position": job["cue_position"],
        "isolation_condition": job["isolation_condition"], "model_id": ctx["model_name"],
        "model_commit": ctx["model_revision"], "tokenizer_commit": ctx["tokenizer_sha256"],
        "chat_template": sha256_text(str(getattr(tokenizer, "chat_template", "") or "")),
        "answer_wrapper_id": wrapper, "target_answer_ids": gold["target_ids"] if gold else None,
        "target_span_start": gold["span_start"] if gold else None,
        "target_span_end": gold["span_end"] if gold else None,
        "generated_answer_raw": generated,
        "parsed_answer": {"value": parsed.value, "unit": parsed.unit} if parsed.status == "PARSED" else None,
        "parse_status": parsed.status,
        "gold_logprob_raw": gold["logprob_raw"] if gold else None,
        "gold_logprob_per_token": gold["logprob_per_token"] if gold else None,
        "alternative_scores": ({"decoy": decoy, "decoy_under_anchor_prompt": decoy_anchor} if decoy else None),
        "correctness": correctness, "correctness_rule": vs.CORRECTNESS_RULE,
        "relative_error": rel_error, "correctness_strict_1e-3": strict, "seed": ctx["seed"], "dtype": ctx["dtype"],
        "wall_time": round(time.time() - started, 4), "artifact_checksum": None,
        "job_id": job["job_id"], "structure_id": job["structure_id"], "instance": job["instance"],
        "cell_id": job["cell_id"], "expected_effect": job["expected_effect"], "status": status,
        "contract_fingerprint": sc.contract_fingerprint(), "source_commit": ctx["source_commit"],
        "authorization_ref": ctx["authorization_ref"], "gold_text": job["gold_text"],
        "gold_value": job["gold_value"], "gold_unit": job["gold_unit"],
    }
    missing = missing_record_fields(record)
    if missing:
        raise RuntimeError(f"record violates the v2 data contract; missing {missing}")
    record["artifact_checksum"] = sha256_text(json.dumps(record, sort_keys=True, default=str))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--model-key", required=True, choices=["qwen_primary", "llama_primary"])
    parser.add_argument("--authorization-ref", default="", help="Mandatory: cite the user's authorization record.")
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", default=None, help="float32, float16 or bfloat16 (default: bfloat16 on cuda).")
    parser.add_argument("--model-path", default=None, help="Override the registry path (tests only).")
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.authorization_ref.strip():
        print("Refusing to run: --authorization-ref is required (the pilot has not been authorized by default).",
              file=sys.stderr)
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

    sha = git("rev-parse", "HEAD")
    git_available = bool(sha)
    if not sha:  # no git on the node: take the commit the submitter recorded, and say so in the header
        sha = os.environ.get("PHYSMON_SOURCE_COMMIT", "")
    if not sha:
        print("Refusing to run: no git on this node and PHYSMON_SOURCE_COMMIT is not set (no provenance).",
              file=sys.stderr)
        return 8
    day = git("log", "-1", "--format=%cd", "--date=format:%Y%m%d") or time.strftime("%Y%m%d")
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

    jobs = [json.loads(line) for line in (plan_dir / "job_manifest.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    jobs = [j for j in jobs if j["model_key"] == args.model_key]
    anchor_user_prompts = {(j["structure_id"], j["instance"]): j["user_prompt"] for j in jobs if j["cell_id"] == "no_cue"}
    jobs = jobs[: args.max_jobs]
    ctx = {
        "run_id": f"{attempt}", "model_name": registry["name"], "model_revision": model_manifest_revision(args.model_key),
        "tokenizer_sha256": sha256_file(path / "tokenizer.json"), "dtype": dtype_name, "seed": args.seed,
        "source_commit": sha, "authorization_ref": args.authorization_ref, "max_new_tokens": args.max_new_tokens,
        "anchor_user_prompts": anchor_user_prompts,
    }
    header = {
        "source_commit": sha, "source_commit_from": "git" if git_available else "PHYSMON_SOURCE_COMMIT (git unavailable)",
        "git_status_short": git("status", "--short").splitlines() if git_available else "NOT AVAILABLE",
        "host": socket.gethostname(),
        "device": args.device, "python": platform.python_version(), "torch": torch.__version__,
        "transformers": transformers.__version__, "contract_fingerprint": sc.contract_fingerprint(),
        "model_key": args.model_key, "model_path": str(path), "n_jobs": len(jobs),
        "authorization_ref": args.authorization_ref,
    }
    print(json.dumps(header, indent=2))
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "raw_records.jsonl"
    counts: dict[str, int] = {}
    correctness: dict[str, int] = {}
    started = time.time()
    with records_path.open("w", encoding="utf-8") as handle:
        for job in jobs:
            record = make_record(job, ctx, logprobs, model, tokenizer)
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n")
            handle.flush()
            counts[record["status"]] = counts.get(record["status"], 0) + 1
            correctness[record["correctness"]] = correctness.get(record["correctness"], 0) + 1
    summary = {
        **header, "n_records": sum(counts.values()), "status_counts": counts, "correctness_counts": correctness,
        "total_wall_time_s": round(time.time() - started, 2), "dtype": dtype_name, "seed": args.seed,
        "note": "raw records only; no effect is aggregated here and no cell is promoted to a result",
        "evidence_class": "exploratory; not paper-eligible", "records_sha256": sha256_file(records_path),
        "plan_sha256": sha256_file(plan_dir / "plan.json"),
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_records", "status_counts", "correctness_counts")}, indent=2))
    if jobs:
        assert set(RAW_RECORD_FIELDS) <= set(json.loads(records_path.read_text(encoding="utf-8").splitlines()[0]))
    return 0 if sum(counts.values()) == len(jobs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
