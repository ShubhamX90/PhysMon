#!/usr/bin/env python3
"""Stage 14.12: what the existing pilot records say about copying versus relevance (CPU only; numpy).

Three descriptive pieces, from the bfloat16 `answer_line` records that carry the anchor-prompt decoy score:

1. Unit modulation. The same-unit near cell and the incompatible-unit near cell have the same cue digits, the same gold string
   and the same decoy string; only the unit written for the cue in the prompt differs. The per-structure difference of the
   decoy shift (and of the gold shift and the R_alt shift) between the two cells is therefore a clean contrast of unit
   compatibility. Items whose two cue numerals differ are excluded and counted.
2. Copy rates. The share of parsed generations whose value equals the cue numeral, per cell, with a Wilson 95% interval.
3. Role reversal. In that cell the cue quantity is relevant (the question asks for this value minus the value for system B).
   The pilot records show whether the generations copy the numeral, are correct, or have the right sign. This is NOT a
   matched control for the isolated cells: the question differs, so the copy rate is not comparable and no inference is drawn.

Descriptive and precision-limited; no p-values. A matched relevant-role control needs new scoring of the same candidate strings
in a cell where the same numeral plays a relevant role; it does not exist in the records.

Plan reference: protocol section 5 decision-table row 4 (numeral copying), P4.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT_ROOT = "results/stage14/s151_copying_vs_relevance"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s148 = _load("s148_pilot_analysis", "scripts/v2/s148_pilot_analysis.py")
s149 = _load("s149_noise_and_anchor_analysis", "scripts/v2/s149_noise_and_anchor_analysis.py")


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, centre - half), min(1.0, centre + half)]


def unit_modulation(records: list[dict], rng: np.random.Generator) -> dict[str, Any]:
    """Same-unit near cell minus incompatible-unit near cell, per structure, for decoy, gold and R_alt shifts."""

    index = s148.index_records(records)
    shifts = s149.anchor_shifts(records)
    excluded = 0
    per: dict[str, dict[str, list[float]]] = {m: defaultdict(list) for m in ("decoy_shift", "gold_shift", "r_alt_shift")}
    for (structure, instance, cell), near in shifts.items():
        if cell != s148.NEAR:
            continue
        other = shifts.get((structure, instance, s148.INCOMPAT))
        model = next(iter({k[0] for k in index}))
        a, b = index.get((model, structure, instance, s148.NEAR)), index.get((model, structure, instance, s148.INCOMPAT))
        if other is None or a is None or b is None or a.get("cue_numeric_value") != b.get("cue_numeric_value"):
            excluded += 1
            continue
        for measure in per:
            per[measure][structure].append(near[measure] - other[measure])
    out: dict[str, Any] = {"n_items_excluded": excluded}
    for measure, by_structure in per.items():
        values = {s: float(np.mean(v)) for s, v in sorted(by_structure.items())}
        out[measure] = {"by_structure": values, **s148.cluster_bootstrap(list(values.values()), rng)}
    return out


def copy_rates(records: list[dict]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for cell in sorted({r["cell_id"] for r in records}):
        rows = [r for r in records if r["cell_id"] == cell and r.get("cue_numeric_value") is not None]
        if not rows:
            continue
        parsed = [r for r in rows if r["parse_status"] == "PARSED"]
        k = sum(abs(r["parsed_answer"]["value"] - float(r["cue_numeric_value"])) < 1e-9 for r in parsed)
        out[cell] = {"n_records": len(rows), "n_parsed": len(parsed), "n_equal_to_cue_numeral": int(k),
                     "wilson95": wilson(k, len(parsed))}
    return out


def role_reversal(records: list[dict]) -> dict[str, Any]:
    rows = [r for r in records if r["cell_id"] == "role_reversal"]
    parsed = [r for r in rows if r["parse_status"] == "PARSED"]
    copies = sum(abs(r["parsed_answer"]["value"] - float(r["cue_numeric_value"])) < 1e-9 for r in parsed)
    sign_ok = sum((r["parsed_answer"]["value"] < 0) == (r["gold_value"] < 0) for r in parsed)
    return {"n_records": len(rows), "n_parsed": len(parsed), "n_equal_to_cue_numeral": int(copies),
            "n_correct": sum(r["correctness"] == "correct" for r in rows), "n_with_the_sign_of_the_gold": int(sign_ok),
            "gold_is_negative_in": sum(r["gold_value"] < 0 for r in rows),
            "limit": "the question asks for a difference, so these rates are not comparable with the isolated cells"}


def fmt(x: Any, digits: int = 2) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(results: dict[str, dict]) -> str:
    lines = ["# Stage 14.12 copying versus relevance, from the existing pilot records (descriptive)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. bfloat16, answer_line, ten structures.", ""]
    for model, res in results.items():
        lines += [f"## {model}", "", "**Unit modulation** (same-unit near cell minus incompatible-unit near cell; same gold string, decoy string and cue digits; only the prompt's unit differs):", "",
                  "| measure (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |", "|---|---|---|---|---|"]
        for measure in ("decoy_shift", "gold_shift", "r_alt_shift"):
            c = res["unit_modulation"][measure]
            ci = c["ci95"]
            lines.append(f"| {measure} | {c['n_structures']} | {fmt(c['mean'])} | "
                         f"{'NOT_EVALUATED' if ci is None else f'[{ci[0]:.2f}, {ci[1]:.2f}]'} | {c.get('n_positive', '-')} / {c.get('n_negative', '-')} |")
        lines += ["", f"Items excluded because the two cue numerals differ: {res['unit_modulation']['n_items_excluded']}.", "",
                  "**Generations equal to the cue numeral** (parsed generations; Wilson 95% interval):", "",
                  "| cell | parsed | equal to cue numeral | interval |", "|---|---|---|---|"]
        for cell, c in res["copy_rates"].items():
            w = c["wilson95"]
            lines.append(f"| {cell} | {c['n_parsed']} | {c['n_equal_to_cue_numeral']} | "
                         f"{'NOT_EVALUATED' if w is None else f'[{w[0]:.2f}, {w[1]:.2f}]'} |")
        r = res["role_reversal"]
        lines += ["", f"**Role reversal** (the cue quantity is relevant; the question asks for a difference): {r['n_parsed']} parsed of {r['n_records']}; "
                  f"{r['n_equal_to_cue_numeral']} equal to the cue numeral; {r['n_correct']} correct; {r['n_with_the_sign_of_the_gold']} with the sign of the gold "
                  f"(the gold is negative in {r['gold_is_negative_in']}). {r['limit']}.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of bfloat16 answer_line runs with anchor-prompt decoy scores")
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    args = parser.parse_args()
    sha = s148.git("rev-parse", "HEAD")
    day = s148.git("log", "-1", "--format=%cd", "--date=format:%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2
    rng = np.random.default_rng(s148.SEED)
    results: dict[str, Any] = {}
    inputs = {}
    for path in args.records:
        records = s148.load_records(Path(path))
        inputs[path] = {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "n_records": len(records)}
        results[records[0]["model_id"]] = {"unit_modulation": unit_modulation(records, rng), "copy_rates": copy_rates(records),
                                           "role_reversal": role_reversal(records)}
    summary = {"stage": "14.12", "kind": "copying versus relevance from existing records", "source_commit": sha,
               "git_status_short": s148.git("status", "--short").splitlines(), "command": " ".join(sys.argv), "inputs": inputs,
               "evidence_class": "exploratory; not paper-eligible", "models": results,
               "not_evaluated": {"matched relevant-role control": "no record scores the same candidate string where the same numeral plays a relevant role"}}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(report(results), encoding="utf-8")
    rows = [{"model": m, "cell": c, **{k: v[k] for k in ("n_records", "n_parsed", "n_equal_to_cue_numeral")}}
            for m, r in results.items() for c, v in r["copy_rates"].items()]
    with (out_dir / "copy_rates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model", "cell", "n_records", "n_parsed", "n_equal_to_cue_numeral"])
        writer.writeheader()
        writer.writerows(rows)
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(results)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
