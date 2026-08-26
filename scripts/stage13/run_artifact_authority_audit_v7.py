#!/usr/bin/env python3
"""Repository-wide artifact authority audit (v7).

The v6 audit decided criticality with a single hard-coded string test::

    cls = "critical" if "donor_renamed" in relp and rows == 0 else ...

No other artifact in the repository could ever be classified critical, so the
``critical_authority_zero`` gate check measured one hard-coded path rather than
the state of the evidence base.

v7 classifies by evidence:

*   an artifact is **critical** when it carries zero data rows *and* sits under a
    scientific results path that a claim could draw on;
*   a critical artifact is **resolved** only when a resolution record supplies
    all three links -- a registry experiment whose status is non-authoritative, a
    superseding correction artifact that exists on disk, and a
    ``next_required_experiment`` pointer;
*   resolution records are **validated**, not trusted: a record naming a missing
    registry entry, a missing superseding artifact, or an authoritative status is
    rejected and its artifact stays unresolved.

Resolution here means "documented failure", never "measured null". An artifact
with zero rows is not evidence of a zero effect, and recording it as resolved
does not make it one.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_utils import REPO_ROOT, read_jsonl, write_csv, write_json  # noqa: E402


DATA_SUFFIXES = {".csv", ".jsonl", ".json", ".yaml", ".yml", ".npy", ".npz", ".txt", ".md", ".log", ".out"}
TABULAR_SUFFIXES = {".csv", ".jsonl", ".json"}

# Statuses that mean the run is NOT authoritative evidence. A resolution record
# pointing at an authoritative status is self-contradictory and gets rejected.
NON_AUTHORITATIVE_STATUSES = {
    "partial_not_reportable",
    "failed",
    "superseded",
    "pending",
}

# Paths whose artifacts are governance/diagnostic instrumentation, not claims.
DIAGNOSTIC_MARKERS = ("stage13", "docs/validation", "docs/registry", "docs/stage13")


def count_rows(path: Path) -> int | None:
    """Return data-row count, or None when the format carries no row concept."""

    try:
        if path.suffix == ".csv":
            with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                return sum(1 for _ in csv.DictReader(handle))
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                return sum(1 for line in handle if line.strip())
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return len(payload) if isinstance(payload, list) else None
    except Exception:
        return None
    return None


def classify(relative_path: str, rows: int | None, size: int) -> str:
    """Assign an orphan class from the artifact's evidence role, not its filename."""

    if any(marker in relative_path for marker in DIAGNOSTIC_MARKERS):
        return "diagnostic"
    if "__pycache__" in relative_path or relative_path.endswith(".pyc"):
        return "cache"
    is_scientific_result = relative_path.startswith("results/")
    if rows == 0 and is_scientific_result:
        # Zero rows under a scientific path cannot support any claim and must be
        # explicitly accounted for.
        return "critical"
    if size == 0 and is_scientific_result:
        return "critical"
    if is_scientific_result:
        return "paper_relevant_noncritical"
    return "unknown"


def load_registry_statuses(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        str(row.get("experiment_id", "")): str(row.get("status", ""))
        for row in read_jsonl(str(path.relative_to(REPO_ROOT)))
    }


