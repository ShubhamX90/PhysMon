"""Tests for the M250 phase 2 batch em: new structures S211-S220 (`lib_m250_em`) and their v2.1 role specs (`roles_m250n_em`).

(a) every structure is solver-certified, has a valid gold trace plan on every instance, and its base gold on every instance equals a
closed form written in this file; (b) every spec passes the v2.1 certificate, every R gold at every study and held-out value equals
a closed form written here, every C quantity leaves the answer invariant (checked with routes written here) and every K regime holds
at every value of every instance; (c) the v2.1 wording, lexicon and hygiene rules and the five wording rules of the M0 v2.1 panel review
(J15.1-038/039); (d) program hashes and templates are unique against every existing structure (dataset v1, October templates, every
`library*` / `lib_*` / `lib_m250_*` module); (e) the scene clause leaves the base problem and its gold unchanged; plus mutation tests."""

from __future__ import annotations

import dataclasses
import glob
import importlib
import math
import re
from pathlib import Path

import numpy as np
import pytest
import yaml
from scipy.integrate import solve_ivp

from physmon.benchmark.v2 import certify as ce
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_em as lib
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_em as m
from physmon.benchmark.v2 import trace as tr

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = m.SPECS
SIDS = sorted(SPECS)
STRUCTURES = lib.STRUCTURES
G = 9.8
PI = math.pi


def inst(sid: str, i: int = 0) -> dict[str, float]:
    return dict(STRUCTURES[sid].instances[i])


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


# --- independent closed forms of the base answer (inputs in display units of the structure; result in the answer unit) -----------------


def _s211(i):  # field in the cavity E0 d/R from superposition of two uniformly charged balls; a = q E / m  (m/s^2)
    return (i["q0"] * 1e-6) * (i["E0"] * 1e3) * (i["d"] / i["R"]) / (i["m"] * 1e-3)


def _s212(i):  # capacitance (uF) that cancels the inductive susceptance X_L / |Z|^2
    w = 2 * PI * i["f"]
    xl = w * i["L"] * 1e-3
    return xl / (w * (i["R"] ** 2 + xl ** 2)) * 1e6


def _s213(i):  # spot displacement (cm): tan(theta) (ell/2 + L), tan(theta) = Vd ell / (2 d Va)
    return i["Vd"] * i["ell"] / (2 * i["d"] * i["Va"]) * (i["ell"] / 2 + i["L"])


def _s214(i):  # charge (mC): N B0 pi rc^2 / R
    return i["N"] * (i["B0"] * 1e-3) * PI * (i["rc"] * 1e-2) ** 2 / i["R"] * 1e3


def _s215(i):  # first-arrival load voltage (V)
    z0 = math.sqrt(i["Ltot"] * 1e-3 / (i["Ctot"] * 1e-9))
    return 2 * i["RL"] * i["Vs"] * z0 / ((i["Rs"] + z0) * (i["RL"] + z0))


def _s216(i):  # largest voltage on the second capacitor (V): 2 Veq - V2, charge in uC
    return 2 * (i["C1"] * i["V0"] + i["C2"] * i["V2"]) / (i["C1"] + i["C2"]) - i["V2"]


def _s217_parts(i):
    th = math.radians(i["theta"])
    qe = i["qb"] * 1e-6 * i["E"] * 1e3
    weight = i["m"] * G
    normal = weight * math.cos(th) + qe * math.sin(th)
    drive = qe * math.cos(th) - weight * math.sin(th)
    return drive, normal


def _s217(i):  # speed (m/s)
    drive, normal = _s217_parts(i)
    return math.sqrt(2 * (drive - i["mu"] * normal) / i["m"] * i["s"])


def _s218(i):  # force (mN): (1/2) V^2 C0 d0 / d1^2
    return 0.5 * i["V"] ** 2 * (i["C0"] * 1e-12) * (i["d0"] * 1e-3) / (i["d1"] * 1e-3) ** 2 * 1e3


def _s219(i):  # pitch (m): 2 pi m vpar / (q B)
    return 2 * PI * (i["m"] * 1e-3) * i["vpar"] / ((i["qc"] * 1e-3) * i["B"])


def _s220(i):  # force (mN): (1/2) V^2 (kappa - 1) C0 / ell
    return 0.5 * i["V"] ** 2 * (i["kappa"] - 1) * (i["C0"] * 1e-12) / (i["ell"] * 1e-2) * 1e3


BASE_FORMS = {"S211": _s211, "S212": _s212, "S213": _s213, "S214": _s214, "S215": _s215, "S216": _s216, "S217": _s217, "S218": _s218,
              "S219": _s219, "S220": _s220}
