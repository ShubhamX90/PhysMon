#!/usr/bin/env python3
"""Stage 14.17: analysis of the plausibility-matched numeral-presence control (CPU only; numpy).

Joins the raw records of the score-only run to the plan of `s159_matched_distance_plan.py` (by job id, which is unique) and
computes, for every numeral that appears in a prompt, the plausibility-adjusted presence effect: the log-probability of the numeral
as an answer (target unit, answer-line wrapper) minus the mean log-probability of its matched controls, which are absent from the
prompt, have the same shape and lie at about the same distance from the gold. Roles, structure averaging and the cluster bootstrap
(2,000 resamples, seed 42) are those of `s155_numeral_presence_analysis.py`, so the two analyses read on the same scale.

Reported three ways, frozen in J14.17-002: the primary effect (all matched controls); a sensitivity effect that keeps only controls
whose distance is within a factor of 2 of the numeral's own; and a sensitivity effect that keeps only controls that share the same
count of leading digits with the gold as the numeral. Groups: batch A (S01 to S10), batch B (S11 to S20) and the two pooled,
descriptively. When the Stage 14.14 records are supplied, the unadjusted effect of the same numerals is reported beside it, and the
present-numeral scores of the two runs are compared as a reproducibility check.

Reading rule (frozen): a role's adjusted effect is "above plausibility" only if its 95% interval excludes zero and the mean is at
least 0.4 nats (the 95th percentile of the dtype noise, J14.9-004 and J14.15-007); otherwise it is "not distinguishable from
plausibility at this precision", which is not equivalence. A numeral with no OK matched control is NOT_EVALUATED, never zero.
Descriptive and precision-limited; no p-values.

Plan reference: protocol section 5 row 4; P4; journals J14.14-005 and J14.17.
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

OUT_ROOT = "results/stage14/s160_matched_distance_analysis"
NOISE_THRESHOLD = 0.4
FACTOR = 2.0
BATCH_A_LAST = 10


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s155 = _load("s155_numeral_presence_analysis", "scripts/v2/s155_numeral_presence_analysis.py")
s148 = s155.s148


def batch_of(structure_id: str) -> str:
    return "A" if int(structure_id.lstrip("S")) <= BATCH_A_LAST else "B"


def join(records: list[dict], jobs: list[dict]) -> list[dict]:
    """Records joined to their planned candidate by job id; an unmatched record or a duplicate is an error."""

    by_id = {j["job_id"]: j for j in jobs}
    if len(by_id) != len(jobs):
        raise ValueError("the plan has duplicate job ids")
    seen: set[str] = set()
    rows = []
    for r in records:
        job = by_id.get(r["job_id"])
        if job is None:
            raise ValueError(f"record {r['job_id']} is not in the plan")
        if r["job_id"] in seen:
            raise ValueError(f"duplicate record {r['job_id']}")
        seen.add(r["job_id"])
        rows.append({"job_id": r["job_id"], "structure": job["structure_id"], "instance": int(job["instance"]), "cell": job["cell_id"],
                     "kind": job["candidate_kind"], "text": job["candidate_text"], "matched_to": job["candidate_matched_to"],
                     "role": job["candidate_role"], "unit_type": job.get("unit_type"),
                     "ratio": job.get("control_distance_ratio"), "control_prefix": job.get("control_prefix_overlap"),
                     "own_prefix": job.get("own_prefix_overlap"),
                     "lp": r["gold_logprob_raw"] if r["status"] == "OK" else None})
    return rows


def adjusted_effects(rows: list[dict], variant: str = "primary") -> list[dict]:
    """One adjusted effect per present numeral: lp(present) minus the mean lp of its OK matched controls (variant-filtered)."""

    controls: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r["kind"] == "matched_control" and r["lp"] is not None:
            controls[(r["structure"], r["instance"], r["cell"], r["matched_to"])].append(r)
    out = []
    for r in rows:
        if r["kind"] != "present":
            continue
        chosen = controls.get((r["structure"], r["instance"], r["cell"], r["text"]), [])
        if variant == "within_factor_2":
            chosen = [c for c in chosen if c["ratio"] is not None and 1 / FACTOR <= c["ratio"] <= FACTOR]
        elif variant == "same_prefix_overlap":
            chosen = [c for c in chosen if c["control_prefix"] == c["own_prefix"]]
        effect = None if r["lp"] is None or not chosen else r["lp"] - float(np.mean([c["lp"] for c in chosen]))
        out.append({**r, "effect": effect, "n_controls": len(chosen)})
    return out


def reading(summary: dict[str, Any]) -> str:
    ci = summary.get("ci95")
    if ci is None or summary.get("mean") is None:
        return "NOT_EVALUATED"
    if ci[0] > 0 and summary["mean"] >= NOISE_THRESHOLD:
        return "above plausibility"
    return "not distinguishable from plausibility at this precision"


def analyse_group(effects: list[dict], rng: np.random.Generator) -> dict[str, Any]:
    result = s155.analyse_effects(effects, rng)
    for section in ("role_presence_effect", "paired_contrasts"):
        for entry in result[section].values():
            entry["reading"] = reading(entry)
    return result


def analyse(rows: list[dict], rng: np.random.Generator, earlier_rows: list[dict] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for variant in ("primary", "within_factor_2", "same_prefix_overlap"):
        effects = adjusted_effects(rows, variant)
        groups = {"A": [e for e in effects if batch_of(e["structure"]) == "A"],
                  "B": [e for e in effects if batch_of(e["structure"]) == "B"], "A+B (descriptive pooling)": effects}
        out[variant] = {g: {**analyse_group(es, rng), "n_numerals_without_effect": sum(e["effect"] is None for e in es)}
                        for g, es in groups.items() if es}
    if earlier_rows is not None:
        keyed = {(e["structure"], e["instance"], e["cell"], e["text"]) for e in adjusted_effects(rows) if e["effect"] is not None}
        old = [e for e in s155.presence_effects(earlier_rows)
               if (e["structure"], e["instance"], e["cell"], e["text"]) in keyed]
        new = [e for e in adjusted_effects(rows) if (e["structure"], e["instance"], e["cell"], e["text"]) in {
            (o["structure"], o["instance"], o["cell"], o["text"]) for o in old if o["effect"] is not None}]
        out["unadjusted_same_numerals_batch_A"] = analyse_group(old, rng)
        out["adjusted_same_numerals_batch_A"] = analyse_group(new, rng)
        out["reproducibility"] = reproducibility(rows, earlier_rows)
    return out


def reproducibility(rows: list[dict], earlier_rows: list[dict]) -> dict[str, Any]:
    """Present-numeral scores of this run against the Stage 14.14 run (same prompt, string, model, dtype, node type)."""

    old = {(r["structure"], r["instance"], r["cell"], r["text"]): r["lp"] for r in earlier_rows if r["kind"] == "present"}
    diffs = [abs(r["lp"] - old[k]) for r in rows if r["kind"] == "present" and r["lp"] is not None
             for k in [(r["structure"], r["instance"], r["cell"], r["text"])] if k in old and old[k] is not None]
    if not diffs:
        return {"n": 0, "status": "NOT_EVALUATED"}
    return {"n": len(diffs), "max_abs_difference": float(max(diffs)), "mean_abs_difference": float(np.mean(diffs)),
            "n_exactly_equal": int(sum(d == 0.0 for d in diffs))}


def fmt(x: Any, digits: int = 2) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(models: dict[str, Any]) -> str:
    lines = ["# Stage 14.17 plausibility-matched numeral-presence control (descriptive, precision-limited)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Adjusted presence effect = log-probability",
             "(nats) of a numeral that appears in the prompt, as an answer with the target unit, minus the mean of matched absent numerals of the",
             "same shape at about the same distance from the gold. Intervals are cluster bootstrap over structures (2,000 resamples, seed 42).",
             f"Reading rule: 'above plausibility' needs an interval above zero and a mean of at least {NOISE_THRESHOLD} nats; otherwise 'not",
             "distinguishable from plausibility at this precision', which is not equivalence.", ""]
    for key, res in models.items():
        lines += [f"## {key}", ""]
        for variant in ("primary", "within_factor_2", "same_prefix_overlap"):
            for group, g in res[variant].items():
                lines += [f"### {variant}, batch {group}", "", f"Numerals without an effect: {g['n_numerals_without_effect']}.", "",
                          "| Role | structures | mean adjusted effect | 95% interval | up / down | reading |", "|---|---|---|---|---|---|"]
                for section in ("role_presence_effect", "paired_contrasts"):
                    if section == "paired_contrasts":
                        lines.append("| *paired within a prompt* | | | | | |")
                    for name, c in g[section].items():
                        ci = c["ci95"]
                        lines.append(f"| {name} | {c['n_structures']} | {fmt(c['mean'])} | "
                                     f"{'NOT_EVALUATED' if ci is None else f'[{ci[0]:.2f}, {ci[1]:.2f}]'} | "
                                     f"{c.get('n_positive', '-')} / {c.get('n_negative', '-')} | {c['reading']} |")
                lines.append("")
        if "unadjusted_same_numerals_batch_A" in res:
            lines += ["### Unadjusted (Stage 14.14 control) and adjusted effects of the same batch-A numerals", "",
                      "| Role | unadjusted | adjusted | difference |", "|---|---|---|---|"]
            un, ad = res["unadjusted_same_numerals_batch_A"]["role_presence_effect"], res["adjusted_same_numerals_batch_A"]["role_presence_effect"]
            for name in sorted(set(un) & set(ad)):
                u, a = un[name]["mean"], ad[name]["mean"]
                lines.append(f"| {name} | {fmt(u)} | {fmt(a)} | {fmt(None if u is None or a is None else u - a)} |")
            rep = res["reproducibility"]
            lines += ["", f"Reproducibility of the present-numeral scores against the Stage 14.14 run: {rep}.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of the matched-control run, one per model")
    parser.add_argument("--presence-plan-dir", default=None, help="the Stage 14.14 plan (optional, for the unadjusted comparison)")
    parser.add_argument("--presence-records", nargs="*", default=[], help="the Stage 14.14 raw records, one per model")
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
    plan_manifest = Path(args.plan_dir) / "job_manifest.jsonl"
    jobs_all = [json.loads(line) for line in plan_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    earlier_jobs = None
    if args.presence_plan_dir:
        earlier_jobs = [json.loads(line) for line in (Path(args.presence_plan_dir) / "job_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rng = np.random.default_rng(s148.SEED)
    models: dict[str, Any] = {}
    inputs: dict[str, Any] = {"plan_job_manifest": hashlib.sha256(plan_manifest.read_bytes()).hexdigest()}
    earlier_by_model: dict[str, list[dict]] = {}
    for path in args.presence_records:
        recs = s148.load_records(Path(path))
        inputs[path] = {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "n_records": len(recs)}
        earlier_by_model[recs[0]["model_id"]] = recs
    for path in args.records:
        records = s148.load_records(Path(path))
        inputs[path] = {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "n_records": len(records)}
        model_key = next(j["model_key"] for j in jobs_all if j["job_id"] == records[0]["job_id"])
        model_id = records[0]["model_id"]
        earlier_rows = None
        if earlier_jobs is not None and model_id in earlier_by_model:
            earlier_rows = s155.join(earlier_by_model[model_id], [j for j in earlier_jobs if j["model_key"] == model_key])
        models[model_id] = analyse(join(records, [j for j in jobs_all if j["model_key"] == model_key]), rng, earlier_rows)
    summary = {"stage": "14.17", "kind": "plausibility-matched numeral-presence analysis", "source_commit": sha,
               "git_status_short": s148.git("status", "--short").splitlines(), "command": " ".join(sys.argv), "inputs": inputs,
               "noise_threshold_nats": NOISE_THRESHOLD, "evidence_class": "exploratory; not paper-eligible", "models": models}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(report(models), encoding="utf-8")
    flat = [{"model": m, "variant": v, "group": g, "section": s, "name": n, "n_structures": c["n_structures"], "mean": c["mean"],
             "ci95_low": None if c["ci95"] is None else c["ci95"][0], "ci95_high": None if c["ci95"] is None else c["ci95"][1],
             "reading": c["reading"]}
            for m, r in models.items() for v in ("primary", "within_factor_2", "same_prefix_overlap") for g, gr in r[v].items()
            for s in ("role_presence_effect", "paired_contrasts") for n, c in gr[s].items()]
    with (out_dir / "adjusted_presence_effects.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat[0]) if flat else ["model"])
        writer.writeheader()
        writer.writerows(flat)
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
