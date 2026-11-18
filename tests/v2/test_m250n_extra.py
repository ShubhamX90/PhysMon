"""Tests for the M250 phase 2 extra batch (S251 to S262): the structures, their gold traces and their v2.1 role specs.

(a) every structure passes the existing certifier and has a valid gold plan whose rendered trace ends at the graph's gold; (b) every base gold
and every R gold (study and held-out) equals an independent closed form written in this file, not through the graph; (c) every C quantity
leaves the answer invariant (independent routes written here) and every K regime holds at every value of every instance; (d) the v2.1 wording,
lexicon, pair and hygiene rules and the eight panel and judge wording rules; (e) the scene clause leaves the base problem and its gold unchanged;
(f) the program hash and the template of every structure are new against every existing structure (including the other M250 batches); plus
mutation tests that the spec certificate still rejects planted defects."""

from __future__ import annotations

import dataclasses
import importlib
import math
import pkgutil
import re

import pytest

import physmon.benchmark.v2 as v2pkg
from physmon.benchmark.v2 import certify as cf
from physmon.benchmark.v2 import design as dg
from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_extra as le
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_extra as m
from physmon.benchmark.v2 import trace as tr

SPECS = m.SPECS
SIDS = sorted(SPECS)
U = 1.66053906660e-27
YEAR = 3.15576e7


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

def test_the_batch_is_twelve_structures_with_the_required_composition():
    assert SIDS == [f"S{i}" for i in range(251, 263)] == sorted(le.STRUCTURES) == sorted(m.STRUCTURE_FACTORIES)
    assert set(m.TARGET_TERMS) == set(SIDS) == set(le.PLANS) == set(le.LEVELS)
    levels = list(le.LEVELS.values())
    assert levels.count("upper-university") >= 5 and set(levels) == {"introductory", "upper-university"}
    multistep = [s for s in SIDS if len(le.STRUCTURES[s].computed) >= 3]
    assert len(multistep) >= 5
    assert all(len(le.STRUCTURES[s].instances) >= 4 for s in SIDS)
    domains = {le.STRUCTURES[s].domain for s in SIDS}
    assert {"gravitation", "acoustics", "solid_state", "nuclear", "fluids", "statistical_physics"} == domains


@pytest.mark.parametrize("sid", SIDS)
def test_every_structure_is_solver_certified(sid):
    proof = cf.certify(le.STRUCTURES[sid])
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]


@pytest.mark.parametrize("sid", SIDS)
def test_the_gold_plan_is_valid_and_its_rendered_trace_ends_at_the_gold(sid):
    structure, plan = le.STRUCTURES[sid], le.PLANS[sid]
    assert tr.validate_plan(structure, plan) == []
    for instance in range(len(structure.instances)):
        rendered = tr.render_trace(structure, plan, instance)
        gold = dg.gold_for(structure, dict(structure.instances[instance]))
        assert rendered["gold_answer"]["value"] == pytest.approx(gold, rel=1e-9)


# --- (f) uniqueness against every existing structure -------------------------------------------------------------------------------------

def _existing_structures() -> dict[str, gr.Structure]:
    found: dict[str, gr.Structure] = {}
    for info in pkgutil.iter_modules(v2pkg.__path__):
        if not info.name.startswith(("lib", "library")) or info.name == "lib_m250_extra":
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
    mine = {sid: dg.structure_hash(s) for sid, s in le.STRUCTURES.items()}
    assert len(set(mine.values())) == 12
    assert not set(mine.values()) & set(hashes.values())
    texts = {s.render.context for s in existing.values()}
    assert not {s.render.context for s in le.STRUCTURES.values()} & texts
    laws = {s.law_family for s in existing.values()}
    assert not {s.law_family for s in le.STRUCTURES.values()} & laws
    ids = {s.structure_id for s in existing.values()}
    assert not set(le.STRUCTURES) & ids
    for sid, structure in le.STRUCTURES.items():  # text overlap with the nearest existing structure stays low
        own = _tokens(structure)
        worst = max(len(own & _tokens(s)) / len(own | _tokens(s)) for s in existing.values())
        assert worst < 0.5, (sid, worst)


# --- (b) independent closed forms of the base and R golds --------------------------------------------------------------------------------------

