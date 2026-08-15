#!/usr/bin/env python3
"""Stage 12 multi-site per-variant sensitivity probe.

Combines the last-prompt-token residual stream with the cue-token residual
stream at one layer, using cached Stage 6 activations only.
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
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402


DEFAULT_JSONL_NAME = "run_multi_site_probe_events.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--activation-manifest",
        default="/scratch/pabitra/physmon/activations_stage6/qwen_primary/manifest.json",
    )
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument("--output-dir", default="results/stage12/science/multi_site_probe")
    parser.add_argument("--stage", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_positive_families(path: Path) -> set[str]:
    return set(json.loads(path.read_text(encoding="utf-8"))["positive_families"])


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_tensor_path(entry: dict[str, Any]) -> Path:
    path = Path(str(entry["tensor_path"]))
    if path.exists():
        return path
    raise FileNotFoundError(path)


def load_vectors_for_site(manifest: dict[str, Any], site: str, layer: int) -> dict[tuple[str, int], np.ndarray]:
    payload: dict[tuple[str, int], np.ndarray] = {}
    for entry in manifest["files"]:
        if entry["site"] != site:
            continue
        tid = str(entry["template_id"])
        if tid in STAGE6_EXCLUDE_FROM_PROBE:
            continue
        vid = int(entry["variant_id"])
        tensor = torch.load(resolve_tensor_path(entry), map_location="cpu").float().numpy()
        payload[(tid, vid)] = tensor[layer]
    return payload


def grouped_loo_masks(family_ids: list[str]) -> list[tuple[np.ndarray, np.ndarray]]:
    fam_arr = np.asarray(family_ids)
    return [(fam_arr != held_out, fam_arr == held_out) for held_out in sorted(set(family_ids))]


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_multi_site_probe.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=None,
        model_role="qwen_primary",
    )

    positives = load_positive_families(Path(args.positive_families_file))
    manifest = load_manifest(Path(args.activation_manifest))
    last_vectors = load_vectors_for_site(manifest, "resid_post_last_prompt", int(args.layer))
    cue_vectors = load_vectors_for_site(manifest, "resid_post_cue_token", int(args.layer))

    keys = sorted(set(last_vectors) & set(cue_vectors))
    variant_family_ids = [tid for tid, _ in keys]
    variant_ids = [vid for _, vid in keys]
    x = np.stack(
        [np.concatenate([last_vectors[key], cue_vectors[key]], axis=0) for key in keys],
        axis=0,
    )
    y_variant = np.asarray([int(fid in positives) for fid in variant_family_ids], dtype=int)

    per_variant_scores = []
    per_variant_truth = []
    for train_mask, test_mask in grouped_loo_masks(variant_family_ids):
        scaler = StandardScaler().fit(x[train_mask])
        x_train = scaler.transform(x[train_mask])
        x_test = scaler.transform(x[test_mask])
        clf = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=2000,
            solver="liblinear",
            random_state=args.seed,
        )
        clf.fit(x_train, y_variant[train_mask])
        scores = clf.predict_proba(x_test)[:, 1]
        per_variant_scores.extend(float(score) for score in scores)
        per_variant_truth.extend(int(value) for value in y_variant[test_mask])

    unique_families = sorted(set(variant_family_ids))
    family_truth = np.asarray([int(fid in positives) for fid in unique_families], dtype=int)
    family_mean_scores = []
    for family_id in unique_families:
        scores = [
            score
            for fid, score in zip(variant_family_ids, per_variant_scores, strict=True)
            if fid == family_id
        ]
        family_mean_scores.append(float(np.mean(scores)))

    summary = {
        "layer": int(args.layer),
        "n_families": len(unique_families),
        "n_variant_samples": len(variant_family_ids),
        "feature_dim": int(x.shape[1]),
        "family_mean": {
            "auroc": float(roc_auc_score(family_truth, family_mean_scores)),
            "auprc": float(average_precision_score(family_truth, family_mean_scores)),
        },
        "variant_level": {
            "auroc": float(roc_auc_score(per_variant_truth, per_variant_scores)),
            "auprc": float(average_precision_score(per_variant_truth, per_variant_scores)),
        },
    }
    per_variant_rows = [
        {
            "layer_index": int(args.layer),
            "template_id": fid,
            "variant_id": int(vid),
            "true_label": int(truth),
            "prediction": float(score),
        }
        for fid, vid, truth, score in zip(
            variant_family_ids,
            variant_ids,
            per_variant_truth,
            per_variant_scores,
            strict=True,
        )
    ]
    write_json(output_dir / "multi_site_probe_summary.json", summary)
    write_json(output_dir / "multi_site_probe_predictions.json", per_variant_rows)
    logger.log_event(
        "MULTI_SITE_PROBE_COMPLETE",
        layer=int(args.layer),
        family_mean_auroc=float(summary["family_mean"]["auroc"]),
        variant_level_auroc=float(summary["variant_level"]["auroc"]),
    )


if __name__ == "__main__":
    main()
