"""Proof-carrying certification and mutation testing for DECOY-v2 structures (Stage 14.6; v2 B3.2, p.8; P3.3, p.20).

`certify` runs eleven checks and returns a proof object (the checks, the assumptions, the node table, the symbolic
derivation, the solver route, the tolerances and the seed). A structure is `SOLVER_CERTIFIED` only if every check passes.
That is a statement about the graph, the independent solver and the rendered numerals. It is not a statement about
the English text: that needs independent human review (v2 B4), so every structure keeps the admission category
UNREVIEWED here.

`mutants` and `mutation_report` plant known defects (a cue leaking into the equation, a unit error, a sign flip, a
removed input, a swapped target, a hidden dependence, a divisor whose domain includes zero, a dropped assumption, a
misdeclared target unit) and equivalent rewrites that must still pass. The report gives sensitivity and specificity by
mutator and verifies that each defect fails for an intended reason.
"""

from __future__ import annotations

import dataclasses
import math
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import sympy

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import graph as gr

CHECK_NAMES = (
    "schema", "symbols_acyclic", "dimensions", "target_and_inputs_relevant", "nuisance_independence",
    "assumptions_cover_assumed", "route_agreement", "positive_control", "role_reversal_twin", "boundary_cases",
    "prompt_matches_graph",
)
MIN_RELEVANT_EFFECT = 0.05  # a relevant edit must move the answer by at least 5%
SEED = 42


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


def _safe(name: str, function) -> Check:
    try:
        passed, detail = function()
    except Exception as error:  # a crash is a failed check, never a silent pass
        return Check(name, False, f"{type(error).__name__}: {error}")
    return Check(name, bool(passed), detail)


def _domain_box(structure: gr.Structure) -> dict[str, tuple[float, float]]:
    return {n.name: n.domain for n in structure.inputs if n.domain is not None}


def _si(structure: gr.Structure, display: dict[str, float]) -> dict[str, float]:
    return {n.name: dm.to_si(display[n.name], n.unit) for n in structure.inputs}


def _draws(structure: gr.Structure, n_draws: int, seed: int) -> list[dict[str, float]]:
    """Display-unit input dictionaries: the base point, random interior points and every corner of the box."""

    rng = np.random.default_rng(seed)
    box = _domain_box(structure)
    base = {n.name: float(n.value) for n in structure.inputs if n.value is not None}
    points = [dict(base)]
    for _ in range(n_draws):
        point = dict(base)
        for name, (lo, hi) in box.items():
            point[name] = float(rng.uniform(lo, hi))
        points.append(point)
    names = list(box)
    if 0 < len(names) <= 6:
        for mask in range(2 ** len(names)):
            point = dict(base)
            for bit, name in enumerate(names):
                point[name] = box[name][1] if (mask >> bit) & 1 else box[name][0]
            points.append(point)
    return points


def _routes(structure: gr.Structure, display: dict[str, float], evaluator) -> tuple[float, float]:
    si = _si(structure, display)
    return evaluator(si), float(structure.solver(*gr.solver_inputs(structure, si)))


# ---------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------


def check_schema(structure: gr.Structure) -> tuple[bool, str]:
    names = [n.name for n in structure.nodes]
    problems = []
    if len(set(names)) != len(names):
        problems.append("duplicate node names")
    for node in structure.nodes:
        if node.kind not in ("input", "computed"):
            problems.append(f"{node.name}: kind {node.kind!r}")
        if node.provenance not in gr.PROVENANCE:
            problems.append(f"{node.name}: provenance {node.provenance!r}")
        dm.unit(node.unit)
        if node.kind == "input":
            if node.value is None or node.domain is None:
                problems.append(f"{node.name}: an input needs a value and an admissible domain")
            elif not node.domain[0] < node.domain[1] or not node.domain[0] <= node.value <= node.domain[1]:
                problems.append(f"{node.name}: value outside its admissible domain")
    for assumption in structure.assumptions:
        if assumption.kind not in gr.ASSUMPTION_KINDS:
            problems.append(f"{assumption.assumption_id}: kind {assumption.kind!r}")
    input_names = {n.name for n in structure.inputs}
    for index, instance in enumerate(structure.instances):
        if set(instance) != input_names:
            problems.append(f"instance {index}: keys differ from the input nodes")
            continue
        for node in structure.inputs:
            lo, hi = node.domain or (-math.inf, math.inf)
            if not lo <= instance[node.name] <= hi:
                problems.append(f"instance {index}: {node.name} outside its admissible domain")
    if structure.solver_arity < 1:
        problems.append("solver arity")
    if len(structure.instances) < 2:
        problems.append("at least two numeric instantiations are required")
    if structure.relevant_edit[0] not in input_names:
        problems.append("relevant_edit names a node that is not an input")
    return not problems, "; ".join(problems) or "ok"


