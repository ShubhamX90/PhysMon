"""Tests for the M250 phase 2 mechanics batch: structures S201-S210 (`lib_m250_mech`) and their v2.1 role specs (`roles_m250n_mech`).

(a) every structure is certified by the existing certifier (independent solver route, dimensions, positive control, rendered numerals) and has a
valid gold trace plan whose rendered answer equals the graph's; (b) the base gold of every instance and every R gold at every study and
held-out value equal closed forms written in this file, not read through the graph; (c) every C quantity leaves the answer invariant (checked
with routes written here) and every K regime holds at every value of every instance; (d) the v2.1 wording, lexicon, pair, hygiene and the five
panel-review wording rules; (e) the canonical program hash of every structure differs from every existing structure and every October template,
and the nearest neighbour by text is recorded; (f) the scene clause leaves the base gold unchanged."""

from __future__ import annotations

import dataclasses
import glob
import importlib
import inspect
import math
import re
from pathlib import Path

import numpy as np
import pytest
import yaml
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq, minimize_scalar

from physmon.benchmark.v2 import certify as ce
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_mech as lib
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_mech as m
from physmon.benchmark.v2 import trace as tr

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = m.SPECS
SIDS = sorted(SPECS, key=lambda s: int(s[1:]))
G = 9.8


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


# --- (a) certification, traces, composition ---------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def proofs():
    return {sid: ce.certify(lib.STRUCTURES[sid]) for sid in SIDS}


@pytest.mark.parametrize("sid", SIDS)
def test_every_structure_is_solver_certified_with_four_instances(sid, proofs):
    proof = proofs[sid]
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]
    structure = lib.STRUCTURES[sid]
    assert structure.structure_id == sid and len(structure.instances) >= 4
    assert lib.LEVELS[sid] in ("high_school", "intro_university", "upper_university") and sid in lib.TOPICS
    assert len(structure.solver_route) > 30 and structure.solver_rel_tol <= 1e-6


@pytest.mark.parametrize("sid", SIDS)
def test_gold_trace_plan_is_valid_and_renders_the_graph_answer(sid):
    structure, plan = lib.STRUCTURES[sid], lib.PLANS[sid]
    assert tr.validate_plan(structure, plan) == []
    for instance in range(len(structure.instances)):
        trace = tr.render_trace(structure, plan, instance)
        gold = dg.gold_for(structure, dict(structure.instances[instance]))
        assert trace["gold_answer"]["value"] == pytest.approx(gold, rel=1e-9)
        assert trace["steps"][-1]["kind"] == "answer"


def test_composition_levels_relations_c_k_and_familiarity():
    levels = [lib.LEVELS[s] for s in SIDS]
    upper = [s for s in SIDS if lib.LEVELS[s] == "upper_university"]
    multi = [s for s in SIDS if len(lib.STRUCTURES[s].computed) >= 3]
    assert len(upper) >= 4 and len(multi) >= 4 and set(levels) <= {"intro_university", "upper_university"}
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert (len(c), len(k), len(famous)) == (6, 3, 1) and len(famous) <= 3
    assert set(m.K_KINDS) == set(k) and all(len(v) >= 30 for v in m.K_KINDS.values())
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    assert SIDS == [f"S{n}" for n in range(201, 211)] and set(m.TARGET_TERMS) == set(SIDS)


@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: str(cert["checks"][k]["detail"])[:300] for k in cert["failed"]})
    assert r2.complete(SPECS[sid], cert)
    spec = SPECS[sid]
    assert spec.version == "v2.1" and spec.structure_id == sid and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE
    for stratum in ("cancelling", "conditional"):
        wrapped = getattr(spec, stratum)
        if wrapped is not None:
            assert len(wrapped.heldout_values) == 2 and len(wrapped.spec.values) == 3
    if spec.conditional is not None:
        assert spec.conditional.k_out.feasible is False and not spec.conditional.k_out.values


# --- (b) independent closed forms ---------------------------------------------------------------------------------------------------

def _s201(i, q=0.0):  # cm
    m_, k, b, f0, w = i["m"] + q / 1000, i["k"], i["b"], i["F0"], i["w"]
    return 100 * f0 / abs(complex(k - m_ * w ** 2, b * w))


