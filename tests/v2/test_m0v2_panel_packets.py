"""Tests for the M0 v2 panel packets (s190) and the admission scorer (s190b)."""

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


s190 = _load("s190_m0v2_panel_packets", "scripts/v2/s190_m0v2_panel_packets.py")
s190b = _load("s190b_score_m0v2_admission", "scripts/v2/s190b_score_m0v2_admission.py")

CELLS = s190.load_cells()
ROLE = ("R", "D", "N", "C", "K", "K_out")


def _lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


@pytest.fixture(scope="module")
def build(tmp_path_factory):
    root = tmp_path_factory.mktemp("build")
    assert s190.main(["--out", str(root / "out"), "--scratch", str(root / "scratch")]) == 0
    return root


def test_counts(build):
    out = build / "out"
    p1, p2 = _lines(out / "pass1_packets.jsonl"), _lines(out / "pass2_packets.jsonl")
    assert len(p1) == len(p2) == 12
    assert sorted(p["item_id"] for p in p1) == sorted(f"M0V2-S{n}" for n in
                                                      ("01", "02", "07", "13", "15", "20", "26", "27", "30", "55", "72", "92"))
    assert len(_lines(out / "naturalness_packets.jsonl")) == 100
    assignment = json.loads((out / "assignment_admission.json").read_text())
    assert len(assignment["batches"]) == 6 and all(len(b["items"]) <= 2 for b in assignment["batches"])
    assert assignment["batches"][0]["reviewer_id"] == "claude-opus-5-5:m0v2_admission:batch01"


def test_determinism(build, tmp_path):
    assert s190.main(["--out", str(tmp_path / "out"), "--scratch", str(tmp_path / "scratch")]) == 0
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl", "key_RESTRICTED.json",
                 "naturalness_key_RESTRICTED.json", "manifest.json"):
        assert (build / "out" / name).read_bytes() == (tmp_path / "out" / name).read_bytes(), name
    first = sorted(p.relative_to(build / "scratch").as_posix() for p in (build / "scratch").rglob("*.json"))
    second = sorted(p.relative_to(tmp_path / "scratch").as_posix() for p in (tmp_path / "scratch").rglob("*.json"))
    assert first == second


def test_refuses_to_overwrite(build):
    assert s190.main(["--out", str(build / "out"), "--scratch", str(build / "other")]) == 2
    assert s190.main(["--out", str(build / "new"), "--scratch", str(build / "scratch")]) == 2


def test_no_leaks(build):
    out = build / "out"
    packets = _lines(out / "pass1_packets.jsonl") + _lines(out / "pass2_packets.jsonl") + _lines(
        out / "naturalness_packets.jsonl")
    for batch in (build / "scratch").rglob("*_packet.json"):
        packets.append(json.loads(batch.read_text()))
    for p in packets:
        assert s190.leak_scan(p) == [], p["item_id"]
        text = json.dumps(p)
        for forbidden in ("cell_id", "family", "stratum_key", ":after_context", "R:z", "D:z", "heldout", "K_out"):
            assert forbidden not in text or forbidden == "K_out" and "authors_claims" in p, (p["item_id"], forbidden)
    for p in _lines(out / "naturalness_packets.jsonl"):
        assert set(p) == {"item_id", "problem", "inserted_sentence"}
        assert p["item_id"].startswith("NAT-")
    # sentence ids are neutral: no role letters or structure in the id
    for p in _lines(out / "pass1_packets.jsonl"):
        for s in p["sentences"]:
            assert set(s) == {"sentence_id", "text"} and s["sentence_id"].startswith("T")


def test_scratch_layout(build):
    for run, n in (("m0v2_admission", 6), ("m0v2_naturalness", 9)):
        dirs = sorted((build / "scratch" / run).iterdir())
        assert len(dirs) == n
        for d in dirs:
            assert [p.name for p in (d / "out").iterdir()] == []
            assert {p.name for p in d.iterdir()} - {"out"} and all(
                p.name.endswith("_packet.json") for p in d.iterdir() if p.name != "out")


