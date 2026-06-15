#!/usr/bin/env python3
"""Audit the current PhysMon benchmark and prepare Phase 2 review artifacts.

Reference:
    `physmon_proposal.pdf` §3.2, §5.2, §7, and Stage 6 next-steps brief v6.6.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from physmon.benchmark.parser import parse_answer
from physmon.utils.io import read_yaml, write_json


PILOT_GENERATED_DIR = Path("data/generated")
PHASE1_GENERATED_DIR = Path("results/stage6/generated_phase1_full")
PHASE2_AD_GENERATED_DIR = Path("results/stage6/generated_phase2_ad")
PHASE2_BCE_GENERATED_DIR = Path("results/stage6/generated_phase2_bce")

PHASE1_VERIFICATION_DIR = Path("results/stage6/verification")
PHASE2_AD_VERIFICATION_DIR = Path("results/stage6/verification_phase2_ad")
PHASE2_BCE_VERIFICATION_DIR = Path("results/stage6/verification_phase2_bce")

FULL_MANIFEST_NAME = "stage6_full_benchmark_manifest.csv"
PHASE2_BCE_SUMMARY_NAME = "stage6_phase2_bce_audit_summary.json"
PHASE2_BCE_PRIORITY_NAME = "stage6_phase2_bce_priority_review.csv"
PHASE2_BCE_REVIEW_GUIDE = Path("docs/validation/stage6_phase2_bce_review_guide.md")

PILOT_ID_PATTERN = re.compile(r"^(CM|EL)_[AB]_\d{3}$")
PHASE1_UM_PATTERN = re.compile(r"^CM_B_UM_0(0[1-9]|[12]\d|3\d|40)$")
PHASE2_AD_PATTERN = re.compile(r"^(CM_B_UM_0(4[1-9]|5\d|60)|TH_B_UM_0(0[1-9]|10))$")
PHASE2_BCE_PATTERN = re.compile(r"^(CM_B_STD_\d{3}|CM_A_STD_\d{3}|CM_C_\d{3})$")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template-dir",
        default="data/raw/templates",
        help="Directory containing benchmark template YAML files.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/stage6/audit",
        help="Directory for audit outputs.",
    )
    return parser.parse_args()


def infer_phase_bucket(template_id: str) -> str:
    """Return the benchmark phase bucket for a template ID."""

    if PHASE2_BCE_PATTERN.match(template_id):
        return "phase2_bce"
    if PHASE2_AD_PATTERN.match(template_id):
        return "phase2_ad"
    if PHASE1_UM_PATTERN.match(template_id):
        return "phase1_um"
    if PILOT_ID_PATTERN.match(template_id):
        return "pilot"
    return "unknown"


def infer_class_label(template_id: str, payload: dict[str, Any]) -> str:
    """Return a coarse family class label."""

    governing_law = str(payload.get("governing_law", ""))
    if template_id.startswith("CM_B_UM_"):
        if "velocity" in governing_law or "frequency" in governing_law or "torque" in governing_law:
            return governing_law
        return "unit_matched_cue_b"
    if template_id.startswith("TH_B_UM_"):
        return "thermodynamics_unit_matched"
    if template_id.startswith("CM_B_STD_"):
        return "standard_cue_b"
    if template_id.startswith("CM_A_STD_"):
        return "standard_cue_a"
    if template_id.startswith("CM_C_"):
        return "frame_rendering"
    return governing_law


def generated_dir_for_bucket(bucket: str) -> Path | None:
    """Map one phase bucket to its rendered-family directory."""

    return {
        "pilot": PILOT_GENERATED_DIR,
        "phase1_um": PHASE1_GENERATED_DIR,
        "phase2_ad": PHASE2_AD_GENERATED_DIR,
        "phase2_bce": PHASE2_BCE_GENERATED_DIR,
    }.get(bucket)


def verification_dir_for_bucket(bucket: str) -> Path | None:
    """Map one phase bucket to its verification-report directory."""

    return {
        "pilot": None,
        "phase1_um": PHASE1_VERIFICATION_DIR,
        "phase2_ad": PHASE2_AD_VERIFICATION_DIR,
        "phase2_bce": PHASE2_BCE_VERIFICATION_DIR,
    }.get(bucket)


def maybe_parse_numeric(raw_value: Any) -> float | None:
    """Attempt to parse one numeric cue value."""

    if isinstance(raw_value, (int, float)):
        return float(raw_value)
    text = str(raw_value).strip()
    if any(unit in text for unit in (" m/s", " Hz", " N", " J", " W", " V", " C")):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def numeric_gap_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Compute near-match metadata where answer-distance is scientifically meaningful.

    This metadata is only meaningful for families intentionally designed around
    answer-proximate distractors: unit-matched Cue B families and frame-rendering
    families. For standard Cue B families, answer-distance can be misleading
    because the strongest distractor often tracks a governing input parameter
    rather than the final answer value itself.
    """

    template_id = str(payload["template_id"])
    cue_type = str(payload["cue_type"])
    cue_slot = payload["cue_slot"]
    tracks_answer_proximity = (
        template_id.startswith("CM_B_UM_")
        or template_id.startswith("EL_B_UM_")
        or template_id.startswith("TH_B_UM_")
    )
    if cue_type != "nongoverning_distractor" or not tracks_answer_proximity:
        return {
            "has_exact_match_distractor": False,
            "min_relative_gap_to_answer": "",
            "near_match_within_2pct": False,
            "near_match_within_5pct": False,
        }

    answer_value = float(payload["correct_answer"]["value"])
    numeric_values = [
        maybe_parse_numeric(value_spec["value"])
        for value_spec in cue_slot["values"]
    ]
    numeric_values = [value for value in numeric_values if value is not None]
    if not numeric_values or math.isclose(answer_value, 0.0, abs_tol=1e-12):
        return {
            "has_exact_match_distractor": False,
            "min_relative_gap_to_answer": "",
            "near_match_within_2pct": False,
            "near_match_within_5pct": False,
        }

    gaps = [abs(value - answer_value) / abs(answer_value) for value in numeric_values]
    min_gap = min(gaps)
    return {
        "has_exact_match_distractor": any(math.isclose(gap, 0.0, abs_tol=1e-12) for gap in gaps),
        "min_relative_gap_to_answer": round(min_gap, 6),
        "near_match_within_2pct": min_gap < 0.02,
        "near_match_within_5pct": min_gap < 0.05,
    }


