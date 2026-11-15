"""The non-physics dependency control set (plan of record v2.2, "Supporting conditions"; G1 decision 18).

Sixteen everyday word problems with no physics in them (counts, prices, scores, durations in whole minutes), each a small typed
dependency graph (2-4 relations) with a unique answer, carrying the same role manipulation as the M0 v2 physics structures: one
extra sentence with a number q that either enters the answer (R) or has no path to it (D), at three values, in two phrasing
pairs. The aim is only to tell a general numeric or dependency phenomenon from one that needs physical semantics. The set is
explicitly not powered: a null result there is INCONCLUSIVE.

The physics graph machinery (`graph.py`, `dimensions.py`) is built on SI dimensions and cannot carry "dollars" or "cookies", so
this module is a minimal parallel of it with exact arithmetic: a structure is a list of inputs and of computed nodes (expressions
over earlier names, evaluated with `fractions.Fraction`), plus a hand-coded solver written separately (the independent route).
Everything about wording is shared with M0 v2 and imported, not copied: `rolevalue_v2.PhrasePair`, the consequence and marker
lexicons, the remoteness list, token differences, word counts, digit overlap, and `rolevalue`'s placebo and separation helpers.
The rules are the M0 v2 rules; this module only supplies what the physics graph supplied (evaluation, wiring, foils, cells,
certification, hygiene). `rolevalue_v2.py` and `rolevalue.py` are not changed.
"""

from __future__ import annotations

import hashlib
import math
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import sympy

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

OPS = ("add", "subtract", "replace", "scale")
SCALE_UNIT = "times"  # the unit word of a scale quantity (a multiplier); it is not printed after the number
INSTANCE = 0
MONEY_UNITS = ("dollars",)
NAMESPACE = uuid.UUID("5d0f3c2a-61b4-5a58-9a0e-6e0c0b6f7e11")
LEVEL = "everyday_arithmetic"

# A small lexicon: nothing in a prompt of this set may use physics vocabulary, so physical knowledge cannot help.
PHYSICS_TERMS = (
    "metre", "meter", "kilogram", "newton", "joule", "watt", "volt", "ampere", "ohm", "kelvin", "celsius", "fahrenheit",
    "speed", "velocity", "acceleration", "force", "energy", "temperature", "pressure", "mass", "weight", "gravity", "friction",
    "momentum", "current", "voltage", "charge", "density", "volume", "distance", "length", "height", "width", "area", "angle",
    "wave", "light", "heat", "frequency", "power", "pulley", "lens", "magnet", "electric", "gas", "liquid", "kilometre",
    "kilometer", "centimetre", "centimeter", "mile", "litre", "liter", "gram", "second", "hour", "pound", "ounce", "inch",
    "foot", "feet", "yard", "degree",
)


# --- specification ---------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class NPInput:
    name: str
    description: str
    value: float
    unit: str  # a word ("dollars", "cookies"); two quantities have the same kind when the words are equal


@dataclass(frozen=True)
class NPNode:
    name: str
    expr: str  # over earlier names; + - * / and parentheses only
    description: str
    unit: str
    principle: str  # the rule used (for the gold trace)
    why: str  # why it applies here
    integral: bool = True  # the value must be a whole number (a count, whole minutes); money nodes are checked in cents


@dataclass(frozen=True)
class NPStructure:
    structure_id: str
    title: str
    theme: str
    context: str  # uses {input_name}
    question: str
    quantity_phrase: str  # "the change she gets back" is rendered as "Find the {quantity_phrase}"
    target: str
    target_unit: str
    inputs: tuple[NPInput, ...]
    nodes: tuple[NPNode, ...]
    solver: Callable[..., float]  # positional input values (input order) -> target; written separately from the expressions
    solver_route: str
    assumptions: tuple[str, ...]
    approach: str
    check: str
    target_phrases: tuple[str, ...]
    target_symbols: tuple[str, ...]

    def input(self, name: str) -> NPInput:
        return next(i for i in self.inputs if i.name == name)

    def node(self, name: str) -> NPNode:
        return next(n for n in self.nodes if n.name == name)


