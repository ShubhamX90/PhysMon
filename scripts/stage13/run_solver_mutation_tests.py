#!/usr/bin/env python3
"""Run Stage 13 v5 mutation tests through the actual symbolic verifier."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from physmon.validation.mutation_executor import execute_operator  # noqa: E402
from physmon.validation.mutation_operators import default_mutation_operators  # noqa: E402

from governance_utils import REPO_ROOT, write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifests/physmon_canonical_155.jsonl")
    parser.add_argument("--limit", type=int, default=36)
    parser.add_argument("--records-output", default="results/stage13/benchmark_integrity/mutation_test_records_v5.jsonl")
    parser.add_argument("--summary-output", default="results/stage13/benchmark_integrity/mutation_test_summary_v5.json")
    parser.add_argument("--mutation-dir", default="results/stage13/benchmark_integrity/mutated_templates_v5")
    return parser.parse_args()


def load_manifest(path: str) -> list[dict[str, str]]:
    rows = []
    for line in (REPO_ROOT / path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return [row for row in rows if row.get("is_canonical") is True]


def find_yaml_for_family(fid: str) -> Path | None:
    matches = sorted((REPO_ROOT / "data/raw/templates").rglob(f"{fid}.yaml"))
    return matches[0] if matches else None


def stratified_manifest_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    by_key: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_key[(row.get("domain", ""), row.get("cue_type", ""), row.get("original_or_expansion", ""))].append(row)
    selected: list[dict[str, str]] = []
    for key in sorted(by_key):
        if by_key[key]:
            selected.append(by_key[key].pop(0))
    idx = 0
    all_rows = rows[:]
    while len(selected) < limit and idx < len(all_rows):
        row = all_rows[idx]
        if row not in selected:
            selected.append(row)
        idx += 1
    return selected[:limit]


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    by_operator: dict[str, dict[str, object]] = {}
    for record in records:
        op = str(record["operator_id"])
        bucket = by_operator.setdefault(
            op,
            {
                "operator_id": op,
                "operator_type": record["operator_type"],
                "n_considered": 0,
                "n_applicable": 0,
                "n_executed": 0,
                "n_verified": 0,
                "n_expected_reject": 0,
                "n_actual_reject": 0,
                "n_expected_accept": 0,
                "n_actual_accept": 0,
                "n_unsupported": 0,
                "n_execution_failures": 0,
            },
        )
        bucket["n_considered"] += 1
        if record["coverage_status"] == "coverage_not_supported":
            bucket["n_unsupported"] += 1
        if record["mutation_applied"]:
            bucket["n_applicable"] += 1
            bucket["n_executed"] += 1
        if record["verifier_invoked"]:
            bucket["n_verified"] += 1
        if record["expected_verifier_result"] == "reject":
            bucket["n_expected_reject"] += 1
        if record["expected_verifier_result"] == "accept":
            bucket["n_expected_accept"] += 1
        if record["actual_verifier_passed"] is False:
            bucket["n_actual_reject"] += 1
        if record["actual_verifier_passed"] is True:
            bucket["n_actual_accept"] += 1
        if record["mutation_applied"] and not record["verifier_invoked"]:
            bucket["n_execution_failures"] += 1
    for bucket in by_operator.values():
        bucket["rejection_rate"] = (
            bucket["n_actual_reject"] / bucket["n_expected_reject"] if bucket["n_expected_reject"] else None
        )
        bucket["acceptance_rate"] = (
            bucket["n_actual_accept"] / bucket["n_expected_accept"] if bucket["n_expected_accept"] else None
        )
    negative_verified = sum(1 for r in records if r["operator_type"] == "negative" and r["verifier_invoked"])
    positive_verified = sum(1 for r in records if r["operator_type"] == "positive" and r["verifier_invoked"])
    expected_mismatch = sum(1 for r in records if r["expected_matches_actual"] is False)
    return {
        "status": "VERIFIED_MUTATIONS_EXECUTED" if negative_verified and positive_verified else "MUTATION_VERIFICATION_INCOMPLETE",
        "n_families": len({r["family_id"] for r in records}),
        "n_records": len(records),
        "n_verified": sum(1 for r in records if r["verifier_invoked"]),
        "negative_verified_records": negative_verified,
        "positive_verified_records": positive_verified,
        "expected_mismatch_records": expected_mismatch,
        "operator_summaries": list(by_operator.values()),
        "supersedes": "results/stage13/benchmark_integrity/mutation_test_summary_v3.json",
        "prior_v3_status": "superseded_assigned_outcomes_not_verified",
    }


def main() -> None:
    args = parse_args()
    rows = stratified_manifest_rows(load_manifest(args.manifest), args.limit)
    operators = default_mutation_operators()
    mutation_dir = REPO_ROOT / args.mutation_dir
    records = []
    for row in rows:
        template_path = find_yaml_for_family(row["canonical_family_id"])
        if template_path is None:
            continue
        for operator in operators:
            record = execute_operator(template_path, operator, mutation_dir).to_dict()
            records.append(record)
    output = REPO_ROOT / args.records_output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    write_json(args.summary_output, summarize(records))


if __name__ == "__main__":
    main()
