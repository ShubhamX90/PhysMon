"""Tests for the M250 batch a role specs (`roles_m250_a`: S03 S04 S05 S06 S08 S09 S10 S11 S12 S14 S16 S17 S18 S19 S21 S22 S23).

(a) every spec passes the v2.1 certifier; (b) every R gold, at every study and held-out value, both phrasing pairs and both October
instances, equals a closed form written in this file (not the graph); the D gold equals the same closed form at the neutral value of
q; (c) every C quantity is invariant (intermediate quantity varies, answer does not) and every K predicate holds at every value, on
independently written physics; (d) the v2.1 wording, lexicon and hygiene rules; (e) the scene clause leaves the base problem's gold
and text (apart from the clause) unchanged; plus the composition targets and a few planted mutations the certifier must reject.
"""

from __future__ import annotations

import dataclasses
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m250_a as m  # noqa: E402

V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
BATCH = ("S03", "S04", "S05", "S06", "S08", "S09", "S10", "S11", "S12", "S14", "S16", "S17", "S18", "S19", "S21", "S22", "S23")
SIDS = sorted(m.SPECS)
INSTANCES = (0, 1)
REL = 1e-9


# --- independent physics (display units in, target display unit out) -------------------------------------------------------------

def _rad(deg: float) -> float:
    return math.radians(deg)


def s03(x, q):  # one-dimensional elastic collision by the centre-of-mass frame: the relative velocity reverses
    m1, m2 = x["m1"] + q, x["m2"]
    return 2 * (m1 * x["v1"] + m2 * x["v2"]) / (m1 + m2) - x["v1"]


def s04(x, q):  # energy: (1/2) k x^2 = (1/2) (m + q) v^2
    return math.sqrt(x["k"] * x["x"] ** 2 / (x["m"] + q))


def s05(x, q):  # torque = I alpha with I = (1/2) M r^2 of the composite uniform disc
    return (x["tau"] - x["tau_f"]) / (0.5 * (x["m"] + q) * x["r"] ** 2)


def s06(x, q):  # current divider on the parallel pair
    r_pair = x["R2"] * x["R3"] / (x["R2"] + x["R3"])
    return x["V"] / (x["R1"] + q + r_pair) * x["R2"] / (x["R2"] + x["R3"])


def s08(x, q):  # energy in mJ: Q = Ceq V, U = Q^2 / (2 Ceq), the second capacitor enlarged by q (uF)
    c1, c2 = x["C1"] * 1e-6, (x["C2"] + q) * 1e-6
    ceq = 1 / (1 / c1 + 1 / c2)
    return (ceq * x["V"]) ** 2 / (2 * ceq) * 1e3


def s09(x, q):  # heat gained by the water equals heat lost by the block
    m2 = x["m2"] + q
    tf = (x["m1"] * x["c1"] * x["T1"] + m2 * x["c2"] * x["T2"]) / (x["m1"] * x["c1"] + m2 * x["c2"])
    return tf - x["T2"]


def s10(x, q):  # vertical launch speed, rise to the top, platform raised by q
    vy = x["v"] * math.sin(_rad(x["theta"]))
    return x["h0"] + q + vy * vy / (2 * x["g"])


def s11(x, q):  # constant deceleration mu g from speed v0 + q
    return (x["v0"] + q) ** 2 / (2 * x["mu"] * x["g"])


def s12(x, q):  # static friction supplies the centripetal force on a path of radius r + q
    return math.sqrt(x["mu"] * x["g"] * (x["r"] + q))


def s14(x, q):  # constant speed: power = weight x speed
    return (x["m"] + q) * x["g"] * (x["h"] / x["t"])


def s16(x, q):  # RL charging with the series resistance R + q
    r = x["R"] + q
    return x["V"] / r * (1 - math.exp(-(x["t"] * 1e-3) * r / (x["Lc"] * 1e-3)))


def s17(x, q):  # conduction through the series resistances with the temperature difference raised by q
    return (x["dT"] + q) / (x["Ra"] + x["Rb"])


def s18(x, q):  # isothermal work, volume ratio q: W = p V ln(ratio)
    return x["p1"] * 1e3 * x["V1"] * math.log(q)


def s19(x, q):  # range on level ground with the launch angle theta - q
    return x["v"] ** 2 * math.sin(2 * _rad(x["theta"] - q)) / x["g"]


