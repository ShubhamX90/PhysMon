"""Tests for the M250 phase-1 role specs, batch b (S24 S25 S28 S29 S31 S32 S33 S34 S35 S36 S37 S38 S41 S42 S43 S44 S45).

(a) every spec certifies under the v2.1 certifier; (b) every R gold, at every study and held-out value, equals a closed form written
here from the physics and not read from the graph; (c) every C and K quantity is invariant, checked with a physical chain or a
regime margin written here; (d) the v2.1 wording, lexicon, reversal and hygiene rules hold, and planted violations are caught; (e) the
scene clause leaves the base gold and graph unchanged and the no-cue prompt is the October problem plus the clause.
"""

from __future__ import annotations

import dataclasses
import json
import math
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m250_b as m  # noqa: E402

V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SIDS = sorted(m.SPECS)
G = 9.8
RGAS = 8.314


def sd(sid: str) -> r2.RoleSpecV2:
    return m.SPECS[sid]


@pytest.fixture(scope="module")
def certs():
    return {sid: r2.certify_v2(m.structure(sid), m.SPECS[sid]) for sid in SIDS}


@pytest.fixture(scope="module")
def v1_rows():
    rows = {}
    for line in V1.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["instance"] == 0:
            rows[r["structure_id"]] = r
    return rows


def spec_cert(sid: str, spec: r2.RoleSpecV2) -> dict:
    return r2.certify_v2(m.structure(sid), spec)


def with_pair(spec: r2.RoleSpecV2, index: int, **changes) -> r2.RoleSpecV2:
    pairs = list(spec.pairs)
    pairs[index] = dataclasses.replace(pairs[index], **changes)
    return dataclasses.replace(spec, pairs=tuple(pairs))


# --- (a) certification -------------------------------------------------------------------------------------------------------------

def test_the_batch_is_the_seventeen_assigned_structures_and_nothing_is_infeasible():
    assert SIDS == sorted("S24 S25 S28 S29 S31 S32 S33 S34 S35 S36 S37 S38 S41 S42 S43 S44 S45".split())
    assert set(m.STRUCTURE_FACTORIES) == set(m.SPECS) == set(m.TARGET_TERMS) == set(m.SCENES)
    for sid, reason in m.INFEASIBLE.items():
        assert sid not in m.SPECS and len(reason) >= r2.MIN_RATIONALE
    assert set(m.NO_C) == {s for s in SIDS if sd(s).cancelling is None}
    assert set(m.NO_K) == {s for s in SIDS if sd(s).conditional is None}
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in (*m.NO_C.values(), *m.NO_K.values()))


@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(sd(sid), cert)
    spec = sd(sid)
    assert spec.version == "v2.1" and spec.scene_clause and len(spec.values) == 3 and len(spec.heldout_values) == 2


@pytest.mark.parametrize("sid", SIDS)
def test_c_and_k_are_present_exactly_where_the_tests_check_them(sid):
    assert (sd(sid).cancelling is not None) == (sid in CHAINS)  # every C has a physical chain below
    assert (sd(sid).conditional is not None) == (sid in K_THRESHOLD)  # every K has a regime threshold below


def test_composition_of_the_batch():
    n_c = sum(sd(s).cancelling is not None for s in SIDS)
    n_k = sum(sd(s).conditional is not None for s in SIDS)
    famous = sum(sd(s).cancelling is not None and sd(s).cancelling.familiarity == "famous" for s in SIDS)
    assert n_c >= 0.5 * len(SIDS) and n_k >= 0.3 * len(SIDS)
    assert famous <= n_c / 2
    assert (n_c, n_k, famous) == (11, 7, 3)
    kinds = {s: (sd(s).pairs[0].d_kind, sd(s).pairs[1].d_kind) for s in SIDS}
    assert all(k == ("other_object_same_scene", "same_object_other_event") for k in kinds.values())


# --- (b) every R gold against a closed form written here ----------------------------------------------------------------------------

