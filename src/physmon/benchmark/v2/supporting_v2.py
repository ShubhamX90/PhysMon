"""Supporting cells of M0 v2: the October conditions regenerated for one base instance, with certified tolerance status.

The October design (`design.py`) cued the answer with a same-unit value at a "near" distance, but its near cells (5.38 and
5.4 for a gold of 5.387) lay inside or at the edge of the grading tolerance and no cell held the displayed gold itself.
Here the proximity of a same-unit value on a separate object is a set of distinct, certified conditions:

* `exact`: the displayed gold (four significant figures); graded correct by every view, so a copy would be a correct answer
  (`cue_equals_gold`; `source_ambiguous` by design);
* `near_high_overlap`, `near_low_overlap`: a value 1.1% to 5% from the gold that is graded wrong by the declared rule, the
  convertible rule and the 1% rule, sharing at least two (high) or at most one (low) leading digits with the gold;
* `moderate` (1.3 times the gold) and `far` (5 times the gold), as in October;
* `incompatible_unit_same_digits`: the digits of the displayed gold with a unit of another dimension;
* `convertible_unit_same_magnitude`: the gold's magnitude in a convertible unit (different digits), graded correct by the
  convertible and 1% views (`source_ambiguous` by design, listed in `ambiguous_views`).

Each cell records its tolerance status under the three grading views (`physmon.scoring.grading_views`) and is flagged
`source_ambiguous` when a cue that is meant to be wrong lies inside a tolerance.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import graph as gr
from physmon.scoring import grading_views as gv
from physmon.scoring import unit_convertible as uc
from physmon.scoring import v2_scorer as vs

NEAR_OUTSIDE_MIN = 0.011  # the 1% grading rule plus a margin: a near cue is at least 1.1% from the gold
NEAR_OUTSIDE_MAX = 0.05
HIGH_OVERLAP_MIN = 2
LOW_OVERLAP_MAX = 1
EXACT_SIGNIFICANT = 4
METADATA_VALUE = 21.0

PROXIMITY_CELLS = ("nongov_same_unit_exact", "nongov_same_unit_near_high_overlap", "nongov_same_unit_near_low_overlap",
                   "nongov_same_unit_moderate", "nongov_same_unit_far", "nongov_incompatible_unit_same_digits",
                   "nongov_convertible_unit_same_magnitude")
DESIGN_CELLS = ("nonnumeric_extra", "numeric_metadata", "relevant_edit", "role_reversal")
BY_DESIGN_AMBIGUOUS = ("nongov_same_unit_exact", "nongov_convertible_unit_same_magnitude")
ALL_CELLS = ("nonnumeric_extra", "numeric_metadata", *PROXIMITY_CELLS, "relevant_edit", "role_reversal")


def tolerance_status(value: float, unit: str, gold: float, gold_unit: str, significant: int = 4) -> dict[str, Any]:
    """How the three grading views grade an answer equal to `value` `unit` against `gold` `gold_unit`; the numeral is
    printed with `significant` figures (the printed text sets the last-place tolerance of the declared rule)."""

    text = dg.positional(value, significant)
    parsed = vs.ParsedOutput("PARSED", float(text), vs.normalise_unit(dg.display_unit(unit)), text)
    graded = gv.grade_all(parsed, gold, gold_unit)
    return {"numeral": text, "declared": graded["declared"], "convertible": graded["convertible"],
            "rel1pct": graded["rel1pct"], "dimension_status": graded["dimension_status"],
            "relative_error": graded["relative_error_dimchecked"]}


def near_value(gold: float, high_overlap: bool, gold_unit: str) -> tuple[float | None, dict[str, Any] | None]:
    """The smallest-deviation three-figure value 1.5% to 5% from the gold, graded wrong by every view, with the overlap asked."""

    magnitude = abs(gold)
    if magnitude < 1e-12:
        return None, None
    steps = sorted({round(NEAR_OUTSIDE_MIN + 0.0005 * k, 6) for k in range(int((NEAR_OUTSIDE_MAX - NEAR_OUTSIDE_MIN) / 0.0005) + 1)})
    for eps in sorted((s * sign for s in steps for sign in (-1, 1)), key=lambda e: (abs(e), e)):
        candidate = float(f"{magnitude * (1 + eps):.3g}")
        deviation = abs(candidate / magnitude - 1)
        if candidate <= 0 or not NEAR_OUTSIDE_MIN <= deviation <= NEAR_OUTSIDE_MAX:
            continue
        shared = dg.common_leading_digits(candidate, magnitude)
        if (high_overlap and shared < HIGH_OVERLAP_MIN) or (not high_overlap and shared > LOW_OVERLAP_MAX):
            continue
        status = tolerance_status(candidate, gold_unit, gold, gold_unit, 3)
        if all(status[v] == "wrong" for v in gv.VIEWS):
            return candidate, {**status, "shared_leading_digits": shared, "deviation": deviation}
    return None, None


@dataclasses.dataclass
class Support:
    structure_id: str
    instance: int
    cell_id: str
    condition: str
    feasible: bool
    reason: str = ""
    prompt: str = ""
    cue_value: float | None = None
    cue_unit: str | None = None
    gold_value: float = 0.0
    gold_unit: str = ""
    expected_effect: str = "invariant"
    factors: dict[str, str] = dataclasses.field(default_factory=dict)
    foils: dict[str, float] = dataclasses.field(default_factory=dict)
    tolerance: dict[str, Any] | None = None
    cue_equals_gold: bool = False
    source_ambiguous: bool = False
    ambiguous_by_design: bool = False
    ambiguous_views: list[str] = dataclasses.field(default_factory=list)
    marker_free: bool | None = None
    input_display: dict[str, float] | None = None
    sentence: str = ""
    base_gold: float = 0.0


def _factors(role: str, proximity: str, unit: str, overlap: str, isolation: str) -> dict[str, str]:
    return {"cue_semantic_role": role, "numeric_proximity": proximity, "unit_type": unit, "digit_overlap": overlap,
            "cue_position": dg.CUE_POSITION, "isolation_condition": isolation}


def _assemble(structure: gr.Structure, display: dict[str, float], extra: str, question: str | None = None) -> str:
    context = dg.context_text(structure, display)
    return f"{context} {extra}\n\n{question or dg.question_text(structure, display)}"


def support_cells(structure: gr.Structure, instance: int = 0) -> list[Support]:
    from physmon.benchmark.v2 import rolevalue_v2 as r2  # local import: r2 does not depend on this module

    render = structure.render
    display = dict(structure.instances[instance])
    gold = dg.gold_for(structure, display)
    gold_unit = render.target_unit
    target_dim = dm.UNITS[gold_unit].dim
    out: list[Support] = []

    def base(cid: str, **kw: Any) -> Support:
        fields = {"gold_value": gold, "gold_unit": gold_unit, "input_display": display, "base_gold": gold, "feasible": True, **kw}
        return Support(structure.structure_id, instance, cid, cid, **fields)

    def cue_cell(cid: str, template: str, value: float, unit: str, factors: dict[str, str], significant: int,
                 foils: dict[str, float], tolerance: dict[str, Any] | None, equals: bool) -> Support:
        text = dg.positional(value, significant)
        sentence = template.format(v=text, u=dg.display_unit(unit))
        cell = base(cid, prompt=_assemble(structure, display, sentence), cue_value=float(text), cue_unit=unit, factors=factors,
                    foils=foils, tolerance=tolerance, cue_equals_gold=equals, sentence=sentence)
        cell.marker_free = not r2.marker_hits(sentence)
        # a cue that any grading view marks correct could be the source of a correct answer: source_ambiguous. The exact-match
        # cell (graded correct by every view) and the convertible-unit cell (correct under the convertible and 1% views) are
        # source-ambiguous BY DESIGN (`ambiguous_by_design`); every other proximity cell is certified outside all three views.
        if tolerance is not None:
            cell.ambiguous_views = [v for v in gv.VIEWS if tolerance[v] == "correct"]
            cell.source_ambiguous = bool(cell.ambiguous_views)
            cell.ambiguous_by_design = cid in BY_DESIGN_AMBIGUOUS
        return cell

    # October cells reused as designed: non-numeric extra, numeric metadata, edit, role reversal
    for cid in ("nonnumeric_extra", "numeric_metadata", "relevant_edit", "role_reversal"):
        rendered = dg.render_cell(structure, instance, cid)
        if not rendered.feasible:
            out.append(base(cid, feasible=False, reason=rendered.reason))
            continue
        cell = base(cid, prompt=rendered.prompt, cue_value=rendered.cue_value, cue_unit=rendered.cue_unit,
                    gold_value=rendered.gold_value or gold, expected_effect=rendered.expected_effect or "invariant",
                    factors=dict(rendered.factors or {}), input_display=rendered.input_display)
        sentence = {"nonnumeric_extra": render.nonnumeric_sentence,
                    "numeric_metadata": render.metadata_sentence.format(v=dg.positional(METADATA_VALUE, 3),
                                                                        u=render.metadata_unit),
                    "role_reversal": render.comparison_sentence.format(v=dg.positional(rendered.cue_value or 0, 3),
                                                                       u=dg.display_unit(gold_unit))
                    if cid == "role_reversal" else ""}.get(cid, "")
        cell.sentence = sentence
        cell.marker_free = not r2.marker_hits(sentence) if sentence else None
        if cid == "relevant_edit":
            cell.foils = {"neglect": gold}
            cell.expected_effect = "changes"
        if cid == "role_reversal":
            cell.foils = {"ignore_reference": gold, "copy": float(dg.positional(rendered.cue_value, 3))}
            cell.expected_effect = "changes"
        out.append(cell)
    # a changed answer must be separated from the base answer for edit and reversal
    for cell in out:
        if cell.cell_id in ("relevant_edit", "role_reversal") and cell.feasible:
            cell.source_ambiguous = not abs(cell.gold_value - gold) > 0.01 * max(abs(cell.gold_value), abs(gold))

    exact = float(dg.positional(gold, EXACT_SIGNIFICANT))
    status = tolerance_status(exact, gold_unit, gold, gold_unit)
    cell = cue_cell("nongov_same_unit_exact", render.isolated_sentence, exact, gold_unit,
                    _factors("nongoverning_isolated", "exact", "same", "full", "stated_isolated"), EXACT_SIGNIFICANT,
                    {"copy": exact}, status, True)
    out.append(cell)
    for cid, high in (("nongov_same_unit_near_high_overlap", True), ("nongov_same_unit_near_low_overlap", False)):
        value, status = near_value(gold, high, gold_unit)
        if value is None:
            out.append(base(cid, feasible=False, reason=f"no three-figure value {NEAR_OUTSIDE_MIN:.1%} to {NEAR_OUTSIDE_MAX:.0%} from "
                                                          f"the gold with {'at least 2' if high else 'at most 1'} shared leading "
                                                          "digits is graded wrong by all three views"))
            continue
        out.append(cue_cell(cid, render.isolated_sentence, value, gold_unit,
                            _factors("nongoverning_isolated", "near_outside_tolerance", "same", "high" if high else "low",
                                     "stated_isolated"), 3, {"copy": value}, status, False))
    for cid, factor, label in (("nongov_same_unit_moderate", dg.MODERATE_FACTOR, "moderate"), ("nongov_same_unit_far", dg.FAR_FACTOR, "far")):
        value = float(f"{abs(gold) * factor:.3g}")
        status = tolerance_status(value, gold_unit, gold, gold_unit, 3)
        out.append(cue_cell(cid, render.isolated_sentence, value, gold_unit,
                            _factors("nongoverning_isolated", label, "same", "not_controlled", "stated_isolated"), 3,
                            {"copy": value}, status, False))
    incompatible_dim = dm.UNITS[render.incompatible_unit].dim
    if incompatible_dim == target_dim:
        out.append(base("nongov_incompatible_unit_same_digits", feasible=False,
                        reason=f"the incompatible unit {render.incompatible_unit} has the target's dimension"))
    else:
        status = tolerance_status(exact, render.incompatible_unit, gold, gold_unit)
        out.append(cue_cell("nongov_incompatible_unit_same_digits", render.incompatible_sentence, exact, render.incompatible_unit,
                            _factors("nongoverning_isolated", "same_digits", "incompatible", "full", "stated_isolated"),
                            EXACT_SIGNIFICANT, {"digit_copy": exact}, status, False))
    if not render.equivalent_unit or dm.UNITS[render.equivalent_unit].dim != target_dim:
        out.append(base("nongov_convertible_unit_same_magnitude", feasible=False,
                        reason="no convertible unit of the target's dimension is defined"))
    else:
        value = float(dg.positional(dm.convert(abs(gold), gold_unit, render.equivalent_unit), EXACT_SIGNIFICANT))
        status = tolerance_status(value, render.equivalent_unit, gold, gold_unit)
        ratio = uc.conversion_ratio(render.equivalent_unit, gold_unit)
        cell = cue_cell("nongov_convertible_unit_same_magnitude", render.isolated_sentence, value, render.equivalent_unit,
                        _factors("nongoverning_isolated", "equal_magnitude", "equivalent", "different_digits", "stated_isolated"),
                        EXACT_SIGNIFICANT, {"copy": value * (ratio or 1.0)}, status, False)
        cell.cue_equals_gold = False
        out.append(cell)
    return out
