#!/usr/bin/env python3
# ruff: noqa: E402
"""Run Stage 5 surface-only baseline models over per-family Stage 4 data.

Reference:
    `physmon_proposal.pdf` §10 and the Stage 5 preparation brief.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold, StratifiedKFold

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.probing.metrics import compute_auprc, compute_auroc, compute_brier  # noqa: E402
from physmon.utils.io import read_yaml, write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402


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
    "cot_text_classifier",
    "answer_rationale_classifier",
)
DEFAULT_CONTINUOUS_TARGET_COLUMNS = ("qwen_S_lp_repair", "llama_S_lp_repair")
DEFAULT_STAGE6_CONTINUOUS_TARGET_COLUMNS = ("qwen_S_lp", "llama_S_lp")


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
        "--exclude-ids",
        nargs="*",
        default=(),
        help="Optional template ids to exclude from baseline fitting.",
    )
    parser.add_argument(
        "--target-measure",
        choices=("hat_s_binary", "slp_binary"),
        default="hat_s_binary",
        help="Binary target family used for the surface baseline labels.",
    )
    parser.add_argument(
        "--positive-families-file",
        default=None,
        help="Optional JSON file with a precomputed positive-family set for one custom model.",
    )
    parser.add_argument(
        "--continuous-target-column",
        default=None,
        help="Optional explicit continuous target column, e.g. deepseek_S_lp.",
    )
    parser.add_argument(
        "--custom-model-key",
        default=None,
        help="Optional result key used with --positive-families-file or --continuous-target-column.",
    )
    parser.add_argument(
        "--behavioural-jsonl",
        default=None,
        help="Optional behavioural JSONL used by text baselines over generated answers/CoT.",
    )
    parser.add_argument(
        "--baseline-type",
        choices=DEFAULT_BASELINES,
        default=None,
        help="Optional single baseline to run instead of the full suite.",
    )
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE, help="Scientific stage number for logging.")
    return parser.parse_args()


def load_family_rows(path: Path) -> list[dict[str, str]]:
    """Load Stage 4 per-family CSV rows."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def filter_family_rows(
    rows: list[dict[str, str]],
    exclude_ids: set[str],
) -> list[dict[str, str]]:
    """Drop any template ids explicitly excluded from one baseline run."""

    if not exclude_ids:
        return rows
    return [row for row in rows if row["template_id"] not in exclude_ids]


def load_family_prompts(generated_dir: Path, template_id: str) -> tuple[str, str]:
    """Load the base prompt and cue sentence for one rendered family."""

    payload = read_yaml(generated_dir / f"{template_id}.json")
    base_variant = next(variant for variant in payload["variants"] if int(variant["variant_id"]) == 0)
    return str(base_variant["prompt"]), str(base_variant["cue_sentence"])


def load_family_generated_texts(path: Path) -> dict[str, list[str]]:
    """Load per-family generated texts from one behavioural JSONL."""

    generated: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") != "variant_record":
                continue
            template_id = str(record["template_id"])
            text = str(record.get("generated_text", "")).strip()
            if not text:
                continue
            generated.setdefault(template_id, []).append(text)
    return generated


def make_binary_labels(scores: np.ndarray, threshold: float | None) -> tuple[np.ndarray, str]:
    """Convert continuous sensitivity scores into evaluation labels."""

    if threshold is None:
        return (scores > 0.0).astype(int), "exploratory_any_flip"
    return (scores >= threshold).astype(int), "pre_registered_threshold"


def resolve_binary_target_columns(
    rows: list[dict[str, str]],
    target_measure: str,
) -> tuple[str, ...]:
    """Resolve the per-model target columns available in the supplied CSV."""

    if not rows:
        raise ValueError("No per-family rows available for surface baseline analysis.")

    available = set(rows[0].keys())
    if target_measure == "hat_s_binary":
        return DEFAULT_TARGET_COLUMNS

    stage6_columns = DEFAULT_STAGE6_CONTINUOUS_TARGET_COLUMNS
    if all(column in available for column in stage6_columns):
        return stage6_columns

    stage5_columns = tuple(column.replace("_hat_S", "_S_lp_repair") for column in DEFAULT_TARGET_COLUMNS)
    if all(column in available for column in stage5_columns):
        return stage5_columns

    raise KeyError(
        "Could not resolve S_lp columns in per-family CSV. "
        f"Available columns: {sorted(available)}"
    )


