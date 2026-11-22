"""Tests for the M250 phase 3 batch acwaves (S321 to S330: acoustics and mechanical waves).

(a) every structure is solver-certified, has a valid gold plan and at least four instances; every role spec passes the v2.1 certificate;
(b) the base gold of every instance and every R gold at every study and held-out value equal closed forms written in this file (not
through the graph); (c) every C quantity leaves the answer invariant (through its own physical route) and every K regime holds at every
value of every instance, with the regime-ignoring answer from a closed form written here, and the physics of the K claims is checked
independently (a microphone inside the circle, shallow water, a partly immersed cube); (d) the v2.1 wording rules, the rules of the
panel reviews and the N grammar of `test_m250_n_fill_grammar.py`; (e) the scene clause leaves the base problem and its gold
unchanged; (f) the symbolic program of every structure is new against dataset v1 and every library module; plus mutation tests."""

from __future__ import annotations

import cmath
import dataclasses
import importlib
import inspect
import json
import math
import re
from pathlib import Path

import numpy as np
import pytest

from physmon.benchmark.v2 import certify as ct
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import lib_m250p3_acwaves as lw
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250p3_acwaves as m
from physmon.benchmark.v2 import trace as tr
from physmon.benchmark.v2.graph import Structure

REPO_ROOT = Path(__file__).resolve().parents[2]
V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SPECS = m.SPECS
SIDS = sorted(SPECS)  # S329 is recorded infeasible (no natural R quantity); its structure stays certified below
G = 9.8
FIRST_PERSON = ("second", "another", "identical", "same type", "other")


def spec_cert(sid: str, spec: r2.RoleSpecV2) -> dict:
    return r2.certify_v2(m.structure(sid), spec)


def with_pair(spec: r2.RoleSpecV2, index: int, **changes) -> r2.RoleSpecV2:
    pairs = list(spec.pairs)
    pairs[index] = dataclasses.replace(pairs[index], **changes)
    return dataclasses.replace(spec, pairs=tuple(pairs))


@pytest.fixture(scope="module")
def certs():
    return {sid: spec_cert(sid, SPECS[sid]) for sid in SIDS}


@pytest.fixture(scope="module")
def cells():
    return {sid: r2.role_cells_v2(m.structure(sid), SPECS[sid], 0, include_heldout=True) for sid in SIDS}


# --- independent closed forms (display units in, display units out) -----------------------------------------------------------------


def _s321(i, rot_add=0.0):
    v = 2 * math.pi * (i["rot"] + rot_add) / 60 * i["r"]
    return i["f"] * i["c"] / (i["c"] - v) - i["f"] * i["c"] / (i["c"] + v)


def _s322(i, vs_add=0.0):  # in the frame of the air the observer recedes from the crests at u_o and the source follows at u_s
    ua, ub = i["vs"] + vs_add - i["w"], i["vo"] - i["w"]
    return i["f"] * (i["c"] - ub) / (i["c"] - ua) - i["f"]


def _s323(i, m_add=0.0):  # t = 2 (sqrt(a + L) - sqrt(a)) / sqrt(g) with a the length of rope that weighs as much as the block
    a = (i["M"] + m_add) * i["L"] / i["mr"]
    return 2 * (math.sqrt(a + i["L"]) - math.sqrt(a)) / math.sqrt(i["g"])


def _s324(i, m_add_g=0.0, x_m=None):  # mW: the complex amplitude of the transmitted wave at the knot (and at a distance x along)
    z1 = math.sqrt(i["T"] * i["rho"] * math.pi * (i["d1"] * 1e-3) ** 2 / 4)
    z2 = math.sqrt(i["T"] * i["rho"] * math.pi * (i["d2"] * 1e-3) ** 2 / 4)
    w = 2 * math.pi * i["f"]
    amplitude = 2 * z1 / (z1 + z2 + 1j * (i["m"] + m_add_g) * 1e-3 * w)
    if x_m is not None:
        amplitude *= cmath.exp(-1j * w * math.sqrt(i["rho"] * math.pi * (i["d2"] * 1e-3) ** 2 / 4 / i["T"]) * x_m)
    return i["P0"] * z2 / z1 * abs(amplitude) ** 2


def _s325(i, d_add=0.0):
    d = i["d"] + d_add
    return d / i["c"] - d / math.sqrt(i["E"] * 1e6 / i["rho"])


def _s326(i, r2_add=0.0):
    return i["eta"] * (i["p1"] / (2 * math.pi * i["r1"] ** 2) + i["p2"] / (2 * math.pi * (i["r2"] + r2_add) ** 2))


def _s327(i, d_add=0.0):  # hours: group speed of deep-water gravity waves is half the phase speed sqrt(g lambda / 2 pi)
    return (i["D"] + d_add) * 1e3 / (0.5 * math.sqrt(i["g"] * i["lam"] / (2 * math.pi))) / 3600


def _s328(i, rw_add=0.0):
    vol = (i["a"] * 1e-2) ** 3
    weight = i["rb"] * vol * i["g"]
    tension_water = weight - (i["rw"] + rw_add) * vol * i["g"]
    mass_length = i["ms"] * 1e-3 * i["L"]
    return math.sqrt(weight / mass_length) / 2 - math.sqrt(tension_water / mass_length) / 2


