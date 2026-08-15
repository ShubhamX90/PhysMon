#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 10 same-answer/no-cue donor control."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.models.hooks import set_global_seed  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402

from run_behavioural import format_prompt_with_chat_template, load_rendered_families  # noqa: E402
from run_causal_patching import (  # noqa: E402
    DEFAULT_BEHAVIOURAL_JSONL,
    DEFAULT_JSONL_NAME,
    build_patch_hook,
    compute_answer_logprob_from_logits,
    load_variant_logprob_table,
    locate_sensitive_variant,
)


DEFAULT_STAGE = 10
DEFAULT_SEED = 42
DEFAULT_MHK_SUMMARY = "results/stage8/multi_head_knockout/patching_summary.json"
FLOAT_PATTERN = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


class EmptyResultPanelError(RuntimeError):
    """Raised when donor selection produced no evaluable target-donor pairs."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", required=True, help="Target family directory to patch into.")
    parser.add_argument("--patch-families", nargs="+", required=True)
    parser.add_argument("--family-csv", required=True, help="Target family per-family CSV.")
    parser.add_argument(
        "--donor-family-dir",
        default=None,
        help="Optional donor family directory. Defaults to --family-dir.",
    )
    parser.add_argument(
        "--donor-family-csv",
        default=None,
        help="Optional donor family per-family CSV. Defaults to --family-csv.",
    )
    parser.add_argument("--patch-layer", type=int, default=16)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--mkh-summary", default=DEFAULT_MHK_SUMMARY)
    parser.add_argument("--answer-tolerance", type=float, default=0.20)
    parser.add_argument("--max-donors-per-family", type=int, default=3)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def extract_numeric_value(text: str) -> float | None:
    match = FLOAT_PATTERN.search(str(text))
    return float(match.group(0)) if match else None


def load_family_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["template_id"]: row for row in csv.DictReader(handle)}


def resolve_patch_position(prompt_ids: torch.Tensor) -> int:
    return int(prompt_ids.shape[1] - 1)


def summarize_same_answer_rows(
    rows: list[dict[str, Any]],
    *,
    n_target_families: int,
    reference_mhk: float,
) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "n_target_families": n_target_families,
            "mean_recovery": None,
            "median_recovery": None,
            "reference_mhk_mean_recovery": reference_mhk,
            "specificity_ratio_vs_mhk": None,
            "status": "FAILED_EMPTY_RESULT_PANEL",
            "paper_eligibility": False,
            "scientific_null": False,
            "summary_defaulted_zero": False,
            "failure_reason": "No eligible target-donor pairs were evaluated; zero rows are not a zero effect.",
        }
    mean_recovery = float(np.mean([row["recovery_fraction"] for row in rows]))
    return {
        "rows": len(rows),
        "n_target_families": n_target_families,
        "mean_recovery": mean_recovery,
        "median_recovery": float(np.median([row["recovery_fraction"] for row in rows])),
        "reference_mhk_mean_recovery": reference_mhk,
        "specificity_ratio_vs_mhk": (reference_mhk / mean_recovery) if abs(mean_recovery) > 1e-9 else None,
        "status": "COMPLETE",
        "paper_eligibility": False,
        "scientific_null": False,
        "summary_defaulted_zero": False,
    }


def select_donors(
    *,
    target_family_id: str,
    family_payloads: dict[str, dict[str, Any]],
    family_rows: dict[str, dict[str, str]],
    tolerance: float,
    max_donors: int,
) -> list[str]:
    target_value = extract_numeric_value(str(family_payloads[target_family_id]["correct_answer"]))
    if target_value is None or abs(target_value) < 1e-12:
        return []
    candidates: list[tuple[float, float, str]] = []
    for family_id, payload in family_payloads.items():
        if family_id == target_family_id:
            continue
        row = family_rows.get(family_id, {})
        if not row:
            continue
        parse_ok = row.get("qwen_parse_ok", "")
        parse_rate = float(row.get("qwen_parse_rate_family", "0") or "0")
        if parse_ok:
            if parse_ok.lower() not in {"true", "1", "yes"}:
                continue
        elif parse_rate < 0.5:
            continue
        slp = float(row.get("qwen_S_lp", "1e9") or "1e9")
        if slp >= 0.3:
            continue
        answer_value = extract_numeric_value(str(payload["correct_answer"]))
        if answer_value is None:
            continue
        relative_gap = abs(answer_value - target_value) / abs(target_value)
        if relative_gap > tolerance:
            continue
        candidates.append((relative_gap, slp, family_id))
    candidates.sort()
    return [family_id for _, _, family_id in candidates[:max_donors]]


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_same_answer_donor.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    donor_family_rows = load_family_rows(Path(args.donor_family_csv or args.family_csv))
    target_family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir)
    }
    donor_family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.donor_family_dir or args.family_dir)
    }
    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)
    mhk_summary = {}
    mhk_path = Path(args.mkh_summary)
    if mhk_path.exists():
        mhk_summary = __import__("json").loads(mhk_path.read_text())
    reference_mhk = float(mhk_summary.get("best_mean_recovery_fraction", 0.0) or 0.0)

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Same-answer donor patching currently requires TransformerLens support.")
    model_device = next(bundle.hooked_model.parameters()).device

    rows: list[dict[str, Any]] = []
    for family_id in args.patch_families:
        donors = select_donors(
            target_family_id=family_id,
            family_payloads=donor_family_payloads,
            family_rows=donor_family_rows,
            tolerance=args.answer_tolerance,
            max_donors=args.max_donors_per_family,
        )
        if not donors:
            continue
        family_payload = target_family_payloads[family_id]
        variant_logprobs = behavioural_table[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(variant_logprobs)
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload
            for variant_payload in family_payload["variants"]
        }
        sensitive_variant = variants_by_id[sensitive_variant_id]
        sensitive_prompt = format_prompt_with_chat_template(str(sensitive_variant["prompt"]), bundle.tokenizer)
        sensitive_prompt_ids = bundle.tokenizer(
            sensitive_prompt, return_tensors="pt", add_special_tokens=True
        ).input_ids.to(model_device)
        answer_ids = bundle.tokenizer(
            str(family_payload["correct_answer"]), return_tensors="pt", add_special_tokens=False
        ).input_ids.to(model_device)
        sensitive_full_ids = torch.cat([sensitive_prompt_ids, answer_ids], dim=1)
        sensitive_position = resolve_patch_position(sensitive_prompt_ids)

        for donor_id in donors:
            donor_payload = donor_family_payloads[donor_id]
            donor_variants = {
                int(variant_payload["variant_id"]): variant_payload
                for variant_payload in donor_payload["variants"]
            }
            donor_prompt = format_prompt_with_chat_template(str(donor_variants[0]["prompt"]), bundle.tokenizer)
            donor_prompt_ids = bundle.tokenizer(
                donor_prompt, return_tensors="pt", add_special_tokens=True
            ).input_ids.to(model_device)
            donor_full_ids = torch.cat([donor_prompt_ids, answer_ids], dim=1)
            donor_position = resolve_patch_position(donor_prompt_ids)

            hook_name = f"blocks.{args.patch_layer}.hook_resid_post"
            _, donor_cache = bundle.hooked_model.run_with_cache(
                donor_full_ids,
                names_filter=lambda name: name == hook_name,
            )
            donor_resid = donor_cache[hook_name][0, donor_position, :].detach().clone()
            patched_logits = bundle.hooked_model.run_with_hooks(
                sensitive_full_ids,
                fwd_hooks=[(hook_name, build_patch_hook(donor_resid, position=sensitive_position))],
            )
            patched_logprob = compute_answer_logprob_from_logits(
                full_ids=sensitive_full_ids,
                prompt_length=int(sensitive_prompt_ids.shape[1]),
                logits=patched_logits,
            )
            patched_slp = float(variant_logprobs[base_variant_id] - patched_logprob)
            recovery = 0.0 if abs(original_slp) < 1e-6 else 1.0 - (patched_slp / original_slp)
            rows.append(
                {
                    "family_id": family_id,
                    "donor_id": donor_id,
                    "patch_layer": args.patch_layer,
                    "original_S_lp": float(original_slp),
                    "patched_S_lp": patched_slp,
                    "recovery_fraction": recovery,
                }
            )

    summary = summarize_same_answer_rows(
        rows,
        n_target_families=len(args.patch_families),
        reference_mhk=reference_mhk,
    )

    with (output_dir / "same_answer_donor_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "family_id",
                "donor_id",
                "patch_layer",
                "original_S_lp",
                "patched_S_lp",
                "recovery_fraction",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    write_json(output_dir / "same_answer_donor_summary.json", summary)
    if not rows:
        logger.log_event("FAILED_EMPTY_RESULT_PANEL", **summary)
        raise EmptyResultPanelError(summary["failure_reason"])
    logger.log_event("SAME_ANSWER_DONOR_COMPLETE", **summary)


if __name__ == "__main__":
    main()
