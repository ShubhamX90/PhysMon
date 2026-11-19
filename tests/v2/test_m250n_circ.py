"""Tests for the M250 phase 2 batch circ (S263 to S272: AC and DC circuits and electronics; acoustics).

(a) every structure passes the existing certifier and has a valid gold plan whose rendered trace ends at the graph's gold, and every role
spec passes the v2.1 certificate; (b) every base gold and every R gold (study and held-out) equals an independent closed form written in this
file, not through the graph; (c) every C quantity leaves the answer invariant (independent routes written here) and every K regime holds at
every value of every instance, with the regime-ignoring answer from a closed form written here; (d) the v2.1 wording, lexicon, pair and
hygiene rules and the eight panel and judge wording rules, and article agreement over every rendered sentence; (e) the scene clause leaves the
base problem and its gold unchanged; (f) the program hash and the template of every structure are new against every existing structure
(including the other M250 batches); plus mutation tests that the spec certificate still rejects planted defects."""

from __future__ import annotations

import dataclasses
import importlib
import math
import pkgutil
import re

import pytest
from scipy.integrate import quad

import physmon.benchmark.v2 as v2pkg
from physmon.benchmark.v2 import certify as cf
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_circ as lc
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_circ as m
from physmon.benchmark.v2 import trace as tr

SPECS = m.SPECS
SIDS = sorted(SPECS)
MU0 = 1.257e-6


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
    assert SIDS == [f"S{i}" for i in range(263, 273)] == sorted(lc.STRUCTURES) == sorted(m.STRUCTURE_FACTORIES)
    assert set(m.TARGET_TERMS) == set(SIDS) == set(lc.PLANS) == set(lc.LEVELS) == set(lc.TOPICS)
    upper = [s for s in SIDS if lc.LEVELS[s] == "upper_university"]
    assert len(upper) >= 4 and set(lc.LEVELS.values()) <= {"intro_university", "upper_university"}
    multistep = [s for s in SIDS if len(lc.STRUCTURES[s].computed) >= 3]
    assert len(multistep) >= 4
    assert all(len(lc.STRUCTURES[s].instances) >= 4 for s in SIDS)
    domains = {lc.STRUCTURES[s].domain for s in SIDS}
    assert domains == {"circuits", "acoustics"}
    assert sum(lc.STRUCTURES[s].domain == "circuits" for s in SIDS) == 6 and sum(lc.STRUCTURES[s].domain == "acoustics" for s in SIDS) == 4
    assert all(lc.TOPICS[s] for s in SIDS)


@pytest.mark.parametrize("sid", SIDS)
def test_every_structure_is_solver_certified(sid):
    proof = cf.certify(lc.STRUCTURES[sid])
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]


@pytest.mark.parametrize("sid", SIDS)
def test_the_gold_plan_is_valid_and_its_rendered_trace_ends_at_the_gold(sid):
    structure, plan = lc.STRUCTURES[sid], lc.PLANS[sid]
    assert tr.validate_plan(structure, plan) == []
    for instance in range(len(structure.instances)):
        rendered = tr.render_trace(structure, plan, instance)
        gold = dg.gold_for(structure, dict(structure.instances[instance]))
        assert rendered["gold_answer"]["value"] == pytest.approx(gold, rel=1e-9)


# --- (f) uniqueness against every existing structure -------------------------------------------------------------------------------------

def _existing_structures() -> dict[str, gr.Structure]:
    found: dict[str, gr.Structure] = {}
    for info in pkgutil.iter_modules(v2pkg.__path__):
        if not info.name.startswith(("lib", "library")) or info.name == "lib_m250_circ":
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
    return set(re.findall(r"[a-z]{4,}", text))


def test_program_hashes_and_templates_are_new_against_every_existing_structure():
    existing = _existing_structures()
    assert len(existing) >= 90  # dataset v1 S01 to S95 plus the later libraries and the other M250 batches
    hashes = {k: dg.structure_hash(s) for k, s in existing.items()}
    mine = {sid: dg.structure_hash(s) for sid, s in lc.STRUCTURES.items()}
    assert len(set(mine.values())) == 10
    assert not set(mine.values()) & set(hashes.values())
    texts = {s.render.context for s in existing.values()}
    assert not {s.render.context for s in lc.STRUCTURES.values()} & texts
    laws = {s.law_family for s in existing.values()}
    assert not {s.law_family for s in lc.STRUCTURES.values()} & laws
    ids = {s.structure_id for s in existing.values()}
    assert not set(lc.STRUCTURES) & ids
    for sid, structure in lc.STRUCTURES.items():  # text overlap with the nearest existing structure stays low
        own = _tokens(structure)
        worst = max(len(own & _tokens(s)) / len(own | _tokens(s)) for s in existing.values())
        assert worst < 0.5, (sid, worst)


