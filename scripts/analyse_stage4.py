#!/usr/bin/env python3
# ruff: noqa: E402
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
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.benchmark.parser import parse_answer  # noqa: E402
from physmon.utils.io import ensure_parent_dir, read_yaml, write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402


DEFAULT_STAGE = 4
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "analyse_stage4_events.jsonl"
PRIMARY_FLIP_GATE_COUNT = 6
STAGE6_POSITIVE_GATE_COUNT = 12
MODEL_KEYS = ("qwen_primary", "llama_primary")
THRESHOLD_TARGET_RATES = (0.2, 0.3, 0.4)
SUSPECT_FAMILY_FLAGS = {
    ("llama_primary", "EL_A_004"): "degraded_calculation_error",
    ("llama_primary", "EL_A_005"): "suspect_single_variant_anomaly",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Stage 4 analysis."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen-output", help="Glob or path for the Qwen Stage 4 JSONL.")
    parser.add_argument("--llama-output", help="Glob or path for the Llama Stage 4 JSONL.")
    parser.add_argument(
        "--jsonl-glob",
        help=(
            "Glob matching behavioural JSONL files for both primary models. "
            "Used by Stage 6 D1 to auto-detect the Qwen and Llama outputs."
        ),
    )
    parser.add_argument("--output-dir", required=True, help="Directory for Stage 4 analysis artifacts.")
    parser.add_argument(
        "--template-dir",
        default="data/raw/templates",
        help="Directory containing canonical template YAML files.",
    )
    parser.add_argument(
        "--repair-run",
        nargs="?",
        const=True,
        default=False,
        type=parse_optional_bool,
        help="Annotate outputs as the repaired Stage 4 measurement and compare against the original run.",
    )
    parser.add_argument(
        "--reparse",
        nargs="?",
        const=True,
        default=False,
        type=parse_optional_bool,
        help="Re-parse generated_text and ignore parsed_answer fields stored in JSONL.",
    )
    parser.add_argument(
        "--original-per-family",
        default="results/stage4/analysis/stage4_per_family.csv",
        help="Original Stage 4 per-family CSV used for S_lp comparison during repair analysis.",
    )
    parser.add_argument(
        "--prior-repair-per-family",
        default="results/stage4_repair/analysis/stage4_per_family.csv",
        help="Prior repair-run per-family CSV used to verify S_lp stability after reparsing.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic split seed.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Binary S_lp threshold used for Stage 6 positive-rate checks.",
    )
    parser.add_argument(
        "--plot-only",
        action="store_true",
        help=(
            "Regenerate only the histogram from an existing per-family CSV in the output directory. "
            "This skips the JSONL analysis computation."
        ),
    )
    return parser.parse_args()


def parse_optional_bool(raw_value: str | None) -> bool:
    """Accept either `--flag` or `--flag true/false` command-line forms."""

    if raw_value is None:
        return True
    lowered = raw_value.strip().lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got {raw_value!r}.")


def resolve_single_path(path_or_glob: str) -> Path:
    """Resolve one exact file path from a direct path or a glob pattern."""

    matches = sorted(glob(path_or_glob))
    if not matches:
        raise FileNotFoundError(f"No files match {path_or_glob!r}.")
    if len(matches) > 1:
        raise ValueError(f"Expected exactly one match for {path_or_glob!r}, found {matches}.")
    return Path(matches[0])


def resolve_model_paths_from_glob(path_glob: str) -> dict[str, Path]:
    """Resolve one behavioural JSONL path per primary model from a shared glob."""

    matches = [Path(path) for path in sorted(glob(path_glob))]
    if not matches:
        raise FileNotFoundError(f"No files match {path_glob!r}.")

    resolved: dict[str, Path] = {}
    for path in matches:
        if path.name.startswith("qwen_primary_"):
            resolved["qwen_primary"] = path
        elif path.name.startswith("llama_primary_"):
            resolved["llama_primary"] = path

    missing = [model_key for model_key in MODEL_KEYS if model_key not in resolved]
    if missing:
        raise FileNotFoundError(
            f"Could not resolve behavioural JSONL files for {missing} from glob {path_glob!r}."
        )
    return resolved


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