@dataclass(frozen=True)
class NPSpec:
    structure_id: str
    quantity_phrase: str
    unit: str  # the unit word of q (`times` for a scale quantity)
    values: tuple[float, ...]  # three study values
    heldout_values: tuple[float, ...]  # two held-out values, certified, never emitted
    wiring: rv.RelevantWiring
    pairs: tuple[r2.PhrasePair, ...]
    notes: str = ""
    author: str = "agent"


# --- evaluation ------------------------------------------------------------------------------------------------------------------

def _frac(x: float | Fraction) -> Fraction:
    return x if isinstance(x, Fraction) else Fraction(str(x))


def input_values(structure: NPStructure) -> dict[str, Fraction]:
    return {i.name: _frac(i.value) for i in structure.inputs}


def node_values(structure: NPStructure, inputs: dict[str, Fraction]) -> dict[str, Fraction]:
    """Every node value (exact), computed in the listed order from `inputs`."""

    env: dict[str, Fraction] = dict(inputs)
    for node in structure.nodes:
        env[node.name] = eval(node.expr, {"__builtins__": {}}, dict(env))  # noqa: S307 - expressions are spec literals
        env[node.name] = _frac(env[node.name])
    return env


def target_exact(structure: NPStructure, inputs: dict[str, Fraction]) -> Fraction:
    return node_values(structure, inputs)[structure.target]


def solver_value(structure: NPStructure, inputs: dict[str, Fraction]) -> Fraction:
    return _frac(structure.solver(*[inputs[i.name] for i in structure.inputs]))


def wired(structure: NPStructure, wiring: rv.RelevantWiring, q: float) -> dict[str, Fraction]:
    out = input_values(structure)
    x, qf = out[wiring.input_name], _frac(q)
    out[wiring.input_name] = {"add": x + qf, "subtract": x - qf, "replace": qf, "scale": x * qf}[wiring.op]
    return out


def gold_base(structure: NPStructure) -> float:
    return float(target_exact(structure, input_values(structure)))


def gold_r(structure: NPStructure, wiring: rv.RelevantWiring, q: float) -> tuple[float, float]:
    """(graph route, solver route) of the relevant-role answer."""

    inputs = wired(structure, wiring, q)
    return float(target_exact(structure, inputs)), float(solver_value(structure, inputs))


def misuse_foils(structure: NPStructure, spec: NPSpec, value: float) -> dict[str, float]:
    """Answers produced by each prespecified misuse of q: `copy` (q in the target's unit, when q is of the target's kind) or
    `digit_copy` (the numeral read as the answer), and replace, add or subtract on every input of q's unit; for a scale
    quantity, add and replace on the wired input."""

    foils: dict[str, float] = {"copy": float(_frac(value))} if spec.unit == structure.target_unit else {"digit_copy": float(_fmt_num(value))}
    candidates = [i.name for i in structure.inputs if i.unit == spec.unit]
    if spec.wiring.op == "scale":
        candidates = [spec.wiring.input_name]
    for name in candidates:
        for op in ("replace", "add", "subtract"):
            if spec.wiring.op == "scale" and op == "subtract":
                continue
            try:
                answer = target_exact(structure, wired(structure, rv.RelevantWiring(name, op, ""), value))
            except ZeroDivisionError:
                continue
            foils[f"{op}:{name}"] = float(answer)
    return foils


def _fmt_num(value: float) -> str:
    return rv._fmt(value)


def equivalent_foils(structure: NPStructure, spec: NPSpec) -> list[str]:
    """Misuse foils that give the relevant answer at every study and held-out value (subtracting q from the bill is the same
    computation as adding it to the purchase): not misuses in the R world, so they are dropped from every cell, as the wired
    operation itself is, and recorded."""

    values = (*spec.values, *spec.heldout_values)
    names: set[str] | None = None
    for v in values:
        y_r = gold_r(structure, spec.wiring, v)[0]
        same = {n for n, f in misuse_foils(structure, spec, v).items() if math.isclose(f, y_r, rel_tol=1e-9)}
        names = same if names is None else names & same
    return sorted(names or set())


