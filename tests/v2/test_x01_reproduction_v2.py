"""Tests for the Stage 14.1 / X01 reproduction script (pure functions and refusal behaviour)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "x01_reproduce_phase1", REPO_ROOT / "scripts/v2/x01_reproduce_phase1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


x01 = _load()


def _record(model, family, variant, logprob):
    return {
        "model_name": model,
        "template_id": family,
        "variant_id": variant,
        "logprob_correct_answer": logprob,
    }


def test_slp_is_none_when_a_variant_is_missing_never_zero():
    records = [_record(x01.QWEN, "F1", v, -10.0 - v) for v in range(4)]
    records += [_record(x01.QWEN, "F2", v, -10.0) for v in range(3)]  # only three variants
    records += [_record(x01.QWEN, "F3", v, None if v == 2 else -10.0) for v in range(4)]
    result = x01.slp_by_model(records)[x01.QWEN]
    assert result["F1"] == pytest.approx(3.0)
    assert result["F2"] is None
    assert result["F3"] is None


def test_numeric_outcome_follows_the_reported_precision():
    assert x01.numeric("x", "0.7596", 0.75956, [])["outcome"] == "verified"
    mismatch = x01.numeric("x", "0.7596", 0.7048, [])
    assert mismatch["outcome"] == "unreproducible"
    assert mismatch["detail"]


def test_count_outcome():
    assert x01.count("n", 140, 140, [])["outcome"] == "verified"
    assert x01.count("n", 140, 139, [])["outcome"] == "unreproducible"


def test_update_ledger_derives_the_label_from_the_worst_component(tmp_path):
    row = {
        "claim_id": "T-01", "row_type": "phase1_ledger_item", "source_tag": "SUBMITTED",
        "source_ref": "t", "statement": "s", "reported_value": "1",
        "verification_label": "not_yet_checked", "evidence_status": "NOT_EVALUATED",
        "data_role": "UNASSIGNED_LEGACY", "artifacts": [], "checking_task": "X01",
        "paper_eligibility": False,
    }
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    comps = {
        "T-01": [
            x01.component("a", 1, 1, "verified", "", ["data/manifests/physmon_canonical_155.jsonl"]),
            x01.component("b", 2, None, "not_enough_source_data", "no artifact", []),
        ]
    }
    changed = x01.update_ledger(comps, "14.1", "J14.1-999", ledger_path=ledger)
    updated = json.loads(ledger.read_text(encoding="utf-8"))
    assert changed == ["T-01"]
    assert updated["verification_label"] == "not_enough_source_data"
    assert updated["evidence_status"] == "NOT_EVALUATED"
    assert updated["journal_ref"] == "J14.1-999"
    assert "no artifact" in updated["explanation"]


def test_a_verified_row_becomes_exploratory_not_confirmatory(tmp_path):
    row = {
        "claim_id": "T-02", "row_type": "phase1_ledger_item", "source_tag": "SUBMITTED",
        "source_ref": "t", "statement": "s", "reported_value": "1",
        "verification_label": "not_yet_checked", "evidence_status": "NOT_EVALUATED",
        "data_role": "UNASSIGNED_LEGACY", "artifacts": [], "checking_task": "X01",
        "paper_eligibility": False,
    }
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    comps = {"T-02": [x01.component("a", 1, 1, "verified", "", ["data/manifests/physmon_canonical_155.jsonl"])]}
    x01.update_ledger(comps, "14.1", "J14.1-999", ledger_path=ledger)
    updated = json.loads(ledger.read_text(encoding="utf-8"))
    assert updated["evidence_status"] == "exploratory"
    assert updated["paper_eligibility"] is False


def test_a_zero_row_claim_stays_not_evaluated_even_when_verified(tmp_path):
    row = {
        "claim_id": "T-03", "row_type": "phase1_ledger_item", "source_tag": "SUBMITTED",
        "source_ref": "t", "statement": "s", "reported_value": "0 rows",
        "verification_label": "not_yet_checked", "evidence_status": "NOT_EVALUATED",
        "data_role": "UNASSIGNED_LEGACY", "artifacts": [], "checking_task": "X01",
        "paper_eligibility": False, "observed_rows": 0, "scientific_null": False,
    }
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    comps = {"T-03": [x01.component("a", 0, 0, "verified", "", ["data/manifests/physmon_canonical_155.jsonl"])]}
    x01.update_ledger(comps, "14.1", "J14.1-999", ledger_path=ledger)
    assert json.loads(ledger.read_text(encoding="utf-8"))["evidence_status"] == "NOT_EVALUATED"


def test_main_refuses_to_reuse_a_non_empty_attempt_directory(tmp_path, monkeypatch):
    attempt = tmp_path / "attempt_x"
    attempt.mkdir()
    (attempt / "keep.txt").write_text("existing evidence", encoding="utf-8")
    monkeypatch.setattr(
        sys, "argv", ["x01", "--out-root", str(tmp_path), "--attempt-id", "attempt_x"]
    )
    assert x01.main() == 2
    assert (attempt / "keep.txt").read_text(encoding="utf-8") == "existing evidence"


def test_reproduction_runs_end_to_end_into_a_scratch_dir_and_matches_key_values(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x01", "--out-root", str(tmp_path), "--attempt-id", "t1"])
    assert x01.main() == 0
    result = json.loads((tmp_path / "t1" / "reconciliation.json").read_text(encoding="utf-8"))
    summary = result["summary"]
    assert summary["P1L-04"] == "different_but_explained"
    assert summary["P1L-08"] == "not_enough_source_data"
    assert summary["P1L-14"] == "not_enough_source_data"
    assert summary["P1L-16"] == "verified"
    assert result["card"] == "v2_X01_authoritative_reproduction"
    shared = next(c for c in result["components"]["P1L-04"] if c["name"] == "shared_positives")
    assert (shared["reported"], shared["recomputed"]) == (25, 22)
