#!/usr/bin/env python3
# ruff: noqa: E402
"""Compute sensitivity-probe AUROC separately for each cue type."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

from sklearn.metrics import roc_auc_score

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
        "--family-csv",
        default="results/stage6/analysis_d2/stage6_d1_per_family.csv",
    )
    parser.add_argument(
        "--output",
        default="results/stage9/per_cue_type/cue_type_auroc_breakdown.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predictions = json.loads(Path(args.predictions).read_text())
    with Path(args.family_csv).open() as handle:
        family_rows = {row["template_id"]: row for row in csv.DictReader(handle)}

    best_layer = max(
        {row["layer_index"] for row in predictions},
        key=lambda layer: roc_auc_score(
            [r["true_label"] for r in predictions if r["layer_index"] == layer],
            [r["prediction"] for r in predictions if r["layer_index"] == layer],
        ),
    )
    selected = [row for row in predictions if row["layer_index"] == best_layer]

    payload: dict[str, object] = {
        "best_layer": best_layer,
        "cue_types": {},
    }
    for cue_type in sorted({family_rows[row["template_id"]]["cue_type"] for row in selected}):
        rows = [row for row in selected if family_rows[row["template_id"]]["cue_type"] == cue_type]
        y_true = [row["true_label"] for row in rows]
        y_score = [row["prediction"] for row in rows]
        if len(set(y_true)) < 2:
            auroc = None
        else:
            auroc = float(roc_auc_score(y_true, y_score))
        payload["cue_types"][cue_type] = {
            "n_families": len(rows),
            "n_positive": int(sum(y_true)),
            "auroc": auroc,
        }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
