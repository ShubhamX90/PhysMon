"""Tests for the M250 phase 2 batch modern (S241 to S250: photocell, decay crossing, Rutherford, annihilation, laser slowing, gamma shield,
light pressure, proton precession, relativistic cyclotron, electron Bragg diffraction).

(a) every structure is solver-certified, has a valid gold plan and at least four instances, and every role spec passes the v2.1 certificate;
(b) the base gold of every instance and every R gold at every study and held-out value equal closed forms written in this file (not through
the graph); (c) every C quantity leaves the answer invariant (checked by a route written here that carries the quantity through the
intermediate relations) and every K regime holds at every value of every instance, with the regime-ignoring answer from a closed form written
here; (d) the v2.1 wording rules and the eight rules of the panel reviews (a pair-1 R names the moment of the question, no R contradicts the
base, the co-present object is of another type and receives an ordinary action, answer-deciding conditions are stated, a pair-1 D that adds
something says "only", no D or N contradicts the scene); (e) the scene clause leaves the base problem and its gold unchanged; (f) the symbolic
program of every structure is new against dataset v1, every `library*`/`lib_*` structure and the other M250 ranges; plus mutation tests of
the certificate, and the gold trace of every emitted cell ends at the cell's gold."""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import math
import re
from pathlib import Path

import pytest
from scipy.optimize import brentq

from physmon.benchmark.v2 import certify as ct
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import lib_m250_modern as lm
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_modern as m
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


def _s241(i, p_add=0.0):  # photon energy in J, photons per second, electrons per second, current in uA
    photon = i["hc"] * EV / i["lam"]  # hc in eV nm over nm is eV
    return i["eta"] * i["e"] * ((i["P"] + p_add) * 1e-3 / photon) * 1e6


def _s242(i, a2_add=0.0):  # hours: ln(A1 / A2') / (lam1 - lam2)
    return math.log(i["A1"] / (i["A2"] + a2_add)) / (math.log(2) * (1 / i["T1"] - 1 / i["T2"]))


def _s243(i, k_add=0.0):  # fm: head-on distance, then the closest approach for the deflection
    head_on = 2 * i["Z"] * i["e"] ** 2 / (4 * math.pi * i["eps0"] * (i["K"] + k_add) * 1e6 * EV)
    return head_on / 2 * (1 + 1 / math.sin(math.radians(i["theta"]) / 2)) * 1e15


def _s244(i, k_add=0.0):  # keV
    k, mc2 = i["K"] + k_add, i["mc2"]
    return (k + 2 * mc2 + math.sqrt(k * k + 2 * k * mc2)) / 2


def _s245(i, k_add=0.0):  # photons: initial speed from the kinetic energy over the speed lost per absorption
    speed = math.sqrt(2 * (i["K"] + k_add) * EV / (i["M"] * U))
    return speed / (i["h"] / (i["lam"] * 1e-9) / (i["M"] * U))


def _s246(i, tc_add=0.0):  # cm
    return (math.log(i["F"]) - i["muc"] * (i["tc"] + tc_add) / 100) / i["mupb"] * 100


def _s247(i, intensity_add=0.0):  # m/s
    c = i["c"] * 1e3
    pressure = (1 + i["Rf"]) * math.cos(math.radians(i["theta"])) ** 2 * (i["I"] + intensity_add) / c
    return pressure * i["A"] / i["m"] * i["t"] * 3600


def _s248(i, b_add=0.0):  # MHz
    return i["gp"] * i["e"] * (i["B"] + b_add) * 1e-3 / (4 * math.pi * i["mp"]) / 1e6


def _s249(i, k_add=0.0):  # MHz
    c = i["c"] * 1e3
    gamma = 1 + (i["K"] + k_add) * 1e6 * EV / (i["m"] * c * c)
    return i["e"] * i["B"] / (2 * math.pi * gamma * i["m"]) / 1e6


def _s250(i, k_add=0.0):  # degrees
    k, mc2 = i["K"] + k_add, i["mc2"]
    pc = math.sqrt(k * k + 2 * k * mc2)  # keV
    lam_pm = i["hc"] / (pc * 1e3) * 1e3
    return math.degrees(math.asin(lam_pm / (2 * i["d"])))