def _expected_sentences() -> dict[str, Counter]:
    expected: dict[str, Counter] = {}
    for c in CELLS:
        if c["family"] != "role_by_value" or c["stratum"] not in ROLE or c["heldout"]:
            continue
        if c["value_index"] not in (1, None):
            continue
        expected.setdefault(c["structure_id"], Counter())[c["sentence"]] += 1
    return expected


def test_every_middle_sentence_once(build):
    out = build / "out"
    expected = _expected_sentences()
    assert sum(sum(v.values()) for v in expected.values()) == 100
    for p in _lines(out / "pass1_packets.jsonl"):
        sid = p["item_id"].removeprefix("M0V2-")
        got = Counter(s["text"] for s in p["sentences"])
        assert got == expected[sid], sid
        assert len({s["sentence_id"] for s in p["sentences"]}) == len(p["sentences"])
    keys = json.loads((out / "naturalness_key_RESTRICTED.json").read_text())
    nat = _lines(out / "naturalness_packets.jsonl")
    got: dict[str, Counter] = {}
    for p in nat:
        got.setdefault(keys[p["item_id"]]["structure_id"], Counter())[p["inserted_sentence"]] += 1
        assert p["inserted_sentence"] in p["problem"]
        assert p["problem"].count(p["inserted_sentence"]) == 1
    assert got == expected


def test_claims_match_cells(build):
    out = build / "out"
    by_text: dict[tuple[str, str], dict] = {}
    for c in CELLS:
        if c["family"] == "role_by_value" and c["stratum"] in ROLE and not c["heldout"] and c["value_index"] in (1, None):
            by_text[(c["structure_id"], c["sentence"])] = c
    for p1, p2 in zip(sorted(_lines(out / "pass1_packets.jsonl"), key=lambda p: p["item_id"]),
                      sorted(_lines(out / "pass2_packets.jsonl"), key=lambda p: p["item_id"]), strict=True):
        sid = p1["item_id"].removeprefix("M0V2-")
        text_of = {s["sentence_id"]: s["text"] for s in p1["sentences"]}
        base = next(c for c in CELLS if c["structure_id"] == sid and c["stratum"] == "none")
        assert p2["base_answer"] == s190.r6(base["gold_value"]) and p2["problem"] == base["prompt"]
        assert {c["sentence_id"] for c in p2["authors_claims"]} == set(text_of)
        for claim in p2["authors_claims"]:
            mid = by_text[(sid, text_of[claim["sentence_id"]])]
            assert claim["stratum"] == {"N": "D", "K_out": "R"}.get(mid["stratum"], mid["stratum"])
            assert claim["stratum"] in ("R", "D", "C", "K")
            if mid["stratum"] == "N":
                assert claim["numeral_free"] is True
                assert claim["certified_answers"] == {"no number": s190.r6(mid["gold_value"])}
                continue
            series = [c for c in CELLS if c["structure_id"] == sid and c["family"] == "role_by_value"
                      and c["stratum"] == mid["stratum"] and c["phrasing_id"] == mid["phrasing_id"]
                      and not c["heldout"]]
            assert claim["values"] == [s190.fmt(c["value"]) for c in sorted(series, key=lambda c: c["value_index"])]
            assert claim["value_shown"] == s190.fmt(mid["value"])
            assert claim["certified_answers"] == {s190.fmt(c["value"]): s190.r6(c["gold_value"]) for c in series}
            # the claim is the cell's gold to the displayed six significant figures
            for c in series:
                got = claim["certified_answers"][s190.fmt(c["value"])]
                assert abs(got - c["gold_value"]) <= 5e-6 * abs(c["gold_value"])
            if mid["stratum"] == "K_out":
                k = by_text[(sid, text_of[claim["outside_regime_of"]])]
                assert k["stratum"] == "K" and k["phrasing_id"] == mid["phrasing_id"] and "regime_note" in claim
            if mid["stratum"] in ("R", "D"):
                twin = by_text[(sid, text_of[claim["minimal_pair_with"]])] if "minimal_pair_with" in claim else None
                if mid["stratum"] == "D":
                    assert twin["stratum"] == "R" and twin["pair_id"] == mid["pair_id"] and twin["value"] == mid["value"]
                    assert claim["d_rationale"] == mid["d_rationale"]
                else:
                    assert "wiring" in claim and "minimal_pair_with" not in claim
            if mid["stratum"] == "K":
                assert "regime" in claim and "counter_regime" in claim["regime"]
            if mid["stratum"] == "C":
                assert claim["cancellation"]["relations"] and claim["cancellation"]["expression_with_q"]


