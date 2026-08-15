#!/usr/bin/env python3
"""Stage 11 proximity-gradient analysis for Cue B sensitivity and H11 recovery."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json


NUMBER_PATTERN = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family-csv",
        type=Path,
        default=Path("results/stage6/analysis_d2/stage6_d1_per_family.csv"),
    )
    parser.add_argument(
        "--family-dir",
        type=Path,
        default=Path("results/stage6/generated_full_benchmark"),
    )
    parser.add_argument(
        "--head11-results",
        type=Path,
        default=Path("results/stage10/full_head_sweep_l16/head_11/patching_results.csv"),
    )
    parser.add_argument(
        "--per-variant-preds",
        type=Path,
        default=Path("results/stage10/per_variant_probe_sweep/loo_predictions_per_variant.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/stage11/science/proximity_gradient"),
    )
    return parser.parse_args()


def extract_first_float(value: Any) -> float | None:
    if value is None:
        return None
    match = NUMBER_PATTERN.search(str(value))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2 or len(y) < 2:
        return None
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    if np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return None
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    slp_rows = {}
    with args.family_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("cue_type") != "nongoverning_distractor":
                continue
            slp_rows[str(row["template_id"])] = row

    h11_recovery = {}
    with args.head11_results.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if int(row["patch_layer"]) != 16:
                continue
            h11_recovery[str(row["family_id"])] = float(row["recovery_fraction"])

    per_variant_rows = json.loads(args.per_variant_preds.read_text(encoding="utf-8"))
    family_probe_scores: dict[str, list[float]] = {}
    for row in per_variant_rows:
        if int(row["layer_index"]) != 16:
            continue
        family_probe_scores.setdefault(str(row["template_id"]), []).append(float(row["prediction"]))
    family_probe_scores_mean = {
        family_id: float(np.mean(scores))
        for family_id, scores in family_probe_scores.items()
        if scores
    }

    records: list[dict[str, Any]] = []
    proximity_values: list[float] = []
    h11_values: list[float] = []
    slp_values: list[float] = []
    probe_values: list[float] = []

    for family_id, row in sorted(slp_rows.items()):
        family_path = args.family_dir / f"{family_id}.json"
        if not family_path.exists():
            continue
        payload = json.loads(family_path.read_text(encoding="utf-8"))
        correct_answer = extract_first_float(payload.get("correct_answer"))
        if correct_answer is None or math.isclose(correct_answer, 0.0):
            continue

        variants = payload.get("variants", [])
        if not variants:
            continue
        sensitive_variant_id = None
        if family_id in h11_recovery:
            # Recover the most-sensitive variant from the saved causal CSV when possible.
            with args.head11_results.open("r", encoding="utf-8", newline="") as handle:
                for causal_row in csv.DictReader(handle):
                    if str(causal_row["family_id"]) == family_id and int(causal_row["patch_layer"]) == 16:
                        sensitive_variant_id = int(causal_row["sensitive_variant_id"])
                        break
        if sensitive_variant_id is None:
            sensitive_variant_id = 1
        variant_map = {int(variant["variant_id"]): variant for variant in variants}
        sensitive_variant = variant_map.get(sensitive_variant_id)
        if sensitive_variant is None:
            continue

        cue_value = extract_first_float(sensitive_variant.get("cue_value"))
        if cue_value is None:
            continue
        proximity = abs(cue_value - correct_answer) / max(abs(correct_answer), 1e-8)
        qwen_slp = float(row.get("qwen_S_lp", "0") or "0")
        h11 = h11_recovery.get(family_id)
        probe_score = family_probe_scores_mean.get(family_id)

        record = {
            "template_id": family_id,
            "correct_answer_numeric": float(correct_answer),
            "cue_value_numeric": float(cue_value),
            "proximity": float(proximity),
            "qwen_S_lp": float(qwen_slp),
            "h11_recovery_l16": float(h11) if h11 is not None else None,
            "per_variant_probe_score_l16": float(probe_score) if probe_score is not None else None,
        }
        records.append(record)

        proximity_values.append(float(proximity))
        slp_values.append(float(qwen_slp))
        if h11 is not None:
            h11_values.append(float(h11))
        if probe_score is not None:
            probe_values.append(float(probe_score))

    # Align arrays only over shared rows for each correlation.
    shared_h11 = [(r["proximity"], r["h11_recovery_l16"]) for r in records if r["h11_recovery_l16"] is not None]
    shared_probe = [(r["proximity"], r["per_variant_probe_score_l16"]) for r in records if r["per_variant_probe_score_l16"] is not None]

    proximity_h11_r = pearson([x for x, _ in shared_h11], [y for _, y in shared_h11])
    proximity_slp_r = pearson([r["proximity"] for r in records], [r["qwen_S_lp"] for r in records])
    proximity_probe_r = pearson([x for x, _ in shared_probe], [y for _, y in shared_probe])

    figure, axis = plt.subplots(figsize=(6.5, 4.5))
    xs = [r["proximity"] for r in records]
    ys = [r["qwen_S_lp"] for r in records]
    axis.scatter(xs, ys, alpha=0.8)
    axis.set_xlabel("|distractor - answer| / |answer|")
    axis.set_ylabel("Qwen S_lp")
    axis.set_title("Cue B distractor proximity vs sensitivity")
    figure.tight_layout()
    figure.savefig(args.output_dir / "proximity_vs_slp.png", dpi=200)
    plt.close(figure)

    summary = {
        "n_families": len(records),
        "pearson_r": {
            "proximity_vs_h11_recovery_l16": proximity_h11_r,
            "proximity_vs_qwen_S_lp": proximity_slp_r,
            "proximity_vs_per_variant_probe_l16": proximity_probe_r,
        },
        "records": records,
        "headline_interpretation": (
            "Negative correlation indicates that nearer distractors produce stronger sensitivity and larger H11-mediated causal effects."
        ),
    }
    write_json(args.output_dir / "proximity_gradient_summary.json", summary)


if __name__ == "__main__":
    main()
