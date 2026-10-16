"""Tests for the Research v2.0 claim-ledger contract (Stage 14.0).

These pin the properties the plan treats as non-negotiable: a zero-row result is never a null,
nothing is confirmatory or paper-eligible without a confirmatory role and a preregistration, and a
checked label always carries its evidence.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance.v2_contract import (  # noqa: E402
    CAUSAL_RECORD_EXTRA_FIELDS,
    RAW_RECORD_FIELDS,
    missing_artifact_paths,
    missing_record_fields,
    validate_ledger_rows,
)

LEDGER = REPO_ROOT / "docs/registry/v2/claim_ledger.jsonl"


def _row(**overrides):
    base = {
        "claim_id": "T-01",
        "row_type": "phase1_ledger_item",
        "source_tag": "SUBMITTED",
        "source_ref": "test",
        "statement": "A test statement.",
        "reported_value": "1",
        "verification_label": "not_yet_checked",
        "evidence_status": "NOT_EVALUATED",
        "data_role": "UNASSIGNED_LEGACY",
        "artifacts": [],
        "checking_task": "X01",
        "paper_eligibility": False,
    }
    base.update(overrides)
    return base


def _load_ledger():
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_valid_row_passes():
    assert validate_ledger_rows([_row()]) == []


def test_committed_ledger_is_valid_and_non_empty():
    rows = _load_ledger()
    assert len(rows) == 25
    assert validate_ledger_rows(rows) == []
    assert missing_artifact_paths(rows, REPO_ROOT) == []


def test_committed_ledger_claims_nothing_is_checked_or_paper_eligible_yet():
    rows = _load_ledger()
    assert {row["verification_label"] for row in rows} == {"not_yet_checked"}
    assert not any(row["paper_eligibility"] for row in rows)
    assert not any(row["evidence_status"] == "confirmatory" for row in rows)
    claim_levels = [row for row in rows if row["row_type"] == "claim_level"]
    assert [row["claim_id"] for row in claim_levels] == ["C1", "C2", "C3", "C4", "C5", "C6"]
    assert {row["gate_status"] for row in claim_levels} == {"not_passed"}


def test_renamed_donor_row_is_unmeasured_not_a_null():
    row = next(item for item in _load_ledger() if item["claim_id"] == "P1L-16")
    assert row["observed_rows"] == 0
    assert row["evidence_status"] == "NOT_EVALUATED"
    assert row["scientific_null"] is False


def test_zero_rows_cannot_be_exploratory_or_a_null():
    errors = validate_ledger_rows([_row(observed_rows=0, evidence_status="exploratory")])
    assert any("zero observed rows" in error for error in errors)
    errors = validate_ledger_rows([_row(observed_rows=0, scientific_null=True)])
    assert any("scientific null" in error for error in errors)


def test_checked_label_needs_stage_journal_and_artifact():
    errors = validate_ledger_rows([_row(verification_label="verified")])
    assert any("verified_in_stage" in error for error in errors)
    assert any("at least one artifact" in error for error in errors)
    ok = _row(
        verification_label="verified",
        verified_in_stage="14.1",
        journal_ref="J14.1-001",
        artifacts=["data/manifests/physmon_canonical_155.jsonl"],
    )
    assert validate_ledger_rows([ok]) == []


def test_different_but_explained_and_unreproducible_need_an_explanation():
    for label in ("different_but_explained", "unreproducible", "not_enough_source_data"):
        row = _row(
            verification_label=label,
            verified_in_stage="14.1",
            journal_ref="J14.1-002",
            artifacts=["data/manifests/physmon_canonical_155.jsonl"],
        )
        assert any("explanation" in error for error in validate_ledger_rows([row]))


def test_confirmatory_needs_role_and_preregistration():
    errors = validate_ledger_rows([_row(evidence_status="confirmatory")])
    assert any("confirmatory data_role" in error for error in errors)
    assert any("preregistration_ref" in error for error in errors)
    ok = _row(
        evidence_status="confirmatory",
        data_role="INTERNAL_CONFIRMATION",
        preregistration_ref="prereg-001",
    )
    assert validate_ledger_rows([ok]) == []


def test_paper_eligibility_needs_confirmatory_and_verified():
    errors = validate_ledger_rows([_row(paper_eligibility=True)])
    assert any("paper_eligibility" in error for error in errors)


def test_claim_level_rows_need_valid_id_and_gate_evidence():
    row = _row(row_type="claim_level", claim_id="C9", gate_status="not_passed")
    assert any("claim_level rows must use claim_id" in e for e in validate_ledger_rows([row]))
    row = _row(row_type="claim_level", claim_id="C3", gate_status="passed")
    assert any("gate_evidence" in error for error in validate_ledger_rows([row]))


def test_vocabulary_and_duplicate_and_missing_field_errors():
    rows = [_row(), _row(evidence_status="complete_exploratory"), _row(claim_id="T-02")]
    errors = validate_ledger_rows(rows)
    assert any("duplicate claim_id" in error for error in errors)
    assert any("evidence_status" in error and "complete_exploratory" in error for error in errors)
    broken = copy.deepcopy(_row(claim_id="T-03"))
    del broken["artifacts"]
    assert any("missing required field 'artifacts'" in e for e in validate_ledger_rows([broken]))


def test_missing_artifact_path_is_reported():
    errors = missing_artifact_paths([_row(artifacts=["results/does_not_exist.json"])], REPO_ROOT)
    assert errors and "does not exist" in errors[0]


def test_raw_record_contract_reports_absent_fields_but_accepts_explicit_none():
    record = dict.fromkeys(RAW_RECORD_FIELDS)
    assert missing_record_fields(record) == []
    del record["target_span_start"]
    assert missing_record_fields(record) == ["target_span_start"]
    assert set(missing_record_fields(record, causal=True)) >= set(CAUSAL_RECORD_EXTRA_FIELDS)