def _s251(q: float) -> float:  # km
    radius, g0, v = 1737e3, 1.62, 1500.0 + q
    mu = g0 * radius ** 2
    return (mu / (mu / radius - v * v / 2) - radius) / 1e3


def _s252(q: float) -> float:  # kJ
    radius, r1, r2 = 6371e3, 6771e3, 7571e3
    return (850.0 + q) * 9.8 * radius ** 2 / 2 * (1 / r1 - 1 / r2) / 1e3


def _s253(q: float) -> float:  # Pa
    z1, z2 = 1.2 * 343.0, 998.0 * 1482.0
    return 2 * z2 / (z1 + z2) * math.sqrt(2 * z1 * (0.012 + q))


def _s254(q: float) -> float:  # W/m^2
    r = 60.0 + q
    return 40.0 / (4 * math.pi * r * r) * math.exp(-0.004 * r)


def _s255(q: float) -> float:  # mm
    n = 200000.0 / 100000.0
    curvature = 24 * (0.000019 - 0.000012) * 60.0 / (1e-3 * (12 + (1 + n) * (1 + 1 / n)))
    return curvature * ((20.0 + q) / 100.0) ** 2 / 2 * 1e3


def _s256(q: float) -> float:  # kJ
    return (0.5 + q) / 0.2072 * 3 * 8.314 * 60.0 / 1e3


def _s257(q: float) -> float:  # Bq
    lp, ld = math.log(2) / (66 * 3600.0), math.log(2) / (6 * 3600.0)
    t = 24 * 3600.0
    return (4000.0 + q) * ld / (ld - lp) * (math.exp(-lp * t) - math.exp(-ld * t))


def _s258(q: float) -> float:  # Bq
    atoms = (0.004 + q) * 1e-3 / (59.93 * U)
    lam = math.log(2) / (5.27 * YEAR)
    return lam * atoms * math.exp(-lam * 8.0 * YEAR)


def _s259(q: float) -> float:  # mol
    kb = 1.381e-23
    x = 2000.0 / math.sqrt(2 * kb * (300.0 + q) / (4.003 * U))
    return 0.5 * (math.erfc(x) + 2 * x * math.exp(-x * x) / math.sqrt(math.pi))


def _collision_rate(pressure_pa: float) -> float:  # GHz
    kb = 1.381e-23
    density = pressure_pa / (kb * 300.0)
    vbar = math.sqrt(8 * kb * 300.0 / (math.pi * 28.0 * U))
    return math.sqrt(2) * density * math.pi * (370e-12) ** 2 * vbar / 1e9


def _s261(q: float) -> float:  # cm/s
    mass = (0.25 + q) * 1e-3
    volume = 4 / 3 * math.pi * (2e-3) ** 3
    return 100 * 2 * 9.8 * (2e-3) ** 2 * (mass / volume - 1260.0) / (9 * 1.0)


def _s262(q: float) -> float:  # min
    tau = 8 * 0.12 * 0.5 * 100e-4 / (math.pi * 900.0 * 9.8 * (3e-3) ** 4)
    return tau * math.log((40.0 + q) / 10.0) / 60.0


# the answer with the role quantity q in the R role (display unit of q), instance 0
R_FORMS = {
    "S251": _s251, "S252": _s252, "S253": _s253, "S254": _s254, "S255": _s255, "S256": _s256, "S257": _s257, "S258": _s258,
    "S259": _s259, "S260": lambda q: _collision_rate((80.0 + q) * 1e3), "S261": _s261, "S262": _s262,
}
BASE = {sid: R_FORMS[sid](0.0) for sid in SIDS}  # the base answer: q = 0 for every add wiring


@pytest.mark.parametrize("sid", SIDS)
def test_the_independent_closed_form_reproduces_the_graph_gold_of_instance_zero(sid):
    structure = le.STRUCTURES[sid]
    for instance in structure.instances:
        assert math.isfinite(dg.gold_for(structure, dict(instance)))
    assert dg.gold_for(structure, dict(structure.instances[0])) == pytest.approx(BASE[sid], rel=1e-9)


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
            assert cell.gold_value == pytest.approx(BASE[sid], rel=1e-9), cell.cell_id
    assert seen_r == {*spec.values, *spec.heldout_values}
    golds = [form(v) for v in spec.values]
    assert all(abs(g - BASE[sid]) > rv.LOOSEST_REL_TOL * max(g, BASE[sid]) for g in golds)
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
    assert len(c) >= 6 and len(k) >= 4 and len(famous) <= 3 and (len(c), len(k), famous) == (6, 5, ["S251"])
    assert set(m.K_KINDS) == set(k) and all(len(v) >= 20 for v in m.K_KINDS.values())
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values


