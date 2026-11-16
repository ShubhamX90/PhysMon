"""Tests for the M250 batch d role specs (`roles_m250_d`): October structures S73-S95 in the role-by-value design of M0 v2.1.

(a) every spec certifies with the v2.1 certifier; (b) every R gold, at every study and held-out value and at every instance of the
structure, equals a closed form written here independently of the graphs; (c) every C and K quantity is invariant (or in regime)
numerically and the out-of-regime law moves the answer; (d) the v2.1 wording, lexicon and hygiene rules hold; (e) the scene clause
leaves the base problem and gold unchanged. The closed forms use plain SI arithmetic and the displayed numerals of the prompt.
"""

from __future__ import annotations

import dataclasses
import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m250_d as m  # noqa: E402

V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SIDS = sorted(m.SPECS)
BATCH = ["S73", "S74", "S75", "S76", "S77", "S78", "S79", "S81", "S82", "S83", "S84", "S85", "S86", "S91", "S93", "S94", "S95"]
EV = 1.602176634e-19  # J per eV
AMU = 1.66053906660e-27  # kg per u
G = 9.8  # every fluids prompt states g = 9.8 m/s^2


def sorted_unique(values):
    return sorted(set(values))


# --- independent closed forms: (inputs as displayed, q in the unit of the R quantity) -> the target in its display unit ------------------

def _s73(x, q):
    width = x["L"] + q  # nm
    e1 = x["hc"] ** 2 / (8 * x["mc2"] * 1000 * width ** 2)  # eV: (eV nm)^2 / (eV nm^2)
    return x["hc"] / ((x["ni"] ** 2 - x["nf"] ** 2) * e1)  # nm


def _s77(x, q):
    kappa = math.sqrt(2 * x["mc2"] * 1e3 * (q - x["Ee"])) / x["hbarc"]  # 1/nm
    return -math.log(x["Tr"]) / (2 * kappa)  # nm


def _s82(x, q):
    lam2 = x["lam1"] * x["T1"] / (x["T2"] + q)
    return x["hc"] / lam2


def _s91(x, q):
    d1, d2 = x["d1"] / 100, x["d2"] / 100
    v1 = math.sqrt(2 * (q - x["rho"]) * G * x["dh"] / 100 / (x["rho"] * ((d1 / d2) ** 4 - 1)))
    return math.pi * d1 ** 2 / 4 * v1 * 1000  # L/s


def _s93(x, q):
    area_tank = math.pi * (x["D"] / 100) ** 2 / 4
    area_hole = math.pi * ((x["d"] + q) / 1000) ** 2 / 4
    return area_tank / area_hole * math.sqrt(2 / G) * (math.sqrt(x["h0"]) - math.sqrt(x["h1"]))


def _s94(x, q):
    speed = x["v"] / 100
    return 8 * math.pi * x["eta"] * (x["L"] + q) * speed ** 2 * 1000  # mW (Poiseuille: dp = 32 eta L v / d^2, Q = pi d^2 v / 4)


def _s95(x, q):
    return ((x["m"] + q) * G / (x["A2"] * 1e-4) + x["rho"] * G * x["h"]) * x["A1"] * 1e-4  # N


CLOSED = {"S73": _s73, "S77": _s77, "S82": _s82, "S91": _s91, "S93": _s93, "S94": _s94, "S95": _s95}
# the value of q that gives the October answer: 0 for an additive wiring, the instance's own input for a replacing one
BASE_Q = {"S73": lambda x: 0.0, "S77": lambda x: x["U0"], "S82": lambda x: 0.0,
          "S91": lambda x: x["rho_m"], "S93": lambda x: 0.0, "S94": lambda x: 0.0, "S95": lambda x: 0.0}



def _instance_inputs(structure, i):
    return {n: float(v) for n, v in structure.instances[i].items()}


@pytest.fixture(scope="module")
def certs():
    return {sid: r2.certify_v2(m.structure(sid), m.SPECS[sid]) for sid in SIDS}


@pytest.fixture(scope="module")
def v1_rows():
    rows = {}
    for line in V1.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["instance"] == 0:
            rows[row["structure_id"]] = row
    return rows


# --- batch bookkeeping ------------------------------------------------------------------------------------------------------------