def test_naturalness_batches(build):
    out = build / "out"
    keys = json.loads((out / "naturalness_key_RESTRICTED.json").read_text())
    assignment = json.loads((out / "assignment_naturalness.json").read_text())
    seen = []
    for b in assignment["batches"]:
        assert len(b["items"]) <= 12
        per = Counter(keys[i]["structure_id"] for i in b["items"])
        assert max(per.values()) <= 2
        groups = [(keys[i]["structure_id"], keys[i]["group"]) for i in b["items"]]
        assert len(set(groups)) == len(groups)  # no R with its own D (or N) twin, no two phrasings of one C or K
        seen += b["items"]
        on_disk = sorted(p.name for p in Path(b["dir"]).glob("*_packet.json"))
        assert on_disk == sorted(f"{i}_packet.json" for i in b["items"])
    assert sorted(seen) == sorted(keys)


def test_gpt_kit_builds(build, tmp_path):
    s183 = _load("s183_make_judge_kit", "scripts/v2/s183_make_judge_kit.py")
    manifest = s183.build(tmp_path / "kit", build / "out", "admission",
                          REPO_ROOT / "docs/validation/v2/llm_panel/judge_prompt_v3.md", "m", "r")
    assert manifest["n_items"] == 12
    key = json.loads((build / "out" / "key_RESTRICTED.json").read_text())
    for k in key.values():  # roles stay exact in the key, golds at full precision
        assert set(k["sentence_strata"].values()) <= {"R", "D", "N", "C", "K", "K_out"}
        assert set(k["full_precision_golds"]) == set(k["sentence_strata"])
    assert any("K_out" in k["sentence_strata"].values() for k in key.values())
    assert {k["expected_verdict"] for k in key.values()} == {"valid"} and {k["split"] for k in key.values()} == {"admission"}


# --- scorer ------------------------------------------------------------------------------------------------------------------

def _review(item: str, validity: str = "valid", flags: dict | None = None, number: int = 2, strata: dict | None = None) -> dict:
    flags = flags or {}
    return {"item_id": item, "pass_number": number, "validity": validity, "defect_flags": list(flags),
            "defect_severity": dict(flags), "defect_reasons": {f: f"because {f}" for f in flags},
            "stratum_assignments": strata or {}, "precision_adequate": True}


def _write(d: Path, review: dict) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{review['item_id']}_pass{review['pass_number']}.json").write_text(json.dumps(review))