def load_positive_families_payload(path: Path) -> dict[str, Any]:
    """Load one externally supplied positive-family payload."""

    return json.loads(path.read_text(encoding="utf-8"))


def resolve_continuous_target_columns(rows: list[dict[str, str]]) -> tuple[str, ...]:
    """Resolve the continuous S_lp columns available in the supplied CSV."""

    if not rows:
        return ()

    available = set(rows[0].keys())
    if all(column in available for column in DEFAULT_STAGE6_CONTINUOUS_TARGET_COLUMNS):
        return DEFAULT_STAGE6_CONTINUOUS_TARGET_COLUMNS
    if all(column in available for column in DEFAULT_CONTINUOUS_TARGET_COLUMNS):
        return DEFAULT_CONTINUOUS_TARGET_COLUMNS
    return ()


def model_key_from_column(column: str) -> str:
    """Map one target column to the canonical model key used in result payloads."""

    if column.startswith("qwen_"):
        return "qwen"
    if column.startswith("llama_"):
        return "llama"
    if column.startswith("deepseek_"):
        return "deepseek"
    raise ValueError(f"Unsupported target column {column!r}.")


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
    cot_documents: list[str],
    answer_rationale_documents: list[str],
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
        elif baseline_name == "cot_text_classifier":
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            features = vectorizer.fit_transform([cot_documents[index] for index in prompt_subset])
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
        elif baseline_name == "answer_rationale_classifier":
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            features = vectorizer.fit_transform([answer_rationale_documents[index] for index in prompt_subset])
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
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )

    family_rows = filter_family_rows(
        load_family_rows(Path(args.family_csv)),
        set(args.exclude_ids),
    )
    generated_dir = Path(args.generated_dir)
    prompts: list[str] = []
    cue_sentences: list[str] = []
    cot_documents: list[str] = []
    answer_rationale_documents: list[str] = []
    labels_by_model: dict[str, dict[str, Any]] = {}
    continuous_targets_by_model: dict[str, dict[str, Any]] = {}
    generated_texts_by_family = (
        load_family_generated_texts(Path(args.behavioural_jsonl))
        if args.behavioural_jsonl
        else {}
    )

    for row in family_rows:
        prompt, cue_sentence = load_family_prompts(generated_dir, row["template_id"])
        prompts.append(prompt)
        cue_sentences.append(cue_sentence)
        generated_text = " ".join(generated_texts_by_family.get(row["template_id"], [])).strip()
        cot_documents.append(generated_text)
        answer_rationale_documents.append(f"{prompt}\n\n{generated_text}".strip())

    threshold_mode = "exploratory_any_flip" if args.threshold is None else "pre_registered_threshold"
    if args.positive_families_file is not None:
        payload = load_positive_families_payload(Path(args.positive_families_file))
        model_key = args.custom_model_key or model_key_from_column(str(payload.get("slp_column", "deepseek_S_lp")))
        positive_families = set(str(item) for item in payload["positive_families"])
        prompt_indices = list(range(len(family_rows)))
        labels = np.asarray(
            [1 if row["template_id"] in positive_families else 0 for row in family_rows],
            dtype=int,
        )
        labels_by_model[model_key] = {
            "labels": labels,
            "prompt_indices": prompt_indices,
        }
        if args.threshold is None:
            threshold_mode = "precomputed_positive_families"
    else:
        target_columns = resolve_binary_target_columns(family_rows, args.target_measure)
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
            labels_by_model[model_key_from_column(target_column)] = {
                "labels": labels,
                "prompt_indices": prompt_indices,
            }

    continuous_columns = (
        (args.continuous_target_column,) if args.continuous_target_column else resolve_continuous_target_columns(family_rows)
    )
    for target_column in continuous_columns:
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
        model_key = args.custom_model_key or model_key_from_column(target_column)
        continuous_targets_by_model[model_key] = {
            "targets": np.asarray(filtered_targets, dtype=float),
            "prompt_indices": prompt_indices,
        }

    baselines_to_run = (args.baseline_type,) if args.baseline_type else DEFAULT_BASELINES
    for baseline_name in baselines_to_run:
        payload = evaluate_baseline(
            baseline_name=baseline_name,
            prompts=prompts,
            cue_sentences=cue_sentences,
            cot_documents=cot_documents,
            answer_rationale_documents=answer_rationale_documents,
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
