#!/usr/bin/env python3
"""Stage 13 v4 balance/confound audit with grouped CV and tie-aware AUROC."""

from __future__ import annotations

import argparse
import json
import math
import random
import re
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from governance_utils import REPO_ROOT, read_csv, write_csv, write_json


NUMERIC_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?", re.I)
VARIABLE_RE = re.compile(r"\b[a-zA-Z](?:_[a-zA-Z0-9]+)?\b")
UNIT_RE = re.compile(r"\b(?:m/s|m/s²|m/s\\^2|N|J|C|V|Pa|kg|K|Hz|rpm|atm|bar|kJ|mC)\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", default="results/canonical/model_family_evidence.csv")
    parser.add_argument("--manifest", default="data/manifests/physmon_canonical_155.jsonl")
    parser.add_argument("--output", default="results/stage13/benchmark_integrity/balance_audit_v3.json")
    parser.add_argument("--fold-output", default="results/stage13/benchmark_integrity/balance_audit_v3_folds.csv")
    parser.add_argument(
        "--prediction-output",
        default="results/stage13/benchmark_integrity/balance_audit_v3_predictions.csv",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_manifest(path: str) -> dict[str, dict[str, Any]]:
    rows = {}
    for line in (REPO_ROOT / path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("is_canonical") is True:
            rows[row["canonical_family_id"]] = row
    return rows


def family_payload(source_path: str) -> dict[str, Any]:
    return json.loads((REPO_ROOT / source_path).read_text(encoding="utf-8"))


def answer_magnitude(answer: str) -> float | None:
    match = NUMERIC_RE.search(str(answer))
    return abs(float(match.group(0))) if match else None


def answer_sign(answer: str) -> str:
    match = NUMERIC_RE.search(str(answer))
    if not match:
        return "unknown"
    value = float(match.group(0))
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


def answer_format(answer: str) -> str:
    text = str(answer)
    if re.search(r"\d+(?:\.\d+)?e[-+]?\d+", text, re.I):
        return "scientific"
    if "." in text:
        return "decimal"
    if "/" in text and re.search(r"\d+\s*/\s*\d+", text):
        return "fraction"
    if re.search(r"\d", text):
        return "integer_like"
    return "textual"


def template_cluster(fid: str) -> str:
    return re.sub(r"_\d+$", "", fid)


def prompt_features(payload: dict[str, Any]) -> dict[str, float]:
    prompts = [str(variant.get("prompt", "")) for variant in payload.get("variants", [])]
    joined = "\n".join(prompts)
    mean_len = float(np.mean([len(prompt) for prompt in prompts])) if prompts else 0.0
    mean_tokens = float(np.mean([len(prompt.split()) for prompt in prompts])) if prompts else 0.0
    return {
        "prompt_length": mean_len,
        "token_count": mean_tokens,
        "number_count": float(len(NUMERIC_RE.findall(joined))),
        "variable_count": float(len(set(VARIABLE_RE.findall(joined)))),
        "equation_count": float(joined.count("=")),
        "unit_token_count": float(len(UNIT_RE.findall(joined))),
    }


def to_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def build_rows(family_csv: str, manifest_path: str) -> list[dict[str, Any]]:
    manifest = load_manifest(manifest_path)
    rows = []
    for row in read_csv(family_csv):
        if row.get("model_id") != "qwen2p5_7b_instruct":
            continue
        fid = row["canonical_family_id"]
        manifest_row = manifest.get(fid)
        if not manifest_row:
            continue
        payload = family_payload(manifest_row["source_family_path"])
        slp_binary = int(float(row.get("S_lp_binary") or 0) >= 1)
        features = prompt_features(payload)
        answer = row.get("canonical_answer") or payload.get("correct_answer", "")
        features.update(
            {
                "answer_magnitude": answer_magnitude(answer),
                "base_correctness": 1.0 if str(row.get("base_variant_correct")).lower() == "true" else 0.0,
                "entropy": to_float(row.get("entropy_score")),
                "domain": row.get("domain") or payload.get("domain", "unknown"),
                "cue_type": row.get("cue_type") or payload.get("cue_type", "unknown"),
                "answer_sign": answer_sign(answer),
                "answer_format": answer_format(answer),
                "template_cluster": template_cluster(fid),
            }
        )
        rows.append({"family_id": fid, "label": slp_binary, **features})
    return rows


def safe_roc_auc(labels: list[int], values: list[float]) -> float | None:
    if len(set(labels)) < 2 or len(set(values)) < 2:
        return None
    return float(roc_auc_score(labels, values))


def bootstrap_ci(labels: list[int], scores: list[float], seed: int, n: int = 500) -> list[float | None]:
    rng = random.Random(seed)
    aucs = []
    indices = list(range(len(labels)))
    for _ in range(n):
        sample = [rng.choice(indices) for _ in indices]
        y = [labels[i] for i in sample]
        s = [scores[i] for i in sample]
        auc = safe_roc_auc(y, s)
        if auc is not None:
            aucs.append(auc)
    if not aucs:
        return [None, None]
    return [float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))]


def bh_adjust(p_values: dict[str, float | None]) -> dict[str, float | None]:
    valid = sorted((p, key) for key, p in p_values.items() if p is not None and not math.isnan(p))
    m = len(valid)
    adjusted: dict[str, float | None] = {key: None for key in p_values}
    prev = 1.0
    for rank, (p, key) in enumerate(reversed(valid), start=1):
        original_rank = m - rank + 1
        value = min(prev, p * m / original_rank)
        adjusted[key] = float(min(value, 1.0))
        prev = value
    return adjusted