# the input that the R quantity is added to (display unit of the quantity equals the input's unit)
R_INPUT = {"S211": "m", "S212": "R", "S213": "Va", "S214": "R", "S215": "Rs", "S216": "C1", "S217": "m", "S218": "V", "S219": "qc",
           "S220": "V"}


def r_form(sid: str, q: float) -> float:
    i = inst(sid)
    i[R_INPUT[sid]] += q
    return BASE_FORMS[sid](i)


def base_answer(sid: str) -> float:
    return BASE_FORMS[sid](inst(sid))


# --- (a) structures ------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_structure_is_solver_certified_and_the_base_gold_matches_the_closed_form_on_every_instance(sid):
    structure = STRUCTURES[sid]
    proof = ce.certify(structure)
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]
    assert len(structure.instances) >= 4 and structure.structure_id == sid
    for index in range(len(structure.instances)):
        assert dg.gold_for(structure, dict(structure.instances[index])) == pytest.approx(BASE_FORMS[sid](inst(sid, index)), rel=1e-9), index


@pytest.mark.parametrize("sid", SIDS)
def test_gold_trace_plan_is_valid_and_ends_on_the_gold_for_every_instance(sid):
    structure, plan = STRUCTURES[sid], lib.PLANS[sid]
    assert not tr.validate_plan(structure, plan)
    for index in range(len(structure.instances)):
        trace = tr.render_trace(structure, plan, index)
        gold = dg.gold_for(structure, dict(structure.instances[index]))
        assert trace["gold_answer"]["value"] == pytest.approx(gold, rel=1e-12)
        assert trace["steps"][-1]["kind"] == "answer" and trace["steps"][-1]["value"] == pytest.approx(gold, rel=1e-12)


def test_the_ten_structures_levels_and_composition():
    assert SIDS == [f"S{n}" for n in range(211, 221)] and set(lib.PLANS) == set(lib.LEVELS) == set(lib.TOPICS) == set(SIDS)
    upper = [s for s in SIDS if lib.LEVELS[s] == "upper_university"]
    multi = [s for s in SIDS if len(STRUCTURES[s].computed) >= 3]
    assert len(upper) >= 4 and len(multi) >= 4 and len(multi) == 10
    assert all(lib.LEVELS[s] in ("upper_university", "intro_university", "high_school") for s in SIDS)
    assert len({s.law_family for s in STRUCTURES.values()}) == 10 and all(s.domain == "electromagnetism" for s in STRUCTURES.values())
    assert [s.structure_id for s in lib.all_structures()] == SIDS


@pytest.mark.parametrize("sid", SIDS)
def test_every_numeral_of_the_base_prompt_is_an_input_and_a_relevant_edit_moves_the_answer(sid):
    structure = STRUCTURES[sid]
    for index in range(len(structure.instances)):
        prompt = f"{dg.context_text(structure, dict(structure.instances[index]))}\n\n{dg.question_text(structure, dict(structure.instances[index]))}"
        shown = sorted(float(dg.input_text(structure, n.name, structure.instances[index][n.name])) for n in structure.inputs)
        assert dg.prompt_numbers(prompt) == shown, (sid, index)
    node, factor = structure.relevant_edit
    edited = dict(structure.instances[0])
    edited[node] = edited[node] * factor
    assert abs(dg.gold_for(structure, edited) - base_answer(sid)) > 0.05 * abs(base_answer(sid))


@pytest.mark.parametrize("sid", SIDS)
def test_mutation_report_catches_every_planted_defect_and_passes_the_equivalent_rewrites(sid):
    rows = ce.mutation_report(STRUCTURES[sid], n_draws=4)
    for row in rows:
        assert row["outcome"] in ("caught", "passed"), row
        assert row["failed_for_an_intended_reason"], row


# --- (d) uniqueness against every existing structure --------------------------------------------------------------------------------------

def _existing_structures() -> dict[str, gr.Structure]:
    found: dict[str, gr.Structure] = {}
    for name in ("library", "library_b", "library_c", "lib_mechanics", "lib_electromagnetism", "lib_thermodynamics", "lib_optics",
                 "lib_quantum", "lib_modern", "lib_fluids"):
        for s in importlib.import_module(f"physmon.benchmark.v2.{name}").all_structures():
            found[s.structure_id] = s
    for path in sorted(glob.glob(str(REPO_ROOT / "src/physmon/benchmark/v2/lib_m250*.py"))):
        name = Path(path).stem
        if name == "lib_m250_em":
            continue
        try:  # another batch may be unfinished; it can only add structures, never remove one
            module = importlib.import_module(f"physmon.benchmark.v2.{name}")
            found.update(module.STRUCTURES)
        except Exception:  # noqa: BLE001
            continue
    return found


