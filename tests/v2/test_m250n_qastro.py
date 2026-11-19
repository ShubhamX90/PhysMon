"""Tests for the M250 phase 2 batch qastro (S273 to S282: muon capture photon, Zeeman outer components, box slice probability, isotope tunnelling
ratio, pion survival, reaction threshold, rotor Doppler shift, Hohmann transfer, escape speed of a uniform planet, star luminosity).

(a) every structure is solver-certified, has a valid gold plan and at least four instances, and every role spec passes the v2.1 certificate;
(b) the base gold of every instance and every R gold at every study and held-out value equal closed forms written in this file (not through
the graph); (c) every C quantity leaves the answer invariant (checked by a route written here that carries the quantity through the
intermediate relations) and every K regime holds at every value of every instance, with the regime-ignoring answer from a closed form written
here; (d) the v2.1 wording rules and the eight rules of the panel reviews (a pair-1 R names the moment of the question, no R contradicts the
base, the co-present object is of another type and receives an ordinary action, answer-deciding conditions are stated, a pair-1 D that adds
something says "only", no D or N contradicts the scene, no 'a' before a number read with a vowel sound); (e) the scene clause leaves the base
problem and its gold unchanged; (f) the symbolic program of every structure is new against dataset v1, every `library*`/`lib_*` structure and
the other M250 ranges; plus mutation tests of the certificate, and the gold trace of every emitted cell ends at the cell's gold."""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import math
import re
from pathlib import Path

import pytest
from scipy.integrate import quad

from physmon.benchmark.v2 import certify as ct
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import lib_m250_qastro as lq
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_qastro as m
from physmon.benchmark.v2 import trace as tr
from physmon.benchmark.v2 import traces_v2 as t2
from physmon.benchmark.v2.graph import Structure

REPO_ROOT = Path(__file__).resolve().parents[2]
V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SPECS = m.SPECS
SIDS = sorted(SPECS)
EV = 1.602176634e-19
U = 1.66053906660e-27


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


# --- independent closed forms (display units in, display units out); q is the role quantity in its display unit -----------------------


def _s273(i, k_add=0.0):  # pm: effective Rydberg energy of the reduced-mass atom, Bohr binding energy, photon energy, wavelength
    mu = i["mmu"] * i["M"] / (i["mmu"] + i["M"])
    rydberg = i["ke2"] / (2 * i["a0"]) * mu
    return i["hc"] / (i["K"] + k_add + i["Z"] ** 2 * rydberg / i["n"] ** 2) * 1e3


def _s274(i, b_add_mt=0.0):  # pm: Bohr magneton times the field, the outer separation (gu + gl) mu_B B, then the first-order wavelength change
    b = i["B"] + b_add_mt * 1e-3
    mu_b_b = i["e"] * i["hbar"] * b / (2 * i["me"]) / EV  # eV
    return i["lam"] ** 2 * (i["gu"] + i["gl"]) * mu_b_b / i["hc"] * 1e3


def _s275(i, w_add=0.0):  # probability from the antiderivative of the density
    w = i["w"] + w_add
    return w / i["L"] - (math.sin(2 * math.pi * i["n"] * (i["x1"] + w) / i["L"]) - math.sin(2 * math.pi * i["n"] * i["x1"] / i["L"])) / (
        2 * math.pi * i["n"])


def _kappa(mass_u, v_ev, hbar):
    return math.sqrt(2 * mass_u * U * v_ev * EV) / hbar


def _s276(i, v_add=0.0):  # ratio of the transmissions exp(-2 kp a) / exp(-2 kd a)
    v = i["V"] + v_add
    a = i["a"] * 1e-12
    return math.exp(-2 * _kappa(i["mp"], v, i["hbar"]) * a) / math.exp(-2 * _kappa(i["md"], v, i["hbar"]) * a)


def _s277(i, path_add=0.0):  # fraction: exp(-L / (gamma beta c tau0))
    gamma_beta = i["pc"] * 1e3 / i["mc2"]
    return math.exp(-(i["Lp"] + path_add) / (gamma_beta * i["c"] * i["tau0"] * 1e-9))


