#!/usr/bin/env python3
"""Aggregate the clean Llama head-by-layer selection sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-dir",
        default="results/stage10/llama_head_selection_sweep",
    )
    parser.add_argument(
        "--output-path",
        default="results/stage10/llama_head_selection_sweep/head_selection_summary.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    results = []
    for summary_path in sorted(base_dir.glob("layer_*/head_*/patching_summary.json")):
        parts = summary_path.parts
        layer = int(parts[-3].split("_")[1])
        head = int(parts[-2].split("_")[1])
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        results.append(
            {
                "layer_index": layer,
                "head_index": head,
                "best_mean_recovery_fraction": float(payload["best_mean_recovery_fraction"]),
                "best_causal_layer": int(payload["best_causal_layer"]),
                "families_with_gt_50pct_recovery": len(payload["families_with_gt_50pct_recovery"]),
            }
        )
    if not results:
        raise FileNotFoundError(f"No patching summaries found under {base_dir}.")

    results.sort(key=lambda row: row["best_mean_recovery_fraction"], reverse=True)
    by_layer: dict[int, list[dict[str, float]]] = {}
    for row in results:
        by_layer.setdefault(int(row["layer_index"]), []).append(row)

    payload = {
        "best_overall": results[0],
        "per_layer_best": {
            str(layer): rows[0]
            for layer, rows in by_layer.items()
        },
        "ranked_results": results,
    }
    write_json(Path(args.output_path), payload)


if __name__ == "__main__":
    main()
