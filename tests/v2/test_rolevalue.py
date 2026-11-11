"""Tests for the role-by-value generator (Stage 15) on structure S01 (Atwood machine with a massive disc pulley)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import library as lib  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402


def s01_spec(**overrides) -> rv.RoleSpec:
    base = dict(
        structure_id="S01", quantity_phrase="a small block", quantity_type="mass", unit="kg", values=(0.4, 0.8, 1.2),
        heldout_values=(0.6, 1.0),
        frame="A {value} {unit} block is {relation}.",
        relevant=rv.RelevantWiring("m1", "add", "a block tied beneath the left block moves with it, adding to its mass"),
        phrasings_r=(rv.Phrasing("r0", "tied firmly beneath the left block"),
                     rv.Phrasing("r1", "glued to the bottom of the left block so that it moves with it")),
        phrasings_d=(rv.Phrasing("d0", "resting on a shelf beside the apparatus"),
                     rv.Phrasing("d1", "sitting in a drawer in another room, unrelated to the setup")),
        nonnumeric_fill="small",
        cancelling=rv.CancellingSpec(
            "the pulley radius", "length", "cm", (8.0, 12.0, 16.0), "The pulley {relation} {value} {unit}.",
            (rv.Phrasing("c0", "has a radius of"), rv.Phrasing("c1", "measures, from its axle to its rim,")),
            "(m2 - m1)*g/(m1 + m2 + (M*q**2/2)/q**2)", ("I = M r^2 / 2", "a = (m2 - m1) g / (m1 + m2 + I / r^2)"),
            "(m2 - m1)*g/(m1 + m2 + M*q**2/2)"),
        conditional=rv.ConditionalSpec(
            "the string's breaking strength", "force", "N", (120.0, 200.0, 300.0), "The string {relation} {value} {unit}.",
            (rv.Phrasing("k0", "can withstand a tension of up to"), rv.Phrasing("k1", "is rated to break only above")),
            "Max(m1*(g + a), m2*(g - a)) < q", "g", 20.0),
    )
    base.update(overrides)
    return rv.RoleSpec(**base)


@pytest.fixture(scope="module")
def s01():
    return lib.s01_atwood_massive_pulley()


def test_certificate_passes_for_a_well_formed_spec(s01):
    cert = rv.certify_role_spec(s01, s01_spec())
    assert cert["passed"], cert["failed"]
    assert cert["checks"]["cancelling"]["passed"] and cert["checks"]["conditional"]["passed"]
    assert rv.complete(s01_spec(), cert)


def test_relevant_answer_matches_hand_computation_through_both_routes(s01):
    si = rv.display_inputs_si(s01, 0)  # m1=3, m2=5, M=2, g=9.8
    graph, solver = rv.gold_r(s01, si, s01_spec(), 0.8)
    expected = (5 - 3.8) * 9.8 / (3.8 + 5 + 1)
    assert graph == pytest.approx(expected) and solver == pytest.approx(expected)


def test_cells_are_minimal_pairs_with_foils_neglect_and_placebo(s01):
    cells = rv.role_cells(s01, s01_spec(), 0)
    by_id = {c.cell_id: c for c in cells}
    r = by_id["R:z1:r0:after_context"]
    d = by_id["D:z1:d0:after_context"]
    y_d = 2 * 9.8 / 9  # m_eff = m1 + m2 + M/2 = 9 kg
    assert d.gold_value == pytest.approx(y_d) and r.gold_value == pytest.approx(1.2 * 9.8 / 9.8)
    assert d.foils["relevant_twin"] == pytest.approx(r.gold_value) and r.foils["neglect"] == pytest.approx(y_d)
    assert r.placebo == pytest.approx(2 * r.gold_value - y_d)
    assert "add:m1" in d.foils and "replace:M" in d.foils and "copy" not in d.foils  # mass is not an acceleration
    # minimal pair: identical prompts apart from the relational phrase
    assert r.prompt.replace("tied firmly beneath the left block", "X") == d.prompt.replace(
        "resting on a shelf beside the apparatus", "X")
    assert all(rv.prompt_value_check(c) for c in cells)
    strata = {c.stratum for c in cells}
    assert strata == {"none", "N", "R", "D", "C", "K"}
    n = by_id["N:after_context"]
    assert "A small block is resting on a shelf beside the apparatus." in n.prompt and n.gold_value == pytest.approx(y_d)
    assert "A 0.8 kg block is tied firmly beneath the left block." in r.prompt
    c = next(c for c in cells if c.stratum == "C")
    assert c.gold_value == pytest.approx(y_d) and "wrong_law" in c.foils
    k = next(c for c in cells if c.stratum == "K")
    assert k.foils["out_of_regime"] == pytest.approx(9.8)


def test_marker_words_are_detected():
    assert not rv.Phrasing("x", "sitting in a drawer in another room, unrelated to the setup").marker_free
    assert rv.Phrasing("x", "resting on a shelf beside the apparatus").marker_free


def test_certificate_fails_for_bad_specs(s01):
    too_few = rv.certify_role_spec(s01, s01_spec(values=(0.4, 0.8)))
    assert not too_few["passed"] and "values_at_least_3" in too_few["failed"]
    markers_only = s01_spec(phrasings_d=(rv.Phrasing("d0", "in a separate room"), rv.Phrasing("d1", "unrelated to it")))
    assert "marker_free_d" in rv.certify_role_spec(s01, markers_only)["failed"]
    wrong_dim = s01_spec(unit="m", quantity_type="length")
    assert "wiring_dimension" in rv.certify_role_spec(s01, wrong_dim)["failed"]
    tiny = s01_spec(values=(0.001, 0.002, 0.003))
    assert "r_separated_from_d" in rv.certify_role_spec(s01, tiny)["failed"]
    no_cancel = s01_spec(cancelling=rv.CancellingSpec(
        "x", "length", "cm", (8.0, 12.0, 16.0), "The pulley {relation} {value} {unit}.",
        (rv.Phrasing("c0", "has a radius of"), rv.Phrasing("c1", "is")), "(m2 - m1)*g/(m1 + m2 + q)", ("r",), "g"))
    assert not rv.certify_role_spec(s01, no_cancel)["checks"]["cancelling"]["passed"]
    bad_regime = s01_spec(conditional=rv.ConditionalSpec(
        "x", "force", "N", (5.0, 200.0, 300.0), "The string {relation} {value} {unit}.",
        (rv.Phrasing("k0", "breaks above"), rv.Phrasing("k1", "is rated at")), "Max(m1*(g + a), m2*(g - a)) < q", "g", 20.0))
    assert not rv.certify_role_spec(s01, bad_regime)["checks"]["conditional"]["passed"]


def test_placebo_switches_to_multiplicative_when_additive_changes_sign():
    value, kind = rv.placebo_value(1.0, 3.0, sign_definite=True)
    assert kind == "multiplicative" and value == pytest.approx(1 / 3)
    value, kind = rv.placebo_value(3.0, 1.0, sign_definite=True)
    assert kind == "additive" and value == pytest.approx(5.0)