def s21(x, q):  # source approaching a stationary listener, emitted frequency f + q
    return (x["f"] + q) * x["c"] / (x["c"] - x["vs"])


def s22(x, q):  # fundamental of a string: f = sqrt(T / mu) / (2 L), mu = m / L, tension T + q
    return math.sqrt((x["T"] + q) / (x["m"] / x["L"])) / (2 * x["L"])


def s23(x, q):  # combined gas law, final temperature T2 + q at the final volume (kPa)
    return x["p1"] * x["V1"] * (x["T2"] + q) / (x["V2"] * x["T1"])


R_GOLD = {"S03": s03, "S04": s04, "S05": s05, "S06": s06, "S08": s08, "S09": s09, "S10": s10, "S11": s11, "S12": s12,
          "S14": s14, "S16": s16, "S17": s17, "S18": s18, "S19": s19, "S21": s21, "S22": s22, "S23": s23}
NEUTRAL = {sid: (lambda x: 0.0) for sid in BATCH}  # q is added or subtracted: the neutral value is 0
NEUTRAL["S18"] = lambda x: x["rho"]  # q replaces the expansion ratio: the base ratio is the neutral value


# --- C chains: q enters an intermediate quantity and cancels from the answer ---------------------------------------------------------

def c_s04(x, q):  # q = natural length (m): stretched length, extension, restoring force, maximum speed
    stretched = q + x["x"]
    extension = stretched - q
    return stretched, math.sqrt(x["k"] / x["m"]) * extension


def c_s05(x, q):  # q = thickness (cm): density from the mass, then I = (1/2) rho pi r^4 t
    t = q * 1e-2
    rho = x["m"] / (math.pi * x["r"] ** 2 * t)
    inertia = 0.5 * rho * math.pi * x["r"] ** 4 * t
    return rho, (x["tau"] - x["tau_f"]) / inertia


def c_s08(x, q):  # q = charging resistance (kOhm): energy from the battery minus energy dissipated, closed forms
    r = q * 1e3
    ceq = 1 / (1 / (x["C1"] * 1e-6) + 1 / (x["C2"] * 1e-6))
    v = x["V"]
    drawn = v * (v / r) * (r * ceq)
    dissipated = (v / r) ** 2 * r * (r * ceq / 2)
    return r * ceq, (drawn - dissipated) * 1e3  # the time constant R Ceq is the q-dependent intermediate


def c_s08_numeric(x, q):  # the same energies by numerical integration of the charging current (midpoint rule)
    r = q * 1e3
    ceq = 1 / (1 / (x["C1"] * 1e-6) + 1 / (x["C2"] * 1e-6))
    tau = r * ceq
    n = 400_000
    t = (np.arange(n) + 0.5) * (40 * tau / n)
    current = x["V"] / r * np.exp(-t / tau)
    dt = 40 * tau / n
    drawn = float(np.sum(x["V"] * current) * dt)
    dissipated = float(np.sum(current ** 2 * r) * dt)
    return (drawn - dissipated) * 1e3


def c_s10(x, q):  # q = mass: kinetic energy of the vertical motion, potential energy gained
    vy = x["v"] * math.sin(_rad(x["theta"]))
    kinetic = 0.5 * q * vy * vy
    return kinetic, x["h0"] + kinetic / (q * x["g"])


def c_s11(x, q):  # q = mass: friction force, deceleration, stopping distance
    friction = x["mu"] * q * x["g"]
    return friction, x["v0"] ** 2 / (2 * (friction / q))


def c_s12(x, q):  # q = mass: friction supplies the centripetal force m v^2 / r
    friction = x["mu"] * q * x["g"]
    return friction, math.sqrt(friction * x["r"] / q)


def c_s14(x, q):  # q = starting height (m): potential energies at the start and the end, work, power
    start, end = x["m"] * x["g"] * q, x["m"] * x["g"] * (q + x["h"])
    return end, (end - start) / x["t"]


def c_s17(x, q):  # q = colder surface temperature (K): the hotter surface, the difference, the flow
    hot = q + x["dT"]
    return hot, (hot - q) / (x["Ra"] + x["Rb"])


def c_s18(x, q):  # q = temperature (K): n R from the initial state, then W = n R T ln(ratio)
    n_r = x["p1"] * 1e3 * x["V1"] / q
    return n_r, n_r * q * math.log(x["rho"])


