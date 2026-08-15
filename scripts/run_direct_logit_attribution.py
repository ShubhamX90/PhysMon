#!/usr/bin/env python3
"""Head-level direct logit attribution by ablation at a fixed layer."""

from __future__ import annotations

import argparse
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
    build_head_knockout_hook,
    load_variant_logprob_table,
    locate_sensitive_variant,
)


DEFAULT_STAGE = 10
DEFAULT_LAYER = 16


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--patch-families", nargs="+", required=True)
    parser.add_argument("--layer", type=int, default=DEFAULT_LAYER)
    parser.add_argument("--heads", nargs="*", type=int, default=None)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def first_answer_token_logit_and_prob(logits: torch.Tensor, token_id: int) -> tuple[float, float]:
    last_logits = logits[0, -1, :]
    probs = torch.softmax(last_logits, dim=-1)
    return float(last_logits[int(token_id)].item()), float(probs[int(token_id)].item())


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_direct_logit_attribution.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Direct logit attribution currently requires TransformerLens support.")
    bundle.hooked_model.set_use_attn_result(True)
    model_device = next(bundle.hooked_model.parameters()).device
    n_heads = int(bundle.hooked_model.cfg.n_heads)
    heads = list(range(n_heads)) if args.heads is None or len(args.heads) == 0 else [int(head) for head in args.heads]

    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, list(args.patch_families))
    }
    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)

    per_head_rows: list[dict[str, Any]] = []
    summary_accumulator: dict[int, dict[str, list[float]]] = {
        head: {
            "base_logit_attr": [],
            "sensitive_logit_attr": [],
            "base_prob_attr": [],
            "sensitive_prob_attr": [],
            "delta_logit_attr": [],
            "delta_prob_attr": [],
        }
        for head in heads
    }

    for family_id in args.patch_families:
        family_payload = family_payloads[family_id]
        variant_logprobs = behavioural_table[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(variant_logprobs)
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload
            for variant_payload in family_payload["variants"]
        }
        answer_token_id = int(
            bundle.tokenizer(
                str(family_payload["correct_answer"]),
                add_special_tokens=False,
            ).input_ids[0]
        )

        for variant_label, variant_id in (("base", base_variant_id), ("sensitive", sensitive_variant_id)):
            variant_payload = variants_by_id[variant_id]
            prompt = format_prompt_with_chat_template(str(variant_payload["prompt"]), bundle.tokenizer)
            input_ids = bundle.tokenizer(
                prompt,
                return_tensors="pt",
                add_special_tokens=True,
            ).input_ids.to(model_device)
            patch_position = int(input_ids.shape[1] - 1)
            clean_logits = bundle.hooked_model(input_ids)
            clean_logit, clean_prob = first_answer_token_logit_and_prob(clean_logits, answer_token_id)

            for head_index in heads:
                hook_name = f"blocks.{int(args.layer)}.attn.hook_result"
                hook_fn = build_head_knockout_hook(position=patch_position, head_indices=[head_index])
                ablated_logits = bundle.hooked_model.run_with_hooks(
                    input_ids,
                    fwd_hooks=[(hook_name, hook_fn)],
                )
                ablated_logit, ablated_prob = first_answer_token_logit_and_prob(ablated_logits, answer_token_id)
                logit_attr = clean_logit - ablated_logit
                prob_attr = clean_prob - ablated_prob

                per_head_rows.append(
                    {
                        "family_id": family_id,
                        "variant_label": variant_label,
                        "variant_id": int(variant_id),
                        "original_S_lp": float(original_slp),
                        "layer_index": int(args.layer),
                        "head_index": int(head_index),
                        "clean_logit": float(clean_logit),
                        "ablated_logit": float(ablated_logit),
                        "logit_attribution": float(logit_attr),
                        "clean_prob": float(clean_prob),
                        "ablated_prob": float(ablated_prob),
                        "probability_attribution": float(prob_attr),
                    }
                )
                summary_accumulator[head_index][f"{variant_label}_logit_attr"].append(float(logit_attr))
                summary_accumulator[head_index][f"{variant_label}_prob_attr"].append(float(prob_attr))

        for head_index in heads:
            family_base = next(
                row for row in per_head_rows
                if row["family_id"] == family_id and row["variant_label"] == "base" and row["head_index"] == head_index
            )
            family_sensitive = next(
                row for row in per_head_rows
                if row["family_id"] == family_id and row["variant_label"] == "sensitive" and row["head_index"] == head_index
            )
            summary_accumulator[head_index]["delta_logit_attr"].append(
                float(family_sensitive["logit_attribution"] - family_base["logit_attribution"])
            )
            summary_accumulator[head_index]["delta_prob_attr"].append(
                float(family_sensitive["probability_attribution"] - family_base["probability_attribution"])
            )

    head_summary = []
    for head_index in heads:
        row = {
            "head_index": int(head_index),
            "mean_base_logit_attr": float(np.mean(summary_accumulator[head_index]["base_logit_attr"])),
            "mean_sensitive_logit_attr": float(np.mean(summary_accumulator[head_index]["sensitive_logit_attr"])),
            "mean_delta_logit_attr": float(np.mean(summary_accumulator[head_index]["delta_logit_attr"])),
            "mean_base_prob_attr": float(np.mean(summary_accumulator[head_index]["base_prob_attr"])),
            "mean_sensitive_prob_attr": float(np.mean(summary_accumulator[head_index]["sensitive_prob_attr"])),
            "mean_delta_prob_attr": float(np.mean(summary_accumulator[head_index]["delta_prob_attr"])),
        }
        head_summary.append(row)
    head_summary.sort(key=lambda row: abs(row["mean_delta_logit_attr"]), reverse=True)

    write_json(output_dir / "direct_logit_attribution_per_head.json", per_head_rows)
    write_json(
        output_dir / "direct_logit_attribution_summary.json",
        {
            "model_role": resolved_spec.role,
            "layer_index": int(args.layer),
            "heads": heads,
            "families": list(args.patch_families),
            "ranked_head_summary": head_summary,
        },
    )
    logger.log_event(
        "DIRECT_LOGIT_ATTRIBUTION_COMPLETE",
        layer_index=int(args.layer),
        family_count=len(args.patch_families),
        head_count=len(heads),
        top_head=int(head_summary[0]["head_index"]) if head_summary else None,
    )


if __name__ == "__main__":
    main()
