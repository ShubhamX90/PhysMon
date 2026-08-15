#!/usr/bin/env python3
"""Validate the Stage 13 experiment registry."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from governance_utils import REPO_ROOT, read_jsonl, repo_path, write_csv, write_json


REQUIRED_FIELDS = {
    "experiment_id",
    "stage",
    "experiment_class",
    "status",
    "paper_eligible",
    "primary_artifacts",
    "raw_artifacts",
    "discovery_or_confirmation",
    "notes",
}
VALID_CLASSES = {
    "diagnostic",
    "exploratory",
    "internal_confirmation",
    "external_confirmation",
    "governance",
    "human_validation",
}
VALID_STATUSES = {
    "planned",
    "queued",
    "running",
    "complete",
    "partial",
    "failed",
    "superseded",
    "unresolved",
}


def validate_row(row: dict[str, Any], line_no: int) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_FIELDS - set(row)
    if missing:
        errors.append(f"line {line_no}: missing fields {sorted(missing)}")
    if row.get("experiment_class") not in VALID_CLASSES:
        errors.append(f"line {line_no}: invalid experiment_class {row.get('experiment_class')!r}")
    if row.get("status") not in VALID_STATUSES:
        errors.append(f"line {line_no}: invalid status {row.get('status')!r}")
    if not isinstance(row.get("paper_eligible"), bool):
        errors.append(f"line {line_no}: paper_eligible must be boolean")
    status = row.get("status")
    for artifact_key in ("primary_artifacts", "raw_artifacts"):
        artifacts = row.get(artifact_key, [])
        if not isinstance(artifacts, list):
            errors.append(f"line {line_no}: {artifact_key} must be a list")
            continue
        for artifact in artifacts:
            if not isinstance(artifact, str):
                errors.append(f"line {line_no}: {artifact_key} contains non-string path")
                continue
            if artifact_key == "primary_artifacts" and status in {"planned", "queued", "running"}:
                continue
            if artifact and not repo_path(artifact).exists():
                errors.append(f"line {line_no}: missing artifact {artifact}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="docs/registry/experiment_registry.jsonl")
    parser.add_argument("--output", default="results/stage13/wave0/registry_verification.json")
    parser.add_argument("--csv-output", default="docs/registry/experiment_registry.csv")
    args = parser.parse_args()

    registry_path = repo_path(args.registry)
    rows = read_jsonl(registry_path) if registry_path.exists() else []
    errors: list[str] = []
    ids: list[str] = []
    for line_no, row in enumerate(rows, start=1):
        ids.append(str(row.get("experiment_id", "")))
        errors.extend(validate_row(row, line_no))
    duplicates = [item for item, count in Counter(ids).items() if item and count > 1]
    for experiment_id in duplicates:
        errors.append(f"duplicate experiment_id: {experiment_id}")

    fieldnames = sorted({key for row in rows for key in row})
    csv_rows = []
    for row in rows:
        csv_rows.append(
            {
                key: "|".join(row[key]) if isinstance(row.get(key), list) else row.get(key, "")
                for key in fieldnames
            }
        )
    if fieldnames:
        write_csv(args.csv_output, csv_rows, fieldnames)
    else:
        Path(REPO_ROOT / args.csv_output).parent.mkdir(parents=True, exist_ok=True)
        with (REPO_ROOT / args.csv_output).open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(["experiment_id"])

    summary = {
        "registry": args.registry,
        "n_rows": len(rows),
        "n_paper_eligible_rows": sum(1 for row in rows if row.get("paper_eligible") is True),
        "n_errors": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    write_json(args.output, summary)


if __name__ == "__main__":
    main()
