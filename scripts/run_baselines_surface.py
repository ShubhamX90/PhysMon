#!/usr/bin/env python3
"""Run Stage 5 surface-only baseline models over per-family Stage 4 data.

Reference:
    `physmon_proposal.pdf` §10 and the Stage 5 preparation brief.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold, StratifiedKFold

from physmon.probing.metrics import compute_auprc, compute_auroc, compute_brier
from physmon.utils.io import read_yaml, write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 5
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_baselines_surface_events.jsonl"
DEFAULT_TARGET_COLUMNS = ("qwen_hat_S", "llama_hat_S")
DEFAULT_UNIT_TOKENS = ("m/s", "m/s^2", "N", "J", "V", "W", "C", "N/C", "Ω", "F", "kg", "m", "s")
DEFAULT_BASELINES = (
    "tfidf_logistic",
    "prompt_statistics",
    "cue_span_only",
    "bag_of_words",
)
DEFAULT_CONTINUOUS_TARGET_COLUMNS = ("qwen_S_lp_repair", "llama_S_lp_repair")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the surface baseline suite."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-csv", required=True, help="Stage 4 per-family CSV.")
    parser.add_argument("--output-dir", required=True, help="Directory for baseline result JSON files.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Optional pre-registered sensitivity threshold. If omitted, uses exploratory any-flip labels.",
    )
    parser.add_argument(
        "--generated-dir",
        default="data/generated",
        help="Rendered family directory used to recover prompt text.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic CV seed.")
    parser.add_argument(
        "--target-measure",
        choices=("hat_s_binary", "slp_binary"),
        default="hat_s_binary",
        help="Binary target family used for the surface baseline labels.",
    )
    return parser.parse_args()


def load_family_rows(path: Path) -> list[dict[str, str]]:
    """Load Stage 4 per-family CSV rows."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_family_prompts(generated_dir: Path, template_id: str) -> tuple[str, str]:
    """Load the base prompt and cue sentence for one rendered family."""

    payload = read_yaml(generated_dir / f"{template_id}.json")
    base_variant = next(variant for variant in payload["variants"] if int(variant["variant_id"]) == 0)
    return str(base_variant["prompt"]), str(base_variant["cue_sentence"])


def make_binary_labels(scores: np.ndarray, threshold: float | None) -> tuple[np.ndarray, str]:
    """Convert continuous sensitivity scores into evaluation labels."""

    if threshold is None:
        return (scores > 0.0).astype(int), "exploratory_any_flip"
    return (scores >= threshold).astype(int), "pre_registered_threshold"


def count_equation_like_tokens(text: str) -> int:
    """Count simple equation-like fragments in prompt text."""

    return len(re.findall(r"[A-Za-z0-9_]+\s*=\s*[-+*/^A-Za-z0-9_.()]+", text))


def prompt_statistics_features(prompts: list[str]) -> np.ndarray:
    """Compute hand-built prompt statistics for the surface baseline."""

    rows = []
    for prompt in prompts:
        digit_count = sum(character.isdigit() for character in prompt)
        unit_count = sum(prompt.count(unit_token) for unit_token in DEFAULT_UNIT_TOKENS)
        rows.append(
            [
                len(prompt),
                digit_count,
                unit_count,
                count_equation_like_tokens(prompt),
            ]
        )
    return np.asarray(rows, dtype=float)


def fit_predict_cv(
    *,
    features: Any,
    labels: np.ndarray,
    build_model,
    is_sparse: bool,
    seed: int,
) -> np.ndarray:
    """Run the maximum legal stratified CV and return out-of-fold probabilities."""

    if len(np.unique(labels)) < 2:
        raise ValueError("Surface baselines require at least one positive and one negative family.")
    class_counts = np.bincount(labels.astype(int))
    nonzero_class_counts = class_counts[class_counts > 0]
    if nonzero_class_counts.size < 2:
        raise ValueError("Surface baselines require at least one positive and one negative family.")
    n_splits = min(5, int(nonzero_class_counts.min()))
    if n_splits < 2:
        raise ValueError("Surface baselines require at least two examples in each class.")

    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    predictions = np.zeros(labels.shape[0], dtype=float)
    for train_indices, test_indices in splitter.split(np.zeros(labels.shape[0]), labels):
        train_features = features[train_indices] if not is_sparse else features[train_indices, :]
        test_features = features[test_indices] if not is_sparse else features[test_indices, :]
        model = build_model()
        model.fit(train_features, labels[train_indices])
        predictions[test_indices] = model.predict_proba(test_features)[:, 1]
    return predictions


def build_logistic_model() -> LogisticRegression:
    """Construct the shared logistic regression estimator for surface baselines."""

    return LogisticRegression(max_iter=2000, solver="liblinear", random_state=DEFAULT_SEED)


def build_ridge_model() -> Ridge:
    """Construct the shared ridge regressor for continuous surface checks."""

    return Ridge(alpha=1.0, random_state=DEFAULT_SEED)


