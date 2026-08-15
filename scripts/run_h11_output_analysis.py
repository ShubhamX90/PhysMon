#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 11 mechanistic analysis of selected Qwen layer-16 head outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE
from physmon.models.hooks import set_global_seed
from physmon.models.loader import load_model, resolve_model_spec
from physmon.utils.io import write_json
from run_behavioural import format_prompt_with_chat_template, load_rendered_families
from run_causal_patching import DEFAULT_BEHAVIOURAL_JSONL, load_variant_logprob_table, locate_sensitive_variant
from run_probing import build_family_feature_tensors, filter_entries_and_tensors, load_per_family_rows, load_site_tensors


DEFAULT_HEADS = (11, 14, 15, 24)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--activation-dir", type=Path, default=Path("/scratch/pabitra/physmon/activations_stage6/qwen_primary/"))
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument("--probe-layer", type=int, default=16)
    parser.add_argument("--family-csv", type=Path, default=Path("results/stage6/analysis_d2/stage6_d1_per_family.csv"))
    parser.add_argument("--positive-families-file", type=Path, default=Path("results/stage6/analysis_d2/stage6_positive_families.json"))
    parser.add_argument("--family-dir", default="results/stage6/generated_full_benchmark/")
    parser.add_argument("--patch-families", nargs="+", required=True)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument("--heads", nargs="+", type=int, default=list(DEFAULT_HEADS))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_positive_families(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(str(item) for item in payload["positive_families"])


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def train_probe_direction(
    *,
    activation_dir: Path,
    site: str,
    layer: int,
    family_csv: Path,
    positive_families: set[str],
) -> np.ndarray:
    family_rows = load_per_family_rows(family_csv)
    entries, tensors = load_site_tensors(activation_dir, site)
    entries, tensors = filter_entries_and_tensors(
        entries,
        tensors,
        family_rows=family_rows,
        exclude_ids=set(STAGE6_EXCLUDE_FROM_PROBE),
        exclude_cue_type=None,
        cue_type=None,
        pilot_only=False,
    )
    family_ids, family_feature_tensors = build_family_feature_tensors(tensors, entries, reducer="mean")
    x_layer = family_feature_tensors[:, layer, :]
    y = np.asarray([int(fid in positive_families) for fid in family_ids], dtype=int)
    scaler = StandardScaler().fit(x_layer)
    x_scaled = scaler.transform(x_layer)
    clf = LogisticRegression(
        C=1.0,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=42,
    )
    clf.fit(x_scaled, y)
    raw_weight = clf.coef_[0] / np.maximum(scaler.scale_, 1e-8)
    return raw_weight / max(np.linalg.norm(raw_weight), 1e-8)


def head_output_vectors(
    *,
    bundle: Any,
    formatted_prompt: str,
    layer: int,
    heads: list[int],
) -> dict[int, np.ndarray]:
    prompt_ids = bundle.tokenizer(
        formatted_prompt,
        return_tensors="pt",
        add_special_tokens=True,
    ).input_ids.to(next(bundle.hooked_model.parameters()).device)
    hook_name = f"blocks.{layer}.attn.hook_result"
    _, cache = bundle.hooked_model.run_with_cache(prompt_ids, names_filter=lambda name: name == hook_name)
    head_outputs = cache[hook_name][0]  # (seq, heads, d_model)
    last_pos = int(prompt_ids.shape[1] - 1)
    return {
        int(head): head_outputs[last_pos, int(head), :].detach().float().cpu().numpy()
        for head in heads
    }


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    positive_families = load_positive_families(args.positive_families_file)
    probe_direction = train_probe_direction(
        activation_dir=args.activation_dir,
        site=args.site,
        layer=args.probe_layer,
        family_csv=args.family_csv,
        positive_families=positive_families,
    )

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Head-output analysis currently requires TransformerLens support.")
    bundle.hooked_model.set_use_attn_result(True)

    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)
    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, list(args.patch_families))
    }

    per_family_rows = []
    for family_id in args.patch_families:
        family_payload = family_payloads[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(behavioural_table[family_id])
        variants_by_id = {int(variant["variant_id"]): variant for variant in family_payload["variants"]}
        base_variant = variants_by_id[base_variant_id]
        sensitive_variant = variants_by_id[sensitive_variant_id]
        base_prompt = format_prompt_with_chat_template(str(base_variant["prompt"]), bundle.tokenizer)
        sensitive_prompt = format_prompt_with_chat_template(str(sensitive_variant["prompt"]), bundle.tokenizer)

        base_vectors = head_output_vectors(bundle=bundle, formatted_prompt=base_prompt, layer=args.layer, heads=list(args.heads))
        sensitive_vectors = head_output_vectors(
            bundle=bundle,
            formatted_prompt=sensitive_prompt,
            layer=args.layer,
            heads=list(args.heads),
        )
        for head in args.heads:
            base_vector = base_vectors[int(head)]
            sensitive_vector = sensitive_vectors[int(head)]
            per_family_rows.append(
                {
                    "family_id": family_id,
                    "head_index": int(head),
                    "original_S_lp": float(original_slp),
                    "base_probe_cosine": cosine(base_vector, probe_direction),
                    "sensitive_probe_cosine": cosine(sensitive_vector, probe_direction),
                    "delta_probe_cosine": cosine(sensitive_vector, probe_direction) - cosine(base_vector, probe_direction),
                    "base_output_norm": float(np.linalg.norm(base_vector)),
                    "sensitive_output_norm": float(np.linalg.norm(sensitive_vector)),
                }
            )

    head_summaries = []
    for head in args.heads:
        rows = [row for row in per_family_rows if int(row["head_index"]) == int(head)]
        head_summaries.append(
            {
                "head_index": int(head),
                "mean_base_probe_cosine": float(np.mean([row["base_probe_cosine"] for row in rows])) if rows else 0.0,
                "mean_sensitive_probe_cosine": float(np.mean([row["sensitive_probe_cosine"] for row in rows])) if rows else 0.0,
                "mean_delta_probe_cosine": float(np.mean([row["delta_probe_cosine"] for row in rows])) if rows else 0.0,
                "mean_base_output_norm": float(np.mean([row["base_output_norm"] for row in rows])) if rows else 0.0,
                "mean_sensitive_output_norm": float(np.mean([row["sensitive_output_norm"] for row in rows])) if rows else 0.0,
            }
        )
    head_summaries.sort(key=lambda row: row["mean_delta_probe_cosine"], reverse=True)

    write_json(output_dir / "h11_output_cosine_per_family.json", per_family_rows)
    write_json(
        output_dir / "h11_output_cosine_summary.json",
        {
            "layer": int(args.layer),
            "probe_layer": int(args.probe_layer),
            "heads": [int(head) for head in args.heads],
            "n_families": len(args.patch_families),
            "head_summaries": head_summaries,
            "headline_interpretation": (
                "Positive delta means a head's last-prompt-token output is more aligned with the layer-16 sensitivity direction "
                "in the most-sensitive variant than in the base variant."
            ),
        },
    )


if __name__ == "__main__":
    main()
