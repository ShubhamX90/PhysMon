"""Review-record contract and agreement metrics for independent validation (Stage 14.5; v2 B4, p.9-10; P3.1-P3.2, p.20).

The v6 annotation schema collapsed a review into one verdict. v2 requires separate validity, clarity, difficulty and
naturalness judgments, explicit uncertainty marking, counterexamples, a blinding attestation, time spent (to size the
workload), and an admission category from B4.5. Agreement is reported as raw agreement, Cohen's kappa and Gwet's AC1
(kappa is misleading under severe imbalance, P3.2), with intervals that resample structure clusters, never single
renderings. Detection sensitivity and false-rejection are reported per planted defect type (B4.4).

Pure functions, numpy only. No reviewer identity is stored here: `reviewer_id` is a pseudonym.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from physmon.governance.v2_contract import ADMISSION_CATEGORIES

VALIDITY = ("valid", "invalid", "uncertain")
CLARITY = ("clear", "ambiguous", "unclear")
NATURALNESS = ("natural", "slightly_artificial", "artificial")
DIFFICULTY_SCALE = (1, 2, 3, 4, 5)
CONFIDENCE_SCALE = (1, 2, 3, 4, 5)

REVIEW_REQUIRED = (
    "reviewer_id", "item_id", "pass_number", "started_at", "completed_at", "minutes_spent",
    "blinding_attestation", "validity", "clarity", "difficulty", "naturalness", "confidence",
    "uncertain_fields", "defect_flags", "counterexamples", "notes",
)
PASS2_REQUIRED = ("equation_consistent", "units_consistent", "answer_correct", "precision_adequate",
                  "admission_category")


def validate_review(record: Mapping[str, Any]) -> list[str]:
    """Return errors for one review record (empty list if valid). A blank required field is an error."""

    errors: list[str] = []
    item = record.get("item_id", "<unknown item>")
    prefix = f"{item}/{record.get('reviewer_id', '<unknown reviewer>')}:"
    for name in REVIEW_REQUIRED:
        if name not in record or record[name] in (None, ""):
            if name in ("uncertain_fields", "defect_flags", "counterexamples", "notes") and name in record:
                continue  # an empty list or empty note is a valid statement
            errors.append(f"{prefix} missing required field '{name}'")
    if errors:
        return errors
    if record["pass_number"] not in (1, 2):
        errors.append(f"{prefix} pass_number must be 1 or 2")
    if record["blinding_attestation"] is not True:
        errors.append(f"{prefix} blinding_attestation must be true (no model outputs, labels, probe scores or "
                      "hypothesis were seen)")
    for name, allowed in (("validity", VALIDITY), ("clarity", CLARITY), ("naturalness", NATURALNESS),
                          ("difficulty", DIFFICULTY_SCALE), ("confidence", CONFIDENCE_SCALE)):
        if record[name] not in allowed:
            errors.append(f"{prefix} {name}={record[name]!r} is not one of {list(allowed)}")
    if not isinstance(record["minutes_spent"], (int, float)) or record["minutes_spent"] <= 0:
        errors.append(f"{prefix} minutes_spent must be a positive number")
    for name in ("uncertain_fields", "defect_flags", "counterexamples"):
        if not isinstance(record[name], list):
            errors.append(f"{prefix} {name} must be a list")
    if record["validity"] == "uncertain" and not record["uncertain_fields"]:
        errors.append(f"{prefix} validity 'uncertain' needs at least one entry in uncertain_fields")
    if record["validity"] == "invalid" and not record["defect_flags"]:
        errors.append(f"{prefix} validity 'invalid' needs at least one entry in defect_flags")
    if record["pass_number"] == 2:
        for name in PASS2_REQUIRED:
            if name not in record or record[name] in (None, ""):
                errors.append(f"{prefix} pass 2 needs '{name}'")
        if record.get("admission_category") not in ADMISSION_CATEGORIES:
            errors.append(f"{prefix} admission_category must be one of {list(ADMISSION_CATEGORIES)}")
    return errors


def raw_agreement(a: Sequence[Any], b: Sequence[Any]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty rating lists")
    return float(np.mean([x == y for x, y in zip(a, b, strict=True)]))


def cohens_kappa(a: Sequence[Any], b: Sequence[Any]) -> float | None:
    """Cohen's kappa; None (not 1.0) when chance agreement is 1, because kappa is undefined there."""

    pa = raw_agreement(a, b)
    categories = sorted(set(a) | set(b), key=str)
    n = len(a)
    pe = sum((sum(x == c for x in a) / n) * (sum(y == c for y in b) / n) for c in categories)
    if pe >= 1.0:
        return None
    return float((pa - pe) / (1.0 - pe))


def gwet_ac1(a: Sequence[Any], b: Sequence[Any], categories: Sequence[Any] | None = None) -> float | None:
    """Gwet's AC1 for two raters; well behaved under severe prevalence imbalance (v2 P3.2, p.20).

    Pass the full category list when a category can be unused, since chance agreement depends on K.
    """

    pa = raw_agreement(a, b)
    cats = list(categories) if categories is not None else sorted(set(a) | set(b), key=str)
    k = len(cats)
    if k < 2:
        return None
    n = len(a)
    pe = 0.0
    for c in cats:
        pi = (sum(x == c for x in a) + sum(y == c for y in b)) / (2.0 * n)
        pe += pi * (1.0 - pi)
    pe /= (k - 1)
    if pe >= 1.0:
        return None
    return float((pa - pe) / (1.0 - pe))


