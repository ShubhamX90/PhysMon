#!/usr/bin/env python3
"""Analyse Stage 4 behavioural outputs and compute pilot sensitivity summaries.

Reference:
    `physmon_proposal.pdf` §3.3, §10, §11 and the Stage 4 brief Part D.
"""

from __future__ import annotations

import argparse
import csv
from glob import glob
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from physmon.utils.io import ensure_parent_dir, read_yaml, write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 4
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "analyse_stage4_events.jsonl"
PRIMARY_FLIP_GATE_COUNT = 6
MODEL_KEYS = ("qwen_primary", "llama_primary")
THRESHOLD_TARGET_RATES = (0.2, 0.3, 0.4)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Stage 4 analysis."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen-output", required=True, help="Glob or path for the Qwen Stage 4 JSONL.")
    parser.add_argument("--llama-output", required=True, help="Glob or path for the Llama Stage 4 JSONL.")
    parser.add_argument("--output-dir", required=True, help="Directory for Stage 4 analysis artifacts.")
    parser.add_argument(
        "--template-dir",
        default="data/raw/templates",
        help="Directory containing canonical template YAML files.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic split seed.")
    return parser.parse_args()


def resolve_single_path(path_or_glob: str) -> Path:
    """Resolve one exact file path from a direct path or a glob pattern."""

    matches = sorted(glob(path_or_glob))
    if not matches:
        raise FileNotFoundError(f"No files match {path_or_glob!r}.")
    if len(matches) > 1:
        raise ValueError(f"Expected exactly one match for {path_or_glob!r}, found {matches}.")
    return Path(matches[0])


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise TypeError(f"Expected JSON object at {path}:{line_number}, found {type(payload)!r}.")
            rows.append(payload)
    return rows


