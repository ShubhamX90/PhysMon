"""Tests for the non-physics dependency control set (plan v2.2 "Supporting conditions"; G1 decision 18; plan revision G1-G2).

Golds are re-derived here by closed-form arithmetic written independently of the node expressions and of the structure solvers.
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import nonphysics as npx  # noqa: E402
from physmon.benchmark.v2 import nonphysics_specs as sp  # noqa: E402
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402

SIDS = sorted(sp.STRUCTURES)

# Closed forms: base answer and the answer with the wired input changed, in the test's own words. Each takes the input dict
# (display values) and returns the target.
CLOSED = {
    "NP01": lambda v: v["paid"] - (v["n"] * v["p"] + v["pen"]),
    "NP02": lambda v: v["trays"] * v["per_tray"] - v["sold"] - v["gift"],
    "NP03": lambda v: v["stock"] - v["boxes"] * v["per_box"] - v["loose"],
    "NP04": lambda v: v["start"] + v["weekly"] * v["weeks"] - v["game"],
    "NP05": lambda v: v["rows"] * v["seats"] - v["sold"] - v["staff"],
    "NP06": lambda v: (v["packs"] * v["per_pack"] - v["kept"]) / v["kids"],
    "NP07": lambda v: v["soup"] + v["salads"] * v["salad"] + v["tip"] - v["coupon"],
    "NP08": lambda v: v["platters"] * v["per"] - v["eaten"] - v["taken"],
    "NP09": lambda v: v["classes"] * v["size"] - v["rows"] * v["seats"],
    "NP10": lambda v: v["rooms"] - v["cleaners"] * v["per"] * v["days"],
    "NP11": lambda v: v["goal"] - v["wins"] * v["win"] - v["draws"] * v["draw"],
    "NP12": lambda v: v["shelves"] * v["per"] - v["loaned"] - v["repair"],
    "NP13": lambda v: v["rows"] * v["per"] - v["eaten"] - v["gift"],
    "NP14": lambda v: v["periods"] * v["lesson"] + v["breaks"] * v["blen"],
    "NP15": lambda v: (v["students"] + v["teachers"]) / v["seats"],
    "NP16": lambda v: v["classes"] * v["copies"] * v["pages"] - v["have"],
}

NUMBER_RE = re.compile(r"\d")


def _inputs(sid):
    return {i.name: Fraction(str(i.value)) for i in sp.STRUCTURES[sid].inputs}


def _wired_closed(sid, q):
    spec = sp.SPECS[sid]
    v = _inputs(sid)
    x, qf = v[spec.wiring.input_name], Fraction(str(q))
    v[spec.wiring.input_name] = {"add": x + qf, "subtract": x - qf, "replace": qf, "scale": x * qf}[spec.wiring.op]
    return v


@pytest.fixture(scope="module")
def certificates():
    return {sid: npx.certify(sp.STRUCTURES[sid], sp.SPECS[sid]) for sid in SIDS}


@pytest.fixture(scope="module")
def all_cells():
    return {sid: npx.cells(sp.STRUCTURES[sid], sp.SPECS[sid]) for sid in SIDS}


def test_sixteen_structures_and_ids():
    assert SIDS == [f"NP{i:02d}" for i in range(1, 17)]
    assert set(sp.SPECS) == set(sp.STRUCTURES)


def test_every_structure_passes_every_check(certificates):
    for sid, cert in certificates.items():
        assert cert["passed"], (sid, cert["failed"])


def test_operations_are_mixed_and_q_enters_at_different_inputs():
    ops = {s.wiring.op for s in sp.SPECS.values()}
    assert ops == {"add", "subtract", "replace", "scale"}
    assert len({(sid, s.wiring.input_name) for sid, s in sp.SPECS.items()}) == 16
    nodes = [len(s.nodes) for s in sp.STRUCTURES.values()]
    assert min(nodes) >= 2 and max(nodes) <= 4
    exprs = " ".join(n.expr for s in sp.STRUCTURES.values() for n in s.nodes)
    for symbol in "+-*/":
        assert symbol in exprs


def test_cell_count_and_strata(all_cells):
    for sid, cells in all_cells.items():
        assert len(cells) == 15, sid
        strata = [c.stratum for c in cells]
        assert strata.count("none") == 1 and strata.count("N") == 2 and strata.count("R") == 6 and strata.count("D") == 6
        assert not {"C", "K", "K_out"} & set(strata)
        assert len({c.cell_id for c in cells}) == 15


def test_determinism(all_cells):
    again = {sid: npx.cells(sp.STRUCTURES[sid], sp.SPECS[sid]) for sid in SIDS}
    for sid in SIDS:
        assert [c.prompt for c in again[sid]] == [c.prompt for c in all_cells[sid]]
        assert [c.gold_value for c in again[sid]] == [c.gold_value for c in all_cells[sid]]
        assert npx.structure_hash(sp.STRUCTURES[sid]) == npx.structure_hash(sp.STRUCTURES[sid])
    hashes = {npx.structure_hash(s) for s in sp.STRUCTURES.values()}
    assert len(hashes) == 16


def test_golds_match_independent_closed_forms(all_cells):
    for sid in SIDS:
        spec = sp.SPECS[sid]
        base = CLOSED[sid](_inputs(sid))
        for q in (*spec.values, *spec.heldout_values):
            r = CLOSED[sid](_wired_closed(sid, q))
            assert math.isclose(npx.gold_r(sp.STRUCTURES[sid], spec.wiring, q)[0], float(r), rel_tol=1e-12), (sid, q)
            assert math.isclose(npx.gold_r(sp.STRUCTURES[sid], spec.wiring, q)[1], float(r), rel_tol=1e-12), (sid, q)
        for cell in all_cells[sid]:
            if cell.stratum == "R":
                expect = CLOSED[sid](_wired_closed(sid, cell.value))
            else:
                expect = base
            assert math.isclose(cell.gold_value, float(expect), rel_tol=1e-12), (sid, cell.cell_id)


def test_answers_exact_sensible_and_whole_for_counts():
    for sid in SIDS:
        st, spec = sp.STRUCTURES[sid], sp.SPECS[sid]
        for q in (None, *spec.values, *spec.heldout_values):
            inputs = _inputs(sid) if q is None else npx.wired(st, spec.wiring, q)
            values = npx.node_values(st, inputs)
            answer = values[st.target]
            assert answer > 0, (sid, q)
            if st.target_unit in npx.MONEY_UNITS:
                assert (answer * 100).denominator == 1
            else:
                assert answer.denominator == 1, (sid, q)
            for node in st.nodes:
                if node.integral:
                    assert values[node.name].denominator == 1, (sid, q, node.name)


def test_r_separated_from_d_and_distinct(all_cells):
    for sid, cells in all_cells.items():
        y_d = [c.gold_value for c in cells if c.stratum == "D"][0]
        rs = sorted({c.gold_value for c in cells if c.stratum == "R"})
        assert len(rs) == 3
        for y in rs:
            assert abs(y - y_d) > 0.01 * max(abs(y), abs(y_d))
        assert all(abs(a - b) > 0.01 * max(a, b) for a, b in zip(rs, rs[1:], strict=False))
        assert {c.gold_value for c in cells if c.stratum in ("D", "N", "none")} == {y_d}


def test_pairs_follow_the_m0_v2_rules(certificates):
    for sid in SIDS:
        spec = sp.SPECS[sid]
        assert [p.pair_id for p in spec.pairs] == ["p0", "p1"]
        assert spec.pairs[0].d_kind == "other_object_same_scene"
        assert spec.pairs[1].d_kind == "same_object_other_event"  # never an undone event (plan revision G1)
        assert len(spec.values) == 3 and len(spec.heldout_values) == 2
        for rec in certificates[sid]["pairs"]:
            assert rec["same_frame_numeral_unit"] and rec["word_count_ok"]
            assert abs(rec["word_counts"][0] - rec["word_counts"][1]) <= 3
            assert all(rec["consequence_free"].values()) and all(rec["marker_free"].values())
            assert rec["remoteness_free_d"] and rec["attach_has_no_digit"]
            assert len(rec["d_rationale"]) >= r2.MIN_RATIONALE
            assert rec["conditions_in_base_text"] and rec["conditions_preserved"]
            assert not NUMBER_RE.search(rec["n_sentence"])


def test_no_identical_sentences_across_pairs(all_cells):
    for sid, cells in all_cells.items():
        for stratum in ("R", "D"):
            sentences = [c.sentence for c in cells if c.stratum == stratum and c.value_index == 0]
            assert len(sentences) == 2 and sentences[0] != sentences[1], (sid, stratum, sentences)
        ns = [c.sentence for c in cells if c.stratum == "N"]
        assert len(set(ns)) == 2, sid


def test_no_undone_kind():
    for spec in sp.SPECS.values():
        assert all(pair.d_kind != "same_object_undone_event" for pair in spec.pairs)


def test_co_present_object_is_in_the_base_context_of_every_cell(all_cells):
    for sid, cells in all_cells.items():
        spec = sp.SPECS[sid]
        context = npx.context_text(sp.STRUCTURES[sid])
        assert not NUMBER_RE.search(re.sub(r"\{[^}]*\}", "", sp.STRUCTURES[sid].context.split(". ")[-1]))
        for cell in cells:
            assert cell.prompt.startswith(context)
        # the words that the D attachment adds against the R attachment name an object of the base context
        diff = r2.token_difference(r2.pair_sentence(spec.pairs[0], "R", 5.0, spec.unit),
                                   r2.pair_sentence(spec.pairs[0], "D", 5.0, spec.unit))
        added = {re.sub(r"'s$", "", w.strip(".,")).lower() for w in diff["added"]}
        keys = {w for w in added if len(w) >= 3 and w not in {"the", "for", "this"}}
        assert any(k in context.lower() for k in keys), (sid, keys, context)


def test_marker_and_consequence_flags_on_cells(all_cells):
    for cells in all_cells.values():
        for c in cells:
            if c.stratum != "none":
                assert c.consequence_free is True and c.marker_free is True
                assert not r2.marker_hits(c.sentence) and not r2.consequence_hits(c.sentence)


def test_numerals_are_inputs_and_value_hygiene(all_cells, certificates):
    for sid, cells in all_cells.items():
        st = sp.STRUCTURES[sid]
        for c in cells:
            assert npx.prompt_numerals_ok(st, c.prompt, c.value), (sid, c.cell_id)
        shown = set(npx.displayed_inputs(st).values())
        for h in certificates[sid]["hygiene"]["R_D"] + certificates[sid]["hygiene"]["R_D_heldout"]:
            assert h["ok"] and h["value"] not in shown
            assert h["digit_overlap_with_inputs"] <= 1 and h["digit_overlap_with_gold"] <= 1
        for c in cells:
            if c.value is not None:
                assert c.digit_overlap_with_inputs <= 1 and c.digit_overlap_with_gold <= 1


def test_r_answers_separated_from_d_answers_in_values():
    for sid in SIDS:
        st, spec = sp.STRUCTURES[sid], sp.SPECS[sid]
        y_d = npx.gold_base(st)
        for q in (*spec.values, *spec.heldout_values):
            assert not math.isclose(float(npx.gold_r(st, spec.wiring, q)[0]), y_d, rel_tol=0.01)
            assert float(q) not in {y_d}


def test_foils_and_placebo(all_cells):
    for sid, cells in all_cells.items():
        for c in cells:
            if c.stratum == "R":
                assert c.placebo is not None and "neglect" in c.foils
                assert abs(c.placebo - c.gold_value) > 0.01 * abs(c.gold_value)
                assert (f"{sp.SPECS[sid].wiring.op}:{sp.SPECS[sid].wiring.input_name}") not in c.foils
            if c.stratum == "D":
                assert "relevant_twin" in c.foils and c.placebo is None
            if c.stratum in ("R", "D"):
                assert ("copy" in c.foils) != ("digit_copy" in c.foils)
        kinds = {k.split(":")[0] for c in cells if c.stratum == "R" for k in c.foils}
        assert {"neglect"} <= kinds
    names = {k.split(":")[0] for cells in all_cells.values() for c in cells for k in c.foils}
    assert {"copy", "digit_copy", "add", "subtract", "replace"} <= names


def test_no_physics_vocabulary_in_any_prompt(all_cells):
    for sid, cells in all_cells.items():
        for c in cells:
            assert npx.physics_hits(c.prompt) == [], (sid, c.cell_id, npx.physics_hits(c.prompt))
    assert npx.physics_hits("The speed of the force") == ["speed", "force"]
    assert npx.physics_hits("a temperature of 5 metres") == ["temperature", "metre"] or set(
        npx.physics_hits("a temperature of 5 metres")) == {"temperature", "metre"}


def test_traces_end_at_gold_and_have_role_steps(all_cells):
    for sid, cells in all_cells.items():
        st, spec = sp.STRUCTURES[sid], sp.SPECS[sid]
        for c in cells:
            trace = npx.trace_for_cell(st, spec, c)
            assert math.isclose(trace["gold_answer"]["value"], c.gold_value, rel_tol=1e-9), (sid, c.cell_id)
            assert trace["steps"][-1]["kind"] == "answer" and trace["steps"][-1]["value"] == trace["gold_answer"]["value"]
            kinds = [s["kind"] for s in trace["steps"]]
            assert [s["n"] for s in trace["steps"]] == list(range(1, len(kinds) + 1))
            assert ("role_entry" in kinds) == (c.stratum == "R")
            assert ("role_note" in kinds) == (c.stratum in ("D", "N"))
            assert kinds.count("derive") == len(st.nodes)
            if c.stratum == "D":
                assert "no path" in trace["text"]
            assert trace["text"].count("Step ") == len(kinds)


def test_target_naming_fields(all_cells):
    for sid in SIDS:
        st = sp.STRUCTURES[sid]
        assert st.target in st.target_symbols
        assert any(p.lower() in st.question.lower() for p in st.target_phrases)


def test_mutations_are_rejected():
    import dataclasses

    sid = "NP01"
    st, spec = sp.STRUCTURES[sid], sp.SPECS[sid]
    # a study value equal to a displayed input
    bad = dataclasses.replace(spec, values=(4.0, spec.values[1], spec.values[2]))
    assert "value_hygiene" in npx.certify(st, bad)["failed"]
    # a marker word in a D attachment
    pair = dataclasses.replace(spec.pairs[0], d_attach="in Tom's basket, unrelated to hers")
    bad = dataclasses.replace(spec, pairs=(pair, spec.pairs[1]))
    assert "marker_free" in npx.certify(st, bad)["failed"]
    # a consequence clause
    pair = dataclasses.replace(spec.pairs[0], r_attach="in Priya's basket, so she pays more")
    bad = dataclasses.replace(spec, pairs=(pair, spec.pairs[1]))
    failed = npx.certify(st, bad)["failed"]
    assert "consequence_free" in failed
    # an undone-event d kind
    pair = dataclasses.replace(spec.pairs[1], d_kind="same_object_undone_event")
    bad = dataclasses.replace(spec, pairs=(spec.pairs[0], pair))
    assert "d_kinds" in npx.certify(st, bad)["failed"]
    # word counts further than three apart
    pair = dataclasses.replace(spec.pairs[0], d_attach="in Tom's basket at the very last till on the far side")
    bad = dataclasses.replace(spec, pairs=(pair, spec.pairs[1]))
    assert "word_count_ok" in npx.certify(st, bad)["failed"]


def _load_builder():
    path = REPO_ROOT / "scripts/v2/s191_build_nonphysics_controls.py"
    module_spec = importlib.util.spec_from_file_location("s191_build", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_builder_is_deterministic_and_refuses_overwrite(tmp_path):
    builder = _load_builder()
    a, b = tmp_path / "a", tmp_path / "b"
    ma, mb = builder.build(a), builder.build(b)
    assert ma["file_sha256"] == mb["file_sha256"]
    assert ma["n_cells"] == 240 and ma["n_structures"] == 16 and not ma["excluded"]
    assert builder.main(["--out", str(a)]) == 2
    rows = [json.loads(line) for line in (a / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    traces = [json.loads(line) for line in (a / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len(traces) == 240
    assert {r["domain"] for r in rows} == {"nonphysics"}
    by_id = {t["job_id"]: t for t in traces}
    for r in rows:
        assert math.isclose(by_id[r["job_id"]]["gold_trace"]["gold_answer"]["value"], r["gold_value"], rel_tol=1e-9)
        assert r["target_symbols"] and r["target_phrases"] and r["family"] == "role_by_value"
    assert {r["d_kind"] for r in rows if r["stratum"] == "D"} == {"other_object_same_scene", "same_object_other_event"}
    cert = json.loads((a / "certificates.json").read_text(encoding="utf-8"))
    assert all(v["certificate"]["passed"] for v in cert.values())
    existing = json.loads(Path(REPO_ROOT / "data/v2/dataset/m0_v2/cells.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert set(existing) - {"textbook_familiarity_reason"} <= set(rows[0]) | {"textbook_familiarity_reason"}