def _s329(i, f_add=0.0):
    speed = (i["f"] + f_add) * 2 * (i["L2"] - i["L1"]) * 1e-2
    return i["T0"] * (speed / i["c0"]) ** 2


def _s330(i, s_add_km=0.0):
    mach = i["v"] / i["c"]
    return ((i["s"] + s_add_km) * 1e3 + i["h"] * 1e3 * math.sqrt(mach ** 2 - 1)) / i["v"]


ANS = {"S321": _s321, "S322": _s322, "S323": _s323, "S324": _s324, "S325": _s325, "S326": _s326, "S327": _s327, "S328": _s328,
       "S329": _s329, "S330": _s330}
# the answer with q in the R role (display unit of q) on instance dict i
R_FORMS = {
    "S321": lambda i, q: _s321(i, rot_add=q), "S322": lambda i, q: _s322(i, vs_add=q), "S323": lambda i, q: _s323(i, m_add=q),
    "S324": lambda i, q: _s324(i, m_add_g=q), "S325": lambda i, q: _s325(i, d_add=q), "S326": lambda i, q: _s326(i, r2_add=q),
    "S327": lambda i, q: _s327(i, d_add=q), "S328": lambda i, q: _s328(i, rw_add=q), "S329": lambda i, q: _s329(i, f_add=q),
    "S330": lambda i, q: _s330(i, s_add_km=q),
}
BASE_GOLD0 = {"S321": 141.16981215437204, "S322": 25.644171779141118, "S323": 0.8251107589143069, "S324": 16.125671471596995,
              "S325": 1.63078063107745, "S326": 0.005506761030979579, "S327": 65.37794520455492, "S328": 3.307243198629294,
              "S329": 292.85177484593834, "S330": 25.361913543711765}


def inst0(sid):
    return dict(lw.STRUCTURES[sid].instances[0])


def base_answer(sid):
    return ANS[sid](inst0(sid))


# --- (a) certification ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_structure_is_certified_with_a_valid_plan_and_enough_instances(sid):
    s = lw.STRUCTURES[sid]
    proof = ct.certify(s)
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]
    assert tr.validate_plan(s, lw.PLANS[sid]) == []
    assert len(s.instances) >= 4 and sid in lw.LEVELS and sid in lw.TOPICS
    for index in range(len(s.instances)):  # the trace renders for every instance and ends at the gold
        trace = tr.render_trace(s, lw.PLANS[sid], index)
        assert trace["gold_answer"]["value"] == pytest.approx(dg.gold_for(s, dict(s.instances[index])), rel=1e-9)


@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(SPECS[sid], cert)
    spec = SPECS[sid]
    assert spec.version == "v2.1" and spec.structure_id == sid and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE
    assert m.CERT_VERSION == "v2.1"


def test_the_batch_is_the_ten_assigned_structures_and_meets_the_composition_targets(certs):
    assert SIDS == [f"S{n}" for n in (*range(321, 329), 330)]
    assert sorted(lw.STRUCTURES) == [f"S{n}" for n in range(321, 331)] and set(m.INFEASIBLE) == {"S329"}
    assert set(m.STRUCTURE_FACTORIES) == set(lw.STRUCTURES) == set(lw.LEVELS) == set(lw.PLANS) == set(lw.TOPICS)
    assert set(SIDS) == set(m.TARGET_TERMS) and len(m.INFEASIBLE["S329"]) >= r2.MIN_RATIONALE
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
        assert (SPECS[sid].conditional is not None) == (sid in m.K_KINDS)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert len(famous) <= 3 and (len(c), len(k)) == (5, 3)
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values
        assert len(m.K_KINDS[sid]) >= 20
    upper = [s for s in SIDS if lw.LEVELS[s] == "upper_university"]
    multi = [s for s in SIDS if len(lw.STRUCTURES[s].computed) >= 3]
    assert len(upper) >= 4 and len(multi) >= 4 and set(lw.LEVELS.values()) <= {"intro_university", "upper_university", "high_school"}
    assert len({lw.STRUCTURES[s].solver_route for s in SIDS}) == 9


# --- (b) independent closed forms ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_the_closed_form_reproduces_every_instance_gold(sid):
    s = lw.STRUCTURES[sid]
    for instance in s.instances:
        assert ANS[sid](dict(instance)) == pytest.approx(dg.gold_for(s, dict(instance)), rel=1e-6)
    assert base_answer(sid) == pytest.approx(BASE_GOLD0[sid], rel=1e-6)


def test_the_infeasible_s329_structure_is_still_certified_with_a_plan():
    s = lw.STRUCTURES["S329"]
    assert ct.certify(s)["status"] == "SOLVER_CERTIFIED" and tr.validate_plan(s, lw.PLANS["S329"]) == []
    i = dict(s.instances[0])
    assert i["T0"] * (i["f"] * 2 * (i["L2"] - i["L1"]) * 1e-2 / i["c0"]) ** 2 == pytest.approx(dg.gold_for(s, i), rel=1e-6)


