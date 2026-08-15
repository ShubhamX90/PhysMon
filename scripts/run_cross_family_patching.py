#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 10 cross-family sufficiency patching."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--family-csv", required=True)
    parser.add_argument("--patch-layer", type=int, default=16)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--n-target-families", type=int, default=20)
    parser.add_argument("--n-donor-families", type=int, default=5)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_patch_position(prompt_ids: torch.Tensor) -> int:
    return int(prompt_ids.shape[1] - 1)


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_cross_family_patching.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    rows = load_rows(Path(args.family_csv))
    cue_b_rows = [
        row for row in rows
        if row.get("cue_type") == "nongoverning_distractor"
        and row.get("qwen_parse_ok", "").lower() in {"true", "1", "yes"}
    ]
    targets = sorted(
        [row for row in cue_b_rows if float(row.get("qwen_S_lp", "1e9") or "1e9") < 0.3],
        key=lambda row: float(row["qwen_S_lp"]),
    )[: args.n_target_families]
    donors = sorted(
        [row for row in cue_b_rows if float(row.get("qwen_S_lp", "0") or "0") > 2.0],
        key=lambda row: float(row["qwen_S_lp"]),
        reverse=True,
    )[: args.n_donor_families]

    target_ids = [row["template_id"] for row in targets]
    donor_ids = [row["template_id"] for row in donors]
    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, sorted(set(target_ids + donor_ids)))
    }
    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)
    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Cross-family patching currently requires TransformerLens support.")
    model_device = next(bundle.hooked_model.parameters()).device

    out_rows: list[dict[str, Any]] = []
    for target_id in target_ids:
        target_payload = family_payloads[target_id]
        target_logprobs = behavioural_table[target_id]
        base_variant_id, _, original_slp = locate_sensitive_variant(target_logprobs)
        target_variants = {
            int(variant_payload["variant_id"]): variant_payload
            for variant_payload in target_payload["variants"]
        }
        target_base = target_variants[base_variant_id]
        target_prompt = format_prompt_with_chat_template(str(target_base["prompt"]), bundle.tokenizer)
        target_prompt_ids = bundle.tokenizer(
            target_prompt, return_tensors="pt", add_special_tokens=True
        ).input_ids.to(model_device)
        answer_ids = bundle.tokenizer(
            str(target_payload["correct_answer"]), return_tensors="pt", add_special_tokens=False
        ).input_ids.to(model_device)
        target_full_ids = torch.cat([target_prompt_ids, answer_ids], dim=1)
        target_position = resolve_patch_position(target_prompt_ids)

        for donor_id in donor_ids:
            donor_payload = family_payloads[donor_id]
            donor_logprobs = behavioural_table[donor_id]
            _, donor_sensitive_id, _ = locate_sensitive_variant(donor_logprobs)
            donor_variants = {
                int(variant_payload["variant_id"]): variant_payload
                for variant_payload in donor_payload["variants"]
            }
            donor_sensitive = donor_variants[donor_sensitive_id]
            donor_prompt = format_prompt_with_chat_template(str(donor_sensitive["prompt"]), bundle.tokenizer)
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
                target_full_ids,
                fwd_hooks=[(hook_name, build_patch_hook(donor_resid, position=target_position))],
            )
            patched_logprob = compute_answer_logprob_from_logits(
                full_ids=target_full_ids,
                prompt_length=int(target_prompt_ids.shape[1]),
                logits=patched_logits,
            )
            patched_slp = float(target_logprobs[base_variant_id] - patched_logprob)
            increase = float(patched_slp - original_slp)
            out_rows.append(
                {
                    "target_family_id": target_id,
                    "donor_family_id": donor_id,
                    "patch_layer": args.patch_layer,
                    "original_S_lp": float(original_slp),
                    "patched_S_lp": patched_slp,
                    "slp_increase": increase,
                    "increased_ge_0p3": int(increase > 0.3),
                }
            )

    summary = {
        "n_targets": len(target_ids),
        "n_donors": len(donor_ids),
        "n_pairs": len(out_rows),
        "mean_slp_increase": float(np.mean([row["slp_increase"] for row in out_rows])) if out_rows else 0.0,
        "fraction_pairs_increased_ge_0p3": float(np.mean([row["increased_ge_0p3"] for row in out_rows])) if out_rows else 0.0,
    }

    with (output_dir / "cross_family_sufficiency_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_family_id",
                "donor_family_id",
                "patch_layer",
                "original_S_lp",
                "patched_S_lp",
                "slp_increase",
                "increased_ge_0p3",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)
    write_json(output_dir / "cross_family_sufficiency_summary.json", summary)
    logger.log_event("CROSS_FAMILY_SUFFICIENCY_COMPLETE", **summary)


if __name__ == "__main__":
    main()
