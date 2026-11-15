"""Tests for the M250 phase 1 role specs of batch c (S46, S47, S48, S51, S52, S53, S54, S56, S57, S61, S62, S63, S64, S65, S66, S67, S71).

(a) every spec passes the v2.1 certificate; (b) every R gold at every study and held-out value equals an independent closed form written in
this file (not through the graph); (c) every C quantity leaves the answer invariant and every K regime holds at every value of every
instance, checked with closed forms and routes written here; (d) the v2.1 wording, lexicon, pair and hygiene rules; (e) the scene
clause leaves the October base problem and its gold unchanged; plus mutation tests that the certificate still rejects planted defects."""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pytest

from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250_c as m

REPO_ROOT = Path(__file__).resolve().parents[2]
V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SPECS = m.SPECS
SIDS = sorted(SPECS)
G = 9.8
COS30, COS40 = math.cos(math.radians(30)), math.cos(math.radians(40))
EV = 1.602176634e-19


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


# --- (a) certification ---------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(SPECS[sid], cert)
    spec = SPECS[sid]
    assert spec.version == "v2.1" and spec.structure_id == sid and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE


def test_the_batch_is_the_seventeen_assigned_structures_and_records_what_is_infeasible_or_absent():
    assert SIDS == sorted("S46 S47 S48 S51 S52 S53 S54 S56 S57 S61 S62 S63 S64 S65 S66 S67 S71".split())
    assert set(m.STRUCTURE_FACTORIES) == set(SIDS) == set(m.TARGET_TERMS)
    assert m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    assert set(m.NO_C) <= set(SIDS) and set(m.NO_K) <= set(SIDS)


def test_composition_targets_c_half_k_third_and_at_most_half_of_c_famous(certs):
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert len(c) / len(SIDS) >= 0.5 and len(k) / len(SIDS) >= 0.3 and len(famous) * 2 <= len(c)
    assert (len(c), len(k), famous) == (10, 7, ["S71"])
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values


# --- (b) independent closed forms of the R gold ----------------------------------------------------------------------------------

def _s52(q: float) -> float:  # heat given up by the water: dTf from the energy balance, then m c (dTw - dTf), kJ
    d_tw = 40.0 + q
    d_tf = (0.5 * 4186 * d_tw - 0.08 * 334e3) / ((0.08 + 0.5) * 4186)
    return 0.5 * 4186 * (d_tw - d_tf) / 1000


def _s64(sep: float) -> float:  # final image distance, cm
    di1 = 12 * 36 / (36 - 12)
    o2 = sep - di1
    return 9 * o2 / (o2 - 9)


# the answer with the role quantity q in the R role (display unit of q), instance 0
R_FORMS = {
    "S46": lambda q: 0.05 * G * math.sin(math.radians(30)) * (0.5 + q) / (0.6 * COS30 * 0.4) ** 2,
    "S47": lambda q: (3 * 100 / (20 + q + 9 * 20)) ** 2 * 20,
    "S48": lambda q: math.sqrt(1 / (0.1 * (40 + q) * 1e-6) - (60 / (2 * 0.1)) ** 2) / (2 * math.pi),
    "S51": lambda q: (0.5 + q) * 8.314 * 300 * (8 ** 0.4 - 1) / 0.4 / 1000,
    "S52": _s52,
    "S53": lambda q: (20 + q) / (0.2 / (0.8 * 12) + 0.05 / (0.04 * 12)),
    "S54": lambda q: 1.5 * ((10 + q) / 5) ** 2 * 1.2 ** 4,
    "S56": lambda q: (200 + q) / (0.3 * 275 / 25),
    "S57": lambda q: (2 + q) * 4186 * ((360 - 290) - 290 * math.log(360 / 290)) / 1000,
    "S61": lambda q: 3 * 600e-9 * (2 + q / 100) / 0.3e-3 * 1000,
    "S62": lambda q: (40 + q) / 2 * COS30 ** 2 * COS40 ** 2,
    "S63": lambda q: 3 / (4 * 0.6) * math.sqrt(1.4 * 8.314 * (293 + q) / 0.029),
    "S64": lambda q: _s64(45 + q),
    "S65": lambda q: math.degrees(math.asin(math.sqrt(1.5 ** 2 - 1.44 ** 2) / q)),  # q replaces the outside index n0 = 1
    "S66": lambda q: math.degrees(math.asin(2 * 650 / 4000) - math.asin(2 * q / 4000)),  # q replaces the shorter wavelength 450 nm
    "S67": lambda q: (50 + q) * (1 - 0.04) ** 2 / (1 - 0.04 ** 2),  # R = ((1.5 - 1) / (1.5 + 1))^2; series sum (1 - R)^2 / (1 - R^2)
    "S71": lambda q: 3e5 * math.sqrt(2 * (1240 / (250 - q) - 2.3) / 511e3),
}
BASE_Q = {"S65": 1.0, "S66": 450.0}  # the q at which the replace wiring gives the October answer; 0 for every add or subtract
OCTOBER_GOLD = {"S46": 2.8356481481481466, "S47": 45.0, "S48": 63.66197723675813, "S51": 4.0449585925840115,
                "S52": 34.58206896551723, "S53": 160.0, "S54": 12.4416, "S56": 60.60606060606061, "S57": 61.07623940874019,
                "S61": 12.000000000000004, "S62": 8.80236133250198, "S63": 428.6608809561108, "S64": 13.5,
                "S65": 24.83458748970158, "S66": 5.962696825934631, "S67": 46.15384615384615, "S71": 967.9805273712188}


