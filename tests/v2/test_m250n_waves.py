"""Tests for the M250 phase 2 batch waves (S231 to S240: waves, acoustics, optics, fluids).

(a) every structure is solver-certified, has a valid gold plan and at least four instances; every role spec passes the v2.1 certificate;
(b) the base gold of every instance and every R gold at every study and held-out value equal closed forms written in this file (not
through the graph); (c) every C quantity leaves the answer invariant and every K regime holds at every value of every instance, with
the regime-ignoring answer from a closed form written here; (d) the v2.1 wording rules and the five rules of the 2026-11-15 panel review
(a pair-1 R names the moment of the question, no R contradicts the base, the co-present object is of another type and receives an
ordinary action); (e) the scene clause leaves the base problem and its gold unchanged; (f) the symbolic program of every structure is
new against dataset v1, every `library*`/`lib_*` structure and the other M250 ranges; plus mutation tests of the certificate."""

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
from physmon.benchmark.v2 import lib_m250_waves as lw
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_waves as m
from physmon.benchmark.v2 import trace as tr
from physmon.benchmark.v2.graph import Structure

REPO_ROOT = Path(__file__).resolve().parents[2]
V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SPECS = m.SPECS
SIDS = sorted(SPECS)
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


def _s231(i, v_add=0.0):
    v = i["v"] + v_add
    return 2 * i["f"] * v / (i["c"] - v)  # f (c + v) / (c - v) - f


def _s232(i, sigma_cut=0.0):  # d(omega)/dk by a central difference of omega(k)
    k0, sigma = 2 * math.pi / (i["lam"] * 1e-2), i["sigma"] - sigma_cut

    def omega(k):
        return math.sqrt(G * k + sigma * k ** 3 / i["rho"])

    dk = k0 * 1e-6
    return (omega(k0 + dk) - omega(k0 - dk)) / (2 * dk)


def _s233(i, p_add=0.0):  # tangent law r_p = tan(theta - theta_t) / tan(theta + theta_t); the power that enters is P0 (1 - r_p^2)
    th = math.radians(i["theta"])
    tt = math.asin(math.sin(th) / i["n"])
    rp = math.tan(th - tt) / math.tan(th + tt)
    return (i["P0"] + p_add) * (1 - rp ** 2)


def _s234(i, length_add=0.0):  # ns
    cos_r = math.sqrt(1 - (math.sin(math.radians(i["theta"])) / i["n"]) ** 2)
    return i["n"] * (i["L"] + length_add) / (i["c"] * 1e3 * cos_r) * 1e9


def _s235(i, h_add_cm=0.0):
    return 2 * math.pi * math.sqrt(i["rho_b"] * (i["h"] + h_add_cm) * 1e-2 / (i["rho_l"] * G))


def _s236(i, l_add_cm=0.0):
    area = math.pi * (i["a"] * 1e-2) ** 2
    leff = (i["l"] + l_add_cm + 2 * i["beta"] * i["a"]) * 1e-2
    return i["c"] / (2 * math.pi) * math.sqrt(area / (i["V"] * 1e-3 * leff))


def _s237(i, h2_add=0.0):  # minutes: integral of dx / sqrt(g h) with h linear in x
    h1, h2, d = i["h1"], i["h2"] + h2_add, i["D"] * 1e3
    return 2 * d * (math.sqrt(h1) - math.sqrt(h2)) / (math.sqrt(G) * (h1 - h2)) / 60


def _s238(i, rot_add=0.0):
    omega = 2 * math.pi * (i["rot"] + rot_add) / 60
    r1, r2_ = i["R1"] * 1e-3, i["R2"] * 1e-3
    return 4 * math.pi * i["eta"] * i["L"] * 1e-2 * omega ** 2 * r1 ** 2 * r2_ ** 2 / (r2_ ** 2 - r1 ** 2)


def _s239(i, thin_um=0.0):
    delta = 2 * math.pi * i["dn"] * (i["d"] - thin_um) / (i["lam"] * 1e-3)
    return i["P0"] * math.sin(2 * math.radians(i["alpha"])) ** 2 * math.sin(delta / 2) ** 2