def _s37(q: float = 0.0) -> float:
    r = (6371.0 + 400.0 + q) * 1e3
    return 2 * math.pi * math.sqrt(r ** 3 / (G * (6371e3) ** 2)) / 60


def _s38(q: float = 0.0) -> float:
    theta = math.radians(62 - q)
    f_wall = (12 / 2 + 70 * 0.6) * G / math.tan(theta)
    return math.hypot(f_wall, (12 + 70) * G)


def _s43(q: float = 0.0) -> float:
    c = 100 / (1 - (3 / 6) * (1 - 1 / 4))  # pF, series layers: 3 mm of kappa = 4 and 3 mm of vacuum
    return (c - 100) * (12 + q) / 1000


def _s45(q: float = 0.0) -> float:
    mass, charge, field = 1e-4, 2e-3, 0.8
    speed = math.sqrt(2 * charge * (2.5 + q) / mass)
    return 100 * mass * speed / (charge * field)


CLOSED = {  # the answer of instance 0 with the role quantity q (display unit of q), from the physics
    "S24": lambda q: 800 * (1 - 300 / (600 + q)),
    "S25": lambda q: 0.5 * 0.250 * (3 + q) ** 2 * 1000,
    "S28": lambda q: 2 * 15 / (2 + q),
    "S29": lambda q: 40 * 3 * math.cos(math.radians(30 + q)),
    "S31": lambda q: 15 * math.sqrt(2 * (20 + q) / G),
    "S32": lambda q: (0.5 * 800 * 0.1 ** 2) / (0.25 * (0.5 + q) * G),
    "S33": lambda q: (0.150 + q / 1000) * (20 + 0.6 * 20) / 0.008,
    "S34": lambda q: 6 ** 2 / (2 * (5 / 7) * G * math.sin(math.radians(25 + q))),
    "S35": lambda q: 2 * math.pi * math.sqrt((1.2 + q) * math.cos(math.radians(30)) / G),
    "S36": lambda q: 2 * math.pi * math.sqrt((1.2 ** 2 / 12 + (0.3 - q / 100) ** 2) / (G * (0.3 - q / 100))),
    "S37": _s37,
    "S38": _s38,
    "S41": lambda q: 80 * (4 / 5) * (30 / (60 + q)) ** 2,
    "S42": lambda q: (12 + q) ** 2 / (2 * 3 ** 2),
    "S43": _s43,
    "S44": lambda q: 0.025 * G / (((350 + q) / 1000) * 0.5),
    "S45": _s45,
}


def test_the_closed_forms_reproduce_the_october_base_answers(v1_rows):
    for sid in SIDS:
        assert CLOSED[sid](0.0) == pytest.approx(v1_rows[sid]["gold_answer"]["value"], rel=1e-9), sid
        assert v1_rows[sid]["gold_answer"]["unit"] == m.structure(sid).render.target_unit


@pytest.mark.parametrize("sid", SIDS)
def test_every_r_gold_at_every_value_matches_the_closed_form(sid):
    spec, structure = sd(sid), m.structure(sid)
    cells = r2.role_cells_v2(structure, spec, 0, include_heldout=True)
    values = [*spec.values, *spec.heldout_values]
    r_cells = [c for c in cells if c.stratum == "R"]
    assert len(r_cells) == 2 * len(values)
    for c in r_cells:
        assert c.gold_value == pytest.approx(CLOSED[sid](c.value), rel=1e-9), (c.cell_id, c.value)
    base = CLOSED[sid](0.0)
    for c in cells:
        if c.stratum in ("D", "N", "none", "C", "K"):
            assert c.gold_value == pytest.approx(base, rel=1e-9), c.cell_id
    # R answers differ from the base answer and from each other by more than the loosest tolerance
    answers = [CLOSED[sid](v) for v in spec.values]
    assert all(abs(a - base) > rv.LOOSEST_REL_TOL * max(abs(a), abs(base)) for a in answers)
    assert all(abs(a - b) > rv.LOOSEST_REL_TOL * max(abs(a), abs(b)) for i, a in enumerate(answers) for b in answers[i + 1:])


