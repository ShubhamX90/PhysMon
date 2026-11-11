"""Three grading views, a dimension-checked relative error and all-match foil matching (Stage 15; plan of record Section 4.5).

Views, always reported together:

* `declared`: the Stage 14 declared rule (protocol 4b, `v2_scorer.classify_answer`): exact unit, within half a unit in the
  last printed place and within 0.5% of the gold. Primary.
* `convertible`: the same rule after converting the answer to the gold unit (`unit_convertible.classify_convertible`).
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

VIEWS = ("declared", "convertible", "rel1pct")
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

    known = {uc.canonical_unit(parsed.unit or ""), uc.canonical_unit(gold_unit)} <= set(dm.UNITS)
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


def grade_all(parsed: vs.ParsedOutput, gold_value: float, gold_unit: str) -> dict[str, object]:
    """All three views plus the conversion status and the dimension-checked relative error."""

    converted = to_gold_unit(parsed, gold_unit)
    return {
        "declared": vs.classify_answer(parsed, gold_value, gold_unit),
        "convertible": uc.classify_convertible(parsed, gold_value, gold_unit),
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
