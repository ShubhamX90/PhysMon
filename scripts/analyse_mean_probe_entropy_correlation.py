#!/usr/bin/env python3
"""Compare mean-probe predictions against the entropy proxy baseline."""

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

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-csv", default="results/stage6/analysis_d2/stage6_d1_per_family.csv")
    parser.add_argument("--mean-preds", default="results/stage9/mean_probe_stage6/loo_predictions_resid_post_last_prompt.json")
    parser.add_argument("--entropy-preds", default="results/stage9/baselines/entropy/entropy_per_family_scores.json")
    parser.add_argument("--output", default="results/stage10/mean_probe_entropy_correlation.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mean_rows = json.loads(Path(args.mean_preds).read_text(encoding="utf-8"))
    entropy_rows = json.loads(Path(args.entropy_preds).read_text(encoding="utf-8"))
    with Path(args.family_csv).open("r", encoding="utf-8", newline="") as handle:
        family_rows = {row["template_id"]: row for row in csv.DictReader(handle)}

    mean_by_family = {row["template_id"]: float(row["prediction"]) for row in mean_rows}
    entropy_by_family = {row["template_id"]: float(row["prediction"]) for row in entropy_rows}
    ids = sorted(set(mean_by_family) & set(entropy_by_family))
    mean_scores = np.asarray([mean_by_family[i] for i in ids], dtype=float)
    entropy_scores = np.asarray([entropy_by_family[i] for i in ids], dtype=float)
    labels = np.asarray([1 if float(family_rows[i]["qwen_S_lp"]) >= 0.5 else 0 for i in ids], dtype=int)

    corr = pearsonr(mean_scores, entropy_scores)
    hi_mean_lo_entropy = []
    hi_entropy_lo_mean = []
    for tid in ids:
        m = mean_by_family[tid]
        e = entropy_by_family[tid]
        row = {
            "template_id": tid,
            "mean_probe_prediction": float(m),
            "entropy_prediction": float(e),
            "qwen_S_lp": float(family_rows[tid]["qwen_S_lp"]),
            "cue_type": family_rows[tid]["cue_type"],
            "domain": family_rows[tid]["domain"],
        }
        if m >= 0.7 and e <= 0.3:
            hi_mean_lo_entropy.append(row)
        if e >= 0.7 and m <= 0.3:
            hi_entropy_lo_mean.append(row)

    payload = {
        "n_families": len(ids),
        "pearson_r_scores": float(corr.statistic),
        "pearson_r_scores_p_value": float(corr.pvalue),
        "pearson_r_mean_vs_true_label": float(np.corrcoef(mean_scores, labels)[0, 1]),
        "pearson_r_entropy_vs_true_label": float(np.corrcoef(entropy_scores, labels)[0, 1]),
        "n_divergent_high_mean_low_entropy": len(hi_mean_lo_entropy),
        "n_divergent_high_entropy_low_mean": len(hi_entropy_lo_mean),
        "high_mean_low_entropy_families": hi_mean_lo_entropy,
        "high_entropy_low_mean_families": hi_entropy_lo_mean,
        "interpretation": (
            "substantial divergence between mean probe and entropy proxy"
            if corr.statistic < 0.5
            else "mean probe and entropy proxy are moderately aligned"
        ),
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
