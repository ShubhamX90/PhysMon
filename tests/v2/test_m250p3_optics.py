"""Tests for the M250 phase 3 batch optics (S301 to S310: geometric and physical optics).

(a) every structure is solver-certified, has a valid gold plan and at least four instances; every role spec passes the v2.1 certificate;
(b) the base gold of every instance and every R gold at every study and held-out value equal closed forms written in this file (not
through the graph); (c) every C quantity leaves the answer invariant and every K regime holds at every value of every instance, with
the regime-ignoring answer from a closed form written here; (d) the v2.1 wording rules, the five rules of the 2026-11-15 panel review and
rules 6-8 (a pair-1 R names the moment of the question, no R contradicts the base, the co-present object is of another type and receives an
ordinary action, an attaching pair-1 D says "for an earlier run only"); (e) the scene clause leaves the base problem and its gold
unchanged; (f) the symbolic program of every structure is new against dataset v1, every `library*`/`lib_*` structure and the other M250
ranges; (g) the N sentences are grammatical (the fill grammar guard of `test_m250_n_fill_grammar`, repeated here for this module);
plus mutation tests of the certificate."""

from __future__ import annotations

import cmath
import dataclasses
import importlib
import inspect
import json
import math
import re
from pathlib import Path

import pytest
from scipy.special import jn_zeros

from physmon.benchmark.v2 import certify as ct
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import lib_m250p3_optics as lo
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250p3_optics as m
from physmon.benchmark.v2 import trace as tr
from physmon.benchmark.v2.graph import Structure

REPO_ROOT = Path(__file__).resolve().parents[2]
V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SPECS = m.SPECS
SIDS = sorted(SPECS)
FIRST_PERSON = ("second", "another", "identical", "same type", "other")
J1_ZERO = float(jn_zeros(1, 1)[0])


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


def _s301(i, t_add=0.0):  # mm: t sin(theta - theta_r) / cos(theta_r)
    th = math.radians(i["theta"])
    thr = math.asin(math.sin(th) / i["n"])
    return (i["t"] + t_add) * math.sin(th - thr) / math.cos(thr)


def _s302(i, h_add=0.0):  # cm: apparent thicknesses add
    return (i["h"] + h_add) / i["nw"] + i["t"] / i["no"]


def _s303(i, h_add=0.0):  # m^2: pi h^2 / (n^2 - 1)
    return math.pi * (i["h"] + h_add) ** 2 / (i["n"] ** 2 - 1)


def _s304(i, g_add=0.0):  # Newtonian magnification f / (f - x) on each pass; the plane mirror has magnification +1
    f, u = i["f"], i["u"]
    v1 = u * f / (u - f)
    s2 = 2 * (i["g"] + g_add) - v1
    return (f / (f - u)) * (f / (f - s2))


def _s305(i, th_add=0.0):  # deg: the two refractions, summed
    a = math.radians(i["A"])
    th = math.radians(i["theta"] + th_add)
    first = math.asin(math.sin(th) / i["n"])
    out = math.asin(i["n"] * math.sin(a - first))
    return math.degrees((th - first) + (out - (a - first)))


def _s306(i, lam_add=0.0):  # cm
    return i["D"] * 100 * math.tan(math.asin(i["m"] * (i["lam"] + lam_add) * 1e-3 / i["d"]))


def _s307(i, t_add=0.0):  # mm: equal optical paths in the far field
    return i["D"] * 1e3 * math.tan(math.asin((i["n"] - 1) * (i["t"] + t_add) * 1e-6 / (i["d"] * 1e-3)))


def _s308(i, t_add=0.0):  # mW: the coefficient of the whole coated surface from the Airy sum with a complex phase
    n1, n2 = i["n1"], i["n2"]
    r1, r2_ = (1 - n1) / (1 + n1), (n1 - n2) / (n1 + n2)
    phase = cmath.exp(2j * 2 * math.pi * n1 * (i["t"] + t_add) / i["lam"])
    return i["P0"] * abs((r1 + r2_ * phase) / (1 + r1 * r2_ * phase)) ** 2