def fit_predict_regression_cv(
    *,
    features: Any,
    targets: np.ndarray,
    build_model,
    is_sparse: bool,
    seed: int,
) -> np.ndarray:
    """Run deterministic K-fold regression CV and return out-of-fold predictions."""

    n_splits = min(5, len(targets))
    if n_splits < 2:
        raise ValueError("Continuous surface baselines require at least two families.")

    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    predictions = np.zeros(targets.shape[0], dtype=float)
    for train_indices, test_indices in splitter.split(np.zeros(targets.shape[0])):
        train_features = features[train_indices] if not is_sparse else features[train_indices, :]
        test_features = features[test_indices] if not is_sparse else features[test_indices, :]
        model = build_model()
        model.fit(train_features, targets[train_indices])
        predictions[test_indices] = model.predict(test_features)
    return predictions


def evaluate_baseline(
    *,
    baseline_name: str,
    prompts: list[str],
    cue_sentences: list[str],
    labels_by_model: dict[str, np.ndarray],
    threshold_mode: str,
    seed: int,
) -> dict[str, Any]:
    """Evaluate one baseline across both primary-model target columns."""

    if baseline_name not in DEFAULT_BASELINES:
        raise ValueError(f"Unsupported baseline {baseline_name!r}.")

    payload: dict[str, Any] = {
        "baseline_name": baseline_name,
        "threshold_mode": threshold_mode,
        "results_by_model": {},
    }
    for model_key, label_bundle in labels_by_model.items():
        labels = label_bundle["labels"]
        prompt_subset = label_bundle["prompt_indices"]
        if len(np.unique(labels)) < 2:
            payload["results_by_model"][model_key] = {
                "status": "skipped_insufficient_class_variation",
                "evaluated_families": int(labels.shape[0]),
                "positive_rate": float(labels.mean()) if labels.size else 0.0,
            }
            continue

        if baseline_name == "tfidf_logistic":
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            features = vectorizer.fit_transform([prompts[index] for index in prompt_subset])
            try:
                probabilities = fit_predict_cv(
                    features=features,
                    labels=labels,
                    build_model=build_logistic_model,
                    is_sparse=True,
                    seed=seed,
                )
            except ValueError as error:
                payload["results_by_model"][model_key] = {
                    "status": "skipped_insufficient_class_support",
                    "evaluated_families": int(labels.shape[0]),
                    "positive_rate": float(labels.mean()) if labels.size else 0.0,
                    "reason": str(error),
                }
                continue
        elif baseline_name == "prompt_statistics":
            features = prompt_statistics_features([prompts[index] for index in prompt_subset])
            try:
                probabilities = fit_predict_cv(
                    features=features,
                    labels=labels,
                    build_model=build_logistic_model,
                    is_sparse=False,
                    seed=seed,
                )
            except ValueError as error:
                payload["results_by_model"][model_key] = {
                    "status": "skipped_insufficient_class_support",
                    "evaluated_families": int(labels.shape[0]),
                    "positive_rate": float(labels.mean()) if labels.size else 0.0,
                    "reason": str(error),
                }
                continue
        elif baseline_name == "cue_span_only":
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            features = vectorizer.fit_transform([cue_sentences[index] for index in prompt_subset])
            try:
                probabilities = fit_predict_cv(
                    features=features,
                    labels=labels,
                    build_model=build_logistic_model,
                    is_sparse=True,
                    seed=seed,
                )
            except ValueError as error:
                payload["results_by_model"][model_key] = {
                    "status": "skipped_insufficient_class_support",
                    "evaluated_families": int(labels.shape[0]),
                    "positive_rate": float(labels.mean()) if labels.size else 0.0,
                    "reason": str(error),
                }
                continue
        elif baseline_name == "bag_of_words":
            vectorizer = CountVectorizer(ngram_range=(1, 1), min_df=1)
            features = vectorizer.fit_transform([prompts[index] for index in prompt_subset])
            try:
                probabilities = fit_predict_cv(
                    features=features,
                    labels=labels,
                    build_model=build_logistic_model,
                    is_sparse=True,
                    seed=seed,
                )
            except ValueError as error:
                payload["results_by_model"][model_key] = {
                    "status": "skipped_insufficient_class_support",
                    "evaluated_families": int(labels.shape[0]),
                    "positive_rate": float(labels.mean()) if labels.size else 0.0,
                    "reason": str(error),
                }
                continue
        else:
            raise ValueError(f"Unsupported baseline {baseline_name!r}.")

        payload["results_by_model"][model_key] = {
            "status": "ok",
            "evaluated_families": int(labels.shape[0]),
            "auroc": compute_auroc(labels, probabilities),
            "auprc": compute_auprc(labels, probabilities),
            "brier": compute_brier(labels, probabilities),
            "positive_rate": float(labels.mean()),
        }
    return payload


