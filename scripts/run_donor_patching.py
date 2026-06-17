#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 9 donor-based causal controls: unrelated-domain and same-answer donors."""

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


DEFAULT_STAGE = 9
DEFAULT_SEED = 42
FLOAT_PATTERN = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", required=True)
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--patch-families", nargs="+", required=True)
    parser.add_argument("--donor-families", nargs="+", required=True)
    parser.add_argument("--family-csv", required=True)
    parser.add_argument("--donor-mode", default="unrelated_and_same_answer")
    parser.add_argument("--patch-layers", nargs="+", type=int, default=[16])
    parser.add_argument("--patch-site", default="resid_post_last_prompt")
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def extract_numeric_value(answer: str) -> float | None:
    match = FLOAT_PATTERN.search(str(answer))
    return float(match.group(0)) if match else None


def load_family_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["template_id"]: row for row in csv.DictReader(handle)}


def select_same_answer_donors(
    *,
    test_family_id: str,
    family_payloads: dict[str, dict[str, Any]],
    family_rows: dict[str, dict[str, str]],
    n_donors: int = 3,
    answer_tolerance: float = 0.15,
) -> list[str]:
    """Pick low-S_lp donors whose numeric correct answers are close to the test family."""

    test_value = extract_numeric_value(str(family_payloads[test_family_id]["correct_answer"]))
    if test_value is None or abs(test_value) < 1e-12:
        return []
    candidates: list[tuple[str, float]] = []
    for family_id, payload in family_payloads.items():
        if family_id == test_family_id:
            continue
        answer_value = extract_numeric_value(str(payload["correct_answer"]))
        if answer_value is None:
            continue
        relative_gap = abs(answer_value - test_value) / abs(test_value)
        if relative_gap >= answer_tolerance:
            continue
        row = family_rows.get(family_id, {})
        slp = float(row.get("qwen_S_lp", "1.0") or "1.0")
        if slp >= 0.2:
            continue
        candidates.append((family_id, slp))
    candidates.sort(key=lambda item: item[1])
    return [family_id for family_id, _ in candidates[:n_donors]]


def resolve_patch_position(prompt_ids: torch.Tensor) -> int:
    return int(prompt_ids.shape[1] - 1)


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role) if args.model_role else resolve_model_spec(role=args.model_role)
    logger = ExperimentLogger(
        script_name="run_donor_patching.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    all_family_ids = sorted(set(args.patch_families + args.donor_families))
    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, all_family_ids)
    }
    family_rows = load_family_rows(Path(args.family_csv))
    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Donor patching currently requires TransformerLens support.")
    model_device = next(bundle.hooked_model.parameters()).device

    rows: list[dict[str, Any]] = []
    for family_id in args.patch_families:
        family_payload = family_payloads[family_id]
        variant_logprobs = behavioural_table[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(variant_logprobs)
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload for variant_payload in family_payload["variants"]
        }
        sensitive_variant = variants_by_id[sensitive_variant_id]
        sensitive_prompt = format_prompt_with_chat_template(str(sensitive_variant["prompt"]), bundle.tokenizer)
        sensitive_prompt_ids = bundle.tokenizer(
            sensitive_prompt,
            return_tensors="pt",
            add_special_tokens=True,
        ).input_ids.to(model_device)
        answer_ids = bundle.tokenizer(
            str(family_payload["correct_answer"]),
            return_tensors="pt",
            add_special_tokens=False,
        ).input_ids.to(model_device)
        sensitive_full_ids = torch.cat([sensitive_prompt_ids, answer_ids], dim=1)
        sensitive_position = resolve_patch_position(sensitive_prompt_ids)

        donor_modes: dict[str, list[str]] = {
            "unrelated": list(args.donor_families),
            "same_answer_low_slp": select_same_answer_donors(
                test_family_id=family_id,
                family_payloads=family_payloads,
                family_rows=family_rows,
            ),
        }
        for donor_mode, donor_ids in donor_modes.items():
            for donor_id in donor_ids:
                donor_payload = family_payloads[donor_id]
                donor_variants_by_id = {
                    int(variant_payload["variant_id"]): variant_payload for variant_payload in donor_payload["variants"]
                }
                donor_base_variant = donor_variants_by_id[0]
                donor_prompt = format_prompt_with_chat_template(str(donor_base_variant["prompt"]), bundle.tokenizer)
                donor_prompt_ids = bundle.tokenizer(
                    donor_prompt,
                    return_tensors="pt",
                    add_special_tokens=True,
                ).input_ids.to(model_device)
                donor_full_ids = torch.cat([donor_prompt_ids, answer_ids], dim=1)
                donor_position = resolve_patch_position(donor_prompt_ids)

                candidate_hook_names = {f"blocks.{layer_index}.hook_resid_post" for layer_index in args.patch_layers}
                _, donor_cache = bundle.hooked_model.run_with_cache(
                    donor_full_ids,
                    names_filter=lambda name: name in candidate_hook_names,
                )
                for patch_layer in args.patch_layers:
                    hook_name = f"blocks.{patch_layer}.hook_resid_post"
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
                            "donor_mode": donor_mode,
                            "donor_id": donor_id,
                            "patch_layer": int(patch_layer),
                            "original_S_lp": float(original_slp),
                            "patched_S_lp": patched_slp,
                            "recovery_fraction": recovery,
                        }
                    )

    summary: dict[str, Any] = {"rows": len(rows), "by_mode": {}}
    for donor_mode in sorted(set(row["donor_mode"] for row in rows)):
        mode_rows = [row for row in rows if row["donor_mode"] == donor_mode]
        summary["by_mode"][donor_mode] = {
            "mean_recovery": float(np.mean([row["recovery_fraction"] for row in mode_rows])) if mode_rows else 0.0,
            "median_recovery": float(np.median([row["recovery_fraction"] for row in mode_rows])) if mode_rows else 0.0,
            "n_rows": len(mode_rows),
        }

    with (output_dir / "donor_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "family_id",
                "donor_mode",
                "donor_id",
                "patch_layer",
                "original_S_lp",
                "patched_S_lp",
                "recovery_fraction",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    write_json(output_dir / "donor_summary.json", summary)
    logger.log_event("DONOR_PATCHING_COMPLETE", **summary)


if __name__ == "__main__":
    main()