def test_every_structure_of_the_batch_has_a_spec_or_a_reasoned_infeasibility():
    assert sorted(set(m.SPECS) | set(m.INFEASIBLE)) == BATCH and not set(m.SPECS) & set(m.INFEASIBLE)
    assert set(CLOSED) == set(m.SPECS) == set(m.STRUCTURE_FACTORIES) == set(m.TARGET_TERMS)
    for sid, reason in m.INFEASIBLE.items():
        assert len(reason) >= 200, sid


def test_composition_counts_and_familiarity():
    c = [s for s in m.SPECS.values() if s.cancelling is not None]
    k = [s for s in m.SPECS.values() if s.conditional is not None]
    assert sorted(s.structure_id for s in c) == ["S91", "S93", "S94", "S95"]
    assert sorted(s.structure_id for s in k) == ["S91"] and set(m.NO_K) == {"S94"} and len(m.NO_K["S94"]) >= 200
    assert sum(s.cancelling.familiarity == "famous" for s in c) <= len(c) / 2
    assert all(s.cancelling.familiarity in r2.FAMILIARITY for s in c)


def test_target_naming_is_present_and_names_the_question():
    for sid in SIDS:
        phrases, symbols = m.TARGET_TERMS[sid]
        question = m.structure(sid).render.question.lower()
        assert phrases and symbols and any(p.lower() in question for p in phrases), sid


# --- (a) the certifier ------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(m.SPECS[sid], cert)
    spec = m.SPECS[sid]
    assert spec.version == "v2.1" and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert [p.pair_id for p in spec.pairs] == ["p0", "p1"] and spec.pairs[0].d_kind == "other_object_same_scene"
    assert spec.pairs[1].d_kind == "same_object_other_event"


# --- (b) every R gold against a closed form ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_r_golds_equal_the_closed_form_at_every_value_and_instance(sid):
    structure, spec = m.structure(sid), m.SPECS[sid]
    legacy = r2.to_legacy(spec)
    formula = CLOSED[sid]
    for i in range(len(structure.instances)):
        x = _instance_inputs(structure, i)
        si = rv.display_inputs_si(structure, i)
        for value in (*spec.values, *spec.heldout_values):
            expected = formula(x, value)
            graph, solver = rv.gold_r(structure, si, legacy, value)
            assert graph == pytest.approx(expected, rel=1e-9), (sid, i, value)
            assert solver == pytest.approx(expected, rel=1e-6), (sid, i, value)  # the independently coded solver route
        # the October answer of the instance: the same formula at the no-op value of q
        base = dg.gold_for(structure, dict(structure.instances[i]))
        assert base == pytest.approx(formula(x, BASE_Q[sid](x)), rel=1e-9), (sid, i)


@pytest.mark.parametrize("sid", SIDS)
def test_emitted_cells_carry_the_closed_form_golds(sid):
    structure, spec = m.structure(sid), m.SPECS[sid]
    x = _instance_inputs(structure, 0)
    cells = r2.role_cells_v2(structure, spec, 0, include_heldout=True)
    base = CLOSED[sid](x, BASE_Q[sid](x))
    seen_r = 0
    for cell in cells:
        if cell.stratum == "R":
            assert cell.gold_value == pytest.approx(CLOSED[sid](x, cell.value), rel=1e-9), cell.cell_id
            seen_r += 1
        elif cell.stratum in ("D", "N", "none", "C", "K"):
            assert cell.gold_value == pytest.approx(base, rel=1e-9), cell.cell_id
    assert seen_r == 2 * 5  # five values (3 study, 2 held out), two phrasings
    for cell in (c for c in cells if c.stratum == "D"):
        twin = next(c for c in cells if c.stratum == "R" and c.value == cell.value and c.phrasing_id == f"r{cell.pair_id[1]}")
        assert abs(twin.gold_value - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(twin.gold_value), abs(cell.gold_value))


# --- (c) C and K invariance ----------------------------------------------------------------------------------------------------------

