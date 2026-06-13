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
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

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
    """Run 5-fold CV and return out-of-fold probabilities."""

    if len(np.unique(labels)) < 2:
        raise ValueError("Surface baselines require at least one positive and one negative family.")
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
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

    if baseline_name == "tfidf_logistic":
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        features = vectorizer.fit_transform(prompts)
        feature_builder = lambda labels: fit_predict_cv(  # noqa: E731
            features=features,
            labels=labels,
            build_model=build_logistic_model,
            is_sparse=True,
            seed=seed,
        )
    elif baseline_name == "prompt_statistics":
        features = prompt_statistics_features(prompts)
        feature_builder = lambda labels: fit_predict_cv(  # noqa: E731
            features=features,
            labels=labels,
            build_model=build_logistic_model,
            is_sparse=False,
            seed=seed,
        )
    elif baseline_name == "cue_span_only":
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        features = vectorizer.fit_transform(cue_sentences)
        feature_builder = lambda labels: fit_predict_cv(  # noqa: E731
            features=features,
            labels=labels,
            build_model=build_logistic_model,
            is_sparse=True,
            seed=seed,
        )
    elif baseline_name == "bag_of_words":
        vectorizer = CountVectorizer(ngram_range=(1, 1), min_df=1)
        features = vectorizer.fit_transform(prompts)
        feature_builder = lambda labels: fit_predict_cv(  # noqa: E731
            features=features,
            labels=labels,
            build_model=build_logistic_model,
            is_sparse=True,
            seed=seed,
        )
    else:
        raise ValueError(f"Unsupported baseline {baseline_name!r}.")

    payload: dict[str, Any] = {
        "baseline_name": baseline_name,
        "threshold_mode": threshold_mode,
        "results_by_model": {},
    }
    for model_key, labels in labels_by_model.items():
        probabilities = feature_builder(labels)
        payload["results_by_model"][model_key] = {
            "auroc": compute_auroc(labels, probabilities),
            "auprc": compute_auprc(labels, probabilities),
            "brier": compute_brier(labels, probabilities),
            "positive_rate": float(labels.mean()),
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
    labels_by_model: dict[str, np.ndarray] = {}

    for row in family_rows:
        prompt, cue_sentence = load_family_prompts(generated_dir, row["template_id"])
        prompts.append(prompt)
        cue_sentences.append(cue_sentence)

    threshold_mode = "exploratory_any_flip" if args.threshold is None else "pre_registered_threshold"
    for target_column in DEFAULT_TARGET_COLUMNS:
        scores = np.asarray([float(row[target_column]) for row in family_rows], dtype=float)
        labels_by_model[target_column.replace("_hat_S", "")] = make_binary_labels(scores, args.threshold)[0]

    for baseline_name in DEFAULT_BASELINES:
        payload = evaluate_baseline(
            baseline_name=baseline_name,
            prompts=prompts,
            cue_sentences=cue_sentences,
            labels_by_model=labels_by_model,
            threshold_mode=threshold_mode,
            seed=args.seed,
        )
        write_json(output_dir / f"surface_{baseline_name}.json", payload)
        logger.log_event("SURFACE_BASELINE_COMPLETE", baseline_name=baseline_name, threshold_mode=threshold_mode)


if __name__ == "__main__":
    main()