# --- rendering -------------------------------------------------------------------------------------------------------------------

def input_text(value: float) -> str:
    return dg.positional(float(value), 4)


def context_text(structure: NPStructure) -> str:
    return structure.context.format(**{i.name: input_text(i.value) for i in structure.inputs})


def assemble(structure: NPStructure, sentence: str, instruction: str | None = None) -> str:
    context = context_text(structure)
    head = f"{context} {sentence}" if sentence else context
    prompt = f"{head}\n\n{structure.question}"
    return f"{prompt} {instruction}" if instruction else prompt


def displayed_inputs(structure: NPStructure) -> dict[str, float]:
    return {i.name: float(input_text(i.value)) for i in structure.inputs}


def prompt_numerals_ok(structure: NPStructure, prompt: str, value: float | None) -> bool:
    expected = sorted([*displayed_inputs(structure).values()] + ([float(rv._fmt(value))] if value is not None else []))
    return dg.prompt_numbers(prompt) == expected


def value_hygiene(structure: NPStructure, value: float, golds: list[float]) -> dict[str, Any]:
    shown = displayed_inputs(structure)
    equals = sorted(n for n, x in shown.items() if math.isclose(float(rv._fmt(value)), x, rel_tol=1e-9))
    overlap_inputs = max(r2.digit_overlap(value, x) for x in shown.values())
    overlap_gold = max(r2.digit_overlap(value, g) for g in golds)
    return {"value": value, "equals_input": equals, "digit_overlap_with_inputs": overlap_inputs,
            "digit_overlap_with_gold": overlap_gold,
            "ok": not equals and overlap_inputs <= r2.MAX_DIGIT_OVERLAP and overlap_gold <= r2.MAX_DIGIT_OVERLAP}


def physics_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [t for t in PHYSICS_TERMS if re.search(rf"(?<![a-z]){re.escape(t)}s?(?![a-z])", lowered)]


def structure_hash(structure: NPStructure) -> str:
    """A hash of the symbolic program: the target as an expression over the inputs, in input order."""

    names = [i.name for i in structure.inputs] + [n.name for n in structure.nodes]
    exprs = {n.name: gr.parse_expr(n.expr, names) for n in structure.nodes}
    target = exprs[structure.target]
    for node in reversed(structure.nodes):  # substitute computed names until only inputs remain
        target = target.subs({sympy.Symbol(node.name): exprs[node.name]})
    canonical = f"{sorted(str(s) for s in target.free_symbols)}|{sympy.srepr(sympy.simplify(target))}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def structure_uuid(structure: NPStructure) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{structure.structure_id}:{structure_hash(structure)}"))


# --- cells -----------------------------------------------------------------------------------------------------------------------

def _flags(sentence: str) -> tuple[bool, bool]:
    return (not r2.consequence_hits(sentence), not r2.marker_hits(sentence))


def _overlaps(structure: NPStructure, value: float | None, golds: list[float]) -> tuple[int | None, int | None]:
    if value is None:
        return None, None
    shown = displayed_inputs(structure)
    return max(r2.digit_overlap(value, x) for x in shown.values()), max(r2.digit_overlap(value, g) for g in golds)


