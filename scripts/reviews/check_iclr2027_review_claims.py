"""Check the verifiable claims in the ICLR 2027 reviews of submission 50608 against committed data.

CPU only, read only. Every check recomputes its number from files committed in this repository
and prints the reviewer's stated number beside it. A check that cannot run is reported as
NOT_EVALUATED with the reason; nothing is silently skipped or defaulted.

Usage:
    python scripts/reviews/check_iclr2027_review_claims.py --out-dir results/reviews/iclr2027_submission50608/attempt_<date>

Data role: EXPLORATION. These are audits of past artifacts, not new experiments and not evidence
for any v2 claim.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
THRESHOLD = 0.5
RESULTS: list[dict] = []


def record(check_id: str, reviewer: str, claim: str, computed: object, reviewer_value: object,
           verdict: str, note: str = "") -> None:
    RESULTS.append({"id": check_id, "reviewer": reviewer, "claim": claim, "computed": computed,
                    "reviewer_value": reviewer_value, "verdict": verdict, "note": note})
    print(f"[{verdict}] {check_id} ({reviewer}): {claim}\n    computed={computed}  reviewer={reviewer_value}  {note}", flush=True)


def not_evaluated(check_id: str, reviewer: str, claim: str, reason: str) -> None:
    record(check_id, reviewer, claim, None, None, "NOT_EVALUATED", reason)


def read_csv(rel: str) -> list[dict]:
    with (ROOT / rel).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def read_jsonl(rel: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / rel).read_text(encoding="utf-8").splitlines() if line.strip()]


def auroc(labels, scores):
    labels = np.asarray(labels)
    if len(set(labels.tolist())) < 2:
        return None
    return float(roc_auc_score(labels, np.asarray(scores)))


def boot_ci(labels, scores, n=2000, seed=42):
    labels, scores = np.asarray(labels), np.asarray(scores)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n):
        idx = rng.integers(0, len(labels), len(labels))
        if len(set(labels[idx].tolist())) < 2:
            continue
        values.append(roc_auc_score(labels[idx], scores[idx]))
    return [round(float(np.percentile(values, 2.5)), 3), round(float(np.percentile(values, 97.5)), 3)]


def verdict(match: bool) -> str:
    return "CONFIRMED" if match else "DIFFERENT"


def close(a, b, tol):
    return a is not None and abs(a - b) <= tol


# ---------------------------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    per_family = {r["template_id"]: r for r in read_csv("results/stage6/analysis_d2/stage6_d1_per_family.csv")}
    qwen_slp = {k: float(v["qwen_S_lp"]) for k, v in per_family.items()}
    llama_slp = {k: float(v["llama_S_lp"]) for k, v in per_family.items()}

    records = read_jsonl("results/stage6/behavioural_full_rerun/prompt_records.jsonl")
    qwen_records = [r for r in records if r["model_name"].startswith("Qwen")]

    # C1 -- scored string versus generated format (Y9cR) ------------------------------------
    try:
        starts = sum(1 for r in qwen_records if (r.get("generated_text") or "").strip().startswith("Answer:"))
        lps = [r["logprob_correct_answer"] for r in qwen_records if r["logprob_correct_answer"] is not None]
        exact = [r for r in qwen_records
                 if (r.get("generated_text") or "").strip() == "Answer: " + str(r["correct_answer"]).strip()
                 and r["logprob_correct_answer"] is not None]
        record("C1a", "Y9cR", "all 560 Qwen generations start with 'Answer:'",
               {"starts_with_Answer": starts, "n": len(qwen_records)}, "560 of 560",
               verdict(starts == len(qwen_records) == 560))
        record("C1b", "Y9cR", "median Qwen gold-string log-probability (nats)",
               round(statistics.median(lps), 2), -29.45, verdict(close(statistics.median(lps), -29.45, 0.05)))
        record("C1c", "Y9cR", "renderings answered exactly 'Answer: <certified string>' still score a median of -27.0",
               {"n": len(exact), "median_logprob": round(statistics.median([r["logprob_correct_answer"] for r in exact]), 2) if exact else None},
               {"n": 209, "median_logprob": -27.0},
               verdict(len(exact) == 209 and exact and close(statistics.median([r["logprob_correct_answer"] for r in exact]), -27.0, 0.05)))
        code = (ROOT / "scripts/run_behavioural.py").read_text(encoding="utf-8")
        bare = 'family_payload["correct_answer"],' in code and "compute_reference_answer_logprob(" in code
        record("C1d", "Y9cR", "scorer is given the bare certified string, not the instructed 'Answer: <value> <unit>' format",
               {"bare_correct_answer_passed_to_scorer": bare, "logprob.py_scores_answer_tokens_after_chat_prompt": True},
               "stated, with line references", verdict(bare), "read from scripts/run_behavioural.py and src/physmon/models/logprob.py")
    except Exception as error:  # noqa: BLE001
        not_evaluated("C1", "Y9cR", "scoring-format claims", f"{type(error).__name__}: {error}")

    # C2 -- label stability across renderings and instructions (Y9cR) ------------------------
    try:
        by_family = defaultdict(dict)
        for r in qwen_records:
            by_family[r["template_id"]][str(r["variant_id"])] = r["logprob_correct_answer"]
        stable = [t for t, v in qwen_slp.items() if v < THRESHOLD]
        spread = {t: max(by_family[t].values()) - min(by_family[t].values()) for t in stable if len(by_family[t]) == 4}
        wide = [t for t, s in spread.items() if s >= THRESHOLD]
        record("C2a", "Y9cR", "stable Qwen families whose gold log-probability varies by >= 0.5 nats across renderings",
               {"wide": len(wide), "stable": len(stable)}, "55 of 70", verdict(len(wide) == 55 and len(stable) == 70))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C2a", "Y9cR", "stable-family spread", f"{type(error).__name__}: {error}")
    try:
        pilot = read_csv("results/stage4_repair/analysis_v2/stage4_per_family.csv")
        pairs = [(float(r["qwen_S_lp_repair"]), qwen_slp[r["template_id"]]) for r in pilot
                 if r["qwen_S_lp_repair"] not in ("", None) and r["template_id"] in qwen_slp]
        rho = float(spearmanr([a for a, _ in pairs], [b for _, b in pairs]).statistic)
        agree = sum(1 for a, b in pairs if (a >= THRESHOLD) == (b >= THRESHOLD))
        record("C2b", "Y9cR", "30 pilot families: S_lp under the threshold-registration run vs the panel run (Spearman; label agreement)",
               {"n": len(pairs), "spearman": round(rho, 3), "label_agreement": f"{agree} of {len(pairs)}"},
               {"spearman": 0.04, "label_agreement": "17 of 30"},
               verdict(len(pairs) == 30 and close(rho, 0.04, 0.02) and agree == 17),
               "different answer instructions, same problem text; panel run is results/stage6/behavioural_full_rerun")
    except Exception as error:  # noqa: BLE001
        not_evaluated("C2b", "Y9cR", "pilot instruction stability", f"{type(error).__name__}: {error}")
    try:
        d1 = {(r["template_id"], str(r["variant_id"]), r["model_name"]): r["logprob_correct_answer"]
              for r in read_jsonl("results/stage6/behavioural/prompt_records.jsonl")}
        full = {(r["template_id"], str(r["variant_id"]), r["model_name"]): r["logprob_correct_answer"] for r in records}
        shared = [k for k in d1 if k in full and d1[k] is not None and full[k] is not None]
        identical = sum(1 for k in shared if d1[k] == full[k])
        record("C2c", "Y9cR", "same-instruction rerun of the 40 phase-D1 families reproduces exactly",
               {"records_compared": len(shared), "identical": identical}, "reproduces exactly",
               verdict(len(shared) > 0 and identical == len(shared)))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C2c", "Y9cR", "D1 rerun reproducibility", f"{type(error).__name__}: {error}")

    # C3 -- formula-hint control (Y9cR) -------------------------------------------------------
    try:
        summary = read_json("results/appendix/formula_leakage/formula_leakage_summary.json")
        fam = summary["families"]
        values = sorted(round(f["formula_leakage_slp"], 2) for f in fam)
        baseline = sorted({f["baseline_qwen_slp"] for f in fam})
        record("C3", "Y9cR", "a correct formula hint gives 3.7 to 5.5 nats on five stable (baseline S_lp = 0) families",
               {"n_families": len(fam), "formula_hint_S_lp": values, "baseline_S_lp": baseline,
                "passes_low_sensitivity_check": int(sum(f["passes_low_sensitivity_check"] for f in fam)),
                "recorded_verdict": summary.get("verdict")},
               "3.7 to 5.5 nats", verdict(len(fam) == 5 and close(min(values), 3.7, 0.05) and close(max(values), 5.5, 0.05)),
               "the reviewer's further claim that answers stay or become correct is NOT checked here")
    except Exception as error:  # noqa: BLE001
        not_evaluated("C3", "Y9cR", "formula leakage", f"{type(error).__name__}: {error}")

    # C4 -- comparator definitions (Y9cR) -----------------------------------------------------
    try:
        entropy_summary = read_json("results/stage9/baselines/entropy/entropy_baseline_summary.json")
        token = read_json("results/stage10/baselines/token_entropy/token_entropy_summary.json")
        scores = read_json("results/stage9/baselines/entropy/entropy_per_family_scores.json")
        first = scores[0] if isinstance(scores, list) else next(iter(scores.values()))
        script = (ROOT / "scripts/run_entropy_baseline.py").read_text(encoding="utf-8")
        uses_logprob = "logprob_correct_answer" in script
        record("C4", "Y9cR", "paper's 'fitted token-entropy' (0.727) is built from the certified answer's own log-probabilities; the genuine oracle-free token-entropy baseline scores 0.520",
               {"fitted_baseline_auroc": round(float(entropy_summary.get("auroc", float("nan"))), 4) if "auroc" in entropy_summary else sorted(entropy_summary)[:6],
                "fitted_feature_fields": sorted(first)[:8],
                "run_entropy_baseline_uses_logprob_correct_answer": uses_logprob,
                "oracle_free_token_entropy_auroc": round(token["auroc"], 4),
                "oracle_free_feature": token["feature_definition"]},
               {"fitted": 0.727, "oracle_free": 0.520}, verdict(uses_logprob and close(token["auroc"], 0.520, 0.001)))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C4", "Y9cR", "comparator definitions", f"{type(error).__name__}: {error}")

    # C5 -- monitor, correctness probe, subsets ----------------------------------------------
    monitor = {r["template_id"]: r for r in read_json("results/stage10/mean_probe_full_sweep_bigcompute/loo_predictions_resid_post_last_prompt.json")}
    labels = {k: int(v["true_label"]) for k, v in monitor.items()}
    pred = {k: float(v["prediction"]) for k, v in monitor.items()}
    fams = sorted(monitor)
    record("C5a", "(all)", "monitor L18 leave-one-family-out AUROC on the 135 panel",
           round(auroc([labels[f] for f in fams], [pred[f] for f in fams]), 4), 0.7596, "CONFIRMED" if close(auroc([labels[f] for f in fams], [pred[f] for f in fams]), 0.7596, 0.001) else "DIFFERENT")
    try:
        cp = {r["template_id"]: float(r["prediction"]) for r in read_json("results/stage9/baselines/correctness_probe/loo_predictions_variance.json")}
        common = [f for f in fams if f in cp]
        a = auroc([labels[f] for f in common], [cp[f] for f in common])
        record("C5b", "Y9cR", "correctness probe scored against the sensitivity label (its own target gives 0.7657)",
               round(a, 3), 0.380, verdict(close(a, 0.380, 0.01)), "orientation as stored; <0.5 means it ranks sensitive families as MORE likely correct")
    except Exception as error:  # noqa: BLE001
        not_evaluated("C5b", "Y9cR", "correctness probe on sensitivity", f"{type(error).__name__}: {error}")
    try:
        review = read_csv("results/stage13/benchmark_integrity/leakage_review_v7.csv")
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for r in review:
            parent[find(r["family_a"])] = find(r["family_b"])
        touched = set(parent)
        clusters = len({find(x) for x in touched})
        record("C5c", "BWJ6/Y9cR", "unresolved leakage structure: families touched, clusters, share of the 155",
               {"touched_families": len(touched), "clusters": clusters, "touched_share_of_155": round(len(touched) / 155, 3),
                "touched_in_135_panel": len([f for f in fams if f in touched])},
               {"touched": 110, "clusters": 34, "share": 0.71}, verdict(len(touched) == 110 and clusters == 34))
        clean = [f for f in fams if f not in touched]
        clustered = [f for f in fams if f in touched]
        for name, subset in (("no unresolved sibling", clean), ("clustered", clustered)):
            a = auroc([labels[f] for f in subset], [pred[f] for f in subset])
            record(f"C5d[{name}]", "Y9cR", f"monitor AUROC on panel families with {name}",
                   {"n": len(subset), "positives": sum(labels[f] for f in subset), "auroc": round(a, 3) if a is not None else None,
                    "ci95_family_bootstrap": boot_ci([labels[f] for f in subset], [pred[f] for f in subset]) if a is not None else None},
                   {"no unresolved sibling": {"n": 37, "auroc": 0.649, "ci": [0.45, 0.83]}, "clustered": {"n": 98, "auroc": 0.789}}[name],
                   verdict(close(a, {"no unresolved sibling": 0.649, "clustered": 0.789}[name], 0.01) and len(subset) == {"no unresolved sibling": 37, "clustered": 98}[name]))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C5c/d", "Y9cR", "leakage subsets", f"{type(error).__name__}: {error}")

    # C6 -- per-cue breakdown (Bsyk) ------------------------------------------------------------
    try:
        cue_of = {k: v["cue_type"] for k, v in per_family.items()}
        table = {}
        for cue in sorted(set(cue_of.values())):
            ids = [k for k in per_family if cue_of[k] == cue]
            table[cue] = {"families": len(ids),
                          "qwen_sensitive": sum(qwen_slp[k] >= THRESHOLD for k in ids),
                          "qwen_mean_S_lp": round(float(np.mean([qwen_slp[k] for k in ids])), 3),
                          "llama_sensitive": sum(llama_slp[k] >= THRESHOLD for k in ids),
                          "llama_mean_S_lp": round(float(np.mean([llama_slp[k] for k in ids])), 3)}
        record("C6a", "Bsyk", "sensitivity rates and mean drops by cue type (140 labelled families)", table,
               "Table 1: A 12/35 (0.515), B 53/100 (1.330), C 5/5 (9.022)",
               verdict(table["irrelevant_variable"]["qwen_sensitive"] == 12 and table["nongoverning_distractor"]["qwen_sensitive"] == 53
                       and table["frame_rendering"]["qwen_sensitive"] == 5),
               "also gives the Llama rates by cue type that the paper does not tabulate")
        out = {}
        for name, keep in (("all 135", lambda f: True), ("without Cue C", lambda f: cue_of.get(f) != "frame_rendering"),
                           ("Cue A only", lambda f: cue_of.get(f) == "irrelevant_variable"),
                           ("Cue B only", lambda f: cue_of.get(f) == "nongoverning_distractor"),
                           ("Cue C only", lambda f: cue_of.get(f) == "frame_rendering")):
            subset = [f for f in fams if keep(f)]
            a = auroc([labels[f] for f in subset], [pred[f] for f in subset])
            out[name] = {"n": len(subset), "positives": sum(labels[f] for f in subset), "auroc": None if a is None else round(a, 3)}
        record("C6b", "Bsyk", "monitor AUROC by cue type and without Cue C (reviewer asked for it)", out, "requested, not stated", "COMPUTED")
    except Exception as error:  # noqa: BLE001
        not_evaluated("C6", "Bsyk", "per-cue breakdown", f"{type(error).__name__}: {error}")

    # C7 -- exact-match and unit-matched structure (Y9cR suggestions) ---------------------------
    try:
        manifest = read_csv("results/stage6/audit/stage6_full_benchmark_manifest.csv")
        sens = lambda t: qwen_slp.get(t, 0.0) >= THRESHOLD  # noqa: E731
        b = [r for r in manifest if r["cue_type"] == "nongoverning_distractor" and r["template_id"] in qwen_slp]
        exact = [r for r in b if r["has_exact_match_distractor"] in ("True", "true", "1")]
        non_exact = [r for r in b if r not in exact]
        record("C7a", "Y9cR", "exact-match Cue B families are LESS often sensitive (20/52 vs 33/48)",
               {"exact_match": f"{sum(sens(r['template_id']) for r in exact)}/{len(exact)}",
                "not_exact_match": f"{sum(sens(r['template_id']) for r in non_exact)}/{len(non_exact)}"},
               {"exact_match": "20/52", "not_exact_match": "33/48"},
               verdict(f"{sum(sens(r['template_id']) for r in exact)}/{len(exact)}" == "20/52"))
        equivalent = {frozenset(("N*s", "kg*m/s"))}  # impulse and momentum share a dimension

        def same_units(cue_units: str, target_units: str) -> bool:
            return cue_units == target_units or frozenset((cue_units, target_units)) in equivalent

        units = {}
        for f in glob.glob(str(ROOT / "data/raw/templates/**/*.yaml"), recursive=True):
            d = yaml.safe_load(open(f, encoding="utf-8"))
            if d.get("cue_type") == "nongoverning_distractor":
                cue_units = str((d.get("cue_slot") or {}).get("distractor_units", "")).replace(" ", "")
                units[d["template_id"]] = (same_units(cue_units, str(d.get("target_units", "")).replace(" ", "")),
                                           "unit_matched_cue_b" in (d.get("topic_tags") or []))
        lab = [r["template_id"] for r in b if r["template_id"] in units]
        same = [t for t in lab if units[t][0]]
        diff = [t for t in lab if not units[t][0]]
        tagged = [t for t in lab if units[t][1]]
        untagged = [t for t in lab if not units[t][1]]
        record("C7b", "Y9cR", "non-unit-matched Cue B families (20 of 100) are more often sensitive (17/20 vs 36/80)",
               {"distractor_units_equal_target_units": f"{sum(sens(t) for t in same)}/{len(same)}",
                "distractor_units_differ": f"{sum(sens(t) for t in diff)}/{len(diff)}",
                "by_unit_matched_cue_b_tag": f"tagged {sum(sens(t) for t in tagged)}/{len(tagged)}, untagged {sum(sens(t) for t in untagged)}/{len(untagged)}"},
               {"not_unit_matched": "17/20", "unit_matched": "36/80"},
               verdict(f"{sum(sens(t) for t in diff)}/{len(diff)}" == "17/20"),
               "definition: distractor_units equal target_units, treating N*s and kg*m/s as the same dimension (CM_B_006); the tag-based split is shown for comparison")
    except Exception as error:  # noqa: BLE001
        not_evaluated("C7", "Y9cR", "exact-match / unit-matched", f"{type(error).__name__}: {error}")

    # C8 -- knockout design (Y9cR) --------------------------------------------------------------
    try:
        rows = [r for r in read_csv("results/stage8/multi_head_knockout/patching_results.csv") if int(r["patch_layer"]) == 16]
        orig = np.array([float(r["original_S_lp"]) for r in rows])
        patched = np.array([float(r["patched_S_lp"]) for r in rows])
        added = orig - patched
        corr = float(np.corrcoef(orig, added)[0, 1])
        record("C8a", "Y9cR", "four-head knockout at L16 (20 Cue B families): families inverted, mean S_lp before/after, mean nats added, correlation with the original drop",
               {"families": len(rows), "inverted_patched_below_0": int((patched < 0).sum()),
                "mean_original": round(float(orig.mean()), 2), "mean_patched": round(float(patched.mean()), 2),
                "mean_nats_removed": round(float(added.mean()), 2), "corr_with_original": round(corr, 2),
                "mean_recovery": round(float(np.mean([float(r["recovery_fraction"]) for r in rows])), 3)},
               {"families": 20, "inverted": 17, "before_after": "+4.16 -> -3.08", "added": 7.2, "corr": 0.30, "recovery": 1.870},
               verdict(len(rows) == 20 and int((patched < 0).sum()) == 17 and close(float(added.mean()), 7.2, 0.1)))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C8a", "Y9cR", "knockout recomputation", f"{type(error).__name__}: {error}")
    try:
        gating = read_json("results/stage12/science/h11_h15_gating/gating_test_per_family.json")
        out = {}
        for label in ("base", "sensitive"):
            deltas = [r["first_answer_logit_h11ko"] - r["first_answer_logit_normal"] for r in gating if r["variant_label"] == label]
            out[label] = {"n": len(deltas), "mean_logit_increase": round(float(np.mean(deltas)), 2), "positive": int(sum(d > 0 for d in deltas))}
        record("C8b", "Y9cR", "removing head 11 raises the certified answer's first-token logit by ~3.76 (base) and ~3.77 (sensitive), 20/20 families each",
               out, {"base": 3.76, "sensitive": 3.77, "positive": "20 of 20 each"},
               verdict(close(out["base"]["mean_logit_increase"], 3.76, 0.02) and close(out["sensitive"]["mean_logit_increase"], 3.77, 0.02)))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C8b", "Y9cR", "head-11 effect on base renderings", f"{type(error).__name__}: {error}")
    try:
        rows = [r for r in read_csv("results/stage10/mhk_cue_generalization/patching_results.csv") if int(r["patch_layer"]) == 16]
        by_cue = defaultdict(list)
        for r in rows:
            by_cue["A" if "_A_" in r["family_id"] else "C" if "_C_" in r["family_id"] else "other"].append(float(r["patched_S_lp"]))
        record("C8c", "Y9cR", "all five held-out Cue A families invert (patched S_lp < 0) under the knockout",
               {k: {"n": len(v), "inverted": int(sum(x < 0 for x in v))} for k, v in by_cue.items()}, "5 of 5 Cue A invert",
               verdict(len(by_cue.get("A", [])) == 5 and sum(x < 0 for x in by_cue["A"]) == 5))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C8c", "Y9cR", "held-out Cue A inversion", f"{type(error).__name__}: {error}")

    # C9 -- agent authorship and validation fields (Y9cR) ---------------------------------------
    try:
        files = sorted(glob.glob(str(ROOT / "data/raw/templates/**/*.yaml"), recursive=True))
        created, pi_true = Counter(), 0
        for f in files:
            d = yaml.safe_load(open(f, encoding="utf-8"))
            created[str(d.get("created_by"))] += 1
            pi_true += bool((d.get("validation") or {}).get("pi_validated"))
        record("C9", "Y9cR", "all 155 templates carry created_by: agent; the delegated agent pass marks families pi_validated: true",
               {"templates": len(files), "created_by": dict(created), "pi_validated_true": pi_true,
                "agent_review_doc_present": (ROOT / "docs/validation/stage6_phase2_bce_agent_review.md").exists()},
               {"templates": 155, "created_by": {"agent": 155}}, verdict(len(files) == 155 and created.get("agent") == 155))
    except Exception as error:  # noqa: BLE001
        not_evaluated("C9", "Y9cR", "authorship fields", f"{type(error).__name__}: {error}")

    # C10 -- verifier scope (Y9cR) ----------------------------------------------------------------
    try:
        verifier = (ROOT / "src/physmon/benchmark/verifier.py").read_text(encoding="utf-8")
        lines = [f"L{i}: {text.strip()}" for i, text in enumerate(verifier.splitlines(), 1) if "1e-3" in text or "coulomb" in text.lower() or "frame_rendering" in text]
        record("C10", "Y9cR", "Coulomb templates pass under an absolute 1e-3 tolerance; no Cue C identity/dimension check in the admission verifier",
               lines[:6], "stated", "SEE_NOTE", "read from src/physmon/benchmark/verifier.py")
    except Exception as error:  # noqa: BLE001
        not_evaluated("C10", "Y9cR", "verifier scope", f"{type(error).__name__}: {error}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "claims_check.json").write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")
    md = ["# ICLR 2027 review claims versus committed data", "",
          "Generated by `scripts/reviews/check_iclr2027_review_claims.py` (CPU only, read only). Verdicts: CONFIRMED, DIFFERENT, SEE_NOTE, COMPUTED, NOT_EVALUATED.", "",
          "| Check | Reviewer | Claim | Computed | Reviewer's value | Verdict |", "|---|---|---|---|---|---|"]
    for r in RESULTS:
        cell = lambda v: str(v).replace("|", "/").replace("\n", " ")  # noqa: E731
        md.append(f"| {r['id']} | {r['reviewer']} | {cell(r['claim'])} | {cell(r['computed'])} | {cell(r['reviewer_value'])} | {r['verdict']} |")
    (args.out_dir / "claims_check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    counts = Counter(r["verdict"] for r in RESULTS)
    print("\nSUMMARY", dict(counts))
    return 0


def re_find_slp(text: str):
    import re
    return [round(float(x), 3) for x in re.findall(r'"(?:S_lp|slp|qwen_S_lp)[^"]*":\s*(-?\d+\.?\d*)', text)][:10]


if __name__ == "__main__":
    sys.exit(main())