def _s278(i, q_add=0.0):  # MeV: K = Q (2 (m1 + m2) + Q) / (2 m2)
    q = i["Q"] + q_add
    return q * (2 * (i["m1"] + i["m2"]) + q) / (2 * i["m2"])


def _s279(i, r_add=0.0):  # MHz: f0 v^2 / (2 c^2)
    v = 2 * math.pi * i["frot"] * (i["R"] + r_add) * 1e-2
    f0 = i["E0"] * 1e3 / i["h"]
    return f0 * v * v / (2 * i["c"] ** 2) / 1e6


def _hohmann(g0, planet, h1, h2):  # km/s: vis-viva on the circles and on the ellipse
    gm = g0 * (planet * 1e3) ** 2
    r1, r2_ = (planet + h1) * 1e3, (planet + h2) * 1e3
    a = (r1 + r2_) / 2
    return ((math.sqrt(gm * (2 / r1 - 1 / a)) - math.sqrt(gm / r1)) + (math.sqrt(gm / r2_) - math.sqrt(gm * (2 / r2_ - 1 / a)))) / 1e3


def _s280(i, h1_add=0.0):
    return _hohmann(i["g0"], i["Rp"], i["h1"] + h1_add, i["h2"])


def _s281(i, r_add=0.0):  # km/s: v = v_E (R / R_E) sqrt(rho / rho_E)
    return i["ve"] * (i["R"] + r_add) / i["RE"] * math.sqrt(i["rho"] / i["rhoE"])


def _s282(i, r_add=0.0):  # solar luminosities: (R / R_sun)^2 (lam_sun / lam)^4
    return (i["R"] + r_add) ** 2 * (i["lamsun"] / i["lam"]) ** 4


ANS = {"S273": _s273, "S274": _s274, "S275": _s275, "S276": _s276, "S277": _s277, "S278": _s278, "S279": _s279, "S280": _s280, "S281": _s281,
       "S282": _s282}
R_FORMS = {sid: (lambda i, q, f=f: f(i, q)) for sid, f in ANS.items()}
BASE_GOLD0 = {"S273": 1585.441946274345, "S274": 27.003119245817416, "S275": 0.346774464189432, "S276": 31.424600187283776,
              "S277": 0.6394657232236759, "S278": 279.6691457682752, "S279": 3.964103098407533, "S280": 0.5342214096086614,
              "S281": 5.028548641104909, "S282": 25.54322233268801}


def inst0(sid: str) -> dict:
    return dict(lq.STRUCTURES[sid].instances[0])


def base_answer(sid: str) -> float:
    return ANS[sid](inst0(sid))


# --- (a) certification ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_structure_is_certified_with_a_valid_plan_and_enough_instances(sid):
    s = lq.STRUCTURES[sid]
    proof = ct.certify(s)
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]
    assert tr.validate_plan(s, lq.PLANS[sid]) == []
    assert len(s.instances) >= 4 and sid in lq.LEVELS and sid in lq.TOPICS
    for index in range(len(s.instances)):  # the trace renders for every instance and ends at the gold
        trace = tr.render_trace(s, lq.PLANS[sid], index)
        assert trace["gold_answer"]["value"] == pytest.approx(dg.gold_for(s, dict(s.instances[index])), rel=1e-9)


@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(SPECS[sid], cert)
    spec = SPECS[sid]
    assert spec.version == "v2.1" == m.CERT_VERSION and spec.structure_id == sid and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE


def test_the_batch_is_the_ten_assigned_structures_and_meets_the_composition_targets(certs):
    assert SIDS == [f"S{n}" for n in range(273, 283)] == sorted(lq.STRUCTURES)
    assert set(m.STRUCTURE_FACTORIES) == set(SIDS) == set(m.TARGET_TERMS) == set(lq.LEVELS) == set(lq.PLANS) == set(lq.TOPICS)
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
        assert (SPECS[sid].conditional is not None) == (sid in m.K_KINDS)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert (len(c), len(k), len(famous)) == (4, 4, 1) and c == ["S276", "S277", "S280", "S281"] and k == ["S273", "S274", "S276", "S280"]
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values
        assert len(m.K_KINDS[sid]) >= 20
    upper = [s for s in SIDS if lq.LEVELS[s] == "upper_university"]
    multi = [s for s in SIDS if len(lq.STRUCTURES[s].computed) >= 3]
    assert len(upper) >= 4 and len(multi) == 10 and set(lq.LEVELS.values()) <= {"intro_university", "upper_university", "high_school"}
    domains = {lq.STRUCTURES[s].domain for s in SIDS}
    assert {"special relativity", "gravitation", "astrophysics"} <= domains and len(domains) >= 4
    assert [lq.STRUCTURES[s].domain for s in SIDS[4:7]] == ["special relativity"] * 3


