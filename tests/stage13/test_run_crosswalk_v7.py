"""Tests for the v7 run-level registry crosswalk.

v6 built its denominator by slugifying results/** filenames. These tests pin the
replacement: the denominator comes from jobs that actually ran, and a mapping is
only called a match when the evidence identifies the experiment.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "stage13" / "build_run_crosswalk_v7.py"
COVERAGE_PATH = REPO_ROOT / "results" / "stage13" / "wave0" / "registry_coverage_v7.json"
CROSSWALK_PATH = REPO_ROOT / "docs" / "registry" / "historical_run_crosswalk_v7.csv"


def _load():
    spec = importlib.util.spec_from_file_location("build_run_crosswalk_v7", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


crosswalk = _load()


def _registry(**overrides):
    entry = {
        "experiment_id": "stage6_qwen_behavioural_full_rerun",
        "stage": "Stage6",
        "model_id": "qwen2p5_7b_instruct",
        "experiment_class": "behavioural",
        "family_manifest": "data/manifests/physmon_canonical_155.jsonl",
    }
    entry.update(overrides)
    return entry


def _match(job_name, registry):
    cache = {id(e): crosswalk.stage_of(str(e.get("stage", "")) or str(e.get("experiment_id", ""))) for e in registry}
    return crosswalk.match_job(
        crosswalk.expand(crosswalk.tokens(job_name)),
        registry,
        crosswalk.stage_of(job_name),
        cache,
        crosswalk.kind_of(job_name),
    )


def test_stage_of_extracts_both_naming_conventions():
    assert crosswalk.stage_of("physmon_stage6_extract_qwen") == "6"
    assert crosswalk.stage_of("physmon_s12_donren_a1") == "12"
    assert crosswalk.stage_of("Stage6") == "6"
    assert crosswalk.stage_of("no_stage_here") is None


def test_disagreeing_stage_is_disqualifying():
    """A stage-4 job must never be matched to a stage-6 experiment."""

    _, status, _ = _match("physmon_stage4_qwen", [_registry()])
    assert status == "unmatched"


def test_model_name_overlap_alone_is_not_identification():
    """Sharing only the model name matches almost everything and must not count."""

    registry = [_registry(experiment_id="stage6_qwen_something_else")]
    _, status, _ = _match("qwen", registry)
    assert status == "unmatched"


def test_agreeing_stage_and_kind_produces_a_match():
    _, status, score = _match("stage6_d1_qwen", [_registry()])
    assert status == "matched"
    assert score > 0


def test_contradicted_experiment_kind_downgrades_to_partial():
    """An extraction job and a behavioural experiment are different runs."""

    _, status, _ = _match("physmon_stage6_extract_qwen_t1", [_registry()])
    assert status == "partially_matched"


def test_infrastructure_jobs_are_identified():
    assert crosswalk.is_infrastructure("physmon_smoke_a100")
    assert crosswalk.is_infrastructure("physmon_part2_validate")
    assert not crosswalk.is_infrastructure("physmon_s12_donren_a1")


def test_stopwords_prevent_hardware_tags_from_matching():
    assert "a100" not in crosswalk.tokens("physmon_s12_donren_a1")
    assert "physmon" not in crosswalk.tokens("physmon_s12_donren_a1")


@pytest.mark.skipif(not COVERAGE_PATH.exists(), reason="coverage artifact not generated yet")
class TestGeneratedCrosswalk:
    @staticmethod
    def _coverage():
        return json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))

    def test_denominator_comes_from_real_slurm_evidence(self):
        coverage = self._coverage()
        assert coverage["denominator_source"] == "sharanga_slurm_logs_joined_to_sacct"
        assert coverage["supersedes"].endswith("registry_coverage_v6.json")

    def test_infrastructure_jobs_are_counted_not_dropped(self):
        coverage = self._coverage()
        assert coverage["n_infrastructure_jobs"] > 0
        assert (
            coverage["n_expected_science_runs"] + coverage["n_infrastructure_jobs"]
            == coverage["n_jobs_in_inventory"]
        )

    def test_all_science_runs_are_accounted_for(self):
        coverage = self._coverage()
        assert (
            coverage["matched"] + coverage["partial"] + coverage["unmatched"]
            == coverage["n_expected_science_runs"]
        )

    def test_strict_coverage_is_reported_alongside_lenient(self):
        coverage = self._coverage()
        assert coverage["strict_coverage_fraction"] <= coverage["coverage_fraction"]

    @pytest.mark.skipif(not CROSSWALK_PATH.exists(), reason="crosswalk not generated")
    def test_no_matched_row_has_a_contradicting_stage(self):
        import csv

        with CROSSWALK_PATH.open(encoding="utf-8", newline="") as handle:
            rows = [r for r in csv.DictReader(handle) if r["mapping_status"] == "matched"]
        for row in rows:
            job_stage = crosswalk.stage_of(row["job_name"])
            entry_stage = crosswalk.stage_of(row["registry_experiment_id"])
            if job_stage and entry_stage:
                assert job_stage == entry_stage, row

    @pytest.mark.skipif(not CROSSWALK_PATH.exists(), reason="crosswalk not generated")
    def test_unmatched_rows_never_claim_a_registry_experiment(self):
        import csv

        with CROSSWALK_PATH.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["mapping_status"] == "unmatched":
                    assert row["registry_experiment_id"] == ""