def _s202(i, q=0.0):  # km/s
    return i["u"] * math.log((i["md"] + q + i["mf"]) / (i["md"] + q))


def _s203(i, q=0.0):  # s
    g, om, r = i["g"] + q, i["Om"], i["R"]
    return 2 * math.pi / (om * math.sqrt(1 - (g / (om ** 2 * r)) ** 2))


def _s204(i, q=0.0):  # J
    m1 = i["m1"] + q
    return 0.5 * m1 * i["m2"] / (m1 + i["m2"]) * (i["v1"] ** 2 + i["v2"] ** 2)


def _s205(i, q=0.0):  # mN
    mass, r, alpha, t = (i["m"] + q) / 1000, i["r"] / 100, i["alpha"], i["t"]
    return 1000 * mass * math.hypot((alpha * t) ** 2 * r, alpha * r)


def _s206(i, q=0.0):  # cm
    g, r = i["g"] + q, i["R"] / 100
    return i["h0"] - 100 * i["Om"] ** 2 * r ** 2 / (4 * g)


def _s207(i, q=0.0):  # m/s^2
    m1, m2, m3 = i["m1"] + q, i["m2"], i["m3"]
    return i["g"] * (m1 * (m2 + m3) - 4 * m2 * m3) / (m1 * (m2 + m3) + 4 * m2 * m3)


def _s208(i, q=0.0):  # J
    i1, i2, w1 = 0.5 * i["m1"] * (i["r1"] / 100) ** 2, i["I2"] + q, i["n1"] * math.pi / 30
    return 0.5 * i1 * i2 / (i1 + i2) * w1 ** 2


def _s209(i, q=0.0):  # rad/s, angular momentum about the rod's centre and the parallel-axis theorem
    big_m, length, mm, v, d = i["M"], i["L"], i["m"] + q, i["v"], i["d"]
    i_o = big_m * length ** 2 / 12 + mm * d ** 2
    return mm * v * d * big_m / (big_m + mm) / (i_o - (mm * d) ** 2 / (big_m + mm))


def _s210(i, q=0.0):  # s
    return 2 * i["m"] / (i["b"] + q) * math.log(1 / i["f"])


FORMS = {"S201": _s201, "S202": _s202, "S203": _s203, "S204": _s204, "S205": _s205, "S206": _s206, "S207": _s207, "S208": _s208,
         "S209": _s209, "S210": _s210}


@pytest.mark.parametrize("sid", SIDS)
def test_the_base_gold_of_every_instance_equals_the_closed_form(sid):
    structure = lib.STRUCTURES[sid]
    for instance in structure.instances:
        assert dg.gold_for(structure, dict(instance)) == pytest.approx(FORMS[sid](instance), rel=1e-9)
    assert len({round(dg.gold_for(structure, dict(i)), 6) for i in structure.instances}) == len(structure.instances)


def base_answer(sid: str) -> float:
    return FORMS[sid](dict(lib.STRUCTURES[sid].instances[0]))


@pytest.mark.parametrize("sid", SIDS)
def test_every_r_gold_at_every_value_equals_the_closed_form_and_every_other_gold_the_base(sid, cells):
    spec, form = SPECS[sid], FORMS[sid]
    instance0 = dict(lib.STRUCTURES[sid].instances[0])
    seen_r = set()
    for cell in cells[sid]:
        if cell.stratum == "R":
            assert cell.gold_value == pytest.approx(form(instance0, cell.value), rel=1e-9), cell.cell_id
            seen_r.add(cell.value)
        else:
            assert cell.stratum in ("none", "N", "D", "C", "K"), cell.cell_id
            assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9), cell.cell_id
    assert seen_r == {*spec.values, *spec.heldout_values}
    golds = [form(instance0, v) for v in spec.values]
    assert all(abs(g - base_answer(sid)) > rv.LOOSEST_REL_TOL * max(g, base_answer(sid)) for g in golds)
    assert len({round(g, 6) for g in golds}) == 3