def check_symbols_acyclic(structure: gr.Structure) -> tuple[bool, str]:
    gr.topological_order(structure)
    return True, "acyclic; every symbol declared"


def check_dimensions(structure: gr.Structure) -> tuple[bool, str]:
    dims = {n.name: dm.unit(n.unit).dim for n in structure.nodes}
    names = list(dims)
    for node in structure.computed:
        got = dm.expr_dimension(gr.parse_expr(node.expr, names), dims)
        if got != dims[node.name]:
            return False, f"{node.name}: expression has dimension {got.label()}, declared {dims[node.name].label()}"
    target = structure.node(structure.target)
    if dm.unit(structure.render.target_unit).dim != dims[target.name]:
        return False, "the answer unit does not match the dimension of the target node"
    return True, f"{len(structure.computed)} computed nodes and the answer unit are dimensionally consistent"


def check_target_and_inputs_relevant(structure: gr.Structure) -> tuple[bool, str]:
    if structure.node(structure.target).kind != "computed":
        return False, "the target is not a computed node"
    needed = gr.ancestors(structure, structure.target)
    unused = [n.name for n in structure.inputs if n.name not in needed]
    return not unused, f"inputs not influencing the target: {unused}" if unused else "every input is an ancestor"


def check_nuisance_independence(structure: gr.Structure) -> tuple[bool, str]:
    symbol = gr.NUISANCE_SYMBOL
    in_nodes = any(n.name == symbol for n in structure.nodes)
    in_exprs = any(re.search(rf"\b{symbol}\b", n.expr or "") for n in structure.computed)
    if in_nodes or in_exprs:
        return False, f"the nuisance symbol {symbol!r} appears in the graph"
    full = dg.target_expression(structure)
    return symbol not in {str(s) for s in full.free_symbols}, "the nuisance symbol is not an ancestor of the target"


def check_assumptions_cover_assumed(structure: gr.Structure) -> tuple[bool, str]:
    names = {n.name for n in structure.nodes}
    covered = {name for a in structure.assumptions for name in a.applies_to}
    missing = [n.name for n in structure.nodes if n.provenance == "assumed" and n.name not in covered]
    dangling = sorted(covered - names)
    if missing or dangling:
        return False, f"assumed nodes without an assumption: {missing}; assumptions naming absent nodes: {dangling}"
    return True, "every assumed node is covered and every assumption names an existing node"


def check_route_agreement(structure: gr.Structure, n_draws: int, seed: int) -> tuple[bool, str]:
    evaluator = gr.compile_target(structure)
    worst, worst_point = 0.0, None
    for point in _draws(structure, n_draws, seed):
        graph_value, solver_value = _routes(structure, point, evaluator)
        scale = max(abs(graph_value), abs(solver_value), 1e-300)
        error = abs(graph_value - solver_value) / scale
        if error > worst:
            worst, worst_point = error, point
    ok = worst <= structure.solver_rel_tol
    return ok, f"worst relative disagreement {worst:.2e} (tolerance {structure.solver_rel_tol:.0e}) over the base " \
               f"point, {n_draws} random points and the domain corners" + ("" if ok else f" at {worst_point}")


def check_positive_control(structure: gr.Structure) -> tuple[bool, str]:
    node, factor = structure.relevant_edit
    base = {n.name: float(n.value) for n in structure.inputs}
    edited = dict(base)
    edited[node] = base[node] * factor
    evaluator = gr.compile_target(structure)
    g0, s0 = _routes(structure, base, evaluator)
    g1, s1 = _routes(structure, edited, evaluator)
    effect = abs(g1 - g0) / max(abs(g0), 1e-300)
    agree = abs(g1 - s1) <= structure.solver_rel_tol * max(abs(g1), 1e-300) and \
        abs(g0 - s0) <= structure.solver_rel_tol * max(abs(g0), 1e-300)
    lo, hi = _domain_box(structure).get(node, (-math.inf, math.inf))
    inside = lo - 1e-9 * abs(lo) <= edited[node] <= hi + 1e-9 * abs(hi)
    ok = effect >= MIN_RELEVANT_EFFECT and agree and inside
    return ok, f"editing {node} by x{factor} moves the answer by {effect:.1%} (minimum {MIN_RELEVANT_EFFECT:.0%}); " \
               f"routes agree: {agree}; edit inside the admissible domain: {inside}"