def c_s21(x, q):  # q = initial distance (m): arrival times of two successive wavefronts
    t_first = q / x["c"]
    period = 1 / x["f"]
    t_second = period + (q - x["vs"] * period) / x["c"]
    return t_first, 1 / (t_second - t_first)


def c_s22(x, q):  # q = cross-section (mm^2): density, linear density, frequency
    area = q * 1e-6
    rho = x["m"] / (area * x["L"])
    mu = rho * area
    return rho, math.sqrt(x["T"] / mu) / (2 * x["L"])


C_CHAIN = {"S04": c_s04, "S05": c_s05, "S08": c_s08, "S10": c_s10, "S11": c_s11, "S12": c_s12, "S14": c_s14, "S17": c_s17,
           "S18": c_s18, "S21": c_s21, "S22": c_s22}


# --- K regimes: predicate on display-unit inputs (true inside), and the answer if the regime failed ------------------------------------

def k_s04(x, q):
    return x["x"] < q


def k_s05(x, q):
    return q < x["tau"]


def k_s06(x, q):  # power dissipated in the second resistor of the pair
    return s06(x, 0.0) ** 2 * x["R3"] < q


def k_s08(x, q):  # voltage across the first capacitor of two in series
    ceq = 1 / (1 / x["C1"] + 1 / x["C2"])
    return ceq * x["V"] / x["C1"] < q


def k_s10(x, q):
    return s10(x, 0.0) < q


def k_s14(x, q):
    return s14(x, 0.0) < q


def k_s22(x, q):
    return x["T"] < q


K_PRED = {"S04": k_s04, "S05": k_s05, "S06": k_s06, "S08": k_s08, "S10": k_s10, "S14": k_s14, "S22": k_s22}
K_ALT = {  # the answer if the regime failed (target display unit), for the separation check
    "S04": lambda x, q: q * math.sqrt(x["k"] / x["m"]),
    "S05": lambda x, q: 0.0,
    "S06": lambda x, q: 0.0,
    "S08": lambda x, q: 0.5 * (x["C2"] * 1e-6) * x["V"] ** 2 * 1e3,
    "S10": lambda x, q: q,
    "S14": lambda x, q: q,
    "S22": lambda x, q: 0.0,
}


# --- fixtures ----------------------------------------------------------------------------------------------------------------------

def v1_row(sid: str, instance: int) -> dict:
    for line in V1.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["structure_id"] == sid and row["instance"] == instance:
            return row
    raise AssertionError(f"no October row for {sid} instance {instance}")


@pytest.fixture(scope="module")
def structures():
    return {sid: m.structure(sid) for sid in SIDS}


@pytest.fixture(scope="module")
def certs(structures):
    return {sid: r2.certify_v2(structures[sid], m.SPECS[sid]) for sid in SIDS}


@pytest.fixture(scope="module")
def cells(structures):
    return {(sid, i): r2.role_cells_v2(structures[sid], m.SPECS[sid], i, include_heldout=True) for sid in SIDS for i in INSTANCES}


def all_sentences(spec: r2.RoleSpecV2) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"R": [], "D": [], "N": []}
    for pair in spec.pairs:
        for value in (*spec.values, *spec.heldout_values):
            out["R"].append(r2.pair_sentence(pair, "R", value, spec.unit))
            out["D"].append(r2.pair_sentence(pair, "D", value, spec.unit))
        out["N"].append(r2.pair_sentence(pair, "D", None, spec.unit))
    return out


def sub_sentences(sub) -> list[str]:
    return [rv._sentence(sub.frame, v, sub.unit, p.relation, sub.nonnumeric_fill) for v in sub.values for p in sub.phrasings]


# --- the batch ------------------------------------------------------------------------------------------------------------------------

def test_the_batch_is_the_seventeen_structures_and_every_one_is_accounted_for():
    assert tuple(sorted(m.SPECS)) == BATCH
    assert set(m.STRUCTURE_FACTORIES) == set(BATCH) == set(m.TARGET_TERMS)
    assert not set(m.INFEASIBLE) & set(m.SPECS) and set(m.SPECS) | set(m.INFEASIBLE) == set(BATCH)
    for sid, spec in m.SPECS.items():
        assert spec.structure_id == sid and spec.version == r2.VERSION_V21
        assert (spec.cancelling is None) == (sid in m.NO_C) and (spec.conditional is None) == (sid in m.NO_K), sid
    for reasons in (m.NO_C, m.NO_K, m.INFEASIBLE):
        assert all(len(text) >= r2.MIN_RATIONALE for text in reasons.values())


