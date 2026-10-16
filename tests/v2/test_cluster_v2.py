"""Tests for the Stage 14.4 structure-cluster helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance import cluster as cl  # noqa: E402


def test_components_are_transitive_and_singletons_are_kept():
    cluster_of = cl.union_find_components(
        ["a", "b", "c", "d", "e", "f"], [("a", "b"), ("b", "c"), ("e", "d")]
    )
    assert cluster_of["a"] == cluster_of["b"] == cluster_of["c"] == "a"
    assert cluster_of["d"] == cluster_of["e"] == "d"
    assert cluster_of["f"] == "f"
    assert len(set(cluster_of.values())) == 3


def test_components_add_nodes_that_only_appear_in_pairs():
    cluster_of = cl.union_find_components([], [("x", "y")])
    assert cluster_of == {"x": "x", "y": "x"}


def test_labelling_is_deterministic_regardless_of_pair_order():
    pairs = [("a", "b"), ("c", "b"), ("d", "c")]
    first = cl.union_find_components("abcde", pairs)
    second = cl.union_find_components("abcde", list(reversed(pairs)))
    assert first == second


def test_loo_exposure_needs_another_cohort_member():
    cluster_of = cl.union_find_components("abcdef", [("a", "b"), ("b", "c"), ("d", "e")])
    cohort = ["a", "b", "d", "f"]  # c and e are outside the cohort
    exposure = cl.loo_exposure(cohort, cluster_of)
    assert exposure == {"a": True, "b": True, "d": False, "f": False}
    assert cl.loo_exposure(["zz"], cluster_of) == {"zz": False}  # unknown family is a singleton


def test_leave_one_group_out_partitions_every_row_once():
    groups = ["g1", "g2", "g1", "g3", "g2"]
    seen = []
    for train, test in cl.leave_one_group_out(groups):
        assert set(train) | set(test) == set(range(5)) and not set(train) & set(test)
        assert len({groups[i] for i in test}) == 1
        seen.extend(test.tolist())
    assert sorted(seen) == [0, 1, 2, 3, 4]
    assert [len(t) for _, t in cl.leave_one_out(4)] == [1, 1, 1, 1]


def test_cluster_bootstrap_is_deterministic_and_skips_undefined_resamples():
    labels = np.array([0, 1, 0, 1, 0, 1, 1, 0])
    scores = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.6, 0.4])
    groups = ["A", "A", "B", "B", "C", "C", "D", "D"]

    def stat(index):
        return cl.auroc_or_none(labels[index], scores[index])

    first = cl.cluster_bootstrap(groups, stat, n_resamples=200, seed=3)
    second = cl.cluster_bootstrap(groups, stat, n_resamples=200, seed=3)
    assert first == second
    assert first["n_usable_resamples"] <= 200
    assert first["ci95_low"] <= first["ci95_high"]


def test_auroc_or_none_is_none_for_one_class_not_a_half():
    assert cl.auroc_or_none(np.array([1, 1, 1]), np.array([0.1, 0.2, 0.3])) is None
    assert cl.auroc_or_none(np.array([0, 1]), np.array([0.2, 0.9])) == pytest.approx(1.0)