def build_family_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group mixed variant/family-summary records by template id."""

    families: dict[str, dict[str, Any]] = {}
    for record in records:
        template_id = str(record["template_id"])
        family_bucket = families.setdefault(template_id, {"variants": [], "summary": None})
        record_type = record.get("record_type")
        if record_type == "variant_record":
            family_bucket["variants"].append(record)
        elif record_type == "family_summary":
            family_bucket["summary"] = record
        else:
            raise ValueError(f"Unexpected record_type={record_type!r} for template {template_id}.")
    return families


def recompute_hat_s(variant_records: list[dict[str, Any]]) -> tuple[float | None, int]:
    """Recompute answer-flip sensitivity from parsed answers."""

    confident_records = [
        record
        for record in sorted(variant_records, key=lambda item: int(item["variant_id"]))
        if record.get("parse_confident") and record.get("parsed_answer") is not None
    ]
    num_valid_parses = len(confident_records)
    if num_valid_parses < 2:
        return None, num_valid_parses
    parsed_answers = [str(record["parsed_answer"]) for record in confident_records]
    comparisons = 0
    flips = 0
    for left_index in range(len(parsed_answers)):
        for right_index in range(left_index + 1, len(parsed_answers)):
            comparisons += 1
            flips += int(parsed_answers[left_index] != parsed_answers[right_index])
    return flips / comparisons, num_valid_parses


def recompute_logprob_drop(variant_records: list[dict[str, Any]]) -> float | None:
    """Recompute max log-probability drop from the base variant."""

    ordered_records = sorted(variant_records, key=lambda item: int(item["variant_id"]))
    base_record = next((record for record in ordered_records if int(record["variant_id"]) == 0), None)
    if base_record is None or base_record.get("logprob_correct_answer") is None:
        return None
    base_logprob = float(base_record["logprob_correct_answer"])
    drops: list[float] = []
    for record in ordered_records:
        logprob_value = record.get("logprob_correct_answer")
        if logprob_value is None:
            continue
        drops.append(base_logprob - float(logprob_value))
    return max(drops) if drops else None


def compute_summary_stats(values: list[float]) -> dict[str, float]:
    """Compute robust summary statistics for one list of sensitivity values."""

    if not values:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "max": 0.0,
        }
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "p25": float(np.quantile(array, 0.25)),
        "p75": float(np.quantile(array, 0.75)),
        "max": float(array.max()),
    }


def choose_thresholds(train_scores: list[float]) -> dict[str, dict[str, float]]:
    """Choose candidate thresholds targeting approximate positive-class rates."""

    if not train_scores:
        return {}
    score_array = np.asarray(sorted(set(train_scores)), dtype=float)
    candidates: dict[str, dict[str, float]] = {}
    for target_rate in THRESHOLD_TARGET_RATES:
        best_threshold = float(score_array[0])
        best_rate = float(np.mean(np.asarray(train_scores) >= best_threshold))
        best_error = abs(best_rate - target_rate)
        for threshold in score_array:
            observed_rate = float(np.mean(np.asarray(train_scores) >= float(threshold)))
            observed_error = abs(observed_rate - target_rate)
            if observed_error < best_error:
                best_threshold = float(threshold)
                best_rate = observed_rate
                best_error = observed_error
        candidates[f"target_{int(target_rate * 100)}pct"] = {
            "threshold": best_threshold,
            "observed_positive_rate": best_rate,
        }
    return candidates


def load_template_metadata(template_dir: Path, template_id: str) -> dict[str, Any]:
    """Load template metadata needed for the per-family CSV."""

    payload = read_yaml(template_dir / f"{template_id}.yaml")
    return {
        "domain": payload["domain"],
        "cue_type": payload["cue_type"],
        "governing_law": payload["governing_law"],
    }


def write_per_family_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Write the Stage 4 per-family comparison table."""

    fieldnames = [
        "template_id",
        "domain",
        "cue_type",
        "governing_law",
        "qwen_hat_S",
        "qwen_S_lp",
        "llama_hat_S",
        "llama_S_lp",
        "qwen_parse_ok",
        "llama_parse_ok",
        "both_sensitive",
        "notes",
    ]
    output_file = ensure_parent_dir(output_path)
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_histograms(
    qwen_values: list[float],
    llama_values: list[float],
    output_path: Path,
) -> None:
    """Render the two-panel pilot sensitivity histogram figure."""

    figure, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for axis, values, title in zip(
        axes,
        (qwen_values, llama_values),
        ("Qwen", "Llama"),
        strict=True,
    ):
        data = np.asarray(values or [0.0], dtype=float)
        axis.hist(data, bins=min(10, max(3, len(data))), color="#4C78A8", alpha=0.85)
        for quantile_value, color in zip(
            (np.quantile(data, 0.2), np.quantile(data, 0.4)),
            ("#F58518", "#54A24B"),
            strict=True,
        ):
            axis.axvline(float(quantile_value), color=color, linestyle="--", linewidth=1.5)
        axis.set_title(title)
        axis.set_xlabel(r"$\hat{S}_\theta$")
    axes[0].set_ylabel("Family Count")
    figure.suptitle("Pilot Family Sensitivity Distribution (N=30)")
    figure.tight_layout()
    ensure_parent_dir(output_path)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def main() -> None:
    """Run the full Stage 4 analysis pipeline."""

    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="analyse_stage4.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )

    qwen_path = resolve_single_path(args.qwen_output)
    llama_path = resolve_single_path(args.llama_output)
    template_dir = Path(args.template_dir)

    model_payloads = {
        "qwen_primary": build_family_index(load_jsonl(qwen_path)),
        "llama_primary": build_family_index(load_jsonl(llama_path)),
    }
    all_template_ids = sorted(set(model_payloads["qwen_primary"]) | set(model_payloads["llama_primary"]))
    per_model_summary: dict[str, dict[str, Any]] = {}
    per_family_rows: list[dict[str, Any]] = []
    per_model_hat_s: dict[str, list[float]] = {model_key: [] for model_key in MODEL_KEYS}
    primary_any_flip_count = 0
    cross_counts = {
        "families_both_sensitive": 0,
        "families_only_qwen_sensitive": 0,
        "families_only_llama_sensitive": 0,
        "families_neither_sensitive": 0,
    }

    for model_key in MODEL_KEYS:
        family_map = model_payloads[model_key]
        hat_s_values: list[float] = []
        logprob_values: list[float] = []
        degraded_families: list[str] = []
        total_variants = 0
        successful_parses = 0
        exact_answer_matches = 0

        for template_id, bundle in family_map.items():
            variant_records = bundle["variants"]
            total_variants += len(variant_records)
            successful_parses += sum(
                int(record.get("parse_confident") and record.get("parsed_answer") is not None)
                for record in variant_records
            )
            exact_answer_matches += sum(
                int(record.get("parsed_answer") == record.get("correct_answer"))
                for record in variant_records
                if record.get("parsed_answer") is not None
            )
            hat_s_value, num_valid_parses = recompute_hat_s(variant_records)
            if num_valid_parses < 4:
                degraded_families.append(template_id)
            if hat_s_value is not None:
                hat_s_values.append(hat_s_value)
            logprob_drop = recompute_logprob_drop(variant_records)
            if logprob_drop is not None:
                logprob_values.append(logprob_drop)
            summary_record = bundle["summary"]
            if summary_record is not None and summary_record.get("answer_flip_rate") not in {None, hat_s_value}:
                logger.log_event(
                    "FAMILY_SUMMARY_MISMATCH",
                    model_key=model_key,
                    template_id=template_id,
                    reported_answer_flip_rate=summary_record.get("answer_flip_rate"),
                    recomputed_answer_flip_rate=hat_s_value,
                )

        per_model_hat_s[model_key] = hat_s_values
        summary_stats = compute_summary_stats(hat_s_values)
        logprob_stats = compute_summary_stats(logprob_values)
        families_with_any_flip = sum(value > 0.0 for value in hat_s_values)
        per_model_summary[model_key] = {
            "families_with_any_flip": families_with_any_flip,
            "pct_families_with_any_flip": families_with_any_flip / max(len(family_map), 1),
            "hat_S_theta_mean": summary_stats["mean"],
            "hat_S_theta_median": summary_stats["median"],
            "hat_S_theta_p25": summary_stats["p25"],
            "hat_S_theta_p75": summary_stats["p75"],
            "hat_S_theta_max": summary_stats["max"],
            "S_lp_theta_mean": logprob_stats["mean"],
            "parse_success_rate": successful_parses / max(total_variants, 1),
            "answer_correct_rate": exact_answer_matches / max(successful_parses, 1),
            "families_degraded": degraded_families,
        }

    for template_id in all_template_ids:
        metadata = load_template_metadata(template_dir, template_id)
        qwen_bundle = model_payloads["qwen_primary"][template_id]
        llama_bundle = model_payloads["llama_primary"][template_id]
        qwen_hat_s, qwen_valid_parses = recompute_hat_s(qwen_bundle["variants"])
        llama_hat_s, llama_valid_parses = recompute_hat_s(llama_bundle["variants"])
        qwen_sensitive = bool(qwen_hat_s is not None and qwen_hat_s > 0.0)
        llama_sensitive = bool(llama_hat_s is not None and llama_hat_s > 0.0)
        if qwen_sensitive and llama_sensitive:
            cross_counts["families_both_sensitive"] += 1
        elif qwen_sensitive:
            cross_counts["families_only_qwen_sensitive"] += 1
        elif llama_sensitive:
            cross_counts["families_only_llama_sensitive"] += 1
        else:
            cross_counts["families_neither_sensitive"] += 1
        primary_any_flip_count += int(qwen_sensitive or llama_sensitive)

        notes: list[str] = []
        if qwen_valid_parses < 4:
            notes.append("qwen_degraded")
        if llama_valid_parses < 4:
            notes.append("llama_degraded")

        per_family_rows.append(
            {
                "template_id": template_id,
                "domain": metadata["domain"],
                "cue_type": metadata["cue_type"],
                "governing_law": metadata["governing_law"],
                "qwen_hat_S": "" if qwen_hat_s is None else qwen_hat_s,
                "qwen_S_lp": "" if (qwen_logprob := recompute_logprob_drop(qwen_bundle["variants"])) is None else qwen_logprob,
                "llama_hat_S": "" if llama_hat_s is None else llama_hat_s,
                "llama_S_lp": "" if (llama_logprob := recompute_logprob_drop(llama_bundle["variants"])) is None else llama_logprob,
                "qwen_parse_ok": qwen_valid_parses == 4,
                "llama_parse_ok": llama_valid_parses == 4,
                "both_sensitive": qwen_sensitive and llama_sensitive,
                "notes": ";".join(notes),
            }
        )

    rng = np.random.default_rng(args.seed)
    shuffled_template_ids = all_template_ids.copy()
    rng.shuffle(shuffled_template_ids)
    split_index = int(round(len(shuffled_template_ids) * 0.7))
    train_template_ids = set(shuffled_template_ids[:split_index])
    threshold_candidates = {
        model_key: choose_thresholds(
            [
                float(row[f"{model_key.split('_')[0]}_hat_S"])
                for row in per_family_rows
                if row["template_id"] in train_template_ids and row[f"{model_key.split('_')[0]}_hat_S"] != ""
            ]
        )
        for model_key in MODEL_KEYS
    }

    gate_4_pass = primary_any_flip_count >= PRIMARY_FLIP_GATE_COUNT
    gate_4_evidence = (
        f"{primary_any_flip_count} of {len(all_template_ids)} pilot families showed at least one answer "
        f"flip on at least one PRIMARY_DENSE model (threshold for PASS: >= {PRIMARY_FLIP_GATE_COUNT})."
    )
    summary_payload = {
        "qwen_primary": per_model_summary["qwen_primary"],
        "llama_primary": per_model_summary["llama_primary"],
        "cross_model": {
            **cross_counts,
            "families_with_any_primary_flip": primary_any_flip_count,
        },
        "threshold_candidates": threshold_candidates,
        "gate_4_pass": gate_4_pass,
        "gate_4_evidence": gate_4_evidence,
    }

    write_json(output_dir / "stage4_sensitivity_summary.json", summary_payload)
    write_per_family_csv(sorted(per_family_rows, key=lambda row: row["template_id"]), output_dir / "stage4_per_family.csv")
    plot_histograms(
        per_model_hat_s["qwen_primary"],
        per_model_hat_s["llama_primary"],
        output_dir / "stage4_sensitivity_hist.png",
    )
    logger.log_event(
        "STAGE4_ANALYSIS_COMPLETE",
        qwen_output=str(qwen_path.resolve()),
        llama_output=str(llama_path.resolve()),
        gate_4_pass=gate_4_pass,
        gate_4_evidence=gate_4_evidence,
    )


if __name__ == "__main__":
    main()
