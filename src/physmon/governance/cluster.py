"""Structure-cluster helpers for Stage 14.4 (v2 P3.5-P3.6, p.20; card X05, p.40).

Pure functions, numpy only. A cluster is a connected component of the graph whose edges are the unresolved
cross-family structural relations, so transitive siblings never straddle a split (P3.5: "group by connected
components of the relevant relation").
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator, Mapping, Sequence

import numpy as np

from physmon.governance import recompute as rc


def union_find_components(
    nodes: Iterable[Hashable], pairs: Iterable[tuple[Hashable, Hashable]]
) -> dict[Hashable, str]:
    """Connected components. Every node gets a cluster id; isolated nodes are singletons.

    The id of a cluster is its smallest member (as a string), so the labelling is deterministic.
    """

    parent: dict[Hashable, Hashable] = {node: node for node in nodes}

    def find(item: Hashable) -> Hashable:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for left, right in pairs:
        for item in (left, right):
            parent.setdefault(item, item)
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_left] = root_right
    members: dict[Hashable, list[str]] = {}
    for node in parent:
        members.setdefault(find(node), []).append(str(node))
    label_of_root = {root: min(items) for root, items in members.items()}
    return {node: label_of_root[find(node)] for node in parent}


def cluster_sizes(cluster_of: Mapping[Hashable, str], cohort: Iterable[Hashable] | None = None) -> dict[str, int]:
    """Cluster id -> number of members (restricted to `cohort` if given)."""

    selected = list(cluster_of) if cohort is None else [n for n in cohort if n in cluster_of]
    sizes: dict[str, int] = {}
    for node in selected:
        sizes[cluster_of[node]] = sizes.get(cluster_of[node], 0) + 1
    return sizes


def loo_exposure(cohort: Sequence[Hashable], cluster_of: Mapping[Hashable, str]) -> dict[Hashable, bool]:
    """Under leave-one-family-out, a held-out family is exposed iff another cohort member shares its cluster.

    A family absent from `cluster_of` is its own singleton and is therefore not exposed.
    """

    sizes = cluster_sizes(cluster_of, cohort)
    return {family: bool(family in cluster_of and sizes.get(cluster_of[family], 0) >= 2) for family in cohort}


def leave_one_group_out(groups: Sequence[str]) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield (train_index, test_index) for each distinct group, in sorted group order."""

    array = np.asarray(list(groups))
    for group in sorted(set(array.tolist())):
        test = np.where(array == group)[0]
        train = np.where(array != group)[0]
        yield train, test


def leave_one_out(n: int) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    for index in range(n):
        yield np.delete(np.arange(n), index), np.array([index])


def cluster_bootstrap(
    groups: Sequence[str],
    statistic,
    n_resamples: int = 2000,
    seed: int = 42,
) -> dict[str, float | int]:
    """Percentile interval for `statistic(index_array)` resampling whole clusters with replacement.

    `statistic` receives the concatenated row indices of the resampled clusters and may return None when it is
    undefined (for example one class); such resamples are skipped and counted.
    """

    array = np.asarray(list(groups))
    labels = sorted(set(array.tolist()))
    members = {g: np.where(array == g)[0] for g in labels}
    generator = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(n_resamples):
        picks = generator.integers(0, len(labels), len(labels))
        index = np.concatenate([members[labels[p]] for p in picks])
        value = statistic(index)
        if value is not None:
            values.append(float(value))
    if not values:
        return {"ci95_low": float("nan"), "ci95_high": float("nan"), "n_usable_resamples": 0}
    arr = np.asarray(values)
    return {
        "ci95_low": float(np.percentile(arr, 2.5)),
        "ci95_high": float(np.percentile(arr, 97.5)),
        "n_usable_resamples": int(arr.size),
    }


def auroc_or_none(labels: np.ndarray, scores: np.ndarray) -> float | None:
    """AUROC, or None when only one class is present (never 0.5 by default)."""

    if len(set(labels.tolist())) < 2:
        return None
    return rc.auroc(labels, scores)
