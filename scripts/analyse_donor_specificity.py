#!/usr/bin/env python3
"""Summarise donor-control specificity fractions for the dominant H11 circuit.

Stage 12 brief Part 6 asks for a subtraction-style analysis:

  pure_sensitivity = h11_mhk_recovery - stable_donor_recovery
  sensitivity_fraction = pure_sensitivity / h11_mhk_recovery

This script computes the original-benchmark values and, when available, the
same quantities for the variable-renamed families.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_fraction(h11: float, stable: float) -> dict[str, float]:
    pure = h11 - stable
    frac = pure / h11 if abs(h11) > 1e-9 else 0.0
    return {
        "h11_mean_recovery": float(h11),
        "stable_donor_mean_recovery": float(stable),
        "pure_sensitivity_contribution": float(pure),
        "sensitivity_specific_fraction": float(frac),
    }


def has_evaluable_rows(summary: dict[str, Any]) -> bool:
    return int(summary.get("rows") or 0) > 0 and summary.get("mean_recovery") is not None


def maybe_block(h11_path: Path, same_path: Path, stable_path: Path) -> dict[str, Any] | None:
    if not (h11_path.exists() and same_path.exists() and stable_path.exists()):
        return None

    h11 = load_json(h11_path)
    same = load_json(same_path)
    stable = load_json(stable_path)

    if not has_evaluable_rows(same) or not has_evaluable_rows(stable):
        return {
            "status": "incomplete_empty_result_panel",
            "same_answer_raw_rows": int(same.get("rows") or 0),
            "stable_raw_rows": int(stable.get("rows") or 0),
            "mean_recovery": None,
            "median_recovery": None,
            "scientific_null": False,
            "paper_eligibility": False,
            "interpretation": (
                "The donor-on-renamed controls produced zero evaluable rows. "
                "Their summaries defaulted to zero recovery, so no scientific "
                "null or specificity claim can be made from these runs."
            ),
        }

    block = compute_fraction(
        float(h11["best_mean_recovery_fraction"]),
        float(stable["mean_recovery"]),
    )
    block["same_answer_donor_mean_recovery"] = float(same["mean_recovery"])
    block["same_answer_specificity_ratio_vs_h11"] = (
        float(h11["best_mean_recovery_fraction"]) / float(same["mean_recovery"])
        if abs(float(same["mean_recovery"])) > 1e-9
        else None
    )
    block["stable_specificity_ratio_vs_h11"] = (
        float(h11["best_mean_recovery_fraction"]) / float(stable["mean_recovery"])
        if abs(float(stable["mean_recovery"])) > 1e-9
        else None
    )
    return block


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="results/stage12/science/donor_specificity/donor_specificity_summary.json",
        help="Output JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    original = maybe_block(
        Path("results/stage10/full_head_sweep_l16/head_11/patching_summary.json"),
        Path("results/stage10/same_answer_donor/same_answer_donor_summary.json"),
        Path("results/stage10/stable_donor/stable_donor_summary.json"),
    )
    renamed = maybe_block(
        Path("results/stage11/science/variable_renaming/h11_knockout/patching_summary.json"),
        Path("results/stage12/science/donor_renamed/same_answer/same_answer_donor_summary.json"),
        Path("results/stage12/science/donor_renamed/stable/stable_donor_summary.json"),
    )

    payload = {
        "original_benchmark": original,
        "renamed_families": renamed,
        "notes": {
            "renamed_families": (
                "Pending donor-on-renamed runs"
                if renamed is None
                else "Computed only when donor-on-renamed outputs contain evaluable rows; empty panels are non-reportable."
            )
        },
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