def check_role_reversal_twin(structure: gr.Structure) -> tuple[bool, str]:
    """When the same quantity becomes relevant (the answer is target minus a reference), the answer must follow it."""

    target_unit = structure.render.target_unit
    reference = gr.Node(gr.NUISANCE_SYMBOL, "input", "reference_quantity", target_unit, "reference system value",
                        value=1.0, provenance="measured", domain=(0.0, 1e9))
    twin_node = gr.Node("rr_target", "computed", "difference", target_unit, "target minus reference",
                        expr=f"{structure.target} - {gr.NUISANCE_SYMBOL}", provenance="computed")
    twin = dataclasses.replace(structure, nodes=structure.nodes + (reference, twin_node), target="rr_target")
    evaluator = gr.compile_target(twin)
    base = {n.name: float(n.value) for n in structure.inputs}
    gold = gr.target_value_display(structure, _si(structure, base))
    answers = []
    for scale in (0.7, 1.3):
        point = dict(base)
        point[gr.NUISANCE_SYMBOL] = abs(gold) * scale
        si = {n.name: dm.to_si(point[n.name], n.unit) for n in twin.inputs}
        solver_answer = structure.solver(*gr.solver_inputs(structure, _si(structure, base))) - si[gr.NUISANCE_SYMBOL]
        answers.append((evaluator(si), solver_answer, si[gr.NUISANCE_SYMBOL]))
    routes_agree = all(abs(a - b) <= 1e-6 * max(abs(a), 1e-300) + 1e-12 for a, b, _ in answers)
    follows = abs((answers[0][0] - answers[1][0]) - (answers[1][2] - answers[0][2])) <= 1e-9 * max(abs(gold), 1.0)
    return routes_agree and follows, f"routes agree: {routes_agree}; the answer tracks the reference value exactly: " \
                                     f"{follows}"


def check_boundary_cases(structure: gr.Structure) -> tuple[bool, str]:
    evaluator = gr.compile_target(structure)
    box = _domain_box(structure)
    names = list(box)
    base = {n.name: float(n.value) for n in structure.inputs}
    bad = []
    for mask in range(2 ** len(names)):
        point = dict(base)
        for bit, name in enumerate(names):
            point[name] = box[name][1] if (mask >> bit) & 1 else box[name][0]
        value = evaluator(_si(structure, point))
        if not math.isfinite(value):
            bad.append(point)
    return not bad, f"{2 ** len(names)} domain corners evaluated; non-finite results: {len(bad)}"


def check_prompt_matches_graph(structure: gr.Structure) -> tuple[bool, str]:
    cells = dg.all_cells(structure)
    feasible = [c for c in cells if c.feasible]
    wrong = [f"{c.instance}:{c.cell_id}" for c in feasible if not dg.prompt_matches_graph(structure, c)]
    return not wrong, f"{len(feasible)} of {len(cells)} cells feasible; prompts whose numerals do not match the " \
                      f"graph: {wrong}"


def certify(structure: gr.Structure, n_draws: int = 40, seed: int = SEED) -> dict[str, Any]:
    checks = [
        _safe("schema", lambda: check_schema(structure)),
        _safe("symbols_acyclic", lambda: check_symbols_acyclic(structure)),
        _safe("dimensions", lambda: check_dimensions(structure)),
        _safe("target_and_inputs_relevant", lambda: check_target_and_inputs_relevant(structure)),
        _safe("nuisance_independence", lambda: check_nuisance_independence(structure)),
        _safe("assumptions_cover_assumed", lambda: check_assumptions_cover_assumed(structure)),
        _safe("route_agreement", lambda: check_route_agreement(structure, n_draws, seed)),
        _safe("positive_control", lambda: check_positive_control(structure)),
        _safe("role_reversal_twin", lambda: check_role_reversal_twin(structure)),
        _safe("boundary_cases", lambda: check_boundary_cases(structure)),
        _safe("prompt_matches_graph", lambda: check_prompt_matches_graph(structure)),
    ]
    passed = all(c.passed for c in checks)
    proof: dict[str, Any] = {
        "structure_id": structure.structure_id, "title": structure.title, "domain": structure.domain,
        "law_family": structure.law_family,
        "status": "SOLVER_CERTIFIED" if passed else "FAILED",
        "admission_category": "UNREVIEWED",
        "statement": "Certifies the graph, the independent solver route and the rendered numerals. Does not certify "
                     "the English text or the physical modelling choices; independent expert review is required.",
        "checks": [dataclasses.asdict(c) for c in checks],
        "solver_route": structure.solver_route, "solver_rel_tol": structure.solver_rel_tol,
        "seed": seed, "n_random_draws": n_draws,
        "assumptions": [dataclasses.asdict(a) for a in structure.assumptions],
        "nodes": [{"name": n.name, "kind": n.kind, "quantity_type": n.quantity_type, "unit": n.unit,
                   "dimension": dm.unit(n.unit).dim.label(), "provenance": n.provenance, "frame": n.frame,
                   "sign_convention": n.sign_convention, "domain": n.domain, "expr": n.expr, "value": n.value}
                  for n in structure.nodes],
    }
    if passed:
        proof["symbolic_derivation"] = str(dg.target_expression(structure))
        proof["program_hash"] = dg.structure_hash(structure)
        proof["structure_uuid"] = dg.structure_uuid(structure)
    return proof