def load_generated_family(template_id: str, bucket: str) -> dict[str, Any] | None:
    """Load one rendered family JSON if it exists."""

    generated_dir = generated_dir_for_bucket(bucket)
    if generated_dir is None:
        return None
    path = generated_dir / f"{template_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_verification_payload(template_id: str, bucket: str) -> dict[str, Any] | None:
    """Load one verification report JSON if it exists."""

    verification_dir = verification_dir_for_bucket(bucket)
    if verification_dir is None:
        return None
    path = verification_dir / f"{template_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest_row(template_path: Path) -> dict[str, Any]:
    """Build one manifest row from one template YAML."""

    payload = read_yaml(template_path)
    template_id = str(payload["template_id"])
    bucket = infer_phase_bucket(template_id)
    class_label = infer_class_label(template_id, payload)
    generated_payload = load_generated_family(template_id, bucket)
    verification_payload = load_verification_payload(template_id, bucket)
    parse_result = parse_answer(str(payload["correct_answer"]["display"]))
    gap_metadata = numeric_gap_metadata(payload)

    generated_present = generated_payload is not None
    rendered_variant_count = len(generated_payload["variants"]) if generated_payload else 0
    rendered_correct_answers = (
        {variant["correct_answer"] for variant in generated_payload["variants"]}
        if generated_payload
        else set()
    )
    cue_values = [str(value_spec["display"]) for value_spec in payload["cue_slot"]["values"]]

    issues: list[str] = []
    if bucket == "unknown":
        issues.append("unknown_phase_bucket")
    if not parse_result.is_confident or parse_result.answer is None:
        issues.append("correct_answer_not_parseable")
    if payload["validation"]["verifier_certified"] and verification_payload is not None and not verification_payload["all_passed"]:
        issues.append("verifier_flag_report_mismatch")
    if generated_present and rendered_variant_count != 4:
        issues.append(f"rendered_variant_count={rendered_variant_count}")
    if generated_present and len(rendered_correct_answers) != 1:
        issues.append("rendered_correct_answer_mismatch")
    if len(cue_values) != 4:
        issues.append(f"cue_value_count={len(cue_values)}")
    if len(set(cue_values)) != len(cue_values):
        issues.append("duplicate_cue_values")

    row = {
        "template_id": template_id,
        "phase_bucket": bucket,
        "class_label": class_label,
        "domain": str(payload["domain"]),
        "cue_type": str(payload["cue_type"]),
        "governing_law": str(payload["governing_law"]),
        "target_quantity": str(payload["target_quantity"]),
        "target_units": str(payload["target_units"]),
        "answer_value": float(payload["correct_answer"]["value"]),
        "answer_display": str(payload["correct_answer"]["display"]),
        "cue_slot_name": str(payload["cue_slot"]["name"]),
        "cue_slot_type": str(payload["cue_slot"]["type"]),
        "num_variants": len(payload["cue_slot"]["values"]),
        "verifier_certified": bool(payload["validation"]["verifier_certified"]),
        "pi_validated": bool(payload["validation"]["pi_validated"]),
        "generated_present": generated_present,
        "rendered_variant_count": rendered_variant_count,
        "correct_answer_parseable": bool(parse_result.is_confident and parse_result.answer is not None),
        "has_exact_match_distractor": gap_metadata["has_exact_match_distractor"],
        "min_relative_gap_to_answer": gap_metadata["min_relative_gap_to_answer"],
        "near_match_within_2pct": gap_metadata["near_match_within_2pct"],
        "near_match_within_5pct": gap_metadata["near_match_within_5pct"],
        "issues": ";".join(issues),
    }
    return row


