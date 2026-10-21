#!/usr/bin/env python3
"""Stage 14.14: analysis of the numeral-presence control (CPU only; numpy).

Joins the raw records of the numeral-presence run to its plan (by job id) and computes, for every numeral that appears in a
prompt, the presence effect: the log-probability of the numeral as an answer (target unit, answer-line wrapper) minus that of its
matched absent control (same shape, not in the prompt, not near the gold) under the same prompt. Per prompt and role the effects
are averaged, then by structure, with a cluster bootstrap over structures (2,000 resamples, seed 42).

Roles: `relevant_input` (a number the problem needs), `cue_nongoverning_isolated` (split by unit type: same as the requested
quantity, or incompatible), `cue_irrelevant_metadata`, `cue_relevant_reference` (role-reversal cell). The key contrasts are paired
within a prompt: the cue numeral's presence effect minus the mean presence effect of the relevant inputs of the same prompt, and the
same-unit cue minus the incompatible-unit cue.

A numeral whose record is not OK, or whose control does not exist, is NOT_EVALUATED and left out; it is never counted as zero.
Descriptive and precision-limited; no p-values. Presence effects are differences of raw sums over strings of equal shape.

Plan reference: protocol section 5 row 4; P4; journals J14.12-002 and J14.14.
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

OUT_ROOT = "results/stage14/s155_numeral_presence_analysis"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s148 = _load("s148_pilot_analysis", "scripts/v2/s148_pilot_analysis.py")


def join(records: list[dict], jobs: list[dict]) -> list[dict]:
    """Records joined to their planned candidate; an unmatched record or an extra copy is an error, not a silent drop.

    A control string can legitimately be drawn for two numerals of one prompt (for example a one-digit numeral); the plan then holds
    two jobs with one id, and the run holds two records with that id. They are paired in order, each with its own `matched_to`.
    """

    by_id: dict[str, list[dict]] = defaultdict(list)
    for j in jobs:
        by_id[j["job_id"]].append(j)
    used: dict[str, int] = defaultdict(int)
    rows = []
    for r in records:
        planned = by_id.get(r["job_id"])
        if not planned:
            raise ValueError(f"record {r['job_id']} is not in the plan")
        if used[r["job_id"]] >= len(planned):
            raise ValueError(f"duplicate record {r['job_id']}")
        job = planned[used[r["job_id"]]]
        used[r["job_id"]] += 1
        rows.append({"job_id": r["job_id"], "structure": job["structure_id"], "instance": int(job["instance"]),
                     "cell": job["cell_id"], "kind": job["candidate_kind"], "text": job["candidate_text"],
                     "matched_to": job["candidate_matched_to"], "role": job["candidate_role"],
                     "unit_type": job.get("unit_type"), "lp": r["gold_logprob_raw"] if r["status"] == "OK" else None})
    return rows


def presence_effects(rows: list[dict]) -> list[dict]:
    """One presence effect per present numeral: lp(present) minus lp(matched control) under the same prompt."""

    controls = {(r["structure"], r["instance"], r["cell"], r["matched_to"]): r["lp"] for r in rows if r["kind"] == "absent_control"}
    out = []
    for r in rows:
        if r["kind"] != "present":
            continue
        control = controls.get((r["structure"], r["instance"], r["cell"], r["text"]))
        effect = None if r["lp"] is None or control is None else r["lp"] - control
        out.append({**r, "effect": effect})
    return out


def role_key(effect_row: dict) -> str:
    role = effect_row["role"]
    if role == "cue_nongoverning_isolated":
        return f"{role}[{effect_row['unit_type']}]"
    return role


def by_prompt(effects: list[dict]) -> dict[tuple[str, int, str], dict[str, float]]:
    """Mean presence effect of each role in each prompt."""

    grouped: dict[tuple[str, int, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for e in effects:
        if e["effect"] is not None:
            grouped[(e["structure"], e["instance"], e["cell"])][role_key(e)].append(e["effect"])
    return {k: {role: float(np.mean(v)) for role, v in roles.items()} for k, roles in grouped.items()}


def summarise(values_by_structure: dict[str, list[float]], rng: np.random.Generator) -> dict[str, Any]:
    values = {s: float(np.mean(v)) for s, v in sorted(values_by_structure.items())}
    return {"by_structure": values, **s148.cluster_bootstrap(list(values.values()), rng)}


def analyse(rows: list[dict], rng: np.random.Generator) -> dict[str, Any]:
    return analyse_effects(presence_effects(rows), rng)


def analyse_effects(effects: list[dict], rng: np.random.Generator) -> dict[str, Any]:
    """Role summaries and paired contrasts from per-numeral effects (`structure`, `instance`, `cell`, `role`, `unit_type`, `effect`)."""

    prompts = by_prompt(effects)
    n_not_evaluated = sum(e["effect"] is None for e in effects)
    role_means: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (structure, _, cell), roles in prompts.items():
        for role, value in roles.items():
            role_means[role][structure].append(value)
            if role == "relevant_input" and cell == s148.ANCHOR:
                role_means["relevant_input[no_cue prompt only]"][structure].append(value)
    paired: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (structure, _, cell), roles in prompts.items():
        relevant = roles.get("relevant_input")
        for role, value in roles.items():
            if role.startswith("cue_") and relevant is not None:
                paired[f"{role} minus relevant_input (same prompt)"][structure].append(value - relevant)
    same = {k: v for k, v in prompts.items() if k[2] == s148.NEAR}
    for (structure, instance, _), roles in same.items():
        other = prompts.get((structure, instance, s148.INCOMPAT))
        a, b = roles.get("cue_nongoverning_isolated[same]"), (other or {}).get("cue_nongoverning_isolated[incompatible]")
        if a is not None and b is not None:
            paired["same-unit near cue minus incompatible-unit near cue"][structure].append(a - b)
    return {"n_numerals": len(effects), "n_not_evaluated": int(n_not_evaluated),
            "role_presence_effect": {r: summarise(v, rng) for r, v in sorted(role_means.items())},
            "paired_contrasts": {k: summarise(v, rng) for k, v in sorted(paired.items())}}


def fmt(x: Any, digits: int = 2) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(models: dict[str, Any]) -> str:
    lines = ["# Stage 14.14 numeral-presence control (descriptive, precision-limited)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Presence effect = log-probability (nats) of a",
             "numeral that appears in the prompt, as an answer with the target unit, minus that of a matched absent numeral under the same prompt.",
             "Ten structures; intervals are cluster bootstrap (2,000 resamples, seed 42).", ""]
    for key, res in models.items():
        lines += [f"## {key}", "", f"Numerals {res['n_numerals']}; NOT_EVALUATED {res['n_not_evaluated']}.", "",
                  "| Role | structures | mean presence effect | 95% interval | up / down |", "|---|---|---|---|---|"]
        for section in ("role_presence_effect", "paired_contrasts"):
            if section == "paired_contrasts":
                lines += ["| *paired within a prompt* | | | | |"]
            for name, c in res[section].items():
                ci = c["ci95"]
                lines.append(f"| {name} | {c['n_structures']} | {fmt(c['mean'])} | "
                             f"{'NOT_EVALUATED' if ci is None else f'[{ci[0]:.2f}, {ci[1]:.2f}]'} | {c.get('n_positive', '-')} / {c.get('n_negative', '-')} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of the presence run, one per model")
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
    rng = np.random.default_rng(s148.SEED)
    models: dict[str, Any] = {}
    inputs = {"plan_job_manifest": hashlib.sha256((Path(args.plan_dir) / "job_manifest.jsonl").read_bytes()).hexdigest()}
    for path in args.records:
        records = s148.load_records(Path(path))
        inputs[path] = {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "n_records": len(records)}
        model_key = next(j["model_key"] for j in jobs_all if j["job_id"] == records[0]["job_id"])
        jobs = [j for j in jobs_all if j["model_key"] == model_key]
        models[records[0]["model_id"]] = analyse(join(records, jobs), rng)
    summary = {"stage": "14.14", "kind": "numeral-presence control analysis", "source_commit": sha,
               "git_status_short": s148.git("status", "--short").splitlines(), "command": " ".join(sys.argv), "inputs": inputs,
               "evidence_class": "exploratory; not paper-eligible", "models": models}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(report(models), encoding="utf-8")
    rows = [{"model": m, "section": s, "name": n, "n_structures": c["n_structures"], "mean": c["mean"],
             "ci95_low": None if c["ci95"] is None else c["ci95"][0], "ci95_high": None if c["ci95"] is None else c["ci95"][1]}
            for m, r in models.items() for s in ("role_presence_effect", "paired_contrasts") for n, c in r[s].items()]
    with (out_dir / "presence_effects.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model", "section", "name", "n_structures", "mean", "ci95_low", "ci95_high"])
        writer.writeheader()
        writer.writerows(rows)
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