# ---------------------------------------------------------------------------------------------
# Mutation testing
# ---------------------------------------------------------------------------------------------


@dataclass
class Mutant:
    mutator_id: str
    kind: str  # "negative" (must be caught) or "positive" (must still pass)
    structure: gr.Structure
    expected_failed: frozenset[str]
    note: str


def _replace_node(structure: gr.Structure, name: str, **changes) -> gr.Structure:
    nodes = tuple(dataclasses.replace(n, **changes) if n.name == name else n for n in structure.nodes)
    return dataclasses.replace(structure, nodes=nodes)


def _denominator_inputs(structure: gr.Structure) -> list[str]:
    """Inputs that are multiplicative factors of a denominator, so that setting one to zero is a true singularity.

    An input that only appears inside a sum in the denominator (for example `C1` in `C1*C2/(C1 + C2)`) is excluded:
    its being zero does not make the denominator vanish, so a domain reaching zero there is not a defect.
    """

    names = [n.name for n in structure.nodes]
    inputs = {n.name for n in structure.inputs}
    found: list[str] = []
    for node in structure.computed:
        denominator = sympy.denom(sympy.together(gr.parse_expr(node.expr, names)))
        for factor in sympy.Mul.make_args(denominator):
            base = factor.base if factor.is_Pow else factor
            if base.is_Symbol and str(base) in inputs and str(base) not in found:
                found.append(str(base))
    return found