ANS = {"S241": _s241, "S242": _s242, "S243": _s243, "S244": _s244, "S245": _s245, "S246": _s246, "S247": _s247, "S248": _s248,
       "S249": _s249, "S250": _s250}
R_FORMS = {sid: (lambda i, q, f=f: f(i, q)) for sid, f in ANS.items()}
BASE_GOLD0 = {"S241": 4.838176227719101, "S242": 14.81259, "S243": 54.91588923581221, "S244": 1514.6555309114628,
              "S245": 27163.441573890617, "S246": 5.8879254649702295, "S247": 114.98865, "S248": 14.8979215314053,
              "S249": 16.527117830343805, "S250": 2.4794174696718065}


def inst0(sid: str) -> dict:
    return dict(lm.STRUCTURES[sid].instances[0])


def base_answer(sid: str) -> float:
    return ANS[sid](inst0(sid))


# --- (a) certification ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_structure_is_certified_with_a_valid_plan_and_enough_instances(sid):
    s = lm.STRUCTURES[sid]
    proof = ct.certify(s)
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]
    assert tr.validate_plan(s, lm.PLANS[sid]) == []
    assert len(s.instances) >= 4 and sid in lm.LEVELS and sid in lm.TOPICS
    for index in range(len(s.instances)):  # the trace renders for every instance and ends at the gold
        trace = tr.render_trace(s, lm.PLANS[sid], index)
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
    assert SIDS == [f"S{n}" for n in range(241, 251)] == sorted(lm.STRUCTURES)
    assert set(m.STRUCTURE_FACTORIES) == set(SIDS) == set(m.TARGET_TERMS) == set(lm.LEVELS) == set(lm.PLANS) == set(lm.TOPICS)
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
        assert (SPECS[sid].conditional is not None) == (sid in m.K_KINDS)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert (len(c), len(k), len(famous)) == (6, 3, 0) and c == ["S242", "S245", "S246", "S247", "S248", "S250"] and k == ["S241", "S243", "S245"]
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values
        assert len(m.K_KINDS[sid]) >= 20
    upper = [s for s in SIDS if lm.LEVELS[s] == "upper_university"]
    multi = [s for s in SIDS if len(lm.STRUCTURES[s].computed) >= 3]
    assert len(upper) >= 4 and len(multi) == 10 and set(lm.LEVELS.values()) <= {"intro_university", "upper_university", "high_school"}
    assert len({lm.STRUCTURES[s].domain for s in SIDS}) >= 3


# --- (b) independent closed forms ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_the_closed_form_reproduces_every_instance_gold(sid):
    s = lm.STRUCTURES[sid]
    for instance in s.instances:
        assert ANS[sid](dict(instance)) == pytest.approx(dg.gold_for(s, dict(instance)), rel=1e-6)
    assert base_answer(sid) == pytest.approx(BASE_GOLD0[sid], rel=1e-6)


def test_the_s243_orbit_equation_and_the_s244_conservation_laws_agree_with_the_closed_forms():  # a third route for two of the structures
    i = inst0("S243")
    head_on = 2 * i["Z"] * i["e"] ** 2 / (4 * math.pi * i["eps0"] * i["K"] * 1e6 * EV)
    b = head_on / 2 / math.tan(math.radians(i["theta"]) / 2)  # impact parameter of the hyperbola that deflects by theta
    r = (head_on + math.sqrt(head_on ** 2 + 4 * b * b)) / 2  # r^2 - D r - b^2 = 0
    assert r * 1e15 == pytest.approx(base_answer("S243"), rel=1e-9)
    j = inst0("S244")
    e_pos, mc2 = j["K"] + j["mc2"], j["mc2"]
    p = math.sqrt(e_pos ** 2 - mc2 ** 2)  # momentum of the positron (times c)
    forward, backward = (e_pos + mc2 + p) / 2, (e_pos + mc2 - p) / 2
    assert forward + backward == pytest.approx(e_pos + mc2, rel=1e-12) and forward - backward == pytest.approx(p, rel=1e-9)
    assert forward == pytest.approx(base_answer("S244"), rel=1e-9)


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
    for instance in lm.STRUCTURES[sid].instances:  # the response holds on every instance, not only the emitted one
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