def _s309(i, d_add=0.0):  # km
    return i["L"] * math.asin(J1_ZERO * i["lam"] * 1e-9 / (math.pi * (i["D"] + d_add) * 1e-2))


def _s310(i, p_add=0.0):  # mW: only the component perpendicular to the plane of incidence is reflected at Brewster's angle
    return (i["P0"] + p_add) * math.sin(math.radians(i["psi"])) ** 2 * ((i["n"] ** 2 - 1) / (i["n"] ** 2 + 1)) ** 2


ANS = {"S301": _s301, "S302": _s302, "S303": _s303, "S304": _s304, "S305": _s305, "S306": _s306, "S307": _s307, "S308": _s308,
       "S309": _s309, "S310": _s310}
# the answer with q in the R role (display unit of q) on instance dict i
R_FORMS = {
    "S301": lambda i, q: _s301(i, t_add=q), "S302": lambda i, q: _s302(i, h_add=q), "S303": lambda i, q: _s303(i, h_add=q),
    "S304": lambda i, q: _s304(i, g_add=q), "S305": lambda i, q: _s305(i, th_add=q), "S306": lambda i, q: _s306(i, lam_add=q),
    "S307": lambda i, q: _s307(i, t_add=q), "S308": lambda i, q: _s308(i, t_add=q), "S309": lambda i, q: _s309(i, d_add=q),
    "S310": lambda i, q: _s310(i, p_add=q),
}
BASE_GOLD0 = {"S301": 4.691756255158122, "S302": 26.63802363050483, "S303": 13.23808063159179, "S304": 0.1764705882352941,
              "S305": 25.38177767834771, "S306": 39.25930550244178, "S307": 12.000216005832174, "S308": 0.06654280049468342,
              "S309": 1.7190840694491414, "S310": 0.3893371932984206}
# the 1e-6 tolerance of the solver route of S307 (exact slit-to-point distances) and the 1e-4 of S309 (the stated zero of J1 is rounded)
REL = {"S307": 1e-6, "S309": 1e-6}


def inst0(sid):
    return dict(lo.STRUCTURES[sid].instances[0])


def base_answer(sid):
    return ANS[sid](inst0(sid))


# --- (a) certification ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_structure_is_certified_with_a_valid_plan_and_enough_instances(sid):
    s = lo.STRUCTURES[sid]
    proof = ct.certify(s)
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]
    assert tr.validate_plan(s, lo.PLANS[sid]) == []
    assert len(s.instances) >= 4 and sid in lo.LEVELS and sid in lo.TOPICS
    for index in range(len(s.instances)):  # the trace renders for every instance and ends at the gold
        trace = tr.render_trace(s, lo.PLANS[sid], index)
        assert trace["gold_answer"]["value"] == pytest.approx(dg.gold_for(s, dict(s.instances[index])), rel=1e-9)


@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(SPECS[sid], cert)
    spec = SPECS[sid]
    assert spec.version == "v2.1" and m.CERT_VERSION == "v2.1" and spec.structure_id == sid
    assert len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE


def test_the_batch_is_the_ten_assigned_structures_and_meets_the_composition_targets(certs):
    assert SIDS == [f"S{n}" for n in range(301, 311)] == sorted(lo.STRUCTURES)
    assert set(m.STRUCTURE_FACTORIES) == set(SIDS) == set(m.TARGET_TERMS) == set(lo.LEVELS) == set(lo.PLANS) == set(lo.TOPICS)
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
        assert (SPECS[sid].conditional is not None) == (sid in m.K_KINDS)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert len(c) >= 6 and len(famous) <= 3 and (len(c), len(k)) == (7, 2)
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values
        assert len(m.K_KINDS[sid]) >= 20
    upper = [s for s in SIDS if lo.LEVELS[s] == "upper_university"]
    multi = [s for s in SIDS if len(lo.STRUCTURES[s].computed) >= 3]
    assert len(upper) >= 4 and len(multi) >= 4 and set(lo.LEVELS.values()) <= {"intro_university", "upper_university", "high_school"}
    assert {lo.STRUCTURES[s].domain for s in SIDS} == {"optics"}
    # five geometric and five physical structures
    assert len(SIDS) == 10