def mutants(structure: gr.Structure) -> list[Mutant]:
    out: list[Mutant] = []
    target = structure.node(structure.target)
    names = [n.name for n in structure.nodes]

    leak = gr.Node(gr.NUISANCE_SYMBOL, "input", target.quantity_type, structure.render.target_unit,
                   "a nuisance value wired into the equation", value=1.0, domain=(0.5, 2.0))
    leaked = _replace_node(dataclasses.replace(structure, nodes=structure.nodes + (leak,)), target.name,
                           expr=f"({target.expr}) + {gr.NUISANCE_SYMBOL}/1000")
    out.append(Mutant("cue_leak_into_equation", "negative", leaked,
                      frozenset({"nuisance_independence", "route_agreement"}), "target depends on the nuisance cue"))

    first_input = structure.inputs[0]
    wrong_unit = "m" if dm.unit(first_input.unit).dim == dm.unit("kg").dim else "kg"
    out.append(Mutant("unit_error", "negative", _replace_node(structure, first_input.name, unit=wrong_unit),
                      frozenset({"dimensions"}), f"{first_input.name} declared in {wrong_unit}"))

    out.append(Mutant("sign_flip", "negative", _replace_node(structure, target.name, expr=f"-({target.expr})"),
                      frozenset({"route_agreement"}), "target expression negated"))

    needed = [n for n in structure.inputs if n.name in gr.ancestors(structure, structure.target)
              and n.provenance != "assumed"]
    if needed:
        removed = dataclasses.replace(structure, nodes=tuple(n for n in structure.nodes if n.name != needed[0].name))
        out.append(Mutant("remove_required_input", "negative", removed, frozenset({"symbols_acyclic", "schema"}),
                          f"input {needed[0].name} removed"))

    intermediates = [n for n in structure.computed if n.name != structure.target]
    if intermediates:
        out.append(Mutant("swap_target", "negative", dataclasses.replace(structure, target=intermediates[-1].name),
                          frozenset({"dimensions", "route_agreement"}),
                          f"target swapped for {intermediates[-1].name}"))

    hidden = gr.Node("h_hid", "input", "dimensionless", "1", "an undeclared extra dependence", value=1.0,
                     provenance="assumed", domain=(0.5, 2.0))
    hidden_dependence = _replace_node(dataclasses.replace(structure, nodes=structure.nodes + (hidden,)), target.name,
                                      expr=f"({target.expr})*(1 + h_hid/100)")
    out.append(Mutant("hidden_dependence", "negative", hidden_dependence,
                      frozenset({"route_agreement", "assumptions_cover_assumed"}), "an extra input scales the target"))

    divisors = _denominator_inputs(structure)
    if divisors:
        node = structure.node(divisors[0])
        out.append(Mutant("divisor_domain_includes_zero", "negative",
                          _replace_node(structure, node.name, domain=(0.0, node.domain[1])),
                          frozenset({"boundary_cases", "route_agreement"}),
                          f"the domain of divisor {node.name} reaches zero"))

    sole = [a for a in structure.assumptions
            if any(n.provenance == "assumed" and n.name in a.applies_to
                   and sum(n.name in b.applies_to for b in structure.assumptions) == 1 for n in structure.nodes)]
    if sole:
        out.append(Mutant("drop_sole_assumption", "negative",
                          dataclasses.replace(structure, assumptions=tuple(
                              a for a in structure.assumptions if a is not sole[0])),
                          frozenset({"assumptions_cover_assumed"}), f"assumption {sole[0].assumption_id} dropped"))

    wrong_answer_unit = "kg" if dm.unit(structure.render.target_unit).dim != dm.unit("kg").dim else "m"
    out.append(Mutant("misdeclared_answer_unit", "negative",
                      dataclasses.replace(structure, render=dataclasses.replace(
                          structure.render, target_unit=wrong_answer_unit)),
                      frozenset({"dimensions"}), f"answer unit declared as {wrong_answer_unit}"))

    rewritten = structure
    for node in structure.computed:
        simplified = str(sympy.simplify(gr.parse_expr(node.expr, names)))
        rewritten = _replace_node(rewritten, node.name, expr=simplified)
    out.append(Mutant("equivalent_rewrite", "positive", rewritten, frozenset(), "expressions simplified"))

    out.append(Mutant("rename_symbols", "positive", _renamed(structure), frozenset(), "every node renamed"))
    return out


def _renamed(structure: gr.Structure) -> gr.Structure:
    names = [n.name for n in structure.nodes]
    mapping = {n: f"z_{n}" for n in names}
    symbol_map = {sympy.Symbol(a): sympy.Symbol(b) for a, b in mapping.items()}
    nodes = tuple(dataclasses.replace(
        n, name=mapping[n.name],
        expr=str(gr.parse_expr(n.expr, names).xreplace(symbol_map)) if n.expr else None) for n in structure.nodes)
    assumptions = tuple(dataclasses.replace(a, applies_to=tuple(mapping[x] for x in a.applies_to))
                        for a in structure.assumptions)

    def retemplate(text: str) -> str:
        for old, new in mapping.items():
            text = text.replace("{" + old + "}", "{" + new + "}")
        return text

    render = dataclasses.replace(
        structure.render, context=retemplate(structure.render.context), question=retemplate(structure.render.question),
        formats={mapping.get(k, k): v for k, v in structure.render.formats.items()})
    instances = tuple({mapping[k]: v for k, v in inst.items()} for inst in structure.instances)
    return dataclasses.replace(
        structure, nodes=nodes, target=mapping[structure.target], assumptions=assumptions, render=render,
        relevant_edit=(mapping[structure.relevant_edit[0]], structure.relevant_edit[1]), instances=instances)


def mutation_report(structure: gr.Structure, n_draws: int = 12) -> list[dict[str, Any]]:
    rows = []
    for mutant in mutants(structure):
        proof = certify(mutant.structure, n_draws=n_draws)
        failed = {c["name"] for c in proof["checks"] if not c["passed"]}
        if mutant.kind == "negative":
            outcome = "caught" if failed else "ESCAPED"
            intended = bool(failed & mutant.expected_failed)
        else:
            outcome = "passed" if not failed else "WRONGLY_REJECTED"
            intended = not failed
        rows.append({"structure_id": structure.structure_id, "mutator_id": mutant.mutator_id, "kind": mutant.kind,
                     "outcome": outcome, "failed_checks": sorted(failed),
                     "failed_for_an_intended_reason": intended, "note": mutant.note})
    return rows
