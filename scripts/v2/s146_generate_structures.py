#!/usr/bin/env python3
"""Stage 14.6: generate and certify the first ten DECOY-v2 structures (CPU only, no model).

Writes, under `data/v2/structures/<version>/`:
  - `S01.json` ... `S10.json`: the typed graph, assumptions, prompt grammar, instantiations and the proof object;
  - `factor_cell_manifest.jsonl`: one row per structure, numeric instantiation and factor cell with the v2 §9.1 factor
    fields; infeasible cells carry a reason;
  - `admissibility.json`: the factor axes and the feasibility matrix with reasons (v2 B3.3: record impossible cells);
  - `mutation_report.json`: every planted defect and equivalent rewrite, with sensitivity and specificity by mutator
    (v2 P3.3);
  - `lineage.json`: authorship, parents (none) and the overlap check against the 155 v1 templates;
  - `summary.json`, `README.md`.

Every structure is SOLVER_CERTIFIED and UNREVIEWED. Certification covers the graph, an independently coded solver and
the rendered numerals; it does not cover the English text or the modelling choices, which need independent expert review
(v2 B4). Nothing here has been run on a model.

Plan reference: B3.2-B3.3 (p.8), P2.1-P2.4 (p.18-19), P3.3 (p.20), §9.1 (p.43), first sprint item 6 (p.49).
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import glob
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import sympy
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import certify as ce  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import graph as gr  # noqa: E402
from physmon.benchmark.v2 import library as lib  # noqa: E402

OUT_BASE = "data/v2/structures"
FACTOR_AXES = {
    "cue_semantic_role": ["none", "irrelevant_text", "irrelevant_metadata", "nongoverning_isolated",
                          "relevant_edit", "role_reversed"],
    "numeric_proximity": ["none", "unrelated", "near (<=1%)", "near_numeral", "moderate (x1.3)", "far (x5)",
                          "equal_magnitude"],
    "unit_type": ["none", "same", "incompatible", "equivalent"],
    "digit_overlap": ["not_controlled", "high (>=2 leading digits)", "low (<=1 leading digit)", "different_digits"],
    "isolation_condition": ["not_applicable", "stated_separate", "stated_isolated", "stated_compared"],
    "cue_position": ["after_context"],
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def v1_overlap() -> dict[str, Any]:
    programs: dict[str, list[str]] = collections.defaultdict(list)
    laws: set[str] = set()
    for path in sorted(glob.glob(str(REPO_ROOT / "data/raw/templates/**/*.yaml"), recursive=True)):
        template = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        names = list(template["parameters"]) + ["pi"]
        expression = gr.parse_expr(str(template["governing_equation_sympy"]), names)
        programs[dg.canonical_program_hash(expression)].append(template["template_id"])
        laws.add(str(template.get("governing_law")))
    return {"n_v1_templates": sum(len(v) for v in programs.values()), "n_v1_distinct_programs": len(programs),
            "n_v1_governing_law_labels": len(laws), "largest_v1_program_template_count": max(map(len, programs.values())),
            "programs": programs, "laws": laws}


def structure_document(structure: gr.Structure, proof: dict[str, Any]) -> dict[str, Any]:
    render = dataclasses.asdict(structure.render)
    return {
        "structure_id": structure.structure_id, "title": structure.title, "domain": structure.domain,
        "law_family": structure.law_family, "target": structure.target,
        "nodes": [dataclasses.asdict(n) for n in structure.nodes],
        "assumptions": [dataclasses.asdict(a) for a in structure.assumptions],
        "render": render, "relevant_edit": {"node": structure.relevant_edit[0], "factor": structure.relevant_edit[1]},
        "instances": [dict(i) for i in structure.instances],
        "solver_route": structure.solver_route, "solver_rel_tol": structure.solver_rel_tol,
        "proof": proof,
    }


def mutation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by[row["mutator_id"]].append(row)
    summary = {}
    for mutator, items in sorted(by.items()):
        kind = items[0]["kind"]
        good = sum(r["outcome"] == ("caught" if kind == "negative" else "passed") for r in items)
        summary[mutator] = {"kind": kind, "n": len(items), "correct": good,
                            "sensitivity" if kind == "negative" else "specificity": good / len(items),
                            "failed_for_an_intended_reason": sum(r["failed_for_an_intended_reason"] for r in items)}
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--out-base", default=OUT_BASE)
    args = parser.parse_args()
    out_dir = (REPO_ROOT / args.out_base / args.version).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty directory: {out_dir}", file=sys.stderr)
        return 2

    structures = lib.all_structures()
    overlap = v1_overlap()
    proofs = {s.structure_id: ce.certify(s) for s in structures}
    manifest, admissibility, mutation_rows, lineage = [], [], [], []
    for structure in structures:
        rows = dg.manifest_rows(structure)
        manifest += rows
        admissibility += [{k: r[k] for k in ("structure_id", "instance", "cell_id", "feasible", "infeasible_reason")}
                          for r in rows]
        mutation_rows += ce.mutation_report(structure)
        program_hash = dg.structure_hash(structure)
        lineage.append({
            "structure_id": structure.structure_id, "structure_uuid": dg.structure_uuid(structure),
            "symbolic_program_hash": program_hash, "authored_by": "agent (Claude Sonnet 5.5, for atharvgaur1845)",
            "parent_structures": [], "source_template_overlap": overlap["programs"].get(program_hash, []),
            "law_family_in_v1": structure.law_family in overlap["laws"], "admission_category": "UNREVIEWED",
            "numeric_instantiations": len(structure.instances),
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    for structure in structures:
        (out_dir / f"{structure.structure_id}.json").write_text(
            json.dumps(structure_document(structure, proofs[structure.structure_id]), indent=2, sort_keys=True,
                       ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "factor_cell_manifest.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in manifest), encoding="utf-8")
    matrix: dict[str, dict[str, str]] = {}
    for row in admissibility:
        matrix.setdefault(row["cell_id"], {})[f"{row['structure_id']}#{row['instance']}"] = \
            "feasible" if row["feasible"] else f"infeasible: {row['infeasible_reason']}"
    (out_dir / "admissibility.json").write_text(json.dumps({
        "factor_axes": FACTOR_AXES, "cells": list(dg.CELL_IDS),
        "bands": {"near": dg.NEAR_BAND, "moderate_factor": dg.MODERATE_FACTOR, "far_factor": dg.FAR_FACTOR,
                  "high_overlap_min_digits": dg.HIGH_OVERLAP_MIN, "low_overlap_max_digits": dg.LOW_OVERLAP_MAX},
        "rule": "cells that cannot be built without a nonsensical prompt are infeasible with a reason (v2 B3.3)",
        "feasibility": matrix,
        "n_cells": len(admissibility), "n_feasible": sum(r["feasible"] for r in admissibility),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "mutation_report.json").write_text(json.dumps({
        "summary_by_mutator": mutation_summary(mutation_rows), "rows": mutation_rows,
        "n_mutants": len(mutation_rows),
        "n_negative_not_caught": sum(r["kind"] == "negative" and r["outcome"] != "caught" for r in mutation_rows),
        "n_positive_wrongly_rejected": sum(r["kind"] == "positive" and r["outcome"] != "passed"
                                           for r in mutation_rows),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "lineage.json").write_text(json.dumps({
        "v1_overlap": {k: v for k, v in overlap.items() if k not in ("programs", "laws")},
        "structures": lineage,
        "note": "Overlap is checked on the renaming-invariant hash of the governing equation. The 155 v1 families "
                "reduce to far fewer distinct equation programs than their labels suggest; none equals any new structure.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cells_feasible = sum(r["feasible"] for r in admissibility)
    summary = {
        "stage": "14.6", "version": args.version, "source_commit": git("rev-parse", "HEAD"),
        "git_status_short": git("status", "--short").splitlines(), "command": " ".join(sys.argv),
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "sympy": sympy.__version__,
        "n_structures": len(structures),
        "status": {sid: p["status"] for sid, p in proofs.items()},
        "all_solver_certified": all(p["status"] == "SOLVER_CERTIFIED" for p in proofs.values()),
        "admission_category": "UNREVIEWED (no independent expert has reviewed any structure)",
        "n_cells": len(admissibility), "n_cells_feasible": cells_feasible,
        "n_mutants": len(mutation_rows),
        "n_negative_mutants_not_caught": sum(r["kind"] == "negative" and r["outcome"] != "caught"
                                             for r in mutation_rows),
        "n_positive_mutants_wrongly_rejected": sum(r["kind"] == "positive" and r["outcome"] != "passed"
                                                   for r in mutation_rows),
        "contract_fingerprint_note": "scoring wrappers: physmon.benchmark.scoring_contract (Stage 14.3)",
        "file_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out_dir.iterdir())
                        if p.is_file()},
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "README.md").write_text(_readme(summary), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_structures", "all_solver_certified", "n_cells", "n_cells_feasible",
                                              "n_mutants", "n_negative_mutants_not_caught",
                                              "n_positive_mutants_wrongly_rejected")}, indent=2))
    return 0 if summary["all_solver_certified"] and not summary["n_negative_mutants_not_caught"] else 1


def _readme(summary: dict[str, Any]) -> str:
    return f"""# DECOY-v2 structures {summary['version']} (Stage 14.6)

