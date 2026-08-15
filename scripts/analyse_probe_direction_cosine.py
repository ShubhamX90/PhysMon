#!/usr/bin/env python3
"""Compute cosine similarity between probe directions across selected layers."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402

from run_probing import (  # noqa: E402
    build_family_feature_tensors,
    choose_logistic_c,
    infer_positive_families,
    load_site_tensors,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation-dir", required=True)
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument(
        "--family-csv",
        default="results/stage6/analysis_d2/stage6_d1_per_family.csv",
    )
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument(
        "--probe-type",
        choices=("variance", "mean"),
        default="variance",
    )
    parser.add_argument("--layers", nargs="+", type=int, default=[10, 13, 16, 18])
    parser.add_argument(
        "--output-path",
        default="results/stage10/probe_direction_cosine/probe_direction_cosine.json",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def normalise(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        return vector
    return vector / norm


def fit_probe_direction(
    x_layer: np.ndarray,
    y: np.ndarray,
    family_ids: list[str],
    *,
    seed: int,
) -> dict[str, Any]:
    scaler = StandardScaler().fit(x_layer)
    x_scaled = scaler.transform(x_layer)
    chosen_c = choose_logistic_c(
        x_scaled,
        y,
        family_ids,
        aggregation_mode="mean",
        pca_dims=None,
    )
    clf = LogisticRegression(
        C=chosen_c,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=seed,
    )
    clf.fit(x_scaled, y)
    coef_scaled = clf.coef_[0].astype(np.float64)
    scale = scaler.scale_.astype(np.float64)
    raw_direction = coef_scaled / np.where(scale == 0.0, 1.0, scale)
    return {
        "chosen_c": float(chosen_c),
        "intercept": float(clf.intercept_[0]),
        "coef_norm_scaled": float(np.linalg.norm(coef_scaled)),
        "coef_norm_raw": float(np.linalg.norm(raw_direction)),
        "direction_raw_unit": normalise(raw_direction),
        "direction_scaled_unit": normalise(coef_scaled),
    }


def main() -> None:
    args = parse_args()
    reducer = "variance" if args.probe_type == "variance" else "mean"
    entries, tensors = load_site_tensors(Path(args.activation_dir), args.site)
    family_ids, feature_tensors = build_family_feature_tensors(tensors, entries, reducer=reducer)
    positives, threshold = infer_positive_families(
        family_csv=Path(args.family_csv),
        positive_families_file=Path(args.positive_families_file),
    )
    y = np.asarray([int(family_id in positives) for family_id in family_ids], dtype=int)

    directions: dict[int, dict[str, Any]] = {}
    for layer in args.layers:
        directions[int(layer)] = fit_probe_direction(
            feature_tensors[:, int(layer), :],
            y,
            family_ids,
            seed=args.seed,
        )

    cosine_matrix: list[dict[str, Any]] = []
    for left_layer in args.layers:
        left = directions[int(left_layer)]["direction_raw_unit"]
        row = {"layer_index": int(left_layer), "cosines": {}}
        for right_layer in args.layers:
            right = directions[int(right_layer)]["direction_raw_unit"]
            row["cosines"][str(int(right_layer))] = float(np.dot(left, right))
        cosine_matrix.append(row)

    precursor = {
        "10_vs_16": float(
            np.dot(directions[10]["direction_raw_unit"], directions[16]["direction_raw_unit"])
        ) if 10 in directions and 16 in directions else None,
        "13_vs_16": float(
            np.dot(directions[13]["direction_raw_unit"], directions[16]["direction_raw_unit"])
        ) if 13 in directions and 16 in directions else None,
        "10_vs_18": float(
            np.dot(directions[10]["direction_raw_unit"], directions[18]["direction_raw_unit"])
        ) if 10 in directions and 18 in directions else None,
        "13_vs_18": float(
            np.dot(directions[13]["direction_raw_unit"], directions[18]["direction_raw_unit"])
        ) if 13 in directions and 18 in directions else None,
    }

    payload = {
        "probe_type": args.probe_type,
        "site": args.site,
        "positive_threshold": float(threshold),
        "layers": [int(layer) for layer in args.layers],
        "direction_metadata": {
            str(layer): {
                "chosen_c": directions[int(layer)]["chosen_c"],
                "intercept": directions[int(layer)]["intercept"],
                "coef_norm_scaled": directions[int(layer)]["coef_norm_scaled"],
                "coef_norm_raw": directions[int(layer)]["coef_norm_raw"],
            }
            for layer in args.layers
        },
        "cosine_matrix": cosine_matrix,
        "precursor_similarity": precursor,
    }
    write_json(Path(args.output_path), payload)


if __name__ == "__main__":
    main()
