#!/usr/bin/env python3
"""Stage 15 G2 step 1: report of the design-validation pilot (dataset named by the cells file; CPU only; numpy/scipy).

The analysis is fixed here, before any record of the pilot exists (plan: `docs/registry/v2/g2/design_validation_pilot_plan.md`). It
computes, per model and per structure, the four design blocks of that plan, each number with its denominator:

1. Grading: O3 completion statuses, correct counts under the three views, the declared-vs-rel1pct gap, parse failures among COMPLETE
   per cell (flag > 5%), and a seeded audit sample (seed 197, 10 records per model and stratum) for the main session to read.
2. Certification: R cells (share matching the R gold, share matching the base gold), D and N cells (share matching the base gold, any
   misuse class, the placebo), the modal COMPLETE answer per cell and what it is, and cells whose modal answer is "none" in every model.
3. Ambiguity: rule-B phrasing agreement on tracking share per structure, WORDING_DEPENDENT structures, S26 R1 and S55 R1 reported apart.
4. Feasibility: no-cue correctness against the band [0.30, 0.85], T_R, budget exhaustion and format failure, generated tokens.

No hypothesis status, no F1-F3 label, no Holm (the plan forbids them for M0). A record whose completion status is not COMPLETE is never
counted wrong: it is its own category. A cell, structure or model without records is NOT_EVALUATED, never zero.

Usage:
  PYTHONNOUSERSITE=1 PYTHONPATH=src python scripts/v2/s197_g2_pilot_report.py --cells data/v2/dataset/m0_v22/cells.jsonl \
      --records <run_id>=<raw_records.jsonl> [--records ...] --out-dir <new directory>
Writes report.json, report.md and audit_sample.jsonl; refuses to overwrite any of them.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scipy import stats

from physmon.analysis import rolevalue_stats as rs
from physmon.scoring import grading_views as gv

NOT_EVALUATED = "NOT_EVALUATED"
PARSE_FLAG = 0.05
BAND = (0.30, 0.85)  # decision 9 (reported beside the no-cue correctness; not a test here)
AUDIT_SEED = 197
AUDIT_N = 10
TAIL_CHARS = 400
DEFAULT_K = 24
STRATA = ("none", "R", "D", "N", "C", "K", "K_out", "support")
BUDGET_STATUSES = ("BUDGET_EXHAUSTED", "TRUNCATED")
VIEW_FIELDS = {"declared": "grade_declared", "convertible": "grade_convertible", "rel1pct": "grade_rel1pct"}
MEDIUM_FLAG_CELLS = (("S26", "r1"), ("S55", "r1"))
OUTPUT_FILES = ("report.json", "report.md", "audit_sample.jsonl")


# --- small helpers ------------------------------------------------------------------------------------------------------

def share(k: int, n: int) -> dict[str, Any]:
    """A count with its denominator; no denominator is NOT_EVALUATED, never a zero share."""

    return {"k": k, "n": n, "share": (k / n) if n else None}


def fmt(s: Mapping[str, Any] | None) -> str:
    if s is None or s.get("share") is None:
        return NOT_EVALUATED
    return f"{s['k']}/{s['n']} ({s['share']:.3f})"


def is_complete(record: Mapping[str, Any]) -> bool:
    return record.get("completion_status") == "COMPLETE"


def is_unparsed_complete(record: Mapping[str, Any]) -> bool:
    """A COMPLETE record without a usable value in the gold unit (not parsed, unknown unit or wrong dimension)."""

    return is_complete(record) and record.get("value_in_gold_unit") is None


def status_class(record: Mapping[str, Any]) -> str:
    status = record.get("completion_status")
    if status == "COMPLETE":
        return "COMPLETE"
    return "BUDGET" if status in BUDGET_STATUSES else "FORMAT"


def sig4(value: float) -> float:
    return float(f"{value:.4g}")


def base_prefix(job_id: str) -> str:
    """Structure-instance prefix of a job id (`S01-i0:R:z0:r0:after_context` -> `S01-i0`)."""

    return job_id.split(":", 1)[0]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(path) as handle:
        return [json.loads(line) for line in handle if line.strip()]


# --- per-cell quantities (blocks 1 and 2) -------------------------------------------------------------------------------

def modal_answer(recs: Sequence[Mapping[str, Any]], cell: rs.Cell) -> dict[str, Any]:
    """Modal COMPLETE answer (4 significant figures, in the gold unit) and what a certified route predicts for it."""

    values = [sig4(float(r["value_in_gold_unit"])) for r in recs if is_complete(r) and r.get("value_in_gold_unit") is not None]
    if not values:
        return {"status": NOT_EVALUATED, "n_valued": 0}
    counts = Counter(values)
    top = max(counts.values())
    tied = sorted(v for v, c in counts.items() if c == top)
    value = tied[0]  # deterministic tie-break: the smallest rounded value; `tie` says so
    targets: dict[str, float | None] = {"gold": cell.gold, "placebo": cell.placebo, **cell.foils}
    matches = gv.match_foils(value, targets)["matches"]
    if "gold" in matches:
        kind = "gold"
    elif any(m != "placebo" for m in matches):
        kind = "foil"
    elif "placebo" in matches:
        kind = "placebo"
    else:
        kind = "none"
    return {"status": "OK", "value": value, "count": top, "n_valued": len(values), "tie": len(tied) > 1,
            "kind": kind, "matches": matches}


def misuse_classes(cell: rs.Cell) -> dict[str, list[float]]:
    """Per misuse class the unconfounded declared values of the cell (neglect is not a misuse; see `rolevalue_stats`)."""

    skip = rs._confounded_names(cell)
    classes: dict[str, list[float]] = defaultdict(list)
    for name, target in cell.foils.items():
        if name in rs.NOT_MISUSE or name in skip or target is None:
            continue
        classes[rs.curve_class(name)].append(float(target))
    return dict(classes)


def cell_stats(cell: rs.Cell, recs: Sequence[Mapping[str, Any]], base_gold: float | None, k_expected: int) -> dict[str, Any]:
    """Everything the four blocks need from one cell's records."""

    if not recs:
        return {"status": NOT_EVALUATED, "stratum": cell.stratum, "structure_id": cell.structure_id,
                "phrasing_id": cell.phrasing_id, "value_index": cell.value_index, "n_records": 0, "expected": k_expected}
    complete = [r for r in recs if is_complete(r)]
    statuses = Counter(str(r.get("completion_status")) for r in recs)
    out: dict[str, Any] = {
        "status": "OK", "stratum": cell.stratum, "structure_id": cell.structure_id, "phrasing_id": cell.phrasing_id,
        "value_index": cell.value_index, "n_records": len(recs), "expected": k_expected, "statuses": dict(statuses),
        "n_complete": len(complete),
        "correct": {view: share(sum(r.get(field) == "correct" for r in complete), len(complete))
                    for view, field in VIEW_FIELDS.items()},
        "tracking_all": share(sum(rs.tracking(r) for r in recs), len(recs)),
    }
    out["gap_rel1pct_minus_declared"] = (out["correct"]["rel1pct"]["k"] - out["correct"]["declared"]["k"]) if complete else None
    unparsed = sum(is_unparsed_complete(r) for r in complete)
    out["unparsed_complete"] = share(unparsed, len(complete))
    out["parse_flag"] = bool(complete) and unparsed / len(complete) > PARSE_FLAG
    fmt_fail = sum(status_class(r) == "FORMAT" for r in recs)
    out["format_failure"] = share(fmt_fail, len(recs))
    out["format_flag"] = fmt_fail / len(recs) > PARSE_FLAG
    out["tokens"] = [int(r["n_generated_tokens"]) for r in recs if r.get("n_generated_tokens") is not None]
    cert: dict[str, Any] = {"modal": modal_answer(recs, cell)}
    if cell.stratum == "R":
        cert["r_gold"] = share(out["correct"]["declared"]["k"], len(complete))
        cert["base_gold"] = (share(sum(rs.matches_value(r, base_gold) for r in complete), len(complete))
                             if base_gold is not None else None)
    if cell.stratum in ("D", "N"):
        cert["base_gold"] = share(out["correct"]["declared"]["k"], len(complete))
        classes = misuse_classes(cell)
        cert["misuse"] = (None if not classes else {
            "by_class": {h: share(sum(any(rs.matches_value(r, t) for t in ts) for r in complete), len(complete))
                         for h, ts in sorted(classes.items())},
            "any": share(sum(any(rs.matches_value(r, t) for ts in classes.values() for t in ts) for r in complete),
                         len(complete))})
        cert["placebo"] = (share(sum(rs.matches_value(r, cell.placebo) for r in complete), len(complete))
                           if cell.placebo is not None else None)
    out["certification"] = cert
    return out


