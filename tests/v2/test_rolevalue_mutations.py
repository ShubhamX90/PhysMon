"""G1 mutation tests for the role-by-value generator: each test takes a certified M0 spec, breaks one property on purpose,
and requires the certificate to fail (plan of record G1: "the role-by-value generator ... with mutation tests"). A mutation
that still certifies is a hole in the certificate."""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import roles_m0  # noqa: E402

P = rv.Phrasing


def cert(sid: str, spec: rv.RoleSpec) -> dict:
    return rv.certify_role_spec(roles_m0.structure(sid), spec)


@pytest.mark.parametrize("sid", sorted(roles_m0.ROLE_SPECS))
def test_every_unmutated_m0_spec_certifies(sid):
    c = cert(sid, roles_m0.ROLE_SPECS[sid])
    assert c["passed"] and not c["strata_failed"], (c["failed"], c["strata_failed"])


# --- primary R/D contrast ---------------------------------------------------------------------------------------------------

def test_wiring_onto_an_input_of_another_dimension_fails():
    spec = roles_m0.ROLE_SPECS["S01"]
    bad = dataclasses.replace(spec, relevant=rv.RelevantWiring("g", "add", "x"))  # a mass added to g
    assert "wiring_dimension" in cert("S01", bad)["failed"]


def test_wiring_onto_a_computed_node_fails():
    spec = roles_m0.ROLE_SPECS["S01"]
    bad = dataclasses.replace(spec, relevant=rv.RelevantWiring("m_eff", "add", "x"))
    assert "wiring_dimension" in cert("S01", bad)["failed"]


def test_values_too_small_to_move_the_answer_fail():
    spec = roles_m0.ROLE_SPECS["S30"]
    bad = dataclasses.replace(spec, values=(0.001, 0.002, 0.003))
    assert "r_separated_from_d" in cert("S30", bad)["failed"]


def test_repeated_values_fail():
    spec = roles_m0.ROLE_SPECS["S07"]
    bad = dataclasses.replace(spec, values=(2.0, 2.0, 5.0))
    assert "r_values_distinct" in cert("S07", bad)["failed"]


def test_only_marked_irrelevant_phrasings_fail():
    spec = roles_m0.ROLE_SPECS["S13"]
    bad = dataclasses.replace(spec, phrasings_d=(P("d0", "in a separate room"), P("d1", "unrelated to the pendulum")))
    assert "marker_free_d" in cert("S13", bad)["failed"]


def test_a_single_phrasing_per_role_fails():
    spec = roles_m0.ROLE_SPECS["S15"]
    bad = dataclasses.replace(spec, phrasings_r=spec.phrasings_r[:1])
    assert "phrasings_r_at_least_2" in cert("S15", bad)["failed"]


def test_a_frame_without_the_relation_slot_fails():
    spec = roles_m0.ROLE_SPECS["S01"]
    bad = dataclasses.replace(spec, frame="A {value} {unit} block is nearby.")
    assert "frame_slots" in cert("S01", bad)["failed"]


def test_a_wrong_independent_solver_fails():
    structure = roles_m0.structure("S01")
    broken = dataclasses.replace(structure, solver=lambda *xs: 1.01 * structure.solver(*xs))
    assert "routes_agree" in rv.certify_role_spec(broken, roles_m0.ROLE_SPECS["S01"])["failed"]


# --- cancelling stratum C ---------------------------------------------------------------------------------------------------

def _with_c(sid: str, **changes) -> dict:
    spec = roles_m0.ROLE_SPECS[sid]
    return cert(sid, dataclasses.replace(spec, cancelling=dataclasses.replace(spec.cancelling, **changes)))["checks"]["cancelling"]


def test_c_quantity_that_does_not_cancel_fails():
    c = _with_c("S01", expr_with_q="(m2 - m1)*g/(m1 + m2 + M/2 + q)")  # also dimensionally wrong: either check must fail
    assert not c["passed"]


def test_c_expression_that_differs_from_the_graph_fails():
    c = _with_c("S13", expr_with_q="2*pi*sqrt(2*L/g)*q/q")
    assert not c["passed"] and not c["matches_graph_target"]


def test_c_wrong_law_dimension_is_recorded_not_blocking():
    # a misuse may be dimensionally wrong (forgetting 1/r^2 gives kg + kg m^2): recorded on the certificate, not blocking
    c = _with_c("S01", wrong_law="(m2 - m1)*g/(m1 + m2 + M*q**2/2)")
    assert c["wrong_law_consistent"] is False and c["wrong_law_has_target_dimension"] is False and c["passed"]
    c = _with_c("S01", wrong_law="(m2 - m1)*g/(m1 + m2 + M/2)/q")  # the angular acceleration a / r
    assert c["wrong_law_consistent"] is True and c["wrong_law_has_target_dimension"] is False and c["passed"]