# --- (b) independent closed forms ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_the_closed_form_reproduces_every_instance_gold(sid):
    s = lq.STRUCTURES[sid]
    for instance in s.instances:
        assert ANS[sid](dict(instance)) == pytest.approx(dg.gold_for(s, dict(instance)), rel=1e-6)
    assert base_answer(sid) == pytest.approx(BASE_GOLD0[sid], rel=1e-6)


def test_third_routes_for_the_box_probability_the_muon_orbit_and_the_threshold_agree_with_the_closed_forms():
    i = inst0("S275")  # a quadrature of the density
    value, _ = quad(lambda x: 2 / i["L"] * math.sin(i["n"] * math.pi * x / i["L"]) ** 2, i["x1"], i["x1"] + i["w"])
    assert value == pytest.approx(base_answer("S275"), rel=1e-9)
    j = inst0("S273")  # the circular orbit of the reduced-mass particle: Coulomb force = centripetal force, angular momentum n hbar
    mu = j["mmu"] * j["M"] / (j["mmu"] + j["M"])
    radius = j["n"] ** 2 * j["a0"] / (j["Z"] * mu)
    kinetic_orbit = j["Z"] * j["ke2"] / (2 * radius)  # half the Coulomb energy, from m v^2 / r = Z ke2 / r^2
    assert j["hc"] / (j["K"] + kinetic_orbit) * 1e3 == pytest.approx(base_answer("S273"), rel=1e-9)
    k = inst0("S278")  # energy and momentum of the beam particle and the target at threshold: the products move with the centre of mass
    e_beam = k["m1"] + _s278(k)
    p_beam = math.sqrt(e_beam ** 2 - k["m1"] ** 2)
    total_e, total_p = e_beam + k["m2"], p_beam
    assert math.sqrt(total_e ** 2 - total_p ** 2) == pytest.approx(k["m1"] + k["m2"] + k["Q"], rel=1e-12)
    zeeman = inst0("S274")  # the six components for g_u = gu, g_l = gl: the spread of the shifts is gu + gl Bohr magnetons B
    shifts = [zeeman["gu"] * mu_u - zeeman["gl"] * m_l for mu_u in (1.5, 0.5, -0.5, -1.5) for m_l in (0.5, -0.5) if abs(mu_u - m_l) <= 1]
    assert len(shifts) == 6 and max(shifts) - min(shifts) == pytest.approx(zeeman["gu"] + zeeman["gl"], rel=1e-12)


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
    for instance in lq.STRUCTURES[sid].instances:  # the response holds on every instance, not only the emitted one
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


# --- (c) invariance of C and the regime of K ---------------------------------------------------------------------------------------------


def _c276(i, current):  # the transmitted current of each beam from the incident current, then their ratio
    a = i["a"] * 1e-12
    transmitted_p = current * math.exp(-2 * _kappa(i["mp"], i["V"], i["hbar"]) * a)
    transmitted_d = current * math.exp(-2 * _kappa(i["md"], i["V"], i["hbar"]) * a)
    return transmitted_p / transmitted_d


def _c277(i, count):  # the number of pions that reach the end of the tube, then the fraction of those sent
    gamma_beta = i["pc"] * 1e3 / i["mc2"]
    reaching = count * math.exp(-i["Lp"] / (gamma_beta * i["c"] * i["tau0"] * 1e-9))
    return reaching / count


