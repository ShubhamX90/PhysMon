"""Tests for the M0 v2 dataset: the wording rules, value hygiene, traces, supporting cells and the builder (plan revision v2.2,
amendments A2-A9). The sealed `m0_pilot` is checked as unchanged and as reproducible by `s177` as far as it ever was."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m0, roles_m0v2  # noqa: E402
from physmon.benchmark.v2 import supporting_v2 as su  # noqa: E402
from physmon.scoring import grading_views as gv  # noqa: E402

V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
SIDS = sorted(roles_m0v2.ROLE_SPECS)
# The sealed pilot as committed (commit e0f35aa and later) and the output of the current s177 builder. They differ: the
# builder gained the digit_copy foil (G1 decision 26, commit 86977b3) and further certificate fields after the pilot was sealed.
SEALED_SHA256 = {"cells.jsonl": "01031c8dd44a9df89768496393c00c6ec8fed943568f4f80cb9e895f1c6093a4",
                 "certificates.json": "37ea4b70645a9f545890f019ff9904887470205d0361678a4847c3835d7c4072",
                 "summary.json": "5282b4dec5d0a085632b0824853a14fdc4fb5cf6e6e18a5a954a56e839f5d2c1"}
S177_REBUILD_CELLS_SHA256 = "eca63983a3b5a666ddb8733e783a4a38ee740a2868e2b930052842c62016d70d"


UNDONE_OR_OTHER = {sid: "same_object_undone_event" for sid in
                   ("S01", "S07", "S13", "S15", "S26", "S27", "S30", "S55", "S72")}
UNDONE_OR_OTHER.update({sid: "same_object_other_event" for sid in ("S02", "S20", "S92")})


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s188 = _load("s188", "scripts/v2/s188_build_m0_v2.py")
s177 = _load("s177", "scripts/v2/s177_build_m0_pilot.py")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("m0v2") / "m0_v2"
    manifest = s188.build(out, V1)
    return out, manifest


@pytest.fixture(scope="module")
def rows(built):
    return read_jsonl(built[0] / "cells.jsonl")


@pytest.fixture(scope="module")
def traces(built):
    return {r["job_id"]: r for r in read_jsonl(built[0] / "traces.jsonl")}


@pytest.fixture(scope="module")
def certs():
    return {sid: r2.certify_v2(roles_m0v2.structure(sid), roles_m0v2.ROLE_SPECS[sid]) for sid in SIDS}


def spec_cert(sid: str, spec: r2.RoleSpecV2) -> dict:
    return r2.certify_v2(roles_m0v2.structure(sid), spec)


def with_pair(spec: r2.RoleSpecV2, index: int, **changes) -> r2.RoleSpecV2:
    pairs = list(spec.pairs)
    pairs[index] = dataclasses.replace(pairs[index], **changes)
    return dataclasses.replace(spec, pairs=tuple(pairs))


# --- the builder -----------------------------------------------------------------------------------------------------------------

def test_two_builds_are_identical_and_the_builder_refuses_to_overwrite(built, tmp_path):
    out, _ = built
    second = tmp_path / "again"
    s188.build(second, V1)
    for name in ("cells.jsonl", "traces.jsonl", "certificates.json", "manifest.json", "README.md"):
        assert (out / name).read_bytes() == (second / name).read_bytes(), name
    with pytest.raises(FileExistsError):
        s188.build(second, V1)
    assert s188.main(["--out", str(second)]) == 2


def test_the_committed_dataset_is_what_the_builder_produces(built):
    committed = REPO_ROOT / "data/v2/dataset/m0_v2"
    if not committed.exists():
        pytest.skip("data/v2/dataset/m0_v2 is not built yet")
    for name in ("cells.jsonl", "traces.jsonl", "certificates.json", "manifest.json", "README.md"):
        assert sha(committed / name) == sha(built[0] / name), name


def test_m0_pilot_files_are_untouched():
    for name, digest in SEALED_SHA256.items():
        assert sha(REPO_ROOT / "data/v2/dataset/m0_pilot" / name) == digest, name


def test_s177_still_builds_what_it_built_before_m0_v2(tmp_path):
    """The old specs and `rolevalue.py` are unchanged by M0 v2: the s177 rebuild has the hash it had before this work. Against the
    sealed file it differs only by what later commits added (the digit_copy foil of decision 26)."""

    summary = s177.build(tmp_path / "m0", V1)
    assert summary["excluded"] == [] and summary["cells_sha256"] == S177_REBUILD_CELLS_SHA256
    rebuilt = read_jsonl(tmp_path / "m0" / "cells.jsonl")
    sealed = read_jsonl(REPO_ROOT / "data/v2/dataset/m0_pilot/cells.jsonl")
    assert len(rebuilt) == len(sealed)
    for new, old in zip(rebuilt, sealed, strict=True):
        new["foils"] = {k: v for k, v in new["foils"].items() if k != "digit_copy"}
        new["role"]["confounded"] = [p for p in new["role"]["confounded"] if "digit_copy" not in p]
        assert new == old, new["job_id"]


def test_counts(built, rows):
    _, manifest = built
    assert manifest["n_cells"] == len(rows) == sum(manifest["by_stratum"].values())
    expected = Counter()
    for sid in SIDS:
        spec = roles_m0v2.ROLE_SPECS[sid]
        k_out = spec.conditional is not None and spec.conditional.k_out.feasible
        for stratum, n in (("none", 1), ("N", 2), ("R", 6), ("D", 6), ("C", 6 if spec.cancelling else 0),
                           ("K", 6 if spec.conditional else 0), ("K_out", 2 * len(spec.conditional.k_out.values) if k_out else 0)):
            expected[("role_by_value", stratum)] += n
        expected[("supporting", "support")] += 11 + 5
    got = Counter((r["family"], r["stratum"]) for r in rows)
    assert got == +expected
    assert manifest["by_family"] == {"role_by_value": 262, "supporting": 192}
    assert set(manifest["file_sha256"]) == {"cells.jsonl", "traces.jsonl", "certificates.json", "README.md"}
    assert all(not r["heldout"] for r in rows)


def test_rows_carry_the_requested_fields(rows):
    needed = {"family", "d_kind", "pair_id", "consequence_free", "marker_free", "instruction", "digit_overlap_with_inputs",
              "digit_overlap_with_gold", "source_ambiguous", "foils", "placebo", "job_id", "structure_id", "instance", "cell_id", "prompt", "gold_value", "gold_unit", "cue_semantic_role",
              "unit_type", "numeric_proximity", "digit_overlap", "cue_position", "isolation_condition", "expected_effect"}
    assert all(needed <= set(r) for r in rows)
    ids = [r["job_id"] for r in rows]
    assert len(ids) == len(set(ids))
    s170 = _load("s170", "scripts/v2/s170_sampled_run.py")
    assert all(all(k in r for k in s170.JOB_FIELDS) for r in rows)
    for r in rows:
        if r["family"] == "role_by_value":
            assert r["stratum"] == "none" or (r["consequence_free"] is True and r["marker_free"] is True), r["cell_id"]
            assert r["source_ambiguous"] is False
    assert all(r["role"]["stratum"] == "support" for r in rows if r["family"] == "supporting")


def test_no_cue_prompts_are_the_october_problems(built):
    assert built[1]["no_cue_prompt_differs_from_v1"] == [] and built[1]["excluded"] == []


# --- certification and the numbers ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_every_spec_certifies(sid, certs):
    cert = certs[sid]
    assert cert["passed"], (cert["failed"], {k: cert["checks"][k]["detail"] for k in cert["failed"]})
    assert r2.complete(roles_m0v2.ROLE_SPECS[sid], cert)


G = 9.8
CLOSED_FORMS = {  # independent closed forms of the answer with the role quantity q (instance 0), written separately from the graphs
    "S01": lambda q: (5 - (3 + q)) * G / ((3 + q) + 5 + 2 / 2),
    "S02": lambda q: math.sqrt(2 * G * (math.sin(math.radians(30)) - 0.15 * math.cos(math.radians(30))) * (4 + q)),
    "S07": lambda q: 12 * (1 - math.exp(-0.08 / ((5e3 + q * 1e3) * 20e-6))),
    "S13": lambda q: 2 * math.pi * math.sqrt((0.8 + q) / G),
    "S15": lambda q: (12 + q) ** 2 * (1 / 6 + 1 / 12),
    "S20": lambda q: 12 * (40 + q) / (40 + q - 12),
    "S26": lambda q: math.degrees(math.asin(math.sin(math.radians(40 + q)) / 1.5)),
    "S27": lambda q: 101 + q + 1000 * G * 12 / 1000,
    "S30": lambda q: (2 + q) * 4186 * 40 / 1500,
    "S55": lambda q: math.sqrt(3 * 8.314 * (300 + q) / 0.004),
    "S72": lambda q: 1240 / math.sqrt(2 * 511e3 * (150 + q)) * 1000,
    "S92": lambda q: (q - 600) * G * 0.1 ** 3,
}


def test_every_gold_matches_an_independent_closed_form(rows):
    checked = 0
    for r in rows:
        if r["family"] != "role_by_value":
            continue
        f = CLOSED_FORMS[r["structure_id"]]
        base = 1000 if r["structure_id"] == "S92" else 0
        if r["stratum"] == "R":
            expected = f(r["value"])
        elif r["stratum"] == "K_out":
            expected = 12 * (1 - math.exp(-r["value"] * 1e-3 / (5e3 * 20e-6)))
        else:
            expected = f(base)
        assert r["gold_value"] == pytest.approx(expected, rel=1e-9), r["job_id"]
        checked += 1
    assert checked == 262


def test_r_and_d_are_certified_to_differ_and_cells_are_not_confounded_by_the_numeral(rows):
    for r in rows:
        if r["family"] == "role_by_value" and r["stratum"] in ("R", "D"):
            assert not r["source_ambiguous"]
    by = {r["job_id"]: r for r in rows}
    for r in rows:
        if r["family"] == "role_by_value" and r["stratum"] == "R":
            twin = by[r["job_id"].replace(":R:", ":D:").replace(f":{r['phrasing_id']}:", f":d{r['phrasing_id'][1:]}:")]
            assert twin["foils"]["relevant_twin"] == r["gold_value"]
            assert not math.isclose(twin["gold_value"], r["gold_value"], rel_tol=rv.LOOSEST_REL_TOL)


# --- wording rules ---------------------------------------------------------------------------------------------------------------

def test_the_consequence_lexicon_catches_the_m0_giveaway_and_ordinary_causal_words():
    assert r2.consequence_hits("down this same incline from where it was released, so it was already moving when the stated "
                               "distance began")
    for text in ("so that it moves with it", "therefore the mass", "thus", "hence", "because of", "since the", "which means",
                 "meaning that", "as a result", "this means", "consequently", "adding to its mass", "aiding its emf"):
        assert r2.consequence_hits(text), text
    for text in ("also placed on the shelf", "a small block is resting on the bench", "the sofa", "A 3 V cell is wired in series"):
        assert not r2.consequence_hits(text), text


def test_the_marker_lexicon_extends_the_october_one():
    assert set(rv.MARKER_WORDS) <= set(r2.MARKER_WORDS_V2) and len(r2.MARKER_WORDS_V2) > len(rv.MARKER_WORDS)
    for text in ("a block unrelated to the setup", "a separate system", "an unconnected cell", "lying unused in a drawer",
                 "disconnected from the circuit"):
        assert r2.marker_hits(text), text
    assert not r2.marker_hits("resting on the bench beside the apparatus")
    assert r2.remoteness_hits("across the floor of the next room yesterday")


@pytest.mark.parametrize("sid", SIDS)
def test_every_sentence_is_consequence_free_and_marker_free(sid):
    structure, spec = roles_m0v2.structure(sid), roles_m0v2.ROLE_SPECS[sid]
    for cell in r2.role_cells_v2(structure, spec, 0, include_heldout=True):
        assert not r2.consequence_hits(cell.sentence), cell.sentence
        assert not r2.marker_hits(cell.sentence), cell.sentence
        assert cell.consequence_free in (True, None) and cell.marker_free in (True, None)


@pytest.mark.parametrize("sid", SIDS)
def test_phrasing_pairs(sid, certs):
    spec = roles_m0v2.ROLE_SPECS[sid]
    assert [p.pair_id for p in spec.pairs] == ["p0", "p1"]
    assert spec.pairs[0].d_kind == "other_object_same_scene" and spec.pairs[1].d_kind == UNDONE_OR_OTHER[sid]
    assert spec.pairs[1].d_kind in r2.D_KINDS_SAME_OBJECT
    records = certs[sid]["pairs"]
    for pair, rec in zip(spec.pairs, records, strict=True):
        assert abs(rec["word_counts"][0] - rec["word_counts"][1]) <= r2.MAX_WORD_DIFF
        assert rec["token_difference"]["removed"] and rec["token_difference"]["added"]
        assert rec["remoteness_free_d"] and len(pair.d_rationale) >= r2.MIN_RATIONALE
        assert pair.conditions_preserved and rec["conditions_in_base_text"]
        if pair.frame_matched:
            assert rec["same_frame_numeral_unit"]
            r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
            d_sentence = r2.pair_sentence(pair, "D", spec.values[0], spec.unit)
            assert r_sentence.replace(pair.r_attach, "@") == d_sentence.replace(pair.d_attach, "@")
            assert r2.pair_sentence(pair, "D", None, spec.unit).count(pair.d_attach) == 1  # N is the D sentence without the numeral
    unmatched = [(sid, p.pair_id) for p in spec.pairs if not p.frame_matched]
    assert unmatched in ([], [("S02", "p0")], [("S26", "p0")])


def test_only_s02_and_s26_pair_0_are_declared_unmatched_and_say_why():
    unmatched = {(sid, p.pair_id): p for sid, s in roles_m0v2.ROLE_SPECS.items() for p in s.pairs if not p.frame_matched}
    assert sorted(unmatched) == [("S02", "p0"), ("S26", "p0")]
    assert all(len(p.frame_mismatch_reason) > 100 for p in unmatched.values())


def test_s26_pair_0_sentences_and_physics_unchanged():
    spec = roles_m0v2.ROLE_SPECS["S26"]
    p = spec.pairs[0]
    assert r2.pair_sentence(p, "R", 6.0, "deg") == "The incoming ray is then tilted 6° farther from the normal, in the plane of incidence."
    assert r2.pair_sentence(p, "D", 6.0, "deg") == "A ceiling lamp above the bench is then tilted 6° farther from the vertical."
    assert r2.pair_sentence(p, "D", None, "deg") == "A ceiling lamp above the bench is then tilted a little farther from the vertical."
    assert spec.relevant == rv.RelevantWiring("theta1", "add", spec.relevant.rationale) and spec.values == (6.0, 11.0, 14.0)


def test_each_numeral_appears_once_and_the_n_control_has_none(rows):
    for r in rows:
        if r["family"] == "role_by_value" and r["stratum"] == "N":
            assert not any(ch.isdigit() for ch in r["sentence"]) and r["value"] is None
            assert r["foils"] == {} and r["pair_id"] in ("p0", "p1") and r["d_kind"] is not None
    for sid in SIDS:
        d_kinds = {r["d_kind"] for r in rows if r["structure_id"] == sid and r["stratum"] == "D"}
        assert d_kinds == {"other_object_same_scene", UNDONE_OR_OTHER[sid]}


# --- value hygiene ----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_study_values_pass_hygiene(sid, certs):
    hygiene = certs[sid]["hygiene"]
    for name, items in hygiene.items():
        if "heldout" in name:
            continue
        for h in items:
            assert h["ok"] and not h["equals_input"], (sid, name, h)
            assert h["digit_overlap_with_inputs"] <= r2.MAX_DIGIT_OVERLAP and h["digit_overlap_with_gold"] <= r2.MAX_DIGIT_OVERLAP
    assert certs[sid]["checks"]["foils_not_equal_to_other_cells_golds"]["ok"]


def test_hygiene_rejects_the_old_m0_values():
    s07 = roles_m0v2.ROLE_SPECS["S07"]
    assert "value_hygiene" in spec_cert("S07", dataclasses.replace(s07, values=(1.0, 2.0, 5.0)))["failed"]  # 5 kOhm = the resistor
    s30 = roles_m0v2.ROLE_SPECS["S30"]
    assert "value_hygiene" in spec_cert("S30", dataclasses.replace(s30, values=(0.5, 1.0, 2.0)))["failed"]  # 2 kg = the water mass
    s72 = roles_m0v2.ROLE_SPECS["S72"]
    failed = spec_cert("S72", dataclasses.replace(s72, values=(50.0, 100.0, 200.0)))["failed"]
    assert "value_hygiene" in failed  # 100 eV shares its digits with the 100.15 pm answer
    s01 = roles_m0v2.ROLE_SPECS["S01"]
    assert "foils_not_equal_to_other_cells_golds" in spec_cert("S01", dataclasses.replace(s01, values=(0.4, 0.8, 1.2)))["failed"]


def test_digit_overlap_counts_leading_digits_and_ignores_magnitude():
    assert r2.digit_overlap(0.4, 40) == 3 and r2.digit_overlap(1.2, 1.67) == 1 and r2.digit_overlap(100, 100.15) == 3
    assert r2.digit_overlap(3.5, 5.0) == 0


def test_recorded_overlaps_match_a_recount(rows):
    for r in rows:
        if r["family"] == "role_by_value" and r["value"] is not None and r["stratum"] not in ("K_out",):
            structure = roles_m0v2.structure(r["structure_id"])
            shown = r2.displayed_inputs(structure, r["instance"])
            assert r["digit_overlap_with_inputs"] == max(r2.digit_overlap(r["value"], x) for x in shown.values())
            assert r["digit_overlap_with_gold"] == r2.digit_overlap(r["value"], r["gold_value"])


# --- mutation tests on the new specs (the M0 mutation tests, applied to M0 v2) --------------------------------------------------------

def test_a_consequence_clause_fails_the_certificate():
    spec = with_pair(roles_m0v2.ROLE_SPECS["S02"], 1, r_attach="down this incline, so it was already moving when the stated "
                                                              "distance began")
    assert "consequence_free" in spec_cert("S02", spec)["failed"]


def test_a_marker_word_fails_the_certificate():
    spec = with_pair(roles_m0v2.ROLE_SPECS["S13"], 0, d_attach="hanging from a nail on a nearby wall, unrelated to the pendulum")
    assert "marker_free" in spec_cert("S13", spec)["failed"]


def test_remoteness_only_wording_fails_the_certificate():
    spec = with_pair(roles_m0v2.ROLE_SPECS["S13"], 0, d_attach="coiled up in a drawer in the next room")
    assert "remoteness_free_d" in spec_cert("S13", spec)["failed"]


def test_a_pair_with_different_lengths_fails_the_certificate():
    spec = with_pair(roles_m0v2.ROLE_SPECS["S01"], 0, d_attach="resting on the bench beside the apparatus that the students "
                                                              "assembled earlier in the afternoon")
    assert "word_count_ok" in spec_cert("S01", spec)["failed"]


def test_swapped_d_kinds_and_a_missing_rationale_fail():
    spec = roles_m0v2.ROLE_SPECS["S27"]
    assert "d_kinds" in spec_cert("S27", with_pair(spec, 1, d_kind="other_object_same_scene"))["failed"]
    assert "d_kinds" in spec_cert("S27", with_pair(spec, 1, d_kind="nonsense"))["failed"]
    assert "d_kinds" not in spec_cert("S27", with_pair(spec, 1, d_kind="same_object_other_event"))["failed"]
    swapped = dataclasses.replace(spec, pairs=(dataclasses.replace(spec.pairs[0], d_kind="same_object_other_event"), spec.pairs[1]))
    assert "d_kinds" in spec_cert("S27", swapped)["failed"]
    assert "d_rationale_ok" in spec_cert("S27", with_pair(spec, 0, d_rationale="none"))["failed"]


def test_a_stated_condition_that_is_not_in_the_problem_fails():
    spec = with_pair(roles_m0v2.ROLE_SPECS["S02"], 1, conditions_preserved=("released from rest", "the block is on ice"))
    assert "conditions_in_base_text" in spec_cert("S02", spec)["failed"]


def test_a_single_pair_or_a_changed_pair_id_fails():
    spec = roles_m0v2.ROLE_SPECS["S15"]
    assert not spec_cert("S15", dataclasses.replace(spec, pairs=spec.pairs[:1]))["passed"]
    assert "exactly_two_pairs" in spec_cert("S15", with_pair(spec, 1, pair_id="p2"))["failed"]


def test_an_unmatched_frame_must_be_declared_with_a_reason():
    spec = roles_m0v2.ROLE_SPECS["S01"]
    changed = with_pair(spec, 0, d_frame="A second {value} {unit} block is {relation}.")
    assert "frame_mismatch_reason_ok" in spec_cert("S01", changed)["failed"]
    declared = with_pair(spec, 0, d_frame="A second {value} {unit} block is {relation}.",
                         frame_mismatch_reason="The second block needs its own noun phrase because it is another object here "
                                               "and the frame must say so.")
    assert spec_cert("S01", declared)["passed"]


def test_a_missing_numeral_or_a_second_numeral_in_the_prompt_fails():
    spec = roles_m0v2.ROLE_SPECS["S01"]
    assert "attach_has_no_digit" in spec_cert("S01", with_pair(spec, 0, d_attach="resting on bench number 4"))["failed"]


def test_numeric_mutations_still_fail_for_the_new_specs():
    s01 = roles_m0v2.ROLE_SPECS["S01"]
    assert "wiring_dimension" in spec_cert("S01", dataclasses.replace(s01, relevant=rv.RelevantWiring("g", "add", "x")))["numeric"]["failed"]
    assert "wiring_dimension" in spec_cert("S01", dataclasses.replace(
        s01, relevant=rv.RelevantWiring("m_eff", "add", "x")))["numeric"]["failed"]
    s30 = roles_m0v2.ROLE_SPECS["S30"]
    assert "r_separated_from_d" in spec_cert("S30", dataclasses.replace(s30, values=(0.001, 0.002, 0.003)))["numeric"]["failed"]
    s07 = roles_m0v2.ROLE_SPECS["S07"]
    assert "r_values_distinct" in spec_cert("S07", dataclasses.replace(s07, values=(2.0, 2.0, 7.0)))["numeric"]["failed"]
    structure = roles_m0v2.structure("S01")
    broken = dataclasses.replace(structure, solver=lambda *xs: 1.01 * structure.solver(*xs))
    assert "routes_agree" in r2.certify_v2(broken, s01)["numeric"]["failed"]
    bad_c = dataclasses.replace(s01.cancelling, spec=dataclasses.replace(s01.cancelling.spec, expr_with_q="(m2 - m1)*g*q"))
    assert not spec_cert("S01", dataclasses.replace(s01, cancelling=bad_c))["passed"]
    bad_k = dataclasses.replace(s01.conditional, spec=dataclasses.replace(s01.conditional.spec, counter_regime_value=1000.0))
    assert not spec_cert("S01", dataclasses.replace(s01, conditional=bad_k))["passed"]


def test_c_familiarity_is_tagged_and_checked(certs):
    tags = {}
    for sid in SIDS:
        spec = roles_m0v2.ROLE_SPECS[sid]
        if spec.cancelling is None:
            assert "c_familiarity_tag" not in certs[sid]["checks"]
            continue
        tags[sid] = spec.cancelling.familiarity
        assert certs[sid]["checks"]["c_familiarity_tag"]["ok"]
    assert set(tags.values()) <= set(r2.FAMILIARITY) and tags["S02"] == "famous" and tags["S13"] == "famous"
    assert len(tags) == 8
    spec = roles_m0v2.ROLE_SPECS["S02"]
    bad = dataclasses.replace(spec, cancelling=dataclasses.replace(spec.cancelling, familiarity="well known"))
    assert "c_familiarity_tag" in spec_cert("S02", bad)["failed"]


# --- K_out ----------------------------------------------------------------------------------------------------------------------------

def test_k_out_feasibility_is_judged_and_the_cells_are_certified(rows, certs):
    feasible = {sid: roles_m0v2.ROLE_SPECS[sid].conditional.k_out.feasible
                for sid in SIDS if roles_m0v2.ROLE_SPECS[sid].conditional is not None}
    assert feasible == {"S01": False, "S02": False, "S07": True, "S15": False, "S92": False}
    for sid in feasible:
        ko = roles_m0v2.ROLE_SPECS[sid].conditional.k_out
        assert len(ko.reason) >= r2.MIN_RATIONALE and certs[sid]["checks"]["k_out_judged"]["ok"]
        assert bool(ko.values) == ko.feasible
    k_out = [r for r in rows if r["stratum"] == "K_out"]
    assert {r["structure_id"] for r in k_out} == {"S07"} and len(k_out) == 4
    for r in k_out:
        assert r["expected_effect"] == "changes" and r["foils"]["regime_ignored"] == pytest.approx(6.608052430593341)
        assert r["gold_value"] < r["foils"]["regime_ignored"] * 0.99 and r["value"] < 80  # the break comes before the asked 80 ms
    assert certs["S07"]["checks"]["k_out_predicate_false_and_answer_moves"]["ok"]


# --- supporting cells -------------------------------------------------------------------------------------------------------------------

def test_october_near_cells_were_inside_the_grading_tolerance():
    for cue in (5.38, 5.4):
        status = su.tolerance_status(cue, "m/s", 5.386607582838665, "m/s", 3)
        assert status["rel1pct"] == "correct", cue  # a model copying the October "near" cell was graded correct


@pytest.mark.parametrize("sid", SIDS)
def test_proximity_cells_have_certified_tolerance_status(sid, rows):
    by = {r["condition"]: r for r in rows if r["structure_id"] == sid and r["family"] == "supporting"}
    exact = by["nongov_same_unit_exact"]
    assert exact["cue_equals_gold"] and set(exact["tolerance_status"][v] for v in gv.VIEWS) == {"correct"}
    assert exact["source_ambiguous"] and exact["source_ambiguous_by_design"] and exact["ambiguous_views"] == list(gv.VIEWS)
    assert exact["gold_value"] == pytest.approx(float(dg.positional(exact["gold_value"], 4)), rel=1e-3)
    for name, high in (("nongov_same_unit_near_high_overlap", True), ("nongov_same_unit_near_low_overlap", False)):
        if name not in by:
            continue
        r = by[name]
        t = r["tolerance_status"]
        assert {t[v] for v in gv.VIEWS} == {"wrong"} and t["relative_error"] > 0.0105
        assert su.NEAR_OUTSIDE_MIN <= abs(r["cue_numeric_value"] / r["gold_value"] - 1) <= su.NEAR_OUTSIDE_MAX
        shared = dg.common_leading_digits(r["cue_numeric_value"], r["gold_value"])
        assert (shared >= su.HIGH_OVERLAP_MIN) if high else (shared <= su.LOW_OVERLAP_MAX)
        assert not r["source_ambiguous"] and not r["cue_equals_gold"]
        assert r["digit_overlap_with_gold"] == shared
    for name in ("nongov_same_unit_moderate", "nongov_same_unit_far", "nongov_incompatible_unit_same_digits"):
        assert {by[name]["tolerance_status"][v] for v in gv.VIEWS} == {"wrong"}
    conv = by["nongov_convertible_unit_same_magnitude"]["tolerance_status"]
    assert conv["declared"] == "wrong" and conv["convertible"] == "correct" and conv["rel1pct"] == "correct"
    inc = by["nongov_incompatible_unit_same_digits"]
    assert inc["tolerance_status"]["dimension_status"] == "WRONG_DIMENSION" and inc["cue_numeric_value"] == exact["cue_numeric_value"]
    assert conv["declared"] == "wrong" and by["nongov_convertible_unit_same_magnitude"]["source_ambiguous_by_design"]
    assert by["nongov_convertible_unit_same_magnitude"]["ambiguous_views"] == ["convertible", "rel1pct"]
    assert {c for c, r in by.items() if r["source_ambiguous"]} == {"nongov_same_unit_exact", "nongov_convertible_unit_same_magnitude"}
    assert all(r["source_ambiguous_by_design"] for r in by.values() if r["source_ambiguous"])


def test_every_infeasible_condition_in_the_committed_certificates_has_a_reason():
    path = REPO_ROOT / "data/v2/dataset/m0_v2/certificates.json"
    if not path.exists():
        pytest.skip("not built")
    data = json.loads(path.read_text(encoding="utf-8"))
    for sid, rec in data.items():
        for item in rec["infeasible"]:
            assert item["feasible"] is False and len(item["reason"]) > 30, (sid, item)


def test_near_value_is_outside_tolerance_for_a_sweep_of_golds():
    rng = np.random.default_rng(20261114)
    found = 0
    for gold in 10 ** rng.uniform(-2, 4, 300):
        for high in (True, False):
            value, status = su.near_value(float(gold), high, "m")
            if value is None:
                continue
            found += 1
            assert {status[v] for v in gv.VIEWS} == {"wrong"}
            assert su.NEAR_OUTSIDE_MIN <= abs(value / gold - 1) <= su.NEAR_OUTSIDE_MAX
    assert found > 400


def test_relevance_instruction_cells(rows):
    instr = [r for r in rows if r["instruction"] == "relevance"]
    assert len(instr) == 12 * 5 and all(r["family"] == "supporting" and r["prompt"].endswith(r2.INSTRUCTION_RELEVANCE) for r in instr)
    for sid in SIDS:
        mine = {r["cell_id"] for r in instr if r["structure_id"] == sid}
        assert mine == {"no_cue:instr_relevance", "R:z1:r0:after_context:instr_relevance", "R:z1:r1:after_context:instr_relevance",
                        "D:z1:d0:after_context:instr_relevance", "D:z1:d1:after_context:instr_relevance"}
    by = {r["cell_id"]: r for r in rows if r["structure_id"] == "S01"}
    plain = by["R:z1:r0:after_context"]
    assert by["R:z1:r0:after_context:instr_relevance"]["prompt"] == plain["prompt"] + " " + r2.INSTRUCTION_RELEVANCE
    assert by["R:z1:r0:after_context:instr_relevance"]["gold_value"] == plain["gold_value"]


def test_position_cells_are_infeasible_with_reasons_and_none_are_emitted(rows, certs):
    assert not [r for r in rows if r["position"] == "before_context"]
    for sid in SIDS:
        pair = roles_m0v2.ROLE_SPECS[sid].pairs[0]
        assert pair.before_context_ok is False and len(pair.before_context_reason) > 60
        assert certs[sid]["checks"]["before_context_judged"]["ok"]
    # a pair declared feasible would produce the before-context cells, with the sentence ahead of the context
    spec = with_pair(roles_m0v2.ROLE_SPECS["S01"], 0, before_context_ok=True)
    structure = roles_m0v2.structure("S01")
    cells = r2.role_cells_v2(structure, spec, 0)
    extra, infeasible = r2.variants(structure, spec, 0, cells)
    moved = [c for c in extra if c.position == "before_context"]
    assert len(moved) == 2 and not infeasible and all(c.prompt.startswith(c.sentence) for c in moved)


# --- traces -----------------------------------------------------------------------------------------------------------------------------

def test_every_cell_has_a_trace_that_ends_at_its_gold(rows, traces):
    assert {r["job_id"] for r in rows} == set(traces)
    for r in rows:
        t = traces[r["job_id"]]["gold_trace"]
        assert t["gold_answer"]["value"] == pytest.approx(r["gold_value"], rel=1e-9), r["job_id"]
        assert t["steps"][-1]["kind"] == "answer" and t["steps"][-1]["value"] == pytest.approx(r["gold_value"], rel=1e-9)
        assert t["text"].count("\n") + 1 == len(t["steps"]) and t["steps"][0]["kind"] == "restate"


def test_trace_content_by_stratum(rows, traces):
    for r in rows:
        t = traces[r["job_id"]]["gold_trace"]
        kinds = [s["kind"] for s in t["steps"]]
        text = t["text"]
        if r["family"] == "role_by_value" and r["stratum"] == "R":
            entry = next(s for s in t["steps"] if s["kind"] == "role_entry")
            assert entry["q"] == r["value"] and "Every later step uses the changed" in text
            assert kinds.index("role_entry") < kinds.index("derive")
        elif r["family"] == "role_by_value" and r["stratum"] in ("D", "N"):
            assert "role_note" in kinds and ("no path to the target" in text or "contains no number" in text)
            assert "role_entry" not in kinds
        elif r["family"] == "role_by_value" and r["stratum"] == "C":
            spec = roles_m0v2.ROLE_SPECS[r["structure_id"]].cancelling.spec
            assert kinds.count("c_relation") == len(spec.intermediate_relations) and "c_cancel" in kinds
            assert "derivative with respect to q is 0" in text and all(rel in text for rel in spec.intermediate_relations)
        elif r["family"] == "role_by_value" and r["stratum"] == "K":
            check = next(s for s in t["steps"] if s["kind"] == "regime_check")
            assert check["holds"] is True and check["lhs"] != check["rhs"] and "which is true" in text
        elif r["family"] == "role_by_value" and r["stratum"] == "K_out":
            check = next(s for s in t["steps"] if s["kind"] == "regime_check")
            assert check["holds"] is False and "out_of_regime" in kinds and "which is false" in text


def test_r_trace_changes_the_wired_input_in_the_derivation(rows, traces):
    r = next(x for x in rows if x["job_id"] == "S01-i0:R:z0:r0:after_context")
    t = traces[r["job_id"]]["gold_trace"]
    assert "m1' = m1 + q = 3 + 0.6 = 3.6 kg" in t["text"] and "m_eff = (3.6) + (5) + (2)/2" in t["text"]
    base = traces["S01-i0:no_cue"]["gold_trace"]
    assert base["gold_answer"]["value"] == pytest.approx(2.177777777777778)
    assert "no path" not in base["text"] and "m_eff = (3) + (5) + (2)/2" in base["text"]


def test_supporting_traces_edit_and_reversal(rows, traces):
    edit = traces["S01-i0:S:relevant_edit"]["gold_trace"]
    assert edit["gold_answer"]["value"] == pytest.approx((6 - 3) * 9.8 / (3 + 6 + 1))
    rev = traces["S01-i0:S:role_reversal"]["gold_trace"]
    assert rev["gold_answer"]["value"] == pytest.approx(2.177777777777778 - 2.83) and any(s["kind"] == "combine" for s in rev["steps"])


def test_prompt_numerals_are_inputs_plus_the_single_cue(rows):
    for r in rows:
        if r["family"] != "role_by_value":
            continue
        structure = roles_m0v2.structure(r["structure_id"])
        shown = sorted([*r2.displayed_inputs(structure, r["instance"]).values()] + ([float(rv._fmt(r["value"]))] if r["value"] is not None else []))
        assert dg.prompt_numbers(r["prompt"]) == shown, r["job_id"]


def test_the_readme_states_status_role_and_the_changes(built):
    text = (built[0] / "README.md").read_text(encoding="utf-8")
    for needle in ("EXPLORATION", "NOT yet reviewed by the LLM panel", "m0_pilot", "consequence", "other_object_same_scene",
                   "same_object_other_event", "same_object_undone_event", "textbook_familiarity", "K_out", "exact-match", "pair_frame_matched"):
        assert needle in text, needle
    assert roles_m0.ROLE_SPECS  # the old specs are still importable, unchanged


# --- independent physics checks (closed forms written here, not taken from the graphs) -----------------------------------------------------

EDITED_GOLD = {  # gold of the `relevant_edit` supporting cell (one input of instance 0 changed), written out by hand
    "S01": lambda: (6 - 3) * G / (3 + 6 + 2 / 2),  # m2 5 -> 6 kg
    "S02": lambda: math.sqrt(2 * G * (math.sin(math.radians(30)) - 0.15 * math.cos(math.radians(30))) * 6),  # d 4 -> 6 m
    "S07": lambda: 12 * (1 - math.exp(-0.120 / (5e3 * 20e-6))),  # t 80 -> 120 ms
    "S13": lambda: 2 * math.pi * math.sqrt(1.2 / G),  # L 0.8 -> 1.2 m
    "S15": lambda: 15 ** 2 * (1 / 6 + 1 / 12),  # emf 12 -> 15 V
    "S20": lambda: 12 * 50 / (50 - 12),  # do 40 -> 50 cm
    "S26": lambda: math.degrees(math.asin(math.sin(math.radians(50)) / 1.5)),  # theta1 40 -> 50 deg
    "S27": lambda: 101 + 1000 * G * 18 / 1000,  # depth 12 -> 18 m
    "S30": lambda: 2 * 4186 * 50 / 1500,  # rise 40 -> 50 K
    "S55": lambda: math.sqrt(3 * 8.314 * 375 / 0.004),  # T 300 -> 375 K
    "S72": lambda: 1240 / math.sqrt(2 * 511e3 * 187.5) * 1000,  # Ke 150 -> 187.5 eV
    "S92": lambda: (1250 - 600) * G * 0.1 ** 3,  # rho_l 1000 -> 1250 kg/m3
}
REFERENCE = {"S01": 2.83, "S02": 7.0, "S07": 8.59, "S13": 2.33, "S15": 46.8, "S20": 22.3, "S26": 33.0, "S27": 284.0,
             "S30": 290.0, "S55": 1780.0, "S72": 130.0, "S92": 5.1}


def test_supporting_edit_and_reversal_golds_match_hand_formulas(rows):
    by = {(r["structure_id"], r["condition"]): r for r in rows if r["family"] == "supporting"}
    for sid in SIDS:
        assert by[(sid, "relevant_edit")]["gold_value"] == pytest.approx(EDITED_GOLD[sid](), rel=1e-9), sid
        base = CLOSED_FORMS[sid](1000 if sid == "S92" else 0)
        assert by[(sid, "role_reversal")]["gold_value"] == pytest.approx(base - REFERENCE[sid], rel=1e-9), sid
        assert by[(sid, "relevant_edit")]["gold_value"] != pytest.approx(base, rel=0.01)


def test_regime_predicates_hold_by_hand_for_every_k_value():
    """Instance-0 margins of the K regimes, written out by hand: the K values are all on the stated side of the threshold."""

    a_atwood = (5 - 3) * G / (3 + 5 + 2 / 2)
    assert max(3 * (G + a_atwood), 5 * (G - a_atwood)) == pytest.approx(38.1111, abs=1e-3)  # S01 string tension (N)
    spec = roles_m0v2.ROLE_SPECS
    assert all(v > 38.11 for v in (*spec["S01"].conditional.spec.values, *spec["S01"].conditional.heldout_values))
    assert math.tan(math.radians(30)) == pytest.approx(0.57735, abs=1e-5)  # S02 (the 40 degree instance has 0.839)
    assert all(0.15 <= v < 0.57735 for v in (*spec["S02"].conditional.spec.values, *spec["S02"].conditional.heldout_values))
    assert all(v > 80 for v in (*spec["S07"].conditional.spec.values, *spec["S07"].conditional.heldout_values))  # ms > the asked 80 ms
    assert 12 / 6 == 2.0 and all(v > 2.0 for v in (*spec["S15"].conditional.spec.values, *spec["S15"].conditional.heldout_values))
    assert (1000 - 600) * G * 0.1 ** 3 == pytest.approx(3.92) and all(
        v > 3.92 for v in (*spec["S92"].conditional.spec.values, *spec["S92"].conditional.heldout_values))
    for v in spec["S07"].conditional.k_out.values:
        assert v < 80  # the break comes before the asked time: out of the regime


def test_s01_foils_and_placebo_match_hand_formulas(rows):
    by = {r["cell_id"]: r for r in rows if r["structure_id"] == "S01"}
    q = 0.6
    r = by["R:z0:r0:after_context"]
    f = r["foils"]

    def atwood(m1, m2, pulley=2.0):
        return (m2 - m1) * G / (m1 + m2 + pulley / 2)

    assert r["gold_value"] == pytest.approx(atwood(3 + q, 5))
    assert f["neglect"] == pytest.approx(atwood(3, 5))
    assert f["add:m2"] == pytest.approx(atwood(3, 5 + q)) and f["subtract:m1"] == pytest.approx(atwood(3 - q, 5))
    assert f["replace:m1"] == pytest.approx(atwood(q, 5)) and f["replace:m2"] == pytest.approx(atwood(3, q))
    assert f["add:M"] == pytest.approx(atwood(3, 5, 2 + q))
    assert f["digit_copy"] == q and "copy" not in f  # a mass copied into an acceleration answer is a digit copy (decision 26)
    assert "add:m1" not in f  # the wiring itself is the gold, not a misuse
    assert r["placebo"] == pytest.approx(2 * atwood(3 + q, 5) - atwood(3, 5))
    d = by["D:z0:d0:after_context"]
    assert d["foils"]["relevant_twin"] == pytest.approx(atwood(3 + q, 5))


# --- the second round of review: held-out values, d_rationale on rows, the wording of the pairs ---------------------------------------------

@pytest.mark.parametrize("sid", SIDS)
def test_two_heldout_values_per_quantity_are_certified_and_clean_but_never_emitted(sid, certs, rows):
    spec = roles_m0v2.ROLE_SPECS[sid]
    assert len(spec.heldout_values) == 2 and not set(spec.heldout_values) & set(spec.values)
    quantities = [(spec.heldout_values, "R_D_heldout", ("R", "D"))]
    if spec.cancelling:
        assert len(spec.cancelling.heldout_values) == 2 and not set(spec.cancelling.heldout_values) & set(spec.cancelling.spec.values)
        assert certs[sid]["checks"]["c_heldout_two_certified"]["ok"]
        quantities.append((spec.cancelling.heldout_values, "C_heldout", ("C",)))
    if spec.conditional:
        assert len(spec.conditional.heldout_values) == 2 and not set(spec.conditional.heldout_values) & set(spec.conditional.spec.values)
        assert certs[sid]["checks"]["k_heldout_two_certified"]["ok"]
        quantities.append((spec.conditional.heldout_values, "K_heldout", ("K", "K_out")))
    assert certs[sid]["checks"]["heldout_value_hygiene"]["ok"]
    for values, name, _ in quantities:
        assert [h["value"] for h in certs[sid]["hygiene"][name]] == list(values)
        assert all(h["ok"] and not h["equals_input"] for h in certs[sid]["hygiene"][name])
    for values, _, strata in quantities:
        emitted = {r["value"] for r in rows if r["structure_id"] == sid and r["stratum"] in strata and r["family"] == "role_by_value"}
        assert emitted and not emitted & set(values)


def test_heldout_values_that_break_a_certificate_are_caught():
    s55 = roles_m0v2.ROLE_SPECS["S55"]
    # q = 1 mol makes the wrong C law sqrt(3RT/(qM)) equal the gold: the held-out value would not separate the foil
    bad = dataclasses.replace(s55, cancelling=dataclasses.replace(s55.cancelling, heldout_values=(1.0, 3.5)))
    assert "c_heldout_two_certified" in spec_cert("S55", bad)["failed"]
    s02 = roles_m0v2.ROLE_SPECS["S02"]
    bad_k = dataclasses.replace(s02, conditional=dataclasses.replace(s02.conditional, heldout_values=(0.7, 0.3)))
    assert "k_heldout_two_certified" in spec_cert("S02", bad_k)["failed"]  # mu_s = 0.7 > tan 30 deg: the block would not slide
    s01 = roles_m0v2.ROLE_SPECS["S01"]
    assert "heldout_value_hygiene" in spec_cert("S01", dataclasses.replace(s01, heldout_values=(0.7, 3.0)))["failed"]  # 3 kg = input


def test_rows_carry_the_rationale_the_token_difference_and_the_pair_frame_flag(rows):
    for r in rows:
        if r["family"] != "role_by_value" or r["stratum"] not in ("R", "D", "N"):
            continue
        diff = r["pair_token_difference"]
        assert diff["removed"] and diff["added"] and isinstance(r["pair_frame_matched"], bool)
        if r["stratum"] in ("D", "N"):
            assert len(r["d_rationale"]) >= r2.MIN_RATIONALE
        else:
            assert r["d_rationale"] is None
        assert (r["pair_frame_matched"] is False) == ((r["structure_id"], r["pair_id"]) in (("S02", "p0"), ("S26", "p0")))
    for r in rows:
        if r["family"] == "supporting":
            assert r["condition"] in {"nonnumeric_extra", "numeric_metadata", "relevant_edit", "role_reversal", "instr_relevance",
                                      *su.PROXIMITY_CELLS}, r["condition"]


def test_consequence_lexicon_covers_more_words_and_the_prompts_stay_clean():
    for text in ("accordingly the", "due to the", "ensuring that", "which is why", "contributes a force"):
        assert r2.consequence_hits(text), text
    for r in read_jsonl(REPO_ROOT / "data/v2/dataset/m0_v2/cells.jsonl") if (REPO_ROOT / "data/v2/dataset/m0_v2").exists() else []:
        if r["family"] == "role_by_value" and r["sentence"]:
            assert not r2.consequence_hits(r["sentence"]) and not r2.marker_hits(r["sentence"])


def test_s07_and_s15_d_sentences_describe_complete_circuits():
    """A D object that is a bare resistor or cell 'in series with a lamp' would be an open circuit; each carries its own source."""

    s07 = roles_m0v2.ROLE_SPECS["S07"].pairs[0]
    assert "second battery" in s07.d_attach and "lamp" in s07.d_attach
    s15 = roles_m0v2.ROLE_SPECS["S15"].pairs[0]
    assert "fan" in s15.d_attach and "cell" in s15.frame  # a cell driving a fan is a complete loop


def test_c_rows_carry_the_familiarity_tag(rows):
    for r in rows:
        if r["family"] == "role_by_value" and r["stratum"] == "C":
            spec = roles_m0v2.ROLE_SPECS[r["structure_id"]].cancelling
            assert r["textbook_familiarity"] == spec.familiarity and r["textbook_familiarity_reason"] == spec.familiarity_reason
        else:
            assert r["textbook_familiarity"] is None
    c_rows = {r["structure_id"]: r["textbook_familiarity"] for r in rows if r["stratum"] == "C"}
    assert len(c_rows) == 8 and sum(v == "famous" for v in c_rows.values()) <= len(c_rows) / 2  # at most half famous (plan A4)


def test_manifest_counts_by_d_kind(built):
    m = built[1]
    assert m["by_d_kind_d_cells"] == {"other_object_same_scene": 36, "same_object_other_event": 9, "same_object_undone_event": 27}
    for sid, kinds in m["by_d_kind_by_structure"].items():
        assert kinds == sorted(["other_object_same_scene", UNDONE_OR_OTHER[sid]]), sid


def test_every_row_has_target_phrases_and_symbols(rows):
    for r in rows:
        assert r["target_phrases"] and r["target_symbols"], r["job_id"]
        assert all(isinstance(s, str) and s for s in (*r["target_phrases"], *r["target_symbols"]))
        phrases, symbols = roles_m0v2.TARGET_TERMS[r["structure_id"]]
        assert r["target_phrases"] == list(phrases) and r["target_symbols"] == list(symbols)


@pytest.mark.parametrize("sid", SIDS)
def test_trace_extractor_reads_the_base_gold_trace_from_the_base_row(sid, rows, traces):
    """`context_from_row` (frozen H4 extractor) with the row's own target terms finds the target in the base gold trace and
    extracts the base gold. (The extractor takes the terms as arguments, not from row fields, so they are passed explicitly.)"""

    from physmon.analysis import trace_extractor as te

    row = next(r for r in rows if r["structure_id"] == sid and r["cell_id"] == "no_cue")
    ctx = te.context_from_row(row, target_phrases=row["target_phrases"], target_symbols=row["target_symbols"])
    assert ctx.target_phrases == tuple(row["target_phrases"]) and ctx.target_symbols == tuple(row["target_symbols"])
    text = traces[row["job_id"]]["gold_trace"]["text"]
    result = te.classify_trace(text, ctx)
    assert result.status == "TRACE_CORRECT", (sid, result.status, result.statement_text if hasattr(result, "statement_text") else "")
    assert result.value_in_gold_unit == pytest.approx(row["gold_value"], rel=5e-3)
