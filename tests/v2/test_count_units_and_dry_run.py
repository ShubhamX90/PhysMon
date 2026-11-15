"""Tests for count and money units in the grading stack and for the grading dry run (Stage 15; admission checks 4.1 and 4.2)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract_v2 as rc2  # noqa: E402
from physmon.scoring import grading_views as gv  # noqa: E402
from physmon.scoring import unit_convertible as uc  # noqa: E402
from physmon.scoring.v2_scorer import ParsedOutput  # noqa: E402

_spec = importlib.util.spec_from_file_location("s194", REPO_ROOT / "scripts" / "v2" / "s194_grading_dry_run.py")
s194 = importlib.util.module_from_spec(_spec)
sys.modules["s194"] = s194
_spec.loader.exec_module(s194)


def p(value: float, unit: str, text: str | None = None) -> ParsedOutput:
    return ParsedOutput("PARSED", value, unit, text or str(value))


def final_line(value: str, unit: str) -> ParsedOutput:
    return rc2.assess(f"Final answer: {value} {unit}", hit_token_limit=False, thinking_expected=False).parsed


def test_count_unit_exact_and_singular_plural():
    views = gv.grade_all(p(12.0, "cookies", "12"), 12.0, "cookies")
    assert (views["declared"], views["convertible"], views["rel1pct"]) == ("correct", "correct", "correct")
    singular = gv.grade_all(p(1.0, "cookie", "1"), 1.0, "cookies")
    assert singular["declared"] == "wrong"  # the primary view still needs the exact unit string
    assert singular["convertible"] == "correct" and singular["rel1pct"] == "correct" and singular["dimension_status"] == "SAME_UNIT"


def test_counts_of_different_nouns_are_never_interconvertible():
    views = gv.grade_all(p(12.0, "students", "12"), 12.0, "cookies")
    assert (views["declared"], views["convertible"], views["rel1pct"]) == ("wrong", "wrong", "wrong")
    assert views["dimension_status"] == "WRONG_DIMENSION" and views["value_in_gold_unit"] is None
    assert uc.conversion_ratio("cookies", "students") is None and uc.conversion_ratio("cookie", "cookies") == 1.0
    assert gv.grade_all(p(12.0, "dollars", "12"), 12.0, "points")["dimension_status"] == "WRONG_DIMENSION"


def test_count_is_not_convertible_to_a_physical_unit_or_unknown_noun():
    assert gv.grade_all(p(5.0, "s", "5"), 5.0, "buses")["dimension_status"] == "WRONG_DIMENSION"
    assert gv.grade_all(p(5.0, "buses", "5"), 5.0, "s")["rel1pct"] == "wrong"
    unknown = gv.grade_all(p(5.0, "flurbs", "5"), 5.0, "buses")
    assert unknown["dimension_status"] == "UNKNOWN_UNIT" and unknown["rel1pct"] == "wrong"


def test_money_spellings_under_the_contract_final_line():
    for unit in ("dollars", "dollar", "$", "USD", "usd"):
        views = gv.grade_all(final_line("36", unit), 36.0, "dollars")
        assert views["convertible"] == "correct" and views["rel1pct"] == "correct", unit
    assert gv.grade_all(final_line("36", "dollars"), 36.0, "dollars")["declared"] == "correct"
    assert gv.grade_all(final_line("36", "$"), 36.0, "dollars")["declared"] == "wrong"
    # "$36" and "USD 36" are not the contract format (the number comes first), so they are unparseable, never graded
    for text in ("Final answer: $36", "Final answer: USD 36"):
        assert rc2.assess(text, hit_token_limit=False, thinking_expected=False).parsed.status == "UNPARSEABLE"
    assert gv.grade_all(final_line("37", "dollars"), 36.0, "dollars")["rel1pct"] == "wrong"


def test_minutes_are_time_and_convert_through_the_time_dimension():
    assert uc.canonical_unit("minutes") == "min" and uc.canonical_unit("minute") == "min"
    for value, unit in ((1.5, "h"), (5400.0, "s"), (90.0, "minutes"), (90.0, "minute")):
        views = gv.grade_all(final_line(f"{value:g}", unit), 90.0, "minutes")
        assert views["convertible"] == "correct" and views["rel1pct"] == "correct", unit
    assert gv.grade_all(final_line("90", "minutes"), 90.0, "minutes")["declared"] == "correct"
    assert gv.grade_all(final_line("90", "min"), 90.0, "minutes")["declared"] == "wrong"
    assert gv.grade_all(final_line("90", "students"), 90.0, "minutes")["dimension_status"] == "WRONG_DIMENSION"


def test_times_is_its_own_dimension_and_a_bare_number_is_never_accepted():
    assert gv.grade_all(final_line("3", "times"), 3.0, "times")["declared"] == "correct"
    assert gv.grade_all(final_line("3", "time"), 3.0, "times")["convertible"] == "correct"
    assert gv.grade_all(final_line("3", "students"), 3.0, "times")["rel1pct"] == "wrong"
    # a bare number has no final line in the contract; the unit "1" stays excluded from conversion, as for physical units
    assert rc2.assess("Final answer: 3", hit_token_limit=False, thinking_expected=False).parsed.status == "UNPARSEABLE"
    assert gv.grade_all(p(3.0, "1", "3"), 3.0, "times")["rel1pct"] == "wrong"
    assert gv.grade_all(p(3.0, "1", "3"), 3.0, "cookies")["convertible"] == "wrong"
    assert gv.grade_all(p(3.0, "1", "3"), 3.0, "m")["convertible"] == "wrong"  # unchanged physical rule


def test_physical_unit_canonicalisation_is_unchanged():
    assert uc.canonical_unit("meters") == "m" and uc.canonical_unit("Hz") == "Hz" and uc.canonical_unit("flurbs") == "flurbs"
    assert "points" not in uc.ALIASES and "dollars" not in uc.ALIASES  # the H4 extractor reads ALIASES; it must not change
    assert uc.conversion_ratio("mJ", "J") == pytest.approx(1e-3)


@pytest.mark.parametrize("dataset", ["m0_v2", "nonphysics_v1"])
def test_dry_run_on_committed_datasets_has_no_unexpected_failures(dataset):
    report = s194.run_dataset(REPO_ROOT / "data" / "v2" / "dataset" / dataset)
    assert report["n_unexpected_failures"] == 0, report["unexpected_failures"][:3]
    assert report["checks_by_family_and_view"]["gold:declared"]["checks"] == 3 * report["n_cells"]
    assert report["checks_by_family_and_view"]["gold_alt_unit:convertible"]["checks"] > 0


def test_dry_run_flags_a_foil_equal_to_the_gold_exempts_confounded_and_refuses_overwrite(tmp_path):
    base = {"job_id": "X:foil", "gold_value": 10.0, "gold_unit": "students", "foils": {"copy": 10.0}, "placebo": 11.0,
            "source_ambiguous": False, "ambiguous_views": [], "confounded": [], "tolerance_status": None, "unit": None}
    result = s194.dry_run_cell(base)
    assert [f["check"].split(":")[1] for f in result["failures"]] == ["copy", "copy"]
    exempt = s194.dry_run_cell({**base, "confounded": ["copy~gold"]})
    assert not exempt["failures"] and len(exempt["source_ambiguous_exempt"]) == 2
    (tmp_path / "ds").mkdir()
    (tmp_path / "ds" / "cells.jsonl").write_text(json.dumps(base) + "\n", encoding="utf-8")
    assert s194.main([str(tmp_path / "ds"), "--out-root", str(tmp_path / "out")]) == 1
    assert (tmp_path / "out" / "ds" / "report.json").exists() and (tmp_path / "out" / "ds" / "report.md").exists()
    assert s194.main([str(tmp_path / "ds"), "--out-root", str(tmp_path / "out")]) == 2  # refuses to overwrite


def test_dry_run_renders_every_format_through_the_contract_reader():
    for kind in ("plain_full", "plain_4sf", "sci_4sf", "plain_6sf", "sci_6sf"):
        for value in (3.0, 0.00123456, 6608052.43, -412.28, 1765.715):
            parsed = s194.read_back(s194.render(value, kind), "m")
            assert parsed.status == "PARSED" and parsed.value == pytest.approx(value, rel=1e-3), (kind, value)
