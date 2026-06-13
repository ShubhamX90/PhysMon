"""Unit tests for Stage 5 probe metrics."""

from __future__ import annotations

import math

import numpy as np

from physmon.probing.metrics import (
    compute_auprc,
    compute_auroc,
    compute_brier,
    compute_ece,
    compute_fnr_at_fpr,
)


Y_TRUE = np.array([0, 0, 1, 1])
Y_SCORE = np.array([0.05, 0.35, 0.8, 0.95])


def test_compute_auroc_returns_expected_value() -> None:
    """AUROC should be perfect for strictly ordered positive scores."""

    assert math.isclose(compute_auroc(Y_TRUE, Y_SCORE), 1.0)


def test_compute_auprc_returns_expected_value() -> None:
    """AUPRC should be perfect for strictly ordered positive scores."""

    assert math.isclose(compute_auprc(Y_TRUE, Y_SCORE), 1.0)


def test_compute_brier_returns_expected_value() -> None:
    """Brier score should match the squared-error mean for binary probabilities."""

    expected = ((0.05**2) + (0.35**2) + ((1 - 0.8) ** 2) + ((1 - 0.95) ** 2)) / 4
    assert math.isclose(compute_brier(Y_TRUE, Y_SCORE), expected)


def test_compute_ece_returns_nonnegative_value() -> None:
    """ECE should be finite and nonnegative for valid probabilities."""

    ece = compute_ece(Y_TRUE, Y_SCORE, n_bins=4)
    assert math.isfinite(ece)
    assert ece >= 0.0


def test_compute_fnr_at_fpr_returns_zero_for_separable_scores() -> None:
    """FNR@FPR should be zero when a perfect threshold exists below the target FPR."""

    assert math.isclose(compute_fnr_at_fpr(Y_TRUE, Y_SCORE, target_fpr=0.0), 0.0)
