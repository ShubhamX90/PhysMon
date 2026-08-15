#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 10 attention-pattern analysis for Qwen shortcut-sensitivity heads.

For each family, compare the last-prompt-token attention mass assigned to the
distractor-value token span in the base variant versus the most-sensitive
variant. This tests whether the identified causal heads attend more strongly to
the distractor tokens under sensitivity-inducing cue settings.
"""

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
    load_variant_logprob_table,
    locate_sensitive_variant,
)


DEFAULT_STAGE = 10
DEFAULT_SEED = 42
DEFAULT_LAYER = 16
DEFAULT_HEADS = (26, 24, 13, 11)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--patch-families", nargs="+", required=True)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--layer", type=int, default=DEFAULT_LAYER)
    parser.add_argument("--heads", nargs="+", type=int, default=list(DEFAULT_HEADS))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def find_substring_token_span(prompt: str, substring: str, tokenizer: Any) -> list[int]:
    """Return prompt token indices whose character spans overlap a substring."""

    if not substring:
        return []
    start = prompt.find(substring)
    if start < 0:
        return []
    end = start + len(substring)
    try:
        tokenized = tokenizer(
            prompt,
            add_special_tokens=False,
            return_offsets_mapping=True,
        )
        offsets = tokenized.get("offset_mapping") or []
    except (NotImplementedError, TypeError, ValueError):
        offsets = []

    span: list[int] = []
    if offsets:
        for token_index, (token_start, token_end) in enumerate(offsets):
            if token_end <= token_start:
                continue
            if token_start < end and token_end > start:
                span.append(int(token_index))
    if span:
        return span

    prefix = tokenizer(prompt[:start], add_special_tokens=False).input_ids
    substring_ids = tokenizer(substring, add_special_tokens=False).input_ids
    if not substring_ids:
        return []
    return list(range(len(prefix), len(prefix) + len(substring_ids)))


def attention_mass_for_prompt(
    *,
    bundle: Any,
    formatted_prompt: str,
    layer: int,
    heads: list[int],
    token_span: list[int],
) -> dict[int, float]:
    """Compute last-prompt-token attention mass on one token span for selected heads."""

    prompt_ids = bundle.tokenizer(
        formatted_prompt,
        return_tensors="pt",
        add_special_tokens=True,
    ).input_ids.to(next(bundle.hooked_model.parameters()).device)
    hook_name = f"blocks.{layer}.attn.hook_pattern"
    _, cache = bundle.hooked_model.run_with_cache(
        prompt_ids,
        names_filter=lambda name: name == hook_name,
    )
    patterns = cache[hook_name][0]  # (n_heads, dest_pos, src_pos)
    last_pos = int(prompt_ids.shape[1] - 1)
    if not token_span:
        return {head: 0.0 for head in heads}
    return {
        int(head): float(patterns[int(head), last_pos, token_span].sum().item())
        for head in heads
    }


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_attention_pattern_analysis.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Attention-pattern analysis currently requires TransformerLens support.")

    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, list(args.patch_families))
    }
    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)

    per_family_rows: list[dict[str, Any]] = []
    for family_id in args.patch_families:
        family_payload = family_payloads[family_id]
        variant_logprobs = behavioural_table[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(variant_logprobs)
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload
            for variant_payload in family_payload["variants"]
        }
        base_variant = variants_by_id[base_variant_id]
        sensitive_variant = variants_by_id[sensitive_variant_id]

        base_prompt = format_prompt_with_chat_template(str(base_variant["prompt"]), bundle.tokenizer)
        sensitive_prompt = format_prompt_with_chat_template(str(sensitive_variant["prompt"]), bundle.tokenizer)
        base_span = find_substring_token_span(base_prompt, str(base_variant["cue_value"]), bundle.tokenizer)
        sensitive_span = find_substring_token_span(sensitive_prompt, str(sensitive_variant["cue_value"]), bundle.tokenizer)
        base_masses = attention_mass_for_prompt(
            bundle=bundle,
            formatted_prompt=base_prompt,
            layer=args.layer,
            heads=list(args.heads),
            token_span=base_span,
        )
        sensitive_masses = attention_mass_for_prompt(
            bundle=bundle,
            formatted_prompt=sensitive_prompt,
            layer=args.layer,
            heads=list(args.heads),
            token_span=sensitive_span,
        )
        for head in args.heads:
            per_family_rows.append(
                {
                    "family_id": family_id,
                    "head_index": int(head),
                    "original_S_lp": float(original_slp),
                    "base_attention_mass": float(base_masses[int(head)]),
                    "sensitive_attention_mass": float(sensitive_masses[int(head)]),
                    "delta_attention_mass": float(sensitive_masses[int(head)] - base_masses[int(head)]),
                    "base_cue_token_count": len(base_span),
                    "sensitive_cue_token_count": len(sensitive_span),
                }
            )

    head_summary = []
    for head in args.heads:
        head_rows = [row for row in per_family_rows if int(row["head_index"]) == int(head)]
        deltas = [float(row["delta_attention_mass"]) for row in head_rows]
        head_summary.append(
            {
                "head_index": int(head),
                "mean_base_attention_mass": float(np.mean([row["base_attention_mass"] for row in head_rows])) if head_rows else 0.0,
                "mean_sensitive_attention_mass": float(np.mean([row["sensitive_attention_mass"] for row in head_rows])) if head_rows else 0.0,
                "mean_delta_attention_mass": float(np.mean(deltas)) if deltas else 0.0,
                "median_delta_attention_mass": float(np.median(deltas)) if deltas else 0.0,
                "fraction_sensitive_gt_base": float(np.mean([delta > 0 for delta in deltas])) if deltas else 0.0,
            }
        )
    head_summary.sort(key=lambda row: row["mean_delta_attention_mass"], reverse=True)

    write_json(output_dir / "attention_pattern_per_family.json", per_family_rows)
    write_json(
        output_dir / "attention_pattern_summary.json",
        {
            "layer": int(args.layer),
            "heads": [int(head) for head in args.heads],
            "n_families": len(args.patch_families),
            "head_summary": head_summary,
            "headline_interpretation": (
                "Positive mean delta indicates that the head assigns more last-prompt-token attention mass "
                "to distractor-value tokens in the most-sensitive variant than in the base variant."
            ),
        },
    )
    logger.log_event(
        "ATTENTION_PATTERN_COMPLETE",
        layer=int(args.layer),
        heads=[int(head) for head in args.heads],
        n_families=len(args.patch_families),
    )


if __name__ == "__main__":
    main()
