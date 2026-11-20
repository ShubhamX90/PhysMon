"""Three grading views, a dimension-checked relative error and all-match foil matching (Stage 15; plan of record Section 4.5).

Views, always reported together:

* `declared`: grader version v2 (amendment A2, 2026-11-20): exact unit, absolute error at most max(half a unit in the last
  printed place, 0.1% of the gold) and at most 0.5% of the gold. Primary.
* `declared_v1` (extra view, not in `VIEWS`): the Stage 14 rule (protocol 4b, `v2_scorer.classify_answer`): exact unit, within
  half a unit in the last printed place AND within 0.5% of the gold. Kept so v1 stays reproducible.
* `convertible`: the v2 rule after converting the answer to the gold unit (v1 form: `unit_convertible.classify_convertible`).
* `rel1pct`: relative error at most 1% after a dimension-checked conversion to the gold unit (the field convention of UGPhysics
  and PHYSICS). An answer in a unit of another dimension, or an unknown unit, is wrong under this view and is flagged.

Foil matching (outcome O4): a parsed answer, converted to the gold unit, is compared with every prespecified foil value (misuse
curves, the cue value, the placebo). Every foil it matches is kept: `UNIQUE_MATCH`, `MULTI_MATCH` or `NO_MATCH`. A match is never
evidence of a misuse on its own; misuse hypotheses are read as curves across values in the analysis.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from physmon.scoring import unit_convertible as uc
from physmon.scoring import v2_scorer as vs

GRADER_VERSION = "v2"
VIEWS = ("declared", "convertible", "rel1pct")
EXTRA_VIEWS = ("declared_v1",)
ALL_VIEWS = VIEWS + EXTRA_VIEWS
V2_FLOOR_REL_TOL = 1e-3  # A2: the rounding test never demands more than 0.1% of the gold
REL_1PCT = 0.01
DIMENSION_STATUSES = ("SAME_UNIT", "CONVERTED", "WRONG_DIMENSION", "UNKNOWN_UNIT", "NOT_PARSED")
MATCH_CLASSES = ("UNIQUE_MATCH", "MULTI_MATCH", "NO_MATCH", "NOT_PARSED")
_TINY = 1e-300


@dataclass(frozen=True)
class Converted:
    """A parsed answer expressed in the gold unit."""

    status: str  # one of DIMENSION_STATUSES
    value: float | None  # the answer in the gold unit, when convertible
    ratio: float | None


def to_gold_unit(parsed: vs.ParsedOutput, gold_unit: str) -> Converted:
    """Convert a parsed answer to the gold unit with the dimension registry; never across dimensions."""

    if parsed.status != "PARSED" or parsed.value is None:
        return Converted("NOT_PARSED", None, None)
    if parsed.unit == vs.normalise_unit(gold_unit) or uc.canonical_unit(parsed.unit or "") == uc.canonical_unit(gold_unit):
        return Converted("SAME_UNIT", parsed.value, 1.0)
    ratio = uc.conversion_ratio(parsed.unit or "", gold_unit)
    if ratio is not None:
        return Converted("CONVERTED", parsed.value * ratio, ratio)
    from physmon.benchmark.v2 import dimensions as dm

    known = {uc.canonical_unit(parsed.unit or ""), uc.canonical_unit(gold_unit)} <= (set(dm.UNITS) | set(uc.COUNT_UNITS))
    return Converted("WRONG_DIMENSION" if known else "UNKNOWN_UNIT", None, None)


def relative_error_dimchecked(parsed: vs.ParsedOutput, gold_value: float, gold_unit: str) -> float | None:
    """|answer - gold| / |gold| after conversion to the gold unit; None if not parsed or not convertible."""

    converted = to_gold_unit(parsed, gold_unit)
    if converted.value is None:
        return None
    return abs(converted.value - gold_value) / max(abs(gold_value), _TINY)


def grade_rel1pct(parsed: vs.ParsedOutput, gold_value: float, gold_unit: str, tol: float = REL_1PCT) -> str:
    """`correct`, `wrong`, or the parse status (never `wrong` for an answer that was not parsed)."""

    if parsed.status != "PARSED":
        return parsed.status
    error = relative_error_dimchecked(parsed, gold_value, gold_unit)
    if error is None:
        return "wrong"
    return "correct" if error <= tol * (1 + 1e-9) else "wrong"


def value_ok_v2(error: float, half_unit: float, gold_value: float) -> bool:
    """Grader v2 value test: error <= max(half_unit, 0.1% of gold) and error <= 0.5% of gold (v1 accepts imply v2 accepts)."""

    scale = max(abs(gold_value), _TINY)
    return error <= max(half_unit, V2_FLOOR_REL_TOL * scale) * (1 + 1e-9) and error <= vs.COARSE_REL_TOL * scale


def classify_declared_v2(parsed: vs.ParsedOutput, gold_value: float, gold_unit: str) -> str:
    """Grader v2 `declared`: exact gold unit, then `value_ok_v2`; the parse status when nothing was parsed."""

    if parsed.status != "PARSED":
        return parsed.status
    right_unit = parsed.unit == vs.normalise_unit(gold_unit)
    error = abs(parsed.value - gold_value)
    return "correct" if right_unit and value_ok_v2(error, vs.half_unit_in_last_place(parsed.value_text), gold_value) else "wrong"


def classify_convertible_v2(parsed: vs.ParsedOutput, gold_value: float, gold_unit: str) -> str:
    """Grader v2 `convertible`: `classify_declared_v2` after conversion to the gold unit (same conversion as v1)."""

    if parsed.status != "PARSED":
        return parsed.status
    if parsed.unit == vs.normalise_unit(gold_unit) or uc.canonical_unit(parsed.unit) == uc.canonical_unit(gold_unit):
        ratio = 1.0
    else:
        ratio = uc.conversion_ratio(parsed.unit, gold_unit)
        if ratio is None:
            return "wrong"
    error = abs(parsed.value * ratio - gold_value)
    return "correct" if value_ok_v2(error, vs.half_unit_in_last_place(parsed.value_text) * ratio, gold_value) else "wrong"


def grade_all(parsed: vs.ParsedOutput, gold_value: float, gold_unit: str) -> dict[str, object]:
    """All views (v2 declared and convertible, `declared_v1`, rel1pct) plus the conversion status and the dimension-checked relative error."""

    converted = to_gold_unit(parsed, gold_unit)
    return {
        "declared": classify_declared_v2(parsed, gold_value, gold_unit),
        "declared_v1": vs.classify_answer(parsed, gold_value, gold_unit),
        "convertible": classify_convertible_v2(parsed, gold_value, gold_unit),
        "rel1pct": grade_rel1pct(parsed, gold_value, gold_unit),
        "dimension_status": converted.status,
        "value_in_gold_unit": converted.value,
        "relative_error_dimchecked": (abs(converted.value - gold_value) / max(abs(gold_value), _TINY)
                                      if converted.value is not None else None),
    }


def within(value: float, target: float, rel_tol: float) -> bool:
    """|value - target| <= rel_tol * max(|value|, |target|); exact zero matches only exact zero."""

    if not (math.isfinite(value) and math.isfinite(target)):
        return False
    scale = max(abs(value), abs(target))
    if scale == 0.0:
        return True
    return abs(value - target) <= rel_tol * scale * (1 + 1e-12)


def match_foils(value_in_gold_unit: float | None, foils: Mapping[str, float | None], rel_tol: float = vs.COARSE_REL_TOL
                ) -> dict[str, object]:
    """Every foil the answer matches within `rel_tol`; the class says whether it matched one, several or none."""

    if value_in_gold_unit is None:
        return {"match_class": "NOT_PARSED", "matches": []}
    matches = sorted(name for name, foil in foils.items() if foil is not None and within(value_in_gold_unit, float(foil), rel_tol))
    if not matches:
        return {"match_class": "NO_MATCH", "matches": []}
    return {"match_class": "UNIQUE_MATCH" if len(matches) == 1 else "MULTI_MATCH", "matches": matches}


def separated(values: Mapping[str, float], rel_tol: float) -> list[tuple[str, str]]:
    """Pairs of named values that are NOT separated by more than `rel_tol` (used by generators and certificates)."""

    names = sorted(values)
    return [(a, b) for i, a in enumerate(names) for b in names[i + 1:] if within(values[a], values[b], rel_tol)]
