"""Tests for M0 v2.4 (journal J15.1-048): M0 v2.3 with S72 pair 1 a same-electron event and the S26, S55, S92 naturalness rewrites.

The M0 v2.1 builder's own checks (scene clause is the only change to the October problem, base gold unchanged, rendering and numeral
self-checks, unique job ids) run inside the build, which here goes to a temporary directory only (never `data/`). Here: every spec
certifies under the full rule set; the build has no exclusions; golds equal closed forms; each listed change is present; unchanged
structures equal M0 v2.3; no sentence uses meta wording; no D or N sentence contradicts its scene clause; articles are right; the
builder refuses a spec outside the full-rule-set version; the panel packets cover the changed structures, keep the numeral-free note
and leak no key.
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
from physmon.benchmark.v2 import roles_m0v23, roles_m0v24  # noqa: E402

G = 9.8
ALL = ("S01", "S07", "S13", "S15", "S20", "S26", "S27", "S30", "S55", "S72", "S92")
CHANGED = ("S26", "S55", "S72", "S92")
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
    s202 = _load("s202", "scripts/v2/s202_build_m0_v24.py")
    out = tmp_path_factory.mktemp("m0v24") / "m0_v24"
    assert s202.main(["--out", str(out)]) == 0
    rows = [json.loads(line) for line in (out / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    return s202, out, manifest, rows


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
    assert set(roles_m0v24.REJECTED) == {"S02"} and tuple(sorted(roles_m0v24.ROLE_SPECS)) == ALL
    assert roles_m0v24.VERSION == "v2.4" and roles_m0v24.CERT_VERSION == r2.VERSION_V21 == "v2.1"
    assert tuple(roles_m0v24.CHANGED) == CHANGED
    for sid, spec in roles_m0v24.ROLE_SPECS.items():
        assert spec.version == "v2.1", sid
        assert (spec is roles_m0v23.ROLE_SPECS[sid]) == (sid in UNCHANGED), sid  # unchanged structures are the v2.3 objects
        assert ("M0 v2.4" in spec.notes) == (sid in CHANGED), sid


@pytest.mark.parametrize("sid", ALL)
def test_every_spec_certifies_under_the_full_rule_set_and_is_complete(sid):
    spec = roles_m0v24.ROLE_SPECS[sid]
    cert = r2.certify_v2(roles_m0v24.structure(sid), spec)
    assert not cert["failed"], cert["failed"]
    assert r2.complete(spec, cert)
    assert cert["checks"]["scene_clause_ok"]["ok"] and cert["checks"]["d_not_on_target"]["ok"]


def test_builder_refuses_a_spec_outside_the_full_rule_set(built, monkeypatch, tmp_path):
    s202 = built[0]
    weak = dict(roles_m0v24.ROLE_SPECS)
    weak["S26"] = dataclasses.replace(weak["S26"], version="v2.2")
    monkeypatch.setattr(roles_m0v24, "ROLE_SPECS", weak)
    with pytest.raises(SystemExit, match="S26"):
        s202.check_versions()
    with pytest.raises(SystemExit, match="S26"):
        s202.s192.build(tmp_path / "never", REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl")
    assert not (tmp_path / "never").exists()


def test_build_has_no_exclusions_and_eleven_structures(built):
    s202, out, manifest, rows = built
    assert manifest["excluded"] == [] and manifest["n_structures"] == 11 and "S02" not in manifest["by_structure"]
    assert manifest["version"] == "m0_v2.4" and {r["m0_version"] for r in rows} == {"m0_v2.4"}
    assert manifest["base_prompt_is_october_problem_plus_scene_clause"] and manifest["base_gold_unchanged"]
    assert s202.main(["--out", str(out)]) == 2  # refuses to overwrite


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


def test_golds_and_base_prompts_equal_m0_v23_and_unchanged_structures_are_identical(built):
    _, _, _, rows = built
    old = {r["job_id"]: r for r in map(json.loads, (REPO_ROOT / "data/v2/dataset/m0_v23/cells.jsonl")
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

def test_s72_pair_one_is_a_same_electron_event_after_the_determination(built):
    _, out, _, rows = built
    spec = roles_m0v24.ROLE_SPECS["S72"]
    assert spec.pairs[0] is roles_m0v23.ROLE_SPECS["S72"].pairs[0]  # the proton D is kept
    assert spec.pairs[1].d_kind == "same_object_other_event" and spec.pairs[1].d_kind_note == ""
    assert spec.pairs[1].frame_matched
    r1, d1, n1 = (_sentence(rows, "S72", s, "p1") for s in ("R", "D", "N"))
    assert r1 == ("The electron in this apparatus gains a further 40 eV of kinetic energy in one more accelerating gap before "
                  "the wavelength is determined.")
    assert d1 == ("The electron in this apparatus gains a further 40 eV of kinetic energy in one more accelerating gap after "
                  "the wavelength has been determined.")
    assert n1 == ("The electron in this apparatus gains a further amount of kinetic energy in one more accelerating gap after "
                  "the wavelength has been determined.")
    assert "alpha" not in " ".join(_sentence(rows, "S72", s, p) for s in ("R", "D", "N") for p in ("p0", "p1"))
    assert _sentence(rows, "S72", "D", "p0").endswith("is given to the proton by one more accelerating stage.")
    assert {r["d_kind"] for r in rows if r["structure_id"] == "S72" and r["stratum"] == "D"} == {
        "other_object_same_scene", "same_object_other_event"}
    assert all(r["d_kind_note"] is None for r in rows if r["structure_id"] == "S72")
    cert = json.loads((out / "certificates.json").read_text(encoding="utf-8"))
    assert cert["S72"]["role_certificate"]["passed"]


def test_s26_says_the_order_in_ordinary_words(built):
    _, _, _, rows = built
    assert _sentence(rows, "S26", "R", "p0") == "The ray is then tilted until its angle of incidence at the interface has grown by 6°."
    assert _sentence(rows, "S26", "R", "p1") == (
        "Before the refraction was observed, the laser that produces the ray was tilted until the angle of incidence had grown "
        "by 6°.")
    assert _sentence(rows, "S26", "D", "p0") == (
        "The camera on the tripod is then tilted until its angle from the vertical has grown by 6°.")
    assert _sentence(rows, "S26", "D", "p1").startswith("In an earlier experiment, the laser that produces the ray was tilted")
    for stratum in ("R", "D", "N"):
        for pair in ("p0", "p1"):
            digits = re.findall(r"\d+(?:\.\d+)?", _sentence(rows, "S26", stratum, pair))
            assert digits == (["6"] if stratum != "N" else []), (stratum, pair, digits)  # no numeral but the cue
    assert roles_m0v24.ROLE_SPECS["S26"].pairs[1].frame_matched


def test_s55_pair_one_has_no_from_the_stated_temperature(built):
    _, _, _, rows = built
    assert _sentence(rows, "S55", "R", "p1") == (
        "Once the sample was in equilibrium, a heater warmed it by 50 K just before the molecular speeds were measured.")
    assert _sentence(rows, "S55", "D", "p1") == "Once the sample was in equilibrium, a heater warmed it by 50 K in an earlier experiment."
    assert _sentence(rows, "S55", "N", "p1") == (
        "Once the sample was in equilibrium, a heater warmed it by a few kelvin in an earlier experiment.")
    assert _sentence(rows, "S55", "R", "p0").startswith("Before the molecular speeds are measured, a heater warms this gas sample")
    assert "thermally insulated" in _base(rows, "S55")["prompt"]


def test_s92_numeral_free_fill_is_natural(built):
    _, _, _, rows = built
    assert _sentence(rows, "S92", "N", "p0") == (
        "A liquid whose density is somewhat greater than the original's is poured into the second tank beside this one.")
    assert _sentence(rows, "S92", "N", "p1") == (
        "For an earlier experiment only, the liquid in the tank was replaced by one whose density is somewhat greater than the "
        "original's, with the string still holding the cube under it.")
    assert not any("different from" in r["sentence"] for r in rows if r["structure_id"] == "S92")
    assert _sentence(rows, "S92", "D", "p0") == "A liquid whose density is 1150 kg/m³ is poured into the second tank beside this one."


def test_changes_table_lists_exactly_the_changed_structures():
    assert set(roles_m0v24.CHANGES) == set(CHANGED)


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
    for sid, spec in roles_m0v24.ROLE_SPECS.items():
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
    s203 = _load("s203", "scripts/v2/s203_m0v24_panel_packets.py")
    root = tmp_path_factory.mktemp("packets24")
    args = ["--out", str(root / "out"), "--scratch", str(root / "scratch"), "--data-dir", str(out)]
    assert s203.main(args) == 0
    return s203, root, args


def test_packets_cover_the_four_changed_structures(packets):
    s203, root, _ = packets
    p1, p2 = _lines(root / "out/pass1_packets.jsonl"), _lines(root / "out/pass2_packets.jsonl")
    assert len(p1) == len(p2) == 4 and {p["item_id"] for p in p1} == {f"M0V24-{sid}" for sid in CHANGED}
    admission = json.loads((root / "out/assignment_admission.json").read_text())
    assert admission["run_id"] == "m0v24_admission" and sorted(len(b["items"]) for b in admission["batches"]) == [2, 2]
    assert json.loads((root / "out/assignment_naturalness.json").read_text())["run_id"] == "m0v24_naturalness"
    assert (root / "scratch/m0v24_admission").is_dir() and (root / "scratch/m0v24_naturalness").is_dir()
    assert s203.s193.OUT_DIR.endswith("admission_m0v24") and s203.s193.SCRATCH == "/scratch/pabitra/physmon/judge"
    natural = _lines(root / "out/naturalness_packets.jsonl")
    assert len(natural) == 6 + 8 + 6 + 10  # S26 + S55 + S72 + S92: every role sentence is re-rated


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
    assert n_claims == 8
    for p in _lines(root / "out/pass1_packets.jsonl"):
        assert "authors_claims" not in p and "numeral-free control" not in json.dumps(p)


def test_s72_claims_say_same_electron_event_and_carry_no_old_note(packets):
    _, root, _ = packets
    s72 = next(p for p in _lines(root / "out/pass2_packets.jsonl") if p["item_id"] == "M0V24-S72")
    kinds = [c.get("d_kind") for c in s72["authors_claims"] if c["stratum"] == "D" and not c.get("numeral_free")]
    assert sorted(kinds) == ["another event of the target object, which leaves no state behind",
                             "another object in the same scene (introduced in the problem text)"]
    assert not any("d_kind_note" in c for c in s72["authors_claims"])
    assert "alpha" not in json.dumps(s72["authors_claims"])


def test_packets_leak_no_key_fields_and_are_deterministic(packets, tmp_path):
    s203, root, args = packets
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl"):
        for p in _lines(root / "out" / name):
            assert s203.s193.leak_scan(p) == []
    by_id = {p["item_id"]: p for p in _lines(root / "out/pass2_packets.jsonl")}
    for sid in CHANGED:
        spec = roles_m0v24.ROLE_SPECS[sid]
        assert spec.scene_clause in by_id[f"M0V24-{sid}"]["problem"]
    again = ["--out", str(tmp_path / "out"), "--scratch", str(tmp_path / "scratch"), "--data-dir", args[-1]]
    assert s203.main(again) == 0
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl"):
        assert (root / "out" / name).read_bytes() == (tmp_path / "out" / name).read_bytes(), name
    assert s203.main(args) == 2  # refuses to overwrite


def test_instructions_are_the_exact_frozen_prompts(packets):
    _, root, _ = packets
    for run, prompt in (("m0v24_admission", "judge_prompt_v3.md"), ("m0v24_naturalness", "naturalness_prompt_v2.md")):
        dirs = sorted((root / "scratch" / run).iterdir())
        assert dirs
        frozen = (REPO_ROOT / "docs/validation/v2/llm_panel" / prompt).read_bytes()
        assert all((d / "instructions.md").read_bytes() == frozen for d in dirs)


def test_v23_specs_are_not_modified_by_importing_v24():
    assert roles_m0v23.ROLE_SPECS["S72"].pairs[1].d_kind == "other_object_same_scene"
    assert "stated angle of incidence" in roles_m0v23.ROLE_SPECS["S26"].pairs[1].frame
