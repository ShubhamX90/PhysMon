"""Tests of the judge-qualification bank v3, the frozen judge prompt's output contract and the qualification scorer."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import roles_m0  # noqa: E402
from physmon.governance.review import validate_review  # noqa: E402
from physmon.validation import rolevalue_bank as rb  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s178 = _load("s178", "scripts/v2/s178_build_judge_bank.py")
s179 = _load("s179", "scripts/v2/s179_score_judges.py")
PROMPT = REPO_ROOT / "docs/validation/v2/llm_panel/judge_prompt_v1.md"


@pytest.fixture(scope="module")
def bank(tmp_path_factory):
    out = tmp_path_factory.mktemp("bank") / "v3"
    manifest = s178.build(out)
    key = json.loads((out / "key_RESTRICTED.json").read_text())
    p1 = {json.loads(x)["item_id"]: json.loads(x) for x in (out / "pass1_packets.jsonl").read_text().splitlines()}
    p2 = {json.loads(x)["item_id"]: json.loads(x) for x in (out / "pass2_packets.jsonl").read_text().splitlines()}
    return manifest, key, p1, p2


def test_bank_counts_and_split(bank):
    manifest, key, p1, p2 = bank
    assert manifest["n_items"] == 63 and set(p1) == set(p2) == set(key)
    assert manifest["by_split"] == {"qualification": 53, "heldout": 10}
    assert manifest["expected"] == {"invalid|qualification": 39, "valid|qualification": 14, "valid|heldout": 4,
                                    "invalid|heldout": 6}
    for t in rb.ROLE_DEFECT_TYPES:
        assert manifest["by_type_split"][f"{t}|heldout"] == 1


def test_packets_leak_nothing(bank):
    _, key, p1, p2 = bank
    for pk in list(p1.values()) + list(p2.values()):
        assert not any(f in pk for f in s178.LEAK_FIELDS), pk["item_id"]  # top level (legacy parameters have "description")
        assert all("label" not in c for c in pk.get("authors_claims", []))  # internal R0/D1 labels never shown
        if pk["kind"] == "role":
            assert all(re.fullmatch(r"T[0-9A-F]{4}", s["sentence_id"]) for s in pk["sentences"])
    for item_id, pk in p1.items():
        assert "authors_claims" not in pk and "relations" not in pk
        if pk["kind"] == "role":
            assert "authors_claims" in p2[item_id]


def _claims(p2, item_id, stratum):
    return [c for c in p2[item_id]["authors_claims"] if c["stratum"] == stratum]


def test_each_planted_defect_is_really_present(bank):
    _, key, _, p2 = bank
    for item_id, k in key.items():
        if k["source"] != "role_m0" or k["defect_type"] == "valid":
            continue
        sid = k["structure_id"]
        structure, spec = roles_m0.structure(sid), roles_m0.ROLE_SPECS[sid]
        good = rb._r_answers(structure, spec)
        pk = p2[item_id]
        texts = {s["sentence_id"]: s["text"] for s in pk["sentences"]}
        if k["defect_type"] == "failed_transformation_identity":
            assert all(c["certified_answers"] != good for c in _claims(p2, item_id, "R"))
        elif k["defect_type"] == "relevant_variable_removed_from_equation":
            assert all(set(c["certified_answers"].values()) == {pk["base_answer"]} for c in _claims(p2, item_id, "R"))
        elif k["defect_type"] == "inconsistent_units":
            assert dm.UNITS[pk["target_unit"]].dim != dm.UNITS[structure.render.target_unit].dim
        elif k["defect_type"] == "invalid_parameter_domain":
            shown = [texts[c["sentence_id"]] for c in _claims(p2, item_id, "K")]
            assert all(rv._fmt(spec.conditional.counter_regime_value) in t for t in shown)
        elif k["defect_type"] == "hidden_coupling":
            assert len(_claims(p2, item_id, "R")) == 1  # R1 removed
            coupled = [texts[c["sentence_id"]] for c in _claims(p2, item_id, "D")]
            assert any(spec.phrasings_r[1].relation in t for t in coupled)
        elif k["defect_type"] == "rendering_not_minimal":
            d_texts = [texts[c["sentence_id"]] for c in _claims(p2, item_id, "D")]
            assert any(rv._fmt(spec.values[rb.DISPLAY_INDEX + 1]) in t for t in d_texts)
        assert k["detectable_in"] == "pass2"


def _review(item_id, pass_number, validity, flags=(), strata=None):
    r = {"reviewer_id": "test", "item_id": item_id, "pass_number": pass_number, "started_at": "t", "completed_at": "t",
         "minutes_spent": 3, "blinding_attestation": True, "validity": validity, "clarity": "clear", "difficulty": 3,
         "naturalness": "natural", "confidence": 4, "uncertain_fields": ["x"] if validity == "uncertain" else [],
         "defect_flags": list(flags), "counterexamples": [], "notes": "", "stratum_assignments": strata or {}}
    if pass_number == 2:
        r.update(equation_consistent=True, units_consistent=True, answer_correct=validity == "valid",
                 precision_adequate=True,
                 admission_category="CERTIFIED_AND_VALIDATED" if validity == "valid" else "SOLVER_INVALID")
    return r


def _write(directory, reviews):
    directory.mkdir(parents=True, exist_ok=True)
    for r in reviews:
        (directory / f"{r['item_id']}_pass{r['pass_number']}.json").write_text(json.dumps(r))


def _perfect(key, p2):
    out = []
    for item_id, k in key.items():
        strata = ({c["sentence_id"]: {"stratum": c["stratum"]} for c in p2[item_id].get("authors_claims", [])}
                  if k["source"] == "role_m0" else {})
        out.append(_review(item_id, 1, "valid", strata=strata))
        out.append(_review(item_id, 2, "valid") if k["expected_verdict"] == "valid"
                   else _review(item_id, 2, "invalid", [k["defect_type"]]))
    return out


def test_a_perfect_judge_qualifies_and_a_flawed_one_does_not(bank, tmp_path):
    _, key, _, p2 = bank
    bank_dir = tmp_path / "b"
    s178.build(bank_dir)
    _write(tmp_path / "perfect", _perfect(key, p2))
    good = s179.score(*s179.load_reviews(tmp_path / "perfect")[:1], key, p2)
    assert good["verdict"] == "QUALIFIED" and good["blind_stratum_agreement"]["rate"] == 1.0
    wrong_reason = [r if r["pass_number"] == 1 or key[r["item_id"]]["expected_verdict"] == "valid"
                    else {**r, "defect_flags": ["other"]} for r in _perfect(key, p2)]
    _write(tmp_path / "wrong", wrong_reason)
    bad = s179.score(*s179.load_reviews(tmp_path / "wrong")[:1], key, p2)
    assert bad["verdict"] == "NOT_QUALIFIED" and bad["checks"]["Q1_detected_for_declared_reason"]["detected"] == 0
    reject_all = [r if key[r["item_id"]]["expected_verdict"] != "valid" or r["pass_number"] == 1
                  else _review(r["item_id"], 2, "invalid", ["other"]) for r in _perfect(key, p2)]
    _write(tmp_path / "reject", reject_all)
    assert not s179.score(*s179.load_reviews(tmp_path / "reject")[:1], key, p2)["checks"]["Q3_all_valid_accepted"]["pass"]
    _write(tmp_path / "partial", [r for r in _perfect(key, p2) if not r["item_id"].startswith("L-")])
    missing = s179.score(*s179.load_reviews(tmp_path / "partial")[:1], key, p2)
    assert missing["verdict"] == "NOT_QUALIFIED" and len(missing["missing_pass2_reviews"]) == 33


def test_the_prompts_output_example_satisfies_the_review_contract():
    text = PROMPT.read_text()
    block = re.search(r"```json\n(.*?)\n```", text, re.S).group(1)
    block = block.replace('"valid|invalid|uncertain"', '"valid"').replace('"clear|ambiguous|unclear"', '"clear"')
    block = re.sub(r'"R\|D\|C\|K"', '"R"', block)
    example = json.loads(block)
    assert validate_review(example) == []
    categories = re.findall(r"`([A-Z_]{6,})`", text.split("admission_category")[-1])
    for cat in categories:
        p2 = {**example, "pass_number": 2, "equation_consistent": True, "units_consistent": True, "answer_correct": True,
              "precision_adequate": True, "admission_category": cat}
        assert validate_review(p2) == [], cat
    assert {"CERTIFIED_AND_VALIDATED", "SOLVER_INVALID"} <= set(categories)
    vocab = set(re.findall(r"`([a-z_]+)` \(", text))
    assert set(rb.ROLE_DEFECT_TYPES) <= vocab  # every planted type is in the judge's vocabulary