def _c_closed(sid, x, q):
    """The target with the C quantity written into the governing relations independently of the graph; q cancels."""
    if sid == "S91":  # q = height of the axis in m: Bernoulli with the elevation terms on both sections
        d1, d2 = x["d1"] / 100, x["d2"] / 100
        dp = (x["rho_m"] - x["rho"]) * G * x["dh"] / 100
        p2 = 0.0
        p1 = p2 + dp
        v1 = math.sqrt(2 * ((p1 + x["rho"] * G * q) - (p2 + x["rho"] * G * q)) / (x["rho"] * ((d1 / d2) ** 4 - 1)))
        return math.pi * d1 ** 2 / 4 * v1 * 1000
    if sid == "S93":  # q = density of the water in kg/m^3: hydrostatic pressure and the kinetic term both carry it
        area_tank = math.pi * (x["D"] / 100) ** 2 / 4
        area_hole = math.pi * (x["d"] / 1000) ** 2 / 4
        speed_per_root_h = math.sqrt(2 * (q * G * 1.0) / q)  # v = sqrt(2 p / rho) with p = rho g h, per sqrt(h)
        return area_tank / area_hole * 2 * (math.sqrt(x["h0"]) - math.sqrt(x["h1"])) / speed_per_root_h
    if sid == "S94":  # q = pressure at the outlet in kPa: the power is the pressure difference times the flow
        flow = math.pi * (x["d"] / 1000) ** 2 / 4 * (x["v"] / 100)
        drop = 32 * x["eta"] * x["L"] * (x["v"] / 100) / (x["d"] / 1000) ** 2
        p_in = q * 1e3 + drop
        return (p_in - q * 1e3) * flow * 1000  # mW
    if sid == "S95":  # q = atmospheric pressure in kPa: absolute pressures on both pistons, the atmosphere also on the outer faces
        p_l = q * 1e3 + x["m"] * G / (x["A2"] * 1e-4)
        p_s = p_l + x["rho"] * G * x["h"]
        return (p_s - q * 1e3) * x["A1"] * 1e-4
    raise AssertionError(sid)


@pytest.mark.parametrize("sid", ["S91", "S93", "S94", "S95"])
def test_c_quantity_cancels_numerically_at_every_value_and_instance(sid):
    structure, spec = m.structure(sid), m.SPECS[sid]
    wrapped = spec.cancelling
    assert wrapped is not None and len(wrapped.heldout_values) == 2
    for i in range(len(structure.instances)):
        x = _instance_inputs(structure, i)
        base = CLOSED[sid](x, BASE_Q[sid](x))
        for value in (*wrapped.spec.values, *wrapped.heldout_values):
            assert _c_closed(sid, x, value) == pytest.approx(base, rel=1e-9), (sid, i, value)
    # the wrong law (q kept) moves the answer at two of three study values at instance 0
    x0 = _instance_inputs(structure, 0)
    base0 = CLOSED[sid](x0, BASE_Q[sid](x0))
    values_all = rv.all_node_values(structure, rv.display_inputs_si(structure, 0))
    moved = 0
    for value in wrapped.spec.values:
        from physmon.benchmark.v2 import dimensions as dm

        wrong = dm.from_si(rv._eval_expr(wrapped.spec.wrong_law, structure, values_all, dm.to_si(value, wrapped.spec.unit)),
                           structure.render.target_unit)
        moved += abs(wrong - base0) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(base0))
    assert moved >= 2
    assert len(wrapped.spec.intermediate_relations) >= 3 and "famous" != wrapped.familiarity


def test_c_cells_have_the_base_gold_and_a_numeral_the_prompt_shows():
    for sid in ("S91", "S93", "S94", "S95"):
        structure, spec = m.structure(sid), m.SPECS[sid]
        base = dg.gold_for(structure, dict(structure.instances[0]))
        cells = [c for c in r2.role_cells_v2(structure, spec, 0) if c.stratum == "C"]
        assert len(cells) == 6 and all(c.gold_value == pytest.approx(base, rel=1e-12) for c in cells)
        assert all(f"{c.value:g}" in c.sentence for c in cells)


def test_k_s91_throat_pressure_stays_positive_and_the_cavitation_limit_moves_the_answer():
    structure, spec = m.structure("S91"), m.SPECS["S91"]
    wrapped = spec.conditional
    assert wrapped is not None and not wrapped.k_out.feasible and not wrapped.k_out.values
    for i in range(len(structure.instances)):
        x = _instance_inputs(structure, i)
        dp_kpa = (x["rho_m"] - x["rho"]) * G * x["dh"] / 100 / 1e3
        gold = CLOSED["S91"](x, x["rho_m"])
        for p_wide in (*wrapped.spec.values, *wrapped.heldout_values):
            assert p_wide - dp_kpa > 0  # the throat pressure is positive: no cavitation, so the stated reading gives the flow
            d1, d2 = x["d1"] / 100, x["d2"] / 100
            limit = math.pi * d1 ** 2 / 4 * math.sqrt(2 * p_wide * 1e3 / (x["rho"] * ((d1 / d2) ** 4 - 1))) * 1000
            assert abs(limit - gold) > rv.LOOSEST_REL_TOL * max(limit, gold)
        assert not wrapped.spec.counter_regime_value - dp_kpa > 0  # 5 kPa would put the throat below zero pressure


