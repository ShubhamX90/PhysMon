#!/usr/bin/env python3
"""Write the Stage 13 Wave 0 and Wave 1A v7 gate reports.

Design rule, taken from the closing instruction of the v6 brief: do not optimize
for a green gate.  Three v6 checks passed on form rather than substance --
``claim_matrix_populated`` passed while every claim had an empty artifact list,
``run_crosswalk_substantive`` passed at 4.5% coverage on a fabricated
denominator, and ``canonical_evidence_multimodel`` passed with 185 of 465 rows
null and only one field populated.

The v7 gate applies the stricter criterion to each of those checks.  Where the
underlying v7 artifact has not been rebuilt yet, the check fails and says so
rather than inheriting the v6 pass.  A gate that reports outstanding work is the
intended output, not a defect.

Each check records which artifact version it was computed from, so a reader can
tell a v7 result from a carried-forward v6 one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_utils import REPO_ROOT, git_info, sha256_file, write_json  # noqa: E402


def load(path: str) -> dict[str, Any] | None:
    resolved = REPO_ROOT / path
    if not resolved.exists():
        return None
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def check(
    check_id: str,
    passed: bool,
    detail: str,
    source: str,
    criterion: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": bool(passed),
        "detail": detail,
        "computed_from": source,
        "criterion": criterion,
    }


def build_wave0() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    rule_path = REPO_ROOT / "docs/proposals/PhysMon_Part_II_governing_document_rule.md"
    rule_text = rule_path.read_text(encoding="utf-8") if rule_path.exists() else ""
    checks.append(
        check(
            "governing_document_rule_correct",
            bool(rule_text) and "v1.1" in rule_text and "erratum" in rule_text.lower(),
            "rule names complete v1.1 plus the erratum" if rule_text else "rule file missing",
            "docs/proposals/PhysMon_Part_II_governing_document_rule.md",
            "Rule must name the complete Part II v1.1 read together with the erratum.",
        )
    )

    coverage = load("results/stage13/wave0/registry_coverage_v7.json")
    if coverage is None:
        checks.append(
            check(
                "run_crosswalk_real_denominator", False,
                "registry_coverage_v7.json absent", "missing",
                "Expected runs must come from evidence that a job executed.",
            )
        )
    else:
        real_source = coverage.get("denominator_source") == "sharanga_slurm_logs_joined_to_sacct"
        checks.append(
            check(
                "run_crosswalk_real_denominator",
                real_source and coverage.get("n_expected_science_runs", 0) > 0,
                f"{coverage.get('n_expected_science_runs')} science runs from real Slurm IDs; "
                f"coverage {coverage.get('coverage_fraction')} "
                f"(strict {coverage.get('strict_coverage_fraction')})",
                "results/stage13/wave0/registry_coverage_v7.json",
                "Denominator must be jobs with real Slurm identities, not globbed filenames.",
            )
        )

    authority = load("docs/registry/artifact_authority_audit_v7.json")
    if authority is None:
        checks.append(
            check("critical_authority_zero", False, "artifact_authority_audit_v7.json absent",
                  "missing", "Every critical artifact must carry a validated resolution record.")
        )
    else:
        checks.append(
            check(
                "critical_authority_zero",
                authority.get("critical_unresolved", 1) == 0
                and authority.get("n_resolution_records_rejected", 1) == 0,
                f"{authority.get('n_critical')} critical, "
                f"{authority.get('critical_unresolved')} unresolved, "
                f"{authority.get('n_resolution_records_rejected')} records rejected",
                "docs/registry/artifact_authority_audit_v7.json",
                "Every critical artifact must carry a validated resolution record.",
            )
        )

    canonical = load("results/stage13/wave0/canonical_evidence_verification_v7.json")
    if canonical is None:
        legacy = load("results/stage13/wave0/canonical_evidence_verification_v6.json") or {}
        populated = legacy.get("populated_fields", {})
        nulls = sum((legacy.get("null_reason_counts") or {}).values())
        checks.append(
            check(
                "canonical_evidence_substantive", False,
                f"no v7 rebuild; v6 populates only {list(populated)} across "
                f"{legacy.get('model_family_rows')} rows with {nulls} nulls",
                "results/stage13/wave0/canonical_evidence_verification_v6.json",
                "Canonical evidence must span more than S_lp with source-linked values. "
                "The v6 pass is not inherited.",
            )
        )
    else:
        populated = canonical.get("populated_fields", {})
        checks.append(
            check(
                "canonical_evidence_substantive",
                len(populated) > 1 and canonical.get("source_linked_values", 0) > 0,
                f"{len(populated)} populated field types",
                "results/stage13/wave0/canonical_evidence_verification_v7.json",
                "Canonical evidence must span more than S_lp with source-linked values.",
            )
        )

    claims = load("docs/registry/claim_evidence_matrix_v7.json")
    if claims is None:
        legacy = load("docs/registry/claim_evidence_matrix_v6.json") or {}
        legacy_claims = legacy.get("claims", [])
        with_artifacts = sum(1 for c in legacy_claims if c.get("authoritative_artifacts"))
        checks.append(
            check(
                "claim_matrix_substantive", False,
                f"no v7 rebuild; {with_artifacts}/{len(legacy_claims)} v6 claims cite an artifact",
                "docs/registry/claim_evidence_matrix_v6.json",
                "Every claim needs a real estimate, interval, and cited authoritative "
                "artifacts. The v6 pass is not inherited.",
            )
        )
    else:
        claim_rows = claims.get("claims", [])
        with_artifacts = sum(1 for c in claim_rows if c.get("authoritative_artifacts"))
        checks.append(
            check(
                "claim_matrix_substantive",
                bool(claim_rows) and with_artifacts == len(claim_rows),
                f"{with_artifacts}/{len(claim_rows)} claims cite an authoritative artifact",
                "docs/registry/claim_evidence_matrix_v7.json",
                "Every claim needs a real estimate, interval, and cited authoritative artifacts.",
            )
        )

    return finalize("stage13_wave0_gate", checks)


def build_wave1a() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    leakage = load("results/stage13/benchmark_integrity/leakage_audit_v7.json")
    if leakage is None:
        checks.append(
            check("leakage_review_resolved", False, "leakage_audit_v7.json absent", "missing",
                  "Leakage cannot pass while unresolved cross-family candidates remain.")
        )
    else:
        checks.append(
            check(
                "leakage_review_resolved",
                leakage.get("status") == "PASS",
                f"status={leakage.get('status')}; "
                f"{leakage.get('unresolved_cross_family_review')} unresolved variant pairs = "
                f"{leakage.get('unresolved_family_pairs')} family pairs in "
                f"{leakage.get('unresolved_family_clusters')} clusters",
                "results/stage13/benchmark_integrity/leakage_audit_v7.json",
                "Leakage cannot pass while unresolved cross-family candidates remain.",
            )
        )
        checks.append(
            check(
                "leakage_population_untruncated",
                leakage.get("population_truncated") is False
                and leakage.get("n_families") == 155,
                f"{leakage.get('n_prompt_records')} prompts over {leakage.get('n_families')} families",
                "results/stage13/benchmark_integrity/leakage_audit_v7.json",
                "The audit must cover the whole prompt population with no truncation.",
            )
        )

    # Checks whose v6 artifacts are unchanged this cycle are carried forward and
    # labelled as such, so a reader can see they are not v7 results.
    legacy = load("results/stage13/benchmark_integrity/wave1a_gate_v6.json") or {}
    carried = {
        c["check_id"]: c.get("passed", False)
        for c in legacy.get("checks", [])
        if c["check_id"] != "leakage_review_resolved"
    }
    for check_id, passed in carried.items():
        checks.append(
            check(
                check_id, passed, "carried forward unchanged from v6",
                "results/stage13/benchmark_integrity/wave1a_gate_v6.json",
                "Carried forward; not re-derived in v7.",
            )
        )

    return finalize("stage13_wave1a_software_materials_gate", checks)


def finalize(gate_name: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [c["check_id"] for c in checks if not c["passed"]]
    git = git_info()
    return {
        "gate_name": gate_name,
        "gate_version": "7.0",
        "status": "PASS" if not failures else "FAIL",
        "critical_failures": failures,
        "checks": checks,
        "paper_eligibility": False,
        "permission_for_wave2": False,
        "human_pilot": "PENDING",
        "git_commit": git.get("commit"),
        "git_dirty": git.get("dirty"),
        "gate_policy": (
            "Checks that passed on form in v6 are re-evaluated against their stricter "
            "criterion. Where a v7 artifact does not exist, the check fails rather than "
            "inheriting the v6 pass."
        ),
    }


def render(path: str, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Gate version: {payload['gate_version']}",
        f"- Human pilot: `{payload['human_pilot']}`",
        f"- Paper eligibility: `{payload['paper_eligibility']}`",
        f"- Permission for Wave 2: `{payload['permission_for_wave2']}`",
        f"- Source commit: `{payload['git_commit']}`",
        "",
        "## Checks",
        "",
    ]
    for entry in payload["checks"]:
        mark = "PASS" if entry["passed"] else "FAIL"
        lines.append(f"### {mark} `{entry['check_id']}`")
        lines.append("")
        lines.append(f"- Detail: {entry['detail']}")
        lines.append(f"- Computed from: `{entry['computed_from']}`")
        lines.append(f"- Criterion: {entry['criterion']}")
        lines.append("")
    lines += ["## Gate policy", "", payload["gate_policy"], ""]
    (REPO_ROOT / path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave0-json", default="results/stage13/wave0/wave0_gate_v7.json")
    parser.add_argument(
        "--wave1a-json", default="results/stage13/benchmark_integrity/wave1a_gate_v7.json"
    )
    args = parser.parse_args()

    wave0 = build_wave0()
    wave1a = build_wave1a()
    write_json(args.wave0_json, wave0)
    write_json(args.wave1a_json, wave1a)
    render("docs/stage13/wave0_gate_v7_report.md", "Stage 13 Wave 0 Gate v7", wave0)
    render("docs/stage13/wave1a_gate_v7_report.md", "Stage 13 Wave 1A Gate v7", wave1a)

    for payload in (wave0, wave1a):
        print(f"{payload['gate_name']}: {payload['status']}")
        for entry in payload["checks"]:
            print(f"  {'PASS' if entry['passed'] else 'FAIL'}  {entry['check_id']}: {entry['detail']}")
        print()


if __name__ == "__main__":
    main()
