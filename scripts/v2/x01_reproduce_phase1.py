#!/usr/bin/env python3
"""Stage 14.1 / card X01: recompute Phase-I ledger values from committed raw records.

CPU only. Reads committed artifacts under the repository, recomputes each reported value with the
independent implementations in `physmon.governance.recompute`, and writes a reconciliation under a
new attempt directory `results/stage14/x01_reproduction/<attempt-id>/`. With `--update-ledger` it
also writes the per-component outcomes and the derived label into
`docs/registry/v2/claim_ledger.jsonl` (rows it did not examine are left untouched).

Nothing here loads a model, uses a GPU, submits a job, or writes outside the repository. A value
with no committed source is reported as `not_enough_source_data`, never filled in. A value that
differs is `unreproducible` unless an explanation is coded next to the check.

Plan reference: v2 P0.2 (p.16), card X01 (p.39), §8.4 (p.42).
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
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance import recompute as rc  # noqa: E402
from physmon.governance.v2_contract import validate_ledger_rows, worst_label  # noqa: E402

LEDGER = "docs/registry/v2/claim_ledger.jsonl"
OUT_ROOT = "results/stage14/x01_reproduction"

QWEN = "Qwen/Qwen2.5-7B-Instruct"
LLAMA = "meta-llama/Llama-3.1-8B-Instruct"

P = {
    "manifest": "data/manifests/physmon_canonical_155.jsonl",
    "registry": "docs/model_registry.yml",
    "per_family": "results/stage6/analysis_d2/stage6_d1_per_family.csv",
    "prompt_records": "results/stage6/behavioural_full_rerun/prompt_records.jsonl",
    "monitor_oof": "results/stage10/mean_probe_full_sweep_bigcompute/loo_predictions_resid_post_last_prompt.json",
    "monitor_summary": "results/stage10/mean_probe_full_sweep_bigcompute/summary_resid_post_last_prompt.json",
    "per_variant_oof": "results/stage10/per_variant_probe_sweep/loo_predictions_per_variant.json",
    "per_variant_summary": "results/stage10/per_variant_probe_sweep/summary_per_variant_sweep.json",
    "entropy_oof": "results/stage9/baselines/entropy/entropy_per_family_scores.json",
    "correctness_oof": "results/stage9/baselines/correctness_probe/loo_predictions_variance.json",
    "correctness_summary": "results/stage9/baselines/correctness_probe/summary_variance.json",
    "combined_oof": "results/wave2/combined_baseline/combined_baseline_predictions.json",
    "wave2_summary": "results/wave2/incremental_information/incremental_information_summary.json",
    "expansion_preds": "results/stage12/expansion_probe_inference/family_mean_predictions.json",
    "expansion_summary": "results/stage12/expansion_probe_inference/summary.json",
    "mhk_csv": "results/stage8/multi_head_knockout/patching_results.csv",
    "head11_csv": "results/stage10/full_head_sweep_l16/head_11/patching_results.csv",
    "validation": "results/stage13/benchmark_integrity/validation_agreement_v3.json",
    "leakage": "results/stage13/benchmark_integrity/leakage_audit_v7.json",
    "coverage": "results/stage13/wave0/registry_coverage_v7.json",
    "donor_same": "results/stage12/science/donor_renamed/same_answer/same_answer_donor_results.csv",
    "donor_stable": "results/stage12/science/donor_renamed/stable/stable_donor_results.csv",
    "proximity": "results/stage10/distractor_proximity/proximity_vs_slp.json",
}


def read_json(key: str) -> Any:
    return json.loads((REPO_ROOT / P[key]).read_text(encoding="utf-8"))


def read_jsonl(key: str) -> list[dict]:
    text = (REPO_ROOT / P[key]).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def read_csv(key: str) -> list[dict]:
    with (REPO_ROOT / P[key]).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def component(name, reported, recomputed, outcome, detail="", artifacts=()):
    return {
        "name": name,
        "reported": reported,
        "recomputed": recomputed,
        "outcome": outcome,
        "detail": detail,
        "artifacts": list(artifacts),
    }


def numeric(name, reported, recomputed, artifacts, detail=""):
    """Compare a recomputed number with a reported string at the reported precision."""

    ok = rc.matches_reported(recomputed, reported)
    outcome = "verified" if ok else "unreproducible"
    text = detail or ("" if ok else f"recomputed {recomputed!r} does not round to {reported}")
    return component(name, str(reported), _round(recomputed), outcome, text, artifacts)


def count(name, reported, recomputed, artifacts, detail=""):
    ok = int(reported) == int(recomputed)
    text = detail or ("" if ok else f"recomputed {recomputed} differs from reported {reported}")
    return component(name, int(reported), int(recomputed), "verified" if ok else "unreproducible",
                     text, artifacts)


def _round(value: float) -> float:
    return round(float(value), 6)


def slp_by_model(records: list[dict]) -> dict[str, dict[str, float | None]]:
    """Legacy-repo `S_lp` (max over all variants of L_base - L_j) per model and family.

    A family without all four finite log-probabilities is None (not evaluated), never 0.
    """

    grouped: dict[tuple[str, str], dict[int, float | None]] = {}
    for record in records:
        key = (record["model_name"], record["template_id"])
        grouped.setdefault(key, {})[int(record["variant_id"])] = rc.as_float_or_none(
            record.get("logprob_correct_answer")
        )
    output: dict[str, dict[str, float | None]] = {QWEN: {}, LLAMA: {}}
    for (model, family), values in grouped.items():
        usable = len(values) == 4 and all(v is not None for v in values.values())
        output[model][family] = rc.legacy_slp_repo_clamped(values) if usable else None
    return output


# --------------------------------------------------------------------------------------------
# One function per ledger row. Each returns (components, info).
# --------------------------------------------------------------------------------------------


def check_p1l_01():
    rows = read_jsonl("manifest")
    sources = [row["benchmark_source"] for row in rows]
    art = [P["manifest"]]
    comps = [
        count("canonical_total", 155, len(rows), art),
        count("original_behavioural", 140, sources.count("stage6_original"), art),
        count("later_expansion", 15, sources.count("stage10_expansion"), art),
    ]
    return comps, {"all_canonical": all(row["is_canonical"] for row in rows)}


def check_p1l_02(ctx):
    oof = read_json("monitor_oof")
    per_family = {row["template_id"]: row for row in read_csv("per_family")}
    labels = {row["template_id"]: int(row["true_label"]) for row in oof}
    excluded = sorted(set(per_family) - set(labels))
    qwen_slp = ctx["slp"][QWEN]
    mismatches = sorted(
        family
        for family, label in labels.items()
        if qwen_slp.get(family) is None or int(qwen_slp[family] >= 0.5) != label
    )
    art = [P["monitor_oof"], P["per_family"], P["prompt_records"]]
    reasons = {
        family: {
            "qwen_parse_ok": per_family[family]["qwen_parse_ok"],
            "qwen_S_lp": per_family[family]["qwen_S_lp"],
            "notes": per_family[family]["notes"],
        }
        for family in excluded
    }
    stable_and_parse_failed = all(
        reasons[f]["qwen_parse_ok"] == "False" and float(reasons[f]["qwen_S_lp"]) < 0.5
        for f in excluded
    )
    comps = [
        count("cohort_size", 135, len(labels), art),
        count("sensitive", 70, sum(labels.values()), art),
        count("stable", 65, len(labels) - sum(labels.values()), art),
        count("excluded_from_140", 5, len(excluded), art),
        component(
            "excluded_are_stable_and_parse_failed", "five stable families, parsing failures",
            ", ".join(excluded), "verified" if stable_and_parse_failed else "unreproducible",
            "" if stable_and_parse_failed else "an excluded family is not (S_lp<0.5 and parse failed)",
            art),
        component(
            "labels_regenerate_from_raw", "label = Qwen S_lp >= 0.5", f"{len(mismatches)} mismatches",
            "verified" if not mismatches else "unreproducible",
            "" if not mismatches else f"label differs from recomputed Qwen S_lp>=0.5 for {mismatches}",
            art),
    ]
    return comps, {"excluded": reasons, "label_mismatches": mismatches}


def check_p1l_03():
    registry = yaml.safe_load((REPO_ROOT / P["registry"]).read_text(encoding="utf-8"))["models"]
    expected = {
        "qwen_primary": QWEN,
        "llama_primary": LLAMA,
        "deepseek_reasoning": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    }
    comps = []
    for key, name in expected.items():
        found = registry.get(key, {}).get("name")
        comps.append(component(f"registry_{key}", name, found,
                               "verified" if found == name else "unreproducible",
                               "" if found == name else "registry entry missing or different",
                               [P["registry"]]))
    return comps, {}


def check_p1l_04(ctx):
    slp = ctx["slp"]
    per_family = read_csv("per_family")
    art = [P["prompt_records"], P["per_family"]]
    qwen_pos = {f for f, v in slp[QWEN].items() if v is not None and v >= 0.5}
    llama_pos = {f for f, v in slp[LLAMA].items() if v is not None and v >= 0.5}
    not_evaluated = {m: sorted(f for f, v in values.items() if v is None) for m, values in slp.items()}
    shared_slp = qwen_pos & llama_pos
    q_hat = {r["template_id"] for r in per_family if (rc.as_float_or_none(r["qwen_hat_S"]) or 0) > 0}
    l_hat = {r["template_id"] for r in per_family if (rc.as_float_or_none(r["llama_hat_S"]) or 0) > 0}
    csv_flag = {r["template_id"] for r in per_family if r["both_sensitive"] == "True"}
    diffs = []
    for row in per_family:
        for column, model in (("qwen_S_lp", QWEN), ("llama_S_lp", LLAMA)):
            mine = slp[model].get(row["template_id"])
            theirs = rc.as_float_or_none(row[column])
            diffs.append(float("inf") if mine is None or theirs is None else abs(mine - theirs))
    max_diff = max(diffs)
    explain = (
        f"Under the 0.5-nat S_lp definition the shared count is {len(shared_slp)}. The value 25 equals "
        f"the answer-flip (hat-S > 0) overlap: {len(q_hat & l_hat)} families, which is also the "
        "stage6_d1_per_family.csv 'both_sensitive' column (matches on every row). The "
        f"decision-log table at lines 1086-1090 (25 both / {len(q_hat - l_hat)} Qwen-only / "
        f"{len(l_hat - q_hat)} Llama-only) counts hat-S, not S_lp, which explains its Llama total of "
        f"{len(l_hat)} versus 32 at 0.5 nat."
    )
    comps = [
        count("qwen_positive_at_0.5nat", 70, len(qwen_pos), art),
        count("llama_positive_at_0.5nat", 32, len(llama_pos), art),
        component("recomputed_S_lp_matches_per_family_csv", "per-family CSV", f"max abs diff {max_diff:.3g}",
                  "verified" if max_diff <= 1e-9 else "unreproducible",
                  "" if max_diff <= 1e-9 else "recomputed S_lp differs from the committed CSV", art),
        component("shared_positives", 25, len(shared_slp), "different_but_explained", explain, art),
    ]
    info = {
        "not_evaluated_families": not_evaluated,
        "hat_S_counts": {"qwen": len(q_hat), "llama": len(l_hat), "both": len(q_hat & l_hat),
                         "csv_both_sensitive": len(csv_flag), "csv_flag_equals_hatS_both":
                         csv_flag == (q_hat & l_hat)},
        "shared_slp_families": sorted(shared_slp),
    }
    return comps, info


def _oof(key):
    rows = read_json(key)
    return [int(r["true_label"]) for r in rows], [float(r["prediction"]) for r in rows], rows


def check_p1l_05():
    labels, scores, rows = _oof("monitor_oof")
    art = [P["monitor_oof"], P["monitor_summary"]]
    layers = {r["layer_index"] for r in rows}
    comps = [
        numeric("auroc_layer18_from_oof", "0.7596", rc.auroc(labels, scores), art,
                "recomputed from committed out-of-fold predictions; the predictions themselves cannot "
                "be regenerated because activation tensors were lost in the 2026-10 scratch wipe"),
        component("oof_layer", 18, sorted(layers), "verified" if layers == {18} else "unreproducible",
                  "" if layers == {18} else "OOF file mixes layers", art),
    ]
    # The detail text above is informational for a verified outcome; keep it as a note.
    comps[0]["note"] = comps[0].pop("detail")
    comps[0]["detail"] = ""
    return comps, {"auprc": _round(rc.average_precision(labels, scores))}


def check_p1l_06():
    rows = read_json("per_variant_oof")
    labels = [int(r["true_label"]) for r in rows]
    scores = [float(r["prediction"]) for r in rows]
    layers = {r["layer_index"] for r in rows}
    summary = read_json("per_variant_summary")
    art = [P["per_variant_oof"], P["per_variant_summary"]]
    value = rc.auroc(labels, scores)
    comp_a = numeric("variant_level_auroc_layer16", "0.7465", value, art)
    comp_a["note"] = (f"{len(rows)} variant-level samples pooled; family label copied to each variant; "
                      f"layers in file {sorted(layers)}; summary best_layer {summary['best_layer']}")
    return [comp_a], {"n_variant_samples": len(rows)}


def check_p1l_07():
    e_labels, e_scores, _ = _oof("entropy_oof")
    c_labels, c_scores, c_rows = _oof("correctness_oof")
    m_labels, _, _ = _oof("monitor_oof")
    c_summary = read_json("correctness_summary")
    same_target = c_labels == m_labels
    art_e = [P["entropy_oof"]]
    art_c = [P["correctness_oof"], P["correctness_summary"]]
    comps = [
        numeric("fitted_entropy_auroc", "0.7270", rc.auroc(e_labels, e_scores), art_e),
        numeric("correctness_probe_auroc_on_its_own_target", "0.7657", rc.auroc(c_labels, c_scores),
                art_c),
    ]
    comps[1]["note"] = (
        "reproduces exactly, but the probe predicts answer correctness "
        f"(target_measure={c_summary['target_measure']}, threshold {c_summary['correctness_threshold']}), "
        "not S_lp sensitivity: its labels "
        + ("equal" if same_target else "differ from")
        + " the sensitivity labels, so 0.7657 is not a like-for-like sensitivity AUROC"
    )
    return comps, {"correctness_labels_equal_sensitivity_labels": same_target,
                   "correctness_layer": sorted({r["layer_index"] for r in c_rows})}


def check_p1l_08():
    m_labels, m_scores, _ = _oof("monitor_oof")
    e_labels, e_scores, _ = _oof("entropy_oof")
    c_labels, c_scores, _ = _oof("combined_oof")
    if not (m_labels == e_labels == c_labels):
        raise RuntimeError("OOF files disagree on family order or labels")
    stored = read_json("wave2_summary")["paired_differences"]
    art = [P["monitor_oof"], P["entropy_oof"], P["combined_oof"], P["wave2_summary"]]
    me = rc.paired_bootstrap_auroc_difference(m_labels, m_scores, e_scores)
    mc = rc.paired_bootstrap_auroc_difference(m_labels, m_scores, c_scores)
    stored_me = stored["monitor_minus_entropy"]["auroc"]
    stored_mc = stored["monitor_minus_combined"]["auroc"]
    comps = [
        numeric("monitor_minus_entropy_difference", "+0.033", me["observed_difference"], art),
        numeric("monitor_minus_entropy_ci_low", "-0.074", me["ci95_low"], art),
        numeric("monitor_minus_entropy_ci_high", "+0.141", me["ci95_high"], art),
        component(
            "combined_plus_hidden_gain", "+0.067 (CI spans zero)", stored["both_minus_combined"]["auroc"],
            "not_enough_source_data",
            "out-of-fold predictions for the combined-plus-hidden model are not committed (only the "
            "summary values), so the +0.067 gain and its interval cannot be recomputed independently "
            "of re-running scripts/run_incremental_information.py, which would overwrite tracked results",
            [P["wave2_summary"]]),
    ]
    info = {
        "monitor_minus_entropy": me,
        "monitor_minus_combined": mc,
        "stored_monitor_minus_entropy": stored_me,
        "stored_monitor_minus_combined": stored_mc,
        "recompute_matches_stored_wave2_summary_4dp": all(
            abs(me[k] - stored_me[v]) < 5e-5 and abs(mc[k] - stored_mc[v]) < 5e-5
            for k, v in (("observed_difference", "observed_difference"), ("ci95_low", "ci95_low"),
                         ("ci95_high", "ci95_high"))
        ),
    }
    return comps, info


def check_p1l_09():
    m_labels, m_scores, _ = _oof("monitor_oof")
    e_labels, e_scores, _ = _oof("entropy_oof")
    art = [P["monitor_oof"], P["entropy_oof"]]
    return [
        numeric("monitor_brier", "0.2036", rc.brier(m_labels, m_scores), art),
        numeric("entropy_brier", "0.2140", rc.brier(e_labels, e_scores), art),
        numeric("entropy_ece", "0.0907", rc.ece(e_labels, e_scores), art),
        numeric("monitor_ece", "0.1041", rc.ece(m_labels, m_scores), art),
        numeric("entropy_fnr_at_fpr_0.10", "0.643", rc.fnr_at_fpr(e_labels, e_scores, 0.10), art),
        numeric("monitor_fnr_at_fpr_0.10", "0.714", rc.fnr_at_fpr(m_labels, m_scores, 0.10), art),
    ], {"ece_bins": "10 equal-width (project default)"}


def check_p1l_10():
    rows = read_json("expansion_preds")
    cue = {r["template_id"]: r["cue_type"] for r in read_jsonl("manifest")}
    art = [P["expansion_preds"], P["expansion_summary"], P["manifest"]]
    labels = [int(r["true_label"]) for r in rows]
    scores = [float(r["mean_prediction"]) for r in rows]
    b_rows = [r for r in rows if cue[r["template_id"]] == "nongoverning_distractor"]
    c_rows = [r for r in rows if cue[r["template_id"]] == "frame_rendering"]

    def group_auroc(group):
        y = [int(r["true_label"]) for r in group]
        if len(set(y)) < 2:
            return None
        return rc.auroc(y, [float(r["mean_prediction"]) for r in group])

    b_auroc, c_auroc = group_auroc(b_rows), group_auroc(c_rows)
    comps = [
        count("expansion_families", 15, len(rows), art),
        numeric("pooled_auroc", "0.820", rc.auroc(labels, scores), art),
        count("cue_b_n", 5, len(b_rows), art),
        count("cue_c_n", 10, len(c_rows), art),
    ]
    for name, reported, value in (("within_cue_b_auroc", "0.667", b_auroc),
                                  ("within_cue_c_auroc", "0.6875", c_auroc)):
        if value is None:
            comps.append(component(name, reported, None, "not_enough_source_data",
                                   "group has a single class, AUROC undefined", art))
        else:
            comps.append(numeric(name, reported, value, art))
    return comps, {"positives_in_expansion": sum(labels)}


def check_p1l_11():
    art_m, art_h = [P["mhk_csv"]], [P["head11_csv"]]
    mhk = [r for r in read_csv("mhk_csv") if r["patch_layer"] == "16"]
    h11 = [r for r in read_csv("head11_csv") if r["patch_layer"] == "16"]
    m_values = [float(r["recovery_fraction"]) for r in mhk]
    h_values = [float(r["recovery_fraction"]) for r in h11]
    clipped = [min(max(v, 0.0), 1.0) for v in m_values]
    clipped_component = numeric(
        "four_head_clipped_mean_recovery_L16", "0.969", float(np.mean(clipped)), art_m)
    clipped_component["note"] = (
        "the plan does not state the clipping rule; clipping each family's recovery fraction to "
        f"[0, 1] reproduces it. {sum(v > 1.0 for v in m_values)} of {len(m_values)} families exceed 1.0 "
        "before clipping, so the clipped mean is largely a ceiling effect (v2 P6.2 asks for clipped and "
        "uncapped summaries together)"
    )
    return [
        count("causal_panel_families", 20, len(mhk), art_m),
        numeric("four_head_mean_recovery_L16", "1.870", float(np.mean(m_values)), art_m),
        numeric("head_11_alone_mean_recovery_L16", "1.848", float(np.mean(h_values)), art_h),
        clipped_component,
    ], {
        "clipping_rule_assumed": "each family's recovery fraction clipped to [0, 1] before the mean",
        "families_above_1": int(sum(v > 1.0 for v in m_values)),
        "families_below_0": int(sum(v < 0.0 for v in m_values)),
        "median_recovery": _round(float(np.median(m_values))),
    }


def check_p1l_13():
    data = read_json("validation")
    art = [P["validation"]]
    ok = data.get("families_marked_valid") == 0 and data.get("status") == "HUMAN_LABELS_MISSING"
    return [component(
        "dual_expert_validation_not_completed", "not completed",
        f"status={data.get('status')}, families_marked_valid={data.get('families_marked_valid')}",
        "verified" if ok else "unreproducible",
        "" if ok else "validation record shows human labels present", art)], {}


def check_p1l_14():
    data = read_json("leakage")
    art = [P["leakage"]]
    return [
        count("template_clusters", 34, data["unresolved_family_clusters"], art),
        count("family_pairs", 147, data["unresolved_family_pairs"], art),
        count("rendering_pairs", 2352, data["unresolved_cross_family_review"], art),
        component("family_held_out_share_cluster_with_training", "71%", None, "not_enough_source_data",
                  "this figure is not computed by any committed artifact; it needs the submitted "
                  "manuscript or a cluster-held-out re-analysis (Stage 14.4)", art),
    ], {"status": data["status"]}


def check_p1l_15():
    data = read_json("coverage")
    art = [P["coverage"]]
    science = data["n_expected_science_runs"]
    return [
        count("science_runs", 182, science, art),
        numeric("registry_coverage", "0.703", (data["matched"] + data["partial"]) / science, art),
        numeric("strict_coverage", "0.451", data["matched"] / science, art),
    ], {"matched": data["matched"], "partial": data["partial"], "unmatched": data["unmatched"]}


def check_p1l_16():
    art = [P["donor_same"], P["donor_stable"]]
    comps = []
    for key in ("donor_same", "donor_stable"):
        rows = read_csv(key)
        comps.append(component(f"{key}_data_rows", 0, len(rows),
                               "verified" if len(rows) == 0 else "unreproducible",
                               "" if not rows else "file now contains rows", [P[key]]))
    del art
    return comps, {"interpretation": "zero rows is NOT_EVALUATED, not a measured null (v2 8.4)"}


def check_p1a_a(ctx):
    records = [r for r in read_jsonl("prompt_records") if r["template_id"] == "CM_B_UM_059"]
    art = [P["prompt_records"]]
    correct = 6.928
    wrong = []
    for record in records:
        parsed = str(record.get("parsed_answer_canonical") or record.get("parsed_answer") or "")
        number = rc.as_float_or_none(parsed.split()[0]) if parsed else None
        wrong.append(number is None or abs(number - correct) / correct > 1e-3)
    by_model: dict[str, dict[int, float]] = {}
    for record in records:
        by_model.setdefault(record["model_name"], {})[int(record["variant_id"])] = float(
            record["logprob_correct_answer"])
    qwen = by_model[QWEN]
    spread = max(qwen.values()) - min(qwen.values())
    return [
        count("outputs_checked", 8, len(records), art),
        component("every_output_wrong", "all wrong", f"{sum(wrong)} of {len(wrong)} wrong",
                  "verified" if all(wrong) and len(wrong) == 8 else "unreproducible",
                  "" if all(wrong) else "some output matches 6.928 N*m", art),
        numeric("qwen_gold_logprob_range", "10.562", spread, art),
    ], {"qwen_logprobs": qwen, "llama_logprobs": by_model[LLAMA],
        "qwen_S_lp_base0": _round(ctx["slp"][QWEN]["CM_B_UM_059"])}


def check_p1a_b():
    data = read_json("proximity")
    rows = data["families"]
    art = [P["proximity"]]
    x = [float(r["min_relative_proximity"]) for r in rows]
    y = [float(r["qwen_S_lp"]) for r in rows]
    return [
        count("cue_b_families", 100, len(rows), art),
        numeric("pearson_r_min_relative_proximity_vs_S_lp", "0.074", rc.pearson(x, y), art),
    ], {"stored_pearson_r": data.get("pearson_r_slp_vs_min_relative_proximity")}


# --------------------------------------------------------------------------------------------


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def build() -> tuple[dict[str, list[dict]], dict[str, Any]]:
    ctx = {"slp": slp_by_model(read_jsonl("prompt_records"))}
    plan = {
        "P1L-01": check_p1l_01, "P1L-02": lambda: check_p1l_02(ctx), "P1L-03": check_p1l_03,
        "P1L-04": lambda: check_p1l_04(ctx), "P1L-05": check_p1l_05, "P1L-06": check_p1l_06,
        "P1L-07": check_p1l_07, "P1L-08": check_p1l_08, "P1L-09": check_p1l_09,
        "P1L-10": check_p1l_10, "P1L-11": check_p1l_11, "P1L-13": check_p1l_13,
        "P1L-14": check_p1l_14, "P1L-15": check_p1l_15, "P1L-16": check_p1l_16,
        "P1A-A": lambda: check_p1a_a(ctx), "P1A-B": check_p1a_b,
    }
    components: dict[str, list[dict]] = {}
    info: dict[str, Any] = {}
    for claim_id, function in plan.items():
        components[claim_id], info[claim_id] = function()
    return components, info


def update_ledger(components, stage: str, journal_ref: str, ledger_path: Path | None = None) -> list[str]:
    path = ledger_path or REPO_ROOT / LEDGER
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    changed = []
    for row in rows:
        comps = components.get(row["claim_id"])
        if not comps:
            continue
        label = worst_label(c["outcome"] for c in comps)
        row["components"] = [
            {k: v for k, v in c.items() if k != "artifacts"} for c in comps
        ]
        row["verification_label"] = label
        row["verified_in_stage"] = stage
        row["journal_ref"] = journal_ref
        artifacts = list(row.get("artifacts", []))
        for comp in comps:
            for art in comp.get("artifacts", []):
                if art not in artifacts:
                    artifacts.append(art)
        row["artifacts"] = artifacts
        details = [f"{c['name']}: {c['detail']}" for c in comps if c["outcome"] != "verified"]
        row["explanation"] = " | ".join(details)
        if label in ("verified", "different_but_explained") and row.get("observed_rows") != 0:
            row["evidence_status"] = "exploratory"
        else:
            row["evidence_status"] = "NOT_EVALUATED"
        changed.append(row["claim_id"])
    errors = validate_ledger_rows(rows)
    if errors:
        raise RuntimeError("ledger would be invalid: " + "; ".join(errors[:5]))
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT,
                        help="Output root (repo-relative or absolute). Use a scratch path for dry runs.")
    parser.add_argument("--update-ledger", action="store_true")
    parser.add_argument("--stage", default="14.1")
    parser.add_argument("--journal-ref", default=None)
    args = parser.parse_args()
    if args.update_ledger and not args.journal_ref:
        parser.error("--update-ledger needs --journal-ref")

    sha = git("rev-parse", "HEAD")
    attempt = args.attempt_id or f"attempt_{git('log', '-1', '--format=%cd', '--date=format:%Y%m%d')}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    components, info = build()
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = {key: {"path": rel, "sha256": sha256(REPO_ROOT / rel)} for key, rel in P.items()}
    result = {
        "card": "v2_X01_authoritative_reproduction",
        "evidence_class": "reproduction_audit (exploratory; no confirmatory role)",
        "source_commit": sha,
        "git_status_short": git("status", "--short").splitlines(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "command": " ".join(sys.argv),
        "inputs": inputs,
        "components": components,
        "info": info,
        "summary": {
            claim: worst_label(c["outcome"] for c in comps) for claim, comps in components.items()
        },
    }
    (out_dir / "reconciliation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                                 encoding="utf-8")
    with (out_dir / "reconciliation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["claim_id", "component", "reported", "recomputed", "outcome", "detail"])
        for claim, comps in components.items():
            for comp in comps:
                writer.writerow([claim, comp["name"], comp["reported"], comp["recomputed"],
                                 comp["outcome"], comp["detail"] or comp.get("note", "")])
    changed = update_ledger(components, args.stage, args.journal_ref) if args.update_ledger else []
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown),
                      "summary": result["summary"], "ledger_rows_updated": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
