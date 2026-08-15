#!/usr/bin/env python3
"""Inventory result artifacts and flag authority/provenance risks."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from governance_utils import REPO_ROOT, classify_result_path, file_record, write_csv, write_json


def scan_results(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(REPO_ROOT)
        record = file_record(rel)
        record["artifact_class"] = classify_result_path(path)
        record["stage"] = next((part for part in rel.parts if part.startswith("stage")), "unknown")
        record["authority_status"] = "unresolved_pending_registry_link"
        rows.append(record)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--json-output", default="docs/registry/artifact_authority_audit.json")
    parser.add_argument("--md-output", default="docs/registry/artifact_authority_audit.md")
    parser.add_argument("--csv-output", default="docs/registry/artifact_authority_audit.csv")
    args = parser.parse_args()

    rows = scan_results(REPO_ROOT / args.results_root)
    by_stage: dict[str, int] = defaultdict(int)
    by_class: dict[str, int] = defaultdict(int)
    empty = []
    for row in rows:
        by_stage[str(row["stage"])] += 1
        by_class[str(row["artifact_class"])] += 1
        if row.get("size_bytes") == 0:
            empty.append(row["path"])
    summary = {
        "n_artifacts": len(rows),
        "by_stage": dict(sorted(by_stage.items())),
        "by_artifact_class": dict(sorted(by_class.items())),
        "empty_files": empty,
        "paper_eligible_claim": "NONE; this audit is an inventory only",
        "authority_status": "unresolved_until_linked_to_registry_and_raw_inputs",
        "artifacts": rows,
    }
    write_json(args.json_output, summary)
    fieldnames = [
        "path",
        "exists",
        "size_bytes",
        "sha256",
        "artifact_class",
        "stage",
        "authority_status",
    ]
    write_csv(args.csv_output, rows, fieldnames)

    md = [
        "# Stage 13 Artifact Authority Audit",
        "",
        "This audit inventories files only. It does not make any result paper-eligible.",
        "",
        f"- Artifacts scanned: {len(rows)}",
        f"- Empty files: {len(empty)}",
        "",
        "## Counts By Stage",
        "",
    ]
    for stage, count in sorted(by_stage.items()):
        md.append(f"- {stage}: {count}")
    md.extend(["", "## Counts By Artifact Class", ""])
    for artifact_class, count in sorted(by_class.items()):
        md.append(f"- {artifact_class}: {count}")
    md.extend(["", "## Blocking Note", ""])
    md.append(
        "All historical artifacts remain `unresolved_pending_registry_link` until connected "
        "to raw inputs, execution metadata, and the discovery/confirmation partition."
    )
    Path(REPO_ROOT / args.md_output).write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

