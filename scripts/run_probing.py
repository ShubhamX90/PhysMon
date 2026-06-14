#!/usr/bin/env python3
"""Stage 5 probe training and evaluation entry point.

Reference:
    `physmon_proposal.pdf` §9, §11 and the Stage 5 brief Parts D, G, H.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
import torch

from physmon.formal.constructs import STAGE5_POSITIVE_FAMILIES, STAGE5_SLP_THRESHOLD
from physmon.probing.metrics import compute_auprc, compute_auroc, compute_brier
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 5
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_probing_events.jsonl"
DEFAULT_C_VALUES = (0.001, 0.01, 0.1, 1.0, 10.0)
DEFAULT_RIDGE_ALPHA = 1.0
DEFAULT_RANDOM_BASELINE_DRAWS = 100
DEFAULT_FAMILY_CSV = "results/stage4_repair/analysis_v2/stage4_per_family.csv"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 5 probing runner."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation-dir", required=True, help="Activation directory containing manifest.json.")
    parser.add_argument("--site", required=True, help="Activation site, e.g. resid_post_last_prompt.")
    parser.add_argument("--model-role", required=True, help="Model role label for reporting.")
    parser.add_argument(
        "--target-measure",
        choices=("slp_binary", "slp_continuous"),
        default="slp_binary",
        help="Primary target measure for summary reporting.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for Stage 5 probing artifacts.")
    parser.add_argument("--family-csv", default=DEFAULT_FAMILY_CSV, help="Stage 4/5 per-family CSV.")
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


def load_site_tensors(
    activation_dir: Path,
    site: str,
) -> tuple[list[str], np.ndarray]:
    """Load all variant tensors for one site into a dense numpy array."""

    manifest = load_manifest(activation_dir / "manifest.json")
    matching = [entry for entry in manifest["files"] if entry["site"] == site]
    if not matching:
        raise FileNotFoundError(f"No manifest entries for site '{site}' in {activation_dir}.")
    matching.sort(key=lambda item: (item["template_id"], int(item["variant_id"])))

    tensors = [torch.load(entry["tensor_path"], map_location="cpu").float().numpy() for entry in matching]
    template_ids = [str(entry["template_id"]) for entry in matching]
    stacked = np.stack(tensors, axis=0)
    return template_ids, stacked


def binary_labels_for_templates(template_ids: list[str]) -> np.ndarray:
    """Return pre-registered binary S_lp labels for the requested families."""

    return np.asarray([int(template_id in STAGE5_POSITIVE_FAMILIES) for template_id in template_ids], dtype=int)


def continuous_targets_for_templates(
    template_ids: list[str],
    *,
    family_rows: dict[str, dict[str, str]],
    model_role: str,
) -> np.ndarray:
    """Return continuous S_lp targets for the requested families."""

    column = "qwen_S_lp_repair" if "qwen" in model_role else "llama_S_lp_repair"
    return np.asarray([float(family_rows[template_id][column]) for template_id in template_ids], dtype=float)


def family_level_indices(template_ids: list[str]) -> tuple[list[str], np.ndarray]:
    """Return sorted unique family ids and per-variant group indices."""

    families = sorted(set(template_ids))
    family_to_index = {template_id: index for index, template_id in enumerate(families)}
    groups = np.asarray([family_to_index[template_id] for template_id in template_ids], dtype=int)
    return families, groups


def aggregate_family_predictions(
    family_ids: list[str],
    template_ids: list[str],
    variant_predictions: np.ndarray,
) -> np.ndarray:
    """Average variant predictions into one family-level score per unique template id."""

    outputs = []
    predictions = np.asarray(variant_predictions, dtype=float)
    for family_id in family_ids:
        mask = np.asarray([template_id == family_id for template_id in template_ids], dtype=bool)
        outputs.append(float(predictions[mask].mean()))
    return np.asarray(outputs, dtype=float)


def choose_logistic_c(
    x_train: np.ndarray,
    y_train: np.ndarray,
    group_ids: np.ndarray,
    c_values: tuple[float, ...] = DEFAULT_C_VALUES,
) -> float:
    """Select the best logistic regularization strength by grouped AUROC."""

    unique_groups = np.unique(group_ids)
    n_splits = min(5, len(unique_groups))
    if n_splits < 2:
        return 1.0

    splitter = GroupKFold(n_splits=n_splits)
    best_c = c_values[0]
    best_score = -np.inf
    for c_value in c_values:
        fold_scores: list[float] = []
        for train_indices, val_indices in splitter.split(x_train, y_train, groups=group_ids):
            model = LogisticRegression(
                C=c_value,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=DEFAULT_SEED,
            )
            model.fit(x_train[train_indices], y_train[train_indices])
            val_variant_scores = model.predict_proba(x_train[val_indices])[:, 1]
            val_template_ids = [str(group_ids[index]) for index in val_indices]
            val_families = sorted(set(val_template_ids))
            family_scores = aggregate_family_predictions(val_families, val_template_ids, val_variant_scores)
            family_labels = np.asarray(
                [int(y_train[val_indices][np.where(np.asarray(val_template_ids) == family_id)[0][0]]) for family_id in val_families],
                dtype=int,
            )
            if len(np.unique(family_labels)) < 2:
                continue
            fold_scores.append(compute_auroc(family_labels, family_scores))
        mean_score = float(np.mean(fold_scores)) if fold_scores else -np.inf
        if mean_score > best_score:
            best_score = mean_score
            best_c = c_value
    return best_c


def run_layerwise_binary_loo(
    tensors: np.ndarray,
    template_ids: list[str],
    labels: np.ndarray,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run layer-wise family-level LOO logistic probing."""

    family_ids, family_groups = family_level_indices(template_ids)
    layer_summaries: list[dict[str, Any]] = []
    best_layer_predictions: list[dict[str, Any]] = []
    best_auroc = -np.inf

    for layer_index in range(tensors.shape[1]):
        x_layer = tensors[:, layer_index, :]
        family_prediction_rows: list[dict[str, Any]] = []
        for held_out_family in family_ids:
            test_mask = np.asarray([template_id == held_out_family for template_id in template_ids], dtype=bool)
            train_mask = ~test_mask
            x_train = x_layer[train_mask]
            y_train = labels[train_mask]
            train_groups = family_groups[train_mask]
            chosen_c = choose_logistic_c(x_train, y_train, train_groups)
            model = LogisticRegression(
                C=chosen_c,
                class_weight="balanced",
                max_iter=2000,
                solver="liblinear",
                random_state=DEFAULT_SEED,
            )
            model.fit(x_train, y_train)
            test_scores = model.predict_proba(x_layer[test_mask])[:, 1]
            family_prediction_rows.append(
                {
                    "template_id": held_out_family,
                    "layer_index": layer_index,
                    "prediction": float(test_scores.mean()),
                    "true_label": int(held_out_family in STAGE5_POSITIVE_FAMILIES),
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


def run_layerwise_continuous_loo(
    tensors: np.ndarray,
    template_ids: list[str],
    targets: np.ndarray,
) -> list[dict[str, Any]]:
    """Run layer-wise family-level LOO ridge regression on continuous S_lp."""

    family_ids, _ = family_level_indices(template_ids)
    layer_summaries: list[dict[str, Any]] = []
    for layer_index in range(tensors.shape[1]):
        x_layer = tensors[:, layer_index, :]
        family_predictions: list[float] = []
        family_targets: list[float] = []
        for held_out_family in family_ids:
            test_mask = np.asarray([template_id == held_out_family for template_id in template_ids], dtype=bool)
            train_mask = ~test_mask
            model = Ridge(alpha=DEFAULT_RIDGE_ALPHA, random_state=DEFAULT_SEED)
            model.fit(x_layer[train_mask], targets[train_mask])
            predicted = model.predict(x_layer[test_mask])
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
                "rmse": float(np.sqrt(np.mean((np.asarray(family_targets) - np.asarray(family_predictions)) ** 2))),
            }
        )
    return layer_summaries


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
    draws: int = DEFAULT_RANDOM_BASELINE_DRAWS,
) -> dict[str, float]:
    """Estimate a norm-matched random-direction AUROC null for one layer."""

    rng = np.random.default_rng(DEFAULT_SEED)
    family_ids, _ = family_level_indices(template_ids)
    x_layer = tensors[:, layer_index, :]
    aurocs: list[float] = []
    for _ in range(draws):
        direction = rng.normal(size=x_layer.shape[1])
        direction /= np.linalg.norm(direction) + 1e-12
        variant_scores = x_layer @ direction
        family_scores = aggregate_family_predictions(family_ids, template_ids, variant_scores)
        family_labels = np.asarray([int(family_id in STAGE5_POSITIVE_FAMILIES) for family_id in family_ids], dtype=int)
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
) -> dict[str, float]:
    """Fit on all source activations and evaluate on target-model family labels."""

    source_labels = np.asarray([int(template_id in STAGE5_POSITIVE_FAMILIES) for template_id in source_template_ids], dtype=int)
    model = LogisticRegression(
        C=best_c,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=DEFAULT_SEED,
    )
    model.fit(source_tensors[:, best_layer, :], source_labels)
    target_variant_scores = model.predict_proba(target_tensors[:, best_layer, :])[:, 1]
    target_family_ids, _ = family_level_indices(target_template_ids)
    target_family_scores = aggregate_family_predictions(target_family_ids, target_template_ids, target_variant_scores)
    target_column = "qwen_S_lp_repair" if "qwen" in target_role else "llama_S_lp_repair"
    target_labels = np.asarray(
        [
            int(float(target_family_rows[family_id][target_column]) >= STAGE5_SLP_THRESHOLD)
            for family_id in target_family_ids
        ],
        dtype=int,
    )
    return {
        "auroc": compute_auroc(target_labels, target_family_scores),
        "positive_rate": float(target_labels.mean()),
    }


