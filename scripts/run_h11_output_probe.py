#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 11/12 probing over selected single-head outputs.

Supports either a single selected layer or a full layer sweep across all model
layers for one or more heads.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
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


DEFAULT_HEADS = (11, 14, 15, 24)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", default="results/stage6/generated_full_benchmark/")
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument(
        "--sweep-all-layers",
        action="store_true",
        help="Run the selected head-output probes across every layer.",
    )
    parser.add_argument("--heads", nargs="+", type=int, default=list(DEFAULT_HEADS))
    parser.add_argument("--positive-families-file", default="results/stage6/analysis_d2/stage6_positive_families.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_positive_families(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(str(item) for item in payload["positive_families"])


def load_filtered_payloads(family_dir: str | Path) -> list[dict[str, Any]]:
    payloads = load_rendered_families(family_dir)
    return [payload for payload in payloads if payload["template_id"] not in STAGE6_EXCLUDE_FROM_PROBE]


def grouped_loo_masks(family_ids: list[str]) -> list[tuple[np.ndarray, np.ndarray]]:
    fam_arr = np.asarray(family_ids)
    unique = sorted(set(family_ids))
    return [(fam_arr != held_out, fam_arr == held_out) for held_out in unique]


def collect_head_outputs(
    *,
    bundle: Any,
    family_payloads: list[dict[str, Any]],
    layer: int,
    heads: list[int],
) -> tuple[list[str], list[int], dict[int, np.ndarray]]:
    hook_name = f"blocks.{layer}.attn.hook_result"
    by_head: dict[int, list[np.ndarray]] = {int(head): [] for head in heads}
    variant_family_ids: list[str] = []
    variant_ids: list[int] = []
    for family_payload in family_payloads:
        for variant in sorted(family_payload["variants"], key=lambda item: int(item["variant_id"])):
            prompt = format_prompt_with_chat_template(str(variant["prompt"]), bundle.tokenizer)
            prompt_ids = bundle.tokenizer(
                prompt,
                return_tensors="pt",
                add_special_tokens=True,
            ).input_ids.to(next(bundle.hooked_model.parameters()).device)
            _, cache = bundle.hooked_model.run_with_cache(prompt_ids, names_filter=lambda name: name == hook_name)
            head_outputs = cache[hook_name][0]  # (seq, heads, d_model)
            last_pos = int(prompt_ids.shape[1] - 1)
            for head in heads:
                by_head[int(head)].append(head_outputs[last_pos, int(head), :].detach().float().cpu().numpy())
            variant_family_ids.append(str(family_payload["template_id"]))
            variant_ids.append(int(variant["variant_id"]))
    stacked = {head: np.stack(rows, axis=0) for head, rows in by_head.items()}
    return variant_family_ids, variant_ids, stacked


def run_layer_probe(
    *,
    head_outputs: dict[int, np.ndarray],
    layer: int,
    heads: list[int],
    variant_family_ids: list[str],
    variant_ids: list[int],
    positives: set[str],
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    y_variant = np.asarray([int(fid in positives) for fid in variant_family_ids], dtype=int)
    unique_families = sorted(set(variant_family_ids))
    family_truth = np.asarray([int(fid in positives) for fid in unique_families], dtype=int)
    grouped_folds = grouped_loo_masks(variant_family_ids)
    summary_rows = []
    all_predictions = []
    for head in heads:
        x = head_outputs[int(head)]
        per_variant_scores = []
        per_variant_truth = []
        for train_mask, test_mask in grouped_folds:
            scaler = StandardScaler().fit(x[train_mask])
            x_train = scaler.transform(x[train_mask])
            x_test = scaler.transform(x[test_mask])
            clf = LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=seed,
            )
            clf.fit(x_train, y_variant[train_mask])
            scores = clf.predict_proba(x_test)[:, 1]
            per_variant_scores.extend(float(score) for score in scores)
            per_variant_truth.extend(int(value) for value in y_variant[test_mask])

        family_mean_scores = []
        for family_id in unique_families:
            scores = [
                score
                for fid, score in zip(variant_family_ids, per_variant_scores, strict=True)
                if fid == family_id
            ]
            family_mean_scores.append(float(np.mean(scores)))
        family_auroc = float(roc_auc_score(family_truth, family_mean_scores))
        family_auprc = float(average_precision_score(family_truth, family_mean_scores))
        variant_auroc = float(roc_auc_score(per_variant_truth, per_variant_scores))
        variant_auprc = float(average_precision_score(per_variant_truth, per_variant_scores))
        summary_rows.append(
            {
                "head_index": int(head),
                "layer_index": int(layer),
                "family_mean_auroc": family_auroc,
                "family_mean_auprc": family_auprc,
                "per_variant_auroc": variant_auroc,
                "per_variant_auprc": variant_auprc,
            }
        )
        for family_id, variant_id, score, truth in zip(
            variant_family_ids,
            variant_ids,
            per_variant_scores,
            per_variant_truth,
            strict=True,
        ):
            all_predictions.append(
                {
                    "head_index": int(head),
                    "layer_index": int(layer),
                    "template_id": family_id,
                    "variant_id": int(variant_id),
                    "prediction": float(score),
                    "true_label": int(truth),
                }
            )
    return summary_rows, all_predictions


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    positives = load_positive_families(Path(args.positive_families_file))
    resolved_spec = resolve_model_spec(model_key=args.model_role)
    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Head-output probing currently requires TransformerLens support.")
    bundle.hooked_model.set_use_attn_result(True)

    family_payloads = load_filtered_payloads(args.family_dir)
    layer_indices = (
        list(range(int(bundle.hooked_model.cfg.n_layers)))
        if args.sweep_all_layers
        else [int(args.layer)]
    )
    summary_rows = []
    all_predictions = []
    for layer in layer_indices:
        variant_family_ids, variant_ids, head_outputs = collect_head_outputs(
            bundle=bundle,
            family_payloads=family_payloads,
            layer=int(layer),
            heads=list(args.heads),
        )
        layer_summary_rows, layer_predictions = run_layer_probe(
            head_outputs=head_outputs,
            layer=int(layer),
            heads=list(args.heads),
            variant_family_ids=variant_family_ids,
            variant_ids=variant_ids,
            positives=positives,
            seed=args.seed,
        )
        summary_rows.extend(layer_summary_rows)
        all_predictions.extend(layer_predictions)

    summary_rows.sort(key=lambda row: (row["head_index"], -row["family_mean_auroc"], row["layer_index"]))
    write_json(output_dir / "head_output_probe_summary.json", summary_rows)
    write_json(output_dir / "head_output_probe_predictions.json", all_predictions)
    if args.sweep_all_layers:
        best_by_head = []
        for head in sorted(set(int(row["head_index"]) for row in summary_rows)):
            rows = [row for row in summary_rows if int(row["head_index"]) == head]
            best = max(rows, key=lambda row: row["family_mean_auroc"])
            best_by_head.append(best)
        best_by_head.sort(key=lambda row: row["family_mean_auroc"], reverse=True)
        write_json(output_dir / "head_output_probe_best_by_head.json", best_by_head)


if __name__ == "__main__":
    main()