def test_the_s324_amplitudes_agree_with_a_transfer_through_a_short_heavy_section():
    # a third route for the junction: the bead replaced by a very short uniform section of the same mass, whose transmission is the
    # standard slab formula with the section's own impedance and phase; it tends to the point-mass answer as the section shortens
    i = inst0("S324")
    z1 = math.sqrt(i["T"] * i["rho"] * math.pi * (i["d1"] * 1e-3) ** 2 / 4)
    z2 = math.sqrt(i["T"] * i["rho"] * math.pi * (i["d2"] * 1e-3) ** 2 / 4)
    w, mass, length = 2 * math.pi * i["f"], i["m"] * 1e-3, 1e-9
    zk, kl = math.sqrt(i["T"] * mass / length), w * math.sqrt(mass * length / i["T"])
    fraction = 4 * z1 * z2 / ((z1 + z2) ** 2 * math.cos(kl) ** 2 + (zk + z1 * z2 / zk) ** 2 * math.sin(kl) ** 2)
    assert i["P0"] * fraction == pytest.approx(base_answer("S324"), rel=1e-6)


def test_the_s330_boom_geometry_agrees_with_the_mach_cone_angle():
    i = inst0("S330")
    mu = math.asin(i["c"] / i["v"])
    assert (i["s"] * 1e3 + i["h"] * 1e3 / math.tan(mu)) / i["v"] == pytest.approx(base_answer("S330"), rel=1e-9)


@pytest.mark.parametrize("sid", SIDS)
def test_every_r_gold_at_every_value_equals_the_closed_form_and_every_other_gold_the_base(sid, cells):
    spec, form = SPECS[sid], R_FORMS[sid]
    seen_r = set()
    for cell in cells[sid]:
        if cell.stratum == "R":
            assert cell.gold_value == pytest.approx(form(inst0(sid), cell.value), rel=1e-6), cell.cell_id
            seen_r.add(cell.value)
        else:
            assert cell.stratum in ("none", "N", "D", "C", "K"), cell.cell_id
            assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-6), cell.cell_id
    assert seen_r == {*spec.values, *spec.heldout_values}
    golds = [form(inst0(sid), v) for v in spec.values]
    assert all(abs(g - base_answer(sid)) > rv.LOOSEST_REL_TOL * max(g, base_answer(sid)) for g in golds)
    assert len({round(g, 6) for g in golds}) == 3
    for instance in lw.STRUCTURES[sid].instances:  # the response holds on every instance, not only the emitted one
        base = ANS[sid](dict(instance))
        assert all(abs(form(dict(instance), v) - base) > rv.LOOSEST_REL_TOL * max(abs(base), 1e-12) for v in spec.values)


@pytest.mark.parametrize("sid", SIDS)
def test_the_four_r_and_d_cells_per_value_exist_in_both_pairs_and_n_has_no_numeral(sid, cells):
    spec = SPECS[sid]
    r_cells = [c for c in cells[sid] if c.stratum == "R"]
    d_cells = [c for c in cells[sid] if c.stratum == "D"]
    assert len(r_cells) == len(d_cells) == 2 * (len(spec.values) + len(spec.heldout_values))
    assert {c.pair_id for c in r_cells} == {"p0", "p1"} == {c.pair_id for c in d_cells}
    n_cells = [c for c in cells[sid] if c.stratum == "N"]
    assert len(n_cells) == 2 and all(not any(ch.isdigit() for ch in c.sentence) and c.value is None for c in n_cells)
    assert [c.d_kind for c in n_cells] == [p.d_kind for p in spec.pairs]


# --- (c) invariance of C and the regime of K -----------------------------------------------------------------------------------------


def _c322(i, q_m):  # crest n leaves the car at n / f and meets the cyclist q ahead; the heard frequency is 1 / (T5 - T4)
    def arrival(n):
        return (q_m + (i["c"] + i["w"] - i["vs"]) * n / i["f"]) / (i["c"] + i["w"] - i["vo"])

    return 1 / (arrival(5) - arrival(4)) - i["f"]


def _c324(i, q):
    return _s324(i, x_m=q)  # the power of the travelling wave read at q along the thick string


def _c325(i, area_cm2):  # stiffness E A / l and mass rho A l of a piece of length l
    a, length = area_cm2 * 1e-4, 0.37
    speed = length * math.sqrt((i["E"] * 1e6 * a / length) / (i["rho"] * a * length))
    return i["d"] / i["c"] - i["d"] / speed


def _c326(i, area_cm2):  # the power received by the diaphragm divided by its area
    a = area_cm2 * 1e-4
    return (_s326(i) * a) / a


def _c327(i, density):  # omega^2 = (restoring force per area rho g) / (inertia per area rho / k)
    k = 2 * math.pi / i["lam"]
    omega = math.sqrt(density * i["g"] / (density / k))
    return i["D"] * 1e3 / (omega / (2 * k)) / 3600


def _c329(i, diameter_cm):  # end correction 0.3 d: the two resonances are L1 + e = lambda / 4 and L2 + e = 3 lambda / 4
    e = 0.3 * diameter_cm
    lam = 2 * ((i["L2"] + e) - (i["L1"] + e)) * 1e-2
    return i["T0"] * (i["f"] * lam / i["c0"]) ** 2