def test_scorer_on_synthetic_reviews(tmp_path):
    key = {"M0V2-S01": {"structure_id": "S01", "sentence_strata": {"Ta": "R", "Tb": "N"}},
           "M0V2-S02": {"structure_id": "S02", "sentence_strata": {}},
           "M0V2-S07": {"structure_id": "S07", "sentence_strata": {}},
           "M0V2-S13": {"structure_id": "S13", "sentence_strata": {}},
           "M0V2-S15": {"structure_id": "S15", "sentence_strata": {}}}
    nat_key = {"NAT-1": {"structure_id": "S01", "label": "R0", "stratum": "R"},
               "NAT-2": {"structure_id": "S01", "label": "D0", "stratum": "D"},
               "NAT-3": {"structure_id": "S02", "label": "R0", "stratum": "R"}}
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        _write(d, _review("M0V2-S01", strata={"Ta": {"stratum": "R"}, "Tb": {"stratum": "R"}}, number=1))
        _write(d, _review("M0V2-S01", flags={"hidden_coupling": "medium"} if d == a else {"missing_assumption": "low"}))
    _write(a, _review("M0V2-S02"))
    _write(b, _review("M0V2-S02", flags={"contradictory_distractor_statement": "high"}, validity="invalid"))
    _write(a, _review("M0V2-S07", validity="uncertain"))
    _write(b, _review("M0V2-S07"))
    _write(a, _review("M0V2-S13", flags={"missing_assumption": "high"}))  # valid verdict but a high flag
    _write(b, _review("M0V2-S13"))
    _write(a, _review("M0V2-S15"))  # judge b has no review: incomplete
    ra, rb = tmp_path / "ra", tmp_path / "rb"
    ra.mkdir(), rb.mkdir()
    (ra / "NAT-1.json").write_text(json.dumps({"item_id": "NAT-1", "rating": "natural", "reason": "ok"}))
    (ra / "more.json").write_text(json.dumps([{"item_id": "NAT-2", "rating": "slightly_artificial", "reason": "stiff"}]))
    (rb / "NAT-1.json").write_text(json.dumps({"item_id": "NAT-1", "rating": "natural", "reason": "ok"}))
    (rb / "NAT-2.json").write_text(json.dumps({"item_id": "NAT-2", "rating": "natural", "reason": "ok"}))
    (rb / "NAT-3.json").write_text(json.dumps({"item_id": "NAT-3", "rating": "artificial", "reason": "no one writes this"}))
    report = s190b.score(key, nat_key, {"claude": [a], "gpt": [b]}, {"claude": [ra], "gpt": [rb]})
    status = {k: v["status"] for k, v in report["structures"].items()}
    assert status == {"M0V2-S01": "ADMIT", "M0V2-S02": "REJECT", "M0V2-S07": "REJECT", "M0V2-S13": "REJECT",
                      "M0V2-S15": "INCOMPLETE"}
    assert any("contradictory_distractor_statement" in r for r in report["structures"]["M0V2-S02"]["reasons"])
    assert any("high flag missing_assumption" in r for r in report["structures"]["M0V2-S13"]["reasons"])
    assert any("uncertain" in r for r in report["structures"]["M0V2-S07"]["reasons"])
    s01 = report["structures"]["M0V2-S01"]
    assert any("medium" in n for n in s01["notes"])
    assert s01["blind_stratum_agreement"]["claude"]["mismatches"] == [
        {"sentence_id": "Tb", "authors_stratum": "N", "judge_stratum": "R"}]
    assert {k: v["status"] for k, v in report["sentences"].items()} == {"NAT-1": "OK", "NAT-2": "OK", "NAT-3": "REWRITE"}
    assert report["sentences"]["NAT-2"]["slightly_artificial"]
    assert s01["ready"] and not report["structures"]["M0V2-S02"]["ready"]
    # a missing naturalness rating is pending, not natural
    report2 = s190b.score(key, nat_key, {"claude": [a]}, {"claude": [ra]}, min_judges=1)
    assert report2["sentences"]["NAT-3"]["status"] == "PENDING"
    assert report2["structures"]["M0V2-S15"]["status"] == "ADMIT"
    md = s190b.render_markdown(report)
    assert "REWRITE" in md and "M0V2-S02: REJECT" in md


def test_scorer_cli_refuses_overwrite(build, tmp_path):
    out = tmp_path / "rep"
    args = ["--bank", str(build / "out"), "--out-dir", str(out)]
    assert s190b.main(args) == 0
    assert (out / "admission_report.json").exists() and (out / "admission_report.md").exists()
    report = json.loads((out / "admission_report.json").read_text())
    assert report["structure_counts"] == {"INCOMPLETE": 12}  # no reviews: nothing is admitted or rejected
    assert s190b.main(args) == 2
