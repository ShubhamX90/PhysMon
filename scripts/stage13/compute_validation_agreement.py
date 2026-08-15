#!/usr/bin/env python3
"""Compute Stage 13 validation agreement when human labels are available."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from itertools import combinations

from governance_utils import write_json


FIELDS = [
    "overall_verdict",
    "assumptions_sufficient",
    "answer_invariant",
    "semantic_equivalence",
    "certificate_valid",
]


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    labels = sorted({value for pair in pairs for value in pair})
    observed = sum(a == b for a, b in pairs) / len(pairs)
    left = Counter(a for a, _ in pairs)
    right = Counter(b for _, b in pairs)
    expected = sum((left[label] / len(pairs)) * (right[label] / len(pairs)) for label in labels)
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else None
    return (observed - expected) / (1.0 - expected)


def pairwise_for_field(rows: list[dict[str, str]], field: str) -> list[tuple[str, str]]:
    by_family: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        family_id = row.get("family_id") or row.get("packet_id") or row.get("template_id") or ""
        value = row.get(field, "")
        if family_id and value:
            by_family[family_id].append(value)
    pairs = []
    for values in by_family.values():
        for left, right in combinations(values, 2):
            pairs.append((left, right))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="docs/validation/validation_status_v2.csv")
    parser.add_argument("--output", default="results/stage13/benchmark_integrity/validation_agreement_v3.json")
    args = parser.parse_args()

    try:
        with open(args.annotations, "r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except FileNotFoundError:
        write_json(args.output, {"status": "ANNOTATION_FILE_MISSING", "paper_eligibility": False})
        return

    labeled_rows = [row for row in rows if any(row.get(field, "") for field in FIELDS)]
    if not labeled_rows:
        write_json(
            args.output,
            {
                "status": "HUMAN_LABELS_MISSING",
                "raw_agreement": None,
                "cohens_kappa": None,
                "cue_relevance_agreement": None,
                "invariance_agreement": None,
                "assumption_sufficiency_agreement": None,
                "semantic_equivalence_agreement": None,
                "domain_breakdown": {},
                "cue_breakdown": {},
                "adjudication_rate": None,
                "missing_field_rate": 1.0,
                "families_marked_valid": 0,
                "paper_eligibility": False,
            },
        )
        return

    field_metrics = {}
    all_pairs = []
    for field in FIELDS:
        pairs = pairwise_for_field(labeled_rows, field)
        all_pairs.extend(pairs)
        field_metrics[field] = {
            "n_pairs": len(pairs),
            "raw_agreement": (sum(a == b for a, b in pairs) / len(pairs)) if pairs else None,
            "cohens_kappa": cohen_kappa(pairs),
        }
    missing_total = sum(1 for row in rows for field in FIELDS if not row.get(field, ""))
    denom = max(len(rows) * len(FIELDS), 1)
    write_json(
        args.output,
        {
            "status": "AGREEMENT_COMPUTED",
            "raw_agreement": (sum(a == b for a, b in all_pairs) / len(all_pairs)) if all_pairs else None,
            "cohens_kappa": cohen_kappa(all_pairs),
            "field_metrics": field_metrics,
            "cue_relevance_agreement": field_metrics.get("overall_verdict", {}).get("raw_agreement"),
            "invariance_agreement": field_metrics.get("answer_invariant", {}).get("raw_agreement"),
            "assumption_sufficiency_agreement": field_metrics.get("assumptions_sufficient", {}).get("raw_agreement"),
            "semantic_equivalence_agreement": field_metrics.get("semantic_equivalence", {}).get("raw_agreement"),
            "domain_breakdown": {},
            "cue_breakdown": {},
            "adjudication_rate": None,
            "missing_field_rate": missing_total / denom,
            "families_marked_valid": sum(row.get("overall_verdict") == "valid" for row in labeled_rows),
            "paper_eligibility": False,
        },
    )


if __name__ == "__main__":
    main()
