#!/usr/bin/env python3
"""Select parser-audit candidates from existing behavioural JSONL files."""

from __future__ import annotations

import argparse
from itertools import islice

from governance_utils import REPO_ROOT, read_jsonl, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--behavioural-dir", default="results/stage6/behavioural_full_rerun")
    parser.add_argument("--per-model", type=int, default=20)
    parser.add_argument("--output", default="docs/validation/parser_audit_candidates.jsonl")
    args = parser.parse_args()

    rows = []
    for path in sorted((REPO_ROOT / args.behavioural_dir).glob("*.jsonl")):
        if path.name in {"family_summaries.jsonl", "prompt_records.jsonl", "run_behavioural_events.jsonl"}:
            continue
        candidates = []
        for row in read_jsonl(path):
            if row.get("record_type") != "variant_record":
                continue
            candidates.append(
                {
                    "candidate_id": f"{path.stem}::{row.get('template_id')}::{row.get('variant_id')}",
                    "template_id": row.get("template_id", ""),
                    "variant_id": row.get("variant_id", ""),
                    "model_role": row.get("model_role", ""),
                    "generated_text": row.get("generated_text", ""),
                    "parser_output": row.get("parsed_answer", ""),
                    "parser_confident": row.get("parse_confident", ""),
                    "correct_answer": row.get("correct_answer", ""),
                    "human_parser_judgment": "",
                    "human_notes": "",
                    "source_path": str(path.relative_to(REPO_ROOT)),
                }
            )
        rows.extend(list(islice(candidates, args.per_model)))
    write_jsonl(args.output, rows)


if __name__ == "__main__":
    main()

