#!/usr/bin/env python3
"""Incremental information of hidden states over non-activation evidence (§8.4).

Part II §8.4 states the decisive question directly: "The critical question is not
merely which standalone model has the largest AUROC. It is whether hidden states
improve prediction and calibration beyond all information available without
activation access."

This script runs that three-way comparison:

1.  the combined non-activation baseline;
2.  the prompt-side hidden-state monitor;
3.  both together.

Every difference is reported with a **paired** family bootstrap, resampling the
same families for both models on each iteration. Comparing two independently
bootstrapped intervals is a weaker and different test, and it is not what §8.4
asks for.

The combination model is fit under the same nested family-level cross-validation
as the baseline, so its score is out-of-fold rather than in-sample.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from physmon.probing.metrics import (  # noqa: E402
    compute_auprc,
    compute_auroc,
    compute_brier,
    compute_ece,
    compute_fnr_at_fpr,
    paired_bootstrap_difference,
)
from run_combined_baseline import nested_cv_predictions  # noqa: E402

MONITOR_SOURCE = "results/stage10/mean_probe_full_sweep_bigcompute/loo_predictions_resid_post_last_prompt.json"

# The strongest single non-activation comparator that is already an out-of-fold
# prediction on this exact panel, so it can be paired with the monitor directly
# without refitting either model.
ENTROPY_SOURCE = "results/stage9/baselines/entropy/entropy_per_family_scores.json"


def load_json(rel_path: str | Path) -> Any:
    path = Path(rel_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return json.loads(path.read_text(encoding="utf-8"))


def metrics_for(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    return {
        "auroc": round(compute_auroc(labels, scores), 4),
        "auprc": round(compute_auprc(labels, scores), 4),
        "brier": round(compute_brier(labels, scores), 4),
        "ece": round(compute_ece(labels, scores), 4),
        "fnr_at_fpr_0.10": round(compute_fnr_at_fpr(labels, scores, 0.10), 4),
        "fnr_at_fpr_0.20": round(compute_fnr_at_fpr(labels, scores, 0.20), 4),
    }


def risk_coverage(labels: np.ndarray, scores: np.ndarray, points: int = 10) -> list[dict[str, float]]:
    """Error rate among the most-confident fraction of families."""

    order = np.argsort(-np.abs(scores - 0.5))  # most confident first
    curve = []
    for step in range(1, points + 1):
        k = max(1, int(len(labels) * step / points))
        idx = order[:k]
        predicted = (scores[idx] >= 0.5).astype(int)
        curve.append(
            {
                "coverage": round(k / len(labels), 3),
                "error_rate": round(float((predicted != labels[idx]).mean()), 4),
                "n": int(k),
            }
        )
    return curve


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combined-predictions", default="results/wave2/combined_baseline/combined_baseline_predictions.json")
    parser.add_argument("--outer-folds", type=int, default=5)
    parser.add_argument("--inner-folds", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-reps", type=int, default=10000)
    parser.add_argument("--output-dir", default="results/wave2/incremental_information")
    args = parser.parse_args()

    combined_rows = load_json(args.combined_predictions)
    combined_by_family = {r["template_id"]: float(r["prediction"]) for r in combined_rows}
    label_by_family = {r["template_id"]: int(r["true_label"]) for r in combined_rows}

    monitor_rows = load_json(MONITOR_SOURCE)
    monitor_by_family = {str(r["template_id"]): float(r["prediction"]) for r in monitor_rows}

    families = sorted(set(combined_by_family) & set(monitor_by_family))
    labels = np.array([label_by_family[f] for f in families], dtype=int)
    combined = np.array([combined_by_family[f] for f in families], dtype=float)
    monitor = np.array([monitor_by_family[f] for f in families], dtype=float)

    # Model 3: both sources of evidence, fit out-of-fold under the same scheme.
    stacked = np.column_stack([combined, monitor])
    both, chosen = nested_cv_predictions(
        stacked, labels, args.outer_folds, args.inner_folds,
        [0.01, 0.1, 1.0, 10.0, 100.0], args.seed,
    )

    entropy_rows = load_json(ENTROPY_SOURCE)
    entropy_by_family = {str(r["template_id"]): float(r["prediction"]) for r in entropy_rows}
    entropy = np.array([entropy_by_family[f] for f in families], dtype=float)

    models = {
        "combined_non_activation": combined,
        "entropy_fitted_baseline": entropy,
        "hidden_state_monitor": monitor,
        "combined_plus_hidden_state": both,
    }

    comparisons = {
        "monitor_minus_combined": ("hidden_state_monitor", "combined_non_activation"),
        "both_minus_combined": ("combined_plus_hidden_state", "combined_non_activation"),
        "both_minus_monitor": ("combined_plus_hidden_state", "hidden_state_monitor"),
        "monitor_minus_entropy": ("hidden_state_monitor", "entropy_fitted_baseline"),
    }

    paired: dict[str, Any] = {}
    for name, (a, b) in comparisons.items():
        entry: dict[str, Any] = {}
        for metric in ("auroc", "auprc", "brier"):
            result = paired_bootstrap_difference(
                labels, models[a], models[b], metric=metric,
                n_resamples=args.bootstrap_reps, seed=args.seed,
            )
            result["excludes_zero"] = bool(
                (result["ci95_low"] > 0) or (result["ci95_high"] < 0)
            )
            entry[metric] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in result.items()}
        paired[name] = entry

    headline = paired["monitor_minus_combined"]["auroc"]
    if headline["excludes_zero"] and headline["observed_difference"] > 0:
        verdict = (
            "Hidden states add information beyond the combined non-activation baseline "
            "on this panel: the paired interval excludes zero."
        )
    elif headline["excludes_zero"]:
        verdict = "The combined non-activation baseline beats the monitor; the paired interval excludes zero."
    else:
        verdict = (
            "The paired interval includes zero. Hidden states are NOT demonstrated to add "
            "information beyond the combined non-activation baseline on this panel. Part II "
            "§22.3 directs reframing the monitor as a compact internal proxy rather than a "
            "superior detector if this holds."
        )

    summary = {
        "analysis": "incremental_information_of_hidden_states",
        "reference": "PhysMon Part II 8.4",
        "n_families": len(families),
        "n_positive": int((labels == 1).sum()),
        "n_negative": int((labels == 0).sum()),
        "resampling_unit": "canonical_family",
        "bootstrap": {"seed": args.seed, "resamples": args.bootstrap_reps, "paired": True},
        "combination_cv": {
            "scheme": "nested_stratified_family_level",
            "outer_folds": args.outer_folds,
            "inner_folds": args.inner_folds,
            "selected_C_per_outer_fold": chosen,
        },
        "model_metrics": {name: metrics_for(labels, scores) for name, scores in models.items()},
        "paired_differences": paired,
        "risk_coverage": {name: risk_coverage(labels, scores) for name, scores in models.items()},
        "verdict": verdict,
        "strongest_non_activation_comparator": {
            "name": "entropy_fitted_baseline",
            "auroc": round(compute_auroc(labels, entropy), 4),
            "note": (
                "The published fitted entropy baseline outscores the combined raw "
                "non-activation model on this panel, so the combined model is not the "
                "strongest available non-activation comparator. A stronger baseline "
                "would narrow the monitor's margin further, not widen it."
            ),
        },
        "status": "complete_exploratory",
        "experiment_class": "exploratory_unfrozen",
        "paper_eligibility": False,
        "note": (
            "Discovery-tier. The monitor layer, threshold and panel were selected on "
            "these same families in earlier stages; this is not a confirmatory result."
        ),
    }

    output_dir = REPO_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "incremental_information_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary["model_metrics"], indent=2))
    for name, entry in paired.items():
        auroc = entry["auroc"]
        print(
            f"{name}: dAUROC={auroc['observed_difference']:+.4f} "
            f"CI[{auroc['ci95_low']:+.4f},{auroc['ci95_high']:+.4f}] "
            f"excludes_zero={auroc['excludes_zero']}"
        )
    print("\nVERDICT:", verdict)


if __name__ == "__main__":
    main()