# --- (b) independent closed forms ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SIDS)
def test_the_closed_form_reproduces_every_instance_gold(sid):
    s = lo.STRUCTURES[sid]
    for instance in s.instances:
        assert ANS[sid](dict(instance)) == pytest.approx(dg.gold_for(s, dict(instance)), rel=REL.get(sid, 1e-9))
    assert base_answer(sid) == pytest.approx(BASE_GOLD0[sid], rel=REL.get(sid, 1e-9))


def test_s306_and_s301_agree_with_a_second_independent_route():
    # S301: the same sideways shift from the exit point of the ray and the incident line
    i = inst0("S301")
    th = math.radians(i["theta"])
    thr = math.asin(math.sin(th) / i["n"])
    exit_x = i["t"] * math.tan(thr)
    assert (i["t"] * math.tan(th) - exit_x) * math.cos(th) == pytest.approx(base_answer("S301"), rel=1e-9)
    # S303: the area from the radius at the critical angle
    i = inst0("S303")
    radius = i["h"] * math.tan(math.asin(1 / i["n"]))
    assert math.pi * radius ** 2 == pytest.approx(base_answer("S303"), rel=1e-9)
    # S310: Brewster's angle from the tangent law; the s amplitude from the sine law
    i = inst0("S310")
    brewster = math.atan(i["n"])
    refracted = math.pi / 2 - brewster
    assert math.sin(refracted) == pytest.approx(math.sin(brewster) / i["n"], rel=1e-12)
    rs = -math.sin(brewster - refracted) / math.sin(brewster + refracted)
    assert i["P0"] * math.sin(math.radians(i["psi"])) ** 2 * rs ** 2 == pytest.approx(base_answer("S310"), rel=1e-9)


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
    for instance in lo.STRUCTURES[sid].instances:  # the response holds on every instance, not only the emitted one
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


def _c301(i, screen_cm):  # coordinates along a screen parallel to the plate: the emergent ray and the line of the incident ray
    th = math.radians(i["theta"])
    thr = math.asin(math.sin(th) / i["n"])
    q = screen_cm * 10.0  # mm
    x_emergent = i["t"] * math.tan(thr) + q * math.tan(th)
    x_incident = (i["t"] + q) * math.tan(th)
    return (x_incident - x_emergent) * math.cos(th)


def _c302(i, eye_cm):  # the apparent distance of the coin from the eye, minus the height of the eye
    return (eye_cm + i["h"] / i["nw"] + i["t"] / i["no"]) - eye_cm


def _c304(i, height_mm):  # the heights of the first and the final images over the height of the object
    f, u, g = i["f"], i["u"], i["g"]
    v1 = u * f / (u - f)
    s2 = 2 * g - v1
    v2 = s2 * f / (s2 - f)
    h2 = height_mm * (v1 / u) * (v2 / s2)
    return h2 / height_mm


def _c305(i, screen_cm):  # the spot on a screen square to the incident ray, then the arctangent of its displacement over the distance
    delta = math.radians(_s305(i))
    shift = screen_cm * math.tan(delta)
    return math.degrees(math.atan(shift / screen_cm))


def _c307(i, lam_nm):  # fringe count of the film, then the fringe position from the count and the fringe spacing in the sine
    lam = lam_nm * 1e-9
    count = (i["n"] - 1) * i["t"] * 1e-6 / lam
    sine = count * lam / (i["d"] * 1e-3)
    return i["D"] * 1e3 * math.tan(math.asin(sine))


