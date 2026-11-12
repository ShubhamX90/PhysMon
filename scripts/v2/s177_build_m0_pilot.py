#!/usr/bin/env python3
"""Stage 15: build the M0 design-validation pilot cells from the certified role specs (`benchmark/v2/roles_m0.py`).

For every structure: certify the spec (a structure whose primary certificate fails is excluded and listed); then, on
instance 0 at the after-context position, emit the 14 core cells of the plan of record (no cue; the non-numeric
sentence; R and D at the three study values in two phrasings each) and, where the spec has them, the C and K cells (three
values, two phrasings). Held-out values are not emitted. Rows are in the job format of `s170_sampled_run.py plan --cells`,
with the role metadata (stratum, value index, phrasing, marker-free flag, placebo, confounded pairs) under `role`.

Outputs (refusing to overwrite): <out>/cells.jsonl, <out>/certificates.json, <out>/summary.json.
Also checks that each structure's rendered no-cue prompt equals the v1 dataset problem text of the same instance, so the
pilot's no-cue cells are the problems already calibrated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import roles_m0  # noqa: E402

INSTANCE = 0
POSITION = "after_context"


def v1_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {f"{r['structure_id']}:{r['instance']}": r for r in rows}


def job_row(cell: rv.RoleCell, structure, spec: rv.RoleSpec, v1: dict[str, Any]) -> dict[str, Any]:
    target_dim = dm.UNITS[structure.render.target_unit].dim
    if cell.unit is None:
        unit_type = None
    else:
        unit_type = "same" if dm.UNITS[cell.unit].dim == target_dim else "different"
    if cell.stratum == "none":
        isolation = None
    else:
        isolation = "marker_free" if cell.marker_free else "marked"
    return {
        "job_id": f"{structure.structure_id}-i{cell.instance}:{cell.cell_id}", "structure_id": structure.structure_id,
        "instance": cell.instance, "cell_id": cell.cell_id, "structure_uuid": dg.structure_uuid(structure),
        "template_cluster_id": v1.get("template_cluster_id", f"V2C-{structure.structure_id}"),
        "symbolic_program_hash": dg.structure_hash(structure), "prompt": cell.prompt, "gold_value": cell.gold_value,
        "gold_unit": cell.gold_unit, "domain": v1.get("domain", structure.domain), "level": v1.get("level"),
        "cue_semantic_role": cell.stratum, "cue_numeric_value": cell.value, "unit_type": unit_type,
        "numeric_proximity": None, "digit_overlap": None, "cue_position": cell.position if cell.stratum != "none" else None,
        "isolation_condition": isolation, "expected_effect": "changes" if cell.stratum == "R" else "invariant",
        "foils": cell.foils,
        "role": {"stratum": cell.stratum, "value_index": cell.value_index, "value": cell.value, "unit": cell.unit,
                 "phrasing_id": cell.phrasing_id, "marker_free": cell.marker_free, "placebo": cell.placebo,
                 "confounded": cell.confounded, "heldout": cell.heldout, "quantity": spec.quantity_phrase,
                 "relevant_wiring": f"{spec.relevant.op}:{spec.relevant.input_name}"},
    }


def build(out: Path, dataset: Path) -> dict[str, Any]:
    v1 = v1_rows(dataset)
    rows: list[dict[str, Any]] = []
    certificates: dict[str, Any] = {}
    excluded, mismatched = [], []
    for sid, spec in sorted(roles_m0.ROLE_SPECS.items()):
        structure = roles_m0.structure(sid)
        cert = rv.certify_role_spec(structure, spec)
        certificates[sid] = cert
        if not rv.complete(spec, cert):
            excluded.append({"structure_id": sid, "failed": cert["failed"]})
            continue
        base = v1.get(f"{sid}:{INSTANCE}", {})
        cells = rv.role_cells(structure, spec, INSTANCE, positions=(POSITION,))
        no_cue = next(c for c in cells if c.stratum == "none")
        if base and base.get("problem") != no_cue.prompt:
            mismatched.append(sid)
        for cell in cells:
            if cell.stratum in ("C", "K") and not cert["checks"][{"C": "cancelling", "K": "conditional"}[cell.stratum]]["passed"]:
                continue  # a failed C or K stratum is dropped; the R/D core stays
            if not rv.prompt_value_check(cell):
                raise SystemExit(f"rendering self-check failed for {sid} {cell.cell_id}")
            rows.append(job_row(cell, structure, spec, base))
    ids = [r["job_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate job ids")
    out.mkdir(parents=True, exist_ok=False)
    text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    (out / "cells.jsonl").write_text(text, encoding="utf-8")
    (out / "certificates.json").write_text(json.dumps(certificates, indent=2, sort_keys=True, default=str) + "\n",
                                           encoding="utf-8")
    summary = {"n_cells": len(rows), "n_structures": len({r["structure_id"] for r in rows}), "instance": INSTANCE,
               "position": POSITION, "by_stratum": dict(Counter(r["cue_semantic_role"] for r in rows)),
               "by_structure": dict(Counter(r["structure_id"] for r in rows)), "excluded": excluded,
               "no_cue_prompt_differs_from_v1": mismatched,
               "cells_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
               "data_role": "EXPLORATION", "review": "lead agent only (provisional); LLM panel and user review pending"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/v2/dataset/m0_pilot")
    parser.add_argument("--dataset", default="data/v2/dataset/v1/dataset.jsonl")
    args = parser.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else REPO_ROOT / args.out
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    summary = build(out, REPO_ROOT / args.dataset)
    print(json.dumps(summary, indent=2))
    return 0 if not summary["excluded"] else 1


if __name__ == "__main__":
    sys.exit(main())