@pytest.mark.parametrize("sid", SIDS)
def test_target_terms_are_written_for_the_extractor(sid):
    phrases, symbols = m.TARGET_TERMS[sid]
    assert phrases and symbols and all(isinstance(s, str) and s for s in (*phrases, *symbols))
    assert len(set(phrases)) == len(phrases) and len(set(symbols)) == len(symbols)


# --- (a) certification ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_passes_the_v21_certifier(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (sid, cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(m.SPECS[sid], cert)
    for key in ("exactly_two_pairs", "d_kinds", "reversal_free", "d_not_on_target", "scene_clause_ok", "scene_clause_in_base_context",
                "d0_refers_to_scene_object", "value_hygiene", "heldout_value_hygiene", "consequence_free", "marker_free"):
        assert cert["checks"][key]["ok"], (sid, key)


def test_the_two_pairs_are_one_co_present_and_one_other_event():
    for sid, spec in m.SPECS.items():
        assert [p.d_kind for p in spec.pairs] == [r2.D_KIND_CO_PRESENT, r2.D_KIND_OTHER_EVENT], sid
        assert all(p.frame_matched for p in spec.pairs), sid  # one frame per pair: no declared exceptions in this batch


# --- (b) R and D golds against closed forms ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_r_golds_equal_the_independent_closed_form_at_every_value_pair_and_instance(sid, structures, cells):
    spec = m.SPECS[sid]
    formula = R_GOLD[sid]
    for instance in INSTANCES:
        x = dict(structures[sid].instances[instance])
        r_cells = [c for c in cells[(sid, instance)] if c.stratum == "R"]
        assert len(r_cells) == 2 * (len(spec.values) + len(spec.heldout_values))
        for cell in r_cells:
            assert cell.value is not None
            expected = formula(x, cell.value)
            assert cell.gold_value == pytest.approx(expected, rel=REL), (sid, instance, cell.cell_id)
        assert {c.value for c in r_cells} == {*spec.values, *spec.heldout_values}


@pytest.mark.parametrize("sid", SIDS)
def test_d_gold_is_the_base_answer_at_the_neutral_value_and_the_october_gold(sid, structures, cells):
    for instance in INSTANCES:
        x = dict(structures[sid].instances[instance])
        expected = R_GOLD[sid](x, NEUTRAL[sid](x))
        for cell in cells[(sid, instance)]:
            if cell.stratum in ("D", "N", "none"):
                assert cell.gold_value == pytest.approx(expected, rel=REL), (sid, instance, cell.cell_id)
        assert v1_row(sid, instance)["gold_answer"]["value"] == pytest.approx(expected, rel=REL), (sid, instance)


@pytest.mark.parametrize("sid", SIDS)
def test_r_separates_from_d_and_the_study_values_from_each_other(sid, structures):
    spec = m.SPECS[sid]
    for instance in INSTANCES:
        x = dict(structures[sid].instances[instance])
        base = R_GOLD[sid](x, NEUTRAL[sid](x))
        golds = [R_GOLD[sid](x, v) for v in spec.values]
        assert all(abs(g - base) > 0.01 * max(abs(g), abs(base)) for g in golds), (sid, instance)
        assert all(abs(a - b) > 0.01 * max(abs(a), abs(b)) for i, a in enumerate(golds) for b in golds[i + 1:]), (sid, instance)


# --- (c) C invariance and K regimes ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", sorted(C_CHAIN))
def test_c_answer_is_invariant_while_the_intermediate_quantity_varies(sid, structures):
    c = m.SPECS[sid].cancelling
    assert c is not None
    for instance in INSTANCES:
        x = dict(structures[sid].instances[instance])
        base = R_GOLD[sid](x, NEUTRAL[sid](x))
        intermediates = []
        for value in (*c.spec.values, *c.heldout_values):
            intermediate, answer = C_CHAIN[sid](x, value)
            intermediates.append(intermediate)
            assert answer == pytest.approx(base, rel=1e-9), (sid, instance, value)
        assert len({round(i, 12) for i in intermediates}) == len(intermediates), (sid, instance)  # q really enters the chain
        spread = max(intermediates) - min(intermediates)
        assert spread > 1e-6 * max(abs(i) for i in intermediates), (sid, instance)


