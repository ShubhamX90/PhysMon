"""Tests for the three grading views, the dimension-checked relative error and all-match foil matching (Stage 15)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.scoring import grading_views as gv  # noqa: E402
from physmon.scoring.v2_scorer import ParsedOutput  # noqa: E402


def p(value: float, unit: str, text: str | None = None) -> ParsedOutput:
    return ParsedOutput("PARSED", value, unit, text or repr(value))


def test_same_unit_answer_within_1_percent_but_off_in_printed_precision():
    views = gv.grade_all(p(2.19, "m/s^2", "2.19"), 2.177777, "m/s^2")
    assert views["declared"] == "wrong" and views["rel1pct"] == "correct" and views["dimension_status"] == "SAME_UNIT"
    assert views["relative_error_dimchecked"] == pytest.approx(abs(2.19 - 2.177777) / 2.177777)


def test_converted_units_are_graded_after_a_dimension_check():
    views = gv.grade_all(p(1.125, "J", "1.125"), 1125.0, "mJ")
    assert views["declared"] == "wrong" and views["convertible"] == "correct" and views["rel1pct"] == "correct"
    assert views["dimension_status"] == "CONVERTED" and views["value_in_gold_unit"] == pytest.approx(1125.0)


def test_an_answer_in_another_dimension_is_wrong_and_flagged_never_converted():
    views = gv.grade_all(p(2.17, "W", "2.17"), 2.17, "m/s^2")
    assert views["rel1pct"] == "wrong" and views["dimension_status"] == "WRONG_DIMENSION"
    assert views["relative_error_dimchecked"] is None
    unknown = gv.grade_all(p(2.17, "flurbs", "2.17"), 2.17, "m/s^2")
    assert unknown["dimension_status"] == "UNKNOWN_UNIT"


def test_unparsed_answers_carry_their_status_in_every_view_never_wrong():
    for status in ("BUDGET_EXHAUSTED", "FORMAT_INVALID", "UNPARSEABLE", "EMPTY", "MULTIPLE_CANDIDATES"):
        views = gv.grade_all(ParsedOutput(status), 2.0, "m")
        assert views["declared"] == status and views["convertible"] == status and views["rel1pct"] == status
        assert views["dimension_status"] == "NOT_PARSED"


def test_foil_matching_keeps_every_match():
    foils = {"copy": 2.83, "substitute": 2.83 * 1.001, "add": 5.0, "placebo": None}
    both = gv.match_foils(2.831, foils, rel_tol=0.005)
    assert both["match_class"] == "MULTI_MATCH" and both["matches"] == ["copy", "substitute"]
    one = gv.match_foils(5.01, foils, rel_tol=0.005)
    assert one == {"match_class": "UNIQUE_MATCH", "matches": ["add"]}
    assert gv.match_foils(9.0, foils)["match_class"] == "NO_MATCH"
    assert gv.match_foils(None, foils)["match_class"] == "NOT_PARSED"


def test_within_handles_zero_and_sign():
    assert gv.within(0.0, 0.0, 0.01) and not gv.within(1e-9, 0.0, 0.01)
    assert not gv.within(-2.0, 2.0, 0.01) and gv.within(-2.0, -2.01, 0.01)


def test_separated_lists_only_pairs_inside_the_tolerance():
    values = {"gold": 10.0, "copy": 10.04, "substitute": 20.0}
    assert gv.separated(values, 0.005) == [("copy", "gold")]
    assert gv.separated(values, 0.001) == []