@pytest.mark.parametrize("sid", SIDS)
def test_the_four_r_and_d_cells_per_value_exist_in_both_pairs_and_n_has_no_numeral(sid, cells):
    spec = SPECS[sid]
    r_cells = [c for c in cells[sid] if c.stratum == "R"]
    d_cells = [c for c in cells[sid] if c.stratum == "D"]
    assert len(r_cells) == len(d_cells) == 2 * (len(spec.values) + len(spec.heldout_values))
    assert {c.pair_id for c in r_cells} == {"p0", "p1"} == {c.pair_id for c in d_cells}
    n_cells = [c for c in cells[sid] if c.stratum == "N"]
    assert len(n_cells) == 2 and all(not any(ch.isdigit() for ch in c.sentence) and c.value is None for c in n_cells)
    assert [c.d_kind for c in n_cells] == [p.d_kind for p in spec.pairs] == ["other_object_same_scene", "same_object_other_event"]


# --- (c) invariance of C and the regime of K ---------------------------------------------------------------------------------------

def _c_s201(i, phase_deg):  # drive F0 cos(w t + phase): solve the cosine and sine equations of the steady state
    k, mm, b, f0, w, phi = i["k"], i["m"], i["b"], i["F0"], i["w"], math.radians(phase_deg)
    stiff = k - mm * w ** 2
    a, c = np.linalg.solve(np.array([[stiff, b * w], [-b * w, stiff]]), f0 * np.array([math.cos(phi), -math.sin(phi)]))
    return 100 * math.hypot(a, c)


def _c_s202(i, rate):  # burn time, then the quadrature of dv = u r dt / (m0 - r t)
    m0, tb = i["md"] + i["mf"], i["mf"] / rate
    value, _ = quad(lambda t: i["u"] * rate / (m0 - rate * t), 0.0, tb, epsabs=1e-13, epsrel=1e-12)
    return value


def _c_s203(i, mass_g):  # the curvature of the effective potential at its minimum, for a bead of this mass
    mass, r, om, g = mass_g / 1000, i["R"], i["Om"], i["g"]

    def potential(theta):
        return -mass * g * r * math.cos(theta) - 0.5 * mass * r ** 2 * om ** 2 * math.sin(theta) ** 2

    best = minimize_scalar(potential, bounds=(0.05, math.pi / 2), method="bounded", options={"xatol": 1e-12})
    h = 1e-4
    curvature = (potential(best.x + h) - 2 * potential(best.x) + potential(best.x - h)) / h ** 2
    return 2 * math.pi / math.sqrt(curvature / (mass * r ** 2))


def _c_s206(i, density):  # pressure balance p = p0 + rho (Om^2 r^2 / 2 - g z) with the liquid conserved
    om, g, radius = i["Om"], i["g"], i["R"] / 100

    def surface(r, z0):  # the height z at which the pressure equals the atmospheric pressure, at radius r
        return brentq(lambda z: density * (om ** 2 * r ** 2 / 2 - g * (z - z0)), z0 - 5, z0 + 5, xtol=1e-14)

    def volume_error(z0):
        volume, _ = quad(lambda r: 2 * math.pi * r * surface(r, z0), 0.0, radius, epsabs=1e-13, epsrel=1e-12)
        return volume - math.pi * radius ** 2 * i["h0"] / 100

    return 100 * brentq(volume_error, 0.0, 1.0, xtol=1e-13)


def _c_s208(i, torque):  # slipping time and heat from the relative speed, analytically in the torque
    i1, i2, w1 = 0.5 * i["m1"] * (i["r1"] / 100) ** 2, i["I2"], i["n1"] * math.pi / 30
    i_red = i1 * i2 / (i1 + i2)
    t_slip = i_red * w1 / torque
    heat, _ = quad(lambda t: torque * (w1 - torque * t / i_red), 0.0, t_slip, epsabs=1e-12, epsrel=1e-12)
    return heat