def test_c_set_matches_the_specs():
    assert sorted(C_CHAIN) == sorted(sid for sid, spec in m.SPECS.items() if spec.cancelling is not None)
    assert sorted(K_PRED) == sorted(sid for sid, spec in m.SPECS.items() if spec.conditional is not None)


def test_the_charging_energy_bookkeeping_matches_numerical_integration(structures):
    for instance in INSTANCES:
        x = dict(structures["S08"].instances[instance])
        base = R_GOLD["S08"](x, 0.0)
        for value in m.SPECS["S08"].cancelling.spec.values:
            assert c_s08_numeric(x, value) == pytest.approx(base, rel=1e-4), (instance, value)


def test_the_cancelling_wrong_laws_are_not_the_gold(structures, certs):
    for sid in C_CHAIN:
        assert certs[sid]["numeric"]["checks"]["cancelling"]["wrong_law_separated_at_2_of_3"] is True, sid
        assert certs[sid]["numeric"]["checks"]["cancelling"]["derivative_zero"] is True, sid


@pytest.mark.parametrize("sid", sorted(K_PRED))
def test_k_predicate_holds_inside_the_regime_and_fails_at_the_counter_value(sid, structures):
    k = m.SPECS[sid].conditional
    assert k is not None
    for instance in INSTANCES:
        x = dict(structures[sid].instances[instance])
        base = R_GOLD[sid](x, NEUTRAL[sid](x))
        for value in (*k.spec.values, *k.heldout_values):
            assert K_PRED[sid](x, value), (sid, instance, value)
            alt = K_ALT[sid](x, value)
            assert abs(alt - base) > 0.01 * max(abs(alt), abs(base)), (sid, instance, value)  # the regime matters
        assert not K_PRED[sid](x, k.spec.counter_regime_value), (sid, instance)


@pytest.mark.parametrize("sid", sorted(K_PRED))
def test_k_out_is_recorded_with_a_reason(sid):
    k = m.SPECS[sid].conditional
    assert not k.k_out.feasible and not k.k_out.values and len(k.k_out.reason) >= r2.MIN_RATIONALE


def test_c_and_k_cells_carry_the_base_gold_at_every_value(cells, structures):
    for (sid, instance), group in cells.items():
        x = dict(structures[sid].instances[instance])
        base = R_GOLD[sid](x, NEUTRAL[sid](x))
        for cell in group:
            if cell.stratum in ("C", "K"):
                assert cell.gold_value == pytest.approx(base, rel=REL), (sid, instance, cell.cell_id)


# --- (d) wording, lexicon and hygiene rules -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_no_role_sentence_has_a_consequence_clause_a_marker_word_or_a_reversal(sid):
    spec = m.SPECS[sid]
    sentences = all_sentences(spec)
    for role, texts in sentences.items():
        for text in texts:
            assert not r2.consequence_hits(text), (sid, role, text, r2.consequence_hits(text))
            assert not r2.marker_hits(text), (sid, role, text, r2.marker_hits(text))
    for text in (*sentences["D"], *sentences["N"]):
        assert not r2.reversal_hits(text), (sid, text, r2.reversal_hits(text))
        assert not r2.remoteness_hits(text), (sid, text)
    for sub in (spec.cancelling.spec if spec.cancelling else None, spec.conditional.spec if spec.conditional else None):
        if sub is not None:
            for text in sub_sentences(sub):
                assert not r2.consequence_hits(text) and not r2.marker_hits(text), (sid, text)
    clause = spec.scene_clause
    assert not r2.consequence_hits(clause) and not r2.marker_hits(clause) and not r2.reversal_hits(clause), (sid, clause)


@pytest.mark.parametrize("sid", SIDS)
def test_pairs_differ_only_in_the_attachment_and_stay_within_three_words(sid):
    spec = m.SPECS[sid]
    for pair in spec.pairs:
        for value in spec.values:
            r_text = r2.pair_sentence(pair, "R", value, spec.unit)
            d_text = r2.pair_sentence(pair, "D", value, spec.unit)
            assert r_text.replace(pair.r_attach, "@") == d_text.replace(pair.d_attach, "@"), (sid, pair.pair_id)
            assert abs(len(r2.words(r_text)) - len(r2.words(d_text))) <= r2.MAX_WORD_DIFF, (sid, pair.pair_id, r_text, d_text)
            diff = r2.token_difference(r_text, d_text)
            assert set(diff["removed"]) | set(diff["added"]), (sid, pair.pair_id)
            numerals = [t for t in (*diff["removed"], *diff["added"]) if re.search(r"\d", t)]
            assert not numerals, (sid, pair.pair_id, numerals)  # the numeral and the unit are shared
        assert not re.search(r"\d", pair.r_attach + pair.d_attach)
        n_text = r2.pair_sentence(pair, "D", None, spec.unit)
        assert not re.search(r"\d", n_text), (sid, n_text)
        assert len(pair.d_rationale) >= r2.MIN_RATIONALE


