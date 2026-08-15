#!/usr/bin/env python3
"""Stage 11 latent-family geometry analysis for Qwen vs DeepSeek sensitivity.

This script asks whether the DeepSeek-amplified / Qwen-low families occupy a
representation-space region closer to "both-sensitive" families than to
"neither-sensitive" families in Qwen's layer-16 hidden states.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE
from physmon.utils.io import write_json
from run_probing import build_family_feature_tensors, filter_entries_and_tensors, load_per_family_rows, load_site_tensors


DEFAULT_ACTIVATION_DIR = Path("/scratch/pabitra/physmon/activations_stage6/qwen_primary/")
DEFAULT_FAMILY_CSV = Path("results/stage6/analysis_d2/stage6_d1_per_family.csv")
DEFAULT_DEEPSEEK_CSV = Path("results/stage8/analysis_deepseek/deepseek_per_family.csv")
DEFAULT_POSITIVES = Path("results/stage6/analysis_d2/stage6_positive_families.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation-dir", type=Path, default=DEFAULT_ACTIVATION_DIR)
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument("--family-csv", type=Path, default=DEFAULT_FAMILY_CSV)
    parser.add_argument("--deepseek-csv", type=Path, default=DEFAULT_DEEPSEEK_CSV)
    parser.add_argument("--positive-families-file", type=Path, default=DEFAULT_POSITIVES)
    parser.add_argument("--output-dir", type=Path, default=Path("results/stage11/science/latent_family_geometry"))
    return parser.parse_args()


def load_positive_families(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(str(item) for item in payload["positive_families"])


def load_deepseek_positive_labels(path: Path, *, threshold: float = 0.5) -> dict[str, int]:
    labels: dict[str, int] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            template_id = str(row["template_id"])
            slp_raw = row.get("deepseek_S_lp", "") or "0"
            parse_rate_raw = row.get("deepseek_parse_rate_family", "") or "0"
            parse_rate = float(parse_rate_raw)
            slp_value = float(slp_raw)
            labels[template_id] = int(parse_rate >= 0.5 and slp_value >= threshold)
    return labels


def centroid(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.zeros((matrix.shape[1],), dtype=float)
    return matrix.mean(axis=0)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    positives_qwen = load_positive_families(args.positive_families_file)
    positives_deepseek = load_deepseek_positive_labels(args.deepseek_csv)

    family_rows = load_per_family_rows(args.family_csv)
    entries, tensors = load_site_tensors(args.activation_dir, args.site)
    entries, tensors = filter_entries_and_tensors(
        entries,
        tensors,
        family_rows=family_rows,
        exclude_ids=set(STAGE6_EXCLUDE_FROM_PROBE),
        exclude_cue_type=None,
        cue_type=None,
        pilot_only=False,
    )
    family_ids, family_feature_tensors = build_family_feature_tensors(
        tensors,
        entries,
        reducer="mean",
    )
    x_layer = family_feature_tensors[:, args.layer, :]

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x_layer)
    pca50 = PCA(n_components=min(50, x_scaled.shape[0], x_scaled.shape[1]), random_state=42)
    x_pca50 = pca50.fit_transform(x_scaled)
    pca2 = PCA(n_components=2, random_state=42)
    x_pca2 = pca2.fit_transform(x_pca50)

    group_masks = {
        "A_both_sensitive": np.asarray(
            [int(fid in positives_qwen and positives_deepseek.get(fid, 0) == 1) for fid in family_ids],
            dtype=bool,
        ),
        "B_qwen_only": np.asarray(
            [int(fid in positives_qwen and positives_deepseek.get(fid, 0) == 0) for fid in family_ids],
            dtype=bool,
        ),
        "C_deepseek_latent": np.asarray(
            [int(fid not in positives_qwen and positives_deepseek.get(fid, 0) == 1) for fid in family_ids],
            dtype=bool,
        ),
        "D_neither": np.asarray(
            [int(fid not in positives_qwen and positives_deepseek.get(fid, 0) == 0) for fid in family_ids],
            dtype=bool,
        ),
    }

    centroids_50 = {
        name: centroid(x_pca50[mask]) if mask.any() else np.zeros((x_pca50.shape[1],), dtype=float)
        for name, mask in group_masks.items()
    }

    per_family_rows: list[dict[str, Any]] = []
    latent_distance_ratios: list[float] = []
    latent_ids: list[str] = []
    for index, family_id in enumerate(family_ids):
        row = {
            "template_id": family_id,
            "qwen_positive": int(family_id in positives_qwen),
            "deepseek_positive": int(positives_deepseek.get(family_id, 0)),
            "pca2_x": float(x_pca2[index, 0]),
            "pca2_y": float(x_pca2[index, 1]),
        }
        for group_name, group_centroid in centroids_50.items():
            row[f"dist_to_{group_name}"] = float(np.linalg.norm(x_pca50[index] - group_centroid))
        if group_masks["C_deepseek_latent"][index]:
            dist_a = row["dist_to_A_both_sensitive"]
            dist_d = row["dist_to_D_neither"]
            ratio = float(dist_a / max(dist_d, 1e-8))
            row["latent_distance_ratio_A_over_D"] = ratio
            latent_distance_ratios.append(ratio)
            latent_ids.append(family_id)
        per_family_rows.append(row)

    train_mask = group_masks["A_both_sensitive"] | group_masks["D_neither"]
    latent_mask = group_masks["C_deepseek_latent"]
    x_train = x_pca50[train_mask]
    y_train = np.asarray(group_masks["A_both_sensitive"][train_mask], dtype=int)
    x_latent = x_pca50[latent_mask]

    classifier_summary: dict[str, Any]
    if len(np.unique(y_train)) >= 2 and x_latent.shape[0] > 0:
        clf = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=2000,
            solver="liblinear",
            random_state=42,
        )
        clf.fit(x_train, y_train)
        latent_scores = clf.predict_proba(x_latent)[:, 1]
        classifier_summary = {
            "trained_on_groups": ["A_both_sensitive", "D_neither"],
            "latent_predicted_sensitive_fraction": float(np.mean(latent_scores >= 0.5)),
            "latent_mean_sensitive_probability": float(np.mean(latent_scores)),
            "latent_scores": [
                {"template_id": family_id, "pred_sensitive_probability": float(score)}
                for family_id, score in zip(latent_ids, latent_scores, strict=True)
            ],
        }
    else:
        classifier_summary = {"trained_on_groups": ["A_both_sensitive", "D_neither"], "latent_scores": []}

    centroid_distance_summary = {
        name: {
            "count": int(mask.sum()),
            "centroid_norm": float(np.linalg.norm(centroids_50[name])),
        }
        for name, mask in group_masks.items()
    }
    latent_closer_to = "A_both_sensitive" if np.mean(latent_distance_ratios or [1.0]) < 1.0 else "D_neither"
    output = {
        "layer": int(args.layer),
        "site": args.site,
        "n_families": len(family_ids),
        "group_counts": {name: int(mask.sum()) for name, mask in group_masks.items()},
        "centroid_summary": centroid_distance_summary,
        "latent_closer_to": latent_closer_to,
        "latent_mean_distance_ratio_A_over_D": float(np.mean(latent_distance_ratios)) if latent_distance_ratios else None,
        "classifier_summary": classifier_summary,
        "families": per_family_rows,
        "headline_interpretation": (
            "Latent families lie closer to the both-sensitive centroid than to the neither-sensitive centroid."
            if latent_closer_to == "A_both_sensitive"
            else "Latent families do not cluster nearer to the both-sensitive centroid under this geometry analysis."
        ),
    }
    write_json(args.output_dir / "latent_family_geometry.json", output)


if __name__ == "__main__":
    main()
