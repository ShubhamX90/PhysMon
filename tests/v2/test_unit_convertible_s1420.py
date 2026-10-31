"""Tests for the Stage 14.20 unit-convertible sensitivity grading."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract as rc  # noqa: E402
from physmon.scoring import unit_convertible as uc  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402


def parsed(text):
    return rc.parse_final(f"Final answer: {text}").parsed


def test_the_four_speed_test_mismatches_are_correct_when_units_are_convertible_and_wrong_by_the_declared_rule():
    cases = [("1.125 J", 1125.0, "mJ"), ("720 pC", 0.72, "nC"), ("4.2 degrees", 4.2027, "deg"), ("3885 years", 3885.35, "yr")]
    for answer, gold, unit in cases:
        p = parsed(answer)
        assert vs.classify_answer(p, gold, unit) == "wrong"
        assert uc.classify_convertible(p, gold, unit) == "correct", answer


def test_it_equals_the_declared_rule_when_the_units_already_match_and_keeps_the_precision_rule():
    assert uc.classify_convertible(parsed("2.18 m/s^2"), 2.1777, "m/s^2") == vs.classify_answer(parsed("2.18 m/s^2"), 2.1777, "m/s^2") == "correct"
    assert uc.classify_convertible(parsed("2.17 m/s^2"), 2.1777, "m/s^2") == "wrong"
    assert uc.classify_convertible(parsed("2 m"), 2.178, "m") == "wrong"  # too coarse for the 0.5% guard
    assert uc.classify_convertible(parsed("1.1 J"), 1125.0, "mJ") == "wrong"  # right unit family, wrong value after conversion
    assert uc.classify_convertible(parsed("1.13 J"), 1125.0, "mJ") == "correct"  # 1.125 rounded to the printed precision
    assert uc.classify_convertible(parsed("1.14 J"), 1125.0, "mJ") == "wrong"  # outside half a unit of the last printed place


def test_a_unit_of_another_dimension_an_unknown_unit_or_a_dimensionless_gold_stays_wrong():
    assert uc.classify_convertible(parsed("1125 W"), 1125.0, "mJ") == "wrong"
    assert uc.classify_convertible(parsed("5 furlongs"), 5.0, "m") == "wrong"
    assert uc.classify_convertible(parsed("0.5 deg"), 0.5, "1") == "wrong"
    assert uc.conversion_ratio("deg", "rad") == pytest.approx(0.017453292519943295)
    assert uc.conversion_ratio("kJ", "J") == 1000.0 and uc.conversion_ratio("J", "1") is None


def test_ungraded_parse_statuses_pass_through_and_micro_sign_spellings_are_accepted():
    assert uc.classify_convertible(rc.parse_final("no final line", hit_token_limit=True).parsed, 5.0, "m") == "TRUNCATED"
    assert uc.canonical_unit("µm") == "μm" and uc.canonical_unit("Years") == "yr" and uc.canonical_unit("m/s²") == "m/s^2"
