"""Tests for the Stage 14.4 structure-overlap analysis (hermetic: committed artifacts only)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "s144_structure_overlap", REPO_ROOT / "scripts/v2/s144_structure_overlap.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s144 = _load()


def _row(template_id, qwen_s_lp, parse_ok, notes=""):
    return {"template_id": template_id, "cue_type": "nongoverning_distractor",
            "qwen_S_lp": str(qwen_s_lp), "qwen_parse_ok": parse_ok, "notes": notes}


def test_excluded_five_detects_an_outcome_dependent_filter():
    rows = [
        _row("A", 0.0, "False", "qwen_degraded"), _row("B", 0.25, "False", "qwen_degraded"),
        _row("C", 3.0, "False", "qwen_degraded"), _row("D", 5.0, "False", "qwen_degraded"),
        _row("E", 0.0, "True"), _row("F", 2.0, "True"),
    ]
    cohort = {"C", "D", "E", "F"}  # the stable parse failures A and B are excluded
    result = s144.excluded_five(rows, cohort)
    assert result["n_qwen_parse_failure_families"] == 4
    assert [r["template_id"] for r in result["excluded"]] == ["A", "B"]
    assert result["exclusion_depends_on_the_outcome_label"] is True
    assert result["qwen_parse_failures_outside_the_degraded_set"] == 0


def test_excluded_five_flag_is_true_only_for_the_stable_excluded_sensitive_kept_pattern():
    rows = [_row("A", 0.0, "False", "qwen_degraded"), _row("B", 4.0, "False", "qwen_degraded")]
    # A (stable) excluded and B (sensitive) kept: the exclusion tracks the outcome.
    assert s144.excluded_five(rows, {"B"})["exclusion_depends_on_the_outcome_label"] is True
    # The reverse pattern (sensitive excluded, stable kept) is a different rule and is not flagged by this test.
    assert s144.excluded_five(rows, {"A"})["exclusion_depends_on_the_outcome_label"] is False
    # Excluding both or neither carries no label pattern.
    assert s144.excluded_five(rows, set())["exclusion_depends_on_the_outcome_label"] is False
    assert s144.excluded_five(rows, {"A", "B"})["exclusion_depends_on_the_outcome_label"] is False


def test_exposure_summary_counts_families_with_a_cluster_mate():
    manifest = {f: {"cue_type": "nongoverning_distractor", "domain": "mechanics"} for f in "abcdef"}
    cluster_of = s144.cl.union_find_components(sorted(manifest), [("a", "b"), ("b", "c"), ("d", "e")])
    info, exposure = s144.exposure_summary(cluster_of, [("a", "b"), ("b", "c"), ("d", "e")], manifest,
                                           ["a", "b", "d", "f"])
    assert info["n_families_in_unresolved_review"] == 5
    assert info["n_clusters_with_two_or_more_families"] == 2
    assert info["cohort_exposed_under_leave_one_family_out"] == 2
    assert exposure == {"a": True, "b": True, "d": False, "f": False}


@pytest.fixture(scope="module")
def committed_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("s144")
    ledger = out / "ledger.jsonl"
    shutil.copy(REPO_ROOT / s144.LEDGER, ledger)
    s144.N_BOOT = 20  # speed; the committed attempt uses 2000
    original = s144.update_ledger
    s144.update_ledger = lambda summary, ref: original(summary, ref, ledger_path=ledger)
    argv = sys.argv
    sys.argv = ["s144", "--out-root", str(out), "--attempt-id", "t1", "--update-ledger", "--journal-ref", "J-test"]
    try:
        assert s144.main() == 0
    finally:
        sys.argv = argv
        s144.update_ledger = original
    result = json.loads((out / "t1" / "summary.json").read_text(encoding="utf-8"))
    return out, ledger, result


def test_clusters_reproduce_the_audit_counts(committed_run):
    _, _, result = committed_run
    exposure = result["summary"]["exposure"]
    assert exposure["n_family_pairs"] == 147
    assert exposure["n_families_in_unresolved_review"] == 110
    assert exposure["n_clusters_with_two_or_more_families"] == 34
    assert exposure["n_singleton_families"] == 45
    assert exposure["share_of_all_155_families_in_a_cluster"] == pytest.approx(110 / 155)
    assert exposure["cohort_exposed_under_leave_one_family_out"] == 95
    assert exposure["cohort_size"] == 135


def test_the_five_exclusions_are_outcome_dependent_in_the_committed_data(committed_run):
    _, _, result = committed_run
    five = result["summary"]["excluded_five"]
    assert five["exclusion_depends_on_the_outcome_label"] is True
    assert len(five["excluded"]) == 5 and len(five["kept_despite_parse_failure"]) == 6


def test_cluster_held_out_comparison_covers_both_cohorts_and_labels_the_monitor_not_evaluated(committed_run):
    _, _, result = committed_run
    summary = result["summary"]
    assert set(summary["cv_comparison_135_cohort"]["predictors"]) >= {
        "metadata_law_cue_domain", "tfidf_prompt_text", "prompt_statistics", "fitted_entropy_features",
        "combined_non_activation"}
    assert summary["cv_comparison_135_cohort"]["n_families"] == 135
    assert summary["cv_comparison_140_inclusion_agnostic"]["n_families"] == 140
    assert summary["hidden_state_monitor_cluster_held_out"].startswith("NOT_EVALUATED")
    split = summary["stored_and_refit_loo_predictions_by_cluster_exposure"]
    monitor = split["hidden_state_monitor_layer18_stored_LOO"]
    assert monitor["exposed_to_cluster_mate_in_training"]["n"] == 95
    assert monitor["singleton_no_cluster_mate"]["n"] == 40
    assert monitor["all"]["auroc"] == pytest.approx(0.7596, abs=5e-4)


def test_ledger_update_resolves_the_71_percent_component(committed_run):
    _, ledger, _ = committed_run
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    row = next(r for r in rows if r["claim_id"] == "P1L-14")
    component = next(c for c in row["components"] if c["name"] == "family_held_out_share_cluster_with_training")
    assert component["outcome"] == "different_but_explained"
    assert "110/155" in component["recomputed"] and "95/135" in component["recomputed"]
    assert row["verification_label"] == "different_but_explained"
    assert row["paper_eligibility"] is False


def test_main_refuses_to_reuse_a_non_empty_attempt_directory(tmp_path, monkeypatch):
    attempt = tmp_path / "attempt_x"
    attempt.mkdir()
    (attempt / "keep.txt").write_text("existing evidence", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["s144", "--out-root", str(tmp_path), "--attempt-id", "attempt_x"])
    assert s144.main() == 2
    assert (attempt / "keep.txt").read_text(encoding="utf-8") == "existing evidence"
