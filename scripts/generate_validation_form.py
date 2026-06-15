#!/usr/bin/env python3
"""Generate Markdown and CSV validation forms from rendered PhysMon families.

Reference:
    physmon_proposal.pdf §7 (Validation Protocol) and Stage 6 benchmark workflow.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from physmon.utils.io import read_yaml


QUESTION_ROWS = (
    (
        "Q1",
        "Is the cue clearly irrelevant (Cue A) or clearly non-governing (Cue B) for the stated target?",
    ),
    (
        "Q2",
        "Do all 4 variants present the same physics problem with the same correct answer?",
    ),
    (
        "Q3",
        "Is the stated correct answer unambiguously right for the governing law?",
    ),
    (
        "Q4",
        "Is the problem statement clear and unambiguous to a competent undergraduate physics reader?",
    ),
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for validation-form generation."""

    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--template-filter",
        help="One prefix or a comma-separated list of prefixes to include.",
    )
    selection.add_argument("--template-list", nargs="+", help="Explicit template-id list to include.")
    parser.add_argument(
        "--template-dir",
        default="data/raw/templates",
        help="Directory containing template YAML files.",
    )
    parser.add_argument(
        "--generated-dir",
        required=True,
        help="Directory containing rendered family JSON files.",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Top-level Markdown heading for the generated form.",
    )
    parser.add_argument("--output-md", required=True, help="Markdown output path.")
    parser.add_argument("--output-csv", required=True, help="CSV output path.")
    return parser.parse_args()


def select_template_paths(
    template_dir: Path,
    template_filter: str | None,
    template_list: list[str] | None,
) -> list[Path]:
    """Select template YAML paths from one filter or explicit list."""

    if template_list:
        paths = [template_dir / f"{template_id}.yaml" for template_id in template_list]
    else:
        assert template_filter is not None
        prefixes = [part.strip() for part in template_filter.split(",") if part.strip()]
        paths = sorted(
            path
            for path in template_dir.glob("*.yaml")
            if any(path.stem.startswith(prefix) for prefix in prefixes)
        )
    missing = [path for path in paths if not path.exists()]
    if missing:
        labels = ", ".join(path.stem for path in missing)
        raise FileNotFoundError(f"Missing template YAML file(s): {labels}.")
    return paths


def load_rendered_family(generated_dir: Path, template_id: str) -> dict[str, Any]:
    """Load one rendered family JSON payload."""

    path = generated_dir / f"{template_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing rendered family JSON for {template_id}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_markdown_section(payload: dict[str, Any], rendered: dict[str, Any]) -> list[str]:
    """Build one family section in Markdown."""

    lines = [
        f"## {payload['template_id']}",
        "",
        f"- Domain: `{payload['domain']}`",
        f"- Cue type: `{payload['cue_type']}`",
        f"- Governing law: `{payload['governing_law']}`",
        "",
        "```text",
    ]
    for variant in rendered["variants"]:
        variant_id = variant["variant_id"]
        prompt = variant["prompt"]
        lines.extend([f"[Variant {variant_id}]", prompt, ""])
    lines.extend(
        [
            "```",
            "",
            f"Stated correct answer: `{payload['correct_answer']['display']}`",
            "",
            "| Question | Your answer (Y/N) | Notes |",
            "|---|---|---|",
        ]
    )
    for question_id, question_text in QUESTION_ROWS:
        lines.append(f"| {question_id}: {question_text} | | |")
    lines.extend(["", "Free-text notes:", "", "---", ""])
    return lines


def write_markdown(
    *,
    title: str,
    template_payloads: list[dict[str, Any]],
    rendered_payloads: dict[str, dict[str, Any]],
    output_path: Path,
) -> None:
    """Write the Markdown validation form."""

    lines = [f"# {title}", ""]
    for payload in template_payloads:
        template_id = str(payload["template_id"])
        lines.extend(build_markdown_section(payload, rendered_payloads[template_id]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(template_payloads: list[dict[str, Any]], output_path: Path) -> None:
    """Write the CSV validation form."""

    rows: list[dict[str, str]] = []
    for payload in template_payloads:
        template_id = str(payload["template_id"])
        for question_id, question_text in QUESTION_ROWS:
            rows.append(
                {
                    "template_id": template_id,
                    "question": question_id,
                    "question_text": question_text,
                    "answer": "",
                    "notes": "",
                }
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Generate the requested Markdown and CSV validation forms."""

    args = parse_args()
    template_paths = select_template_paths(
        Path(args.template_dir),
        args.template_filter,
        args.template_list,
    )
    template_payloads = [read_yaml(path) for path in template_paths]
    rendered_payloads = {
        str(payload["template_id"]): load_rendered_family(Path(args.generated_dir), str(payload["template_id"]))
        for payload in template_payloads
    }
    write_markdown(
        title=args.title,
        template_payloads=template_payloads,
        rendered_payloads=rendered_payloads,
        output_path=Path(args.output_md),
    )
    write_csv(template_payloads, Path(args.output_csv))
    print(Path(args.output_md))
    print(Path(args.output_csv))


if __name__ == "__main__":
    main()
