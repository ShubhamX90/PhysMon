"""Tests for the M250 phase 3 fluids batch (S311 to S320): the structures, their gold traces and their v2.1 role specs.

(a) every structure passes the existing certifier and has a valid gold plan whose rendered trace ends at the graph's gold; (b) every base gold
and every R gold (study and held-out) equals an independent closed form written in this file, not through the graph; (c) every C quantity
leaves the answer invariant (independent routes written here) and every K regime holds at every value of every instance; (d) the v2.1 wording,
lexicon, pair and hygiene rules and the panel wording rules, the article agreement and the N fill grammar; (e) the scene clause leaves the
base problem and its gold unchanged; (f) the program hash and the template of every structure are new against every existing structure; plus
mutation tests that the spec certificate still rejects planted defects."""

from __future__ import annotations

import dataclasses
import importlib
import math
import pkgutil
import re

import pytest
from scipy.integrate import quad
from scipy.optimize import brentq

import physmon.benchmark.v2 as v2pkg
from physmon.benchmark.v2 import certify as cf
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250p3_fluids as lf
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250p3_fluids as m
from physmon.benchmark.v2 import trace as tr

SPECS = m.SPECS
SIDS = sorted(SPECS)


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


# --- (a) structures, certification, plans ---------------------------------------------------------------------------------------------

def test_the_batch_is_ten_structures_with_the_required_composition():
    assert SIDS == [f"S{i}" for i in range(311, 321)] == sorted(lf.STRUCTURES) == sorted(m.STRUCTURE_FACTORIES)
    assert set(m.TARGET_TERMS) == set(SIDS) == set(lf.PLANS) == set(lf.LEVELS)
    levels = list(lf.LEVELS.values())
    assert levels.count("upper-university") >= 4 and set(levels) == {"introductory", "upper-university"}
    multistep = [s for s in SIDS if len(lf.STRUCTURES[s].computed) >= 3]
    assert len(multistep) >= 4 and len(multistep) == 10
    assert all(len(lf.STRUCTURES[s].instances) >= 4 for s in SIDS)
    assert all(lf.STRUCTURES[s].domain == "fluids" for s in SIDS)
    assert all(m.CERT_VERSION == "v2.1" and SPECS[s].version == "v2.1" for s in SIDS)


@pytest.mark.parametrize("sid", SIDS)
def test_every_structure_is_solver_certified(sid):
    proof = cf.certify(lf.STRUCTURES[sid])
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]


@pytest.mark.parametrize("sid", SIDS)
def test_the_gold_plan_is_valid_and_its_rendered_trace_ends_at_the_gold(sid):
    structure, plan = lf.STRUCTURES[sid], lf.PLANS[sid]
    assert tr.validate_plan(structure, plan) == []
    for instance in range(len(structure.instances)):
        rendered = tr.render_trace(structure, plan, instance)
        gold = dg.gold_for(structure, dict(structure.instances[instance]))
        assert rendered["gold_answer"]["value"] == pytest.approx(gold, rel=1e-9)


# --- (f) uniqueness against every existing structure -------------------------------------------------------------------------------------

def _existing_structures() -> dict[str, gr.Structure]:
    found: dict[str, gr.Structure] = {}
    for info in pkgutil.iter_modules(v2pkg.__path__):
        if not info.name.startswith(("lib", "library")) or info.name == "lib_m250p3_fluids":
            continue
        try:
            module = importlib.import_module(f"physmon.benchmark.v2.{info.name}")
        except Exception:  # another author's module may be mid-edit; its structures are checked by its own tests
            continue
        for attr in dir(module):
            factory = getattr(module, attr)
            if callable(factory) and re.fullmatch(r"s\d+_\w+", attr):
                try:
                    structure = factory()
                except TypeError:
                    continue
                if isinstance(structure, gr.Structure):
                    found[f"{info.name}:{structure.structure_id}"] = structure
    return found


def _tokens(structure: gr.Structure) -> set[str]:
    text = f"{structure.render.context} {structure.render.question}".lower()
    return {w for w in re.findall(r"[a-z]{4,}", text)}