@pytest.fixture(scope="module")
def existing():
    return _existing_structures()


def _v1_programs() -> dict[str, str]:
    programs = {}
    for path in sorted(glob.glob(str(REPO_ROOT / "data/raw/templates/**/*.yaml"), recursive=True)):
        template = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        names = list(template["parameters"]) + ["pi"]
        programs[dg.canonical_program_hash(gr.parse_expr(str(template["governing_equation_sympy"]), names))] = template["template_id"]
    return programs


def test_canonical_program_hashes_are_unique_against_v1_decoy_and_every_existing_structure(existing):
    assert len(existing) >= 95
    assert not set(SIDS) & set(existing)
    own = {sid: dg.structure_hash(STRUCTURES[sid]) for sid in SIDS}
    assert len(set(own.values())) == len(SIDS)
    taken = {dg.structure_hash(s): sid for sid, s in existing.items()}
    assert not set(own.values()) & set(taken), {sid: taken[h] for sid, h in own.items() if h in taken}
    v1 = _v1_programs()
    assert len(v1) >= 30 and not set(own.values()) & set(v1), {sid: v1[h] for sid, h in own.items() if h in v1}
    uuids = {dg.structure_uuid(STRUCTURES[sid]) for sid in SIDS}
    assert len(uuids) == len(SIDS)


def _tokens(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for word in re.findall(r"[a-z]+", text.lower()):
        counts[word] = counts.get(word, 0) + 1
    return counts


def _cosine(a: dict[str, int], b: dict[str, int]) -> float:
    dot = sum(a[k] * b.get(k, 0) for k in a)
    return dot / math.sqrt(sum(v * v for v in a.values()) * sum(v * v for v in b.values()))


def test_templates_and_texts_differ_from_every_existing_structure_and_the_nearest_neighbour_is_far(existing):
    for sid in SIDS:
        own = STRUCTURES[sid]
        text = f"{own.render.context} {own.render.question}"
        scores = [(_cosine(_tokens(text), _tokens(f"{o.render.context} {o.render.question}")), oid) for oid, o in existing.items()]
        best, nearest = max(scores)
        assert best < 0.9, (sid, nearest, best)  # the nearest neighbour by bag-of-words cosine of the base text
        assert all(o.render.context != own.render.context and o.law_family != own.law_family and o.title != own.title
                   for o in existing.values())
        signature = {(round(float(v), 6), n.unit) for n in own.inputs for v in [own.instances[0][n.name]]}
        for oid, o in existing.items():
            for k in range(len(o.instances)):
                other = {(round(float(o.instances[k][n.name]), 6), n.unit) for n in o.inputs}
                assert len(signature & other) / len(signature) < 1.0 or len(signature) < 3, (sid, oid, k)


# --- (b) role certification and independent closed forms ----------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(SPECS[sid], cert)
    spec = SPECS[sid]
    assert spec.version == "v2.1" and spec.structure_id == sid and len(spec.values) == 3 and len(spec.heldout_values) == 2
    assert spec.relevant.rationale and len(spec.scene_object_rationale) >= r2.MIN_RATIONALE


def test_the_batch_records_what_is_infeasible_or_absent_and_meets_the_composition_targets(certs):
    assert set(m.STRUCTURE_FACTORIES) == set(SIDS) == set(m.TARGET_TERMS) and m.INFEASIBLE == {}
    for sid in SIDS:
        assert (SPECS[sid].cancelling is None) == (sid in m.NO_C) and (SPECS[sid].conditional is None) == (sid in m.NO_K)
    assert all(len(reason) >= r2.MIN_RATIONALE for reason in [*m.NO_C.values(), *m.NO_K.values()])
    c = [s for s in SIDS if SPECS[s].cancelling is not None]
    k = [s for s in SIDS if SPECS[s].conditional is not None]
    famous = [s for s in c if SPECS[s].cancelling.familiarity == "famous"]
    assert (len(c), len(k), famous) == (7, 4, ["S214", "S219"]) and len(c) >= 6 and len(k) >= 4 and len(famous) <= 3
    assert set(m.K_KINDS) == set(k) and all(len(v) > 20 for v in m.K_KINDS.values())
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values


@pytest.mark.parametrize("sid", SIDS)
def test_every_r_gold_at_every_value_equals_the_closed_form_and_every_other_gold_the_base(sid, cells):
    spec = SPECS[sid]
    seen_r = set()
    for cell in cells[sid]:
        if cell.stratum == "R":
            assert cell.gold_value == pytest.approx(r_form(sid, cell.value), rel=1e-9), cell.cell_id
            seen_r.add(cell.value)
        else:
            assert cell.stratum in ("none", "N", "D", "C", "K"), cell.cell_id
            assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9), cell.cell_id
    assert seen_r == {*spec.values, *spec.heldout_values}
    golds = [r_form(sid, v) for v in spec.values]
    assert all(abs(g - base_answer(sid)) > rv.LOOSEST_REL_TOL * max(g, base_answer(sid)) for g in golds)
    assert len({round(g, 6) for g in golds}) == 3


