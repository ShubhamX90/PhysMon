#!/usr/bin/env python3
"""Aggregate pairwise head-interaction runs at layer 16."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-dir",
        default="results/stage10/pairwise_head_interactions",
    )
    parser.add_argument(
        "--heads",
        nargs="+",
        type=int,
        default=[26, 24, 13, 11],
    )
    parser.add_argument(
        "--output-path",
        default="results/stage10/pairwise_head_interactions/interaction_summary.json",
    )
    return parser.parse_args()


def subset_name(heads: tuple[int, ...]) -> str:
    return "_".join(str(head) for head in heads)


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    subset_results: dict[tuple[int, ...], float] = {}
    for summary_path in sorted(base_dir.glob("subset_*/patching_summary.json")):
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        subset = tuple(int(head) for head in payload["multi_head_knockout"])
        subset_results[subset] = float(payload["best_mean_recovery_fraction"])
    if not subset_results:
        raise FileNotFoundError(f"No pairwise interaction results found under {base_dir}.")

    heads = [int(head) for head in args.heads]
    matrix = []
    synergy_over_best_single = []
    for left in heads:
        matrix_row = {"head_index": left, "recoveries": {}}
        synergy_row = {"head_index": left, "synergy_over_best_single": {}}
        single_left = subset_results.get((left,), np.nan)
        for right in heads:
            if left == right:
                pair_value = single_left
                synergy_value = 0.0
            else:
                subset = tuple(sorted((left, right), reverse=False))
                pair_value = subset_results.get(subset, np.nan)
                single_right = subset_results.get((right,), np.nan)
                synergy_value = float(pair_value - max(single_left, single_right))
            matrix_row["recoveries"][str(right)] = None if np.isnan(pair_value) else float(pair_value)
            synergy_row["synergy_over_best_single"][str(right)] = None if np.isnan(synergy_value) else float(synergy_value)
        matrix.append(matrix_row)
        synergy_over_best_single.append(synergy_row)

    subset_rows = [
        {
            "subset": list(subset),
            "subset_name": subset_name(subset),
            "best_mean_recovery_fraction": float(value),
        }
        for subset, value in sorted(subset_results.items(), key=lambda item: (len(item[0]), item[0]))
    ]
    payload = {
        "heads": heads,
        "subset_results": subset_rows,
        "pairwise_recovery_matrix": matrix,
        "pairwise_synergy_over_best_single": synergy_over_best_single,
    }
    write_json(Path(args.output_path), payload)


if __name__ == "__main__":
    main()