def _c308(i, area_mm2):  # intensity times area
    area = area_mm2 * 1e-6
    return (i["P0"] / area) * (_s308(i) / i["P0"]) * area


def _c309(i, focal_cm):  # radius of the first dark ring in the focal plane, then the angle it subtends at the telescope
    theta = math.asin(J1_ZERO * i["lam"] * 1e-9 / (math.pi * i["D"] * 1e-2))
    radius = focal_cm * theta
    return i["L"] * (radius / focal_cm)


C_ROUTES = {"S301": _c301, "S302": _c302, "S304": _c304, "S305": _c305, "S307": _c307, "S308": _c308, "S309": _c309}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {sid for sid in SIDS if SPECS[sid].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value_on_every_instance(sid, cells):
    spec = SPECS[sid].cancelling
    for instance in lo.STRUCTURES[sid].instances:
        base = ANS[sid](dict(instance))
        for value in (*spec.spec.values, *spec.heldout_values):
            assert C_ROUTES[sid](dict(instance), value) == pytest.approx(base, rel=REL.get(sid, 1e-9)), (sid, value)
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-6)
        assert abs(cell.foils["wrong_law"] - cell.gold_value) > rv.LOOSEST_REL_TOL * abs(cell.gold_value), cell.cell_id


def _k303(i, cone_deg):  # (regime holds, answer if the cone were the limit)
    crit = math.degrees(math.asin(1 / i["n"]))
    return cone_deg > crit, math.pi * (i["h"] * math.tan(math.radians(cone_deg))) ** 2


def _k308(i, coherence_um):  # coherent regime; the incoherent answer adds the powers of the successive reflections
    n1, n2 = i["n1"], i["n2"]
    r1s, r2s = ((1 - n1) / (1 + n1)) ** 2, ((n1 - n2) / (n1 + n2)) ** 2
    incoherent = r1s + (1 - r1s) ** 2 * r2s / (1 - r1s * r2s)
    return coherence_um * 1e-6 > 20 * n1 * i["t"] * 1e-9, i["P0"] * incoherent


K_REGIME = {"S303": _k303, "S308": _k308}


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_REGIME) == {sid for sid in SIDS if SPECS[sid].conditional is not None} == set(m.K_KINDS)


@pytest.mark.parametrize("sid", sorted(K_REGIME))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    instances = [dict(i) for i in lo.STRUCTURES[sid].instances]
    for value in (*spec.spec.values, *spec.heldout_values):
        for instance in instances:
            holds, alternative = K_REGIME[sid](instance, value)
            assert holds, (sid, value, instance)
            base = ANS[sid](instance)
            assert abs(alternative - base) > rv.LOOSEST_REL_TOL * abs(base)
    assert not any(K_REGIME[sid](i, spec.spec.counter_regime_value)[0] for i in instances)
    k_cells = [c for c in cells[sid] if c.stratum == "K"]
    assert len(k_cells) == 2 * len(spec.spec.values)
    for cell in k_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-6)  # inside the regime the answer is the base answer
        assert cell.foils["out_of_regime"] == pytest.approx(K_REGIME[sid](inst0(sid), cell.value)[1], rel=1e-6), cell.cell_id
    assert not [c for c in cells[sid] if c.stratum == "K_out"] and len(spec.k_out.reason) >= r2.MIN_RATIONALE
    assert m.K_KINDS[sid]


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
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        d_sentence = r2.pair_sentence(pair, "D", spec.values[0], spec.unit)
        if pair.pair_id == "p0":
            assert pair.frame_matched and rec["same_frame_numeral_unit"]  # one frame, numeral and unit
            assert r_sentence.replace(pair.r_attach, "@") == d_sentence.replace(pair.d_attach, "@")  # attachment-only difference
        else:  # pair 1 differs in tense only: "has been" in R, "had been" in D
            assert pair.d_frame == pair.frame.replace("has been", "had been") and len(pair.frame_mismatch_reason) >= 40
            assert r_sentence.replace(pair.r_attach, "@").replace("has been", "had been") == d_sentence.replace(pair.d_attach, "@")
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
    # the R attachment ties the change to the moment the question asks about
    assert re.match(r"before\b", pair.r_attach.lower()), pair.r_attach
    assert not re.search(r"\b(afterwards|just before that|later|earlier|previously)\b", r_sentence.lower())
    assert re.search(r"\bearlier\b", pair.d_attach)
    # the event is in the past and its sentence names the very object the question asks about
    assert re.search(r"\bhas been (?:laid|poured|added|slid|raised|tuned|brushed|deposited|opened|turned)\b", pair.frame), pair.frame
    assert re.search(r"\bhad been\b", pair.d_frame) and pair.d_attach == "For an earlier run only"
    assert pair.frame.startswith("{relation},")


