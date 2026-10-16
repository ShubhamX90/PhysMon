"""Typed executable computation graphs for DECOY-v2 (Stage 14.6; v2 B3.2, p.8; P2.1, p.18).

A structure is a directed acyclic graph. Input nodes carry a value in a declared display unit; computed nodes carry
an expression over their parent nodes, evaluated in SI. Every node records its quantity type, unit (and hence
dimension), reference frame, sign convention and provenance (measured, computed or assumed). A structure also carries
its explicit assumptions, a prompt grammar, and an *independent* hand-coded numeric solver, so that certification
compares two routes that were written separately (v2 B3.2: "multiple routes ... not merely multiple outputs of the
same symbolic equation generator").

Nuisance quantities are never nodes of a correct graph: they appear only in the rendered text. A graph that makes the
target depend on a nuisance symbol is a defect that certification must reject.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import sympy

from physmon.benchmark.v2 import dimensions as dm

NUISANCE_SYMBOL = "n_dist"
PROVENANCE = ("measured", "computed", "assumed")
ASSUMPTION_KINDS = ("modelling", "boundary_condition")


class GraphError(ValueError):
    """Raised for a structurally invalid graph (cycle, undeclared symbol, bad node)."""


@dataclass(frozen=True)
class Node:
    name: str
    kind: str  # "input" or "computed"
    quantity_type: str
    unit: str
    description: str
    value: float | None = None  # inputs: value in `unit`
    expr: str | None = None  # computed: expression over parent node names, in SI
    provenance: str = "measured"
    frame: str = "laboratory frame"
    sign_convention: str = "magnitudes are positive"
    uncertainty: float | None = None
    domain: tuple[float, float] | None = None  # admissible range in `unit` (inputs)


@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    text: str
    kind: str  # "modelling" or "boundary_condition"
    applies_to: tuple[str, ...]


@dataclass(frozen=True)
class RenderSpec:
    """Prompt grammar. Templates use `{node_name}` for input values and `{v}` / `{u}` for a cue value and unit."""

    context: str
    question: str
    quantity_phrase: str
    target_unit: str
    isolated_sentence: str  # a separate system B with a same-unit quantity
    incompatible_sentence: str  # a quantity with a different dimension
    incompatible_unit: str
    metadata_sentence: str  # unrelated numeric metadata
    metadata_unit: str
    nonnumeric_sentence: str
    comparison_sentence: str  # a reference system B that the question compares against (role reversal)
    equivalent_unit: str | None = None  # a convertible unit of the target unit, for the same-magnitude cell
    fixed_numbers: tuple[str, ...] = ()
    formats: dict[str, str] = field(default_factory=dict)  # node name -> format spec (default ".4g")


@dataclass(frozen=True)
class Structure:
    structure_id: str
    title: str
    domain: str
    law_family: str
    nodes: tuple[Node, ...]
    target: str
    assumptions: tuple[Assumption, ...]
    render: RenderSpec
    relevant_edit: tuple[str, float]  # (input node name, multiplicative factor)
    solver: Callable[..., float]  # positional SI inputs in input-node order -> target in SI
    solver_arity: int
    solver_route: str  # a sentence naming how the independent route differs from the graph's closed form
    solver_rel_tol: float = 1e-9
    instances: tuple[dict[str, float], ...] = ()  # numeric instantiations: input values in display units

    @property
    def inputs(self) -> tuple[Node, ...]:
        return tuple(n for n in self.nodes if n.kind == "input")

    @property
    def computed(self) -> tuple[Node, ...]:
        return tuple(n for n in self.nodes if n.kind == "computed")

    def node(self, name: str) -> Node:
        for candidate in self.nodes:
            if candidate.name == name:
                return candidate
        raise GraphError(f"no node named {name!r}")


_RESERVED = {"pi": sympy.pi}


def parse_expr(text: str, names: Sequence[str] = ()) -> sympy.Expr:
    """Parse with an explicit symbol table so node names such as `I`, `E`, `C` or `S` stay plain symbols."""

    local = {name: sympy.Symbol(name) for name in names}
    local.update(_RESERVED)
    return sympy.sympify(text, locals=local)


def topological_order(structure: Structure) -> list[Node]:
    """Nodes in dependency order. Raises GraphError for a cycle or an undeclared symbol."""

    names = [n.name for n in structure.nodes]
    if len(set(names)) != len(names):
        raise GraphError("duplicate node names")
    by_name = {n.name: n for n in structure.nodes}
    parents: dict[str, set[str]] = {}
    for node in structure.nodes:
        if node.kind == "input":
            parents[node.name] = set()
        elif node.kind == "computed":
            if not node.expr:
                raise GraphError(f"computed node {node.name!r} has no expression")
            symbols = {str(s) for s in parse_expr(node.expr, names).free_symbols}
            unknown = symbols - set(by_name)
            if unknown:
                raise GraphError(f"node {node.name!r} uses undeclared symbol(s) {sorted(unknown)}")
            parents[node.name] = symbols
        else:
            raise GraphError(f"node {node.name!r} has kind {node.kind!r}")
    ordered: list[Node] = []
    placed: set[str] = set()
    remaining = dict(parents)
    while remaining:
        ready = sorted(n for n, deps in remaining.items() if deps <= placed)
        if not ready:
            raise GraphError(f"cycle among {sorted(remaining)}")
        for name in ready:
            ordered.append(by_name[name])
            placed.add(name)
            del remaining[name]
    return ordered


def ancestors(structure: Structure, name: str) -> set[str]:
    """All nodes the named node depends on (transitively)."""

    by_name = {n.name: n for n in structure.nodes}
    names = list(by_name)
    found: set[str] = set()
    stack = [name]
    while stack:
        node = by_name[stack.pop()]
        if node.kind != "computed":
            continue
        for symbol in parse_expr(node.expr or "0", names).free_symbols:
            if str(symbol) not in found:
                found.add(str(symbol))
                stack.append(str(symbol))
    return found


def compile_target(structure: Structure) -> Callable[[dict[str, float]], float]:
    """A fast evaluator: SI input values by node name -> target value in SI."""

    order = topological_order(structure)
    names = [n.name for n in structure.nodes]
    compiled: list[tuple[str, Callable[..., float], list[str]]] = []
    for node in order:
        if node.kind != "computed":
            continue
        expression = parse_expr(node.expr or "0", names)
        arguments = sorted(str(s) for s in expression.free_symbols)
        function = sympy.lambdify([sympy.Symbol(a) for a in arguments], expression, modules="math")
        compiled.append((node.name, function, arguments))
    target = structure.target

    def evaluate(si_inputs: dict[str, float]) -> float:
        values = dict(si_inputs)
        for name, function, arguments in compiled:
            values[name] = function(*[values[a] for a in arguments])
        return float(values[target])

    return evaluate


def base_si_inputs(structure: Structure) -> dict[str, float]:
    return {n.name: dm.to_si(float(n.value), n.unit) for n in structure.inputs}


def solver_inputs(structure: Structure, si_inputs: dict[str, float]) -> Sequence[float]:
    """Positional SI values for the hand-coded solver, in input-node order, truncated to its arity."""

    values = [si_inputs[n.name] for n in structure.inputs]
    if len(values) < structure.solver_arity:
        raise GraphError(f"solver expects {structure.solver_arity} inputs but the graph has {len(values)}")
    return values[: structure.solver_arity]


def target_value_si(structure: Structure, si_inputs: dict[str, float] | None = None) -> float:
    return compile_target(structure)(si_inputs if si_inputs is not None else base_si_inputs(structure))


def target_value_display(structure: Structure, si_inputs: dict[str, float] | None = None) -> float:
    return dm.from_si(target_value_si(structure, si_inputs), structure.render.target_unit)