@pytest.mark.parametrize("sid", SIDS)
def test_d_kinds_scene_object_and_event_anchoring(sid):
    spec = m.SPECS[sid]
    p0, p1 = spec.pairs
    scene = spec.scene_clause
    d0 = r2.pair_sentence(p0, "D", spec.values[0], spec.unit)
    assert spec.scene_refs and all(ref in scene and ref in d0 for ref in spec.scene_refs), (sid, scene, d0)
    assert spec.target_terms and not [t for t in spec.target_terms if t.lower() in p0.d_attach.lower()], sid
    assert r2.prior_marker_hits(p1.d_attach), (sid, p1.d_attach)  # the same-object D is history
    assert not r2.prior_marker_hits(p1.r_attach), (sid, p1.r_attach)
    assert len(spec.scene_object_rationale) >= r2.MIN_RATIONALE and p0.before_context_reason


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_is_number_free_and_the_last_sentence_of_the_base_context(sid, structures):
    spec = m.SPECS[sid]
    scene = spec.scene_clause
    assert scene.endswith(".") and not re.search(r"\d", scene) and "\n" not in scene
    context = dg.context_text(structures[sid], dict(structures[sid].instances[0]))
    assert context.count(scene) == 1 and context.endswith(scene)
    assert r2.words(scene)[0][0].isupper()


@pytest.mark.parametrize("sid", SIDS)
def test_every_prompt_numeral_is_a_displayed_input_or_the_role_value(sid, structures, cells):
    for cell in cells[(sid, 0)]:
        assert r2._prompt_numerals_ok(structures[sid], 0, cell.prompt, cell.value), (sid, cell.cell_id)
        assert spec_scene_in(sid, cell.prompt), (sid, cell.cell_id)


def spec_scene_in(sid: str, prompt: str) -> bool:
    return m.SPECS[sid].scene_clause in prompt


@pytest.mark.parametrize("sid", SIDS)
def test_value_hygiene_and_study_values(sid, certs):
    spec = m.SPECS[sid]
    assert len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert not set(spec.values) & set(spec.heldout_values)
    hygiene = certs[sid]["hygiene"]
    for name, rows in hygiene.items():
        assert all(h["ok"] for h in rows), (sid, name)
    for sub, held in ((spec.cancelling.spec, spec.cancelling.heldout_values) if spec.cancelling else (None, ()),
                      (spec.conditional.spec, spec.conditional.heldout_values) if spec.conditional else (None, ())):
        if sub is not None:
            assert len(sub.values) == 3 and len(held) == 2 and not set(sub.values) & set(held)


def test_familiarity_tags_and_reasons_and_famous_limit():
    tags = [spec.cancelling.familiarity for spec in m.SPECS.values() if spec.cancelling]
    assert all(t in r2.FAMILIARITY for t in tags)
    assert all(len(s.cancelling.familiarity_reason) >= 20 for s in m.SPECS.values() if s.cancelling)
    assert tags.count("famous") <= len(tags) / 2


def test_composition_targets():
    n = len(m.SPECS)
    n_c = sum(spec.cancelling is not None for spec in m.SPECS.values())
    n_k = sum(spec.conditional is not None for spec in m.SPECS.values())
    assert n == 17 and n_c / n >= 0.5 and n_k / n >= 0.3, (n_c, n_k)


# --- (e) the scene clause leaves the base problem unchanged -------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_leaves_the_base_gold_unchanged(sid, structures):
    base = m.STRUCTURE_FACTORIES[sid]()
    scened = structures[sid]
    assert [dg.gold_for(scened, dict(i)) for i in scened.instances] == [dg.gold_for(base, dict(i)) for i in base.instances]
    assert scened.nodes == base.nodes and scened.target == base.target and scened.instances == base.instances
    assert scened.render.question == base.render.question
    assert scened.render.context == f"{base.render.context} {m.SPECS[sid].scene_clause}"