def base_answer(sid: str) -> float:
    return R_FORMS[sid](BASE_Q.get(sid, 0.0))


@pytest.mark.parametrize("sid", SIDS)
def test_the_independent_closed_form_reproduces_the_october_gold(sid):
    assert base_answer(sid) == pytest.approx(OCTOBER_GOLD[sid], rel=1e-9)


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
    # R differs from D at every value by more than the loosest tolerance, and the R values differ from one another
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


# --- (c) invariance of C and the regime of K ---------------------------------------------------------------------------------------

def _s47_c(turns: float) -> float:  # primary turns 3 N2: the ratio is N1 / N2, then reflected resistance, currents, power
    ratio = (3 * turns) / turns
    i1 = 100 / (20 + ratio ** 2 * 20)
    return (ratio * i1) ** 2 * 20


def _s48_c(charge_uc: float) -> float:  # the characteristic polynomial scaled by Q0 has the same roots
    roots = np.roots([charge_uc * 1e-6 * 0.1, charge_uc * 1e-6 * 60, charge_uc * 1e-6 / 40e-6])
    return float(abs(roots[0].imag) / (2 * math.pi))


def _s51_c(volume_l: float) -> float:  # p1 = n R T / V1, then the adiabat p V^gamma = const to the final volume
    v1 = volume_l * 1e-3
    p1 = 0.5 * 8.314 * 300 / v1
    v2 = v1 / 8
    p2 = p1 * 8 ** 1.4
    return (p2 * v2 - p1 * v1) / 0.4 / 1000


def _s53_c(t_cold: float) -> float:
    return ((t_cold + 20) - t_cold) / (0.2 / (0.8 * 12) + 0.05 / (0.04 * 12))


def _s56_c(minutes: float) -> float:  # heat removed in time t, work needed, then power
    t = minutes * 60
    return (200 * t / (0.3 * 275 / 25)) / t


def _s62_c(area_mm2: float) -> float:  # intensity through the stack, times the area
    a = area_mm2 * 1e-6
    i0 = 40e-3 / a
    return i0 / 2 * COS30 ** 2 * COS40 ** 2 * a * 1e3


def _s63_c(p_kpa: float) -> float:  # density from the ideal-gas law, c^2 = gamma p / rho, f = 3 c / (4 L)
    p = p_kpa * 1e3
    rho = p * 0.029 / (8.314 * 293)
    return 3 * math.sqrt(1.4 * p / rho) / (4 * 0.6)


def _s64_c(height_cm: float) -> float:  # first image from the heights (parallel-ray construction, then centre ray)
    image_height = height_cm * 12 / (36 - 12)
    di1 = 36 * image_height / height_cm
    o2 = 45 - di1
    return 9 * o2 / (o2 - 9)


def _s66_c(distance_m: float) -> float:  # positions on the screen, then the angles back from them
    y1 = distance_m * math.tan(math.asin(2 * 450e-9 / 4e-6))
    y2 = distance_m * math.tan(math.asin(2 * 650e-9 / 4e-6))
    return math.degrees(math.atan(y2 / distance_m) - math.atan(y1 / distance_m))


def _s71_c(intensity: float) -> float:  # photon flux from the intensity, energy per photon back from it
    photon = 1240 / 250 * EV
    flux = intensity / photon
    energy_ev = intensity / flux / EV
    return 3e5 * math.sqrt(2 * (energy_ev - 2.3) / 511e3)


C_ROUTES = {"S47": _s47_c, "S48": _s48_c, "S51": _s51_c, "S53": _s53_c, "S56": _s56_c, "S62": _s62_c, "S63": _s63_c, "S64": _s64_c,
            "S66": _s66_c, "S71": _s71_c}


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


def _i1(i):
    return i["Vs"] / (i["Rs"] + i["a"] ** 2 * i["RL"])


def _pw(i):
    return i["Pc"] / (i["f"] * i["Tc"] / (i["Th"] - i["Tc"]))


# (quantity that the regime compares with q, direction); the predicate is "quantity < q" for "lt", "T > q" for "gt"
K_QUANTITY = {"S47": (_i1, "lt"), "S51": (lambda i: i["r"], "lt"), "S53": (lambda i: i["dT"], "lt"), "S56": (_pw, "lt"),
              "S62": (lambda i: i["P0"], "lt"), "S63": (lambda i: i["T"], "gt"), "S67": (lambda i: i["P0"], "lt")}


