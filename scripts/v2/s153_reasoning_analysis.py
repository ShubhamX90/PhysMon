#!/usr/bin/env python3
"""Stage 14.13: analysis of the reasoning-allowed run, to the rule frozen in journal J14.13-002 (CPU only; numpy).

Per model: eligibility strata with denominators (all valid, parseable, base-correct no-cue anchors), the gate for the correctness
endpoint (at least 8 of the 20 no-cue anchors correct, else NOT_EVALUATED and the floor is reported as persisting), the
correct-to-wrong flip share of each cue cell among base-correct instantiations by structure (cluster bootstrap over structures
that have at least one graded base-correct item) with the reverse transition as the chance reading, the copy rate of the cue
numeral in the final answer per cell (Wilson interval), the parse outcomes by cell, and the response to the relevant edit.
Outcomes that are not graded (TRUNCATED, UNPARSEABLE, MULTIPLE_CANDIDATES, EMPTY) are NOT_EVALUATED: they are in neither the
numerator nor the denominator of a flip share, and they are reported by cell and model. Descriptive; ten structures; no p-values.

Plan reference: B2.4 (p.8), §8.4 (p.42), protocol sections 3, 4 and 4b.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT_ROOT = "results/stage14/s153_reasoning_analysis"
GATE_MIN_BASE_CORRECT = 8
GRADED = ("correct", "wrong")


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s148 = _load("s148_pilot_analysis", "scripts/v2/s148_pilot_analysis.py")
s151 = _load("s151_copying_vs_relevance", "scripts/v2/s151_copying_vs_relevance.py")


def key_of(record: dict) -> tuple[str, int, str]:
    return record["structure_id"], int(record["instance"]), record["cell_id"]


def index(records: list[dict]) -> dict[tuple[str, int, str], dict]:
    out: dict[tuple[str, int, str], dict] = {}
    for record in records:
        key = key_of(record)
        if key in out:
            raise ValueError(f"duplicate record for {key}")
        out[key] = record
    return out


def eligibility(records: list[dict], idx: dict) -> dict[str, Any]:
    anchors = [r for k, r in idx.items() if k[2] == s148.ANCHOR]
    return {"all_valid_items": sum(r["status"] == "OK" for r in records),
            "parseable": sum(r["parse_status"] == "PARSED" for r in records),
            "anchors": len(anchors), "anchors_graded": sum(r["correctness"] in GRADED for r in anchors),
            "base_correct_anchors": sum(r["correctness"] == "correct" for r in anchors),
            "gate_min_base_correct": GATE_MIN_BASE_CORRECT}


def flip_shares(idx: dict, rng: np.random.Generator) -> dict[str, Any]:
    """Wrong share of each cue cell among base-correct instantiations, and the reverse among base-wrong ones."""

    out: dict[str, Any] = {}
    for cell in s148.CUE_CELLS:
        for label, anchor_state, target in (("flip_to_wrong_given_base_correct", "correct", "wrong"),
                                            ("rescue_to_correct_given_base_wrong", "wrong", "correct")):
            by_structure: dict[str, list[float]] = defaultdict(list)
            n_graded = n_hit = n_not_graded = 0
            for (structure, instance, c), rec in idx.items():
                if c != cell:
                    continue
                anchor = idx.get((structure, instance, s148.ANCHOR))
                if anchor is None or anchor["correctness"] != anchor_state:
                    continue
                if rec["correctness"] not in GRADED:
                    n_not_graded += 1
                    continue
                n_graded += 1
                n_hit += rec["correctness"] == target
                by_structure[structure].append(float(rec["correctness"] == target))
            values = {s: float(np.mean(v)) for s, v in sorted(by_structure.items())}
            out[f"{label}[{cell}]"] = {"n_graded": n_graded, "n_hit": int(n_hit), "n_not_graded": n_not_graded,
                                       "by_structure": values, **s148.cluster_bootstrap(list(values.values()), rng)}
    return out


def cell_outcomes(records: list[dict]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cell in sorted({r["cell_id"] for r in records}):
        rows = [r for r in records if r["cell_id"] == cell]
        counts: dict[str, int] = defaultdict(int)
        for r in rows:
            counts[r["parse_status"]] += 1
        graded = [r for r in rows if r["correctness"] in GRADED]
        out[cell] = {"n": len(rows), "parse_status_counts": dict(sorted(counts.items())),
                     "n_graded": len(graded), "n_correct": sum(r["correctness"] == "correct" for r in graded),
                     "mean_generated_tokens": float(np.mean([r["n_generated_tokens"] for r in rows]))}
    return out


def assay_check(idx: dict) -> dict[str, Any]:
    edit = [r for k, r in idx.items() if k[2] == "relevant_edit"]
    graded = [r for r in edit if r["correctness"] in GRADED]
    return {"n": len(edit), "n_graded": len(graded), "n_correct_under_edit": sum(r["correctness"] == "correct" for r in graded),
            "note": "the gold of this cell differs from the anchor's; a correct answer under the edited prompt shows the assay follows a relevant change"}


def analyse_model(records: list[dict], rng: np.random.Generator) -> dict[str, Any]:
    idx = index(records)
    strata = eligibility(records, idx)
    gate_met = strata["base_correct_anchors"] >= GATE_MIN_BASE_CORRECT
    entry: dict[str, Any] = {"model_id": records[0]["model_id"], "n_records": len(records), "eligibility": strata,
                             "gate_met": gate_met, "cell_outcomes": cell_outcomes(records),
                             "copy_rate_of_cue_numeral": s151.copy_rates(records), "relevant_edit_assay": assay_check(idx)}
    if gate_met:
        entry["correctness_transitions"] = flip_shares(idx, rng)
    else:
        entry["correctness_transitions"] = (f"NOT_EVALUATED: {strata['base_correct_anchors']} of {strata['anchors']} no-cue anchors are correct, "
                                            f"below the gate of {GATE_MIN_BASE_CORRECT}; the correctness floor persists")
    return entry


def fmt(x: Any, digits: int = 2) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(models: dict[str, Any]) -> str:
    lines = ["# Stage 14.13 reasoning-allowed pilot analysis (descriptive)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Rule frozen in J14.13-002 before the run.",
             "Ungraded outcomes (TRUNCATED, UNPARSEABLE, MULTIPLE_CANDIDATES, EMPTY) are NOT_EVALUATED and in no flip share.", ""]
    for key, res in models.items():
        e = res["eligibility"]
        lines += [f"## {key}", "", f"Records {res['n_records']}; valid {e['all_valid_items']}; parseable {e['parseable']}; no-cue anchors {e['anchors']} "
                  f"(graded {e['anchors_graded']}, correct {e['base_correct_anchors']}); gate (at least {e['gate_min_base_correct']} correct): "
                  f"{'met' if res['gate_met'] else 'NOT met'}.", ""]
        t = res["correctness_transitions"]
        if isinstance(t, str):
            lines += [t, ""]
        else:
            lines += ["| Transition | graded | hits | structures | mean share [interval] |", "|---|---|---|---|---|"]
            for name, c in t.items():
                ci = c["ci95"]
                lines.append(f"| {name} | {c['n_graded']} | {c['n_hit']} | {c['n_structures']} | "
                             f"{fmt(c['mean'])} {'' if ci is None else f'[{ci[0]:.2f}, {ci[1]:.2f}]'} |")
            lines.append("")
        lines += ["| Cell | n | parse outcomes | graded | correct | mean generated tokens |", "|---|---|---|---|---|---|"]
        for cell, c in res["cell_outcomes"].items():
            lines.append(f"| {cell} | {c['n']} | {c['parse_status_counts']} | {c['n_graded']} | {c['n_correct']} | {c['mean_generated_tokens']:.0f} |")
        a = res["relevant_edit_assay"]
        lines += ["", f"Relevant-edit assay: {a['n_correct_under_edit']} correct of {a['n_graded']} graded ({a['n']} records).", "",
                  "Cue numeral as the final answer: " + "; ".join(
                      f"{c.replace('nongov_', '')} {v['n_equal_to_cue_numeral']}/{v['n_parsed']}" for c, v in res["copy_rate_of_cue_numeral"].items()), ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of the reasoning run, one per model")
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
    models: dict[str, Any] = {}
    inputs = {}
    for path in args.records:
        records = s148.load_records(Path(path))
        inputs[path] = {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "n_records": len(records)}
        models[records[0]["model_id"]] = analyse_model(records, rng)
    summary = {"stage": "14.13", "kind": "reasoning-allowed pilot analysis", "source_commit": sha,
               "git_status_short": s148.git("status", "--short").splitlines(), "command": " ".join(sys.argv), "inputs": inputs,
               "evidence_class": "exploratory; not paper-eligible", "gate_min_base_correct": GATE_MIN_BASE_CORRECT, "models": models}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(report(models), encoding="utf-8")
    rows = [{"model": m, "cell": c, **{k: v[k] for k in ("n", "n_graded", "n_correct", "mean_generated_tokens")}}
            for m, r in models.items() for c, v in r["cell_outcomes"].items()]
    with (out_dir / "cell_outcomes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model", "cell", "n", "n_graded", "n_correct", "mean_generated_tokens"])
        writer.writeheader()
        writer.writerows(rows)
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
