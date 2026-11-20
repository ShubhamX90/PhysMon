"""Grader version v2 (amendment A2): examples from the G2 pilot, the v1 view, and the property that v2 never rejects what v1 accepts."""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from physmon.scoring import grading_views as gv  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402


def parsed(text: str, unit: str) -> vs.ParsedOutput:
    return vs.ParsedOutput("PARSED", float(text), vs.normalise_unit(unit), text)


def views(text: str, unit: str, gold: float, gold_unit: str) -> dict:
    return gv.grade_all(parsed(text, unit), gold, gold_unit)


def test_version_and_extra_view():
    assert gv.GRADER_VERSION == "v2" and "declared_v1" in gv.EXTRA_VIEWS and "declared_v1" not in gv.VIEWS
    assert views("1", "m", 1.0, "m").keys() >= {"declared", "declared_v1", "convertible", "rel1pct"}


def test_more_digits_correct_in_v2_wrong_in_v1():
    g = views("1367.71", "m/s", 1367.7170760065842, "m/s")
    assert g["declared"] == "correct" and g["convertible"] == "correct" and g["declared_v1"] == "wrong"
    g = views("6.607", "V", 6.608052430593341, "V")
    assert g["declared"] == "correct" and g["declared_v1"] == "wrong"


def test_near_match_cue_copy_wrong():
    gold = 1367.7
    g = views(f"{gold * 1.011:.5g}", "m/s", gold, "m/s")  # 1.1% off
    assert g["declared"] == g["declared_v1"] == g["convertible"] == "wrong"


def test_point3_percent_off_printed_precisely_wrong_in_both():
    g = views("1371.8", "m/s", 1367.7, "m/s")  # error 4.1 > 0.1% of gold (1.37) and > half-ULP 0.05
    assert g["declared"] == g["declared_v1"] == "wrong"


def test_correct_rounding_correct_in_both():
    g = views("1370", "m/s", 1367.7, "m/s")  # 0.17% off; the parser reads "1370" as printed to the unit (half-ULP 0.5)
    g2 = views("1.37e3", "m/s", 1367.7, "m/s")  # three significant figures, half-ULP 5
    assert g2["declared"] == g2["declared_v1"] == "correct"
    assert g["declared"] == "wrong" and g["declared_v1"] == "wrong"  # error 2.3 > max(0.5, 1.37)


def test_unit_mismatch_wrong():
    g = views("1367.7", "km/s", 1367.7, "m/s")
    assert g["declared"] == g["declared_v1"] == "wrong"
    assert views("1367.7", "m/s", 1367.7, "m/s")["declared"] == "correct"


def test_convertible_applies_v2_after_conversion():
    g = views("1.36771", "km/s", 1367.7170760065842, "m/s")
    assert g["declared"] == "wrong" and g["convertible"] == "correct"


def test_non_parsed_status_passes_through():
    p = vs.ParsedOutput("UNPARSEABLE")
    g = gv.grade_all(p, 1.0, "m")
    assert g["declared"] == g["declared_v1"] == g["convertible"] == "UNPARSEABLE"


def test_v2_never_rejects_what_v1_accepts_and_v1_unchanged():
    rng = random.Random(206)
    n_gain = 0
    for _ in range(20000):
        gold = rng.uniform(-1, 1) * 10 ** rng.uniform(-4, 6)
        if gold == 0:
            continue
        rel = rng.choice([0, 1e-6, 1e-4, 5e-4, 1e-3, 2e-3, 4e-3, 6e-3, 2e-2]) * rng.uniform(-1, 1)
        sf = rng.randint(1, 9)
        text = f"{gold * (1 + rel):.{sf}e}"
        if rng.random() < 0.5:
            text = f"{float(text):.{rng.randint(0, 6)}f}"
        p = parsed(text, "m")
        v1, v2 = vs.classify_answer(p, gold, "m"), gv.classify_declared_v2(p, gold, "m")
        assert gv.grade_all(p, gold, "m")["declared_v1"] == v1
        if v1 == "correct":
            assert v2 == "correct"
        n_gain += v1 == "wrong" and v2 == "correct"
        if v2 == "correct":
            assert abs(p.value - gold) <= 0.005 * abs(gold) * (1 + 1e-9)
    assert n_gain > 0