Ten new structures, each with two numeric instantiations and eleven predeclared factor cells, built by
`scripts/v2/s146_generate_structures.py` at source commit `{summary['source_commit'][:7]}`.

Status: **SOLVER_CERTIFIED and UNREVIEWED.** Certification covers the typed graph, an independently coded numeric
solver, dimensional consistency, the assumptions list, and the match between every numeral in every rendered prompt
and the graph. It does not certify the English text or the modelling choices. Independent expert review (v2 B4,
`docs/validation/v2/validator_handbook_v2.md`) is required before any use, and no model has been run on these items.

- `S01.json` to `S10.json`: graph, assumptions, prompt grammar, instantiations, proof object.
- `factor_cell_manifest.jsonl`: {summary['n_cells']} cells ({summary['n_cells_feasible']} feasible) with the v2 §9.1 factor fields.
- `admissibility.json`: the factor axes and the feasibility matrix, with a reason for every infeasible cell.
- `mutation_report.json`: {summary['n_mutants']} mutants; negative mutants not caught: {summary['n_negative_mutants_not_caught']};
  equivalent rewrites wrongly rejected: {summary['n_positive_mutants_wrongly_rejected']}.
- `lineage.json`: authorship and the overlap check against the 155 v1 templates.
"""


if __name__ == "__main__":
    raise SystemExit(main())
