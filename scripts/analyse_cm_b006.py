#!/usr/bin/env python3
"""Stage 5.1 diagnostic analysis centered on the CM_B_006 inversion.

Reference:
    Stage 5 follow-up brief v5.1 Part A.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

from physmon.formal.constructs import STAGE5_POSITIVE_FAMILIES

from run_probing import (
    binary_labels_for_templates,
    group_variant_positions,
    load_logprob_table,
    load_per_family_rows,
    load_site_tensors,
    resolve_behavioural_jsonl,
)


DEFAULT_LAYER = 15
DEFAULT_OUTPUT_DIR = "results/stage5/diagnostic"
DEFAULT_FAMILY_CSV = "results/stage4_repair/analysis_v2/stage4_per_family.csv"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the CM_B_006 diagnostic."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation-dir", required=True, help="Activation directory containing manifest.json.")
    parser.add_argument("--families", nargs="+", required=True, help="Focused families for detailed analysis.")
    parser.add_argument("--layer", type=int, default=DEFAULT_LAYER, help="Layer index to inspect.")
    parser.add_argument("--site", default="resid_post_last_prompt", help="Activation site to inspect.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for diagnostics.")
    parser.add_argument("--family-csv", default=DEFAULT_FAMILY_CSV, help="Stage 4/5 per-family CSV.")
    parser.add_argument(
        "--behavioural-jsonl",
        default=None,
        help="Optional behavioural JSONL; defaults to the latest Qwen file.",
    )
    return parser.parse_args()


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""

    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def pairwise_l2_distances(vectors: np.ndarray) -> list[dict[str, float]]:
    """Return pairwise L2 distances between family variants."""

    outputs: list[dict[str, float]] = []
    for left_index in range(vectors.shape[0]):
        for right_index in range(left_index + 1, vectors.shape[0]):
            outputs.append(
                {
                    "left_variant": float(left_index),
                    "right_variant": float(right_index),
                    "l2_distance": float(np.linalg.norm(vectors[left_index] - vectors[right_index])),
                }
            )
    return outputs


def save_json(path: Path, payload: Any) -> None:
    """Write one JSON payload with stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_pca_plot(
    family_means: dict[str, np.ndarray],
    family_rows: dict[str, dict[str, str]],
    output_path: Path,
) -> list[dict[str, Any]]:
    """Render the top-2 PCA projection of family means and return plotted coordinates."""

    ordered_ids = sorted(family_means)
    matrix = np.stack([family_means[template_id] for template_id in ordered_ids], axis=0)
    projection = PCA(n_components=2, random_state=42).fit_transform(matrix)

    figure, axis = plt.subplots(figsize=(8, 6))
    plotted_points: list[dict[str, Any]] = []
    for index, template_id in enumerate(ordered_ids):
        row = family_rows[template_id]
        label = int(template_id in STAGE5_POSITIVE_FAMILIES)
        color = "#b91c1c" if label else "#2563eb"
        marker = "o" if row["domain"] == "mechanics" else "s"
        x_value = float(projection[index, 0])
        y_value = float(projection[index, 1])
        axis.scatter(x_value, y_value, c=color, marker=marker, s=52, alpha=0.85)
        axis.text(x_value, y_value, template_id, fontsize=7, alpha=0.8)
        plotted_points.append(
            {
                "template_id": template_id,
                "pc1": x_value,
                "pc2": y_value,
                "domain": row["domain"],
                "cue_type": row["cue_type"],
                "true_label": label,
            }
        )

    axis.set_xlabel("PC1")
    axis.set_ylabel("PC2")
    axis.set_title("Layer-15 Family Means PCA")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
    return plotted_points