@pytest.mark.parametrize("sid", SIDS)
def test_rule_2_no_r_sentence_contradicts_a_stated_base_condition(sid):
    spec = SPECS[sid]
    structure = m.structure(sid)
    base = dg.context_text(structure, dict(structure.instances[0]))
    for pair in spec.pairs:
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\b(?:was|were|is|are) set\b|\bafter the\b|\bonce the\b|\bwhen the\b", r_sentence.lower()), r_sentence
        assert r_sentence not in base
    for pair in spec.pairs:
        for condition in pair.conditions_preserved:
            assert condition in base and not re.search(r"\bnot\b|\bno longer\b", pair.r_attach.lower())
    # the R sentences read as a further change: "further", "laid on", "poured into", "added to" or "brushed onto" ...
    for pair in spec.pairs:
        text = r2.pair_sentence(pair, "R", spec.values[0], spec.unit).lower()
        assert re.search(r"further|laid|poured|brushed|slid|raised", text), text


@pytest.mark.parametrize("sid", SIDS)
def test_rule_3_and_4_the_co_present_object_is_of_another_type_and_the_action_is_an_ordinary_one(sid):
    spec = SPECS[sid]
    pair = spec.pairs[0]
    scene = spec.scene_clause.lower()
    assert not any(re.search(rf"\b{w}\b", scene) for w in FIRST_PERSON), scene  # no "a second, identical ..." object of the target's type
    for term in spec.target_terms:  # the co-present object is not named with the target's own noun
        noun = term.lower().replace("the ", "").replace("this ", "")
        assert noun not in pair.d_attach.lower(), (term, pair.d_attach)
        assert not re.match(rf"an? (?:\w+ ){{0,2}}{re.escape(noun)}\b", scene), scene
    assert all(ref.lower() in pair.d_attach.lower() for ref in spec.scene_refs)
    furniture = ("stool", "desk lamp", "chair", "shelf", "cupboard", "drawer")
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


NEEDLES = {
    "S301": ("parallel-sided plate", "does not absorb light", "refractive index is taken as one"),
    "S302": ("do not mix", "flat and horizontal", "straight down"),
    "S303": ("total internal reflection", "flat, still surface", "treated as a point"),
    "S304": ("thin converging lens", "perpendicular to the axis", "perfectly reflecting plane mirror"),
    "S305": ("does not disperse or absorb light", "perpendicular to the edge", "refractive index of one"),
    "S306": ("tunable laser", "far-field pattern", "maximum of order zero"),
    "S307": ("does not disperse or absorb light", "far-field", "optical paths from the two slits are equal"),
    "S308": ("normal incidence", "coherent over the thickness", "only the light reflected by the coated front surface"),
    "S309": ("diffraction of the light at this stop alone", "just resolved", "incoherent", "adjustable circular stop"),
    "S310": ("plane-polarised", "adjustable laser", "none of the light polarised in the plane of incidence is reflected", "only the first surface"),
}


