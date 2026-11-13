"""Tests of the requalification bank v4 (s186) and the requal scoring of s179."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
BANK = REPO_ROOT / "docs/validation/v2/llm_panel/bank_v4"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s186 = _load("s186", "scripts/v2/s186_build_requal_bank.py")
s179 = _load("s179", "scripts/v2/s179_score_judges.py")
key = json.loads((BANK / "key_RESTRICTED.json").read_text())
p1 = {json.loads(x)["item_id"]: json.loads(x) for x in (BANK / "pass1_packets.jsonl").read_text().splitlines()}
p2 = {json.loads(x)["item_id"]: json.loads(x) for x in (BANK / "pass2_packets.jsonl").read_text().splitlines()}


def test_composition_and_no_overlap_with_bank_v3():
    assert len(key) == 32 and sum(k["expected_verdict"] == "invalid" for k in key.values()) == 22
    for t in ("missing_assumption", "insufficient_boundary_condition", "contradictory_distractor_statement",
              "invalid_numerical_precision"):
        assert sum(k["defect_type"] == t for k in key.values()) == 3, t
    v3 = json.loads((REPO_ROOT / "docs/validation/v2/llm_panel/bank_v3/key_RESTRICTED.json").read_text())
    shared = set(key) & set(v3)
    assert all(v3[i]["split"] == "heldout" for i in shared)  # only the unseen held-out items carry over
    fresh_families = {k["structure_id"] for k in key.values() if k["source"] == "fresh_v1_inject"}
    assert not fresh_families & s186.excluded_families()


def test_packets_leak_nothing_and_deletions_happened():
    for pk in list(p1.values()) + list(p2.values()):
        assert not any(f in pk for f in s186.s178.LEAK_FIELDS)
    for i, k in key.items():
        if k["source"] == "role_m0_condition_deleted":
            old, new, *_ = s186.ROLE_CONDITION_EDITS[k["structure_id"]]
            assert old not in p1[i]["problem"] and (not new or new in p1[i]["problem"])
        if k["source"] == "role_m0_heldout_v4_wording":
            regimes = [c.get("regime") for c in p2[i].get("authors_claims", []) if c.get("regime")]
            assert all("for_reference_only_outside_the_regime" in r for r in regimes)


def test_requal_scoring_thresholds():
    def rev(i, n, validity, flags=()):
        r = {"reviewer_id": "t", "item_id": i, "pass_number": n, "started_at": "t", "completed_at": "t", "minutes_spent": 1,
             "blinding_attestation": True, "validity": validity, "clarity": "clear", "difficulty": 3, "naturalness": "natural",
             "confidence": 4, "uncertain_fields": [], "defect_flags": list(flags), "counterexamples": [], "notes": ""}
        if n == 2:
            r.update(equation_consistent=True, units_consistent=True, answer_correct=True, precision_adequate=True,
                     admission_category="CERTIFIED_AND_VALIDATED" if validity == "valid" else "SOLVER_INVALID")
        return r

    perfect = {}
    for i, k in key.items():
        perfect[(i, 2)] = rev(i, 2, "valid") if k["expected_verdict"] == "valid" else rev(i, 2, "invalid", [k["defect_type"]])
    assert s179.score(perfect, key, p2, "requal")["verdict"] == "QUALIFIED"
    miss = dict(perfect)
    for i, k in key.items():
        if k["defect_type"] == "missing_assumption":
            miss[(i, 2)] = rev(i, 2, "valid")
    res = s179.score(miss, key, p2, "requal")
    assert res["verdict"] == "NOT_QUALIFIED" and not res["checks"]["R3_failed_types_recovered"]["pass"]