def validate_resolution(
    record: dict[str, Any], registry: dict[str, str]
) -> tuple[bool, list[str]]:
    """Check a resolution record's three required links. Returns (valid, problems)."""

    problems: list[str] = []

    experiment_id = str(record.get("registry_experiment_id", ""))
    if not experiment_id:
        problems.append("missing registry_experiment_id")
    elif experiment_id not in registry:
        problems.append(f"registry_experiment_id not in registry: {experiment_id}")
    elif registry[experiment_id] not in NON_AUTHORITATIVE_STATUSES:
        problems.append(
            f"registry status {registry[experiment_id]!r} is authoritative; a zero-row "
            "artifact cannot be resolved against an authoritative run"
        )

    superseding = record.get("superseding_artifacts") or []
    if not superseding:
        problems.append("missing superseding_artifacts")
    for artifact in superseding:
        if not (REPO_ROOT / str(artifact)).exists():
            problems.append(f"superseding artifact does not exist: {artifact}")

    if not str(record.get("next_required_experiment", "")).strip():
        problems.append("missing next_required_experiment")

    if record.get("scientific_null") is not False:
        problems.append("scientific_null must be explicitly false for a zero-row artifact")

    return (not problems), problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolutions", default="results/stage13/wave0/authority_resolutions_v7.jsonl")
    parser.add_argument("--registry", default="docs/registry/experiment_registry.jsonl")
    parser.add_argument("--audit-json", default="docs/registry/artifact_authority_audit_v7.json")
    parser.add_argument("--audit-md", default="docs/registry/artifact_authority_audit_v7.md")
    parser.add_argument("--orphans-csv", default="results/stage13/wave0/orphan_artifacts_v7.csv")
    args = parser.parse_args()

    registry = load_registry_statuses(REPO_ROOT / args.registry)

    resolutions: dict[str, dict[str, Any]] = {}
    resolution_problems: dict[str, list[str]] = {}
    resolutions_path = REPO_ROOT / args.resolutions
    if resolutions_path.exists():
        for record in read_jsonl(args.resolutions):
            artifact = str(record.get("artifact_path", ""))
            valid, problems = validate_resolution(record, registry)
            if valid:
                resolutions[artifact] = record
            else:
                resolution_problems[artifact] = problems

    records: list[dict[str, Any]] = []
    type_counts: Counter = Counter()
    for root_name in ("results", "docs"):
        for path in sorted((REPO_ROOT / root_name).rglob("*")):
            if not path.is_file() or path.suffix.lower() not in DATA_SUFFIXES:
                continue
            relative = str(path.relative_to(REPO_ROOT))
            size = path.stat().st_size
            rows = count_rows(path) if path.suffix in TABULAR_SUFFIXES else None
            orphan_class = classify(relative, rows, size)
            resolved = relative in resolutions
            type_counts[path.suffix.lstrip(".")] += 1
            records.append(
                {
                    "path": relative,
                    "artifact_type": path.suffix.lstrip("."),
                    "size_bytes": size,
                    "raw_data_rows": "" if rows is None else rows,
                    "orphan_class": orphan_class,
                    "zero_row_cannot_support_null": rows == 0,
                    "resolution_status": (
                        "resolved_documented_failure"
                        if resolved
                        else ("rejected_resolution" if relative in resolution_problems else "unresolved")
                    ),
                    "registry_experiment_id": (
                        resolutions[relative].get("registry_experiment_id", "") if resolved else ""
                    ),
                    "resolution_problems": "; ".join(resolution_problems.get(relative, [])),
                }
            )

    criticals = [r for r in records if r["orphan_class"] == "critical"]
    critical_unresolved = [
        r for r in criticals if r["resolution_status"] != "resolved_documented_failure"
    ]
    zero_row_total = sum(1 for r in records if r["zero_row_cannot_support_null"])

    audit = {
        "status": (
            "PASS_ALL_CRITICAL_ARTIFACTS_RESOLVED"
            if not critical_unresolved
            else "FAIL_REPOSITORY_WIDE_AUTHORITY_UNRESOLVED"
        ),
        "method": "evidence_based_classification_v7",
        "supersedes": "docs/registry/artifact_authority_audit_v6.json",
        "supersession_reason": (
            "v6 assigned the critical class with the hard-coded test "
            "'donor_renamed' in path and rows == 0, so no other artifact in the "
            "repository could ever be classified critical."
        ),
        "n_artifacts_scanned": len(records),
        "artifacts_scanned_by_type": dict(type_counts),
        "orphan_classes": dict(Counter(r["orphan_class"] for r in records)),
        "n_critical": len(criticals),
        "critical_unresolved": len(critical_unresolved),
        "critical_unresolved_paths": [r["path"] for r in critical_unresolved],
        "critical_resolved_paths": [
            r["path"] for r in criticals if r["resolution_status"] == "resolved_documented_failure"
        ],
        "zero_row_issues": zero_row_total,
        "n_resolution_records_accepted": len(resolutions),
        "n_resolution_records_rejected": len(resolution_problems),
        "rejected_resolution_details": resolution_problems,
        "resolution_semantics": (
            "Resolved means documented failure with a registry link, a superseding "
            "artifact, and a next required experiment. It never means measured null."
        ),
    }

    write_json(args.audit_json, audit)
    write_csv(
        args.orphans_csv,
        records,
        [
            "path", "artifact_type", "size_bytes", "raw_data_rows", "orphan_class",
            "zero_row_cannot_support_null", "resolution_status",
            "registry_experiment_id", "resolution_problems",
        ],
    )

    lines = [
        "# Artifact Authority Audit v7",
        "",
        f"Status: `{audit['status']}`",
        "",
        f"- Artifacts scanned: {audit['n_artifacts_scanned']}",
        f"- Critical artifacts: {audit['n_critical']}",
        f"- Critical unresolved: {audit['critical_unresolved']}",
        f"- Zero-row artifacts: {audit['zero_row_issues']}",
        f"- Resolution records accepted: {audit['n_resolution_records_accepted']}",
        f"- Resolution records rejected: {audit['n_resolution_records_rejected']}",
        "",
        "## Orphan classes",
        "",
    ]
    for name, count in sorted(audit["orphan_classes"].items()):
        lines.append(f"- `{name}`: {count}")
    lines += ["", "## Critical artifacts", ""]
    for record in criticals:
        lines.append(
            f"- `{record['path']}` -- rows={record['raw_data_rows']} "
            f"status={record['resolution_status']} "
            f"registry={record['registry_experiment_id'] or 'none'}"
        )
    lines += [
        "",
        "## Resolution semantics",
        "",
        audit["resolution_semantics"],
        "",
    ]
    (REPO_ROOT / args.audit_md).write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({k: v for k, v in audit.items() if not isinstance(v, dict)}, indent=2))


if __name__ == "__main__":
    main()