def _c242(i, efficiency):  # the two count rates, equated by a root finder
    l1, l2 = math.log(2) / i["T1"], math.log(2) / i["T2"]
    return brentq(lambda t: efficiency * i["A1"] * math.exp(-l1 * t) - efficiency * i["A2"] * math.exp(-l2 * t), 0.0, 1e4, xtol=1e-12)


def _c245(i, rate_mhz):  # force from photon momentum times scattering rate, deceleration, stopping time, then the photons scattered in it
    rate = rate_mhz * 1e6
    force = i["h"] / (i["lam"] * 1e-9) * rate
    stop_time = math.sqrt(2 * i["K"] * EV / (i["M"] * U)) / (force / (i["M"] * U))
    return rate * stop_time


def _c246(i, intensity):  # the intensity behind the shield from the factor, then the thickness from the intensity ratio
    behind = intensity / i["F"]
    return (math.log(intensity / behind) - i["muc"] * i["tc"] / 100) / i["mupb"] * 100


def _c247(i, photon_ev):  # photons per area per second, momentum of one photon, momentum flux, then force, acceleration and speed
    c = i["c"] * 1e3
    flux = i["I"] / (photon_ev * EV)
    momentum = photon_ev * EV / c
    pressure = (1 + i["Rf"]) * math.cos(math.radians(i["theta"])) ** 2 * flux * momentum
    return pressure * i["A"] / i["m"] * i["t"] * 3600


def _c248(i, tilt_deg):  # torque per unit of the perpendicular spin component
    tilt = math.radians(tilt_deg)
    gyro = i["gp"] * i["e"] / (2 * i["mp"])
    torque_per_spin = gyro * i["B"] * 1e-3 * math.sin(tilt)  # (mu B sin q) / L
    perpendicular = math.sin(tilt)  # L sin q / L
    return torque_per_spin / perpendicular / (2 * math.pi) / 1e6


def _c250(i, film_cm):  # the ring radius on the film, then the glancing angle recovered from it
    pc = math.sqrt(i["K"] ** 2 + 2 * i["K"] * i["mc2"])
    theta = math.asin(i["hc"] / (pc * 1e3) * 1e3 / (2 * i["d"]))
    radius = film_cm * 1e-2 * math.tan(2 * theta)
    return math.degrees(math.atan(radius / (film_cm * 1e-2)) / 2)


C_ROUTES = {"S242": _c242, "S245": _c245, "S246": _c246, "S247": _c247, "S248": _c248, "S250": _c250}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value_on_every_instance(sid, cells):
    spec = SPECS[sid].cancelling
    for instance in lm.STRUCTURES[sid].instances:
        for q in (*spec.spec.values, *spec.heldout_values):
            assert C_ROUTES[sid](dict(instance), q) == pytest.approx(ANS[sid](dict(instance)), rel=1e-6), (instance, q)
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-6)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


def _eph_ev(i):
    return i["hc"] / i["lam"]


def _doppler_ghz(i):
    return math.sqrt(2 * i["K"] * EV / (i["M"] * U)) / (i["lam"] * 1e-9) / 1e9


K_REGIME = {"S241": lambda i, q: _eph_ev(i) > q, "S243": lambda i, q: _s243(i) > q, "S245": lambda i, q: _doppler_ghz(i) < q}


def _k_alt(sid: str, q: float) -> float:  # the answer that ignoring the regime would give, instance 0
    i = inst0(sid)
    return {"S241": lambda: 0.0, "S243": lambda: q,
            "S245": lambda: i["M"] * U * q * 1e9 * (i["lam"] * 1e-9) ** 2 / i["h"]}[sid]()


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_REGIME) == {s for s in SIDS if SPECS[s].conditional is not None}