def cells(structure: NPStructure, spec: NPSpec, *, include_heldout: bool = False) -> list[r2.Cell]:
    """No cue, one N per pair, R and D at every value and pair: 1 + 2 + 12 = 15 cells at three study values."""

    target_unit = structure.target_unit
    y_d = gold_base(structure)
    sign_definite = y_d > 0
    equivalent = set(equivalent_foils(structure, spec))
    out = [r2.Cell(structure.structure_id, INSTANCE, "no_cue", "role_by_value", "none", None, None, None, None, None, None,
                   "after_context", None, "", assemble(structure, ""), y_d, target_unit)]
    for index, pair in enumerate(spec.pairs):
        sentence = r2.pair_sentence(pair, "D", None, spec.unit)
        c, m = _flags(sentence)
        out.append(r2.Cell(structure.structure_id, INSTANCE, f"N:d{index}:after_context", "role_by_value", "N", None, None, None,
                           f"d{index}", pair.pair_id, pair.d_kind, "after_context", None, sentence, assemble(structure, sentence),
                           y_d, target_unit, consequence_free=c, marker_free=m))
    values = list(spec.values) + (list(spec.heldout_values) if include_heldout else [])
    for z, value in enumerate(values):
        heldout = z >= len(spec.values)
        y_r, _ = gold_r(structure, spec.wiring, value)
        foils = misuse_foils(structure, spec, value)
        placebo, _kind = rv.placebo_value(y_r, y_d, sign_definite)
        base_foils = {k: v for k, v in foils.items()
                      if k != f"{spec.wiring.op}:{spec.wiring.input_name}" and k not in equivalent}
        for role in ("R", "D"):
            for index, pair in enumerate(spec.pairs):
                sentence = r2.pair_sentence(pair, role, value, spec.unit)
                gold = y_r if role == "R" else y_d
                cell_foils = dict(base_foils)
                if role == "D":
                    cell_foils["relevant_twin"] = y_r
                else:
                    cell_foils["neglect"] = y_d
                named = {"gold": gold, **cell_foils}
                confounded = [f"{a}~{b}" for a, b in rv._not_separated(named) if "gold" in (a, b)]
                c, m = _flags(sentence)
                o_in, o_gold = _overlaps(structure, value, [gold])
                out.append(r2.Cell(structure.structure_id, INSTANCE, f"{role}:z{z}:{role.lower()}{index}:after_context",
                                   "role_by_value", role, z, value, spec.unit, f"{role.lower()}{index}", pair.pair_id,
                                   pair.d_kind if role == "D" else None, "after_context", None, sentence,
                                   assemble(structure, sentence), gold, target_unit, cell_foils,
                                   placebo if role == "R" else None, confounded, c, m, o_in, o_gold, heldout))
    return out


# --- certification ---------------------------------------------------------------------------------------------------------------

def _within(a: float, b: float, tol: float) -> bool:
    scale = max(abs(a), abs(b))
    return scale == 0 or abs(a - b) <= tol * scale


