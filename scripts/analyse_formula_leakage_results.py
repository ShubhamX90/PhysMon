#!/usr/bin/env python3
"""Analyse behavioural results for the Appendix A formula-leakage sanity check."""

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

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--per-family-csv",
        default="results/appendix/formula_leakage/analysis/formula_leakage_per_family.csv",
    )
    parser.add_argument(
        "--source-summary",
        default="results/appendix/formula_leakage/formula_leakage_summary.json",
    )
    parser.add_argument("--output-dir", default="results/appendix/formula_leakage")
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(Path(args.per_family_csv))
    baseline = json.loads(Path(args.source_summary).read_text(encoding="utf-8"))
    baseline_map = {row["template_id"]: row for row in baseline["families"]}

    analysed = []
    low_slp_count = 0
    for row in rows:
        template_id = str(row["template_id"])
        source_family = template_id.removesuffix("_FORMULA")
        baseline_row = baseline_map.get(source_family, {})
        observed_slp = float(row.get("qwen_S_lp", "0") or "0")
        parse_rate = float(row.get("qwen_parse_rate_family", "0") or "0")
        low_slp = observed_slp < 0.5
        if low_slp:
            low_slp_count += 1
        analysed.append(
            {
                "template_id": template_id,
                "source_family": source_family,
                "baseline_qwen_slp": float(baseline_row.get("baseline_qwen_slp", 0.0) or 0.0),
                "formula_leakage_slp": observed_slp,
                "parse_rate_family": parse_rate,
                "passes_low_sensitivity_check": low_slp,
            }
        )

    summary = {
        "execution_status": "behavioural_complete",
        "n_families": len(analysed),
        "n_low_sensitivity": low_slp_count,
        "fraction_low_sensitivity": (low_slp_count / len(analysed)) if analysed else None,
        "verdict": "PASS" if analysed and low_slp_count == len(analysed) else "MIXED",
        "families": analysed,
    }
    write_json(output_dir / "formula_leakage_analysis_summary.json", summary)
    write_json(output_dir / "formula_leakage_summary.json", summary)


if __name__ == "__main__":
    main()
