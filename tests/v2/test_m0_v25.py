"""Tests for M0 v2.5 (journal J15.1-051): M0 v2.4 with S26 D0/N0 and S55 pair 1 rewritten after the naturalness review.

The M0 v2.1 builder's own checks (scene clause is the only change to the October problem, base gold unchanged, rendering and numeral
self-checks, unique job ids) run inside the build, which here goes to a temporary directory only (never `data/`). Here: every spec
certifies under the full rule set; the build has no exclusions; golds equal closed forms; each listed change is present; the other
nine structures equal M0 v2.4 cell for cell; no meta wording; no D or N sentence contradicts its scene clause; articles are right; the
builder refuses a spec outside the full-rule-set version; the panel packets cover S26 and S55, keep the numeral-free note and leak no key.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "v2"))

from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m0v24, roles_m0v25  # noqa: E402

G = 9.8
ALL = ("S01", "S07", "S13", "S15", "S20", "S26", "S27", "S30", "S55", "S72", "S92")
CHANGED = ("S26", "S55")
UNCHANGED = tuple(s for s in ALL if s not in CHANGED)
N_NOTE = ("This sentence is the numeral-free control by design: it deliberately carries no number; the matching D sentence "
          "carries the number.")


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    s204 = _load("s204", "scripts/v2/s204_build_m0_v25.py")
    out = tmp_path_factory.mktemp("m0v25") / "m0_v25"
    assert s204.main(["--out", str(out)]) == 0
    rows = [json.loads(line) for line in (out / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    return s204, out, manifest, rows


def _sentence(rows, sid, stratum, pair):
    """The sentence of the first study value (or the numeral-free control) of one pair."""

    matches = [r for r in rows if r["structure_id"] == sid and r["stratum"] == stratum and r.get("pair_id") == pair
               and r["family"] == "role_by_value" and r.get("value_index") in (0, None)]
    assert len(matches) == 1, (sid, stratum, pair, len(matches))
    return matches[0]["sentence"]


def _base(rows, sid):
    return next(r for r in rows if r["structure_id"] == sid and r["stratum"] == "none")


# --- specs ------------------------------------------------------------------------------------------------------------------------

def test_spec_set_and_versions():
    assert set(roles_m0v25.REJECTED) == {"S02"} and tuple(sorted(roles_m0v25.ROLE_SPECS)) == ALL
    assert roles_m0v25.VERSION == "v2.5" and roles_m0v25.CERT_VERSION == r2.VERSION_V21 == "v2.1"
    assert tuple(roles_m0v25.CHANGED) == CHANGED
    for sid, spec in roles_m0v25.ROLE_SPECS.items():
        assert spec.version == "v2.1", sid
        assert (spec is roles_m0v24.ROLE_SPECS[sid]) == (sid in UNCHANGED), sid  # unchanged structures are the v2.4 objects
        assert ("M0 v2.5" in spec.notes) == (sid in CHANGED), sid


@pytest.mark.parametrize("sid", ALL)
def test_every_spec_certifies_under_the_full_rule_set_and_is_complete(sid):
    spec = roles_m0v25.ROLE_SPECS[sid]
    cert = r2.certify_v2(roles_m0v25.structure(sid), spec)
    assert not cert["failed"], cert["failed"]
    assert r2.complete(spec, cert)
    assert cert["checks"]["scene_clause_ok"]["ok"] and cert["checks"]["d_not_on_target"]["ok"]


def test_builder_refuses_a_spec_outside_the_full_rule_set(built, monkeypatch, tmp_path):
    s204 = built[0]
    weak = dict(roles_m0v25.ROLE_SPECS)
    weak["S26"] = dataclasses.replace(weak["S26"], version="v2.2")
    monkeypatch.setattr(roles_m0v25, "ROLE_SPECS", weak)
    with pytest.raises(SystemExit, match="S26"):
        s204.check_versions()
    with pytest.raises(SystemExit, match="S26"):
        s204.s192.build(tmp_path / "never", REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl")
    assert not (tmp_path / "never").exists()


def test_build_has_no_exclusions_and_eleven_structures(built):
    s204, out, manifest, rows = built
    assert manifest["excluded"] == [] and manifest["n_structures"] == 11 and "S02" not in manifest["by_structure"]
    assert manifest["version"] == "m0_v2.5" and {r["m0_version"] for r in rows} == {"m0_v2.5"}
    assert manifest["base_prompt_is_october_problem_plus_scene_clause"] and manifest["base_gold_unchanged"]
    assert s204.main(["--out", str(out)]) == 2  # refuses to overwrite


# --- golds ------------------------------------------------------------------------------------------------------------------------

CLOSED = {
    "S01": lambda q: (5 - (3 + q)) * G / (3 + q + 5 + 2 / 2),
    "S07": lambda q: 12 * (1 - math.exp(-0.080 / ((5 + q) * 1e3 * 20e-6))),
    "S13": lambda q: 2 * math.pi * math.sqrt((0.8 + q) / G),
    "S15": lambda q: (12 + q) ** 2 * (1 / 6 + 1 / 12),
    "S20": lambda q: 12 * (40 + q) / (40 + q - 12),
    "S26": lambda q: math.degrees(math.asin(math.sin(math.radians(40 + q)) / 1.5)),
    "S27": lambda q: 101 + q + 1000 * G * 12 / 1000,
    "S30": lambda q: (2 + q) * 4186 * 40 / 1500,
    "S55": lambda q: math.sqrt(3 * 8.314 * (300 + q) / 4e-3),
    "S72": lambda q: 1240 / math.sqrt(2 * 511e3 * (150 + q)) * 1e3,
    "S92": lambda q: q * G * 1e-3 - 600 * 1e-3 * G,
}


@pytest.mark.parametrize("sid", ALL)
def test_r_golds_equal_closed_forms_and_d_golds_the_base(sid, built):
    _, _, _, rows = built
    base = _base(rows, sid)["gold_value"]
    assert base == pytest.approx(CLOSED[sid](1000 if sid == "S92" else 0), rel=1e-9)
    rd = [r for r in rows if r["structure_id"] == sid and r["family"] == "role_by_value" and r["stratum"] in ("R", "D")]
    assert len(rd) == 2 * 2 * 3
    for r in rd:
        expected = CLOSED[sid](r["value"]) if r["stratum"] == "R" else base
        assert r["gold_value"] == pytest.approx(expected, rel=1e-9), r["cell_id"]


def test_golds_and_base_prompts_equal_m0_v24_and_unchanged_structures_are_identical(built):
    _, _, _, rows = built
    old = {r["job_id"]: r for r in map(json.loads, (REPO_ROOT / "data/v2/dataset/m0_v24/cells.jsonl")
                                       .read_text(encoding="utf-8").splitlines())}
    assert {r["job_id"] for r in rows} == set(old)
    for r in rows:
        o = old[r["job_id"]]
        assert r["gold_value"] == pytest.approx(o["gold_value"], rel=1e-12), r["cell_id"]
        if r["stratum"] == "none":
            assert r["prompt"] == o["prompt"]
        if r["structure_id"] in UNCHANGED:
            a = {k: v for k, v in r.items() if k != "m0_version"}
            b = {k: v for k, v in o.items() if k != "m0_version"}
            assert a == b, r["cell_id"]


# --- each listed change ----------------------------------------------------------------------------------------------------------

def test_s26_d0_and_n0_have_a_purpose_and_plain_wording(built):
    _, _, _, rows = built
    assert _sentence(rows, "S26", "D", "p0") == (
        "The camera on the tripod is then tilted 6° farther from the vertical to keep the ray in view.")
    assert _sentence(rows, "S26", "N", "p0") == (
        "The camera on the tripod is then tilted a little farther from the vertical to keep the ray in view.")
    assert not any("has grown by" in _sentence(rows, "S26", s, "p0") for s in ("D", "N"))
    # R0 and pair 1 are the M0 v2.4 sentences
    assert _sentence(rows, "S26", "R", "p0") == "The ray is then tilted until its angle of incidence at the interface has grown by 6°."
    assert _sentence(rows, "S26", "R", "p1") == (
        "Before the refraction was observed, the laser that produces the ray was tilted until the angle of incidence had grown "
        "by 6°.")
    assert _sentence(rows, "S26", "D", "p1").startswith("In an earlier experiment, the laser that produces the ray was tilted")
    for stratum in ("R", "D", "N"):
        for pair in ("p0", "p1"):
            digits = re.findall(r"\d+(?:\.\d+)?", _sentence(rows, "S26", stratum, pair))
            assert digits == (["6"] if stratum != "N" else []), (stratum, pair, digits)  # no numeral but the cue
    pairs = roles_m0v25.ROLE_SPECS["S26"].pairs
    assert not pairs[0].frame_matched and pairs[0].d_attach == "the vertical" and pairs[1].frame_matched
    assert "pointless" not in json.dumps(roles_m0v25.CHANGES["S26"])


def test_s55_pair_one_has_a_coherent_earlier_experiment_and_a_just_before_r(built):
    _, _, _, rows = built
    r1, d1, n1 = (_sentence(rows, "S55", s, "p1") for s in ("R", "D", "N"))
    assert r1 == "Just before the molecular speeds were measured, a heater warmed this gas sample by 50 K."
    assert d1 == "In an earlier experiment, a heater warmed this gas sample by 50 K."
    assert n1 == "In an earlier experiment, a heater warmed this gas sample by a few kelvin."
    for text in (r1, d1, n1):
        assert "equilibrium" not in text and "stated" not in text
    pair = roles_m0v25.ROLE_SPECS["S55"].pairs[1]
    assert pair.frame_matched and pair.d_kind == "same_object_other_event"
    assert abs(len(r1.split()) - len(d1.split())) <= 3
    assert roles_m0v25.ROLE_SPECS["S55"].pairs[0] is roles_m0v24.ROLE_SPECS["S55"].pairs[0]  # pair 0 unchanged
    assert _sentence(rows, "S55", "R", "p0").startswith("Before the molecular speeds are measured, a heater warms this gas sample")
    assert "thermally insulated" in _base(rows, "S55")["prompt"]


def test_s72_and_s92_are_the_m0_v24_specs(built):
    _, _, _, rows = built
    for sid in ("S72", "S92"):
        assert roles_m0v25.ROLE_SPECS[sid] is roles_m0v24.ROLE_SPECS[sid]
    assert _sentence(rows, "S72", "D", "p1").endswith("after the wavelength has been determined.")
    assert _sentence(rows, "S92", "N", "p1").endswith("somewhat greater than the original's, with the string still holding the cube under it.")


def test_changes_table_lists_exactly_the_changed_structures():
    assert set(roles_m0v25.CHANGES) == set(CHANGED)


# --- wording rules over every sentence -------------------------------------------------------------------------------------------

# "stated" and "before any" anywhere; "given" as meta wording ("the given angle", "given that"), not the verb in "is given to the proton"
META = re.compile(r"\bstated\b|\bbefore any\b|\b(?:the|a|an|its) given\b|\bgiven (?:that|value|angle|temperature|energy)\b",
                  re.IGNORECASE)


def test_no_meta_wording_in_any_sentence_or_scene_clause(built):
    _, _, _, rows = built
    for r in rows:
        for field in ("sentence", "scene_clause"):
            assert not META.search(r[field] or ""), (r["cell_id"], field, r[field])
    for bad in ("than the stated angle of incidence", "From the stated temperature", "the given angle", "before any change"):
        assert META.search(bad), bad  # the pattern bites
    assert not META.search("an extra amount of kinetic energy is given to the proton")


RULE_8 = (
    (r"\bempty\b", r"\b(?:fills?|filled|full|now holds)\b"),
    (r"\bdoes not boil\b", r"\bboil"),
    (r"\bNo heat is lost\b", r"\b(?:heat (?:is|was) lost|loses|losing|loss)\b"),
    (r"\bthermally insulated\b", r"\b(?:conduct|touch(?:es|ed)?|exchanges?|in contact)\b"),
    (r"\bdoes not leak\b", r"\b(?:leaks?|leaked|leaking|discharg)"),
    (r"\bat rest\b", r"\b(?:stirred|stirs|flows?|sloshes|moving)\b"),
    (r"\bopen to the same air\b", r"\b(?:sealed|closed|lid)\b"),
)


def test_no_d_or_n_sentence_contradicts_its_scene_clause(built):
    _, _, _, rows = built
    checked = 0
    for r in rows:
        if r["stratum"] not in ("D", "N") or r["family"] != "role_by_value":
            continue
        for scene_pattern, forbidden in RULE_8:
            if re.search(scene_pattern, r["scene_clause"]):
                checked += 1
                assert not re.search(forbidden, r["sentence"], re.IGNORECASE), (r["cell_id"], r["sentence"])
    assert checked >= 40


def test_rule_7_phrase_is_kept_on_the_attachment_d1s(built):
    _, _, _, rows = built
    for sid in ("S01", "S07", "S13", "S15", "S92"):
        for stratum in ("D", "N"):
            assert "for an earlier experiment only" in _sentence(rows, sid, stratum, "p1").lower(), (sid, stratum)


def _vowel_sound_number(text: str) -> bool:
    integer = text.split(".")[0].replace(",", "")
    return bool(re.fullmatch(r"8\d{0,3}|11|18|11\d{3}|18\d{3}", integer))


def _wrong_articles(sentence: str) -> list[str]:
    return [m.group(0) for m in re.finditer(r"\b[Aa] (\d[\d.,]*)", sentence) if _vowel_sound_number(m.group(1).rstrip(".,"))]


def test_no_a_before_a_vowel_sound_number(built):
    from physmon.benchmark.v2 import rolevalue as rv

    _, _, _, rows = built
    for r in rows:
        assert not _wrong_articles(r["sentence"]) and not _wrong_articles(r["prompt"]), r["cell_id"]
    for sid, spec in roles_m0v25.ROLE_SPECS.items():
        for pair in spec.pairs:
            for value in (*spec.values, *spec.heldout_values):
                for role in ("R", "D"):
                    text = r2.pair_sentence(pair, role, value, spec.unit)
                    assert not _wrong_articles(text), (sid, value, text)
        for wrapped in (spec.cancelling, spec.conditional):
            if wrapped is None:
                continue
            sub = wrapped.spec
            values = (*sub.values, *wrapped.heldout_values, *(wrapped.k_out.values if hasattr(wrapped, "k_out") else ()))
            for value in values:
                for phrasing in sub.phrasings:
                    text = rv._sentence(sub.frame, value, sub.unit, phrasing.relation, sub.nonnumeric_fill)
                    assert not _wrong_articles(text), (sid, value, text)
    assert _wrong_articles("A 8 kPa pressure rise") and not _wrong_articles("A 7.5 kPa pressure rise")


# --- panel packets -----------------------------------------------------------------------------------------------------------------

def _lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


@pytest.fixture(scope="module")
def packets(built, tmp_path_factory):
    _, out, _, _ = built
    s205 = _load("s205", "scripts/v2/s205_m0v25_panel_packets.py")
    root = tmp_path_factory.mktemp("packets24")
    args = ["--out", str(root / "out"), "--scratch", str(root / "scratch"), "--data-dir", str(out)]
    assert s205.main(args) == 0
    return s205, root, args


def test_packets_cover_the_two_changed_structures(packets):
    s205, root, _ = packets
    p1, p2 = _lines(root / "out/pass1_packets.jsonl"), _lines(root / "out/pass2_packets.jsonl")
    assert len(p1) == len(p2) == 2 and {p["item_id"] for p in p1} == {f"M0V25-{sid}" for sid in CHANGED}
    admission = json.loads((root / "out/assignment_admission.json").read_text())
    assert admission["run_id"] == "m0v25_admission" and sorted(len(b["items"]) for b in admission["batches"]) == [2]
    assert json.loads((root / "out/assignment_naturalness.json").read_text())["run_id"] == "m0v25_naturalness"
    assert (root / "scratch/m0v25_admission").is_dir() and (root / "scratch/m0v25_naturalness").is_dir()
    assert s205.s193.OUT_DIR.endswith("admission_m0v25") and s205.s193.SCRATCH == "/scratch/pabitra/physmon/judge"
    natural = _lines(root / "out/naturalness_packets.jsonl")
    assert len(natural) == 6 + 8  # S26 + S55: every role sentence is re-rated


def test_every_n_claim_keeps_the_numeral_free_note(packets):
    _, root, _ = packets
    n_claims = 0
    for p in _lines(root / "out/pass2_packets.jsonl"):
        for claim in p["authors_claims"]:
            if claim.get("numeral_free"):
                n_claims += 1
                assert claim["numeral_free_note"] == N_NOTE
            else:
                assert "numeral_free_note" not in claim
    assert n_claims == 4
    for p in _lines(root / "out/pass1_packets.jsonl"):
        assert "authors_claims" not in p and "numeral-free control" not in json.dumps(p)


def test_packets_leak_no_key_fields_and_are_deterministic(packets, tmp_path):
    s205, root, args = packets
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl"):
        for p in _lines(root / "out" / name):
            assert s205.s193.leak_scan(p) == []
    by_id = {p["item_id"]: p for p in _lines(root / "out/pass2_packets.jsonl")}
    for sid in CHANGED:
        spec = roles_m0v25.ROLE_SPECS[sid]
        assert spec.scene_clause in by_id[f"M0V25-{sid}"]["problem"]
    again = ["--out", str(tmp_path / "out"), "--scratch", str(tmp_path / "scratch"), "--data-dir", args[-1]]
    assert s205.main(again) == 0
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl"):
        assert (root / "out" / name).read_bytes() == (tmp_path / "out" / name).read_bytes(), name
    assert s205.main(args) == 2  # refuses to overwrite


def test_instructions_are_the_exact_frozen_prompts(packets):
    _, root, _ = packets
    for run, prompt in (("m0v25_admission", "judge_prompt_v3.md"), ("m0v25_naturalness", "naturalness_prompt_v2.md")):
        dirs = sorted((root / "scratch" / run).iterdir())
        assert dirs
        frozen = (REPO_ROOT / "docs/validation/v2/llm_panel" / prompt).read_bytes()
        assert all((d / "instructions.md").read_bytes() == frozen for d in dirs)


def test_v24_specs_are_not_modified_by_importing_v25():
    assert roles_m0v24.ROLE_SPECS["S55"].pairs[1].r_attach == "just before the molecular speeds were measured"
    assert "has grown by" in roles_m0v24.ROLE_SPECS["S26"].pairs[0].d_frame
