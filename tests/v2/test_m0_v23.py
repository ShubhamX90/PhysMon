"""Tests for M0 v2.3 (journal J15.1-046): M0 v2.2 revised for the legitimate flags of the GPT judge (wording rules 1-8).

The M0 v2.1 builder's own checks (scene clause is the only change to the October problem, base gold unchanged, rendering and
numeral self-checks, unique job ids) run inside the build, which here goes to a temporary directory only (never `data/`). Here:
every spec certifies under the full rule set and is complete; the build has no exclusions and 11 structures; every R gold equals an
independent closed form and every D gold the base; each listed change is present; no D or N sentence contradicts its scene clause
(rule 8); the rule-7 phrase is on the attachment D1s; the base gold is unchanged; the panel packets carry the numeral-free note and
leak no key field.
"""

from __future__ import annotations

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
from physmon.benchmark.v2 import roles_m0v21, roles_m0v22, roles_m0v23  # noqa: E402

G = 9.8
ALL = ("S01", "S07", "S13", "S15", "S20", "S26", "S27", "S30", "S55", "S72", "S92")
ATTACHMENT_D1 = ("S01", "S07", "S13", "S15", "S92")
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
    s200 = _load("s200", "scripts/v2/s200_build_m0_v23.py")
    root = tmp_path_factory.mktemp("m0v23")
    out = root / "m0_v23"
    assert s200.main(["--out", str(out)]) == 0
    rows = [json.loads(line) for line in (out / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    return s200, out, manifest, rows


def _sentence(rows, sid, stratum, pair, support=False):
    """The sentence of the first study value (or the numeral-free control) of one pair."""

    matches = [r for r in rows if r["structure_id"] == sid and r["stratum"] == stratum and r.get("pair_id") == pair
               and r["family"] == "role_by_value" and r.get("value_index") in (0, None)]
    assert len(matches) == 1, (sid, stratum, pair, len(matches))
    return matches[0]["sentence"]


# --- specs ------------------------------------------------------------------------------------------------------------------------

def test_s02_stays_rejected_and_the_eleven_structures_are_kept():
    assert set(roles_m0v23.REJECTED) == {"S02"}
    assert tuple(sorted(roles_m0v23.ROLE_SPECS)) == ALL
    assert set(roles_m0v23.ROLE_SPECS) == set(roles_m0v22.ROLE_SPECS)
    assert roles_m0v23.VERSION == "v2.3"
    for sid, spec in roles_m0v23.ROLE_SPECS.items():
        assert "M0 v2.3" in spec.notes, sid
        assert spec.version == roles_m0v23.CERT_VERSION == r2.VERSION_V21  # certify_v2 applies the full rule set only for this value


@pytest.mark.parametrize("sid", ALL)
def test_every_spec_certifies_under_the_full_rule_set_and_is_complete(sid):
    spec = roles_m0v23.ROLE_SPECS[sid]
    cert = r2.certify_v2(roles_m0v23.structure(sid), spec)
    assert not cert["failed"], cert["failed"]
    assert r2.complete(spec, cert)
    assert cert["checks"]["scene_clause_ok"]["ok"] and cert["checks"]["d_not_on_target"]["ok"]


def test_build_has_no_exclusions_and_eleven_structures(built):
    _, _, manifest, rows = built
    assert manifest["excluded"] == []
    assert manifest["n_structures"] == 11 and "S02" not in manifest["by_structure"]
    assert manifest["version"] == "m0_v2.3" and {r["m0_version"] for r in rows} == {"m0_v2.3"}
    assert manifest["base_prompt_is_october_problem_plus_scene_clause"] and manifest["base_gold_unchanged"]


def test_builder_refuses_to_overwrite(built):
    s200, out, _, _ = built
    assert s200.main(["--out", str(out)]) == 2


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
    base = next(r for r in rows if r["structure_id"] == sid and r["stratum"] == "none")["gold_value"]
    assert base == pytest.approx(CLOSED[sid](1000 if sid == "S92" else 0), rel=1e-9)  # S92: the original liquid
    rd = [r for r in rows if r["structure_id"] == sid and r["family"] == "role_by_value" and r["stratum"] in ("R", "D")]
    assert len(rd) == 2 * 2 * 3  # R and D, two pairs, three study values (held-out values are certified, not celled)
    for r in rd:
        expected = CLOSED[sid](r["value"]) if r["stratum"] == "R" else base
        assert r["gold_value"] == pytest.approx(expected, rel=1e-9), r["cell_id"]


def test_base_gold_is_unchanged_against_m0_v21_and_v22(built):
    _, _, _, rows = built
    for old in ("m0_v21", "m0_v22"):
        committed = (REPO_ROOT / f"data/v2/dataset/{old}/cells.jsonl").read_text(encoding="utf-8").splitlines()
        base_old = {json.loads(x)["structure_id"]: json.loads(x)["gold_value"] for x in committed
                    if json.loads(x)["stratum"] == "none"}
        for r in rows:
            if r["stratum"] == "none":
                assert r["gold_value"] == pytest.approx(base_old[r["structure_id"]], rel=1e-12), (old, r["structure_id"])


def test_unchanged_structures_and_unchanged_cells_equal_m0_v22(built):
    _, _, _, rows = built
    committed = (REPO_ROOT / "data/v2/dataset/m0_v22/cells.jsonl").read_text(encoding="utf-8").splitlines()
    old = {r["job_id"]: r for r in map(json.loads, committed)}
    assert {r["job_id"] for r in rows} == set(old)
    changed_per_structure: dict[str, int] = {}
    for r in rows:
        a = {k: v for k, v in r.items() if k != "m0_version"}
        b = {k: v for k, v in old[r["job_id"]].items() if k != "m0_version"}
        if a != b:
            changed_per_structure[r["structure_id"]] = changed_per_structure.get(r["structure_id"], 0) + 1
            if r["structure_id"] in ("S01", "S13", "S15"):  # only the pair-1 D and N sentences (and their support twins) are reworded
                o = old[r["job_id"]]
                if r["sentence"] != o["sentence"] or r["prompt"] != o["prompt"]:
                    assert r["stratum"] in ("D", "N", "support") and r["pair_id"] == "p1" and "d1" in r["cell_id"], r["cell_id"]
                else:
                    assert r["stratum"] not in ("D", "N") or r["pair_id"] != "p1", r["cell_id"]  # the other differences are metadata
    assert set(changed_per_structure) == set(roles_m0v23.CHANGED)  # S20 and S72 rows are untouched
    # unchanged gold everywhere: only the wording moved
    for r in rows:
        assert r["gold_value"] == pytest.approx(old[r["job_id"]]["gold_value"], rel=1e-12), r["cell_id"]


# --- each listed change ----------------------------------------------------------------------------------------------------------

def test_rule_7_phrase_on_every_attachment_d1_and_n1(built):
    _, _, _, rows = built
    for sid in ATTACHMENT_D1:
        for stratum in ("D", "N"):
            text = _sentence(rows, sid, stratum, "p1")
            assert "for an earlier experiment only" in text.lower(), (sid, stratum, text)
    assert _sentence(rows, "S01", "D", "p1") == "A 0.6 kg block was hung from the left block for an earlier experiment only."
    assert _sentence(rows, "S07", "D", "p1").endswith("in series with the capacitor for an earlier experiment only.")
    assert _sentence(rows, "S13", "D", "p1").endswith("between the string and the bob for an earlier experiment only.")
    assert _sentence(rows, "S15", "D", "p1").startswith("For an earlier experiment only, a 1.5 V cell")
    assert _sentence(rows, "S92", "D", "p1").startswith("For an earlier experiment only, the liquid in the tank was replaced")
    # the R twins are not marked, and the non-attaching events keep "in an earlier experiment"
    for sid in ATTACHMENT_D1:
        assert "only" not in _sentence(rows, sid, "R", "p1").split()
    for sid in ("S20", "S26", "S55"):
        assert "in an earlier experiment" in _sentence(rows, sid, "D", "p1")


def test_s07_k_out_rationale_and_scene_clause(built):
    _, out, _, rows = built
    reason = roles_m0v23.ROLE_SPECS["S07"].conditional.k_out.reason
    assert "which the in-regime answer does not need" not in reason
    assert "needs before the break as well" in reason or "before the break as well as after it" in reason
    assert "does not need" not in reason
    base = next(r for r in rows if r["structure_id"] == "S07" and r["stratum"] == "none")["prompt"]
    assert "the capacitor does not leak" in base and "ideal" in base
    cert = json.loads((out / "certificates.json").read_text(encoding="utf-8"))
    assert cert["S07"]["k_out_reason"] == reason


def test_s26_both_r_sentences_start_from_the_stated_angle(built):
    _, _, _, rows = built
    assert _sentence(rows, "S26", "R", "p0") == "The ray is then tilted 6° farther from the normal than the stated angle of incidence."
    assert _sentence(rows, "S26", "R", "p1") == (
        "The laser that produces the ray was tilted 6° farther from the normal than the stated angle of incidence before the "
        "refraction was observed.")
    for stratum in ("R", "D", "N"):
        for pair in ("p0", "p1"):
            digits = re.findall(r"\d+(?:\.\d+)?", _sentence(rows, "S26", stratum, pair))
            assert digits == (["6"] if stratum != "N" else []), (stratum, pair, digits)  # no numeral other than the cue
    assert "than the stated angle of incidence in an earlier experiment" in _sentence(rows, "S26", "D", "p1")


def test_s27_scene_clause_and_cross_section(built):
    _, _, _, rows = built
    base = next(r for r in rows if r["structure_id"] == "S27" and r["stratum"] == "none")["prompt"]
    assert "the liquid in both tanks is at rest" in base and "open to the same air above" in base
    assert "the depth is measured in the first tank" in base and not re.search(r"\d", roles_m0v23.ROLE_SPECS["S27"].scene_clause)
    c_sentences = {r["sentence"] for r in rows if r["structure_id"] == "S27" and r["stratum"] == "C" and r["value_index"] == 0}
    assert c_sentences == {"The first tank has a uniform horizontal cross-sectional area of 0.5 m².",
                           "The first tank has vertical sides and a flat base with an area of 0.5 m²."}
    assert not any("flat base with an area" in s and "vertical sides" not in s for s in c_sentences)


def test_s30_scene_clause_states_no_heat_loss_and_no_boiling(built):
    _, _, _, rows = built
    base = next(r for r in rows if r["structure_id"] == "S30" and r["stratum"] == "none")["prompt"]
    assert "No heat is lost to the surroundings" in base and "the water does not boil" in base


def test_s55_scene_clause_and_pair_one(built):
    _, _, _, rows = built
    base = next(r for r in rows if r["structure_id"] == "S55" and r["stratum"] == "none")["prompt"]
    assert "The two flasks are thermally insulated from each other." in base
    assert _sentence(rows, "S55", "R", "p1") == ("From the stated temperature, a heater warmed this gas sample by 50 K before the "
                                                 "molecular speeds are measured.")
    assert _sentence(rows, "S55", "D", "p1") == ("From the stated temperature, a heater warmed this gas sample by 50 K in an "
                                                 "earlier experiment.")
    assert _sentence(rows, "S55", "R", "p0").startswith("Before the molecular speeds are measured, a heater warms this gas sample")


def test_s92_second_tank_stays_empty_and_liquid_is_poured_into_it(built):
    _, _, _, rows = built
    base = next(r for r in rows if r["structure_id"] == "S92" and r["stratum"] == "none")["prompt"]
    assert "A second, empty tank stands beside it." in base
    assert _sentence(rows, "S92", "D", "p0") == "A liquid whose density is 1150 kg/m³ is poured into the second tank beside this one."
    assert _sentence(rows, "S92", "N", "p0") == (
        "A liquid whose density is different from the original's is poured into the second tank beside this one.")
    assert _sentence(rows, "S92", "R", "p0").endswith("now replaces the original liquid in this tank.")
    assert not any(re.search(r"\bfills?\b", r["sentence"]) for r in rows if r["structure_id"] == "S92")


# --- rule 8: no D or N sentence contradicts its scene clause ------------------------------------------------------------------------

# scene-clause pattern -> pattern that a D or N sentence of the same structure must not match (a state that contradicts the clause)
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
    # the old wording is what the rule catches: M0 v2.2's S92 D0 said the second tank "now fills" against "empty"
    old = "A liquid whose density is 1150 kg/m³ now fills the second tank beside this one."
    assert re.search(RULE_8[0][1], old, re.IGNORECASE)


# --- panel packets -----------------------------------------------------------------------------------------------------------------

def _lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


@pytest.fixture(scope="module")
def packets(built, tmp_path_factory):
    _, out, _, _ = built
    s201 = _load("s201", "scripts/v2/s201_m0v23_panel_packets.py")
    root = tmp_path_factory.mktemp("packets23")
    args = ["--out", str(root / "out"), "--scratch", str(root / "scratch"), "--data-dir", str(out)]
    assert s201.main(args) == 0
    return s201, root, args


def test_packets_cover_all_eleven_structures_in_batches_of_two(packets):
    s201, root, _ = packets
    p1, p2 = _lines(root / "out/pass1_packets.jsonl"), _lines(root / "out/pass2_packets.jsonl")
    assert len(p1) == len(p2) == 11 and all(p["item_id"].startswith("M0V23-") for p in p1)
    assert {p["item_id"] for p in p1} == {f"M0V23-{sid}" for sid in ALL}
    admission = json.loads((root / "out/assignment_admission.json").read_text())
    assert admission["run_id"] == "m0v23_admission" and sorted(len(b["items"]) for b in admission["batches"]) == [1, 2, 2, 2, 2, 2]
    natural = json.loads((root / "out/assignment_naturalness.json").read_text())
    assert natural["run_id"] == "m0v23_naturalness"
    assert (root / "scratch/m0v23_admission").is_dir() and (root / "scratch/m0v23_naturalness").is_dir()
    assert s201.s193.OUT_DIR.endswith("admission_m0v23") and s201.s193.SCRATCH == "/scratch/pabitra/physmon/judge"


def test_every_n_claim_carries_the_numeral_free_note_and_nothing_else_does(packets):
    _, root, _ = packets
    n_claims = 0
    for p in _lines(root / "out/pass2_packets.jsonl"):
        for claim in p["authors_claims"]:
            if claim.get("numeral_free"):
                n_claims += 1
                assert claim["numeral_free_note"] == N_NOTE
            else:
                assert "numeral_free_note" not in claim
    assert n_claims == 22  # two numeral-free controls on each of 11 structures
    for p in _lines(root / "out/pass1_packets.jsonl"):
        assert "authors_claims" not in p and "numeral-free control" not in json.dumps(p)


def test_packets_leak_no_key_fields_and_carry_the_new_scene_clauses(packets):
    s201, root, _ = packets
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl"):
        for p in _lines(root / "out" / name):
            assert s201.s193.leak_scan(p) == []
            assert "structure_id" not in p and "expected_verdict" not in p
    by_id = {p["item_id"]: p for p in _lines(root / "out/pass2_packets.jsonl")}
    for sid, spec in roles_m0v23.ROLE_SPECS.items():
        packet = by_id[f"M0V23-{sid}"]
        assert spec.scene_clause in packet["problem"] and spec.scene_clause in packet["scene_clause_note"]
    s07 = by_id["M0V23-S07"]
    assert any("non-leaking capacitor" in json.dumps(c) and "does not need" not in json.dumps(c) for c in s07["authors_claims"])
    assert not any("does not need" in json.dumps(c) for c in s07["authors_claims"])
    s55 = by_id["M0V23-S55"]
    assert any("kg/mol" in r and "1e-3" in r for r in s55["relations"])
    natural = _lines(root / "out/naturalness_packets.jsonl")
    assert len(natural) == 90
    keys = json.loads((root / "out/naturalness_key_RESTRICTED.json").read_text())
    for p in natural:
        assert set(p) == {"item_id", "problem", "inserted_sentence"} and p["problem"].count(p["inserted_sentence"]) == 1
        assert p["item_id"] in keys


def test_instructions_are_the_exact_frozen_prompts_and_no_overwrite(packets):
    s201, root, args = packets
    for run, prompt in (("m0v23_admission", "judge_prompt_v3.md"), ("m0v23_naturalness", "naturalness_prompt_v2.md")):
        dirs = sorted((root / "scratch" / run).iterdir())
        assert dirs
        frozen = (REPO_ROOT / "docs/validation/v2/llm_panel" / prompt).read_bytes()
        assert all((d / "instructions.md").read_bytes() == frozen for d in dirs)
    assert s201.main(args) == 2


def test_packets_are_deterministic(packets, tmp_path):
    s201, root, args = packets
    again = ["--out", str(tmp_path / "out"), "--scratch", str(tmp_path / "scratch"), "--data-dir", args[-1]]
    assert s201.main(again) == 0
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl"):
        assert (root / "out" / name).read_bytes() == (tmp_path / "out" / name).read_bytes(), name


def test_v21_and_v22_specs_are_not_modified_by_importing_v23():
    assert roles_m0v21.ROLE_SPECS["S92"].pairs[0].d_attach == "now fills the second tank beside this one"
    assert roles_m0v22.ROLE_SPECS["S26"].pairs[1].r_attach == "before the refraction was observed"


# --- article before a number ---------------------------------------------------------------------------------------------------------

def _vowel_sound_number(text: str) -> bool:
    """A number read with a vowel sound: 8, 11, 18, 80-89, 800-899, 8000-8999 (and 11 or 18 on their own or as thousands)."""

    integer = text.split(".")[0].replace(",", "")
    return bool(re.fullmatch(r"8\d{0,3}|11|18|11\d{3}|18\d{3}", integer))


def _wrong_articles(sentence: str) -> list[str]:
    return [m.group(0) for m in re.finditer(r"\b[Aa] (\d[\d.,]*)", sentence) if _vowel_sound_number(m.group(1).rstrip(".,"))]


def test_article_check_catches_the_known_failures():
    for bad in ("A 8 kPa pressure rise", "a 11 V cell", "a 18 cm cord", "A 85 g mass", "a 800 g block", "a 8000 kg truck"):
        assert _wrong_articles(bad), bad
    for good in ("A 7.5 kPa pressure rise", "a 15 kPa rise", "A 0.8 kg block", "an 8 kPa rise", "a 9 kPa rise", "a 1.1 V cell",
                 "a 110 kg mass", "A 0.6 kg block", "The pulley has a radius of 8 cm."):
        assert not _wrong_articles(good), good


def test_no_rendered_sentence_has_a_before_a_vowel_sound_number(built):
    from physmon.benchmark.v2 import rolevalue as rv

    _, _, _, rows = built
    for r in rows:
        assert not _wrong_articles(r["sentence"]), (r["cell_id"], r["sentence"])
        assert not _wrong_articles(r["prompt"]), (r["cell_id"], r["prompt"])
    # held-out values are certified but never emitted: render every frame at every study and held-out value of every structure
    for sid, spec in roles_m0v23.ROLE_SPECS.items():
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
    assert 9.0 in roles_m0v23.ROLE_SPECS["S27"].heldout_values and 8.0 not in roles_m0v23.ROLE_SPECS["S27"].heldout_values
