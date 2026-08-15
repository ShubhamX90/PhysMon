#!/usr/bin/env python3
"""Aggregate generic head-sweep outputs of the form head_*/patching_summary.json."""

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
    parser.add_argument("--base-dir", required=True)
    parser.add_argument("--output-path", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    rows = []
    for summary_path in sorted(base_dir.glob("head_*/patching_summary.json")):
        head = int(summary_path.parent.name.split("_")[1])
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        rows.append(
            {
                "head_index": head,
                "best_causal_layer": int(payload["best_causal_layer"]),
                "best_mean_recovery_fraction": float(payload["best_mean_recovery_fraction"]),
                "families_with_gt_50pct_recovery": len(payload["families_with_gt_50pct_recovery"]),
                "families_with_lt_10pct_recovery": len(payload.get("families_with_lt_10pct_recovery", [])),
            }
        )
    if not rows:
        raise FileNotFoundError(f"No head_*/patching_summary.json files found under {base_dir}")
    rows.sort(key=lambda row: row["best_mean_recovery_fraction"], reverse=True)
    by_layer: dict[int, list[dict[str, float]]] = {}
    for row in rows:
        by_layer.setdefault(int(row["best_causal_layer"]), []).append(row)
    payload = {
        "best_overall": rows[0],
        "per_layer_best": {str(layer): layer_rows[0] for layer, layer_rows in by_layer.items()},
        "ranked_results": rows,
    }
    write_json(Path(args.output_path), payload)


if __name__ == "__main__":
    main()