def _c_s210(i, spring):  # integrate the oscillator and find when the exact envelope has fallen to the fraction
    mm, b, k = i["m"], i["b"], spring
    gam, wd = b / (2 * mm), math.sqrt(k / mm - (b / (2 * mm)) ** 2)
    solution = solve_ivp(lambda t, y: [y[1], -(k * y[0] + b * y[1]) / mm], (0.0, 60.0), [1.0, 0.0], rtol=1e-12, atol=1e-14, dense_output=True)

    def ratio(t):
        x, v = solution.sol(t)
        return math.sqrt(x ** 2 + ((v + gam * x) / wd) ** 2) / math.sqrt(1 + (gam / wd) ** 2) - i["f"]

    return brentq(ratio, 1e-6, 59.0, xtol=1e-12)


C_ROUTES = {"S201": _c_s201, "S202": _c_s202, "S203": _c_s203, "S206": _c_s206, "S208": _c_s208, "S210": _c_s210}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value(sid, cells):
    spec = SPECS[sid].cancelling
    instance0 = dict(lib.STRUCTURES[sid].instances[0])
    for q in (*spec.spec.values, *spec.heldout_values):
        assert C_ROUTES[sid](instance0, q) == pytest.approx(base_answer(sid), rel=1e-6), q
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


def test_c_familiarity_tags_and_the_cap_on_famous_quantities():
    tags = {s: SPECS[s].cancelling.familiarity for s in C_ROUTES}
    assert tags == {"S201": "standard", "S202": "standard", "S203": "famous", "S206": "standard", "S208": "standard", "S210": "standard"}
    assert sum(t == "famous" for t in tags.values()) <= 3


def _k_quantity(sid, i):  # the quantity that the regime compares with q, in SI (m or N), for one instance
    if sid == "S201":
        return _s201(i) / 100  # the amplitude, which is the largest extension of the spring
    if sid == "S205":
        return _s205(i) / 1000  # the friction force that holds the coin
    rise_cm = 100 * i["Om"] ** 2 * (i["R"] / 100) ** 2 / (2 * i["g"])
    return (i["h0"] + rise_cm / 2) / 100  # S206: the depth of the liquid at the wall, which must stay below the rim


K_UNIT = {"S201": 1e-2, "S205": 1e-3, "S206": 1e-2}  # SI factor of the K quantity's display unit


def _k_alt(sid: str, q_display: float) -> float:  # the answer a regime-ignoring misuse of q gives, instance 0, in the target display unit
    if sid in ("S201", "S205"):
        return q_display  # the response would be capped at the limit (cm, mN)
    i = dict(lib.STRUCTURES[sid].instances[0])
    return q_display - 100 * i["Om"] ** 2 * (i["R"] / 100) ** 2 / (2 * i["g"])  # rim height minus the rise of the paraboloid, cm


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_UNIT) == {s for s in SIDS if SPECS[s].conditional is not None}


@pytest.mark.parametrize("sid", sorted(K_UNIT))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    instances = [dict(i) for i in lib.STRUCTURES[sid].instances]
    assert len(instances) == 4
    for q in (*spec.spec.values, *spec.heldout_values):
        assert all(_k_quantity(sid, i) < q * K_UNIT[sid] for i in instances), q
    assert not any(_k_quantity(sid, i) < spec.spec.counter_regime_value * K_UNIT[sid] for i in instances)
    k_cells = [c for c in cells[sid] if c.stratum == "K"]
    assert len(k_cells) == 2 * len(spec.spec.values)
    for cell in k_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9)  # inside the regime the answer is the base answer
        assert cell.foils["out_of_regime"] == pytest.approx(_k_alt(sid, cell.value), rel=1e-9), cell.cell_id
        assert abs(cell.foils["out_of_regime"] - cell.gold_value) > rv.LOOSEST_REL_TOL * abs(cell.gold_value)
    assert not [c for c in cells[sid] if c.stratum == "K_out"] and len(spec.k_out.reason) >= r2.MIN_RATIONALE


# --- (d) wording, lexicons, pairs, hygiene, the five panel rules ----------------------------------------------------------------------

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
            assert r2.prior_marker_hits(pair.d_attach) and not r2.prior_marker_hits(pair.r_attach)
        if pair.d_kind == "other_object_same_scene":
            assert not [t for t in spec.target_terms if t.lower() in pair.d_attach.lower()]
    scene_refs_ok = all(r in spec.scene_clause and r in certs[sid]["pairs"][0]["d_sentence"] for r in spec.scene_refs)
    assert spec.scene_refs and scene_refs_ok  # the D sentence of pair 0 names an object that the scene clause introduced