# --- (b) independent closed forms of the base and R golds --------------------------------------------------------------------------------------

def _s263(q: float) -> float:  # ohm metres; the box in the left gap is raised by q ohm
    return (12.0 + q) * (100.0 - 41.5) / 41.5 * math.pi * (0.30e-3) ** 2 / 4 / 1.5


def _s264(q: float) -> float:  # degrees; q ohm more series resistance
    xl, xc = 2 * math.pi * 500.0 * 25e-3, 1 / (2 * math.pi * 500.0 * 6e-6)
    return math.degrees(math.atan(abs(xl - xc) / (30.0 + q)))


def _rectified_mean(vp: float, vd: float) -> float:  # numerical mean of max(|vp sin| - 2 vd, 0) over a half cycle
    start = math.asin(2 * vd / vp)
    value, _ = quad(lambda t: max(abs(vp * math.sin(t)) - 2 * vd, 0.0), 0.0, math.pi, points=[start, math.pi - start], epsabs=0, epsrel=1e-12)
    return value / math.pi


def _s265(q: float) -> float:  # volts
    return _rectified_mean(math.sqrt(2) * (230.0 + q) / 4.0, 0.7)


def _s266(q: float) -> float:  # watts; a further load of q watts at the same voltage
    current = (480.0 + q) / 24.0
    return current ** 2 * (0.05 + (120.0 / 1200.0) ** 2 * 3.0)


def _s267(q: float) -> float:  # milliseconds; the explicit ODE solution v = V R2 / (R1 + R2) (1 - exp(-t (R1 + R2) / (R1 R2 C)))
    r1, r2_, c = 4.7e3, 6.8e3, (22.0 + q) * 1e-6
    return -math.log(1 - 0.9) * r1 * r2_ * c / (r1 + r2_) * 1e3


def _s268(q: float) -> float:  # millijoules
    inductance = MU0 * 800.0 ** 2 * math.pi * 0.015 ** 2 / 0.40
    return 0.5 * inductance * ((12.0 + q) / 4.0) ** 2 * 1e3


def _s269(q: float) -> float:  # hertz; the pipe is tuned to a fork of 440 + q hertz
    return (440.0 + q) * (math.sqrt(301.0 / 288.0) - 1.0)


def _s270(q: float) -> float:  # hertz
    f, w, v, c = 1500.0 + q, 6.0, 9.0, 343.0
    return f * (1 - (c - w) * (c - v) / (c * (c + w)))


def _s271(q: float) -> float:  # centimetres; q centimetres of rod welded on
    return (1.2 + q / 100.0) * 343.0 / math.sqrt(70000e6 / 2700.0) * 100.0


def _s272(q: float) -> float:  # seconds
    return 343.0 / 512.0 / 2 / ((1.5 + q) * 1e-2)


R_FORMS = {"S263": _s263, "S264": _s264, "S265": _s265, "S266": _s266, "S267": _s267, "S268": _s268, "S269": _s269, "S270": _s270,
           "S271": _s271, "S272": _s272}
BASE = {sid: R_FORMS[sid](0.0) for sid in SIDS}  # the base answer: q = 0 for every add wiring


@pytest.mark.parametrize("sid", SIDS)
def test_the_independent_closed_form_reproduces_the_graph_gold_of_instance_zero(sid):
    structure = lc.STRUCTURES[sid]
    for instance in structure.instances:
        assert math.isfinite(dg.gold_for(structure, dict(instance)))
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(BASE[sid], rel=1e-9)


@pytest.mark.parametrize("sid", SIDS)
def test_every_r_gold_at_every_value_equals_the_closed_form_and_every_other_gold_the_base(sid, cells):
    spec, form = SPECS[sid], R_FORMS[sid]
    seen_r = set()
    for cell in cells[sid]:
        if cell.stratum == "R":
            assert cell.gold_value == pytest.approx(form(cell.value), rel=1e-8), cell.cell_id
            seen_r.add(cell.value)
        else:
            assert cell.stratum in ("none", "N", "D", "C", "K"), cell.cell_id
            assert cell.gold_value == pytest.approx(BASE[sid], rel=1e-8), cell.cell_id
    assert seen_r == {*spec.values, *spec.heldout_values}
    golds = [form(v) for v in spec.values]
    assert all(abs(g - BASE[sid]) > rv.LOOSEST_REL_TOL * max(g, BASE[sid]) for g in golds)
    assert len({float(f"{g:.6g}") for g in golds}) == 3


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
    assert spec.version == "v2.1" == m.CERT_VERSION and spec.structure_id == sid and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE


