"""Gold solving traces for every M0 v2 cell (plan revision v2.2, amendment A7).

A trace is rendered from the typed graph and the cell's wiring, never written by hand with numbers, so it cannot disagree with
the certificate. It extends `trace.py` (the October base trace) with the step that is specific to the cell:

* R: the step where q enters the input the spec wires it to, then the base relations on the changed input, ending at the
  cell's certified answer;
* D and N: the base trace plus one explicit line saying the sentence's quantity (or, for N, nothing) has no path to the target;
* C: q is given, enters the relations the spec lists, the unsimplified expression is evaluated with q, and the symbolic
  derivative with respect to q is shown to vanish;
* K: the regime predicate is evaluated numerically (both sides) and found true, then the base relations are used;
* K_out: the same predicate is found false and the out-of-regime law is evaluated;
* supporting cells: the base trace plus a line for the added sentence; the relevant edit is traced on the edited input and the
  role reversal subtracts the reference value.

The last value of a trace (`gold_trace["gold_answer"]["value"]`) is computed by the trace's own steps from the graph, and the
tests require it to equal the cell's gold within 1e-9 relative.
"""

from __future__ import annotations

import dataclasses
import importlib
import re
from typing import Any

import sympy

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import trace as tr

DOMAIN_MODULES = ("lib_mechanics", "lib_electromagnetism", "lib_thermodynamics", "lib_optics", "lib_quantum", "lib_modern",
                  "lib_fluids")
OP_TEXT = {"add": "{n}' = {n} + q", "subtract": "{n}' = {n} - q", "replace": "{n}' = q", "scale": "{n}' = {n} x q"}


def plans() -> dict[str, tr.Plan]:
    found: dict[str, tr.Plan] = {}
    for name in DOMAIN_MODULES:
        found.update(getattr(importlib.import_module(f"physmon.benchmark.v2.{name}"), "PLANS", {}))
    return found


def _num(x: float) -> str:
    return f"{x:.4g}"


def _with_unit(value: float, unit: str) -> str:
    return _num(value) if unit in ("1", "") else f"{_num(value)} {unit}"


def _subst(expression: str, names: list[str], values: dict[str, float]) -> str:
    pattern = re.compile(r"\b(" + "|".join(sorted((re.escape(n) for n in names), key=len, reverse=True)) + r")\b")
    return pattern.sub(lambda m: f"({_num(values[m.group(1)])})" if m.group(1) in values else m.group(1), expression)


def _givens(structure: gr.Structure, display: dict[str, float]) -> dict[str, Any]:
    return {"kind": "givens", "items": [
        {"name": n.name, "description": n.description, "value": display[n.name], "unit": dg.display_unit(n.unit),
         "provenance": "stated constant" if n.provenance == "assumed" else "given"} for n in structure.inputs]}


def _derive_steps(structure: gr.Structure, plan: tr.Plan, si: dict[str, float]) -> list[dict[str, Any]]:
    """The plan's derivation steps evaluated from the SI inputs `si` (updated in place with the computed nodes)."""

    names = [n.name for n in structure.nodes]
    by_name = {n.name: n for n in structure.nodes}
    steps = []
    for step in plan.steps:
        node = by_name[step.node]
        expression = node.expr or ""
        parents = sorted(str(s) for s in gr.parse_expr(expression, names).free_symbols)
        value_si = float(gr.parse_expr(expression, names).subs({p: si[p] for p in parents}).evalf())
        si[node.name] = value_si
        steps.append({"kind": "derive", "node": node.name, "description": node.description, "principle": step.principle,
                      "why": step.why, "relation": f"{node.name} = {expression}  (SI units)",
                      "substitution": f"{node.name} = {tr._substitute(expression, names, si)}", "value_si": value_si,
                      "value": dm.from_si(value_si, node.unit), "unit": dg.display_unit(node.unit)})
    return steps


