#!/usr/bin/env python3
# ruff: noqa: E402
"""Compute calibration bins and ECE for the primary sensitivity probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions",
        default="results/stage6/probing/primary_variance/loo_predictions_variance.json",
    )
    parser.add_argument(
        "--output-dir",
        default="results/stage9/calibration",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions = json.loads(Path(args.predictions).read_text())
    best_layer = max(
        {row["layer_index"] for row in predictions},
        key=lambda layer: __import__("sklearn.metrics").metrics.roc_auc_score(
            [r["true_label"] for r in predictions if r["layer_index"] == layer],
            [r["prediction"] for r in predictions if r["layer_index"] == layer],
        ),
    )
    rows = [row for row in predictions if row["layer_index"] == best_layer]
    scores = np.asarray([row["prediction"] for row in rows], dtype=float)
    labels = np.asarray([row["true_label"] for row in rows], dtype=float)

    bins = np.linspace(0.0, 1.0, 11)
    payload_bins = []
    ece = 0.0
    for left, right in zip(bins[:-1], bins[1:], strict=True):
        if right == 1.0:
            mask = (scores >= left) & (scores <= right)
        else:
            mask = (scores >= left) & (scores < right)
        if not np.any(mask):
            payload_bins.append({"bin_left": float(left), "bin_right": float(right), "count": 0})
            continue
        mean_pred = float(scores[mask].mean())
        mean_true = float(labels[mask].mean())
        count = int(mask.sum())
        ece += abs(mean_pred - mean_true) * (count / len(scores))
        payload_bins.append(
            {
                "bin_left": float(left),
                "bin_right": float(right),
                "count": count,
                "mean_predicted": mean_pred,
                "mean_observed": mean_true,
            }
        )

    plt.figure(figsize=(5, 5))
    xs = [0.5 * (row["bin_left"] + row["bin_right"]) for row in payload_bins if row["count"] > 0]
    ys = [row["mean_observed"] for row in payload_bins if row["count"] > 0]
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.plot(xs, ys, marker="o")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel("Predicted probability")
    plt.ylabel("Observed frequency")
    plt.title(f"Calibration at layer {best_layer}")
    plt.tight_layout()
    plt.savefig(output_dir / "reliability_diagram.png", dpi=200)
    plt.close()

    write_json(
        output_dir / "calibration_summary.json",
        {
            "best_layer": best_layer,
            "ece": float(ece),
            "bins": payload_bins,
        },
    )


if __name__ == "__main__":
    main()
