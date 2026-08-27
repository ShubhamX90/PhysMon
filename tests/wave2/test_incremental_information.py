"""Tests for the Wave 2 combined baseline and incremental-information harness.

The decisive §8.4 comparison is easy to get wrong in ways that flatter the
monitor. These tests pin the properties that keep it honest: the baseline
contains no activation-derived or label-leaking feature, and differences are
tested with a genuinely paired bootstrap.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.probing.metrics import paired_bootstrap_difference  # noqa: E402

SUMMARY = REPO_ROOT / "results/wave2/incremental_information/incremental_information_summary.json"
BASELINE = REPO_ROOT / "results/wave2/combined_baseline/combined_baseline_summary.json"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


combined = _load("run_combined_baseline", "scripts/run_combined_baseline.py")


class TestPairedBootstrap:
    def test_identical_models_have_zero_difference(self):
        rng = np.random.default_rng(0)
        labels = rng.integers(0, 2, 80)
        scores = rng.random(80)
        result = paired_bootstrap_difference(labels, scores, scores, n_resamples=300)
        assert result["observed_difference"] == pytest.approx(0.0)
        assert result["ci95_low"] == pytest.approx(0.0)
        assert result["ci95_high"] == pytest.approx(0.0)

    def test_pairing_uses_the_same_resample_for_both_models(self):
        """A paired interval on identical models is exactly zero.

        An unpaired implementation would resample the two models independently
        and produce a non-degenerate interval here.
        """

        rng = np.random.default_rng(3)
        labels = rng.integers(0, 2, 60)
        scores = rng.random(60)
        result = paired_bootstrap_difference(labels, scores, scores, n_resamples=500)
        assert result["ci95_high"] - result["ci95_low"] == pytest.approx(0.0)

    def test_clearly_better_model_yields_an_interval_excluding_zero(self):
        rng = np.random.default_rng(1)
        labels = np.array([0] * 60 + [1] * 60)
        strong = np.clip(
            np.concatenate([rng.normal(0.2, 0.1, 60), rng.normal(0.8, 0.1, 60)]), 0.0, 1.0
        )
        weak = rng.random(120)
        result = paired_bootstrap_difference(labels, strong, weak, n_resamples=800)
        assert result["observed_difference"] > 0
        assert result["ci95_low"] > 0

    def test_is_deterministic_under_the_fixed_seed(self):
        rng = np.random.default_rng(2)
        labels = rng.integers(0, 2, 50)
        a, b = rng.random(50), rng.random(50)
        assert paired_bootstrap_difference(labels, a, b, n_resamples=200) == \
            paired_bootstrap_difference(labels, a, b, n_resamples=200)

    def test_rejects_unequal_length_inputs(self):
        with pytest.raises(ValueError):
            paired_bootstrap_difference(np.array([0, 1]), np.array([0.1, 0.9]), np.array([0.5]))

    def test_rejects_an_unknown_metric(self):
        with pytest.raises(ValueError):
            paired_bootstrap_difference(
                np.array([0, 1]), np.array([0.1, 0.9]), np.array([0.2, 0.8]), metric="nope"
            )


class TestBaselineComposition:
    def test_activation_derived_correctness_probe_is_excluded(self):
        """Its artifact carries layer_index: it is a probe over hidden states."""

        excluded = combined.ACTIVATION_DERIVED_EXCLUSIONS
        assert any("correctness_probe" in path for path in excluded)

    def test_raw_sources_contain_no_fitted_model_output(self):
        """Stacking other baselines' fitted predictions leaks labels across folds."""

        raw_fields = {field for _, field, _ in combined.NON_ACTIVATION_SOURCES}
        assert "prediction" not in raw_fields
        assert "prediction_margin" not in raw_fields
        assert "prediction_directional" not in raw_fields

    def test_fitted_outputs_are_available_only_behind_the_flag(self):
        fitted = {name for _, _, name in combined.FITTED_BASELINE_OUTPUTS}
        assert {"entropy_model", "blackbox_directional", "blackbox_margin"} == fitted


@pytest.mark.skipif(not BASELINE.exists(), reason="baseline not generated")
class TestGeneratedBaseline:
    @staticmethod
    def _s():
        return json.loads(BASELINE.read_text(encoding="utf-8"))

    def test_default_run_declares_no_leakage(self):
        summary = self._s()
        assert summary["includes_fitted_baseline_outputs"] is False
        assert summary["leakage_warning"].startswith("none")

    def test_cv_is_nested_and_family_level(self):
        cv = self._s()["cv"]
        assert cv["scheme"] == "nested_stratified_family_level"
        assert cv["resampling_unit"] == "canonical_family"
        assert len(cv["selected_C_per_outer_fold"]) == cv["outer_folds"]

    def test_run_is_exploratory_and_not_paper_eligible(self):
        summary = self._s()
        assert summary["experiment_class"] == "exploratory_unfrozen"
        assert summary["paper_eligibility"] is False


@pytest.mark.skipif(not SUMMARY.exists(), reason="incremental information not generated")
class TestGeneratedComparison:
    @staticmethod
    def _s():
        return json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_all_three_models_are_reported(self):
        metrics = self._s()["model_metrics"]
        assert {"combined_non_activation", "hidden_state_monitor", "combined_plus_hidden_state"} <= set(metrics)

    def test_every_difference_is_paired(self):
        assert self._s()["bootstrap"]["paired"] is True

    def test_verdict_matches_the_headline_interval(self):
        summary = self._s()
        headline = summary["paired_differences"]["monitor_minus_combined"]["auroc"]
        if headline["excludes_zero"]:
            assert "NOT demonstrated" not in summary["verdict"]
        else:
            assert "NOT demonstrated" in summary["verdict"]

    def test_calibration_is_reported_not_only_ranking(self):
        """§8.4 asks about calibration as well as AUROC."""

        for metrics in self._s()["model_metrics"].values():
            assert "brier" in metrics and "ece" in metrics

    def test_risk_coverage_curves_are_present(self):
        curves = self._s()["risk_coverage"]
        for curve in curves.values():
            assert len(curve) > 1
            assert curve[-1]["coverage"] == pytest.approx(1.0, abs=0.01)

    def test_result_is_not_marked_confirmatory(self):
        summary = self._s()
        assert summary["paper_eligibility"] is False
        assert summary["experiment_class"] == "exploratory_unfrozen"
