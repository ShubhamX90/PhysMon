#!/usr/bin/env python3
"""Stage 14.20: analysis of a thinking-model run on the gold dataset (CPU only; numpy).

Reads the raw records of `s164_thinking_run.py` (source `base`, the no-cue problems) and the dataset (for domain and level) and reports,
descriptively and with the frozen rules below:

1. Throughput: generated tokens, wall time, aggregate tokens per second (the per-record wall time is the batch time divided by the batch
   size, so the sum is the total generation time), and the distribution of generated tokens (median, 90th percentile, maximum).
2. Outcomes: parse statuses, the share of thinking that closed, the share that hit the token limit (TRUNCATED), and correctness by the
   declared rule (protocol section 4b) among graded records. TRUNCATED, UNPARSEABLE, MULTIPLE_CANDIDATES and EMPTY are NOT_EVALUATED, never wrong.
3. Per-problem consistency: for each problem (structure and instance) the number of samples, graded and correct. A problem is a CONSISTENT
   ANCHOR if it has at least `--min-samples` samples, every sample is graded, and every graded sample is correct. Problems with a
   mix are UNSTABLE; problems with no correct sample are FAILED; problems with an ungraded sample and no wrong one are INCOMPLETE.
4. Correctness by level and domain (author-judged levels), with a cluster bootstrap over structures (2,000 resamples, seed 42), because
   the structure, not the instantiation, is the independent unit.
5. The anchors file: a JSON list of "structure:instance" keys of the consistent anchors, for `s164_thinking_run.py --ids-file`, and the number
   of distinct structures they come from (the gate for a distractor run is at least 20 anchor structures; below that the distractor
   endpoint is NOT_EVALUATED).

Nothing is promoted to a result: the run is exploratory; data role EXPLORATION; not paper-eligible. Plan reference: B2.4 eligibility strata,
protocol sections 3 and 4b; journals J14.13 and J14.19.
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
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT_ROOT = "results/stage14/s165_thinking_analysis"
DATASET = "data/v2/dataset/v1/dataset.jsonl"
SEED = 42
N_BOOT = 2000
GATE_ANCHOR_STRUCTURES = 20
GRADED = ("correct", "wrong")


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def quantile(values: list[float], q: float) -> float | None:
    return float(np.quantile(values, q)) if values else None


def throughput(records: list[dict]) -> dict[str, Any]:
    tokens = [r["n_generated_tokens"] for r in records]
    wall = sum(r["wall_time"] for r in records)
    return {"n_records": len(records), "generated_tokens_total": int(sum(tokens)), "generation_wall_time_s": round(wall, 2),
            "aggregate_tokens_per_s": None if wall <= 0 else round(sum(tokens) / wall, 2),
            "tokens_median": quantile(tokens, 0.5), "tokens_p90": quantile(tokens, 0.9), "tokens_max": max(tokens) if tokens else None,
            "batch_size": sorted({r["batch_size"] for r in records}), "max_sampling": sorted({json.dumps(r["sampling"], sort_keys=True) for r in records})}


def outcomes(records: list[dict]) -> dict[str, Any]:
    n = len(records)
    graded = [r for r in records if r["correctness"] in GRADED]
    correct = sum(r["correctness"] == "correct" for r in graded)
    return {"n_records": n, "parse_status": dict(Counter(r["parse_status"] for r in records)),
            "correctness": dict(Counter(r["correctness"] for r in records)),
            "thinking_closed_share": None if not n else sum(bool(r["thinking_closed"]) for r in records) / n,
            "truncated_share": None if not n else sum(r["parse_status"] == "TRUNCATED" for r in records) / n,
            "n_graded": len(graded), "n_correct": correct,
            "correct_share_of_graded": None if not graded else correct / len(graded),
            "correct_share_of_all": None if not n else correct / n}


def classify_problem(rows: list[dict], min_samples: int) -> str:
    graded = [r for r in rows if r["correctness"] in GRADED]
    correct = sum(r["correctness"] == "correct" for r in graded)
    wrong = len(graded) - correct
    if len(rows) >= min_samples and len(graded) == len(rows) and wrong == 0:
        return "CONSISTENT_ANCHOR"
    if correct == 0 and wrong > 0:
        return "FAILED"
    if correct > 0 and wrong > 0:
        return "UNSTABLE"
    return "INCOMPLETE"  # ungraded samples remain and nothing is wrong, or too few samples, or no graded record at all


def per_problem(records: list[dict], min_samples: int) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        groups[f"{r['structure_id']}:{r['instance']}"].append(r)
    out = {}
    for key, rows in sorted(groups.items()):
        graded = [r for r in rows if r["correctness"] in GRADED]
        out[key] = {"structure_id": rows[0]["structure_id"], "n_samples": len(rows), "n_graded": len(graded),
                    "n_correct": sum(r["correctness"] == "correct" for r in graded), "class": classify_problem(rows, min_samples),
                    "mean_tokens": float(np.mean([r["n_generated_tokens"] for r in rows]))}
    return out


def structure_means(problems: dict[str, dict], value) -> dict[str, float]:
    by: dict[str, list[float]] = defaultdict(list)
    for p in problems.values():
        v = value(p)
        if v is not None:
            by[p["structure_id"]].append(v)
    return {s: float(np.mean(v)) for s, v in by.items()}


def bootstrap(values: dict[str, float], rng: np.random.Generator) -> dict[str, Any]:
    arr = np.array(list(values.values()))
    if len(arr) < 2:
        return {"n_structures": len(arr), "mean": None if not len(arr) else float(arr.mean()), "ci95": None, "status": "NOT_EVALUATED"}
    means = [float(rng.choice(arr, size=len(arr), replace=True).mean()) for _ in range(N_BOOT)]
    return {"n_structures": len(arr), "mean": float(arr.mean()), "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]}


def correct_rate(problem: dict) -> float | None:
    return None if problem["n_graded"] == 0 else problem["n_correct"] / problem["n_graded"]


def analyse(records: list[dict], dataset: list[dict], min_samples: int, rng: np.random.Generator) -> dict[str, Any]:
    meta = {f"{d['structure_id']}:{d['instance']}": d for d in dataset}
    problems = per_problem(records, min_samples)
    classes = Counter(p["class"] for p in problems.values())
    anchors = [k for k, p in problems.items() if p["class"] == "CONSISTENT_ANCHOR"]
    anchor_structures = sorted({problems[k]["structure_id"] for k in anchors})
    by_level: dict[str, dict] = {}
    by_domain: dict[str, dict] = {}
    for label, getter, sink in (("level", lambda k: meta[k]["level"], by_level), ("domain", lambda k: meta[k]["domain"], by_domain)):
        groups: dict[str, dict[str, dict]] = defaultdict(dict)
        for k, p in problems.items():
            groups[getter(k) if k in meta else "unknown"][k] = p
        for name, sub in sorted(groups.items()):
            sink[name] = {"n_problems": len(sub), "classes": dict(Counter(p["class"] for p in sub.values())),
                          "correct_rate_by_structure": bootstrap(structure_means(sub, correct_rate), rng)}
        del label
    return {"throughput": throughput(records), "outcomes": outcomes(records), "problems": {"n": len(problems), "classes": dict(classes)},
            "overall_correct_rate_by_structure": bootstrap(structure_means(problems, correct_rate), rng),
            "by_level": by_level, "by_domain": by_domain,
            "anchors": {"n": len(anchors), "n_structures": len(anchor_structures), "keys": anchors,
                        "gate_min_structures": GATE_ANCHOR_STRUCTURES,
                        "distractor_endpoint": ("estimable" if len(anchor_structures) >= GATE_ANCHOR_STRUCTURES else
                                                f"NOT_EVALUATED: {len(anchor_structures)} anchor structures, at least {GATE_ANCHOR_STRUCTURES} needed")},
            "problems_detail": problems}


def fmt(x: Any, digits: int = 3) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(model: str, res: dict[str, Any]) -> str:
    t, o, a = res["throughput"], res["outcomes"], res["anchors"]
    lines = [f"# Stage 14.20 thinking-model run: {model} (descriptive)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. TRUNCATED and other ungraded outcomes are",
             "NOT_EVALUATED, never wrong. The structure is the independent unit; intervals are cluster bootstrap over structures (2,000, seed 42).", "",
             f"Records {t['n_records']}; generated tokens {t['generated_tokens_total']}; generation time {t['generation_wall_time_s']} s; "
             f"aggregate {fmt(t['aggregate_tokens_per_s'], 1)} tokens/s; tokens per record median {fmt(t['tokens_median'], 0)}, 90th percentile "
             f"{fmt(t['tokens_p90'], 0)}, maximum {t['tokens_max']}; batch size {t['batch_size']}.", "",
             f"Parse statuses {o['parse_status']}; correctness {o['correctness']}; thinking closed {fmt(o['thinking_closed_share'])}; "
             f"truncated {fmt(o['truncated_share'])}; correct share of graded {fmt(o['correct_share_of_graded'])} "
             f"({o['n_correct']} of {o['n_graded']}); of all records {fmt(o['correct_share_of_all'])}.", "",
             f"Problems {res['problems']['n']}: {res['problems']['classes']}. Overall correct rate by structure "
             f"{fmt(res['overall_correct_rate_by_structure']['mean'])} {res['overall_correct_rate_by_structure'].get('ci95')}.", "",
             f"Consistent anchors: {a['n']} problems from {a['n_structures']} structures; distractor endpoint: {a['distractor_endpoint']}.", ""]
    for title, block in (("Level (author-judged)", res["by_level"]), ("Domain", res["by_domain"])):
        lines += [f"## {title}", "", "| group | problems | classes | correct rate by structure | 95% interval |", "|---|---|---|---|---|"]
        for name, g in block.items():
            c = g["correct_rate_by_structure"]
            ci = c.get("ci95")
            lines.append(f"| {name} | {g['n_problems']} | {g['classes']} | {fmt(c['mean'])} | {'NOT_EVALUATED' if ci is None else f'[{ci[0]:.3f}, {ci[1]:.3f}]'} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of the base run(s), one per model")
    parser.add_argument("--dataset", default=DATASET)
    parser.add_argument("--min-samples", type=int, default=4, help="samples per problem needed for a CONSISTENT_ANCHOR")
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    args = parser.parse_args()
    import subprocess

    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=False).stdout.strip()
    attempt = args.attempt_id or f"attempt_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2
    dataset = load_records(REPO_ROOT / args.dataset)
    rng = np.random.default_rng(SEED)
    models: dict[str, Any] = {}
    inputs: dict[str, Any] = {args.dataset: hashlib.sha256((REPO_ROOT / args.dataset).read_bytes()).hexdigest()}
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in args.records:
        records = load_records(Path(path))
        inputs[path] = {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "n_records": len(records)}
        if not records:
            continue
        name = records[0]["model_id"]
        models[name] = analyse(records, dataset, args.min_samples, rng)
        slug = name.replace("/", "_")
        (out_dir / f"{slug}_anchors.json").write_text(json.dumps(models[name]["anchors"]["keys"], indent=1) + "\n", encoding="utf-8")
        (out_dir / f"{slug}_report.md").write_text(report(name, models[name]), encoding="utf-8")
    summary = {"stage": "14.20", "kind": "thinking-model run analysis", "source_commit": sha, "command": " ".join(sys.argv), "inputs": inputs,
               "min_samples": args.min_samples, "evidence_class": "exploratory; not paper-eligible", "models": models}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
