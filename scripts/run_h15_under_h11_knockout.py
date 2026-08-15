#!/usr/bin/env python3
"""Test whether H11 knockout suppresses H15's direct logit contribution."""

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


DEFAULT_STAGE = 12
DEFAULT_LAYER = 16
DEFAULT_H11 = 11
DEFAULT_H15 = 15


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--patch-families", nargs="+", required=True)
    parser.add_argument("--layer", type=int, default=DEFAULT_LAYER)
    parser.add_argument("--gate-head", type=int, default=DEFAULT_H11)
    parser.add_argument("--target-head", type=int, default=DEFAULT_H15)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def first_answer_token_id(bundle: Any, answer: str) -> int:
    return int(bundle.tokenizer(answer, add_special_tokens=False).input_ids[0])


def first_answer_token_logit(logits: torch.Tensor, token_id: int) -> float:
    return float(logits[0, -1, int(token_id)].item())


def head_direct_logit_contribution(
    *,
    bundle: Any,
    input_ids: torch.Tensor,
    layer: int,
    head_index: int,
    answer_token_id: int,
) -> float:
    hook_name = f"blocks.{layer}.attn.hook_result"
    _, cache = bundle.hooked_model.run_with_cache(input_ids, names_filter=lambda name: name == hook_name)
    head_outputs = cache[hook_name][0]
    last_pos = int(input_ids.shape[1] - 1)
    head_vec = head_outputs[last_pos, int(head_index), :]
    contrib = bundle.hooked_model.unembed(head_vec.unsqueeze(0))[0, int(answer_token_id)]
    return float(contrib.detach().cpu().item())


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_h15_under_h11_knockout.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("H11->H15 gating test currently requires TransformerLens support.")
    bundle.hooked_model.set_use_attn_result(True)
    model_device = next(bundle.hooked_model.parameters()).device

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
        answer_token_id = first_answer_token_id(bundle, str(family_payload["correct_answer"]))
        for variant_label, variant_id in (("base", base_variant_id), ("sensitive", sensitive_variant_id)):
            variant_payload = variants_by_id[int(variant_id)]
            prompt = format_prompt_with_chat_template(str(variant_payload["prompt"]), bundle.tokenizer)
            input_ids = bundle.tokenizer(
                prompt,
                return_tensors="pt",
                add_special_tokens=True,
            ).input_ids.to(model_device)
            patch_position = int(input_ids.shape[1] - 1)

            clean_logits = bundle.hooked_model(input_ids)
            h15_logit_normal = head_direct_logit_contribution(
                bundle=bundle,
                input_ids=input_ids,
                layer=int(args.layer),
                head_index=int(args.target_head),
                answer_token_id=answer_token_id,
            )
            clean_first_token_logit = first_answer_token_logit(clean_logits, answer_token_id)

            hook_name = f"blocks.{int(args.layer)}.attn.hook_result"
            h11_hook = build_head_knockout_hook(position=patch_position, head_indices=[int(args.gate_head)])
            with bundle.hooked_model.hooks(fwd_hooks=[(hook_name, h11_hook)]):
                ko_logits, ko_cache = bundle.hooked_model.run_with_cache(
                    input_ids,
                    names_filter=lambda name: name == hook_name,
                )
            ko_head_outputs = ko_cache[hook_name][0]
            h15_vec_ko = ko_head_outputs[patch_position, int(args.target_head), :]
            h15_logit_h11ko = float(
                bundle.hooked_model.unembed(h15_vec_ko.unsqueeze(0))[0, int(answer_token_id)].detach().cpu().item()
            )
            ko_first_token_logit = first_answer_token_logit(ko_logits, answer_token_id)

            per_family_rows.append(
                {
                    "family_id": family_id,
                    "variant_label": variant_label,
                    "variant_id": int(variant_id),
                    "original_S_lp": float(original_slp),
                    "layer_index": int(args.layer),
                    "gate_head": int(args.gate_head),
                    "target_head": int(args.target_head),
                    "h15_logit_contribution_normal": h15_logit_normal,
                    "h15_logit_contribution_h11ko": h15_logit_h11ko,
                    "h15_logit_reduction": float(h15_logit_h11ko - h15_logit_normal),
                    "first_answer_logit_normal": clean_first_token_logit,
                    "first_answer_logit_h11ko": ko_first_token_logit,
                }
            )

    def mean_for(variant_label: str, key: str) -> float:
        rows = [row[key] for row in per_family_rows if row["variant_label"] == variant_label]
        return float(np.mean(rows)) if rows else 0.0

    sensitive_normal = mean_for("sensitive", "h15_logit_contribution_normal")
    sensitive_h11ko = mean_for("sensitive", "h15_logit_contribution_h11ko")
    summary = {
        "layer_index": int(args.layer),
        "gate_head": int(args.gate_head),
        "target_head": int(args.target_head),
        "n_rows": len(per_family_rows),
        "mean_h15_logit_normal_base": mean_for("base", "h15_logit_contribution_normal"),
        "mean_h15_logit_h11ko_base": mean_for("base", "h15_logit_contribution_h11ko"),
        "mean_h15_logit_normal_sensitive": sensitive_normal,
        "mean_h15_logit_h11ko_sensitive": sensitive_h11ko,
        "mean_h15_logit_reduction_sensitive": float(sensitive_h11ko - sensitive_normal),
        "relative_reduction_sensitive_pct": (
            float(100.0 * (sensitive_h11ko - sensitive_normal) / abs(sensitive_normal))
            if abs(sensitive_normal) > 1e-9
            else None
        ),
    }

    write_json(output_dir / "gating_test_per_family.json", per_family_rows)
    write_json(output_dir / "gating_test_summary.json", summary)
    logger.log_event(
        "H15_UNDER_H11_KNOCKOUT_COMPLETE",
        layer_index=int(args.layer),
        gate_head=int(args.gate_head),
        target_head=int(args.target_head),
        mean_h15_logit_normal_sensitive=float(summary["mean_h15_logit_normal_sensitive"]),
        mean_h15_logit_h11ko_sensitive=float(summary["mean_h15_logit_h11ko_sensitive"]),
    )


if __name__ == "__main__":
    main()
