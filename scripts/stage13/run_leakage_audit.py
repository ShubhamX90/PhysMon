#!/usr/bin/env python3
"""Run a conservative benchmark leakage/duplicate audit."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path

from governance_utils import REPO_ROOT, sha256_text, write_csv, write_json


def prompt_rows(generated_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(generated_dir.glob("*.json")):
        try:
            family = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        fid = family.get("template_id", path.stem)
        for variant in family.get("variants", []):
            prompt = str(variant.get("prompt", ""))
            rows.append(
                {
                    "template_id": fid,
                    "variant_id": variant.get("variant_id", ""),
                    "prompt_sha256": sha256_text(prompt),
                    "prompt": prompt,
                    "source_path": str(path.relative_to(REPO_ROOT)),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-dir", default="results/stage6/generated_full_benchmark")
    parser.add_argument("--json-output", default="results/stage13/benchmark_integrity/leakage_audit.json")
    parser.add_argument("--review-output", default="results/stage13/benchmark_integrity/leakage_review.csv")
    args = parser.parse_args()

    rows = prompt_rows(REPO_ROOT / args.generated_dir)
    exact: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        exact.setdefault(str(row["prompt_sha256"]), []).append(row)
    exact_duplicates = [group for group in exact.values() if len(group) > 1]

    near_rows = []
    for idx, left in enumerate(rows):
        for right in rows[idx + 1 :]:
            if left["template_id"] == right["template_id"]:
                continue
            ratio = difflib.SequenceMatcher(None, str(left["prompt"]), str(right["prompt"])).ratio()
            if ratio >= 0.92:
                near_rows.append(
                    {
                        "left_template_id": left["template_id"],
                        "left_variant_id": left["variant_id"],
                        "right_template_id": right["template_id"],
                        "right_variant_id": right["variant_id"],
                        "similarity": round(ratio, 4),
                        "review_status": "needs_human_review",
                    }
                )
    write_csv(
        args.review_output,
        near_rows,
        [
            "left_template_id",
            "left_variant_id",
            "right_template_id",
            "right_variant_id",
            "similarity",
            "review_status",
        ],
    )
    write_json(
        args.json_output,
        {
            "n_prompts": len(rows),
            "n_exact_duplicate_groups": len(exact_duplicates),
            "n_near_duplicate_pairs_at_0_92": len(near_rows),
            "exact_duplicate_groups": exact_duplicates[:50],
            "review_csv": args.review_output,
            "status": "PASS" if not exact_duplicates else "FAIL",
        },
    )


if __name__ == "__main__":
    main()

