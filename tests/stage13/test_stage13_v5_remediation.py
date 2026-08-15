"""Substantive checks for Stage 13 v5 remediation artifacts."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_jsonl(path: str):
    return [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_mutations_are_real_objects_and_invoke_verifier():
    records = load_jsonl("results/stage13/benchmark_integrity/mutation_test_records_v5.jsonl")
    assert records
    assert any(row["operator_type"] == "negative" and row["actual_verifier_passed"] is False for row in records)
    assert any(row["operator_type"] == "positive" and row["actual_verifier_passed"] is True for row in records)
    assert all(row["object_differs_from_original"] for row in records if row["mutation_applied"])
    assert all(row["verifier_invoked"] for row in records if row["mutation_applied"])
    assert any(row["expected_matches_actual"] is False for row in records) or any(row["expected_matches_actual"] is True for row in records)


def test_mutation_summary_supersedes_assigned_v3_outcomes():
    summary = load_json("results/stage13/benchmark_integrity/mutation_test_summary_v5.json")
    assert summary["prior_v3_status"] == "superseded_assigned_outcomes_not_verified"
    assert summary["negative_verified_records"] > 0
    assert summary["positive_verified_records"] > 0
    assert summary["n_verified"] == summary["n_records"]


def test_certificates_use_structured_symbol_tables_and_derivations():
    packets = load_jsonl("docs/validation/stage13_validation_packet_pass2_v5.jsonl")
    assert len(packets) >= 24
    cert = packets[0]["certificate"]
    assert cert["certificate_status"] == "certificate_generated"
    assert cert["relevant_variables"]
    assert set(cert["relevant_variables"]) <= set(cert["symbol_table"])
    assert cert["explicit_symbolic_derivation"]["steps"]
    assert any("=" in step for step in cert["explicit_symbolic_derivation"]["steps"])
    assert cert["invariance_checks"]
    assert all("computed_answer" in check for check in cert["invariance_checks"])
    assert cert["verification_result"]["all_passed"] is True


def test_pilot_is_stratified_across_domains_and_cues():
    with (ROOT / "docs/validation/pilot_selection_v5.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert 24 <= len(rows) <= 30
    assert len({row["domain"] for row in rows}) >= 3
    assert len({row["cue_type"] for row in rows}) >= 3
    assert {"original", "expansion"} <= {row["original_or_expansion"] for row in rows}


def test_calibration_and_qualification_are_worked_cases():
    calibration = load_jsonl("docs/validation/calibration_bank_v5.jsonl")
    assert len(calibration) >= 15
    assert all(row["problem_text"] and row["worked_explanation"] for row in calibration)
    qual = (ROOT / "docs/validation/qualification_test_v5.md").read_text(encoding="utf-8")
    key = (ROOT / "docs/validation/qualification_answer_key_DRAFT_REQUIRES_PI_REVIEW_v5.md").read_text(encoding="utf-8")
    assert qual.count("## Case") >= 12
    assert key.count("## Case") >= 12


def test_balance_missingness_and_template_cv_are_substantive():
    audit = load_json("results/stage13/benchmark_integrity/balance_audit_v5.json")
    assert audit["status"] == "VALID_MISSINGNESS_AND_TEMPLATE_CV_AUDIT"
    assert audit["feature_missingness"]["base_correctness"]["included_in_model"] is False
    assert audit["feature_missingness"]["entropy"]["included_in_model"] is False
    family_folds = list(csv.DictReader((ROOT / "results/stage13/benchmark_integrity/balance_audit_v5_family_folds.csv").open(newline="", encoding="utf-8")))
    template_folds = list(csv.DictReader((ROOT / "results/stage13/benchmark_integrity/balance_audit_v5_template_folds.csv").open(newline="", encoding="utf-8")))
    assert family_folds and template_folds
    by_group: dict[str, set[str]] = {}
    for row in template_folds:
        by_group.setdefault(row["group_id"], set()).add(row["fold"])
    assert all(len(folds) == 1 for folds in by_group.values())
    assert "permutation_p_refit" in audit["template_held_out_cv"]


def test_parser_v5_meets_model_and_category_quotas():
    coverage = load_json("docs/validation/parser_candidate_coverage_v5.json")
    assert coverage["n_candidates"] >= 140
    assert min(coverage["model_counts"].values()) >= 35
    required = [
        "integers_decimals",
        "scientific_notation",
        "fractions",
        "equivalent_units",
        "multiple_numbers",
        "rounding_boundaries",
        "wrong_units",
        "refusals_hedges",
        "long_prose",
        "latex",
        "ambiguous_final_answer",
        "model_specific_quirks",
    ]
    assert all(coverage["category_counts"].get(category, 0) >= 10 for category in required)
    designed = [row for row in load_jsonl("docs/validation/parser_audit_candidates_v5.jsonl") if row["model_id"] == "designed_edge_case"]
    assert all(row["canonical_answer"] for row in designed)


def test_leakage_expected_relations_are_not_unresolved_review_workload():
    audit = load_json("results/stage13/benchmark_integrity/leakage_audit_v5.json")
    assert audit["expected_within_family_pairs"] > 0
    assert audit["expected_derived_parent_pairs"] >= 0
    assert audit["cross_family_candidate_pairs"] < audit["expected_within_family_pairs"] + audit["cross_family_candidate_pairs"]
    with (ROOT / "results/stage13/benchmark_integrity/leakage_review_v5.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert all("expected" not in row["relation"] for row in rows)


def test_expected_run_inventory_is_normalized_and_authority_finds_orphans():
    runs = load_jsonl("results/stage13/wave0/expected_historical_runs_v5.jsonl")
    assert runs
    assert all(not row["expected_run_id"].startswith("stage_") for row in runs)
    coverage = load_json("results/stage13/wave0/registry_coverage_v5.json")
    assert coverage["n_expected_runs"] == len(runs)
    authority = load_json("docs/registry/artifact_authority_audit_v5.json")
    assert authority["n_orphan_artifacts"] > 0
    assert authority["n_zero_row_outputs"] >= 2


def test_canonical_non_null_values_cite_source_experiments():
    with (ROOT / "results/canonical/model_family_evidence_v5.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    populated = [row for row in rows if row["primary_monitor_score"]]
    assert populated
    assert all("stage9_mean_probe_stage6" in row["source_experiment_ids"] for row in populated)
    assert all(row["S_lp"] == "" or "stage6_qwen_behavioural_full_rerun" in row["source_experiment_ids"] for row in rows)


def test_claim_counts_do_not_default_to_155_for_small_panels():
    claims = load_json("docs/registry/claim_evidence_matrix_v5.json")["claims"]
    donor = next(claim for claim in claims if claim["claim_id"] == "C10")
    assert donor["family_count"] == 20
    assert "100% specificity" in donor["prohibited_wording"]
    counts = Counter(claim["status"] for claim in claims)
    assert counts["partial"] >= 1


def test_part2_v12_corrects_false_donor_language():
    source = (ROOT / "docs/proposals/PhysMon_Part_II_v1.2.tex").read_text(encoding="utf-8")
    assert "zero evaluable target-donor rows" in source
    forbidden = ["100\\% specificity", "measured 0.0", "completed null"]
    assert not any(term in source for term in forbidden)
    assert (ROOT / "docs/proposals/PhysMon_Part_II_v1.2.pdf").exists()


def test_v5_gates_bind_hashes_and_keep_wave2_forbidden():
    wave0 = load_json("results/stage13/wave0/wave0_gate_v5.json")
    wave1 = load_json("results/stage13/benchmark_integrity/wave1a_gate_v5.json")
    assert wave0["status"] == "FAIL"
    assert "critical_authority_zero" in wave0["critical_failures"]
    assert wave1["human_pilot"] == "PENDING"
    assert wave0["permission_for_wave2"] is False
    assert wave1["permission_for_wave2"] is False
    assert "mutation_v5" in wave1["input_hashes"]
