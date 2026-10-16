#!/usr/bin/env python3
"""Stage 14.4: structure overlap, cluster-held-out baselines, and the five excluded families (CPU only).

Reconstructs the 34 structure clusters from the committed unresolved cross-family review, reconciles the plan's
"71% of family-held-out tests share a cluster with training", compares family-held-out (leave-one-family-out)
with cluster-held-out (leave-one-cluster-out) evaluation for predictors that need no activations, splits the
stored out-of-fold predictions by cluster exposure, and examines the parse-failure exclusion of five families.

The hidden-state monitor itself cannot be re-fitted under cluster-held-out folds here: the activation tensors
were lost in the October 2026 scratch wipe. Its cluster-held-out AUROC is therefore NOT_EVALUATED; only its stored
leave-one-family-out predictions are analysed. The label is the legacy Qwen `S_lp >= 0.5` label, used here as the
historical Phase-I target (the legacy label is not a primary endpoint for new claims; journal J14.2-008).

Plan reference: B1.4, B1.6 (p.7-8), P0.4 (p.16), P3.5-P3.6 (p.20), card X05 (p.40), B05 and B08 (p.32).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance import cluster as cl  # noqa: E402
from physmon.governance import recompute as rc  # noqa: E402
from physmon.governance.v2_contract import validate_ledger_rows, worst_label  # noqa: E402

OUT_ROOT = "results/stage14/s144_structure_overlap"
LEDGER = "docs/registry/v2/claim_ledger.jsonl"
SEED = 42
N_BOOT = 2000

INPUTS = {
    "review": "results/stage13/benchmark_integrity/leakage_review_v7.csv",
    "leakage_audit": "results/stage13/benchmark_integrity/leakage_audit_v7.json",
    "manifest": "data/manifests/physmon_canonical_155.jsonl",
    "per_family": "results/stage6/analysis_d2/stage6_d1_per_family.csv",
    "rendered": "results/stage6/generated_full_benchmark",
    "monitor_oof": "results/stage10/mean_probe_full_sweep_bigcompute/loo_predictions_resid_post_last_prompt.json",
    "entropy_oof": "results/stage9/baselines/entropy/entropy_per_family_scores.json",
    "combined_oof": "results/wave2/combined_baseline/combined_baseline_predictions.json",
    "prompt_records": "results/stage6/behavioural_full_rerun/prompt_records.jsonl",
}


def read_json(key: str):
    return json.loads((REPO_ROOT / INPUTS[key]).read_text(encoding="utf-8"))


def read_csv(key: str) -> list[dict]:
    with (REPO_ROOT / INPUTS[key]).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


# ---------------------------------------------------------------------------------------------
# Clusters and exposure
# ---------------------------------------------------------------------------------------------


def build_clusters() -> tuple[dict[str, str], list[tuple[str, str]], dict[str, dict]]:
    manifest = {r["canonical_family_id"]: r for r in map(json.loads, (REPO_ROOT / INPUTS["manifest"]).read_text(
        encoding="utf-8").splitlines()) if r.get("canonical_family_id")}
    pairs = sorted({tuple(sorted((r["family_a"], r["family_b"]))) for r in read_csv("review")})
    cluster_of = cl.union_find_components(sorted(manifest), pairs)
    return cluster_of, pairs, manifest


def exposure_summary(cluster_of, pairs, manifest, cohort: list[str]) -> dict[str, Any]:
    in_review = {f for p in pairs for f in p}
    sizes_all = cl.cluster_sizes(cluster_of)
    non_singleton = {c: s for c, s in sizes_all.items() if s >= 2}
    exposure = cl.loo_exposure(cohort, cluster_of)
    exposed_n = sum(exposure.values())
    return {
        "n_canonical_families": len(manifest),
        "n_family_pairs": len(pairs),
        "n_families_in_unresolved_review": len(in_review),
        "n_clusters_with_two_or_more_families": len(non_singleton),
        "cluster_size_distribution": sorted(non_singleton.values(), reverse=True),
        "n_singleton_families": sum(1 for s in sizes_all.values() if s == 1),
        "share_of_all_155_families_in_a_cluster": len(in_review) / len(manifest),
        "cohort_size": len(cohort),
        "cohort_exposed_under_leave_one_family_out": exposed_n,
        "cohort_share_exposed_under_leave_one_family_out": exposed_n / len(cohort),
        "exposed_by_cue_type": {
            cue: [sum(1 for f in cohort if manifest[f]["cue_type"] == cue and exposure[f]),
                  sum(1 for f in cohort if manifest[f]["cue_type"] == cue)]
            for cue in sorted({manifest[f]["cue_type"] for f in cohort})
        },
    }, exposure


# ---------------------------------------------------------------------------------------------
# Features and cross-validated baselines
# ---------------------------------------------------------------------------------------------


def prompt_text(template_id: str) -> str:
    family = json.loads((REPO_ROOT / INPUTS["rendered"] / f"{template_id}.json").read_text(encoding="utf-8"))
    variant = min(family["variants"], key=lambda v: int(v["variant_id"]))
    return str(variant["prompt"])


def prompt_stats(text: str) -> list[float]:
    numbers = re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)
    return [float(len(text)), float(len(text.split())), float(sum(ch.isdigit() for ch in text)),
            float(len(numbers)), float(len(re.findall(r"[.?!]", text)))]


def oof_predictions(fit_predict, n: int, splits) -> np.ndarray:
    out = np.full(n, np.nan)
    for train, test in splits:
        out[test] = fit_predict(train, test)
    if np.isnan(out).any():
        raise RuntimeError("some rows received no out-of-fold prediction")
    return out


def make_predictors(families, labels, manifest, per_family, entropy):
    from scipy import sparse
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    y = np.asarray(labels)
    texts = [prompt_text(f) for f in families]
    stats = np.asarray([prompt_stats(t) for t in texts])
    meta = [[per_family[f]["governing_law"], manifest[f]["cue_type"], manifest[f]["domain"]] for f in families]
    ent = None
    if entropy is not None:
        ent = np.asarray([[entropy[f]["entropy_proxy_score"], entropy[f]["mean_logprob_correct_answer"]]
                          for f in families])

    def lr():
        return LogisticRegression(C=1.0, max_iter=2000)

    def fit_dense(builder):
        def run(train, test):
            enc = builder()
            xtr = enc.fit_transform(train)
            xte = enc.transform(test)
            model = lr().fit(xtr, y[train])
            return model.predict_proba(xte)[:, 1]
        return run

    class Meta:
        def fit_transform(self, idx):
            self.enc = OneHotEncoder(handle_unknown="ignore")
            return self.enc.fit_transform([meta[i] for i in idx])

        def transform(self, idx):
            return self.enc.transform([meta[i] for i in idx])

    class Tfidf:
        def fit_transform(self, idx):
            self.enc = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            return self.enc.fit_transform([texts[i] for i in idx])

        def transform(self, idx):
            return self.enc.transform([texts[i] for i in idx])

    class Dense:
        def __init__(self, matrix):
            self.matrix = matrix

        def fit_transform(self, idx):
            self.enc = StandardScaler()
            return self.enc.fit_transform(self.matrix[idx])

        def transform(self, idx):
            return self.enc.transform(self.matrix[idx])

    class Combined:
        def fit_transform(self, idx):
            self.meta, self.stats, self.ent = Meta(), Dense(stats), Dense(ent)
            return sparse.hstack([self.meta.fit_transform(idx), self.stats.fit_transform(idx),
                                  self.ent.fit_transform(idx)]).tocsr()

        def transform(self, idx):
            return sparse.hstack([self.meta.transform(idx), self.stats.transform(idx),
                                  self.ent.transform(idx)]).tocsr()

    predictors = {
        "metadata_law_cue_domain": fit_dense(Meta),
        "tfidf_prompt_text": fit_dense(Tfidf),
        "prompt_statistics": fit_dense(lambda: Dense(stats)),
    }
    if ent is not None:
        predictors["fitted_entropy_features"] = fit_dense(lambda: Dense(ent))
        predictors["combined_non_activation"] = fit_dense(Combined)
    return predictors


def cv_comparison(families, labels, cluster_of, manifest, per_family, entropy) -> dict[str, Any]:
    y = np.asarray(labels)
    n = len(families)
    groups = [cluster_of[f] for f in families]
    predictors = make_predictors(families, labels, manifest, per_family, entropy)
    result: dict[str, Any] = {"n_families": n, "n_positive": int(y.sum()), "n_clusters": len(set(groups)),
                              "seed": SEED, "bootstrap_resamples": N_BOOT, "predictors": {}}
    for name, fit_predict in predictors.items():
        loo = oof_predictions(fit_predict, n, cl.leave_one_out(n))
        loco = oof_predictions(fit_predict, n, cl.leave_one_group_out(groups))
        a_loo, a_loco = rc.auroc(y, loo), rc.auroc(y, loco)

        def diff(index, loo=loo, loco=loco):
            if len(set(y[index].tolist())) < 2:
                return None
            return rc.auroc(y[index], loo[index]) - rc.auroc(y[index], loco[index])

        ci = cl.cluster_bootstrap(groups, diff, n_resamples=N_BOOT, seed=SEED)
        result["predictors"][name] = {
            "auroc_leave_one_family_out": a_loo,
            "auroc_leave_one_cluster_out": a_loco,
            "difference_family_minus_cluster": a_loo - a_loco,
            "difference_cluster_bootstrap": ci,
        }
    return result


def exposure_split(name, labels, scores, families, exposure, cluster_of) -> dict[str, Any]:
    y = np.asarray(labels)
    s = np.asarray(scores)
    out: dict[str, Any] = {"n": len(families)}
    for tag, mask in (("all", np.ones(len(families), bool)),
                      ("exposed_to_cluster_mate_in_training", np.array([exposure[f] for f in families])),
                      ("singleton_no_cluster_mate", np.array([not exposure[f] for f in families]))):
        idx = np.where(mask)[0]
        groups = [cluster_of[families[i]] for i in idx]
        value = cl.auroc_or_none(y[idx], s[idx])

        def stat(index, idx=idx):
            sel = idx[index]
            return cl.auroc_or_none(y[sel], s[sel])

        ci = cl.cluster_bootstrap(groups, stat, n_resamples=N_BOOT, seed=SEED) if value is not None else None
        out[tag] = {"n": int(idx.size), "n_positive": int(y[idx].sum()), "auroc": value, "cluster_bootstrap": ci}
    out["name"] = name
    return out


# ---------------------------------------------------------------------------------------------
# The five excluded families
# ---------------------------------------------------------------------------------------------


def excluded_five(per_family_rows, cohort) -> dict[str, Any]:
    degraded = [r for r in per_family_rows if r["notes"].startswith("qwen_degraded")]
    rows = []
    for r in degraded:
        slp = float(r["qwen_S_lp"])
        rows.append({"template_id": r["template_id"], "cue_type": r["cue_type"], "qwen_S_lp": slp,
                     "qwen_parse_ok": r["qwen_parse_ok"], "qwen_label_at_0.5nat": int(slp >= 0.5),
                     "in_135_cohort": r["template_id"] in cohort})
    excluded = [r for r in rows if not r["in_135_cohort"]]
    kept = [r for r in rows if r["in_135_cohort"]]
    outcome_dependent = (all(r["qwen_label_at_0.5nat"] == 0 for r in excluded)
                         and all(r["qwen_label_at_0.5nat"] == 1 for r in kept))
    nondegraded_failures = sum(1 for r in per_family_rows
                               if not r["notes"].startswith("qwen_degraded") and r["qwen_parse_ok"] == "False")
    return {
        "n_qwen_parse_failure_families": len(rows),
        "excluded": excluded,
        "kept_despite_parse_failure": kept,
        "exclusion_depends_on_the_outcome_label": outcome_dependent,
        "qwen_parse_failures_outside_the_degraded_set": nondegraded_failures,
        "prevalence_with_the_five": {"positives": 70, "n": 140, "share": 70 / 140},
        "prevalence_in_135_cohort": {"positives": 70, "n": 135, "share": 70 / 135},
        "s_lp_needs_free_generation_parsing": False,
        "note": ("S_lp is a teacher-forced log-probability difference and is defined for all 140 families "
                 "(all five excluded families have a finite S_lp); the exclusion was not needed to compute "
                 "the label. Excluding only parse-failed families that are negative is an outcome-dependent "
                 "inclusion rule (v2 P0.4, B08)."),
    }


# ---------------------------------------------------------------------------------------------


def update_ledger(summary, journal_ref: str, ledger_path: Path | None = None) -> list[str]:
    path = ledger_path or REPO_ROOT / LEDGER
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    exp = summary["exposure"]
    changed = []
    for row in rows:
        if row["claim_id"] != "P1L-14":
            continue
        comps = [c for c in row["components"] if c["name"] != "family_held_out_share_cluster_with_training"]
        comps.append({
            "name": "family_held_out_share_cluster_with_training",
            "reported": "71%",
            "recomputed": f"{exp['n_families_in_unresolved_review']}/{exp['n_canonical_families']} = "
                          f"{exp['share_of_all_155_families_in_a_cluster']:.4f} (all canonical families); "
                          f"{exp['cohort_exposed_under_leave_one_family_out']}/{exp['cohort_size']} = "
                          f"{exp['cohort_share_exposed_under_leave_one_family_out']:.4f} (135-family monitoring "
                          "cohort under leave-one-family-out)",
            "outcome": "different_but_explained",
            "detail": "71% reproduces as the share of all 155 canonical families that sit in a cluster of two or "
                      "more; for the 135-family monitoring cohort under leave-one-family-out the share is "
                      f"{exp['cohort_share_exposed_under_leave_one_family_out']:.1%}. The plan does not say which "
                      "denominator it used.",
        })
        row["components"] = comps
        row["verification_label"] = worst_label(c["outcome"] for c in comps)
        row["verified_in_stage"] = "14.1, 14.4"
        row["journal_ref"] = f"J14.1-008, {journal_ref}"
        row["explanation"] = " | ".join(f"{c['name']}: {c['detail']}" for c in comps if c["outcome"] != "verified")
        row["evidence_status"] = "exploratory"
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
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--update-ledger", action="store_true")
    parser.add_argument("--journal-ref", default=None)
    args = parser.parse_args()
    if args.update_ledger and not args.journal_ref:
        parser.error("--update-ledger needs --journal-ref")

    sha = git("rev-parse", "HEAD")
    day = git("log", "-1", "--format=%cd", "--date=format:%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    import sklearn

    cluster_of, pairs, manifest = build_clusters()
    per_family_rows = read_csv("per_family")
    per_family = {r["template_id"]: r for r in per_family_rows}
    monitor = read_json("monitor_oof")
    cohort = [r["template_id"] for r in monitor]
    cohort_labels = {r["template_id"]: int(r["true_label"]) for r in monitor}
    exposure_info, exposure = exposure_summary(cluster_of, pairs, manifest, cohort)

    entropy_rows = {r["template_id"]: r for r in read_json("entropy_oof")}
    families_135 = sorted(cohort)
    labels_135 = [cohort_labels[f] for f in families_135]
    cv_135 = cv_comparison(families_135, labels_135, cluster_of, manifest, per_family, entropy_rows)

    families_140 = sorted(per_family)
    labels_140 = [int(float(per_family[f]["qwen_S_lp"]) >= 0.5) for f in families_140]
    cv_140 = cv_comparison(families_140, labels_140, cluster_of, manifest, per_family, None)

    stored = {}
    for key, name in (("monitor_oof", "hidden_state_monitor_layer18_stored_LOO"),
                      ("entropy_oof", "fitted_entropy_stored_LOO"),
                      ("combined_oof", "combined_non_activation_stored_nested_CV")):
        rows = read_json(key)
        by_id = {r["template_id"]: r for r in rows}
        stored[name] = exposure_split(name, [by_id[f]["true_label"] for f in families_135],
                                      [by_id[f]["prediction"] for f in families_135], families_135,
                                      exposure, cluster_of)
    # A non-activation predictor fitted leave-one-family-out, split the same way (template recognition probe).
    meta_pred = make_predictors(families_135, labels_135, manifest, per_family, entropy_rows)
    for name in ("metadata_law_cue_domain", "tfidf_prompt_text"):
        loo = oof_predictions(meta_pred[name], len(families_135), cl.leave_one_out(len(families_135)))
        stored[f"{name}_refit_LOO"] = exposure_split(name, labels_135, loo, families_135, exposure, cluster_of)

    five = excluded_five(per_family_rows, set(cohort))
    summary = {
        "exposure": exposure_info,
        "cv_comparison_135_cohort": cv_135,
        "cv_comparison_140_inclusion_agnostic": cv_140,
        "stored_and_refit_loo_predictions_by_cluster_exposure": stored,
        "excluded_five": five,
        "hidden_state_monitor_cluster_held_out": "NOT_EVALUATED (activation tensors lost in the 2026-10 scratch wipe)",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    clusters_csv = out_dir / "clusters.csv"
    sizes = cl.cluster_sizes(cluster_of)
    cohort_set = set(cohort)
    with clusters_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["family", "cluster_id", "cluster_size", "cue_type", "domain", "in_135_cohort",
                         "exposed_under_leave_one_family_out"])
        for family in sorted(manifest):
            writer.writerow([family, cluster_of[family], sizes[cluster_of[family]], manifest[family]["cue_type"],
                             manifest[family]["domain"], int(family in cohort_set),
                             int(exposure.get(family, False)) if family in cohort_set else ""])
    result = {
        "stage": "14.4",
        "evidence_class": "exploratory diagnostic on legacy data; not paper-eligible; legacy S_lp label used as the "
                          "historical Phase-I target only",
        "source_commit": sha,
        "git_status_short": git("status", "--short").splitlines(),
        "command": " ".join(sys.argv),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "inputs": {k: {"path": v, "sha256": hashlib.sha256((REPO_ROOT / v).read_bytes()).hexdigest()
                       if (REPO_ROOT / v).is_file() else None} for k, v in INPUTS.items()},
        "summary": summary,
    }
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    changed = update_ledger(summary, args.journal_ref) if args.update_ledger else []
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "exposure": {k: exposure_info[k] for k in (
        "n_families_in_unresolved_review", "n_clusters_with_two_or_more_families",
        "share_of_all_155_families_in_a_cluster", "cohort_share_exposed_under_leave_one_family_out")},
        "ledger_rows_updated": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
