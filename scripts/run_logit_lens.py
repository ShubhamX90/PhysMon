#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 10 logit-lens trajectories for representative sensitive families.

Tracks the first-answer-token probability across layers for the base and
most-sensitive variants of selected families, using prompt-side residuals at the
last prompt token.
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
DEFAULT_LAYER_CANDIDATE_COUNT = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--family-csv", required=True)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--n-families", type=int, default=DEFAULT_LAYER_CANDIDATE_COUNT)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def select_representative_families(rows: list[dict[str, str]], n_families: int) -> list[str]:
    """Pick a mixed cue-type panel weighted toward high sensitivity."""

    selected: list[str] = []
    for cue_type in ("nongoverning_distractor", "irrelevant_variable", "frame_rendering"):
        cue_rows = [
            row for row in rows
            if row.get("cue_type") == cue_type and float(row.get("qwen_S_lp", "0") or "0") > 0.5
        ]
        cue_rows.sort(key=lambda row: float(row.get("qwen_S_lp", "0") or "0"), reverse=True)
        quota = 3 if cue_type != "frame_rendering" else 4
        selected.extend([row["template_id"] for row in cue_rows[:quota]])
    if len(selected) < n_families:
        extra = [
            row["template_id"]
            for row in sorted(rows, key=lambda row: float(row.get("qwen_S_lp", "0") or "0"), reverse=True)
            if row["template_id"] not in selected
        ]
        selected.extend(extra[: max(0, n_families - len(selected))])
    return selected[:n_families]


def first_answer_token_probability(
    *,
    model: Any,
    resid_vector: torch.Tensor,
    answer_token_id: int,
) -> float:
    """Project one residual vector through ln_final + unembed and score one token."""

    normalized = model.ln_final(resid_vector.view(1, 1, -1))
    logits = model.unembed(normalized)[0, 0, :]
    probs = torch.softmax(logits, dim=-1)
    return float(probs[int(answer_token_id)].item())


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_logit_lens.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Logit-lens analysis currently requires TransformerLens support.")

    rows = load_rows(Path(args.family_csv))
    family_ids = list(args.families) if args.families else select_representative_families(rows, args.n_families)
    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, family_ids)
    }
    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)
    model_device = next(bundle.hooked_model.parameters()).device

    per_family = []
    all_delta_peaks = []
    for family_id in family_ids:
        family_payload = family_payloads[family_id]
        variant_logprobs = behavioural_table[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(variant_logprobs)
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload
            for variant_payload in family_payload["variants"]
        }
        base_variant = variants_by_id[base_variant_id]
        sensitive_variant = variants_by_id[sensitive_variant_id]
        answer_token_id = int(
            bundle.tokenizer(
                str(family_payload["correct_answer"]),
                add_special_tokens=False,
            ).input_ids[0]
        )

        family_result = {
            "family_id": family_id,
            "cue_type": family_payload.get("cue_type"),
            "original_S_lp": float(original_slp),
            "layers": [],
        }
        layer_deltas = []
        for variant_label, variant_payload in (("base", base_variant), ("sensitive", sensitive_variant)):
            prompt = format_prompt_with_chat_template(str(variant_payload["prompt"]), bundle.tokenizer)
            prompt_ids = bundle.tokenizer(
                prompt,
                return_tensors="pt",
                add_special_tokens=True,
            ).input_ids.to(model_device)
            last_pos = int(prompt_ids.shape[1] - 1)
            cache_names = lambda name: name.endswith(".hook_resid_post")
            _, cache = bundle.hooked_model.run_with_cache(prompt_ids, names_filter=cache_names)
            probs = []
            for layer_index in range(bundle.hooked_model.cfg.n_layers):
                resid = cache[f"blocks.{layer_index}.hook_resid_post"][0, last_pos, :].detach()
                probs.append(first_answer_token_probability(model=bundle.hooked_model, resid_vector=resid, answer_token_id=answer_token_id))
            family_result[f"{variant_label}_first_token_probs"] = probs

        for layer_index, (base_prob, sensitive_prob) in enumerate(
            zip(
                family_result["base_first_token_probs"],
                family_result["sensitive_first_token_probs"],
                strict=True,
            )
        ):
            delta = float(base_prob - sensitive_prob)
            layer_deltas.append(delta)
            family_result["layers"].append(
                {
                    "layer_index": int(layer_index),
                    "base_first_token_prob": float(base_prob),
                    "sensitive_first_token_prob": float(sensitive_prob),
                    "delta_first_token_prob": delta,
                }
            )
        peak_layer = int(np.argmax(layer_deltas))
        all_delta_peaks.append(peak_layer)
        family_result["peak_delta_layer"] = peak_layer
        family_result["peak_delta_value"] = float(layer_deltas[peak_layer])
        per_family.append(family_result)

    summary = {
        "model_role": resolved_spec.role,
        "n_families": len(per_family),
        "families": family_ids,
        "mean_peak_delta_layer": float(np.mean(all_delta_peaks)) if all_delta_peaks else None,
        "median_peak_delta_layer": float(np.median(all_delta_peaks)) if all_delta_peaks else None,
    }
    write_json(output_dir / "logit_lens_per_family.json", per_family)
    write_json(output_dir / "logit_lens_summary.json", summary)
    logger.log_event("LOGIT_LENS_COMPLETE", **summary)


if __name__ == "__main__":
    main()