def main() -> None:
    """Run Stage 5 probing over extracted activation tensors."""

    args = parse_args()
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_probing.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
        model_role=args.model_role,
    )

    template_ids, tensors = load_site_tensors(Path(args.activation_dir), args.site)
    family_rows = load_per_family_rows(Path(args.family_csv))
    binary_labels = np.asarray([int(template_id in STAGE5_POSITIVE_FAMILIES) for template_id in template_ids], dtype=int)
    continuous_targets = continuous_targets_for_templates(
        template_ids,
        family_rows=family_rows,
        model_role=args.model_role,
    )

    layer_binary, best_predictions = run_layerwise_binary_loo(tensors, template_ids, binary_labels)
    layer_continuous = run_layerwise_continuous_loo(tensors, template_ids, continuous_targets)
    best_binary = max(layer_binary, key=lambda item: item["auroc"])
    best_continuous = max(layer_continuous, key=lambda item: item["pearson_r"])
    plot_layer_curve(layer_binary, output_dir / f"layer_auroc_curve_{args.site}.png")

    ordered_best_predictions = sorted(best_predictions, key=lambda item: item["template_id"])
    best_labels = np.asarray([row["true_label"] for row in ordered_best_predictions], dtype=int)
    best_scores = np.asarray([row["prediction"] for row in ordered_best_predictions], dtype=float)
    bootstrap_summary = bootstrap_auroc_ci(best_labels, best_scores)
    random_baseline = random_direction_baseline(
        tensors,
        template_ids,
        binary_labels,
        layer_index=int(best_binary["layer_index"]),
    )

    best_c = float(ordered_best_predictions[0]["selected_c"])
    cross_model_summary = None
    if args.cross_model_activation_dir:
        target_template_ids, target_tensors = load_site_tensors(Path(args.cross_model_activation_dir), args.site)
        cross_model_summary = cross_model_validation(
            source_tensors=tensors,
            source_template_ids=template_ids,
            target_tensors=target_tensors,
            target_template_ids=target_template_ids,
            best_layer=int(best_binary["layer_index"]),
            best_c=best_c,
            target_family_rows=family_rows,
            target_role=args.cross_model_role,
        )

    summary_payload = {
        "model_role": args.model_role,
        "site": args.site,
        "target_measure": args.target_measure,
        "best_layer": int(best_binary["layer_index"]),
        "best_auroc": float(best_binary["auroc"]),
        "best_auprc": float(best_binary["auprc"]),
        "best_brier": float(best_binary["brier"]),
        "best_pearson_r": float(best_continuous["pearson_r"]),
        "bootstrap_auroc": bootstrap_summary,
        "random_direction_baseline": random_baseline,
        "embedding_layer_auroc": float(next(item["auroc"] for item in layer_binary if item["layer_index"] == 0)),
        "cross_model_validation": cross_model_summary,
    }

    save_json(output_dir / f"layer_auroc_{args.site}.json", layer_binary)
    save_json(output_dir / f"loo_predictions_{args.site}.json", ordered_best_predictions)
    save_json(output_dir / f"summary_{args.site}.json", summary_payload)
    save_json(output_dir / f"layer_pearson_{args.site}.json", layer_continuous)
    logger.log_event(
        "PROBING_COMPLETE",
        model_role=args.model_role,
        site=args.site,
        best_layer=summary_payload["best_layer"],
        best_auroc=summary_payload["best_auroc"],
        best_pearson_r=summary_payload["best_pearson_r"],
    )


if __name__ == "__main__":
    main()
