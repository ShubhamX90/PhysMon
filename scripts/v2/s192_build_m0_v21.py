#!/usr/bin/env python3
"""Stage 15: build M0 v2.1 (`data/v2/dataset/m0_v21/`): M0 v2 revised after the LLM panel review (plan revision v2.2, section G).

Same twelve structures, base instance, study values, wirings, C and K quantities and builder logic as `s188_build_m0_v2.py` (whose
helpers this script reuses; `m0_v2` stays as the record of the review and is rebuilt byte for byte by s188). What changes
(specs in `src/physmon/benchmark/v2/roles_m0v21.py`):

* G1: no `same_object_undone_event`; pair 1 is a genuine other event of the target object (or, for S72 only, a second co-present
  object of a different type, with `d_kind_note`); the certificate rejects reversal patterns and D quantities that act on the target;
* G2: the co-present object of d0 is introduced by one number-free clause appended to the base context of every cell of the
  structure (`scene_clause`); the base gold is unchanged and the builder checks that the no-cue prompt is the October problem
  with that clause inserted before the question, and nothing else;
* G4: wording fixes and naturalness rewrites of the D, N and R sentences.

Deterministic; refuses to overwrite an existing directory. Status: agent-authored, solver-certified, NOT yet reviewed by the LLM
panel. Data role: EXPLORATION.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m0v21  # noqa: E402
from physmon.benchmark.v2 import supporting_v2 as su  # noqa: E402
from physmon.benchmark.v2 import traces_v2 as t2  # noqa: E402


def _load_s188():
    spec = importlib.util.spec_from_file_location("s188_build_m0_v2", REPO_ROOT / "scripts/v2/s188_build_m0_v2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["s188_build_m0_v2"] = module
    spec.loader.exec_module(module)
    return module


s188 = _load_s188()

INSTANCE = s188.INSTANCE
STATUS = "agent-authored, solver-certified, NOT yet reviewed by the LLM panel (and not yet reviewed by a human)"
DATA_ROLE = s188.DATA_ROLE
VERSION = "m0_v2.1"


def _add_v21_fields(row: dict[str, Any], spec: r2.RoleSpecV2) -> dict[str, Any]:
    pair = next((p for p in spec.pairs if p.pair_id == row.get("pair_id")), None) if row["family"] == "role_by_value" else None
    row["m0_version"] = VERSION
    row["scene_clause"] = spec.scene_clause
    row["scene_object_rationale"] = spec.scene_object_rationale
    row["d_kind_note"] = pair.d_kind_note if pair is not None and row["stratum"] in ("D", "N") and pair.d_kind_note else None
    return row


def build(out: Path, dataset: Path) -> dict[str, Any]:
    v1 = s188.v1_rows(dataset)
    plans = t2.plans()
    rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    certificates: dict[str, Any] = {}
    excluded, scene_only_difference_failed, gold_changed = [], [], []
    for sid, spec in sorted(roles_m0v21.ROLE_SPECS.items()):
        structure = roles_m0v21.structure(sid)
        cert = r2.certify_v2(structure, spec)
        base = v1.get(f"{sid}:{INSTANCE}", {})
        record: dict[str, Any] = {"role_certificate": cert, "infeasible": [], "supporting": [], "scene_clause": spec.scene_clause,
                                  "scene_object_rationale": spec.scene_object_rationale}
        certificates[sid] = record
        if not r2.complete(spec, cert):
            excluded.append({"structure_id": sid, "failed": cert["failed"]})
            continue
        cells = r2.role_cells_v2(structure, spec, INSTANCE)
        extra, infeasible = r2.variants(structure, spec, INSTANCE, cells)
        record["infeasible"] += infeasible
        if spec.conditional is not None and not spec.conditional.k_out.feasible:
            record["infeasible"].append({"cell_id": "K_out", "condition": "K_out", "feasible": False,
                                         "reason": spec.conditional.k_out.reason})
        record["k_out_feasible"] = None if spec.conditional is None else spec.conditional.k_out.feasible
        record["k_out_reason"] = None if spec.conditional is None else spec.conditional.k_out.reason
        record["c_textbook_familiarity"] = None if spec.cancelling is None else {
            "textbook_familiarity": spec.cancelling.familiarity, "reason": spec.cancelling.familiarity_reason}
        no_cue = next(c for c in cells if c.stratum == "none")
        # the base problem is the October problem with the scene clause before the question, and nothing else
        if base:
            expected = base["problem"].replace("\n\n", f" {spec.scene_clause}\n\n", 1)
            if expected != no_cue.prompt:
                scene_only_difference_failed.append(sid)
            if not math.isclose(base["gold_answer"]["value"], no_cue.gold_value, rel_tol=1e-12):
                gold_changed.append(sid)
        plan = plans[sid]
        for cell in [*cells, *extra]:
            if not r2._prompt_numerals_ok(structure, INSTANCE, cell.prompt, cell.value):
                raise SystemExit(f"rendering self-check failed for {sid} {cell.cell_id}")
            if spec.scene_clause not in cell.prompt:
                raise SystemExit(f"scene clause missing in {sid} {cell.cell_id}")
            row = _add_v21_fields(s188.role_row(cell, structure, spec, base), spec)
            rows.append(row)
            trace = t2.trace_for_role_cell(structure, spec, plan, cell)
            trace_rows.append({"job_id": row["job_id"], "cell_id": cell.cell_id, "structure_id": sid, "instance": INSTANCE,
                               "family": cell.family, "stratum": row["stratum"], "gold_trace": {
                                   **trace, "kind": "solving technique rendered from the typed graph and the cell's wiring; "
                                                    "not model-generated text"}})
        for sup in su.support_cells(structure, INSTANCE):
            entry = {"cell_id": f"S:{sup.cell_id}", "feasible": sup.feasible, "reason": sup.reason,
                     "tolerance_status": sup.tolerance, "source_ambiguous": sup.source_ambiguous,
                     "cue_equals_gold": sup.cue_equals_gold}
            record["supporting"].append(entry)
            if not sup.feasible:
                record["infeasible"].append({"cell_id": f"S:{sup.cell_id}", "condition": sup.cell_id, "feasible": False,
                                             "reason": sup.reason})
                continue
            if sup.cue_value is not None and sup.cell_id not in ("role_reversal",) and not s188._support_numerals_ok(structure, sup):
                raise SystemExit(f"rendering self-check failed for {sid} {sup.cell_id}")
            if spec.scene_clause not in sup.prompt:
                raise SystemExit(f"scene clause missing in {sid} {sup.cell_id}")
            row = _add_v21_fields(s188.support_row(sup, structure, base), spec)
            rows.append(row)
            trace = t2.trace_for_support(structure, plan, sup)
            trace_rows.append({"job_id": row["job_id"], "cell_id": row["cell_id"], "structure_id": sid, "instance": INSTANCE,
                               "family": "supporting", "stratum": "support", "gold_trace": {
                                   **trace, "kind": "solving technique rendered from the typed graph; not model-generated text"}})
    if scene_only_difference_failed or gold_changed:
        raise SystemExit(f"base problem check failed: scene-only {scene_only_difference_failed}, gold changed {gold_changed}")
    ids = [r["job_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate job ids")
    out.mkdir(parents=True, exist_ok=False)
    cells_text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    traces_text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in trace_rows)
    cert_text = json.dumps(certificates, indent=2, sort_keys=True, default=str, ensure_ascii=False) + "\n"
    (out / "cells.jsonl").write_text(cells_text, encoding="utf-8")
    (out / "traces.jsonl").write_text(traces_text, encoding="utf-8")
    (out / "certificates.json").write_text(cert_text, encoding="utf-8")
    counts = {"n_cells": len(rows), "n_structures": len({r["structure_id"] for r in rows}),
              "by_family": dict(sorted(Counter(r["family"] for r in rows).items())),
              "by_stratum": dict(sorted(Counter(r["stratum"] for r in rows).items())),
              "by_structure": dict(sorted(Counter(r["structure_id"] for r in rows).items())),
              "by_family_and_stratum": dict(sorted(Counter(f"{r['family']}/{r['stratum']}" for r in rows).items())),
              "by_d_kind_d_cells": dict(sorted(Counter(r["d_kind"] for r in rows if r["stratum"] == "D").items())),
              "by_d_kind_by_structure": {sid: sorted({r["d_kind"] for r in rows if r["stratum"] == "D" and r["structure_id"] == sid})
                                         for sid in sorted({r["structure_id"] for r in rows})},
              "by_condition_supporting": dict(sorted(Counter(r["condition"] for r in rows if r["family"] == "supporting").items()))}
    (out / "README.md").write_text(readme(counts, certificates, excluded, rows), encoding="utf-8")
    manifest = {**counts, "instance": INSTANCE, "excluded": excluded, "version": VERSION,
                "base_prompt_is_october_problem_plus_scene_clause": True, "base_gold_unchanged": True,
                "scene_clauses": {sid: s.scene_clause for sid, s in sorted(roles_m0v21.ROLE_SPECS.items())},
                "data_role": DATA_ROLE, "status": STATUS,
                "n_infeasible_conditions": sum(len(c["infeasible"]) for c in certificates.values()),
                "k_out_feasible": {sid: c.get("k_out_feasible") for sid, c in sorted(certificates.items())},
                "file_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                for name in ("cells.jsonl", "traces.jsonl", "certificates.json", "README.md")}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def readme(counts: dict[str, Any], certificates: dict[str, Any], excluded: list, rows: list[dict[str, Any]]) -> str:
    inf = Counter(r["condition"] for c in certificates.values() for r in c["infeasible"])
    ambiguous = Counter(r["condition"] for r in rows if r["source_ambiguous"])
    k_out = sorted(sid for sid, c in certificates.items() if c.get("k_out_feasible"))
    kinds = counts["by_d_kind_d_cells"]
    lines = [
        "# M0 v2.1: M0 v2 revised after the LLM panel review", "",
        f"Data role: **{DATA_ROLE}**. Status: **{STATUS}**.", "",
        f"{counts['n_cells']} cells on {counts['n_structures']} structures (instance 0 of each), a gold solving trace for every "
        "cell, a certificate for every structure. Built by `scripts/v2/s192_build_m0_v21.py` from `src/physmon/benchmark/v2/"
        "roles_m0v21.py` (which reuses the M0 v2 specs for everything it does not change); rebuild with the same command for "
        "identical files (the builder refuses to overwrite). `m0_v2` is unchanged and stays as the record of the review that led "
        "here (`docs/validation/v2/llm_panel/admission_m0v2/`).", "",
        "## What changed against M0 v2, and why (plan revision v2.2, section G)", "",
        "1. **No undone events (G1).** `same_object_undone_event` is withdrawn: a change applied to the target and then reversed "
        "acts on the target and cancels (stratum C), so it is not a disconnected sentence. Pair 1 of every structure is now a "
        "genuine other event of the target object that leaves no state behind (`same_object_other_event`: history in an earlier "
        "experiment, or an event after the stated process, for example a jug emptied into the water after the heating ended). For "
        "S72 only, no honest same-object event exists for an energy quantity, so pair 1 puts the energy on a second co-present "
        "object of a different type (an alpha particle; `other_object_same_scene` with `d_kind_note`). The certificate rejects any D or N "
        "phrasing with a reversal pattern (`again`, `back`, `removed`, `taken out`, `cut out`, `loses`, `lets it ... back`, ...), any "
        "co-present D that names the target, and any same-object D without a time anchor away from the stated situation.",
        "2. **Scene integration (G2).** The co-present object of d0 is introduced by one number-free clause (the scene clause) appended to the base "
        "context of EVERY cell of the structure (no cue, N, R, D, C, K, K_out and supporting), so the pair-0 D sentence refers to "
        "an object that is already in the scene, as R refers to the target. The clause is on every row (`scene_clause`, "
        "`scene_object_rationale`). The base problem is the October problem with the clause before the question and nothing else; "
        "the base gold and every gold of the role cells are unchanged (the builder and the tests check this).",
        "3. **Wording fixes (G4).** S27 r1 (time marker 'Afterwards', same R wiring), S07 K ('broken again' reworded), S13 (the cord is "
        "stated light in every sentence), S55 (the g/mol to kg/mol conversion is stated in the relation listed to the panel), S02 "
        "R0 (no meta-wording) and the S02 quantity label.",
        "4. **Naturalness rewrites.** Every D, N and R sentence was rewritten from the panel's reasons as a plausible part of the "
        "scene; the pair rules hold (same frame, numeral and unit; attachment-only difference except S02 p0 and S26 p0, declared "
        "with reasons; word counts within 3; marker- and consequence-free; value hygiene). C and K sentences are those of M0 v2 "
        "except S07's k0.", "",
        f"D cells by kind: {kinds}. K_out exists for {', '.join(k_out) or 'no structure'} only.", "",
        "## Files", "",
        "As in M0 v2 (`cells.jsonl`, `traces.jsonl`, `certificates.json`, `manifest.json`), with the extra row fields `m0_version`, "
        "`scene_clause`, `scene_object_rationale` and `d_kind_note` (pair-1 D and N rows of a structure whose pair 1 is co-present).",
        "", "## Reading `source_ambiguous`", "",
        f"True on these rows only (by design): {dict(sorted(ambiguous.items()))}.", "",
        "## Counts", "",
        f"By family: {counts['by_family']}. By stratum: {counts['by_stratum']}.", "",
        "Conditions that could not be built (never replaced by a nonsensical prompt; reasons in the certificates): "
        + (", ".join(f"{k} x{v}" for k, v in sorted(inf.items())) or "none") + ".", "",
        "## What has not been done", "",
        "No LLM-panel or human review of M0 v2.1 yet, and no model has seen the cells. Panel packets are built by "
        "`scripts/v2/s193_m0v21_panel_packets.py`.", ""]
    if excluded:
        lines += ["## Excluded structures", "", json.dumps(excluded), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/v2/dataset/m0_v21")
    parser.add_argument("--dataset", default="data/v2/dataset/v1/dataset.jsonl")
    args = parser.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else REPO_ROOT / args.out
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    summary = build(out, REPO_ROOT / args.dataset)
    print(json.dumps({k: summary[k] for k in ("n_cells", "n_structures", "by_family", "by_stratum", "excluded")}, indent=2))
    return 0 if not summary["excluded"] else 1


if __name__ == "__main__":
    sys.exit(main())