def main() -> None:
    """Run the CM_B_006 inversion analysis."""

    args = parse_args()
    activation_dir = Path(args.activation_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entries, tensors = load_site_tensors(activation_dir, args.site)
    if args.layer < 0 or args.layer >= tensors.shape[1]:
        raise ValueError(f"Layer {args.layer} is out of range for {tensors.shape[1]} layers.")

    grouped = group_variant_positions(entries)
    family_rows = load_per_family_rows(Path(args.family_csv))
    behavioural_path = resolve_behavioural_jsonl(args.behavioural_jsonl, "qwen_primary")
    behavioural_logprobs = load_logprob_table(behavioural_path)

    layer_vectors = tensors[:, args.layer, :]
    family_means: dict[str, np.ndarray] = {}
    family_variant_vectors: dict[str, np.ndarray] = {}
    for template_id, positions in grouped.items():
        indices = [position for position, _ in positions]
        family_variant_vectors[template_id] = layer_vectors[indices]
        family_means[template_id] = family_variant_vectors[template_id].mean(axis=0)

    if "CM_B_006" not in family_means or "CM_B_003" not in family_means:
        raise KeyError("CM_B_006 and CM_B_003 must both be present in the activation directory.")

    similarities = []
    cm_b006_mean = family_means["CM_B_006"]
    for template_id, family_mean in sorted(family_means.items()):
        similarities.append(
            {
                "template_id": template_id,
                "cosine_similarity_to_cm_b006": cosine_similarity(cm_b006_mean, family_mean),
                "true_label": int(template_id in STAGE5_POSITIVE_FAMILIES),
                "domain": family_rows[template_id]["domain"],
                "cue_type": family_rows[template_id]["cue_type"],
            }
        )
    similarities.sort(key=lambda item: item["cosine_similarity_to_cm_b006"], reverse=True)

    family_norms = [
        {
            "template_id": template_id,
            "mean_activation_norm": float(np.linalg.norm(family_mean)),
            "true_label": int(template_id in STAGE5_POSITIVE_FAMILIES),
            "s_lp_qwen": float(family_rows[template_id]["qwen_S_lp_repair"]),
        }
        for template_id, family_mean in sorted(family_means.items())
    ]
    family_norms.sort(key=lambda item: item["mean_activation_norm"], reverse=True)

    focus_details: dict[str, Any] = {}
    for template_id in args.families:
        if template_id not in family_variant_vectors:
            raise KeyError(f"Requested family {template_id} is missing from {activation_dir}.")
        variant_vectors = family_variant_vectors[template_id]
        pairwise_distances = pairwise_l2_distances(variant_vectors)
        logprobs = behavioural_logprobs.get(template_id, {})
        pairwise_logprob_deltas = []
        for left_index in range(variant_vectors.shape[0]):
            for right_index in range(left_index + 1, variant_vectors.shape[0]):
                pairwise_logprob_deltas.append(
                    {
                        "left_variant": float(left_index),
                        "right_variant": float(right_index),
                        "abs_logprob_delta": float(abs(logprobs[left_index] - logprobs[right_index])),
                    }
                )
        focus_details[template_id] = {
            "within_family_l2_distances": pairwise_distances,
            "variant_norms": [
                float(np.linalg.norm(variant_vectors[index])) for index in range(variant_vectors.shape[0])
            ],
            "pairwise_logprob_deltas": pairwise_logprob_deltas,
            "base_to_v1_l2_distance": float(np.linalg.norm(variant_vectors[0] - variant_vectors[1])),
            "base_to_v1_cosine_similarity": cosine_similarity(variant_vectors[0], variant_vectors[1]),
            "variant_logprobs": {str(key): float(value) for key, value in sorted(logprobs.items())},
        }

    ordered_family_ids = sorted(family_means)
    train_matrix = np.stack([family_means[template_id] for template_id in ordered_family_ids], axis=0)
    train_labels = binary_labels_for_templates(ordered_family_ids)
    full_probe = LogisticRegression(
        C=1.0,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=42,
    )
    full_probe.fit(train_matrix, train_labels)
    full_predictions = full_probe.predict_proba(train_matrix)[:, 1]
    training_predictions = [
        {
            "template_id": template_id,
            "prediction": float(full_predictions[index]),
            "true_label": int(train_labels[index]),
            "s_lp_qwen": float(family_rows[template_id]["qwen_S_lp_repair"]),
        }
        for index, template_id in enumerate(ordered_family_ids)
    ]
    training_predictions.sort(key=lambda item: item["prediction"], reverse=True)

    pca_points = render_pca_plot(family_means, family_rows, output_dir / "cm_b006_pca.png")

    payload = {
        "layer": args.layer,
        "site": args.site,
        "focus_families": args.families,
        "cm_b006_top_similarities": similarities[:12],
        "family_activation_norms": family_norms,
        "focus_family_details": focus_details,
        "training_set_probe_predictions": training_predictions,
        "cm_b006_training_prediction": next(
            item for item in training_predictions if item["template_id"] == "CM_B_006"
        ),
        "cm_b003_training_prediction": next(
            item for item in training_predictions if item["template_id"] == "CM_B_003"
        ),
        "pca_points": pca_points,
    }
    save_json(output_dir / "cm_b006_analysis.json", payload)


if __name__ == "__main__":
    main()
