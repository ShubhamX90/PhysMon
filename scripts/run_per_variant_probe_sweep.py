#!/usr/bin/env python3
"""Stage 10 per-variant sensitivity probe sweep across all layers."""

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


DEFAULT_JSONL_NAME = "run_per_variant_probe_sweep_events.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--activation-manifest",
        default="/scratch/pabitra/physmon/activations_stage6/qwen_primary/manifest.json",
    )
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument(
        "--output-dir",
        default="results/stage10/per_variant_probe_sweep",
    )
    parser.add_argument("--stage", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_tensor_path(entry: dict[str, Any]) -> Path:
    path = Path(str(entry["tensor_path"]))
    if path.exists():
        return path
    raise FileNotFoundError(path)


def load_positive_families(path: Path) -> set[str]:
    return set(json.loads(path.read_text(encoding="utf-8"))["positive_families"])


def load_variant_matrix(
    *,
    manifest_path: Path,
    site: str,
) -> tuple[list[str], list[int], np.ndarray]:
    manifest = load_manifest(manifest_path)
    grouped: dict[str, dict[int, np.ndarray]] = {}
    for entry in manifest["files"]:
        if entry["site"] != site:
            continue
        tid = str(entry["template_id"])
        if tid in STAGE6_EXCLUDE_FROM_PROBE:
            continue
        vid = int(entry["variant_id"])
        tensor = torch.load(resolve_tensor_path(entry), map_location="cpu").float().numpy()
        grouped.setdefault(tid, {})[vid] = tensor

    family_ids = sorted(grouped)
    variant_family_ids: list[str] = []
    variant_ids: list[int] = []
    vectors: list[np.ndarray] = []
    for tid in family_ids:
        vids = sorted(grouped[tid])
        if vids != [0, 1, 2, 3]:
            raise ValueError(f"{tid} missing variants: {vids}")
        for vid in vids:
            variant_family_ids.append(tid)
            variant_ids.append(vid)
            vectors.append(grouped[tid][vid])
    return variant_family_ids, variant_ids, np.stack(vectors, axis=0)


def grouped_folds(family_ids: list[str]) -> list[tuple[np.ndarray, np.ndarray]]:
    unique = sorted(set(family_ids))
    fam_arr = np.asarray(family_ids)
    folds = []
    for held_out in unique:
        test_mask = fam_arr == held_out
        train_mask = ~test_mask
        folds.append((train_mask, test_mask))
    return folds


def bootstrap_ci(labels: np.ndarray, scores: np.ndarray, *, seed: int, n_boot: int = 1000) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    values: list[float] = []
    n = len(labels)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        y = labels[idx]
        if len(set(y.tolist())) < 2:
            continue
        s = scores[idx]
        values.append(float(roc_auc_score(y, s)))
    values.sort()
    return {
        "mean": float(np.mean(values)),
        "ci_lower": float(np.quantile(values, 0.025)),
        "ci_upper": float(np.quantile(values, 0.975)),
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_per_variant_probe_sweep.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=None,
        model_role="qwen_primary",
    )

    positives = load_positive_families(Path(args.positive_families_file))
    variant_family_ids, variant_ids, x = load_variant_matrix(
        manifest_path=Path(args.activation_manifest),
        site=args.site,
    )
    y = np.asarray([int(tid in positives) for tid in variant_family_ids], dtype=int)
    folds = grouped_folds(variant_family_ids)
    num_layers = x.shape[1]

    layer_rows: list[dict[str, float]] = []
    best_scores = None
    best_layer = None
    best_auroc = -1.0

    for layer in range(num_layers):
        scores: list[float] = []
        rows = []
        for train_mask, test_mask in folds:
            scaler = StandardScaler().fit(x[train_mask, layer, :])
            x_train = scaler.transform(x[train_mask, layer, :])
            x_test = scaler.transform(x[test_mask, layer, :])
            clf = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=args.seed)
            clf.fit(x_train, y[train_mask])
            probs = clf.predict_proba(x_test)[:, 1]
            scores.extend(float(p) for p in probs)
            for fid, vid, truth, pred in zip(
                np.asarray(variant_family_ids)[test_mask],
                np.asarray(variant_ids)[test_mask],
                y[test_mask],
                probs,
                strict=True,
            ):
                rows.append(
                    {
                        "template_id": str(fid),
                        "variant_id": int(vid),
                        "true_label": int(truth),
                        "prediction": float(pred),
                        "layer_index": layer,
                    }
                )
        score_arr = np.asarray(scores, dtype=float)
        auroc = float(roc_auc_score(y, score_arr))
        auprc = float(average_precision_score(y, score_arr))
        layer_rows.append({"layer_index": layer, "auroc": auroc, "auprc": auprc})
        if auroc > best_auroc:
            best_auroc = auroc
            best_layer = layer
            best_scores = rows

    assert best_scores is not None and best_layer is not None
    best_pred_arr = np.asarray([row["prediction"] for row in best_scores], dtype=float)
    summary = {
        "best_layer": int(best_layer),
        "best_auroc": float(best_auroc),
        "best_auprc": float(average_precision_score(y, best_pred_arr)),
        "bootstrap_auroc": bootstrap_ci(y, best_pred_arr, seed=args.seed),
        "n_variant_samples": len(variant_family_ids),
        "n_families": len(set(variant_family_ids)),
        "site": args.site,
    }

    write_json(output_dir / "layer_auroc_per_variant.json", layer_rows)
    write_json(output_dir / "loo_predictions_per_variant.json", best_scores)
    write_json(output_dir / "summary_per_variant_sweep.json", summary)
    logger.log_event("PER_VARIANT_SWEEP_COMPLETE", **summary)


if __name__ == "__main__":
    main()