def expected_unit_for_record(record: dict[str, Any]) -> str | None:
    """Recover the expected answer unit from the gold answer when one exists."""

    gold = canonical_correct_answer(record)
    if gold is None or " " not in gold:
        return None
    return gold.split(" ", maxsplit=1)[1]


def canonical_correct_answer(record: dict[str, Any]) -> str | None:
    """Normalize the stored gold answer using the same parser used for generations."""

    correct_answer = record.get("correct_answer")
    if not isinstance(correct_answer, str) or not correct_answer.strip():
        return None
    return parse_answer(correct_answer).answer


def reparse_variant_record(record: dict[str, Any]) -> dict[str, Any]:
    """Recompute parsed-answer fields from the raw generated text."""

    reparsed = dict(record)
    generated_text = reparsed.get("generated_text")
    if not isinstance(generated_text, str) or not generated_text.strip():
        reparsed["parsed_answer"] = None
        reparsed["parsed_answer_canonical"] = None
        reparsed["parse_confidence"] = 0.0
        reparsed["parse_confident"] = False
        return reparsed

    parse_result = parse_answer(generated_text, expected_unit=expected_unit_for_record(reparsed))
    reparsed["parsed_answer"] = parse_result.display_answer
    reparsed["parsed_answer_canonical"] = parse_result.answer
    reparsed["parse_confidence"] = parse_result.confidence
    reparsed["parse_confident"] = parse_result.is_confident
    return reparsed


def stored_canonical_answer(record: dict[str, Any]) -> str | None:
    """Read the canonical parsed answer from a variant record."""

    canonical = record.get("parsed_answer_canonical")
    if isinstance(canonical, str) and canonical.strip():
        return canonical
    parsed_answer = record.get("parsed_answer")
    if isinstance(parsed_answer, str) and parsed_answer.strip():
        return parsed_answer
    return None


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
        if record.get("parse_confident") and stored_canonical_answer(record) is not None
    ]
    num_valid_parses = len(confident_records)
    if num_valid_parses < 2:
        return None, num_valid_parses
    parsed_answers = [str(stored_canonical_answer(record)) for record in confident_records]
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


def flag_artifact_family(
    *,
    model_key: str,
    template_id: str,
    raw_hat_s: float | None,
) -> tuple[str | None, bool]:
    """Return any hard-coded artifact flag and whether to exclude it from clean hat_S counts."""

    if raw_hat_s is None or raw_hat_s <= 0.0:
        return None, False
    flag = SUSPECT_FAMILY_FLAGS.get((model_key, template_id))
    if flag is None:
        return None, False
    return flag, True


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


def stage6_class_name(template_id: str) -> str | None:
    """Map Stage 6 Phase 1 template ids to their semantic class bucket."""

    if not template_id.startswith("CM_B_UM_"):
        return None
    suffix = int(template_id.rsplit("_", maxsplit=1)[1])
    if 1 <= suffix <= 8:
        return "force_force"
    if 9 <= suffix <= 14:
        return "velocity_velocity"
    if 15 <= suffix <= 20:
        return "current_current"
    if 21 <= suffix <= 26:
        return "voltage_voltage"
    if 27 <= suffix <= 31:
        return "torque_torque"
    if 32 <= suffix <= 36:
        return "frequency_frequency"
    if 37 <= suffix <= 40:
        return "charge_charge"
    return None


def infer_output_prefix(output_dir: Path, args: argparse.Namespace) -> str:
    """Infer the output filename prefix for the current analysis run."""

    if args.plot_only and args.jsonl_glob and output_dir.name == "analysis_d2":
        return "stage6_d2"
    return "stage6_d1" if args.jsonl_glob else "stage4"


