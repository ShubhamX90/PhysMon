#!/usr/bin/env python3
# ruff: noqa: E402
"""Prompt-condition auxiliary probe and per-variant sensitivity analyses.

Originally introduced in Stage 9.5 at layer 18. In Stage 11 this script also
supports a full layer sweep to compare Level-1 cue decoding against Level-2
sensitivity prediction across depth.
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

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE
from physmon.utils.io import write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_JSONL_NAME = "run_prompt_condition_probe_events.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--activation-manifest",
        default="/scratch/pabitra/physmon/activations_stage6/qwen_primary/manifest.json",
    )
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument("--layer", type=int, default=18)
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument(
        "--behavioural-jsonl",
        default="results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl",
    )
    parser.add_argument("--output-dir", default="results/stage9/prompt_condition_probe")
    parser.add_argument(
        "--sweep-all-layers",
        action="store_true",
        help="Run the prompt-condition and per-variant sensitivity analyses across every layer.",
    )
    parser.add_argument("--stage", type=int, default=9)
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


def load_behavioural_logprobs(path: Path) -> dict[str, dict[int, float]]:
    by_family: dict[str, dict[int, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            rec = json.loads(line)
            if rec.get("record_type") != "variant_record":
                continue
            tid = str(rec["template_id"])
            if tid in STAGE6_EXCLUDE_FROM_PROBE:
                continue
            by_family.setdefault(tid, {})[int(rec["variant_id"])] = float(rec["logprob_correct_answer"])
    return by_family


def load_variant_tensor_stack(
    *,
    manifest_path: Path,
    site: str,
    layer: int | None = None,
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
        grouped.setdefault(tid, {})[vid] = tensor if layer is None else tensor[layer]

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


def grouped_loo_indices(family_ids: list[str]) -> list[tuple[np.ndarray, np.ndarray]]:
    unique = sorted(set(family_ids))
    fam_arr = np.asarray(family_ids)
    result = []
    for held_out in unique:
        test_mask = fam_arr == held_out
        train_mask = ~test_mask
        result.append((train_mask, test_mask))
    return result


def run_layer_analysis(
    *,
    x: np.ndarray,
    layer: int,
    positives: set[str],
    behavioural_logprobs: dict[str, dict[int, float]],
    variant_family_ids: list[str],
    variant_ids: list[int],
    seed: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    y_prompt = np.asarray(variant_ids, dtype=int)
    y_sensitivity_variant = np.asarray([int(tid in positives) for tid in variant_family_ids], dtype=int)
    most_sensitive_variant_by_family = {
        tid: min(logprobs.items(), key=lambda item: item[1])[0]
        for tid, logprobs in behavioural_logprobs.items()
    }
    y_most_sensitive_variant = np.asarray(
        [int(vid == most_sensitive_variant_by_family[fid]) for fid, vid in zip(variant_family_ids, variant_ids, strict=True)],
        dtype=int,
    )

    multiclass_correct = 0
    multiclass_total = 0
    per_variant_scores = []
    per_variant_truth = []
    most_sensitive_scores = []
    most_sensitive_truth = []
    grouped_folds = grouped_loo_indices(variant_family_ids)
    for train_mask, test_mask in grouped_folds:
        scaler = StandardScaler().fit(x[train_mask])
        x_train = scaler.transform(x[train_mask])
        x_test = scaler.transform(x[test_mask])

        clf_prompt = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=seed)
        clf_prompt.fit(x_train, y_prompt[train_mask])
        preds = clf_prompt.predict(x_test)
        multiclass_correct += int((preds == y_prompt[test_mask]).sum())
        multiclass_total += int(test_mask.sum())

        clf_sens = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=seed)
        clf_sens.fit(x_train, y_sensitivity_variant[train_mask])
        scores = clf_sens.predict_proba(x_test)[:, 1]
        per_variant_scores.extend(float(value) for value in scores)
        per_variant_truth.extend(int(value) for value in y_sensitivity_variant[test_mask])

        clf_most = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=seed)
        clf_most.fit(x_train, y_most_sensitive_variant[train_mask])
        most_scores = clf_most.predict_proba(x_test)[:, 1]
        most_sensitive_scores.extend(float(value) for value in most_scores)
        most_sensitive_truth.extend(int(value) for value in y_most_sensitive_variant[test_mask])

    prompt_condition_accuracy = multiclass_correct / multiclass_total

    unique_families = sorted(set(variant_family_ids))
    family_vectors = []
    family_labels = []
    for tid in unique_families:
        mask = np.asarray([fid == tid for fid in variant_family_ids], dtype=bool)
        family_vectors.append(x[mask].mean(axis=0))
        family_labels.append(int(tid in positives))
    family_vectors = np.asarray(family_vectors, dtype=float)
    family_labels_arr = np.asarray(family_labels, dtype=int)

    mode_a_scores = []
    for i in range(len(unique_families)):
        train_mask = np.ones(len(unique_families), dtype=bool)
        train_mask[i] = False
        scaler = StandardScaler().fit(family_vectors[train_mask])
        x_train = scaler.transform(family_vectors[train_mask])
        x_test = scaler.transform(family_vectors[~train_mask])
        clf = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=seed)
        clf.fit(x_train, family_labels_arr[train_mask])
        mode_a_scores.append(float(clf.predict_proba(x_test)[0, 1]))
    mode_a_auroc = float(roc_auc_score(family_labels_arr, mode_a_scores))
    mode_a_auprc = float(average_precision_score(family_labels_arr, mode_a_scores))

    per_variant_rows = []
    for fid, vid, truth, score in zip(
        variant_family_ids,
        variant_ids,
        per_variant_truth,
        per_variant_scores,
        strict=True,
    ):
        per_variant_rows.append(
            {
                "layer_index": int(layer),
                "template_id": fid,
                "variant_id": int(vid),
                "true_label": int(truth),
                "prediction": float(score),
            }
        )
    family_mean_scores = []
    for tid in unique_families:
        rows = [row for row in per_variant_rows if row["template_id"] == tid]
        family_mean_scores.append(float(np.mean([row["prediction"] for row in rows])))
    mode_b_auroc = float(roc_auc_score(family_labels_arr, family_mean_scores))
    mode_b_auprc = float(average_precision_score(family_labels_arr, family_mean_scores))
    most_sensitive_variant_auroc = float(roc_auc_score(most_sensitive_truth, most_sensitive_scores))
    most_sensitive_variant_auprc = float(average_precision_score(most_sensitive_truth, most_sensitive_scores))

    return (
        {
            "layer": int(layer),
            "prompt_condition_4class_accuracy": prompt_condition_accuracy,
            "most_sensitive_variant_binary_auroc": most_sensitive_variant_auroc,
            "most_sensitive_variant_binary_auprc": most_sensitive_variant_auprc,
            "mode_a_family_mean_auroc": mode_a_auroc,
            "mode_a_family_mean_auprc": mode_a_auprc,
            "mode_b_per_variant_auroc": mode_b_auroc,
            "mode_b_per_variant_auprc": mode_b_auprc,
            "n_families": len(unique_families),
            "n_variant_samples": len(variant_family_ids),
        },
        per_variant_rows,
    )


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_prompt_condition_probe.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=None,
        model_role="qwen_primary",
    )

    positives = load_positive_families(Path(args.positive_families_file))
    behavioural_logprobs = load_behavioural_logprobs(Path(args.behavioural_jsonl))
    variant_family_ids, variant_ids, tensor_stack = load_variant_tensor_stack(
        manifest_path=Path(args.activation_manifest),
        site=args.site,
        layer=None,
    )

    layer_indices = list(range(tensor_stack.shape[1])) if args.sweep_all_layers else [int(args.layer)]
    layer_summaries = []
    per_variant_rows_all = []
    for layer_index in layer_indices:
        summary, per_variant_rows = run_layer_analysis(
            x=tensor_stack[:, layer_index, :],
            layer=layer_index,
            positives=positives,
            behavioural_logprobs=behavioural_logprobs,
            variant_family_ids=variant_family_ids,
            variant_ids=variant_ids,
            seed=args.seed,
        )
        summary["site"] = args.site
        layer_summaries.append(summary)
        per_variant_rows_all.extend(per_variant_rows)

    best_prompt = max(layer_summaries, key=lambda row: row["prompt_condition_4class_accuracy"])
    best_mode_b = max(layer_summaries, key=lambda row: row["mode_b_per_variant_auroc"])

    output_summary = {
        "site": args.site,
        "requested_layer": int(args.layer),
        "sweep_all_layers": bool(args.sweep_all_layers),
        "best_prompt_condition_layer": int(best_prompt["layer"]),
        "best_prompt_condition_accuracy": float(best_prompt["prompt_condition_4class_accuracy"]),
        "best_mode_b_layer": int(best_mode_b["layer"]),
        "best_mode_b_per_variant_auroc": float(best_mode_b["mode_b_per_variant_auroc"]),
    }
    if not args.sweep_all_layers:
        output_summary.update(layer_summaries[0])

    write_json(output_dir / "prompt_condition_probe_summary.json", output_summary)
    write_json(output_dir / "prompt_condition_layer_sweep.json", layer_summaries)
    write_json(output_dir / "per_variant_predictions.json", per_variant_rows_all)
    logger.log_event(
        "PROMPT_CONDITION_PROBE_COMPLETE",
        sweep_all_layers=bool(args.sweep_all_layers),
        best_prompt_condition_layer=int(output_summary["best_prompt_condition_layer"]),
        best_mode_b_layer=int(output_summary["best_mode_b_layer"]),
        best_mode_b_per_variant_auroc=float(output_summary["best_mode_b_per_variant_auroc"]),
    )


if __name__ == "__main__":
    main()
