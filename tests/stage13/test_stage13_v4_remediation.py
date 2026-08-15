import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_jsonl(path: str):
    return [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]


def load_script_module(path: str, name: str):
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_zero_row_donor_controls_are_failed_not_zero_effects():
    audit = load_json("results/stage13/benchmark_integrity/donor_renamed_empty_panel_audit_v4.json")
    for control in audit["controls"].values():
        assert control["raw_data_rows"] == 0
        assert control["summary_defaulted_zero"] is True
        assert control["mean_recovery"] is None
        assert control["median_recovery"] is None
        assert control["scientific_null"] is False
        assert control["status"] == "FAILED_EMPTY_RESULT_PANEL"

    registry = {row["experiment_id"]: row for row in load_jsonl("docs/registry/experiment_registry.jsonl")}
    for experiment_id in ["stage12_donor_renamed_same_answer", "stage12_donor_renamed_stable"]:
        assert registry[experiment_id]["status"] == "partial_not_reportable"
        assert registry[experiment_id]["raw_data_rows"] == 0
        assert registry[experiment_id]["scientific_null"] is False


def test_donor_scripts_return_null_summaries_for_empty_panels():
    same = load_script_module("scripts/run_same_answer_donor.py", "run_same_answer_donor_for_test")
    stable = load_script_module("scripts/run_stable_donor.py", "run_stable_donor_for_test")
    same_summary = same.summarize_same_answer_rows([], n_target_families=10, reference_mhk=1.0)
    stable_summary = stable.summarize_stable_donor_rows([], n_target_families=10)
    for summary in [same_summary, stable_summary]:
        assert summary["rows"] == 0
        assert summary["mean_recovery"] is None
        assert summary["median_recovery"] is None
        assert summary["status"] == "FAILED_EMPTY_RESULT_PANEL"
        assert summary["paper_eligibility"] is False
        assert summary["scientific_null"] is False


def test_donor_specificity_v4_does_not_pool_empty_renamed_controls():
    summary = load_json("results/stage12/science/donor_specificity/donor_specificity_summary_v4_correction.json")
    renamed = summary["renamed_families"]
    assert renamed["status"] == "incomplete_empty_result_panel"
    assert renamed["same_answer_raw_rows"] == 0
    assert renamed["stable_raw_rows"] == 0
    assert renamed["mean_recovery"] is None
    assert renamed["scientific_null"] is False


def test_balance_v3_uses_tie_aware_sklearn_auc_and_grouped_cv():
    audit = load_json("results/stage13/benchmark_integrity/balance_audit_v3.json")
    assert audit["status"] == "VALID_GROUPED_CV_AUDIT"
    assert audit["combined_surface_model"]["n_folds"] == 5
    assert audit["combined_surface_model"]["n_oof_predictions"] > 0
    assert audit["combined_surface_model"]["combined_grouped_cv_auroc"] is not None

    rows = []
    with (ROOT / "results/stage13/benchmark_integrity/balance_audit_v3_predictions.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    sklearn_auc = roc_auc_score(
        [int(row["label"]) for row in rows],
        [float(row["oof_surface_score"]) for row in rows],
    )
    assert abs(sklearn_auc - audit["combined_surface_model"]["combined_grouped_cv_auroc"]) < 1e-12


def test_parser_v3_is_balanced_and_distinguishes_fraction_from_unit_slash():
    status = load_json("results/stage13/benchmark_integrity/parser_audit_status_v3.json")
    assert status["n_candidates"] >= 120
    assert min(status["model_counts"].values()) >= 30
    rows = load_jsonl("docs/validation/parser_audit_candidates_v3.jsonl")
    by_id = {row["candidate_id"]: row for row in rows}
    assert by_id["designed::edge_fraction"]["category"] == "fraction"
    assert by_id["designed::edge_unit_slash"]["category"] == "equivalent_units"
    assert re.search(r"\d+\s*/\s*\d+", by_id["designed::edge_fraction"]["raw_output"])


def test_pass2_v3_certificates_have_non_empty_content():
    packets = load_jsonl("docs/validation/stage13_validation_packet_pass2_v3.jsonl")
    assert len(packets) == 25
    for packet in packets:
        cert = packet["certificate"]
        assert cert["governing_equations"]
        assert cert["symbolic_derivation"]
        assert cert["stated_assumptions"]
        assert cert["invariance_checks"]
        assert cert["dimensional_checks"]


def test_mutation_v3_executes_positive_and_negative_certificate_checks():
    summary = load_json("results/stage13/benchmark_integrity/mutation_test_summary_v3.json")
    assert summary["negative_operators_executed"]
    assert summary["positive_operators_executed"]
    assert summary["negative_rejection_rate"] == 1.0
    assert summary["positive_acceptance_rate"] == 1.0


def test_leakage_v3_actually_evaluates_derived_prompts():
    leakage = load_json("results/stage13/benchmark_integrity/leakage_audit_v3.json")
    assert leakage["derived_variants_actually_evaluated"] is True
    assert leakage["n_derived_prompts"] > 0
    assert leakage["pair_candidate_count"] >= leakage["connected_component_cluster_count"]


def test_canonical_v4_has_valid_null_reasons():
    result = load_json("results/stage13/wave0/canonical_evidence_verification_v4.json")
    allowed = set(result["valid_null_reasons"])
    assert set(result["null_reason_counts"]) <= allowed
    assert sum(result["null_reason_counts"].values()) > 0


def test_wave1a_v4_fails_truthfully_until_human_pilot_ready():
    gate = load_json("results/stage13/benchmark_integrity/wave1a_gate_v4.json")
    assert gate["status"] == "FAIL"
    assert gate["human_pilot_status"] == "NOT_READY"
    assert gate["permission_for_wave2"] is False


def test_gate_v4_binds_final_artifact_hashes():
    gate = load_json("results/stage13/wave0/wave0_gate_v4.json")
    hashes = gate["input_hashes"]
    assert hashes["authority_v4"]
    assert hashes["balance_v3"]
    assert hashes["mutation_v3"]
    assert hashes["parser_v3"]