@pytest.mark.parametrize("sid", SIDS)
def test_the_r_and_d_cells_exist_in_both_pairs_and_n_has_no_numeral(sid, cells):
    spec = SPECS[sid]
    r_cells = [c for c in cells[sid] if c.stratum == "R"]
    d_cells = [c for c in cells[sid] if c.stratum == "D"]
    assert len(r_cells) == len(d_cells) == 2 * (len(spec.values) + len(spec.heldout_values))
    assert {c.pair_id for c in r_cells} == {"p0", "p1"} == {c.pair_id for c in d_cells}
    n_cells = [c for c in cells[sid] if c.stratum == "N"]
    assert len(n_cells) == 2 and all(not any(ch.isdigit() for ch in c.sentence) and c.value is None for c in n_cells)
    assert [c.d_kind for c in n_cells] == ["other_object_same_scene", "same_object_other_event"]


# --- C: invariance with routes written here ---------------------------------------------------------------------------------------------

def _s211_c(radius_cm):  # superposition of a whole uniformly charged ball and a ball of opposite charge density in the cavity
    i, eps0 = inst("S211"), 8.854e-12
    big_r, d, a = i["R"] * 1e-2, i["d"] * 1e-2, radius_cm * 1e-2
    rho = 3 * eps0 * i["E0"] * 1e3 / big_r
    point = np.array([d + 0.013, 0.007, -0.004])  # an arbitrary point inside the cavity (offset 15 mm from its centre)
    to_cavity = point - np.array([d, 0.0, 0.0])
    removed = rho * 4 / 3 * PI * a ** 3 * to_cavity / (4 * PI * eps0 * a ** 3)
    whole = rho * 4 / 3 * PI * big_r ** 3 * point / (4 * PI * eps0 * big_r ** 3)
    return i["q0"] * 1e-6 * float(np.linalg.norm(whole - removed)) / (i["m"] * 1e-3)


def _s212_c(volts):  # phasor currents with the supply voltage as the reference
    i = inst("S212")
    w = 2 * PI * i["f"]
    motor_current = volts / complex(i["R"], w * i["L"] * 1e-3)
    return -motor_current.imag / (w * volts) * 1e6


def _s213_c(mass_u):  # one elementary charge on an ion of the given mass, with plates, time of flight and drift
    i, e = inst("S213"), 1.602176634e-19
    mass = mass_u * 1.66053906660e-27
    speed = math.sqrt(2 * e * i["Va"] / mass)
    a_y = e * i["Vd"] / (mass * i["d"] * 1e-2)
    t = i["ell"] * 1e-2 / speed
    y_exit = 0.5 * a_y * t * t
    return (y_exit + a_y * t * i["L"] * 1e-2 / speed) * 1e2


def _s214_c(ms):  # constant emf over the time the field takes, current times that time
    i, t = inst("S214"), ms * 1e-3
    emf = i["N"] * i["B0"] * 1e-3 * PI * (i["rc"] * 1e-2) ** 2 / t
    return emf / i["R"] * t * 1e3


def _s215_c(length_m):  # per-metre parameters, then the wave and load-end equations as a linear system
    i = inst("S215")
    z0 = math.sqrt((i["Ltot"] * 1e-3 / length_m) / (i["Ctot"] * 1e-9 / length_m))
    launched, _ = np.linalg.solve(np.array([[1.0, i["Rs"]], [1.0, -z0]]), np.array([i["Vs"], 0.0]))
    v_load, _, _ = np.linalg.solve(np.array([[1.0, 0.0, -1.0], [0.0, z0, 1.0], [1.0, -i["RL"], 0.0]]), np.array([launched, launched, 0.0]))
    return float(v_load)