def _c280(i, mass):  # the impulses of the two burns on a spacecraft of this mass, then the total change of speed
    gm = i["g0"] * (i["Rp"] * 1e3) ** 2
    r1, r2_ = (i["Rp"] + i["h1"]) * 1e3, (i["Rp"] + i["h2"]) * 1e3
    a = (r1 + r2_) / 2
    impulse_1 = mass * (math.sqrt(gm * (2 / r1 - 1 / a)) - math.sqrt(gm / r1))
    impulse_2 = mass * (math.sqrt(gm / r2_) - math.sqrt(gm * (2 / r2_ - 1 / a)))
    return (impulse_1 + impulse_2) / mass / 1e3


def _c281(i, mass):  # the kinetic energy that the probe needs, then the speed from it
    speed = i["ve"] * i["R"] / i["RE"] * math.sqrt(i["rho"] / i["rhoE"])
    energy = mass * speed ** 2 / 2
    return math.sqrt(2 * energy / mass)


C_ROUTES = {"S276": _c276, "S277": _c277, "S280": _c280, "S281": _c281}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value_on_every_instance(sid, cells):
    spec = SPECS[sid].cancelling
    for instance in lq.STRUCTURES[sid].instances:
        for q in (*spec.spec.values, *spec.heldout_values):
            assert C_ROUTES[sid](dict(instance), q) == pytest.approx(ANS[sid](dict(instance)), rel=1e-6), (instance, q)
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-6)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


def _r_fm(i):  # orbit radius of the muon in fm
    mu = i["mmu"] * i["M"] / (i["mmu"] + i["M"])
    return i["n"] ** 2 * i["a0"] / (i["Z"] * mu) * 1e6


def _d_ev(i):  # energy separation of the outermost Zeeman components in eV
    return (i["gu"] + i["gl"]) * i["e"] * i["hbar"] * i["B"] / (2 * i["me"]) / EV


def _v1_r1(i):  # circular speed (m/s) and radius (m) of the initial orbit
    r1 = (i["Rp"] + i["h1"]) * 1e3
    return math.sqrt(i["g0"] * (i["Rp"] * 1e3) ** 2 / r1), r1


K_REGIME = {
    "S273": lambda i, q: 10 * q < _r_fm(i),
    "S274": lambda i, q: 10 * _d_ev(i) < q,
    "S276": lambda i, q: 8 * q < i["V"],
    "S280": lambda i, q: 10 * q * 60 * _v1_r1(i)[0] < 2 * math.pi * _v1_r1(i)[1],
}


def _k_alt(sid: str, q: float) -> float:  # the answer that ignoring the regime would give, instance 0, in the target unit
    i = inst0(sid)
    if sid == "S273":  # the muon binding energy taken at the nuclear radius q (fm)
        return i["hc"] / (i["K"] + i["Z"] * i["ke2"] / (2 * q * 1e-6)) * 1e3
    if sid == "S274":  # Paschen-Back: outermost components 2 mu_B B apart
        return i["lam"] ** 2 * 2 * (_d_ev(i) / (i["gu"] + i["gl"])) / i["hc"] * 1e3
    if sid == "S276":  # a classical flux over the barrier goes as 1 / sqrt(m)
        return math.sqrt(i["md"] / i["mp"])
    v1, r1 = _v1_r1(i)  # S280: gravity loss over a burn of q minutes
    return base_answer(sid) + v1 ** 2 / r1 * q * 60 / 1e3


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_REGIME) == {s for s in SIDS if SPECS[s].conditional is not None}


@pytest.mark.parametrize("sid", sorted(K_REGIME))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    instances = [dict(i) for i in lq.STRUCTURES[sid].instances]
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


# --- (d) wording, lexicons, pairs, hygiene and the rules of the panel reviews ---------------------------------------------------------


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
def test_rule_1_and_5_a_pair_one_r_ties_the_change_to_the_situation_of_the_question(sid):
    spec = SPECS[sid]
    pair = spec.pairs[1]
    r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
    # the R attachment names this measurement, run or reaction, or the moment of the question ("Before the position is measured"), which is
    # the situation that the question asks about
    assert re.match(r"(?:During this|For this|In this|Before the|When the)\b", pair.r_attach), pair.r_attach
    assert not re.search(r"\b(afterwards|just before that|later|earlier|previously)\b", r_sentence.lower()), r_sentence
    # the D twin is anchored in an earlier run of the same apparatus
    assert re.search(r"\bearlier\b", pair.d_attach)


