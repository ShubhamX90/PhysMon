"""Tests for the M250 phase 2 thermodynamics batch (S221 to S230): the structures, their gold traces and their v2.1 role specs.

(a) every structure passes the existing certifier and has a valid gold plan whose rendered trace ends at the graph's gold; (b) every base gold
and every R gold (study and held-out) equals an independent closed form written in this file, not through the graph; (c) every C quantity
leaves the answer invariant (independent routes written here) and every K regime holds at every value of every instance; (d) the v2.1 wording,
lexicon, pair and hygiene rules and the five panel wording rules; (e) the scene clause leaves the base problem and its gold unchanged;
(f) the program hash and the template of every structure are new against every existing structure; plus mutation tests that the spec
certificate still rejects planted defects."""

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
from physmon.benchmark.v2 import lib_m250_thermo as lt
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_thermo as m
from physmon.benchmark.v2 import trace as tr

SPECS = m.SPECS
SIDS = sorted(SPECS)
SIGMA = 5.67e-8


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
    assert SIDS == [f"S{i}" for i in range(221, 231)] == sorted(lt.STRUCTURES) == sorted(m.STRUCTURE_FACTORIES)
    assert set(m.TARGET_TERMS) == set(SIDS) == set(lt.PLANS) == set(lt.LEVELS)
    levels = list(lt.LEVELS.values())
    assert levels.count("upper-university") >= 4 and set(levels) == {"introductory", "upper-university"}
    multistep = [s for s in SIDS if len(lt.STRUCTURES[s].computed) >= 3]
    assert len(multistep) >= 4
    assert all(len(lt.STRUCTURES[s].instances) >= 4 for s in SIDS)
    assert all(lt.STRUCTURES[s].domain == "thermodynamics" for s in SIDS)


@pytest.mark.parametrize("sid", SIDS)
def test_every_structure_is_solver_certified(sid):
    proof = cf.certify(lt.STRUCTURES[sid])
    assert proof["status"] == "SOLVER_CERTIFIED", [c for c in proof["checks"] if not c["passed"]]


@pytest.mark.parametrize("sid", SIDS)
def test_the_gold_plan_is_valid_and_its_rendered_trace_ends_at_the_gold(sid):
    structure, plan = lt.STRUCTURES[sid], lt.PLANS[sid]
    assert tr.validate_plan(structure, plan) == []
    for instance in range(len(structure.instances)):
        rendered = tr.render_trace(structure, plan, instance)
        gold = dg.gold_for(structure, dict(structure.instances[instance]))
        assert rendered["gold_answer"]["value"] == pytest.approx(gold, rel=1e-9)


# --- (f) uniqueness against every existing structure -------------------------------------------------------------------------------------

def _existing_structures() -> dict[str, gr.Structure]:
    found: dict[str, gr.Structure] = {}
    for info in pkgutil.iter_modules(v2pkg.__path__):
        if not info.name.startswith(("lib", "library")) or info.name == "lib_m250_thermo":
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
    mine = {sid: dg.structure_hash(s) for sid, s in lt.STRUCTURES.items()}
    assert len(set(mine.values())) == 10
    assert not set(mine.values()) & set(hashes.values())
    texts = {s.render.context for s in existing.values()}
    assert not {s.render.context for s in lt.STRUCTURES.values()} & texts
    laws = {s.law_family for s in existing.values()}
    assert not {s.law_family for s in lt.STRUCTURES.values()} & laws
    for sid, structure in lt.STRUCTURES.items():  # text overlap with the nearest existing structure stays low
        own = _tokens(structure)
        worst = max(len(own & _tokens(s)) / len(own | _tokens(s)) for s in existing.values())
        assert worst < 0.5, (sid, worst)


# --- (b) independent closed forms of the base and R golds --------------------------------------------------------------------------------------

def _s230(q: float) -> float:
    m1, m2, c, t1, t2 = 2.0 + q, 3.0, 900.0, 360.0, 290.0
    tf = (m1 * t1 + m2 * t2) / (m1 + m2)
    return c * (m1 * math.log(tf / t1) + m2 * math.log(tf / t2))


def _s226(q: float) -> float:
    return ((2 * (800.0 + q) ** 4 + 300.0 ** 4) / 3) ** 0.25


def _s227(q: float) -> float:
    t = 300.0 + q
    boltzmann = 3 * math.exp(-6000.0 / (8.314 * t))
    return 6.0 * boltzmann / (1 + boltzmann)


def _s228(q: float) -> float:  # minutes
    h = 25.0 + q
    return 2700 * 900 * 0.003 / h * math.log((450.0 - 300.0) / (350.0 - 300.0)) / 60


