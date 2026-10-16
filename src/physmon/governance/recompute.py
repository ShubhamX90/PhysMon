"""Independent recomputation helpers for Stage 14 reproduction and audit work.

These functions are written from the metric definitions with numpy only. They deliberately do not
call `physmon.probing.metrics` (which wraps scikit-learn), so that agreement between the two is
evidence that the original metric code does what its documentation says (v2 card X01: "independent
implementation, no circular calculations from summary tables", p.39).

The bootstrap reproduces the project's resampling scheme exactly (same generator, same draw order,
same one-class skip rule) so that a stored interval can be reproduced to the printed precision.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np


def _as_arrays(y_true: Iterable[int], y_score: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    labels = np.asarray(list(y_true), dtype=int).reshape(-1)
    scores = np.asarray(list(y_score), dtype=float).reshape(-1)
    if labels.shape != scores.shape:
        raise ValueError(f"shape mismatch: {labels.shape} vs {scores.shape}")
    if not set(labels.tolist()) <= {0, 1}:
        raise ValueError("labels must be 0/1")
    return labels, scores


def _average_ranks(values: np.ndarray) -> np.ndarray:
    """Average ranks (1-based) with ties sharing the mean rank."""

    unique, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    cumulative = np.cumsum(counts)
    mean_rank_per_value = cumulative - (counts - 1) / 2.0
    del unique
    return mean_rank_per_value[inverse]


def auroc(y_true: Iterable[int], y_score: Iterable[float]) -> float:
    """Area under the ROC curve via the tie-aware Mann-Whitney statistic."""

    labels, scores = _as_arrays(y_true, y_score)
    n_pos = int(labels.sum())
    n_neg = int(labels.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        raise ValueError("AUROC needs both classes")
    ranks = _average_ranks(scores)
    return float((ranks[labels == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def average_precision(y_true: Iterable[int], y_score: Iterable[float]) -> float:
    """Average precision: sum over distinct thresholds of (R_n - R_{n-1}) * P_n."""

    labels, scores = _as_arrays(y_true, y_score)
    n_pos = int(labels.sum())
    if n_pos == 0 or n_pos == labels.size:
        raise ValueError("average precision needs both classes")
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    true_positives = np.cumsum(sorted_labels)
    predicted_positives = np.arange(1, labels.size + 1)
    boundary = np.r_[np.diff(sorted_scores) != 0, True]
    tp = true_positives[boundary]
    precision = tp / predicted_positives[boundary]
    recall = tp / n_pos
    previous_recall = np.r_[0.0, recall[:-1]]
    return float(np.sum((recall - previous_recall) * precision))


def brier(y_true: Iterable[int], y_score: Iterable[float]) -> float:
    labels, scores = _as_arrays(y_true, y_score)
    return float(np.mean((scores - labels) ** 2))


def ece(y_true: Iterable[int], y_score: Iterable[float], n_bins: int = 10) -> float:
    """Expected calibration error with equal-width bins; the last bin includes 1.0."""

    labels, scores = _as_arrays(y_true, y_score)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = float(labels.size)
    error = 0.0
    for index in range(n_bins):
        if index == n_bins - 1:
            in_bin = (scores >= edges[index]) & (scores <= edges[index + 1])
        else:
            in_bin = (scores >= edges[index]) & (scores < edges[index + 1])
        if in_bin.any():
            error += abs(labels[in_bin].mean() - scores[in_bin].mean()) * (in_bin.sum() / total)
    return float(error)


def fnr_at_fpr(y_true: Iterable[int], y_score: Iterable[float], target_fpr: float) -> float:
    """False-negative rate at the best operating point whose FPR does not exceed the target."""

    labels, scores = _as_arrays(y_true, y_score)
    n_pos = int(labels.sum())
    n_neg = int(labels.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        raise ValueError("FNR@FPR needs both classes")
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    boundary = np.r_[np.diff(sorted_scores) != 0, True]
    tpr = np.r_[0.0, (np.cumsum(sorted_labels) / n_pos)[boundary]]
    fpr = np.r_[0.0, (np.cumsum(1 - sorted_labels) / n_neg)[boundary]]
    return float(1.0 - tpr[fpr <= target_fpr].max())


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.size != b.size or a.size < 2:
        raise ValueError("Pearson needs two equal-length samples of at least 2 values")
    a = a - a.mean()
    b = b - b.mean()
    return float((a @ b) / np.sqrt((a @ a) * (b @ b)))


def paired_bootstrap_auroc_difference(
    y_true: Iterable[int],
    y_score_a: Iterable[float],
    y_score_b: Iterable[float],
    n_resamples: int = 10000,
    seed: int = 42,
) -> dict[str, float | int]:
    """Paired family-level bootstrap for AUROC(a) - AUROC(b), matching the project's scheme."""

    labels, scores_a = _as_arrays(y_true, y_score_a)
    _, scores_b = _as_arrays(y_true, y_score_b)
    observed = auroc(labels, scores_a) - auroc(labels, scores_b)
    generator = np.random.default_rng(seed)
    n_units = labels.size
    differences: list[float] = []
    for _ in range(n_resamples):
        index = generator.integers(0, n_units, n_units)
        sampled = labels[index]
        if len(np.unique(sampled)) < 2:
            continue
        differences.append(auroc(sampled, scores_a[index]) - auroc(sampled, scores_b[index]))
    array = np.asarray(differences, dtype=float)
    return {
        "observed_difference": float(observed),
        "ci95_low": float(np.percentile(array, 2.5)),
        "ci95_high": float(np.percentile(array, 97.5)),
        "proportion_favouring_a": float((array > 0).mean()),
        "n_usable_resamples": int(array.size),
    }


def legacy_slp_repo_clamped(logprobs_by_variant: Mapping[int, float], base: int = 0) -> float:
    """Legacy `S_lp` as implemented in the repo: max over ALL variants of (L_base - L_j).

    Includes `j = base`, so the value is never negative (see `physmon.formal.sensitivity`).
    """

    base_value = logprobs_by_variant[base]
    return max(base_value - value for value in logprobs_by_variant.values())


def legacy_slp_plan_signed(logprobs_by_variant: Mapping[int, float], base: int = 0) -> float:
    """Legacy `S_lp` as written in v2 B1.3 / P1.1: max over `j != base` of (L_base - L_j).

    Can be negative. This is the form behind the plan's "+10.031 at base 0, -9.094 at base 1".
    """

    base_value = logprobs_by_variant[base]
    return max(base_value - value for key, value in logprobs_by_variant.items() if key != base)


def matches_reported(recomputed: float, reported: str | float) -> bool:
    """True if `recomputed` rounds to the reported value at the reported number of decimals."""

    text = str(reported).strip().lstrip("+")
    decimals = len(text.split(".")[1]) if "." in text else 0
    return bool(round(float(recomputed), decimals) == round(float(text), decimals))


def as_float_or_none(value: Any) -> float | None:
    """Parse a CSV or JSON value; blank, missing or non-numeric values become None (not 0)."""

    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(parsed) else parsed