# Rule 4 (no second object of the target's type) and rule 3 (an ordinary action on the co-present object): the noun of the object and the type
# of the target, written out so that a change of either is a deliberate edit.
TARGET_TYPE = {"S201": "block", "S202": "rocket", "S203": "bead", "S204": "skater", "S205": "coin", "S206": "tank", "S207": "block",
               "S208": "disc", "S209": "clay", "S210": "block"}
CO_PRESENT_OBJECT = {"S201": "trolley", "S202": "tug", "S203": "crane", "S204": "coach", "S205": "dish", "S206": "goods lift",
                     "S207": "toolbox", "S208": "grinding wheel", "S209": "vase", "S210": "door"}
ORDINARY_ACTION = {"S201": "stuck to", "S202": "bolted to", "S203": "accelerates upward", "S204": "carried by", "S205": "stuck to",
                   "S206": "accelerates upward", "S207": "placed in", "S208": "fitted to", "S209": "pressed onto", "S210": "fitted to"}


@pytest.mark.parametrize("sid", SIDS)
def test_panel_rules_1_to_5(sid):
    spec = SPECS[sid]
    p0, p1 = spec.pairs
    d0 = r2.pair_sentence(p0, "D", spec.values[0], spec.unit)
    # rule 4: the co-present object is a different type from the target, and the scene clause introduces it exactly once
    obj = CO_PRESENT_OBJECT[sid]
    assert obj in spec.scene_clause and obj in d0 and TARGET_TYPE[sid] not in obj and obj not in TARGET_TYPE[sid]
    assert spec.scene_clause.count(TARGET_TYPE[sid]) == 0 or sid in ("S206",)  # the lift's clause may name the tank it stands beside
    assert not re.search(r"\b(second|another|identical|same)\b.*\b" + re.escape(TARGET_TYPE[sid]) + r"\b", spec.scene_clause.lower())
    # rule 3: an ordinary, purposeful action, and no precise measure on unrelated furniture (nothing like "tilted 11 degrees")
    assert ORDINARY_ACTION[sid] in d0 and not re.search(r"\b(tilted|pushed|moved)\b", d0)
    # rule 1 and 5: the pair-1 R sentence ties the change to the moment the question asks about and is not bare history
    r1 = r2.pair_sentence(p1, "R", spec.values[0], spec.unit)
    assert r1.endswith(p1.r_attach + ".")
    assert p1.r_attach.startswith(("before ", "shortly before ")) and not r2.prior_marker_hits(r1) and "afterwards" not in r1.lower()
    assert not re.search(r"\b(earlier|previously|previous)\b", r1.lower())
    # rule 7: the pair-1 D event, which adds or attaches something to the target, says it was there for that earlier run only
    d1 = r2.pair_sentence(p1, "D", spec.values[0], spec.unit)
    assert p1.d_attach.startswith(("for an earlier", "on an earlier")) and p1.d_attach.endswith(" only") and d1.endswith(" only.")
    # rule 8: the D and N sentences use the objects as the scene clause introduces them (standing, floating or serving), as the target of an
    # ordinary event, and never state a state that the clause or the base denies
    assert re.search(r"\b(stands|floats|serves)\b", spec.scene_clause)
    for sentence in (d0, r2.pair_sentence(p0, "D", None, spec.unit), d1, r2.pair_sentence(p1, "D", None, spec.unit)):
        assert not re.search(r"\b(now fills|is filled|fills)\b", sentence.lower()), sentence
    # rule 2: no R sentence restates or contradicts a stated base value: it states a quantity that is added, never one that is an input
    context = dg.context_text(m.structure(sid), dict(lib.STRUCTURES[sid].instances[0]))
    assert spec.relevant.op == "add" and spec.relevant.input_name in {n.name for n in lib.STRUCTURES[sid].inputs}
    for pair in spec.pairs:
        sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\b(changed|replaced|instead|now)\b", sentence.lower()), sentence
        assert not any(w in sentence.lower() for w in ("after the angle", "stated", "same value"))
    assert context.count(spec.scene_clause) == 1


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
def test_every_answer_deciding_condition_is_stated_in_the_base_text(sid):
    structure = lib.STRUCTURES[sid]
    text = dg.context_text(structure, dict(structure.instances[0])).lower()
    must = {"S201": ("transient motion has died out", "frictionless", "hooke", "no object outside the apparatus exerts a force"), "S202": ("starts at rest", "empty space", "all this fuel", "no object outside the rocket"),
            "S203": ("without friction", "rests in equilibrium", "kept constant by a motor", "air resistance is negligible"),
            "S204": ("frictionless", "hold on to each other", "due east", "due north", "treated as particles"),
            "S205": ("starts from rest", "has not slipped", "constant angular acceleration", "fixed vertical axis", "air resistance is negligible"),
            "S206": ("no liquid spills", "solid body", "constant angular speed", "incompressible", "evaporation is negligible"),
            "S207": ("without friction", "released from", "stay taut", "move only vertically", "air resistance is negligible"),
            "S208": ("frictionless axle", "grip each other", "at rest", "dissipated as heat in the coupling", "rigid"),
            "S209": ("smooth horizontal table", "sticks to the rod", "perpendicular", "treated as a point"),
            "S210": ("released from rest", "frictionless", "damping is light", "light and ideal", "air resistance is negligible")}[sid]
    for phrase in must:
        assert phrase in text, (sid, phrase)