def test_program_hashes_and_templates_are_new_against_every_existing_structure():
    existing = _existing_structures()
    assert len(existing) >= 90  # dataset v1 S01 to S95 plus the later libraries
    hashes = {k: dg.structure_hash(s) for k, s in existing.items()}
    mine = {sid: dg.structure_hash(s) for sid, s in lf.STRUCTURES.items()}
    assert len(set(mine.values())) == 10
    assert not set(mine.values()) & set(hashes.values())
    texts = {s.render.context for s in existing.values()}
    assert not {s.render.context for s in lf.STRUCTURES.values()} & texts
    laws = {s.law_family for s in existing.values()}
    assert not {s.law_family for s in lf.STRUCTURES.values()} & laws
    for sid, structure in lf.STRUCTURES.items():  # text overlap with the nearest existing structure stays low
        own = _tokens(structure)
        worst = max(len(own & _tokens(s)) / len(own | _tokens(s)) for s in existing.values())
        assert worst < 0.5, (sid, worst)


# --- (b) independent closed forms of the base and R golds --------------------------------------------------------------------------------

G = 9.81


def _s311(q: float) -> float:  # q in m: the force at the foot from the moment of the pressure about the hinge, kN
    d, h, w = 1.2 + q, 1.5, 2.0
    return 1000.0 * G * w * (d * h / 2 + h * h / 3) / 1000.0


def _s312(q: float) -> float:  # q in cm: the area of the hole and the spherical-cap integral, minutes
    h0, radius = 0.15 + q / 100.0, 0.30
    hole = math.pi * 0.008 ** 2 / 4
    return math.pi * (4 * radius / 3 * h0 ** 1.5 - 0.4 * h0 ** 2.5) / (hole * math.sqrt(2 * G)) / 60.0


def _s313(q: float) -> float:  # q in m: the pressure divider of the two resistances (the viscosity cancels), kPa
    k1, k2 = 1.2 / 3.0 ** 4, (0.8 + q) / 2.0 ** 4
    return 60.0 * k2 / (k1 + k2)


def _s314(q: float) -> float:  # q in m: Blasius friction factor and the Darcy form, kPa
    d, length, v, rho, eta = 0.05, 40.0 + q, 1.2, 998.0, 0.001
    friction = 0.316 * (rho * v * d / eta) ** -0.25
    return friction * length / d * rho * v * v / 2 / 1000.0


def _s315(q: float) -> float:  # q in cm: the sedimentation coefficient and the logarithm of the distances, minutes
    s = 2 * (0.4e-6) ** 2 * 900.0 / (9 * 0.001)
    omega = 2000.0 * math.pi / 30.0
    return math.log(14.0 / (8.0 - q)) / (s * omega ** 2) / 60.0


def _s316(q: float) -> float:  # q in g: the volume in the water from the buoyancy balance, cm
    a = 0.10
    mass = 880.0 * a ** 3 + (30.0 + q) / 1000.0
    return (mass - 800.0 * a ** 3) / ((1000.0 - 800.0) * a * a) * 100.0


def _s317(q: float) -> float:  # q is the new inner radius in mm: the vertical surface-tension force over g, grams
    return 2 * math.pi * (q * 1e-3) * 0.0728 * math.cos(math.radians(20.0)) / G * 1000.0


def _s318(q: float) -> float:  # q in L/s: continuity and Bernoulli, kPa
    flow = (12.0 + q) / 1000.0
    v1, v2 = flow / (math.pi * 0.05 ** 2), flow / (math.pi * 0.02 ** 2)
    return 300.0 - 998.0 * (v2 ** 2 - v1 ** 2) / 2 / 1000.0


def _s319(q: float) -> float:  # q in mm: weight equal to the quadratic drag, m/s
    r = 0.015 + q / 1000.0
    return math.sqrt(8 * 917.0 * G * r / (3 * 0.47 * 1.2))


def _s320(q: float) -> float:  # q in cm: twice the geometric mean of the depth above the hole and the height of the hole, m
    return 2 * math.sqrt((0.5 + q / 100.0) * 0.8)