def test_composition_c_k_and_familiarity_and_the_recorded_absences(certs):
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert len(c) >= 6 and len(k) >= 4 and len(famous) <= 3 and (len(c), len(k), famous) == (9, 5, ["S268"])
    assert set(m.K_KINDS) == set(k) and all(len(v) >= 20 for v in m.K_KINDS.values())
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values


# --- (c) invariance of C and the regime of K ---------------------------------------------------------------------------------------------------

def _s263_c(diameter_mm: float) -> float:  # arbitrary bridge-wire material; the two parts have resistances rho_w length / area
    area = math.pi * (diameter_mm * 1e-3) ** 2 / 4
    left, right = 5e-7 * 0.415 / area, 5e-7 * (1.0 - 0.415) / area
    return 12.0 * right / left * math.pi * (0.30e-3) ** 2 / 4 / 1.5


def _s264_c(volts: float) -> float:  # amplitude of the current, voltage over the resistor and the net reactive voltage, degrees
    xl, xc = 2 * math.pi * 500.0 * 25e-3, 1 / (2 * math.pi * 500.0 * 6e-6)
    current = volts / math.hypot(30.0, xl - xc)
    return math.degrees(math.atan2(current * abs(xl - xc), current * 30.0))


def _s265_c(ohms: float) -> float:  # mean load current, then the mean voltage = R times it
    vp = math.sqrt(2) * 230.0 / 4.0
    start = math.asin(1.4 / vp)
    current, _ = quad(lambda t: max(abs(vp * math.sin(t)) - 1.4, 0.0) / ohms, 0.0, math.pi, points=[start, math.pi - start], epsabs=0,
                      epsrel=1e-12)
    return ohms * current / math.pi


def _s267_c(volts: float) -> float:  # explicit final voltage, then the time to reach 0.9 of it, ms
    final = volts * 6.8e3 / (4.7e3 + 6.8e3)
    tau = 4.7e3 * 6.8e3 / (4.7e3 + 6.8e3) * 22e-6
    return -tau * math.log(1 - 0.9 * final / final) * 1e3


def _s268_c(ohms: float) -> float:  # integral of I^2 R dt of the decaying current, millijoules
    inductance = MU0 * 800.0 ** 2 * math.pi * 0.015 ** 2 / 0.40
    i0 = 12.0 / 4.0
    energy, _ = quad(lambda t: (i0 * math.exp(-ohms * t / inductance)) ** 2 * ohms, 0.0, 60 * inductance / ohms, epsabs=0, epsrel=1e-12)
    return energy * 1e3


def _s269_c(end_cm: float) -> float:  # physical length plus end correction is the tuned effective length
    c1, c2 = 331.3 * math.sqrt(288.0 / 273.15), 331.3 * math.sqrt(301.0 / 273.15)
    physical = c1 / (4 * 440.0) - end_cm * 1e-2
    return c2 / (4 * (physical + end_cm * 1e-2)) - 440.0


def _s270_c(distance: float) -> float:  # arrival times of crests 5 and 6 at the microphone
    f, w, v, c = 1500.0, 6.0, 9.0, 343.0

    def arrival(n: int) -> float:
        hit = (distance + c * n / f) / (c - w)
        return (distance + (c + w) * hit) / (c - v)

    return f - 1 / (arrival(6) - arrival(5))


def _s271_c(area_cm2: float) -> float:  # stiffness per length Y A over mass per length rho A
    area = area_cm2 * 1e-4
    speed = math.sqrt(70000e6 * area / (2700.0 * area))
    return 343.0 / (speed / (2 * 1.2)) / 2 * 100.0


def _s272_c(start_cm: float) -> float:  # instants at which the column length q - v t equals 5 lambda / 4 and then 3 lambda / 4
    lam, speed = 343.0 / 512.0, 1.5e-2
    first = (start_cm * 1e-2 - 5 * lam / 4) / speed
    second = (start_cm * 1e-2 - 3 * lam / 4) / speed
    return second - first