@pytest.mark.parametrize("sid", sorted(K_REGIME))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    instances = [dict(i) for i in lm.STRUCTURES[sid].instances]
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
def test_rule_1_and_5_a_pair_one_r_ties_the_change_to_the_situation_of_the_question_in_the_present_tense(sid):
    spec = SPECS[sid]
    pair = spec.pairs[1]
    r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
    # the R attachment names this measurement, shield, run or sample, which is the situation that the question asks about
    assert re.match(r"(?:During|For|At the moment of preparation of) this\b", pair.r_attach), pair.r_attach
    assert not re.search(r"\b(afterwards|just before that|later|earlier|previously|was|were|had)\b", r_sentence.lower()), r_sentence
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
    assert not re.search(r"\b\d", pair.frame)  # the action is not a precise measured act on unrelated furniture: its number is the value slot
    # the action is one that the co-present object plausibly receives: a lamp that lights a dial or a screen, a nozzle on a jet, a layer on a roof
    ordinary = {"S241": "lamp", "S242": "batch", "S243": "accelerating gap", "S244": "accelerating gap", "S245": "nozzle", "S246": "layer",
                "S247": "lamp", "S248": "coil", "S249": "accelerating gap", "S250": "accelerating stage"}[sid]
    assert ordinary in pair.frame
    assert len({s.lower() for s in spec.scene_refs}) == len(spec.scene_refs)


NEEDLES = {
    "S241": ("every released electron is collected", "passes all of the light"),
    "S242": ("decay independently", "only those", "background counts are negligible", "the same efficiency"),
    "S243": ("purely electrostatic", "scattered only once", "do not affect the motion", "non-relativistic", "stay at rest"),
    "S244": ("exactly two photons", "free electron that is at rest", "no other particle"),
    "S245": ("stays in resonance", "averages to zero", "non-relativistic", "no other force"),
    "S246": ("narrow beam", "falls exponentially", "scattered out of the beam", "energy of these gamma rays"),
    "S247": ("frictionless rail", "starts at rest", "in vacuum", "no other force", "heating of the mirror is neglected", "specularly"),
    "S248": ("free proton", "uniform, constant magnetic field", "no other magnetic field"),
    "S249": ("uniform, constant magnetic field", "neglect radiation", "no electric field", "relativistic mechanics"),
    "S250": ("in vacuum", "relativistic momentum", "first-order bragg reflection"),
}


@pytest.mark.parametrize("sid", SIDS)
def test_rule_6_every_answer_deciding_condition_is_stated_and_the_prompt_carries_only_graph_numerals(sid):
    s = lm.STRUCTURES[sid]
    for index in range(len(s.instances)):
        cell = dg.render_cell(s, index, "no_cue")
        assert dg.prompt_matches_graph(s, cell)
    text = dg.context_text(m.structure(sid), dict(s.instances[0])).lower()
    assert all(n in text for n in NEEDLES[sid]), [n for n in NEEDLES[sid] if n not in text]
    scene = SPECS[sid].scene_clause.lower()  # a neighbouring object is separated from the target in the scene itself
    isolation = {"S241": "shielded", "S242": "outside its shielding", "S243": "well to the side", "S244": "own beam tube",
                 "S245": "does not enter", "S246": "well to the side", "S247": "do not shine", "S248": "outside the gap",
                 "S249": "own magnet", "S250": "own vacuum line"}[sid]
    assert isolation in scene


@pytest.mark.parametrize("sid", SIDS)
def test_rule_7_a_pair_one_d_that_adds_something_says_that_it_was_there_for_that_event_only(sid):
    pair = SPECS[sid].pairs[1]
    assert re.search(r"\bonly, ", pair.d_attach) and not re.search(r"\bonly\b", pair.r_attach)
    # the verb is inside the attachment (one frame for R and D): present tense for this event, past tense for the earlier one
    assert re.search(r"\b(?:puts|mixes in|gives|lay)$", pair.r_attach), pair.r_attach
    assert re.search(r"\b(?:put|mixed in|gave|laid)$", pair.d_attach), pair.d_attach
    assert "{relation}" in pair.frame and pair.frame.startswith("{relation} {value} {unit}")


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
    assert cr0 == cd0 and cr1 == cd1  # d_i shares the frame of r_i: only the attachment differs
    assert r1.replace(p1.r_attach, "@") == d1.replace(p1.d_attach, "@") and r0.replace(p0.r_attach, "@") == d0.replace(p0.d_attach, "@")


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
    structure, plan = m.structure(sid), lm.PLANS[sid]
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
        if path.stem == "lib_m250_modern":
            continue
        try:  # another agent's range may be mid-edit; a module that does not import cannot clash and is skipped
            module = importlib.import_module(f"physmon.benchmark.v2.{path.stem}")
        except Exception:  # noqa: BLE001
            continue
        for sid, structure in getattr(module, "STRUCTURES", {}).items():
            found[f"{path.stem}:{sid}"] = dg.structure_hash(structure)
    return found