# --- (c) invariance of C and the regime of K ---------------------------------------------------------------------------------------------------

def _s251_c(mass: float) -> float:  # energy of the probe in joules, then the turning point, km
    radius, g0, v = 1737e3, 1.62, 1500.0
    energy = mass * (v * v / 2 - g0 * radius)
    r_max = mass * g0 * radius ** 2 / (-energy)
    return (r_max - radius) / 1e3


def _s253_c(freq: float) -> float:  # wavelengths, impedances Z = rho lambda f, then the pressure amplitude in the water
    z1 = 1.2 * (343.0 / freq) * freq
    z2 = 998.0 * (1482.0 / freq) * freq
    transmitted = 0.012 * 4 * z1 * z2 / (z1 + z2) ** 2
    return math.sqrt(2 * z2 * transmitted)


def _s255_c(width_mm: float) -> float:  # moment and stiffness both proportional to the width, mm
    width = width_mm * 1e-3
    n = 2.0
    moment = width * 24 * (0.000019 - 0.000012) * 60.0 * (1e-3 * (12 + (1 + n) * (1 + 1 / n))) ** -1 * 1.0
    return moment / width * 0.2 ** 2 / 2 * 1e3


def _s256_c(power: float) -> float:  # time to deliver the heat, heat delivered in that time, kJ
    needed = 0.5 / 0.2072 * 3 * 8.314 * 60.0
    time = needed / power
    return power * time / 1e3


def _s259_c(p_kpa: float) -> float:  # number density, density of the fast atoms, and their ratio, mol
    kb = 1.381e-23
    x = 2000.0 / math.sqrt(2 * kb * 300.0 / (4.003 * U))
    fast_fraction = math.erfc(x) + 2 * x * math.exp(-x * x) / math.sqrt(math.pi)
    density = p_kpa * 1e3 / (kb * 300.0)
    return 0.5 * (density * fast_fraction) / density


def _s260_c(volume_l: float) -> float:  # number of molecules from the ideal-gas law, number density, then the rate, GHz
    kb, volume = 1.381e-23, volume_l * 1e-3
    count = 80e3 * volume / (kb * 300.0)
    return _collision_rate(count / volume * kb * 300.0)


C_ROUTES = {"S251": _s251_c, "S253": _s253_c, "S255": _s255_c, "S256": _s256_c, "S259": _s259_c, "S260": _s260_c}


def test_c_routes_exist_exactly_for_the_c_quantities():
    assert set(C_ROUTES) == {s for s in SIDS if SPECS[s].cancelling is not None}


@pytest.mark.parametrize("sid", sorted(C_ROUTES))
def test_c_quantity_leaves_the_answer_invariant_at_every_value(sid, cells):
    spec = SPECS[sid].cancelling
    for q in (*spec.spec.values, *spec.heldout_values):
        assert C_ROUTES[sid](q) == pytest.approx(BASE[sid], rel=1e-9), q
    c_cells = [c for c in cells[sid] if c.stratum == "C"]
    assert len(c_cells) == 2 * len(spec.spec.values)
    for cell in c_cells:
        assert cell.gold_value == pytest.approx(BASE[sid], rel=1e-9)
        wrong = cell.foils["wrong_law"]
        assert abs(wrong - cell.gold_value) > rv.LOOSEST_REL_TOL * max(abs(wrong), abs(cell.gold_value)), cell.cell_id
    assert spec.spec.intermediate_relations and spec.familiarity in r2.FAMILIARITY


def _lam(i: dict) -> float:  # mean free path in metres
    return 1.381e-23 * i["T"] / (math.sqrt(2) * math.pi * (i["d"] * 1e-12) ** 2 * i["p"] * 1e3)


