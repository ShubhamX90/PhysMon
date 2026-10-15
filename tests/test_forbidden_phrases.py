"""The forbidden-claim checker must still flag the phrases, with a minimal exemption list."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_forbidden_phrases.py"
spec = importlib.util.spec_from_file_location("check_forbidden_phrases_for_test", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_flags_each_forbidden_phrase(tmp_path):
    for phrase in checker.FORBIDDEN_PHRASES:
        file = tmp_path / "note.md"
        file.write_text(f"We report a {phrase} here.\n", encoding="utf-8")
        violations = checker._scan_file(file, Path("docs/note.md"))
        assert violations and phrase in violations[0]


def test_clean_text_is_not_flagged(tmp_path):
    file = tmp_path / "note.md"
    file.write_text("The probe predicts sensitivity; it is a monitor signal.\n", encoding="utf-8")
    assert checker._scan_file(file, Path("docs/note.md")) == []


def test_exemptions_are_limited_to_the_checker_and_one_verbatim_extraction():
    assert checker.SKIP_PATHS == {
        Path("scripts/check_forbidden_phrases.py"),
        Path("docs/proposals/PhysMon_Research_v2.extracted.txt"),
    }