def structure_bootstrap(
    cluster_of_item: Sequence[str],
    statistic,
    n_resamples: int = 2000,
    seed: int = 42,
) -> dict[str, float | int]:
    """Percentile interval resampling whole structure clusters (not renderings or items).

    `statistic(index_array)` returns a float or None (skipped, counted as unusable).
    """

    array = np.asarray(list(cluster_of_item))
    labels = sorted(set(array.tolist()))
    members = {g: np.where(array == g)[0] for g in labels}
    generator = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(n_resamples):
        picks = generator.integers(0, len(labels), len(labels))
        value = statistic(np.concatenate([members[labels[p]] for p in picks]))
        if value is not None:
            values.append(float(value))
    if not values:
        return {"ci95_low": float("nan"), "ci95_high": float("nan"), "n_usable_resamples": 0}
    arr = np.asarray(values)
    return {"ci95_low": float(np.percentile(arr, 2.5)), "ci95_high": float(np.percentile(arr, 97.5)),
            "n_usable_resamples": int(arr.size)}


def pairwise_agreement_report(
    ratings_a: Mapping[str, Any],
    ratings_b: Mapping[str, Any],
    categories: Sequence[Any],
    cluster_of_item: Mapping[str, str] | None = None,
    n_resamples: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    """Raw agreement, kappa and AC1 for two reviewers over the items both rated, with cluster bootstrap CIs."""

    items = sorted(set(ratings_a) & set(ratings_b))
    if not items:
        raise ValueError("the two reviewers share no items")
    a = [ratings_a[i] for i in items]
    b = [ratings_b[i] for i in items]
    report: dict[str, Any] = {
        "n_items": len(items),
        "n_items_only_one_reviewer": len(set(ratings_a) ^ set(ratings_b)),
        "raw_agreement": raw_agreement(a, b),
        "cohens_kappa": cohens_kappa(a, b),
        "gwet_ac1": gwet_ac1(a, b, categories),
    }
    if cluster_of_item is not None:
        groups = [cluster_of_item.get(i, i) for i in items]

        def ac1(index):
            return gwet_ac1([a[i] for i in index], [b[i] for i in index], categories)

        report["gwet_ac1_cluster_bootstrap"] = structure_bootstrap(groups, ac1, n_resamples, seed)
    return report


def detection_by_defect(
    decisions: Iterable[Mapping[str, Any]],
    key: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Per planted-defect-type detection and false-rejection (v2 B4.4).

    `decisions` are review records. `key[item_id]` has `defect_type`, `expected_verdict` ('valid' or 'invalid') and
    `detectable_in` ('pass1' or 'pass2'). Only reviews of the pass in which the defect is visible are counted. A
    defect is `detected` when validity is 'invalid' and `flagged` when it is 'invalid' or 'uncertain'. For the valid
    control the counts are false rejections. A reviewer who flags a type must also name it to earn `attributed`.
    """

    totals: dict[str, dict[str, int]] = {}
    for record in decisions:
        item = key.get(record["item_id"])
        if item is None:
            continue
        needed_pass = 2 if item["detectable_in"] == "pass2" else 1
        if record["pass_number"] != needed_pass:
            continue
        entry = totals.setdefault(item["defect_type"], {
            "n_reviews": 0, "invalid": 0, "uncertain": 0, "valid": 0, "attributed": 0})
        entry["n_reviews"] += 1
        entry[record["validity"]] += 1
        if record["validity"] == "invalid" and item["defect_type"] in record.get("defect_flags", []):
            entry["attributed"] += 1
    report: dict[str, Any] = {}
    for defect_type, entry in sorted(totals.items()):
        n = entry["n_reviews"]
        is_control = key_expected(key, defect_type) == "valid"
        report[defect_type] = {
            **entry,
            ("false_rejection_rate" if is_control else "sensitivity_detected"): entry["invalid"] / n,
            ("false_uncertain_rate" if is_control else "sensitivity_flagged"):
                (entry["uncertain"] if is_control else entry["invalid"] + entry["uncertain"]) / n,
            **({} if is_control else {"attribution_rate": entry["attributed"] / n}),
        }
    return report


def key_expected(key: Mapping[str, Mapping[str, Any]], defect_type: str) -> str:
    for item in key.values():
        if item["defect_type"] == defect_type:
            return str(item["expected_verdict"])
    raise KeyError(defect_type)


def missed_defect_types(report: Mapping[str, Any], minimum_sensitivity: float | None = None) -> list[str]:
    """Defect types no reviewer detected (or below an explicit, caller-declared floor).

    The plan sets no numeric qualification threshold and warns that no arbitrary agreement threshold substitutes for
    reviewing concrete physics defects (B4.5 Gate B4, p.10). With no floor given, only types with zero detections are
    listed; a type with zero reviews is reported as missed, not silently absent.
    """

    missed = []
    for defect_type, entry in report.items():
        if entry.get("false_rejection_rate") is not None:
            continue
        value = entry["sensitivity_detected"]
        if value == 0 or (minimum_sensitivity is not None and value < minimum_sensitivity):
            missed.append(defect_type)
    return sorted(missed)


def completeness(records: Iterable[Mapping[str, Any]], expected_items: Sequence[str],
                 reviewers: Sequence[str]) -> dict[str, Any]:
    """Which (reviewer, item, pass) reviews are missing: a missing review is NOT_EVALUATED, never agreement."""

    seen = {(r["reviewer_id"], r["item_id"], r["pass_number"]) for r in records}
    missing = [(r, i, p) for r in reviewers for i in expected_items for p in (1, 2) if (r, i, p) not in seen]
    return {"expected": len(reviewers) * len(expected_items) * 2, "present": len(seen),
            "missing": [list(m) for m in missing]}