def _s216_c(mh):  # time integration of the lossless circuit with the given inductance
    i, ind = inst("S216"), mh * 1e-3
    c1, c2, v0, v2 = i["C1"] * 1e-6, i["C2"] * 1e-6, i["V0"], i["V2"]
    total = c1 * v0 + c2 * v2
    omega = math.sqrt((c1 + c2) / (ind * c1 * c2))
    end = 1.5 * 2 * PI / omega
    sol = solve_ivp(lambda t, y: [y[1], ((total - y[0]) / c1 - y[0] / c2) / ind], (0.0, end), [c2 * v2, 0.0],
                    t_eval=np.linspace(0.0, end, 200001), rtol=1e-12, atol=1e-18)
    return float(sol.y[0].max() / c2)


def _s219_c(v_perp):  # radius, period of the projected circle, advance along the field
    i = inst("S219")
    radius = i["m"] * 1e-3 * v_perp / (i["qc"] * 1e-3 * i["B"])
    return i["vpar"] * 2 * PI * radius / v_perp


C_ROUTES = {"S211": _s211_c, "S212": _s212_c, "S213": _s213_c, "S214": _s214_c, "S215": _s215_c, "S216": _s216_c, "S219": _s219_c}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value(sid, cells):
    spec = SPECS[sid].cancelling
    tolerance = 1e-5 if sid in ("S211", "S216") else 1e-9
    for q in (*spec.spec.values, *spec.heldout_values):
        assert C_ROUTES[sid](q) == pytest.approx(base_answer(sid), rel=max(tolerance, 1e-9) if sid != "S211" else 5e-4), q
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


# --- K: the regime holds at every value of every instance and fails at the counter value ------------------------------------------------------

def _k214(i, q):  # the coil lies inside the solenoid: rc < q (cm)
    return i["rc"] < q


def _k217(i, q):  # static friction is exceeded: drive > mu_s N
    drive, normal = _s217_parts(i)
    return drive > q * normal


def _k218(i, q):  # the largest field in the gap (smallest separation) is below the breakdown field (kV/m)
    return i["V"] / (i["d0"] * 1e-3) / 1e3 < q


def _k220(i, q):  # the slab is only partly in: inserted length (cm) below the plate length
    return 0 < q < i["ell"]


K_FORMS = {"S214": _k214, "S217": _k217, "S218": _k218, "S220": _k220}


def _k_alt(sid, q, cell_instance):  # what the answer would be if the regime did not hold (question's unit)
    if sid == "S214":
        i = inst("S214", cell_instance)
        return i["N"] * i["B0"] * 1e-3 * PI * (q * 1e-2) ** 2 / i["R"] * 1e3
    return 0.0


def test_k_quantities_are_exactly_those_with_a_regime_closed_form():
    assert set(K_FORMS) == {s for s in SIDS if SPECS[s].conditional is not None}


@pytest.mark.parametrize("sid", sorted(K_FORMS))
def test_k_regime_holds_at_every_value_on_every_instance_and_fails_at_the_counter_value(sid, cells):
    spec = SPECS[sid].conditional
    structure = STRUCTURES[sid]
    assert len(structure.instances) == 4
    for q in (*spec.spec.values, *spec.heldout_values):
        assert all(K_FORMS[sid](inst(sid, k), q) for k in range(4)), q
    assert not any(K_FORMS[sid](inst(sid, k), spec.spec.counter_regime_value) for k in range(4))
    k_cells = [c for c in cells[sid] if c.stratum == "K"]
    assert len(k_cells) == 2 * len(spec.spec.values)
    for cell in k_cells:
        assert cell.gold_value == pytest.approx(base_answer(sid), rel=1e-9)  # inside the regime the answer is the base answer
        assert cell.foils["out_of_regime"] == pytest.approx(_k_alt(sid, cell.value, 0), rel=1e-9, abs=1e-12), cell.cell_id
        assert abs(cell.foils["out_of_regime"] - cell.gold_value) > rv.LOOSEST_REL_TOL * abs(cell.gold_value)
    assert not [c for c in cells[sid] if c.stratum == "K_out"] and len(spec.k_out.reason) >= r2.MIN_RATIONALE


def test_the_s217_drive_exceeds_static_friction_by_a_margin_for_the_stated_instances():
    ratios = [_s217_parts(inst("S217", k))[0] / _s217_parts(inst("S217", k))[1] for k in range(4)]
    assert min(ratios) > 1.0 and max(SPECS["S217"].conditional.spec.values) < min(ratios)
    assert all(SPECS["S217"].conditional.spec.values[j] > inst("S217")["mu"] for j in range(3))  # static above kinetic, as in physics