# the answer with the role quantity q in the R role (display unit of q), instance 0
R_FORMS = {"S311": _s311, "S312": _s312, "S313": _s313, "S314": _s314, "S315": _s315, "S316": _s316, "S317": _s317, "S318": _s318,
           "S319": _s319, "S320": _s320}
BASE_ARG = {sid: 0.0 for sid in SIDS}
BASE_ARG["S317"] = 0.6  # replace: the base radius
BASE_GOLD = {sid: R_FORMS[sid](BASE_ARG[sid]) for sid in SIDS}


def base_answer(sid: str) -> float:
    return BASE_GOLD[sid]


@pytest.mark.parametrize("sid", SIDS)
def test_the_independent_closed_form_reproduces_the_graph_gold_of_instance_zero(sid):
    structure = lf.STRUCTURES[sid]
    for instance in structure.instances:
        assert math.isfinite(dg.gold_for(structure, dict(instance)))
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(base_answer(sid), rel=1e-9)


@pytest.mark.parametrize("sid", SIDS)
def test_every_r_gold_at_every_value_equals_the_closed_form_and_every_other_gold_the_base(sid, cells):
    spec, form = SPECS[sid], R_FORMS[sid]
    seen_r = set()
    for cell in cells[sid]:
        if cell.stratum == "R":
            assert cell.gold_value == pytest.approx(form(cell.value), rel=1e-9), cell.cell_id
            seen_r.add(cell.value)
        else:
            assert cell.stratum in ("none", "N", "D", "C", "K"), cell.cell_id
            assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9), cell.cell_id
    assert seen_r == {*spec.values, *spec.heldout_values}
    golds = [form(v) for v in spec.values]
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
    assert [c.d_kind for c in n_cells] == [p.d_kind for p in spec.pairs]


# --- (a) certification of every spec -----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(SPECS[sid], cert)
    spec = SPECS[sid]
    assert spec.version == "v2.1" and spec.structure_id == sid and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE


def test_composition_c_k_and_familiarity_and_the_recorded_absences(certs):
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert len(c) >= 6 and len(famous) <= 3 and len(k) >= 4
    assert (len(c), len(k), famous) == (7, 4, ["S320"])
    assert set(m.K_KINDS) == set(k) and all(len(v) >= 20 for v in m.K_KINDS.values())
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values


# --- (c) invariance of C and the regime of K ---------------------------------------------------------------------------------------------------

def _s311_c(p_kpa: float) -> float:  # absolute pressure on the wet face less the air on the dry face, moment about the hinge, kN
    p = p_kpa * 1e3
    moment, _ = quad(lambda s: ((p + 1000.0 * G * (1.2 + s)) - p) * 2.0 * s, 0.0, 1.5, epsabs=0.0, epsrel=1e-13)
    return moment / 1.5 / 1000.0


def _s312_c(rho: float) -> float:  # mass in the bowl over the mass outflow rate, integrated over the depth, minutes
    hole, radius = math.pi * 0.008 ** 2 / 4, 0.30
    seconds, _ = quad(lambda h: rho * math.pi * (2 * radius * h - h * h) / (rho * hole * math.sqrt(2 * G * h)), 0.0, 0.15,
                      epsabs=0.0, epsrel=1e-13)
    return seconds / 60.0


def _s313_c(p_kpa: float) -> float:  # absolute pressures through the two resistances, then the gauge pressure at the joint, kPa
    res1, res2 = 1.2 / 3.0 ** 4, 0.8 / 2.0 ** 4
    outlet = p_kpa
    inlet = p_kpa + 60.0
    joint = outlet + (inlet - outlet) * res2 / (res1 + res2)
    return joint - p_kpa


def _s314_c(p_kpa: float) -> float:  # the upstream pressure is the downstream pressure plus the drop; the drop is their difference, kPa
    return (p_kpa + _s314(0.0)) - p_kpa


def _s316_c(depth_cm: float) -> float:  # root of the net pressure force on the cube with the top face at the given depth, cm
    a, top = 0.10, depth_cm / 100.0
    weight = (880.0 * a ** 3 + 0.030) * G

    def net(x):
        p_top = 800.0 * G * top
        p_bottom = 800.0 * G * (top + a - x) + 1000.0 * G * x
        return (p_bottom - p_top) * a * a - weight

    return brentq(net, -1.0, 1.0, xtol=1e-15) * 100.0


