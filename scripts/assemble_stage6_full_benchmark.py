#!/usr/bin/env python3
"""Assemble the frozen 140-family Stage 6 benchmark into one rendered directory.

Reference:
    physmon_proposal.pdf §7 and Stage 6 benchmark-freeze workflow.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DEFAULT_INPUT_DIRS = (
    "data/generated",
    "results/stage6/generated_phase1_full",
    "results/stage6/generated_phase2_ad",
    "results/stage6/generated_phase2_bce",
)
EXPECTED_FAMILY_COUNT = 140


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for benchmark assembly."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dirs",
        nargs="+",
        default=list(DEFAULT_INPUT_DIRS),
        help="Ordered list of rendered-family directories to merge.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/stage6/generated_full_benchmark",
        help="Destination directory for the merged rendered-family JSON files.",
    )
    parser.add_argument(
        "--summary-path",
        default="results/stage6/generated_full_benchmark/assembly_summary.json",
        help="Path for the assembly summary JSON.",
    )
    return parser.parse_args()


def main() -> None:
    """Copy rendered-family JSON files into one frozen full-benchmark directory."""

    args = parse_args()
    output_dir = Path(args.output_dir)
    summary_path = Path(args.summary_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    copied: dict[str, str] = {}
    by_source: dict[str, int] = {}
    duplicates: dict[str, list[str]] = {}

    for input_dir_text in args.input_dirs:
        input_dir = Path(input_dir_text)
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
        family_paths = sorted(input_dir.glob("*.json"))
        by_source[str(input_dir)] = len(family_paths)
        for family_path in family_paths:
            template_id = family_path.stem
            if template_id in copied:
                duplicates.setdefault(template_id, [copied[template_id]]).append(str(family_path))
                continue
            destination = output_dir / family_path.name
            shutil.copy2(family_path, destination)
            copied[template_id] = str(family_path)

    if duplicates:
        duplicate_lines = ", ".join(
            f"{template_id}: {paths}" for template_id, paths in sorted(duplicates.items())
        )
        raise RuntimeError(f"Duplicate template IDs encountered during assembly: {duplicate_lines}")

    merged_files = sorted(output_dir.glob("*.json"))
    if len(merged_files) != EXPECTED_FAMILY_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_FAMILY_COUNT} merged family JSON files, found {len(merged_files)}."
        )

    payload = {
        "expected_family_count": EXPECTED_FAMILY_COUNT,
        "merged_family_count": len(merged_files),
        "source_counts": by_source,
        "output_dir": str(output_dir.resolve()),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(output_dir)
    print(summary_path)


if __name__ == "__main__":
    main()