C_ROUTES = {"S263": _s263_c, "S264": _s264_c, "S265": _s265_c, "S267": _s267_c, "S268": _s268_c, "S269": _s269_c, "S270": _s270_c,
            "S271": _s271_c, "S272": _s272_c}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value(sid, cells):
    spec = SPECS[sid].cancelling
    for q in (*spec.spec.values, *spec.heldout_values):
        assert C_ROUTES[sid](q) == pytest.approx(BASE[sid], rel=1e-8), q
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(BASE[sid], rel=1e-8)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


def _s269_leff(i: dict) -> float:  # effective length of the pipe, m
    return 331.3 * math.sqrt(i["T1"] / i["T0"]) / (4 * i["f"])


def _s272_lam(i: dict) -> float:  # wavelength, m
    return i["c"] / i["f"]


# (does the regime hold on an instance for the K value q in its display unit?)
K_HOLDS = {
    "S264": lambda i, q: q * 1e3 > 10 * i["f"],
    "S266": lambda i, q: q < 0.8,
    "S269": lambda i, q: 600 * q * 1e-6 < i["c0"] * math.sqrt(i["T1"] / i["T0"]) / (4 * i["f"]),
    "S271": lambda i, q: 10 * q * 1e-3 < i["Lr"],
    "S272": lambda i, q: q * 1e-2 < 0.29 * _s272_lam(i),
}


def _k_alt(sid: str, q: float) -> float:  # the answer a regime-ignoring misuse of q would give, instance 0 (target display unit)
    if sid == "S264":  # q read as the frequency of the drive
        w = 2 * math.pi * q * 1e3
        return math.degrees(math.atan(abs(w * 25e-3 - 1 / (w * 6e-6)) / 30.0))
    if sid == "S266":
        return BASE["S266"] * (1 + q * q)
    if sid == "S269":  # q (micrometres) read as the length of the pipe
        return 331.3 * math.sqrt(301.0 / 273.15) / (4 * q * 1e-6) - 440.0
    if sid == "S271":  # the diameter (mm) read as the spacing, in centimetres
        return q / 10.0
    return q * 1e-2 / 1.5e-2  # S272: the radius (cm) divided by the fall speed, seconds


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_HOLDS) == {s for s in SIDS if SPECS[s].conditional is not None}


@pytest.mark.parametrize("sid", sorted(K_HOLDS))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    instances = [dict(i) for i in m.structure(sid).instances]
    assert len(instances) == 4
    for q in (*spec.spec.values, *spec.heldout_values):
        assert all(K_HOLDS[sid](i, q) for i in instances), q
    assert not any(K_HOLDS[sid](i, spec.spec.counter_regime_value) for i in instances)
    k_cells = [c for c in cells[sid] if c.stratum == "K"]
    assert len(k_cells) == 2 * len(spec.spec.values)
    for cell in k_cells:
        assert cell.gold_value == pytest.approx(BASE[sid], rel=1e-8)  # inside the regime the answer is the base answer
        assert cell.foils["out_of_regime"] == pytest.approx(_k_alt(sid, cell.value), rel=1e-8), cell.cell_id
        assert abs(cell.foils["out_of_regime"] - cell.gold_value) > rv.LOOSEST_REL_TOL * abs(cell.gold_value)
    assert not [c for c in cells[sid] if c.stratum == "K_out"] and len(spec.k_out.reason) >= r2.MIN_RATIONALE
    assert m.K_KINDS[sid]


# --- (d) wording, lexicons, pairs, hygiene and the eight wording rules --------------------------------------------------------------------------

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
        if pair.d_kind == "same_object_other_event":
            assert r2.prior_marker_hits(pair.d_attach) and not r2.prior_marker_hits(pair.r_attach)
        else:
            assert not [t for t in spec.target_terms if t.lower() in pair.d_attach.lower()]
    scene_refs_ok = all(r in spec.scene_clause and r in certs[sid]["pairs"][0]["d_sentence"] for r in spec.scene_refs)
    assert spec.scene_refs and scene_refs_ok