C_ROUTES = {"S322": _c322, "S324": _c324, "S325": _c325, "S326": _c326, "S327": _c327}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value_on_every_instance(sid, cells):
    spec = SPECS[sid].cancelling
    for instance in lw.STRUCTURES[sid].instances:
        for q in (*spec.spec.values, *spec.heldout_values):
            assert C_ROUTES[sid](dict(instance), q) == pytest.approx(ANS[sid](dict(instance)), rel=1e-6), (instance, q)
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-6)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


def _s321_k(i, q):
    return q > i["r"]


def _s327_k(i, q):
    return q > i["lam"] / 2


def _s328_k(i, q):
    return q > i["a"]


K_REGIME = {"S321": _s321_k, "S327": _s327_k, "S328": _s328_k}


def _k_alt(sid: str, q: float) -> float:  # the answer that the law of the other regime would give, instance 0
    i = inst0(sid)
    if sid == "S321":
        v = 2 * math.pi * i["rot"] / 60 * i["r"]
        return i["f"] * i["c"] / (i["c"] - v * q / i["r"]) - i["f"] * i["c"] / (i["c"] + v * q / i["r"])
    if sid == "S327":  # shallow water: group speed sqrt(g h)
        return i["D"] * 1e3 / math.sqrt(G * q) / 3600
    vol_edge = i["a"] * 1e-2
    weight = i["rb"] * vol_edge ** 3 * i["g"]
    partly = weight - i["rw"] * vol_edge ** 2 * (q * 1e-2) * i["g"]  # only the part of the cube below the water surface is immersed
    mass_length = i["ms"] * 1e-3 * i["L"]
    return math.sqrt(weight / mass_length) / 2 - math.sqrt(partly / mass_length) / 2


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_REGIME) == {s for s in SIDS if SPECS[s].conditional is not None}


@pytest.mark.parametrize("sid", sorted(K_REGIME))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    instances = [dict(i) for i in lw.STRUCTURES[sid].instances]
    assert len(instances) == 4
    for q in (*spec.spec.values, *spec.heldout_values):
        assert all(K_REGIME[sid](i, q) for i in instances), q
    assert not any(K_REGIME[sid](i, spec.spec.counter_regime_value) for i in instances)
    k_cells = [c for c in cells[sid] if c.stratum == "K"]
    assert len(k_cells) == 2 * len(spec.spec.values)
    for cell in k_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-6)  # inside the regime the answer is the base answer
        assert cell.foils["out_of_regime"] == pytest.approx(_k_alt(sid, cell.value), rel=1e-6), cell.cell_id
        assert abs(cell.foils["out_of_regime"] - cell.gold_value) > rv.LOOSEST_REL_TOL * abs(cell.gold_value)
    assert not [c for c in cells[sid] if c.stratum == "K_out"] and len(spec.k_out.reason) >= r2.MIN_RATIONALE
    assert m.K_KINDS[sid]


def _heard_extremes(f, r, rot, c, dist):  # highest minus lowest frequency by scanning the arrival-time derivative, microphone at dist
    def heard(phi):
        h = 1e-6

        def arrival(a):
            return a / rot + math.hypot(dist - r * math.cos(a), r * math.sin(a)) / c

        return f / ((arrival(phi + h) - arrival(phi - h)) / (2 * h / rot))

    values = [heard(p) for p in np.linspace(0, 2 * math.pi, 4001)]
    return max(values) - min(values)


def test_k_claim_s321_a_microphone_inside_the_circle_hears_the_component_v_q_over_r():
    i = inst0("S321")
    rot = 2 * math.pi * i["rot"] / 60
    for q in (0.3, 0.5):  # inside the circle of radius 0.8 m
        assert _heard_extremes(i["f"], i["r"], rot, i["c"], q) == pytest.approx(_k_alt("S321", q), rel=2e-5)
    assert _heard_extremes(i["f"], i["r"], rot, i["c"], 4.1) == pytest.approx(base_answer("S321"), rel=2e-5)  # outside: the stated law


def test_k_claim_s327_the_finite_depth_group_speed_tends_to_the_deep_and_the_shallow_laws():
    def group_speed(lam, depth):
        k = 2 * math.pi / lam
        omega = lambda kk: math.sqrt(G * kk * math.tanh(kk * depth))  # noqa: E731
        dk = k * 1e-6
        return (omega(k + dk) - omega(k - dk)) / (2 * dk)

    i = inst0("S327")
    assert group_speed(i["lam"], 2800.0) == pytest.approx(0.5 * math.sqrt(G * i["lam"] / (2 * math.pi)), rel=1e-9)  # deep
    assert group_speed(i["lam"], 0.5) == pytest.approx(math.sqrt(G * 0.5), rel=1e-2)  # shallow: wavelength much greater than depth