def _s317_c(depth_mm: float) -> float:  # column above the lower end less the depth of the lower end below the dish level, grams
    r, depth = 0.6e-3, depth_mm * 1e-3
    rise = 2 * 0.0728 * math.cos(math.radians(20.0)) / (1000.0 * G * r)
    return 1000.0 * math.pi * r * r * ((depth + rise) - depth) * 1000.0


def _s320_c(rho: float) -> float:  # exit speed from the gauge pressure of the water above the hole, then the projectile, m
    speed = math.sqrt(2 * (rho * G * 0.5) / rho)
    return speed * math.sqrt(2 * 0.8 / G)


C_ROUTES = {"S311": _s311_c, "S312": _s312_c, "S313": _s313_c, "S314": _s314_c, "S316": _s316_c, "S317": _s317_c, "S320": _s320_c}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value(sid, cells):
    spec = SPECS[sid].cancelling
    for q in (*spec.spec.values, *spec.heldout_values):
        assert C_ROUTES[sid](q) == pytest.approx(base_answer(sid), rel=1e-9), q
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


def _re_s314(i: dict) -> float:
    return i["rho"] * i["v"] * i["D"] * 1e-2 / i["eta"]


def _re_s315(i: dict) -> float:  # particle Reynolds number at the bottom of the tube, where the speed is greatest
    s = 2 * (i["r"] * 1e-6) ** 2 * (i["rs"] - i["rf"]) / (9 * i["eta"])
    speed = s * (i["n"] * math.pi / 30.0) ** 2 * i["x2"] * 1e-2
    return i["rf"] * speed * 2 * i["r"] * 1e-6 / i["eta"]


def _depth_s316(i: dict) -> float:  # cm
    a = i["a"] * 1e-2
    mass = i["rc"] * a ** 3 + i["m"] * 1e-3
    return (mass - i["ro"] * a ** 3) / ((i["rw"] - i["ro"]) * a * a) * 100.0


def _p2_s318(i: dict) -> float:  # kPa
    flow = i["Q"] * 1e-3
    v1, v2 = flow / (math.pi * (i["d1"] * 1e-2) ** 2 / 4), flow / (math.pi * (i["d2"] * 1e-2) ** 2 / 4)
    return i["p1"] - i["rho"] * (v2 ** 2 - v1 ** 2) / 2 / 1000.0


# (quantity that the regime compares with q on an instance, direction): "lt" means quantity < q, "gt" means quantity > q
K_QUANTITY = {"S314": (_re_s314, "gt"), "S315": (_re_s315, "lt"), "S316": (_depth_s316, "lt"), "S318": (_p2_s318, "gt")}


def _k_alt(sid: str, q: float) -> float:  # the answer the regime-ignoring misuse of q would give, instance 0 (target display unit)
    return {"S314": lambda q: 32 * 0.001 * 40.0 * 1.2 / 0.05 ** 2 / 1000.0,  # the laminar Poiseuille drop, kPa
            "S315": lambda q: _s315(0.0) * (1 + 3 * q / 16),
            "S316": lambda q: q,
            "S318": lambda q: q}[sid](q)


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_QUANTITY) == {s for s in SIDS if SPECS[s].conditional is not None}


@pytest.mark.parametrize("sid", sorted(K_QUANTITY))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    quantity, direction = K_QUANTITY[sid]
    instances = [dict(i) for i in m.structure(sid).instances]
    assert len(instances) == 4

    def holds(i, q):
        return quantity(i) < q if direction == "lt" else quantity(i) > q

    for q in (*spec.spec.values, *spec.heldout_values):
        assert all(holds(i, q) for i in instances), q
    assert not any(holds(i, spec.spec.counter_regime_value) for i in instances)
    k_cells = [c for c in cells[sid] if c.stratum == "K"]
    assert len(k_cells) == 2 * len(spec.spec.values)
    for cell in k_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9)  # inside the regime the answer is the base answer
        assert cell.foils["out_of_regime"] == pytest.approx(_k_alt(sid, cell.value), rel=1e-9), cell.cell_id
        assert abs(cell.foils["out_of_regime"] - cell.gold_value) > rv.LOOSEST_REL_TOL * abs(cell.gold_value)
    assert not [c for c in cells[sid] if c.stratum == "K_out"] and len(spec.k_out.reason) >= r2.MIN_RATIONALE