def test_program_hashes_and_templates_differ_from_every_existing_structure():
    mine = {sid: dg.structure_hash(s) for sid, s in lm.STRUCTURES.items()}
    assert len(set(mine.values())) == len(mine)
    existing = _existing_hashes()
    assert len(existing) >= 90
    assert not set(mine.values()) & set(existing.values())
    v1 = [json.loads(line) for line in V1.read_text(encoding="utf-8").splitlines() if line.strip()]
    v1_hashes = {r["symbolic_program_hash"] for r in v1}
    v1_ids = {r["structure_id"] for r in v1}
    assert not set(mine.values()) & v1_hashes and not set(lm.STRUCTURES) & v1_ids
    assert not {s.law_family for s in lm.STRUCTURES.values()} & {r["law_family"] for r in v1}
    # the rendered templates differ as well: no context text of a new structure equals one of dataset v1
    v1_problems = {r["problem"].split("\n\n")[0] for r in v1}
    for s in lm.STRUCTURES.values():
        assert dg.context_text(s, dict(s.instances[0])) not in v1_problems


# --- mutation tests: the certificate still rejects planted defects -----------------------------------------------------------------------


def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S248"]
    assert "reversal_free" in spec_cert("S248", with_pair(spec, 1, d_attach="In an earlier run, taken out again"))["failed"]
    assert "consequence_free" in spec_cert("S248", with_pair(spec, 0, r_attach="the sample, so that it precesses faster"))["failed"]
    assert "marker_free" in spec_cert("S248", with_pair(spec, 0, d_attach="an unrelated compass"))["failed"]
    assert "remoteness_free_d" in spec_cert("S248", with_pair(spec, 0, d_attach="the compass in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S244"]
    assert "d_not_on_target" in spec_cert("S244", with_pair(spec, 0, d_attach="the positrons in the chamber"))["failed"]
    assert "d_not_on_target" in spec_cert("S244", with_pair(spec, 1, d_attach="For a different annihilation"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S244", dataclasses.replace(spec, scene_refs=("chamber",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s246 = SPECS["S246"]
    assert "value_hygiene" in spec_cert("S246", dataclasses.replace(s246, values=(4.3, 7.7, 30.0)))["failed"]  # 30 cm is the wall input
    bad_c = dataclasses.replace(s246.cancelling, spec=dataclasses.replace(s246.cancelling.spec, expr_with_q="(log(q/(q/F)) - muc*tc)/mupb + q"))
    assert not spec_cert("S246", dataclasses.replace(s246, cancelling=bad_c))["passed"]
    s241 = SPECS["S241"]
    bad_k = dataclasses.replace(s241.conditional, spec=dataclasses.replace(s241.conditional.spec, counter_regime_value=1.0))
    assert not spec_cert("S241", dataclasses.replace(s241, conditional=bad_k))["passed"]  # 1 eV is below every photon energy: not a counter value
    low_k = dataclasses.replace(s241.conditional, spec=dataclasses.replace(s241.conditional.spec, values=(2.5, 3.0, 3.3)))
    assert not spec_cert("S241", dataclasses.replace(s241, conditional=low_k))["passed"]  # the cell would be below threshold on instance 3


def test_the_certifier_rejects_a_planted_defect_in_a_new_structure():
    s = lm.STRUCTURES["S243"]
    broken = dataclasses.replace(s, nodes=tuple(
        dataclasses.replace(n, expr="Z*ke2/K") if n.name == "D" else n for n in s.nodes))  # the factor 2 of the alpha charge is dropped
    assert ct.certify(broken)["status"] == "FAILED"