# --- (e) uniqueness against every existing structure and every October template -----------------------------------------------------------

def existing_structures() -> dict[str, gr.Structure]:
    found: dict[str, gr.Structure] = {}
    modules = ["library", "library_b", "library_c", "lib_mechanics", "lib_electromagnetism", "lib_fluids", "lib_modern", "lib_optics",
               "lib_quantum", "lib_thermodynamics"]
    modules += [Path(p).stem for p in sorted(glob.glob(str(REPO_ROOT / "src/physmon/benchmark/v2/lib_m250_*.py"))) if "lib_m250_mech" not in p]
    for name in modules:
        module = importlib.import_module(f"physmon.benchmark.v2.{name}")
        for _, function in inspect.getmembers(module, inspect.isfunction):
            if function.__module__ != module.__name__ or function.__name__ == "all_structures" or inspect.signature(function).parameters:
                continue
            if re.match(r"^s\d+_", function.__name__):
                structure = function()
                if isinstance(structure, gr.Structure):
                    found[f"{name}:{structure.structure_id}"] = structure
        for structure in getattr(module, "STRUCTURES", {}).values():
            found[f"{name}:{structure.structure_id}"] = structure
    return found


def template_hashes() -> dict[str, str]:
    out = {}
    for path in sorted(glob.glob(str(REPO_ROOT / "data/raw/templates/**/*.yaml"), recursive=True)):
        template = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        names = [*template["parameters"], "pi"]
        out[template["template_id"]] = dg.canonical_program_hash(gr.parse_expr(str(template["governing_equation_sympy"]), names))
    return out


def test_program_hashes_and_laws_are_unique_against_every_existing_structure_and_every_template():
    existing = existing_structures()
    assert len(existing) >= 80
    old_hashes = {dg.structure_hash(s): key for key, s in existing.items()}
    old_laws = {s.law_family for s in existing.values()}
    templates = template_hashes()
    assert len(templates) >= 100
    mine = {sid: dg.structure_hash(lib.STRUCTURES[sid]) for sid in SIDS}
    assert len(set(mine.values())) == len(SIDS)  # distinct within the batch
    for sid, program in mine.items():
        assert program not in old_hashes, (sid, old_hashes.get(program))
        assert program not in set(templates.values()), sid
        assert lib.STRUCTURES[sid].law_family not in old_laws
        assert dg.structure_uuid(lib.STRUCTURES[sid])
    ids = {s.structure_id for key, s in existing.items()}
    assert not ids & set(SIDS)


