#!/usr/bin/env python3
# ruff: noqa: E402
"""Simple log-probability variance baseline from existing behavioural outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE
from physmon.utils.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--behavioural-jsonl",
        default="results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl",
    )
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument(
        "--output",
        default="results/stage9/baselines/entropy/entropy_baseline_summary.json",
    )
    parser.add_argument(
        "--per-family-output",
        default="results/stage9/baselines/entropy/entropy_per_family_scores.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    positives = set(json.loads(Path(args.positive_families_file).read_text())["positive_families"])
    by_family: dict[str, dict[int, float]] = {}
    with Path(args.behavioural_jsonl).open() as handle:
        for line in handle:
            rec = json.loads(line)
            if rec.get("record_type") != "variant_record":
                continue
            tid = rec["template_id"]
            if tid in STAGE6_EXCLUDE_FROM_PROBE:
                continue
            by_family.setdefault(tid, {})[int(rec["variant_id"])] = float(rec["logprob_correct_answer"])

    family_ids = sorted(by_family)
    features = []
    labels = []
    for tid in family_ids:
        vals = np.asarray([by_family[tid][i] for i in sorted(by_family[tid])], dtype=float)
        features.append([float(vals.std()), float(vals.mean())])
        labels.append(int(tid in positives))
    x = np.asarray(features, dtype=float)
    y = np.asarray(labels, dtype=int)

    preds = []
    per_family_rows = []
    for i, tid in enumerate(family_ids):
        mask = np.ones(len(family_ids), dtype=bool)
        mask[i] = False
        clf = LogisticRegression(max_iter=2000, solver="lbfgs")
        clf.fit(x[mask], y[mask])
        pred = float(clf.predict_proba(x[~mask])[0, 1])
        preds.append(pred)
        per_family_rows.append(
            {
                "template_id": tid,
                "entropy_proxy_score": float(x[i, 0]),
                "mean_logprob_correct_answer": float(x[i, 1]),
                "prediction": pred,
                "true_label": int(y[i]),
            }
        )

    payload = {
        "n_families": len(family_ids),
        "feature_definition": "std_and_mean_of_logprob_correct_answer_across_4_variants",
        "auroc": float(roc_auc_score(y, preds)),
        "auprc": float(average_precision_score(y, preds)),
    }
    write_json(Path(args.output), payload)
    write_json(Path(args.per_family_output), per_family_rows)


if __name__ == "__main__":
    main()
