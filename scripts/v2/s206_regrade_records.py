#!/usr/bin/env python3
"""Re-grade stored Stage 15 records under grader version v2 (amendment A2, docs/registry/v2/g1/freeze/amendments.md).

CPU only. Reads a `raw_records.jsonl` written by `s170_sampled_run.py` and the cells file, recomputes every grading view and
`correctness` from the record's stored parsed answer and its gold, and writes a NEW file (default
`<dir>/raw_records_grader_v2.jsonl`; it refuses to overwrite). The input is never modified. The parse status is never changed.

The stored parsed answer holds the value and unit but older records not the number as printed, which the rounding test needs.
The printed text is therefore read back with the contract parser from `generated_answer_raw`, and the result is ASSERTED to equal
the stored value, unit and completion status (a record where it does not is reported as a mismatch, never silently used).

Checks, reported rather than hidden: recomputed v1 equals the stored `grade_declared`; recomputed rel1pct equals the stored one;
no declared correct->wrong transition. On any failed check no output file is written and the exit code is 3.

  PYTHONNOUSERSITE=1 PYTHONPATH=src python scripts/v2/s206_regrade_records.py --records RAW.jsonl --cells CELLS.jsonl
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from physmon.benchmark import reasoning_contract_v2 as rc2  # noqa: E402
from physmon.scoring import grading_views as gv  # noqa: E402
from physmon.scoring import unit_convertible as uc  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402

VIEW_FIELDS = {"declared": "grade_declared", "declared_v1": "grade_declared_v1", "convertible": "grade_convertible",
               "rel1pct": "grade_rel1pct"}
RULE = "declared (grader v2, amendment A2)"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stored_parse(record: dict[str, Any]) -> tuple[vs.ParsedOutput, str | None]:
    """The record's parsed answer as a ParsedOutput, with the printed text; (parse, error) where error means a mismatch."""

    pa = record["parsed_answer"]
    text = pa.get("value_text")
    if text is None:  # older records: read the printed text back and require it to agree with what was stored
        completion = rc2.assess(record["generated_answer_raw"], hit_token_limit=bool(record["hit_token_limit"]),
                                thinking_expected=record.get("thinking_mode") == "on")
        p = completion.parsed
        if completion.status != "COMPLETE" or p.status != "PARSED" or p.value != pa["value"] or p.unit != pa["unit"]:
            return vs.ParsedOutput("PARSED", pa["value"], pa["unit"], repr(pa["value"])), "reparse_disagrees_with_stored_parse"
        text = p.value_text
    return vs.ParsedOutput("PARSED", pa["value"], pa["unit"], text), None


def regrade_record(record: dict[str, Any], gold_value: float, gold_unit: str, source_sha: str, problems: list[dict[str, Any]],
                   transitions: dict[str, collections.Counter]) -> dict[str, Any]:
    new = dict(record)
    new["grader_version"] = gv.GRADER_VERSION
    new["regraded_from_sha256"] = source_sha
    if record.get("status") != "OK" or record.get("completion_status") != "COMPLETE" or not record.get("parsed_answer"):
        new["grade_declared_v1"] = record.get("grade_declared")  # nothing to compare: the status stands
        return new
    parsed, error = stored_parse(record)
    if error:
        problems.append({"job_id": record["job_id"], "problem": error})
    views = gv.grade_all(parsed, gold_value, gold_unit)
    old_convertible = uc.classify_convertible(parsed, gold_value, gold_unit)
    checks = {"v1_equals_stored_grade_declared": views["declared_v1"] == record["grade_declared"],
              "rel1pct_equals_stored": views["rel1pct"] == record["grade_rel1pct"],
              "v1_convertible_equals_stored": old_convertible == record["grade_convertible"]}
    for name, ok in checks.items():
        if not ok:
            problems.append({"job_id": record["job_id"], "problem": name, "stored_declared": record["grade_declared"],
                             "recomputed_v1": views["declared_v1"], "value_text": parsed.value_text})
    old = {"declared": record["grade_declared"], "declared_v1": record["grade_declared"],
           "convertible": record["grade_convertible"], "rel1pct": record["grade_rel1pct"]}
    for view in VIEW_FIELDS:
        transitions[view][(old[view], views[view])] += 1
        new[VIEW_FIELDS[view]] = views[view]
    new["correctness"] = views["declared"]
    new["correctness_rule"] = RULE
    new["o2_semantic_correct"] = views["convertible"]  # COMPLETE records: the O2 reading is the contract reading
    return new


def summarise(transitions: dict[str, collections.Counter]) -> dict[str, Any]:
    out = {}
    for view, counter in transitions.items():
        out[view] = {"wrong_to_correct": counter[("wrong", "correct")], "correct_to_wrong": counter[("correct", "wrong")],
                     "unchanged_correct": counter[("correct", "correct")], "unchanged_wrong": counter[("wrong", "wrong")]}
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None, help="default: raw_records_grader_v2.jsonl beside the input")
    args = parser.parse_args(argv)
    out = args.out or args.records.with_name("raw_records_grader_v2.jsonl")
    if out.exists():
        print(f"refusing to overwrite {out}", file=sys.stderr)
        return 2
    cells = {}
    with open(args.cells) as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                cells[row["job_id"]] = (float(row["gold_value"]), row["gold_unit"])
    source_sha = sha256_file(args.records)
    problems: list[dict[str, Any]] = []
    transitions: dict[str, collections.Counter] = {v: collections.Counter() for v in VIEW_FIELDS}
    new_rows, n_not_regraded = [], 0
    with open(args.records) as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            key = record["job_id"].rsplit(":s", 1)[0]
            if key not in cells:
                problems.append({"job_id": record["job_id"], "problem": "cell_not_in_cells_file"})
                new_rows.append(record)
                continue
            gold_value, gold_unit = cells[key]
            if "gold_value" in record and (float(record["gold_value"]) != gold_value or record.get("gold_unit") != gold_unit):
                problems.append({"job_id": record["job_id"], "problem": "gold_differs_from_cells_file"})
            row = regrade_record(record, gold_value, gold_unit, source_sha, problems, transitions)
            n_not_regraded += "correctness_rule" not in row or row["correctness_rule"] != RULE
            new_rows.append(row)
    summary = {"input": str(args.records), "input_sha256": source_sha, "output": str(out), "grader_version": gv.GRADER_VERSION,
               "n_records": len(new_rows), "n_records_kept_as_is_non_complete": n_not_regraded,
               "transitions": summarise(transitions), "n_problems": len(problems), "problems": problems[:20]}
    summary["declared_correct_to_wrong_is_zero"] = summary["transitions"]["declared"]["correct_to_wrong"] == 0
    ok = not problems and summary["declared_correct_to_wrong_is_zero"]
    if ok:
        with open(out, "x") as handle:
            for row in new_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    else:
        summary["output"] = None
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
