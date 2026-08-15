#!/usr/bin/env python3
"""Aggregate per-head results from the Stage 10 full L16 head sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="results/stage10/full_head_sweep_l16")
    parser.add_argument("--output", default="results/stage10/full_head_sweep_l16/head_sweep_summary.json")
    return parser.parse_args()


def load_head_summary(path: Path) -> dict[str, Any] | None:
    summary_path = path / "patching_summary.json"
    if not summary_path.exists():
        return None
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    return {
        "head_index": int(path.name.split("_")[-1]),
        "best_layer": int(payload["best_causal_layer"]),
        "best_mean_recovery_fraction": float(payload["best_mean_recovery_fraction"]),
        "gt_50pct_family_count": len(payload.get("families_with_gt_50pct_recovery", [])),
        "lt_10pct_family_count": len(payload.get("families_with_lt_10pct_recovery", [])),
    }


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    summaries = []
    for path in sorted(input_dir.glob("head_*")):
        loaded = load_head_summary(path)
        if loaded is not None:
            summaries.append(loaded)

    summaries.sort(key=lambda row: row["best_mean_recovery_fraction"], reverse=True)
    active_heads = [row for row in summaries if row["best_mean_recovery_fraction"] > 0.10]
    payload = {
        "n_heads_completed": len(summaries),
        "top_heads": summaries[:10],
        "heads_gt_10pct_recovery": [row["head_index"] for row in active_heads],
        "active_head_count": len(active_heads),
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