def _k_alt(sid: str, q: float) -> float:  # the answer the regime-ignoring misuse of q would give, instance 0 (W for S51 in kJ)
    return {"S47": lambda q: 0.0, "S51": lambda q: 0.5 * 8.314 * 300 * (q ** 0.4 - 1) / 0.4 / 1000,
            "S53": lambda q: 20 / (0.2 / (0.8 * 12)), "S56": lambda q: q, "S62": lambda q: 40.0, "S63": lambda q: 0.0,
            "S67": lambda q: 50.0}[sid](q)


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


# --- (d) wording, lexicons, pairs, hygiene ------------------------------------------------------------------------------------------

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
    assert spec.pairs[0].d_kind == "other_object_same_scene" and spec.pairs[1].d_kind in r2.D_KINDS_V21
    assert spec.pairs[1].d_kind == "other_object_same_scene" if sid == "S54" else spec.pairs[1].d_kind == "same_object_other_event"
    if sid == "S54":
        assert len(spec.pairs[1].d_kind_note) >= r2.MIN_RATIONALE
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
        if pair.pair_id == "p1" and sid != "S54":
            assert r2.prior_marker_hits(pair.d_attach)  # the same-object D is anchored in time away from the stated experiment
            assert not r2.prior_marker_hits(pair.r_attach)
        if pair.d_kind == "other_object_same_scene":
            assert not [t for t in spec.target_terms if t.lower() in pair.d_attach.lower()]
    scene_refs_ok = all(r in spec.scene_clause and r in certs[sid]["pairs"][0]["d_sentence"] for r in spec.scene_refs)
    assert spec.scene_refs and scene_refs_ok  # the D sentence of pair 0 names an object that the scene clause introduced


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


# --- (e) the scene clause leaves the October problem and its answer unchanged -----------------------------------------------------------

@pytest.fixture(scope="module")
def october():
    rows = [json.loads(line) for line in V1.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {f"{r['structure_id']}:{r['instance']}": r for r in rows}


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_is_the_only_change_to_the_base_problem_and_the_gold_is_unchanged(sid, october):
    base = october[f"{sid}:0"]
    structure, original = m.structure(sid), m.STRUCTURE_FACTORIES[sid]()
    scene = SPECS[sid].scene_clause
    prompt = rv._assemble(structure, 0, "", "after_context")
    assert prompt == base["problem"].replace("\n\n", f" {scene}\n\n", 1)
    assert prompt.replace(f" {scene}", "", 1) == rv._assemble(original, 0, "", "after_context") == base["problem"]
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(base["gold_answer"]["value"], rel=1e-12)
    assert dg.structure_hash(structure) == dg.structure_hash(original) and structure.nodes == original.nodes
    assert dg.context_text(structure, dict(structure.instances[0])).endswith(scene)
    for instance in range(len(structure.instances)):  # every instance's answer is the original graph's
        display = dict(structure.instances[instance])
        assert dg.gold_for(structure, display) == pytest.approx(dg.gold_for(original, display), rel=1e-12)
    for cell in r2.role_cells_v2(structure, SPECS[sid], 0):
        assert scene in cell.prompt and r2._prompt_numerals_ok(structure, 0, cell.prompt, cell.value)


# --- mutation tests: the certificate still rejects planted defects ---------------------------------------------------------------------

def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S57"]
    assert "reversal_free" in spec_cert("S57", with_pair(spec, 1, d_attach="In an earlier experiment, taken out again")).get(
        "failed", [])
    assert "consequence_free" in spec_cert("S57", with_pair(spec, 0, r_attach="poured into the tank, so that it is cooled"))["failed"]
    assert "marker_free" in spec_cert("S57", with_pair(spec, 0, d_attach="poured into an unrelated second tank"))["failed"]
    assert "remoteness_free_d" in spec_cert("S57", with_pair(spec, 0, d_attach="poured into the tank in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S61"]
    assert "d_not_on_target" in spec_cert("S61", with_pair(spec, 0, d_attach="screen near the slits"))["failed"]
    assert "d_not_on_target" in spec_cert("S61", with_pair(spec, 1, d_attach="in a different experiment"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S61", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s47 = SPECS["S47"]
    assert "value_hygiene" in spec_cert("S47", dataclasses.replace(s47, values=(1.5, 3.5, 20.0)))["failed"]  # 20 ohm is the load input
    bad_c = dataclasses.replace(s47.cancelling, spec=dataclasses.replace(
        s47.cancelling.spec, expr_with_q="(((a*q/q)*(Vs/(Rs + (a*q/q)**2*RL)))**2)*RL*q"))
    assert not spec_cert("S47", dataclasses.replace(s47, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s47.conditional, spec=dataclasses.replace(s47.conditional.spec, counter_regime_value=100.0))
    assert not spec_cert("S47", dataclasses.replace(s47, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s47.conditional, spec=dataclasses.replace(s47.conditional.spec, values=(1.0, 2.0, 3.0)))
    assert not spec_cert("S47", dataclasses.replace(s47, conditional=low_k))["passed"]  # the fuse would blow on instance 2