def _s240(i, rho=None):  # kPa: p0 - rho g H - rho v^2 / 2 with v^2 = 2 g h
    rho = i["rho"] if rho is None else rho
    return i["p0"] - rho * G * (i["H"] + i["h"]) / 1000


ANS = {"S231": _s231, "S232": _s232, "S233": _s233, "S234": _s234, "S235": _s235, "S236": _s236, "S237": _s237, "S238": _s238,
       "S239": _s239, "S240": _s240}
# the answer with q in the R role (display unit of q) on instance dict i
R_FORMS = {
    "S231": lambda i, q: _s231(i, v_add=q), "S232": lambda i, q: _s232(i, sigma_cut=q), "S233": lambda i, q: _s233(i, p_add=q),
    "S234": lambda i, q: _s234(i, length_add=q), "S235": lambda i, q: _s235(i, h_add_cm=q), "S236": lambda i, q: _s236(i, l_add_cm=q),
    "S237": lambda i, q: _s237(i, h2_add=q), "S238": lambda i, q: _s238(i, rot_add=q), "S239": lambda i, q: _s239(i, thin_um=q),
    "S240": lambda i, q: _s240(i, rho=q),
}
BASE_GOLD0 = {"S231": 7.764705882352928, "S232": 0.18589122408042544, "S233": 4.4661745050987784, "S234": 12.847077955138971,
              "S235": 0.8863069119258409, "S236": 121.98497323531254, "S237": 29.18830311427555, "S238": 0.18294293837123202,
              "S239": 5.119622468437586, "S240": 78.76}


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


def test_the_batch_is_the_ten_assigned_structures_and_meets_the_composition_targets(certs):
    assert SIDS == [f"S{n}" for n in range(231, 241)] == sorted(lw.STRUCTURES)
    assert set(m.STRUCTURE_FACTORIES) == set(SIDS) == set(m.TARGET_TERMS) == set(lw.LEVELS) == set(lw.PLANS)
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
        assert (SPECS[sid].conditional is not None) == (sid in m.K_KINDS)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert len(c) >= 6 and len(k) >= 4 and len(famous) <= 3 and (len(c), len(k)) == (7, 8)
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values
        assert len(m.K_KINDS[sid]) >= 20
    upper = [s for s in SIDS if lw.LEVELS[s] == "upper_university"]
    multi = [s for s in SIDS if len(lw.STRUCTURES[s].computed) >= 3]
    assert len(upper) >= 4 and len(multi) >= 4 and set(lw.LEVELS.values()) <= {"intro_university", "upper_university", "high_school"}
    assert len({lw.STRUCTURES[s].domain for s in SIDS}) >= 3


# --- (b) independent closed forms ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_the_closed_form_reproduces_every_instance_gold(sid):
    s = lw.STRUCTURES[sid]
    for instance in s.instances:
        assert ANS[sid](dict(instance)) == pytest.approx(dg.gold_for(s, dict(instance)), rel=1e-6)
    assert base_answer(sid) == pytest.approx(BASE_GOLD0[sid], rel=1e-6)


def test_the_s233_fresnel_amplitudes_agree_with_a_complex_linear_solve():  # a third route for the least familiar structure
    i = inst0("S233")
    th = math.radians(i["theta"])
    ct_ = cmath.sqrt(1 - (math.sin(th) / i["n"]) ** 2)
    r, t = np.linalg.solve(np.array([[-math.cos(th), -ct_], [1.0, -i["n"]]], dtype=complex), np.array([-math.cos(th), -1.0], dtype=complex))
    assert i["P0"] * (1 - abs(r) ** 2) == pytest.approx(base_answer("S233"), rel=1e-9)
    assert i["P0"] * (i["n"] * ct_ * abs(t) ** 2 / math.cos(th)).real == pytest.approx(base_answer("S233"), rel=1e-9)


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


def _c231(i, q_m):  # crest tracking: crest n leaves at n/f, meets the wall that starts q away, the echo returns at c
    def arrival(n):
        t_hit = (q_m + i["c"] * n / i["f"]) / (i["c"] + i["v"])
        return (t_hit * (i["c"] - i["v"]) + q_m) / i["c"]

    return 1 / (arrival(5) - arrival(4)) - i["f"]