def certify(structure: NPStructure, spec: NPSpec) -> dict[str, Any]:
    """Every check of one structure and its spec; `passed` is true only if all blocking checks pass."""

    checks: dict[str, Any] = {}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        checks[name] = {"ok": bool(ok), "detail": detail}

    # structure
    names = [i.name for i in structure.inputs]
    ordered = True
    for node in structure.nodes:
        used = {str(s) for s in gr.parse_expr(node.expr, [*names, *[n.name for n in structure.nodes]]).free_symbols}
        ordered &= used <= set(names) and node.name not in names
        names.append(node.name)
    check("nodes_in_dependency_order", ordered)
    check("relations_2_to_4", 2 <= len(structure.nodes) <= 4, len(structure.nodes))
    check("target_is_last_node", structure.nodes[-1].name == structure.target)
    check("target_unit_matches", structure.node(structure.target).unit == structure.target_unit, structure.target_unit)
    check("inputs_typed", all(i.unit and i.description for i in structure.inputs))
    check("all_inputs_used", {i.name for i in structure.inputs} <= {str(s) for s in gr.parse_expr(
        "+".join(n.expr for n in structure.nodes), names).free_symbols}, [i.name for i in structure.inputs])
    context = context_text(structure)
    text = " ".join([context, structure.question])
    check("base_numerals_are_the_inputs", prompt_numerals_ok(structure, assemble(structure, ""), None))
    check("no_physics_vocabulary_in_base", not physics_hits(text), physics_hits(text))
    base_values = node_values(structure, input_values(structure))
    base_ok = all((not n.integral) or base_values[n.name].denominator == 1 for n in structure.nodes)
    check("integral_nodes_whole_in_base", base_ok, {n.name: str(base_values[n.name]) for n in structure.nodes})
    gold = float(base_values[structure.target])
    cents_ok = (structure.target_unit not in MONEY_UNITS) or (base_values[structure.target] * 100).denominator == 1
    check("answer_is_exact_and_sensible", gold > 0 and cents_ok and structure.target_unit == structure.node(structure.target).unit,
          gold)
    check("base_routes_agree", math.isclose(float(solver_value(structure, input_values(structure))), gold, rel_tol=1e-9),
          [gold, float(solver_value(structure, input_values(structure)))])
    nphrase = [p for p in structure.target_phrases if p.lower() in structure.question.lower()]
    check("target_naming", bool(nphrase) and bool(structure.target_symbols) and structure.target in structure.target_symbols,
          {"phrases_in_question": nphrase, "symbols": list(structure.target_symbols)})
    # spec
    check("values_3_heldout_2", len(spec.values) == 3 and len(spec.heldout_values) == 2, [spec.values, spec.heldout_values])
    check("wiring_known", spec.wiring.op in OPS and spec.wiring.input_name in {i.name for i in structure.inputs}
          and len(spec.wiring.rationale) >= r2.MIN_RATIONALE, [spec.wiring.input_name, spec.wiring.op])
    unit_ok = (spec.unit == SCALE_UNIT) if spec.wiring.op == "scale" else (
        spec.wiring.input_name in {i.name for i in structure.inputs} and structure.input(spec.wiring.input_name).unit == spec.unit)
    check("wiring_unit_consistent", unit_ok, [spec.unit, spec.wiring.op])
    if not (checks["wiring_known"]["ok"] and checks["wiring_unit_consistent"]["ok"]) or len(spec.pairs) != 2:
        return {"passed": False, "failed": [k for k, v in checks.items() if not v["ok"]], "checks": checks, "pairs": [],
                "hygiene": {}, "numeric": {}}
    rows: dict[float, dict[str, Any]] = {}
    for value in (*spec.values, *spec.heldout_values):
        graph_r, solver_r = gold_r(structure, spec.wiring, value)
        inputs = wired(structure, spec.wiring, value)
        nv = node_values(structure, inputs)
        whole = all((not n.integral) or nv[n.name].denominator == 1 for n in structure.nodes)
        cents = (structure.target_unit not in MONEY_UNITS) or (nv[structure.target] * 100).denominator == 1
        rows[value] = {"y_r": graph_r, "solver_r": solver_r, "routes_agree": math.isclose(graph_r, solver_r, rel_tol=1e-9),
                       "whole_numbers": whole, "cents": cents, "sensible": graph_r > 0, "foils": misuse_foils(structure, spec, value)}
    check("routes_agree", all(r["routes_agree"] for r in rows.values()))
    check("r_integral_nodes_whole", all(r["whole_numbers"] and r["cents"] for r in rows.values()),
          {str(v): [r["whole_numbers"], r["cents"]] for v, r in rows.items()})
    check("r_answers_positive", all(r["sensible"] for r in rows.values()), {str(v): r["y_r"] for v, r in rows.items()})
    check("r_separated_from_d", all(abs(r["y_r"] - gold) > rv.LOOSEST_REL_TOL * max(abs(r["y_r"]), abs(gold)) for r in rows.values()))
    study = [rows[v]["y_r"] for v in spec.values]
    check("r_values_distinct", all(abs(a - b) > rv.LOOSEST_REL_TOL * max(abs(a), abs(b))
                                   for i, a in enumerate(study) for b in study[i + 1:]), study)
    # pairs
    check("exactly_two_pairs", [p.pair_id for p in spec.pairs] == list(r2.PAIR_IDS))
    check("d_kinds", spec.pairs[0].d_kind == r2.D_KIND_CO_PRESENT and spec.pairs[1].d_kind == "same_object_other_event",
          [p.d_kind for p in spec.pairs])
    pair_records = []
    for pair in spec.pairs:
        value0, unit = spec.values[0], spec.unit
        r_sentence, d_sentence = r2.pair_sentence(pair, "R", value0, unit), r2.pair_sentence(pair, "D", value0, unit)
        n_sentence = r2.pair_sentence(pair, "D", None, unit)
        record: dict[str, Any] = {"pair_id": pair.pair_id, "d_kind": pair.d_kind, "r_sentence": r_sentence, "d_sentence": d_sentence,
                                  "n_sentence": n_sentence, "d_rationale": pair.d_rationale,
                                  "conditions_preserved": list(pair.conditions_preserved),
                                  "token_difference": r2.token_difference(r_sentence, d_sentence),
                                  "word_counts": [len(r2.words(r_sentence)), len(r2.words(d_sentence))]}
        record["word_count_ok"] = abs(record["word_counts"][0] - record["word_counts"][1]) <= r2.MAX_WORD_DIFF
        record["same_frame_numeral_unit"] = (r_sentence.replace(pair.r_attach, "@") == d_sentence.replace(pair.d_attach, "@")
                                             and pair.frame_matched)
        record["pair_frame_matched"] = pair.frame_matched
        sentences = {"R": [r2.pair_sentence(pair, "R", v, unit) for v in spec.values],
                     "D": [r2.pair_sentence(pair, "D", v, unit) for v in spec.values], "N": [n_sentence]}
        record["consequence_free"] = {k: not any(r2.consequence_hits(s) for s in v) for k, v in sentences.items()}
        record["marker_free"] = {k: not any(r2.marker_hits(s) for s in v) for k, v in sentences.items()}
        record["remoteness_free_d"] = not any(r2.remoteness_hits(s) for s in sentences["D"])
        record["no_physics_vocabulary"] = not any(physics_hits(s) for v in sentences.values() for s in v)
        record["attach_has_no_digit"] = not any(re.search(r"\d", a) for a in (pair.r_attach, pair.d_attach))
        record["d_rationale_ok"] = len(pair.d_rationale.strip()) >= r2.MIN_RATIONALE
        missing = [c for c in pair.conditions_preserved if c not in context]
        record["conditions_listed"] = bool(pair.conditions_preserved)
        record["conditions_in_base_text"] = not missing
        record["conditions_missing"] = missing
        record["numerals_ok"] = all(prompt_numerals_ok(structure, assemble(structure, s), v)
                                    for role in ("R", "D") for s, v in zip(sentences[role], spec.values, strict=True))
        record["n_has_no_digit"] = not re.search(r"\d", n_sentence)
        pair_records.append(record)
    for key in ("word_count_ok", "attach_has_no_digit", "d_rationale_ok", "conditions_listed", "conditions_in_base_text",
                "numerals_ok", "remoteness_free_d", "no_physics_vocabulary", "n_has_no_digit"):
        check(key, all(p[key] for p in pair_records), [p[key] for p in pair_records])
    check("same_frame_numeral_unit", all(p["same_frame_numeral_unit"] for p in pair_records),
          [p["same_frame_numeral_unit"] for p in pair_records])
    check("consequence_free", all(all(p["consequence_free"].values()) for p in pair_records))
    check("marker_free", all(all(p["marker_free"].values()) for p in pair_records))
    # hygiene and separation across the emitted cells
    all_cells = cells(structure, spec)
    held_cells = cells(structure, spec, include_heldout=True)
    golds = sorted({round(c.gold_value, 12) for c in held_cells})
    hygiene = {"R_D": [value_hygiene(structure, v, golds) for v in spec.values],
               "R_D_heldout": [value_hygiene(structure, v, golds) for v in spec.heldout_values]}
    check("value_hygiene", all(h["ok"] for h in hygiene["R_D"]), hygiene["R_D"])
    check("heldout_value_hygiene", all(h["ok"] for h in hygiene["R_D_heldout"]), hygiene["R_D_heldout"])
    d_cells = [c for c in all_cells if c.stratum == "D"]
    degenerate = sorted({n for n in (d_cells[0].foils if d_cells else {})
                         if all(_within(c.foils[n], c.gold_value, rv.LOOSEST_REL_TOL) for c in d_cells if n in c.foils)})
    confounded = {c.cell_id: c.confounded for c in all_cells if c.confounded}
    blocking = {cid: [p for p in pairs if not all(n in degenerate or n == "gold" for n in p.split("~"))]
                for cid, pairs in confounded.items()}
    blocking = {k: v for k, v in blocking.items() if v}
    check("no_confounded_foils_except_degenerate", not blocking, blocking)
    skip = {"relevant_twin", "neglect", *degenerate}
    collisions = []
    for cell in held_cells:
        for name, foil in cell.foils.items():
            if name in skip:
                continue
            for g in golds:
                if _within(foil, g, rv.LOOSEST_REL_TOL) and not math.isclose(g, round(cell.gold_value, 12), rel_tol=1e-9):
                    collisions.append({"cell": cell.cell_id, "foil": name, "foil_value": foil, "other_gold": g})
    check("foils_not_equal_to_other_cells_golds", not collisions, collisions)
    placebos = [c.placebo for c in all_cells if c.placebo is not None]
    plac_bad = []
    for c in all_cells:
        if c.placebo is None:
            continue
        for g in golds:
            if _within(c.placebo, g, rv.LOOSEST_REL_TOL):
                plac_bad.append({"cell": c.cell_id, "placebo": c.placebo, "gold": g})
    check("placebo_separated_from_every_gold", not plac_bad, plac_bad)
    check("cell_count_15", len(all_cells) == 15, len(all_cells))
    failed = [k for k, v in checks.items() if not v["ok"]]
    return {"passed": not failed, "failed": failed, "checks": checks, "pairs": pair_records, "hygiene": hygiene,
            "numeric": {"gold_d": gold, "r": {str(v): {k: r[k] for k in ("y_r", "solver_r")} for v, r in rows.items()},
                        "degenerate_misuse_foils": degenerate, "equivalent_to_wiring_dropped": equivalent_foils(structure, spec),
                        "placebos": placebos, "all_confounded_pairs": confounded}}