# --- (c) C and K invariance, checked with physics written here ---------------------------------------------------------------------------


def chain_s24(i, q):  # q mol of ideal gas on a Carnot cycle: the heat Qh fixes the volume ratio
    ln_ratio = i["Qh"] * 1e3 / (q * RGAS * i["Th"])
    return (q * RGAS * i["Th"] * ln_ratio - q * RGAS * i["Tc"] * ln_ratio) / 1e3


def chain_s25(i, q):  # steady ramp over q ms: emf = L I / T, average current I / 2, energy = emf x I/2 x T
    emf = i["Lind"] * 1e-3 * i["Icur"] / (q * 1e-3)
    return emf * (i["Icur"] / 2) * (q * 1e-3) * 1000


def chain_s29(i, q):  # pulled for q seconds at constant speed: work over time
    work = i["F"] * math.cos(math.radians(i["theta"])) * (i["v"] * q)
    return work / q


def chain_s31(i, q):  # a stone of mass q: acceleration is weight over mass
    accel = q * i["g"] / q
    return i["v"] * math.sqrt(2 * i["h"] / accel)


def chain_s34(i, q):  # radius q cm: I = (2/5) m R^2 and rolling without slipping
    radius = q / 100
    inertia_over_mass = 0.4 * radius ** 2
    accel = i["g"] * math.sin(math.radians(i["theta"])) / (1 + inertia_over_mass / radius ** 2)
    return i["v0"] ** 2 / (2 * accel)


def chain_s35(i, q):  # bob mass q: T cos(theta) = m g, T sin(theta) = m v^2 / r
    tension = q * i["g"] / math.cos(math.radians(i["theta"]))
    r = i["L"] * math.sin(math.radians(i["theta"]))
    speed = math.sqrt(tension * math.sin(math.radians(i["theta"])) / q * r)
    return 2 * math.pi * r / speed


def chain_s36(i, q):  # rod mass q: I = m (L^2/12 + d^2), restoring torque m g d
    inertia = q * (i["L"] ** 2 / 12 + i["d"] ** 2)
    omega = math.sqrt(q * i["g"] * i["d"] / inertia)
    return 2 * math.pi / omega


def chain_s37(i, q):  # satellite mass q: gravity m g R^2 / r^2 supplies m v^2 / r
    r = (i["R"] + i["h"]) * 1e3
    force = q * i["g"] * (i["R"] * 1e3) ** 2 / r ** 2
    speed = math.sqrt(force / q * r)
    return 2 * math.pi * r / speed / 60


def chain_s38(i, q):  # ladder length q: torques about the foot
    th = math.radians(i["theta"])
    f_wall = (i["m"] * i["g"] * (q / 2) + i["M"] * i["g"] * i["x"] * q) * math.cos(th) / (q * math.sin(th))
    return math.hypot(f_wall, (i["m"] + i["M"]) * i["g"])


def chain_s41(i, q):  # sphere radius q cm: the charge divides in proportion to the radius (capacitance)
    total = i["rq"] - 1.0  # units of the smaller charge, opposite signs
    each = total * q / (q + q)
    return i["F0"] * each ** 2 / i["rq"] * (i["d0"] / i["d1"]) ** 2


def chain_s42(i, q):  # original length q cm at constant volume: resistivity from R0 with an arbitrary section
    area0, length0 = 1e-6, q / 100
    rho = i["R0"] * area0 / length0
    length1 = i["k"] * length0
    area1 = area0 * length0 / length1
    return i["V"] ** 2 / (rho * length1 / area1)


CHAINS = {"S24": chain_s24, "S25": chain_s25, "S29": chain_s29, "S31": chain_s31, "S34": chain_s34, "S35": chain_s35,
          "S36": chain_s36, "S37": chain_s37, "S38": chain_s38, "S41": chain_s41, "S42": chain_s42}


