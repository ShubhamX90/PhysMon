#!/usr/bin/env python3
"""Summarize Stage 5.1 follow-up artifacts into one comparative JSON.

Reference:
    Stage 5 follow-up brief v5.1 Part E.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_TIER1_SUMMARY = "results/stage5/probing/summary_resid_post_last_prompt.json"
DEFAULT_TIER1_LOO = "results/stage5/probing/loo_predictions_resid_post_last_prompt.json"
DEFAULT_TIER2_SUMMARY = "results/stage5/probing_tier2/summary_resid_post_cue_token.json"
DEFAULT_TIER2_LOO = "results/stage5/probing_tier2/loo_predictions_resid_post_cue_token.json"
DEFAULT_CONTRAST_SUMMARY = "results/stage5/probing/summary_contrast.json"
DEFAULT_PCA50_SUMMARY = "results/stage5/probing/summary_pca50.json"
DEFAULT_SURFACE_BASELINE = "results/stage5/baselines_repair_v2/surface_tfidf_logistic_slp_binary.json"
DEFAULT_OUTPUT = "results/stage5/followup_comparison.json"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 5.1 comparative summary."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier1-summary", default=DEFAULT_TIER1_SUMMARY)
    parser.add_argument("--tier1-loo", default=DEFAULT_TIER1_LOO)
    parser.add_argument("--tier2-summary", default=DEFAULT_TIER2_SUMMARY)
    parser.add_argument("--tier2-loo", default=DEFAULT_TIER2_LOO)
    parser.add_argument("--contrast-summary", default=DEFAULT_CONTRAST_SUMMARY)
    parser.add_argument("--pca50-summary", default=DEFAULT_PCA50_SUMMARY)
    parser.add_argument("--surface-baseline", default=DEFAULT_SURFACE_BASELINE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_json(path: str) -> dict[str, Any]:
    """Load one JSON file."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def extract_cm_b006_prediction(path: str) -> float:
    """Return the family-level LOO prediction for `CM_B_006`."""

    payload = load_json(path)
    for row in payload:
        if row["template_id"] == "CM_B_006":
            return float(row["prediction"])
    raise KeyError(f"CM_B_006 was not found in {path}.")


def main() -> None:
    """Write the Stage 5.1 comparative summary JSON."""

    args = parse_args()
    tier1_summary = load_json(args.tier1_summary)
    tier2_summary = load_json(args.tier2_summary)
    contrast_summary = load_json(args.contrast_summary)
    pca50_summary = load_json(args.pca50_summary)
    surface_baseline = load_json(args.surface_baseline)

    payload = {
        "tier1_best_auroc": float(tier1_summary["best_auroc"]),
        "tier1_best_layer": int(tier1_summary["best_layer"]),
        "tier2_best_auroc": float(tier2_summary["best_auroc"]),
        "tier2_best_layer": int(tier2_summary["best_layer"]),
        "contrast_probe_best_auroc": float(contrast_summary["best_auroc"]),
        "pca50_tier1_best_auroc": float(pca50_summary["best_auroc"]),
        "cm_b006_tier1_prediction": extract_cm_b006_prediction(args.tier1_loo),
        "cm_b006_tier2_prediction": extract_cm_b006_prediction(args.tier2_loo),
        "surface_baseline_auroc": float(surface_baseline["results_by_model"]["qwen"]["auroc"]),
        "random_direction_p95": float(
            tier1_summary["random_direction_baseline"]["p95_auroc"]
        ),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
