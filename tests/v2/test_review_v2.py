"""Tests for the v2 review-record contract and agreement metrics (Stage 14.5)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance import review as rv  # noqa: E402


def _record(**overrides):
    base = {
        "reviewer_id": "R1", "item_id": "Q001", "pass_number": 1,
        "started_at": "2026-10-16T10:00:00+05:30", "completed_at": "2026-10-16T10:12:00+05:30",
        "minutes_spent": 12.0, "blinding_attestation": True, "validity": "valid", "clarity": "clear",
        "difficulty": 3, "naturalness": "natural", "confidence": 4, "uncertain_fields": [],
        "defect_flags": [], "counterexamples": [], "notes": "",
    }
    base.update(overrides)
    return base


def _pass2(**overrides):
    fields = {"pass_number": 2, "equation_consistent": True, "units_consistent": True, "answer_correct": True,
              "precision_adequate": True, "admission_category": "CERTIFIED_AND_VALIDATED"}
    fields.update(overrides)
    return _record(**fields)


def test_a_complete_pass1_and_pass2_record_is_valid():
    assert rv.validate_review(_record()) == []
    assert rv.validate_review(_pass2()) == []


def test_blank_required_fields_and_missing_attestation_are_errors():
    assert any("missing required field 'validity'" in e for e in rv.validate_review(_record(validity="")))
    assert any("blinding_attestation" in e for e in rv.validate_review(_record(blinding_attestation=False)))
    assert any("minutes_spent" in e for e in rv.validate_review(_record(minutes_spent=0)))


def test_invalid_and_uncertain_verdicts_need_their_evidence():
    assert any("defect_flags" in e for e in rv.validate_review(_record(validity="invalid")))
    assert rv.validate_review(_record(validity="invalid", defect_flags=["missing_assumption"])) == []
    assert any("uncertain_fields" in e for e in rv.validate_review(_record(validity="uncertain")))
    assert rv.validate_review(_record(validity="uncertain", uncertain_fields=["assumptions"])) == []


def test_pass2_needs_the_certificate_judgments_and_a_known_admission_category():
    bad = _pass2()
    del bad["answer_correct"]
    assert any("answer_correct" in e for e in rv.validate_review(bad))
    assert any("admission_category" in e for e in rv.validate_review(_pass2(admission_category="GOOD")))


def test_judgments_are_separate_and_each_has_its_own_vocabulary():
    assert any("clarity" in e for e in rv.validate_review(_record(clarity="fine")))
    assert any("naturalness" in e for e in rv.validate_review(_record(naturalness="ok")))
    assert any("difficulty" in e for e in rv.validate_review(_record(difficulty=9)))


def test_kappa_and_ac1_match_hand_calculation_and_sklearn():
    a = ["valid", "valid", "invalid", "invalid"]
    b = ["valid", "invalid", "invalid", "invalid"]
    assert rv.raw_agreement(a, b) == pytest.approx(0.75)
    assert rv.cohens_kappa(a, b) == pytest.approx(0.5)
    assert rv.gwet_ac1(a, b, ["valid", "invalid"]) == pytest.approx(0.28125 / 0.53125)
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    generator = np.random.default_rng(4)
    x = generator.choice(["valid", "invalid", "uncertain"], 60, p=[0.6, 0.3, 0.1]).tolist()
    y = generator.choice(["valid", "invalid", "uncertain"], 60, p=[0.6, 0.3, 0.1]).tolist()
    assert rv.cohens_kappa(x, y) == pytest.approx(sklearn_metrics.cohen_kappa_score(x, y), abs=1e-12)


def test_kappa_is_undefined_not_one_when_every_rating_is_identical_and_constant():
    same = ["valid"] * 10
    assert rv.cohens_kappa(same, same) is None
    # AC1 stays defined under extreme prevalence, which is why the plan asks for it alongside kappa.
    assert rv.gwet_ac1(same, same, ["valid", "invalid"]) == pytest.approx(1.0)


def test_ac1_is_not_misled_by_prevalence_where_kappa_is():
    a = ["valid"] * 18 + ["invalid", "valid"]
    b = ["valid"] * 18 + ["valid", "invalid"]
    assert rv.raw_agreement(a, b) == pytest.approx(0.9)
    assert rv.cohens_kappa(a, b) < 0 < rv.gwet_ac1(a, b, ["valid", "invalid"])


def test_pairwise_report_resamples_clusters_and_is_deterministic():
    items = [f"Q{i:02d}" for i in range(12)]
    a = {i: ("valid" if n % 3 else "invalid") for n, i in enumerate(items)}
    b = {i: ("valid" if n % 4 else "invalid") for n, i in enumerate(items)}
    clusters = {i: f"C{n // 2}" for n, i in enumerate(items)}
    one = rv.pairwise_agreement_report(a, b, ["valid", "invalid"], clusters, n_resamples=100, seed=1)
    two = rv.pairwise_agreement_report(a, b, ["valid", "invalid"], clusters, n_resamples=100, seed=1)
    assert one == two and one["n_items"] == 12
    assert one["gwet_ac1_cluster_bootstrap"]["ci95_low"] <= one["gwet_ac1_cluster_bootstrap"]["ci95_high"]
    with pytest.raises(ValueError):
        rv.pairwise_agreement_report({"x": "valid"}, {"y": "valid"}, ["valid", "invalid"])


KEY = {
    "Q1": {"defect_type": "hidden_coupling", "expected_verdict": "invalid", "detectable_in": "pass1"},
    "Q2": {"defect_type": "hidden_coupling", "expected_verdict": "invalid", "detectable_in": "pass1"},
    "Q3": {"defect_type": "invalid_numerical_precision", "expected_verdict": "invalid", "detectable_in": "pass2"},
    "Q4": {"defect_type": "valid_equivalent_rewrite", "expected_verdict": "valid", "detectable_in": "pass1"},
}


def test_detection_is_counted_per_defect_type_and_only_in_the_pass_where_it_is_visible():
    records = [
        _record(item_id="Q1", validity="invalid", defect_flags=["hidden_coupling"]),
        _record(item_id="Q2", validity="uncertain", uncertain_fields=["coupling"]),
        _record(item_id="Q3", validity="invalid", defect_flags=["invalid_numerical_precision"]),  # pass 1: ignored
        _pass2(item_id="Q3", validity="valid"),  # pass 2 missed it
        _record(item_id="Q4", validity="invalid", defect_flags=["missing_assumption"]),  # false rejection
    ]
    report = rv.detection_by_defect(records, KEY)
    coupling = report["hidden_coupling"]
    assert coupling["n_reviews"] == 2
    assert coupling["sensitivity_detected"] == pytest.approx(0.5)
    assert coupling["sensitivity_flagged"] == pytest.approx(1.0)
    assert coupling["attribution_rate"] == pytest.approx(0.5)
    assert report["invalid_numerical_precision"]["sensitivity_detected"] == 0.0
    assert report["valid_equivalent_rewrite"]["false_rejection_rate"] == pytest.approx(1.0)
    assert rv.missed_defect_types(report) == ["invalid_numerical_precision"]
    assert rv.missed_defect_types(report, minimum_sensitivity=0.75) == [
        "hidden_coupling", "invalid_numerical_precision"]


def test_completeness_reports_missing_reviews_instead_of_assuming_agreement():
    records = [_record(reviewer_id="R1", item_id="Q1"), _pass2(reviewer_id="R1", item_id="Q1")]
    result = rv.completeness(records, ["Q1", "Q2"], ["R1", "R2"])
    assert result["expected"] == 8 and result["present"] == 2
    assert ["R2", "Q1", 1] in result["missing"] and ["R1", "Q2", 2] in result["missing"]