@pytest.mark.parametrize("sid", sorted(CHAINS))
def test_c_quantity_cancels_in_a_physical_chain_at_every_value_and_instance(sid):
    spec, structure = sd(sid), m.structure(sid)
    assert spec.cancelling is not None
    for inst in structure.instances:
        target = dg.gold_for(structure, dict(inst))
        for q in (*spec.cancelling.spec.values, *spec.cancelling.heldout_values):
            assert CHAINS[sid](inst, q) == pytest.approx(target, rel=1e-9), (sid, inst, q)
    # the instance-0 base answer of the chain is the closed form (the same physics, written twice)
    assert CHAINS[sid](dict(structure.instances[0]), spec.cancelling.spec.values[0]) == pytest.approx(CLOSED[sid](0.0), rel=1e-9)


@pytest.mark.parametrize("sid", sorted(CHAINS))
def test_c_wrong_law_is_separated_and_the_spec_lists_the_intermediate_relations(sid, certs):
    c = certs[sid]["checks"]
    assert c["c_heldout_two_certified"]["ok"] and c["c_familiarity_tag"]["ok"]
    spec = sd(sid).cancelling
    assert len(spec.spec.intermediate_relations) >= 2 and spec.spec.wrong_law and "q" in spec.spec.wrong_law
    assert "q" in spec.spec.expr_with_q  # present before it cancels
    numeric = certs[sid]["numeric"]["checks"]["cancelling"]
    assert numeric["derivative_zero"] and numeric["numeric_invariance"] and numeric["wrong_law_separated_at_2_of_3"]


# K: the regime holds when the K value is on the stated side of a threshold written here from the physics.
K_THRESHOLD = {
    "S25": lambda i: i["Icur"],  # core linear up to q A: needs q above the working current
    "S28": lambda i: 2 * i["v"],  # the car's speed at the catch-up instant a t = 2 v
    "S29": lambda i: i["F"],  # breaking strength above the tension
    "S32": lambda i: i["x"],  # elastic limit above the compression (cm)
    "S34": lambda i: 2 * math.tan(math.radians(i["theta"])) / 7,  # f/N needed to keep rolling
    "S38": lambda i: ((i["m"] / 2 + i["M"] * i["x"]) / math.tan(math.radians(i["theta"]))) / (i["m"] + i["M"]),  # f/N needed
    "S44": lambda i: i["L"],  # field wider than the rod (cm)
}


@pytest.mark.parametrize("sid", sorted(K_THRESHOLD))
def test_k_regime_holds_at_every_value_and_instance_and_fails_at_the_counter_regime_value(sid):
    spec, structure = sd(sid), m.structure(sid)
    assert spec.conditional is not None
    k = spec.conditional
    for inst in structure.instances:
        threshold = K_THRESHOLD[sid](dict(inst))
        assert all(v > threshold for v in (*k.spec.values, *k.heldout_values)), (sid, dict(inst), threshold)
        assert k.spec.counter_regime_value < threshold, (sid, dict(inst), threshold)
    # the regime fails at the K_out values exactly where K_out is feasible
    assert k.k_out.feasible == (sid == "S28")
    assert (len(k.k_out.values) == 2) == k.k_out.feasible


def _catch_up_time(a: float, v: float, top: float) -> float:
    """Time at which a car that accelerates at a up to a top speed draws level with a truck at v, by bracketing (independent)."""

    def gap(t: float) -> float:
        t_top = top / a
        car = a * t * t / 2 if t <= t_top else top * top / (2 * a) + top * (t - t_top)
        return car - v * t

    lo, hi = 1e-9, 1.0
    while gap(hi) <= 0:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if gap(mid) <= 0 else (lo, mid)
    return (lo + hi) / 2