# --- (d) wording, lexicons, pairs, hygiene and the panel rules ---------------------------------------------------------------------------

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
        assert pair.frame_matched and rec["same_frame_numeral_unit"]
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
        else:
            assert not [t for t in spec.target_terms if t.lower() in pair.d_attach.lower()]
    scene_refs_ok = all(r in spec.scene_clause and r in certs[sid]["pairs"][0]["d_sentence"] for r in spec.scene_refs)
    assert spec.scene_refs and scene_refs_ok


@pytest.mark.parametrize("sid", SIDS)
def test_the_panel_wording_rules(sid):
    spec = SPECS[sid]
    p0, p1 = spec.pairs
    # rules 1 and 5: the pair-1 R sentence ties the event to the asked moment (before it, present tense); the D sentence is anchored in
    # an earlier experiment and is in the past tense
    assert p1.r_attach.startswith("Before "), p1.r_attach
    assert re.search(r"\bhas (been|added|grown)\b", p1.r_attach) and not re.search(r"\b(was|were|had|also)\b", p1.r_attach)
    assert p1.d_attach.startswith("For an earlier experiment only, ") and re.search(r"\bhad (been|added|grown)\b", p1.d_attach)
    assert not re.search(r"\bafter\b|\bwas set\b|\bhad been set\b|\bset to\b", r2.pair_sentence(p1, "R", spec.values[0], spec.unit))
    # rule 2: no R sentence contradicts a stated condition or value
    for pair in spec.pairs:
        text = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\bset\b|\bheld at\b|\bfixed at\b|\binstead\b|\bnow\b", text), text
    # rule 3: the action on the co-present object is an ordinary one for that kind of object
    ordinary = {"S311": "the stock tank", "S312": "the watering can", "S313": "the garden hose",
                "S314": "the last marker post", "S315": "the sample bottle", "S316": "the fishing float",
                "S317": "the nozzle of the dropper", "S318": "the fountain", "S319": "the icicle", "S320": "the rain barrel"}
    assert p0.d_attach == ordinary[sid]
    assert not re.search(r"\b\d+(\.\d+)?\s*(cm|mm|degrees|°)\b", spec.scene_clause)
    # rule 4: the co-present object is never 'a second ...' or 'identical'
    assert not re.search(r"\b(second|another|identical|same|other|twin)\b", spec.scene_clause.lower())
    for term in spec.target_terms:
        assert term.lower() not in p0.d_attach.lower()


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


@pytest.mark.parametrize("sid", SIDS)
def test_target_naming_for_the_h4_extractor(sid):
    phrases, symbols = m.TARGET_TERMS[sid]
    structure = m.structure(sid)
    question = dg.question_text(structure, dict(structure.instances[0])).lower()
    assert any(p.lower() in question for p in phrases) and structure.target in symbols and len(set(symbols)) == len(symbols)


# --- (e) the scene clause leaves the base problem and its answer unchanged ------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_is_the_only_change_to_the_base_problem_and_the_gold_is_unchanged(sid):
    structure, original = m.structure(sid), lf.STRUCTURES[sid]
    scene = SPECS[sid].scene_clause
    prompt = rv._assemble(structure, 0, "", "after_context")
    plain = rv._assemble(original, 0, "", "after_context")
    assert prompt == plain.replace("\n\n", f" {scene}\n\n", 1)
    assert prompt.replace(f" {scene}", "", 1) == plain
    assert dg.structure_hash(structure) == dg.structure_hash(original) and structure.nodes == original.nodes
    assert dg.context_text(structure, dict(structure.instances[0])).endswith(scene)
    for instance in range(len(structure.instances)):
        display = dict(structure.instances[instance])
        assert dg.gold_for(structure, display) == pytest.approx(dg.gold_for(original, display), rel=1e-12)
    for cell in r2.role_cells_v2(structure, SPECS[sid], 0):
        assert scene in cell.prompt and r2._prompt_numerals_ok(structure, 0, cell.prompt, cell.value)


