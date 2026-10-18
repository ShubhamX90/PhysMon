#!/usr/bin/env python3
"""Stage 14.7: plan the two-model pilot (dry run; tokenizers only; NOT authorized to run).

Builds the exact job manifest for the pilot in `docs/stage14/pilot_protocol.md` from the committed factor-cell manifest,
with the real Qwen and Llama tokenizers, and reports the cost that can be computed without a GPU: number of jobs and
forward passes, prompt and target token totals, and which cells have a decoy candidate for answer competition. It does
not load a model, does not use a GPU, does not submit anything, and states `authorized_to_run: false`.

GPU time is deliberately not estimated: no throughput has been measured on the current stack (v2 §9, p.42: "specific
throughput and costs must be measured on Sharanga rather than invented").

Plan reference: B6.1 (p.12), §9 cost model and compute ladder (p.42-43), protocol sections 2 and 6.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402
from physmon.utils.paths import expand_model_path  # noqa: E402

OUT_ROOT = "results/stage14/s147_pilot_plan"
MANIFEST = "data/v2/structures/v1/factor_cell_manifest.jsonl"
PROTOCOL = "docs/stage14/pilot_protocol.md"
REGISTRY = "docs/model_registry.yml"
WRAPPER = "answer_line"
MODELS = ("qwen_primary", "llama_primary")
DECOY_CELLS = ("nongov_same_unit_near_high_overlap", "nongov_same_unit_near_low_overlap",
               "nongov_same_unit_moderate", "nongov_same_unit_far", "nongov_incompatible_unit_near")
MAX_NEW_TOKENS = 40
BLOCKERS = [
    "independent expert review of the ten structures (all UNREVIEWED)",
    "ten structures, not the 40 to 60 that B6.1 asks for",
    "P0 gate open (values recomputed, not regenerated through the model)",
    "post-wipe GPU validation of the two models is incomplete",
    "no explicit user authorization to submit Slurm jobs, and no live preflight of partition and caps",
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tokenizers(model_keys: tuple[str, ...]) -> tuple[dict[str, Any], dict[str, Any]]:
    from transformers import AutoTokenizer

    registry = yaml.safe_load((REPO_ROOT / REGISTRY).read_text(encoding="utf-8"))["models"]
    tokenizers, provenance = {}, {}
    for key in model_keys:
        path = Path(expand_model_path(registry[key]["path"]))
        tokenizers[key] = AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=False)
        provenance[key] = {"model_name": registry[key]["name"], "path": str(path),
                           "tokenizer.json_sha256": sha256_file(path / "tokenizer.json"),
                           "tokenizer_config.json_sha256": sha256_file(path / "tokenizer_config.json")}
    return tokenizers, provenance


def read_manifest(structures: set[str] | None, manifest: str = MANIFEST) -> list[dict]:
    rows = [json.loads(line) for line in (REPO_ROOT / manifest).read_text(encoding="utf-8").splitlines()
            if line.strip()]
    return [r for r in rows if not structures or r["structure_id"] in structures]


def target_texts(row: dict, wrapper: str = WRAPPER) -> tuple[str, str | None]:
    """The gold string and (for numeric-cue cells) the decoy string, both under one wrapper."""

    unit = dg.display_unit(row["gold_unit"])
    gold = sc.render_target(wrapper, dg.positional(row["gold_value"], 4), unit)
    decoy = None
    if row["cell_id"] in DECOY_CELLS and row.get("cue_numeric_value") is not None:
        decoy = sc.render_target(wrapper, dg.positional(row["cue_numeric_value"], 3), unit)
    return gold, decoy


def build_jobs(rows: list[dict], tokenizers: dict[str, Any], model_keys: tuple[str, ...],
               wrappers: tuple[str, ...] = (WRAPPER,)) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for key in model_keys:
        tok = tokenizers[key]
        for wrapper in wrappers:
            system = sc.instruction_for(wrapper)
            for row in rows:
                if not row["feasible"]:
                    continue
                gold, decoy = target_texts(row, wrapper)
                prompt = vs.build_chat_prompt(tok, system, row["prompt"])
                gold_pair = vs.tokenize_pair(tok, prompt, gold)
                decoy_pair = vs.tokenize_pair(tok, prompt, decoy) if decoy else None
                # The answer_line job id has no wrapper suffix, so the committed pilot plan and its records keep their ids.
                suffix = "" if wrapper == WRAPPER else f":{wrapper}"
                jobs.append({
                    "job_id": f"{key}:{row['structure_id']}:{row['instance']}:{row['cell_id']}{suffix}",
                    "model_key": key, "wrapper_id": wrapper, "structure_id": row["structure_id"],
                    "structure_uuid": row["structure_uuid"], "template_cluster_id": row["template_cluster_id"],
                    "symbolic_program_hash": row["symbolic_program_hash"], "instance": row["instance"],
                    "cell_id": row["cell_id"], "expected_effect": row["expected_effect"],
                    "cue_semantic_role": row.get("cue_semantic_role"), "numeric_proximity": row.get("numeric_proximity"),
                    "unit_type": row.get("unit_type"), "digit_overlap": row.get("digit_overlap"),
                    "cue_position": row.get("cue_position"), "isolation_condition": row.get("isolation_condition"),
                    "cue_numeric_value": row.get("cue_numeric_value"), "cue_unit": row.get("cue_unit"),
                    "gold_value": row["gold_value"], "gold_unit": row["gold_unit"],
                    "user_prompt": row["prompt"], "user_prompt_sha256": row["prompt_sha256"],
                    "formatted_prompt_sha256": gold_pair.prompt_sha256,
                    "gold_text": gold, "decoy_text": decoy, "decoy_defined": decoy is not None,
                    "n_prompt_tokens": len(gold_pair.prompt_ids), "n_gold_tokens": len(gold_pair.target_ids),
                    "n_decoy_tokens": len(decoy_pair.target_ids) if decoy_pair else None,
                    "gold_tokenization_status": gold_pair.status,
                    "decoy_tokenization_status": decoy_pair.status if decoy_pair else "NOT_APPLICABLE",
                    "leading_special_tokens": gold_pair.n_leading_special,
                })
    return jobs


def cost_summary(jobs: list[dict[str, Any]], n_cells_total: int, n_cells_feasible: int) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "n_cells_in_manifest": n_cells_total, "n_cells_feasible": n_cells_feasible,
        "n_cells_infeasible_not_run": n_cells_total - n_cells_feasible,
        "max_new_tokens_per_generation": MAX_NEW_TOKENS, "per_model": {},
    }
    for key in sorted({j["model_key"] for j in jobs}):
        mine = [j for j in jobs if j["model_key"] == key]
        decoys = [j for j in mine if j["decoy_defined"]]
        prompt_tokens = [j["n_prompt_tokens"] for j in mine]
        forward_tokens = sum(j["n_prompt_tokens"] + j["n_gold_tokens"] for j in mine) + sum(
            j["n_prompt_tokens"] + j["n_decoy_tokens"] for j in decoys)
        audit = {}
        for wrapper in sorted({j["wrapper_id"] for j in mine}):
            rows_w = [j for j in mine if j["wrapper_id"] == wrapper]
            audit[wrapper] = {
                "n_jobs": len(rows_w),
                "mean_gold_tokens": float(np.mean([j["n_gold_tokens"] for j in rows_w])),
                "duplicate_special_token": sum(j["gold_tokenization_status"] == "DUPLICATE_SPECIAL_TOKEN" for j in rows_w),
                "boundary_mismatch_gold": sum(j["gold_tokenization_status"] == "BOUNDARY_MISMATCH" for j in rows_w),
                "boundary_mismatch_decoy": sum(j["decoy_tokenization_status"] == "BOUNDARY_MISMATCH" for j in rows_w)}
        summary["per_model"][key] = {
            "tokenizer_audit_by_wrapper": audit,
            "n_jobs": len(mine), "n_jobs_with_decoy": len(decoys),
            "n_scoring_forward_passes": len(mine) + len(decoys), "n_generations": len(mine),
            "prompt_tokens_min_mean_max": [int(min(prompt_tokens)), float(np.mean(prompt_tokens)),
                                           int(max(prompt_tokens))],
            "total_tokens_through_scoring_forward_passes": int(forward_tokens),
            "total_prompt_tokens_for_generation_prefill": int(sum(prompt_tokens)),
            "max_generated_tokens": len(mine) * MAX_NEW_TOKENS,
            "tokenization_failures": {
                "duplicate_special_token": sum(j["gold_tokenization_status"] == "DUPLICATE_SPECIAL_TOKEN"
                                               for j in mine),
                "boundary_mismatch_gold": sum(j["gold_tokenization_status"] == "BOUNDARY_MISMATCH" for j in mine),
                "boundary_mismatch_decoy": sum(j["decoy_tokenization_status"] == "BOUNDARY_MISMATCH" for j in mine),
            },
        }
    summary["gpu_time_estimate"] = "NOT ESTIMATED: no throughput has been measured on the current stack"
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--structures", nargs="*", default=None, help="Restrict to these structure ids (tests).")
    parser.add_argument("--manifest", default=MANIFEST,
                        help="Factor-cell manifest (default: S01 to S10; data/v2/structures/v2/ holds S11 to S20).")
    parser.add_argument("--models", nargs="*", default=list(MODELS))
    parser.add_argument("--wrappers", nargs="*", default=[WRAPPER], choices=sorted(sc.WRAPPERS),
                        help="Output wrappers (Stage 14.3 contract); the default reproduces the committed pilot plan.")
    args = parser.parse_args()

    sha = git("rev-parse", "HEAD")
    day = git("log", "-1", "--format=%cd", "--date=format:%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    import transformers

    model_keys = tuple(args.models)
    tokenizers, provenance = load_tokenizers(model_keys)
    rows = read_manifest(set(args.structures) if args.structures else None, args.manifest)
    wrappers = tuple(args.wrappers)
    jobs = build_jobs(rows, tokenizers, model_keys, wrappers)
    summary = cost_summary(jobs, len(rows), sum(1 for r in rows if r["feasible"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "job_manifest.jsonl").write_text(
        "".join(json.dumps(j, sort_keys=True, ensure_ascii=False) + "\n" for j in jobs), encoding="utf-8")
    plan = {
        "stage": "14.7", "kind": "pilot plan (dry run)", "authorized_to_run": False, "blockers": BLOCKERS,
        "source_commit": sha, "git_status_short": git("status", "--short").splitlines(),
        "command": " ".join(sys.argv), "transformers": transformers.__version__,
        "contract_version": sc.CONTRACT_VERSION, "contract_fingerprint": sc.contract_fingerprint(),
        "wrapper_id": wrappers[0] if len(wrappers) == 1 else "multiple", "wrapper_ids": list(wrappers),
        "instructions": {w: sc.instruction_for(w) for w in wrappers}, "instruction": sc.instruction_for(wrappers[0]),
        "protocol": {"path": PROTOCOL, "sha256": sha256_file(REPO_ROOT / PROTOCOL)},
        "manifest": {"path": args.manifest, "sha256": sha256_file(REPO_ROOT / args.manifest)},
        "tokenizers": provenance, "cost": summary, "n_jobs": len(jobs),
        "data_role": "EXPLORATION", "evidence_class": "exploratory; not paper-eligible; not run",
    }
    (out_dir / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "n_jobs": len(jobs), "authorized_to_run": False,
                      "per_model": {k: {m: v[m] for m in ("n_jobs", "n_jobs_with_decoy", "n_scoring_forward_passes")}
                                    for k, v in summary["per_model"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
