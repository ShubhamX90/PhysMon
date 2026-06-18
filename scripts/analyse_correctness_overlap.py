#!/usr/bin/env python3
# ruff: noqa: E402
"""Analyse overlap and anti-correlation between sensitivity and correctness probes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from scipy.stats import pearsonr

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sensitivity-predictions",
        default="results/stage6/probing/primary_variance/loo_predictions_variance.json",
    )
    parser.add_argument(
        "--correctness-predictions",
        default="results/stage9/baselines/correctness_probe/loo_predictions_variance.json",
    )
    parser.add_argument(
        "--sensitivity-layer-auroc",
        default="results/stage6/probing/primary_variance/layer_auroc_variance.json",
    )
    parser.add_argument(
        "--correctness-layer-auroc",
        default="results/stage9/baselines/correctness_probe/layer_auroc_variance.json",
    )
    parser.add_argument(
        "--output",
        default="results/stage9/correctness_probe/overlap_analysis.json",
    )
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    sens_predictions = load_json(Path(args.sensitivity_predictions))
    corr_predictions = load_json(Path(args.correctness_predictions))
    sens_layer_auroc = load_json(Path(args.sensitivity_layer_auroc))
    corr_layer_auroc = load_json(Path(args.correctness_layer_auroc))

    sens_best = max(sens_layer_auroc, key=lambda item: item["auroc"])
    corr_best = max(corr_layer_auroc, key=lambda item: item["auroc"])

    sens_by_family = {
        row["template_id"]: row for row in sens_predictions if row["layer_index"] == sens_best["layer_index"]
    }
    corr_by_family = {
        row["template_id"]: row for row in corr_predictions if row["layer_index"] == corr_best["layer_index"]
    }
    family_ids = sorted(set(sens_by_family) & set(corr_by_family))

    sens_scores = [float(sens_by_family[family_id]["prediction"]) for family_id in family_ids]
    corr_scores = [float(corr_by_family[family_id]["prediction"]) for family_id in family_ids]
    sens_labels = [int(sens_by_family[family_id]["true_label"]) for family_id in family_ids]
    corr_labels = [int(corr_by_family[family_id]["true_label"]) for family_id in family_ids]

    score_corr = pearsonr(sens_scores, corr_scores)
    label_corr = pearsonr(sens_labels, corr_labels)

    threshold = 0.5
    both_pos = sum(
        s >= threshold and c >= threshold for s, c in zip(sens_scores, corr_scores, strict=True)
    )
    sens_only = sum(
        s >= threshold and c < threshold for s, c in zip(sens_scores, corr_scores, strict=True)
    )
    corr_only = sum(
        s < threshold and c >= threshold for s, c in zip(sens_scores, corr_scores, strict=True)
    )
    both_neg = sum(
        s < threshold and c < threshold for s, c in zip(sens_scores, corr_scores, strict=True)
    )

    sens_only_positive_families = [
        {
            "template_id": family_id,
            "sensitivity_prediction": float(sens_by_family[family_id]["prediction"]),
            "correctness_prediction": float(corr_by_family[family_id]["prediction"]),
            "sensitivity_true_label": int(sens_by_family[family_id]["true_label"]),
            "correctness_true_label": int(corr_by_family[family_id]["true_label"]),
        }
        for family_id in family_ids
        if sens_by_family[family_id]["prediction"] >= 0.9 and corr_by_family[family_id]["prediction"] <= 0.1
    ]

    cm_c_005 = next(item for item in sens_only_positive_families if item["template_id"] == "CM_C_005")

    # Verification invariants from the Stage 9 close-out brief.
    assert abs(score_corr.statistic - (-0.3322919782499855)) < 1e-9
    assert abs(label_corr.statistic - (-0.34641737110744764)) < 1e-9
    assert both_pos == 34
    assert sens_only == 25
    assert corr_only == 64
    assert sens_best["layer_index"] == 18
    assert corr_best["layer_index"] == 24
    assert cm_c_005["sensitivity_true_label"] == 1 and cm_c_005["correctness_true_label"] == 1
    assert cm_c_005["sensitivity_prediction"] >= 0.95
    assert cm_c_005["correctness_prediction"] <= 0.05

    payload = {
        "n_families": len(family_ids),
        "score_pearson": {
            "statistic": float(score_corr.statistic),
            "p_value": float(score_corr.pvalue),
        },
        "label_pearson": {
            "statistic": float(label_corr.statistic),
            "p_value": float(label_corr.pvalue),
        },
        "threshold": threshold,
        "prediction_overlap": {
            "both_positive": both_pos,
            "sensitivity_only": sens_only,
            "correctness_only": corr_only,
            "both_negative": both_neg,
        },
        "best_layers": {
            "sensitivity": sens_best,
            "correctness": corr_best,
        },
        "sensitivity_only_positive_families": sens_only_positive_families,
        "headline_interpretation": (
            "The two probes are anti-correlated "
            f"(score_pearson = {score_corr.statistic:.3f}, label_pearson = {label_corr.statistic:.3f}) "
            "and operate at different network depths (sensitivity L18, correctness L24). "
            "They detect opposite family populations: the sensitivity probe identifies families "
            "where distractor confusion reduces internal confidence; the correctness probe identifies "
            "families the model answers reliably. CM_C_005 (correctly answered, S_lp=13.83 nats) is "
            "the key counter-example — maximal sensitivity detection, near-zero correctness-probe score — "
            "ruling out difficulty as the sole explanation."
        ),
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
