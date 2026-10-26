"""Tests for the Stage 14.19 gold-trace renderer and plan validator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.benchmark.v2 import graph as gr  # noqa: E402
from physmon.benchmark.v2 import library, library_b, library_c  # noqa: E402
from physmon.benchmark.v2 import trace as tr  # noqa: E402

BRAKING = tr.Plan(
    approach="A sliding car decelerates at a constant rate set by friction, so use kinematics with that deceleration to find the stopping distance.",
    steps=(tr.Step("d", "Newton's second law with kinetic friction, then constant-deceleration kinematics v^2 = 2 a d",
                   "The friction force mu m g is the only horizontal force, so the deceleration is mu g; the car stops when v reaches zero."),),
    check="Doubling the speed quadruples the distance, as expected from v^2; the units are metres.")


def s11():
    return next(s for s in library_b.all_structures() if s.structure_id == "S11")


def test_a_valid_plan_renders_a_trace_whose_last_value_is_the_solver_value():
    structure = s11()
    trace = tr.render_trace(structure, BRAKING, 0)
    kinds = [s["kind"] for s in trace["steps"]]
    assert kinds == ["restate", "givens", "assumptions", "approach", "derive", "check", "answer"]
    solver = structure.solver(*gr.solver_inputs(structure, {n.name: dm.to_si(structure.instances[0][n.name], n.unit) for n in structure.inputs}))
    assert trace["gold_answer"]["value"] == pytest.approx(solver, rel=1e-6)
    derive = next(s for s in trace["steps"] if s["kind"] == "derive")
    assert derive["relation"].startswith("d = v0**2/(2*mu*g)") and "(20)" in derive["substitution"] and derive["unit"] == "m"
    assert [s["n"] for s in trace["steps"]] == list(range(1, 8))
    assert "Answer:" in trace["text"] and "Newton's second law" in trace["text"]


def test_the_trace_numbers_come_from_the_graph_for_every_instantiation():
    structure = s11()
    for i, instance in enumerate(structure.instances):
        trace = tr.render_trace(structure, BRAKING, i)
        v0, mu, g = instance["v0"], instance["mu"], instance["g"]
        assert trace["gold_answer"]["value"] == pytest.approx(v0 ** 2 / (2 * mu * g))


def test_a_plan_that_misses_a_node_has_a_wrong_order_or_is_too_terse_is_rejected():
    atwood = library.all_structures()[0]  # S01 has two computed nodes (m_eff, a)
    one = tr.Plan("A long enough approach sentence for the validator to accept it.",
                  (tr.Step("a", "Newton's second law for the whole system", "It gives the acceleration from the net driving weight and the total inertia."),),
                  "The acceleration is smaller than g, as it must be for a balanced system.")
    assert any("without a step" in p for p in tr.validate_plan(atwood, one))
    reversed_plan = tr.Plan(one.approach, (one.steps[0], tr.Step("m_eff", "The effective inertia of the blocks plus half the pulley mass", "The disc pulley adds half its mass to the moving inertia.")), one.check)
    problems = tr.validate_plan(atwood, reversed_plan)
    assert any("dependency order" in p for p in problems) and any("last step" in p for p in problems)
    terse = tr.Plan("short", BRAKING.steps, "tiny")
    assert any("approach is too short" in p for p in tr.validate_plan(s11(), terse)) and any("check is too short" in p for p in tr.validate_plan(s11(), terse))
    with pytest.raises(ValueError, match="plan is not valid"):
        tr.render_trace(s11(), terse, 0)


def test_a_plan_with_an_unknown_or_duplicate_node_is_rejected():
    bad = tr.Plan(BRAKING.approach, (tr.Step("zzz", "A law with a long enough name here", "A reason that is long enough to count here."), *BRAKING.steps), BRAKING.check)
    assert any("not computed nodes" in p for p in tr.validate_plan(s11(), bad))
    dup = tr.Plan(BRAKING.approach, (*BRAKING.steps, *BRAKING.steps), BRAKING.check)
    assert any("more than one step" in p for p in tr.validate_plan(s11(), dup))


def test_substitution_does_not_replace_inside_function_names_or_longer_names():
    structure = next(s for s in library_c.all_structures() if s.structure_id == "S26")  # asin(n1*sin(theta1)/n2)
    plan = tr.Plan("Use Snell's law to relate the angles in the two media and solve for the refraction angle.",
                   (tr.Step("theta2", "Snell's law of refraction n1 sin(theta1) = n2 sin(theta2)", "The tangential wave-vector component is conserved across the interface."),),
                   "The ray bends toward the normal when entering the denser medium, so theta2 < theta1.")
    step = next(s for s in tr.render_trace(structure, plan, 0)["steps"] if s["kind"] == "derive")
    assert "asin(" in step["substitution"] and "sin((" in step["substitution"] and "theta" not in step["substitution"].split("=", 1)[1]


def test_the_new_units_are_dimensionally_consistent():
    assert dm.convert(1.0, "eV", "J") == pytest.approx(1.602176634e-19)
    assert dm.unit("T").dim == dm.unit("N").dim / (dm.unit("A").dim * dm.unit("m").dim)
    assert dm.unit("Wb").dim == dm.unit("T").dim * dm.unit("m^2").dim
    assert dm.unit("V/m").dim == dm.unit("N/C").dim
    assert dm.unit("eV*nm").dim == dm.unit("J").dim * dm.unit("m").dim
    assert dm.convert(500.0, "nm", "m") == pytest.approx(5e-7)
    with pytest.raises(dm.DimensionError):
        dm.convert(1.0, "T", "V/m")