# --- (d) wording, lexicons, pairs, hygiene and the rules of the panel reviews -------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_every_emitted_sentence_is_consequence_free_marker_free_and_reversal_free_where_it_must_be(sid, cells):
    spec = SPECS[sid]
    for cell in cells[sid]:
        if cell.stratum == "none":
            continue
        assert not r2.consequence_hits(cell.sentence), cell.sentence
        assert not r2.marker_hits(cell.sentence), cell.sentence
        assert cell.consequence_free is True and cell.marker_free is True
        if cell.stratum in ("D", "N"):
            assert not r2.reversal_hits(cell.sentence) and not r2.remoteness_hits(cell.sentence), cell.sentence
    assert not r2.marker_hits(spec.scene_clause) and not r2.consequence_hits(spec.scene_clause)
    assert spec.scene_clause.endswith(".") and not any(ch.isdigit() for ch in spec.scene_clause)


@pytest.mark.parametrize("sid", SIDS)
def test_pairs_follow_the_v21_rules(sid, certs):
    spec = SPECS[sid]
    assert [p.pair_id for p in spec.pairs] == ["p0", "p1"]
    assert spec.pairs[0].d_kind == "other_object_same_scene" and spec.pairs[1].d_kind == "same_object_other_event"
    for pair, rec in zip(spec.pairs, certs[sid]["pairs"], strict=True):
        assert pair.frame_matched and rec["same_frame_numeral_unit"]  # one frame, numeral and unit within each pair
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        d_sentence = r2.pair_sentence(pair, "D", spec.values[0], spec.unit)
        assert r_sentence.replace(pair.r_attach, "@") == d_sentence.replace(pair.d_attach, "@")  # attachment-only difference
        assert abs(len(r_sentence.split()) - len(d_sentence.split())) <= r2.MAX_WORD_DIFF
        assert r2.pair_sentence(pair, "D", None, spec.unit).count(pair.d_attach) == 1
        assert not any(ch.isdigit() for ch in pair.r_attach + pair.d_attach)
        assert len(pair.d_rationale) >= r2.MIN_RATIONALE and pair.conditions_preserved and rec["conditions_in_base_text"]
        assert not r2.reversal_hits(d_sentence) and not r2.remoteness_hits(d_sentence)
        if pair.pair_id == "p1":
            assert r2.prior_marker_hits(pair.d_attach)  # the same-object D is anchored in time away from the stated experiment
            assert not r2.prior_marker_hits(pair.r_attach)
        if pair.d_kind == "other_object_same_scene":
            assert not [t for t in spec.target_terms if t.lower() in pair.d_attach.lower()]
    assert spec.scene_refs and all(r in spec.scene_clause and r in certs[sid]["pairs"][0]["d_sentence"] for r in spec.scene_refs)


@pytest.mark.parametrize("sid", SIDS)
def test_rule_1_and_5_a_pair_one_r_names_the_moment_of_the_question_and_is_not_bare_history(sid):
    spec = SPECS[sid]
    pair = spec.pairs[1]
    r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
    assert re.match(r"before\b", pair.r_attach.lower()), pair.r_attach  # the change is tied to the moment the question asks about
    assert not re.search(r"\b(afterwards|just before that|later|earlier|previously)\b", r_sentence.lower())
    assert re.search(r"\bearlier\b", pair.d_attach)  # the D twin is anchored in an earlier experiment, run or forecast


@pytest.mark.parametrize("sid", SIDS)
def test_rule_2_no_r_sentence_contradicts_a_stated_base_condition(sid):
    spec = SPECS[sid]
    structure = m.structure(sid)
    base = dg.context_text(structure, dict(structure.instances[0]))
    for pair in spec.pairs:
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\b(?:was|were|is|are) set\b|\bafter the\b|\bonce the\b|\bwhen the\b", r_sentence.lower()), r_sentence
        assert r_sentence not in base
        assert "further" in r_sentence  # every R reads unambiguously as a further change of the stated value
    # a base condition that an R sentence changes is not worded as constant or fixed
    changed = {"S321": "constant", "S322": "constant", "S323": "constant", "S328": "constant", "S329": "constant"}
    if sid in changed:
        assert changed[sid] not in base.lower().replace("constant value", "").replace("stated constant", "")
    for pair in spec.pairs:
        for condition in pair.conditions_preserved:
            assert condition in base and not re.search(r"\bnot\b|\bno longer\b", pair.r_attach.lower())


@pytest.mark.parametrize("sid", SIDS)
def test_rule_3_and_4_the_co_present_object_is_of_another_type_and_the_action_is_an_ordinary_one(sid):
    spec = SPECS[sid]
    pair = spec.pairs[0]
    scene = spec.scene_clause.lower()
    assert not any(re.search(rf"\b{w}\b", scene) for w in FIRST_PERSON if w != "other"), scene
    for term in spec.target_terms:  # the co-present object is not named with the target's own noun
        noun = term.lower().replace("the ", "").replace("this ", "")
        assert noun not in pair.d_attach.lower(), (term, pair.d_attach)
    assert all(ref in pair.d_attach for ref in spec.scene_refs) or all(ref in pair.d_attach for ref in spec.scene_refs[:1])
    furniture = ("stool", "desk lamp", "chair", "table", "shelf", "cupboard", "drawer")
    assert not any(w in scene or w in pair.d_attach.lower() for w in furniture)
    assert not re.search(r"\b\d", pair.frame)


