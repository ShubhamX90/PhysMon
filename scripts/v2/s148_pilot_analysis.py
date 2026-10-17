#!/usr/bin/env python3
"""Stage 14.8: descriptive analysis of the Stage 14.7 pilot records (CPU only; numpy).

Implements section 3 to 5 of `docs/stage14/pilot_protocol.md` on the raw records of the two-model pilot. It computes
only what the protocol names: per-cell means, signed contrasts of the gold log-probability against the no-cue anchor
of the same instantiation, D_lp (range, SD and MAD of the gold log-probability across cells that share the gold string),
R_alt (gold minus decoy log-probability) where a decoy exists, the assay-response check for the relevant edit, copy
rates of the decoy numeral, eligibility strata with denominators, and a structure-level summary with a cluster bootstrap
over structures (2,000 resamples, seed 42). No p-values are computed for interactions. The independent unit is the
structure (v2 §8.1); with ten structures every interval is wide and is reported as precision-limited, never as a null.

Endpoints that cannot be computed are written as NOT_EVALUATED with a reason (v2 §8.4), never as zero: the
correctness-transition endpoint when the anchors are almost never correct, the presentation-noise floor (no repeat or
dtype pass exists), and the model-positive stratum (no sensitivity label exists for v2 structures).

Plan reference: protocol sections 3 to 5; v2 §8.1 to §8.4 (p.41-42), B2.2 to B2.5 (p.7-8), P1.5 to P1.7 (p.17).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT_ROOT = "results/stage14/s148_pilot_analysis"
N_BOOT = 2000
SEED = 42
ANCHOR = "no_cue"
CUE_CELLS = ("nonnumeric_extra", "numeric_metadata", "nongov_same_unit_near_high_overlap",
             "nongov_same_unit_near_low_overlap", "nongov_same_unit_moderate", "nongov_same_unit_far",
             "nongov_incompatible_unit_near", "nongov_same_magnitude_convertible_unit")
SHARED_GOLD_CELLS = (ANCHOR, *CUE_CELLS)  # the gold string is identical across these within an instantiation
NEAR, FAR, MOD, INCOMPAT, CONVERT = ("nongov_same_unit_near_high_overlap", "nongov_same_unit_far",
                                     "nongov_same_unit_moderate", "nongov_incompatible_unit_near",
                                     "nongov_same_magnitude_convertible_unit")
DECOY_CELLS = ("nongov_same_unit_near_high_overlap", "nongov_same_unit_near_low_overlap", "nongov_same_unit_moderate",
               "nongov_same_unit_far", "nongov_incompatible_unit_near")


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                              check=False).stdout.strip()
    except OSError:
        return ""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def decoy_lp(record: dict) -> float | None:
    alt = record.get("alternative_scores") or {}
    decoy = alt.get("decoy") if isinstance(alt, dict) else None
    if not decoy or decoy.get("status") != "OK":
        return None
    return decoy.get("logprob_raw")


def gold_lp(record: dict) -> float | None:
    return record["gold_logprob_raw"] if record.get("status") == "OK" else None


def r_alt(record: dict) -> float | None:
    g, d = gold_lp(record), decoy_lp(record)
    return None if g is None or d is None else g - d


def mad(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    return float(np.median(np.abs(arr - np.median(arr))))


def index_records(records: list[dict]) -> dict[tuple[str, str, int, str], dict]:
    index: dict[tuple[str, str, int, str], dict] = {}
    for record in records:
        key = (record["model_id"], record["structure_id"], int(record["instance"]), record["cell_id"])
        if key in index:
            raise ValueError(f"duplicate record for {key}")
        index[key] = record
    return index


def item_contrasts(cells: dict[str, dict]) -> dict[str, float | None]:
    """All named contrasts for one instantiation (cells: cell_id to record). None means NOT_EVALUATED."""

    def lp(cell: str) -> float | None:
        return gold_lp(cells[cell]) if cell in cells else None

    def ra(cell: str) -> float | None:
        return r_alt(cells[cell]) if cell in cells else None

    def diff(a: float | None, b: float | None) -> float | None:
        return None if a is None or b is None else a - b

    out: dict[str, float | None] = {}
    for cell in CUE_CELLS:
        out[f"gold_lp[{cell}] - gold_lp[{ANCHOR}]"] = diff(lp(cell), lp(ANCHOR))
    out["gold_lp[near_high_overlap] - gold_lp[far]"] = diff(lp(NEAR), lp(FAR))
    out["gold_lp[near_high_overlap] - gold_lp[moderate]"] = diff(lp(NEAR), lp(MOD))
    out["gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near]"] = diff(lp(NEAR), lp(INCOMPAT))
    out["gold_lp[near_high_overlap] - gold_lp[convertible_unit]"] = diff(lp(NEAR), lp(CONVERT))
    out["R_alt[near_high_overlap] - R_alt[far]"] = diff(ra(NEAR), ra(FAR))
    out["R_alt[near_high_overlap] - R_alt[moderate]"] = diff(ra(NEAR), ra(MOD))
    out["R_alt[near_high_overlap] - R_alt[incompatible_unit_near]"] = diff(ra(NEAR), ra(INCOMPAT))
    return out


def d_lp(cells: dict[str, dict]) -> dict[str, float | None]:
    values = [gold_lp(cells[c]) for c in SHARED_GOLD_CELLS if c in cells and gold_lp(cells[c]) is not None]
    if len(values) < 2:
        return {"n_cells": len(values), "range": None, "sd": None, "mad": None}
    return {"n_cells": len(values), "range": float(max(values) - min(values)),
            "sd": float(np.std(values, ddof=1)), "mad": mad(values)}


def cluster_bootstrap(values: list[float], rng: np.random.Generator, n_boot: int = N_BOOT) -> dict[str, Any]:
    """Cluster bootstrap over structures of the mean of structure-level values (percentile interval)."""

    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        return {"n_structures": int(arr.size), "mean": float(arr.mean()) if arr.size else None, "ci95": None,
                "status": "NOT_EVALUATED: fewer than two structures"}
    draws = rng.integers(0, arr.size, size=(n_boot, arr.size))
    means = arr[draws].mean(axis=1)
    return {"n_structures": int(arr.size), "mean": float(arr.mean()),
            "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
            "n_positive": int((arr > 0).sum()), "n_negative": int((arr < 0).sum()), "n_zero": int((arr == 0).sum()),
            "status": "precision-limited descriptive interval; not a test"}


def structure_level(per_item: dict[tuple[str, int], dict[str, float | None]], name: str) -> dict[str, float]:
    """Mean over the instantiations of a structure for which the contrast exists; structures with none are dropped."""

    by_structure: dict[str, list[float]] = defaultdict(list)
    for (structure, _), contrasts in per_item.items():
        value = contrasts.get(name)
        if value is not None:
            by_structure[structure].append(value)
    return {s: float(np.mean(v)) for s, v in sorted(by_structure.items())}


def assay_response(index: dict, model: str, structures: list[str]) -> dict[str, Any]:
    """Does the free generation change when the relevant variable is edited (a 20% to 50% change in the gold)?"""

    rows = []
    for structure in structures:
        for instance in sorted({k[2] for k in index if k[0] == model and k[1] == structure}):
            base, edit = index.get((model, structure, instance, ANCHOR)), index.get((model, structure, instance, "relevant_edit"))
            if not base or not edit:
                continue
            row = {"structure": structure, "instance": instance, "gold_base": base["gold_value"],
                   "gold_edit": edit["gold_value"], "gen_base": None, "gen_edit": None, "changed": None,
                   "moved_toward_new_gold": None, "direction_matches": None}
            if base["parse_status"] == "PARSED" and edit["parse_status"] == "PARSED":
                gb, ge = base["parsed_answer"]["value"], edit["parsed_answer"]["value"]
                row.update(gen_base=gb, gen_edit=ge, changed=ge != gb,
                           moved_toward_new_gold=abs(ge - edit["gold_value"]) < abs(gb - edit["gold_value"]),
                           direction_matches=(ge != gb) and ((ge - gb > 0) == (edit["gold_value"] - base["gold_value"] > 0)))
            rows.append(row)
    evaluable = [r for r in rows if r["changed"] is not None]
    return {"n_pairs": len(rows), "n_evaluable": len(evaluable),
            "n_generation_changed": sum(bool(r["changed"]) for r in evaluable),
            "n_changed_in_the_direction_of_the_gold": sum(bool(r["direction_matches"]) for r in evaluable),
            "n_moved_toward_new_gold": sum(bool(r["moved_toward_new_gold"]) for r in evaluable),
            "rows": rows}


def copy_rates(records: list[dict]) -> dict[str, dict[str, Any]]:
    """Share of generations whose value equals the cue numeral, per cell with a numeric cue (descriptive only)."""

    out: dict[str, dict[str, Any]] = {}
    for cell in DECOY_CELLS:
        rows = [r for r in records if r["cell_id"] == cell and r["parse_status"] == "PARSED"
                and r.get("cue_numeric_value") is not None]
        copies = sum(abs(r["parsed_answer"]["value"] - float(r["cue_numeric_value"])) < 1e-9 for r in rows)
        out[cell] = {"n_parsed": len(rows), "n_equal_to_cue_numeral": int(copies),
                     "n_records": sum(r["cell_id"] == cell for r in records)}
    return out


def eligibility(records: list[dict], index: dict, model: str) -> dict[str, Any]:
    mine = [r for r in records if r["model_id"] == model]
    anchors = [r for r in mine if r["cell_id"] == ANCHOR]
    return {"all_valid_items": sum(r["status"] == "OK" for r in mine),
            "format_parseable": sum(r["parse_status"] == "PARSED" for r in mine),
            "anchors": len(anchors), "anchors_parseable": sum(r["parse_status"] == "PARSED" for r in anchors),
            "base_correct_anchors": sum(r["correctness"] == "correct" for r in anchors),
            "model_positive": "NOT_EVALUATED: no sensitivity label exists for the v2 structures"}


def analyse_model(records: list[dict], model: str, rng: np.random.Generator) -> dict[str, Any]:
    index = index_records(records)
    mine = [r for r in records if r["model_id"] == model]
    structures = sorted({r["structure_id"] for r in mine})
    per_item: dict[tuple[str, int], dict[str, float | None]] = {}
    dlp: dict[tuple[str, int], dict[str, float | None]] = {}
    for structure in structures:
        for instance in sorted({int(r["instance"]) for r in mine if r["structure_id"] == structure}):
            cells = {c: index[(model, structure, instance, c)] for c in {k[3] for k in index
                     if k[0] == model and k[1] == structure and k[2] == instance}}
            per_item[(structure, instance)] = item_contrasts(cells)
            dlp[(structure, instance)] = d_lp(cells)
    names = list(next(iter(per_item.values())).keys())
    contrasts = {}
    for name in names:
        by_structure = structure_level(per_item, name)
        contrasts[name] = {"by_structure": by_structure, **cluster_bootstrap(list(by_structure.values()), rng)}
    cell_means = {}
    for cell in sorted({r["cell_id"] for r in mine}):
        rows = [r for r in mine if r["cell_id"] == cell]
        lps = [gold_lp(r) for r in rows if gold_lp(r) is not None]
        ras = [r_alt(r) for r in rows if r_alt(r) is not None]
        cell_means[cell] = {"n": len(rows), "mean_gold_logprob": float(np.mean(lps)) if lps else None,
                            "n_with_R_alt": len(ras), "mean_R_alt": float(np.mean(ras)) if ras else None,
                            "R_alt": None if ras else "NOT_EVALUATED: no decoy candidate for this cell"}
    d_struct = {}
    for key in ("range", "sd", "mad"):
        values = {s: float(np.mean([dlp[(s, i)][key] for (s2, i) in dlp if s2 == s and dlp[(s, i)][key] is not None]))
                  for s in structures if any(dlp[(s, i)][key] is not None for (s2, i) in dlp if s2 == s)}
        d_struct[key] = {"by_structure": values, **cluster_bootstrap(list(values.values()), rng)}
    return {"model_id": model, "n_records": len(mine), "n_structures": len(structures),
            "eligibility": eligibility(records, index, model), "cell_means": cell_means,
            "contrasts": contrasts, "D_lp": d_struct, "assay_response_relevant_edit": assay_response(index, model, structures),
            "copy_rate_of_cue_numeral": copy_rates(mine), "per_item_contrasts": {
                f"{s}/{i}": v for (s, i), v in sorted(per_item.items())}}


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c) for c in columns})


def fmt(x: Any, digits: int = 2) -> str:
    return "NOT_EVALUATED" if x is None else f"{x:.{digits}f}"


def report(results: dict[str, dict], summary: dict[str, Any]) -> str:
    lines = ["# Stage 14.8 pilot analysis (descriptive, precision-limited)", "",
             "Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Ten structures are the",
             "independent units (v2 §8.1); intervals are cluster bootstrap over structures (2,000 resamples, seed 42) and are",
             "descriptions of precision, not tests. A contrast is a difference of raw log-probabilities (nats) of the same gold",
             "string; cells whose gold differs from the anchor (relevant edit, role reversal) are not in these contrasts.", ""]
    for model, res in results.items():
        e = res["eligibility"]
        lines += [f"## {model}", "",
                  f"Records {res['n_records']}; all-valid {e['all_valid_items']}; format-parseable {e['format_parseable']}; "
                  f"no-cue anchors {e['anchors']} (parseable {e['anchors_parseable']}, correct {e['base_correct_anchors']}). "
                  f"Model-positive stratum: {e['model_positive']}.", ""]
        lines += ["| Contrast (nats) | structures | mean | 95% cluster-bootstrap interval | structures up / down |", "|---|---|---|---|---|"]
        for name, c in res["contrasts"].items():
            ci = c["ci95"]
            lines.append(f"| {name} | {c['n_structures']} | {fmt(c['mean'])} | "
                         f"{'NOT_EVALUATED' if ci is None else f'[{ci[0]:.2f}, {ci[1]:.2f}]'} | "
                         f"{c.get('n_positive', '-')} / {c.get('n_negative', '-')} |")
        a = res["assay_response_relevant_edit"]
        lines += ["", f"Assay response to the relevant edit: {a['n_evaluable']} evaluable instantiation pairs of {a['n_pairs']}; "
                  f"the generated value changed in {a['n_generation_changed']}, changed in the direction of the new gold in "
                  f"{a['n_changed_in_the_direction_of_the_gold']}, moved closer to the new gold in {a['n_moved_toward_new_gold']}.", ""]
        lines += ["| Cell | n | mean gold log-prob | n with R_alt | mean R_alt |", "|---|---|---|---|---|"]
        for cell, m in res["cell_means"].items():
            lines.append(f"| {cell} | {m['n']} | {fmt(m['mean_gold_logprob'])} | {m['n_with_R_alt']} | {fmt(m['mean_R_alt'])} |")
        lines += ["", "Copy of the cue numeral as the generated answer (descriptive): " + "; ".join(
            f"{cell.replace('nongov_', '')} {v['n_equal_to_cue_numeral']}/{v['n_parsed']}"
            for cell, v in res["copy_rate_of_cue_numeral"].items()), ""]
    lines += ["## Not evaluated", ""] + [f"- {k}: {v}" for k, v in summary["not_evaluated"].items()] + [""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="+", required=True, help="raw_records.jsonl files, one per model")
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    args = parser.parse_args()

    sha = git("rev-parse", "HEAD")
    day = git("log", "-1", "--format=%cd", "--date=format:%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    all_records: list[dict] = []
    inputs = {}
    for path in args.records:
        recs = load_records(Path(path))
        all_records += recs
        inputs[path] = {"sha256": sha256_file(Path(path)), "n_records": len(recs)}
    models = sorted({r["model_id"] for r in all_records})
    rng = np.random.default_rng(SEED)
    results = {m: analyse_model(all_records, m, rng) for m in models}

    not_evaluated = {
        "correctness-transition endpoint (C_gen)": "base-correct anchors are almost empty, so no transition from correct to wrong is estimable",
        "presentation-noise floor (P1.7)": "no repeat pass or dtype variation was run; cue effects cannot be read against a noise distribution",
        "model-positive stratum": "no sensitivity label exists for the v2 structures",
        "R_alt for cells without a numeric cue": "no decoy candidate (v2 §4); recorded as null in the raw records",
        "interaction tests": "not attempted: ten structures cannot support a powered interaction claim (protocol section 1)"}
    summary = {"stage": "14.8", "kind": "descriptive pilot analysis", "source_commit": sha,
               "git_status_short": git("status", "--short").splitlines(), "command": " ".join(sys.argv),
               "inputs": inputs, "n_bootstrap": N_BOOT, "seed": SEED, "evidence_class": "exploratory; not paper-eligible",
               "not_evaluated": not_evaluated, "models": {m: {k: v for k, v in r.items() if k != "per_item_contrasts"}
                                                         for m, r in results.items()}}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = [{"model": m, "contrast": name, "n_structures": c["n_structures"], "mean": c["mean"],
             "ci95_low": None if c["ci95"] is None else c["ci95"][0], "ci95_high": None if c["ci95"] is None else c["ci95"][1],
             "n_positive": c.get("n_positive"), "n_negative": c.get("n_negative")}
            for m, r in results.items() for name, c in r["contrasts"].items()]
    write_csv(out_dir / "contrasts_structure_level.csv", rows,
              ["model", "contrast", "n_structures", "mean", "ci95_low", "ci95_high", "n_positive", "n_negative"])
    item_rows = [{"model": m, "item": item, "contrast": name, "value": value}
                 for m, r in results.items() for item, v in r["per_item_contrasts"].items() for name, value in v.items()]
    write_csv(out_dir / "contrasts_by_item.csv", item_rows, ["model", "item", "contrast", "value"])
    (out_dir / "report.md").write_text(report(results, summary), encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "models": models,
                      "n_contrasts": {m: len(r["contrasts"]) for m, r in results.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