# the answer with the role quantity q in the R role (display unit of q), instance 0
R_FORMS = {
    "S221": lambda q: (2 + q) * 3.5 * 8.314 * 60 / 1000,
    "S222": lambda q: (50 + q) * (1 - 300 / 600) * 265 / (300 - 265),
    "S223": lambda q: (0.2 + q) * (334e3 / 273 + 4186 * math.log(313 / 273)),
    "S224": lambda q: -8.314 * ((1.5 + q) * math.log((1.5 + q) / (4.0 + q)) + 2.5 * math.log(2.5 / (4.0 + q))),
    "S225": lambda q: 120 * math.log(5 / 3) / math.log((9 + q) / 3),
    "S226": _s226,
    "S227": _s227,
    "S228": _s228,
    "S229": lambda q: 293 + q + 0.5 * 300 ** 2 / 2 / 130,
    "S230": _s230,
}
OCTOBER_GOLD = {sid: R_FORMS[sid](0.0) for sid in SIDS}  # the base answer: q = 0 for every add wiring


def base_answer(sid: str) -> float:
    return OCTOBER_GOLD[sid]


@pytest.mark.parametrize("sid", SIDS)
def test_the_independent_closed_form_reproduces_the_graph_gold_of_every_instance(sid):
    structure = lt.STRUCTURES[sid]
    for instance in structure.instances:
        gold = dg.gold_for(structure, dict(instance))
        assert math.isfinite(gold)
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
    assert len(c) >= 6 and len(famous) <= 3 and (len(c), len(k), famous) == (8, 3, ["S229"])
    assert set(m.K_KINDS) == set(k) and all(len(v) >= 20 for v in m.K_KINDS.values())
    for sid in c:
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"] and certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
    for sid in k:
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"] and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert SPECS[sid].conditional.k_out.feasible is False and not SPECS[sid].conditional.k_out.values


# --- (c) invariance of C and the regime of K ---------------------------------------------------------------------------------------------------

def _s221_c(p_kpa: float) -> float:  # volume from the ideal-gas law, Charles's law to the final volume, then dU + p dV, kJ
    p = p_kpa * 1e3
    v1 = 2.0 * 8.314 * 300 / p
    v2 = v1 * 360 / 300
    return (2.0 * 2.5 * 8.314 * 60 + p * (v2 - v1)) / 1000


def _s222_c(minutes: float) -> float:  # energy taken from the furnace in the run, work, heat removed, then the rate, kW
    t = minutes * 60
    q_h = 50e3 * t
    work = q_h * (1 - 300 / 600)
    q_c = work * 265 / (300 - 265)
    return q_c / t / 1000


def _s223_c(power: float) -> float:  # time to melt, heat delivered while melting, entropy of melting, then the warming, J/K
    t_melt = 0.2 * 334e3 / power
    return power * t_melt / 273 + 0.2 * 4186 * math.log(313 / 273)


def _s224_c(volume_l: float) -> float:  # compartment volumes from the amounts, then each gas expands to the whole volume
    v = volume_l * 1e-3
    v1, v2 = v * 1.5 / 4.0, v * 2.5 / 4.0
    return 8.314 * (1.5 * math.log(v / v1) + 2.5 * math.log(v / v2))


def _s225_c(k: float) -> float:  # heat current per unit length, then the fall of the temperature to the asked radius
    per_length = 2 * math.pi * k * (420 - 300) / math.log(9 / 3)
    return per_length * math.log(5 / 3) / (2 * math.pi * k)


def _s226_c(eps: float) -> float:  # fluxes with the gap conductance, then the fourth power of the shield temperature
    conductance = SIGMA * eps / (2 - eps)
    flux = conductance * (800.0 ** 4 - 300.0 ** 4) / 3
    return (800.0 ** 4 - flux / conductance) ** 0.25


def _s228_c(area: float) -> float:  # heat capacity of the plate, loss coefficient of both faces, time constant, then the time, min
    capacity = 2700 * 900 * (0.006 * area)
    loss = 2 * 25.0 * area
    return capacity / loss * math.log(150 / 50) / 60


def _s229_c(mass_g: float) -> float:  # kinetic energy, heat taken in, then the rise through m c
    mass = mass_g * 1e-3
    return 293 + 0.5 * (mass * 300 ** 2 / 2) / (mass * 130)


C_ROUTES = {"S221": _s221_c, "S222": _s222_c, "S223": _s223_c, "S224": _s224_c, "S225": _s225_c, "S226": _s226_c, "S228": _s228_c,
            "S229": _s229_c}


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


# (quantity that the regime compares with q on an instance, direction); the predicate is "quantity < q" for "lt", "T > q" for "gt"
K_QUANTITY = {"S221": (lambda i: 5 * i["T2"], "lt"), "S223": (lambda i: i["Tw"], "lt"),
              "S229": (lambda i: i["T0"] + i["f"] * i["v"] ** 2 / 2 / i["c"], "lt")}