@pytest.mark.parametrize("sid", SIDS)
def test_value_hygiene_for_every_study_and_held_out_value(sid, cells):
    spec, structure = SPECS[sid], m.structure(sid)
    golds = sorted({round(c.gold_value, 12) for c in cells[sid] if not c.heldout})
    shown = r2.displayed_inputs(structure, 0)
    groups = {"R_D": (*spec.values, *spec.heldout_values)}
    if spec.cancelling:
        groups["C"] = (*spec.cancelling.spec.values, *spec.cancelling.heldout_values)
    if spec.conditional:
        groups["K"] = (*spec.conditional.spec.values, *spec.conditional.heldout_values)
    for name, values in groups.items():
        assert len(set(values)) == len(values), name
        for v in values:
            h = r2.value_hygiene(structure, 0, v, golds)
            assert h["ok"] and not h["equals_input"], (sid, name, h)
            assert all(not math.isclose(float(rv._fmt(v)), x, rel_tol=1e-9) for x in shown.values())
            assert h["digit_overlap_with_inputs"] <= r2.MAX_DIGIT_OVERLAP and h["digit_overlap_with_gold"] <= r2.MAX_DIGIT_OVERLAP


@pytest.mark.parametrize("sid", SIDS)
def test_target_naming_for_the_h4_extractor(sid):
    phrases, symbols = m.TARGET_TERMS[sid]
    structure = m.structure(sid)
    question = dg.question_text(structure, dict(structure.instances[0])).lower()
    assert any(p.lower() in question for p in phrases) and structure.target in symbols and len(set(symbols)) == len(symbols)


@pytest.mark.parametrize("sid", SIDS)
def test_every_answer_deciding_condition_is_stated_and_the_prompt_carries_only_graph_numerals(sid):
    s = lw.STRUCTURES[sid]
    for index in range(len(s.instances)):
        cell = dg.render_cell(s, index, "no_cue")
        assert dg.prompt_matches_graph(s, cell)
    text = dg.context_text(s, dict(s.instances[0])).lower()
    needles = {"S321": ("outside the circle", "air is still", "horizontal plane"),
               "S322": ("steady wind", "relative to the moving air", "stays behind the cyclist"),
               "S323": ("flexible, inextensible", "hangs at rest", "g ="),
               "S324": ("nothing returns", "point mass", "gravity is neglected", "stated density" if False else "same density"),
               "S325": ("still air", "thinner than the pulse", "speed of sound in the air as"),
               "S326": ("hard ground", "does not absorb", "different tones"),
               "S327": ("much deeper than the wavelength", "negligible", "group speed"),
               "S328": ("completely immersed", "buoyancy is neglected", "in its fundamental"),
               "S329": ("same at both resonances", "one temperature", "c₀"),
               "S330": ("still", "faster than sound", "every height")}[sid]
    assert all(n in text for n in needles)


# --- (e) the scene clause leaves the base problem and its gold unchanged ------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_is_the_only_change_to_the_base_problem_and_the_gold_is_unchanged(sid):
    structure, original = m.structure(sid), m.STRUCTURE_FACTORIES[sid]()
    scene = SPECS[sid].scene_clause
    prompt = rv._assemble(structure, 0, "", "after_context")
    assert prompt.replace(f" {scene}", "", 1) == rv._assemble(original, 0, "", "after_context")
    assert dg.context_text(structure, dict(structure.instances[0])).endswith(scene)
    assert dg.structure_hash(structure) == dg.structure_hash(original) and structure.nodes == original.nodes
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(BASE_GOLD0[sid], rel=1e-9)
    for instance in range(len(structure.instances)):
        display = dict(structure.instances[instance])
        assert dg.gold_for(structure, display) == pytest.approx(dg.gold_for(original, display), rel=1e-12)
    for cell in r2.role_cells_v2(structure, SPECS[sid], 0):
        assert scene in cell.prompt and r2._prompt_numerals_ok(structure, 0, cell.prompt, cell.value)


# --- (f) a new symbolic program --------------------------------------------------------------------------------------------------------


def _existing_hashes() -> dict[str, str]:
    found: dict[str, str] = {}
    for name in ("library", "library_b", "library_c", "lib_mechanics", "lib_electromagnetism", "lib_thermodynamics", "lib_optics",
                 "lib_quantum", "lib_modern", "lib_fluids"):
        module = importlib.import_module(f"physmon.benchmark.v2.{name}")
        for fname, factory in inspect.getmembers(module, inspect.isfunction):
            if re.fullmatch(r"s\d\d_.*|s\d\d\d_.*", fname):
                try:
                    structure = factory()
                except TypeError:
                    continue
                if isinstance(structure, Structure):
                    found[f"{name}:{structure.structure_id}"] = dg.structure_hash(structure)
    for path in sorted((REPO_ROOT / "src/physmon/benchmark/v2").glob("lib_m250*.py")):
        if path.stem == "lib_m250p3_acwaves":
            continue
        try:  # another agent's range may be mid-edit; a module that does not import cannot clash and is skipped
            module = importlib.import_module(f"physmon.benchmark.v2.{path.stem}")
        except Exception:  # noqa: BLE001
            continue
        for sid, structure in getattr(module, "STRUCTURES", {}).items():
            found[f"{path.stem}:{sid}"] = dg.structure_hash(structure)
    return found


