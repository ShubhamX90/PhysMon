#!/usr/bin/env python3
"""Train a per-variant family-sensitivity probe on one activation set and score another."""

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
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--target-manifest", required=True)
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument("--layer", type=int, required=True)
    parser.add_argument("--source-positive-families-file", required=True)
    parser.add_argument("--target-positive-families-file", default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_positive_families(path: Path | None) -> set[str]:
    if path is None:
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(str(item) for item in payload["positive_families"])


def load_variant_samples(manifest_path: Path, *, site: str) -> tuple[list[str], list[int], np.ndarray]:
    manifest = load_manifest(manifest_path)
    grouped: dict[str, dict[int, np.ndarray]] = {}
    for entry in manifest["files"]:
        if str(entry["site"]) != site:
            continue
        template_id = str(entry["template_id"])
        variant_id = int(entry["variant_id"])
        tensor = torch.load(Path(str(entry["tensor_path"])), map_location="cpu").float().numpy()
        grouped.setdefault(template_id, {})[variant_id] = tensor

    family_ids = sorted(grouped)
    variant_family_ids: list[str] = []
    variant_ids: list[int] = []
    vectors: list[np.ndarray] = []
    for family_id in family_ids:
        for variant_id in sorted(grouped[family_id]):
            variant_family_ids.append(family_id)
            variant_ids.append(variant_id)
            vectors.append(grouped[family_id][variant_id])
    return variant_family_ids, variant_ids, np.stack(vectors, axis=0)


def safe_binary_metrics(y_true: np.ndarray, scores: np.ndarray) -> dict[str, float | None]:
    if len(np.unique(y_true)) < 2:
        return {"auroc": None, "auprc": None}
    return {
        "auroc": float(roc_auc_score(y_true, scores)),
        "auprc": float(average_precision_score(y_true, scores)),
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_positive = load_positive_families(Path(args.source_positive_families_file))
    target_positive = load_positive_families(Path(args.target_positive_families_file)) if args.target_positive_families_file else set()

    src_family_ids, src_variant_ids, src_x = load_variant_samples(Path(args.source_manifest), site=args.site)
    tgt_family_ids, tgt_variant_ids, tgt_x = load_variant_samples(Path(args.target_manifest), site=args.site)

    src_y = np.asarray([int(fid in source_positive) for fid in src_family_ids], dtype=int)
    scaler = StandardScaler().fit(src_x[:, args.layer, :])
    x_train = scaler.transform(src_x[:, args.layer, :])
    clf = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=args.seed)
    clf.fit(x_train, src_y)

    tgt_scores = clf.predict_proba(scaler.transform(tgt_x[:, args.layer, :]))[:, 1]
    variant_predictions = []
    for family_id, variant_id, score in zip(tgt_family_ids, tgt_variant_ids, tgt_scores, strict=True):
        variant_predictions.append(
            {
                "template_id": str(family_id),
                "variant_id": int(variant_id),
                "prediction": float(score),
                "true_label": int(family_id in target_positive) if target_positive else None,
                "layer_index": int(args.layer),
            }
        )

    unique_target_families = sorted(set(tgt_family_ids))
    family_rows = []
    family_scores = []
    family_truth = []
    for family_id in unique_target_families:
        scores = [row["prediction"] for row in variant_predictions if row["template_id"] == family_id]
        mean_score = float(np.mean(scores))
        family_scores.append(mean_score)
        truth = int(family_id in target_positive) if target_positive else None
        if truth is not None:
            family_truth.append(truth)
        family_rows.append(
            {
                "template_id": family_id,
                "mean_prediction": mean_score,
                "true_label": truth,
            }
        )

    variant_metrics = safe_binary_metrics(
        np.asarray([row["true_label"] for row in variant_predictions if row["true_label"] is not None], dtype=int),
        np.asarray([row["prediction"] for row in variant_predictions if row["true_label"] is not None], dtype=float),
    ) if target_positive else {"auroc": None, "auprc": None}
    family_metrics = safe_binary_metrics(
        np.asarray(family_truth, dtype=int),
        np.asarray(family_scores, dtype=float),
    ) if target_positive else {"auroc": None, "auprc": None}

    summary = {
        "layer": int(args.layer),
        "site": args.site,
        "n_source_families": len(set(src_family_ids)),
        "n_target_families": len(unique_target_families),
        "variant_level": variant_metrics,
        "family_mean": family_metrics,
    }
    write_json(output_dir / "per_variant_predictions.json", variant_predictions)
    write_json(output_dir / "family_mean_predictions.json", family_rows)
    write_json(output_dir / "summary.json", summary)


if __name__ == "__main__":
    main()