def _k_alt(sid: str, q: float) -> float:  # the answer the regime-ignoring misuse of q would give, instance 0
    return {"S221": lambda q: 2.0 * 4.5 * 8.314 * 60 / 1000,
            "S223": lambda q: 0.2 * (334e3 / 273 + 4186 * math.log(q / 273)),
            "S229": lambda q: q}[sid](q)


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


# --- (d) wording, lexicons, pairs, hygiene and the five panel rules -----------------------------------------------------------------------

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
def test_the_five_panel_wording_rules(sid):
    spec = SPECS[sid]
    p0, p1 = spec.pairs
    # rule 1 and 5: the pair-1 R sentence is in the present tense and ties the event to the asked moment; the D sentence is anchored in an
    # earlier occasion (a prior marker) and is in the past tense
    assert re.match(r"(While|When|Before) ", p1.r_attach), p1.r_attach
    assert re.search(r"\b(is|are|has|also holds|takes|includes)\b", p1.r_attach)
    assert not re.search(r"\b(was|were|had|took|included|added)\b|(?<!has )\bwarmed\b", p1.r_attach)
    assert re.search(r"\b(was|were|took|held|included|warmed|added|wrapped)\b", p1.d_attach)
    assert not re.search(r"\bafter\b|\bwas set\b|\bhad been set\b|\bset to\b", r2.pair_sentence(p1, "R", spec.values[0], spec.unit))
    # rule 2: no R sentence contradicts a stated condition: it never restates a base quantity with 'is held at', 'is set', 'at ... K'
    for pair in spec.pairs:
        text = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        assert not re.search(r"\bset\b|\bheld at\b|\bfixed at\b|\binstead\b|\bnow\b", text), text
    # rule 3: the action on the co-present object is one of a short list of ordinary actions for that kind of object
    ordinary = ("let into the gas bottle", "to the hot-water tank by an element", "put into the dispenser", "let into the balloon",
                "round the hot-water tank", "the water in the kettle", "the water bath", "the fins of the heat sink", "the target frame",
                "poured into the mould")
    assert p0.d_attach in ordinary
    assert not re.search(r"\b\d+(\.\d+)?\s*(cm|mm|degrees|°)\b", spec.scene_clause)
    # rule 4: the co-present object is of a different type from the target and is never 'a second ...' or 'identical'
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
    structure, original = m.structure(sid), lt.STRUCTURES[sid]
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
    spec = SPECS["S230"]
    assert "reversal_free" in spec_cert("S230", with_pair(spec, 1, d_attach="In an earlier run, the hotter block was taken out of"))[
        "failed"]
    assert "consequence_free" in spec_cert("S230", with_pair(spec, 0, r_attach="added to the hotter block, so that it grows"))["failed"]
    assert "marker_free" in spec_cert("S230", with_pair(spec, 0, d_attach="poured into an unrelated mould"))["failed"]
    assert "remoteness_free_d" in spec_cert("S230", with_pair(spec, 0, d_attach="poured into the mould in the next room"))["failed"]


def test_a_co_present_d_on_the_target_and_a_same_object_d_without_a_time_anchor_are_rejected():
    spec = SPECS["S229"]
    assert "d_not_on_target" in spec_cert("S229", with_pair(spec, 0, d_attach="the bullet"))["failed"]
    assert "d_not_on_target" in spec_cert("S229", with_pair(spec, 1, d_attach="Before the shot, sunshine also warmed"))["failed"]
    assert "d0_refers_to_scene_object" in spec_cert("S229", dataclasses.replace(spec, scene_refs=("bench",)))["failed"]


def test_a_changed_value_set_breaks_hygiene_and_a_broken_cancellation_or_regime_is_rejected():
    s229 = SPECS["S229"]
    assert "value_hygiene" in spec_cert("S229", dataclasses.replace(s229, values=(9.0, 17.0, 300.0)))["failed"]  # 300 is the speed input
    bad_c = dataclasses.replace(s229.cancelling, spec=dataclasses.replace(s229.cancelling.spec, expr_with_q="T0 + f*(q*v**2/2)/(q*c)*q"))
    assert not spec_cert("S229", dataclasses.replace(s229, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s229.conditional, spec=dataclasses.replace(s229.conditional.spec, counter_regime_value=900.0))
    assert not spec_cert("S229", dataclasses.replace(s229, conditional=bad_k))["passed"]
    low_k = dataclasses.replace(s229.conditional, spec=dataclasses.replace(s229.conditional.spec, values=(300.0, 350.0, 400.0)))
    assert not spec_cert("S229", dataclasses.replace(s229, conditional=low_k))["passed"]  # the bullet would melt on instance 0