@pytest.mark.parametrize("sid", SIDS)
def test_no_cue_prompt_is_the_october_problem_with_the_clause_before_the_question(sid, structures, cells):
    clause = m.SPECS[sid].scene_clause
    for instance in INSTANCES:
        row = v1_row(sid, instance)
        no_cue = next(c for c in cells[(sid, instance)] if c.stratum == "none")
        assert no_cue.prompt == row["problem"].replace("\n\n", f" {clause}\n\n", 1), (sid, instance)
        assert no_cue.gold_value == pytest.approx(row["gold_answer"]["value"], rel=1e-12), (sid, instance)


@pytest.mark.parametrize("sid", SIDS)
def test_cell_counts_per_instance(sid, cells):
    spec = m.SPECS[sid]
    group = cells[(sid, 0)]
    count = {s: sum(c.stratum == s for c in group) for s in ("none", "N", "R", "D", "C", "K", "K_out")}
    n_values = len(spec.values) + len(spec.heldout_values)
    assert count["none"] == 1 and count["N"] == 2 and count["R"] == count["D"] == 2 * n_values
    assert count["C"] == (len(spec.cancelling.spec.values) * 2 if spec.cancelling else 0)
    assert count["K"] == (len(spec.conditional.spec.values) * 2 if spec.conditional else 0) and count["K_out"] == 0


# --- planted mutations the certifier must reject ------------------------------------------------------------------------------------------

def _cert(sid: str, spec: r2.RoleSpecV2) -> dict:
    return r2.certify_v2(r2.with_scene(m.STRUCTURE_FACTORIES[sid](), spec.scene_clause), spec)


def test_certifier_rejects_a_broken_cancellation_a_reversed_d_and_a_marker():
    spec = m.SPECS["S11"]
    broken = dataclasses.replace(spec, cancelling=dataclasses.replace(
        spec.cancelling, spec=dataclasses.replace(spec.cancelling.spec, expr_with_q="v0**2/(2*mu*g*q)")))
    assert not _cert("S11", broken)["passed"]
    reversed_d = dataclasses.replace(spec, pairs=(spec.pairs[0], dataclasses.replace(spec.pairs[1], d_attach="and taken back again")))
    assert "reversal_free" in _cert("S11", reversed_d)["failed"]
    marked = dataclasses.replace(spec, pairs=(dataclasses.replace(spec.pairs[0], d_attach="bus, which is unrelated"), spec.pairs[1]))
    assert "marker_free" in _cert("S11", marked)["failed"]


def test_certifier_rejects_an_in_regime_failure_a_scene_number_and_a_target_word_in_d():
    spec = m.SPECS["S04"]
    out_of_regime = dataclasses.replace(spec, conditional=dataclasses.replace(
        spec.conditional, spec=dataclasses.replace(spec.conditional.spec, values=(0.26, 0.34, 0.12))))
    assert not _cert("S04", out_of_regime)["passed"]
    numbered = dataclasses.replace(spec, scene_clause="Two trolleys stand on the floor beside the table 3.")
    assert not _cert("S04", numbered)["passed"]
    on_target = dataclasses.replace(spec, pairs=(dataclasses.replace(spec.pairs[0], d_attach="the block"), spec.pairs[1]))
    assert "d_not_on_target" in _cert("S04", on_target)["failed"]


# --- wording rules 6-8 and article agreement (retrofit, journal J15.1-046) ---------------------------------------------------------
# Rule 6 (every answer-determining condition stated number-free) is a judgement made in the scene clause and cannot be pattern-checked;
# these tests pin the parts that can be: rules 7 and 8, article agreement, and that the two pairs read as different sentences.

ATTACHING_P1 = ("S03", "S04", "S05", "S06", "S08", "S09", "S10", "S14", "S16")


def _rule_sentences(spec: r2.RoleSpecV2) -> list[tuple[str, str, str]]:
    """(role, pair id, sentence) for every R, D and N sentence of both pairs at every study and held-out value."""

    out = []
    for pair in spec.pairs:
        for value in (*spec.values, *spec.heldout_values):
            out.append(("R", pair.pair_id, r2.pair_sentence(pair, "R", value, spec.unit)))
            out.append(("D", pair.pair_id, r2.pair_sentence(pair, "D", value, spec.unit)))
        out.append(("N", pair.pair_id, r2.pair_sentence(pair, "D", None, spec.unit)))
    return out