def _c233(i, area_mm2):  # intensity times area
    a = area_mm2 * 1e-6
    th = math.radians(i["theta"])
    tt = math.asin(math.sin(th) / i["n"])
    rp = math.tan(th - tt) / math.tan(th + tt)
    return (i["P0"] * 1e-3 / a) * (1 - rp ** 2) * a * 1e3


def _c234(i, diameter_cm):  # count of legs times the length of a leg
    thr = math.asin(math.sin(math.radians(i["theta"])) / i["n"])
    legs = i["L"] * math.tan(thr) / (diameter_cm * 1e-2)
    return i["n"] * legs * (diameter_cm * 1e-2 / math.sin(thr)) / (i["c"] * 1e3) * 1e9


def _c235(i, radius_cm):  # m = rho_b pi r^2 h, k = rho_l g pi r^2
    r = radius_cm * 1e-2
    return 2 * math.pi * math.sqrt(i["rho_b"] * math.pi * r ** 2 * i["h"] * 1e-2 / (i["rho_l"] * G * math.pi * r ** 2))


def _c236(i, density):  # m = rho A Leff, k = rho c^2 A^2 / V
    area = math.pi * (i["a"] * 1e-2) ** 2
    leff = (i["l"] + 2 * i["beta"] * i["a"]) * 1e-2
    return math.sqrt(density * i["c"] ** 2 * area ** 2 / (i["V"] * 1e-3) / (density * area * leff)) / (2 * math.pi)


def _c238(i, density):  # nu = eta / rho, torque with rho nu
    nu = i["eta"] / density
    omega = 2 * math.pi * i["rot"] / 60
    r1, r2_ = i["R1"] * 1e-3, i["R2"] * 1e-3
    return 4 * math.pi * density * nu * i["L"] * 1e-2 * omega ** 2 * r1 ** 2 * r2_ ** 2 / (r2_ ** 2 - r1 ** 2)


def _c240(i, bore_mm):  # speed at the crest from the flow rate and the area, then Bernoulli
    area = math.pi * (bore_mm * 1e-3) ** 2 / 4
    v = math.sqrt(2 * G * i["h"])
    return i["p0"] - i["rho"] * G * i["H"] / 1000 - i["rho"] * ((area * v) / area) ** 2 / 2000


C_ROUTES = {"S231": _c231, "S233": _c233, "S234": _c234, "S235": _c235, "S236": _c236, "S238": _c238, "S240": _c240}
UNITS_OF_Q = {"S231": 1.0}


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


def _s232_k(i, q):
    return 2 * math.pi / (i["lam"] * 1e-2) * q * 1e-2 > 6


def _s234_k(i, q):
    return i["n"] * math.sqrt(1 - (math.sin(math.radians(i["theta"])) / i["n"]) ** 2) > q


def _s235_k(i, q):
    d0 = i["rho_b"] * i["h"] / i["rho_l"]
    return min(d0, i["h"] - d0) > q


def _s236_k(i, q):
    return 6 * q * 1e-2 * _s236(i) < i["c"]


def _s237_k(i, q):
    return q * 1e3 > 20 * i["h1"]


def _s238_k(i, q):
    return i["rot"] < q


def _s239_k(i, q):
    return q > 10 * i["dn"] * i["d"]


def _s240_k(i, q):
    return _s240(i) > q


K_REGIME = {"S232": _s232_k, "S234": _s234_k, "S235": _s235_k, "S236": _s236_k, "S237": _s237_k, "S238": _s238_k, "S239": _s239_k,
            "S240": _s240_k}