# the ordinary, purposeful actions on the co-present objects (rule 3)
ORDINARY = {
    "S263": "the resistance of the rheostat", "S264": "the fan", "S265": "the lamp", "S266": "the charger", "S267": "the flash unit",
    "S268": "the doorbell", "S269": "the guitar string", "S270": "the violin", "S271": "the railing", "S272": "the pond",
}
# rule 6: answer-deciding conditions stated number-free in the base text
CONDITIONS = {
    "S263": ("uniform bridge wire", "uniform material", "negligible resistance", "one steady temperature", "reads zero"),
    "S264": ("ideal sinusoidal", "ideal components", "steady sinusoidal state", "in series"),
    "S265": ("ideal switch", "no smoothing capacitor", "two diodes conduct at a time", "transformer is ideal", "no resistance"),
    "S266": ("links every turn", "core loss are negligible", "steady sinusoidal", "resistive load"),
    "S267": ("negligible internal resistance", "without leakage", "uncharged at first", "final steady value"),
    "S268": ("ideal battery", "negligible resistance", "steady value", "air-cored", "long"),
    "S269": ("do not change with temperature", "all at one temperature", "closed at one end"),
    "S270": ("still air", "constant", "sends the sound straight back", "own rest frame", "same line"),
    "S271": ("thin metal rod", "fundamental longitudinal mode", "both ends free", "clamped exactly at its middle"),
    "S272": ("closed below by the water", "constant", "fixed end correction", "steadily"),
}


@pytest.mark.parametrize("sid", SIDS)
def test_the_eight_wording_rules(sid):
    spec, structure = SPECS[sid], m.structure(sid)
    p0, p1 = spec.pairs
    context = dg.context_text(structure, dict(structure.instances[0]))
    first = r2.pair_sentence(p1, "R", spec.values[0], spec.unit)
    d_first = r2.pair_sentence(p1, "D", spec.values[0], spec.unit)
    # rules 1 and 5: the pair-1 R sentence is in the present tense and tied to the asked moment; the D sentence is anchored earlier
    assert re.match(r"(While|When|Before|At the start) ", p1.r_attach), p1.r_attach
    assert not re.search(r"\b(was|were|had|took|held|included|contained|fed|fell|received|carried|rolled|flew)\b", p1.r_attach), p1.r_attach
    assert re.search(r"\b(was|were|had|contained|included|fed|fell|rolled)\b", p1.d_attach)
    assert re.match(r"(In|On) an earlier ", p1.d_attach)
    # rule 7: an event that attaches something says it applies for one run only; any other pair-1 event names an earlier experiment
    adds = "only" in p1.frame
    assert adds == (sid in ATTACHING_P1)
    assert adds or p1.d_attach.startswith("In an earlier experiment"), p1.d_attach
    assert (", for one" in first and first.rstrip(".").endswith("only")) if adds else "only" not in first.lower()
    assert d_first.rstrip(".").endswith("only") if adds else "only" not in d_first.lower()
    # rule 2: no R sentence contradicts a stated condition, and every R sentence that changes a value is a further change
    for pair in spec.pairs:
        text = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\bset\b|\bheld at\b|\bfixed at\b|\binstead\b|\bnow\b|\bafter\b", text), text
        assert "further" in text, text
    # rule 3: the action on the co-present object is one ordinary action for that kind of object
    assert ORDINARY[sid] in p0.d_attach
    assert not re.search(r"\b\d+(\.\d+)?\s*(cm|mm|degrees|°)\b", spec.scene_clause)
    # rule 4: the co-present object is of a different type from the target and is never 'a second ...' or 'identical'
    assert not re.search(r"\b(second|another|identical|same|other|twin)\b", spec.scene_clause.lower())
    for term in spec.target_terms:
        assert term.lower() not in p0.d_attach.lower()
    # rule 6: the answer-deciding conditions stand in the base text, number-free
    for phrase in CONDITIONS[sid]:
        assert phrase in context, (sid, phrase)
    # rule 8: no D or N sentence contradicts the scene clause or the base (no state claims about the scene object)
    for pair in spec.pairs:
        for role_text in (r2.pair_sentence(pair, "D", spec.values[0], spec.unit), r2.pair_sentence(pair, "D", None, spec.unit)):
            assert not re.search(r"\b(empty|full|fills|filled|always|never|already|now|no longer|instead)\b", role_text), role_text
    assert not re.search(r"\b(empty|full|fills|filled)\b", spec.scene_clause)


ATTACHING_P1 = {"S263", "S264", "S266", "S267", "S268", "S271"}  # the pair-1 event adds or attaches something to the target


def _content(text: str, attach: str) -> set[str]:
    stripped = text.replace(attach, " ")
    return set(re.findall(r"[a-z']{3,}", stripped.lower()))