def test_s28_top_speed_is_irrelevant_in_regime_and_k_out_answers_follow_from_the_cap(certs):
    spec = sd("S28")
    for inst in m.structure("S28").instances:
        a, v = inst["a"], inst["v"]
        for top in (*spec.conditional.spec.values, *spec.conditional.heldout_values):
            assert _catch_up_time(a, v, top) == pytest.approx(2 * v / a, rel=1e-6)
        for top in spec.conditional.k_out.values:
            assert _catch_up_time(a, v, top) == pytest.approx(top ** 2 / (2 * a * (top - v)), rel=1e-6)
            assert abs(_catch_up_time(a, v, top) - 2 * v / a) > 0.01 * 2 * v / a
    cells = [c for c in r2.role_cells_v2(m.structure("S28"), spec, 0) if c.stratum == "K_out"]
    assert len(cells) == 4 and {c.value for c in cells} == {17.0, 21.0}
    for c in cells:
        assert c.gold_value == pytest.approx(_catch_up_time(2.0, 15.0, c.value), rel=1e-6)
    assert certs["S28"]["checks"]["k_out_predicate_false_and_answer_moves"]["ok"]


@pytest.mark.parametrize("sid", sorted(K_THRESHOLD))
def test_k_out_feasibility_is_judged_with_a_reason(sid, certs):
    k = sd(sid).conditional
    assert len(k.k_out.reason) >= r2.MIN_RATIONALE and certs[sid]["checks"]["k_out_judged"]["ok"]
    if not k.k_out.feasible:
        assert not k.k_out.values and certs[sid]["checks"]["k_out_infeasible_has_no_values"]["ok"]
    assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"]


def test_s34_and_s38_k_thresholds_agree_with_a_force_balance():
    # rolling needs f = (2/7) m g sin(theta) = mu N with N = m g cos(theta); the ladder needs f = Fwall with N = (m + M) g
    th = math.radians(25)
    a = 5 * G * math.sin(th) / 7
    assert (G * math.sin(th) - a) / (G * math.cos(th)) == pytest.approx(2 * math.tan(th) / 7)
    inst = dict(m.structure("S38").instances[0])
    f_wall = (inst["m"] / 2 + inst["M"] * inst["x"]) * G / math.tan(math.radians(inst["theta"]))
    assert f_wall / ((inst["m"] + inst["M"]) * G) == pytest.approx(K_THRESHOLD["S38"](inst))


# --- (d) wording, lexicons, reversal, hygiene --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_sentence_is_consequence_marker_free_and_reversal_free(sid):
    spec, structure = sd(sid), m.structure(sid)
    for cell in r2.role_cells_v2(structure, spec, 0, include_heldout=True):
        assert not r2.consequence_hits(cell.sentence), cell.sentence
        assert not r2.marker_hits(cell.sentence), cell.sentence
        assert cell.consequence_free in (True, None) and cell.marker_free in (True, None)
        if cell.stratum in ("D", "N"):
            assert not r2.reversal_hits(cell.sentence), cell.sentence
    assert not r2.consequence_hits(spec.scene_clause) and not r2.marker_hits(spec.scene_clause)


