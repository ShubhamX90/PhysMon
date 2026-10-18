#!/usr/bin/env python3
"""Stage 14.16: analysis of the legacy-family X03 run, to the rule frozen in journal J14.16-003 (CPU only; numpy).

Joins the raw records to the plan by job id. For each family, wrapper, model and numeral cue candidate u it computes the
within-string presence effect: the log-probability of the candidate under its own rendering (the diagonal) minus the mean
log-probability of the same string under the other renderings in which the numeral does not appear. Family values are averaged
within a Stage 14.4 template cluster; the interval is a cluster bootstrap (2,000 resamples, seed 42). The wrapper interaction is the
cluster-level difference from `answer_line`, with the frozen dominance and invariance criteria; D_lp is the range of the gold
log-probability across the four renderings.

A candidate with no usable off-diagonal cell, a record that is not OK, and a family without a numeric cue are NOT_EVALUATED and
left out, never counted as zero. Descriptive and precision-limited; no p-values.

Plan reference: card X03 (v2 p.39), P1.3 and P1.4 (p.17), journal J14.16-003.
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

OUT_ROOT = "results/stage14/s157_legacy_x03_analysis"
REFERENCE_WRAPPER = "answer_line"
DOMINANCE_FRACTION = 0.5


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s148 = _load("s148_pilot_analysis", "scripts/v2/s148_pilot_analysis.py")


def join(records: list[dict], jobs: list[dict]) -> list[dict]:
    by_id = {j["job_id"]: j for j in jobs}
    seen: set[str] = set()
    rows = []
    for r in records:
        if r["job_id"] not in by_id:
            raise ValueError(f"record {r['job_id']} is not in the plan")
        if r["job_id"] in seen:
            raise ValueError(f"duplicate record {r['job_id']}")
        seen.add(r["job_id"])
        j = by_id[r["job_id"]]
        rows.append({**{k: j[k] for k in ("structure_id", "template_cluster_id", "wrapper_id", "candidate_kind", "candidate_text",
                                          "candidate_source_variant", "candidate_numeral_in_prompt", "prompt_variant",
                                          "cue_semantic_role")},
                     "lp": r["gold_logprob_raw"] if r["status"] == "OK" else None})
    return rows


def presence_effects(rows: list[dict]) -> dict[tuple[str, str, str], float]:
    """(family, wrapper, cue role) to the mean over the family's candidates of diagonal minus mean usable off-diagonal."""

    cells: dict[tuple[str, str, int, int], float | None] = {}
    foreign_flag: dict[tuple[str, str, int, int], bool] = {}
    role: dict[str, str] = {}
    for r in rows:
        if r["candidate_kind"] != "cue_candidate":
            continue
        key = (r["structure_id"], r["wrapper_id"], int(r["candidate_source_variant"]), int(r["prompt_variant"]))
        cells[key] = r["lp"]
        foreign_flag[key] = bool(r["candidate_numeral_in_prompt"])
        role[r["structure_id"]] = r["cue_semantic_role"]
    per_candidate: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (family, wrapper, u, v), lp in cells.items():
        if u != v or lp is None:
            continue
        off = [cells[(family, wrapper, u, w)] for (f2, w2, u2, w) in cells
               if (f2, w2, u2) == (family, wrapper, u) and w != u and cells[(f2, w2, u2, w)] is not None
               and not foreign_flag[(f2, w2, u2, w)]]
        if off:
            per_candidate[(family, wrapper)].append(lp - float(np.mean(off)))
    return {(f, w, role[f]): float(np.mean(v)) for (f, w), v in per_candidate.items()}


def d_lp_ranges(rows: list[dict]) -> dict[tuple[str, str, str], float]:
    gold: dict[tuple[str, str], list[float]] = defaultdict(list)
    role: dict[str, str] = {}
    for r in rows:
        if r["candidate_kind"] == "gold" and r["lp"] is not None:
            gold[(r["structure_id"], r["wrapper_id"])].append(r["lp"])
            role[r["structure_id"]] = r["cue_semantic_role"]
    return {(f, w, role[f]): float(max(v) - min(v)) for (f, w), v in gold.items() if len(v) >= 2}


