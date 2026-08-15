#!/usr/bin/env python3
"""Analyse Cue B distractor proximity against S_lp."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-csv", default="results/stage6/analysis_d2/stage6_d1_per_family.csv")
    parser.add_argument("--generated-dir", default="results/stage6/generated_full_benchmark")
    parser.add_argument("--output", default="results/stage10/distractor_proximity/proximity_vs_slp.json")
    return parser.parse_args()


def parse_num(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    match = NUM_RE.search(str(value))
    return float(match.group(0)) if match else math.nan


def main() -> None:
    args = parse_args()
    with Path(args.family_csv).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cue_b_rows = [row for row in rows if row["cue_type"] == "nongoverning_distractor"]

    results = []
    for row in cue_b_rows:
        path = Path(args.generated_dir) / f"{row['template_id']}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        correct = parse_num(payload.get("correct_answer"))
        if correct == 0 or math.isnan(correct):
            continue
        proximities = []
        for variant in payload.get("variants", []):
            cue = parse_num(variant.get("cue_value"))
            if math.isnan(cue):
                continue
            proximities.append(abs(cue - correct) / abs(correct))
        if not proximities:
            continue
        results.append(
            {
                "template_id": row["template_id"],
                "domain": row["domain"],
                "qwen_S_lp": float(row["qwen_S_lp"]),
                "min_relative_proximity": float(min(proximities)),
                "mean_relative_proximity": float(np.mean(proximities)),
                "correct_answer_numeric": float(correct),
            }
        )

    slp = np.asarray([r["qwen_S_lp"] for r in results], dtype=float)
    prox = np.asarray([r["min_relative_proximity"] for r in results], dtype=float)
    payload = {
        "n_families": len(results),
        "pearson_r_slp_vs_min_relative_proximity": float(np.corrcoef(slp, prox)[0, 1]) if len(results) > 1 else None,
        "families": sorted(results, key=lambda r: r["qwen_S_lp"], reverse=True),
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