def test_program_hashes_and_templates_differ_from_every_existing_structure():
    mine = {sid: dg.structure_hash(s) for sid, s in lw.STRUCTURES.items()}
    assert len(set(mine.values())) == len(mine)
    existing = _existing_hashes()
    assert len(existing) >= 90
    assert not set(mine.values()) & set(existing.values())
    v1 = [json.loads(line) for line in V1.read_text(encoding="utf-8").splitlines() if line.strip()]
    v1_hashes = {r["symbolic_program_hash"] for r in v1}
    v1_ids = {r["structure_id"] for r in v1}
    assert not set(mine.values()) & v1_hashes and not set(lw.STRUCTURES) & v1_ids
    assert not {s.law_family for s in lw.STRUCTURES.values()} & {r["law_family"] for r in v1}
    assert not {s.law_family for s in lw.STRUCTURES.values()} & {s.law_family for name in ("lib_m250_waves", "lib_m250_circ", "lib_m250_extra")
                                                                  for s in importlib.import_module(f"physmon.benchmark.v2.{name}").STRUCTURES.values()}
    v1_problems = {r["problem"].split("\n\n")[0] for r in v1}  # the rendered templates differ as well
    for s in lw.STRUCTURES.values():
        assert dg.context_text(s, dict(s.instances[0])) not in v1_problems


# --- mutation tests: the certificate still rejects planted defects -----------------------------------------------------------------------