def by_cluster(values: dict[tuple[str, str, str], float], cluster_of: dict[str, str], wrapper: str,
               roles: set[str] | None = None) -> dict[str, list[float]]:
    out: dict[str, list[float]] = defaultdict(list)
    for (family, w, role), value in values.items():
        if w == wrapper and (roles is None or role in roles):
            out[cluster_of[family]].append(value)
    return out


def summarise(by: dict[str, list[float]], rng: np.random.Generator) -> dict[str, Any]:
    values = {c: float(np.mean(v)) for c, v in sorted(by.items())}
    return {"n_families": sum(len(v) for v in by.values()), "by_cluster": values, **s148.cluster_bootstrap(list(values.values()), rng)}


def difference(candidate: dict[tuple[str, str, str], float], cluster_of: dict[str, str], wrapper: str, roles: set[str] | None,
               rng: np.random.Generator) -> dict[str, Any]:
    """Per cluster: mean over families of (effect under the wrapper minus effect under answer_line), for families with both."""

    by: dict[str, list[float]] = defaultdict(list)
    for (family, w, role), value in candidate.items():
        if w != wrapper or (roles is not None and role not in roles):
            continue
        ref = candidate.get((family, REFERENCE_WRAPPER, role))
        if ref is not None:
            by[cluster_of[family]].append(value - ref)
    return summarise(by, rng)


def classify(diff: dict[str, Any], reference_mean: float | None) -> dict[str, Any]:
    ci, mean = diff.get("ci95"), diff.get("mean")
    if ci is None or mean is None or reference_mean is None:
        return {"excludes_zero": None, "dominates": None, "status": "NOT_EVALUATED"}
    excludes = ci[0] > 0 or ci[1] < 0
    return {"excludes_zero": bool(excludes), "dominates": bool(excludes and abs(mean) >= DOMINANCE_FRACTION * abs(reference_mean)),
            "status": "evaluated"}


def analyse_model(rows: list[dict], cluster_of: dict[str, str], rng: np.random.Generator) -> dict[str, Any]:
    effects = presence_effects(rows)
    dlp = d_lp_ranges(rows)
    wrappers = sorted({w for (_, w, _) in effects} | {w for (_, w, _) in dlp})
    groups = {"all numeral-cue families": None, "nongoverning_distractor": {"nongoverning_distractor"},
              "irrelevant_variable": {"irrelevant_variable"}}
    out: dict[str, Any] = {"n_effects": len(effects), "wrappers": {}}
    verdicts = []
    ref_means: dict[str, float | None] = {}
    for gname, roles in groups.items():
        ref = summarise(by_cluster(effects, cluster_of, REFERENCE_WRAPPER, roles), rng)
        ref_means[gname] = ref["mean"]
    for wrapper in wrappers:
        entry: dict[str, Any] = {"presence_effect": {}, "interaction_vs_reference": {}, "D_lp_range": None, "D_lp_vs_reference": None}
        for gname, roles in groups.items():
            entry["presence_effect"][gname] = summarise(by_cluster(effects, cluster_of, wrapper, roles), rng)
            if wrapper != REFERENCE_WRAPPER:
                diff = difference(effects, cluster_of, wrapper, roles, rng)
                entry["interaction_vs_reference"][gname] = {**diff, **classify(diff, ref_means[gname])}
        entry["D_lp_range"] = summarise(by_cluster(dlp, cluster_of, wrapper), rng)
        if wrapper != REFERENCE_WRAPPER:
            entry["D_lp_vs_reference"] = difference(dlp, cluster_of, wrapper, None, rng)
            verdicts.append(entry["interaction_vs_reference"]["all numeral-cue families"])
        out["wrappers"][wrapper] = entry
    evaluated = [v for v in verdicts if v["status"] == "evaluated"]
    out["overall"] = {"wrappers_that_dominate": sorted(w for w, e in out["wrappers"].items()
                                                       if e["interaction_vs_reference"].get("all numeral-cue families", {}).get("dominates")),
                      "invariance": None if not evaluated else not any(v["excludes_zero"] for v in evaluated),
                      "note": "invariance means no interval excludes zero at this number of clusters; it is not equivalence"}
    return out