def test_c_expression_with_the_wrong_dimension_fails():
    c = _with_c("S30", expr_with_q="m*c*((q+dT)-q)/P*q/q*c")  # numerically different and dimensionally wrong
    assert not c["passed"] and c["expr_dimension_ok"] is False


def test_c_wrong_law_equal_to_the_gold_fails():
    c = _with_c("S30", wrong_law="m*c*((q+dT)-q)/P")
    assert not c["passed"]


def test_c_frame_without_slots_fails():
    c = _with_c("S55", frame="The gas sample is large.")
    assert not c["passed"] and c.get("frame_ok") is False


# --- conditional stratum K --------------------------------------------------------------------------------------------------

def _with_k(sid: str, **changes) -> dict:
    spec = roles_m0.ROLE_SPECS[sid]
    return cert(sid, dataclasses.replace(spec, conditional=dataclasses.replace(spec.conditional, **changes)))["checks"][
        "conditional"]


def test_k_value_outside_the_regime_fails():
    c = _with_k("S92", values=(1.0, 50.0, 80.0))  # a 1 N string would break
    assert not c["passed"] and not c["predicate_holds_at_all_values"]


def test_k_counter_value_inside_the_regime_fails():
    c = _with_k("S15", counter_regime_value=50.0)
    assert not c["passed"] and not c["counter_regime_value_breaks_predicate"]


def test_k_dimensionally_invalid_out_of_regime_law_fails():
    c = _with_k("S01", out_of_regime_law="g + q")  # m/s^2 + N
    assert not c["passed"] and c.get("out_of_regime_dimension_ok") is False


def test_k_dimensionally_invalid_predicate_fails():
    c = _with_k("S01", predicate="m1 < q")  # kg compared with N
    assert not c["passed"] and c.get("predicate_dimension_ok") is False


# --- rendering ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", sorted(roles_m0.ROLE_SPECS))
def test_rendered_cells_are_minimal_pairs_and_numerals_appear(sid):
    structure, spec = roles_m0.structure(sid), roles_m0.ROLE_SPECS[sid]
    cells = rv.role_cells(structure, spec, 0, positions=("after_context", "before_context"))
    assert all(rv.prompt_value_check(c) for c in cells)
    by = {c.cell_id: c for c in cells}
    for c in cells:
        if c.stratum != "R":
            continue
        twin = by[c.cell_id.replace("R:", "D:").replace(f":{c.phrasing_id}:", f":{spec.phrasings_d[0].phrasing_id}:")]
        r_rel = next(p.relation for p in spec.phrasings_r if p.phrasing_id == c.phrasing_id)
        assert c.prompt.replace(r_rel, "\x00") == twin.prompt.replace(spec.phrasings_d[0].relation, "\x00")
    for stratum, sub in (("C", spec.cancelling), ("K", spec.conditional)):
        if sub is not None:
            text = rv._sentence(sub.frame, None, None, sub.phrasings[0].relation, sub.nonnumeric_fill)
            assert "{" not in text and "}" not in text  # the non-numeric fill renders cleanly


@pytest.mark.parametrize("sid", sorted(roles_m0.ROLE_SPECS))
def test_every_cell_has_exactly_one_copy_foil_matching_its_rendered_numeral(sid):
    # G1 decision 26: `copy` when q has the target's dimension, else `digit_copy` (the numeral as typed, read in the
    # target display unit); a digit copy that coincides with the gold is recorded as confounded, never silently matched
    from physmon.benchmark.v2 import dimensions as dm

    structure, spec = roles_m0.structure(sid), roles_m0.ROLE_SPECS[sid]
    target_dim = dm.UNITS[structure.render.target_unit].dim
    for c in rv.role_cells(structure, spec, 0):
        if c.stratum in ("none", "N"):
            continue
        same = dm.UNITS[c.unit].dim == target_dim
        assert ("copy" in c.foils) == same and ("digit_copy" in c.foils) == (not same), c.cell_id
        if not same:
            numeral = rv._fmt(c.value)
            assert c.foils["digit_copy"] == float(numeral) and numeral in c.prompt
            gold_close = abs(c.foils["digit_copy"] - c.gold_value) <= rv.LOOSEST_REL_TOL * max(
                abs(c.foils["digit_copy"]), abs(c.gold_value))
            assert gold_close == ("digit_copy~gold" in c.confounded), c.cell_id