# --- gold traces -----------------------------------------------------------------------------------------------------------------

def _num(x: float | Fraction) -> str:
    return f"{float(x):.4g}"


def _subst(expression: str, env: dict[str, Fraction]) -> str:
    pattern = re.compile(r"\b(" + "|".join(sorted((re.escape(n) for n in env), key=len, reverse=True)) + r")\b")
    return pattern.sub(lambda m: f"({_num(env[m.group(1)])})", expression)


def _text_of(steps: list[dict[str, Any]]) -> str:
    lines = []
    for s in steps:
        head, kind = f"Step {s['n']}. ", s["kind"]
        if kind == "restate":
            lines.append(head + s["text"])
        elif kind == "givens":
            lines.append(head + "Given: " + "; ".join(f"{i['name']} = {_num(i['value'])} {i['unit']} ({i['description']})"
                                                       for i in s["items"]))
        elif kind == "assumptions":
            lines.append(head + "Assumptions: " + " ".join(s["items"]))
        elif kind == "approach":
            lines.append(head + "Approach: " + s["text"])
        elif kind == "derive":
            lines.append(head + f"{s['principle'].rstrip('. ')}. {s['why'].rstrip(' ')} {s['relation']}. {s['substitution']} = "
                                f"{_num(s['value'])} {s['unit']}.")
        elif kind == "check":
            lines.append(head + "Check: " + s["text"])
        elif kind == "answer":
            lines.append(head + "Answer: " + s["text"] + ".")
        else:
            lines.append(head + s["text"])
    return "\n".join(lines)