def _all_numeric_sentences(spec: r2.RoleSpecV2) -> list[str]:
    texts = [s for _, _, s in _rule_sentences(spec)]
    for sub in (spec.cancelling, spec.conditional):
        if sub is not None:
            texts += [rv._sentence(sub.spec.frame, v, sub.spec.unit, p.relation, sub.spec.nonnumeric_fill)
                      for v in (*sub.spec.values, *sub.heldout_values) for p in sub.spec.phrasings]
    return texts


def _vowel_sound_number(token: str) -> bool:
    """True when the numeral `token` (digits, optional decimal part) is read with a vowel sound: eight, eleven, eighteen, eighty..."""

    whole = token.split(".")[0].replace(",", "")
    if whole.startswith("8"):
        return True
    return whole[:2] in ("11", "18") and len(whole) in (2, 4, 5)


@pytest.mark.parametrize("sid", SIDS)
def test_article_agrees_with_the_number_that_follows_it_in_every_rendered_sentence(sid):
    spec = m.SPECS[sid]
    for text in (*_all_numeric_sentences(spec), spec.scene_clause):
        for article, token in re.findall(r"\b([Aa]n?) (\d[\d.,]*)", text):
            assert article.lower() == ("an" if _vowel_sound_number(token) else "a"), (sid, text)


@pytest.mark.parametrize("sid", SIDS)
def test_a_pair_1_d_that_attaches_something_says_it_was_there_for_that_experiment_only(sid):
    spec = m.SPECS[sid]
    p1 = spec.pairs[1]
    if p1.d_kind != r2.D_KIND_OTHER_EVENT:
        return
    d_attach = p1.d_attach.lower()
    assert "earlier" in d_attach or "previous" in d_attach or "after the" in d_attach, (sid, p1.d_attach)
    if sid in ATTACHING_P1:
        assert d_attach.endswith(" only") and "earlier" in d_attach, (sid, p1.d_attach)
        for value in spec.values:
            assert " only" in r2.pair_sentence(p1, "D", value, spec.unit), sid
        assert " only" in r2.pair_sentence(p1, "D", None, spec.unit), sid
        assert " only" not in p1.r_attach.lower(), (sid, p1.r_attach)
    else:
        assert not d_attach.endswith(" only"), (sid, p1.d_attach)  # nothing is attached: "in an earlier experiment" suffices


@pytest.mark.parametrize("sid", SIDS)
def test_no_d_or_n_sentence_states_a_condition_that_contradicts_the_scene_clause(sid):
    spec = m.SPECS[sid]
    scene = spec.scene_clause.lower()
    for role, pair_id, text in _rule_sentences(spec):
        if role == "R":
            continue
        lowered = text.lower()
        if "empty" in scene and pair_id == "p0":  # an empty object may be filled by an action, never described as holding something
            assert not re.search(r"\b(?:now )?(?:fills?|filled|holds?|contains?)\b", lowered), (sid, text)
        # a D/N sentence never restates the scene object as lacking what the scene clause gives it, or as already changed
        assert not re.search(r"\b(?:now|already) (?:fills?|holds?|contains?|is empty)\b", lowered), (sid, text)
        assert "no longer" not in lowered and "instead of" not in lowered, (sid, text)


@pytest.mark.parametrize("sid", SIDS)
def test_the_two_pairs_give_different_r_sentences_and_different_d_sentences(sid):
    spec = m.SPECS[sid]
    p0, p1 = spec.pairs
    for value in (*spec.values, *spec.heldout_values):
        assert r2.pair_sentence(p0, "R", value, spec.unit) != r2.pair_sentence(p1, "R", value, spec.unit), sid
        assert r2.pair_sentence(p0, "D", value, spec.unit) != r2.pair_sentence(p1, "D", value, spec.unit), sid
    assert r2.pair_sentence(p0, "D", None, spec.unit) != r2.pair_sentence(p1, "D", None, spec.unit), sid


@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_has_no_meta_wording_about_given_or_stated_values(sid):
    clause = m.SPECS[sid].scene_clause.lower()
    for phrase in ("given", "stated", "before any", "anything", "any water", "wherever", "onto a", "stays fixed", "joined to"):
        assert phrase not in clause, (sid, phrase, clause)