@pytest.mark.parametrize("sid", SIDS)
def test_pair_rules(sid, certs):
    spec = sd(sid)
    assert [p.pair_id for p in spec.pairs] == ["p0", "p1"]
    assert spec.pairs[0].d_kind == "other_object_same_scene" and spec.pairs[1].d_kind == "same_object_other_event"
    for pair, rec in zip(spec.pairs, certs[sid]["pairs"], strict=True):
        assert pair.frame_matched and rec["same_frame_numeral_unit"]  # one frame, numeral and unit; only the attachment differs
        assert abs(rec["word_counts"][0] - rec["word_counts"][1]) <= r2.MAX_WORD_DIFF
        assert rec["token_difference"]["removed"] or rec["token_difference"]["added"]  # the attachment differs
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        d_sentence = r2.pair_sentence(pair, "D", spec.values[0], spec.unit)
        assert r_sentence.replace(pair.r_attach, "@") == d_sentence.replace(pair.d_attach, "@")
        assert pair.conditions_preserved and rec["conditions_in_base_text"] and len(pair.d_rationale) >= r2.MIN_RATIONALE
        n_sentence = r2.pair_sentence(pair, "D", None, spec.unit)
        assert not re.search(r"\d", n_sentence) and n_sentence.count(pair.d_attach) == 1
        for text in (r_sentence, d_sentence, n_sentence):
            assert text[0].isupper() and text.rstrip().endswith(".")
    p0, p1 = spec.pairs
    assert all(r in r2.pair_sentence(p0, "D", spec.values[0], spec.unit) for r in spec.scene_refs)
    assert not any(t.lower() in p0.d_attach.lower() for t in spec.target_terms)  # a co-present D does not name the target
    assert r2.prior_marker_hits(p1.d_attach)  # the other event is anchored in the past
    assert not r2.prior_marker_hits(p1.r_attach)


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_has_no_numeral_and_closes_the_base_context(sid):
    spec, structure = sd(sid), m.structure(sid)
    context = dg.context_text(structure, dict(structure.instances[0]))
    assert not re.search(r"\d", spec.scene_clause) and spec.scene_clause.endswith(".")
    assert context.count(spec.scene_clause) == 1 and context.endswith(spec.scene_clause)
    assert len(spec.scene_object_rationale) >= r2.MIN_RATIONALE and spec.scene_refs


@pytest.mark.parametrize("sid", SIDS)
def test_study_and_heldout_values_pass_hygiene_and_prompts_carry_one_numeral(sid, certs):
    hygiene = certs[sid]["hygiene"]
    for name, items in hygiene.items():
        for h in items:
            assert h["ok"] and not h["equals_input"], (sid, name, h)
            assert h["digit_overlap_with_inputs"] <= r2.MAX_DIGIT_OVERLAP and h["digit_overlap_with_gold"] <= r2.MAX_DIGIT_OVERLAP
    structure = m.structure(sid)
    for cell in r2.role_cells_v2(structure, sd(sid), 0):
        assert r2._prompt_numerals_ok(structure, 0, cell.prompt, cell.value), cell.cell_id
        if cell.stratum == "N":
            assert not any(ch.isdigit() for ch in cell.sentence) and cell.value is None
    spec = sd(sid)
    assert not set(spec.values) & set(spec.heldout_values)
    for quantity in (spec.cancelling, spec.conditional):
        if quantity is not None:
            held = quantity.heldout_values
            assert len(held) == 2 and not set(held) & set(quantity.spec.values)


@pytest.mark.parametrize("sid", SIDS)
def test_target_naming_is_present(sid):
    phrases, symbols = m.TARGET_TERMS[sid]
    assert phrases and symbols and all(isinstance(x, str) and x for x in (*phrases, *symbols))
    question = dg.question_text(m.structure(sid), dict(m.structure(sid).instances[0])).lower()
    assert any(p.lower() in question for p in phrases), (sid, phrases, question)