def _stokes_speed(i: dict) -> float:  # m/s
    volume = 4 / 3 * math.pi * (i["r"] * 1e-3) ** 3
    return 2 * i["g"] * (i["r"] * 1e-3) ** 2 * (i["m"] * 1e-3 / volume - i["rf"]) / (9 * i["eta"])


def _drain_reynolds(i: dict) -> float:
    speed = i["rho"] * i["g"] * (i["h0"] * 1e-2) * (i["r"] * 1e-3) ** 2 / (8 * i["eta"] * i["Lc"] * 1e-2)
    return i["rho"] * speed * 2 * i["r"] * 1e-3 / i["eta"]


# (does the regime hold on an instance for the K value q in its display unit?)
K_HOLDS = {
    "S254": lambda i, q: 5 * q / 100.0 < i["r"],
    "S256": lambda i, q: i["T1"] > 2 * q,
    "S260": lambda i, q: 10 * _lam(i) < q / 100.0,
    "S261": lambda i, q: i["rf"] * _stokes_speed(i) * 2 * i["r"] * 1e-3 / i["eta"] < q,
    "S262": lambda i, q: _drain_reynolds(i) < q,
}


def _k_alt(sid: str, q: float) -> float:  # the answer a regime-ignoring misuse of q would give, instance 0 (target display unit)
    if sid == "S254":
        return 40.0 * math.exp(-0.004 * 60.0) / (math.pi * (q / 100.0) ** 2)
    if sid == "S256":
        return 0.5 / 0.2072 * (12 * math.pi ** 4 / 5) * 8.314 * (360.0 ** 4 - 300.0 ** 4) / (4 * q ** 3) / 1e3
    if sid == "S260":
        return math.sqrt(8 * 1.381e-23 * 300.0 / (math.pi * 28.0 * U)) / (q / 100.0) / 1e9
    if sid == "S261":
        return BASE["S261"] / (1 + 3 * q / 16)
    return BASE["S262"] * q / 1000.0


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
        assert cell.gold_value == pytest.approx(BASE[sid], rel=1e-9)  # inside the regime the answer is the base answer
        assert cell.foils["out_of_regime"] == pytest.approx(_k_alt(sid, cell.value), rel=1e-9), cell.cell_id
        assert abs(cell.foils["out_of_regime"] - cell.gold_value) > rv.LOOSEST_REL_TOL * abs(cell.gold_value)
    assert not [c for c in cells[sid] if c.stratum == "K_out"] and len(spec.k_out.reason) >= r2.MIN_RATIONALE


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
    assert spec.pairs[0].d_kind == "other_object_same_scene"
    assert spec.pairs[1].d_kind == ("other_object_same_scene" if sid == "S258" else "same_object_other_event")
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
    assert spec.pairs[1].d_kind_note if sid == "S258" else True
    scene_refs_ok = all(r in spec.scene_clause and r in certs[sid]["pairs"][0]["d_sentence"] for r in spec.scene_refs)
    assert spec.scene_refs and scene_refs_ok


# the ordinary, purposeful actions on the co-present objects (rule 3)
ORDINARY = {
    "S251": "the weather balloon", "S252": "stowed aboard the recovery ship", "S253": "the boathouse wall", "S254": "the dog",
    "S255": "the cable is paid out", "S256": "cast onto the lead weight", "S257": "loaded into the transport container",
    "S258": "stored in the vault", "S259": "the window frame", "S260": "let into the gas cylinder", "S261": "loaded into the fishing float",
    "S262": "the bucket",
}
# rule 6: answer-deciding conditions stated number-free in the base text
CONDITIONS = {
    "S251": ("no atmosphere", "does not rotate", "no other body", "inverse-square"),
    "S252": ("inverse-square", "ignored", "circular"),
    "S253": ("normal incidence", "uniform and lossless", "nothing returns from below", "continuous across the surface"),
    "S254": ("high above the ground", "air is still", "uniformly in all directions"),
    "S255": ("do not depend on temperature", "carries no load", "curvature stays small", "slowly", "free of stress"),
    "S256": ("stays solid", "loses no heat", "classical regime", "slowly"),
    "S257": ("no daughter isotope", "stable nuclide", "Nothing is removed"),
    "S258": ("not radioactive", "nothing is added"),
    "S259": ("ideal monatomic gas", "thermal equilibrium", "Maxwell distribution"),
    "S260": ("ideal gas", "thermal equilibrium", "only collisions between molecules", "hard spheres"),
    "S261": ("at rest", "Stokes drag", "far from the walls", "stays inside"),
    "S262": ("steady and laminar", "hydrostatic pressure", "end effects", "open tank"),
}