def compute_stage6_class_summary(
    rows: list[dict[str, Any]],
    *,
    model_key: str,
    threshold: float,
) -> dict[str, dict[str, float | int]]:
    """Aggregate Stage 6 D1 S_lp results by class."""

    model_prefix = model_key.split("_", maxsplit=1)[0]
    class_buckets: dict[str, list[float]] = {}
    for row in rows:
        class_name = stage6_class_name(row["template_id"])
        if class_name is None:
            continue
        raw_value = row.get(f"{model_prefix}_S_lp")
        if raw_value in {"", None}:
            continue
        class_buckets.setdefault(class_name, []).append(float(raw_value))

    summary: dict[str, dict[str, float | int]] = {}
    for class_name, values in class_buckets.items():
        array = np.asarray(values, dtype=float)
        summary[class_name] = {
            "family_count": int(array.size),
            "mean_S_lp": float(array.mean()),
            "median_S_lp": float(np.median(array)),
            "positive_count": int(np.sum(array >= threshold)),
            "positive_rate": float(np.mean(array >= threshold)),
        }
    return summary


def write_per_family_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Write the Stage 4 per-family comparison table."""
    fieldnames = list(rows[0].keys()) if rows else [
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


def load_per_family_csv_rows(output_path: Path) -> list[dict[str, str]]:
    """Load an existing per-family CSV for plot-only regeneration."""

    if not output_path.exists():
        raise FileNotFoundError(f"Per-family CSV not found at {output_path}.")
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_original_per_family_csv(path: Path) -> dict[str, dict[str, str]]:
    """Load the original Stage 4 per-family CSV by template id."""

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["template_id"]: row for row in csv.DictReader(handle)}


def plot_histograms(
    qwen_hat_values: list[float],
    llama_hat_values: list[float],
    qwen_slp_values: list[float],
    llama_slp_values: list[float],
    output_path: Path,
) -> None:
    """Render the pilot sensitivity figure with both hat_S and S_lp distributions."""

    figure, axes = plt.subplots(2, 2, figsize=(12, 9), sharey="row")
    panels = (
        (axes[0, 0], qwen_hat_values, "Qwen", r"$\hat{S}_\theta$"),
        (axes[0, 1], llama_hat_values, "Llama", r"$\hat{S}_\theta$"),
        (axes[1, 0], qwen_slp_values, "Qwen", r"$S^{lp}_\theta$"),
        (axes[1, 1], llama_slp_values, "Llama", r"$S^{lp}_\theta$"),
    )
    for axis, values, title, xlabel in panels:
        data = np.asarray(values or [0.0], dtype=float)
        axis.hist(data, bins=min(10, max(3, len(data))), color="#4C78A8", alpha=0.85)
        for quantile_value, color in zip(
            (np.quantile(data, 0.2), np.quantile(data, 0.4)),
            ("#F58518", "#54A24B"),
            strict=True,
        ):
            axis.axvline(float(quantile_value), color=color, linestyle="--", linewidth=1.5)
        axis.set_title(f"{title} {xlabel}")
        axis.set_xlabel(xlabel)
    axes[0, 0].set_ylabel("Family Count")
    axes[1, 0].set_ylabel("Family Count")
    figure.suptitle("Pilot Family Sensitivity Distribution (N=30)")
    figure.tight_layout()
    ensure_parent_dir(output_path)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def load_slp_baseline_csv(path: Path) -> dict[str, dict[str, str]]:
    """Load an earlier repair-analysis CSV for S_lp stability comparison."""

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["template_id"]: row for row in csv.DictReader(handle)}


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

    if args.jsonl_glob:
        resolved_paths = resolve_model_paths_from_glob(args.jsonl_glob)
        qwen_path = resolved_paths["qwen_primary"]
        llama_path = resolved_paths["llama_primary"]
    else:
        if not args.qwen_output or not args.llama_output:
            raise ValueError("Provide either --jsonl-glob or both --qwen-output and --llama-output.")
        qwen_path = resolve_single_path(args.qwen_output)
        llama_path = resolve_single_path(args.llama_output)
    template_dir = Path(args.template_dir)
    output_prefix = infer_output_prefix(output_dir, args)

    if args.plot_only:
        candidate_inputs = [
            output_dir / f"{output_prefix}_per_family.csv",
            output_dir / "stage6_d1_per_family.csv",
            output_dir / "stage4_per_family.csv",
        ]
        per_family_source = next((path for path in candidate_inputs if path.exists()), None)
        if per_family_source is None:
            raise FileNotFoundError(
                "Could not find an existing per-family CSV for plot regeneration in "
                f"{output_dir}. Looked for {[str(path.name) for path in candidate_inputs]}."
            )

        rows = load_per_family_csv_rows(per_family_source)
        qwen_hat_values = [float(row["qwen_hat_S"]) for row in rows if row.get("qwen_hat_S") not in {"", None}]
        llama_hat_values = [float(row["llama_hat_S"]) for row in rows if row.get("llama_hat_S") not in {"", None}]
        qwen_slp_values = [float(row["qwen_S_lp"]) for row in rows if row.get("qwen_S_lp") not in {"", None}]
        llama_slp_values = [float(row["llama_S_lp"]) for row in rows if row.get("llama_S_lp") not in {"", None}]
        plot_histograms(
            qwen_hat_values,
            llama_hat_values,
            qwen_slp_values,
            llama_slp_values,
            output_dir / f"{output_prefix}_sensitivity_hist.png",
        )
        logger.log_event(
            "STAGE4_PLOT_REGENERATED",
            output_prefix=output_prefix,
            source_per_family_csv=str(per_family_source.resolve()),
        )
        return

    original_per_family = load_original_per_family_csv(Path(args.original_per_family)) if args.repair_run else {}
    prior_repair_per_family = (
        load_slp_baseline_csv(Path(args.prior_repair_per_family))
        if args.repair_run and Path(args.prior_repair_per_family) != output_dir / "stage4_per_family.csv"
        else {}
    )

    model_payloads = {
        "qwen_primary": build_family_index(load_jsonl(qwen_path)),
        "llama_primary": build_family_index(load_jsonl(llama_path)),
    }
    if args.reparse:
        for family_map in model_payloads.values():
            for bundle in family_map.values():
                bundle["variants"] = [reparse_variant_record(record) for record in bundle["variants"]]
    all_template_ids = sorted(set(model_payloads["qwen_primary"]) | set(model_payloads["llama_primary"]))
    per_model_summary: dict[str, dict[str, Any]] = {}
    per_family_rows: list[dict[str, Any]] = []
    per_model_hat_s: dict[str, list[float]] = {model_key: [] for model_key in MODEL_KEYS}
    per_model_slp: dict[str, list[float]] = {model_key: [] for model_key in MODEL_KEYS}
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
        artifact_flagged_families: list[str] = []
        total_variants = 0
        successful_parses = 0
        exact_answer_matches = 0

        for template_id, bundle in family_map.items():
            variant_records = bundle["variants"]
            total_variants += len(variant_records)
            successful_parses += sum(
                int(record.get("parse_confident") and stored_canonical_answer(record) is not None)
                for record in variant_records
            )
            exact_answer_matches += sum(
                int(stored_canonical_answer(record) == canonical_correct_answer(record))
                for record in variant_records
                if stored_canonical_answer(record) is not None
            )
            raw_hat_s_value, num_valid_parses = recompute_hat_s(variant_records)
            artifact_flag, exclude_from_clean_count = flag_artifact_family(
                model_key=model_key,
                template_id=template_id,
                raw_hat_s=raw_hat_s_value,
            )
            clean_hat_s_value = 0.0 if exclude_from_clean_count and raw_hat_s_value is not None else raw_hat_s_value
            if num_valid_parses < 4:
                degraded_families.append(template_id)
            if artifact_flag is not None:
                artifact_flagged_families.append(f"{template_id}:{artifact_flag}")
            if clean_hat_s_value is not None:
                hat_s_values.append(clean_hat_s_value)
            logprob_drop = recompute_logprob_drop(variant_records)
            if logprob_drop is not None:
                logprob_values.append(logprob_drop)
            summary_record = bundle["summary"]
            if summary_record is not None and summary_record.get("answer_flip_rate") not in {None, raw_hat_s_value}:
                logger.log_event(
                    "FAMILY_SUMMARY_MISMATCH",
                    model_key=model_key,
                    template_id=template_id,
                    reported_answer_flip_rate=summary_record.get("answer_flip_rate"),
                    recomputed_answer_flip_rate=raw_hat_s_value,
                )

        per_model_hat_s[model_key] = hat_s_values
        per_model_slp[model_key] = logprob_values
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
            "families_artifact_flagged": artifact_flagged_families,
        }

    slp_stability = {"matches_prior_repair": True, "mismatches": []}

    for template_id in all_template_ids:
        metadata = load_template_metadata(template_dir, template_id)
        qwen_bundle = model_payloads["qwen_primary"][template_id]
        llama_bundle = model_payloads["llama_primary"][template_id]
        qwen_hat_s_raw, qwen_valid_parses = recompute_hat_s(qwen_bundle["variants"])
        llama_hat_s_raw, llama_valid_parses = recompute_hat_s(llama_bundle["variants"])
        qwen_flag, qwen_exclude = flag_artifact_family(
            model_key="qwen_primary",
            template_id=template_id,
            raw_hat_s=qwen_hat_s_raw,
        )
        llama_flag, llama_exclude = flag_artifact_family(
            model_key="llama_primary",
            template_id=template_id,
            raw_hat_s=llama_hat_s_raw,
        )
        qwen_hat_s = 0.0 if qwen_exclude and qwen_hat_s_raw is not None else qwen_hat_s_raw
        llama_hat_s = 0.0 if llama_exclude and llama_hat_s_raw is not None else llama_hat_s_raw
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
        if qwen_flag is not None:
            notes.append(f"qwen_{qwen_flag}")
        if llama_flag is not None:
            notes.append(f"llama_{llama_flag}")

        qwen_logprob = recompute_logprob_drop(qwen_bundle["variants"])
        llama_logprob = recompute_logprob_drop(llama_bundle["variants"])
        row: dict[str, Any] = {
            "template_id": template_id,
            "domain": metadata["domain"],
            "cue_type": metadata["cue_type"],
            "governing_law": metadata["governing_law"],
            "stage6_class": stage6_class_name(template_id) or "",
            "qwen_hat_S_raw": "" if qwen_hat_s_raw is None else qwen_hat_s_raw,
            "qwen_hat_S": "" if qwen_hat_s is None else qwen_hat_s,
            "llama_hat_S_raw": "" if llama_hat_s_raw is None else llama_hat_s_raw,
            "llama_hat_S": "" if llama_hat_s is None else llama_hat_s,
            "qwen_parse_ok": qwen_valid_parses == 4,
            "llama_parse_ok": llama_valid_parses == 4,
            "both_sensitive": qwen_sensitive and llama_sensitive,
            "notes": ";".join(notes),
        }
        if args.repair_run:
            original_row = original_per_family.get(template_id, {})
            row.update(
                {
                    "qwen_S_lp": original_row.get("qwen_S_lp", ""),
                    "llama_S_lp": original_row.get("llama_S_lp", ""),
                    "qwen_S_lp_repair": "" if qwen_logprob is None else qwen_logprob,
                    "llama_S_lp_repair": "" if llama_logprob is None else llama_logprob,
                }
            )
        else:
            row.update(
                {
                    "qwen_S_lp": "" if qwen_logprob is None else qwen_logprob,
                    "llama_S_lp": "" if llama_logprob is None else llama_logprob,
                }
            )

        if args.repair_run and prior_repair_per_family:
            prior_row = prior_repair_per_family.get(template_id, {})
            for column_name, new_value in (
                ("qwen_S_lp_repair", qwen_logprob),
                ("llama_S_lp_repair", llama_logprob),
            ):
                prior_value = prior_row.get(column_name, "")
                if prior_value == "" or new_value is None:
                    continue
                if not np.isclose(float(prior_value), float(new_value)):
                    slp_stability["matches_prior_repair"] = False
                    slp_stability["mismatches"].append(
                        {
                            "template_id": template_id,
                            "column": column_name,
                            "prior_value": float(prior_value),
                            "reparsed_value": float(new_value),
                        }
                    )

        per_family_rows.append(row)

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
    slp_threshold_candidates = {
        model_key: choose_thresholds(
            [
                float(row[f"{model_key.split('_')[0]}_S_lp_repair"])
                for row in per_family_rows
                if args.repair_run
                and row["template_id"] in train_template_ids
                and row.get(f"{model_key.split('_')[0]}_S_lp_repair", "") != ""
            ]
        )
        for model_key in MODEL_KEYS
    }

    stage6_mode = bool(args.jsonl_glob)
    qwen_slp_positive_count = sum(
        1
        for row in per_family_rows
        if row.get("qwen_S_lp") not in {"", None} and float(row["qwen_S_lp"]) >= args.threshold
    )
    qwen_slp_positive_rate = qwen_slp_positive_count / max(len(per_family_rows), 1)
    gate_4_pass = primary_any_flip_count >= PRIMARY_FLIP_GATE_COUNT
    gate_4_evidence = (
        f"{primary_any_flip_count} of {len(all_template_ids)} pilot families showed at least one answer "
        f"flip on at least one PRIMARY_DENSE model (threshold for PASS: >= {PRIMARY_FLIP_GATE_COUNT})."
    )
    stage6_gate_pass = qwen_slp_positive_count >= STAGE6_POSITIVE_GATE_COUNT
    stage6_gate_evidence = (
        f"{qwen_slp_positive_count} of {len(all_template_ids)} Stage 6 Phase D1 families reached "
        f"Qwen S_lp >= {args.threshold:.1f} nats (threshold for PASS: >= {STAGE6_POSITIVE_GATE_COUNT})."
    )
    summary_payload = {
        "repair_run": args.repair_run,
        "qwen_primary": per_model_summary["qwen_primary"],
        "llama_primary": per_model_summary["llama_primary"],
        "cross_model": {
            **cross_counts,
            "families_with_any_primary_flip": primary_any_flip_count,
        },
        "threshold_candidates": threshold_candidates,
        "slp_threshold_candidates": slp_threshold_candidates,
        "slp_stability_check": slp_stability,
        "gate_4_pass": gate_4_pass,
        "gate_4_evidence": gate_4_evidence,
    }
    if stage6_mode:
        summary_payload["stage6_d1"] = {
            "threshold": args.threshold,
            "qwen_slp_positive_count": qwen_slp_positive_count,
            "qwen_slp_positive_rate": qwen_slp_positive_rate,
            "gate_pass": stage6_gate_pass,
            "gate_evidence": stage6_gate_evidence,
            "per_class_qwen": compute_stage6_class_summary(
                per_family_rows,
                model_key="qwen_primary",
                threshold=args.threshold,
            ),
            "per_class_llama": compute_stage6_class_summary(
                per_family_rows,
                model_key="llama_primary",
                threshold=args.threshold,
            ),
        }

    write_json(output_dir / f"{output_prefix}_sensitivity_summary.json", summary_payload)
    write_per_family_csv(
        sorted(per_family_rows, key=lambda row: row["template_id"]),
        output_dir / f"{output_prefix}_per_family.csv",
    )
    plot_histograms(
        per_model_hat_s["qwen_primary"],
        per_model_hat_s["llama_primary"],
        per_model_slp["qwen_primary"],
        per_model_slp["llama_primary"],
        output_dir / f"{output_prefix}_sensitivity_hist.png",
    )
    logger.log_event(
        "STAGE4_ANALYSIS_COMPLETE",
        qwen_output=str(qwen_path.resolve()),
        llama_output=str(llama_path.resolve()),
        gate_4_pass=gate_4_pass,
        gate_4_evidence=gate_4_evidence,
        stage6_d1_gate_pass=stage6_gate_pass if stage6_mode else None,
    )


if __name__ == "__main__":
    main()
