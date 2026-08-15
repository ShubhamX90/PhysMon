#!/usr/bin/env python3
"""Stage 11/12 cross-cue probe transfer.

Supports either a single selected layer or a full layer sweep. The core
question is whether Cue A and Cue B share a transferable sensitivity direction
at any depth, or remain orthogonal throughout the network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE
from physmon.utils.io import write_json
from run_probing import (
    build_family_feature_tensors,
    choose_logistic_c,
    filter_entries_and_tensors,
    load_per_family_rows,
    load_site_tensors,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation-dir", type=Path, default=Path("/scratch/pabitra/physmon/activations_stage6/qwen_primary/"))
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument(
        "--sweep-all-layers",
        action="store_true",
        help="Evaluate Cue A/B transfer and probe-direction cosine similarity at every layer.",
    )
    parser.add_argument("--family-csv", type=Path, default=Path("results/stage6/analysis_d2/stage6_d1_per_family.csv"))
    parser.add_argument("--positive-families-file", type=Path, default=Path("results/stage6/analysis_d2/stage6_positive_families.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/stage11/science/cross_cue_transfer"))
    return parser.parse_args()


def load_positive_families(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(str(item) for item in payload["positive_families"])


def fit_probe(
    x_train: np.ndarray,
    y_train: np.ndarray,
    train_groups: list[str],
) -> tuple[StandardScaler, LogisticRegression, np.ndarray]:
    scaler = StandardScaler().fit(x_train)
    x_train_scaled = scaler.transform(x_train)
    chosen_c = choose_logistic_c(
        x_train_scaled,
        y_train,
        train_groups,
        aggregation_mode="mean",
        pca_dims=None,
    )
    model = LogisticRegression(
        C=chosen_c,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=42,
    )
    model.fit(x_train_scaled, y_train)
    raw_weight = model.coef_[0] / np.maximum(scaler.scale_, 1e-8)
    return scaler, model, raw_weight


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def run_layer(
    *,
    layer: int,
    x_layer: np.ndarray,
    labels: np.ndarray,
    family_ids: list[str],
    cue_types: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    cue_a_mask = np.asarray([cue == "irrelevant_variable" for cue in cue_types], dtype=bool)
    cue_b_mask = np.asarray([cue == "nongoverning_distractor" for cue in cue_types], dtype=bool)

    x_a, y_a = x_layer[cue_a_mask], labels[cue_a_mask]
    x_b, y_b = x_layer[cue_b_mask], labels[cue_b_mask]
    ids_a = [fid for fid, keep in zip(family_ids, cue_a_mask, strict=True) if keep]
    ids_b = [fid for fid, keep in zip(family_ids, cue_b_mask, strict=True) if keep]

    scaler_a, model_a, weight_a = fit_probe(x_a, y_a, ids_a)
    scaler_b, model_b, weight_b = fit_probe(x_b, y_b, ids_b)

    scores_a_on_b = model_a.predict_proba(scaler_a.transform(x_b))[:, 1]
    scores_b_on_a = model_b.predict_proba(scaler_b.transform(x_a))[:, 1]

    np.save(output_dir / f"cue_a_weight_vector_layer{layer}.npy", weight_a)
    np.save(output_dir / f"cue_b_weight_vector_layer{layer}.npy", weight_b)
    return {
        "layer": int(layer),
        "cue_a_count": len(ids_a),
        "cue_b_count": len(ids_b),
        "cue_a_train_on_cue_b_test": {
            "auroc": float(roc_auc_score(y_b, scores_a_on_b)),
            "auprc": float(average_precision_score(y_b, scores_a_on_b)),
        },
        "cue_b_train_on_cue_a_test": {
            "auroc": float(roc_auc_score(y_a, scores_b_on_a)),
            "auprc": float(average_precision_score(y_a, scores_b_on_a)),
        },
        "probe_vector_cosine_similarity": {
            "cue_a_vs_cue_b": cosine(weight_a, weight_b),
        },
    }


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    family_rows = load_per_family_rows(args.family_csv)
    positives = load_positive_families(args.positive_families_file)
    entries, tensors = load_site_tensors(args.activation_dir, args.site)
    entries, tensors = filter_entries_and_tensors(
        entries,
        tensors,
        family_rows=family_rows,
        exclude_ids=set(STAGE6_EXCLUDE_FROM_PROBE),
        exclude_cue_type="frame_rendering",
        cue_type=None,
        pilot_only=False,
    )
    family_ids, family_feature_tensors = build_family_feature_tensors(tensors, entries, reducer="mean")
    labels = np.asarray([int(fid in positives) for fid in family_ids], dtype=int)
    cue_types = [family_rows[fid]["cue_type"] for fid in family_ids]
    layer_indices = list(range(family_feature_tensors.shape[1])) if args.sweep_all_layers else [int(args.layer)]
    layer_summaries = [
        run_layer(
            layer=layer,
            x_layer=family_feature_tensors[:, layer, :],
            labels=labels,
            family_ids=family_ids,
            cue_types=cue_types,
            output_dir=args.output_dir,
        )
        for layer in layer_indices
    ]
    best_cosine = max(layer_summaries, key=lambda row: abs(row["probe_vector_cosine_similarity"]["cue_a_vs_cue_b"]))
    best_a_to_b = max(layer_summaries, key=lambda row: row["cue_a_train_on_cue_b_test"]["auroc"])
    best_b_to_a = max(layer_summaries, key=lambda row: row["cue_b_train_on_cue_a_test"]["auroc"])
    summary = {
        "requested_layer": int(args.layer),
        "sweep_all_layers": bool(args.sweep_all_layers),
        "best_cosine_layer": int(best_cosine["layer"]),
        "best_cosine_similarity": float(best_cosine["probe_vector_cosine_similarity"]["cue_a_vs_cue_b"]),
        "best_cue_a_train_on_cue_b_layer": int(best_a_to_b["layer"]),
        "best_cue_a_train_on_cue_b_auroc": float(best_a_to_b["cue_a_train_on_cue_b_test"]["auroc"]),
        "best_cue_b_train_on_cue_a_layer": int(best_b_to_a["layer"]),
        "best_cue_b_train_on_cue_a_auroc": float(best_b_to_a["cue_b_train_on_cue_a_test"]["auroc"]),
        "headline_interpretation": (
            "Cross-cue transfer quantifies whether Cue A and Cue B share a transferable sensitivity direction at any depth."
        ),
    }
    if not args.sweep_all_layers:
        summary.update(layer_summaries[0])
        write_json(args.output_dir / "cross_cue_transfer_summary.json", summary)
    else:
        write_json(args.output_dir / "cross_cue_transfer_summary.json", summary)
        write_json(args.output_dir / "cross_cue_layer_sweep.json", layer_summaries)


if __name__ == "__main__":
    main()