@pytest.mark.parametrize("sid", SIDS)
def test_the_two_phrasing_pairs_are_genuinely_different_wordings(sid):
    spec = SPECS[sid]
    p0, p1 = spec.pairs
    v, u = spec.values[0], spec.unit
    for role in ("R", "D"):
        a = _content(r2.pair_sentence(p0, role, v, u), p0.r_attach if role == "R" else p0.d_attach)
        b = _content(r2.pair_sentence(p1, role, v, u), p1.r_attach if role == "R" else p1.d_attach)
        assert len(a ^ b) >= 3, (sid, role, sorted(a ^ b))
        assert p0.frame != p1.frame
    r0, r1 = (r2.pair_sentence(p, "R", v, u) for p in spec.pairs)
    d0, d1 = (r2.pair_sentence(p, "D", v, u) for p in spec.pairs)
    assert r0 != r1 and d0 != d1
    for pair in spec.pairs:
        for value in (*spec.values, *spec.heldout_values):
            assert r2.pair_sentence(pair, "R", value, spec.unit) != r2.pair_sentence(pair, "D", value, spec.unit)


FORBIDDEN_SCENE_WORDS = r"\b(given|stated|before any|after any|anything|any water|any liquid|wherever|onto a|joined to|the original)\b"


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_has_only_physical_conditions_no_meta_or_hypothetical_wording(sid):
    assert not re.search(FORBIDDEN_SCENE_WORDS, SPECS[sid].scene_clause.lower()), SPECS[sid].scene_clause


def vowel_sound_number(s: str) -> bool:
    """True when the numeral reads with a vowel sound (eight, eleven, eighteen, ...)."""
    whole = s.split(".")[0].lstrip("+-")
    return whole[:1] == "8" or (whole[:2] in ("11", "18") and len(whole) in (2, 4, 5))


def article_violations(sentence: str) -> list[str]:
    return [mt.group(0) for mt in re.finditer(r"(?<![\w'])[Aa] (\d[\d.]*)", sentence) if vowel_sound_number(mt.group(1))]


def all_rendered_sentences(sid: str) -> list[str]:
    spec, structure = SPECS[sid], m.structure(sid)
    out = [c.sentence for c in r2.role_cells_v2(structure, spec, 0, include_heldout=True)]
    out += [dg.context_text(structure, dict(i)) for i in structure.instances]
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
    structure, original = m.structure(sid), lc.STRUCTURES[sid]
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
    spec = SPECS["S266"]
    assert "reversal_free" in spec_cert("S266", with_pair(spec, 1, d_attach="In an earlier run, the secondary winding also fed back"))["failed"]
    assert "consequence_free" in spec_cert("S266", with_pair(spec, 0, r_attach="the secondary winding, so that it heats"))["failed"]
    assert "marker_free" in spec_cert("S266", with_pair(spec, 0, d_attach="an unrelated charger"))["failed"]
    assert "remoteness_free_d" in spec_cert("S266", with_pair(spec, 0, d_attach="the charger in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S272"]
    assert "d_not_on_target" in spec_cert("S272", with_pair(spec, 0, d_attach="the tube"))["failed"]
    assert "d_not_on_target" in spec_cert("S272", with_pair(spec, 1, d_attach="In another tube, the water level fell"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S272", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s267 = SPECS["S267"]
    assert "value_hygiene" in spec_cert("S267", dataclasses.replace(s267, values=(6.2, 15.0, 6.8)))["failed"]  # 6.8 is the R2 input
    bad_c = dataclasses.replace(s267.cancelling, spec=dataclasses.replace(
        s267.cancelling.spec, expr_with_q="-log(1 - (p*q*R2/(R1 + R2))/(q*R2/(R1 + R2)))*Rth*C + q"))
    assert not spec_cert("S267", dataclasses.replace(s267, cancelling=bad_c))["passed"]
    s272 = SPECS["S272"]
    bad_k = dataclasses.replace(s272.conditional, spec=dataclasses.replace(s272.conditional.spec, counter_regime_value=1.0))
    assert not spec_cert("S272", dataclasses.replace(s272, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s272.conditional, spec=dataclasses.replace(s272.conditional.spec, values=(30.0, 35.0, 40.0)))
    assert not spec_cert("S272", dataclasses.replace(s272, conditional=low_k))["passed"]  # cross modes would propagate


def test_the_certifier_rejects_a_planted_defect_in_a_new_structure():
    s = lc.STRUCTURES["S265"]
    broken = dataclasses.replace(s, nodes=tuple(
        dataclasses.replace(n, expr="(2/pi)*(Vp*cos(th0) - Vd*(pi/2 - th0))") if n.name == "Vavg" else n for n in s.nodes))  # one drop only
    assert cf.certify(broken)["status"] == "FAILED"