def _shingles(text: str, n: int = 3) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z]+", text.lower())
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def nearest_neighbour(sid: str, existing: dict[str, gr.Structure]) -> tuple[str, float]:
    """The existing structure whose base problem text has the highest Jaccard similarity of word trigrams with this structure's."""

    mine = _shingles(dg.context_text(lib.STRUCTURES[sid], dict(lib.STRUCTURES[sid].instances[0])) + " " +
                     dg.question_text(lib.STRUCTURES[sid], dict(lib.STRUCTURES[sid].instances[0])))
    best = ("", 0.0)
    for key, other in existing.items():
        theirs = _shingles(dg.context_text(other, dict(other.instances[0])) + " " + dg.question_text(other, dict(other.instances[0])))
        score = len(mine & theirs) / max(len(mine | theirs), 1)
        if score > best[1]:
            best = (key, score)
    return best


def test_no_structure_is_a_near_duplicate_of_an_existing_one_by_text():
    existing = existing_structures()
    for sid in SIDS:
        key, score = nearest_neighbour(sid, existing)
        assert score < 0.2, (sid, key, score)  # the recorded nearest neighbour and its score; a near-duplicate would exceed 0.2


# --- (f) the scene clause leaves the base problem and its answer unchanged ---------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_is_the_only_change_to_the_base_problem_and_the_gold_is_unchanged(sid):
    structure, original = m.structure(sid), lib.STRUCTURES[sid]
    scene = SPECS[sid].scene_clause
    prompt = rv._assemble(structure, 0, "", "after_context")
    original_prompt = rv._assemble(original, 0, "", "after_context")
    assert prompt == original_prompt.replace("\n\n", f" {scene}\n\n", 1)
    assert prompt.replace(f" {scene}", "", 1) == original_prompt
    assert dg.structure_hash(structure) == dg.structure_hash(original) and structure.nodes == original.nodes
    assert dg.context_text(structure, dict(structure.instances[0])).endswith(scene)
    for instance in range(len(structure.instances)):
        display = dict(structure.instances[instance])
        assert dg.gold_for(structure, display) == pytest.approx(dg.gold_for(original, display), rel=1e-12)
    for cell in r2.role_cells_v2(structure, SPECS[sid], 0):
        assert scene in cell.prompt and r2._prompt_numerals_ok(structure, 0, cell.prompt, cell.value)


# --- mutation tests: the certificate still rejects planted defects ---------------------------------------------------------------------------

def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S207"]
    assert "reversal_free" in spec_cert("S207", with_pair(spec, 1, d_attach="In an earlier run, taken out again"))["failed"]
    assert "consequence_free" in spec_cert("S207", with_pair(spec, 0, r_attach="hung from the single block, so that it is heavier"))["failed"]
    assert "marker_free" in spec_cert("S207", with_pair(spec, 0, d_attach="placed in an unrelated toolbox"))["failed"]
    assert "remoteness_free_d" in spec_cert("S207", with_pair(spec, 0, d_attach="placed in the toolbox in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S204"]
    assert "d_not_on_target" in spec_cert("S204", with_pair(spec, 0, d_attach="the skater moving north"))["failed"]
    assert "d_not_on_target" in spec_cert("S204", with_pair(spec, 1, d_attach="On a different outing"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S204", dataclasses.replace(spec, scene_refs=("rink",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s210 = SPECS["S210"]
    assert "value_hygiene" in spec_cert("S210", dataclasses.replace(s210, values=(0.15, 0.19, 0.2)))["failed"]  # 0.2 kg/s is the damper input
    bad_c = dataclasses.replace(s210.cancelling, spec=dataclasses.replace(
        s210.cancelling.spec, expr_with_q="(2*m/b)*log(sqrt((q/2)/(q*f**2/2)))*q"))
    assert not spec_cert("S210", dataclasses.replace(s210, cancelling=bad_c))["passed"]
    s205 = SPECS["S205"]
    bad_k = dataclasses.replace(s205.conditional, spec=dataclasses.replace(s205.conditional.spec, counter_regime_value=500.0))
    assert not spec_cert("S205", dataclasses.replace(s205, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s205.conditional, spec=dataclasses.replace(s205.conditional.spec, values=(10.0, 20.0, 30.0)))
    assert not spec_cert("S205", dataclasses.replace(s205, conditional=low_k))["passed"]  # the friction needed exceeds these limits
