"""Tests for the M0 v2.1 panel packets (s193) and the amended naturalness rule 6.1 of the scorer (s190b)."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "v2"))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


s193 = _load("s193_m0v21_panel_packets", "scripts/v2/s193_m0v21_panel_packets.py")
s190b = _load("s190b_score_m0v2_admission", "scripts/v2/s190b_score_m0v2_admission.py")


def _lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


@pytest.fixture(scope="module")
def build(tmp_path_factory):
    root = tmp_path_factory.mktemp("build21")
    assert s193.main(["--out", str(root / "out"), "--scratch", str(root / "scratch")]) == 0
    return root


def test_counts_and_ids(build):
    out = build / "out"
    p1, p2 = _lines(out / "pass1_packets.jsonl"), _lines(out / "pass2_packets.jsonl")
    assert len(p1) == len(p2) == 12 and all(p["item_id"].startswith("M0V21-") for p in p1)
    assert len(_lines(out / "naturalness_packets.jsonl")) == 100
    assert len(json.loads((out / "assignment_admission.json").read_text())["batches"]) == 6


def test_instructions_are_the_exact_frozen_prompts(build):
    for run, prompt in (("m0v21_admission", "judge_prompt_v3.md"), ("m0v21_naturalness", "naturalness_prompt_v2.md")):
        dirs = sorted((build / "scratch" / run).iterdir())
        assert dirs
        frozen = (REPO_ROOT / "docs/validation/v2/llm_panel" / prompt).read_bytes()
        assert all((d / "instructions.md").read_bytes() == frozen for d in dirs)
    assignment = json.loads((build / "out/assignment_naturalness.json").read_text())
    assert assignment["prompt"].endswith("naturalness_prompt_v2.md")


def test_naturalness_batching_rules_and_no_leaks(build):
    out = build / "out"
    keys = json.loads((out / "naturalness_key_RESTRICTED.json").read_text())
    assignment = json.loads((out / "assignment_naturalness.json").read_text())
    seen = []
    for b in assignment["batches"]:
        assert len(b["items"]) <= 12
        assert max(Counter(keys[i]["structure_id"] for i in b["items"]).values()) <= 2
        groups = [(keys[i]["structure_id"], keys[i]["group"]) for i in b["items"]]
        assert len(set(groups)) == len(groups)  # never an R with its own D
        seen += b["items"]
    assert sorted(seen) == sorted(keys)
    for p in _lines(out / "naturalness_packets.jsonl"):
        assert set(p) == {"item_id", "problem", "inserted_sentence"} and p["problem"].count(p["inserted_sentence"]) == 1
        assert s193.leak_scan(p) == []
    d_keys = [k for k in keys.values() if k["stratum"] == "D"]
    assert len(d_keys) == 24 and all(k["twin_label"] == "R" + k["label"][1:] for k in d_keys)


def test_packets_carry_scene_notes_relation_notes_and_honest_pair_claims(build):
    out = build / "out"
    cells = s193.load_cells()
    for p in _lines(out / "pass2_packets.jsonl"):
        sid = p["item_id"].removeprefix("M0V21-")
        clause = next(c["scene_clause"] for c in cells if c["structure_id"] == sid)
        assert clause in p["problem"] and clause in p["scene_clause_note"]
        for claim in p["authors_claims"]:
            if claim["stratum"] == "D" and not claim.get("numeral_free"):
                assert "d_kind" in claim
                assert ("minimal_pair_with" in claim) != ("paired_with" in claim)
                if "paired_with" in claim:
                    assert sid in ("S02", "S26") and "NOT share one frame" in claim["pair_note"]
    s55 = next(p for p in _lines(out / "pass2_packets.jsonl") if p["item_id"] == "M0V21-S55")
    assert any("kg/mol" in r and "1e-3" in r for r in s55["relations"])
    s72 = next(p for p in _lines(out / "pass2_packets.jsonl") if p["item_id"] == "M0V21-S72")
    assert any("d_kind_note" in c for c in s72["authors_claims"])


def test_determinism_and_no_overwrite(build, tmp_path):
    assert s193.main(["--out", str(tmp_path / "out"), "--scratch", str(tmp_path / "scratch")]) == 0
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl", "manifest.json"):
        assert (build / "out" / name).read_bytes() == (tmp_path / "out" / name).read_bytes(), name
    assert s193.main(["--out", str(build / "out"), "--scratch", str(build / "x")]) == 2


# --- amended 6.1 -------------------------------------------------------------------------------------------------------------

def test_twin_violation_levels():
    f = s190b.twin_violation
    assert f("artificial", "natural") and not f("artificial", "slightly_artificial") and not f("slightly_artificial", "natural")
    assert not f("natural", "artificial") and not f(None, "natural") and not f("natural", None)


def test_scorer_applies_the_amended_naturalness_rule(tmp_path):
    key = {"M0V21-S01": {"structure_id": "S01", "sentence_strata": {}}}
    nat_key = {"N1": {"structure_id": "S01", "label": "R0", "stratum": "R"},
               "N2": {"structure_id": "S01", "label": "D0", "stratum": "D", "twin_label": "R0"},
               "N3": {"structure_id": "S01", "label": "R1", "stratum": "R"},
               "N4": {"structure_id": "S01", "label": "D1", "stratum": "D", "twin_label": "R1"},
               "N5": {"structure_id": "S01", "label": "N0", "stratum": "N"}}
    ratings = {"N1": "natural", "N2": "artificial", "N3": "artificial", "N4": "slightly_artificial", "N5": "slightly_artificial"}
    d = tmp_path / "r"
    d.mkdir()
    for k, v in ratings.items():
        (d / f"{k}.json").write_text(json.dumps({"item_id": k, "rating": v, "reason": "x"}))
    report = s190b.score(key, nat_key, {}, {"claude": [d]}, min_judges=0)
    st = {k: v["status"] for k, v in report["sentences"].items()}
    assert st == {"N1": "OK", "N2": "REWRITE", "N3": "REWRITE", "N4": "OK", "N5": "OK"}  # artificial anywhere is a rewrite
    assert report["sentences"]["N2"]["twin_gap"] == [{"rater": "claude", "d": "artificial", "r_twin": "natural", "twin_label": "R0"}]
    assert report["sentences"]["N4"]["twin_gap"] == []  # one level worse than a natural... N3 is artificial, so D is fine
    md = s190b.render_markdown(report)
    assert "more than one level worse" in md
    # a missing R twin rating leaves its D pending
    (d / "N1.json").unlink()
    (d / "N2.json").write_text(json.dumps({"item_id": "N2", "rating": "natural", "reason": "x"}))
    again = s190b.score(key, nat_key, {}, {"claude": [d]}, min_judges=0)
    assert again["sentences"]["N2"]["status"] == "PENDING"


def test_scorer_cli_on_the_v21_bank(build, tmp_path):
    out = tmp_path / "rep"
    assert s190b.main(["--bank", str(build / "out"), "--out-dir", str(out), "--title", "M0 v2.1 admission report"]) == 0
    report = json.loads((out / "admission_report.json").read_text())
    assert report["structure_counts"] == {"INCOMPLETE": 12} and report["title"] == "M0 v2.1 admission report"
