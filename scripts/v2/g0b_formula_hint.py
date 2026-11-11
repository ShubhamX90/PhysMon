#!/usr/bin/env python3
"""G0 item (b): the formula-hint record of Phase I, per family (review check C3, extended).

Reads `results/appendix/formula_leakage/` (five stable families, each rendered as a base prompt and
the same prompt with a correct formula hint, Qwen2.5-7B-Instruct) and records per family:

* the legacy S_lp shift, recomputed from the raw records as L(base) - L(hint) of the bare
  certified string (positive = the hint LOWERED the gold-string log-probability);
* the generated answer under each prompt and whether it is correct, so that "the answer stays /
  becomes correct" (the reviewer's further claim, not checked by C3) is read from the records.

Grading rule (stated here; chosen after seeing the ten generated answers, so it is a
descriptive reading, not a frozen endpoint): the parsed answer's first number must be within a
relative tolerance (default 1e-3) of the certified value and its unit must equal the certified
unit after removing spaces, `*`, `·` and `⋅`. The result is also reported at 1e-2 to show that
it does not depend on the tolerance. Records duplicated across reruns must agree; otherwise the
family is NOT_EVALUATED. A model without its own records is NOT_EVALUATED, never "no effect".

CPU only, read only. Data role EXPLORATION; audit of past artifacts.

Usage:
    python3 scripts/v2/g0b_formula_hint.py --out-dir results/g0/attempt_20261112
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("results/appendix/formula_leakage")
NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
UNIT_DROP = str.maketrans("", "", " *·⋅")


def split_answer(text: str | None) -> tuple[float | None, str]:
    """First number in the text and the unit string after it (normalised)."""

    if not text:
        return None, ""
    match = NUMBER.search(text)
    if match is None:
        return None, ""
    unit = text[match.end():].strip().rstrip(".").translate(UNIT_DROP)
    return float(match.group(0)), unit


def is_correct(parsed: str | None, gold: str, rel_tol: float) -> bool | None:
    """True/False by the stated rule; None when the answer has no number (not gradable)."""

    value, unit = split_answer(parsed)
    gold_value, gold_unit = split_answer(gold)
    if value is None or gold_value is None:
        return None
    close = abs(value - gold_value) <= rel_tol * max(abs(gold_value), 1e-12)
    return close and unit == gold_unit


def transition(base: bool | None, hint: bool | None) -> str:
    if base is None or hint is None:
        return "NOT_EVALUATED"
    return {(True, True): "stays_correct", (False, True): "becomes_correct",
            (True, False): "becomes_wrong", (False, False): "stays_wrong"}[(base, hint)]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, rel_tols: tuple[float, ...] = (1e-3, 1e-2)) -> dict[str, Any]:
    source = root / SOURCE
    summary = json.loads((source / "formula_leakage_summary.json").read_text(encoding="utf-8"))
    baseline = {f["template_id"]: f for f in summary["families"]}
    records = [json.loads(line) for line in
               (source / "behavioural" / "prompt_records.jsonl").read_text(encoding="utf-8").splitlines()
               if line.strip()]
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["model_name"], record["template_id"], int(record["variant_id"]))].append(record)

    run_files = sorted((source / "behavioural").glob("*_primary_*.jsonl"))
    file_info = []
    for path in run_files:
        lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        models = sorted({x.get("model_name") for x in lines if x.get("model_name")})
        file_info.append({"file": path.relative_to(root).as_posix(), "sha256": file_sha256(path),
                          "model_names_inside": models})
    by_hash: dict[str, list[str]] = defaultdict(list)
    for item in file_info:
        by_hash[item["sha256"]].append(item["file"])

    models: dict[str, Any] = {}
    for model_name in sorted({key[0] for key in grouped}):
        families = {}
        for template_id in sorted({key[1] for key in grouped if key[0] == model_name}):
            cells = {variant: grouped[(model_name, template_id, variant)] for variant in (0, 1)}
            entry: dict[str, Any] = {"source_family": baseline.get(template_id, {}).get("source_family"),
                                     "baseline_source_S_lp": baseline.get(template_id, {}).get("baseline_qwen_slp")}
            problems = []
            for variant, rows in cells.items():
                if not rows:
                    problems.append(f"variant {variant} has no record")
                elif len({json.dumps(r, sort_keys=True) for r in rows}) != 1:
                    problems.append(f"variant {variant} has {len(rows)} records that disagree")
            if problems:
                entry.update({"status": "NOT_EVALUATED", "reason": "; ".join(problems)})
                families[template_id] = entry
                continue
            base, hint = cells[0][0], cells[1][0]
            entry.update({
                "status": "EVALUATED",
                "n_duplicate_records_per_cell": len(cells[0]),
                "hint_text": hint.get("cue_value"),
                "gold": base["correct_answer"],
                "logprob_gold_base": base["logprob_correct_answer"],
                "logprob_gold_hint": hint["logprob_correct_answer"],
                "S_lp_shift_base_minus_hint": round(base["logprob_correct_answer"] - hint["logprob_correct_answer"], 6),
                "summary_formula_leakage_slp": baseline.get(template_id, {}).get("formula_leakage_slp"),
                "answer_base": base.get("parsed_answer"),
                "answer_hint": hint.get("parsed_answer"),
            })
            for tol in rel_tols:
                b = is_correct(base.get("parsed_answer"), base["correct_answer"], tol)
                h = is_correct(hint.get("parsed_answer"), hint["correct_answer"], tol)
                entry[f"correct_base@{tol:g}"] = b
                entry[f"correct_hint@{tol:g}"] = h
                entry[f"transition@{tol:g}"] = transition(b, h)
            families[template_id] = entry
        evaluated = [f for f in families.values() if f["status"] == "EVALUATED"]
        counts = {}
        for tol in rel_tols:
            key = f"transition@{tol:g}"
            counts[key] = {name: sum(1 for f in evaluated if f[key] == name)
                           for name in ("stays_correct", "becomes_correct", "becomes_wrong", "stays_wrong",
                                        "NOT_EVALUATED")}
        shifts = [f["S_lp_shift_base_minus_hint"] for f in evaluated]
        models[model_name] = {
            "families": families,
            "n_families_evaluated": len(evaluated),
            "S_lp_shift_range": [min(shifts), max(shifts)] if shifts else None,
            "label_fires_at_0.5": sum(1 for s in shifts if s >= 0.5),
            "transition_counts": counts,
        }

    expected_models = {"Qwen/Qwen2.5-7B-Instruct": "qwen", "meta-llama/Llama-3.1-8B-Instruct": "llama"}
    not_evaluated_models = {}
    for name, short in sorted(expected_models.items()):
        if name in models:
            continue
        reason = "no records with this model_name in prompt_records.jsonl"
        for item in file_info:
            if short in Path(item["file"]).name.lower() and name not in item["model_names_inside"]:
                twins = [f for f in by_hash[item["sha256"]] if f != item["file"]]
                reason += (f"; {item['file']} holds only {item['model_names_inside']}"
                           + (f" and is byte-identical to {twins}" if twins else ""))
        not_evaluated_models[name] = reason
    return {
        "source": SOURCE.as_posix(),
        "grading_rule": "first number within relative tolerance of the certified value and unit equal after "
                        "removing spaces, '*', '·', '⋅'; chosen after seeing the answers (descriptive)",
        "run_files": file_info,
        "identical_run_files": [files for files in by_hash.values() if len(files) > 1],
        "models": models,
        "models_NOT_EVALUATED": not_evaluated_models,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = ["# G0 (b): formula-hint record (Phase I, five stable families)", "",
             "Data role EXPLORATION; audit of committed Phase-I records. `S_lp shift` = L(base) - L(hint) of the "
             "bare certified string, so a positive value means the correct formula hint LOWERED the gold-string "
             "log-probability and the legacy label fires at >= 0.5.", "",
             "| Model | Family | S_lp shift | Answer (base) | Answer (hint) | Gold | Transition (1e-3) | (1e-2) |",
             "|---|---|---|---|---|---|---|---|"]
    for model, block in report["models"].items():
        for family, f in block["families"].items():
            if f["status"] != "EVALUATED":
                lines.append(f"| {model} | {family} | NOT_EVALUATED: {f['reason']} | | | | | |")
                continue
            lines.append(f"| {model} | {family} | {f['S_lp_shift_base_minus_hint']:.3f} | {f['answer_base']} | "
                         f"{f['answer_hint']} | {f['gold']} | {f['transition@0.001']} | {f['transition@0.01']} |")
    for model, reason in report["models_NOT_EVALUATED"].items():
        lines.append(f"| {model} | all | NOT_EVALUATED: {reason} | | | | | |")
    lines += ["", f"Grading rule: {report['grading_rule']}.",
              f"Identical run files: {report['identical_run_files']}."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    report = run(args.root)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "g0b_formula_hint.json").write_text(json.dumps(report, indent=2, sort_keys=True,
                                                                   ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(report, args.out_dir / "g0b_formula_hint.md")
    for model, block in report["models"].items():
        print(f"{model}: shifts {block['S_lp_shift_range']}, label fires {block['label_fires_at_0.5']}, "
              f"transitions {block['transition_counts']}")
    for model, reason in report["models_NOT_EVALUATED"].items():
        print(f"{model}: NOT_EVALUATED ({reason})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
