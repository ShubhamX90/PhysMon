#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 9 correctness residualisation for the Stage 6 sensitivity probe."""

from __future__ import annotations

import argparse
import csv
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
from physmon.probing.metrics import compute_brier  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402


DEFAULT_STAGE = 9
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_correctness_residualisation_events.jsonl"
DEFAULT_C_GRID = (0.001, 0.01, 0.1, 1.0, 10.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--activation-manifest",
        default="/scratch/pabitra/physmon/activations_stage6/qwen_primary/manifest.json",
    )
    parser.add_argument(
        "--site",
        default="resid_post_last_prompt",
    )
    parser.add_argument("--layer", type=int, default=18)
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument(
        "--family-csv",
        default="results/stage6/analysis_d2/stage6_d1_per_family.csv",
    )
    parser.add_argument(
        "--behavioural-jsonl",
        default="results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl",
    )
    parser.add_argument("--correctness-threshold", type=float, default=0.75)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_tensor_path(entry: dict[str, Any]) -> Path:
    candidate = Path(str(entry["tensor_path"]))
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Missing activation tensor: {candidate}")


def load_family_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["template_id"]: row for row in csv.DictReader(handle)}


def canonicalize_expected_answer(raw_answer: str) -> str | None:
    from physmon.benchmark.parser import parse_answer

    parsed = parse_answer(str(raw_answer))
    return parsed.answer if parsed.is_confident else None


def load_correctness_rates(behavioural_jsonl: Path) -> dict[str, float]:
    correct_counts: dict[str, int] = {}
    total_counts: dict[str, int] = {}
    expected_cache: dict[str, str | None] = {}
    with behavioural_jsonl.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") != "variant_record":
                continue
            template_id = str(record["template_id"])
            expected_answer = expected_cache.setdefault(
                template_id,
                canonicalize_expected_answer(str(record.get("correct_answer", ""))),
            )
            parsed_answer = record.get("parsed_answer_canonical")
            parse_confident = bool(record.get("parse_confident", False))
            total_counts[template_id] = total_counts.get(template_id, 0) + 1
            if parse_confident and expected_answer is not None and parsed_answer == expected_answer:
                correct_counts[template_id] = correct_counts.get(template_id, 0) + 1
    return {
        template_id: correct_counts.get(template_id, 0) / total_counts[template_id]
        for template_id in total_counts
        if total_counts[template_id] > 0
    }


def load_variance_features(
    *,
    manifest_path: Path,
    site: str,
    layer: int,
    exclude_ids: set[str],
) -> tuple[list[str], np.ndarray]:
    manifest = load_manifest(manifest_path)
    grouped: dict[str, dict[int, np.ndarray]] = {}
    for entry in manifest["files"]:
        if entry["site"] != site:
            continue
        template_id = str(entry["template_id"])
        if template_id in exclude_ids:
            continue
        variant_id = int(entry["variant_id"])
        tensor = torch.load(resolve_tensor_path(entry), map_location="cpu").float().numpy()
        grouped.setdefault(template_id, {})[variant_id] = tensor[layer]

    family_ids = sorted(grouped)
    features: list[np.ndarray] = []
    for template_id in family_ids:
        variant_map = grouped[template_id]
        variant_ids = sorted(variant_map)
        if variant_ids != [0, 1, 2, 3]:
            raise ValueError(f"{template_id} does not have 4 variants at site {site}: {variant_ids}")
        stacked = np.stack([variant_map[idx] for idx in variant_ids], axis=0)
        features.append(stacked.std(axis=0))
    return family_ids, np.stack(features, axis=0)


def load_sensitivity_labels(
    *,
    family_ids: list[str],
    positive_families_file: Path,
) -> np.ndarray:
    payload = json.loads(positive_families_file.read_text(encoding="utf-8"))
    positives = set(str(item) for item in payload["positive_families"])
    return np.asarray([int(template_id in positives) for template_id in family_ids], dtype=int)