# --- aggregation over cells -----------------------------------------------------------------------------------------------

def grading_block(cell_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Block 1 over a set of cells, per stratum: O3 statuses, correct counts per view, gap, with denominators."""

    out: dict[str, Any] = {}
    for stratum in STRATA:
        rows = [c for c in cell_rows if c["stratum"] == stratum]
        if not rows:
            continue
        evaluated = [c for c in rows if c["status"] == "OK"]
        if not evaluated:
            out[stratum] = {"status": NOT_EVALUATED, "n_cells": len(rows), "n_cells_missing": len(rows)}
            continue
        statuses: Counter[str] = Counter()
        for c in evaluated:
            statuses.update(c["statuses"])
        n_complete = sum(c["n_complete"] for c in evaluated)
        correct = {v: share(sum(c["correct"][v]["k"] for c in evaluated), n_complete) for v in VIEW_FIELDS}
        out[stratum] = {
            "status": "OK", "n_cells": len(rows), "n_cells_missing": len(rows) - len(evaluated),
            "n_records": sum(c["n_records"] for c in evaluated), "o3_statuses": dict(sorted(statuses.items())),
            "n_complete": n_complete, "correct": correct,
            "gap_rel1pct_minus_declared": share(correct["rel1pct"]["k"] - correct["declared"]["k"], n_complete),
            "unparsed_complete": share(sum(c["unparsed_complete"]["k"] for c in evaluated), n_complete),
        }
    return out


def feasibility_block(cell_rows: Sequence[Mapping[str, Any]], structure_id: str | None) -> dict[str, Any]:
    """Block 4 for one structure (or the whole model when `structure_id` is None)."""

    rows = [c for c in cell_rows if structure_id is None or c["structure_id"] == structure_id]
    ok = [c for c in rows if c["status"] == "OK"]
    out: dict[str, Any] = {"n_cells": len(rows), "n_cells_missing": len(rows) - len(ok)}
    no_cue = [c for c in ok if c["stratum"] == "none"]
    if no_cue:
        n_all = sum(c["n_records"] for c in no_cue)
        n_complete = sum(c["n_complete"] for c in no_cue)
        k = sum(c["correct"]["declared"]["k"] for c in no_cue)
        primary = share(k, n_all)  # tracking over every sample present: non-COMPLETE is not correct, and not counted wrong
        among = share(k, n_complete)
        out["no_cue"] = {"correct_of_all_samples": primary, "correct_of_complete": among,
                         "n_noncomplete": n_all - n_complete, "band": list(BAND),
                         "in_band": (BAND[0] <= primary["share"] <= BAND[1]) if primary["share"] is not None else NOT_EVALUATED}
    else:
        out["no_cue"] = {"status": NOT_EVALUATED, "band": list(BAND)}
    r_rows = [c for c in ok if c["stratum"] == "R"]
    if r_rows:
        k = sum(c["correct"]["declared"]["k"] for c in r_rows)
        out["T_R"] = {"of_all_samples": share(sum(c["tracking_all"]["k"] for c in r_rows), sum(c["n_records"] for c in r_rows)),
                      "of_complete": share(k, sum(c["n_complete"] for c in r_rows))}
    else:
        out["T_R"] = {"status": NOT_EVALUATED}
    n_rec = sum(c["n_records"] for c in ok)
    if n_rec:
        classes = Counter()
        for c in ok:
            for status, count in c["statuses"].items():
                classes[status_class({"completion_status": status})] += count
        tokens = [t for c in ok for t in c["tokens"]]
        out["budget_exhaustion"] = share(classes["BUDGET"], n_rec)
        out["format_failure"] = share(classes["FORMAT"], n_rec)
        out["tokens"] = ({"n": len(tokens), "mean": sum(tokens) / len(tokens), "max": max(tokens)} if tokens
                         else {"status": NOT_EVALUATED})
    else:
        out["budget_exhaustion"] = out["format_failure"] = out["tokens"] = {"status": NOT_EVALUATED}
    return out


# --- block 3: phrasing agreement -------------------------------------------------------------------------------------------

def newcombe(k1: int, n1: int, k0: int, n0: int, level: float) -> tuple[float, float, float]:
    """Newcombe hybrid-score interval for p1 - p0 (Wilson score intervals of each proportion)."""

    z = stats.norm.ppf(1 - (1 - level) / 2)

    def wilson(k: int, n: int) -> tuple[float, float]:
        p = k / n
        centre = (p + z * z / (2 * n)) / (1 + z * z / n)
        half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        return centre - half, centre + half

    l1, u1 = wilson(k1, n1)
    l0, u0 = wilson(k0, n0)
    p1, p0 = k1 / n1, k0 / n0
    d = p1 - p0
    return (d - math.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2), d)


def agreement_per_structure(k_a: int, n_a: int, k_b: int, n_b: int, margin: float) -> dict[str, Any]:
    """Rule B (`rolevalue_stats.AGREEMENT_RULE_TEXT["B"]`) for one structure's two phrasings on tracking share. The library rule runs
    on differences over >= 6 structures; here the unit is one structure, so the difference is p_a - p_b over the pooled samples with a
    Newcombe interval: AGREE iff the 90% interval lies inside +-margin (TOST at 0.05), DISAGREE iff the 95% interval excludes zero and
    extends beyond the margin (DISAGREE takes precedence, as in `classify`), else UNRESOLVED."""

    if not n_a or not n_b:
        return {"agreement": NOT_EVALUATED, "n_a": n_a, "n_b": n_b}
    lo95, hi95, diff = newcombe(k_a, n_a, k_b, n_b, 0.95)
    lo90, hi90, _ = newcombe(k_a, n_a, k_b, n_b, 0.90)
    excludes_zero = lo95 > 0 or hi95 < 0
    if excludes_zero and (hi95 > margin or lo95 < -margin):
        label = rs.DISAGREE
    elif lo90 > -margin and hi90 < margin:
        label = rs.AGREE
    else:
        label = rs.UNRESOLVED
    return {"agreement": label, "diff": diff, "ci95": [lo95, hi95], "ci90": [lo90, hi90], "margin": margin,
            "a": share(k_a, n_a), "b": share(k_b, n_b)}


def ambiguity_block(by_cell: Mapping[str, Sequence[Mapping[str, Any]]], cells: Mapping[str, rs.Cell],
                    cell_rows: Mapping[str, Mapping[str, Any]], structures: Sequence[str]) -> dict[str, Any]:
    """Block 3 for one model: per structure and twin (R, D) the rule-B state on tracking, the cross-structure library rule B on the
    same differences, WORDING_DEPENDENT structures, and the medium-flag cells reported on their own."""

    index = rs.phrasing_indices(cells)
    margins = {"R": rs.SESOI["F2"], "D": rs.SESOI["F1"]}
    per: dict[str, dict[str, Any]] = {}
    diffs: dict[str, list[float]] = {"R": [], "D": []}
    for sid in structures:
        per[sid] = {}
        for stratum in ("R", "D"):
            counts = {0: [0, 0, 0], 1: [0, 0, 0]}  # successes, samples, non-COMPLETE per phrasing index
            for key, recs in by_cell.items():
                c = cells[key]
                if c.structure_id != sid or c.stratum != stratum or key not in index or index[key] not in counts:
                    continue
                slot = counts[index[key]]
                slot[0] += sum(rs.tracking(r) for r in recs)
                slot[1] += len(recs)
                slot[2] += sum(not is_complete(r) for r in recs)
            res = agreement_per_structure(counts[0][0], counts[0][1], counts[1][0], counts[1][1], margins[stratum])
            res["n_noncomplete"] = {"phrasing_0": counts[0][2], "phrasing_1": counts[1][2]}
            per[sid][stratum] = res
            if res["agreement"] != NOT_EVALUATED:
                diffs[stratum].append(res["diff"])
    wording = sorted(sid for sid, d in per.items() if any(v["agreement"] == rs.DISAGREE for v in d.values()))
    cross = {s: rs.phrasing_difference_agreement(diffs[s], margins[s]) for s in ("R", "D")}
    medium: dict[str, Any] = {}
    for sid, phrasing in MEDIUM_FLAG_CELLS:
        rows = {k: v for k, v in cell_rows.items() if v["structure_id"] == sid and v["stratum"] == "R"
                and v["phrasing_id"] == phrasing}
        medium[f"{sid} R:{phrasing}"] = rows if rows else NOT_EVALUATED
    return {"per_structure": per, "wording_dependent": wording, "cross_structure_rule_B": cross, "medium_flag_cells": medium,
            "note": "tracking = library `tracking` (non-COMPLETE counts as not tracking; its number is beside each state)"}


# --- one model -------------------------------------------------------------------------------------------------------------

def analyse_model(records: Sequence[Mapping[str, Any]], cells: Mapping[str, rs.Cell], base_golds: Mapping[str, float],
                  k_expected: int) -> dict[str, Any]:
    by_cell = rs.group_records(records, cells)
    rows = {key: cell_stats(cell, by_cell.get(key, []), base_golds.get(base_prefix(key)), k_expected)
            for key, cell in cells.items()}
    structures = sorted({c.structure_id for c in cells.values()})
    row_list = list(rows.values())
    out: dict[str, Any] = {
        "n_records": len(records), "n_cells": len(cells), "n_cells_without_records": sum(r["status"] != "OK" for r in row_list),
        "grading": {"all": grading_block(row_list), "by_structure": {s: grading_block(
            [r for r in row_list if r["structure_id"] == s]) for s in structures}},
        "parse_flagged_cells": sorted(k for k, r in rows.items() if r.get("parse_flag")),
        "format_flagged_cells": sorted(k for k, r in rows.items() if r.get("format_flag")),
        "ambiguity": ambiguity_block(by_cell, cells, rows, structures),
        "feasibility": {"all": feasibility_block(row_list, None),
                        "by_structure": {s: feasibility_block(row_list, s) for s in structures}},
        "cells": {k: {kk: vv for kk, vv in r.items() if kk != "tokens"} for k, r in rows.items()},
    }
    return out


def audit_sample(model: str, records: Sequence[Mapping[str, Any]], cells: Mapping[str, rs.Cell]) -> list[dict[str, Any]]:
    """Deterministic sample (seed 197) of up to 10 records per stratum, drawn from every record of the model."""

    pools: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for r in records:
        pools[cells[rs.cell_key(r)].stratum].append(r)
    out = []
    for stratum in sorted(pools):
        pool = sorted(pools[stratum], key=lambda r: str(r["job_id"]))
        for r in random.Random(f"{AUDIT_SEED}|{model}|{stratum}").sample(pool, min(AUDIT_N, len(pool))):
            out.append({"model": model, "stratum": stratum, "job_id": r["job_id"], "cell": rs.cell_key(r),
                        "gold_value": r.get("gold_value"), "gold_unit": r.get("gold_unit"),
                        "parsed_answer": r.get("parsed_answer"), "value_in_gold_unit": r.get("value_in_gold_unit"),
                        "completion_status": r.get("completion_status"),
                        **{field: r.get(field) for field in VIEW_FIELDS.values()},
                        "response_tail": str(r.get("generated_answer_raw") or "")[-TAIL_CHARS:]})
    return out


def none_modal_cells(models: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """R, D and N cells whose modal COMPLETE answer is `none` in every model with an evaluable modal answer (a model that has none
    for the cell is listed in `not_evaluated_models`; at least one model must be evaluable)."""

    flagged: dict[str, Any] = {}
    keys = sorted({k for m in models.values() for k, c in m["cells"].items() if c["stratum"] in ("R", "D", "N")})
    for key in keys:
        kinds, missing = {}, []
        for name, m in models.items():
            modal = m["cells"][key].get("certification", {}).get("modal", {"status": NOT_EVALUATED})
            if modal["status"] == "OK":
                kinds[name] = modal["kind"]
            else:
                missing.append(name)
        if kinds and all(v == "none" for v in kinds.values()):
            flagged[key] = {"models": sorted(kinds), "not_evaluated_models": missing,
                            "modal": {n: models[n]["cells"][key]["certification"]["modal"]["value"] for n in kinds}}
    return flagged


def dataset_label(cells_rows: Sequence[Mapping[str, Any]]) -> str:
    """The dataset version named by the cells file (`m0_version`), e.g. `m0_v2.5`; never a hard-coded label."""

    labels = sorted({str(r["m0_version"]) for r in cells_rows if r.get("m0_version")})
    return "+".join(labels) if labels else "unknown dataset"


def grader_versions(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Grader versions carried by the records; records without the field were graded by v1 (before amendment A2)."""

    return sorted({str(r.get("grader_version") or "v1") for r in records})


def build_report(cells_rows: Sequence[Mapping[str, Any]], runs: Mapping[str, Sequence[Mapping[str, Any]]],
                 k_expected: int = DEFAULT_K, title: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cells = rs.cells_from_rows(cells_rows)
    base_golds = {base_prefix(r["job_id"]): float(r["gold_value"]) for r in cells_rows if r.get("stratum") == "none"}
    models = {name: analyse_model(recs, cells, base_golds, k_expected) for name, recs in runs.items()}
    sample = [row for name, recs in runs.items() for row in audit_sample(name, recs, cells)]
    wording_models: dict[str, list[str]] = defaultdict(list)
    for name, m in models.items():
        for sid in m["ambiguity"]["wording_dependent"]:
            wording_models[sid].append(name)
    report = {
        "plan": "docs/registry/v2/g2/design_validation_pilot_plan.md", "evidence_class": "EXPLORATION",
        "no_hypothesis_status": "no F1-F3 label, no Holm, no model selection (plan, 'Not done here')",
        "dataset": dataset_label(cells_rows), "title": title,
        "grader_version_per_run": {name: grader_versions(recs) for name, recs in runs.items()},
        "k_expected_per_cell": k_expected, "primary_view": rs.PRIMARY_VIEW, "audit_seed": AUDIT_SEED,
        "models": models,
        "modal_none_in_every_model": none_modal_cells(models),
        "wording_dependent": {sid: sorted(ms) for sid, ms in sorted(wording_models.items())},
        "wording_review_required": sorted(sid for sid, ms in wording_models.items() if len(ms) >= 2),
    }
    return report, sample


# --- markdown ----------------------------------------------------------------------------------------------------------------

def render_markdown(report: Mapping[str, Any]) -> str:
    versions = sorted({v for vs_ in report.get("grader_version_per_run", {}).values() for v in vs_}) or ["unknown"]
    lines = [f"# {report.get('title') or 'G2 design-validation pilot report (' + str(report.get('dataset', 'unknown dataset')) + ')'}", "",
             f"Dataset: {report.get('dataset', 'unknown')}. Grader version of the records: {', '.join(versions)} "
             "(v2 = amendment A2 declared rule; `grade_declared_v1` stays in the records).", "",
             "EXPLORATION, sampled. Plan: `docs/registry/v2/g2/design_validation_pilot_plan.md`. No hypothesis status, no F1-F3 "
             "label, no Holm. Non-COMPLETE records are their own category, never wrong; missing records are NOT_EVALUATED. "
             f"Expected samples per cell: {report['k_expected_per_cell']}.", ""]
    for name, m in report["models"].items():
        lines += [f"## Model `{name}`", "",
                  f"Records {m['n_records']}; cells {m['n_cells']}, of which without records {m['n_cells_without_records']}.", "",
                  "### 1. Grading (all structures)", "",
                  "| stratum | cells (missing) | O3 statuses | COMPLETE | declared | convertible | rel1pct | gap rel1pct-declared | "
                  "unparsed among COMPLETE |", "|---|---|---|---|---|---|---|---|---|"]
        for stratum, g in m["grading"]["all"].items():
            if g["status"] != "OK":
                lines.append(f"| {stratum} | {g['n_cells']} ({g['n_cells_missing']}) | {NOT_EVALUATED} | | | | | | |")
                continue
            statuses = ", ".join(f"{k} {v}" for k, v in g["o3_statuses"].items())
            lines.append(f"| {stratum} | {g['n_cells']} ({g['n_cells_missing']}) | {statuses} | {g['n_complete']} | "
                         f"{fmt(g['correct']['declared'])} | {fmt(g['correct']['convertible'])} | {fmt(g['correct']['rel1pct'])} | "
                         f"{fmt(g['gap_rel1pct_minus_declared'])} | {fmt(g['unparsed_complete'])} |")
        lines += ["", "Per structure, all strata (correct among COMPLETE):", "",
                  "| structure | records | COMPLETE | declared | convertible | rel1pct |", "|---|---|---|---|---|---|"]
        for sid, blocks in m["grading"]["by_structure"].items():
            ok = [g for g in blocks.values() if g["status"] == "OK"]
            if not ok:
                lines.append(f"| {sid} | 0 | 0 | {NOT_EVALUATED} | {NOT_EVALUATED} | {NOT_EVALUATED} |")
                continue
            n_c = sum(g["n_complete"] for g in ok)
            cols = [fmt(share(sum(g["correct"][v]["k"] for g in ok), n_c)) for v in VIEW_FIELDS]
            lines.append(f"| {sid} | {sum(g['n_records'] for g in ok)} | {n_c} | " + " | ".join(cols) + " |")
        flagged = m["parse_flagged_cells"]
        lines += ["", f"Cells with more than {PARSE_FLAG:.0%} of COMPLETE records unparsed (no value in the gold unit): "
                  f"{len(flagged)}" + (": " + ", ".join(f"`{k}`" for k in flagged) if flagged else "") + ".",
                  f"Cells with more than {PARSE_FLAG:.0%} of all records failing the answer format (UNPARSEABLE and similar): "
                  f"{len(m['format_flagged_cells'])}" + (": " + ", ".join(f"`{k}`" for k in m["format_flagged_cells"])
                                                         if m["format_flagged_cells"] else "") + ".", "",
                  "### 2. Certification (per cell)", "",
                  "| cell | R gold | base gold | misuse (any) | placebo | modal (n of valued) | modal is |",
                  "|---|---|---|---|---|---|---|"]
        for key, c in m["cells"].items():
            if c["stratum"] not in ("R", "D", "N") or c["status"] != "OK":
                if c["stratum"] in ("R", "D", "N"):
                    lines.append(f"| `{key}` | {NOT_EVALUATED} | | | | | |")
                continue
            cert = c["certification"]
            modal = cert["modal"]
            mis = cert.get("misuse")
            mis_txt = fmt(mis["any"]) if mis else ("no declared misuse values" if c["stratum"] == "N" else NOT_EVALUATED)
            if mis:
                mis_txt += " [" + ", ".join(f"{h} {fmt(s)}" for h, s in mis["by_class"].items()) + "]"
            modal_txt = (f"{modal['value']:.4g} ({modal['count']} of {modal['n_valued']}{', tie' if modal['tie'] else ''})"
                         if modal["status"] == "OK" else NOT_EVALUATED)
            kind = (modal["kind"] + (" (" + ", ".join(modal["matches"]) + ")" if modal["matches"] else "")
                    if modal["status"] == "OK" else NOT_EVALUATED)
            def cell_fmt(name: str, cert: Mapping[str, Any] = cert) -> str:
                if name not in cert or (name == "placebo" and cert[name] is None):  # a cell without a declared placebo
                    return "n/a"
                return fmt(cert[name])

            if c["stratum"] == "R":
                mis_txt = "n/a"
            lines.append(f"| `{key}` ({c['structure_id']}) | {cell_fmt('r_gold')} | {cell_fmt('base_gold')} | {mis_txt} | "
                         f"{cell_fmt('placebo')} | {modal_txt} | {kind} |")
        lines += ["", "### 3. Ambiguity (rule B on tracking share, phrasing 0 vs 1)", "",
                  "| structure | R state (diff, 95% CI) | D state (diff, 95% CI) |", "|---|---|---|"]
        for sid, d in m["ambiguity"]["per_structure"].items():
            cols = []
            for s in ("R", "D"):
                v = d[s]
                cols.append(v["agreement"] if v["agreement"] == NOT_EVALUATED else
                            f"{v['agreement']} ({v['diff']:+.3f}, [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}]; "
                            f"{fmt(v['a'])} vs {fmt(v['b'])})")
            lines.append(f"| {sid} | {cols[0]} | {cols[1]} |")
        cross = m["ambiguity"]["cross_structure_rule_B"]
        lines += ["", "Cross-structure rule B (library `phrasing_difference_agreement` on per-structure differences): "
                  + "; ".join(f"{s}: {cross[s]['agreement']} (J={cross[s].get('J')})" for s in ("R", "D")) + ".",
                  "WORDING_DEPENDENT structures (DISAGREE on R or D twins): "
                  + (", ".join(m["ambiguity"]["wording_dependent"]) or "none") + ".", "",
                  "Medium-flag cells (reported apart):", ""]
        for label, rows in m["ambiguity"]["medium_flag_cells"].items():
            if rows == NOT_EVALUATED:
                lines.append(f"* {label}: {NOT_EVALUATED}")
                continue
            for key, c in rows.items():
                cert = c.get("certification", {})
                lines.append(f"* {label} cell `{key}`: R gold {fmt(cert.get('r_gold'))}; base gold {fmt(cert.get('base_gold'))}; "
                             f"modal {cert['modal'].get('value', NOT_EVALUATED) if cert else NOT_EVALUATED}.")
        lines += ["", "### 4. Feasibility", "",
                  "| structure | no-cue correct, of all samples | of COMPLETE | band [0.30, 0.85] | T_R of all | T_R of COMPLETE | "
                  "budget exhausted | format failure | tokens mean / max |", "|---|---|---|---|---|---|---|---|---|"]
        for sid, f in {**m["feasibility"]["by_structure"], "ALL": m["feasibility"]["all"]}.items():
            nc, tr = f["no_cue"], f["T_R"]
            tok = f["tokens"]
            in_band = nc.get("in_band", NOT_EVALUATED)
            band_txt = {True: "in band", False: "out of band"}.get(in_band, in_band)
            tok_txt = f"{tok['mean']:.0f} / {tok['max']}" if "mean" in tok else NOT_EVALUATED
            lines.append(
                f"| {sid} | {fmt(nc.get('correct_of_all_samples'))} | {fmt(nc.get('correct_of_complete'))} | "
                f"{band_txt} | {fmt(tr.get('of_all_samples'))} | {fmt(tr.get('of_complete'))} | "
                f"{fmt(f['budget_exhaustion'])} | {fmt(f['format_failure'])} | "
                f"{tok_txt} |")
        lines.append("")
    lines += ["## Cells whose modal answer is `none` in every model", ""]
    flagged = report["modal_none_in_every_model"]
    lines += ([f"* `{k}`: modal {v['modal']}; models {', '.join(v['models'])}"
               + (f"; not evaluated in {', '.join(v['not_evaluated_models'])}" if v["not_evaluated_models"] else "")
               for k, v in flagged.items()] or ["None."])
    lines += ["", "## WORDING_DEPENDENT structures across models", ""]
    lines += ([f"* {sid}: {', '.join(ms)}" + (" (wording review required: two or more models)"
                                              if sid in report["wording_review_required"] else "")
               for sid, ms in report["wording_dependent"].items()] or ["None."])
    lines += ["", "Audit sample: `audit_sample.jsonl` (seed 197, up to 10 records per model and stratum) for the main session to read.", ""]
    return "\n".join(lines)


# --- output ---------------------------------------------------------------------------------------------------------------

def write_outputs(out_dir: Path, report: Mapping[str, Any], sample: Sequence[Mapping[str, Any]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = [name for name in OUTPUT_FILES if (out_dir / name).exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite {', '.join(existing)} in {out_dir}")
    with open(out_dir / "report.json", "x") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
        handle.write("\n")
    with open(out_dir / "report.md", "x") as handle:
        handle.write(render_markdown(report))
    with open(out_dir / "audit_sample.jsonl", "x") as handle:
        for row in sample:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--records", action="append", required=True, metavar="RUN_ID=PATH")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--title", default=None, help="report title (default: from the dataset version in the cells file)")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="expected samples per cell (only for the NOT_EVALUATED table)")
    args = parser.parse_args(argv)
    runs: dict[str, list[dict[str, Any]]] = {}
    for spec in args.records:
        name, _, path = spec.partition("=")
        if not name or not path or name in runs:
            parser.error(f"--records needs a unique RUN_ID=PATH, got {spec!r}")
        runs[name] = read_jsonl(Path(path))
    existing = [n for n in OUTPUT_FILES if (args.out_dir / n).exists()]
    if existing:
        print(f"refusing to overwrite {', '.join(existing)} in {args.out_dir}", file=sys.stderr)
        return 2
    report, sample = build_report(read_jsonl(args.cells), runs, args.k, args.title)
    write_outputs(args.out_dir, report, sample)
    print(f"wrote {args.out_dir / 'report.json'}, report.md and audit_sample.jsonl ({len(runs)} model(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
