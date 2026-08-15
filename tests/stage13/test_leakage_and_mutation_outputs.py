import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_leakage_audit_v2_keeps_near_duplicate_review_unresolved_not_pass():
    result = json.loads(
        (ROOT / "results/stage13/benchmark_integrity/leakage_audit_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["status"] in {
        "PASS",
        "FAIL_EXACT_CROSS_SPLIT_DUPLICATE",
        "INCOMPLETE_PENDING_NEAR_DUPLICATE_REVIEW",
    }
    assert result["status"] != "PASS" or result["n_near_duplicate_clusters"] == 0
    assert result["n_prompts"] >= 155
    assert result["derived_variants_included"] is True


def test_leakage_review_v2_has_clustered_canonical_family_links():
    review_path = ROOT / "results/stage13/benchmark_integrity/leakage_review_v2.csv"
    with review_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if rows:
        required = {"cluster_id", "family_a", "family_b", "detector", "review_priority", "cross_split"}
        assert required <= set(rows[0])


def test_balance_audit_v2_is_substantive_not_descriptive_only():
    result = json.loads(
        (ROOT / "results/stage13/benchmark_integrity/balance_audit_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["status"] == "INCOMPLETE_SUBSTANTIVE_AUDIT_READY"
    assert result["strongest_confound"]["feature"]
    assert result["grouped_cv_combined_surface_feature_auroc"] is not None
    assert "prompt_length" in result["feature_audits"]


def test_mutation_harness_records_supported_and_unsupported_coverage():
    result = json.loads(
        (ROOT / "results/stage13/benchmark_integrity/mutation_test_summary_v2.json").read_text(
            encoding="utf-8"
        )
    )
    statuses = set(result["status_counts"])
    assert "coverage_not_supported" in statuses
    assert "executed_control" in statuses
    assert result["paper_eligibility"] is False


def test_mutation_operator_applicability_contract():
    from physmon.validation.mutation_operators import default_mutation_operators

    family = {
        "template_id": "T",
        "variants": [{"prompt": "A force F = 2 N acts on mass m = 1 kg."}],
        "cue_type": "nongoverning_distractor",
    }
    outcomes = [operator.apply(family) for operator in default_mutation_operators()]
    assert any(out.status == "executed_control" for out in outcomes)
    assert any(out.status == "coverage_not_supported" for out in outcomes)
    assert all(out.operator_id for out in outcomes)