@pytest.mark.parametrize("sid", SIDS)
def test_every_answer_deciding_condition_is_stated_and_the_prompt_carries_only_graph_numerals(sid):
    s = lo.STRUCTURES[sid]
    for index in range(len(s.instances)):
        for cell_id in ("no_cue",):
            cell = dg.render_cell(s, index, cell_id)
            assert dg.prompt_matches_graph(s, cell)
    text = dg.context_text(s, dict(s.instances[0])).lower()
    assert all(n in text for n in NEEDLES[sid]), [n for n in NEEDLES[sid] if n not in text]


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
        if path.stem == "lib_m250p3_optics":
            continue
        try:  # another agent's range may be mid-edit; a module that does not import cannot clash and is skipped
            module = importlib.import_module(f"physmon.benchmark.v2.{path.stem}")
        except Exception:  # noqa: BLE001
            continue
        for sid, structure in getattr(module, "STRUCTURES", {}).items():
            found[f"{path.stem}:{sid}"] = dg.structure_hash(structure)
    return found


def test_program_hashes_and_templates_differ_from_every_existing_structure():
    mine = {sid: dg.structure_hash(s) for sid, s in lo.STRUCTURES.items()}
    assert len(set(mine.values())) == len(mine)
    existing = _existing_hashes()
    assert len(existing) >= 140
    assert not set(mine.values()) & set(existing.values())
    v1 = [json.loads(line) for line in V1.read_text(encoding="utf-8").splitlines() if line.strip()]
    v1_hashes = {r["symbolic_program_hash"] for r in v1}
    v1_ids = {r["structure_id"] for r in v1}
    assert not set(mine.values()) & v1_hashes and not set(lo.STRUCTURES) & v1_ids
    assert not {s.law_family for s in lo.STRUCTURES.values()} & {r["law_family"] for r in v1}
    # the rendered templates differ as well: no context text of a new structure equals one of dataset v1
    v1_problems = {r["problem"].split("\n\n")[0] for r in v1}
    for s in lo.STRUCTURES.values():
        assert dg.context_text(s, dict(s.instances[0])) not in v1_problems


# --- mutation tests: the certificate still rejects planted defects -----------------------------------------------------------------------