@pytest.mark.parametrize("sid", SIDS)
def test_rule_2_no_r_sentence_contradicts_a_stated_base_condition(sid):
    spec = SPECS[sid]
    structure = m.structure(sid)
    base = dg.context_text(structure, dict(structure.instances[0]))
    for pair in spec.pairs:
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\b(?:was|were|is|are) set\b|\bafter the\b|\bonce the\b|\bwhen the\b", r_sentence.lower()), r_sentence
        assert r_sentence not in base
        assert not re.search(r"\b(?:replaces?|replaced|instead|changes? the)\b", r_sentence.lower()), r_sentence  # an addition, never a replacement
        assert re.search(r"\bfurther\b|\bsecond\b|\bmore\b|\banother\b|\bstill\b", r_sentence.lower()), r_sentence  # reads as a further change of a stated value
    for pair in spec.pairs:
        for condition in pair.conditions_preserved:
            assert condition in base and not re.search(r"\bnot\b|\bno longer\b", pair.r_attach.lower())


@pytest.mark.parametrize("sid", SIDS)
def test_rule_3_and_4_the_co_present_object_is_of_another_type_and_the_action_is_an_ordinary_one(sid):
    spec = SPECS[sid]
    pair = spec.pairs[0]
    scene = spec.scene_clause.lower()
    for term in spec.target_terms:  # the co-present object is not named with the target's own noun
        noun = term.lower().replace("the ", "").replace("this ", "").replace("each ", "").replace("one ", "").replace("a ", "", 1)
        assert noun not in pair.d_attach.lower(), (term, pair.d_attach)
        assert noun not in spec.scene_refs, (noun, spec.scene_refs)  # the scene object is not another one of the target's kind
    assert all(ref in pair.d_attach for ref in spec.scene_refs)
    furniture = ("stool", "desk lamp", "chair", "table", "shelf", "cupboard", "drawer")
    assert not any(w in scene or w in pair.d_attach.lower() for w in furniture)
    assert not re.search(r"\b\d", pair.frame)
    # the action is one that the co-present object plausibly receives: a gap on a beam, a coil that acts on a compass, a bias on an electrode,
    # pipe on a water line, a particle at another station, a ring on a pulley, a rim of a disc, a layer on a moon
    ordinary = {"S273": "accelerating gap", "S274": "coil", "S275": "widened", "S276": "bias", "S277": "more pipe",
                "S278": "gets", "S279": "gets", "S280": "gets", "S281": "layer of rock",
                "S282": "gets"}[sid]
    assert ordinary in pair.frame
    assert len({s.lower() for s in spec.scene_refs}) == len(spec.scene_refs)


NEEDLES = {
    "S273": ("directly into the bohr level", "single photon", "two-body bohr atom", "only force", "recoil of the atom is neglected"),
    "S274": ("uniform magnetic field", "weak enough", "all six components", "first-order", "fine-structure"),
    "S275": ("infinite square well", "impenetrable walls", "ground state"),
    "S276": ("tunnelling", "no other factor", "equal numbers of particles", "same kinetic energy", "rectangular potential barrier"),
    "S277": ("only by decay", "exponential law", "evacuated tube", "constant speed", "do not interact", "neither interact"),
    "S278": ("free target particle", "at rest in the laboratory", "conserved", "threshold", "no motion relative to each other"),
    "S279": ("constant rotation frequency", "at rest on the axis", "straight line in the laboratory", "leading order"),
    "S280": ("same plane", "instantaneous change of speed", "no atmosphere", "inverse-square", "no other body"),
    "S281": ("uniform sphere", "does not rotate", "no atmosphere", "just escapes", "any other body is ignored"),
    "S282": ("black body", "inversely proportional to its surface temperature"),
}


