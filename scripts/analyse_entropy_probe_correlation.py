#!/usr/bin/env python3
# ruff: noqa: E402
"""Compare family-level entropy proxy scores against the primary variance probe."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import pearsonr

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entropy-per-family",
        default="results/stage9/baselines/entropy/entropy_per_family_scores.json",
    )
    parser.add_argument(
        "--probe-predictions",
        default="results/stage6/probing/primary_variance/loo_predictions_variance.json",
    )
    parser.add_argument(
        "--family-csv",
        default="results/stage6/analysis_d2/stage6_d1_per_family.csv",
    )
    parser.add_argument(
        "--output",
        default="results/stage9/baselines/entropy/entropy_vs_probe_correlation.json",
    )
    return parser.parse_args()


def normalize_unit_interval(values: list[float]) -> list[float]:
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return [0.5 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def main() -> None:
    args = parse_args()
    entropy_rows = json.loads(Path(args.entropy_per_family).read_text())
    probe_rows = json.loads(Path(args.probe_predictions).read_text())
    with Path(args.family_csv).open() as handle:
        family_rows = {row["template_id"]: row for row in csv.DictReader(handle)}

    entropy_by_family = {row["template_id"]: row for row in entropy_rows}
    probe_by_family = {
        row["template_id"]: row for row in probe_rows if int(row["layer_index"]) == 18
    }
    family_ids = sorted(set(entropy_by_family) & set(probe_by_family))

    entropy_scores_raw = [float(entropy_by_family[f]["entropy_proxy_score"]) for f in family_ids]
    probe_scores = [float(probe_by_family[f]["prediction"]) for f in family_ids]
    true_labels = [int(probe_by_family[f]["true_label"]) for f in family_ids]
    entropy_scores_norm = normalize_unit_interval(entropy_scores_raw)
    probe_scores_norm = normalize_unit_interval(probe_scores)

    high_probe_low_entropy = []
    high_entropy_low_probe = []
    for family_id, entropy_raw, entropy_norm, probe_score, probe_norm, true_label in zip(
        family_ids,
        entropy_scores_raw,
        entropy_scores_norm,
        probe_scores,
        probe_scores_norm,
        true_labels,
        strict=True,
    ):
        row = {
            "template_id": family_id,
            "cue_type": family_rows[family_id]["cue_type"],
            "domain": family_rows[family_id]["domain"],
            "qwen_S_lp": float(family_rows[family_id]["qwen_S_lp"]),
            "probe_prediction": probe_score,
            "entropy_proxy_score_raw": entropy_raw,
            "entropy_proxy_score_normalized": entropy_norm,
            "true_label": true_label,
        }
        if probe_norm >= 0.6 and entropy_norm <= 0.3:
            high_probe_low_entropy.append(row)
        if entropy_norm >= 0.6 and probe_norm <= 0.3:
            high_entropy_low_probe.append(row)

    latent_family_ids = {"CM_B_STD_003", "CM_C_003", "CM_A_STD_005", "CM_A_STD_010"}
    latent_in_divergent = [
        row["template_id"] for row in high_probe_low_entropy if row["template_id"] in latent_family_ids
    ]

    score_corr = pearsonr(entropy_scores_raw, probe_scores)
    entropy_label_corr = pearsonr(entropy_scores_raw, true_labels)
    probe_label_corr = pearsonr(probe_scores, true_labels)

    interpretation = (
        "near-identical family-level signal"
        if score_corr.statistic > 0.85
        else "shared but meaningfully divergent family-level signal"
        if score_corr.statistic > 0.65
        else "substantial divergence between entropy proxy and variance probe"
    )

    payload = {
        "n_families": len(family_ids),
        "pearson_r_scores": float(score_corr.statistic),
        "pearson_r_scores_p_value": float(score_corr.pvalue),
        "pearson_r_entropy_vs_true_label": float(entropy_label_corr.statistic),
        "pearson_r_probe_vs_true_label": float(probe_label_corr.statistic),
        "high_probe_low_entropy_families": high_probe_low_entropy,
        "high_entropy_low_probe_families": high_entropy_low_probe,
        "n_divergent_high_probe_low_entropy": len(high_probe_low_entropy),
        "n_divergent_high_entropy_low_probe": len(high_entropy_low_probe),
        "deepseek_latent_families_in_divergent_set": latent_in_divergent,
        "interpretation": interpretation,
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