def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S323"]
    assert "reversal_free" in spec_cert("S323", with_pair(spec, 1, d_attach="In an earlier run, the block also carried and then lost"))["failed"]
    assert "consequence_free" in spec_cert("S323", with_pair(spec, 0, r_attach="the block, so that it hangs lower"))["failed"]
    assert "marker_free" in spec_cert("S323", with_pair(spec, 0, d_attach="an unrelated bucket of sand"))["failed"]
    assert "remoteness_free_d" in spec_cert("S323", with_pair(spec, 0, d_attach="the bucket of sand in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S324"]
    assert "d_not_on_target" in spec_cert("S324", with_pair(spec, 0, d_attach="the bead on the bench"))["failed"]
    assert "d_not_on_target" in spec_cert("S324", with_pair(spec, 1, d_attach="In a different run, the bead also carried"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S324", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s327 = SPECS["S327"]
    assert "value_hygiene" in spec_cert("S327", dataclasses.replace(s327, values=(1800.0, 1100.0, 1000.0)))["failed"]  # D is an input
    bad_c = dataclasses.replace(s327.cancelling, spec=dataclasses.replace(s327.cancelling.spec, expr_with_q="D/(sqrt(q*g*k/q)/(2*k)) + q"))
    assert not spec_cert("S327", dataclasses.replace(s327, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s327.conditional, spec=dataclasses.replace(s327.conditional.spec, counter_regime_value=3000.0))
    assert not spec_cert("S327", dataclasses.replace(s327, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s327.conditional, spec=dataclasses.replace(s327.conditional.spec, values=(40.0, 60.0, 70.0)))
    assert not spec_cert("S327", dataclasses.replace(s327, conditional=low_k))["passed"]  # the ocean would not be deep on instance 3


def test_the_certifier_rejects_a_planted_defect_in_a_new_structure():
    s = lw.STRUCTURES["S324"]
    broken = dataclasses.replace(s, nodes=tuple(
        dataclasses.replace(n, expr="4*Z1*Z2/((Z1 + Z2)**2 + Xm)") if n.name == "tr" else n for n in s.nodes))  # the bead term is not squared
    assert ct.certify(broken)["status"] == "FAILED"


# --- (g) wording rules 6-8, the article rule and the N grammar --------------------------------------------------------------------------

ATTACHING_P1 = {"S323", "S324", "S328"}  # the pair-1 event attaches or adds something (and says for an earlier run only)
BANNED_FILLS = ("further a little", "another a little", "a further a ", "another a ", "by a further a", "a further an ")
A_VOWEL_WORD = re.compile(r"\ba ([aeiou]\w*)", re.IGNORECASE)
A_VOWEL_OK = re.compile(r"^(uni\w*|use\w*|usual\w*|one\w*|once|eu\w*|ubiquit\w*|ultra\w*\b)", re.IGNORECASE)


def vowel_sound_number(s: str) -> bool:
    """True when the numeral reads with a vowel sound (eight, eleven, eighteen, ...)."""
    whole = s.split(".")[0].lstrip("+-")
    return whole[:1] == "8" or (whole[:2] in ("11", "18") and len(whole) in (2, 4, 5))


def article_violations(sentence: str) -> list[str]:
    return [mt.group(0) for mt in re.finditer(r"\b[Aa] (\d[\d.]*)", sentence) if vowel_sound_number(mt.group(1))]


def all_rendered_sentences(sid: str) -> list[str]:
    spec, structure = SPECS[sid], m.structure(sid)
    out = [c.sentence for c in r2.role_cells_v2(structure, spec, 0, include_heldout=True)]
    if spec.cancelling is not None:
        sub = spec.cancelling.spec
        out += [rv._sentence(sub.frame, v, sub.unit, p.relation, sub.nonnumeric_fill)
                for v in (*sub.values, *spec.cancelling.heldout_values) for p in sub.phrasings]
    if spec.conditional is not None:
        sub = spec.conditional.spec
        vals = (*sub.values, *spec.conditional.heldout_values, *spec.conditional.k_out.values)
        out += [rv._sentence(sub.frame, v, sub.unit, p.relation, sub.nonnumeric_fill) for v in vals for p in sub.phrasings]
    return out


def test_article_checker_catches_planted_violations():
    assert article_violations("A 18 V cell was added.") == ["A 18"]
    assert article_violations("Before it, a 8.5 cm rod and a 11 kg mass and a 85 N force.") == ["a 8.5", "a 11", "a 85"]
    assert not article_violations("A 16 V cell, a 0.8 kg mass, a 118 N force, a 3.5 V cell and an 18 V cell.")


@pytest.mark.parametrize("sid", SIDS)
def test_no_rendered_sentence_has_a_wrong_article_before_a_number(sid):
    for sentence in all_rendered_sentences(sid):
        assert not article_violations(sentence), (sid, sentence)


@pytest.mark.parametrize("sid", SIDS)
def test_n_sentences_follow_the_fill_grammar(sid):
    spec = SPECS[sid]
    for pair in spec.pairs:
        n = r2.pair_sentence(pair, "D", None, spec.unit)
        assert not [b for b in BANNED_FILLS if b in n.lower()], n
        assert n[0].isupper() and n.endswith("."), n
        for match in A_VOWEL_WORD.finditer(n):
            assert match.group(1).lower() == "unit" or A_VOWEL_OK.match(match.group(1)), n
    for sentence in all_rendered_sentences(sid):
        assert not [b for b in BANNED_FILLS if b in sentence.lower()], sentence
        for match in A_VOWEL_WORD.finditer(sentence):
            assert match.group(1).lower() == "unit" or A_VOWEL_OK.match(match.group(1)), sentence


@pytest.mark.parametrize("sid", SIDS)
def test_rule_7_attaching_pair_1_d_says_for_an_earlier_run_only(sid):
    spec = SPECS[sid]
    p1 = spec.pairs[1]
    d_sentence = r2.pair_sentence(p1, "D", spec.values[0], spec.unit)
    n_sentence = r2.pair_sentence(p1, "D", None, spec.unit)
    if sid in ATTACHING_P1:
        for text in (d_sentence, n_sentence):
            assert re.search(r"\bfor an earlier (experiment|run|trial|test|survey|mission|day) only\b", text, re.IGNORECASE), text
            assert "in an earlier" not in text.lower()
        assert "only" not in r2.pair_sentence(p1, "R", spec.values[0], spec.unit).lower()
    else:
        assert "earlier" in d_sentence and "only" not in d_sentence.lower()


@pytest.mark.parametrize("sid", SIDS)
def test_rule_8_no_d_or_n_sentence_states_a_state_that_the_scene_clause_contradicts(sid):
    spec = SPECS[sid]
    scene = spec.scene_clause.lower()
    for pair in spec.pairs:
        for value in (spec.values[0], None):
            text = r2.pair_sentence(pair, "D", value, spec.unit).lower()
            assert not re.search(r"\b(now (fills|stands|lies|hangs|sits)|no longer|instead|already)\b", text), text
    p0 = spec.pairs[0]
    assert all(r in scene and r in r2.pair_sentence(p0, "D", spec.values[0], spec.unit).lower() for r in spec.scene_refs)
    context = dg.context_text(m.structure(sid), dict(m.structure(sid).instances[0])).lower()
    assert scene in context


@pytest.mark.parametrize("sid", SIDS)
def test_r_and_d_sentences_differ_within_each_pair(sid):
    spec = SPECS[sid]
    for pair in spec.pairs:
        for value in (*spec.values, *spec.heldout_values):
            assert r2.pair_sentence(pair, "R", value, spec.unit) != r2.pair_sentence(pair, "D", value, spec.unit)
    r0, r1 = (r2.pair_sentence(p, "R", spec.values[0], spec.unit) for p in spec.pairs)
    d0, d1 = (r2.pair_sentence(p, "D", spec.values[0], spec.unit) for p in spec.pairs)
    assert r0 != r1 and d0 != d1


FORBIDDEN_SCENE_WORDS = r"\b(given|stated|before any|after any|anything|any water|any liquid|wherever|onto a|joined to)\b"


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_has_only_physical_conditions_no_meta_or_hypothetical_wording(sid):
    assert not re.search(FORBIDDEN_SCENE_WORDS, SPECS[sid].scene_clause.lower()), SPECS[sid].scene_clause


@pytest.mark.parametrize("sid", SIDS)
def test_no_meta_wording_in_the_base_text(sid):
    text = dg.context_text(m.structure(sid), dict(m.structure(sid).instances[0])).lower()
    assert not re.search(r"\b(given|the original|for this problem|assume)\b", text), text