def evaluate_continuous_tfidf(
    *,
    prompts: list[str],
    targets_by_model: dict[str, dict[str, Any]],
    seed: int,
) -> dict[str, Any]:
    """Evaluate TF-IDF ridge regression against continuous S_lp targets."""

    payload: dict[str, Any] = {
        "baseline_name": "tfidf_continuous",
        "results_by_model": {},
    }
    for model_key, target_bundle in targets_by_model.items():
        targets = target_bundle["targets"]
        prompt_subset = target_bundle["prompt_indices"]
        if targets.shape[0] < 2:
            payload["results_by_model"][model_key] = {
                "status": "skipped_insufficient_examples",
                "evaluated_families": int(targets.shape[0]),
            }
            continue
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        features = vectorizer.fit_transform([prompts[index] for index in prompt_subset])
        predictions = fit_predict_regression_cv(
            features=features,
            targets=targets,
            build_model=build_ridge_model,
            is_sparse=True,
            seed=seed,
        )
        if np.std(targets) == 0.0 or np.std(predictions) == 0.0:
            pearson_r = 0.0
        else:
            pearson_r = float(np.corrcoef(targets, predictions)[0, 1])
        rmse = float(np.sqrt(np.mean((targets - predictions) ** 2)))
        payload["results_by_model"][model_key] = {
            "status": "ok",
            "evaluated_families": int(targets.shape[0]),
            "pearson_r": pearson_r,
            "rmse": rmse,
            "target_mean": float(targets.mean()),
            "prediction_mean": float(predictions.mean()),
        }
    return payload


def main() -> None:
    """Run the Stage 5 surface baseline suite."""

    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_baselines_surface.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )

    family_rows = load_family_rows(Path(args.family_csv))
    generated_dir = Path(args.generated_dir)
    prompts: list[str] = []
    cue_sentences: list[str] = []
    labels_by_model: dict[str, dict[str, Any]] = {}
    continuous_targets_by_model: dict[str, dict[str, Any]] = {}

    for row in family_rows:
        prompt, cue_sentence = load_family_prompts(generated_dir, row["template_id"])
        prompts.append(prompt)
        cue_sentences.append(cue_sentence)

    threshold_mode = "exploratory_any_flip" if args.threshold is None else "pre_registered_threshold"
    target_columns = (
        DEFAULT_TARGET_COLUMNS
        if args.target_measure == "hat_s_binary"
        else tuple(column.replace("_hat_S", "_S_lp_repair") for column in DEFAULT_TARGET_COLUMNS)
    )
    for target_column in target_columns:
        filtered_scores: list[float] = []
        prompt_indices: list[int] = []
        for index, row in enumerate(family_rows):
            raw_value = row[target_column]
            if raw_value == "":
                continue
            filtered_scores.append(float(raw_value))
            prompt_indices.append(index)
        scores = np.asarray(filtered_scores, dtype=float)
        labels, _ = make_binary_labels(scores, args.threshold)
        labels_by_model[
            target_column.replace("_hat_S", "").replace("_S_lp_repair", "")
        ] = {
            "labels": labels,
            "prompt_indices": prompt_indices,
        }

    for target_column in DEFAULT_CONTINUOUS_TARGET_COLUMNS:
        filtered_targets: list[float] = []
        prompt_indices: list[int] = []
        for index, row in enumerate(family_rows):
            raw_value = row.get(target_column, "")
            if raw_value == "":
                continue
            filtered_targets.append(float(raw_value))
            prompt_indices.append(index)
        if not filtered_targets:
            continue
        continuous_targets_by_model[target_column.replace("_S_lp_repair", "")] = {
            "targets": np.asarray(filtered_targets, dtype=float),
            "prompt_indices": prompt_indices,
        }

    for baseline_name in DEFAULT_BASELINES:
        payload = evaluate_baseline(
            baseline_name=baseline_name,
            prompts=prompts,
            cue_sentences=cue_sentences,
            labels_by_model=labels_by_model,
            threshold_mode=threshold_mode,
            seed=args.seed,
        )
        suffix = "_slp_binary" if args.target_measure == "slp_binary" else ""
        write_json(output_dir / f"surface_{baseline_name}{suffix}.json", payload)
        logger.log_event(
            "SURFACE_BASELINE_COMPLETE",
            baseline_name=baseline_name,
            threshold_mode=threshold_mode,
            target_measure=args.target_measure,
        )

    if continuous_targets_by_model:
        continuous_payload = evaluate_continuous_tfidf(
            prompts=prompts,
            targets_by_model=continuous_targets_by_model,
            seed=args.seed,
        )
        write_json(output_dir / "surface_tfidf_continuous.json", continuous_payload)
        logger.log_event("SURFACE_BASELINE_CONTINUOUS_COMPLETE", baseline_name="tfidf_continuous")


if __name__ == "__main__":
    main()