def test_k_sentences_have_the_base_gold():
    for sid in ("S91",):
        structure, spec = m.structure(sid), m.SPECS[sid]
        base = dg.gold_for(structure, dict(structure.instances[0]))
        cells = [c for c in r2.role_cells_v2(structure, spec, 0) if c.stratum == "K"]
        assert len(cells) == 6 and all(c.gold_value == pytest.approx(base, rel=1e-12) for c in cells)
        assert not [c for c in r2.role_cells_v2(structure, spec, 0) if c.stratum == "K_out"]


# --- (d) wording, lexicon and hygiene ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_sentence_is_consequence_free_marker_free_reversal_free_and_number_free_where_needed(sid):
    structure, spec = m.structure(sid), m.SPECS[sid]
    for cell in r2.role_cells_v2(structure, spec, 0, include_heldout=True):
        assert not r2.consequence_hits(cell.sentence), cell.sentence
        assert not r2.marker_hits(cell.sentence), cell.sentence
        if cell.stratum in ("D", "N"):
            assert not r2.reversal_hits(cell.sentence), cell.sentence
            assert not r2.remoteness_hits(cell.sentence), cell.sentence
        if cell.stratum == "N":
            assert not any(ch.isdigit() for ch in cell.sentence) and cell.value is None
        assert cell.consequence_free in (True, None) and cell.marker_free in (True, None)
        assert r2._prompt_numerals_ok(structure, 0, cell.prompt, cell.value)


@pytest.mark.parametrize("sid", SIDS)
def test_pairs_differ_only_in_the_attachment_and_d_is_not_on_the_target(sid, certs):
    spec = m.SPECS[sid]
    for pair, rec in zip(spec.pairs, certs[sid]["pairs"], strict=True):
        assert pair.frame_matched and rec["same_frame_numeral_unit"]
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        d_sentence = r2.pair_sentence(pair, "D", spec.values[0], spec.unit)
        assert r_sentence.replace(pair.r_attach, "@") == d_sentence.replace(pair.d_attach, "@")
        assert abs(len(r_sentence.split()) - len(d_sentence.split())) <= r2.MAX_WORD_DIFF
        assert r2.pair_sentence(pair, "D", None, spec.unit).count(pair.d_attach) == 1
        assert rec["d_not_on_target"] and rec["reversal_free"] and len(pair.d_rationale) >= r2.MIN_RATIONALE
        assert pair.conditions_preserved and rec["conditions_in_base_text"]
        assert not any(ch.isdigit() for ch in pair.r_attach + pair.d_attach)
    assert r2.prior_marker_hits(spec.pairs[1].d_attach)  # the same-object D is anchored in time away from the stated situation
    assert not r2.prior_marker_hits(spec.pairs[1].r_attach)


@pytest.mark.parametrize("sid", SIDS)
def test_study_and_heldout_values_pass_hygiene(sid, certs):
    for name, items in certs[sid]["hygiene"].items():
        for h in items:
            assert h["ok"] and not h["equals_input"], (sid, name, h)
            assert h["digit_overlap_with_inputs"] <= r2.MAX_DIGIT_OVERLAP and h["digit_overlap_with_gold"] <= r2.MAX_DIGIT_OVERLAP
    assert certs[sid]["checks"]["foils_not_equal_to_other_cells_golds"]["ok"]
    assert certs[sid]["checks"]["no_confounded_foils_except_degenerate"]["ok"]


