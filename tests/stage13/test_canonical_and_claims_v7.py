"""Tests for the v7 canonical evidence table and claim-evidence matrix.

Both v6 artifacts passed their gate checks on shape. These tests pin the
content properties that replaced that: values carry sources, missing values
carry precise reasons, a silently-empty loader fails the build, and estimates
reproduce the governing document's published numbers.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_JSON = REPO_ROOT / "results/stage13/wave0/canonical_evidence_verification_v7.json"
CANONICAL_CSV = REPO_ROOT / "results/canonical/model_family_evidence_v7.csv"
CLAIMS_JSON = REPO_ROOT / "docs/registry/claim_evidence_matrix_v7.json"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


claims_module = _load("build_claim_matrix_v7", "scripts/stage13/build_claim_matrix_v7.py")


class TestAurocImplementation:
    def test_perfect_separation_is_one(self):
        labels = np.array([0, 0, 1, 1])
        scores = np.array([0.1, 0.2, 0.8, 0.9])
        assert claims_module.auroc(labels, scores) == pytest.approx(1.0)

    def test_reversed_separation_is_zero(self):
        labels = np.array([0, 0, 1, 1])
        scores = np.array([0.9, 0.8, 0.2, 0.1])
        assert claims_module.auroc(labels, scores) == pytest.approx(0.0)

    def test_all_ties_is_one_half(self):
        """Tied scores must average ranks, not silently favour one class."""

        labels = np.array([0, 1, 0, 1])
        scores = np.array([0.5, 0.5, 0.5, 0.5])
        assert claims_module.auroc(labels, scores) == pytest.approx(0.5)

    def test_single_class_returns_none_rather_than_a_number(self):
        assert claims_module.auroc(np.array([1, 1, 1]), np.array([0.1, 0.2, 0.3])) is None

    def test_matches_sklearn_on_random_data(self):
        sklearn_metrics = pytest.importorskip("sklearn.metrics")
        rng = np.random.default_rng(0)
        labels = rng.integers(0, 2, 200)
        scores = rng.random(200)
        assert claims_module.auroc(labels, scores) == pytest.approx(
            sklearn_metrics.roc_auc_score(labels, scores)
        )

    def test_bootstrap_is_deterministic_under_the_fixed_seed(self):
        rng = np.random.default_rng(1)
        labels = rng.integers(0, 2, 60)
        scores = rng.random(60)
        first = claims_module.bootstrap_ci(labels, scores, reps=200)
        second = claims_module.bootstrap_ci(labels, scores, reps=200)
        assert first == second


@pytest.mark.skipif(not CANONICAL_JSON.exists(), reason="canonical v7 not generated")
class TestCanonicalEvidence:
    @staticmethod
    def _v():
        return json.loads(CANONICAL_JSON.read_text(encoding="utf-8"))

    def test_populates_more_than_S_lp(self):
        """The v6 table populated only S_lp and still passed its check."""

        verification = self._v()
        assert verification["n_populated_field_types"] > 1
        assert "S_lp" in verification["populated_fields"]

    def test_covers_three_models_and_all_families(self):
        verification = self._v()
        assert verification["canonical_families"] == 155
        assert set(verification["rows_by_model"]) == {
            "qwen_primary", "llama_primary", "deepseek_reasoning"
        }

    def test_no_source_silently_loaded_zero_values(self):
        """A wrong field name must fail the build, not become a null reason."""

        assert self._v()["empty_sources"] == []

    def test_every_populated_value_cites_an_artifact(self):
        with CANONICAL_CSV.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        checked = 0
        for row in rows:
            for key, value in row.items():
                if key.endswith("__source") or key.endswith("__null_reason") or key.endswith("__experiment_ids"):
                    continue
                if key in {"model_id", "canonical_family_id", "domain", "cue_type", "original_or_expansion"}:
                    continue
                if value != "":
                    assert row.get(f"{key}__source"), f"{key} populated without a source"
                    checked += 1
        assert checked > 0

    def test_missing_values_carry_a_precise_reason(self):
        allowed = {
            "not_applicable", "not_measured", "source_not_ingested", "source_unresolved",
            "source_missing", "excluded_ineligible", "parser_invalid",
            "human_validation_pending", "unexpected_missing",
        }
        for key in self._v()["null_reason_counts"]:
            assert key.split(":", 1)[1] in allowed

    def test_human_validation_pending_is_not_a_catch_all(self):
        """Task V6.49 forbids using it for missing monitor or causal data."""

        reasons = self._v()["null_reason_counts"]
        assert not any(k.endswith(":human_validation_pending") for k in reasons)


@pytest.mark.skipif(not CLAIMS_JSON.exists(), reason="claim matrix v7 not generated")
class TestClaimMatrix:
    @staticmethod
    def _c():
        return json.loads(CLAIMS_JSON.read_text(encoding="utf-8"))

    def test_every_claim_cites_an_authoritative_artifact(self):
        payload = self._c()
        assert payload["n_claims_with_artifacts"] == payload["n_claims"]

    def test_no_claim_uses_the_placeholder_estimate(self):
        for claim in self._c()["claims"]:
            assert claim["current_estimate"] != "see linked artifacts"

    def test_family_counts_are_not_defaulted_to_155(self):
        """Task V6.50 forbids defaulting the panel size to the inventory size."""

        for claim in self._c()["claims"]:
            assert claim["family_count"] != 155

    def test_estimates_reproduce_the_governing_document(self):
        """Part II 2.3 headline monitoring values, recomputed from raw artifacts."""

        by_id = {c["claim_id"]: c for c in self._c()["claims"]}
        expected = {"C02": 0.760, "C03": 0.738, "C04": 0.766, "C05": 0.727, "C06": 0.668, "C07": 0.703}
        for claim_id, published in expected.items():
            assert by_id[claim_id]["current_estimate"] == pytest.approx(published, abs=0.002)

    def test_qwen_causal_recovery_is_taken_at_the_frozen_site_layer(self):
        """Pooling across layers dilutes the effect from 1.87 to 0.26."""

        detail = {c["claim_id"]: c for c in self._c()["claims"]}["C08"]["evidence_detail"]
        assert detail["site_layer"] == "16"
        assert detail["estimate"] == pytest.approx(1.87, abs=0.01)
        assert "per_layer_mean_recovery" in detail

    def test_a_recovery_interval_spanning_zero_is_downgraded(self):
        for claim in self._c()["claims"]:
            interval = claim["confidence_interval"]
            if isinstance(interval, list) and claim.get("interval_spans_zero"):
                assert claim["status"] == "estimated_not_distinguishable_from_zero"
                assert interval[0] <= 0 <= interval[1]

    def test_donor_specificity_stays_unsupported(self):
        claim = {c["claim_id"]: c for c in self._c()["claims"]}["C10"]
        assert claim["status"] == "downgraded_unsupported"
        assert claim["family_count"] == 0
        assert "no scientific null" in claim["allowed_wording"].lower()

    def test_nothing_is_marked_paper_eligible(self):
        payload = self._c()
        assert payload["paper_eligibility"] is False
        for claim in payload["claims"]:
            assert claim["discovery_or_confirmation"] == "discovery"

    def test_bootstrap_settings_match_the_governance_policy(self):
        stats = self._c()["statistics"]
        assert stats["bootstrap_seed"] == 42
        assert stats["bootstrap_repetitions"] == 10000
        assert stats["resampling_unit"] == "canonical_family"
