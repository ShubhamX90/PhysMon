#!/usr/bin/env python3
"""Fit the combined non-activation baseline (Part II §8.3.4).

Part II §8.3.4 calls a model trained on *all* non-activation features "the
correct practical comparator for the incremental value of internal states", and
§8.4 makes the three-way comparison against it the decisive monitoring result.
No such combined model existed anywhere in this repository: the individual
baselines were each fit and reported separately, and never joined.

What counts as non-activation matters more than it looks.  The Stage 9
"correctness probe" is a linear probe over hidden states -- its artifact carries
a ``layer_index`` -- so including it here would put activation-derived
information into the baseline that activations are supposed to be tested
against, and would quietly destroy the comparison.  It is excluded, and offered
separately as an activation-based comparator.

Evaluation follows §8.2: nested family-level cross-validation, with the inner
folds selecting regularization and the outer folds untouched during selection.
The canonical family is the resampling unit throughout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.probing.metrics import (  # noqa: E402
    compute_auprc,
    compute_auroc,
    compute_brier,
    compute_ece,
)

NUMERIC_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?", re.I)
SYMBOL_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")

# Raw non-activation measurements: (artifact, field, feature name).
#
# Only genuinely measured quantities belong here. The other baselines publish
# *fitted* LogisticRegression outputs -- entropy "prediction",
# blackbox "prediction_directional" and "prediction_margin" -- each trained on
# these same 135 labels. Stacking those as features and re-evaluating under a
# fresh k-fold split leaks label information across folds: the fitted value for
# a training-fold family was produced by a model that saw test-fold labels.
# Including them raises the reported AUROC from 0.705 to 0.930, which is an
# artifact of the leak rather than a stronger baseline.
NON_ACTIVATION_SOURCES = [
    ("results/stage9/baselines/entropy/entropy_per_family_scores.json", "entropy_proxy_score", "entropy_proxy"),
    ("results/stage9/baselines/entropy/entropy_per_family_scores.json", "mean_logprob_correct_answer", "mean_logprob_correct"),
]

# Fitted outputs of other baselines, available only behind an explicit flag.
FITTED_BASELINE_OUTPUTS = [
    ("results/stage9/baselines/entropy/entropy_per_family_scores.json", "prediction", "entropy_model"),
    ("results/stage9/baselines/blackbox_counterfactual/family_scores.json", "prediction_directional", "blackbox_directional"),
    ("results/stage9/baselines/blackbox_counterfactual/family_scores.json", "prediction_margin", "blackbox_margin"),
]

# Excluded on purpose; see the module docstring.
ACTIVATION_DERIVED_EXCLUSIONS = {
    "results/stage9/baselines/correctness_probe/loo_predictions_variance.json": (
        "carries layer_index: a probe over hidden states, not a non-activation feature"
    ),
}

LABEL_SOURCE = "results/stage10/mean_probe_full_sweep_bigcompute/loo_predictions_resid_post_last_prompt.json"


def load_json(rel_path: str) -> Any:
    return json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))


def load_labels() -> dict[str, int]:
    return {str(r["template_id"]): int(r["true_label"]) for r in load_json(LABEL_SOURCE)}


def prompt_statistics(template_id: str) -> dict[str, float]:
    """Surface features computed from the family's own template."""

    matches = sorted((REPO_ROOT / "data/raw/templates").rglob(f"{template_id}.yaml"))
    if not matches:
        return {}
    payload = yaml.safe_load(matches[0].read_text(encoding="utf-8"))
    template = (payload.get("prompt_template") or {}).get("full_template") or ""
    equation = str(payload.get("governing_equation_sympy") or "")
    answer = (payload.get("correct_answer") or {}).get("value")
    try:
        answer_magnitude = float(np.log10(abs(float(answer)))) if answer not in (None, 0) else 0.0
    except (TypeError, ValueError):
        answer_magnitude = 0.0
    return {
        "prompt_chars": float(len(template)),
        "prompt_words": float(len(template.split())),
        "prompt_numbers": float(len(NUMERIC_RE.findall(template))),
        "equation_symbols": float(len(set(SYMBOL_RE.findall(equation)))),
        "equation_chars": float(len(equation)),
        "n_parameters": float(len(payload.get("parameters") or {})),
        "answer_log10_magnitude": answer_magnitude,
    }


def build_feature_matrix(
    include_prompt_statistics: bool = True,
    include_fitted_outputs: bool = False,
) -> tuple[list[str], np.ndarray, np.ndarray, list[str]]:
    labels_by_family = load_labels()
    sources = list(NON_ACTIVATION_SOURCES)
    if include_fitted_outputs:
        sources += FITTED_BASELINE_OUTPUTS
    tables: dict[str, dict[str, float]] = {}
    for rel_path, field, name in sources:
        rows = load_json(rel_path)
        tables[name] = {
            str(r["template_id"]): float(r[field])
            for r in rows
            if r.get(field) is not None
        }

    families = sorted(set(labels_by_family) & set.intersection(*(set(t) for t in tables.values())))
    feature_names = [name for _, _, name in sources]

    prompt_features: dict[str, dict[str, float]] = {}
    if include_prompt_statistics:
        for family in families:
            stats = prompt_statistics(family)
            if stats:
                prompt_features[family] = stats
        if prompt_features:
            feature_names += sorted(next(iter(prompt_features.values())))

    matrix = []
    for family in families:
        row = [tables[name][family] for _, _, name in sources]
        if include_prompt_statistics and prompt_features:
            stats = prompt_features.get(family, {})
            row += [stats.get(key, 0.0) for key in sorted(next(iter(prompt_features.values())))]
        matrix.append(row)

    return (
        feature_names,
        np.asarray(matrix, dtype=float),
        np.asarray([labels_by_family[f] for f in families], dtype=int),
        families,
    )


