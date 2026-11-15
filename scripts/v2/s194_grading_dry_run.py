#!/usr/bin/env python3
"""Stage 15: grading dry run (dataset admission standard checks 4.1 and 4.2).

For every cell of each dataset directory the gold is written as a contract final line in every declared answer format and read
back by the real contract parser (`reasoning_contract_v2.assess`), then graded under all three views (`grading_views.grade_all`).
Every misuse foil and the placebo is written the same way and graded; under the primary (declared) view none may be correct.

Answer formats written for the gold (all in the gold unit unless stated):

* `plain_full`   the gold at full float precision ("2.177777777777778");
* `plain_4sf`    rounded to four significant figures;
* `sci_4sf`      scientific notation with four significant figures ("2.178e+00"; the contract final-line number accepts an exponent);
* `alt_unit_*`   the same quantity in every other unit of the same dimension the registry knows (and the singular or plural count
  noun, or `$` for dollars), six significant figures, plain and scientific. The declared view requires the exact gold unit, so an
  alternative unit is expected WRONG there and is only required CORRECT under `convertible` and `rel1pct`.

The first three must be CORRECT under all three views. A foil recorded in the cell's `confounded` list as indistinguishable from the gold is listed as exempt with that reason. A supporting
proximity cell (it carries `tolerance_status`) has the cue numeral in the CUE's unit as its foil: the dry run re-derives the three
recorded per-view statuses of that numeral and compares them, and a numeral correct under a view must be marked source-ambiguous
for it. A cell the dataset marks `source_ambiguous` for a view is reported in its own
list and is not a failure for that view. Nothing is loosened to make a cell pass: a failure is a finding about the grader or the
dataset and is listed with its cause.

Usage: s194_grading_dry_run.py [DATASET_DIR ...] [--out-root results/stage15/grading_dry_run] [--overwrite]
Default datasets: data/v2/dataset/m0_v2 and data/v2/dataset/nonphysics_v1. Exit status 1 when an unexpected failure exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract_v2 as rc2  # noqa: E402
from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.scoring import grading_views as gv  # noqa: E402
from physmon.scoring import unit_convertible as uc  # noqa: E402

DEFAULT_DATASETS = ("data/v2/dataset/m0_v2", "data/v2/dataset/nonphysics_v1")
DEFAULT_OUT = "results/stage15/grading_dry_run"
GOLD_FORMATS = ("plain_full", "plain_4sf", "sci_4sf")  # required CORRECT under every view
VIEW_KEYS = {"declared": "declared", "convertible": "convertible", "rel1pct": "rel1pct"}


def render(value: float, kind: str) -> str:
    if kind == "plain_full":
        return repr(float(value))
    if kind in ("plain_4sf", "plain_6sf"):
        sig = 4 if kind == "plain_4sf" else 6
        if abs(value) >= 10 ** sig:  # a plain integer cannot show fewer figures: write every integer digit, as a model rounding would
            return str(round(value))
        return format(Decimal(f"{value:.{sig}g}"), "f")
    if kind == "sci_4sf":
        return f"{value:.3e}"
    if kind == "sci_6sf":
        return f"{value:.5e}"
    raise ValueError(kind)


def read_back(value_text: str, unit: str) -> Any:
    """The parse of a contract final line carrying `value_text` and `unit` (the real contract reader, no thinking)."""

    return rc2.assess(f"Final answer: {value_text} {unit}", hit_token_limit=False, thinking_expected=False).parsed


def alternative_units(gold_unit: str) -> list[tuple[str, float]]:
    """(unit string, factor to multiply a gold-unit value by) for every other spelling or unit of the same quantity."""

    out: list[tuple[str, float]] = []
    canon = uc.canonical_unit(gold_unit)
    if canon in uc.COUNT_UNITS:
        plural = canon
        singular = next((k for k, v in uc.COUNT_ALIASES.items() if v == plural and k.isalpha()), None)
        for text in (plural, singular, "$" if plural == "dollars" else None, "USD" if plural == "dollars" else None):
            if text and text != gold_unit:
                out.append((text, 1.0))
        return out
    unit = dm.UNITS.get(canon)
    if unit is None or canon == "1":
        return out
    for name, other in dm.UNITS.items():
        if name not in (canon, "1") and other.dim == unit.dim:
            out.append((name, unit.factor / other.factor))
    singular_alias = [k for k, v in uc.ALIASES.items() if v == canon and k.isalpha() and k != gold_unit]
    out.extend((alias, 1.0) for alias in singular_alias)
    return out


def grade_text(value_text: str, unit: str, gold: float, gold_unit: str) -> dict[str, Any]:
    parsed = read_back(value_text, unit)
    if parsed.status != "PARSED":
        return {"parse_status": parsed.status, "declared": parsed.status, "convertible": parsed.status, "rel1pct": parsed.status,
                "dimension_status": "NOT_PARSED"}
    views = gv.grade_all(parsed, gold, gold_unit)
    return {"parse_status": "PARSED", "declared": views["declared"], "convertible": views["convertible"],
            "rel1pct": views["rel1pct"], "dimension_status": views["dimension_status"]}


def dry_run_cell(row: dict[str, Any]) -> dict[str, Any]:
    gold, unit = float(row["gold_value"]), row["gold_unit"]
    ambiguous = set(row.get("ambiguous_views") or []) if row.get("source_ambiguous") else set()
    cell_id = row.get("job_id") or row.get("cell_id")
    failures: list[dict[str, Any]] = []
    exempt: list[dict[str, Any]] = []
    n_checks = Counter()

    def record(kind: str, text: str, shown_unit: str, graded: dict[str, Any], required: tuple[str, ...], expect_correct: bool) -> None:
        for view in required:
            n_checks[(kind, view)] += 1
            ok = (graded[view] == "correct") == expect_correct
            if ok:
                continue
            entry = {"cell": cell_id, "check": kind, "view": view, "text": f"{text} {shown_unit}", "grade": graded[view],
                     "dimension_status": graded["dimension_status"], "gold": gold, "gold_unit": unit}
            (exempt if view in ambiguous else failures).append({**entry, "source_ambiguous_view": view in ambiguous})

    for kind in GOLD_FORMATS:
        text = render(gold, kind)
        record(f"gold:{kind}", text, unit, grade_text(text, unit, gold, unit), tuple(VIEW_KEYS), True)
    for alt, factor in alternative_units(unit):
        for kind in ("plain_6sf", "sci_6sf"):
            text = render(gold * factor, kind)
            graded = grade_text(text, alt, gold, unit)
            record(f"gold_alt_unit:{kind}", text, alt, graded, ("convertible", "rel1pct"), True)
    confounded = set(row.get("confounded") or [])
    tolerance = row.get("tolerance_status")
    if tolerance and row.get("unit"):
        # supporting proximity cell: the foil is the cue numeral in the CUE's unit, so the dataset's recorded per-view
        # status of that numeral is re-derived and compared; a numeral graded correct under a view must be marked ambiguous there
        graded = grade_text(tolerance["numeral"], row["unit"], gold, unit)
        for view in VIEW_KEYS:
            n_checks[("support_tolerance_status", view)] += 1
            if graded[view] != tolerance[view]:
                failures.append({"cell": cell_id, "check": "support_tolerance_status", "view": view, "grade": graded[view],
                                 "text": f"{tolerance['numeral']} {row['unit']} (dataset says {tolerance[view]})",
                                 "dimension_status": graded["dimension_status"], "gold": gold, "gold_unit": unit,
                                 "source_ambiguous_view": False})
            elif graded[view] == "correct" and view not in ambiguous:
                failures.append({"cell": cell_id, "check": "support_correct_not_marked_ambiguous", "view": view, "grade": "correct",
                                 "text": f"{tolerance['numeral']} {row['unit']}", "dimension_status": graded["dimension_status"],
                                 "gold": gold, "gold_unit": unit, "source_ambiguous_view": False})
        return {"cell": cell_id, "failures": failures, "source_ambiguous_exempt": exempt, "n_foils": 0,
                "checks": {f"{k}|{v}": n for (k, v), n in n_checks.items()}}
    foil_values: dict[str, float] = {name: float(value) for name, value in (row.get("foils") or {}).items() if value is not None}
    if row.get("placebo") is not None:
        foil_values["placebo"] = float(row["placebo"])
    for name, value in foil_values.items():
        for kind in ("plain_full", "plain_4sf"):
            text = render(value, kind)
            graded = grade_text(text, unit, gold, unit)
            if graded["declared"] == "correct" and (f"{name}~gold" in confounded or f"gold~{name}" in confounded):
                exempt.append({"cell": cell_id, "check": f"foil:{name}:{kind}", "view": "declared", "text": f"{text} {unit}",
                               "grade": "correct", "dimension_status": graded["dimension_status"], "gold": gold, "gold_unit": unit,
                               "source_ambiguous_view": False, "exempt_reason": "foil recorded as confounded with the gold"})
                n_checks[(f"foil:{name}:{kind}", "declared")] += 1
                continue
            record(f"foil:{name}:{kind}", text, unit, graded, ("declared",), False)
    return {"cell": cell_id, "failures": failures, "source_ambiguous_exempt": exempt, "n_foils": len(foil_values),
            "checks": {f"{k}|{v}": n for (k, v), n in n_checks.items()}}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_dataset(dataset_dir: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in (dataset_dir / "cells.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [dry_run_cell(row) for row in rows]
    checks: Counter = Counter()
    for result in results:
        checks.update(result["checks"])
    by_check: dict[str, dict[str, int]] = {}
    for key, n in sorted(checks.items()):
        kind, view = key.split("|")
        family = kind.split(":")[0] if not kind.startswith("foil") else "foil"
        by_check.setdefault(f"{family}:{view}", {"checks": 0})["checks"] += n
    failures = [f for r in results for f in r["failures"]]
    exempt = [f for r in results for f in r["source_ambiguous_exempt"]]
    return {
        "dataset": dataset_dir.name, "dataset_dir": str(dataset_dir), "n_cells": len(rows),
        "n_cells_with_foils": sum(1 for r in results if r["n_foils"]), "n_foil_values": sum(r["n_foils"] for r in results),
        "n_source_ambiguous_cells": sum(1 for r in rows if r.get("source_ambiguous")),
        "checks_by_family_and_view": by_check, "n_unexpected_failures": len(failures), "unexpected_failures": failures,
        "n_source_ambiguous_exempt": len(exempt), "source_ambiguous_exempt": exempt,
        "failures_by_check": dict(Counter(f"{f['check'].split(':')[0]}:{f['view']}" for f in failures)),
        "cells_with_failures": sorted({f["cell"] for f in failures}),
        "grader": {"contract_fingerprint": rc2.contract_fingerprint(),
                   "unit_convertible_sha256": file_sha256(Path(uc.__file__)), "grading_views_sha256": file_sha256(Path(gv.__file__))},
        "gold_formats": list(GOLD_FORMATS),
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [f"# Grading dry run: {report['dataset']}", "",
             f"Cells: {report['n_cells']}; cells with foils or placebo: {report['n_cells_with_foils']} "
             f"({report['n_foil_values']} values); source-ambiguous cells: {report['n_source_ambiguous_cells']}.",
             f"Unexpected failures: **{report['n_unexpected_failures']}**; source-ambiguous exemptions: "
             f"{report['n_source_ambiguous_exempt']}.", "",
             "| check family : view | checks run |", "|---|---|"]
    lines += [f"| {k} | {v['checks']} |" for k, v in report["checks_by_family_and_view"].items()]
    lines += ["", "Gold formats required correct under every view: " + ", ".join(report["gold_formats"]) + ". Alternative units are "
              "required correct under `convertible` and `rel1pct` only. Foils and the placebo must not be correct under `declared`.", ""]
    lines.append("## Unexpected failures")
    lines += [f"- {f['cell']} | {f['check']} | {f['view']} | `{f['text']}` graded {f['grade']} ({f['dimension_status']})"
              for f in report["unexpected_failures"]] or ["None."]
    lines.append("")
    lines.append("## Source-ambiguous exemptions")
    lines += [f"- {f['cell']} | {f['check']} | {f['view']} | `{f['text']}` graded {f['grade']}"
              for f in report["source_ambiguous_exempt"]] or ["None."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("datasets", nargs="*", help="dataset directories containing cells.jsonl")
    parser.add_argument("--out-root", default=DEFAULT_OUT)
    parser.add_argument("--overwrite", action="store_true", help="replace an existing report (default: refuse)")
    args = parser.parse_args(argv)
    datasets = [Path(d) if Path(d).is_absolute() else REPO_ROOT / d for d in (args.datasets or DEFAULT_DATASETS)]
    out_root = Path(args.out_root) if Path(args.out_root).is_absolute() else REPO_ROOT / args.out_root
    status = 0
    for dataset_dir in datasets:
        report = run_dataset(dataset_dir)
        out_dir = out_root / dataset_dir.name
        if (out_dir / "report.json").exists() and not args.overwrite:
            print(f"refusing to overwrite {out_dir / 'report.json'} (use --overwrite)", file=sys.stderr)
            return 2
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out_dir / "report.md").write_text(markdown(report), encoding="utf-8")
        print(f"{report['dataset']}: {report['n_cells']} cells, {report['n_unexpected_failures']} unexpected failures, "
              f"{report['n_source_ambiguous_exempt']} source-ambiguous exemptions")
        if report["n_unexpected_failures"]:
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