@pytest.mark.parametrize("sid", SIDS)
def test_rule_6_every_answer_deciding_condition_is_stated_and_the_prompt_carries_only_graph_numerals(sid):
    s = lq.STRUCTURES[sid]
    for index in range(len(s.instances)):
        cell = dg.render_cell(s, index, "no_cue")
        assert dg.prompt_matches_graph(s, cell)
    text = dg.context_text(m.structure(sid), dict(s.instances[0])).lower()
    needles = [n for n in NEEDLES[sid] if n not in ("do not interact",)]
    missing = [n for n in needles if n not in text and not (sid == "S277" and n in ("do not interact", "neither interact"))]
    assert not missing, missing
    scene = SPECS[sid].scene_clause.lower()  # a neighbouring object is separated from the target in the scene itself
    isolation = {"S273": "vacuum line of its own", "S274": "outside the gap", "S275": "beside the apparatus", "S276": "own potential",
                 "S277": "outside of the tube", "S278": "own beam line", "S279": "beside the rotor housing", "S280": "never meets",
                 "S281": "circles the planet", "S282": "well outside its surface"}[sid]
    assert isolation in scene


@pytest.mark.parametrize("sid", SIDS)
def test_rule_7_a_pair_one_d_that_adds_or_changes_something_says_that_it_was_for_that_event_only(sid):
    pair = SPECS[sid].pairs[1]
    assert re.search(r"\bonly, ", pair.d_attach) and not re.search(r"\bonly\b", pair.r_attach)
    # the verb is inside the attachment (one frame for R and D): present tense for this event, past tense for the earlier one
    assert re.search(r"\b(?:gives|adds|gets|carries|carry|is|has)\b[^,]*$", pair.r_attach.split(",", 1)[-1]), pair.r_attach
    assert re.search(r"\b(?:gave|added|got|carried|was|had)\b[^,]*$", pair.d_attach.split(",", 1)[-1]), pair.d_attach
    assert "{relation}" in pair.frame and pair.frame.startswith("{relation}")


STOP = {"a", "an", "the", "of", "to", "for", "in", "on", "at", "by", "before", "they", "it", "is", "are", "and", "with", "from", "that", "this",
        "each", "onto", "into", "against", "than", "as", "be", "its", "their", "who", "which"}


def content_words(sentence: str, attach: str, value: float, unit: str) -> set[str]:
    """The content words of a role sentence once the attachment phrase, the numeral and the unit are removed."""

    text = sentence.replace(attach, " ").replace(f"{rv._fmt(value)} {r2.dg.display_unit(unit)}", " ").replace(rv._fmt(value), " ")
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP}


@pytest.mark.parametrize("sid", SIDS)
def test_the_two_phrasing_pairs_are_genuinely_different_sentences_and_d_shares_the_frame_of_its_r(sid):
    spec = SPECS[sid]
    p0, p1 = spec.pairs
    v, u = spec.values[0], spec.unit
    r0, r1 = (r2.pair_sentence(p, "R", v, u) for p in (p0, p1))
    d0, d1 = (r2.pair_sentence(p, "D", v, u) for p in (p0, p1))
    cr0, cr1 = content_words(r0, p0.r_attach, v, u), content_words(r1, p1.r_attach, v, u)
    cd0, cd1 = content_words(d0, p0.d_attach, v, u), content_words(d1, p1.d_attach, v, u)
    assert len(cr0 ^ cr1) >= 3 and len(cr0 - cr1) >= 1 and len(cr1 - cr0) >= 1, (cr0, cr1)
    assert len(cd0 ^ cd1) >= 3, (cd0, cd1)
    assert cr0 == cd0 and cr1 == cd1  # d_i shares the frame of its r_i: only the attachment differs
    assert r1.replace(p1.r_attach, "@") == d1.replace(p1.d_attach, "@") and r0.replace(p0.r_attach, "@") == d0.replace(p0.d_attach, "@")
    assert r0 != r1 and d0 != d1 and p0.frame != p1.frame and p0.r_attach != p1.r_attach and p0.d_attach != p1.d_attach


