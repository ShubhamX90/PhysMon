#!/usr/bin/env python3
"""Generate the Stage 3 pilot human-validation markdown form and CSV scaffold.

Reference: Stage 3 brief Part D.7.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from physmon.utils.io import read_yaml


VALIDATION_QUESTIONS = (
    ("Q1", "Is the cue clearly irrelevant (Cue A) or clearly non-governing (Cue B) for the stated target?"),
    ("Q2", "Do all 4 variants present the same physics problem with the same correct answer?"),
    ("Q3", "Is the stated correct answer unambiguously right for the governing law?"),
    ("Q4", "Is the problem statement clear and unambiguous to a competent undergraduate physics reader?"),
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for validation-form generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-dir", required=True, help="Directory containing YAML templates.")
    parser.add_argument("--generated-dir", required=True, help="Directory containing rendered family JSON.")
    parser.add_argument("--markdown-output", required=True, help="Markdown form output path.")
    parser.add_argument("--csv-output", required=True, help="CSV scaffold output path.")
    return parser.parse_args()


def main() -> None:
    """Generate the markdown and CSV validation scaffolds."""
    args = parse_args()
    template_dir = Path(args.template_dir)
    generated_dir = Path(args.generated_dir)

    sections: list[str] = ["# Pilot Validation Form", ""]
    csv_rows: list[dict[str, str]] = []
    for family_path in sorted(generated_dir.glob("*.json")):
        family_payload = json.loads(family_path.read_text(encoding="utf-8"))
        template_id = str(family_payload["template_id"])
        template_payload = read_yaml(template_dir / f"{template_id}.yaml")
        sections.extend(build_markdown_section(template_payload, family_payload))
        for question_key, question_text in VALIDATION_QUESTIONS:
            csv_rows.append(
                {
                    "template_id": template_id,
                    "question": question_key,
                    "question_text": question_text,
                    "answer": "",
                    "notes": "",
                }
            )

    Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.markdown_output).write_text("\n".join(sections) + "\n", encoding="utf-8")
    Path(args.csv_output).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.csv_output).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["template_id", "question", "question_text", "answer", "notes"])
        writer.writeheader()
        writer.writerows(csv_rows)


def build_markdown_section(template_payload: dict, family_payload: dict) -> list[str]:
    """Build one markdown section for a single rendered family."""
    lines = [
        f"## {template_payload['template_id']}",
        "",
        f"- Domain: `{template_payload['domain']}`",
        f"- Cue type: `{template_payload['cue_type']}`",
        f"- Governing law: `{template_payload['governing_law']}`",
        "",
        "```text",
    ]
    for variant in family_payload["variants"]:
        lines.append(f"[Variant {variant['variant_id']}]")
        lines.append(variant["prompt"])
        lines.append("")
    lines.extend(
        [
            "```",
            "",
            f"Stated correct answer: `{template_payload['correct_answer']['display']}`",
            "",
            "| Question | Your answer (Y/N) | Notes |",
            "|---|---|---|",
        ]
    )
    for question_key, question_text in VALIDATION_QUESTIONS:
        lines.append(f"| {question_key}: {question_text} | | |")
    lines.extend(["", "Free-text notes:", "", "---", ""])
    return lines


if __name__ == "__main__":
    main()