# --- (c) wording, lexicons, pairs, hygiene ----------------------------------------------------------------------------------------------------

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
        assert abs(len(r_sentence.split()) - len(d_sentence.split())) <= r2.MAX_WORD_DIFF  # within three words
        assert r2.pair_sentence(pair, "D", None, spec.unit).count(pair.d_attach) == 1
        assert not any(ch.isdigit() for ch in pair.r_attach + pair.d_attach)
        assert len(pair.d_rationale) >= r2.MIN_RATIONALE and pair.conditions_preserved and rec["conditions_in_base_text"]
        assert not r2.reversal_hits(d_sentence) and not r2.remoteness_hits(d_sentence)
        if pair.pair_id == "p1":
            assert r2.prior_marker_hits(pair.d_attach) and not r2.prior_marker_hits(pair.r_attach)
        else:
            assert not [t for t in spec.target_terms if t.lower() in pair.d_attach.lower()]
    assert spec.scene_refs and all(r in spec.scene_clause and r in certs[sid]["pairs"][0]["d_sentence"] for r in spec.scene_refs)


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


# --- the five wording rules of the M0 v2.1 panel review (J15.1-038/039) ---------------------------------------------------------------------

TARGET_OBJECT = {"S211": "bead", "S212": "motor", "S213": "ions", "S214": "coil", "S215": "source", "S216": "capacitor",
                 "S217": "block", "S218": "battery", "S219": "bead", "S220": "battery"}
PURPOSEFUL = ("attached", "connected", "accelerates", "added", "strapped")  # ordinary actions on a co-present object
PURPOSELESS = ("moved", "tilted", "pushed", "turned", "rotated", "shifted", "nudged", "raised")
MOMENT = r"\b(?:before|at the moment|as it enters)\b"  # ties the R event to the moment that the question asks about
PAST_AUXILIARIES = re.compile(r"\b(was|were|had|did)\b")
CONTRADICTORS = ("replaced", "instead", "changed to", "reset", "was set", "after the", "set to", "now ")


@pytest.mark.parametrize("sid", SIDS)
def test_rule_1_pair_one_r_names_the_asked_moment_on_the_same_object_and_d_is_history(sid):
    pair = SPECS[sid].pairs[1]
    assert re.search(MOMENT, pair.r_attach) and not r2.prior_marker_hits(pair.r_attach)
    assert any(word in pair.d_attach for word in ("earlier", "previous"))
    target = TARGET_OBJECT[sid]
    assert target in pair.r_attach or target in pair.frame or target in pair.d_attach or sid in ("S213", "S215", "S216", "S219")
    assert pair.d_attach.split(" for an earlier")[0].count(" ") >= 2  # D keeps the same event, only the time anchor differs


@pytest.mark.parametrize("sid", SIDS)
def test_rule_2_no_r_sentence_contradicts_a_stated_base_value_or_condition(sid):
    spec, structure = SPECS[sid], STRUCTURES[sid]
    context = dg.context_text(structure, dict(structure.instances[0])).lower()
    for pair in spec.pairs:
        sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit).lower()
        assert not any(w in sentence for w in CONTRADICTORS), sentence
        for cond in pair.conditions_preserved:  # every stated condition that the R event must leave intact is in the base
            assert cond.lower() in context
    # an extra element is added to a stated quantity, so the base text must not call that quantity a "total"
    assert "total resistance" not in context and "total capacitance of the first" not in context
    node = structure.node(R_INPUT[sid])
    assert node.kind == "input" and spec.relevant.op == "add" and spec.relevant.input_name == R_INPUT[sid]


@pytest.mark.parametrize("sid", SIDS)
def test_rule_3_the_action_on_the_co_present_object_is_ordinary_and_purposeful(sid):
    spec = SPECS[sid]
    pair = spec.pairs[0]
    sentence = r2.pair_sentence(pair, "D", spec.values[0], spec.unit).lower()
    assert any(v in sentence for v in PURPOSEFUL) and not any(re.search(rf"\b{v}\b", sentence) for v in PURPOSELESS), sentence
    assert not re.search(r"\b\d+(?:\.\d+)? ?(?:degrees|°|cm|mm) (?:farther|nearer|closer)\b", sentence)


@pytest.mark.parametrize("sid", SIDS)
def test_rule_4_the_co_present_object_is_not_of_the_targets_type(sid):
    spec, structure = SPECS[sid], STRUCTURES[sid]
    context = dg.context_text(structure, dict(structure.instances[0])).lower() + " " + dg.question_text(
        structure, dict(structure.instances[0])).lower()
    for ref in spec.scene_refs:  # the object named by the scene clause occurs nowhere else in the base problem
        assert ref.lower() not in context
    target = TARGET_OBJECT[sid]
    assert target not in spec.scene_clause.lower() and "second" not in spec.scene_clause.lower() and "identical" not in spec.scene_clause.lower()
    for ref in spec.scene_refs:
        assert target not in ref.lower()


