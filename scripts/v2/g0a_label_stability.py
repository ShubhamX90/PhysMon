#!/usr/bin/env python3
"""G0 item (a): cross-instruction stability of the legacy S_lp label on the 30 pilot families.

Extends review check C2b (`scripts/reviews/check_iclr2027_review_claims.py`, Qwen only) to both
Phase-I models. For each model it compares the 30 pilot families' legacy `S_lp` between runs that
score the same problem texts under different prompting regimes, and, as a control, between two
runs under the same regime:

* `stage4_original`  - first Stage 4 run (`results/stage4/...`, commit 31a7857);
* `stage4_repair`    - the run the 0.5-nat threshold was registered on (commit 953c31e);
* `stage6_panel`     - the Phase-I panel run (`results/stage6/behavioural_full_rerun`, commit
  ffeeeff), whose runner sends the one-line "Answer: [value] [unit]" system prompt;
* `stage6_d1`        - the phase-D1 run (`results/stage6/behavioural`, commit 0894353), same
  runner and system prompt as the panel run (same-regime control; it covers only some of the
  pilot families).

Per pair and model: n, Spearman rank correlation, label agreement at 0.5 nats, positives in each
run, and the per-family values. Values come from the committed per-family CSVs and, where the
raw records are unique per (family, variant, model), are recomputed from the records with the
repo's clamped S_lp. A pair that the records cannot support is NOT_EVALUATED with the reason,
never a zero. CPU only, read only. Data role EXPLORATION; audit of past artifacts.

Usage:
    python3 scripts/v2/g0a_label_stability.py --out-dir results/g0/attempt_20261112
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance.recompute import legacy_slp_repo_clamped, spearman  # noqa: E402

THRESHOLD = 0.5
MODELS = {"qwen": "Qwen/Qwen2.5-7B-Instruct", "llama": "meta-llama/Llama-3.1-8B-Instruct"}
PILOT_CSV = "results/stage4_repair/analysis_v2/stage4_per_family.csv"
PANEL_CSV = "results/stage6/analysis_d2/stage6_d1_per_family.csv"
RUNS = {
    "stage4_original": {"records": "results/stage4/behavioural/prompt_records.jsonl", "commit": "31a7857"},
    "stage4_repair": {"records": "results/stage4_repair/behavioural/prompt_records.jsonl", "commit": "953c31e"},
    "stage6_d1": {"records": "results/stage6/behavioural/prompt_records.jsonl", "commit": "0894353"},
    "stage6_panel": {"records": "results/stage6/behavioural_full_rerun/prompt_records.jsonl", "commit": "ffeeeff"},
}
# (run a, run b, family scope, description). Scope "pilot" = the 30 pilot families; "shared" =
# every family scored in both runs (the D1 run holds none of the pilot families).
PAIRS = (
    ("stage4_repair", "stage6_panel", "pilot", "C2b extended: threshold-registration run vs panel run (different regimes)"),
    ("stage4_original", "stage4_repair", "pilot", "first Stage 4 run vs its repair (different prompt formatting)"),
    ("stage4_original", "stage6_panel", "pilot", "first Stage 4 run vs panel run (different regimes)"),
    ("stage6_d1", "stage6_panel", "pilot", "same-regime control on the pilot families"),
    ("stage6_d1", "stage6_panel", "shared", "same-regime control on the D1 families: phase-D1 run vs panel run"),
)
# Read in this shift from `git show <commit>:scripts/run_behavioural.py` [V]: 31a7857 and 953c31e
# define no system prompt; 0894353 and ffeeeff define SYSTEM_PROMPT with the one-line format.
RUNNER_SYSTEM_PROMPT = {"stage4_original": False, "stage4_repair": False, "stage6_d1": True,
                        "stage6_panel": True}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def slp_from_records(records: list[dict[str, Any]], model_name: str) -> tuple[dict[str, float] | None, str]:
    """Clamped S_lp per family, or (None, reason) when the records are not one run."""

    by_family: dict[str, dict[int, list[float | None]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        if record.get("model_name") != model_name or record.get("record_type", "variant_record") != "variant_record":
            continue
        by_family[record["template_id"]][int(record["variant_id"])].append(record["logprob_correct_answer"])
    if not by_family:
        return None, f"no records for {model_name}"
    duplicated = sum(1 for variants in by_family.values() for values in variants.values() if len(values) > 1)
    if duplicated:
        return None, f"{duplicated} (family, variant) cells have several records (several runs in one file)"
    out: dict[str, float] = {}
    for family, variants in by_family.items():
        values = {variant: vals[0] for variant, vals in variants.items()}
        if 0 in values and all(v is not None for v in values.values()) and len(values) >= 2:
            out[family] = legacy_slp_repo_clamped(values)
    return out, "recomputed from records"


def generation_style(records: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    texts = [(r.get("generated_text") or "") for r in records if r.get("model_name") == model_name]
    if not texts:
        return {"n_records": 0}
    return {"n_records": len(texts),
            "median_generated_chars": statistics.median(len(t) for t in texts),
            "share_starting_with_Answer": round(sum(t.strip().startswith("Answer:") for t in texts) / len(texts), 3)}


def compare(a: dict[str, float], b: dict[str, float], families: list[str]) -> dict[str, Any]:
    """Spearman and label agreement on the families present in both runs."""

    common = [f for f in families if f in a and f in b]
    if len(common) < 3:
        return {"status": "NOT_EVALUATED", "n": len(common),
                "reason": f"only {len(common)} pilot families present in both runs (need >= 3)"}
    xs, ys = [a[f] for f in common], [b[f] for f in common]
    labels_a = [x >= THRESHOLD for x in xs]
    labels_b = [y >= THRESHOLD for y in ys]
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        rho = None
        rho_note = "constant values in one run: Spearman undefined"
    else:
        rho = round(float(spearman(xs, ys)), 3)
        rho_note = ""
    agree = sum(1 for p, q in zip(labels_a, labels_b) if p == q)
    return {
        "status": "EVALUATED",
        "n": len(common),
        "spearman": rho,
        "spearman_note": rho_note,
        "label_agreement": agree,
        "label_agreement_share": round(agree / len(common), 3),
        "positives_a": sum(labels_a),
        "positives_b": sum(labels_b),
        "chance_agreement": round((sum(labels_a) * sum(labels_b)
                                   + (len(common) - sum(labels_a)) * (len(common) - sum(labels_b)))
                                  / len(common) ** 2, 3),
        "per_family": {f: {"a": round(a[f], 4), "b": round(b[f], 4)} for f in common},
    }


def run(root: Path) -> dict[str, Any]:
    pilot_rows = read_csv(root / PILOT_CSV)
    panel_rows = {r["template_id"]: r for r in read_csv(root / PANEL_CSV)}
    families = sorted(r["template_id"] for r in pilot_rows)
    report: dict[str, Any] = {"threshold_nats": THRESHOLD, "pilot_families": len(families),
                              "runs": {}, "models": {}}
    records_by_run = {name: read_jsonl(root / spec["records"]) for name, spec in RUNS.items()}
    for name, spec in RUNS.items():
        report["runs"][name] = {**spec, "runner_sends_one_line_answer_system_prompt": RUNNER_SYSTEM_PROMPT[name],
                                "generation_style": {m: generation_style(records_by_run[name], full)
                                                     for m, full in MODELS.items()}}
    for model, full_name in MODELS.items():
        csv_values = {
            "stage4_original": {r["template_id"]: float(r[f"{model}_S_lp"]) for r in pilot_rows if r[f"{model}_S_lp"]},
            "stage4_repair": {r["template_id"]: float(r[f"{model}_S_lp_repair"]) for r in pilot_rows
                              if r[f"{model}_S_lp_repair"]},
            "stage6_panel": {t: float(r[f"{model}_S_lp"]) for t, r in panel_rows.items() if r[f"{model}_S_lp"]},
        }
        recomputed: dict[str, Any] = {}
        sources: dict[str, dict[str, float]] = {}
        for name in RUNS:
            values, note = slp_from_records(records_by_run[name], full_name)
            recomputed[name] = {"status": "EVALUATED" if values is not None else "NOT_EVALUATED", "note": note}
            if values is not None and name in csv_values:
                shared = [f for f in families if f in values and f in csv_values[name]]
                mismatches = [f for f in shared if abs(values[f] - csv_values[name][f]) > 1e-6]
                recomputed[name].update({"families_compared_with_csv": len(shared),
                                         "mismatches_with_csv": mismatches})
            # Prefer the committed CSV; fall back to the records (the D1 run has no pilot CSV column).
            sources[name] = csv_values.get(name) or (values or {})
        pairs = {}
        for left, right, scope, description in PAIRS:
            scope_families = families if scope == "pilot" else sorted(set(sources[left]) & set(sources[right]))
            result = compare(sources[left], sources[right], scope_families)
            result["description"] = description
            result["family_scope"] = scope
            pairs[f"{left}__vs__{right}__{scope}"] = result
        report["models"][model] = {"recomputation": recomputed, "pairs": pairs}
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = ["# G0 (a): cross-instruction stability of the legacy S_lp label (30 pilot families)", "",
             "Data role EXPLORATION; audit of committed Phase-I records; not evidence for any v2 claim.",
             f"Threshold {report['threshold_nats']} nats. Agreement is the number of the n families with the same "
             "label in both runs; `chance` is the agreement expected from the two positive rates alone.", "",
             "| Model | Pair | n | Spearman | Label agreement | Chance | Positives (a / b) |",
             "|---|---|---|---|---|---|---|"]
    for model, block in report["models"].items():
        for pair, result in block["pairs"].items():
            if result["status"] != "EVALUATED":
                lines.append(f"| {model} | {pair} | {result['n']} | NOT_EVALUATED | {result['reason']} | | |")
                continue
            lines.append(f"| {model} | {pair} | {result['n']} | {result['spearman']} | "
                         f"{result['label_agreement']} of {result['n']} | {result['chance_agreement']} | "
                         f"{result['positives_a']} / {result['positives_b']} |")
    lines += ["", "## Runs", ""]
    for name, spec in report["runs"].items():
        style = "; ".join(f"{m}: median {s.get('median_generated_chars')} chars, "
                          f"{s.get('share_starting_with_Answer')} start with 'Answer:'"
                          for m, s in spec["generation_style"].items() if s.get("n_records"))
        lines.append(f"- `{name}` (commit {spec['commit']}, one-line system prompt in runner: "
                     f"{spec['runner_sends_one_line_answer_system_prompt']}): {style}")
    lines += ["", "## Recomputation from raw records", ""]
    for model, block in report["models"].items():
        for name, item in block["recomputation"].items():
            extra = ""
            if "mismatches_with_csv" in item:
                extra = f"; {item['families_compared_with_csv']} compared with the CSV, " \
                        f"{len(item['mismatches_with_csv'])} mismatches"
            lines.append(f"- {model} `{name}`: {item['status']} ({item['note']}{extra})")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    report = run(args.root)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "g0a_label_stability.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                                          encoding="utf-8")
    write_markdown(report, args.out_dir / "g0a_label_stability.md")
    for model, block in report["models"].items():
        for pair, result in block["pairs"].items():
            if result["status"] == "EVALUATED":
                print(f"{model} {pair}: n={result['n']} spearman={result['spearman']} "
                      f"agreement={result['label_agreement']}/{result['n']}")
            else:
                print(f"{model} {pair}: NOT_EVALUATED ({result['reason']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
