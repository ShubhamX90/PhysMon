#!/usr/bin/env python3
"""Re-score DeepSeek causal patching runs on DeepSeek-valid positive families only."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deepseek-csv",
        default="results/stage8/analysis_deepseek/deepseek_per_family.csv",
    )
    parser.add_argument(
        "--patching-results",
        nargs="+",
        required=True,
        help="One or more patching_results.csv files to re-score.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
    )
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--min-parse-rate", type=float, default=0.5)
    return parser.parse_args()


def load_valid_positive_families(path: Path, *, threshold: float, min_parse_rate: float) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keep = set()
    for row in rows:
        parse_rate = float(row.get("deepseek_parse_rate_family", "0") or "0")
        slp = float(row.get("deepseek_S_lp", "0") or "0")
        if parse_rate >= min_parse_rate and slp >= threshold:
            keep.add(str(row["template_id"]))
    return keep


def summarize_run(csv_path: Path, valid_positive: set[str]) -> dict[str, object]:
    df = pd.read_csv(csv_path)
    family_col = "template_id" if "template_id" in df.columns else "family_id"
    df = df[df[family_col].isin(valid_positive)].copy()
    if df.empty:
        return {
            "patching_results": str(csv_path),
            "n_valid_positive_rows": 0,
            "n_valid_positive_families": 0,
            "best_layer": None,
            "best_mean_recovery_fraction": None,
            "families_gt_50pct": [],
        }

    layer_means = (
        df.groupby("patch_layer", as_index=False)["recovery_fraction"]
        .mean()
        .sort_values("recovery_fraction", ascending=False)
    )
    best_layer = int(layer_means.iloc[0]["patch_layer"])
    best_mean = float(layer_means.iloc[0]["recovery_fraction"])
    best_df = df[df["patch_layer"] == best_layer].copy()
    fam_best = (
        best_df.sort_values([family_col, "recovery_fraction"], ascending=[True, False])
        .drop_duplicates(family_col)
    )
    gt_50 = sorted(
        str(fid)
        for fid in fam_best.loc[fam_best["recovery_fraction"] > 0.5, family_col].tolist()
    )
    return {
        "patching_results": str(csv_path),
        "n_valid_positive_rows": int(len(df)),
        "n_valid_positive_families": int(df[family_col].nunique()),
        "best_layer": best_layer,
        "best_mean_recovery_fraction": best_mean,
        "families_gt_50pct": gt_50,
        "layer_means": [
            {
                "patch_layer": int(row.patch_layer),
                "mean_recovery_fraction": float(row.recovery_fraction),
            }
            for row in layer_means.itertuples(index=False)
        ],
    }


def main() -> None:
    args = parse_args()
    valid_positive = load_valid_positive_families(
        Path(args.deepseek_csv),
        threshold=args.threshold,
        min_parse_rate=args.min_parse_rate,
    )
    payload = {
        "threshold": args.threshold,
        "min_parse_rate": args.min_parse_rate,
        "n_valid_positive_families": len(valid_positive),
        "valid_positive_families": sorted(valid_positive),
        "runs": [
            summarize_run(Path(path), valid_positive)
            for path in args.patching_results
        ],
    }
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)


if __name__ == "__main__":
    main()
