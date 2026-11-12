"""Role-by-value cells for DECOY-v2 (Stage 15; plan of record Sections 4.2 "four role strata", 4.3 "role-by-value design").

A `RoleSpec` attaches one quantity q to a structure in physical roles, at three or more values, in two or more phrasings:

* R (relevant): q is wired into an input node of the structure (`add`, `subtract`, `replace` or `scale`), so the certified
  answer y*_R(z) is recomputed through the graph and, independently, through the structure's hand-coded solver.
* D (structurally disconnected): the same sentence frame and numeral, with a relational phrase that puts q on something with
  no path to the target. y*_D(z) is the base gold for every z.
* C (algebraically cancelling, optional): a quantity of the same system that appears in the governing relations but cancels
  (certified by an identically zero derivative of an unsimplified expression and by numeric invariance). Intermediate use is
  correct physics; only the final answer must be invariant.
* K (conditionally irrelevant, optional): a quantity whose influence depends on a regime predicate that holds at every value;
  the counter-regime value at which it would matter is documented.

R and D cells of one value are minimal pairs: same frame, numeral, unit, position and question; only the relational phrase
differs. Each cell carries its certified answer, the prespecified misuse foils (copy; substitute, add or subtract on every
input of q's dimension; the relevant twin's answer for D cells; the irrelevant-role answer, i.e. neglect, for R cells), the
placebo value for R cells, and the pairs that are not separated beyond the loosest grading tolerance. `certify_role_spec`
returns the checks; a spec that fails any blocking check yields no cells.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import sympy

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import graph as gr

LOOSEST_REL_TOL = 0.01  # the 1% grading view: values closer than this cannot be told apart by any view
MARKER_WORDS = ("unrelated", "separate", "isolated", "independent", "not connected", "no connection", "irrelevant",
                "takes no part", "nothing to do", "different system", "another system", "never interacts", "not attached",
                "not part of", "no effect")
OPS = ("add", "subtract", "replace", "scale")
POSITIONS = ("after_context", "before_context")
Q = "q"  # the symbol of the role quantity in C and K expressions


@dataclass(frozen=True)
class Phrasing:
    phrasing_id: str
    relation: str  # the relational phrase inserted into the frame (or the whole sentence for C and K)

    @property
    def marker_free(self) -> bool:
        lowered = self.relation.lower()
        return not any(word in lowered for word in MARKER_WORDS)


@dataclass(frozen=True)
class RelevantWiring:
    input_name: str  # the input node q acts on in the R role
    op: str  # add | subtract | replace | scale
    rationale: str  # one sentence: why the R phrasing makes q enter this input this way


@dataclass(frozen=True)
class CancellingSpec:
    quantity_phrase: str
    quantity_type: str
    unit: str
    values: tuple[float, ...]
    frame: str  # a whole sentence with {value} {unit}; one per phrasing via {relation}
    phrasings: tuple[Phrasing, ...]
    expr_with_q: str  # the target as an UNSIMPLIFIED expression over input names and `q` (SI) in which q cancels
    intermediate_relations: tuple[str, ...]  # the relations that contain q before it cancels
    wrong_law: str  # the most plausible wrong law that keeps q (an expression over input names, computed names and q)
    nonnumeric_fill: str = "a"


@dataclass(frozen=True)
class ConditionalSpec:
    quantity_phrase: str
    quantity_type: str
    unit: str
    values: tuple[float, ...]
    frame: str
    phrasings: tuple[Phrasing, ...]
    predicate: str  # expression over input names, computed names and q (SI) that is true inside the regime
    out_of_regime_law: str  # the answer if the regime did not hold (expression over names and q, SI, target unit SI)
    counter_regime_value: float  # a value of q (display unit) at which the predicate is false
    nonnumeric_fill: str = "a"


@dataclass(frozen=True)
class RoleSpec:
    structure_id: str
    quantity_phrase: str  # e.g. "a small block"
    quantity_type: str
    unit: str  # display unit of q
    values: tuple[float, ...]  # >= 3 study values (display unit)
    heldout_values: tuple[float, ...]
    frame: str  # sentence with {value}, {unit} and {relation}, e.g. "A {value} {unit} block is {relation}."
    relevant: RelevantWiring
    phrasings_r: tuple[Phrasing, ...]
    phrasings_d: tuple[Phrasing, ...]
    nonnumeric_fill: str  # replaces "{value} {unit}" in the non-numeric control, e.g. "small"
    cancelling: CancellingSpec | None = None
    conditional: ConditionalSpec | None = None
    author: str = "agent"
    notes: str = ""


@dataclass
class RoleCell:
    structure_id: str
    instance: int
    cell_id: str
    stratum: str  # R | D | C | K | N (non-numeric control) | none (no cue)
    value_index: int | None
    value: float | None
    unit: str | None
    phrasing_id: str | None
    marker_free: bool | None
    position: str
    prompt: str
    gold_value: float
    gold_unit: str
    foils: dict[str, float] = field(default_factory=dict)
    placebo: float | None = None
    confounded: list[str] = field(default_factory=list)
    heldout: bool = False

    def row(self) -> dict[str, Any]:
        return {"structure_id": self.structure_id, "instance": self.instance, "cell_id": self.cell_id,
                "stratum": self.stratum, "value_index": self.value_index, "value": self.value, "unit": self.unit,
                "phrasing_id": self.phrasing_id, "marker_free": self.marker_free, "position": self.position,
                "prompt": self.prompt, "prompt_sha256": hashlib.sha256(self.prompt.encode("utf-8")).hexdigest(),
                "gold_value": self.gold_value, "gold_unit": self.gold_unit, "foils": dict(self.foils),
                "placebo": self.placebo, "confounded": list(self.confounded), "heldout": self.heldout}


# --- evaluation ---------------------------------------------------------------------------------------------------------

def all_node_values(structure: gr.Structure, si_inputs: dict[str, float]) -> dict[str, float]:
    """SI values of every node (inputs and computed) for the given SI inputs."""

    names = [n.name for n in structure.nodes]
    values = dict(si_inputs)
    for node in gr.topological_order(structure):
        if node.kind != "computed":
            continue
        expression = gr.parse_expr(node.expr or "0", names)
        arguments = sorted(str(s) for s in expression.free_symbols)
        values[node.name] = float(sympy.lambdify([sympy.Symbol(a) for a in arguments], expression, modules="math")(
            *[values[a] for a in arguments]))
    return values


def display_inputs_si(structure: gr.Structure, instance: int) -> dict[str, float]:
    display = dict(structure.instances[instance])
    return {n.name: dm.to_si(float(display[n.name]), n.unit) for n in structure.inputs}


def _wired(structure: gr.Structure, si: dict[str, float], wiring: RelevantWiring, q_si: float) -> dict[str, float]:
    out = dict(si)
    x = out[wiring.input_name]
    out[wiring.input_name] = {"add": x + q_si, "subtract": x - q_si, "replace": q_si, "scale": x * q_si}[wiring.op]
    return out


def gold_r(structure: gr.Structure, si: dict[str, float], spec: RoleSpec, value: float) -> tuple[float, float]:
    """(graph route, solver route) of the relevant-role answer in the target display unit."""

    q_si = dm.to_si(value, spec.unit) if spec.relevant.op != "scale" else value
    wired = _wired(structure, si, spec.relevant, q_si)
    graph = dm.from_si(gr.compile_target(structure)(wired), structure.render.target_unit)
    solver = dm.from_si(float(structure.solver(*gr.solver_inputs(structure, wired))), structure.render.target_unit)
    return graph, solver


def _eval_expr(text: str, structure: gr.Structure, values: dict[str, float], q_si: float) -> float:
    names = [n.name for n in structure.nodes] + [Q]
    expression = gr.parse_expr(text, names)
    arguments = sorted(str(s) for s in expression.free_symbols)
    env = {**values, Q: q_si}
    return float(sympy.lambdify([sympy.Symbol(a) for a in arguments], expression, modules="math")(*[env[a] for a in arguments]))


def misuse_foils(structure: gr.Structure, si: dict[str, float], spec: RoleSpec, value: float) -> dict[str, float]:
    """Answers (target display unit) produced by each prespecified misuse of q at this value."""

    target_unit = structure.render.target_unit
    q_dim = dm.UNITS[spec.unit].dim
    q_si = dm.to_si(value, spec.unit)
    foils: dict[str, float] = {}
    if q_dim == dm.UNITS[target_unit].dim:
        foils["copy"] = dm.from_si(q_si, target_unit)
    evaluate = gr.compile_target(structure)
    for node in structure.inputs:
        if dm.UNITS[node.unit].dim != q_dim:
            continue
        for op in ("replace", "add", "subtract"):
            try:
                answer = evaluate(_wired(structure, si, RelevantWiring(node.name, op, ""), q_si))
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            if isinstance(answer, float) and math.isfinite(answer):
                foils[f"{op}:{node.name}"] = dm.from_si(answer, target_unit)
    return foils


def placebo_value(y_r: float, y_d: float, sign_definite: bool) -> tuple[float, str]:
    """As far from the correct answer as the neglect value, on the other side; multiplicative if additive changes sign."""

    additive = 2 * y_r - y_d
    if sign_definite and (additive == 0 or math.copysign(1, additive) != math.copysign(1, y_r)):
        return y_r * (y_r / y_d), "multiplicative"
    return additive, "additive"


def _not_separated(values: dict[str, float]) -> list[tuple[str, str]]:
    names = sorted(values)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            scale = max(abs(values[a]), abs(values[b]))
            if scale == 0 or abs(values[a] - values[b]) <= LOOSEST_REL_TOL * scale:
                out.append((a, b))
    return out


# --- certification -------------------------------------------------------------------------------------------------------

def certify_role_spec(structure: gr.Structure, spec: RoleSpec) -> dict[str, Any]:
    """Blocking checks for one spec on every instance of the structure; returns {'passed': bool, 'checks': {...}}."""

    checks: dict[str, Any] = {}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        checks[name] = {"ok": bool(ok), "detail": detail}

    check("values_at_least_3", len(spec.values) >= 3, list(spec.values))
    check("phrasings_r_at_least_2", len(spec.phrasings_r) >= 2, [p.phrasing_id for p in spec.phrasings_r])
    check("phrasings_d_at_least_2", len(spec.phrasings_d) >= 2, [p.phrasing_id for p in spec.phrasings_d])
    check("marker_free_d", any(p.marker_free for p in spec.phrasings_d), [p.relation for p in spec.phrasings_d])
    check("marker_free_r", any(p.marker_free for p in spec.phrasings_r), [p.relation for p in spec.phrasings_r])
    check("frame_slots", all(s in spec.frame for s in ("{value}", "{unit}", "{relation}")), spec.frame)
    check("op_known", spec.relevant.op in OPS, spec.relevant.op)
    check("unit_known", spec.unit in dm.UNITS, spec.unit)
    try:
        node = structure.node(spec.relevant.input_name)
        dims_ok = spec.relevant.op == "scale" or dm.UNITS[node.unit].dim == dm.UNITS[spec.unit].dim
        check("wiring_dimension", node.kind == "input" and dims_ok, f"{node.name} [{node.unit}] {spec.relevant.op} q [{spec.unit}]")
    except (gr.GraphError, KeyError) as exc:
        check("wiring_dimension", False, str(exc))
        return {"passed": False, "checks": checks}
    per_instance = []
    for instance in range(len(structure.instances)):
        si = display_inputs_si(structure, instance)
        y_d = dg.gold_for(structure, dict(structure.instances[instance]))
        rows = {}
        for value in (*spec.values, *spec.heldout_values):
            graph_r, solver_r = gold_r(structure, si, spec, value)
            route_ok = math.isclose(graph_r, solver_r, rel_tol=max(structure.solver_rel_tol, 1e-9) * 10, abs_tol=1e-12)
            foils = misuse_foils(structure, si, spec, value)
            rows[value] = {"y_r": graph_r, "solver_r": solver_r, "route_ok": route_ok, "foils": foils}
        values = list(spec.values)
        response_ok = all(abs(rows[v]["y_r"] - y_d) > LOOSEST_REL_TOL * max(abs(rows[v]["y_r"]), abs(y_d)) for v in values)
        spread_ok = all(abs(rows[a]["y_r"] - rows[b]["y_r"]) > LOOSEST_REL_TOL * max(abs(rows[a]["y_r"]), abs(rows[b]["y_r"]))
                        for i, a in enumerate(values) for b in values[i + 1:])
        per_instance.append({"instance": instance, "y_d": y_d, "routes_agree": all(r["route_ok"] for r in rows.values()),
                             "r_separated_from_d": response_ok, "r_values_distinct": spread_ok,
                             "y_r": {str(v): rows[v]["y_r"] for v in rows}})
    check("routes_agree", all(p["routes_agree"] for p in per_instance))
    check("r_separated_from_d", all(p["r_separated_from_d"] for p in per_instance))
    check("r_values_distinct", all(p["r_values_distinct"] for p in per_instance))
    checks["per_instance"] = per_instance
    if spec.cancelling is not None:
        checks["cancelling"] = certify_cancelling(structure, spec.cancelling)
    if spec.conditional is not None:
        checks["conditional"] = certify_conditional(structure, spec.conditional)
    blocking = [k for k, v in checks.items() if isinstance(v, dict) and "ok" in v and not v["ok"]]
    stratum_fail = [k for k in ("cancelling", "conditional") if k in checks and not checks[k]["passed"]]
    return {"passed": not blocking, "failed": blocking, "strata_failed": stratum_fail, "checks": checks}


def certify_cancelling(structure: gr.Structure, c: CancellingSpec) -> dict[str, Any]:
    names = [n.name for n in structure.nodes] + [Q]
    out: dict[str, Any] = {}
    try:
        expression = gr.parse_expr(c.expr_with_q, names)
        out["q_present_unsimplified"] = sympy.Symbol(Q) in expression.free_symbols or Q in c.expr_with_q
        out["derivative_zero"] = sympy.simplify(sympy.diff(expression, sympy.Symbol(Q))) == 0
        invariant = True
        matches_graph = True
        for instance in range(len(structure.instances)):
            si = display_inputs_si(structure, instance)
            gold_si = gr.compile_target(structure)(si)
            for value in c.values:
                got = _eval_expr(c.expr_with_q, structure, all_node_values(structure, si), dm.to_si(value, c.unit))
                matches_graph &= math.isclose(got, gold_si, rel_tol=1e-9, abs_tol=1e-12)
            invariant &= matches_graph
        out["numeric_invariance"] = invariant
        out["matches_graph_target"] = matches_graph
        wrong = []
        for instance in range(len(structure.instances)):
            si = display_inputs_si(structure, instance)
            gold = dm.from_si(gr.compile_target(structure)(si), structure.render.target_unit)
            for value in c.values:
                w = dm.from_si(_eval_expr(c.wrong_law, structure, all_node_values(structure, si), dm.to_si(value, c.unit)),
                               structure.render.target_unit)
                wrong.append(abs(w - gold) > LOOSEST_REL_TOL * max(abs(w), abs(gold)))
        out["wrong_law_separated_at_2_of_3"] = sum(wrong) >= max(2, int(len(wrong) * 2 / 3))
    except Exception as exc:  # a malformed spec is a failed check, never a crash of the whole build
        out["error"] = repr(exc)
    out["values_at_least_3"] = len(c.values) >= 3
    out["phrasings_at_least_2"] = len(c.phrasings) >= 2
    out["intermediate_relations_listed"] = bool(c.intermediate_relations)
    out["passed"] = all(out.get(k) is True for k in ("q_present_unsimplified", "derivative_zero", "numeric_invariance",
                                                      "wrong_law_separated_at_2_of_3", "values_at_least_3",
                                                      "phrasings_at_least_2", "intermediate_relations_listed"))
    return out


def certify_conditional(structure: gr.Structure, k: ConditionalSpec) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        inside, outside, separated = True, True, []
        for instance in range(len(structure.instances)):
            si = display_inputs_si(structure, instance)
            values = all_node_values(structure, si)
            gold = dm.from_si(values[structure.target], structure.render.target_unit)
            for value in k.values:
                inside &= bool(_eval_expr(k.predicate, structure, values, dm.to_si(value, k.unit)))
                alt = dm.from_si(_eval_expr(k.out_of_regime_law, structure, values, dm.to_si(value, k.unit)),
                                 structure.render.target_unit)
                separated.append(abs(alt - gold) > LOOSEST_REL_TOL * max(abs(alt), abs(gold)))
            outside &= not bool(_eval_expr(k.predicate, structure, values, dm.to_si(k.counter_regime_value, k.unit)))
        out["predicate_holds_at_all_values"] = inside
        out["counter_regime_value_breaks_predicate"] = outside
        out["out_of_regime_law_separated"] = all(separated)
    except Exception as exc:
        out["error"] = repr(exc)
    out["values_at_least_3"] = len(k.values) >= 3
    out["phrasings_at_least_2"] = len(k.phrasings) >= 2
    out["passed"] = all(out.get(n) is True for n in ("predicate_holds_at_all_values", "counter_regime_value_breaks_predicate",
                                                      "out_of_regime_law_separated", "values_at_least_3",
                                                      "phrasings_at_least_2"))
    return out


# --- rendering -------------------------------------------------------------------------------------------------------------

def _fmt(value: float) -> str:
    return f"{value:.4g}"


def _sentence(frame: str, value: float | None, unit: str | None, relation: str, fill: str) -> str:
    if value is None:
        text = frame.replace("{value} {unit}", fill)
        return text.format(relation=relation)
    return frame.format(value=_fmt(value), unit=dg.display_unit(unit or ""), relation=relation)


def _assemble(structure: gr.Structure, instance: int, sentence: str, position: str) -> str:
    display = dict(structure.instances[instance])
    context = dg.context_text(structure, display)
    question = dg.question_text(structure, display)
    if not sentence:
        return f"{context}\n\n{question}"
    head = f"{sentence} {context}" if position == "before_context" else f"{context} {sentence}"
    return f"{head}\n\n{question}"


def role_cells(structure: gr.Structure, spec: RoleSpec, instance: int, *, positions: tuple[str, ...] = ("after_context",),
               include_heldout: bool = False) -> list[RoleCell]:
    """All cells of one instance: no cue, the non-numeric control, R and D at every value and phrasing, and C and K if given."""

    si = display_inputs_si(structure, instance)
    target_unit = structure.render.target_unit
    y_d = dg.gold_for(structure, dict(structure.instances[instance]))
    sign_definite = all(dg.gold_for(structure, dict(inst)) > 0 for inst in structure.instances) or all(
        dg.gold_for(structure, dict(inst)) < 0 for inst in structure.instances)
    cells = [RoleCell(structure.structure_id, instance, "no_cue", "none", None, None, None, None, None, "after_context",
                      _assemble(structure, instance, "", "after_context"), y_d, target_unit)]
    nonnumeric = _sentence(spec.frame, None, None, spec.phrasings_d[0].relation, spec.nonnumeric_fill)
    for position in positions:
        cells.append(RoleCell(structure.structure_id, instance, f"N:{position}", "N", None, None, None,
                              spec.phrasings_d[0].phrasing_id, spec.phrasings_d[0].marker_free, position,
                              _assemble(structure, instance, nonnumeric, position), y_d, target_unit))
    values = list(spec.values) + (list(spec.heldout_values) if include_heldout else [])
    for index, value in enumerate(values):
        heldout = index >= len(spec.values)
        y_r, _ = gold_r(structure, si, spec, value)
        foils = misuse_foils(structure, si, spec, value)
        placebo, _kind = placebo_value(y_r, y_d, sign_definite)
        for position in positions:
            for role, phrasings in (("R", spec.phrasings_r), ("D", spec.phrasings_d)):
                for phrasing in phrasings:
                    sentence = _sentence(spec.frame, value, spec.unit, phrasing.relation, spec.nonnumeric_fill)
                    gold = y_r if role == "R" else y_d
                    # the misuse foil that equals the relevant wiring is not a misuse in the R world (it is the gold) and in
                    # the D world it duplicates `relevant_twin`; it is dropped from both so matches stay unambiguous
                    cell_foils = {k: v for k, v in foils.items() if k != f"{spec.relevant.op}:{spec.relevant.input_name}"}
                    if role == "D":
                        cell_foils["relevant_twin"] = y_r
                    else:
                        cell_foils["neglect"] = y_d
                    named = {"gold": gold, **cell_foils}
                    confounded = [f"{a}~{b}" for a, b in _not_separated(named) if "gold" in (a, b)]
                    cells.append(RoleCell(structure.structure_id, instance, f"{role}:z{index}:{phrasing.phrasing_id}:{position}",
                                          role, index, value, spec.unit, phrasing.phrasing_id, phrasing.marker_free, position,
                                          _assemble(structure, instance, sentence, position), gold, target_unit, cell_foils,
                                          placebo if role == "R" else None, confounded, heldout))
    for stratum, sub in (("C", spec.cancelling), ("K", spec.conditional)):
        if sub is None:
            continue
        values_all = all_node_values(structure, si)
        for index, value in enumerate(sub.values):
            q_si = dm.to_si(value, sub.unit)
            law = sub.wrong_law if stratum == "C" else sub.out_of_regime_law
            foils = {"wrong_law" if stratum == "C" else "out_of_regime": dm.from_si(
                _eval_expr(law, structure, values_all, q_si), target_unit)}
            if dm.UNITS[sub.unit].dim == dm.UNITS[target_unit].dim:
                foils["copy"] = dm.from_si(q_si, target_unit)
            for phrasing in sub.phrasings:
                sentence = _sentence(sub.frame, value, sub.unit, phrasing.relation, sub.nonnumeric_fill)
                named = {"gold": y_d, **foils}
                confounded = [f"{a}~{b}" for a, b in _not_separated(named) if "gold" in (a, b)]
                cells.append(RoleCell(structure.structure_id, instance, f"{stratum}:z{index}:{phrasing.phrasing_id}:after_context",
                                      stratum, index, value, sub.unit, phrasing.phrasing_id, phrasing.marker_free,
                                      "after_context", _assemble(structure, instance, sentence, "after_context"), y_d,
                                      target_unit, foils, None, confounded))
    return cells


def prompt_value_check(cell: RoleCell) -> bool:
    """The role sentence's numeral appears in the prompt exactly as rendered (a rendering self-check)."""

    if cell.value is None:
        return True
    return re.search(rf"(?<![\d.]){re.escape(_fmt(cell.value))}(?![\d])", cell.prompt) is not None


def complete(spec: RoleSpec, certificate: dict[str, Any]) -> bool:
    """A structure is complete for the primary contrast: R and D at three values in two phrasings, certified."""

    return (certificate["passed"] and len(spec.values) >= 3 and len(spec.phrasings_r) >= 2 and len(spec.phrasings_d) >= 2)


SpecFactory = Callable[[], RoleSpec]
