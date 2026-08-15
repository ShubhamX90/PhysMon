#!/usr/bin/env python3
"""Summarize one behavioural JSONL into family-level S_lp outputs.

Useful for appendix / expansion runs that should not be forced through the
full Stage 4/6 benchmark analysis pipeline.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from physmon.utils.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", required=True, help="Behavioural JSONL to summarize.")
    parser.add_argument("--output-dir", required=True, help="Directory for CSV/JSON summaries.")
    parser.add_argument("--model-prefix", default="qwen", help="Column prefix, e.g. qwen or deepseek.")
    parser.add_argument("--threshold", type=float, default=0.5, help="Positive-family threshold in nats.")
    return parser.parse_args()


def normalize_answer(value: Any) -> str:
    text = str(value or "").strip().lower()
    return " ".join(text.split())


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    families: dict[str, dict[str, Any]] = {}
    with Path(args.jsonl).open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") != "variant_record":
                continue
            template_id = str(record["template_id"])
            entry = families.setdefault(
                template_id,
                {
                    "template_id": template_id,
                    "domain": record.get("domain", ""),
                    "cue_type": record.get("cue_type", ""),
                    "correct_answer": record.get("correct_answer", ""),
                    "variants": {},
                },
            )
            variant_id = int(record["variant_id"])
            parsed_answer = record.get("parsed_answer_canonical") or record.get("parsed_answer")
            correct_answer = record.get("correct_answer")
            parsed_ok = bool(record.get("parse_confident"))
            correct = parsed_ok and normalize_answer(parsed_answer) == normalize_answer(correct_answer)
            entry["variants"][variant_id] = {
                "logprob_correct_answer": float(record.get("logprob_correct_answer", 0.0) or 0.0),
                "parse_confident": parsed_ok,
                "correct": bool(correct),
            }

    prefix = args.model_prefix
    csv_rows = []
    positive_families = []
    for template_id in sorted(families):
        family = families[template_id]
        variants = family["variants"]
        variant_ids = sorted(variants)
        if 0 not in variants:
            continue
        base = variants[0]["logprob_correct_answer"]
        others = [variants[vid]["logprob_correct_answer"] for vid in variant_ids if vid != 0]
        slp = float(base - min(others)) if others else 0.0
        parse_rate = float(sum(int(v["parse_confident"]) for v in variants.values()) / max(len(variants), 1))
        correct_rate = float(sum(int(v["correct"]) for v in variants.values()) / max(len(variants), 1))
        hat_s = 1.0 if len({variants[vid]["correct"] for vid in variant_ids}) > 1 else 0.0
        if slp >= args.threshold:
            positive_families.append(template_id)
        csv_rows.append(
            {
                "template_id": template_id,
                "domain": family["domain"],
                "cue_type": family["cue_type"],
                f"{prefix}_num_valid_parses": int(sum(int(v["parse_confident"]) for v in variants.values())),
                f"{prefix}_parse_rate_family": parse_rate,
                f"{prefix}_correct_rate_family": correct_rate,
                f"{prefix}_hat_S": hat_s,
                f"{prefix}_S_lp": slp,
                f"{prefix}_correct_answer": family["correct_answer"],
                f"{prefix}_positive": int(slp >= args.threshold),
            }
        )

    fieldnames = list(csv_rows[0].keys()) if csv_rows else [
        "template_id",
        "domain",
        "cue_type",
        f"{prefix}_num_valid_parses",
        f"{prefix}_parse_rate_family",
        f"{prefix}_correct_rate_family",
        f"{prefix}_hat_S",
        f"{prefix}_S_lp",
        f"{prefix}_correct_answer",
        f"{prefix}_positive",
    ]
    with (output_dir / "per_family_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    summary = {
        "n_families": len(csv_rows),
        "threshold": float(args.threshold),
        "positive_families": positive_families,
        "positive_count": len(positive_families),
        "positive_rate": float(len(positive_families) / max(len(csv_rows), 1)),
        "mean_slp": float(sum(float(row[f"{prefix}_S_lp"]) for row in csv_rows) / max(len(csv_rows), 1)),
        "model_prefix": prefix,
    }
    write_json(output_dir / "summary.json", summary)


if __name__ == "__main__":
    main()
