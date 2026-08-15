#!/usr/bin/env python3
"""Validate canonical evidence tables."""

from __future__ import annotations

import argparse
from collections import Counter

from governance_utils import read_csv, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", default="results/canonical/model_family_evidence.csv")
    parser.add_argument("--variant", default="results/canonical/model_variant_evidence.csv")
    parser.add_argument("--output", default="results/stage13/wave0/canonical_evidence_verification.json")
    args = parser.parse_args()

    family_rows = read_csv(args.family)
    variant_rows = read_csv(args.variant)
    family_ids = [row["canonical_family_id"] for row in family_rows]
    variant_keys = [
        (row["canonical_family_id"], row["variant_id"], row["model_role"], row["source_path"])
        for row in variant_rows
    ]
    family_counter = Counter(family_ids)
    variant_counter = Counter(variant_keys)
    errors = []
    errors.extend([f"duplicate family id: {fid}" for fid, count in family_counter.items() if count > 1])
    errors.extend([f"duplicate variant key: {key}" for key, count in variant_counter.items() if count > 1])
    missing_family = sorted({row["canonical_family_id"] for row in variant_rows} - set(family_ids))
    if missing_family:
        errors.append(f"variant rows with missing family evidence: {missing_family[:20]}")
    write_json(
        args.output,
        {
            "n_family_rows": len(family_rows),
            "n_variant_rows": len(variant_rows),
            "n_errors": len(errors),
            "errors": errors,
            "status": "PASS" if not errors else "FAIL",
        },
    )


if __name__ == "__main__":
    main()

