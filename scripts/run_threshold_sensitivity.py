#!/usr/bin/env python3
"""Stage 9 threshold sensitivity sweep over saved LOO probe predictions."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_auc_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loo-predictions", required=True, help="Saved family-level LOO prediction JSON.")
    parser.add_argument("--family-csv", required=True, help="Per-family CSV containing qwen_S_lp values.")
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        required=True,
        help="Thresholds in nats at which to relabel S_lp as binary.",
    )
    parser.add_argument(
        "--exclude-ids",
        nargs="*",
        default=(),
        help="Template ids to exclude from the sweep.",
    )
    parser.add_argument(
        "--slp-column",
        default="qwen_S_lp",
        help="Continuous S_lp column to threshold. Default: qwen_S_lp.",
    )
    parser.add_argument(
        "--compare-baseline",
        default=None,
        help=(
            "Optional baseline summary JSON. If provided, the relevant AUROC is recorded as a "
            "reference line; this file does not contain per-family scores."
        ),
    )
    parser.add_argument("--output-dir", required=True, help="Directory for threshold sweep outputs.")
    parser.add_argument("--stage", type=int, default=9, help="Scientific stage number for metadata.")
    return parser.parse_args()


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_predictions(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError(f"Expected a list of prediction rows in {path}, found {type(payload).__name__}.")
    return {str(row["template_id"]): float(row["prediction"]) for row in payload}


def load_slp_values(path: Path, *, slp_column: str, exclude_ids: set[str]) -> dict[str, float]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle)
        result: dict[str, float] = {}
        for row in rows:
            template_id = str(row["template_id"])
            if template_id in exclude_ids:
                continue
            if slp_column not in row:
                raise KeyError(f"Column {slp_column!r} not found in {path}.")
            result[template_id] = float(row[slp_column] or 0.0)
    return result


def baseline_reference_auroc(path: Path | None) -> float | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_model = payload.get("results_by_model", {})
    for key in ("qwen", "deepseek", "llama"):
        if key in by_model and by_model[key].get("status") == "ok":
            return float(by_model[key]["auroc"])
    return None


def run_threshold_sweep(
    predictions: dict[str, float],
    slp_values: dict[str, float],
    thresholds: list[float],
) -> list[dict[str, Any]]:
    shared_ids = sorted(set(predictions) & set(slp_values))
    results: list[dict[str, Any]] = []
    for threshold in thresholds:
        labels = np.asarray([int(slp_values[template_id] >= threshold) for template_id in shared_ids], dtype=int)
        scores = np.asarray([predictions[template_id] for template_id in shared_ids], dtype=float)
        n_positive = int(labels.sum())
        n_negative = int(labels.size - n_positive)
        row: dict[str, Any] = {
            "threshold": float(threshold),
            "n_positive": n_positive,
            "n_negative": n_negative,
        }
        if n_positive < 5 or n_negative < 5:
            row["auroc"] = None
            row["note"] = "skipped_too_few_examples"
        else:
            row["auroc"] = float(roc_auc_score(labels, scores))
        results.append(row)
    return results


def plot_threshold_curve(
    sweep_rows: list[dict[str, Any]],
    output_path: Path,
    *,
    baseline_auroc: float | None,
) -> None:
    valid_rows = [row for row in sweep_rows if row.get("auroc") is not None]
    thresholds = [row["threshold"] for row in valid_rows]
    aurocs = [row["auroc"] for row in valid_rows]

    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(thresholds, aurocs, marker="o", label="Variance probe")
    axis.axvline(0.5, linestyle="--", color="black", alpha=0.6, label="Pre-registered tau=0.5")
    if baseline_auroc is not None:
        axis.axhline(
            baseline_auroc,
            linestyle=":",
            color="tab:red",
            alpha=0.8,
            label=f"Baseline reference ({baseline_auroc:.3f})",
        )
    axis.set_xlabel("Threshold tau (nats)")
    axis.set_ylabel("AUROC")
    axis.set_title("Stage 9 Threshold Sensitivity")
    axis.legend(loc="best")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    predictions = load_predictions(Path(args.loo_predictions))
    slp_values = load_slp_values(
        Path(args.family_csv),
        slp_column=args.slp_column,
        exclude_ids=set(args.exclude_ids),
    )
    baseline_auroc = baseline_reference_auroc(Path(args.compare_baseline)) if args.compare_baseline else None
    sweep_rows = run_threshold_sweep(predictions, slp_values, list(args.thresholds))
    valid_aurocs = [row["auroc"] for row in sweep_rows if row.get("auroc") is not None]
    summary = {
        "stage": args.stage,
        "slp_column": args.slp_column,
        "thresholds": list(args.thresholds),
        "baseline_reference_auroc": baseline_auroc,
        "auroc_min": float(min(valid_aurocs)) if valid_aurocs else None,
        "auroc_max": float(max(valid_aurocs)) if valid_aurocs else None,
        "max_variation": float(max(valid_aurocs) - min(valid_aurocs)) if len(valid_aurocs) >= 2 else 0.0,
        "rows": sweep_rows,
    }

    save_json(output_dir / "threshold_sweep.json", sweep_rows)
    save_json(output_dir / "threshold_sweep_summary.json", summary)
    plot_threshold_curve(
        sweep_rows,
        output_dir / "threshold_auroc_curve.png",
        baseline_auroc=baseline_auroc,
    )


if __name__ == "__main__":
    main()
