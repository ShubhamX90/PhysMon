"""Tests for the v7 artifact authority audit.

The v6 audit passed or failed on a hard-coded path substring. These tests pin
the two properties that replaced it: classification follows evidence, and a
resolution record is validated rather than trusted.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "stage13" / "run_artifact_authority_audit_v7.py"
AUDIT_PATH = REPO_ROOT / "docs" / "registry" / "artifact_authority_audit_v7.json"


def _load():
    spec = importlib.util.spec_from_file_location("run_artifact_authority_audit_v7", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


audit_module = _load()

VALID_RECORD = {
    "artifact_path": "results/x/y.csv",
    "registry_experiment_id": "exp_a",
    "superseding_artifacts": ["docs/registry/experiment_registry.jsonl"],
    "next_required_experiment": "run it properly",
    "scientific_null": False,
}
REGISTRY = {"exp_a": "partial_not_reportable", "exp_authoritative": "complete_exploratory"}


def test_critical_class_is_not_decided_by_a_hard_coded_path_substring():
    """Any zero-row scientific artifact is critical, not only donor_renamed ones."""

    assert audit_module.classify("results/stageX/science/other/results.csv", 0, 100) == "critical"
    assert audit_module.classify("results/stage12/science/donor_renamed/a.csv", 0, 100) == "critical"


def test_nonzero_scientific_artifact_is_not_critical():
    assert audit_module.classify("results/stage6/behavioural/out.csv", 42, 100) == "paper_relevant_noncritical"


def test_governance_artifacts_are_diagnostic_not_critical():
    assert audit_module.classify("results/stage13/wave0/thing.csv", 0, 10) == "diagnostic"
    assert audit_module.classify("docs/validation/validation_status.csv", 0, 10) == "diagnostic"


def test_valid_resolution_record_is_accepted():
    valid, problems = audit_module.validate_resolution(VALID_RECORD, REGISTRY)
    assert valid, problems


def test_resolution_rejected_when_registry_entry_is_missing():
    record = dict(VALID_RECORD, registry_experiment_id="nope")
    valid, problems = audit_module.validate_resolution(record, REGISTRY)
    assert not valid
    assert any("not in registry" in p for p in problems)


def test_resolution_rejected_when_registry_status_is_authoritative():
    """A zero-row artifact cannot be resolved against a run treated as good evidence."""

    record = dict(VALID_RECORD, registry_experiment_id="exp_authoritative")
    valid, problems = audit_module.validate_resolution(record, REGISTRY)
    assert not valid
    assert any("authoritative" in p for p in problems)


def test_resolution_rejected_when_superseding_artifact_does_not_exist():
    record = dict(VALID_RECORD, superseding_artifacts=["docs/registry/not_a_real_file.json"])
    valid, problems = audit_module.validate_resolution(record, REGISTRY)
    assert not valid
    assert any("does not exist" in p for p in problems)


def test_resolution_rejected_without_next_required_experiment():
    record = dict(VALID_RECORD, next_required_experiment="   ")
    valid, problems = audit_module.validate_resolution(record, REGISTRY)
    assert not valid
    assert any("next_required_experiment" in p for p in problems)


def test_resolution_rejected_if_it_claims_a_scientific_null():
    """Zero rows must never be recorded as a measured zero effect."""

    record = dict(VALID_RECORD, scientific_null=True)
    valid, problems = audit_module.validate_resolution(record, REGISTRY)
    assert not valid
    assert any("scientific_null" in p for p in problems)


def test_row_counting_distinguishes_empty_from_absent():
    header_only = REPO_ROOT / "results/stage12/science/donor_renamed/same_answer/same_answer_donor_results.csv"
    if header_only.exists():
        assert audit_module.count_rows(header_only) == 0


@pytest.mark.skipif(not AUDIT_PATH.exists(), reason="audit artifact not generated yet")
class TestGeneratedAudit:
    @staticmethod
    def _audit():
        return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

    def test_every_critical_artifact_is_accounted_for(self):
        audit = self._audit()
        assert audit["n_critical"] == len(audit["critical_resolved_paths"]) + audit["critical_unresolved"]

    def test_no_resolution_record_was_rejected(self):
        assert self._audit()["n_resolution_records_rejected"] == 0

    def test_resolution_never_means_measured_null(self):
        assert "never means measured null" in self._audit()["resolution_semantics"]

    def test_zero_row_artifacts_are_still_reported_even_when_resolved(self):
        # Resolving an artifact must not erase it from the zero-row count.
        assert self._audit()["zero_row_issues"] >= self._audit()["n_critical"]

    def test_scan_covers_more_than_tabular_files(self):
        types = self._audit()["artifacts_scanned_by_type"]
        assert {"json", "csv", "md"} <= set(types)
