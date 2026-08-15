#!/usr/bin/env python3
"""Stage 8 cross-model transfer probe with PCA + Procrustes alignment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from scipy.linalg import orthogonal_procrustes

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.logging import ExperimentLogger  # noqa: E402
from run_probing import (  # noqa: E402
    build_family_feature_tensors,
    infer_positive_families,
    load_site_tensors,
)
from physmon.probing.metrics import compute_auprc, compute_auroc, compute_brier  # noqa: E402


DEFAULT_STAGE = 8
DEFAULT_FAMILY_CSV = "results/stage6/analysis_d2/stage6_d1_per_family.csv"
DEFAULT_JSONL_NAME = "run_cross_model_transfer_events.jsonl"
DEFAULT_SITE = "resid_post_last_prompt"
DEFAULT_NOVEL_FAMILIES = (
    "CM_A_STD_008",
    "CM_B_STD_001",
    "CM_B_STD_003",
    "CM_C_003",
    "CM_B_UM_004",
    "CM_B_UM_051",
    "CM_B_UM_048",
    "CM_A_STD_013",
    "CM_A_STD_005",
    "CM_A_STD_010",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-model", required=True)
    parser.add_argument("--target-model", required=True)
    parser.add_argument("--source-activation-dir", required=True)
    parser.add_argument("--target-activation-dir", required=True)
    parser.add_argument("--source-layer", type=int, required=True)
    parser.add_argument("--target-layer", type=int, required=True)
    parser.add_argument("--alignment-dims", type=int, default=256)
    parser.add_argument("--family-csv", default=DEFAULT_FAMILY_CSV)
    parser.add_argument(
        "--source-positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument(
        "--target-positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families_llama.json",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--families-of-interest",
        nargs="*",
        default=list(DEFAULT_NOVEL_FAMILIES),
        help="Optional family ids for focused cross-architecture score inspection.",
    )
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_layer_matrix(activation_dir: Path, layer_index: int) -> tuple[list[str], np.ndarray]:
    entries, tensors = load_site_tensors(activation_dir, DEFAULT_SITE)
    family_ids, feature_tensors = build_family_feature_tensors(tensors, entries, reducer="variance")
    return family_ids, feature_tensors[:, layer_index, :]


def sanitize_label(label: str) -> str:
    """Convert one model key into a filesystem- and JSON-friendly slug."""

    return label.replace("-", "_").replace("/", "_").replace(" ", "_")


def align_spaces(source: np.ndarray, target: np.ndarray, dims: int) -> tuple[np.ndarray, np.ndarray, float, float]:
    dims = min(dims, source.shape[0], source.shape[1], target.shape[0], target.shape[1])
    source_pca = PCA(n_components=dims, random_state=42)
    target_pca = PCA(n_components=dims, random_state=42)
    source_proj = source_pca.fit_transform(source)
    target_proj = target_pca.fit_transform(target)
    source_centered = source_proj - source_proj.mean(axis=0, keepdims=True)
    target_centered = target_proj - target_proj.mean(axis=0, keepdims=True)
    rotation, _ = orthogonal_procrustes(source_centered, target_centered)
    aligned_source = source_centered @ rotation
    pre_similarity = float(
        np.sum(source_centered * target_centered)
        / (np.linalg.norm(source_centered) * np.linalg.norm(target_centered) + 1e-12)
    )
    post_similarity = float(
        np.sum(aligned_source * target_centered)
        / (np.linalg.norm(aligned_source) * np.linalg.norm(target_centered) + 1e-12)
    )
    return aligned_source, target_centered, pre_similarity, post_similarity


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_cross_model_transfer.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_role=args.source_model,
    )

    source_positive, _ = infer_positive_families(
        family_csv=Path(args.family_csv),
        positive_families_file=Path(args.source_positive_families_file),
    )
    target_positive, _ = infer_positive_families(
        family_csv=Path(args.family_csv),
        positive_families_file=Path(args.target_positive_families_file),
    )

    source_ids, source_layer = build_layer_matrix(Path(args.source_activation_dir), args.source_layer)
    target_ids, target_layer = build_layer_matrix(Path(args.target_activation_dir), args.target_layer)
    common_ids = sorted(set(source_ids) & set(target_ids))
    source_lookup = {family_id: idx for idx, family_id in enumerate(source_ids)}
    target_lookup = {family_id: idx for idx, family_id in enumerate(target_ids)}
    source_matrix = np.stack([source_layer[source_lookup[family_id]] for family_id in common_ids], axis=0)
    target_matrix = np.stack([target_layer[target_lookup[family_id]] for family_id in common_ids], axis=0)

    aligned_source, aligned_target, pre_similarity, post_similarity = align_spaces(
        source_matrix,
        target_matrix,
        args.alignment_dims,
    )

    source_labels = np.asarray([int(family_id in source_positive) for family_id in common_ids], dtype=int)
    target_labels = np.asarray([int(family_id in target_positive) for family_id in common_ids], dtype=int)

    forward_model = LogisticRegression(
        C=10.0,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=args.seed,
    )
    forward_model.fit(aligned_source, source_labels)
    forward_scores = forward_model.predict_proba(aligned_target)[:, 1]

    reverse_model = LogisticRegression(
        C=10.0,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=args.seed,
    )
    reverse_model.fit(aligned_target, target_labels)
    reverse_scores = reverse_model.predict_proba(aligned_source)[:, 1]

    source_slug = sanitize_label(args.source_model)
    target_slug = sanitize_label(args.target_model)
    forward_key = f"{source_slug}_to_{target_slug}"
    reverse_key = f"{target_slug}_to_{source_slug}"

    payload = {
        "common_family_count": len(common_ids),
        "alignment_dims": args.alignment_dims,
        "source_model": args.source_model,
        "target_model": args.target_model,
        "source_layer": args.source_layer,
        "target_layer": args.target_layer,
        "pre_alignment_similarity": pre_similarity,
        "post_alignment_similarity": post_similarity,
        forward_key: {
            "auroc": compute_auroc(target_labels, forward_scores),
            "auprc": compute_auprc(target_labels, forward_scores),
            "brier": compute_brier(target_labels, forward_scores),
        },
        reverse_key: {
            "auroc": compute_auroc(source_labels, reverse_scores),
            "auprc": compute_auprc(source_labels, reverse_scores),
            "brier": compute_brier(source_labels, reverse_scores),
        },
    }
    save_json(output_dir / "alignment_quality.json", payload)

    source_families_scored_by_target_lookup = {
        family_id: float(score) for family_id, score in zip(common_ids, reverse_scores, strict=False)
    }
    target_families_scored_by_source_lookup = {
        family_id: float(score) for family_id, score in zip(common_ids, forward_scores, strict=False)
    }
    novel_payload = {
        "source_model": args.source_model,
        "target_model": args.target_model,
        "families": [],
    }
    for family_id in args.families_of_interest:
        if family_id not in source_lookup or family_id not in target_lookup:
            continue
        novel_payload["families"].append(
            {
                "template_id": family_id,
                f"{source_slug}_label": int(family_id in source_positive),
                f"{target_slug}_label": int(family_id in target_positive),
                f"{target_slug}_score_from_{source_slug}_probe": target_families_scored_by_source_lookup[family_id],
                f"{source_slug}_score_from_{target_slug}_probe": source_families_scored_by_target_lookup[family_id],
            }
        )
    save_json(output_dir / "novel_sensitivity_families.json", novel_payload)

    logger.log_event(
        "CROSS_MODEL_TRANSFER_COMPLETE",
        common_family_count=len(common_ids),
        source_to_target_auroc=payload[forward_key]["auroc"],
        target_to_source_auroc=payload[reverse_key]["auroc"],
        post_alignment_similarity=post_similarity,
    )


if __name__ == "__main__":
    main()
