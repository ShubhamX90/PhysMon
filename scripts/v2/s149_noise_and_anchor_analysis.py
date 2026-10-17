#!/usr/bin/env python3
"""Stage 14.9: dtype noise floor and anchor-matched answer competition from the Stage 14.9 job (CPU only; numpy).

Reads the raw record files of the same plan run in several dtypes (and, optionally, an earlier run of the same plan) and reports:

1. Presentation noise (P1.7): for each record, the difference of the gold log-probability between bfloat16 and float32; its
   distribution (n, mean, SD, MAD, median and 95th percentile of the absolute difference, maximum); the same for every
   contrast of the Stage 14.8 analysis (so a contrast can be read against the noise of that contrast); and whether the
   greedy generation and the correctness label agree across dtypes.
2. Run-to-run reproducibility: the same bfloat16 plan run twice (Stage 14.7 job 399969 against this job), which should
   reproduce the log-probabilities to within hardware noise.
3. Anchor-matched answer competition (v2 §4): for each decoy cell, the shift of the gold log-probability and of the decoy
   log-probability from the no-cue prompt, and their difference (the shift of R_alt, gold minus decoy), by structure with a
   cluster bootstrap over structures. This replaces the unmatched R_alt contrasts of Stage 14.8, which compared different strings.

Descriptive and precision-limited, as in Stage 14.8; no p-values. Anything that cannot be computed is NOT_EVALUATED.

Plan reference: v2 §4, P1.5 to P1.7 (p.17), §8.4 (p.42), protocol sections 3 and 4.
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

OUT_ROOT = "results/stage14/s149_noise_and_anchor"
PRIMARY_DTYPE = "bfloat16"
REFERENCE_DTYPE = "float32"


def _load_s148():
    spec = importlib.util.spec_from_file_location("s148_pilot_analysis", REPO_ROOT / "scripts/v2/s148_pilot_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s148 = _load_s148()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_run(records_path: Path) -> dict[str, Any]:
    summary = json.loads((records_path.parent / "run_summary.json").read_text(encoding="utf-8"))
    return {"path": str(records_path), "model_key": summary["model_key"], "dtype": summary["dtype"],
            "records": s148.load_records(records_path), "sha256": sha256_file(records_path)}


def by_job(records: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for record in records:
        if record["job_id"] in out:
            raise ValueError(f"duplicate job_id {record['job_id']}")
        out[record["job_id"]] = record
    return out


def abs_stats(deltas: list[float]) -> dict[str, Any]:
    if not deltas:
        return {"n": 0, "status": "NOT_EVALUATED: no paired records"}
    arr = np.asarray(deltas, dtype=float)
    a = np.abs(arr)
    return {"n": int(arr.size), "mean": float(arr.mean()), "sd": float(arr.std(ddof=1)) if arr.size > 1 else None,
            "mad": s148.mad(list(arr)), "median_abs": float(np.median(a)), "p95_abs": float(np.percentile(a, 95)),
            "max_abs": float(a.max())}


def paired_gold_deltas(first: list[dict], second: list[dict]) -> tuple[list[dict], dict[str, Any]]:
    """Per matched record: gold log-probability under `first` minus under `second` (same job_id)."""

    a, b = by_job(first), by_job(second)
    rows, gen_same, label_same, n_gen = [], 0, 0, 0
    for job_id in sorted(set(a) & set(b)):
        ra, rb = a[job_id], b[job_id]
        la, lb = s148.gold_lp(ra), s148.gold_lp(rb)
        rows.append({"job_id": job_id, "structure_id": ra["structure_id"], "instance": ra["instance"],
                     "cell_id": ra["cell_id"], "lp_first": la, "lp_second": lb,
                     "delta": None if la is None or lb is None else la - lb})
        if ra["parse_status"] == rb["parse_status"] == "PARSED":
            n_gen += 1
            gen_same += ra["parsed_answer"] == rb["parsed_answer"]
        label_same += ra["correctness"] == rb["correctness"]
    deltas = [r["delta"] for r in rows if r["delta"] is not None]
    agreement = {"n_both_parsed": n_gen, "same_parsed_answer": gen_same, "n_matched": len(rows),
                 "same_correctness_label": label_same, "unmatched_first": len(set(a) - set(b)),
                 "unmatched_second": len(set(b) - set(a))}
    return rows, {"gold_logprob_difference": abs_stats(deltas), "generation_agreement": agreement}


def contrast_noise(first: list[dict], second: list[dict], model_id: str) -> dict[str, Any]:
    """Noise of each Stage 14.8 contrast: its value under `first` minus under `second`, by instantiation."""

    def per_item(records: list[dict]) -> dict[tuple[str, int], dict[str, float | None]]:
        index = s148.index_records(records)
        keys = sorted({(k[1], k[2]) for k in index if k[0] == model_id})
        return {(s, i): s148.item_contrasts({k[3]: v for k, v in index.items() if k[:3] == (model_id, s, i)})
                for s, i in keys}

    pa, pb = per_item(first), per_item(second)
    out: dict[str, Any] = {}
    names = list(next(iter(pa.values())).keys()) if pa else []
    for name in names:
        deltas = [pa[k][name] - pb[k][name] for k in pa
                  if k in pb and pa[k].get(name) is not None and pb[k].get(name) is not None]
        out[name] = abs_stats(deltas)
    return out


def anchor_shifts(records: list[dict]) -> dict[tuple[str, int, str], dict[str, float]]:
    """Per (structure, instance, decoy cell): shift of gold, of decoy and of R_alt from the no-cue prompt."""

    index = s148.index_records(records)
    model_ids = {k[0] for k in index}
    if len(model_ids) != 1:
        raise ValueError("anchor_shifts expects the records of one model")
    model = next(iter(model_ids))
    out: dict[tuple[str, int, str], dict[str, float]] = {}
    for (m, structure, instance, cell), rec in index.items():
        if cell not in s148.DECOY_CELLS or not rec.get("alternative_scores"):
            continue
        anchor = index.get((model, structure, instance, s148.ANCHOR))
        anchor_decoy = (rec["alternative_scores"].get("decoy_under_anchor_prompt") or {})
        g_cue, g_anchor = s148.gold_lp(rec), s148.gold_lp(anchor) if anchor else None
        d_cue = s148.decoy_lp(rec)
        d_anchor = anchor_decoy.get("logprob_raw") if anchor_decoy.get("status") == "OK" else None
        if None in (g_cue, g_anchor, d_cue, d_anchor):
            continue
        out[(structure, instance, cell)] = {"gold_shift": g_cue - g_anchor, "decoy_shift": d_cue - d_anchor,
                                            "r_alt_shift": (g_cue - d_cue) - (g_anchor - d_anchor)}
    return out


def anchor_summary(shifts: dict[tuple[str, int, str], dict[str, float]], rng: np.random.Generator) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cell in s148.DECOY_CELLS:
        for measure in ("gold_shift", "decoy_shift", "r_alt_shift"):
            by_structure: dict[str, list[float]] = defaultdict(list)
            for (s, _, c), v in shifts.items():
                if c == cell:
                    by_structure[s].append(v[measure])
            values = {s: float(np.mean(v)) for s, v in sorted(by_structure.items())}
            out[f"{measure}[{cell}]"] = {"by_structure": values, **s148.cluster_bootstrap(list(values.values()), rng)}
    for first, second in ((s148.NEAR, s148.FAR), (s148.NEAR, s148.INCOMPAT), (s148.NEAR, s148.MOD)):
        by_structure = defaultdict(list)
        for (s, i, c), v in shifts.items():
            other = shifts.get((s, i, second))
            if c == first and other is not None:
                by_structure[s].append(v["r_alt_shift"] - other["r_alt_shift"])
        values = {s: float(np.mean(v)) for s, v in sorted(by_structure.items())}
        out[f"r_alt_shift[{first}] - r_alt_shift[{second}]"] = {
            "by_structure": values, **s148.cluster_bootstrap(list(values.values()), rng)}
    return out


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c) for c in columns})


def fmt(x: Any, digits: int = 3) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(summary: dict[str, Any]) -> str:
    lines = ["# Stage 14.9 dtype noise and anchor-matched answer competition (descriptive)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Log-probabilities are raw sums in nats.", ""]
    for model, res in summary["models"].items():
        lines += [f"## {model}", ""]
        n = res["dtype_noise"]["gold_logprob_difference"]
        lines += [f"**dtype noise, bfloat16 minus float32, gold log-probability per record:** n {n['n']}; mean {fmt(n.get('mean'))}; SD {fmt(n.get('sd'))}; "
                  f"MAD {fmt(n.get('mad'))}; median |difference| {fmt(n.get('median_abs'))}; 95th percentile {fmt(n.get('p95_abs'))}; max {fmt(n.get('max_abs'))}.", ""]
        g = res["dtype_noise"]["generation_agreement"]
        lines += [f"Generations: the parsed answer is identical across dtypes in {g['same_parsed_answer']} of {g['n_both_parsed']} records parsed in both; "
                  f"the correctness label agrees in {g['same_correctness_label']} of {g['n_matched']}.", ""]
        if res.get("reproducibility"):
            r = res["reproducibility"]["gold_logprob_difference"]
            lines += [f"**run-to-run, bfloat16 (this job against job 399969):** n {r['n']}; max |difference| {fmt(r.get('max_abs'))}; median {fmt(r.get('median_abs'))}.", ""]
        lines += ["| Stage 14.8 contrast | n | SD of the dtype difference | 95th percentile of its absolute value |", "|---|---|---|---|"]
        for name, c in res["contrast_noise"].items():
            lines.append(f"| {name} | {c['n']} | {fmt(c.get('sd'))} | {fmt(c.get('p95_abs'))} |")
        lines += ["", "| Anchor-matched shift from the no-cue prompt (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |", "|---|---|---|---|---|"]
        for name, c in res["anchor_matched"].items():
            ci = c["ci95"]
            lines.append(f"| {name} | {c['n_structures']} | {fmt(c['mean'], 2)} | "
                         f"{'NOT_EVALUATED' if ci is None else f'[{ci[0]:.2f}, {ci[1]:.2f}]'} | {c.get('n_positive', '-')} / {c.get('n_negative', '-')} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl of this job, one per model and dtype")
    parser.add_argument("--earlier-bf16", nargs="*", default=[], help="raw_records.jsonl of an earlier bfloat16 run of the same plan")
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

    runs = [load_run(Path(p)) for p in args.records]
    earlier = [load_run(Path(p)) for p in args.earlier_bf16]
    rng = np.random.default_rng(s148.SEED)
    models: dict[str, Any] = {}
    noise_rows: list[dict] = []
    shift_rows: list[dict] = []
    for model_key in sorted({r["model_key"] for r in runs}):
        primary = next((r for r in runs if r["model_key"] == model_key and r["dtype"] == PRIMARY_DTYPE), None)
        reference = next((r for r in runs if r["model_key"] == model_key and r["dtype"] == REFERENCE_DTYPE), None)
        if primary is None:
            continue
        model_id = primary["records"][0]["model_id"]
        entry: dict[str, Any] = {"model_id": model_id}
        if reference is not None:
            rows, stats = paired_gold_deltas(primary["records"], reference["records"])
            entry["dtype_noise"] = stats
            entry["contrast_noise"] = contrast_noise(primary["records"], reference["records"], model_id)
            noise_rows += [{"model": model_key, **r} for r in rows]
        else:
            entry["dtype_noise"] = {"gold_logprob_difference": {"n": 0, "status": "NOT_EVALUATED: no float32 run"},
                                    "generation_agreement": {"n_both_parsed": 0, "same_parsed_answer": 0, "n_matched": 0,
                                                             "same_correctness_label": 0}}
            entry["contrast_noise"] = {}
        prior = next((r for r in earlier if r["model_key"] == model_key), None)
        entry["reproducibility"] = paired_gold_deltas(primary["records"], prior["records"])[1] if prior else None
        shifts = anchor_shifts(primary["records"])
        entry["anchor_matched"] = anchor_summary(shifts, rng)
        shift_rows += [{"model": model_key, "structure_id": s, "instance": i, "cell_id": c, **v}
                       for (s, i, c), v in sorted(shifts.items())]
        models[model_key] = entry

    summary = {"stage": "14.9", "kind": "dtype noise and anchor-matched answer competition", "source_commit": sha,
               "git_status_short": s148.git("status", "--short").splitlines(), "command": " ".join(sys.argv),
               "inputs": {r["path"]: {"model_key": r["model_key"], "dtype": r["dtype"], "sha256": r["sha256"],
                                      "n_records": len(r["records"])} for r in runs + earlier},
               "primary_dtype": PRIMARY_DTYPE, "reference_dtype": REFERENCE_DTYPE, "evidence_class": "exploratory; not paper-eligible",
               "models": models}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "dtype_noise_by_record.csv", noise_rows,
              ["model", "job_id", "structure_id", "instance", "cell_id", "lp_first", "lp_second", "delta"])
    write_csv(out_dir / "anchor_shifts_by_item.csv", shift_rows,
              ["model", "structure_id", "instance", "cell_id", "gold_shift", "decoy_shift", "r_alt_shift"])
    (out_dir / "report.md").write_text(report(summary), encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": sorted(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
