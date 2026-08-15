#!/usr/bin/env python3
"""Validate or summarize parser audit candidates.

Human judgments are not inferred. If labels are blank, the output is an honest
`LABELS_MISSING` report.
"""

from __future__ import annotations

import argparse

from governance_utils import read_jsonl, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="docs/validation/parser_audit_candidates.jsonl")
    parser.add_argument("--output", default="results/stage13/benchmark_integrity/parser_audit_status.json")
    args = parser.parse_args()

    rows = read_jsonl(args.candidates)
    labeled = [row for row in rows if row.get("human_parser_judgment")]
    write_json(
        args.output,
        {
            "n_candidates": len(rows),
            "n_labeled": len(labeled),
            "status": "PASS" if len(labeled) == len(rows) and rows else "LABELS_MISSING",
            "paper_eligible": False,
            "note": "Parser audit requires independent human labels; blank labels are not inferred.",
        },
    )


if __name__ == "__main__":
    main()