@pytest.mark.parametrize("sid", SIDS)
def test_rule_5_r_sentences_are_present_tense_so_a_present_tense_question_has_one_reading(sid):
    spec = SPECS[sid]
    for pair in spec.pairs:
        for value in spec.values:
            assert not PAST_AUXILIARIES.search(r2.pair_sentence(pair, "R", value, spec.unit).lower())
    assert re.search(MOMENT, spec.pairs[1].r_attach)
    question = dg.question_text(STRUCTURES[sid], dict(STRUCTURES[sid].instances[0])).lower()
    assert not PAST_AUXILIARIES.search(question.split("?")[0])  # the question itself is present tense


CONDITIONS_STATED = {
    "S211": ("not to disturb", "neglect gravity", "insulating"), "S212": ("ideal sinusoidal supply", "ideal capacitor", "steady state"),
    "S213": ("evacuated", "from rest", "without striking"), "S214": ("negligible", "falls steadily"),
    "S215": ("lossless", "switched on at time zero", "uncharged"), "S216": ("no resistance", "no current", "positive plates joined"),
    "S217": ("neglect air resistance", "fixed insulating", "rests at the foot"),
    "S218": ("ideal battery", "treat the air as a vacuum", "neglect edge effects", "slowly pulled apart"),
    "S219": ("in a vacuum", "no other force", "neglect gravity"),
    "S220": ("ideal battery", "treat the air as a vacuum", "neglect fringe fields", "linear dielectric"),
}
ISOLATION_PHRASES = ("its own", "of its own", "uncharged", "well clear")


@pytest.mark.parametrize("sid", SIDS)
def test_rule_6_every_answer_determining_condition_is_stated_number_free_and_neighbours_are_isolated(sid):
    structure, spec = m.structure(sid), SPECS[sid]
    context = dg.context_text(structure, dict(structure.instances[0])).lower()
    for phrase in CONDITIONS_STATED[sid]:
        assert phrase in context, phrase
    assert any(p in spec.scene_clause.lower() for p in ISOLATION_PHRASES), spec.scene_clause
    assert not any(ch.isdigit() for ch in spec.scene_clause)


@pytest.mark.parametrize("sid", SIDS)
def test_rule_7_a_pair_one_d_event_that_attaches_or_adds_says_it_was_there_for_that_experiment_only(sid):
    pair = SPECS[sid].pairs[1]
    assert re.search(r"\bfor an earlier \w+ only$", pair.d_attach), pair.d_attach
    assert not r2.reversal_hits(r2.pair_sentence(pair, "D", SPECS[sid].values[0], SPECS[sid].unit))


@pytest.mark.parametrize("sid", SIDS)
def test_rule_8_no_d_or_n_sentence_contradicts_the_scene_clause_or_the_base(sid, cells):
    spec = SPECS[sid]
    for cell in cells[sid]:
        if cell.stratum in ("D", "N"):
            lowered = cell.sentence.lower()
            assert not re.search(r"\b(?:now|already|fills?|filled|empty|full)\b", lowered), cell.sentence
            if cell.pair_id == "p0":  # an action on the co-present object that the scene clause introduced
                assert all(ref in lowered for ref in [r.lower() for r in spec.scene_refs]) and any(v in lowered for v in PURPOSEFUL)


ARTICLE_A_BEFORE_VOWEL_SOUND = re.compile(r"\b[Aa] (?:8|11|18)(?:[.\s]|$)|\b[Aa] 8\d{1,2}(?:[.\s]|$)")


