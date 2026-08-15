#!/usr/bin/env python3
# ruff: noqa: E402
"""Generate model-specific positive-family JSON from a per-family sensitivity CSV.

Reference:
    Stage 6 D2 probing workflow, using pre-registered `S_lp` thresholds to define
    binary positive families for one model.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.logging import ExperimentLogger  # noqa: E402

DEFAULT_STAGE = 6
DEFAULT_SEED = 42
DEFAULT_THRESHOLD = 0.5
DEFAULT_JSONL_NAME = "generate_positive_families_events.jsonl"
MODEL_COLUMNS = {
    "qwen_primary": "qwen_S_lp",
    "llama_primary": "llama_S_lp",
    "deepseek_reasoning": "deepseek_S_lp",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for positive-family generation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-csv", required=True, help="Per-family sensitivity CSV.")
    parser.add_argument(
        "--model-role",
        default=None,
        help="Optional model role whose default S_lp column defines positive families.",
    )
    parser.add_argument(
        "--slp-column",
        default=None,
        help="Optional explicit S_lp column override, e.g. deepseek_S_lp.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Inclusive S_lp threshold used for the positive family set.",
    )
    parser.add_argument(
        "--exclude-ids",
        nargs="*",
        default=(),
        help="Optional template ids to exclude from the output set.",
    )
    parser.add_argument(
        "--exclude-degraded",
        action="store_true",
        help="Exclude rows marked degraded for the selected model, when the CSV provides that signal.",
    )
    parser.add_argument(
        "--min-family-parse-rate",
        type=float,
        default=None,
        help="Optional minimum family-level parse rate required to keep a row.",
    )
    parser.add_argument("--output", required=True, help="Output JSON path.")
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE, help="Scientific stage number.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Recorded deterministic seed.")
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    """Load per-family rows from the Stage 6 CSV."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_slp_column(args: argparse.Namespace) -> str:
    """Resolve the S_lp column used for positive-family generation."""

    if args.slp_column:
        return str(args.slp_column)
    if args.model_role:
        if args.model_role not in MODEL_COLUMNS:
            allowed = ", ".join(sorted(MODEL_COLUMNS))
            raise ValueError(f"Unsupported --model-role {args.model_role!r}. Allowed: {allowed}.")
        return MODEL_COLUMNS[args.model_role]
    raise ValueError("Provide either --model-role or --slp-column.")


def infer_degraded_column(slp_column: str) -> str | None:
    """Infer a degraded-flag column name from one S_lp column name."""

    prefixes = ("qwen_", "llama_", "deepseek_")
    for prefix in prefixes:
        if slp_column.startswith(prefix):
            return f"{prefix}degraded"
    return None


def infer_parse_rate_column(slp_column: str) -> str | None:
    """Infer a family-level parse-rate column name from one S_lp column name."""

    prefixes = ("qwen_", "llama_", "deepseek_")
    for prefix in prefixes:
        if slp_column.startswith(prefix):
            return f"{prefix}parse_rate"
    return None


def main() -> None:
    """Build and save the positive-family JSON artifact."""

    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="generate_positive_families.py",
        stage=args.stage,
        jsonl_path=output_path.parent / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_role=args.model_role,
    )

    rows = load_rows(Path(args.family_csv))
    column = resolve_slp_column(args)
    exclude_ids = set(args.exclude_ids)
    degraded_column = infer_degraded_column(column) if args.exclude_degraded else None
    parse_rate_column = infer_parse_rate_column(column) if args.min_family_parse_rate is not None else None
    positives = sorted(
        row["template_id"]
        for row in rows
        if row["template_id"] not in exclude_ids
        and float(row.get(column, "0") or "0") >= args.threshold
        and (
            degraded_column is None
            or str(row.get(degraded_column, "")).strip().lower() not in {"1", "true", "yes", "y"}
        )
        and (
            parse_rate_column is None
            or float(row.get(parse_rate_column, "0") or "0") >= float(args.min_family_parse_rate)
        )
    )
    payload = {
        "model": args.model_role or "custom",
        "threshold": float(args.threshold),
        "positive_families": positives,
        "excluded_ids": sorted(exclude_ids),
        "seed": int(args.seed),
        "source_csv": str(Path(args.family_csv)),
        "slp_column": column,
        "exclude_degraded": bool(args.exclude_degraded),
        "min_family_parse_rate": args.min_family_parse_rate,
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    logger.log_event(
        "POSITIVE_FAMILIES_GENERATED",
        model_role=args.model_role or "custom",
        threshold=float(args.threshold),
        positive_count=len(positives),
        excluded_count=len(exclude_ids),
        slp_column=column,
        output_path=str(output_path),
    )


if __name__ == "__main__":
    main()
