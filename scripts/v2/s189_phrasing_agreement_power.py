#!/usr/bin/env python3
"""G1 design study (2026-11-14): power and error rates of candidate phrasing-agreement rules for F1-F3.

CPU only, no model, no Slurm. Simulates role-by-value datasets (J structures; R and D roles x 3 values x 2 phrasings, k
samples per cell, N sampled 6k times: the frozen balanced design) with a vectorised count-level generator whose
data-generating process is that of `tests/v2/rolevalue_worlds.py` and of the simulators in
`physmon.analysis.rolevalue_stats` (`simulate_f1/f2/f3`): per-structure base logit, binomial tracking counts, neglect /
placebo / correct categories in R cells, empirical-logit slopes for F3. The vectorised generator is checked against the
real generator plus `structure_estimates` (stage `validate`). Candidate rules A-D are in
`rolevalue_stats.AGREEMENT_RULE_TEXT`; they are evaluated on the SAME simulated datasets.

Stages: grid (main), f3 (F3 estimator efficiency), joint (pooled joint-TOST power in W0 via `joint_tost_power`),
validate (vectorised vs real generator), mixed (mixed-logistic F3 vs the structure-level estimator), report (summary.md).

    python scripts/v2/s189_phrasing_agreement_power.py --stage grid --workers 8
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from physmon.analysis import rolevalue_stats as rs  # noqa: E402

OUT_DIR = REPO / "results" / "stage15" / "g1_power" / "attempt_20261114"
BASE_SEED = 20261114
JS = (24, 30, 40, 60)
KS = (8, 12, 16, 24, 32, 40)
BASELINES = {"default_0.58": 0.58, "low_0.45": 0.45, "high_0.75": 0.75}
OMEGAS = (0.10, 0.20)
SD_STRUCTURE = 1.0  # between-structure SD of the base logit (SimParams default)
PLACEBO_RATE, SD_PLACEBO_LOGIT = 0.02, 0.7  # SimParamsF2 defaults
LOG15 = math.log(1.5)
N_SIMS = 2000
CONTRASTS = ("F1", "F2", "F3")
# world: mean F1 loss per phrasing, mean F2 neglect excess, mean R slope per phrasing (logit per value-index step)
WORLDS = {
    "W0": {"text": "invariant, phrasings agree", "f1": (0.0, 0.0), "f2": 0.0, "slope_r": (0.0, 0.0), "relevant": None,
           "agreeing": True},
    "W1": {"text": "F1 0.15 in both phrasings", "f1": (0.15, 0.15), "f2": 0.0, "slope_r": (0.0, 0.0), "relevant": None,
           "agreeing": True, "pooled": "F1"},
    "W2": {"text": "F1 0.20 in phrasing 0, 0 in phrasing 1", "f1": (0.20, 0.0), "f2": 0.0, "slope_r": (0.0, 0.0),
           "relevant": "F1", "agreeing": False},
    "W3": {"text": "F3 OR 1.5 per step in both phrasings", "f1": (0.0, 0.0), "f2": 0.0, "slope_r": (LOG15, LOG15),
           "relevant": None, "agreeing": True, "pooled": "F3"},
    "W4": {"text": "F3 OR 1.5 per step in phrasing 0 only", "f1": (0.0, 0.0), "f2": 0.0, "slope_r": (LOG15, 0.0),
           "relevant": "F3", "agreeing": False},
    "W4b": {"text": "F3 OR 2.25 per step in phrasing 0 only (extra)", "f1": (0.0, 0.0), "f2": 0.0,
            "slope_r": (2 * LOG15, 0.0), "relevant": "F3", "agreeing": False},
    "W5": {"text": "F2 neglect 0.15 in both phrasings", "f1": (0.0, 0.0), "f2": 0.15, "slope_r": (0.0, 0.0),
           "relevant": None, "agreeing": True, "pooled": "F2"},
}


def logit(p: float) -> float:
    return math.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-x))


# --- vectorised generator -------------------------------------------------------------------------------------------------

def draw_params(world: dict, n: int, J: int, base_p: float, omega: float, omega_ph: float, rng: np.random.Generator) -> dict:
    """Per-structure truth for n datasets x J structures. Heterogeneity follows the existing simulators: the F1 and F2
    effects vary between structures (SD omega) only where their world mean is non-zero (as `simulate_f1/f2`: a null has
    no spread); slopes always carry omega (as `simulate_f3`, independent for R and D). Structure-level deviations are
    shared by the two phrasings; omega_ph adds phrasing-by-structure deviations."""

    L = rng.normal(logit(base_p), SD_STRUCTURE, (n, J))
    u1 = rng.standard_normal((n, J))
    uR, uD = rng.standard_normal((n, J)), rng.standard_normal((n, J))
    uph = rng.standard_normal((n, J, 2, 3)) * omega_ph  # phrasing deviations for F1, slope R, slope D
    p_n = expit(L)
    delta1 = np.zeros((n, J, 2))
    slope_r = np.zeros((n, J, 2))
    slope_d = np.zeros((n, J, 2))
    for p in range(2):
        m1 = world["f1"][p]
        if m1 != 0:
            delta1[:, :, p] = m1 + omega * u1 + uph[:, :, p, 0]
        slope_r[:, :, p] = world["slope_r"][p] + omega * uR + uph[:, :, p, 1]
        slope_d[:, :, p] = omega * uD + uph[:, :, p, 2]
    p_d0 = np.clip(p_n[:, :, None] - delta1, 0.01, 0.99)
    p_plac = expit(rng.normal(logit(PLACEBO_RATE), SD_PLACEBO_LOGIT, (n, J)))
    m2 = world["f2"]
    if m2 > 0:  # gamma with mean m2 and SD omega: non-negative, exact mean
        shape, scale = (m2 / omega) ** 2, omega ** 2 / m2
        d2 = np.minimum(rng.gamma(shape, scale, (n, J)), 0.9)
        d2p = np.maximum(d2[:, :, None] + omega_ph * uph[:, :, :, 0], 0.0)
    else:
        d2p = np.zeros((n, J, 2))
    p_neg = p_plac[:, :, None] + d2p
    total = p_neg + p_plac[:, :, None]
    scale_down = np.where(total > 0.95, 0.95 / total, 1.0)
    return {"L": L, "p_n": p_n, "p_d0": p_d0, "slope_r": slope_r, "slope_d": slope_d, "p_plac": p_plac[:, :, None] * scale_down,
            "p_neg": p_neg * scale_down}


def draw_counts(par: dict, k: int, rng: np.random.Generator) -> dict:
    n, J = par["L"].shape
    z = np.array([-1.0, 0.0, 1.0])
    n_hits = rng.binomial(6 * k, par["p_n"])
    p_d = expit(logit_arr(par["p_d0"])[..., None] + par["slope_d"][..., None] * z)  # (n,J,2,3)
    d_hits = rng.binomial(k, p_d)
    p_r = expit(par["L"][:, :, None, None] + par["slope_r"][..., None] * z)
    p_neg, p_plac = par["p_neg"][..., None], par["p_plac"][..., None]
    p_r = np.minimum(p_r, 1 - p_neg - p_plac)
    neg = rng.binomial(k, np.broadcast_to(p_neg, p_r.shape))
    plac = rng.binomial(k - neg, np.broadcast_to(p_plac, p_r.shape) / (1 - np.broadcast_to(p_neg, p_r.shape)))
    r_hits = rng.binomial(k - neg - plac, p_r / (1 - p_neg - p_plac))
    return {"n_hits": n_hits, "d_hits": d_hits, "r_hits": r_hits, "neg": neg, "plac": plac}


def logit_arr(p):
    return np.log(p / (1 - p))


def emp_logit(s, n):
    return np.log((s + 0.5) / (n - s + 0.5))


def slope3(y):
    """Least-squares slope over value index 0,1,2 of y[..., 3] (equals `rolevalue_stats._slope` for three values)."""

    return (y[..., 2] - y[..., 0]) / 2


def structure_estimates(c: dict, k: int) -> dict:
    """F1-F3 per structure (n,J) pooled over phrasings and under each phrasing, as `rolevalue_stats.structure_estimates`:
    N is shared by both phrasings; R and D cells are restricted to the phrasing."""

    t_n = c["n_hits"] / (6 * k)
    est: dict[str, dict] = {f: {} for f in CONTRASTS}
    for name, ph in (("p0", [0]), ("p1", [1]), ("pooled", [0, 1])):
        n_ph = len(ph)
        d = c["d_hits"][:, :, ph, :].sum(axis=2)  # (n,J,3)
        r = c["r_hits"][:, :, ph, :].sum(axis=2)
        t_d = d.sum(axis=2) / (3 * k * n_ph)
        est["F1"][name] = t_n - t_d
        est["F2"][name] = (c["neg"][:, :, ph, :].sum(axis=(2, 3)) - c["plac"][:, :, ph, :].sum(axis=(2, 3))) / (3 * k * n_ph)
        est["F3"][name] = slope3(emp_logit(r, k * n_ph)) - slope3(emp_logit(d, k * n_ph))
    return est


# --- one grid point -------------------------------------------------------------------------------------------------------

def evaluate_point(args: tuple) -> dict:
    world_id, J, k, base_name, omega, omega_ph, n_sims = args
    world = WORLDS[world_id]
    seed = [BASE_SEED, J, k, int(BASELINES[base_name] * 100), int(round(omega * 100)), int(round(omega_ph * 100)),
            list(WORLDS).index(world_id)]
    rng = np.random.default_rng(np.random.SeedSequence(seed))
    par = draw_params(world, n_sims, J, BASELINES[base_name], omega, omega_ph, rng)
    est = structure_estimates(draw_counts(par, k, rng), k)
    pooled = {f: rs.batch_paired_labels(est[f]["pooled"], rs.SESOI[f], rs.PRIMARY[f][1]) for f in CONTRASTS}
    within = {f: np.isin(pooled[f]["label"], ("EQUIVALENT", "TRIVIAL_EFFECT")) for f in CONTRASTS}
    effect = {f: (pooled[f]["label"] == "EFFECT") & ((pooled[f]["mean"] > 0) | (f == "F3")) for f in CONTRASTS}
    rec: dict = {"world": world_id, "J": J, "k": k, "baseline": base_name, "baseline_p": BASELINES[base_name],
                 "omega": omega, "omega_ph": omega_ph, "n_sims": n_sims, "seed": seed,
                 "mean_estimate": {f: float(pooled[f]["mean"].mean()) for f in CONTRASTS},
                 "pooled_label_probs": {f: {lab: float((pooled[f]["label"] == lab).mean()) for lab in
                                            ("EFFECT", "TRIVIAL_EFFECT", "EQUIVALENT", "INCONCLUSIVE")} for f in CONTRASTS},
                 "pooled_effect_pos": {f: float(effect[f].mean()) for f in CONTRASTS},
                 "pooled_all_equivalent": float(np.all([pooled[f]["label"] == "EQUIVALENT" for f in CONTRASTS], axis=0).mean()),
                 "pooled_all_within": float(np.all([within[f] for f in CONTRASTS], axis=0).mean()), "rules": {}}
    pooled_ok = {"W0": np.all([within[f] for f in CONTRASTS], axis=0)}
    if "pooled" in world:
        pooled_ok[world_id] = effect[world["pooled"]]
    for rule in rs.AGREEMENT_RULES:
        labels = {f: rs.batch_agreement_labels(est[f]["p0"], est[f]["p1"], f, rule) for f in CONTRASTS}
        demote = rs.agreement_demotes(labels, rule)
        any_dis = np.any([labels[f] == rs.DISAGREE for f in CONTRASTS], axis=0)
        out = {"per_contrast": {f: {lab: float((labels[f] == lab).mean()) for lab in (rs.AGREE, rs.DISAGREE, rs.UNRESOLVED)}
                                for f in CONTRASTS},
               "p_demote": float(demote.mean()), "p_any_disagree": float(any_dis.mean()),
               "p_all_agree": float(np.all([labels[f] == rs.AGREE for f in CONTRASTS], axis=0).mean())}
        if world_id in pooled_ok:
            ok = pooled_ok[world_id]
            out["p_pooled_claim"] = float(ok.mean())
            out["p_correct"] = float((ok & ~demote).mean())
        if world["relevant"]:
            out["p_correct"] = float(demote.mean())  # wording dependence flagged by the rule's own demotion criterion
            out["p_demonstrated_any"] = float(any_dis.mean())
            out["p_demonstrated_relevant"] = float((labels[world["relevant"]] == rs.DISAGREE).mean())
        if world_id == "W0":
            out["p_false_pooled_effect"] = float(np.any([effect[f] for f in CONTRASTS], axis=0).mean())
        rec["rules"][rule] = out
    return rec


def run_grid(n_sims: int, workers: int, js, ks, baselines, omegas, worlds, omega_ph: float = 0.0) -> list[dict]:
    tasks = [(w, J, k, b, om, omega_ph, n_sims) for J, k, b, om, w in itertools.product(js, ks, baselines, omegas, worlds)]
    with Pool(workers) as pool:
        return pool.map(evaluate_point, tasks, chunksize=4)


# --- F3 estimator efficiency ------------------------------------------------------------------------------------------------

def f3_estimators(r, d, n):
    """Structure-level F3 candidates from success counts r, d (shape (..., 3)) out of n each:
    E1 frozen: R-D difference of least-squares slopes of the empirical logit;
    E2 probability scale: R-D difference of least-squares slopes of the tracking share;
    E3 information-weighted empirical-logit slope (weights (s+.5)(n-s+.5)/(n+1), one IRLS step)."""

    def wls(s):
        y = emp_logit(s, n)
        w = (s + 0.5) * (n - s + 0.5) / (n + 1)
        x = np.array([-1.0, 0.0, 1.0])
        xbar = (w * x).sum(-1, keepdims=True) / w.sum(-1, keepdims=True)
        ybar = (w * y).sum(-1, keepdims=True) / w.sum(-1, keepdims=True)
        return (w * (x - xbar) * (y - ybar)).sum(-1) / (w * (x - xbar) ** 2).sum(-1)

    return {"E1_empirical_logit": slope3(emp_logit(r, n)) - slope3(emp_logit(d, n)),
            "E2_probability_scale": slope3(r / n) - slope3(d / n),
            "E3_weighted_logit": wls(r) - wls(d)}


def f3_study(n_struct: int = 40000, seed_tag: int = 7) -> dict:
    """Per-structure SD of F3 estimators vs k, null (R and D slopes both 0 + omega heterogeneity) and alternative (R slope
    log 1.5, D 0), with k per cell (one phrasing) and 2k per cell (pooled over phrasings, the primary analysis)."""

    z = np.array([-1.0, 0.0, 1.0])
    out = {}
    for bname, b in BASELINES.items():
        for k in KS:
            for per_cell, label in ((k, "one_phrasing_k"), (2 * k, "pooled_2k")):
                rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, seed_tag, k, int(b * 100), per_cell]))
                L = rng.normal(logit(b), SD_STRUCTURE, n_struct)
                rows = {}
                for scen, (sr, om) in {"null_sampling_only": (0.0, 0.0), "null_omega0.2": (0.0, 0.2),
                                       "alt_OR1.5_sampling_only": (LOG15, 0.0), "alt_OR1.5_omega0.2": (LOG15, 0.2)}.items():
                    s_r = sr + om * rng.standard_normal(n_struct)
                    s_d = om * rng.standard_normal(n_struct)
                    p_r = expit(L[:, None] + s_r[:, None] * z)
                    p_d = expit(L[:, None] + s_d[:, None] * z)
                    est = f3_estimators(rng.binomial(per_cell, p_r), rng.binomial(per_cell, p_d), per_cell)
                    truth_prob = float(np.mean(slope3(p_r) - slope3(p_d)))
                    truth_logit = float(np.mean(s_r - s_d))
                    rows[scen] = {e: {"mean": float(v.mean()), "sd": float(v.std(ddof=1))} for e, v in est.items()}
                    rows[scen]["true_mean_prob_scale"] = truth_prob
                    rows[scen]["true_mean_logit_scale"] = truth_logit
                # margin on each estimator's own scale: its mean under the alternative with no heterogeneity and no noise
                p_r = expit(L[:, None] + LOG15 * z)
                p_d = expit(L[:, None] + 0 * z)
                margin = {"E1_empirical_logit": LOG15, "E3_weighted_logit": LOG15,
                          "E2_probability_scale": float(np.mean(slope3(p_r) - slope3(p_d)))}
                eff = {}
                for e in margin:
                    sd0 = rows["null_sampling_only"][e]["sd"]
                    sdw = rows["null_omega0.2"][e]["sd"]
                    eff[e] = {"margin": margin[e], "sd_null_sampling": sd0, "sd_null_omega0.2": sdw,
                              "sampling_sd_over_margin": sd0 / margin[e], "total_sd_over_margin_omega0.2": sdw / margin[e],
                              "mean_alt_sampling_only": rows["alt_OR1.5_sampling_only"][e]["mean"],
                              "mean_alt_over_margin": rows["alt_OR1.5_sampling_only"][e]["mean"] / margin[e]}
                out[f"{bname}|k={k}|{label}"] = {"scenarios": rows, "efficiency": eff}
    return out


# --- joint TOST power (reuse) ------------------------------------------------------------------------------------------------

def _joint_task(args):
    J, k, base_name, omega, n_sims = args
    b = BASELINES[base_name]
    p1 = rs.SimParams(base_logit=logit(b), sd_structure=SD_STRUCTURE)
    p2 = rs.SimParamsF2()
    p3 = rs.SimParamsF3(base_logit=logit(b), sd_structure=SD_STRUCTURE, sd_slope=omega)
    r = rs.joint_tost_power(p1, p2, p3, J, k, n_sims=n_sims, seed=rs.SEED)
    r.update(baseline=base_name, omega=omega)
    return r


def run_joint(n_sims: int, workers: int, baselines, omegas) -> list[dict]:
    tasks = [(J, k, b, om, n_sims) for J, k, b, om in itertools.product(JS, KS, baselines, omegas)]
    with Pool(workers) as pool:
        return pool.map(_joint_task, tasks, chunksize=1)


# --- validation against the real generator ----------------------------------------------------------------------------------------

def validate(n_datasets: int = 60, J: int = 30, k: int = 8, base_p: float = 0.58, omega: float = 0.2, seed: int = 11) -> dict:
    """The vectorised generator vs `tests/v2/rolevalue_worlds.simulate` + `structure_estimates` + `phrasing_agreement_rules`
    for the same structure-level truth, in a combined world (F1 0.15, F2 0.15, R slope log 1.5 in both phrasings)."""

    sys.path.insert(0, str(REPO / "tests" / "v2"))
    import rolevalue_worlds as rw  # noqa: PLC0415

    world = {"f1": (0.15, 0.15), "f2": 0.15, "slope_r": (LOG15, LOG15), "relevant": None}
    rng = np.random.default_rng(seed)
    par = draw_params(world, n_datasets, J, base_p, omega, 0.0, rng)
    real = {f: {"pooled": [], "p0": [], "p1": []} for f in CONTRASTS}
    real_labels = {r: {f: [] for f in CONTRASTS} for r in rs.AGREEMENT_RULES}
    z = np.array([-1.0, 0.0, 1.0])
    for i in range(n_datasets):
        def probs(cell, j, i=i):
            ph = 0 if cell.phrasing_id in ("r0", "d0") else 1
            if cell.stratum == "N":
                return {"correct": float(par["p_n"][i, j])}
            if cell.stratum == "D":
                pz = expit(logit(par["p_d0"][i, j, ph]) + par["slope_d"][i, j, ph] * z[cell.value_index])
                return {"correct": float(pz)}
            if cell.stratum == "R":
                pn, pp = float(par["p_neg"][i, j, ph]), float(par["p_plac"][i, j, ph])
                pz = expit(par["L"][i, j] + par["slope_r"][i, j, ph] * z[cell.value_index])
                return {"correct": float(min(pz, 1 - pn - pp)), "neglect": pn, "placebo": pp}
            return {"correct": 0.0}
        cells, records = rw.simulate(J, k, probs, seed=int(rng.integers(1 << 31)))
        for name, ph in (("pooled", None), ("p0", 0), ("p1", 1)):
            e = rs.structure_estimates(records, cells, phrasing=ph)
            for f in CONTRASTS:
                real[f][name].append([e[f"S{j:02d}"][f] for j in range(J)])
        ar = rs.phrasing_agreement_rules(records, cells)
        for rule in rs.AGREEMENT_RULES:
            for f in CONTRASTS:
                real_labels[rule][f].append(ar["rules"][rule]["labels"][f])
    # vectorised generator, same truth, many more datasets
    rng2 = np.random.default_rng(seed + 1)
    par2 = draw_params(world, 4000, J, base_p, omega, 0.0, rng2)
    est2 = structure_estimates(draw_counts(par2, k, rng2), k)
    out = {"J": J, "k": k, "baseline_p": base_p, "omega": omega, "n_real_datasets": n_datasets, "n_vectorised_datasets": 4000,
           "estimates": {}, "agreement_labels": {}}
    for f in CONTRASTS:
        out["estimates"][f] = {}
        for name in ("pooled", "p0", "p1"):
            a = np.asarray(real[f][name])
            b = est2[f][name]
            out["estimates"][f][name] = {"real_mean": float(a.mean()), "vec_mean": float(b.mean()),
                                         "real_structure_sd": float(a.std(axis=1, ddof=1).mean()),
                                         "vec_structure_sd": float(b.std(axis=1, ddof=1).mean())}
    for rule in rs.AGREEMENT_RULES:
        out["agreement_labels"][rule] = {}
        for f in CONTRASTS:
            vec = rs.batch_agreement_labels(est2[f]["p0"], est2[f]["p1"], f, rule)
            real_l = np.asarray(real_labels[rule][f])
            out["agreement_labels"][rule][f] = {lab: {"real": float((real_l == lab).mean()), "vec": float((vec == lab).mean())}
                                                for lab in (rs.AGREE, rs.DISAGREE, rs.UNRESOLVED)}
    return out


# --- mixed-logistic F3 -------------------------------------------------------------------------------------------------------

def _mixed_task(args):
    i, scenario, J, k, base_p, omega = args
    sys.path.insert(0, str(REPO / "tests" / "v2"))
    import rolevalue_worlds as rw  # noqa: PLC0415

    world = {"f1": (0.0, 0.0), "f2": 0.0, "slope_r": (LOG15, LOG15) if scenario == "alt" else (0.0, 0.0), "relevant": None}
    rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 99, J, k, int(base_p * 100), i, scenario == "alt"]))
    par = draw_params(world, 1, J, base_p, omega, 0.0, rng)
    z = np.array([-1.0, 0.0, 1.0])

    def probs(cell, j):
        ph = 0 if cell.phrasing_id in ("r0", "d0") else 1
        if cell.stratum == "N":
            return {"correct": float(par["p_n"][0, j])}
        if cell.stratum == "D":
            return {"correct": float(expit(logit(par["p_d0"][0, j, ph]) + par["slope_d"][0, j, ph] * z[cell.value_index]))}
        if cell.stratum == "R":
            return {"correct": float(expit(par["L"][0, j] + par["slope_r"][0, j, ph] * z[cell.value_index]))}
        return {"correct": 0.0}
    cells, records = rw.simulate(J, k, probs, seed=int(rng.integers(1 << 31)))
    est = rs.structure_estimates(records, cells)
    d = [e["F3"] for e in est.values() if e["F3"] is not None]
    summary = rs.paired_summary(d, rs.SESOI["F3"], "two-sided")
    y, x, groups, names, slopes = rs._hier_rows(records, cells, "F3", rs.PRIMARY_VIEW)  # noqa: SLF001
    hier = rs._hier_fit_one(y, x, groups, names, slopes, "R:z", 1, 0.95)  # noqa: SLF001
    return {"structure_mean": float(np.mean(d)), "structure_se": float(np.std(d, ddof=1) / math.sqrt(len(d))),
            "structure_label": summary["outcome"], "hier_status": hier["status"], "hier_estimate": hier.get("estimate"),
            "hier_sd": hier.get("sd"), "hier_method": hier.get("method", "")[:20], "hier_interval": hier.get("interval")}


def run_mixed(n_datasets: int, workers: int, J: int = 30, k: int = 8, base_p: float = 0.58, omega: float = 0.2) -> dict:
    tasks = [(i, sc, J, k, base_p, omega) for sc in ("null", "alt") for i in range(n_datasets)]
    with Pool(workers) as pool:
        rows = pool.map(_mixed_task, tasks, chunksize=1)
    out = {"J": J, "k": k, "baseline_p": base_p, "omega": omega, "n_datasets": n_datasets, "scenarios": {}}
    for sc in ("null", "alt"):
        r = [x for t, x in zip(tasks, rows) if t[1] == sc]
        ok = [x for x in r if x["hier_status"] == "OK" and x["hier_estimate"] is not None]
        sm = np.array([x["structure_mean"] for x in r])
        he = np.array([x["hier_estimate"] for x in ok]) if ok else np.array([np.nan])
        hsd = np.array([x["hier_sd"] for x in ok]) if ok else np.array([np.nan])
        sse = np.array([x["structure_se"] for x in r])
        out["scenarios"][sc] = {
            "structure_level_mean_estimate": float(sm.mean()), "structure_level_sd_across_datasets": float(sm.std(ddof=1)),
            "structure_level_mean_se": float(sse.mean()),
            "mixed_n_ok": len(ok), "mixed_mean_estimate": float(np.nanmean(he)),
            "mixed_sd_across_datasets": float(np.nanstd(he, ddof=1)) if len(ok) > 1 else None,
            "mixed_mean_reported_sd": float(np.nanmean(hsd)),
            "mixed_methods": sorted({x["hier_method"] for x in r}),
            "structure_label_counts": {lab: sum(x["structure_label"] == lab for x in r) for lab in
                                       ("EFFECT", "TRIVIAL_EFFECT", "EQUIVALENT", "INCONCLUSIVE")}}
    return out


# --- reporting -----------------------------------------------------------------------------------------------------------------

def _index(grid):
    return {(r["world"], r["J"], r["k"], r["baseline"], r["omega"], r["omega_ph"]): r for r in grid}


def smallest_k(grid, J, base, omega, omega_ph=0.0):
    """Per rule, the smallest k meeting each criterion and all of them (false DISAGREE: any contrast, agreeing worlds)."""

    idx = _index(grid)
    res = {}
    for rule in rs.AGREEMENT_RULES:
        per = {"correct_W0>=0.80": None, "detect_W2>=0.80": None, "detect_W4>=0.80": None, "demonstrate_W2>=0.80": None,
               "demonstrate_W4>=0.80": None, "false_disagree<=0.05": None, "all_flag_criteria": None,
               "all_demonstrated_criteria": None}
        for k in KS:
            try:
                g = {w: idx[(w, J, k, base, omega, omega_ph)]["rules"][rule] for w in WORLDS}
            except KeyError:
                continue
            fd = max(g[w]["p_any_disagree"] for w in WORLDS if WORLDS[w]["agreeing"])
            c = {"correct_W0>=0.80": g["W0"]["p_correct"] >= 0.8, "detect_W2>=0.80": g["W2"]["p_correct"] >= 0.8,
                 "detect_W4>=0.80": g["W4"]["p_correct"] >= 0.8,
                 "demonstrate_W2>=0.80": g["W2"]["p_demonstrated_relevant"] >= 0.8,
                 "demonstrate_W4>=0.80": g["W4"]["p_demonstrated_relevant"] >= 0.8, "false_disagree<=0.05": fd <= 0.05}
            c["all_flag_criteria"] = c["correct_W0>=0.80"] and c["detect_W2>=0.80"] and c["detect_W4>=0.80"] and c[
                "false_disagree<=0.05"]
            c["all_demonstrated_criteria"] = c["correct_W0>=0.80"] and c["demonstrate_W2>=0.80"] and c[
                "demonstrate_W4>=0.80"] and c["false_disagree<=0.05"]
            for key, ok in c.items():
                if ok and per[key] is None:
                    per[key] = k
        res[rule] = per
    return res


def write_report(out_dir: Path) -> None:
    summ = json.loads((out_dir / "summary.json").read_text())
    grid = summ.get("grid", [])
    lines = ["# s189 phrasing-agreement power study (2026-11-14)", "",
             "Generated by `scripts/v2/s189_phrasing_agreement_power.py --stage report` from `summary.json`. Evidence only; no "
             "design decision is taken here. Simulation: " + f"{summ.get('config', {}).get('n_sims')} datasets per grid point, "
             "t-based labels (no sign-flip/bootstrap method agreement, no leave-k-out).", ""]
    lines += ["## Rules", ""] + [f"* **{r}**: {t}" for r, t in rs.AGREEMENT_RULE_TEXT.items()] + [""]
    if grid:
        idx = _index(grid)
        base, om = "default_0.58", 0.2
        for w, spec in WORLDS.items():
            lines += [f"## {w}: {spec['text']} (omega 0.2, baseline 0.58)", ""]
            relevant = spec["relevant"]
            col = "flag (demonstrated)" if relevant else "correct"
            lines += [f"Cell = {col}; rule x J, columns k = " + ", ".join(map(str, KS)), "",
                      "| rule | J | " + " | ".join(f"k={k}" for k in KS) + " |", "|---|---|" + "---|" * len(KS)]
            for rule in rs.AGREEMENT_RULES:
                for J in (30, 40, 60):
                    cells = []
                    for k in KS:
                        r = idx.get((w, J, k, base, om, 0.0))
                        if r is None:
                            cells.append("n/a")
                            continue
                        x = r["rules"][rule]
                        cells.append(f"{x['p_correct']:.2f} ({x['p_demonstrated_relevant']:.2f})" if relevant
                                     else f"{x['p_correct']:.2f}")
                    lines.append(f"| {rule} | {J} | " + " | ".join(cells) + " |")
            lines.append("")
        lines += ["## P(any contrast DISAGREE) in agreeing worlds (omega 0.2, baseline 0.58)", ""]
        for w in ("W0", "W1", "W3", "W5"):
            lines += [f"### {w}", "", "| rule | J | " + " | ".join(f"k={k}" for k in KS) + " |", "|---|---|" + "---|" * len(KS)]
            for rule in rs.AGREEMENT_RULES:
                for J in (30, 40, 60):
                    lines.append(f"| {rule} | {J} | " + " | ".join(
                        f"{idx[(w, J, k, base, om, 0.0)]['rules'][rule]['p_any_disagree']:.3f}" if (w, J, k, base, om, 0.0) in idx
                        else "n/a" for k in KS) + " |")
            lines.append("")
        lines += ["## W0: P(AGREE) per contrast, rules A / B / C (omega 0.2, baseline 0.58)", "",
                  "| J | k | A F1 | A F2 | A F3 | B F1 | B F2 | B F3 | C F3 |", "|---|---|---|---|---|---|---|---|---|"]
        for J in (30, 40, 60):
            for k in KS:
                r = idx.get(("W0", J, k, base, om, 0.0))
                if r:
                    p = r["rules"]
                    lines.append(f"| {J} | {k} | " + " | ".join(
                        f"{p[ru]['per_contrast'][f]['AGREE']:.2f}" for ru, f in
                        (("A", "F1"), ("A", "F2"), ("A", "F3"), ("B", "F1"), ("B", "F2"), ("B", "F3"), ("C", "F3"))) + " |")
        lines += ["", "## Smallest k meeting the criteria (omega 0.2; null = not reached by k = 40)", ""]
        for bn in BASELINES:
            for J in JS:
                if ("W0", J, KS[0], bn, om, 0.0) not in idx:
                    continue
                sk = smallest_k(grid, J, bn, om)
                lines += [f"### J = {J}, baseline {bn}", "", "| rule | " + " | ".join(next(iter(sk.values()))) + " |",
                          "|---|" + "---|" * len(next(iter(sk.values())))]
                for rule, per in sk.items():
                    lines.append(f"| {rule} | " + " | ".join(str(v) for v in per.values()) + " |")
                lines.append("")
    joint = summ.get("joint")
    if joint:
        lines += ["## Pooled joint-TOST power in W0 (`joint_tost_power`, omega 0.2): joint EQUIVALENT / EQUIVALENT-or-TRIVIAL", "",
                  "| baseline | J | " + " | ".join(f"k={k}" for k in KS) + " |", "|---|---|" + "---|" * len(KS)]
        for bn in BASELINES:
            for J in JS:
                row = {r["k"]: r for r in joint if r["baseline"] == bn and r["J"] == J and abs(r["omega"] - 0.2) < 1e-9}
                if row:
                    lines.append(f"| {bn} | {J} | " + " | ".join(
                        f"{row[k]['joint_equivalence_rate']:.2f} / {row[k]['joint_equivalent_or_trivial_rate']:.2f}" if k in row
                        else "n/a" for k in KS) + " |")
        lines.append("")
    f3 = summ.get("f3_study")
    if f3:
        lines += ["## F3 estimator study: sampling SD per structure and SD / margin (baseline 0.58)", "",
                  "| k | cell n | E1 sd | E1 sd/margin | E2 sd | E2 sd/margin | E3 sd | E3 sd/margin | E1 mean alt/margin |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for k in KS:
            for label in ("one_phrasing_k", "pooled_2k"):
                v = f3[f"default_0.58|k={k}|{label}"]["efficiency"]
                lines.append(f"| {k} | {label} | " + " | ".join(
                    f"{v[e]['sd_null_sampling']:.3f} | {v[e]['sampling_sd_over_margin']:.3f}" for e in
                    ("E1_empirical_logit", "E2_probability_scale", "E3_weighted_logit")) +
                    f" | {v['E1_empirical_logit']['mean_alt_over_margin']:.2f} |")
        lines.append("")
    for key, title in (("validate", "Validation: vectorised vs real generator"), ("mixed", "Mixed-logistic F3 vs structure-level")):
        if summ.get(key):
            lines += [f"## {title}", "", "```json", json.dumps(summ[key], indent=1)[:6000], "```", ""]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["grid", "f3", "joint", "validate", "mixed", "report", "sensitivity"])
    ap.add_argument("--n-sims", type=int, default=N_SIMS)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--js", default=",".join(map(str, JS)))
    ap.add_argument("--omega-ph", type=float, default=0.10)
    a = ap.parse_args()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "summary.json"
    summ = json.loads(path.read_text()) if path.exists() else {}
    workers = min(a.workers, 8)
    t0 = time.time()
    if a.stage == "grid":
        js = tuple(int(x) for x in a.js.split(","))
        summ["grid"] = run_grid(a.n_sims, workers, js, KS, tuple(BASELINES), OMEGAS, tuple(WORLDS))
        summ["config"] = {"n_sims": a.n_sims, "js": js, "ks": KS, "baselines": BASELINES, "omegas": OMEGAS, "worlds": WORLDS,
                          "base_seed": BASE_SEED, "sd_structure": SD_STRUCTURE, "placebo_rate": PLACEBO_RATE,
                          "sd_placebo_logit": SD_PLACEBO_LOGIT, "alpha": rs.ALPHA, "sesoi": rs.SESOI["F1"],
                          "sesoi_f3": rs.SESOI["F3"], "command": " ".join(sys.argv)}
    elif a.stage == "sensitivity":
        summ["sensitivity_phrasing_by_structure"] = run_grid(a.n_sims, workers, (30, 40, 60), KS, ("default_0.58",), (0.20,),
                                                             tuple(WORLDS), omega_ph=a.omega_ph)
    elif a.stage == "f3":
        summ["f3_study"] = f3_study()
    elif a.stage == "joint":
        summ["joint"] = run_joint(1000, workers, tuple(BASELINES), OMEGAS)
    elif a.stage == "validate":
        summ["validate"] = validate()
    elif a.stage == "mixed":
        summ["mixed"] = run_mixed(max(a.n_sims, 1), workers)
    if a.stage != "report":
        path.write_text(json.dumps(summ, indent=1))
    write_report(out_dir)
    print(f"stage {a.stage} done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
