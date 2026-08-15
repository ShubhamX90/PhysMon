#!/usr/bin/env python3
"""Stage 9.5 black-box two-query counterfactual baseline.

Predict which variant in a pair will assign lower log-probability to the correct
answer using only prompt-surface features, then aggregate those pairwise scores
into a family-level sensitivity score.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE
from physmon.utils.io import write_json


NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--behavioural-jsonl",
        default="results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl",
    )
    parser.add_argument(
        "--generated-dir",
        default="results/stage6/generated_full_benchmark",
    )
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument(
        "--output-dir",
        default="results/stage9/baselines/blackbox_counterfactual",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_behavioural(path: Path) -> dict[str, dict[int, float]]:
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


def load_generated_family(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_first_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value)
    match = NUMBER_RE.search(text)
    if match is None:
        return math.nan
    return float(match.group(0))


def extract_numbers(text: str) -> list[float]:
    return [float(match.group(0)) for match in NUMBER_RE.finditer(text)]


def build_family_records(
    generated_dir: Path,
    behavioural: dict[str, dict[int, float]],
    positives: set[str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    family_records: list[dict[str, Any]] = []
    family_label_map: dict[str, int] = {}
    for family_path in sorted(generated_dir.glob("*.json")):
        payload = load_generated_family(family_path)
        if "template_id" not in payload or "variants" not in payload:
            continue
        tid = str(payload["template_id"])
        if tid in STAGE6_EXCLUDE_FROM_PROBE or tid not in behavioural:
            continue
        variants = {}
        for variant in payload["variants"]:
            vid = int(variant["variant_id"])
            prompt = str(variant["prompt"])
            variants[vid] = {
                "variant_id": vid,
                "prompt": prompt,
                "cue_value_numeric": parse_first_number(variant.get("cue_value")),
                "prompt_length": len(prompt),
                "number_count": len(extract_numbers(prompt)),
            }
        if sorted(variants) != [0, 1, 2, 3]:
            continue
        family_records.append(
            {
                "template_id": tid,
                "variants": variants,
                "logprobs": behavioural[tid],
            }
        )
        family_label_map[tid] = int(tid in positives)
    return family_records, family_label_map


def make_pair_rows(family_record: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tid = family_record["template_id"]
    variants = family_record["variants"]
    logprobs = family_record["logprobs"]
    vids = [0, 1, 2, 3]
    for i, a in enumerate(vids):
        for b in vids[i + 1 :]:
            va = variants[a]
            vb = variants[b]
            lp_a = float(logprobs[a])
            lp_b = float(logprobs[b])
            label_b_lower = int(lp_b < lp_a)
            rows.append(
                {
                    "template_id": tid,
                    "variant_a": a,
                    "variant_b": b,
                    "prompt_a": va["prompt"],
                    "prompt_b": vb["prompt"],
                    "cue_diff": float(vb["cue_value_numeric"] - va["cue_value_numeric"])
                    if not (math.isnan(va["cue_value_numeric"]) or math.isnan(vb["cue_value_numeric"]))
                    else 0.0,
                    "length_diff": float(vb["prompt_length"] - va["prompt_length"]),
                    "number_count_diff": float(vb["number_count"] - va["number_count"]),
                    "label_b_lower": label_b_lower,
                }
            )
    return rows


def cosine_distance_row(a_vec: np.ndarray, b_vec: np.ndarray) -> float:
    denom = float(np.linalg.norm(a_vec) * np.linalg.norm(b_vec))
    if denom == 0.0:
        return 0.0
    cosine = float(np.dot(a_vec, b_vec) / denom)
    return 1.0 - cosine


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    positives = set(json.loads(Path(args.positive_families_file).read_text(encoding="utf-8"))["positive_families"])
    behavioural = load_behavioural(Path(args.behavioural_jsonl))
    family_records, family_label_map = build_family_records(Path(args.generated_dir), behavioural, positives)

    all_pair_rows = {record["template_id"]: make_pair_rows(record) for record in family_records}
    family_ids = [record["template_id"] for record in family_records]

    pairwise_correct: list[int] = []
    pairwise_predictions: list[dict[str, Any]] = []
    family_scores_directional: dict[str, float] = {}
    family_scores_margin: dict[str, float] = {}

    for held_out_tid in family_ids:
        train_tids = [tid for tid in family_ids if tid != held_out_tid]
        train_rows = [row for tid in train_tids for row in all_pair_rows[tid]]
        test_rows = all_pair_rows[held_out_tid]

        train_prompts = [row["prompt_a"] for row in train_rows] + [row["prompt_b"] for row in train_rows]
        vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2))
        vectorizer.fit(train_prompts)

        def features_for(rows: list[dict[str, Any]]) -> np.ndarray:
            prompts_a = vectorizer.transform([row["prompt_a"] for row in rows]).toarray()
            prompts_b = vectorizer.transform([row["prompt_b"] for row in rows]).toarray()
            cosine_dist = np.asarray(
                [cosine_distance_row(a_vec, b_vec) for a_vec, b_vec in zip(prompts_a, prompts_b, strict=True)],
                dtype=float,
            )
            numeric = np.asarray(
                [
                    [
                        row["cue_diff"],
                        abs(row["cue_diff"]),
                        row["length_diff"],
                        abs(row["length_diff"]),
                        row["number_count_diff"],
                        abs(row["number_count_diff"]),
                        cosine_dist[idx],
                    ]
                    for idx, row in enumerate(rows)
                ],
                dtype=float,
            )
            return numeric

        x_train = features_for(train_rows)
        y_train = np.asarray([row["label_b_lower"] for row in train_rows], dtype=int)
        x_test = features_for(test_rows)
        y_test = np.asarray([row["label_b_lower"] for row in test_rows], dtype=int)

        scaler = StandardScaler().fit(x_train)
        x_train_scaled = scaler.transform(x_train)
        x_test_scaled = scaler.transform(x_test)

        clf = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=args.seed)
        clf.fit(x_train_scaled, y_train)
        test_probs = clf.predict_proba(x_test_scaled)[:, 1]
        test_preds = (test_probs >= 0.5).astype(int)

        pairwise_correct.extend((test_preds == y_test).astype(int).tolist())
        base_pair_probs = [
            float(prob)
            for row, prob in zip(test_rows, test_probs, strict=True)
            if row["variant_a"] == 0
        ]
        family_scores_directional[held_out_tid] = max(base_pair_probs) if base_pair_probs else float(np.mean(test_probs))
        family_scores_margin[held_out_tid] = float(np.mean(np.abs(test_probs - 0.5)))

        for row, truth, prob, pred in zip(test_rows, y_test, test_probs, test_preds, strict=True):
            pairwise_predictions.append(
                {
                    "template_id": held_out_tid,
                    "variant_a": int(row["variant_a"]),
                    "variant_b": int(row["variant_b"]),
                    "true_label_b_lower": int(truth),
                    "prediction_b_lower": float(prob),
                    "predicted_label_b_lower": int(pred),
                }
            )

    family_labels = np.asarray([family_label_map[tid] for tid in family_ids], dtype=int)
    family_score_directional_arr = np.asarray([family_scores_directional[tid] for tid in family_ids], dtype=float)
    family_score_margin_arr = np.asarray([family_scores_margin[tid] for tid in family_ids], dtype=float)

    summary = {
        "n_families": len(family_ids),
        "n_pairwise_samples": len(pairwise_predictions),
        "pairwise_accuracy": float(accuracy_score(np.asarray([row["true_label_b_lower"] for row in pairwise_predictions], dtype=int), np.asarray([row["predicted_label_b_lower"] for row in pairwise_predictions], dtype=int))),
        "family_level_auroc_directional": float(roc_auc_score(family_labels, family_score_directional_arr)),
        "family_level_auprc_directional": float(average_precision_score(family_labels, family_score_directional_arr)),
        "family_level_auroc_margin": float(roc_auc_score(family_labels, family_score_margin_arr)),
        "family_level_auprc_margin": float(average_precision_score(family_labels, family_score_margin_arr)),
        "family_score_definition_directional": "max_predicted_probability_that_a_nonbase_variant_has_lower_logprob_than_base_variant",
        "family_score_definition_margin": "mean_absolute_pairwise_prediction_margin_from_0.5_across_the_6_variant_pairs",
        "feature_definition": [
            "signed cue-value difference",
            "absolute cue-value difference",
            "signed prompt-length difference",
            "absolute prompt-length difference",
            "signed numeric-token-count difference",
            "absolute numeric-token-count difference",
            "TF-IDF cosine distance",
        ],
    }

    per_family_rows = [
        {
            "template_id": tid,
            "prediction_directional": float(family_scores_directional[tid]),
            "prediction_margin": float(family_scores_margin[tid]),
            "true_label": int(family_label_map[tid]),
        }
        for tid in family_ids
    ]

    write_json(output_dir / "blackbox_counterfactual_summary.json", summary)
    write_json(output_dir / "pairwise_predictions.json", pairwise_predictions)
    write_json(output_dir / "family_scores.json", per_family_rows)


if __name__ == "__main__":
    main()
