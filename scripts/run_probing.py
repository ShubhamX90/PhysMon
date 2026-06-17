#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 5 probe training and evaluation entry point.

Reference:
    `physmon_proposal.pdf` §9, §11 and the Stage 5 briefs Parts D, G, H, and 5.1.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
import random
import sys
from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.benchmark.parser import parse_answer  # noqa: E402
from physmon.formal.constructs import (
    STAGE5_POSITIVE_FAMILIES,
    STAGE5_SLP_THRESHOLD,
    STAGE6_POSITIVE_FAMILIES,
    STAGE6_SLP_THRESHOLD,
)  # noqa: E402
from physmon.probing.metrics import compute_auprc, compute_auroc, compute_brier  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402


DEFAULT_STAGE = 5
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_probing_events.jsonl"
DEFAULT_C_VALUES = (0.001, 0.01, 0.1, 1.0, 10.0)
DEFAULT_RIDGE_ALPHA = 1.0
DEFAULT_RANDOM_BASELINE_DRAWS = 100
DEFAULT_FAMILY_CSV = "results/stage4_repair/analysis_v2/stage4_per_family.csv"
DEFAULT_BEHAVIOURAL_DIR = "results/stage4_repair/behavioural"
DEFAULT_PAIR_THRESHOLD = STAGE5_SLP_THRESHOLD
AGGREGATE_MEAN = "mean"
AGGREGATE_MAX = "max"
DEFAULT_ENSEMBLE_LAYERS = (15, 16, 17, 18, 19, 20)
DEFAULT_PCA_PER_LAYER = 50
DEFAULT_MLP_HIDDEN_LAYERS = (128, 32)
DEFAULT_DOMAIN_GENERALISATION_MODE = "domain_generalisation"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 5 probing runner."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation-dir", required=True, help="Activation directory containing manifest.json.")
    parser.add_argument("--site", required=True, help="Activation site, e.g. resid_post_last_prompt.")
    parser.add_argument("--model-role", required=True, help="Model role label for reporting.")
    parser.add_argument(
        "--target-measure",
        choices=("slp_binary", "slp_continuous", "answer_correctness"),
        default="slp_binary",
        help="Primary target measure for summary reporting.",
    )
    parser.add_argument(
        "--probe-type",
        choices=("mean", "contrast", "variance", "variance_ensemble", "variance_mlp"),
        default="mean",
        help="Probe over family means, within-family variance, or pairwise contrasts.",
    )
    parser.add_argument(
        "--pca-dims",
        type=int,
        default=None,
        help="Optional per-fold PCA dimensionality before probing.",
    )
    parser.add_argument(
        "--layer-filter",
        default=None,
        help="Optional comma-separated layer indices to evaluate.",
    )
    parser.add_argument(
        "--behavioural-jsonl",
        default=None,
        help=(
            "Optional behavioural JSONL for contrast labels and variant-selection metadata; "
            "defaults to the latest matching file."
        ),
    )
    parser.add_argument(
        "--pair-threshold",
        type=float,
        default=DEFAULT_PAIR_THRESHOLD,
        help="Threshold on absolute pairwise logprob difference for contrast labels.",
    )
    parser.add_argument(
        "--n-variants",
        type=int,
        default=4,
        choices=(2, 3, 4),
        help=(
            "Number of variants to use when computing family-level variance features. "
            "n=2 uses base v0 plus the most-sensitive variant by logprob drop; "
            "n=3 uses v0,v1,v2; n=4 uses all variants."
        ),
    )
    parser.add_argument("--output-dir", required=True, help="Directory for Stage 5 probing artifacts.")
    parser.add_argument("--family-csv", default=DEFAULT_FAMILY_CSV, help="Stage 4/5 per-family CSV.")
    parser.add_argument(
        "--positive-families-file",
        default=None,
        help="Optional JSON file with {'threshold': float, 'positive_families': [...]} for binary labels.",
    )
    parser.add_argument(
        "--exclude-ids",
        nargs="*",
        default=(),
        help="Optional template ids to exclude from this probing run.",
    )
    parser.add_argument(
        "--exclude-cue-type",
        default=None,
        help="Optional cue_type value to exclude, e.g. frame_rendering.",
    )
    parser.add_argument(
        "--cue-type",
        default=None,
        help="Optional cue_type value to keep exclusively, e.g. frame_rendering.",
    )
    parser.add_argument(
        "--include-cue-type-only",
        dest="cue_type",
        default=None,
        help="Alias for --cue-type to keep one cue_type exclusively.",
    )
    parser.add_argument(
        "--pilot-only",
        action="store_true",
        help="Allow subset-only analysis runs from filtered family slices without changing labels.",
    )
    parser.add_argument(
        "--cv-mode",
        choices=("loo", "domain_generalisation"),
        default="loo",
        help="Cross-validation mode: leave-one-family-out or held-out domain folds.",
    )
    parser.add_argument(
        "--ensemble-layers",
        nargs="+",
        type=int,
        default=list(DEFAULT_ENSEMBLE_LAYERS),
        help="Layer set used by the variance ensemble probe.",
    )
    parser.add_argument(
        "--pca-per-layer",
        type=int,
        default=DEFAULT_PCA_PER_LAYER,
        help="Per-layer PCA width for variance ensemble features.",
    )
    parser.add_argument(
        "--cross-model-activation-dir",
        default=None,
        help="Optional second activation directory for cross-model validation.",
    )
    parser.add_argument(
        "--cross-model-role",
        default="llama_primary",
        help="Role label for the optional cross-model activation directory.",
    )
    parser.add_argument(
        "--correctness-column",
        default=None,
        help="Optional per-family correctness-rate column. If absent, derive correctness from behavioural JSONL.",
    )
    parser.add_argument(
        "--correctness-threshold",
        type=float,
        default=0.75,
        help="Family correctness threshold for --target-measure answer_correctness.",
    )
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE, help="Scientific stage number for logging.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed.")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    """Set reproducibility seeds for probing experiments."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_manifest(path: Path) -> dict[str, Any]:
    """Load one extraction manifest."""

    return json.loads(path.read_text(encoding="utf-8"))


def load_per_family_rows(path: Path) -> dict[str, dict[str, str]]:
    """Load the Stage 4/5 per-family CSV keyed by template id."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["template_id"]: row for row in csv.DictReader(handle)}


def infer_positive_families(
    *,
    family_csv: Path,
    positive_families_file: Path | None,
) -> tuple[frozenset[str], float]:
    """Resolve the binary sensitivity label source for one probing run."""

    if positive_families_file is not None:
        payload = json.loads(positive_families_file.read_text(encoding="utf-8"))
        positives = frozenset(str(item) for item in payload["positive_families"])
        threshold = float(payload.get("threshold", STAGE6_SLP_THRESHOLD))
        return positives, threshold

    family_csv_text = str(family_csv)
    if "stage6" in family_csv_text:
        return STAGE6_POSITIVE_FAMILIES, STAGE6_SLP_THRESHOLD
    return STAGE5_POSITIVE_FAMILIES, STAGE5_SLP_THRESHOLD


