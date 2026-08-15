#!/usr/bin/env python3
"""Cue-type AUROC comparison for mean, per-variant, variance, and entropy probes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-csv", default="results/stage6/analysis_d2/stage6_d1_per_family.csv")
    parser.add_argument("--mean-preds", default="results/stage9/mean_probe_stage6/loo_predictions_resid_post_last_prompt.json")
    parser.add_argument("--pervar-preds", default="results/stage9/prompt_condition_probe/per_variant_predictions.json")
    parser.add_argument("--variance-preds", default="results/stage6/probing/primary_variance/loo_predictions_variance.json")
    parser.add_argument("--entropy-preds", default="results/stage9/baselines/entropy/entropy_per_family_scores.json")
    parser.add_argument("--output", default="results/stage10/per_cue_probe_comparison.json")
    return parser.parse_args()


def cue_label(raw: str) -> str:
    return {
        "irrelevant_variable": "Cue A",
        "nongoverning_distractor": "Cue B",
        "frame_rendering": "Cue C",
    }.get(raw, raw)


def safe_metrics(labels: list[int], scores: list[float]) -> dict[str, float | None]:
    if len(set(labels)) < 2:
        return {"auroc": None, "auprc": None, "n": len(labels), "n_pos": int(sum(labels))}
    return {
        "auroc": float(roc_auc_score(labels, scores)),
        "auprc": float(average_precision_score(labels, scores)),
        "n": len(labels),
        "n_pos": int(sum(labels)),
    }


def main() -> None:
    args = parse_args()
    with Path(args.family_csv).open("r", encoding="utf-8", newline="") as handle:
        family_rows = list(csv.DictReader(handle))
    cue_by_family = {row["template_id"]: cue_label(row["cue_type"]) for row in family_rows}

    mean_rows = json.loads(Path(args.mean_preds).read_text(encoding="utf-8"))
    variance_rows = json.loads(Path(args.variance_preds).read_text(encoding="utf-8"))
    entropy_rows = json.loads(Path(args.entropy_preds).read_text(encoding="utf-8"))
    pervar_rows = json.loads(Path(args.pervar_preds).read_text(encoding="utf-8"))

    mean_by_family = {row["template_id"]: (int(row["true_label"]), float(row["prediction"])) for row in mean_rows}
    variance_by_family = {row["template_id"]: (int(row["true_label"]), float(row["prediction"])) for row in variance_rows}
    entropy_by_family = {row["template_id"]: (int(row["true_label"]), float(row["prediction"])) for row in entropy_rows}

    pervar_family: dict[str, list[tuple[int, float]]] = {}
    pervar_by_variant: dict[int, dict[str, tuple[int, float]]] = {0: {}, 1: {}, 2: {}, 3: {}}
    for row in pervar_rows:
        tid = row["template_id"]
        vid = int(row["variant_id"])
        truth = int(row["true_label"])
        score = float(row["prediction"])
        pervar_family.setdefault(tid, []).append((truth, score))
        pervar_by_variant[vid][tid] = (truth, score)

    pervar_mean_by_family = {
        tid: (rows[0][0], float(np.mean([score for _, score in rows])))
        for tid, rows in pervar_family.items()
    }

    output: dict[str, dict[str, dict[str, float | None]]] = {
        "mean_probe": {},
        "per_variant_probe_family_avg": {},
        "variance_probe": {},
        "entropy_proxy": {},
        "per_variant_singletons": {},
    }
    for cue in ("Cue A", "Cue B", "Cue C"):
        fams = [tid for tid, label in cue_by_family.items() if label == cue and tid in mean_by_family]
        output["mean_probe"][cue] = safe_metrics(
            [mean_by_family[tid][0] for tid in fams],
            [mean_by_family[tid][1] for tid in fams],
        )
        output["per_variant_probe_family_avg"][cue] = safe_metrics(
            [pervar_mean_by_family[tid][0] for tid in fams if tid in pervar_mean_by_family],
            [pervar_mean_by_family[tid][1] for tid in fams if tid in pervar_mean_by_family],
        )
        output["variance_probe"][cue] = safe_metrics(
            [variance_by_family[tid][0] for tid in fams if tid in variance_by_family],
            [variance_by_family[tid][1] for tid in fams if tid in variance_by_family],
        )
        output["entropy_proxy"][cue] = safe_metrics(
            [entropy_by_family[tid][0] for tid in fams if tid in entropy_by_family],
            [entropy_by_family[tid][1] for tid in fams if tid in entropy_by_family],
        )

    for vid in range(4):
        output["per_variant_singletons"][f"variant_{vid}"] = {}
        for cue in ("Cue A", "Cue B", "Cue C"):
            fams = [tid for tid, label in cue_by_family.items() if label == cue and tid in pervar_by_variant[vid]]
            output["per_variant_singletons"][f"variant_{vid}"][cue] = safe_metrics(
                [pervar_by_variant[vid][tid][0] for tid in fams],
                [pervar_by_variant[vid][tid][1] for tid in fams],
            )

    write_json(Path(args.output), output)


if __name__ == "__main__":
    main()