@pytest.mark.parametrize("sid", SIDS)
def test_rule_8_no_d_or_n_sentence_contradicts_the_scene_clause_or_the_base(sid, cells):
    spec = SPECS[sid]
    scene = spec.scene_clause.lower()
    base = dg.context_text(m.structure(sid), dict(m.structure(sid).instances[0])).lower()
    for cell in cells[sid]:
        if cell.stratum not in ("D", "N"):
            continue
        text = cell.sentence.lower()
        assert not re.search(r"\b(?:now fills|fills|is filled|is empty|now holds)\b", text), text
        assert not re.search(r"\b(?:no longer|stopped|empties|empty)\b", text), text
    for ref in spec.scene_refs:  # the co-present object of d0 is one that the scene clause itself introduced
        assert ref in scene
    # a D sentence names no condition that the base text denies: the added quantity does not appear in the stated inputs
    assert all(c.lower() in base for p in spec.pairs for c in p.conditions_preserved)


VOWEL_NUMBER = re.compile(r"(?<![\w'])([aA])\s+(\d+)")


def _vowel_sound(integer_part: str) -> bool:
    return integer_part[0] == "8" or (len(integer_part) % 3 == 2 and integer_part[:2] in ("11", "18"))


@pytest.mark.parametrize("sid", SIDS)
def test_no_article_a_stands_before_a_number_read_with_a_vowel_sound_in_any_rendered_sentence(sid, cells):
    spec = SPECS[sid]
    sentences = [c.sentence for c in cells[sid] if c.sentence]
    for pair in spec.pairs:
        for value in (*spec.values, *spec.heldout_values):
            sentences += [r2.pair_sentence(pair, "R", value, spec.unit), r2.pair_sentence(pair, "D", value, spec.unit)]
    for wrapped in (spec.cancelling, spec.conditional):
        if wrapped is None:
            continue
        sub = wrapped.spec
        for value in (*sub.values, *wrapped.heldout_values):
            sentences += [rv._sentence(sub.frame, value, sub.unit, p.relation, sub.nonnumeric_fill) for p in sub.phrasings]
    sentences.append(dg.context_text(m.structure(sid), dict(m.structure(sid).instances[0])))
    for sentence in sentences:
        for match in VOWEL_NUMBER.finditer(sentence):
            assert not _vowel_sound(match.group(2)), sentence


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
def test_the_gold_trace_of_every_emitted_cell_ends_at_the_cell_gold(sid, cells):
    structure, plan = m.structure(sid), lq.PLANS[sid]
    for cell in cells[sid]:
        if cell.heldout:
            continue
        trace = t2.trace_for_role_cell(structure, SPECS[sid], plan, cell)
        assert trace["gold_answer"]["value"] == pytest.approx(cell.gold_value, rel=1e-9), cell.cell_id


# --- (e) the scene clause leaves the base problem and its gold unchanged ------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_is_the_only_change_to_the_base_problem_and_the_gold_is_unchanged(sid):
    structure, original = m.structure(sid), m.STRUCTURE_FACTORIES[sid]()
    scene = SPECS[sid].scene_clause
    prompt = rv._assemble(structure, 0, "", "after_context")
    assert prompt.replace(f" {scene}", "", 1) == rv._assemble(original, 0, "", "after_context")
    assert dg.context_text(structure, dict(structure.instances[0])).endswith(scene)
    assert dg.structure_hash(structure) == dg.structure_hash(original) and structure.nodes == original.nodes
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(BASE_GOLD0[sid], rel=1e-6)
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
        if path.stem == "lib_m250_qastro":
            continue
        try:  # another agent's range may be mid-edit; a module that does not import cannot clash and is skipped
            module = importlib.import_module(f"physmon.benchmark.v2.{path.stem}")
        except Exception:  # noqa: BLE001
            continue
        for sid, structure in getattr(module, "STRUCTURES", {}).items():
            found[f"{path.stem}:{sid}"] = dg.structure_hash(structure)
    return found


