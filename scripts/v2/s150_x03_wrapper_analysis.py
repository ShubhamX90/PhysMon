#!/usr/bin/env python3
"""Stage 14.10: X03 wrapper-by-nuisance analysis (CPU only; numpy), to the rule frozen in journal J14.10-001.

For each model and each output wrapper it computes, by structure, the anchor-matched shift of R_alt from the no-cue prompt
in every decoy cell (Stage 14.9), the reference-free range D_lp of the gold log-probability across cells that share the gold
string, the parse rate and the correctness counts. The wrapper-by-nuisance interaction is the per-structure difference of the
shift under a wrapper and under the reference wrapper `answer_line`, summarised by a cluster bootstrap over structures
(2,000 resamples, seed 42).

Frozen criteria (J14.10-001), applied to the same-unit near cell:
- dominance: the wrapper-minus-reference interval excludes zero and |difference| >= half of |shift under the reference|;
- invariance: no wrapper has a difference interval that excludes zero; this means no detectable wrapper dependence at ten
  structures, not equivalence.
Raw sums are compared only within a wrapper and across structures, never across wrappers as quantities of different length.
Descriptive and precision-limited; no p-values. Anything that cannot be computed is NOT_EVALUATED.

Plan reference: card X03 (v2 p.39), P1.3 and P1.4 (p.17), protocol sections 3 and 4.
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

OUT_ROOT = "results/stage14/x03_format_tokenization/analysis"
REFERENCE_WRAPPER = "answer_line"
DOMINANCE_FRACTION = 0.5


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s148 = _load("s148_pilot_analysis", "scripts/v2/s148_pilot_analysis.py")
s149 = _load("s149_noise_and_anchor_analysis", "scripts/v2/s149_noise_and_anchor_analysis.py")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def by_wrapper(records: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        out[record["answer_wrapper_id"]].append(record)
    return dict(out)


def structure_means(per_item: dict[tuple[str, int], float]) -> dict[str, float]:
    by_structure: dict[str, list[float]] = defaultdict(list)
    for (structure, _), value in per_item.items():
        by_structure[structure].append(value)
    return {s: float(np.mean(v)) for s, v in sorted(by_structure.items())}


def wrapper_summary(records: list[dict]) -> dict[str, Any]:
    """Shifts, D_lp, parse and correctness counts for one model under one wrapper."""

    shifts = s149.anchor_shifts(records)
    index = s148.index_records(records)
    model = records[0]["model_id"]
    d_lp: dict[tuple[str, int], float] = {}
    for structure, instance in sorted({(k[1], k[2]) for k in index}):
        cells = {k[3]: v for k, v in index.items() if k[:3] == (model, structure, instance)}
        value = s148.d_lp(cells)["range"]
        if value is not None:
            d_lp[(structure, instance)] = value
    parsed = [r for r in records if r["parse_status"] == "PARSED"]
    return {"n_records": len(records), "n_parsed": len(parsed),
            "parse_status_counts": dict(sorted(_count(r["parse_status"] for r in records).items())),
            "correctness_counts": dict(sorted(_count(r["correctness"] for r in records).items())),
            "mean_gold_answer_tokens": float(np.mean([len(r["target_answer_ids"]) for r in records if r.get("target_answer_ids")]))
            if any(r.get("target_answer_ids") for r in records) else None,
            "shift_by_item": {cell: {(s, i): v["r_alt_shift"] for (s, i, c), v in shifts.items() if c == cell}
                              for cell in s148.DECOY_CELLS},
            "d_lp_by_item": d_lp}


def _count(values) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for v in values:
        out[v] += 1
    return out


def interaction(candidate: dict[tuple[str, int], float], reference: dict[tuple[str, int], float],
                rng: np.random.Generator) -> dict[str, Any]:
    """Per structure, mean over instantiations of candidate minus reference; cluster bootstrap over structures."""

    diffs = {k: candidate[k] - reference[k] for k in candidate if k in reference}
    values = structure_means(diffs)
    return {"by_structure": values, **s148.cluster_bootstrap(list(values.values()), rng)}


def classify(difference: dict[str, Any], reference_shift: float | None) -> dict[str, Any]:
    """Apply the frozen dominance criterion to one wrapper-minus-reference difference of the near-cell shift."""

    ci, mean = difference.get("ci95"), difference.get("mean")
    if ci is None or mean is None or reference_shift is None:
        return {"excludes_zero": None, "dominates": None, "status": "NOT_EVALUATED"}
    excludes = ci[0] > 0 or ci[1] < 0
    large = abs(mean) >= DOMINANCE_FRACTION * abs(reference_shift)
    return {"excludes_zero": bool(excludes), "dominates": bool(excludes and large), "status": "evaluated"}


def analyse_model(records: list[dict], rng: np.random.Generator) -> dict[str, Any]:
    wrappers = by_wrapper(records)
    summaries = {w: wrapper_summary(r) for w, r in sorted(wrappers.items())}
    reference = summaries.get(REFERENCE_WRAPPER)
    ref_near = None
    if reference is not None:
        ref_by = structure_means(reference["shift_by_item"][s148.NEAR])
        ref_near = float(np.mean(list(ref_by.values()))) if ref_by else None
    out: dict[str, Any] = {"model_id": records[0]["model_id"], "wrappers": {}}
    verdicts = []
    for wrapper, summary in summaries.items():
        entry: dict[str, Any] = {k: v for k, v in summary.items() if k not in ("shift_by_item", "d_lp_by_item")}
        entry["shift_by_structure"] = {}
        entry["interaction_vs_reference"] = {}
        for cell, per_item in summary["shift_by_item"].items():
            by_structure = structure_means(per_item)
            entry["shift_by_structure"][cell] = {"by_structure": by_structure,
                                                 **s148.cluster_bootstrap(list(by_structure.values()), rng)}
            if reference is not None and wrapper != REFERENCE_WRAPPER:
                entry["interaction_vs_reference"][cell] = interaction(per_item, reference["shift_by_item"][cell], rng)
        by_structure = structure_means(summary["d_lp_by_item"])
        entry["D_lp_range"] = {"by_structure": by_structure, **s148.cluster_bootstrap(list(by_structure.values()), rng)}
        if reference is not None and wrapper != REFERENCE_WRAPPER:
            entry["D_lp_range_vs_reference"] = interaction(summary["d_lp_by_item"], reference["d_lp_by_item"], rng)
            entry["near_cell_verdict"] = classify(entry["interaction_vs_reference"][s148.NEAR], ref_near)
            verdicts.append(entry["near_cell_verdict"])
        out["wrappers"][wrapper] = entry
    evaluated = [v for v in verdicts if v["status"] == "evaluated"]
    out["overall"] = {
        "n_wrappers_compared": len(evaluated),
        "wrappers_that_dominate": sorted(w for w, e in out["wrappers"].items()
                                         if e.get("near_cell_verdict", {}).get("dominates")),
        "invariance": (None if not evaluated else not any(v["excludes_zero"] for v in evaluated)),
        "note": "invariance means no interval excludes zero at ten structures; it is not equivalence",
    }
    return out


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c) for c in columns})


def fmt(x: Any, digits: int = 2) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(models: dict[str, Any]) -> str:
    lines = ["# Stage 14.10 X03 wrapper analysis (descriptive, precision-limited)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Quantities are anchor-matched shifts of R_alt",
             "(nats) from the no-cue prompt, by structure (n = 10); intervals are cluster bootstrap over structures (2,000 resamples, seed 42).",
             "Criteria were frozen in J14.10-001 before the run. Raw sums are compared within a wrapper only.", ""]
    for key, res in models.items():
        o = res["overall"]
        lines += [f"## {key}", "", f"Wrappers that dominate the near-cell shift: {o['wrappers_that_dominate'] or 'none'}; invariance "
                  f"(no interval excludes zero): {o['invariance']}. {o['note']}.", ""]
        lines += ["| Wrapper | records | parsed | correct | mean gold tokens | near-cell shift (mean [interval]) | minus answer_line [interval] | excludes zero | dominates | D_lp range mean |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for w, e in res["wrappers"].items():
            s = e["shift_by_structure"][s148.NEAR]
            ci = s["ci95"]
            near = f"{fmt(s['mean'])} [{ci[0]:.2f}, {ci[1]:.2f}]" if ci else fmt(s["mean"])
            inter = e["interaction_vs_reference"].get(s148.NEAR)
            ic = None if inter is None else inter["ci95"]
            diff = "reference" if inter is None else (f"{fmt(inter['mean'])} [{ic[0]:.2f}, {ic[1]:.2f}]" if ic else fmt(inter["mean"]))
            v = e.get("near_cell_verdict", {})
            lines.append(f"| {w} | {e['n_records']} | {e['n_parsed']} | {e['correctness_counts'].get('correct', 0)} | "
                         f"{fmt(e['mean_gold_answer_tokens'], 1)} | {near} | {diff} | {v.get('excludes_zero', '-')} | {v.get('dominates', '-')} | "
                         f"{fmt(e['D_lp_range']['mean'])} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of the X03 run, one per model")
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
        inputs[path] = {"sha256": sha256_file(Path(path)), "n_records": len(records)}
        by_model = defaultdict(list)
        for r in records:
            by_model[r["model_id"]].append(r)
        for model_id, rows in sorted(by_model.items()):
            models[model_id] = analyse_model(rows, rng)
    summary = {"stage": "14.10", "kind": "X03 wrapper-by-nuisance analysis", "source_commit": sha,
               "git_status_short": s148.git("status", "--short").splitlines(), "command": " ".join(sys.argv),
               "inputs": inputs, "evidence_class": "exploratory; not paper-eligible", "reference_wrapper": REFERENCE_WRAPPER,
               "dominance_fraction": DOMINANCE_FRACTION, "models": models}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    rows = []
    for model_id, res in models.items():
        for w, e in res["wrappers"].items():
            for cell, inter in e["interaction_vs_reference"].items():
                rows.append({"model": model_id, "wrapper": w, "cell": cell, "n_structures": inter["n_structures"],
                             "mean_difference": inter["mean"], "ci95_low": None if inter["ci95"] is None else inter["ci95"][0],
                             "ci95_high": None if inter["ci95"] is None else inter["ci95"][1]})
    write_csv(out_dir / "wrapper_minus_reference_shift.csv", rows,
              ["model", "wrapper", "cell", "n_structures", "mean_difference", "ci95_low", "ci95_high"])
    (out_dir / "report.md").write_text(report(models), encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
