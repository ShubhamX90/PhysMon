#!/usr/bin/env python3
"""Stage 14.2 / card X02: base-variant invariance challenge (zero-cost, stored values only).

For every four-rendering family and model, recompute the legacy base-relative log-probability
sensitivity under each of the four possible choices of base variant, in both of its written forms:

- `legacy_repo_clamped`: max over all variants j of (L_base - L_j). This is the form implemented in
  `physmon.formal.sensitivity` and `scripts/analyse_stage4.py`; it includes j = base, so it is never negative.
- `legacy_plan_signed`: max over j != base of (L_base - L_j). This is the form written in v2 B1.3 and P1.1;
  it can be negative.

It also reports base-free dispersion (range, sample SD, MAD, median absolute pairwise difference),
label stability under rotation of the base, reclassification matrices, rank concordance, and cross-model
discordance. CPU only; no model call; no new data. The anchor-free and no-cue contrasts that need new model
evaluations are out of scope (v2 P1.1 says they "do require new evaluations").

The range is absolute dispersion. It is not a signed risk measure and has a different null distribution
from the signed legacy statistic (v2 B1.3, P1.1). A family with a missing log-probability is NOT_EVALUATED,
never dropped silently and never scored as 0.

Plan reference: card X02 (p.39); B1.2-B1.3 (p.6-8); P1.1 (p.17); C01-C02 (p.33); §12 item 2 (p.48).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance import recompute as rc  # noqa: E402

OUT_ROOT = "results/stage14/x02_base_rotation"
THRESHOLD = 0.5  # legacy nat threshold, pre-registered 2026-06-14 (commit 5a72370); not re-tuned here
BASES = (0, 1, 2, 3)
QWEN = "Qwen/Qwen2.5-7B-Instruct"
LLAMA = "meta-llama/Llama-3.1-8B-Instruct"
MODELS = (QWEN, LLAMA)

INPUTS = {
    "prompt_records": "results/stage6/behavioural_full_rerun/prompt_records.jsonl",
    "per_family": "results/stage6/analysis_d2/stage6_d1_per_family.csv",
}

# Values quoted by the plan for CM_B_UM_059 (Qwen; v2 B1.3, p.8).
PLAN_EXAMPLE = {
    "template_id": "CM_B_UM_059",
    "gold_logprobs": ["-45.531", "-55.562", "-45.000", "-46.469"],
    "base0_signed": "+10.031",
    "base1_signed": "-9.093",
    "symmetric_range": "10.562",
}


def load_values(path: Path) -> dict[tuple[str, str], dict[int, float | None]]:
    grouped: dict[tuple[str, str], dict[int, float | None]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        key = (record["model_name"], record["template_id"])
        grouped.setdefault(key, {})[int(record["variant_id"])] = rc.as_float_or_none(
            record.get("logprob_correct_answer")
        )
    return grouped


def rotation_row(values: dict[int, float]) -> dict[str, Any]:
    """All base-rotation quantities for one family and model (values: variant -> gold log-prob)."""

    row: dict[str, Any] = {}
    positives = []
    for base in BASES:
        repo = rc.legacy_slp_repo_clamped(values, base)
        plan = rc.legacy_slp_plan_signed(values, base)
        label = int(plan >= THRESHOLD)
        # With a positive threshold the clamp cannot change the label; assert it rather than assume it.
        if label != int(repo >= THRESHOLD):
            raise AssertionError("repo-clamped and plan-signed labels disagree")
        row[f"S_repo_b{base}"] = repo
        row[f"S_plan_b{base}"] = plan
        row[f"y_b{base}"] = label
        positives.append(label)
    series = [values[b] for b in BASES]
    row["n_positive_bases"] = sum(positives)
    row["label_stable"] = int(len(set(positives)) == 1)
    row["label_differs_from_base0"] = int(any(p != positives[0] for p in positives[1:]))
    row["range"] = max(series) - min(series)
    row["sd"] = rc.sample_sd(series)
    row["mad"] = rc.median_abs_deviation(series)
    row["median_abs_pairwise"] = rc.median_abs_pairwise_difference(series)
    row["range_label"] = int(row["range"] >= THRESHOLD)
    row["argmax_variant"] = int(np.argmax(series))
    row["argmin_variant"] = int(np.argmin(series))
    return row


def build_rows(grouped, meta, answers) -> list[dict[str, Any]]:
    rows = []
    for model in MODELS:
        for template_id in sorted(meta):
            values = grouped.get((model, template_id), {})
            usable = len(values) == 4 and all(v is not None for v in values.values())
            base = {
                "model": model,
                "template_id": template_id,
                "cue_type": meta[template_id]["cue_type"],
                "domain": meta[template_id]["domain"],
                "governing_law": meta[template_id]["governing_law"],
                "answer_chars": len(answers.get(template_id, "")),
                "status": "EVALUATED" if usable else "NOT_EVALUATED",
            }
            for b in BASES:
                base[f"L{b}"] = values.get(b)
            if usable:
                base.update(rotation_row({int(k): float(v) for k, v in values.items()}))
            rows.append(base)
    return rows


def _evaluated(rows, model):
    return [r for r in rows if r["model"] == model and r["status"] == "EVALUATED"]


def stability_counts(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    robust_pos = sum(r["n_positive_bases"] == 4 for r in rows)
    robust_neg = sum(r["n_positive_bases"] == 0 for r in rows)
    mixed = n - robust_pos - robust_neg
    return {
        "n": n,
        "positive_under_base0": sum(r["y_b0"] for r in rows),
        "robust_positive_all_four_bases": robust_pos,
        "robust_negative_all_four_bases": robust_neg,
        "base_dependent_mixed": mixed,
        "fraction_base_dependent": (mixed / n) if n else None,
        "positive_under_range_ge_threshold": sum(r["range_label"] for r in rows),
    }


def structural_identities(rows: list[dict]) -> dict[str, Any]:
    """Properties that hold by construction, so they are not read as findings.

    The label under base b is 1 iff some other variant is at least THRESHOLD nats lower than variant b.
    The lowest-likelihood variant used as the base therefore always gets label 0, so no family can be
    positive under all four bases, and a family is positive under at least one base exactly when
    range >= THRESHOLD. "Base-dependent" is thus the same set as "range >= THRESHOLD".
    """

    mixed = sum(1 <= r["n_positive_bases"] <= 3 for r in rows)
    range_positive = sum(r["range_label"] for r in rows)
    return {
        "no_family_positive_under_all_four_bases": all(r["n_positive_bases"] <= 3 for r in rows),
        "lowest_variant_as_base_is_always_negative": all(r[f"y_b{r['argmin_variant']}"] == 0 for r in rows),
        "base_dependent_set_equals_range_positive_set": all(
            (1 <= r["n_positive_bases"] <= 3) == bool(r["range_label"]) for r in rows),
        "n_base_dependent": mixed,
        "n_range_positive": range_positive,
        "families_negative_at_base0_but_range_positive": sum((not r["y_b0"]) and r["range_label"] for r in rows),
        "families_positive_at_base0_but_range_negative": sum(r["y_b0"] and (not r["range_label"]) for r in rows),
    }


def reclassification(rows: list[dict], base: int) -> dict[str, int]:
    out = {"pos_to_pos": 0, "pos_to_neg": 0, "neg_to_pos": 0, "neg_to_neg": 0}
    for r in rows:
        before, after = r["y_b0"], r[f"y_b{base}"]
        out[f"{'pos' if before else 'neg'}_to_{'pos' if after else 'neg'}"] += 1
    return out


def concordance(rows_a: list[dict], rows_b: list[dict], key_a: str, key_b: str) -> dict[str, float | None]:
    xs = [r[key_a] for r in rows_a]
    ys = [r[key_b] for r in rows_b]
    try:
        return {"spearman": rc.spearman(xs, ys), "discordant_pair_fraction": rc.discordant_pair_fraction(xs, ys)}
    except ValueError:
        return {"spearman": None, "discordant_pair_fraction": None}


def stratified(rows: list[dict], key) -> dict[str, Any]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(str(key(r)), []).append(r)
    return {name: stability_counts(items) for name, items in sorted(groups.items())}


def s0_bin(row: dict) -> str:
    value = row["S_repo_b0"]
    if value == 0:
        return "S0 == 0"
    if value < THRESHOLD:
        return "0 < S0 < 0.5"
    if value < 2.0:
        return "0.5 <= S0 < 2"
    return "S0 >= 2"


def answer_length_tercile(rows: list[dict]) -> dict[str, str]:
    order = sorted(rows, key=lambda r: (r["answer_chars"], r["template_id"]))
    labels = {}
    for index, r in enumerate(order):
        labels[r["template_id"]] = ("short", "medium", "long")[min(2, index * 3 // len(order))]
    return labels


def summarise(rows: list[dict]) -> dict[str, Any]:
    summary: dict[str, Any] = {"per_model": {}, "cross_model": {}}
    by_model = {m: _evaluated(rows, m) for m in MODELS}
    for model, items in by_model.items():
        terciles = answer_length_tercile(items)
        summary["per_model"][model] = {
            "n_families_total": sum(r["model"] == model for r in rows),
            "n_evaluated": len(items),
            "not_evaluated": sorted(r["template_id"] for r in rows
                                    if r["model"] == model and r["status"] != "EVALUATED"),
            "overall": stability_counts(items),
            "structural_identities": structural_identities(items),
            "label_counts_by_base": {f"base{b}": sum(r[f"y_b{b}"] for r in items) for b in BASES},
            "reclassification_from_base0": {f"to_base{b}": reclassification(items, b) for b in (1, 2, 3)},
            "range_label_vs_base0_label": {
                "both_positive": sum(r["y_b0"] and r["range_label"] for r in items),
                "base0_negative_range_positive": sum((not r["y_b0"]) and r["range_label"] for r in items),
                "base0_positive_range_negative": sum(r["y_b0"] and (not r["range_label"]) for r in items),
                "both_negative": sum((not r["y_b0"]) and (not r["range_label"]) for r in items),
            },
            "score_rank_concordance_with_base0": {
                f"S_repo_b{b}": concordance(items, items, "S_repo_b0", f"S_repo_b{b}") for b in (1, 2, 3)
            } | {"range": concordance(items, items, "S_repo_b0", "range")},
            "by_cue_type": stratified(items, lambda r: r["cue_type"]),
            "by_domain": stratified(items, lambda r: r["domain"]),
            "by_S0_bin": stratified(items, s0_bin),
            "by_answer_length_tercile_PROXY_chars": stratified(items, lambda r: terciles[r["template_id"]]),
        }
    q, lm = by_model[QWEN], by_model[LLAMA]
    common = sorted({r["template_id"] for r in q} & {r["template_id"] for r in lm})
    qi = {r["template_id"]: r for r in q}
    li = {r["template_id"]: r for r in lm}
    qs = [qi[t] for t in common]
    ls = [li[t] for t in common]
    summary["cross_model"] = {
        "n_common_evaluated_families": len(common),
        "shared_positive_by_base": {
            f"base{b}": sum(1 for a, c in zip(qs, ls) if a[f"y_b{b}"] and c[f"y_b{b}"]) for b in BASES
        },
        "shared_positive_range_ge_threshold": sum(1 for a, c in zip(qs, ls) if a["range_label"] and c["range_label"]),
        "qwen_llama_rank_concordance": {
            **{f"S_repo_b{b}": concordance(qs, ls, f"S_repo_b{b}", f"S_repo_b{b}") for b in BASES},
            "range": concordance(qs, ls, "range", "range"),
            "sd": concordance(qs, ls, "sd", "sd"),
        },
    }
    return summary


def plan_example(rows: list[dict]) -> dict[str, Any]:
    row = next(r for r in rows if r["model"] == QWEN and r["template_id"] == PLAN_EXAMPLE["template_id"])
    logs = [row[f"L{b}"] for b in BASES]
    checks = {
        # units=1.0: the plan prints some values truncated (-55.562 for -55.5625, -9.093 for -9.09375).
        "gold_logprobs": [rc.matches_reported(v, rep, units=1.0)
                          for v, rep in zip(logs, PLAN_EXAMPLE["gold_logprobs"])],
        "base0_signed": rc.matches_reported(row["S_plan_b0"], PLAN_EXAMPLE["base0_signed"], units=1.0),
        "base1_signed": rc.matches_reported(row["S_plan_b1"], PLAN_EXAMPLE["base1_signed"], units=1.0),
        "symmetric_range": rc.matches_reported(row["range"], PLAN_EXAMPLE["symmetric_range"], units=1.0),
    }
    return {
        "template_id": row["template_id"],
        "model": QWEN,
        "gold_logprobs": logs,
        "S_plan_signed_by_base": [row[f"S_plan_b{b}"] for b in BASES],
        "S_repo_clamped_by_base": [row[f"S_repo_b{b}"] for b in BASES],
        "labels_by_base": [row[f"y_b{b}"] for b in BASES],
        "range": row["range"],
        "reported_by_plan": PLAN_EXAMPLE,
        "matches_plan_at_reported_precision": checks,
        "note": ("-55.5625 is an exact binary half-way value; the plan prints -55.562 and the digest "
                 "-55.563, so the base-1 signed value is -9.09375 (plan: about -9.093/-9.094)."),
    }


def discrepancies(summary: dict, example: dict) -> list[dict[str, Any]]:
    q = summary["per_model"][QWEN]
    ledger = [
        {
            "id": "X02-D1",
            "kind": "definition_mismatch",
            "description": "Repo legacy S_lp (max over all variants, includes base) is never negative; the "
                           "plan's base-rotation form (max over j != base) can be negative.",
            "impact": "Labels at 0.5 nat are identical under both forms (the clamp cannot change a comparison "
                      "with a positive threshold; asserted per row). Scores and rank-based comparisons differ. "
                      "The plan's -9.094 for CM_B_UM_059 at base 1 corresponds to the signed form; the repo "
                      "form gives 0.0 there.",
            "evidence": example["S_plan_signed_by_base"] + example["S_repo_clamped_by_base"],
        },
        {
            "id": "X02-D2",
            "kind": "label_instability",
            "description": "Qwen families whose 0.5-nat label depends on which rendering is called the base.",
            "impact": f"{q['overall']['base_dependent_mixed']} of {q['overall']['n']} evaluated Qwen families "
                      "are positive under some bases and negative under others.",
            "evidence": q["overall"],
        },
    ]
    return ledger


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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

    grouped = load_values(REPO_ROOT / INPUTS["prompt_records"])
    with (REPO_ROOT / INPUTS["per_family"]).open(newline="", encoding="utf-8") as handle:
        meta = {r["template_id"]: r for r in csv.DictReader(handle)}
    answers = {}
    for line in (REPO_ROOT / INPUTS["prompt_records"]).read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if int(record["variant_id"]) == 0:
            answers[record["template_id"]] = str(record.get("correct_answer", ""))

    rows = build_rows(grouped, meta, answers)
    summary = summarise(rows)
    example = plan_example(rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    columns = (["model", "template_id", "cue_type", "domain", "governing_law", "answer_chars", "status"]
               + [f"L{b}" for b in BASES]
               + [f"S_repo_b{b}" for b in BASES] + [f"S_plan_b{b}" for b in BASES]
               + [f"y_b{b}" for b in BASES]
               + ["n_positive_bases", "label_stable", "label_differs_from_base0", "range", "sd", "mad",
                  "median_abs_pairwise", "range_label", "argmax_variant", "argmin_variant"])
    with (out_dir / "base_permutation_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "card": "v2_X02_base_variant_invariance_challenge",
        "evidence_class": "exploratory diagnostic of a measurement definition on stored data; "
                          "no confirmatory role; not paper-eligible",
        "source_commit": sha,
        "git_status_short": git("status", "--short").splitlines(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "command": " ".join(sys.argv),
        "threshold_nats": THRESHOLD,
        "definitions": {
            "legacy_repo_clamped": "max over all variants j of (L_base - L_j)  [includes j = base; >= 0]",
            "legacy_plan_signed": "max over j != base of (L_base - L_j)  [v2 B1.3; can be negative]",
            "range": "max_i L_i - min_i L_i  [absolute dispersion; not a signed risk measure]",
        },
        "inputs": {k: {"path": v, "sha256": sha256(REPO_ROOT / v)} for k, v in INPUTS.items()},
        "summary": summary,
        "plan_example": example,
        "discrepancy_ledger": discrepancies(summary, example),
        "interpretation": [
            "Base-dependent labels are the same set as families with range >= 0.5 nat; the near-total "
            "base dependence is a structural property of a base-relative label, not an empirical surprise.",
            "What is empirical: how many legacy-negative families have range >= 0.5 (the legacy label "
            "misses them when variant 0 is not one of the more likely renderings); how the positive count "
            "moves with the base (variant 0 gives the fewest positives for both models); and how the "
            "Qwen/Llama overlap changes with the definition (shared positives by base and by range).",
            "The range is absolute dispersion with a different null distribution from the signed legacy "
            "statistic (v2 B1.3, P1.1). Range >= 0.5 is therefore not a corrected label; no presentation-noise "
            "baseline exists yet (P1.7) and the 0.5 threshold was set for the signed statistic.",
            "Counts are descriptive at the family level; families are not independent (34 structure "
            "clusters, Stage 14.4), so no p-values or intervals are given.",
        ],
        "deferred": [
            "anchor-free no-cue contrasts (need new model evaluations)",
            "family-cluster stratification (Stage 14.4 adjudicates the 34 clusters)",
            "true answer-token-length strata (Stage 14.3 scoring contract; answer_chars is a crude proxy)",
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    q = summary["per_model"][QWEN]["overall"]
    lm = summary["per_model"][LLAMA]["overall"]
    print(json.dumps({"attempt_dir": str(shown), "qwen": q, "llama": lm,
                      "cross_model": summary["cross_model"]["shared_positive_by_base"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