def _finish(structure: gr.Structure, plan: tr.Plan, head: list[dict[str, Any]], derive: list[dict[str, Any]],
            final: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assemble numbered steps; `final` replaces the answer step (role reversal, C, K_out), otherwise the answer is the
    target node's value computed by the derive steps."""

    unit = dg.display_unit(structure.render.target_unit)
    steps = [*head, *derive]
    if final is None:
        value = next(s for s in derive if s["node"] == structure.target)["value"]
        steps += [{"kind": "check", "text": plan.check},
                  {"kind": "answer", "node": structure.target, "value": value, "unit": unit,
                   "text": f"{structure.render.quantity_phrase}: {_num(value)} {unit}"}]
    else:
        steps += final["steps"]
        value = final["value"]
    for i, step in enumerate(steps, start=1):
        step["n"] = i
    return {"structure_id": structure.structure_id, "steps": steps, "gold_answer": {"value": value, "unit": unit},
            "text": text_of(steps)}


def _head(structure: gr.Structure, plan: tr.Plan, display: dict[str, float], extra_givens: list[dict[str, Any]] | None = None,
          role_steps: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    givens = _givens(structure, display)
    givens["items"] += extra_givens or []
    return [{"kind": "restate", "text": f"Find the {structure.render.quantity_phrase}, in "
                                        f"{dg.display_unit(structure.render.target_unit)}."},
            givens, {"kind": "assumptions", "items": [a.text for a in structure.assumptions]},
            *(role_steps or []), {"kind": "approach", "text": plan.approach}]


def text_of(steps: list[dict[str, Any]]) -> str:
    lines = []
    for s in steps:
        head = f"Step {s['n']}. "
        kind = s["kind"]
        if kind == "restate":
            lines.append(head + s["text"])
        elif kind == "givens":
            lines.append(head + "Given: " + "; ".join(
                f"{i['name']} = {_with_unit(i['value'], i['unit'])} ({i['description']}; {i['provenance']})" for i in s["items"]))
        elif kind == "assumptions":
            lines.append(head + "Assumptions: " + " ".join(s["items"]))
        elif kind == "approach":
            lines.append(head + "Approach: " + s["text"])
        elif kind == "derive":
            lines.append(head + f"{s['principle'].rstrip('. ')}. {s['why'].rstrip(' ')} {s['relation']}. {s['substitution']} = "
                                f"{_num(s['value_si'])} (SI) = {_with_unit(s['value'], s['unit'])}.")
        elif kind == "check":
            lines.append(head + "Check: " + s["text"])
        elif kind == "answer":
            lines.append(head + "Answer: " + s["text"] + ".")
        else:  # role_entry, role_note, c_relation, c_combine, c_cancel, regime_check, out_of_regime, combine
            lines.append(head + s["text"])
    return "\n".join(lines)


# --- per-kind traces -------------------------------------------------------------------------------------------------------------

def base_trace(structure: gr.Structure, plan: tr.Plan, instance: int, role_text: str | None = None) -> dict[str, Any]:
    display = dict(structure.instances[instance])
    si = {n.name: dm.to_si(display[n.name], n.unit) for n in structure.inputs}
    steps = [{"kind": "role_note", "text": role_text}] if role_text else None
    return _finish(structure, plan, _head(structure, plan, display, role_steps=steps), _derive_steps(structure, plan, si))


def r_trace(structure: gr.Structure, plan: tr.Plan, instance: int, spec: r2.RoleSpecV2, value: float, sentence: str) -> dict[str, Any]:
    display = dict(structure.instances[instance])
    si = {n.name: dm.to_si(display[n.name], n.unit) for n in structure.inputs}
    w = spec.relevant
    node = structure.node(w.input_name)
    q_si = dm.to_si(value, spec.unit) if w.op != "scale" else value
    x = si[w.input_name]
    wired = rv._wired(structure, si, w, q_si)
    before, after = dm.from_si(x, node.unit), dm.from_si(wired[w.input_name], node.unit)
    q_in_node_unit = dm.from_si(q_si, node.unit) if w.op != "scale" else value
    symbol = {"add": "+", "subtract": "-", "replace": "->", "scale": "x"}[w.op]
    formula = (f"{OP_TEXT[w.op].format(n=w.input_name)} = {_num(before)} {symbol} {_num(q_in_node_unit)} = {_num(after)} "
              f"{dg.display_unit(node.unit)}" if w.op != "replace" else
              f"{OP_TEXT[w.op].format(n=w.input_name)} = {_num(q_in_node_unit)} {dg.display_unit(node.unit)} "
              f"(was {_num(before)} {dg.display_unit(node.unit)})")
    entry = {"kind": "role_entry", "input": w.input_name, "op": w.op, "q": value, "q_unit": dg.display_unit(spec.unit),
             "before": before, "after": after, "unit": dg.display_unit(node.unit),
             "text": f"The added sentence (\"{sentence}\") gives q = {_num(value)} {dg.display_unit(spec.unit)}. {w.rationale} "
                     f"In the graph this changes the input {w.input_name} ({node.description}): {formula}. "
                     f"Every later step uses the changed {w.input_name}."}
    derive = _derive_steps(structure, plan, dict(wired))
    return _finish(structure, plan, _head(structure, plan, display, role_steps=[entry]), derive)


def d_trace(structure: gr.Structure, plan: tr.Plan, instance: int, sentence: str, value: float | None, unit: str | None,
            rationale: str | None) -> dict[str, Any]:
    if value is None:
        text = (f"The added sentence (\"{sentence}\") contains no number: there is no quantity to use, so the problem is the "
                "base problem.")
    else:
        text = (f"The added sentence (\"{sentence}\") gives {_num(value)} {dg.display_unit(unit or '')}. This quantity has no "
                f"path to the target: {rationale[:1].lower() + rationale[1:]} It is not an input of any relation below, so it is not used and the answer is "
                "the base answer.")
    return base_trace(structure, plan, instance, text)


def c_trace(structure: gr.Structure, plan: tr.Plan, instance: int, c: r2.CancellingV2, value: float, sentence: str) -> dict[str, Any]:
    spec = c.spec
    display = dict(structure.instances[instance])
    si = {n.name: dm.to_si(display[n.name], n.unit) for n in structure.inputs}
    node_values = rv.all_node_values(structure, si)
    q_si = dm.to_si(value, spec.unit)
    names = [n.name for n in structure.nodes] + [rv.Q]
    env = {**node_values, rv.Q: q_si}
    extra = [{"name": "q", "description": spec.quantity_phrase, "value": value, "unit": dg.display_unit(spec.unit),
              "provenance": "given"}]
    expr = gr.parse_expr(spec.expr_with_q, names)
    value_si = rv._eval_expr(spec.expr_with_q, structure, node_values, q_si)
    simplified = sympy.simplify(expr)
    derivative = sympy.simplify(sympy.diff(expr, sympy.Symbol(rv.Q)))
    unit = dg.display_unit(structure.render.target_unit)
    shown = dm.from_si(value_si, structure.render.target_unit)
    steps = [{"kind": "role_note", "text": f"The added sentence (\"{sentence}\") gives {spec.quantity_phrase}, q = {_num(value)} "
                                          f"{dg.display_unit(spec.unit)} (= {_num(q_si)} in SI). It belongs to the system, so "
                                          "it may enter intermediate relations; only the final answer must not depend on it."}]
    steps += [{"kind": "c_relation", "text": f"Relation {i} that contains q: {rel}."} for i, rel in enumerate(spec.intermediate_relations, 1)]
    steps.append({"kind": "c_combine", "text": f"Combining them, with q kept: {structure.target} = {spec.expr_with_q}. Substituting the SI "
                                               f"values: {structure.target} = {_subst(spec.expr_with_q, names, env)} = {_num(value_si)} (SI) "
                                               f"= {_num(shown)} {unit}."})
    steps.append({"kind": "c_cancel", "text": f"q cancels: the expression simplifies to {simplified}, and its derivative with respect to q "
                                              f"is {derivative}. The answer is the same for every q: {_num(shown)} {unit}."})
    head = _head(structure, plan, display, extra_givens=extra)
    final = {"steps": [*steps, {"kind": "check", "text": plan.check},
                       {"kind": "answer", "node": structure.target, "value": shown, "unit": unit,
                        "text": f"{structure.render.quantity_phrase}: {_num(shown)} {unit}"}], "value": shown}
    return _finish(structure, plan, head, [], final)


def _predicate_sides(structure: gr.Structure, predicate: str, node_values: dict[str, float], q_si: float) -> tuple[float, str, float, bool]:
    names = [n.name for n in structure.nodes] + [rv.Q]
    expression = gr.parse_expr(predicate, names)
    if not isinstance(expression, sympy.core.relational.Relational):
        raise ValueError(f"predicate {predicate!r} is not a comparison")
    env = {**node_values, rv.Q: q_si}
    sides = []
    for side in (expression.lhs, expression.rhs):
        args = sorted(str(s) for s in side.free_symbols)
        sides.append(float(sympy.lambdify([sympy.Symbol(a) for a in args], side, modules="math")(*[env[a] for a in args])))
    return sides[0], expression.rel_op, sides[1], bool(rv._eval_expr(predicate, structure, node_values, q_si))


def k_trace(structure: gr.Structure, plan: tr.Plan, instance: int, k: r2.ConditionalV2, value: float, sentence: str,
            out_of_regime: bool = False) -> dict[str, Any]:
    spec = k.spec
    display = dict(structure.instances[instance])
    si = {n.name: dm.to_si(display[n.name], n.unit) for n in structure.inputs}
    node_values = rv.all_node_values(structure, si)
    q_si = dm.to_si(value, spec.unit)
    lhs, op, rhs, holds = _predicate_sides(structure, spec.predicate, node_values, q_si)
    names = [n.name for n in structure.nodes] + [rv.Q]
    env = {**node_values, rv.Q: q_si}
    check = {"kind": "regime_check", "predicate": spec.predicate, "lhs": lhs, "rhs": rhs, "holds": holds,
             "text": f"The added sentence (\"{sentence}\") gives {spec.quantity_phrase}, q = {_num(value)} {dg.display_unit(spec.unit)} "
                     f"(= {_num(q_si)} in SI). Regime check: the base relations hold only if {spec.predicate}. With the values "
                     f"above (SI): {_subst(spec.predicate, names, env)} gives {_num(lhs)} {op} {_num(rhs)}, which is "
                     f"{'true' if holds else 'false'}."}
    unit = dg.display_unit(structure.render.target_unit)
    if not out_of_regime:
        if not holds:
            raise ValueError(f"{structure.structure_id}: the in-regime K cell fails its predicate")
        check["text"] += " The condition holds, so the quantity does not act and the base relations apply."
        derive = _derive_steps(structure, plan, dict(si))
        return _finish(structure, plan, _head(structure, plan, display, role_steps=[check]), derive)
    if holds:
        raise ValueError(f"{structure.structure_id}: the K_out cell does not leave the regime")
    law_si = rv._eval_expr(spec.out_of_regime_law, structure, node_values, q_si)
    shown = dm.from_si(law_si, structure.render.target_unit)
    check["text"] += " The condition fails, so the base relations do not give the answer; the out-of-regime law applies."
    law = {"kind": "out_of_regime", "text": f"Out-of-regime law: {structure.target} = {spec.out_of_regime_law}. Substituting the SI values: "
                                            f"{structure.target} = {_subst(spec.out_of_regime_law, names, env)} = {_num(law_si)} (SI) = "
                                            f"{_num(shown)} {unit}."}
    final = {"steps": [law, {"kind": "check", "text": plan.check},
                       {"kind": "answer", "node": structure.target, "value": shown, "unit": unit,
                        "text": f"{structure.render.quantity_phrase}: {_num(shown)} {unit}"}], "value": shown}
    # the intermediate quantities the law uses (for example tau) are derived by the plan steps that it needs
    derive = _derive_steps(structure, plan, dict(si))
    derive = [d for d in derive if d["node"] != structure.target]
    return _finish(structure, plan, _head(structure, plan, display, role_steps=[check]), derive, final)


def edit_trace(structure: gr.Structure, plan: tr.Plan, instance: int, edited: dict[str, float], note: str) -> dict[str, Any]:
    changed = dataclasses.replace(structure, instances=(edited,))
    out = base_trace(changed, plan, 0, note)
    out["structure_id"] = structure.structure_id
    return out


def reversal_trace(structure: gr.Structure, plan: tr.Plan, instance: int, reference: float, sentence: str) -> dict[str, Any]:
    display = dict(structure.instances[instance])
    si = {n.name: dm.to_si(display[n.name], n.unit) for n in structure.inputs}
    derive = _derive_steps(structure, plan, si)
    base = next(s for s in derive if s["node"] == structure.target)["value"]
    unit = dg.display_unit(structure.render.target_unit)
    value = base - reference
    note = {"kind": "role_note", "text": f"The added sentence (\"{sentence}\") gives the corresponding value for system B, "
                                         f"{_num(reference)} {unit}. The question asks for this system's answer minus system B's."}
    combine = {"kind": "combine", "text": f"Subtract: {_num(base)} - {_num(reference)} = {_num(value)} {unit}."}
    final = {"steps": [combine, {"kind": "check", "text": plan.check},
                       {"kind": "answer", "node": structure.target, "value": value, "unit": unit,
                        "text": f"{structure.render.quantity_phrase} minus system B's: {_num(value)} {unit}"}], "value": value}
    return _finish(structure, plan, _head(structure, plan, display, role_steps=[note]), derive, final)


# --- dispatch ---------------------------------------------------------------------------------------------------------------------

def trace_for_role_cell(structure: gr.Structure, spec: r2.RoleSpecV2, plan: tr.Plan, cell: r2.Cell) -> dict[str, Any]:
    pair = next((p for p in spec.pairs if p.pair_id == cell.pair_id), None)
    if cell.stratum == "none":
        return base_trace(structure, plan, cell.instance)
    if cell.stratum == "N":
        return d_trace(structure, plan, cell.instance, cell.sentence, None, None, None)
    if cell.stratum == "R":
        return r_trace(structure, plan, cell.instance, spec, cell.value, cell.sentence)
    if cell.stratum == "D":
        return d_trace(structure, plan, cell.instance, cell.sentence, cell.value, cell.unit, pair.d_rationale)
    if cell.stratum == "C":
        return c_trace(structure, plan, cell.instance, spec.cancelling, cell.value, cell.sentence)
    if cell.stratum == "K":
        return k_trace(structure, plan, cell.instance, spec.conditional, cell.value, cell.sentence)
    if cell.stratum == "K_out":
        return k_trace(structure, plan, cell.instance, spec.conditional, cell.value, cell.sentence, out_of_regime=True)
    raise KeyError(cell.stratum)


def trace_for_support(structure: gr.Structure, plan: tr.Plan, sup: Any) -> dict[str, Any]:
    cid = sup.cell_id
    if cid == "nonnumeric_extra":
        return d_trace(structure, plan, sup.instance, sup.sentence, None, None, None)
    if cid == "relevant_edit":
        node, factor = structure.relevant_edit
        base = dict(structure.instances[sup.instance])
        note = (f"The statement changes the given {node} from {_num(base[node])} to {_num(sup.input_display[node])} "
                f"{dg.display_unit(structure.node(node).unit)} (a relevant edit: it is an input of the relations below). All later "
                "steps use the edited value.")
        return edit_trace(structure, plan, sup.instance, dict(sup.input_display), note)
    if cid == "role_reversal":
        return reversal_trace(structure, plan, sup.instance, sup.cue_value, sup.sentence)
    reasons = {"numeric_metadata": "it is the temperature of the laboratory, not an input of any relation of this problem.",
               "nongov_incompatible_unit_same_digits": "it is a reading of another device in another dimension, not an input of any relation of this "
                                                         "problem, and its numeral must not be copied into the answer.",
               "nongov_convertible_unit_same_magnitude": "it describes another system B in a convertible unit; it is not an input of any "
                                                           "relation of this problem and equals the answer's magnitude only by construction."}
    rationale = reasons.get(cid, "it describes another system B, not an input of any relation of this problem, and its numeral must "
                                 "not be copied into the answer.")
    return d_trace(structure, plan, sup.instance, sup.sentence, sup.cue_value, sup.cue_unit, rationale)
