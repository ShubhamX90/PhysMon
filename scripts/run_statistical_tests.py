#!/usr/bin/env python3
"""Stage 9 statistical tests for Qwen vs DeepSeek and domain generalisation."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import chi2, fisher_exact, wilcoxon
from sklearn.metrics import roc_auc_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen-csv", required=True, help="Stage 6 per-family CSV.")
    parser.add_argument("--deepseek-csv", required=True, help="Stage 8 DeepSeek per-family CSV.")
    parser.add_argument("--qwen-slp-column", default="qwen_S_lp")
    parser.add_argument("--deepseek-slp-column", default="deepseek_S_lp")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--exclude-ids", nargs="*", default=())
    parser.add_argument(
        "--domain-predictions",
        default="results/stage6/probing/domain_generalisation/loo_predictions_variance.json",
        help="Domain-generalisation LOO predictions JSON.",
    )
    parser.add_argument(
        "--domain-summary",
        default="results/stage6/probing/domain_generalisation/summary_variance.json",
        help="Domain-generalisation summary JSON.",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=9)
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def slp_dict(rows: list[dict[str, str]], *, column: str, exclude_ids: set[str]) -> dict[str, float]:
    return {
        str(row["template_id"]): float(row[column] or 0.0)
        for row in rows
        if str(row["template_id"]) not in exclude_ids
    }


def row_map(rows: list[dict[str, str]], *, exclude_ids: set[str]) -> dict[str, dict[str, str]]:
    return {
        str(row["template_id"]): row
        for row in rows
        if str(row["template_id"]) not in exclude_ids
    }


def run_mcnemar_test(
    qwen_slp: dict[str, float],
    deepseek_slp: dict[str, float],
    *,
    threshold: float,
) -> dict[str, Any]:
    families = sorted(set(qwen_slp) & set(deepseek_slp))
    both_positive = qwen_only = deepseek_only = neither = 0
    table = [[0, 0], [0, 0]]
    for family_id in families:
        q_pos = qwen_slp[family_id] >= threshold
        d_pos = deepseek_slp[family_id] >= threshold
        if q_pos and d_pos:
            both_positive += 1
            table[0][0] += 1
        elif q_pos and not d_pos:
            qwen_only += 1
            table[0][1] += 1
        elif not q_pos and d_pos:
            deepseek_only += 1
            table[1][0] += 1
        else:
            neither += 1
            table[1][1] += 1

    discordant = qwen_only + deepseek_only
    statistic = 0.0 if discordant == 0 else ((qwen_only - deepseek_only) ** 2) / discordant
    p_value = float(chi2.sf(statistic, df=1))
    return {
        "both_positive": both_positive,
        "qwen_only": qwen_only,
        "deepseek_only": deepseek_only,
        "neither": neither,
        "contingency_table": table,
        "mcnemar_statistic": float(statistic),
        "p_value": p_value,
        "p_value_str": f"{p_value:.2e}",
        "significant_at_0.001": bool(p_value < 0.001),
    }


def run_wilcoxon_test(qwen_slp: dict[str, float], deepseek_slp: dict[str, float]) -> dict[str, Any]:
    families = sorted(set(qwen_slp) & set(deepseek_slp))
    q_values = np.asarray([qwen_slp[family_id] for family_id in families], dtype=float)
    d_values = np.asarray([deepseek_slp[family_id] for family_id in families], dtype=float)
    statistic, p_value = wilcoxon(q_values, d_values)
    return {
        "n_families": int(len(families)),
        "qwen_median_slp": float(np.median(q_values)),
        "deepseek_median_slp": float(np.median(d_values)),
        "median_qwen_minus_deepseek": float(np.median(q_values - d_values)),
        "wilcoxon_statistic": float(statistic),
        "p_value": float(p_value),
        "p_value_str": f"{float(p_value):.2e}",
        "significant_at_0.001": bool(float(p_value) < 0.001),
    }


def run_fisher_cue_type_test(
    qwen_rows: dict[str, dict[str, str]],
    qwen_slp: dict[str, float],
    deepseek_slp: dict[str, float],
    *,
    threshold: float,
) -> dict[str, Any]:
    cue_b_suppressed = cue_b_persisted = cue_c_suppressed = cue_c_persisted = 0
    for family_id, row in qwen_rows.items():
        cue_type = row.get("cue_type", "")
        q_pos = qwen_slp.get(family_id, 0.0) >= threshold
        d_pos = deepseek_slp.get(family_id, 0.0) >= threshold
        if cue_type == "nongoverning_distractor" and q_pos:
            if d_pos:
                cue_b_persisted += 1
            else:
                cue_b_suppressed += 1
        elif cue_type == "frame_rendering" and q_pos:
            if d_pos:
                cue_c_persisted += 1
            else:
                cue_c_suppressed += 1
    table = [
        [cue_b_suppressed, cue_b_persisted],
        [cue_c_suppressed, cue_c_persisted],
    ]
    odds_ratio, p_value = fisher_exact(table)
    return {
        "contingency_table": table,
        "cue_b_suppressed": cue_b_suppressed,
        "cue_b_persisted": cue_b_persisted,
        "cue_c_suppressed": cue_c_suppressed,
        "cue_c_persisted": cue_c_persisted,
        "odds_ratio": float(odds_ratio),
        "p_value": float(p_value),
        "p_value_str": f"{float(p_value):.2e}",
    }


def load_domain_predictions(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError(f"Expected list payload in {path}.")
    return payload


def permutation_test_domain_gen(
    *,
    family_domain_map: dict[str, str],
    family_labels: dict[str, int],
    family_predictions: dict[str, float],
    observed_macro_auroc: float,
    n_permutations: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    families = sorted(set(family_domain_map) & set(family_labels) & set(family_predictions))
    domains = [family_domain_map[family_id] for family_id in families]
    unique_domains = sorted(set(domains))
    null_aurocs: list[float] = []
    for _ in range(n_permutations):
        shuffled_domains = rng.permutation(domains)
        shuffled_map = dict(zip(families, shuffled_domains, strict=True))
        domain_scores: list[float] = []
        for held_out_domain in unique_domains:
            test_families = [family_id for family_id in families if shuffled_map[family_id] == held_out_domain]
            if len(test_families) < 3:
                continue
            labels = np.asarray([family_labels[family_id] for family_id in test_families], dtype=int)
            scores = np.asarray([family_predictions[family_id] for family_id in test_families], dtype=float)
            if len(np.unique(labels)) < 2:
                continue
            domain_scores.append(float(roc_auc_score(labels, scores)))
        if domain_scores:
            null_aurocs.append(float(np.mean(domain_scores)))

    return {
        "observed_macro_auroc": float(observed_macro_auroc),
        "null_mean": float(np.mean(null_aurocs)),
        "null_std": float(np.std(null_aurocs)),
        "n_permutations": int(n_permutations),
        "p_value": float(np.mean(np.asarray(null_aurocs) >= observed_macro_auroc)),
        "p_value_str": f"{float(np.mean(np.asarray(null_aurocs) >= observed_macro_auroc)):.4f}",
        "significant_at_0.05": bool(float(np.mean(np.asarray(null_aurocs) >= observed_macro_auroc)) < 0.05),
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    exclude_ids = set(args.exclude_ids)

    qwen_rows_list = load_csv_rows(Path(args.qwen_csv))
    deepseek_rows_list = load_csv_rows(Path(args.deepseek_csv))
    qwen_rows = row_map(qwen_rows_list, exclude_ids=exclude_ids)
    qwen_slp = slp_dict(qwen_rows_list, column=args.qwen_slp_column, exclude_ids=exclude_ids)
    deepseek_slp = slp_dict(deepseek_rows_list, column=args.deepseek_slp_column, exclude_ids=exclude_ids)

    mcnemar_result = run_mcnemar_test(qwen_slp, deepseek_slp, threshold=args.threshold)
    wilcoxon_result = run_wilcoxon_test(qwen_slp, deepseek_slp)
    fisher_result = run_fisher_cue_type_test(
        qwen_rows,
        qwen_slp,
        deepseek_slp,
        threshold=args.threshold,
    )

    domain_summary = json.loads(Path(args.domain_summary).read_text(encoding="utf-8"))
    fold_metrics = domain_summary.get("domain_fold_metrics", [])
    if fold_metrics:
        observed_macro = float(np.mean([float(item["auroc"]) for item in fold_metrics]))
    else:
        observed_macro = float(domain_summary["best_auroc"])
    best_layer = int(domain_summary["best_layer"])
    domain_prediction_rows = load_domain_predictions(Path(args.domain_predictions))
    best_rows = [row for row in domain_prediction_rows if int(row["layer_index"]) == best_layer]
    family_domain_map = {family_id: row["domain"] for family_id, row in qwen_rows.items()}
    family_labels = {str(row["template_id"]): int(row["true_label"]) for row in best_rows}
    family_predictions = {str(row["template_id"]): float(row["prediction"]) for row in best_rows}
    permutation_result = permutation_test_domain_gen(
        family_domain_map=family_domain_map,
        family_labels=family_labels,
        family_predictions=family_predictions,
        observed_macro_auroc=observed_macro,
        n_permutations=args.n_permutations,
        seed=args.seed,
    )

    save_json(output_dir / "mcnemar_qwen_vs_deepseek.json", mcnemar_result)
    save_json(output_dir / "wilcoxon_continuous_slp.json", wilcoxon_result)
    save_json(output_dir / "fisher_cue_type_suppression.json", fisher_result)
    save_json(output_dir / "permutation_domain_gen.json", permutation_result)
    save_json(
        output_dir / "statistical_summary.json",
        {
            "stage": args.stage,
            "threshold": args.threshold,
            "mcnemar_qwen_vs_deepseek": mcnemar_result,
            "wilcoxon_continuous_slp": wilcoxon_result,
            "fisher_cue_type_suppression": fisher_result,
            "permutation_domain_gen": permutation_result,
        },
    )


if __name__ == "__main__":
    main()