def _k_alt(sid: str, q: float) -> float:  # the answer that reading the K quantity as the working value would give, instance 0
    i = inst0(sid)
    return {
        "S232": lambda: math.sqrt(G * q * 1e-2),
        "S234": lambda: q * (i["L"] / math.sqrt(1 - (math.sin(math.radians(i["theta"])) / i["n"]) ** 2)) / (i["c"] * 1e3) * 1e9,
        "S235": lambda: 2 * math.pi * math.sqrt((i["rho_b"] * i["h"] / i["rho_l"] * 1e-2 + q * 1e-2) / G),
        "S236": lambda: i["c"] / (4 * q * 1e-2),
        "S237": lambda: i["D"] * 1e3 / math.sqrt(G * q * 1e3 / (2 * math.pi)) / 60,
        "S238": lambda: _s238(i) * (q / i["rot"]) ** 2,
        "S239": lambda: i["P0"] * math.sin(2 * math.radians(i["alpha"])) ** 2 / 2,
        "S240": lambda: q,
    }[sid]()


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


# --- (d) wording, lexicons, pairs, hygiene and the five rules of the panel review ----------------------------------------------------


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
        if sid == "S239" and pair.pair_id == "p1":  # a thinning leaves a lasting change; the measurement D needs its own frame (recorded)
            assert pair.d_frame and pair.frame_mismatch_reason
            continue
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
    # the R attachment ties the change to the moment the question asks about: "before the echo was recorded", "before it struck ..."
    assert re.match(r"before\b", pair.r_attach.lower()), pair.r_attach
    assert not re.search(r"\b(afterwards|just before that|later|earlier|previously)\b", r_sentence.lower())
    # the same sentence frame in the D twin is anchored in an earlier run or survey
    assert re.search(r"\bearlier\b", pair.d_attach)
    # the event is stated in the past perfect (it is over before the asked moment) in the frame shared by R and D
    assert re.search(r"\bhad (?:added|reduced|been|thinned)\b", pair.frame) or sid == "S237"
    if sid == "S237":
        assert pair.frame.startswith("{relation}, dredging added") and pair.r_attach.startswith("Before")


@pytest.mark.parametrize("sid", SIDS)
def test_rule_2_no_r_sentence_contradicts_a_stated_base_condition(sid):
    spec = SPECS[sid]
    structure = m.structure(sid)
    base = dg.context_text(structure, dict(structure.instances[0]))
    for pair in spec.pairs:
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\b(?:was|were|is|are) set\b|\bafter the\b|\bonce the\b|\bwhen the\b", r_sentence.lower()), r_sentence
        assert r_sentence not in base
    # every condition the D events must leave true is stated in the base text and no R wording negates it
    for pair in spec.pairs:
        for condition in pair.conditions_preserved:
            assert condition in base and not re.search(r"\bnot\b|\bno longer\b", pair.r_attach.lower())


@pytest.mark.parametrize("sid", SIDS)
def test_rule_3_and_4_the_co_present_object_is_of_another_type_and_the_action_is_an_ordinary_one(sid):
    spec = SPECS[sid]
    pair = spec.pairs[0]
    scene = spec.scene_clause.lower()
    assert not any(re.search(rf"\b{w}\b", scene) for w in FIRST_PERSON), scene  # no "a second, identical ..." object of the target's type
    for term in spec.target_terms:  # the co-present object is not named with the target's own noun
        noun = term.lower().replace("the ", "").replace("this ", "")
        assert noun not in pair.d_attach.lower(), (term, pair.d_attach)
        assert not re.match(rf"an? (?:\w+ ){{0,2}}{re.escape(noun)}\b", scene), scene  # the scene object itself is not another one of the target's type
    # the D attachment names the scene object, and the action of the frame is the same one that R applies to the target
    assert all(ref in pair.d_attach for ref in spec.scene_refs) or all(ref in pair.d_attach for ref in spec.scene_refs[:1])
    furniture = ("stool", "desk lamp", "chair", "table", "shelf", "cupboard", "drawer")
    assert not any(w in scene or w in pair.d_attach.lower() for w in furniture)
    assert not re.search(r"\b\d", pair.frame)  # the action is not a precise measured act on unrelated furniture: its number is the value slot


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
        for cell_id in ("no_cue",):
            cell = dg.render_cell(s, index, cell_id)
            assert dg.prompt_matches_graph(s, cell)
    text = dg.context_text(s, dict(s.instances[0])).lower()
    needles = {"S231": ("still air", "constant speed"), "S232": ("deeper than the wavelength", "viscosity is negligible"),
               "S233": ("plane of incidence", "does not absorb"), "S234": ("totally internally reflected", "refractive index"),
               "S235": ("upright", "neglect drag"), "S236": ("rigid plug", "adiabatically"), "S237": ("shallow-water", "neglect its height"),
               "S238": ("steady and laminar", "sticks"), "S239": ("normal incidence", "does not absorb"),
               "S240": ("without friction", "incompressible")}[sid]
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
        if path.stem == "lib_m250_waves":
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
    # the rendered templates differ as well: no context text of a new structure equals one of dataset v1
    v1_problems = {r["problem"].split("\n\n")[0] for r in v1}
    for s in lw.STRUCTURES.values():
        assert dg.context_text(s, dict(s.instances[0])) not in v1_problems


