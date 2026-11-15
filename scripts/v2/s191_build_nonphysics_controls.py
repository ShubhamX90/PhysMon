#!/usr/bin/env python3
"""Stage 15: build the non-physics dependency control set (`data/v2/dataset/nonphysics_v1/`).

Plan of record v2.2 ("Supporting conditions") and G1 decision 18: sixteen everyday word problems (no physics) carrying the same R/D role
manipulation as M0 v2, at three values in two phrasing pairs: 16 structures x (no cue + 2 N + 6 R + 6 D) = 240 cells, a gold trace for
every cell, a certificate for every structure. Explicitly not powered: a null result on this set is INCONCLUSIVE. The builder is
deterministic and refuses to overwrite an existing directory. Status: agent-authored, solver-certified, NOT yet reviewed by the LLM
panel. Data role: EXPLORATION (G3).
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

from physmon.benchmark.v2 import nonphysics as npx  # noqa: E402
from physmon.benchmark.v2 import nonphysics_specs as sp  # noqa: E402
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402

STATUS = "agent-authored, solver-certified, NOT yet reviewed by the LLM panel (and not yet reviewed by a human)"
DATA_ROLE = "EXPLORATION"


def row_for(cell: r2.Cell, structure: npx.NPStructure, spec: npx.NPSpec) -> dict[str, Any]:
    base_stratum = cell.stratum
    pair = next((p for p in spec.pairs if p.pair_id == cell.pair_id), None) if base_stratum in ("R", "D", "N") else None
    pair_info: dict[str, Any] = {"d_rationale": None, "pair_frame_matched": None, "pair_token_difference": None}
    if pair is not None:
        r_sentence = r2.pair_sentence(pair, "R", spec.values[0], spec.unit)
        d_sentence = r2.pair_sentence(pair, "D", spec.values[0], spec.unit)
        pair_info = {"d_rationale": pair.d_rationale if base_stratum in ("D", "N") else None,
                     "pair_frame_matched": pair.frame_matched,
                     "pair_token_difference": r2.token_difference(r_sentence, d_sentence)}
    quantity = spec.quantity_phrase if base_stratum in ("R", "D", "N") else None
    unit_type = None if cell.unit is None else ("same" if cell.unit == structure.target_unit else "different")
    row = {
        "job_id": f"{structure.structure_id}-i{cell.instance}:{cell.cell_id}", "structure_id": structure.structure_id,
        "instance": cell.instance, "cell_id": cell.cell_id, "family": cell.family, "stratum": cell.stratum,
        "condition": cell.stratum, "base_stratum": None, "structure_uuid": npx.structure_uuid(structure),
        "template_cluster_id": f"NPC-{structure.structure_id}", "symbolic_program_hash": npx.structure_hash(structure),
        "prompt": cell.prompt, "prompt_sha256": hashlib.sha256(cell.prompt.encode("utf-8")).hexdigest(),
        "gold_value": cell.gold_value, "gold_unit": cell.gold_unit, "domain": "nonphysics", "level": npx.LEVEL,
        "theme": structure.theme, "cue_semantic_role": base_stratum, "cue_numeric_value": cell.value, "unit_type": unit_type,
        "numeric_proximity": None, "digit_overlap": None, "cue_position": cell.position if base_stratum != "none" else None,
        "isolation_condition": None if base_stratum == "none" else ("marker_free" if cell.marker_free else "marked"),
        "expected_effect": "changes" if base_stratum == "R" else "invariant", "foils": dict(cell.foils),
        "value_index": cell.value_index, "value": cell.value, "unit": cell.unit, "phrasing_id": cell.phrasing_id,
        "pair_id": cell.pair_id, "d_kind": cell.d_kind, "position": cell.position, "instruction": None, "instruction_text": None,
        "sentence": cell.sentence, "consequence_free": cell.consequence_free, "marker_free": cell.marker_free,
        "digit_overlap_with_inputs": cell.digit_overlap_with_inputs, "digit_overlap_with_gold": cell.digit_overlap_with_gold,
        "source_ambiguous": cell.source_ambiguous, "cue_equals_gold": False, "placebo": cell.placebo,
        "confounded": list(cell.confounded), "heldout": cell.heldout, "tolerance_status": None,
        "source_ambiguous_by_design": False, "ambiguous_views": [], **pair_info,
        "target_phrases": list(structure.target_phrases), "target_symbols": list(structure.target_symbols),
        "textbook_familiarity": None, "textbook_familiarity_reason": None,
    }
    row["role"] = {"stratum": cell.stratum, "value_index": cell.value_index, "value": cell.value, "unit": cell.unit,
                   "phrasing_id": cell.phrasing_id, "marker_free": cell.marker_free, "placebo": cell.placebo,
                   "confounded": list(cell.confounded), "heldout": cell.heldout, "quantity": quantity,
                   "relevant_wiring": f"{spec.wiring.op}:{spec.wiring.input_name}"}
    return row


def build(out: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    certificates: dict[str, Any] = {}
    excluded = []
    for sid in sorted(sp.STRUCTURES):
        structure, spec = sp.STRUCTURES[sid], sp.SPECS[sid]
        cert = npx.certify(structure, spec)
        certificates[sid] = {
            "certificate": cert, "title": structure.title, "theme": structure.theme, "base_problem": npx.assemble(structure, ""),
            "relations": [{"node": n.name, "expr": n.expr, "unit": n.unit} for n in structure.nodes],
            "solver_route": structure.solver_route,
            "wiring": {"input": spec.wiring.input_name, "op": spec.wiring.op, "rationale": spec.wiring.rationale,
                       "q_unit": spec.unit},
            "study_values": list(spec.values), "heldout_values": list(spec.heldout_values), "notes": spec.notes}
        if not cert["passed"]:
            excluded.append({"structure_id": sid, "failed": cert["failed"]})
            continue
        for cell in npx.cells(structure, spec):
            if not npx.prompt_numerals_ok(structure, cell.prompt, cell.value):
                raise SystemExit(f"rendering self-check failed for {sid} {cell.cell_id}")
            row = row_for(cell, structure, spec)
            rows.append(row)
            trace = npx.trace_for_cell(structure, spec, cell)
            trace_rows.append({"job_id": row["job_id"], "cell_id": cell.cell_id, "structure_id": sid, "instance": npx.INSTANCE,
                               "family": cell.family, "stratum": cell.stratum, "gold_trace": {
                                   **trace, "kind": "solving technique rendered from the typed graph and the cell's wiring; "
                                                    "not model-generated text"}})
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
              "by_stratum": dict(sorted(Counter(r["stratum"] for r in rows).items())),
              "by_structure": dict(sorted(Counter(r["structure_id"] for r in rows).items())),
              "by_d_kind_d_cells": dict(sorted(Counter(r["d_kind"] for r in rows if r["stratum"] == "D").items())),
              "by_wiring_op": dict(sorted(Counter(spec.wiring.op for spec in sp.SPECS.values()).items()))}
    (out / "README.md").write_text(readme(counts, excluded), encoding="utf-8")
    manifest = {**counts, "instance": npx.INSTANCE, "excluded": excluded, "data_role": DATA_ROLE, "status": STATUS,
                "powered": False, "null_result_reading": "INCONCLUSIVE (G1 decision 18)",
                "file_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                for name in ("cells.jsonl", "traces.jsonl", "certificates.json", "README.md")}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def readme(counts: dict[str, Any], excluded: list) -> str:
    lines = [
        "# Non-physics dependency control set, version 1", "",
        f"Data role: **{DATA_ROLE}** (G3). Status: **{STATUS}**.", "",
        f"{counts['n_cells']} cells on {counts['n_structures']} structures, a gold solving trace for every cell, and a certificate "
        "for every structure. Built by `scripts/v2/s191_build_nonphysics_controls.py` from `src/physmon/benchmark/v2/nonphysics.py` "
        "and `nonphysics_specs.py`; rebuild with the same command to get identical files (the builder refuses to overwrite).", "",
        "## What this is", "",
        "The plan of record (v2.2, \"Supporting conditions\") asks for a small non-physics dependency control, GSM-DC-style word "
        "problems with the same role manipulation as the physics set, \"to tell a general numeric or dependency phenomenon from one that "
        "needs physical semantics\". G1 decision 18 fixes its size: 16 structures, R and D at 3 values in 2 phrasings. **It is "
        "explicitly not powered: a null result on this set is INCONCLUSIVE**, not evidence of absence.", "",
        "Each structure is an everyday problem with no physics in it (shopping, recipes, school and class counts, savings, tickets and "
        "seats, inventory, sharing, work schedules, league points, library books, garden rows, a school timetable, minibuses, print "
        "jobs; only counts, dollars and whole minutes), a small typed dependency graph of 2 to 4 relations with exact arithmetic, and "
        "an answer in a unit word. One extra sentence carries a number q:", "",
        "- **R** (relevant): q enters one input of the graph (add, subtract, replace or scale) and the answer changes by a certified "
        "amount; the wiring and the reason are in `certificates.json`.",
        "- **D** (disconnected): the same sentence frame, numeral and unit with a short attachment phrase that gives q no path to the "
        "answer. Pair 0 puts q on another person, shop, class or group that is already in the scene (introduced by one clause in the base "
        "text of every cell of the structure, no number): `other_object_same_scene`. Pair 1 puts q on the same object in another event "
        "that leaves no state behind (history before the stated situation): `same_object_other_event`. A change that is made and then "
        "reversed is cancellation and is not used (plan revision v2.2, G1 and G2).",
        "- **N**: the D sentence with no number (one per pair), and the no-cue problem.", "",
        "The rules are those of M0 v2 and the code imports them from `rolevalue_v2.py` (consequence and marker lexicons, remoteness list, "
        "pair matching with word counts within three, token differences, digit overlap), with the numerical machinery rewritten for exact "
        "arithmetic because the physics graph is tied to SI dimensions: study values equal no displayed numeral and share at most one "
        "leading digit with any input or answer; every R and D answer is exact, positive and, where the unit is a count, a whole number "
        "in every intermediate step; R answers are separated from D answers and from each other by more than 1%; misuse foils (copy or "
        "digit copy, replace, add, subtract on every input of q's unit) and the placebo are computed as in `rolevalue.py`, "
        "with confounded pairs recorded and foils that are algebraically the wired computation dropped and listed; no prompt uses a "
        "word from a small physics lexicon. Two held-out values per structure are certified and never emitted.", "",
        "## Files", "",
        "- `cells.jsonl`: one row per cell, the fields of `data/v2/dataset/m0_v2/cells.jsonl` that apply plus `domain: \"nonphysics\"` and "
        "`theme`; `target_phrases` and `target_symbols` for the H4 trace extractor (count units are not in the extractor's unit "
        "registry, so statements of the target are read through the naming chains those fields provide).",
        "- `traces.jsonl`: one gold trace per cell, ending at the cell's gold (tested to 1e-9).",
        "- `certificates.json`: per structure the base problem, relations, wiring, values and every check.",
        "- `manifest.json`: counts and file hashes.", "",
        "## Counts", "", f"By stratum: {counts['by_stratum']}. D kinds: {counts['by_d_kind_d_cells']}. Wiring operations: "
        f"{counts['by_wiring_op']}.", "",
        "## What has not been done", "",
        "No LLM-panel or human review, and no model has seen the cells. Naturalness of the D and N sentences is the known weak point of "
        "this design (plan revision G3) and has not been rated. No grading dry run has been done with the registry units "
        "(dollars, cookies and so on are outside the unit registry).", ""]
    if excluded:
        lines += ["## Excluded structures", "", json.dumps(excluded), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/v2/dataset/nonphysics_v1")
    args = parser.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else REPO_ROOT / args.out
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    summary = build(out)
    print(json.dumps({k: summary[k] for k in ("n_cells", "n_structures", "by_stratum", "excluded")}, indent=2))
    return 0 if not summary["excluded"] else 1


if __name__ == "__main__":
    sys.exit(main())