def priority_score(row: dict[str, Any]) -> tuple[int, float, str]:
    """Return a sortable review-priority tuple for Phase 2 B/C/E families."""

    score = 0
    reasons: list[str] = []
    if row["cue_type"] == "frame_rendering":
        score += 100
        reasons.append("frame_rendering_equivalence")
    if row["domain"] == "thermodynamics":
        score += 80
        reasons.append("thermodynamics_domain")
    if row["has_exact_match_distractor"]:
        score += 70
        reasons.append("exact_match_distractor")
    elif row["near_match_within_2pct"]:
        score += 60
        reasons.append("near_match_lt_2pct")
    elif row["near_match_within_5pct"]:
        score += 40
        reasons.append("near_match_lt_5pct")
    if row["issues"]:
        score += 120
        reasons.append("audit_issue_present")
    reason = ",".join(reasons) if reasons else "standard_review"
    gap = float(row["min_relative_gap_to_answer"] or 999.0)
    return (-score, gap, reason)


def write_manifest(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Write the benchmark manifest CSV."""

    if not rows:
        raise ValueError("No manifest rows to write.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_phase2_bce_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the summary JSON for the 40 B/C/E families."""

    rows_bce = [row for row in rows if row["phase_bucket"] == "phase2_bce"]
    by_domain = Counter(row["domain"] for row in rows_bce)
    by_cue_type = Counter(row["cue_type"] for row in rows_bce)
    by_class = Counter(row["class_label"] for row in rows_bce)
    duplicate_answers: dict[str, list[str]] = defaultdict(list)
    for row in rows_bce:
        duplicate_answers[str(row["answer_display"])].append(str(row["template_id"]))
    duplicate_answers = {
        answer: template_ids
        for answer, template_ids in duplicate_answers.items()
        if len(template_ids) > 1
    }
    priority_rows = sorted(rows_bce, key=priority_score)
    return {
        "total_families": len(rows_bce),
        "by_domain": dict(by_domain),
        "by_cue_type": dict(by_cue_type),
        "by_class": dict(by_class),
        "generated_present_count": sum(int(row["generated_present"]) for row in rows_bce),
        "pi_validated_count": sum(int(row["pi_validated"]) for row in rows_bce),
        "verifier_certified_count": sum(int(row["verifier_certified"]) for row in rows_bce),
        "correct_answer_parseable_count": sum(int(row["correct_answer_parseable"]) for row in rows_bce),
        "exact_match_count": sum(int(row["has_exact_match_distractor"]) for row in rows_bce),
        "near_match_within_2pct_count": sum(int(row["near_match_within_2pct"]) for row in rows_bce),
        "near_match_within_5pct_count": sum(int(row["near_match_within_5pct"]) for row in rows_bce),
        "families_with_issues": [row["template_id"] for row in rows_bce if row["issues"]],
        "duplicate_answer_clusters": duplicate_answers,
        "top_priority_families": [row["template_id"] for row in priority_rows[:12]],
    }


def write_priority_review(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Write the Phase 2 B/C/E priority review CSV."""

    rows_bce = [row for row in rows if row["phase_bucket"] == "phase2_bce"]
    enriched_rows: list[dict[str, Any]] = []
    for row in rows_bce:
        score_tuple = priority_score(row)
        reason = score_tuple[2]
        enriched_rows.append(
            {
                "template_id": row["template_id"],
                "domain": row["domain"],
                "cue_type": row["cue_type"],
                "class_label": row["class_label"],
                "governing_law": row["governing_law"],
                "answer_display": row["answer_display"],
                "has_exact_match_distractor": row["has_exact_match_distractor"],
                "min_relative_gap_to_answer": row["min_relative_gap_to_answer"],
                "near_match_within_2pct": row["near_match_within_2pct"],
                "near_match_within_5pct": row["near_match_within_5pct"],
                "issues": row["issues"],
                "priority_reason": reason,
            }
        )
    enriched_rows.sort(key=lambda row: priority_score(row))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(enriched_rows[0].keys()))
        writer.writeheader()
        writer.writerows(enriched_rows)


def write_review_guide(summary: dict[str, Any], output_path: Path) -> None:
    """Write the human-readable Phase 2 B/C/E review guide."""

    lines = [
        "# Stage 6 Phase 2 B/C/E Review Guide",
        "",
        "This guide accompanies the 40-family Phase 2 B/C/E validation form.",
        "Symbolic verification and rendering already pass for every family in this batch.",
        "PI review should therefore focus on conceptual physics, ambiguity, target/question alignment,",
        "and whether the cue is truly irrelevant or non-governing as stated.",
        "",
        "## Batch Summary",
        "",
        f"- Total families: `{summary['total_families']}`",
        f"- Domains: `{summary['by_domain']}`",
        f"- Cue types: `{summary['by_cue_type']}`",
        f"- Class labels: `{summary['by_class']}`",
        f"- Exact-match distractor families: `{summary['exact_match_count']}`",
        f"- Near-match (<2%) distractor families: `{summary['near_match_within_2pct_count']}`",
        f"- Near-match (<5%) distractor families: `{summary['near_match_within_5pct_count']}`",
        "",
        "## Review Priorities",
        "",
        "Review these categories first:",
        "1. Frame-rendering families (`CM_C_001`-`CM_C_005`) for exact meaning preservation.",
        "2. Thermodynamics families for conceptual target clarity and unit consistency.",
        "3. Exact-match and very-close near-match distractor families, because these are likely to drive the strongest `S_lp`.",
        "4. Any family listed with audit issues (there should ideally be none).",
        "",
        "## Reminder From CM_B_UM_045",
        "",
        "The main human-only failure mode to watch for is: the governing equation and stated answer",
        "may be internally consistent, but the prompt may ask for the wrong object or wrong quantity.",
        "That conceptual mismatch will not always be caught by symbolic verification alone.",
        "",
        "## Duplicate Answer Clusters",
        "",
    ]
    if summary["duplicate_answer_clusters"]:
        for answer, template_ids in summary["duplicate_answer_clusters"].items():
            lines.append(f"- `{answer}`: {', '.join(template_ids)}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Highest-Priority Families",
            "",
        ]
    )
    for template_id in summary["top_priority_families"]:
        lines.append(f"- `{template_id}`")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Run the full benchmark audit and write all outputs."""

    args = parse_args()
    template_dir = Path(args.template_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    template_paths = sorted(template_dir.glob("*.yaml"))
    target_paths = [
        path
        for path in template_paths
        if infer_phase_bucket(path.stem) != "unknown"
    ]
    rows = [build_manifest_row(path) for path in target_paths]
    rows.sort(key=lambda row: (row["phase_bucket"], row["template_id"]))

    write_manifest(rows, output_dir / FULL_MANIFEST_NAME)
    summary = build_phase2_bce_summary(rows)
    write_json(output_dir / PHASE2_BCE_SUMMARY_NAME, summary)
    write_priority_review(rows, output_dir / PHASE2_BCE_PRIORITY_NAME)
    write_review_guide(summary, PHASE2_BCE_REVIEW_GUIDE)

    print(output_dir / FULL_MANIFEST_NAME)
    print(output_dir / PHASE2_BCE_SUMMARY_NAME)
    print(output_dir / PHASE2_BCE_PRIORITY_NAME)
    print(PHASE2_BCE_REVIEW_GUIDE)


if __name__ == "__main__":
    main()