def univariate(rows: list[dict[str, Any]], numeric: list[str]) -> dict[str, dict[str, Any]]:
    result = {}
    p_values = {}
    for feature in numeric:
        pairs = [(int(row["label"]), row.get(feature)) for row in rows if row.get(feature) is not None]
        y = [label for label, _ in pairs]
        x = [float(value) for _, value in pairs]
        pos = [value for label, value in zip(y, x) if label == 1]
        neg = [value for label, value in zip(y, x) if label == 0]
        pooled = float(np.std(x)) if len(x) > 1 else 0.0
        auc = safe_roc_auc(y, x)
        p_val = None
        if len(set(y)) > 1 and len(set(x)) > 1:
            p_val = float(stats.mannwhitneyu(pos, neg, alternative="two-sided").pvalue) if pos and neg else None
        p_values[feature] = p_val
        result[feature] = {
            "n": len(x),
            "positive_mean": float(np.mean(pos)) if pos else None,
            "negative_mean": float(np.mean(neg)) if neg else None,
            "standardized_effect": ((float(np.mean(pos)) - float(np.mean(neg))) / pooled) if pos and neg and pooled else None,
            "pearson": float(stats.pearsonr(x, y).statistic) if len(set(x)) > 1 and len(set(y)) > 1 else None,
            "spearman": float(stats.spearmanr(x, y).statistic) if len(set(x)) > 1 and len(set(y)) > 1 else None,
            "single_feature_auroc": auc,
            "orientation_independent_auroc": max(auc, 1.0 - auc) if auc is not None else None,
            "mann_whitney_p": p_val,
        }
    adjusted = bh_adjust(p_values)
    for feature, p_val in adjusted.items():
        result[feature]["benjamini_hochberg_q"] = p_val
    return result


def grouped_cv(rows: list[dict[str, Any]], numeric: list[str], categorical: list[str], seed: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    labels = np.array([int(row["label"]) for row in rows])
    groups = np.array([row["family_id"] for row in rows])
    X = pd.DataFrame([{feature: row.get(feature) for feature in numeric + categorical} for row in rows])
    pre = ColumnTransformer(
        [
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )
    model = Pipeline(
        [
            ("preprocess", pre),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear")),
        ]
    )
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    scores = np.zeros(len(rows))
    fold_rows = []
    pred_rows = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(X, labels, groups), start=1):
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]
        model.fit(X_train, labels[train_idx])
        fold_scores = model.predict_proba(X_test)[:, 1]
        scores[test_idx] = fold_scores
        for i in train_idx:
            fold_rows.append({"fold": fold, "family_id": rows[i]["family_id"], "split": "train", "label": int(labels[i])})
        for i, score in zip(test_idx, fold_scores):
            fold_rows.append({"fold": fold, "family_id": rows[i]["family_id"], "split": "test", "label": int(labels[i])})
            pred_rows.append(
                {
                    "family_id": rows[i]["family_id"],
                    "fold": fold,
                    "label": int(labels[i]),
                    "oof_surface_score": float(score),
                }
            )
    auc = safe_roc_auc(labels.tolist(), scores.tolist())
    rng = np.random.default_rng(seed)
    perm_aucs = []
    for _ in range(200):
        perm = rng.permutation(labels)
        perm_auc = safe_roc_auc(perm.tolist(), scores.tolist())
        if perm_auc is not None:
            perm_aucs.append(perm_auc)
    p_value = None
    if auc is not None and perm_aucs:
        p_value = float((sum(value >= auc for value in perm_aucs) + 1) / (len(perm_aucs) + 1))
    summary = {
        "combined_grouped_cv_auroc": auc,
        "combined_grouped_cv_ci95": bootstrap_ci(labels.tolist(), scores.tolist(), seed),
        "permutation_test_p": p_value,
        "n_folds": 5,
        "n_oof_predictions": len(pred_rows),
    }
    return summary, fold_rows, pred_rows


def main() -> None:
    args = parse_args()
    rows = build_rows(args.family, args.manifest)
    numeric = [
        "answer_magnitude",
        "prompt_length",
        "token_count",
        "number_count",
        "variable_count",
        "equation_count",
        "unit_token_count",
        "base_correctness",
        "entropy",
    ]
    categorical = ["domain", "cue_type", "answer_sign", "answer_format", "template_cluster"]
    uni = univariate(rows, numeric)
    cv, folds, predictions = grouped_cv(rows, numeric, categorical, args.seed)
    strongest = max(
        uni.items(),
        key=lambda item: item[1]["orientation_independent_auroc"] or 0.0,
    )
    out = {
        "status": "VALID_GROUPED_CV_AUDIT",
        "supersedes": "results/stage13/benchmark_integrity/balance_audit_v2.json",
        "n_families": len(rows),
        "features": {"numeric": numeric, "categorical": categorical},
        "descriptive_by_label": dict(Counter(row["label"] for row in rows)),
        "single_feature_audits": uni,
        "combined_surface_model": cv,
        "strongest_confound": {
            "feature": strongest[0],
            "orientation_independent_auroc": strongest[1]["orientation_independent_auroc"],
        },
        "correction_method": "Benjamini-Hochberg over univariate Mann-Whitney tests; sklearn tie-aware AUROC.",
        "fold_assignments": args.fold_output,
        "prediction_output": args.prediction_output,
    }
    write_json(args.output, out)
    write_csv(args.fold_output, folds, ["fold", "family_id", "split", "label"])
    write_csv(args.prediction_output, predictions, ["family_id", "fold", "label", "oof_surface_score"])


if __name__ == "__main__":
    main()