def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S306"]
    assert "reversal_free" in spec_cert("S306", with_pair(spec, 1, d_attach="In an earlier run, tuned back again"))["failed"]
    assert "consequence_free" in spec_cert("S306", with_pair(spec, 0, r_attach="The laser, so that it shifts"))["failed"]
    assert "marker_free" in spec_cert("S306", with_pair(spec, 0, d_attach="An unrelated monochromator"))["failed"]
    assert "remoteness_free_d" in spec_cert("S306", with_pair(spec, 0, d_attach="The monochromator in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S302"]
    assert "d_not_on_target" in spec_cert("S302", with_pair(spec, 0, d_attach="the tank on the floor"))["failed"]
    assert "d_not_on_target" in spec_cert("S302", with_pair(spec, 1, d_attach="For a different run only"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S302", dataclasses.replace(spec, scene_refs=("floor",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s308 = SPECS["S308"]
    assert "value_hygiene" in spec_cert("S308", dataclasses.replace(s308, values=(34.0, 38.0, 90.0)))["failed"]  # t is an input
    bad_c = dataclasses.replace(s308.cancelling, spec=dataclasses.replace(s308.cancelling.spec, expr_with_q="(P0/q*Rf)*q + q"))
    assert not spec_cert("S308", dataclasses.replace(s308, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s308.conditional, spec=dataclasses.replace(s308.conditional.spec, counter_regime_value=1000.0))
    assert not spec_cert("S308", dataclasses.replace(s308, conditional=bad_k))["passed"]  # the predicate still holds
    low_k = dataclasses.replace(s308.conditional, spec=dataclasses.replace(s308.conditional.spec, values=(0.05, 0.08, 0.1)))
    assert not spec_cert("S308", dataclasses.replace(s308, conditional=low_k))["passed"]  # the light would be incoherent


def test_the_certifier_rejects_a_planted_defect_in_a_new_structure():
    s = lo.STRUCTURES["S308"]
    broken = dataclasses.replace(s, nodes=tuple(
        dataclasses.replace(n, expr="(r1**2 + r2**2 + 2*r1*r2*cos(delta))/(1 + r1**2*r2**2 + 2*r1*r2*cos(delta))")
        if n.name == "Rf" else n for n in s.nodes))  # cos(delta) in place of cos(2 delta)
    assert ct.certify(broken)["status"] == "FAILED"


# --- (g) wording rules 6-8, article agreement and the N fill grammar ----------------------------------------------------------------------

ATTACHING_P1 = set(SIDS)  # every pair-1 D says "For an earlier run only" (a changed state would otherwise read as still present)


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
    assert sid in ATTACHING_P1
    for text in (d_sentence, n_sentence):
        assert text.startswith("For an earlier run only, ") and text.count("only") == 1 and " had been " in text, text
    assert " has been " in r_sentence
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
    assert all(r.lower() in scene and r.lower() in r2.pair_sentence(p0, "D", spec.values[0], spec.unit).lower() for r in spec.scene_refs)
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


FORBIDDEN_SCENE_WORDS = r"\b(given|stated|before any|after any|anything|any water|any liquid|wherever|onto a|joined to|assume)\b"


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_has_only_physical_conditions_no_meta_or_hypothetical_wording(sid):
    assert not re.search(FORBIDDEN_SCENE_WORDS, SPECS[sid].scene_clause.lower()), SPECS[sid].scene_clause


# the N fill grammar guard of tests/v2/test_m250_n_fill_grammar.py, applied to this module
BANNED_FILLS = ("further a little", "another a little", "a further a ", "another a ", "by a further a", "a further an ")
A_BEFORE_VOWEL_NUMBER = re.compile(r"\ba (8|11|18|80)\d*\b")
A_VOWEL_WORD = re.compile(r"\ba ([aeiou]\w*)", re.IGNORECASE)
A_VOWEL_OK = re.compile(r"^(uni\w*|use\w*|usual\w*|one\w*|once|eu\w*|ubiquit\w*|ultra\w*\b)", re.IGNORECASE)
A_VOWEL_OK_EXACT = {"unit", "unity", "u", "ohm", "ohmic"}


def _problems(sentence: str) -> list[str]:
    found = [b for b in BANNED_FILLS if b in sentence.lower()]
    if A_BEFORE_VOWEL_NUMBER.search(sentence):
        found.append("a before vowel-sound number")
    for match in A_VOWEL_WORD.finditer(sentence):
        word = match.group(1).lower()
        if word in A_VOWEL_OK_EXACT or A_VOWEL_OK.match(word):
            continue
        found.append(f"a before vowel word '{match.group(0)}'")
    return found


@pytest.mark.parametrize("sid", SIDS)
def test_n_sentences_are_grammatical_and_the_guard_catches_planted_fills(sid, cells):
    spec = SPECS[sid]
    for pair in spec.pairs:
        n = r2.pair_sentence(pair, "D", None, spec.unit)
        assert not _problems(n), (sid, n, _problems(n))
        assert n[0].isupper() and n.endswith(".") and "{" not in n
    for cell in cells[sid]:
        if cell.sentence:
            assert not _problems(cell.sentence), (sid, cell.sentence)
    assert _problems("It is raised by a further a little.") and _problems("It is raised by a 85 mW.")
    # the N sentence of each pair is the D sentence with the numeral and unit replaced by the fill
    for pair in spec.pairs:
        d = r2.pair_sentence(pair, "D", spec.values[0], spec.unit)
        n = r2.pair_sentence(pair, "D", None, spec.unit)
        numeral = rv._fmt(spec.values[0])
        unit_text = "" if spec.unit in rv.UNITLESS else (rv.GLUED_UNITS.get(spec.unit) or f" {dg.display_unit(spec.unit)}")
        assert d.replace(numeral + unit_text, pair.nonnumeric_fill) == n, (d, n)