def fmt(x: Any, digits: int = 2) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def interval(c: dict[str, Any]) -> str:
    ci = c.get("ci95")
    return "NOT_EVALUATED" if ci is None else f"[{ci[0]:.2f}, {ci[1]:.2f}]"


def report(models: dict[str, Any]) -> str:
    lines = ["# Stage 14.16 legacy-family X03 analysis (descriptive, precision-limited)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Rule frozen in J14.16-003 before the run.",
             "Presence effect (nats) = candidate numeral's log-probability under its own rendering minus the same string under renderings where",
             "the numeral does not appear. Cluster bootstrap over template clusters (2,000 resamples, seed 42).", ""]
    for key, res in models.items():
        o = res["overall"]
        lines += [f"## {key}", "", f"Wrappers that dominate: {o['wrappers_that_dominate'] or 'none'}; invariance: {o['invariance']}. {o['note']}.", "",
                  "| Wrapper | group | clusters | presence effect [interval] | minus answer_line [interval] | dominates |", "|---|---|---|---|---|---|"]
        for w, e in res["wrappers"].items():
            for g, c in e["presence_effect"].items():
                inter = e["interaction_vs_reference"].get(g)
                diff = "reference" if inter is None else f"{fmt(inter['mean'])} {interval(inter)}"
                dominates = "-" if inter is None else inter["dominates"]
                lines.append(f"| {w} | {g} | {c['n_structures']} | {fmt(c['mean'])} {interval(c)} | {diff} | {dominates} |")
        lines += ["", "| Wrapper | D_lp range mean [interval] | minus answer_line [interval] |", "|---|---|---|"]
        for w, e in res["wrappers"].items():
            d, dd = e["D_lp_range"], e["D_lp_vs_reference"]
            diff = "reference" if dd is None else f"{fmt(dd['mean'])} {interval(dd)}"
            lines.append(f"| {w} | {fmt(d['mean'])} {interval(d)} | {diff} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of the run, one per model")
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
    jobs_all = [json.loads(line) for line in (Path(args.plan_dir) / "job_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    cluster_of = {j["structure_id"]: j["template_cluster_id"] for j in jobs_all}
    rng = np.random.default_rng(s148.SEED)
    models: dict[str, Any] = {}
    inputs = {"plan_job_manifest": hashlib.sha256((Path(args.plan_dir) / "job_manifest.jsonl").read_bytes()).hexdigest()}
    for path in args.records:
        records = s148.load_records(Path(path))
        inputs[path] = {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "n_records": len(records)}
        model_key = next(j["model_key"] for j in jobs_all if j["job_id"] == records[0]["job_id"])
        models[records[0]["model_id"]] = analyse_model(join(records, [j for j in jobs_all if j["model_key"] == model_key]), cluster_of, rng)
    summary = {"stage": "14.16", "kind": "legacy-family X03 analysis", "source_commit": sha,
               "git_status_short": s148.git("status", "--short").splitlines(), "command": " ".join(sys.argv), "inputs": inputs,
               "evidence_class": "exploratory; not paper-eligible", "reference_wrapper": REFERENCE_WRAPPER, "models": models}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(report(models), encoding="utf-8")
    rows = [{"model": m, "wrapper": w, "group": g, "n_clusters": c["n_structures"], "mean": c["mean"],
             "ci95_low": None if c["ci95"] is None else c["ci95"][0], "ci95_high": None if c["ci95"] is None else c["ci95"][1]}
            for m, r in models.items() for w, e in r["wrappers"].items() for g, c in e["presence_effect"].items()]
    with (out_dir / "presence_effects_by_wrapper.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model", "wrapper", "group", "n_clusters", "mean", "ci95_low", "ci95_high"])
        writer.writeheader()
        writer.writerows(rows)
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