def test_the_certifier_rejects_planted_violations():
    def cert(sid, spec):
        return r2.certify_v2(m.structure(sid), spec)

    def with_pair(spec, index, **changes):
        pairs = list(spec.pairs)
        pairs[index] = dataclasses.replace(pairs[index], **changes)
        return dataclasses.replace(spec, pairs=tuple(pairs))

    s95 = m.SPECS["S95"]
    assert "consequence_free" in cert("S95", with_pair(s95, 1, d_attach="in an earlier experiment, so the load was removed"))["failed"]
    assert "reversal_free" in cert("S95", with_pair(s95, 1, d_attach="in an earlier experiment and then taken off"))["failed"]
    assert "marker_free" in cert("S95", with_pair(s95, 0, d_attach="the second lift, which is unrelated"))["failed"]
    assert "d_not_on_target" in cert("S95", with_pair(s95, 0, d_attach="this lift"))["failed"]
    assert "d_not_on_target" in cert("S95", with_pair(s95, 1, d_attach="before the force was applied again"))["failed"]
    assert "value_hygiene" in cert("S95", dataclasses.replace(s95, values=(1200.0, 560.0, 710.0)))["failed"]  # 1200 kg is the load
    assert "scene_clause_ok" in cert("S95", dataclasses.replace(s95, scene_clause="A second lift of 2 kinds stands beside the first."))["failed"]
    assert "d0_refers_to_scene_object" in cert("S95", dataclasses.replace(s95, scene_refs=("crane",)))["failed"]
    s91 = m.SPECS["S91"]
    broken_c = dataclasses.replace(s91.cancelling, spec=dataclasses.replace(s91.cancelling.spec, expr_with_q="pi*d1**2/4*q"))
    assert not cert("S91", dataclasses.replace(s91, cancelling=broken_c))["passed"]
    bad_k = dataclasses.replace(s91.conditional, spec=dataclasses.replace(s91.conditional.spec, counter_regime_value=1000.0))
    assert not cert("S91", dataclasses.replace(s91, conditional=bad_k))["passed"]


# --- (e) the scene clause ----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_the_scene_clause_leaves_the_base_problem_and_gold_unchanged(sid, v1_rows):
    spec = m.SPECS[sid]
    scene_structure, plain = m.structure(sid), m.STRUCTURE_FACTORIES[sid]()
    clause = spec.scene_clause
    assert clause.endswith(".") and not any(ch.isdigit() for ch in clause)
    assert not r2.marker_hits(clause) and not r2.consequence_hits(clause) and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE
    # the same graph, instances and render except the context
    assert scene_structure.nodes == plain.nodes and scene_structure.instances == plain.instances
    assert scene_structure.render.question == plain.render.question
    assert scene_structure.render.context == f"{plain.render.context} {clause}"
    assert dg.structure_hash(scene_structure) == dg.structure_hash(plain)
    for i in range(len(plain.instances)):
        assert dg.gold_for(scene_structure, dict(scene_structure.instances[i])) == dg.gold_for(plain, dict(plain.instances[i]))
    # the no-cue prompt is the October problem with the clause before the question, and nothing else
    row = v1_rows[sid]
    no_cue = next(c for c in r2.role_cells_v2(scene_structure, spec, 0) if c.stratum == "none")
    assert no_cue.prompt == row["problem"].replace("\n\n", f" {clause}\n\n", 1)
    assert no_cue.gold_value == pytest.approx(row["gold_answer"]["value"], rel=1e-12)
    # the clause is in the base context of every cell of every kind, and D0 refers to the object it introduces
    cells = r2.role_cells_v2(scene_structure, spec, 0, include_heldout=True)
    extra, _ = r2.variants(scene_structure, spec, 0, [c for c in cells if not c.heldout])
    assert all(clause in c.prompt for c in [*cells, *extra])
    d0 = r2.pair_sentence(spec.pairs[0], "D", spec.values[0], spec.unit)
    assert all(ref in clause and ref in d0 for ref in spec.scene_refs)


def test_no_spec_uses_the_target_name_in_its_pair_0_d_attachment():
    for sid in SIDS:
        spec = m.SPECS[sid]
        assert spec.target_terms and not [t for t in spec.target_terms if t.lower() in spec.pairs[0].d_attach.lower()]


def test_with_changes_helper_and_structure_are_consistent():
    spec = m.with_changes("S73", values=(1.1, 2.8, 3.2))
    assert spec.values == (1.1, 2.8, 3.2) and spec.structure_id == "S73"
    assert m.structure("S73").render.context.endswith(m.SPECS["S73"].scene_clause)
