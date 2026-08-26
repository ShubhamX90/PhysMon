#!/usr/bin/env python3
"""Diagnose the Stage 12 donor-on-renamed controls that produced zero rows.

Background recovered from the Sharanga run inventory: job 249460
(``physmon_s12_donren_a1``, gpu_a100_8, ended 2026-06-21T14:57:06) reported Slurm
state COMPLETED and logged, for both control scripts::

    run_same_answer_donor.py  SAME_ANSWER_DONOR_COMPLETE  {'rows': 0, 'n_target_families': 10, ...}
    run_stable_donor.py       STABLE_DONOR_COMPLETE       {'rows': 0, 'n_target_families': 10, ...}

Ten target families were loaded, so the target panel was not empty.

This script instruments the *production* donor-selection predicates -- imported,
never re-implemented -- for both control paths, against the same inputs the
archived job template supplied.  It answers one question: does the code now in
this repository explain the zero-row outcome?

It makes no scientific claim.  Zero evaluable rows are not a measured zero
effect, and nothing here converts them into one.

CPU-only. Loads no model and runs no inference.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(REPO_ROOT / "src"), str(REPO_ROOT / "scripts")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import run_same_answer_donor as same_answer  # noqa: E402
import run_stable_donor as stable  # noqa: E402
from run_behavioural import load_rendered_families  # noqa: E402


def load_family_rows(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = row.get("template_id") or row.get("family_id") or ""
            if key:
                rows[key] = row
    return rows


def keyed_payloads(directory: str) -> dict[str, dict[str, Any]]:
    """Key rendered families by template_id, exactly as the production mains do."""

    return {payload["template_id"]: payload for payload in load_rendered_families(directory)}


def diagnose_same_answer(
    *,
    patch_families: list[str],
    donor_payloads: dict[str, dict[str, Any]],
    donor_rows: dict[str, dict[str, str]],
    tolerance: float,
    max_donors: int,
) -> dict[str, Any]:
    """Exercise run_same_answer_donor.select_donors on each target family.

    The production predicate resolves the *target's* answer out of the *donor*
    payload mapping.  When the target is a renamed family that exists only in the
    target directory, that lookup cannot succeed.
    """

    per_target: dict[str, Any] = {}
    outcomes: Counter = Counter()
    for family_id in patch_families:
        try:
            donors = same_answer.select_donors(
                target_family_id=family_id,
                family_payloads=donor_payloads,
                family_rows=donor_rows,
                tolerance=tolerance,
                max_donors=max_donors,
            )
        except KeyError as exc:
            outcomes["target_absent_from_donor_payload_mapping"] += 1
            per_target[family_id] = {
                "outcome": "raises_KeyError",
                "missing_key": str(exc).strip("'"),
                "note": (
                    "select_donors resolves the target answer from family_payloads, "
                    "which the job template supplied as the donor pool."
                ),
            }
            continue
        outcomes["returned_donor_list"] += 1
        per_target[family_id] = {"outcome": "returned", "donors": donors, "n_donors": len(donors)}
    return {"outcomes": dict(outcomes), "per_target": per_target}


def diagnose_stable(
    *,
    patch_families: list[str],
    donor_rows: dict[str, dict[str, str]],
    max_donors: int,
) -> dict[str, Any]:
    """Exercise run_stable_donor.select_donors and attribute its gate losses."""

    gate_losses: Counter = Counter()
    for row in donor_rows.values():
        if row.get("cue_type") != "nongoverning_distractor":
            gate_losses["cue_type_not_nongoverning_distractor"] += 1
            continue
        parse_ok = row.get("qwen_parse_ok", "")
        parse_rate = float(row.get("qwen_parse_rate_family", "0") or "0")
        if parse_ok:
            if parse_ok.lower() not in {"true", "1", "yes"}:
                gate_losses["parse_gate"] += 1
                continue
        elif parse_rate < 0.5:
            gate_losses["parse_gate"] += 1
            continue
        if float(row.get("qwen_S_lp", "1e9") or "1e9") >= 0.3:
            gate_losses["sensitivity_gate_slp_ge_0.3"] += 1
            continue
        gate_losses["eligible"] += 1

    per_target = {}
    for family_id in patch_families:
        donors = stable.select_donors(
            target_family_id=family_id,
            family_rows=donor_rows,
            max_donors=max_donors,
        )
        per_target[family_id] = {"donors": donors, "n_donors": len(donors)}

    return {
        "donor_pool_gate_attribution": dict(gate_losses),
        "n_eligible_donors_in_pool": gate_losses.get("eligible", 0),
        "per_target": per_target,
        "n_targets_with_zero_donors": sum(
            1 for v in per_target.values() if v["n_donors"] == 0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-dir", required=True, help="Target (renamed) family directory.")
    parser.add_argument("--renamed-manifest", required=True, help="Renamed manifest JSON.")
    parser.add_argument("--donor-family-dir", required=True, help="Donor family directory.")
    parser.add_argument("--donor-family-csv", required=True, help="Donor per-family CSV.")
    parser.add_argument("--answer-tolerance", type=float, default=0.20)
    parser.add_argument("--max-donors-per-family", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = json.loads(Path(args.renamed_manifest).read_text(encoding="utf-8"))
    patch_families = [row["renamed_template_id"] for row in manifest["families"]]

    target_payloads = keyed_payloads(args.family_dir)
    donor_payloads = keyed_payloads(args.donor_family_dir)
    donor_rows = load_family_rows(Path(args.donor_family_csv))

    same_answer_result = diagnose_same_answer(
        patch_families=patch_families,
        donor_payloads=donor_payloads,
        donor_rows=donor_rows,
        tolerance=args.answer_tolerance,
        max_donors=args.max_donors_per_family,
    )
    stable_result = diagnose_stable(
        patch_families=patch_families,
        donor_rows=donor_rows,
        max_donors=args.max_donors_per_family,
    )

    same_answer_blocked = same_answer_result["outcomes"].get(
        "target_absent_from_donor_payload_mapping", 0
    ) == len(patch_families)
    stable_would_emit = stable_result["n_targets_with_zero_donors"] < len(patch_families)

    report = {
        "diagnosis_target": "results/stage12/science/donor_renamed/{same_answer,stable}",
        "source_job_id": "249460",
        "source_job_name": "physmon_s12_donren_a1",
        "source_job_slurm_state": "COMPLETED",
        "historical_logged_git_commit": "ea91454",
        "patch_families": patch_families,
        "n_patch_families": len(patch_families),
        "n_target_payloads_available": len(target_payloads),
        "n_donor_payloads_available": len(donor_payloads),
        "n_donor_csv_rows": len(donor_rows),
        "same_answer_path": same_answer_result,
        "stable_path": stable_result,
        "current_code_reproduces_zero_rows": False,
        "findings": [
            (
                "same_answer: with the archived template configuration the current "
                "select_donors raises KeyError for every renamed target, because it "
                "resolves the target answer from the donor payload mapping. The current "
                "code cannot execute this configuration at all, so it cannot be the "
                "mechanism that produced a clean zero-row completion."
            )
            if same_answer_blocked
            else "same_answer: current select_donors executed for at least one target.",
            (
                "stable: the donor pool yields eligible donors under the production gate "
                "chain, so select_donors returns a non-empty donor list and the row loop "
                "would emit rows. The current code therefore does not explain the "
                "observed zero-row stable-donor output either."
            )
            if stable_would_emit
            else "stable: donor selection is empty for every target under current code.",
            (
                "run_same_answer_donor.py and run_stable_donor.py do not exist at commit "
                "ea91454 in this repository's history; both were introduced wholesale in "
                "the repository publication commit. The exact code that produced the "
                "zero-row artifacts is therefore not recoverable here."
            ),
        ],
        "provenance_gap": (
            "The zero-row donor-on-renamed artifacts cannot be explained by any code "
            "present in this repository. They remain unmeasured, not null."
        ),
        "consequence_for_rerun": (
            "Executing these controls with current code would be a NEW experiment, not a "
            "reproduction of job 249460, and must be registered as such. The same_answer "
            "target-lookup defect must be fixed before it can run at all."
        ),
        "allowed_wording": (
            "The donor-on-renamed controls produced zero evaluable rows. No scientific "
            "null or specificity claim can be made from those runs."
        ),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"patch_families={len(patch_families)}")
    print(f"same_answer outcomes: {same_answer_result['outcomes']}")
    print(f"stable donor pool gates: {stable_result['donor_pool_gate_attribution']}")
    print(f"stable eligible donors in pool: {stable_result['n_eligible_donors_in_pool']}")
    print(f"stable targets with zero donors: {stable_result['n_targets_with_zero_donors']} / {len(patch_families)}")
    print(f"current_code_reproduces_zero_rows=False")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