def test_planted_violations_fail_the_certificate():
    s24 = sd("S24")
    assert "consequence_free" in spec_cert("S24", with_pair(s24, 1, r_attach="Afterwards, so the work changes"))["failed"]
    assert "marker_free" in spec_cert("S24", with_pair(s24, 0, d_attach="the second engine, which is unrelated"))["failed"]
    assert "reversal_free" in spec_cert("S24", with_pair(s24, 1, d_attach="In an earlier experiment, and cooled back"))["failed"]
    assert "d_not_on_target" in spec_cert("S24", with_pair(s24, 0, d_attach="the engine"))["failed"]  # the co-present D names the target
    assert "d_not_on_target" in spec_cert("S24", with_pair(s24, 1, d_attach="At the same time"))["failed"]  # no past anchor
    assert "word_count_ok" in spec_cert("S24", with_pair(s24, 0, d_attach="the second engine standing beside the first one in "
                                                                          "the corner of the hall"))["failed"]
    assert "attach_has_no_digit" in spec_cert("S24", with_pair(s24, 0, d_attach="the second engine number 2"))["failed"]
    assert "d_rationale_ok" in spec_cert("S24", with_pair(s24, 0, d_rationale="none"))["failed"]
    assert "conditions_in_base_text" in spec_cert("S24", with_pair(s24, 0, conditions_preserved=("an irreversible engine",)))["failed"]
    assert "d_kinds" in spec_cert("S24", with_pair(s24, 1, d_kind="same_object_undone_event"))["failed"]
    assert "scene_clause_ok" in spec_cert("S24", dataclasses.replace(s24, scene_clause="A kettle of 2 litres stands nearby."))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S24", dataclasses.replace(s24, scene_refs=("tractor",)))["failed"]
    assert "attach_has_no_digit" in spec_cert("S31", with_pair(sd("S31"), 0, r_attach="thrower 2"))["failed"]


def test_planted_c_and_k_violations_fail_the_certificate():
    s31 = sd("S31")
    broken_c = dataclasses.replace(s31.cancelling, spec=dataclasses.replace(s31.cancelling.spec, expr_with_q="v*sqrt(2*h*q/g)"))
    assert not spec_cert("S31", dataclasses.replace(s31, cancelling=broken_c))["passed"]
    bad_tag = dataclasses.replace(s31.cancelling, familiarity="well known")
    assert "c_familiarity_tag" in spec_cert("S31", dataclasses.replace(s31, cancelling=bad_tag))["failed"]
    s28 = sd("S28")
    bad_regime = dataclasses.replace(s28.conditional, spec=dataclasses.replace(s28.conditional.spec, counter_regime_value=100.0))
    assert not spec_cert("S28", dataclasses.replace(s28, conditional=bad_regime))["passed"]
    bad_out = dataclasses.replace(s28.conditional, k_out=dataclasses.replace(s28.conditional.k_out, values=(60.0, 70.0)))
    assert "k_out_predicate_false_and_answer_moves" in spec_cert("S28", dataclasses.replace(s28, conditional=bad_out))["failed"]
    short_reason = dataclasses.replace(sd("S29").conditional, k_out=r2.KOut(False, "no"))
    assert "k_out_judged" in spec_cert("S29", dataclasses.replace(sd("S29"), conditional=short_reason))["failed"]
    s34 = sd("S34")
    assert "wiring_dimension" in spec_cert("S34", dataclasses.replace(s34, relevant=rv.RelevantWiring("g", "add", "x")))["numeric"]["failed"]


# --- (e) the scene clause leaves the base problem unchanged -------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_leaves_the_base_gold_graph_and_prompt_unchanged(sid, v1_rows):
    spec, structure = sd(sid), m.structure(sid)
    original = m.STRUCTURE_FACTORIES[sid]()
    assert structure.nodes == original.nodes and structure.instances == original.instances
    assert dg.structure_hash(structure) == dg.structure_hash(original)
    for index, inst in enumerate(original.instances):
        assert dg.gold_for(structure, dict(inst)) == pytest.approx(dg.gold_for(original, dict(inst)), rel=1e-12), (sid, index)
    base = v1_rows[sid]
    no_cue = rv._assemble(structure, 0, "", "after_context")
    assert no_cue == base["problem"].replace("\n\n", " " + spec.scene_clause + "\n\n", 1)
    assert rv._assemble(original, 0, "", "after_context") == base["problem"]
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(base["gold_answer"]["value"], rel=1e-12)
    cells = r2.role_cells_v2(structure, spec, 0)
    assert next(c for c in cells if c.stratum == "none").prompt == no_cue
    assert all(spec.scene_clause in c.prompt for c in cells)
    # the unit text of every sentence is a unit the prompt grammar knows
    assert spec.unit in dm.UNITS
