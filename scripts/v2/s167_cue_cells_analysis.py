#!/usr/bin/env python3
"""Stage 14.20: sensitivity of a thinking model to distractor cells on its anchors (CPU only; numpy).

Reads the raw records of `s164_thinking_run.py` for the no-cue samples (`--base-records`, Stage A plus the resample job) and for the cue
cells (`--cell-records`), restricted to the anchors file. Rules fixed in journal J14.19-010 before any cell record existed:

1. Baseline, per anchor structure: the share of correct answers among its graded no-cue samples (the model's own sampling noise).
2. Cue cells, per anchor structure and cue role: the share of correct answers among its graded cells, each graded against its own gold by the
   declared rule (for `relevant_edit` and `role_reversed` the gold is the changed answer, so correct means the model followed the change).
3. Contrast, per role: cue-cell correct share minus baseline correct share, per structure; mean over structures with a graded value on both
   sides, with a cluster bootstrap over structures (2,000 resamples, seed 42). A role is read as distinguishable from sampling noise only if
   the 95% interval excludes 0; no one-sided reading rule is used.
4. NOT_EVALUATED (TRUNCATED, UNPARSEABLE, MULTIPLE_CANDIDATES, EMPTY) is counted by role next to the baseline share, never as wrong. A cue that
   lengthens thinking is reported through the share truncated and the median generated tokens, not through correctness.
5. A strict sensitivity reading with the unit-convertible label is reported next to the declared grade.

Nothing is promoted to a result: one model, exploratory, data role EXPLORATION, not paper-eligible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = "results/stage14/s167_cue_cells_analysis"
SEED = 42
N_BOOT = 2000
GRADED = ("correct", "wrong")


def load(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def correct_flag(r: dict, convertible: bool) -> bool | None:
    """True/False for a graded record, None for NOT_EVALUATED."""
    if r["correctness"] not in GRADED:
        return None
    if r["correctness"] == "correct":
        return True
    return bool(convertible and r.get("correct_if_units_convertible") is True)


def share_by_structure(records: list[dict], key_ok: set[str], convertible: bool) -> dict[str, float]:
    by: dict[str, list[bool]] = defaultdict(list)
    for r in records:
        if f"{r['structure_id']}:{r['instance']}" not in key_ok:
            continue
        flag = correct_flag(r, convertible)
        if flag is not None:
            by[r["structure_id"]].append(flag)
    return {s: float(np.mean(v)) for s, v in by.items()}


def bootstrap_mean(values: list[float], rng: np.random.Generator) -> dict[str, Any]:
    if len(values) < 2:
        return {"n_structures": len(values), "mean": None if not values else float(values[0]), "ci95": None, "status": "NOT_EVALUATED"}
    arr = np.array(values)
    means = [float(rng.choice(arr, size=len(arr), replace=True).mean()) for _ in range(N_BOOT)]
    return {"n_structures": len(arr), "mean": float(arr.mean()), "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]}


def reading(b: dict[str, Any]) -> str:
    if b.get("ci95") is None:
        return "NOT_EVALUATED"
    lo, hi = b["ci95"]
    return "distinguishable from sampling noise" if lo > 0 or hi < 0 else "not distinguishable from sampling noise"


def role_outcomes(records: list[dict]) -> dict[str, Any]:
    n = len(records)
    toks = [r["n_generated_tokens"] for r in records]
    cnt = Counter(r["correctness"] for r in records)
    ungraded = n - sum(cnt[c] for c in GRADED)
    return {"n_records": n, "correctness": dict(cnt), "n_not_evaluated": ungraded, "share_truncated": (cnt["TRUNCATED"] / n) if n else None,
            "tokens_median": float(np.median(toks)) if toks else None}


def analyse(base: list[dict], cells: list[dict], anchors: list[str], rng: np.random.Generator, convertible: bool = False) -> dict[str, Any]:
    keep = set(anchors)
    base = [r for r in base if f"{r['structure_id']}:{r['instance']}" in keep]
    cells = [r for r in cells if f"{r['structure_id']}:{r['instance']}" in keep]
    baseline = share_by_structure(base, keep, convertible)
    roles = sorted({r["cue_semantic_role"] for r in cells})
    out: dict[str, Any] = {"n_anchors": len(keep), "n_base_records": len(base), "n_cell_records": len(cells),
                           "baseline_correct_share_by_structure": bootstrap_mean(list(baseline.values()), rng),
                           "baseline_outcomes": role_outcomes(base), "roles": {}}
    for role in roles:
        rows = [r for r in cells if r["cue_semantic_role"] == role]
        share = share_by_structure(rows, keep, convertible)
        paired = sorted(set(share) & set(baseline))
        contrast = bootstrap_mean([share[s] - baseline[s] for s in paired], rng)
        out["roles"][role] = {"outcomes": role_outcomes(rows), "cue_correct_share_by_structure": bootstrap_mean(list(share.values()), rng),
                              "contrast_vs_baseline": contrast, "reading": reading(contrast), "n_paired_structures": len(paired),
                              "expected_effect": sorted({str(r.get("expected_effect")) for r in rows})}
    return out


def fmt(x: Any) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.3f}"


def report(res: dict[str, Any], label: str) -> str:
    lines = [f"# Cue cells on the anchors, {label} (descriptive)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; one model. NOT_EVALUATED is never wrong. Intervals are cluster bootstrap over structures (2,000, seed 42).", "",
             f"Anchors {res['n_anchors']}; no-cue records {res['n_base_records']}; cue-cell records {res['n_cell_records']}; "
             f"baseline correct share by structure {fmt(res['baseline_correct_share_by_structure']['mean'])} {res['baseline_correct_share_by_structure']['ci95']}; "
             f"baseline not evaluated {res['baseline_outcomes']['n_not_evaluated']} of {res['baseline_outcomes']['n_records']}.", "",
             "| cue role | records | not evaluated | truncated share | tokens median | correct share | contrast vs baseline | 95% interval | pairs | reading |", "|---|---|---|---|---|---|---|---|---|---|"]
    for role, v in res["roles"].items():
        c = v["contrast_vs_baseline"]
        lines.append(f"| {role} | {v['outcomes']['n_records']} | {v['outcomes']['n_not_evaluated']} | {fmt(v['outcomes']['share_truncated'])} | "
                     f"{fmt(v['outcomes']['tokens_median'])} | {fmt(v['cue_correct_share_by_structure']['mean'])} | {fmt(c['mean'])} | {c['ci95']} | "
                     f"{v['n_paired_structures']} | {v['reading']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-records", nargs="+", required=True, help="raw_records.jsonl of no-cue runs (Stage A and the resample)")
    parser.add_argument("--cell-records", nargs="+", required=True)
    parser.add_argument("--anchors", required=True, help="JSON list of structure:instance keys (the subset the cells were run on)")
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--out-root", default=OUT_ROOT)
    args = parser.parse_args()
    out_dir = (REPO_ROOT / args.out_root / args.attempt_id).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2
    anchors = json.loads(Path(args.anchors).read_text(encoding="utf-8"))
    base = [r for p in args.base_records for r in load(p)]
    cells = [r for p in args.cell_records for r in load(p)]
    inputs = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [*args.base_records, *args.cell_records, args.anchors]}
    rng = np.random.default_rng(SEED)
    res = {"declared_grade": analyse(base, cells, anchors, rng, False), "unit_convertible_sensitivity": analyse(base, cells, anchors, rng, True)}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(report(res["declared_grade"], "declared grade") + "\n" + report(res["unit_convertible_sensitivity"], "unit-convertible sensitivity"), encoding="utf-8")
    summary = {"stage": "14.20", "kind": "cue cells on anchors", "command": " ".join(sys.argv), "inputs": inputs, "evidence_class": "exploratory; not paper-eligible", "results": res}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"attempt_dir": str(out_dir.relative_to(REPO_ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