# --- mutation tests: the certificate still rejects planted defects -----------------------------------------------------------------------


def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S238"]
    assert "reversal_free" in spec_cert("S238", with_pair(spec, 1, d_attach="in an earlier run, taken out again"))["failed"]
    assert "consequence_free" in spec_cert("S238", with_pair(spec, 0, r_attach="the rotor, so that it turns faster"))["failed"]
    assert "marker_free" in spec_cert("S238", with_pair(spec, 0, d_attach="an unrelated stirrer"))["failed"]
    assert "remoteness_free_d" in spec_cert("S238", with_pair(spec, 0, d_attach="the stirrer in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S234"]
    assert "d_not_on_target" in spec_cert("S234", with_pair(spec, 0, d_attach="the rod on the bench"))["failed"]
    assert "d_not_on_target" in spec_cert("S234", with_pair(spec, 1, d_attach="in a different run"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S234", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s240 = SPECS["S240"]
    assert "value_hygiene" in spec_cert("S240", dataclasses.replace(s240, values=(760.0, 1180.0, 1000.0)))["failed"]  # rho is an input
    bad_c = dataclasses.replace(s240.cancelling, spec=dataclasses.replace(
        s240.cancelling.spec, expr_with_q="p0 - rho*g*H - rho*(v*(pi*q**2/4)/(pi*q**2/4))**2/2 + q"))
    assert not spec_cert("S240", dataclasses.replace(s240, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s240.conditional, spec=dataclasses.replace(s240.conditional.spec, counter_regime_value=1.0))
    assert not spec_cert("S240", dataclasses.replace(s240, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s240.conditional, spec=dataclasses.replace(s240.conditional.spec, values=(60.0, 70.0, 75.0)))
    assert not spec_cert("S240", dataclasses.replace(s240, conditional=low_k))["passed"]  # the liquid would boil on instance 2


def test_the_certifier_rejects_a_planted_defect_in_a_new_structure():
    s = lw.STRUCTURES["S236"]
    broken = dataclasses.replace(s, nodes=tuple(
        dataclasses.replace(n, expr="c*sqrt(A/(V*Leff))") if n.name == "f" else n for n in s.nodes))  # the 1/(2 pi) is dropped
    assert ct.certify(broken)["status"] == "FAILED"


# --- (g) wording rules 6-8 and article agreement (retrofit of J15.1-046) ---------------------------------------------------------------

ATTACHING_P1 = {"S231", "S232", "S233", "S234", "S235", "S236", "S237", "S238", "S240"}  # the pair-1 event adds or attaches something to the target


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
def test_rule_7_attaching_pair_1_d_says_for_an_earlier_run_only(sid):
    spec = SPECS[sid]
    p1 = spec.pairs[1]
    d_sentence = r2.pair_sentence(p1, "D", spec.values[0], spec.unit)
    n_sentence = r2.pair_sentence(p1, "D", None, spec.unit)
    r_sentence = r2.pair_sentence(p1, "R", spec.values[0], spec.unit)
    if sid in ATTACHING_P1:
        for text in (d_sentence, n_sentence):
            assert re.search(r"\bfor an earlier (experiment|run|trial|test|survey|mission|day) only\b", text, re.IGNORECASE), text
    else:
        assert "earlier" in d_sentence and "only" not in d_sentence.lower()
    assert "only" not in r_sentence.lower()


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