def load_correctness_labels(
    *,
    family_ids: list[str],
    family_rows: dict[str, dict[str, str]],
    correctness_rates: dict[str, float],
    threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    rates: list[float] = []
    labels: list[int] = []
    for template_id in family_ids:
        row = family_rows[template_id]
        parse_ok = str(row.get("qwen_parse_ok", "")).strip().lower() == "true"
        rate = float(correctness_rates[template_id])
        rates.append(rate)
        labels.append(int(parse_ok and rate >= threshold))
    return np.asarray(labels, dtype=int), np.asarray(rates, dtype=float)


def residualise_along_direction(x: np.ndarray, w_unit: np.ndarray) -> np.ndarray:
    return x - np.outer(x @ w_unit, w_unit)


def select_c_via_inner_loo(
    *,
    x_train_resid: np.ndarray,
    y_train: np.ndarray,
    c_grid: tuple[float, ...] = DEFAULT_C_GRID,
    seed: int = 42,
) -> tuple[float, float]:
    if len(np.unique(y_train)) < 2:
        return 1.0, float("nan")

    best_c = c_grid[0]
    best_auroc = -np.inf
    for c_value in c_grid:
        inner_scores: list[float] = []
        inner_labels: list[int] = []
        for holdout in range(len(y_train)):
            inner_train_mask = np.ones(len(y_train), dtype=bool)
            inner_train_mask[holdout] = False
            inner_test_mask = ~inner_train_mask
            y_inner_train = y_train[inner_train_mask]
            if len(np.unique(y_inner_train)) < 2:
                continue
            clf = LogisticRegression(
                C=c_value,
                max_iter=2000,
                solver="lbfgs",
                random_state=seed,
            )
            clf.fit(x_train_resid[inner_train_mask], y_inner_train)
            score = float(clf.predict_proba(x_train_resid[inner_test_mask])[0, 1])
            inner_scores.append(score)
            inner_labels.append(int(y_train[holdout]))
        if len(set(inner_labels)) < 2:
            inner_auroc = 0.5
        else:
            inner_auroc = float(roc_auc_score(inner_labels, inner_scores))
        if inner_auroc > best_auroc:
            best_auroc = inner_auroc
            best_c = c_value
    return float(best_c), float(best_auroc)


def run_residualised_loo(
    *,
    x: np.ndarray,
    y_sensitivity: np.ndarray,
    y_correctness: np.ndarray,
    family_ids: list[str],
    seed: int,
) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for holdout in range(len(family_ids)):
        train_mask = np.ones(len(family_ids), dtype=bool)
        train_mask[holdout] = False
        test_mask = ~train_mask

        scaler = StandardScaler().fit(x[train_mask])
        x_train = scaler.transform(x[train_mask])
        x_test = scaler.transform(x[test_mask])

        clf_corr = LogisticRegression(
            C=1.0,
            max_iter=2000,
            solver="lbfgs",
            random_state=seed,
        ).fit(x_train, y_correctness[train_mask])
        w = clf_corr.coef_[0]
        norm = float(np.linalg.norm(w))
        if norm == 0.0:
            raise ValueError(f"Correctness direction collapsed to zero on fold {holdout}.")
        w_unit = w / norm

        x_train_resid = residualise_along_direction(x_train, w_unit)
        x_test_resid = residualise_along_direction(x_test, w_unit)

        best_c, _ = select_c_via_inner_loo(
            x_train_resid=x_train_resid,
            y_train=y_sensitivity[train_mask],
            seed=seed,
        )
        clf_sens = LogisticRegression(
            C=best_c,
            max_iter=2000,
            solver="lbfgs",
            random_state=seed,
        ).fit(x_train_resid, y_sensitivity[train_mask])
        prediction = float(clf_sens.predict_proba(x_test_resid)[0, 1])
        predictions.append(
            {
                "template_id": family_ids[holdout],
                "true_label": int(y_sensitivity[holdout]),
                "prediction": prediction,
            }
        )
    return predictions


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = ExperimentLogger(
        script_name="run_correctness_residualisation.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=None,
        model_role="qwen_primary",
    )

    family_rows = load_family_rows(Path(args.family_csv))
    correctness_rates = load_correctness_rates(Path(args.behavioural_jsonl))
    family_ids, x = load_variance_features(
        manifest_path=Path(args.activation_manifest),
        site=args.site,
        layer=args.layer,
        exclude_ids=set(STAGE6_EXCLUDE_FROM_PROBE),
    )
    y_sensitivity = load_sensitivity_labels(
        family_ids=family_ids,
        positive_families_file=Path(args.positive_families_file),
    )
    y_correctness, correctness_rate_values = load_correctness_labels(
        family_ids=family_ids,
        family_rows=family_rows,
        correctness_rates=correctness_rates,
        threshold=args.correctness_threshold,
    )

    predictions = run_residualised_loo(
        x=x,
        y_sensitivity=y_sensitivity,
        y_correctness=y_correctness,
        family_ids=family_ids,
        seed=args.seed,
    )
    ordered = sorted(predictions, key=lambda item: item["template_id"])
    y_true = np.asarray([row["true_label"] for row in ordered], dtype=int)
    y_score = np.asarray([row["prediction"] for row in ordered], dtype=float)

    residualised_auroc = float(roc_auc_score(y_true, y_score))
    residualised_auprc = float(average_precision_score(y_true, y_score))
    residualised_brier = float(compute_brier(y_true, y_score))

    original_sensitivity_probe_auroc = 0.7307692307692307
    correctness_probe_auroc = 0.7656818181818182
    summary = {
        "original_sensitivity_probe_auroc": original_sensitivity_probe_auroc,
        "correctness_probe_auroc": correctness_probe_auroc,
        "residualised_sensitivity_auroc": residualised_auroc,
        "residualised_auprc": residualised_auprc,
        "residualised_brier": residualised_brier,
        "delta_vs_correctness_probe": residualised_auroc - correctness_probe_auroc,
        "delta_vs_original_sensitivity": residualised_auroc - original_sensitivity_probe_auroc,
        "layer": args.layer,
        "method": "LOO_concept_erasure_single_correctness_direction",
        "correctness_threshold": args.correctness_threshold,
        "n_families": len(family_ids),
        "n_sensitivity_positive": int(y_sensitivity.sum()),
        "n_correctness_positive": int(y_correctness.sum()),
        "verdict": (
            "SENSITIVITY_PROBE_SURVIVES"
            if residualised_auroc >= 0.68
            else "SENSITIVITY_PROBE_WEAKENS"
        ),
    }

    write_json(output_dir / "residualisation_summary.json", summary)
    write_json(output_dir / "loo_predictions.json", ordered)
    write_json(
        output_dir / "family_metadata.json",
        {
            "family_ids": family_ids,
            "correctness_rates": {
                template_id: rate for template_id, rate in zip(family_ids, correctness_rate_values.tolist(), strict=True)
            },
            "correctness_labels": {
                template_id: int(label) for template_id, label in zip(family_ids, y_correctness.tolist(), strict=True)
            },
        },
    )
    logger.log_event("CORRECTNESS_RESIDUALISATION_COMPLETE", **summary)


if __name__ == "__main__":
    main()
