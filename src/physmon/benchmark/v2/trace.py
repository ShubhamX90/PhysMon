"""Gold solution traces for DECOY-v2 structures (Stage 14.19).

A gold trace is not model text. It is a step-by-step solving technique that is built from the typed graph, so its numbers cannot
disagree with the graph: the author of a structure supplies only, for each computed node, the NAMED principle that produces it and the
reason it applies (a `Plan`); `render_trace` supplies the givens, the symbolic relation, the substitution with the instance's SI
values, the result and the unit, all evaluated from the graph, and ends with the answer. `validate_plan` rejects a plan that does not
cover every computed node exactly once, in dependency order, or whose text is empty or too short to teach anything.

A trace is a description of a correct approach. It is checked by the certifier's independent solver (the final value must equal the
solver's) and by blind re-derivation by a separate verifier; it is not a human expert's review and is labelled accordingly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2 import graph as gr

MIN_TEXT = 25  # characters; a principle or reason shorter than this cannot name a law and say why it applies


@dataclass(frozen=True)
class Step:
    node: str  # the computed node this step produces
    principle: str  # the named law, definition or principle used
    why: str  # why it applies in this situation, and what it lets us find


@dataclass(frozen=True)
class Plan:
    approach: str  # the strategy in one or two sentences: what is asked, which physics governs it, in which order
    steps: tuple[Step, ...]
    check: str  # a sanity check: a limiting case, an order of magnitude, a symmetry or a dimensional argument


def validate_plan(structure: gr.Structure, plan: Plan) -> list[str]:
    """Problems with a plan; an empty list means it is acceptable."""

    problems: list[str] = []
    order = [n.name for n in gr.topological_order(structure) if n.kind == "computed"]
    covered = [s.node for s in plan.steps]
    if len(set(covered)) != len(covered):
        problems.append("a computed node has more than one step")
    missing = [n for n in order if n not in covered]
    if missing:
        problems.append(f"computed nodes without a step: {missing}")
    unknown = [n for n in covered if n not in order]
    if unknown:
        problems.append(f"steps for nodes that are not computed nodes: {unknown}")
    position = {name: i for i, name in enumerate(order)}
    known = [n for n in covered if n in position]
    if known != sorted(known, key=position.__getitem__):
        problems.append("steps are not in dependency order")
    if covered and covered[-1] != structure.target:
        problems.append("the last step must produce the target")
    for label, text in (("approach", plan.approach), ("check", plan.check)):
        if len(text.strip()) < MIN_TEXT:
            problems.append(f"{label} is too short")
    for step in plan.steps:
        for label, text in (("principle", step.principle), ("why", step.why)):
            if len(text.strip()) < MIN_TEXT:
                problems.append(f"step for {step.node}: {label} is too short")
    return problems


def _number(value: float) -> str:
    return f"{value:.4g}"


def _with_unit(value: float, unit: str) -> str:
    return _number(value) if unit == "1" else f"{_number(value)} {unit}"


def _substitute(expression: str, names: list[str], si: dict[str, float]) -> str:
    pattern = re.compile(r"\b(" + "|".join(sorted((re.escape(n) for n in names), key=len, reverse=True)) + r")\b")
    return pattern.sub(lambda m: f"({_number(si[m.group(1)])})", expression)


def render_trace(structure: gr.Structure, plan: Plan, instance: int) -> dict[str, Any]:
    """The gold trace of one instantiation, with every number evaluated from the graph."""

    problems = validate_plan(structure, plan)
    if problems:
        raise ValueError(f"{structure.structure_id}: plan is not valid: {problems}")
    display = dict(structure.instances[instance])
    names = [n.name for n in structure.nodes]
    si = {n.name: dm.to_si(display[n.name], n.unit) for n in structure.inputs}
    by_name = {n.name: n for n in structure.nodes}
    steps: list[dict[str, Any]] = [
        {"kind": "restate", "text": f"Find the {structure.render.quantity_phrase}, in {dg.display_unit(structure.render.target_unit)}."},
        {"kind": "givens", "items": [
            {"name": n.name, "description": n.description, "value": display[n.name], "unit": dg.display_unit(n.unit),
             "provenance": "stated constant" if n.provenance == "assumed" else "given"} for n in structure.inputs]},
        {"kind": "assumptions", "items": [a.text for a in structure.assumptions]},
        {"kind": "approach", "text": plan.approach},
    ]
    for step in plan.steps:
        node = by_name[step.node]
        expression = node.expr or ""
        parents = sorted(str(s) for s in gr.parse_expr(expression, names).free_symbols)
        value_si = float(gr.parse_expr(expression, names).subs({p: si[p] for p in parents}).evalf())
        si[node.name] = value_si
        shown = dm.from_si(value_si, node.unit)
        steps.append({"kind": "derive", "node": node.name, "description": node.description, "principle": step.principle,
                      "why": step.why, "relation": f"{node.name} = {expression}  (SI units)",
                      "substitution": f"{node.name} = {_substitute(expression, names, si)}", "value_si": value_si, "value": shown,
                      "unit": dg.display_unit(node.unit)})
    target = by_name[structure.target]
    gold = dg.gold_for(structure, display)
    steps.append({"kind": "check", "text": plan.check})
    steps.append({"kind": "answer", "node": target.name, "value": gold, "unit": dg.display_unit(structure.render.target_unit),
                  "text": f"{structure.render.quantity_phrase}: {_number(gold)} {dg.display_unit(structure.render.target_unit)}"})
    for i, step in enumerate(steps, start=1):
        step["n"] = i
    return {"structure_id": structure.structure_id, "instance": instance, "steps": steps,
            "gold_answer": {"value": gold, "unit": dg.display_unit(structure.render.target_unit)},
            "text": trace_text(steps)}


def trace_text(steps: list[dict[str, Any]]) -> str:
    """The trace as plain numbered text, for reading and for a verifier."""

    lines: list[str] = []
    for s in steps:
        head = f"Step {s['n']}. "
        if s["kind"] == "restate":
            lines.append(head + s["text"])
        elif s["kind"] == "givens":
            lines.append(head + "Given: " + "; ".join(f"{i['name']} = {_with_unit(i['value'], i['unit'])} ({i['description']}; {i['provenance']})"
                                                       for i in s["items"]))
        elif s["kind"] == "assumptions":
            lines.append(head + "Assumptions: " + " ".join(s["items"]))
        elif s["kind"] == "approach":
            lines.append(head + "Approach: " + s["text"])
        elif s["kind"] == "derive":
            lines.append(head + f"{s['principle'].rstrip('. ')}. {s['why'].rstrip(' ')} {s['relation']}. {s['substitution']} = {_number(s['value_si'])} (SI) = "
                         f"{_with_unit(s['value'], s['unit'])}.")
        elif s["kind"] == "check":
            lines.append(head + "Check: " + s["text"])
        elif s["kind"] == "answer":
            lines.append(head + "Answer: " + s["text"] + ".")
    return "\n".join(lines)
