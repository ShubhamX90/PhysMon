#!/usr/bin/env python3
"""Fail lint when repository text makes disallowed PhysMon scientific claims.

Reference: Part V.4 rule 6 of the implementation brief.
"""

from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = ("src", "scripts", "tests", "docs")
SKIP_PATHS = {
    Path("scripts/check_forbidden_phrases.py"),
}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".jsonl", ".sh"}
FORBIDDEN_PHRASES = (
    "reasoning" + " circuit",
    "identified the shortcut" + " mechanism",
    "proved shortcut" + " use",
)


def main() -> None:
    """Scan committed text sources for forbidden scientific-claim phrases."""
    violations: list[str] = []
    for relative_root in SEARCH_ROOTS:
        root_path = REPOSITORY_ROOT / relative_root
        if not root_path.exists():
            continue
        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            relative_path = file_path.relative_to(REPOSITORY_ROOT)
            if relative_path in SKIP_PATHS or file_path.suffix not in TEXT_SUFFIXES:
                continue
            violations.extend(_scan_file(file_path, relative_path))

    if violations:
        print("Forbidden scientific-claim phrases detected:", file=sys.stderr)
        for violation in violations:
            print(violation, file=sys.stderr)
        raise SystemExit(1)


def _scan_file(file_path: Path, relative_path: Path) -> list[str]:
    """Return violation strings for one text file."""
    violations: list[str] = []
    text = file_path.read_text(encoding="utf-8")
    lowered_lines = text.lower().splitlines()
    for line_number, line in enumerate(lowered_lines, start=1):
        for forbidden_phrase in FORBIDDEN_PHRASES:
            if forbidden_phrase in line:
                violations.append(f"{relative_path}:{line_number}: contains '{forbidden_phrase}'")
    return violations


if __name__ == "__main__":
    main()
