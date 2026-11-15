#!/usr/bin/env python3
"""Stage 15: build the M0 v2 design-validation dataset (`data/v2/dataset/m0_v2/`) from the revised role specs.

M0 v2 replaces the sealed `m0_pilot` wording and values (plan revision v2.2, amendments A2-A9) on the same twelve structures and
the same base instance (instance 0):

* role-by-value cells (`family: role_by_value`): no cue; one non-numeric control N per phrasing pair; R and D at three values in
  two phrasing pairs (co-present D and same-object-other-event D); C and K at three values in two phrasings; K_out where the
  question stays well posed outside the regime;
* supporting cells (`family: supporting`): the October conditions regenerated with certified tolerance status (non-numeric
  sentence, numeric metadata, same-unit value on another object at exact / near-outside-tolerance high and low digit overlap /
  moderate / far, incompatible unit with the gold's digits, convertible unit, relevant edit, role reversal), the relevance
  instruction on no-cue, R and D at the middle value, and the sentence before the context where that reads correctly;
* a gold solving trace for every cell (`traces.jsonl`, keyed by job id and cell id), rendered from the typed graph;
* certificates for every structure, a manifest with counts and file hashes, and a README.

Held-out values are certified but never emitted. The builder is deterministic and refuses to overwrite an existing directory.
Status: agent-authored, solver-certified, NOT yet reviewed by the LLM panel. Data role: EXPLORATION.
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
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m0v2  # noqa: E402
from physmon.benchmark.v2 import supporting_v2 as su  # noqa: E402
from physmon.benchmark.v2 import traces_v2 as t2  # noqa: E402

INSTANCE = 0
STATUS = "agent-authored, solver-certified, NOT yet reviewed by the LLM panel (and not yet reviewed by a human)"
DATA_ROLE = "EXPLORATION"


def v1_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {f"{r['structure_id']}:{r['instance']}": r for r in rows}


def _unit_type(structure, unit: str | None) -> str | None:
    if unit is None:
        return None
    return "same" if dm.UNITS[unit].dim == dm.UNITS[structure.render.target_unit].dim else "different"


def target_terms(structure_id: str) -> dict[str, list[str]]:
    phrases, symbols = roles_m0v2.TARGET_TERMS[structure_id]
    return {"target_phrases": list(phrases), "target_symbols": list(symbols)}


def role_row(cell: r2.Cell, structure, spec: r2.RoleSpecV2, v1: dict[str, Any]) -> dict[str, Any]:
    support = cell.family == "supporting"
    quantity = {"R": spec.quantity_phrase, "D": spec.quantity_phrase, "N": spec.quantity_phrase}.get(cell.stratum)
    if cell.stratum == "C" and spec.cancelling:
        quantity = spec.cancelling.spec.quantity_phrase
    if cell.stratum in ("K", "K_out") and spec.conditional:
        quantity = spec.conditional.spec.quantity_phrase
    base_stratum = cell.stratum
    stratum = "support" if support else cell.stratum
    pair = next((p for p in spec.pairs if p.pair_id == cell.pair_id), None) if cell.stratum in ("R", "D", "N") else None
    pair_info: dict[str, Any] = {"d_rationale": None, "pair_frame_matched": None, "pair_token_difference": None}
    if pair is not None:
        r_sentence = r2.pair_sentence(pair, "R", cell.value, spec.unit)
        d_sentence = r2.pair_sentence(pair, "D", cell.value, spec.unit)
        pair_info = {"d_rationale": pair.d_rationale if cell.stratum in ("D", "N") else None,
                     "pair_frame_matched": pair.frame_matched,
                     "pair_token_difference": r2.token_difference(r_sentence, d_sentence)}
    row = {
        "job_id": f"{structure.structure_id}-i{cell.instance}:{cell.cell_id}", "structure_id": structure.structure_id,
        "instance": cell.instance, "cell_id": cell.cell_id, "family": cell.family, "stratum": stratum,
        "condition": ("instr_relevance" if cell.instruction else "before_context") if support else cell.stratum,
        "base_stratum": base_stratum if support else None, "structure_uuid": dg.structure_uuid(structure),
        "template_cluster_id": v1.get("template_cluster_id", f"V2C-{structure.structure_id}"),
        "symbolic_program_hash": dg.structure_hash(structure), "prompt": cell.prompt,
        "prompt_sha256": hashlib.sha256(cell.prompt.encode("utf-8")).hexdigest(), "gold_value": cell.gold_value,
        "gold_unit": cell.gold_unit, "domain": v1.get("domain", structure.domain), "level": v1.get("level"),
        "cue_semantic_role": base_stratum, "cue_numeric_value": cell.value, "unit_type": _unit_type(structure, cell.unit),
        "numeric_proximity": None, "digit_overlap": None, "cue_position": cell.position if cell.stratum != "none" else None,
        "isolation_condition": None if cell.stratum == "none" else ("marker_free" if cell.marker_free else "marked"),
        "expected_effect": "changes" if cell.stratum in ("R", "K_out") else "invariant", "foils": dict(cell.foils),
        "value_index": cell.value_index, "value": cell.value, "unit": cell.unit, "phrasing_id": cell.phrasing_id,
        "pair_id": cell.pair_id, "d_kind": cell.d_kind, "position": cell.position, "instruction": cell.instruction,
        "instruction_text": r2.INSTRUCTION_RELEVANCE if cell.instruction else None, "sentence": cell.sentence,
        "consequence_free": cell.consequence_free, "marker_free": cell.marker_free,
        "digit_overlap_with_inputs": cell.digit_overlap_with_inputs, "digit_overlap_with_gold": cell.digit_overlap_with_gold,
        "source_ambiguous": cell.source_ambiguous, "cue_equals_gold": False, "placebo": cell.placebo,
        "confounded": list(cell.confounded), "heldout": cell.heldout, "tolerance_status": None,
        "source_ambiguous_by_design": False, "ambiguous_views": [], **pair_info, **target_terms(structure.structure_id),
        "textbook_familiarity": spec.cancelling.familiarity if cell.stratum == "C" and spec.cancelling else None,
        "textbook_familiarity_reason": spec.cancelling.familiarity_reason if cell.stratum == "C" and spec.cancelling else None,
    }
    row["role"] = {"stratum": stratum, "value_index": cell.value_index, "value": cell.value, "unit": cell.unit,
                   "phrasing_id": cell.phrasing_id, "marker_free": cell.marker_free, "placebo": cell.placebo,
                   "confounded": list(cell.confounded), "heldout": cell.heldout, "quantity": quantity,
                   "relevant_wiring": f"{spec.relevant.op}:{spec.relevant.input_name}"}
    return row


def support_row(sup: su.Support, structure, v1: dict[str, Any]) -> dict[str, Any]:
    f = sup.factors
    sentence = sup.sentence
    cue = sup.cue_value
    row = {
        "job_id": f"{structure.structure_id}-i{sup.instance}:S:{sup.cell_id}", "structure_id": structure.structure_id,
        "instance": sup.instance, "cell_id": f"S:{sup.cell_id}", "family": "supporting", "stratum": "support",
        "condition": sup.cell_id, "base_stratum": None, "structure_uuid": dg.structure_uuid(structure),
        "template_cluster_id": v1.get("template_cluster_id", f"V2C-{structure.structure_id}"),
        "symbolic_program_hash": dg.structure_hash(structure), "prompt": sup.prompt,
        "prompt_sha256": hashlib.sha256(sup.prompt.encode("utf-8")).hexdigest(), "gold_value": sup.gold_value,
        "gold_unit": sup.gold_unit, "domain": v1.get("domain", structure.domain), "level": v1.get("level"),
        "cue_semantic_role": f.get("cue_semantic_role"), "cue_numeric_value": cue, "unit_type": f.get("unit_type"),
        "numeric_proximity": f.get("numeric_proximity"), "digit_overlap": f.get("digit_overlap"),
        "cue_position": f.get("cue_position"), "isolation_condition": f.get("isolation_condition"),
        "expected_effect": sup.expected_effect, "foils": dict(sup.foils), "value_index": None, "value": cue,
        "unit": sup.cue_unit, "phrasing_id": None, "pair_id": None, "d_kind": None, "position": "after_context",
        "instruction": None, "instruction_text": None, "sentence": sentence,
        "consequence_free": (not r2.consequence_hits(sentence)) if sentence else None, "marker_free": sup.marker_free,
        "digit_overlap_with_inputs": None, "digit_overlap_with_gold": None, "source_ambiguous": sup.source_ambiguous,
        "cue_equals_gold": sup.cue_equals_gold, "placebo": None, "confounded": [], "heldout": False,
        "tolerance_status": sup.tolerance, "source_ambiguous_by_design": sup.ambiguous_by_design,
        "ambiguous_views": list(sup.ambiguous_views), "d_rationale": None, "pair_frame_matched": None,
        "pair_token_difference": None, "textbook_familiarity": None, "textbook_familiarity_reason": None,
        **target_terms(structure.structure_id),
    }
    if cue is not None and sup.cue_unit is not None and sup.cell_id.startswith("nongov"):
        shown = r2.displayed_inputs(structure, sup.instance)
        row["digit_overlap_with_inputs"] = max(r2.digit_overlap(cue, x) for x in shown.values())
        row["digit_overlap_with_gold"] = r2.digit_overlap(cue, sup.gold_value)
    row["role"] = {"stratum": "support", "value_index": None, "value": cue, "unit": sup.cue_unit, "phrasing_id": None,
                   "marker_free": sup.marker_free, "placebo": None, "confounded": [], "heldout": False, "quantity": None,
                   "relevant_wiring": None}
    return row


def build(out: Path, dataset: Path) -> dict[str, Any]:
    v1 = v1_rows(dataset)
    plans = t2.plans()
    rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    certificates: dict[str, Any] = {}
    excluded, mismatched = [], []
    for sid, spec in sorted(roles_m0v2.ROLE_SPECS.items()):
        structure = roles_m0v2.structure(sid)
        cert = r2.certify_v2(structure, spec)
        base = v1.get(f"{sid}:{INSTANCE}", {})
        record: dict[str, Any] = {"role_certificate": cert, "infeasible": [], "supporting": []}
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
        if base and base.get("problem") != no_cue.prompt:
            mismatched.append(sid)
        plan = plans[sid]
        for cell in [*cells, *extra]:
            if not r2._prompt_numerals_ok(structure, INSTANCE, cell.prompt, cell.value):
                raise SystemExit(f"rendering self-check failed for {sid} {cell.cell_id}")
            row = role_row(cell, structure, spec, base)
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
            if sup.cue_value is not None and sup.cell_id not in ("role_reversal",) and not _support_numerals_ok(structure, sup):
                raise SystemExit(f"rendering self-check failed for {sid} {sup.cell_id}")
            row = support_row(sup, structure, base)
            rows.append(row)
            trace = t2.trace_for_support(structure, plan, sup)
            trace_rows.append({"job_id": row["job_id"], "cell_id": row["cell_id"], "structure_id": sid, "instance": INSTANCE,
                               "family": "supporting", "stratum": "support", "gold_trace": {
                                   **trace, "kind": "solving technique rendered from the typed graph; not model-generated text"}})
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
    (out / "README.md").write_text(readme(counts, certificates, excluded, mismatched, rows), encoding="utf-8")
    manifest = {**counts, "instance": INSTANCE, "excluded": excluded, "no_cue_prompt_differs_from_v1": mismatched,
                "data_role": DATA_ROLE, "status": STATUS,
                "n_infeasible_conditions": sum(len(c["infeasible"]) for c in certificates.values()),
                "k_out_feasible": {sid: c.get("k_out_feasible") for sid, c in sorted(certificates.items())},
                "file_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                for name in ("cells.jsonl", "traces.jsonl", "certificates.json", "README.md")}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _support_numerals_ok(structure, sup: su.Support) -> bool:
    expected = sorted([*[float(dg.input_text(structure, n.name, (sup.input_display or {})[n.name])) for n in structure.inputs],
                       *([float(dg.positional(sup.cue_value, 4 if sup.cell_id in (
                           "nongov_same_unit_exact", "nongov_incompatible_unit_same_digits",
                           "nongov_convertible_unit_same_magnitude") else 3))] if sup.cue_value is not None else [])])
    return dg.prompt_numbers(sup.prompt) == expected


def readme(counts: dict[str, Any], certificates: dict[str, Any], excluded: list, mismatched: list,
           rows: list[dict[str, Any]]) -> str:
    inf = Counter(r["condition"] for c in certificates.values() for r in c["infeasible"])
    n_position = sum(1 for r in rows if r["position"] == "before_context")
    n_position_infeasible = inf.get("before_context", 0)
    ambiguous = Counter(r["condition"] for r in rows if r["source_ambiguous"])
    ambiguous_not_by_design = [r["job_id"] for r in rows if r["source_ambiguous"] and not r["source_ambiguous_by_design"]]
    k_out = sorted(sid for sid, c in certificates.items() if c.get("k_out_feasible"))
    lines = [
        "# M0 v2: the design-validation pilot, revised wording and values", "",
        f"Data role: **{DATA_ROLE}**. Status: **{STATUS}**.", "",
        f"{counts['n_cells']} cells on {counts['n_structures']} structures (instance 0 of each), a gold solving trace for every "
        "cell, and a certificate for every structure. Built by `scripts/v2/s188_build_m0_v2.py` from the specs in "
        "`src/physmon/benchmark/v2/roles_m0v2*.py`; rebuild with the same command to get identical files (the builder refuses "
        "to overwrite).", "",
        "## What this is", "",
        "The same twelve structures and the same base problems as the sealed `m0_pilot`. Each structure gets one extra sentence "
        "that carries a number q in a role: R (the answer must change by a certified amount), D (no physical path to the target, "
        "the answer must not change), C (appears in the governing relations and cancels), K (irrelevant while a regime holds), "
        "or N (the same sentence with no number). `m0_pilot` stays untouched; it already ran on models and is an immutable record.",
        "", "## What changed against `m0_pilot`, and why", "",
        "1. **Wording.** In M0, one R sentence explained its own consequence (\"so it was already moving when the stated distance "
        "began\"), a D sentence was unnatural (\"across the floor of the next room yesterday\"), and every D sentence signalled "
        "irrelevance only by being far away in place or time. Now every quantity has exactly two phrasing pairs. In a pair the R "
        "and D sentences share frame, number and unit and differ in a short attachment phrase (the difference is recorded in "
        "`certificates.json`; word counts differ by at most three). Pair 0 is object style and its D puts the number on another "
        "object in the same scene at the same time (`other_object_same_scene`); pair 1 is event style and its D puts it on the "
        "target object in an event that leaves the problem unchanged: `same_object_other_event` (a different event of the same "
        "object: S02, S20, S92) or `same_object_undone_event` (the change is added and then removed: the other nine). A checked list of "
        "consequence words and an extended list of marker words rule out explanations and giveaway words in every sentence; the "
        "flags `consequence_free` and `marker_free` are on every row. Two pairs (S02 and S26, pair 0) cannot share one frame honestly and are "
        "recorded as `pair_frame_matched: false` with the reason. In the nine `same_object_undone_event` structures the R twin says "
        "\"left there\" and the D twin \"taken out again\"; the three `same_object_other_event` structures use a different event "
        "(a slide along a bench, a rinse). Pair 0 of S26 is also recorded unmatched (the subject and the reference direction differ "
        "as well as the attachment). These are judgements a reviewer should check. Every row also carries `target_phrases` and "
        "`target_symbols` for the H4 trace extractor.",
        "2. **Where the number lies.** No study value equals a displayed input, and none shares two leading digits with an input or "
        "with any answer of its structure (the old R values 5 kOhm, 2 kg, 6 V equalled inputs; 100 eV copied the 100.15 pm answer). "
        "Each row records `digit_overlap_with_inputs` and `digit_overlap_with_gold`. No value, read as a number or as a digit "
        "copy, equals another cell's answer.",
        "3. **Gold traces for every cell** (`traces.jsonl`): R traces include the step where q enters, D and N traces the base trace "
        "plus a line saying the quantity has no path to the target, C traces show q entering the listed relations and cancelling, "
        "K traces check the regime predicate numerically. Each trace ends at the cell's certified answer (tested to 1e-9).",
        "4. **Supporting cells from October** (`family: supporting`), with the proximity conditions now distinct and certified "
        "against the grading code: an exact-match value (the displayed gold), a near value 1.1% to 5% from the gold that all "
        "three grading views mark wrong (with high and with low leading-digit overlap), moderate and far values, the gold's digits "
        "in an incompatible unit, the gold's magnitude in a convertible unit, a non-numeric sentence, numeric metadata, a relevant "
        "edit and a role reversal. The October sentences that state that system B is isolated are kept for these cells, so they "
        "carry marker words (`marker_free: false`) by design; the role-by-value cells carry none.",

        "5. **New supporting cells.** The relevance instruction (\"Some of the information given may not be needed. Identify which "
        "quantities matter before you solve.\") appended after the question for no-cue and for R and D at the middle value in both "
        "pairs (`instruction: relevance`). The sentence-before-context position cells (R and D, middle value, pair 0) exist only "
        f"where the sentence reads correctly ahead of the context: {n_position} built, {n_position_infeasible} recorded as "
        "infeasible (each R sentence refers to entities that the context introduces, or to a change that follows the stated "
        "state; the reason is in each structure's certificate). K_out cells (`stratum: K_out`) exist for "
        f"{', '.join(k_out) or 'no structure'} only: the other conditional quantities would make the question ill posed or "
        "ambiguous in time (reasons in the certificates).",
        "6. **C familiarity.** Every cancelling quantity carries `textbook_familiarity` (famous, standard or uncommon) with a "
        "one-line reason, in `certificates.json` under `c_textbook_familiarity` and on every C row.",
        "7. **Held-out values.** Every R/D, C and K quantity keeps two held-out values in its spec, certified and hygiene-checked "
        "like the study values and never emitted as cells (K_out has none).", "",
        "## Files", "",
        "- `cells.jsonl`: one row per cell. Fields of the October job format (usable by `s170_sampled_run.py plan --cells`) plus "
        "`family`, `stratum`, `condition`, `pair_id`, `d_kind`, `phrasing_id`, `instruction`, `consequence_free`, `marker_free`, "
        "`digit_overlap_with_inputs`, `digit_overlap_with_gold`, `source_ambiguous`, `cue_equals_gold`, `foils`, `placebo`, "
        "`confounded`, `tolerance_status`, `d_rationale` (D and N rows), `pair_token_difference`, `pair_frame_matched`, "
        "`source_ambiguous_by_design`, `ambiguous_views`, `textbook_familiarity` (C rows) and a `role` block as in `m0_pilot`. Supporting rows have `stratum: support` and "
        "`role.stratum: support`, so an analysis that selects R, D, C, K, N by stratum does not pool them.",
        "- `traces.jsonl`: one gold trace per cell (`job_id`, `cell_id`, `gold_trace` with structured steps and text).",
        "- `certificates.json`: per structure, every check with pass or fail, the pair records (token differences, word counts), the "
        "value hygiene, the infeasibility records, K_out and C familiarity.",
        "- `manifest.json`: counts and file hashes.", "",
        "## Reading `source_ambiguous` and `cue_equals_gold`", "",
        "`source_ambiguous` is true when the sentence's own numeral (a role value copied or read in the target unit, or a proximity "
        "cue) lies inside a grading tolerance of the gold, so a correct answer could come from the sentence. In this build it is "
        f"true on these rows only: {dict(sorted(ambiguous.items()))}"
        " (the exact-match cell, graded correct by all three views and carrying `cue_equals_gold: true`, and the convertible-unit "
        "cell, graded correct by the convertible and 1% views; `ambiguous_views` lists which). Both are source-ambiguous by "
        f"design (rows that are ambiguous and not by design: {ambiguous_not_by_design or 'none'}). It is false on every other "
        "row, including all near cells, which are certified wrong under the declared, convertible and 1% views.", "",
        "## Counts", "",
        f"By family: {counts['by_family']}. By stratum: {counts['by_stratum']}.", "",
        "Conditions that could not be built (never replaced by a nonsensical prompt; reasons in the certificates): "
        + (", ".join(f"{k} x{v}" for k, v in sorted(inf.items())) or "none") + ".", "",
        "## What has not been done", "",
        "No LLM-panel or human review of these sentences yet, and no model has seen the cells. Physics judgements for each structure "
        "(why the D event is disconnected, which stated conditions it leaves true, why K_out is or is not well posed) are in the "
        "specs and in `certificates.json` for a reviewer to check.", ""]
    if excluded:
        lines += ["## Excluded structures", "", json.dumps(excluded), ""]
    if mismatched:
        lines += ["## No-cue prompt differs from the October problem", "", ", ".join(mismatched), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/v2/dataset/m0_v2")
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
