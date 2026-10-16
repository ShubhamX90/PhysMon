"""Factor cells, rendering and the factor-cell manifest (Stage 14.6; v2 B3.3, p.8; P2.2-P2.3, p.18-19).

Cells are predeclared before any model sees them. Each structure is rendered under:

- `no_cue` (anchor), `nonnumeric_extra` (style-matched sentence, no numeral), `numeric_metadata` (unrelated numeral);
- non-governing same-unit quantities at near distance (with high and with low leading-digit overlap), moderate and far
  distance; a non-governing quantity with the near numeral but an incompatible unit; and the same physical magnitude
  written in a convertible unit (equal magnitude, different digits);
- a relevant edit (a governing input changed, answer recomputed) and a role-reversal twin (the same measured
  quantity now enters the answer).

A cell that cannot be built without a nonsensical prompt is recorded with `feasible=False` and a reason (B3.3:
"explicitly record empty or impossible cells rather than inserting nonsensical prompts"). Proximity bands and the
digit-overlap rule are fixed here, not tuned on outcomes.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from typing import Any

import numpy as np
import sympy

from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import graph as gr

CELL_IDS = (
    "no_cue", "nonnumeric_extra", "numeric_metadata",
    "nongov_same_unit_near_high_overlap", "nongov_same_unit_near_low_overlap",
    "nongov_same_unit_moderate", "nongov_same_unit_far",
    "nongov_incompatible_unit_near", "nongov_same_magnitude_convertible_unit",
    "relevant_edit", "role_reversal",
)
NEAR_BAND = 0.01  # |cue / gold - 1| <= 1%
MODERATE_FACTOR = 1.3
FAR_FACTOR = 5.0
HIGH_OVERLAP_MIN = 2  # leading significant digits shared with the gold answer
LOW_OVERLAP_MAX = 1
CUE_POSITION = "after_context"
NAMESPACE = uuid.UUID("5d0f3c2a-61b4-5a58-9a0e-6e0c0b6f7e11")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


@dataclass
class CellRendering:
    structure_id: str
    instance: int
    cell_id: str
    feasible: bool
    reason: str
    prompt: str = ""
    cue_value: float | None = None
    cue_unit: str | None = None
    gold_value: float | None = None
    gold_unit: str = ""
    expected_effect: str = ""
    factors: dict[str, Any] | None = None
    input_display: dict[str, float] | None = None


def positional(value: float, significant: int) -> str:
    """Plain positional notation with `significant` figures and no exponent."""

    return np.format_float_positional(float(f"{value:.{significant}g}"), trim="-")


def _mantissa_digits(value: float) -> str:
    mantissa = f"{abs(value):.2e}".split("e")[0]  # 3 significant figures
    return mantissa.replace(".", "")


def common_leading_digits(a: float, b: float) -> int:
    da, db = _mantissa_digits(a), _mantissa_digits(b)
    count = 0
    for x, y in zip(da, db, strict=False):
        if x != y:
            break
        count += 1
    return count


def input_text(structure: gr.Structure, name: str, value: float) -> str:
    spec = structure.render.formats.get(name)
    if spec:
        return format(value, spec)
    return positional(value, 4)


def context_text(structure: gr.Structure, display_inputs: dict[str, float]) -> str:
    fields = {n.name: input_text(structure, n.name, display_inputs[n.name]) for n in structure.inputs}
    return structure.render.context.format(**fields)


def question_text(structure: gr.Structure, display_inputs: dict[str, float]) -> str:
    fields = {n.name: input_text(structure, n.name, display_inputs[n.name]) for n in structure.inputs}
    return structure.render.question.format(**fields)


def gold_for(structure: gr.Structure, display_inputs: dict[str, float]) -> float:
    si = {n.name: dm.to_si(display_inputs[n.name], n.unit) for n in structure.inputs}
    return gr.target_value_display(structure, si)


def _near_candidates(gold: float, want_high: bool) -> float | None:
    magnitude = abs(gold)
    if magnitude < 1e-12:
        return None
    reference = float(f"{magnitude:.3g}")
    for eps in sorted(np.linspace(-NEAR_BAND, NEAR_BAND, 401), key=abs):
        if eps == 0:
            continue
        candidate = float(f"{magnitude * (1 + eps):.3g}")
        if candidate == reference or abs(candidate / magnitude - 1) > NEAR_BAND or candidate <= 0:
            continue
        shared = common_leading_digits(candidate, magnitude)
        if (want_high and shared >= HIGH_OVERLAP_MIN) or (not want_high and shared <= LOW_OVERLAP_MAX):
            return candidate
    return None


def display_unit(unit_name: str) -> str:
    """Unit text for prompts: superscripts instead of '^2' so that no stray digit is read as a numeral."""

    return unit_name.replace("^2", "\u00b2").replace("^3", "\u00b3")


def _cue_sentence(template: str, value: float, unit: str) -> str:
    return template.format(v=positional(value, 3), u=display_unit(unit))


def _factors(relevance: str, proximity: str, unit_rel: str, overlap: str, isolation: str) -> dict[str, str]:
    return {"cue_semantic_role": relevance, "numeric_proximity": proximity, "unit_type": unit_rel,
            "digit_overlap": overlap, "cue_position": CUE_POSITION, "isolation_condition": isolation}


def render_cell(structure: gr.Structure, instance: int, cell_id: str) -> CellRendering:
    spec = structure.render
    display = dict(structure.instances[instance])
    gold = gold_for(structure, display)
    cell = CellRendering(structure.structure_id, instance, cell_id, True, "", gold_value=gold,
                         gold_unit=spec.target_unit, expected_effect="invariant", input_display=display)
    context = context_text(structure, display)
    question = question_text(structure, display)

    def assemble(extra: str = "", override: str | None = None) -> str:
        head = context + (" " + extra if extra else "")
        return f"{head}\n\n{override or question}"

    def infeasible(reason: str) -> CellRendering:
        cell.feasible, cell.reason = False, reason
        return cell

    if cell_id == "no_cue":
        cell.prompt = assemble()
        cell.factors = _factors("none", "none", "none", "not_controlled", "not_applicable")
    elif cell_id == "nonnumeric_extra":
        cell.prompt = assemble(spec.nonnumeric_sentence)
        cell.factors = _factors("irrelevant_text", "none", "none", "not_controlled", "stated_separate")
    elif cell_id == "numeric_metadata":
        value = 21.0
        cell.cue_value, cell.cue_unit = value, spec.metadata_unit
        cell.prompt = assemble(_cue_sentence(spec.metadata_sentence, value, spec.metadata_unit))
        cell.factors = _factors("irrelevant_metadata", "unrelated", "incompatible", "not_controlled", "stated_separate")
    elif cell_id in ("nongov_same_unit_near_high_overlap", "nongov_same_unit_near_low_overlap"):
        high = cell_id.endswith("high_overlap")
        value = _near_candidates(gold, high)
        if value is None:
            return infeasible(f"no near-match numeral (within {NEAR_BAND:.0%}) with "
                              f"{'at least ' + str(HIGH_OVERLAP_MIN) if high else 'at most ' + str(LOW_OVERLAP_MAX)} "
                              "shared leading digits for this gold answer")
        cell.cue_value, cell.cue_unit = value, spec.target_unit
        cell.prompt = assemble(_cue_sentence(spec.isolated_sentence, value, spec.target_unit))
        cell.factors = _factors("nongoverning_isolated", "near", "same", "high" if high else "low", "stated_isolated")
    elif cell_id in ("nongov_same_unit_moderate", "nongov_same_unit_far"):
        factor = MODERATE_FACTOR if cell_id.endswith("moderate") else FAR_FACTOR
        value = float(f"{abs(gold) * factor:.3g}")
        if value <= 0:
            return infeasible("zero gold answer")
        cell.cue_value, cell.cue_unit = value, spec.target_unit
        cell.prompt = assemble(_cue_sentence(spec.isolated_sentence, value, spec.target_unit))
        cell.factors = _factors("nongoverning_isolated", "moderate" if factor == MODERATE_FACTOR else "far",
                                "same", "not_controlled", "stated_isolated")
    elif cell_id == "nongov_incompatible_unit_near":
        value = _near_candidates(gold, True) or _near_candidates(gold, False)
        if value is None:
            return infeasible("no near-match numeral for this gold answer")
        cell.cue_value, cell.cue_unit = value, spec.incompatible_unit
        cell.prompt = assemble(_cue_sentence(spec.incompatible_sentence, value, spec.incompatible_unit))
        cell.factors = _factors("nongoverning_isolated", "near_numeral", "incompatible", "high", "stated_isolated")
    elif cell_id == "nongov_same_magnitude_convertible_unit":
        if not spec.equivalent_unit:
            return infeasible("no convertible unit is defined for the target unit")
        value = float(f"{dm.convert(abs(gold), spec.target_unit, spec.equivalent_unit):.3g}")
        cell.cue_value, cell.cue_unit = value, spec.equivalent_unit
        cell.prompt = assemble(_cue_sentence(spec.isolated_sentence, value, spec.equivalent_unit))
        cell.factors = _factors("nongoverning_isolated", "equal_magnitude", "equivalent", "different_digits",
                                "stated_isolated")
    elif cell_id == "relevant_edit":
        node_name, factor = structure.relevant_edit
        edited = dict(display)
        edited[node_name] = float(f"{display[node_name] * factor:.4g}")
        cell.input_display = edited
        cell.gold_value = gold_for(structure, edited)
        cell.prompt = f"{context_text(structure, edited)}\n\n{question_text(structure, edited)}"
        cell.expected_effect = "changed"
        cell.factors = _factors("relevant_edit", "none", "same", "not_controlled", "not_applicable")
    elif cell_id == "role_reversal":
        value = float(f"{abs(gold) * MODERATE_FACTOR:.3g}")
        cell.cue_value, cell.cue_unit = value, spec.target_unit
        cell.gold_value = gold - value
        cell.expected_effect = "changed"
        cell.prompt = assemble(_cue_sentence(spec.comparison_sentence, value, spec.target_unit),
                               question + " Give the answer as this value minus the corresponding value for "
                                          "system B.")
        cell.factors = _factors("role_reversed", "moderate", "same", "not_controlled", "stated_compared")
    else:
        raise KeyError(f"unknown cell {cell_id!r}")
    return cell


def prompt_numbers(text: str) -> list[float]:
    return sorted(float(m) for m in _NUMBER.findall(text))


def expected_prompt_numbers(structure: gr.Structure, cell: CellRendering) -> list[float]:
    values = [float(input_text(structure, n.name, (cell.input_display or {})[n.name])) for n in structure.inputs]
    values += [float(x) for x in structure.render.fixed_numbers]
    if cell.cue_value is not None:
        values.append(float(positional(cell.cue_value, 3)))
    return sorted(values)


def prompt_matches_graph(structure: gr.Structure, cell: CellRendering) -> bool:
    """Every numeral in the prompt is a declared input, a declared fixed number, or the single cue value."""

    return prompt_numbers(cell.prompt) == expected_prompt_numbers(structure, cell)


def all_cells(structure: gr.Structure) -> list[CellRendering]:
    return [render_cell(structure, i, c) for i in range(len(structure.instances)) for c in CELL_IDS]


# ---------------------------------------------------------------------------------------------
# Identity and lineage
# ---------------------------------------------------------------------------------------------


def target_expression(structure: gr.Structure) -> sympy.Expr:
    """The target as one expression over input symbols (computed nodes substituted, latest first)."""

    names = [n.name for n in structure.nodes]
    expressions = {n.name: gr.parse_expr(n.expr, names) for n in structure.computed}
    target = expressions[structure.target]
    for name in [n.name for n in gr.topological_order(structure) if n.kind == "computed"][::-1]:
        target = target.subs({sympy.Symbol(name): expressions[name]})
    return sympy.simplify(target)


def canonical_program_hash(expression: sympy.Expr) -> str:
    """A symbol-renaming-invariant hash of an expression (symbols renamed by sorted first appearance)."""

    symbols = sorted(expression.free_symbols, key=lambda s: sympy.default_sort_key(s))
    renamed = expression.xreplace({s: sympy.Symbol(f"x{i}") for i, s in enumerate(symbols)})
    return hashlib.sha256(sympy.srepr(sympy.simplify(renamed)).encode("utf-8")).hexdigest()


def structure_hash(structure: gr.Structure) -> str:
    return canonical_program_hash(target_expression(structure))


def structure_uuid(structure: gr.Structure) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{structure.structure_id}:{structure_hash(structure)}"))


def manifest_rows(structure: gr.Structure) -> list[dict[str, Any]]:
    """One row per instantiation and cell, with the v2 §9.1 factor fields (p.43)."""

    program_hash, struct_uuid = structure_hash(structure), structure_uuid(structure)
    rows = []
    for cell in all_cells(structure):
        row: dict[str, Any] = {
            "structure_id": structure.structure_id, "structure_uuid": struct_uuid,
            "template_cluster_id": f"V2C-{structure.structure_id}", "symbolic_program_hash": program_hash,
            "instance": cell.instance, "cell_id": cell.cell_id, "feasible": cell.feasible,
            "infeasible_reason": cell.reason, "domain": structure.domain, "law_family": structure.law_family,
            "expected_effect": cell.expected_effect, "admission_category": "UNREVIEWED",
        }
        if cell.feasible:
            row.update({
                **(cell.factors or {}),
                "cue_numeric_value": cell.cue_value, "cue_unit": cell.cue_unit,
                "gold_value": cell.gold_value, "gold_unit": cell.gold_unit,
                "prompt": cell.prompt, "prompt_sha256": hashlib.sha256(cell.prompt.encode("utf-8")).hexdigest(),
                "prompt_matches_graph": prompt_matches_graph(structure, cell),
            })
        rows.append(row)
    return rows