@pytest.mark.parametrize("sid", SIDS)
def test_the_eight_wording_rules(sid):
    spec, structure = SPECS[sid], m.structure(sid)
    p0, p1 = spec.pairs
    context = dg.context_text(structure, dict(structure.instances[0]))
    first = r2.pair_sentence(p1, "R", spec.values[0], spec.unit)
    d_first = r2.pair_sentence(p1, "D", spec.values[0], spec.unit)
    # rules 1 and 5: the pair-1 R sentence is in the present tense and tied to the asked moment; the D sentence is anchored earlier
    if p1.d_kind == "same_object_other_event":
        assert re.match(r"(While|When|Before|At the start) ", p1.r_attach), p1.r_attach
        assert not re.search(r"\b(was|were|had|took|held|included|warmed|received|carried|walked)\b", p1.r_attach), p1.r_attach
        assert re.search(r"\b(was|were|had|took|held|included|warmed|received|carried|loaded|walked|slid|paid|moved|let)\b", p1.d_attach)
        assert re.match(r"(In|On) an earlier ", p1.d_attach)
        # rule 7: an event that attaches something says it applies for one run only; any other pair-1 event names an earlier experiment
        adds = "only" in p1.frame
        assert adds or p1.d_attach.startswith("In an earlier experiment"), p1.d_attach
        assert (", for one" in first and first.rstrip(".").endswith("only")) if adds else True
        assert d_first.rstrip(".").endswith("only") if adds else True
    # rule 2: no R sentence contradicts a stated condition (no restating of a base value as set or fixed)
    for pair in spec.pairs:
        text = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\bset\b|\bheld at\b|\bfixed at\b|\binstead\b|\bnow\b|\bafter\b", text), text
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
            assert not re.search(r"\b(empty|full|fills|filled|always|never|already)\b", role_text), role_text
    assert not re.search(r"\b(empty|full|fills|filled)\b", spec.scene_clause)


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
    structure, original = m.structure(sid), le.STRUCTURES[sid]
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
    spec = SPECS["S256"]
    assert "reversal_free" in spec_cert("S256", with_pair(spec, 1, d_attach="In an earlier experiment, the block was taken out of"))[
        "failed"]
    assert "consequence_free" in spec_cert("S256", with_pair(spec, 0, r_attach="cast onto the block, so that it grows"))["failed"]
    assert "marker_free" in spec_cert("S256", with_pair(spec, 0, d_attach="cast onto an unrelated lead weight"))["failed"]
    assert "remoteness_free_d" in spec_cert("S256", with_pair(spec, 0, d_attach="cast onto the lead weight in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S259"]
    assert "d_not_on_target" in spec_cert("S259", with_pair(spec, 0, d_attach="the flask"))["failed"]
    assert "d_not_on_target" in spec_cert("S259", with_pair(spec, 1, d_attach="Before the speeds are measured, sunshine also warms the flask by"))[
        "failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S259", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s256 = SPECS["S256"]
    assert "value_hygiene" in spec_cert("S256", dataclasses.replace(s256, values=(0.07, 0.18, 0.5)))["failed"]  # 0.5 is the mass input
    bad_c = dataclasses.replace(s256.cancelling, spec=dataclasses.replace(s256.cancelling.spec, expr_with_q="q*((m/M)*3*R*(T2 - T1)/q)*q"))
    assert not spec_cert("S256", dataclasses.replace(s256, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s256.conditional, spec=dataclasses.replace(s256.conditional.spec, counter_regime_value=100.0))
    assert not spec_cert("S256", dataclasses.replace(s256, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s256.conditional, spec=dataclasses.replace(s256.conditional.spec, values=(300.0, 350.0, 400.0)))
    assert not spec_cert("S256", dataclasses.replace(s256, conditional=low_k))["passed"]  # the lattice would not be classical