def _derive(structure: NPStructure, inputs: dict[str, Fraction]) -> tuple[list[dict[str, Any]], dict[str, Fraction]]:
    env: dict[str, Fraction] = dict(inputs)
    steps = []
    for node in structure.nodes:
        substitution = f"{node.name} = {_subst(node.expr, env)}"
        env[node.name] = _frac(eval(node.expr, {"__builtins__": {}}, dict(env)))  # noqa: S307
        steps.append({"kind": "derive", "node": node.name, "description": node.description, "principle": node.principle,
                      "why": node.why, "relation": f"{node.name} = {node.expr}", "substitution": substitution,
                      "value": float(env[node.name]), "unit": node.unit})
    return steps, env


def trace_for_cell(structure: NPStructure, spec: NPSpec, cell: r2.Cell) -> dict[str, Any]:
    """The gold trace of one cell, rendered from the structure and the cell's wiring (never written with numbers by hand)."""

    base = input_values(structure)
    head: list[dict[str, Any]] = [
        {"kind": "restate", "text": f"Find the {structure.quantity_phrase}, in {structure.target_unit}."},
        {"kind": "givens", "items": [{"name": i.name, "description": i.description, "value": i.value, "unit": i.unit,
                                       "provenance": "given"} for i in structure.inputs]},
        {"kind": "assumptions", "items": list(structure.assumptions)}]
    inputs = dict(base)
    sentence = cell.sentence
    if cell.stratum == "R":
        w = spec.wiring
        before = base[w.input_name]
        inputs = wired(structure, w, cell.value)
        after = inputs[w.input_name]
        unit = structure.input(w.input_name).unit
        formula = {"add": f"{w.input_name}' = {w.input_name} + q = {_num(before)} + {_num(cell.value)} = {_num(after)} {unit}",
                   "subtract": f"{w.input_name}' = {w.input_name} - q = {_num(before)} - {_num(cell.value)} = {_num(after)} {unit}",
                   "replace": f"{w.input_name}' = q = {_num(cell.value)} {unit} (was {_num(before)} {unit})",
                   "scale": f"{w.input_name}' = {w.input_name} x q = {_num(before)} x {_num(cell.value)} = {_num(after)} {unit}"}[w.op]
        head.append({"kind": "role_entry", "input": w.input_name, "op": w.op, "q": cell.value, "q_unit": spec.unit,
                     "before": float(before), "after": float(after), "unit": unit,
                     "text": f"The added sentence (\"{sentence}\") gives q = {_num(cell.value)} {spec.unit}. {w.rationale} In the graph "
                             f"this changes the input {w.input_name} ({structure.input(w.input_name).description}): {formula}. Every "
                             f"later step uses the changed {w.input_name}."})
    elif cell.stratum == "D":
        pair = next(p for p in spec.pairs if p.pair_id == cell.pair_id)
        head.append({"kind": "role_note", "text": f"The added sentence (\"{sentence}\") gives {_num(cell.value)} {spec.unit}. This "
                     f"quantity has no path to the target: {pair.d_rationale[:1].lower() + pair.d_rationale[1:]} It is not an input of "
                     "any relation below, so it is not used and the answer is the base answer."})
    elif cell.stratum == "N":
        head.append({"kind": "role_note", "text": f"The added sentence (\"{sentence}\") contains no number: there is no quantity to "
                     "use, so the problem is the base problem."})
    head.append({"kind": "approach", "text": structure.approach})
    derive, env = _derive(structure, inputs)
    value = float(env[structure.target])
    steps = [*head, *derive, {"kind": "check", "text": structure.check},
             {"kind": "answer", "node": structure.target, "value": value, "unit": structure.target_unit,
              "text": f"{structure.quantity_phrase}: {_num(value)} {structure.target_unit}"}]
    for i, step in enumerate(steps, start=1):
        step["n"] = i
    return {"structure_id": structure.structure_id, "steps": steps, "gold_answer": {"value": value, "unit": structure.target_unit},
            "text": _text_of(steps)}
