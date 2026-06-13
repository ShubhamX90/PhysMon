"""Monitoring metrics for Stage 5 probe evaluation.

Reference:
    `physmon_proposal.pdf` §9.4 and the Stage 5 preparation brief.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve


DEFAULT_ECE_BINS = 10


def compute_auroc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Compute AUROC for binary sensitivity labels.

    Args:
        y_true: Binary labels of shape `(n_samples,)`.
        y_score: Predicted probabilities or scores of shape `(n_samples,)`.

    Returns:
        AUROC as a float.
    """

    labels, scores = _validate_binary_inputs(y_true, y_score)
    return float(roc_auc_score(labels, scores))


def compute_auprc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Compute AUPRC for binary sensitivity labels.

    Args:
        y_true: Binary labels of shape `(n_samples,)`.
        y_score: Predicted probabilities or scores of shape `(n_samples,)`.

    Returns:
        AUPRC as a float.
    """

    labels, scores = _validate_binary_inputs(y_true, y_score)
    return float(average_precision_score(labels, scores))


def compute_brier(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Compute the Brier score for probabilistic binary predictions.

    Args:
        y_true: Binary labels of shape `(n_samples,)`.
        y_score: Predicted probabilities of shape `(n_samples,)`.

    Returns:
        Brier score as a float.
    """

    labels, scores = _validate_binary_inputs(y_true, y_score)
    return float(brier_score_loss(labels, scores))


def compute_ece(y_true: np.ndarray, y_score: np.ndarray, n_bins: int = DEFAULT_ECE_BINS) -> float:
    """Compute expected calibration error for binary predictions.

    Args:
        y_true: Binary labels of shape `(n_samples,)`.
        y_score: Predicted probabilities of shape `(n_samples,)`.
        n_bins: Number of equal-width confidence bins.

    Returns:
        Expected calibration error as a float.
    """

    if n_bins <= 0:
        raise ValueError(f"n_bins must be positive, got {n_bins}.")
    labels, scores = _validate_binary_inputs(y_true, y_score)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = float(labels.size)
    ece = 0.0
    for bin_index in range(n_bins):
        left_edge = bin_edges[bin_index]
        right_edge = bin_edges[bin_index + 1]
        if bin_index == n_bins - 1:
            in_bin = (scores >= left_edge) & (scores <= right_edge)
        else:
            in_bin = (scores >= left_edge) & (scores < right_edge)
        if not np.any(in_bin):
            continue
        bin_labels = labels[in_bin]
        bin_scores = scores[in_bin]
        ece += abs(float(bin_labels.mean()) - float(bin_scores.mean())) * (bin_labels.size / total)
    return float(ece)


def compute_fnr_at_fpr(y_true: np.ndarray, y_score: np.ndarray, target_fpr: float) -> float:
    """Compute false-negative rate at the highest threshold with FPR <= target.

    Args:
        y_true: Binary labels of shape `(n_samples,)`.
        y_score: Predicted probabilities or scores of shape `(n_samples,)`.
        target_fpr: Maximum allowed false-positive rate in `[0, 1]`.

    Returns:
        False-negative rate at the selected operating point.
    """

    if target_fpr < 0.0 or target_fpr > 1.0:
        raise ValueError(f"target_fpr must lie in [0, 1], got {target_fpr}.")
    labels, scores = _validate_binary_inputs(y_true, y_score)
    fpr_values, tpr_values, _ = roc_curve(labels, scores)
    eligible_indices = np.where(fpr_values <= target_fpr)[0]
    if eligible_indices.size == 0:
        return 1.0
    best_tpr = float(np.max(tpr_values[eligible_indices]))
    return float(1.0 - best_tpr)


def _validate_binary_inputs(
    y_true: np.ndarray,
    y_score: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate metric inputs and return contiguous float/int arrays."""

    labels = np.asarray(y_true, dtype=int).reshape(-1)
    scores = np.asarray(y_score, dtype=float).reshape(-1)
    if labels.shape != scores.shape:
        raise ValueError(
            f"y_true and y_score must have matching shapes, got {labels.shape} and {scores.shape}."
        )
    unique_labels = set(labels.tolist())
    if not unique_labels.issubset({0, 1}):
        raise ValueError(f"y_true must contain only binary labels 0/1, got {sorted(unique_labels)}.")
    if len(unique_labels) < 2:
        raise ValueError("Binary metrics require both positive and negative labels.")
    if np.any(scores < 0.0) or np.any(scores > 1.0):
        raise ValueError("y_score must contain probabilities in [0, 1].")
    return labels, scores
