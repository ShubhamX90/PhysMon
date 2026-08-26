#!/usr/bin/env python3
"""Diagnose why the Stage 12 donor-on-renamed controls produced zero rows.

Job 249460 (`physmon_s12_donren_a1`, gpu_a100_8, 2026-06-21) reported Slurm state
COMPLETED and logged `SAME_ANSWER_DONOR_COMPLETE` with::

    {'rows': 0, 'n_target_families': 10, 'mean_recovery': 0.0, 'median_recovery': 0.0}

Ten target families were loaded, so the target panel was not empty.  Zero rows
were nevertheless emitted, which means donor selection returned no candidate for
any target.  This script instruments the *real* ``select_donors`` predicate --
imported, never re-implemented -- and reports how many donor candidates survive
each successive filter, per target family.

The output identifies which filter empties the panel.  It makes no claim about
the scientific effect: zero evaluable rows are not a measured zero effect, and
this diagnosis does not turn them into one.

CPU-only.  Loads no model and runs no inference.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
for candidate in (str(SRC_ROOT), str(REPO_ROOT / "scripts")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

# Import the production predicate itself so the diagnosis cannot drift from it.
from run_same_answer_donor import (  # noqa: E402
    extract_numeric_value,
    select_donors,
)
from run_behavioural import load_rendered_families  # noqa: E402


# Mirrors the filter order inside select_donors, used only for attribution.
FILTER_ORDER = [
    "same_family_as_target",
    "missing_donor_csv_row",
    "parse_gate",
    "sensitivity_gate_slp_ge_0.3",
    "donor_answer_unparseable",
    "answer_tolerance_gate",
    "survived",
]


def load_family_csv(path: Path) -> dict[str, dict[str, str]]:
    import csv

    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = row.get("template_id") or row.get("family_id") or ""
            if key:
                rows[key] = row
    return rows


def attribute_drops(
    *,
    target_family_id: str,
    target_payloads: dict[str, dict[str, Any]],
    donor_payloads: dict[str, dict[str, Any]],
    donor_rows: dict[str, dict[str, str]],
    tolerance: float,
) -> Counter:
    """Count donor candidates lost at each filter, following select_donors' order."""

    counts: Counter = Counter()
    target_value = extract_numeric_value(str(target_payloads[target_family_id]["correct_answer"]))
    if target_value is None or abs(target_value) < 1e-12:
        counts["target_answer_unusable"] += 1
        return counts

    for family_id, payload in donor_payloads.items():
        if family_id == target_family_id:
            counts["same_family_as_target"] += 1
            continue
        row = donor_rows.get(family_id, {})
        if not row:
            counts["missing_donor_csv_row"] += 1
            continue
        parse_ok = row.get("qwen_parse_ok", "")
        parse_rate = float(row.get("qwen_parse_rate_family", "0") or "0")
        if parse_ok:
            if parse_ok.lower() not in {"true", "1", "yes"}:
                counts["parse_gate"] += 1
                continue
        elif parse_rate < 0.5:
            counts["parse_gate"] += 1
            continue
        slp = float(row.get("qwen_S_lp", "1e9") or "1e9")
        if slp >= 0.3:
            counts["sensitivity_gate_slp_ge_0.3"] += 1
            continue
        answer_value = extract_numeric_value(str(payload["correct_answer"]))
        if answer_value is None:
            counts["donor_answer_unparseable"] += 1
            continue
        if abs(answer_value - target_value) / abs(target_value) > tolerance:
            counts["answer_tolerance_gate"] += 1
            continue
        counts["survived"] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-dir", required=True, help="Target (renamed) family directory.")
    parser.add_argument("--family-csv", required=True, help="Target per-family CSV.")
    parser.add_argument("--donor-family-dir", required=True, help="Donor family directory.")
    parser.add_argument("--donor-family-csv", required=True, help="Donor per-family CSV.")
    parser.add_argument("--answer-tolerance", type=float, default=0.20)
    parser.add_argument("--max-donors-per-family", type=int, default=3)
    parser.add_argument("--output", required=True, help="Destination JSON report.")
    args = parser.parse_args()

    target_payloads = load_rendered_families(Path(args.family_dir))
    donor_payloads = load_rendered_families(Path(args.donor_family_dir))
    donor_rows = load_family_csv(Path(args.donor_family_csv))
    target_rows = load_family_csv(Path(args.family_csv))

    per_target = {}
    aggregate: Counter = Counter()
    disagreements = []

    for target_family_id in sorted(target_payloads):
        counts = attribute_drops(
            target_family_id=target_family_id,
            target_payloads=target_payloads,
            donor_payloads=donor_payloads,
            donor_rows=donor_rows,
            tolerance=args.answer_tolerance,
        )
        # Cross-check the attribution against the production predicate.
        actual = select_donors(
            target_family_id=target_family_id,
            family_payloads=donor_payloads,
            family_rows=donor_rows,
            tolerance=args.answer_tolerance,
            max_donors=args.max_donors_per_family,
        )
        expected_survivors = counts.get("survived", 0)
        if min(expected_survivors, args.max_donors_per_family) != len(actual):
            disagreements.append(
                {
                    "target_family_id": target_family_id,
                    "attributed_survivors": expected_survivors,
                    "select_donors_returned": len(actual),
                }
            )
        per_target[target_family_id] = {
            "target_answer": str(target_payloads[target_family_id].get("correct_answer", "")),
            "drop_attribution": dict(counts),
            "select_donors_returned": actual,
        }
        aggregate.update(counts)

    report = {
        "diagnosis_of": "results/stage12/science/donor_renamed/{same_answer,stable}",
        "source_job_id": "249460",
        "source_job_name": "physmon_s12_donren_a1",
        "n_target_families": len(target_payloads),
        "n_target_csv_rows": len(target_rows),
        "n_donor_families": len(donor_payloads),
        "n_donor_csv_rows": len(donor_rows),
        "answer_tolerance": args.answer_tolerance,
        "aggregate_drop_attribution": dict(aggregate),
        "total_survivors_across_targets": aggregate.get("survived", 0),
        "attribution_matches_production_predicate": not disagreements,
        "disagreements": disagreements,
        "per_target": per_target,
        "interpretation": (
            "Zero evaluable donor rows are not a measured zero effect. This report "
            "identifies the filter that empties the donor panel; it does not license "
            "any specificity or null claim for the renamed-donor controls."
        ),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"targets={len(target_payloads)} donors={len(donor_payloads)} donor_csv_rows={len(donor_rows)}")
    print("aggregate drop attribution (across all targets):")
    for key in FILTER_ORDER:
        if key in aggregate:
            print(f"  {aggregate[key]:6d}  {key}")
    for key, value in aggregate.items():
        if key not in FILTER_ORDER:
            print(f"  {value:6d}  {key}")
    print(f"attribution_matches_production_predicate={not disagreements}")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