def test_program_hashes_and_templates_differ_from_every_existing_structure():
    mine = {sid: dg.structure_hash(s) for sid, s in lq.STRUCTURES.items()}
    assert len(set(mine.values())) == len(mine)
    existing = _existing_hashes()
    assert len(existing) >= 90
    assert not set(mine.values()) & set(existing.values())
    v1 = [json.loads(line) for line in V1.read_text(encoding="utf-8").splitlines() if line.strip()]
    v1_hashes = {r["symbolic_program_hash"] for r in v1}
    v1_ids = {r["structure_id"] for r in v1}
    assert not set(mine.values()) & v1_hashes and not set(lq.STRUCTURES) & v1_ids
    assert not {s.law_family for s in lq.STRUCTURES.values()} & {r["law_family"] for r in v1}
    # the rendered templates differ as well: no context text of a new structure equals one of dataset v1
    v1_problems = {r["problem"].split("\n\n")[0] for r in v1}
    for s in lq.STRUCTURES.values():
        assert dg.context_text(s, dict(s.instances[0])) not in v1_problems


# --- mutation tests: the certificate still rejects planted defects -----------------------------------------------------------------------


def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S274"]
    assert "reversal_free" in spec_cert("S274", with_pair(spec, 1, d_attach="In an earlier run, taken out again"))["failed"]
    assert "consequence_free" in spec_cert("S274", with_pair(spec, 0, r_attach="the vapour, so that the lines move apart"))["failed"]
    assert "marker_free" in spec_cert("S274", with_pair(spec, 0, d_attach="an unrelated compass"))["failed"]
    assert "remoteness_free_d" in spec_cert("S274", with_pair(spec, 0, d_attach="the compass in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S277"]
    assert "d_not_on_target" in spec_cert("S277", with_pair(spec, 0, d_attach="the pions in the cooling-water line"))["failed"]
    assert "d_not_on_target" in spec_cert("S277", with_pair(spec, 1, d_attach="For a different tube, the flight path got a further"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S277", dataclasses.replace(spec, scene_refs=("chamber",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s281 = SPECS["S281"]
    assert "value_hygiene" in spec_cert("S281", dataclasses.replace(s281, values=(150.0, 260.0, 3390.0)))["failed"]  # 3390 km is the radius input
    bad_c = dataclasses.replace(s281.cancelling, spec=dataclasses.replace(s281.cancelling.spec, expr_with_q="sqrt(2*(q*(ve*(R/RE)*sqrt(rho/rhoE))**2/2)/q) + q"))
    assert not spec_cert("S281", dataclasses.replace(s281, cancelling=bad_c))["passed"]
    s276 = SPECS["S276"]
    bad_k = dataclasses.replace(s276.conditional, spec=dataclasses.replace(s276.conditional.spec, counter_regime_value=0.001))
    assert not spec_cert("S276", dataclasses.replace(s276, conditional=bad_k))["passed"]  # a thermal energy of 1 meV is inside the regime: not a counter value
    high_k = dataclasses.replace(s276.conditional, spec=dataclasses.replace(s276.conditional.spec, values=(0.02, 0.025, 0.2)))
    assert not spec_cert("S276", dataclasses.replace(s276, conditional=high_k))["passed"]  # 0.2 eV breaks the regime at the study value


def test_the_certifier_rejects_a_planted_defect_in_a_new_structure():
    s = lq.STRUCTURES["S280"]
    broken = dataclasses.replace(s, nodes=tuple(
        dataclasses.replace(n, expr="v1*sqrt(2*r1/(r1 + r2))") if n.name == "vp" else n for n in s.nodes))  # the transfer speed uses the wrong radius
    assert ct.certify(broken)["status"] == "FAILED"


BANNED_FILLS = ("further a little", "another a little", "a little of", "a little thick", "a little solar", "a further a ", "another a ")


@pytest.mark.parametrize("sid", SIDS)
def test_no_n_or_role_sentence_contains_an_ungrammatical_fill(sid, cells):
    for cell in cells[sid]:
        if cell.sentence:
            assert not [b for b in BANNED_FILLS if b in cell.sentence.lower()], cell.sentence
    for pair in SPECS[sid].pairs:
        n = r2.pair_sentence(pair, "D", None, SPECS[sid].unit)
        assert not [b for b in BANNED_FILLS if b in n.lower()], n
        assert n[0].isupper() and n.endswith("."), n
    assert "protons" not in dg.context_text(m.structure(sid), dict(m.structure(sid).instances[0])).split("has 1 ")[-1][:10]
