"""Substantive checks for Stage 13 v6 remediation artifacts."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_jsonl(path: str):
    return [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_erratum_is_not_treated_as_full_part2():
    rule = (ROOT / "docs/proposals/PhysMon_Part_II_governing_document_rule.md").read_text(encoding="utf-8")
    assert "complete 42-page Part II v1.1" in rule
    assert "erratum supersedes only the renamed donor-control statements" in rule
    assert "blocked_source_unavailable" in rule
    assert (ROOT / "docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf").exists()


def test_misleading_mutation_names_removed_and_scope_recorded():
    summary = load_json("results/stage13/benchmark_integrity/mutation_test_summary_v6.json")
    active = {row["operator_id"] for row in summary["operator_summaries"]}
    assert "dimensional_corruption" not in active
    assert "target_quantity_change" not in active
    assert "assumption_removal" not in active
    assert "negative_parameter_value" in active
    assert "incorrect_canonical_answer" in active
    assert summary["true_dimensional_mutation_status"] == "unsupported_no_dimensional_checker"
    assert "does not validate full natural-language semantics" in summary["verifier_scope_statement"]


def test_mutation_records_are_verifier_backed_and_portable():
    records = load_jsonl("results/stage13/benchmark_integrity/mutation_test_records_v6.jsonl")
    assert any(row["operator_type"] == "negative" and row["actual_verifier_passed"] is False for row in records if row["verifier_invoked"])
    assert any(row["operator_type"] == "positive" and row["actual_verifier_passed"] is True for row in records if row["verifier_invoked"])
    assert all("/Users/" not in json.dumps(row) for row in records)
    true_unit = [row for row in records if row["operator_id"] == "true_unit_metadata_corruption"]
    assert true_unit
    assert all("unsupported" in row["coverage_status"] for row in true_unit)


def test_certificates_use_symbol_tables_derivations_and_honest_status():
    summary = load_json("results/stage13/benchmark_integrity/certificate_generation_summary_v6.json")
    assert "certificate_generated" not in summary["status_counts"]
    packet = load_jsonl("docs/validation/stage13_validation_packet_pass2_v6.jsonl")[0]
    cert = packet["certificate"]
    assert cert["certificate_status"] in {
        "structured_machine_certificate_verified",
        "frame_equivalence_unverified",
        "certificate_verification_failed",
    }
    assert cert["relevant_variables"]
    assert set(cert["relevant_variables"]) <= set(cert["symbol_table"])
    for symbol, spec in cert["symbol_table"].items():
        assert spec["symbol"] == symbol
        assert spec["source_field"].startswith("parameters.")
    derivation = cert["explicit_symbolic_derivation"]
    assert derivation["numeric_substitution"]
    assert derivation["intermediate_calculation"]
    assert derivation["canonical_answer_comparison"]
    assert cert["dimensional_check"]["status"] == "unit_metadata_recorded_not_symbolically_verified"


def test_frame_unit_conversion_is_numerically_checked_for_supported_case():
    cert = load_json("docs/validation/certificates_v6/CM_C_001.json")
    frame = cert["frame_unit_equivalence_check"]
    assert frame["status"] == "verified_explicit_conversion_table"
    assert all(check["equivalent"] for check in frame["checks"])


def test_no_v6_generated_artifact_contains_local_absolute_path():
    pattern = re.compile(r"/Users/|C:\\|/home/[A-Za-z0-9_.-]+/")
    roots = ["docs/stage13", "docs/proposals", "docs/validation", "docs/registry", "results/stage13", "results/canonical", "schemas"]
    offenders = []
    for root in roots:
        for path in (ROOT / root).rglob("*v6*"):
            if path.is_file() and path.suffix.lower() not in {".pdf", ".png", ".zip", ".pyc"}:
                text = path.read_text(encoding="utf-8")
                if pattern.search(text):
                    offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_validation_materials_have_required_fields_and_strata():
    with (ROOT / "docs/validation/pilot_selection_v6.csv").open(newline="", encoding="utf-8") as handle:
        pilot = list(csv.DictReader(handle))
    assert 24 <= len(pilot) <= 30
    assert len({row["domain"] for row in pilot}) >= 3
    assert len({row["cue_type"] for row in pilot}) >= 3
    assert {"original", "expansion"} <= {row["original_or_expansion"] for row in pilot}
    calibration = load_jsonl("docs/validation/calibration_bank_v6.jsonl")
    assert len(calibration) >= 15
    for case in calibration:
        assert case["all_variants"]
        assert case["governing_law"] != "see explanation"
        assert case["relevant_variables"]
        assert case["designated_cue"]
        assert case["detailed_explanation"]
    pass1 = load_jsonl("docs/validation/stage13_validation_packet_pass1_v6.jsonl")[0]
    for field in ["assumptions_sufficient", "answer_unique", "unintended_covariation", "overall_verdict", "confidence"]:
        assert field in pass1["requested_fields"]


def test_balance_excludes_missing_labels_and_uses_template_groups():
    audit = load_json("results/stage13/benchmark_integrity/balance_audit_v6.json")
    assert audit["n_labeled_families"] == 140
    assert audit["n_unlabeled_families"] == 15
    assert audit["missing_label_policy"].startswith("families without authoritative S_lp are excluded")
    assert audit["template_held_out_cv"]["n_permutations_refit_requested"] == 200
    groups = list(csv.DictReader((ROOT / "results/stage13/benchmark_integrity/balance_audit_v6_groups.csv").open(newline="", encoding="utf-8")))
    assert groups
    assert any("::" in row["template_group"] for row in groups)


def test_parser_candidates_are_unique_and_categories_are_substantive():
    coverage = load_json("docs/validation/parser_candidate_coverage_v6.json")
    assert coverage["n_rows"] == coverage["n_unique_raw_outputs"]
    assert min(coverage["model_counts"].values()) >= 35
    assert coverage["category_counts"]["equivalent_units"] >= 10
    assert coverage["category_counts"]["numeric_fractions"] >= 10
    rows = load_jsonl("docs/validation/parser_audit_candidates_v6.jsonl")
    assert not any("[edge" in row["raw_output"] for row in rows)
    assert any("equivalently" in row["raw_output"] for row in rows if "equivalent_units" in row["categories"])
    assert all(re.search(r"(?<![A-Za-z])\d+\s*/\s*\d+(?![A-Za-z])", row["raw_output"]) for row in rows if "numeric_fractions" in row["categories"])


def test_leakage_detector_coverage_and_expected_relation_handling():
    audit = load_json("results/stage13/benchmark_integrity/leakage_audit_v6.json")
    for detector in [
        "exact_prompt_hash",
        "number_masked_prompt_hash",
        "normalized_symbolic_equation_hash",
        "variable_renaming_invariant_structure_hash",
        "cue_template_hash",
        "numeric_instantiation_sibling_detection",
        "lexical_similarity",
    ]:
        assert audit["detectors"][detector] == "active"
    assert audit["expected_within_family_pairs"] > 0
    assert audit["expected_derived_parent_pairs"] > 0
    assert audit["status"] in {"PASS", "INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW"}


def test_run_crosswalk_authority_canonical_claims_and_gates():
    crosswalk = load_json("results/stage13/wave0/registry_coverage_v6.json")
    assert crosswalk["n_expected_runs"] > 0
    assert crosswalk["unmatched"] >= 0
    authority = load_json("docs/registry/artifact_authority_audit_v6.json")
    assert "json" in authority["artifacts_scanned_by_type"]
    assert authority["zero_row_issues"] >= 2
    canonical = load_json("results/stage13/wave0/canonical_evidence_verification_v6.json")
    assert canonical["model_family_rows"] == 465
    assert set(canonical["rows_by_model"]) == {"qwen_primary", "llama_primary", "deepseek_reasoning"}
    claims = load_json("docs/registry/claim_evidence_matrix_v6.json")["claims"]
    assert any(claim["claim_id"] == "C10" and claim["status"] == "downgraded" for claim in claims)
    assert all(claim["family_count"] != 155 or claim["claim_id"] == "C01" for claim in claims)
    wave0 = load_json("results/stage13/wave0/wave0_gate_v6.json")
    wave1 = load_json("results/stage13/benchmark_integrity/wave1a_gate_v6.json")
    assert wave0["status"] == "FAIL"
    assert wave1["status"] == "FAIL"
    assert wave0["permission_for_wave2"] is False
    assert wave1["permission_for_wave2"] is False