@pytest.mark.parametrize("sid", SIDS)
def test_two_different_phrasings_of_every_role_relation_and_a_grammatical_article(sid, cells):
    spec = SPECS[sid]
    for value in (*spec.values, *spec.heldout_values):
        r0, r1 = (r2.pair_sentence(p, "R", value, spec.unit) for p in spec.pairs)
        d0, d1 = (r2.pair_sentence(p, "D", value, spec.unit) for p in spec.pairs)
        assert r0 != r1 and d0 != d1, (r0, r1)
        assert r2.words(r0) != r2.words(r1)
    n0, n1 = (r2.pair_sentence(p, "D", None, spec.unit) for p in spec.pairs)
    assert n0 != n1
    # "A 8 ohm", "A 11 V", "A 18 ohm", "A 85 V" read with a vowel sound: no sentence of any stratum may use "A" there
    sentences = [c.sentence for c in cells[sid]]
    for wrapped in (spec.cancelling, spec.conditional):
        if wrapped is not None:
            sub = wrapped.spec
            sentences += [rv._sentence(sub.frame, v, sub.unit, p.relation, sub.nonnumeric_fill)
                          for v in (*sub.values, *wrapped.heldout_values) for p in sub.phrasings]
    for pair in spec.pairs:
        sentences += [r2.pair_sentence(pair, role, v, spec.unit) for role in ("R", "D") for v in (*spec.values, *spec.heldout_values)]
    bad = [t for t in sentences if ARTICLE_A_BEFORE_VOWEL_SOUND.search(t)]
    assert not bad, bad
    assert ARTICLE_A_BEFORE_VOWEL_SOUND.search("A 18 Ω resistor is connected.") and not ARTICLE_A_BEFORE_VOWEL_SOUND.search("A 3.5 Ω resistor")


# --- (e) the scene clause leaves the base problem and its answer unchanged ---------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_scene_clause_is_the_only_change_to_the_base_problem_and_the_gold_is_unchanged(sid):
    structure, original = m.structure(sid), m.STRUCTURE_FACTORIES[sid]()
    scene = SPECS[sid].scene_clause
    prompt = rv._assemble(structure, 0, "", "after_context")
    plain = rv._assemble(original, 0, "", "after_context")
    assert prompt == plain.replace("\n\n", f" {scene}\n\n", 1) and prompt.replace(f" {scene}", "", 1) == plain
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(base_answer(sid), rel=1e-9)
    assert dg.structure_hash(structure) == dg.structure_hash(original) and structure.nodes == original.nodes
    assert dg.context_text(structure, dict(structure.instances[0])).endswith(scene)
    for index in range(len(structure.instances)):
        display = dict(structure.instances[index])
        assert dg.gold_for(structure, display) == pytest.approx(dg.gold_for(original, display), rel=1e-12)
    for cell in r2.role_cells_v2(structure, SPECS[sid], 0):
        assert scene in cell.prompt and r2._prompt_numerals_ok(structure, 0, cell.prompt, cell.value)


# --- mutation tests: the certificate still rejects planted defects -----------------------------------------------------------------------------

def test_a_reversal_a_consequence_clause_a_marker_and_a_remote_d_are_rejected():
    spec = SPECS["S215"]
    assert "reversal_free" in spec_cert("S215", with_pair(spec, 1, d_attach="was connected in series with the source, removed in an earlier test"))["failed"]
    assert "consequence_free" in spec_cert("S215", with_pair(spec, 0, r_attach="connected in series with the source, so that it is damped"))["failed"]
    assert "marker_free" in spec_cert("S215", with_pair(spec, 0, d_attach="connected in series with an unrelated signal lamp"))["failed"]
    assert "remoteness_free_d" in spec_cert("S215", with_pair(spec, 0, d_attach="connected in series with the signal lamp in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S218"]
    assert "d_not_on_target" in spec_cert("S218", with_pair(spec, 0, d_attach="the battery near the plates"))["failed"]
    assert "d_not_on_target" in spec_cert("S218", with_pair(spec, 1, d_attach="was connected in series with the battery in a different run"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S218", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s214 = SPECS["S214"]
    assert "value_hygiene" in spec_cert("S214", dataclasses.replace(s214, values=(4.5, 9.5, 12.0)))["failed"]  # 12 ohm is the R input
    bad_c = dataclasses.replace(s214.cancelling, spec=dataclasses.replace(s214.cancelling.spec, expr_with_q="(N*Phi/q)/R*q*q"))
    assert not spec_cert("S214", dataclasses.replace(s214, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s214.conditional, spec=dataclasses.replace(s214.conditional.spec, counter_regime_value=100.0))
    assert not spec_cert("S214", dataclasses.replace(s214, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s214.conditional, spec=dataclasses.replace(s214.conditional.spec, values=(1.0, 2.0, 3.0)))
    assert not spec_cert("S214", dataclasses.replace(s214, conditional=low_k))["passed"]  # the coil would not lie inside the solenoid
    s217 = SPECS["S217"]
    low_static = dataclasses.replace(s217.conditional, spec=dataclasses.replace(s217.conditional.spec, values=(0.35, 0.55, 1.4)))
    assert not spec_cert("S217", dataclasses.replace(s217, conditional=low_static))["passed"]  # 1.4 exceeds the drive on instance 2
