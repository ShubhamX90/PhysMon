#!/usr/bin/env python3
"""Stage 14.20: run the gold dataset on ONE thinking model, batched, with sampling and repeated samples (requires an authorization reference).

Jobs come from the Stage 14.19 dataset: `--source base` takes the no-cue problem of every sample of `dataset.jsonl`; `--source cells`
takes the distractor cells of `factor_cell_manifest.jsonl` (optionally limited by `--cells` and by `--ids-file`, a JSON list of
"structure:instance" keys, for example the base-correct anchors of a first run). Each job is sampled `--n-samples` times, so a
problem a model solves in every sample can be told from one it solves by luck.

The model is prompted as its vendor recommends for thinking (no system message; the final-line instruction is part of the user turn),
generates with sampling (`--temperature`, `--top-p`, `--top-k`; greedy decoding is known to loop on thinking models) and a large
token budget. The text after the last `</think>` is the answer; the final line is parsed with the Stage 14.13 contract and graded with
the declared correctness rule (protocol section 4b). A generation that never closes its thinking, or that hits the token limit
without a final line, is TRUNCATED, an outcome of its own, never wrong and never zero. Only generation is graded: log-probability
fields are null (NOT_EVALUATED). Raw records are written after every batch, so a stopped job leaves valid partial evidence;
`--time-budget-s` stops the loop cleanly and counts the jobs not run. Sampling is not bit-reproducible across batch compositions: the
seed, the batch size and the sampling parameters are recorded.

Provenance, the empty-attempt-directory rule, the authorization reference and the no-git fallback follow `s147_pilot_run.py`.

Plan reference: B2.4 eligibility strata, protocol sections 3 and 4b; journals J14.13 and J14.19.
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

from physmon.benchmark import reasoning_contract as rc  # noqa: E402
from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.governance.v2_contract import missing_record_fields  # noqa: E402
from physmon.scoring import unit_convertible as uc  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402
from physmon.utils.paths import expand_model_path  # noqa: E402

OUT_ROOT = "results/stage14/s164_thinking_run"
REGISTRY = "docs/model_registry.yml"
DATASET_DIR = "data/v2/dataset/v1"
THINK_CLOSE = "</think>"
CONTRACT = "thinking-v1"


def _load_pilot_runner():
    spec = importlib.util.spec_from_file_location("s147_pilot_run", REPO_ROOT / "scripts/v2/s147_pilot_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_pilot_runner()


def display_unit(unit: str) -> str:
    return unit.replace("^2", "\u00b2").replace("^3", "\u00b3")


def user_turn(problem: str, unit: str | None = None) -> str:
    """The instruction and the problem in one user message (thinking models are prompted without a system message).

    With `unit`, the requested answer unit is stated, as it was to the blind solvers that verified the dataset (Stage 14.19); the Stage 14.20
    speed test, which did not state it, had four correct answers graded wrong only for a different unit or spelling.
    """

    stated = f"\n\nGive the final answer in {display_unit(unit)}." if unit else ""
    return f"{rc.INSTRUCTION}\n\n{problem}{stated}"


def split_thinking(text: str) -> tuple[str, str, bool]:
    """(thinking, answer, closed): the text before the last `</think>`, the text after it, and whether the thinking was closed."""

    if THINK_CLOSE not in text:
        return text, "", False
    head, _, tail = text.rpartition(THINK_CLOSE)
    return head, tail, True


def parse_thinking_output(text: str, hit_limit: bool) -> tuple[rc.ReasoningParse, str, str, bool]:
    """(parse of the answer part, thinking, answer, thinking closed).

    Thinking that never closes and hit the token limit is TRUNCATED: the model never reached an answer, and a final-line phrase inside its
    thinking is not an answer. Text without any thinking tag that stopped by itself is parsed as a whole (a model that answered directly).
    """

    thinking, answer, closed = split_thinking(text)
    if closed:
        return rc.parse_final(answer, hit_token_limit=hit_limit), thinking, answer, True
    if hit_limit:
        empty = not text.strip()
        return rc.ReasoningParse(rc.ParsedOutput("EMPTY" if empty else "TRUNCATED"), 0), thinking, answer, False
    return rc.parse_final(text, hit_token_limit=False), thinking, answer, False


def jobs_from_dataset(rows: list[dict], keep: set[str] | None = None) -> list[dict[str, Any]]:
    jobs = []
    for r in rows:
        if keep is not None and f"{r['structure_id']}:{r['instance']}" not in keep:
            continue
        jobs.append({"job_id": f"{r['sample_id']}:no_cue", "structure_id": r["structure_id"], "instance": r["instance"], "cell_id": "no_cue",
                     "structure_uuid": r["structure_uuid"], "template_cluster_id": r["template_cluster_id"],
                     "symbolic_program_hash": r["symbolic_program_hash"], "prompt": r["problem"], "gold_value": r["gold_answer"]["value"],
                     "gold_unit": r["answer_unit"], "cue_semantic_role": None, "cue_numeric_value": None, "unit_type": None,
                     "numeric_proximity": None, "digit_overlap": None, "cue_position": None, "isolation_condition": None,
                     "expected_effect": None})
    return jobs


def jobs_from_manifest(rows: list[dict], cells: list[str] | None, keep: set[str] | None) -> list[dict[str, Any]]:
    jobs = []
    for r in rows:
        if not r["feasible"] or (cells and r["cell_id"] not in cells):
            continue
        if keep is not None and f"{r['structure_id']}:{r['instance']}" not in keep:
            continue
        jobs.append({"job_id": f"{r['structure_id']}-i{r['instance']}:{r['cell_id']}", "structure_id": r["structure_id"],
                     "instance": r["instance"], "cell_id": r["cell_id"], "structure_uuid": r["structure_uuid"],
                     "template_cluster_id": r["template_cluster_id"], "symbolic_program_hash": r["symbolic_program_hash"],
                     "prompt": r["prompt"], "gold_value": r["gold_value"], "gold_unit": r["gold_unit"],
                     "cue_semantic_role": r.get("cue_semantic_role"), "cue_numeric_value": r.get("cue_numeric_value"),
                     "unit_type": r.get("unit_type"), "numeric_proximity": r.get("numeric_proximity"),
                     "digit_overlap": r.get("digit_overlap"), "cue_position": r.get("cue_position"),
                     "isolation_condition": r.get("isolation_condition"), "expected_effect": r.get("expected_effect")})
    return jobs


def eos_ids(model, tokenizer) -> set[int]:
    raw = getattr(model.generation_config, "eos_token_id", None)
    if raw is None:
        raw = tokenizer.eos_token_id
    return set(raw) if isinstance(raw, (list, tuple)) else {int(raw)}


def generate_batch(model, tokenizer, prompts: list[str], max_new_tokens: int, sampling: dict[str, Any], seed: int) -> list[tuple[str, int, bool]]:
    """Left-padded batched generation; (text, new tokens, hit the limit) per prompt. The text is cut at the first end-of-sequence token."""

    import torch

    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:  # Llama-3 tokenizers have no padding token
        tokenizer.pad_token = tokenizer.eos_token
    pad = tokenizer.pad_token_id
    encoded = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
    torch.manual_seed(seed)
    kwargs: dict[str, Any] = {"max_new_tokens": max_new_tokens, "pad_token_id": pad}
    if sampling["do_sample"]:
        kwargs.update(do_sample=True, temperature=sampling["temperature"], top_p=sampling["top_p"])
        if sampling.get("top_k"):
            kwargs["top_k"] = sampling["top_k"]
    else:
        kwargs.update(do_sample=False, temperature=None, top_p=None, top_k=None)
    with torch.no_grad():
        out = model.generate(**encoded, **kwargs)
    stops = eos_ids(model, tokenizer)
    width = encoded["input_ids"].shape[1]
    results = []
    for i in range(len(prompts)):
        generated = out[i, width:].tolist()
        cut = next((j for j, t in enumerate(generated) if t in stops), None)
        hit_limit = cut is None
        used = generated if cut is None else generated[:cut]
        results.append((tokenizer.decode(used, skip_special_tokens=False), len(used) + (0 if cut is None else 1), hit_limit))
    return results


def generate_with_fallback(model, tokenizer, prompts: list[str], max_new_tokens: int, sampling: dict[str, Any], seed: int) -> tuple[list[tuple[str, int, bool]], bool]:
    """Batched generation; on a CUDA out-of-memory error the batch is redone one sequence at a time (and flagged), never skipped."""

    import torch

    try:
        return generate_batch(model, tokenizer, prompts, max_new_tokens, sampling, seed), False
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        singles = [generate_batch(model, tokenizer, [prompt], max_new_tokens, sampling, seed + i + 1)[0] for i, prompt in enumerate(prompts)]
        return singles, True


def make_record(job: dict, sample_index: int, text: str, n_new: int, hit_limit: bool, ctx: dict, tokenizer, wall: float,
                oom_fallback: bool = False) -> dict[str, Any]:
    result, thinking, answer, closed = parse_thinking_output(text, hit_limit)
    parsed = result.parsed
    gold_value = float(job["gold_value"])
    correctness = vs.classify_answer(parsed, gold_value, job["gold_unit"])
    cue = job.get("cue_numeric_value")
    copied = parsed.status == "PARSED" and cue is not None and abs(parsed.value - float(cue)) < 1e-9
    record: dict[str, Any] = {
        "run_id": ctx["run_id"], "phase_id": "stage14_thinking", "exploratory_or_confirmatory": "exploratory",
        "structure_uuid": job["structure_uuid"], "template_cluster_id": job["template_cluster_id"],
        "symbolic_program_hash": job["symbolic_program_hash"], "cue_type": job["cue_semantic_role"],
        "cue_semantic_role": job["cue_semantic_role"], "cue_numeric_value": cue, "unit_type": job["unit_type"],
        "numeric_proximity": job["numeric_proximity"], "digit_overlap": job["digit_overlap"], "cue_position": job["cue_position"],
        "isolation_condition": job["isolation_condition"], "model_id": ctx["model_name"], "model_commit": ctx["model_revision"],
        "tokenizer_commit": ctx["tokenizer_sha256"],
        "chat_template": base.sha256_text(str(getattr(tokenizer, "chat_template", "") or "")),
        "answer_wrapper_id": f"{CONTRACT}:{rc.CONTRACT_VERSION}", "target_answer_ids": None, "target_span_start": None,
        "target_span_end": None, "generated_answer_raw": text,
        "parsed_answer": {"value": parsed.value, "unit": parsed.unit} if parsed.status == "PARSED" else None,
        "parse_status": parsed.status, "gold_logprob_raw": None, "gold_logprob_per_token": None, "alternative_scores": None,
        "correctness": correctness, "correctness_rule": vs.CORRECTNESS_RULE, "relative_error": vs.relative_error(parsed, gold_value),
        "correct_if_units_convertible": uc.classify_convertible(parsed, gold_value, job["gold_unit"]),
        "unit_stated_in_prompt": ctx["state_unit"], "oom_fallback": oom_fallback,
        "correctness_strict_1e-3": vs.classify_answer(parsed, gold_value, job["gold_unit"], rel_tol=vs.STRICT_REL_TOL),
        "copied_cue_numeral": bool(copied) if cue is not None and parsed.status == "PARSED" else None,
        "n_final_lines": result.n_final_lines, "n_generated_tokens": n_new, "hit_token_limit": hit_limit,
        "thinking_closed": closed, "n_thinking_chars": len(thinking), "n_answer_chars": len(answer), "sample_index": sample_index,
        "sampling": ctx["sampling"], "batch_size": ctx["batch_size"], "seed": ctx["seed"], "dtype": ctx["dtype"],
        "wall_time": round(wall, 4), "artifact_checksum": None, "job_id": f"{job['job_id']}:thinking:s{sample_index}",
        "structure_id": job["structure_id"], "instance": job["instance"], "cell_id": job["cell_id"],
        "expected_effect": job["expected_effect"], "status": "OK", "contract_fingerprint": sc.contract_fingerprint(),
        "reasoning_contract_fingerprint": rc.contract_fingerprint(), "source_commit": ctx["source_commit"],
        "authorization_ref": ctx["authorization_ref"], "gold_value": gold_value, "gold_unit": job["gold_unit"],
    }
    missing = missing_record_fields(record)
    if missing:
        raise RuntimeError(f"record violates the v2 data contract; missing {missing}")
    record["artifact_checksum"] = base.sha256_text(json.dumps(record, sort_keys=True, default=str))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", default=DATASET_DIR)
    parser.add_argument("--source", choices=["base", "cells"], default="base")
    parser.add_argument("--cells", nargs="*", default=None, help="cell ids to run when --source cells")
    parser.add_argument("--ids-file", default=None, help="JSON list of 'structure:instance' keys to keep")
    parser.add_argument("--model-key", required=True, help="a key of docs/model_registry.yml")
    parser.add_argument("--authorization-ref", default="", help="Mandatory: cite the user's authorization record.")
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", default=None)
    parser.add_argument("--model-path", default=None, help="Override the registry path (tests only).")
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=12288)
    parser.add_argument("--n-samples", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=0, help="0 = off (the DeepSeek-R1 recommendation); Qwen3 recommends 20")
    parser.add_argument("--greedy", action="store_true")
    parser.add_argument("--no-state-unit", dest="state_unit", action="store_false", help="do not state the requested answer unit in the prompt (the speed-test variant)")
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
    dataset_dir = REPO_ROOT / args.dataset_dir
    keep = set(json.loads(Path(args.ids_file).read_text(encoding="utf-8"))) if args.ids_file else None
    if args.source == "base":
        rows = [json.loads(line) for line in (dataset_dir / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        jobs = jobs_from_dataset(rows, keep)
    else:
        rows = [json.loads(line) for line in (dataset_dir / "factor_cell_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        jobs = jobs_from_manifest(rows, args.cells, keep)
    jobs = jobs[: args.max_jobs]
    sha = base.git("rev-parse", "HEAD")
    git_available = bool(sha)
    if not sha:
        sha = os.environ.get("PHYSMON_SOURCE_COMMIT", "")
    if not sha:
        print("Refusing to run: no git on this node and PHYSMON_SOURCE_COMMIT is not set (no provenance).", file=sys.stderr)
        return 8
    day = base.git("log", "-1", "--format=%cd", "--date=format:%Y%m%d") or time.strftime("%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}_{args.model_key}_{args.source}"
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
    sampling = {"do_sample": not args.greedy, "temperature": args.temperature, "top_p": args.top_p, "top_k": args.top_k}
    revision = base.model_manifest_revision(args.model_key)
    ctx = {"run_id": attempt, "model_name": registry["name"], "model_revision": revision or "NOT_RECORDED",
           "tokenizer_sha256": base.sha256_file(path / "tokenizer.json"), "dtype": dtype_name, "seed": args.seed, "source_commit": sha,
           "authorization_ref": args.authorization_ref, "sampling": sampling, "batch_size": args.batch_size, "state_unit": args.state_unit}
    header = {"source_commit": sha, "source_commit_from": "git" if git_available else "PHYSMON_SOURCE_COMMIT (git unavailable)",
              "git_status_short": base.git("status", "--short").splitlines() if git_available else "NOT AVAILABLE",
              "host": socket.gethostname(), "device": args.device, "python": platform.python_version(), "torch": torch.__version__,
              "transformers": transformers.__version__, "contract_fingerprint": sc.contract_fingerprint(),
              "reasoning_contract_fingerprint": rc.contract_fingerprint(), "model_key": args.model_key, "model_path": str(path),
              "source": args.source, "n_jobs_planned": len(jobs), "n_samples": args.n_samples, "max_new_tokens": args.max_new_tokens,
              "sampling": sampling, "batch_size": args.batch_size, "state_unit": args.state_unit, "time_budget_s": args.time_budget_s,
              "authorization_ref": args.authorization_ref, "model_revision": ctx["model_revision"]}
    print(json.dumps(header, indent=2), flush=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # One (job, sample) pair per sequence; sequences ordered by prompt length so a batch pads little.
    prompts = {j["job_id"]: tokenizer.apply_chat_template([{"role": "user", "content": user_turn(j["prompt"], j["gold_unit"] if args.state_unit else None)}],
                                                          tokenize=False, add_generation_prompt=True, enable_thinking=True) for j in jobs}
    pairs = sorted(((j, k) for j in jobs for k in range(args.n_samples)), key=lambda p: (len(prompts[p[0]["job_id"]]), p[0]["job_id"], p[1]))
    counts: dict[str, int] = {}
    correctness: dict[str, int] = {}
    started = time.time()
    n_run = 0
    with (out_dir / "raw_records.jsonl").open("w", encoding="utf-8") as handle:
        for start in range(0, len(pairs), args.batch_size):
            if args.time_budget_s is not None and time.time() - started > args.time_budget_s:
                break
            batch = pairs[start: start + args.batch_size]
            t0 = time.time()
            outputs, fell_back = generate_with_fallback(model, tokenizer, [prompts[j["job_id"]] for j, _ in batch], args.max_new_tokens, sampling,
                                                        args.seed * 1_000_003 + start)
            wall = (time.time() - t0) / len(batch)
            print(json.dumps({"batch_start": start, "n_pairs": len(pairs), "tokens": sum(o[1] for o in outputs), "wall_s": round(wall * len(batch), 1),
                              "oom_fallback": fell_back}), flush=True)
            for (job, k), (text, n_new, hit) in zip(batch, outputs, strict=True):
                record = make_record(job, k, text, n_new, hit, ctx, tokenizer, wall, fell_back)
                handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n")
                n_run += 1
                counts[record["parse_status"]] = counts.get(record["parse_status"], 0) + 1
                correctness[record["correctness"]] = correctness.get(record["correctness"], 0) + 1
            handle.flush()
    summary = {**header, "n_records": n_run, "n_records_planned": len(pairs), "n_records_not_run": len(pairs) - n_run,
               "parse_status_counts": counts, "correctness_counts": correctness, "total_wall_time_s": round(time.time() - started, 2),
               "dtype": dtype_name, "seed": args.seed, "note": "raw records only; no effect is aggregated here",
               "evidence_class": "exploratory; not paper-eligible", "data_role": "EXPLORATION",
               "records_sha256": base.sha256_file(out_dir / "raw_records.jsonl")}
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_records", "n_records_not_run", "parse_status_counts", "correctness_counts")}, indent=2))
    return 0 if n_run == len(pairs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
