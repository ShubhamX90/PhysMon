"""Agreement tests: independent numpy metrics versus the project's scikit-learn-based metrics.

The independent implementations in `physmon.governance.recompute` are only useful for the X01
reproduction if they agree with the original code on arbitrary inputs, including tied scores.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance import recompute as rc  # noqa: E402
from physmon.probing import metrics as project  # noqa: E402


def _cases():
    generator = np.random.default_rng(20261016)
    cases = []
    for size in (12, 40, 135):
        for tie_levels in (None, 5):
            labels = generator.integers(0, 2, size)
            labels[0], labels[1] = 0, 1
            scores = generator.random(size)
            if tie_levels:
                scores = np.round(scores * tie_levels) / tie_levels
            cases.append((labels, scores))
    return cases


@pytest.mark.parametrize("labels,scores", _cases())
def test_metrics_match_project_implementations(labels, scores):
    assert rc.auroc(labels, scores) == pytest.approx(project.compute_auroc(labels, scores), abs=1e-12)
    assert rc.average_precision(labels, scores) == pytest.approx(
        project.compute_auprc(labels, scores), abs=1e-12
    )
    assert rc.brier(labels, scores) == pytest.approx(project.compute_brier(labels, scores), abs=1e-12)
    assert rc.ece(labels, scores) == pytest.approx(project.compute_ece(labels, scores), abs=1e-12)
    for target in (0.05, 0.1, 0.2):
        assert rc.fnr_at_fpr(labels, scores, target) == pytest.approx(
            project.compute_fnr_at_fpr(labels, scores, target), abs=1e-12
        )


def test_paired_bootstrap_reproduces_the_project_interval_exactly():
    generator = np.random.default_rng(7)
    labels = generator.integers(0, 2, 60)
    labels[:2] = (0, 1)
    scores_a = generator.random(60)
    scores_b = generator.random(60)
    mine = rc.paired_bootstrap_auroc_difference(labels, scores_a, scores_b, n_resamples=300)
    theirs = project.paired_bootstrap_difference(labels, scores_a, scores_b, "auroc", n_resamples=300)
    assert mine["observed_difference"] == pytest.approx(theirs["observed_difference"], abs=1e-12)
    assert mine["ci95_low"] == pytest.approx(theirs["ci95_low"], abs=1e-12)
    assert mine["ci95_high"] == pytest.approx(theirs["ci95_high"], abs=1e-12)
    assert mine["n_usable_resamples"] == theirs["n_usable_resamples"]


def test_single_class_is_an_error_not_a_zero():
    with pytest.raises(ValueError):
        rc.auroc([1, 1, 1], [0.1, 0.2, 0.3])
    with pytest.raises(ValueError):
        rc.fnr_at_fpr([0, 0], [0.1, 0.2], 0.1)


def test_legacy_slp_forms_on_the_plan_example():
    values = {0: -45.53125, 1: -55.5625, 2: -45.0, 3: -46.46875}
    assert rc.legacy_slp_repo_clamped(values, base=0) == pytest.approx(10.03125)
    assert rc.legacy_slp_plan_signed(values, base=0) == pytest.approx(10.03125)
    # Base 1: the plan's signed form is negative; the repo's form is clamped at 0.
    assert rc.legacy_slp_plan_signed(values, base=1) == pytest.approx(-9.09375)
    assert rc.legacy_slp_repo_clamped(values, base=1) == 0.0


def test_matches_reported_uses_the_reported_precision():
    assert rc.matches_reported(0.032501, "+0.033")
    assert rc.matches_reported(-0.0736, "-0.074")
    assert rc.matches_reported(1.86972, "1.870")
    assert not rc.matches_reported(0.7048, "0.7596")


def test_blank_is_none_not_zero():
    assert rc.as_float_or_none("") is None
    assert rc.as_float_or_none(None) is None
    assert rc.as_float_or_none("nan") is None
    assert rc.as_float_or_none("0") == 0.0