def nested_cv_predictions(
    features: np.ndarray,
    labels: np.ndarray,
    outer_folds: int,
    inner_folds: int,
    grid: list[float],
    seed: int,
) -> tuple[np.ndarray, list[float]]:
    """Out-of-fold predictions with regularization chosen inside each outer fold."""

    predictions = np.zeros(len(labels), dtype=float)
    chosen: list[float] = []
    outer = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=seed)

    for train_index, test_index in outer.split(features, labels):
        best_c, best_score = grid[0], -np.inf
        inner = StratifiedKFold(n_splits=inner_folds, shuffle=True, random_state=seed)
        for candidate in grid:
            inner_scores = []
            for inner_train, inner_test in inner.split(features[train_index], labels[train_index]):
                model = Pipeline(
                    [
                        ("scale", StandardScaler()),
                        ("clf", LogisticRegression(C=candidate, max_iter=5000)),
                    ]
                )
                model.fit(features[train_index][inner_train], labels[train_index][inner_train])
                scores = model.predict_proba(features[train_index][inner_test])[:, 1]
                inner_labels = labels[train_index][inner_test]
                if len(np.unique(inner_labels)) < 2:
                    continue
                inner_scores.append(compute_auroc(inner_labels, scores))
            mean_score = float(np.mean(inner_scores)) if inner_scores else -np.inf
            if mean_score > best_score:
                best_c, best_score = candidate, mean_score

        chosen.append(best_c)
        model = Pipeline(
            [("scale", StandardScaler()), ("clf", LogisticRegression(C=best_c, max_iter=5000))]
        )
        model.fit(features[train_index], labels[train_index])
        predictions[test_index] = model.predict_proba(features[test_index])[:, 1]

    return predictions, chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outer-folds", type=int, default=5)
    parser.add_argument("--inner-folds", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-prompt-statistics", action="store_true")
    parser.add_argument(
        "--include-fitted-baseline-outputs",
        action="store_true",
        help="Add other baselines' fitted predictions as features. This LEAKS label "
        "information across folds and inflates the estimate; diagnostic use only.",
    )
    parser.add_argument("--output-dir", default="results/wave2/combined_baseline")
    args = parser.parse_args()

    feature_names, features, labels, families = build_feature_matrix(
        include_prompt_statistics=not args.no_prompt_statistics,
        include_fitted_outputs=args.include_fitted_baseline_outputs,
    )
    if len(families) == 0:
        raise SystemExit("no families with complete non-activation features")

    predictions, chosen = nested_cv_predictions(
        features, labels, args.outer_folds, args.inner_folds,
        [0.01, 0.1, 1.0, 10.0, 100.0], args.seed,
    )

    summary = {
        "model": "combined_non_activation_baseline",
        "reference": "PhysMon Part II 8.3.4 and 8.2",
        "n_families": len(families),
        "n_positive": int((labels == 1).sum()),
        "n_negative": int((labels == 0).sum()),
        "feature_names": feature_names,
        "n_features": features.shape[1],
        "excluded_activation_derived": ACTIVATION_DERIVED_EXCLUSIONS,
        "includes_fitted_baseline_outputs": args.include_fitted_baseline_outputs,
        "leakage_warning": (
            "Fitted baseline outputs were stacked as features. Their values were "
            "produced by models trained on labels that appear in other folds, so this "
            "estimate is inflated and is diagnostic only."
            if args.include_fitted_baseline_outputs
            else "none: all features are raw measurements refit inside the CV"
        ),
        "cv": {
            "scheme": "nested_stratified_family_level",
            "outer_folds": args.outer_folds,
            "inner_folds": args.inner_folds,
            "seed": args.seed,
            "selected_C_per_outer_fold": chosen,
            "resampling_unit": "canonical_family",
        },
        "metrics": {
            "auroc": round(compute_auroc(labels, predictions), 4),
            "auprc": round(compute_auprc(labels, predictions), 4),
            "brier": round(compute_brier(labels, predictions), 4),
            "ece": round(compute_ece(labels, predictions), 4),
        },
        "status": "complete_exploratory",
        "experiment_class": "exploratory_unfrozen",
        "paper_eligibility": False,
        "note": (
            "Discovery-tier. The monitor, threshold and panel were selected on these "
            "same families in earlier stages, so this is not confirmatory evidence."
        ),
    }

    output_dir = REPO_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "combined_baseline_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "combined_baseline_predictions.json").write_text(
        json.dumps(
            [
                {"template_id": f, "prediction": float(p), "true_label": int(l)}
                for f, p, l in zip(families, predictions, labels)
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary["metrics"], indent=2))
    print(f"families={len(families)} features={features.shape[1]} -> {output_dir}")


if __name__ == "__main__":
    main()