# --- mutation tests: the certificate still rejects planted defects ---------------------------------------------------------------------------

def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S314"]
    assert "reversal_free" in spec_cert("S314", with_pair(spec, 1, d_attach="For an earlier experiment only, the downstream tapping "
                                                                         "had been moved back"))["failed"]
    assert "consequence_free" in spec_cert("S314", with_pair(spec, 0, r_attach="the downstream tapping of the pipe, so that the "
                                                                            "distance grows"))["failed"]
    assert "marker_free" in spec_cert("S314", with_pair(spec, 0, d_attach="the last marker post of an unrelated row"))["failed"]
    assert "remoteness_free_d" in spec_cert("S314", with_pair(spec, 0, d_attach="the last marker post in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S316"]
    assert "d_not_on_target" in spec_cert("S316", with_pair(spec, 0, d_attach="the cube"))["failed"]
    assert "d_not_on_target" in spec_cert("S316", with_pair(spec, 1, d_attach="Before the cube goes into the tank, the cube "
                                                                         "had been"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S316", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s314 = SPECS["S314"]
    assert "value_hygiene" in spec_cert("S314", dataclasses.replace(s314, values=(9.0, 17.0, 40.0)))["failed"]  # 40 m is the stated distance
    bad_c = dataclasses.replace(s314.cancelling, spec=dataclasses.replace(s314.cancelling.spec, expr_with_q="q + dp"))
    assert not spec_cert("S314", dataclasses.replace(s314, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s314.conditional, spec=dataclasses.replace(s314.conditional.spec, counter_regime_value=1000.0))
    assert not spec_cert("S314", dataclasses.replace(s314, conditional=bad_k))["passed"]
    high_k = dataclasses.replace(s314.conditional, spec=dataclasses.replace(s314.conditional.spec, values=(90000.0, 100000.0, 110000.0)))
    assert not spec_cert("S314", dataclasses.replace(s314, conditional=high_k))["passed"]  # the flow would be laminar on instance 0


# --- (g) wording rules 6-8, article agreement and the N fill grammar ------------------------------------------------------------------------

def vowel_sound_number(s: str) -> bool:
    """True when the numeral reads with a vowel sound (eight, eleven, eighteen, ...)."""
    whole = s.split(".")[0].lstrip("+-")
    return whole[:1] == "8" or (whole[:2] in ("11", "18") and len(whole) in (2, 4, 5))


def article_violations(sentence: str) -> list[str]:
    return [mt.group(0) for mt in re.finditer(r"\b[Aa] (\d[\d.]*)", sentence) if vowel_sound_number(mt.group(1))]


BANNED_FILLS = ("further a little", "another a little", "a further a ", "another a ", "by a further a", "a further an ")
A_BEFORE_VOWEL_NUMBER = re.compile(r"\ba (8|11|18|80)\d*\b")
A_VOWEL_WORD = re.compile(r"\ba ([aeiou]\w*)", re.IGNORECASE)
A_VOWEL_OK = re.compile(r"^(uni\w*|use\w*|usual\w*|one\w*|once|eu\w*|ubiquit\w*|ultra\w*\b)", re.IGNORECASE)
A_VOWEL_OK_EXACT = {"unit", "unity", "u", "ohm", "ohmic"}


def fill_problems(sentence: str) -> list[str]:
    """The grammar guard of `test_m250_n_fill_grammar.py`, applied to this module's sentences."""
    low = sentence.lower()
    found = [b for b in BANNED_FILLS if b in low]
    if A_BEFORE_VOWEL_NUMBER.search(sentence):
        found.append("a before vowel-sound number")
    for match in A_VOWEL_WORD.finditer(sentence):
        word = match.group(1).lower()
        if word in A_VOWEL_OK_EXACT or A_VOWEL_OK.match(word):
            continue
        found.append(f"a before vowel word '{match.group(0)}'")
    return found


def all_rendered_sentences(sid: str) -> list[str]:
    spec, structure = SPECS[sid], m.structure(sid)
    out = [c.sentence for c in r2.role_cells_v2(structure, spec, 0, include_heldout=True)]
    for pair in spec.pairs:
        out.append(r2.pair_sentence(pair, "D", None, spec.unit))
    if spec.cancelling is not None:
        sub = spec.cancelling.spec
        out += [rv._sentence(sub.frame, v, sub.unit, p.relation, sub.nonnumeric_fill)
                for v in (*sub.values, *spec.cancelling.heldout_values) for p in sub.phrasings]
        out += [rv._sentence(sub.frame, None, sub.unit, p.relation, sub.nonnumeric_fill) for p in sub.phrasings]
    if spec.conditional is not None:
        sub = spec.conditional.spec
        vals = (*sub.values, *spec.conditional.heldout_values, *spec.conditional.k_out.values)
        out += [rv._sentence(sub.frame, v, sub.unit, p.relation, sub.nonnumeric_fill) for v in vals for p in sub.phrasings]
        out += [rv._sentence(sub.frame, None, sub.unit, p.relation, sub.nonnumeric_fill) for p in sub.phrasings]
    return [s for s in out if s]


def test_article_checker_catches_planted_violations():
    assert article_violations("A 18 V cell was added.") == ["A 18"]
    assert article_violations("Before it, a 8.5 cm rod and a 11 kg mass and a 85 N force.") == ["a 8.5", "a 11", "a 85"]
    assert not article_violations("A 16 V cell, a 0.8 kg mass, a 118 N force, a 3.5 V cell and an 18 V cell.")
    assert fill_problems("The tube is raised by a further a few centimetres.")


@pytest.mark.parametrize("sid", SIDS)
def test_no_rendered_sentence_has_a_wrong_article_or_an_ungrammatical_fill(sid):
    spec = SPECS[sid]
    for sentence in all_rendered_sentences(sid):
        assert not article_violations(sentence), (sid, sentence)
        assert not fill_problems(sentence), (sid, sentence, fill_problems(sentence))
        assert not re.search(r"\b(\w+) \1\b", sentence.lower()), (sid, sentence)  # no doubled word such as 'weight weight'
    for pair in spec.pairs:
        n = r2.pair_sentence(pair, "D", None, spec.unit)
        assert n[0].isupper() and n.endswith("."), (sid, n)
        assert not any(ch.isdigit() for ch in n)
    for kind in (spec.cancelling, spec.conditional):
        if kind is not None:
            for phrasing in kind.spec.phrasings:
                text = rv._sentence(kind.spec.frame, None, kind.spec.unit, phrasing.relation, kind.spec.nonnumeric_fill)
                assert text[0].isupper() and text.endswith(".") and not any(ch.isdigit() for ch in text), text


@pytest.mark.parametrize("sid", SIDS)
def test_rule_7_pair_1_d_opens_with_for_an_earlier_experiment_only_and_r_has_no_only_or_also(sid):
    spec = SPECS[sid]
    p1 = spec.pairs[1]
    d_sentence = r2.pair_sentence(p1, "D", spec.values[0], spec.unit)
    n_sentence = r2.pair_sentence(p1, "D", None, spec.unit)
    r_sentence = r2.pair_sentence(p1, "R", spec.values[0], spec.unit)
    for text in (d_sentence, n_sentence):
        assert text.startswith("For an earlier experiment only, ") and text.lower().count("only") == 1, text
        assert "also" not in text.lower()
    assert "only" not in r_sentence.lower() and "also" not in r_sentence.lower() and r_sentence.startswith("Before ")
    assert " has " in r_sentence and " had " in d_sentence  # the perfect tense of R against the past perfect of D


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
def test_r_and_d_sentences_differ_within_each_pair_and_across_pairs(sid):
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
    text = lf.STRUCTURES[sid].render.context.lower()
    assert not re.search(r"\b(given|stated|the original|for this problem|assume)\b", text), text
    assert "{g}" not in text or "take g = {g}" in text  # every constant the solver uses is stated with its value