def load_site_tensors(
    activation_dir: Path,
    site: str,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Load all variant tensors for one site into a dense numpy array."""

    manifest = load_manifest(activation_dir / "manifest.json")
    matching = [entry for entry in manifest["files"] if entry["site"] == site]
    if not matching:
        raise FileNotFoundError(f"No manifest entries for site '{site}' in {activation_dir}.")
    matching.sort(key=lambda item: (str(item["template_id"]), int(item["variant_id"])))

    tensors = [
        torch.load(resolve_tensor_path(activation_dir, entry), map_location="cpu").float().numpy()
        for entry in matching
    ]
    stacked = np.stack(tensors, axis=0)
    return matching, stacked


def filter_entries_and_tensors(
    entries: list[dict[str, Any]],
    tensors: np.ndarray,
    *,
    family_rows: dict[str, dict[str, str]],
    exclude_ids: set[str],
    exclude_cue_type: str | None,
    cue_type: str | None,
    pilot_only: bool,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Filter manifest entries and tensors to one requested Stage 6 analysis subset."""

    kept_entries: list[dict[str, Any]] = []
    kept_indices: list[int] = []
    for index, entry in enumerate(entries):
        template_id = str(entry["template_id"])
        if template_id not in family_rows:
            continue
        if template_id in exclude_ids:
            continue
        row = family_rows[template_id]
        row_cue_type = row.get("cue_type", "")
        if exclude_cue_type and row_cue_type == exclude_cue_type:
            continue
        if cue_type and row_cue_type != cue_type:
            continue
        kept_entries.append(entry)
        kept_indices.append(index)

    if not kept_entries:
        raise ValueError("Filtering removed every activation entry; no probeable families remain.")
    return kept_entries, tensors[np.asarray(kept_indices, dtype=int)]


def resolve_tensor_path(activation_dir: Path, entry: dict[str, Any]) -> Path:
    """Resolve one manifest tensor path, falling back to the local sync directory."""

    candidate = Path(str(entry["tensor_path"]))
    if candidate.exists():
        return candidate

    filename = candidate.name
    local_candidate = activation_dir / str(entry["template_id"]) / filename
    if local_candidate.exists():
        return local_candidate

    raise FileNotFoundError(
        f"Could not resolve tensor for template {entry['template_id']} at "
        f"{candidate} or {local_candidate}."
    )


def resolve_behavioural_jsonl(path: str | None, model_role: str) -> Path:
    """Resolve the behavioural JSONL used for contrast labels."""

    if path is not None:
        return Path(path)

    family_label = "qwen" if "qwen" in model_role else "llama"
    candidates = sorted(Path(DEFAULT_BEHAVIOURAL_DIR).glob(f"{family_label}_primary_*.jsonl"))
    if not candidates:
        raise FileNotFoundError(
            f"No behavioural JSONL matching role '{model_role}' under {DEFAULT_BEHAVIOURAL_DIR}."
        )
    return candidates[-1]


def load_logprob_table(path: Path) -> dict[str, dict[int, float]]:
    """Load per-variant correct-answer logprobs from one behavioural JSONL."""

    table: dict[str, dict[int, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if "variant_id" not in record:
                continue
            template_id = str(record["template_id"])
            variant_id = int(record["variant_id"])
            table.setdefault(template_id, {})[variant_id] = float(record["logprob_correct_answer"])
    return table


def canonicalize_expected_answer(raw_answer: str) -> str | None:
    """Canonicalize one template correct-answer string via the shared parser."""

    parsed = parse_answer(str(raw_answer))
    return parsed.answer if parsed.is_confident else None


def load_correctness_rate_table(
    *,
    family_rows: dict[str, dict[str, str]],
    behavioural_jsonl: Path,
    correctness_column: str | None,
) -> dict[str, float]:
    """Resolve per-family correctness rates from the CSV or behavioural JSONL."""

    if correctness_column:
        available_values = {
            template_id: row.get(correctness_column, "")
            for template_id, row in family_rows.items()
        }
        populated = {
            template_id: float(value)
            for template_id, value in available_values.items()
            if value not in ("", None)
        }
        if populated:
            return populated

    correct_counts: dict[str, int] = {}
    total_counts: dict[str, int] = {}
    expected_cache: dict[str, str | None] = {}
    with behavioural_jsonl.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") != "variant_record":
                continue
            template_id = str(record["template_id"])
            expected_answer = expected_cache.setdefault(
                template_id,
                canonicalize_expected_answer(str(record.get("correct_answer", ""))),
            )
            parsed_answer = record.get("parsed_answer_canonical")
            parse_confident = bool(record.get("parse_confident", False))
            total_counts[template_id] = total_counts.get(template_id, 0) + 1
            if parse_confident and expected_answer is not None and parsed_answer == expected_answer:
                correct_counts[template_id] = correct_counts.get(template_id, 0) + 1
    return {
        template_id: correct_counts.get(template_id, 0) / total_counts[template_id]
        for template_id in total_counts
        if total_counts[template_id] > 0
    }


def selected_variant_ids_for_n(
    variant_ids: list[int],
    variant_logprobs: dict[int, float] | None,
    *,
    n_variants: int,
) -> list[int]:
    """Choose which variant ids to use for one family-level variance feature."""

    ordered_variant_ids = sorted(variant_ids)
    if n_variants == 4:
        return ordered_variant_ids
    if n_variants == 3:
        return ordered_variant_ids[:3]
    if n_variants != 2:
        raise ValueError(f"Unsupported n_variants={n_variants}.")

    if variant_logprobs is None:
        raise ValueError(
            "n_variants=2 requires behavioural logprobs so the most-sensitive variant can be selected."
        )

    if 0 not in variant_logprobs:
        raise KeyError("Variant selection expects base variant id 0 in the behavioural logprob table.")

    base_logprob = float(variant_logprobs[0])
    candidate_ids = [variant_id for variant_id in ordered_variant_ids if variant_id != 0]
    if not candidate_ids:
        raise ValueError("n_variants=2 requires at least one non-base variant.")

    most_sensitive_variant_id = max(
        candidate_ids,
        key=lambda variant_id: base_logprob - float(variant_logprobs[variant_id]),
    )
    return [0, int(most_sensitive_variant_id)]


def parse_layer_filter(layer_filter: str | None, n_layers: int) -> list[int]:
    """Resolve the layer subset requested by the operator."""

    if layer_filter is None:
        return list(range(n_layers))

    layers = sorted({int(token.strip()) for token in layer_filter.split(",") if token.strip()})
    for layer_index in layers:
        if layer_index < 0 or layer_index >= n_layers:
            raise ValueError(f"Layer index {layer_index} is out of range for {n_layers} layers.")
    return layers


def group_variant_positions(entries: list[dict[str, Any]]) -> dict[str, list[tuple[int, int]]]:
    """Group manifest entries by family, preserving variant order."""

    grouped: dict[str, list[tuple[int, int]]] = {}
    for position, entry in enumerate(entries):
        grouped.setdefault(str(entry["template_id"]), []).append((position, int(entry["variant_id"])))
    for family_entries in grouped.values():
        family_entries.sort(key=lambda item: item[1])
    return grouped


def extract_template_ids(entries: list[dict[str, Any]]) -> list[str]:
    """Return template ids aligned with one entry list."""

    return [str(entry["template_id"]) for entry in entries]


def binary_labels_for_templates(
    template_ids: list[str],
    positive_families: frozenset[str],
) -> np.ndarray:
    """Return pre-registered binary S_lp labels for the requested families."""

    return np.asarray(
        [int(template_id in positive_families) for template_id in template_ids],
        dtype=int,
    )


def continuous_targets_for_templates(
    template_ids: list[str],
    *,
    family_rows: dict[str, dict[str, str]],
    model_role: str,
) -> np.ndarray:
    """Return continuous S_lp targets for the requested families."""

    sample_row = next(iter(family_rows.values()))
    if "qwen" in model_role:
        preferred_column = "qwen_S_lp"
        fallback_column = "qwen_S_lp_repair"
    elif "llama" in model_role:
        preferred_column = "llama_S_lp"
        fallback_column = "llama_S_lp_repair"
    elif "deepseek" in model_role:
        preferred_column = "deepseek_S_lp"
        fallback_column = "deepseek_S_lp_repair"
    else:
        raise ValueError(f"Unsupported model_role {model_role!r} for continuous S_lp targets.")
    column = preferred_column if preferred_column in sample_row else fallback_column
    return np.asarray([float(family_rows[template_id][column]) for template_id in template_ids], dtype=float)


def correctness_targets_for_templates(
    template_ids: list[str],
    *,
    correctness_rates: dict[str, float],
    threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return binary correctness labels plus raw correctness rates for one family list."""

    rates = np.asarray([float(correctness_rates[template_id]) for template_id in template_ids], dtype=float)
    labels = (rates >= threshold).astype(int)
    return labels, rates


def domain_labels_for_templates(
    template_ids: list[str],
    *,
    family_rows: dict[str, dict[str, str]],
) -> list[str]:
    """Return domain labels aligned with one family-id list."""

    return [str(family_rows[template_id]["domain"]) for template_id in template_ids]


def family_level_indices(template_ids: list[str]) -> tuple[list[str], np.ndarray]:
    """Return sorted unique family ids and per-example group indices."""

    families = sorted(set(template_ids))
    family_to_index = {template_id: index for index, template_id in enumerate(families)}
    groups = np.asarray([family_to_index[template_id] for template_id in template_ids], dtype=int)
    return families, groups


def aggregate_group_predictions(
    group_names: list[str],
    predictions: np.ndarray,
    labels: np.ndarray,
    *,
    aggregation_mode: str,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Aggregate example-level predictions into family-level scores."""

    unique_groups = sorted(set(group_names))
    family_scores: list[float] = []
    family_labels: list[int] = []
    prediction_array = np.asarray(predictions, dtype=float)
    label_array = np.asarray(labels, dtype=int)
    for family_id in unique_groups:
        mask = np.asarray([group_name == family_id for group_name in group_names], dtype=bool)
        group_predictions = prediction_array[mask]
        group_labels = label_array[mask]
        if aggregation_mode == AGGREGATE_MAX:
            family_scores.append(float(group_predictions.max()))
            family_labels.append(int(group_labels.max()))
        elif aggregation_mode == AGGREGATE_MEAN:
            family_scores.append(float(group_predictions.mean()))
            family_labels.append(int(group_labels[0]))
        else:
            raise ValueError(f"Unsupported aggregation mode '{aggregation_mode}'.")
    return unique_groups, np.asarray(family_scores, dtype=float), np.asarray(family_labels, dtype=int)


def fit_pca_projection(
    x_train: np.ndarray,
    x_eval: np.ndarray,
    pca_dims: int | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit a training-fold PCA and project both training and evaluation arrays."""

    if pca_dims is None:
        return x_train, x_eval

    max_dims = min(int(pca_dims), x_train.shape[0], x_train.shape[1])
    if max_dims < 1:
        raise ValueError(f"PCA dimensionality must remain positive after clipping, got {max_dims}.")

    projector = PCA(n_components=max_dims, random_state=DEFAULT_SEED)
    train_projected = projector.fit_transform(x_train)
    eval_projected = projector.transform(x_eval)
    return train_projected, eval_projected


def ensure_binary_class_support(labels: np.ndarray, *, context: str) -> None:
    """Require at least two classes before fitting any binary classification probe."""

    unique_labels = np.unique(labels)
    if unique_labels.size < 2:
        raise ValueError(
            f"{context} requires at least two classes, but only found labels={unique_labels.tolist()}."
        )


def choose_logistic_c(
    x_train: np.ndarray,
    y_train: np.ndarray,
    group_names: list[str],
    *,
    aggregation_mode: str,
    pca_dims: int | None,
    c_values: tuple[float, ...] = DEFAULT_C_VALUES,
) -> float:
    """Select the best logistic regularization strength by grouped AUROC."""

    ensure_binary_class_support(y_train, context="Logistic regularization selection")
    unique_groups = sorted(set(group_names))
    n_splits = min(5, len(unique_groups))
    if n_splits < 2:
        return 1.0

    splitter = GroupKFold(n_splits=n_splits)
    groups_array = np.asarray(group_names)
    best_c = c_values[0]
    best_score = -np.inf
    for c_value in c_values:
        fold_scores: list[float] = []
        for train_indices, val_indices in splitter.split(x_train, y_train, groups=groups_array):
            x_fold_train, x_fold_val = fit_pca_projection(
                x_train[train_indices],
                x_train[val_indices],
                pca_dims,
            )
            model = LogisticRegression(
                C=c_value,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=DEFAULT_SEED,
            )
            model.fit(x_fold_train, y_train[train_indices])
            val_scores = model.predict_proba(x_fold_val)[:, 1]
            val_group_names = [group_names[index] for index in val_indices]
            _, family_scores, family_labels = aggregate_group_predictions(
                val_group_names,
                val_scores,
                y_train[val_indices],
                aggregation_mode=aggregation_mode,
            )
            if len(np.unique(family_labels)) < 2:
                continue
            fold_scores.append(compute_auroc(family_labels, family_scores))
        mean_score = float(np.mean(fold_scores)) if fold_scores else -np.inf
        if mean_score > best_score:
            best_score = mean_score
            best_c = c_value
    return best_c


def domain_generalisation_folds(domains: list[str]) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Build held-out-domain train/test masks for domain generalisation."""

    unique_domains = sorted(set(domains))
    if len(unique_domains) < 2:
        raise ValueError(
            "Domain generalisation requires at least two domains, "
            f"but only found {unique_domains}."
        )

    domain_array = np.asarray(domains)
    folds: list[tuple[str, np.ndarray, np.ndarray]] = []
    for held_out_domain in unique_domains:
        test_mask = domain_array == held_out_domain
        train_mask = ~test_mask
        folds.append((held_out_domain, train_mask, test_mask))
    return folds


def fit_layerwise_ensemble_projection(
    train_tensor: np.ndarray,
    eval_tensor: np.ndarray,
    *,
    layers: list[int],
    pca_per_layer: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit one PCA per selected layer and concatenate the projections."""

    projected_train_parts: list[np.ndarray] = []
    projected_eval_parts: list[np.ndarray] = []
    for layer_index in layers:
        layer_train = train_tensor[:, layer_index, :]
        layer_eval = eval_tensor[:, layer_index, :]
        max_dims = min(int(pca_per_layer), layer_train.shape[0], layer_train.shape[1])
        if max_dims < 1:
            raise ValueError(
                f"Per-layer PCA dimensionality must remain positive after clipping, got {max_dims}."
            )
        projector = PCA(n_components=max_dims, random_state=DEFAULT_SEED)
        projected_train_parts.append(projector.fit_transform(layer_train))
        projected_eval_parts.append(projector.transform(layer_eval))
    return (
        np.concatenate(projected_train_parts, axis=1),
        np.concatenate(projected_eval_parts, axis=1),
    )


def choose_mlp_alpha(
    x_train: np.ndarray,
    y_train: np.ndarray,
    group_names: list[str],
    *,
    alpha_values: tuple[float, ...] = (1e-4, 1e-3, 1e-2),
) -> float:
    """Select an MLP regularisation strength by grouped AUROC."""

    ensure_binary_class_support(y_train, context="MLP alpha selection")
    unique_groups = sorted(set(group_names))
    n_splits = min(5, len(unique_groups))
    if n_splits < 2:
        return alpha_values[0]

    splitter = GroupKFold(n_splits=n_splits)
    groups_array = np.asarray(group_names)
    best_alpha = alpha_values[0]
    best_score = -np.inf
    for alpha in alpha_values:
        fold_scores: list[float] = []
        for train_indices, val_indices in splitter.split(x_train, y_train, groups=groups_array):
            pipeline = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "mlp",
                        MLPClassifier(
                            hidden_layer_sizes=DEFAULT_MLP_HIDDEN_LAYERS,
                            activation="relu",
                            alpha=alpha,
                            batch_size=min(32, len(train_indices)),
                            learning_rate_init=1e-3,
                            max_iter=800,
                            early_stopping=True,
                            n_iter_no_change=20,
                            random_state=DEFAULT_SEED,
                        ),
                    ),
                ]
            )
            pipeline.fit(x_train[train_indices], y_train[train_indices])
            val_scores = pipeline.predict_proba(x_train[val_indices])[:, 1]
            val_group_names = [group_names[index] for index in val_indices]
            _, family_scores, family_labels = aggregate_group_predictions(
                val_group_names,
                val_scores,
                y_train[val_indices],
                aggregation_mode=AGGREGATE_MEAN,
            )
            if len(np.unique(family_labels)) < 2:
                continue
            fold_scores.append(compute_auroc(family_labels, family_scores))
        mean_score = float(np.mean(fold_scores)) if fold_scores else -np.inf
        if mean_score > best_score:
            best_score = mean_score
            best_alpha = alpha
    return best_alpha


def run_layerwise_binary_loo_mean(
    tensors: np.ndarray,
    entries: list[dict[str, Any]],
    labels: np.ndarray,
    *,
    layer_indices: list[int],
    pca_dims: int | None,
    positive_families: frozenset[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run layer-wise family-level LOO logistic probing over family means."""

    ensure_binary_class_support(labels, context="Layer-wise mean probing")
    template_ids = extract_template_ids(entries)
    family_ids, family_groups = family_level_indices(template_ids)
    layer_summaries: list[dict[str, Any]] = []
    best_layer_predictions: list[dict[str, Any]] = []
    best_auroc = -np.inf

    for layer_index in layer_indices:
        x_layer = tensors[:, layer_index, :]
        family_prediction_rows: list[dict[str, Any]] = []
        for held_out_family in family_ids:
            test_mask = np.asarray([template_id == held_out_family for template_id in template_ids], dtype=bool)
            train_mask = ~test_mask
            x_train = x_layer[train_mask]
            y_train = labels[train_mask]
            train_groups = [template_ids[index] for index in np.where(train_mask)[0]]
            chosen_c = choose_logistic_c(
                x_train,
                y_train,
                train_groups,
                aggregation_mode=AGGREGATE_MEAN,
                pca_dims=pca_dims,
            )
            x_train_projected, x_test_projected = fit_pca_projection(
                x_train,
                x_layer[test_mask],
                pca_dims,
            )
            model = LogisticRegression(
                C=chosen_c,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=DEFAULT_SEED,
            )
            model.fit(x_train_projected, y_train)
            test_scores = model.predict_proba(x_test_projected)[:, 1]
            family_prediction_rows.append(
                {
                    "template_id": held_out_family,
                    "layer_index": layer_index,
                    "prediction": float(test_scores.mean()),
                    "true_label": int(held_out_family in positive_families),
                    "selected_c": chosen_c,
                }
            )

        ordered_predictions = sorted(family_prediction_rows, key=lambda item: item["template_id"])
        y_true = np.asarray([row["true_label"] for row in ordered_predictions], dtype=int)
        y_score = np.asarray([row["prediction"] for row in ordered_predictions], dtype=float)
        summary = {
            "layer_index": layer_index,
            "auroc": compute_auroc(y_true, y_score),
            "auprc": compute_auprc(y_true, y_score),
            "brier": compute_brier(y_true, y_score),
        }
        layer_summaries.append(summary)
        if summary["auroc"] > best_auroc:
            best_auroc = summary["auroc"]
            best_layer_predictions = ordered_predictions

    return layer_summaries, best_layer_predictions


def run_layerwise_continuous_loo_mean(
    tensors: np.ndarray,
    entries: list[dict[str, Any]],
    targets: np.ndarray,
    *,
    layer_indices: list[int],
    pca_dims: int | None,
) -> list[dict[str, Any]]:
    """Run layer-wise family-level LOO ridge regression on continuous S_lp."""

    template_ids = extract_template_ids(entries)
    family_ids, _ = family_level_indices(template_ids)
    layer_summaries: list[dict[str, Any]] = []
    for layer_index in layer_indices:
        x_layer = tensors[:, layer_index, :]
        family_predictions: list[float] = []
        family_targets: list[float] = []
        for held_out_family in family_ids:
            test_mask = np.asarray([template_id == held_out_family for template_id in template_ids], dtype=bool)
            train_mask = ~test_mask
            x_train_projected, x_test_projected = fit_pca_projection(
                x_layer[train_mask],
                x_layer[test_mask],
                pca_dims,
            )
            model = Ridge(alpha=DEFAULT_RIDGE_ALPHA)
            model.fit(x_train_projected, targets[train_mask])
            predicted = model.predict(x_test_projected)
            family_predictions.append(float(predicted.mean()))
            family_targets.append(float(targets[test_mask][0]))
        if np.std(family_predictions) == 0.0 or np.std(family_targets) == 0.0:
            pearson_r = 0.0
        else:
            pearson_r = float(np.corrcoef(family_targets, family_predictions)[0, 1])
        layer_summaries.append(
            {
                "layer_index": layer_index,
                "pearson_r": pearson_r,
                "rmse": float(
                    np.sqrt(np.mean((np.asarray(family_targets) - np.asarray(family_predictions)) ** 2))
                ),
            }
        )
    return layer_summaries


def build_contrast_dataset(
    tensors: np.ndarray,
    entries: list[dict[str, Any]],
    behavioural_logprobs: dict[str, dict[int, float]],
    *,
    pair_threshold: float,
) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
    """Build pairwise contrast examples and labels from family activations."""

    grouped = group_variant_positions(entries)
    contrast_entries: list[dict[str, Any]] = []
    contrast_tensors: list[np.ndarray] = []
    contrast_labels: list[int] = []

    for template_id, positions in sorted(grouped.items()):
        if len(positions) != 4:
            raise ValueError(f"Expected 4 variants for {template_id}, got {len(positions)}.")
        if template_id not in behavioural_logprobs:
            raise KeyError(f"Missing behavioural logprobs for family {template_id}.")
        for left_variant, right_variant in itertools.combinations(range(len(positions)), 2):
            left_position, left_variant_id = positions[left_variant]
            right_position, right_variant_id = positions[right_variant]
            left_logprob = behavioural_logprobs[template_id][left_variant_id]
            right_logprob = behavioural_logprobs[template_id][right_variant_id]
            contrast_entries.append(
                {
                    "template_id": template_id,
                    "pair_id": f"{left_variant_id}_{right_variant_id}",
                    "variant_left": left_variant_id,
                    "variant_right": right_variant_id,
                    "pair_logprob_delta": abs(left_logprob - right_logprob),
                }
            )
            contrast_tensors.append(tensors[left_position] - tensors[right_position])
            contrast_labels.append(int(abs(left_logprob - right_logprob) >= pair_threshold))

    return contrast_entries, np.stack(contrast_tensors, axis=0), np.asarray(contrast_labels, dtype=int)


def build_family_feature_tensors(
    tensors: np.ndarray,
    entries: list[dict[str, Any]],
    *,
    reducer: str,
    n_variants: int = 4,
    behavioural_logprobs: dict[str, dict[int, float]] | None = None,
) -> tuple[list[str], np.ndarray]:
    """Aggregate 4 variant tensors into one family-level feature tensor per family."""

    grouped = group_variant_positions(entries)
    family_ids = sorted(grouped)
    family_tensors: list[np.ndarray] = []
    for template_id in family_ids:
        positions = grouped[template_id]
        if len(positions) != 4:
            raise ValueError(f"Expected 4 variants for {template_id}, got {len(positions)}.")
        selected_variant_ids = selected_variant_ids_for_n(
            [variant_id for _, variant_id in positions],
            behavioural_logprobs.get(template_id) if behavioural_logprobs is not None else None,
            n_variants=n_variants,
        )
        selected_positions = [
            position for position, variant_id in positions if variant_id in set(selected_variant_ids)
        ]
        selected_positions.sort(key=lambda position: next(variant_id for p, variant_id in positions if p == position))
        variant_tensor = np.stack([tensors[position] for position in selected_positions], axis=0)
        if reducer == "mean":
            family_tensors.append(variant_tensor.mean(axis=0))
        elif reducer == "variance":
            family_tensors.append(variant_tensor.std(axis=0, ddof=0))
        else:
            raise ValueError(f"Unsupported family reducer '{reducer}'.")
    return family_ids, np.stack(family_tensors, axis=0)


def run_layerwise_binary_loo_family_features(
    feature_tensors: np.ndarray,
    family_ids: list[str],
    labels: np.ndarray,
    *,
    layer_indices: list[int],
    pca_dims: int | None,
    probe_type: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run layer-wise family-level LOO logistic probing over one feature tensor per family."""

    del probe_type
    ensure_binary_class_support(labels, context="Layer-wise family-feature probing")
    layer_summaries: list[dict[str, Any]] = []
    best_layer_predictions: list[dict[str, Any]] = []
    best_auroc = -np.inf

    for layer_index in layer_indices:
        x_layer = feature_tensors[:, layer_index, :]
        family_prediction_rows: list[dict[str, Any]] = []
        for held_out_index, held_out_family in enumerate(family_ids):
            test_mask = np.asarray([index == held_out_index for index in range(len(family_ids))], dtype=bool)
            train_mask = ~test_mask
            x_train = x_layer[train_mask]
            y_train = labels[train_mask]
            train_groups = [family_ids[index] for index in np.where(train_mask)[0]]
            chosen_c = choose_logistic_c(
                x_train,
                y_train,
                train_groups,
                aggregation_mode=AGGREGATE_MEAN,
                pca_dims=pca_dims,
            )
            x_train_projected, x_test_projected = fit_pca_projection(
                x_train,
                x_layer[test_mask],
                pca_dims,
            )
            model = LogisticRegression(
                C=chosen_c,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=DEFAULT_SEED,
            )
            model.fit(x_train_projected, y_train)
            test_scores = model.predict_proba(x_test_projected)[:, 1]
            family_prediction_rows.append(
                {
                    "template_id": held_out_family,
                    "layer_index": layer_index,
                    "prediction": float(test_scores[0]),
                    "true_label": int(labels[held_out_index]),
                    "selected_c": chosen_c,
                }
            )

        ordered_predictions = sorted(family_prediction_rows, key=lambda item: item["template_id"])
        y_true = np.asarray([row["true_label"] for row in ordered_predictions], dtype=int)
        y_score = np.asarray([row["prediction"] for row in ordered_predictions], dtype=float)
        summary = {
            "layer_index": layer_index,
            "auroc": compute_auroc(y_true, y_score),
            "auprc": compute_auprc(y_true, y_score),
            "brier": compute_brier(y_true, y_score),
        }
        layer_summaries.append(summary)
        if summary["auroc"] > best_auroc:
            best_auroc = summary["auroc"]
            best_layer_predictions = ordered_predictions

    return layer_summaries, best_layer_predictions


def run_layerwise_continuous_loo_family_features(
    feature_tensors: np.ndarray,
    family_ids: list[str],
    targets: np.ndarray,
    *,
    layer_indices: list[int],
    pca_dims: int | None,
) -> list[dict[str, Any]]:
    """Run layer-wise family-level LOO ridge regression over one feature tensor per family."""

    layer_summaries: list[dict[str, Any]] = []
    for layer_index in layer_indices:
        x_layer = feature_tensors[:, layer_index, :]
        family_predictions: list[float] = []
        family_targets: list[float] = []
        for held_out_index, _held_out_family in enumerate(family_ids):
            test_mask = np.asarray([index == held_out_index for index in range(len(family_ids))], dtype=bool)
            train_mask = ~test_mask
            x_train_projected, x_test_projected = fit_pca_projection(
                x_layer[train_mask],
                x_layer[test_mask],
                pca_dims,
            )
            model = Ridge(alpha=DEFAULT_RIDGE_ALPHA)
            model.fit(x_train_projected, targets[train_mask])
            predicted = model.predict(x_test_projected)
            family_predictions.append(float(predicted[0]))
            family_targets.append(float(targets[held_out_index]))
        if np.std(family_predictions) == 0.0 or np.std(family_targets) == 0.0:
            pearson_r = 0.0
        else:
            pearson_r = float(np.corrcoef(family_targets, family_predictions)[0, 1])
        layer_summaries.append(
            {
                "layer_index": layer_index,
                "pearson_r": pearson_r,
                "rmse": float(
                    np.sqrt(np.mean((np.asarray(family_targets) - np.asarray(family_predictions)) ** 2))
                ),
            }
        )
    return layer_summaries


def run_domain_generalisation_binary_family_features(
    feature_tensors: np.ndarray,
    family_ids: list[str],
    labels: np.ndarray,
    *,
    family_rows: dict[str, dict[str, str]],
    layer_indices: list[int],
    pca_dims: int | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Run held-out-domain binary probing over one feature tensor per family."""

    ensure_binary_class_support(labels, context="Domain generalisation family-feature probing")
    domains = domain_labels_for_templates(family_ids, family_rows=family_rows)
    folds = domain_generalisation_folds(domains)
    layer_summaries: list[dict[str, Any]] = []
    best_predictions: list[dict[str, Any]] = []
    best_fold_metrics: list[dict[str, Any]] = []
    best_auroc = -np.inf

    for layer_index in layer_indices:
        x_layer = feature_tensors[:, layer_index, :]
        prediction_rows: list[dict[str, Any]] = []
        fold_metrics: list[dict[str, Any]] = []
        for held_out_domain, train_mask, test_mask in folds:
            x_train = x_layer[train_mask]
            y_train = labels[train_mask]
            x_test = x_layer[test_mask]
            y_test = labels[test_mask]
            test_family_ids = [family_ids[index] for index in np.where(test_mask)[0]]
            train_groups = [family_ids[index] for index in np.where(train_mask)[0]]
            chosen_c = choose_logistic_c(
                x_train,
                y_train,
                train_groups,
                aggregation_mode=AGGREGATE_MEAN,
                pca_dims=pca_dims,
            )
            x_train_projected, x_test_projected = fit_pca_projection(x_train, x_test, pca_dims)
            model = LogisticRegression(
                C=chosen_c,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=DEFAULT_SEED,
            )
            model.fit(x_train_projected, y_train)
            test_scores = model.predict_proba(x_test_projected)[:, 1]
            if len(np.unique(y_test)) >= 2:
                fold_metrics.append(
                    {
                        "held_out_domain": held_out_domain,
                        "layer_index": layer_index,
                        "auroc": compute_auroc(y_test, test_scores),
                        "auprc": compute_auprc(y_test, test_scores),
                        "positive_rate": float(y_test.mean()),
                        "selected_c": chosen_c,
                    }
                )
            for family_id, score, true_label in zip(test_family_ids, test_scores, y_test, strict=True):
                prediction_rows.append(
                    {
                        "template_id": family_id,
                        "layer_index": layer_index,
                        "prediction": float(score),
                        "true_label": int(true_label),
                        "held_out_domain": held_out_domain,
                        "selected_c": chosen_c,
                    }
                )

        ordered_predictions = sorted(prediction_rows, key=lambda item: item["template_id"])
        y_true = np.asarray([row["true_label"] for row in ordered_predictions], dtype=int)
        y_score = np.asarray([row["prediction"] for row in ordered_predictions], dtype=float)
        summary = {
            "layer_index": layer_index,
            "auroc": compute_auroc(y_true, y_score),
            "auprc": compute_auprc(y_true, y_score),
            "brier": compute_brier(y_true, y_score),
        }
        layer_summaries.append(summary)
        if summary["auroc"] > best_auroc:
            best_auroc = summary["auroc"]
            best_predictions = ordered_predictions
            best_fold_metrics = fold_metrics
    return layer_summaries, best_predictions, best_fold_metrics


def run_variance_ensemble_loo(
    feature_tensors: np.ndarray,
    family_ids: list[str],
    labels: np.ndarray,
    *,
    ensemble_layers: list[int],
    pca_per_layer: int,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Run LOO probing on concatenated per-layer variance PCA features."""

    ensure_binary_class_support(labels, context="Variance ensemble LOO probing")
    prediction_rows: list[dict[str, Any]] = []
    for held_out_index, held_out_family in enumerate(family_ids):
        test_mask = np.asarray([index == held_out_index for index in range(len(family_ids))], dtype=bool)
        train_mask = ~test_mask
        x_train, x_test = fit_layerwise_ensemble_projection(
            feature_tensors[train_mask],
            feature_tensors[test_mask],
            layers=ensemble_layers,
            pca_per_layer=pca_per_layer,
        )
        y_train = labels[train_mask]
        train_groups = [family_ids[index] for index in np.where(train_mask)[0]]
        chosen_c = choose_logistic_c(
            x_train,
            y_train,
            train_groups,
            aggregation_mode=AGGREGATE_MEAN,
            pca_dims=None,
        )
        model = LogisticRegression(
            C=chosen_c,
            class_weight="balanced",
            max_iter=2000,
            solver="liblinear",
            random_state=DEFAULT_SEED,
        )
        model.fit(x_train, y_train)
        score = float(model.predict_proba(x_test)[:, 1][0])
        prediction_rows.append(
            {
                "template_id": held_out_family,
                "prediction": score,
                "true_label": int(labels[held_out_index]),
                "selected_c": chosen_c,
            }
        )

    ordered_predictions = sorted(prediction_rows, key=lambda item: item["template_id"])
    y_true = np.asarray([row["true_label"] for row in ordered_predictions], dtype=int)
    y_score = np.asarray([row["prediction"] for row in ordered_predictions], dtype=float)
    summary = {
        "auroc": compute_auroc(y_true, y_score),
        "auprc": compute_auprc(y_true, y_score),
        "brier": compute_brier(y_true, y_score),
    }
    return summary, ordered_predictions


def run_variance_ensemble_domain_generalisation(
    feature_tensors: np.ndarray,
    family_ids: list[str],
    labels: np.ndarray,
    *,
    family_rows: dict[str, dict[str, str]],
    ensemble_layers: list[int],
    pca_per_layer: int,
) -> tuple[dict[str, float], list[dict[str, Any]], list[dict[str, Any]]]:
    """Run held-out-domain probing on concatenated per-layer variance PCA features."""

    ensure_binary_class_support(labels, context="Variance ensemble domain generalisation")
    domains = domain_labels_for_templates(family_ids, family_rows=family_rows)
    folds = domain_generalisation_folds(domains)
    prediction_rows: list[dict[str, Any]] = []
    fold_metrics: list[dict[str, Any]] = []

    for held_out_domain, train_mask, test_mask in folds:
        x_train, x_test = fit_layerwise_ensemble_projection(
            feature_tensors[train_mask],
            feature_tensors[test_mask],
            layers=ensemble_layers,
            pca_per_layer=pca_per_layer,
        )
        y_train = labels[train_mask]
        y_test = labels[test_mask]
        test_family_ids = [family_ids[index] for index in np.where(test_mask)[0]]
        train_groups = [family_ids[index] for index in np.where(train_mask)[0]]
        chosen_c = choose_logistic_c(
            x_train,
            y_train,
            train_groups,
            aggregation_mode=AGGREGATE_MEAN,
            pca_dims=None,
        )
        model = LogisticRegression(
            C=chosen_c,
            class_weight="balanced",
            max_iter=2000,
            solver="liblinear",
            random_state=DEFAULT_SEED,
        )
        model.fit(x_train, y_train)
        scores = model.predict_proba(x_test)[:, 1]
        if len(np.unique(y_test)) >= 2:
            fold_metrics.append(
                {
                    "held_out_domain": held_out_domain,
                    "auroc": compute_auroc(y_test, scores),
                    "auprc": compute_auprc(y_test, scores),
                    "positive_rate": float(y_test.mean()),
                    "selected_c": chosen_c,
                }
            )
        for family_id, score, true_label in zip(test_family_ids, scores, y_test, strict=True):
            prediction_rows.append(
                {
                    "template_id": family_id,
                    "prediction": float(score),
                    "true_label": int(true_label),
                    "held_out_domain": held_out_domain,
                    "selected_c": chosen_c,
                }
            )

    ordered_predictions = sorted(prediction_rows, key=lambda item: item["template_id"])
    y_true = np.asarray([row["true_label"] for row in ordered_predictions], dtype=int)
    y_score = np.asarray([row["prediction"] for row in ordered_predictions], dtype=float)
    summary = {
        "auroc": compute_auroc(y_true, y_score),
        "auprc": compute_auprc(y_true, y_score),
        "brier": compute_brier(y_true, y_score),
    }
    return summary, ordered_predictions, fold_metrics


def run_variance_mlp_loo(
    feature_tensors: np.ndarray,
    family_ids: list[str],
    labels: np.ndarray,
    *,
    layer_indices: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run layer-wise LOO probing with a small MLP over variance features."""

    ensure_binary_class_support(labels, context="Variance MLP probing")
    layer_summaries: list[dict[str, Any]] = []
    best_layer_predictions: list[dict[str, Any]] = []
    best_auroc = -np.inf

    for layer_index in layer_indices:
        x_layer = feature_tensors[:, layer_index, :]
        prediction_rows: list[dict[str, Any]] = []
        for held_out_index, held_out_family in enumerate(family_ids):
            test_mask = np.asarray([index == held_out_index for index in range(len(family_ids))], dtype=bool)
            train_mask = ~test_mask
            x_train = x_layer[train_mask]
            y_train = labels[train_mask]
            train_groups = [family_ids[index] for index in np.where(train_mask)[0]]
            chosen_alpha = choose_mlp_alpha(x_train, y_train, train_groups)
            pipeline = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "mlp",
                        MLPClassifier(
                            hidden_layer_sizes=DEFAULT_MLP_HIDDEN_LAYERS,
                            activation="relu",
                            alpha=chosen_alpha,
                            batch_size=min(32, x_train.shape[0]),
                            learning_rate_init=1e-3,
                            max_iter=800,
                            early_stopping=True,
                            n_iter_no_change=20,
                            random_state=DEFAULT_SEED,
                        ),
                    ),
                ]
            )
            pipeline.fit(x_train, y_train)
            score = float(pipeline.predict_proba(x_layer[test_mask])[:, 1][0])
            prediction_rows.append(
                {
                    "template_id": held_out_family,
                    "layer_index": layer_index,
                    "prediction": score,
                    "true_label": int(labels[held_out_index]),
                    "selected_alpha": chosen_alpha,
                }
            )

        ordered_predictions = sorted(prediction_rows, key=lambda item: item["template_id"])
        y_true = np.asarray([row["true_label"] for row in ordered_predictions], dtype=int)
        y_score = np.asarray([row["prediction"] for row in ordered_predictions], dtype=float)
        summary = {
            "layer_index": layer_index,
            "auroc": compute_auroc(y_true, y_score),
            "auprc": compute_auprc(y_true, y_score),
            "brier": compute_brier(y_true, y_score),
        }
        layer_summaries.append(summary)
        if summary["auroc"] > best_auroc:
            best_auroc = summary["auroc"]
            best_layer_predictions = ordered_predictions
    return layer_summaries, best_layer_predictions


def run_layerwise_binary_loo_contrast(
    contrast_tensors: np.ndarray,
    contrast_entries: list[dict[str, Any]],
    contrast_labels: np.ndarray,
    *,
    layer_indices: list[int],
    pca_dims: int | None,
    positive_families: frozenset[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run layer-wise family-level LOO logistic probing over contrast vectors."""

    ensure_binary_class_support(contrast_labels, context="Layer-wise contrast probing")
    template_ids = [str(entry["template_id"]) for entry in contrast_entries]
    family_ids, _ = family_level_indices(template_ids)
    layer_summaries: list[dict[str, Any]] = []
    best_layer_predictions: list[dict[str, Any]] = []
    best_auroc = -np.inf

    for layer_index in layer_indices:
        x_layer = contrast_tensors[:, layer_index, :]
        family_prediction_rows: list[dict[str, Any]] = []
        for held_out_family in family_ids:
            test_mask = np.asarray([template_id == held_out_family for template_id in template_ids], dtype=bool)
            train_mask = ~test_mask
            x_train = x_layer[train_mask]
            y_train = contrast_labels[train_mask]
            train_groups = [template_ids[index] for index in np.where(train_mask)[0]]
            chosen_c = choose_logistic_c(
                x_train,
                y_train,
                train_groups,
                aggregation_mode=AGGREGATE_MAX,
                pca_dims=pca_dims,
            )
            x_train_projected, x_test_projected = fit_pca_projection(
                x_train,
                x_layer[test_mask],
                pca_dims,
            )
            model = LogisticRegression(
                C=chosen_c,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=DEFAULT_SEED,
            )
            model.fit(x_train_projected, y_train)
            test_scores = model.predict_proba(x_test_projected)[:, 1]
            family_prediction_rows.append(
                {
                    "template_id": held_out_family,
                    "layer_index": layer_index,
                    "prediction": float(test_scores.max()),
                    "true_label": int(held_out_family in positive_families),
                    "selected_c": chosen_c,
                }
            )

        ordered_predictions = sorted(family_prediction_rows, key=lambda item: item["template_id"])
        y_true = np.asarray([row["true_label"] for row in ordered_predictions], dtype=int)
        y_score = np.asarray([row["prediction"] for row in ordered_predictions], dtype=float)
        summary = {
            "layer_index": layer_index,
            "auroc": compute_auroc(y_true, y_score),
            "auprc": compute_auprc(y_true, y_score),
            "brier": compute_brier(y_true, y_score),
        }
        layer_summaries.append(summary)
        if summary["auroc"] > best_auroc:
            best_auroc = summary["auroc"]
            best_layer_predictions = ordered_predictions

    return layer_summaries, best_layer_predictions


def bootstrap_auroc_ci(y_true: np.ndarray, y_score: np.ndarray, draws: int = 1000) -> dict[str, float]:
    """Bootstrap a family-level AUROC confidence interval."""

    rng = np.random.default_rng(DEFAULT_SEED)
    values: list[float] = []
    indices = np.arange(y_true.shape[0])
    for _ in range(draws):
        sample_indices = rng.choice(indices, size=indices.size, replace=True)
        sample_y = y_true[sample_indices]
        sample_scores = y_score[sample_indices]
        if len(np.unique(sample_y)) < 2:
            continue
        values.append(compute_auroc(sample_y, sample_scores))
    if not values:
        return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "ci_lower": float(np.quantile(array, 0.025)),
        "ci_upper": float(np.quantile(array, 0.975)),
    }


def random_direction_baseline(
    tensors: np.ndarray,
    template_ids: list[str],
    labels: np.ndarray,
    layer_index: int,
    *,
    aggregation_mode: str,
    draws: int = DEFAULT_RANDOM_BASELINE_DRAWS,
) -> dict[str, float]:
    """Estimate a norm-matched random-direction AUROC null for one layer."""

    rng = np.random.default_rng(DEFAULT_SEED)
    x_layer = tensors[:, layer_index, :]
    aurocs: list[float] = []
    for _ in range(draws):
        direction = rng.normal(size=x_layer.shape[1])
        direction /= np.linalg.norm(direction) + 1e-12
        example_scores = x_layer @ direction
        group_ids, family_scores, family_labels = aggregate_group_predictions(
            template_ids,
            1.0 / (1.0 + np.exp(-example_scores)),
            labels,
            aggregation_mode=aggregation_mode,
        )
        del group_ids
        aurocs.append(compute_auroc(family_labels, family_scores))
    array = np.asarray(aurocs, dtype=float)
    return {
        "mean_auroc": float(array.mean()),
        "p95_auroc": float(np.quantile(array, 0.95)),
    }


def plot_layer_curve(
    layer_binary: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """Plot AUROC versus layer depth."""

    import matplotlib.pyplot as plt

    layers = [entry["layer_index"] for entry in layer_binary]
    aurocs = [entry["auroc"] for entry in layer_binary]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(layers, aurocs, marker="o")
    axis.set_xlabel("Layer")
    axis.set_ylabel("LOO AUROC")
    axis.set_title("Stage 5 Probe AUROC by Layer")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def save_json(path: Path, payload: Any) -> None:
    """Write JSON with stable formatting for list or mapping payloads."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cross_model_validation(
    *,
    source_tensors: np.ndarray,
    source_template_ids: list[str],
    target_tensors: np.ndarray,
    target_template_ids: list[str],
    best_layer: int,
    best_c: float,
    target_family_rows: dict[str, dict[str, str]],
    target_role: str,
    positive_families: frozenset[str],
    positive_threshold: float,
) -> dict[str, Any]:
    """Fit on all source activations and evaluate on target-model family labels."""

    source_dim = int(source_tensors.shape[2])
    target_dim = int(target_tensors.shape[2])
    if source_dim != target_dim:
        return {
            "status": "skipped",
            "reason": (
                "raw-space cross-model validation requires matching activation dimensions; "
                f"got source_dim={source_dim} and target_dim={target_dim}"
            ),
            "source_dim": float(source_dim),
            "target_dim": float(target_dim),
        }

    source_labels = binary_labels_for_templates(source_template_ids, positive_families)
    model = LogisticRegression(
        C=best_c,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=DEFAULT_SEED,
    )
    model.fit(source_tensors[:, best_layer, :], source_labels)
    target_variant_scores = model.predict_proba(target_tensors[:, best_layer, :])[:, 1]
    _, target_family_scores, _ = aggregate_group_predictions(
        target_template_ids,
        target_variant_scores,
        binary_labels_for_templates(target_template_ids, positive_families),
        aggregation_mode=AGGREGATE_MEAN,
    )
    target_family_ids = sorted(set(target_template_ids))
    sample_row = next(iter(target_family_rows.values()))
    if "qwen" in target_role:
        preferred_column = "qwen_S_lp"
        fallback_column = "qwen_S_lp_repair"
    elif "llama" in target_role:
        preferred_column = "llama_S_lp"
        fallback_column = "llama_S_lp_repair"
    elif "deepseek" in target_role:
        preferred_column = "deepseek_S_lp"
        fallback_column = "deepseek_S_lp_repair"
    else:
        raise ValueError(f"Unsupported target_role {target_role!r} for cross-model validation.")
    target_column = preferred_column if preferred_column in sample_row else fallback_column
    target_labels = np.asarray(
        [
            int(float(target_family_rows[family_id][target_column]) >= positive_threshold)
            for family_id in target_family_ids
        ],
        dtype=int,
    )
    return {
        "status": "ok",
        "auroc": compute_auroc(target_labels, target_family_scores),
        "positive_rate": float(target_labels.mean()),
        "source_dim": float(source_dim),
        "target_dim": float(target_dim),
    }


def artifact_stem(site: str, probe_type: str, pca_dims: int | None) -> str:
    """Resolve the output artifact stem for this run."""

    if probe_type == "contrast":
        return "contrast"
    if probe_type == "variance":
        return "variance"
    if probe_type == "variance_ensemble":
        return "variance_ensemble"
    if probe_type == "variance_mlp":
        return "variance_mlp"
    if pca_dims is not None:
        return f"pca{pca_dims}"
    return site


def main() -> None:
    """Run Stage 5 probing over extracted activation tensors."""

    args = parse_args()
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_probing.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
        model_role=args.model_role,
    )

    family_rows = load_per_family_rows(Path(args.family_csv))
    positive_families, positive_threshold = infer_positive_families(
        family_csv=Path(args.family_csv),
        positive_families_file=Path(args.positive_families_file)
        if args.positive_families_file
        else None,
    )
    entries, tensors = load_site_tensors(Path(args.activation_dir), args.site)
    entries, tensors = filter_entries_and_tensors(
        entries,
        tensors,
        family_rows=family_rows,
        exclude_ids=set(args.exclude_ids),
        exclude_cue_type=args.exclude_cue_type,
        cue_type=args.cue_type,
        pilot_only=args.pilot_only,
    )
    layer_indices = parse_layer_filter(args.layer_filter, tensors.shape[1])
    template_ids = extract_template_ids(entries)
    stem = artifact_stem(args.site, args.probe_type, args.pca_dims)
    if args.probe_type == "variance" and args.n_variants != 4:
        stem = f"{stem}_n{args.n_variants}"

    behavioural_logprobs = None
    if args.probe_type == "variance" and args.n_variants != 4:
        behavioural_path = resolve_behavioural_jsonl(args.behavioural_jsonl, args.model_role)
        behavioural_logprobs = load_logprob_table(behavioural_path)
    elif args.target_measure == "answer_correctness":
        behavioural_path = resolve_behavioural_jsonl(args.behavioural_jsonl, args.model_role)
    else:
        behavioural_path = None

    correctness_rates = None
    if args.target_measure == "answer_correctness":
        if behavioural_path is None:
            raise ValueError("answer_correctness target requires a behavioural JSONL.")
        correctness_rates = load_correctness_rate_table(
            family_rows=family_rows,
            behavioural_jsonl=behavioural_path,
            correctness_column=args.correctness_column,
        )

    if args.probe_type == "variance_ensemble":
        family_ids, feature_tensors = build_family_feature_tensors(tensors, entries, reducer="variance")
        if args.target_measure == "answer_correctness":
            binary_labels, continuous_targets = correctness_targets_for_templates(
                family_ids,
                correctness_rates=correctness_rates,
                threshold=args.correctness_threshold,
            )
        else:
            binary_labels = binary_labels_for_templates(family_ids, positive_families)
            continuous_targets = continuous_targets_for_templates(
                family_ids,
                family_rows=family_rows,
                model_role=args.model_role,
            )
        ensemble_layers = sorted(set(args.ensemble_layers))
        for layer_index in ensemble_layers:
            if layer_index < 0 or layer_index >= feature_tensors.shape[1]:
                raise ValueError(
                    f"Ensemble layer index {layer_index} is out of range for {feature_tensors.shape[1]} layers."
                )
        if args.cv_mode == DEFAULT_DOMAIN_GENERALISATION_MODE:
            ensemble_summary, best_predictions, fold_metrics = run_variance_ensemble_domain_generalisation(
                feature_tensors,
                family_ids,
                binary_labels,
                family_rows=family_rows,
                ensemble_layers=ensemble_layers,
                pca_per_layer=args.pca_per_layer,
            )
        else:
            ensemble_summary, best_predictions = run_variance_ensemble_loo(
                feature_tensors,
                family_ids,
                binary_labels,
                ensemble_layers=ensemble_layers,
                pca_per_layer=args.pca_per_layer,
            )
            fold_metrics = []

        ordered_best_predictions = sorted(best_predictions, key=lambda item: item["template_id"])
        best_labels = np.asarray([row["true_label"] for row in ordered_best_predictions], dtype=int)
        best_scores = np.asarray([row["prediction"] for row in ordered_best_predictions], dtype=float)
        bootstrap_summary = bootstrap_auroc_ci(best_labels, best_scores)
        best_layer = int(ensemble_layers[len(ensemble_layers) // 2])
        random_baseline = random_direction_baseline(
            feature_tensors,
            family_ids,
            binary_labels,
            layer_index=best_layer,
            aggregation_mode=AGGREGATE_MEAN,
        )
        summary_payload = {
            "model_role": args.model_role,
            "site": args.site,
            "probe_type": args.probe_type,
            "target_measure": args.target_measure,
            "cv_mode": args.cv_mode,
            "ensemble_layers": ensemble_layers,
            "pca_per_layer": args.pca_per_layer,
            "best_layer": best_layer,
            "best_auroc": float(ensemble_summary["auroc"]),
            "best_auprc": float(ensemble_summary["auprc"]),
            "best_brier": float(ensemble_summary["brier"]),
            "best_pearson_r": (
                None
                if args.target_measure in {"slp_binary", "answer_correctness"}
                else float(np.corrcoef(continuous_targets, best_scores)[0, 1])
            ),
            "bootstrap_auroc": bootstrap_summary,
            "random_direction_baseline": random_baseline,
            "embedding_layer_auroc": None,
            "cross_model_validation": None,
            "domain_fold_metrics": fold_metrics,
        }
        save_json(output_dir / f"loo_predictions_{stem}.json", ordered_best_predictions)
        save_json(output_dir / f"summary_{stem}.json", summary_payload)
    elif args.probe_type == "variance_mlp":
        if args.cv_mode != "loo":
            raise ValueError("variance_mlp currently supports only --cv-mode loo.")
        family_ids, feature_tensors = build_family_feature_tensors(tensors, entries, reducer="variance")
        binary_labels = binary_labels_for_templates(family_ids, positive_families)
        layer_binary, best_predictions = run_variance_mlp_loo(
            feature_tensors,
            family_ids,
            binary_labels,
            layer_indices=layer_indices,
        )
        best_binary = max(layer_binary, key=lambda item: item["auroc"])
        plot_layer_curve(layer_binary, output_dir / f"layer_auroc_curve_{stem}.png")
        ordered_best_predictions = sorted(best_predictions, key=lambda item: item["template_id"])
        best_labels = np.asarray([row["true_label"] for row in ordered_best_predictions], dtype=int)
        best_scores = np.asarray([row["prediction"] for row in ordered_best_predictions], dtype=float)
        bootstrap_summary = bootstrap_auroc_ci(best_labels, best_scores)
        random_baseline = random_direction_baseline(
            feature_tensors,
            family_ids,
            binary_labels,
            layer_index=int(best_binary["layer_index"]),
            aggregation_mode=AGGREGATE_MEAN,
        )
        embedding_layer_auroc = next(
            (float(item["auroc"]) for item in layer_binary if item["layer_index"] == 0),
            None,
        )
        summary_payload = {
            "model_role": args.model_role,
            "site": args.site,
            "probe_type": args.probe_type,
            "target_measure": args.target_measure,
            "cv_mode": args.cv_mode,
            "evaluated_layers": layer_indices,
            "best_layer": int(best_binary["layer_index"]),
            "best_auroc": float(best_binary["auroc"]),
            "best_auprc": float(best_binary["auprc"]),
            "best_brier": float(best_binary["brier"]),
            "best_pearson_r": None,
            "bootstrap_auroc": bootstrap_summary,
            "random_direction_baseline": random_baseline,
            "embedding_layer_auroc": embedding_layer_auroc,
            "cross_model_validation": None,
        }
        save_json(output_dir / f"layer_auroc_{stem}.json", layer_binary)
        save_json(output_dir / f"loo_predictions_{stem}.json", ordered_best_predictions)
        save_json(output_dir / f"summary_{stem}.json", summary_payload)
    elif args.probe_type == "contrast":
        if args.target_measure != "slp_binary":
            raise ValueError("Contrast probing currently supports only --target-measure slp_binary.")
        behavioural_path = resolve_behavioural_jsonl(args.behavioural_jsonl, args.model_role)
        behavioural_logprobs = load_logprob_table(behavioural_path)
        contrast_entries, contrast_tensors, contrast_labels = build_contrast_dataset(
            tensors,
            entries,
            behavioural_logprobs,
            pair_threshold=args.pair_threshold,
        )
        contrast_template_ids = [str(entry["template_id"]) for entry in contrast_entries]
        layer_binary, best_predictions = run_layerwise_binary_loo_contrast(
            contrast_tensors,
            contrast_entries,
            contrast_labels,
            layer_indices=layer_indices,
            pca_dims=args.pca_dims,
            positive_families=positive_families,
        )
        best_binary = max(layer_binary, key=lambda item: item["auroc"])
        plot_layer_curve(layer_binary, output_dir / f"layer_auroc_curve_{stem}.png")
        ordered_best_predictions = sorted(best_predictions, key=lambda item: item["template_id"])
        best_labels = np.asarray([row["true_label"] for row in ordered_best_predictions], dtype=int)
        best_scores = np.asarray([row["prediction"] for row in ordered_best_predictions], dtype=float)
        bootstrap_summary = bootstrap_auroc_ci(best_labels, best_scores)
        random_baseline = random_direction_baseline(
            contrast_tensors,
            contrast_template_ids,
            contrast_labels,
            int(best_binary["layer_index"]),
            aggregation_mode=AGGREGATE_MAX,
        )
        embedding_layer_auroc = next(
            (float(item["auroc"]) for item in layer_binary if item["layer_index"] == 0),
            None,
        )
        summary_payload: dict[str, Any] = {
            "model_role": args.model_role,
            "site": args.site,
            "probe_type": args.probe_type,
            "target_measure": args.target_measure,
            "pca_dims": args.pca_dims,
            "pair_threshold": args.pair_threshold,
            "behavioural_jsonl": str(behavioural_path),
            "evaluated_layers": layer_indices,
            "best_layer": int(best_binary["layer_index"]),
            "best_auroc": float(best_binary["auroc"]),
            "best_auprc": float(best_binary["auprc"]),
            "best_brier": float(best_binary["brier"]),
            "best_pearson_r": None,
            "bootstrap_auroc": bootstrap_summary,
            "random_direction_baseline": random_baseline,
            "embedding_layer_auroc": embedding_layer_auroc,
            "cross_model_validation": None,
        }
        save_json(output_dir / f"layer_auroc_{stem}.json", layer_binary)
        save_json(output_dir / f"loo_predictions_{stem}.json", ordered_best_predictions)
        save_json(output_dir / f"summary_{stem}.json", summary_payload)
    elif args.probe_type == "variance":
        family_ids, feature_tensors = build_family_feature_tensors(
            tensors,
            entries,
            reducer="variance",
            n_variants=args.n_variants,
            behavioural_logprobs=behavioural_logprobs,
        )
        if args.target_measure == "answer_correctness":
            binary_labels, continuous_targets = correctness_targets_for_templates(
                family_ids,
                correctness_rates=correctness_rates,
                threshold=args.correctness_threshold,
            )
        else:
            binary_labels = binary_labels_for_templates(family_ids, positive_families)
            continuous_targets = continuous_targets_for_templates(
                family_ids,
                family_rows=family_rows,
                model_role=args.model_role,
            )
        if args.cv_mode == DEFAULT_DOMAIN_GENERALISATION_MODE:
            layer_binary, best_predictions, fold_metrics = run_domain_generalisation_binary_family_features(
                feature_tensors,
                family_ids,
                binary_labels,
                family_rows=family_rows,
                layer_indices=layer_indices,
                pca_dims=args.pca_dims,
            )
        else:
            layer_binary, best_predictions = run_layerwise_binary_loo_family_features(
                feature_tensors,
                family_ids,
                binary_labels,
                layer_indices=layer_indices,
                pca_dims=args.pca_dims,
                probe_type=args.probe_type,
            )
            fold_metrics = []
        layer_continuous: list[dict[str, Any]] = []
        if args.target_measure != "answer_correctness":
            layer_continuous = run_layerwise_continuous_loo_family_features(
                feature_tensors,
                family_ids,
                continuous_targets,
                layer_indices=layer_indices,
                pca_dims=args.pca_dims,
            )
        best_binary = max(layer_binary, key=lambda item: item["auroc"])
        best_continuous = (
            max(layer_continuous, key=lambda item: item["pearson_r"])
            if layer_continuous
            else None
        )
        plot_layer_curve(layer_binary, output_dir / f"layer_auroc_curve_{stem}.png")

        ordered_best_predictions = sorted(best_predictions, key=lambda item: item["template_id"])
        best_labels = np.asarray([row["true_label"] for row in ordered_best_predictions], dtype=int)
        best_scores = np.asarray([row["prediction"] for row in ordered_best_predictions], dtype=float)
        bootstrap_summary = bootstrap_auroc_ci(best_labels, best_scores)
        random_baseline = random_direction_baseline(
            feature_tensors,
            family_ids,
            binary_labels,
            layer_index=int(best_binary["layer_index"]),
            aggregation_mode=AGGREGATE_MEAN,
        )

        embedding_layer_auroc = next(
            (float(item["auroc"]) for item in layer_binary if item["layer_index"] == 0),
            None,
        )
        summary_payload = {
            "model_role": args.model_role,
            "site": args.site,
            "probe_type": args.probe_type,
            "target_measure": args.target_measure,
            "pca_dims": args.pca_dims,
            "n_variants": args.n_variants,
            "evaluated_layers": layer_indices,
            "best_layer": int(best_binary["layer_index"]),
            "best_auroc": float(best_binary["auroc"]),
            "best_auprc": float(best_binary["auprc"]),
            "best_brier": float(best_binary["brier"]),
            "best_pearson_r": None if best_continuous is None else float(best_continuous["pearson_r"]),
            "bootstrap_auroc": bootstrap_summary,
            "random_direction_baseline": random_baseline,
            "embedding_layer_auroc": embedding_layer_auroc,
            "cross_model_validation": None,
            "cv_mode": args.cv_mode,
            "domain_fold_metrics": fold_metrics,
            "correctness_threshold": args.correctness_threshold if args.target_measure == "answer_correctness" else None,
        }

        save_json(output_dir / f"layer_auroc_{stem}.json", layer_binary)
        save_json(output_dir / f"loo_predictions_{stem}.json", ordered_best_predictions)
        save_json(output_dir / f"summary_{stem}.json", summary_payload)
        if layer_continuous:
            save_json(output_dir / f"layer_pearson_{stem}.json", layer_continuous)
    else:
        if args.cv_mode != "loo":
            raise ValueError("Mean probing currently supports only --cv-mode loo.")
        if args.target_measure == "answer_correctness":
            binary_labels, continuous_targets = correctness_targets_for_templates(
                template_ids,
                correctness_rates=correctness_rates,
                threshold=args.correctness_threshold,
            )
        else:
            binary_labels = binary_labels_for_templates(template_ids, positive_families)
            continuous_targets = continuous_targets_for_templates(
                template_ids,
                family_rows=family_rows,
                model_role=args.model_role,
            )
        layer_binary, best_predictions = run_layerwise_binary_loo_mean(
            tensors,
            entries,
            binary_labels,
            layer_indices=layer_indices,
            pca_dims=args.pca_dims,
            positive_families=positive_families,
        )
        layer_continuous: list[dict[str, Any]] = []
        if args.target_measure != "answer_correctness":
            layer_continuous = run_layerwise_continuous_loo_mean(
                tensors,
                entries,
                continuous_targets,
                layer_indices=layer_indices,
                pca_dims=args.pca_dims,
            )
        best_binary = max(layer_binary, key=lambda item: item["auroc"])
        best_continuous = (
            max(layer_continuous, key=lambda item: item["pearson_r"])
            if layer_continuous
            else None
        )
        plot_layer_curve(layer_binary, output_dir / f"layer_auroc_curve_{stem}.png")

        ordered_best_predictions = sorted(best_predictions, key=lambda item: item["template_id"])
        best_labels = np.asarray([row["true_label"] for row in ordered_best_predictions], dtype=int)
        best_scores = np.asarray([row["prediction"] for row in ordered_best_predictions], dtype=float)
        bootstrap_summary = bootstrap_auroc_ci(best_labels, best_scores)
        random_baseline = random_direction_baseline(
            tensors,
            template_ids,
            binary_labels,
            layer_index=int(best_binary["layer_index"]),
            aggregation_mode=AGGREGATE_MEAN,
        )

        best_c = float(ordered_best_predictions[0]["selected_c"])
        cross_model_summary = None
        if args.cross_model_activation_dir:
            target_entries, target_tensors = load_site_tensors(Path(args.cross_model_activation_dir), args.site)
            target_template_ids = extract_template_ids(target_entries)
            cross_model_summary = cross_model_validation(
                source_tensors=tensors,
                source_template_ids=template_ids,
                target_tensors=target_tensors,
                target_template_ids=target_template_ids,
                best_layer=int(best_binary["layer_index"]),
                best_c=best_c,
                target_family_rows=family_rows,
                target_role=args.cross_model_role,
                positive_families=positive_families,
                positive_threshold=positive_threshold,
            )

        embedding_layer_auroc = next(
            (float(item["auroc"]) for item in layer_binary if item["layer_index"] == 0),
            None,
        )
        summary_payload = {
            "model_role": args.model_role,
            "site": args.site,
            "probe_type": args.probe_type,
            "target_measure": args.target_measure,
            "pca_dims": args.pca_dims,
            "evaluated_layers": layer_indices,
            "best_layer": int(best_binary["layer_index"]),
            "best_auroc": float(best_binary["auroc"]),
            "best_auprc": float(best_binary["auprc"]),
            "best_brier": float(best_binary["brier"]),
            "best_pearson_r": None if best_continuous is None else float(best_continuous["pearson_r"]),
            "bootstrap_auroc": bootstrap_summary,
            "random_direction_baseline": random_baseline,
            "embedding_layer_auroc": embedding_layer_auroc,
            "cross_model_validation": cross_model_summary,
            "correctness_threshold": args.correctness_threshold if args.target_measure == "answer_correctness" else None,
        }

        save_json(output_dir / f"layer_auroc_{stem}.json", layer_binary)
        save_json(output_dir / f"loo_predictions_{stem}.json", ordered_best_predictions)
        save_json(output_dir / f"summary_{stem}.json", summary_payload)
        if layer_continuous:
            save_json(output_dir / f"layer_pearson_{stem}.json", layer_continuous)

    logger.log_event(
        "PROBING_COMPLETE",
        model_role=args.model_role,
        site=args.site,
        probe_type=args.probe_type,
        pca_dims=args.pca_dims,
        best_layer=summary_payload["best_layer"],
        best_auroc=summary_payload["best_auroc"],
        best_pearson_r=summary_payload["best_pearson_r"],
    )


if __name__ == "__main__":
    main()
