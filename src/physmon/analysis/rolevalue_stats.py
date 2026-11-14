"""Frozen role-by-value analysis (G1; plan of record Sections "Role-by-value design" and "Statistical analysis").

Input: sampled records (from `s170_sampled_run.py collect`) and the cell rows they were generated from (the runner's job
rows, which carry each cell's foils and placebo). Nothing here reads a model or a GPU; every function is tested on
synthetic records before any real role-cell record is analysed.

Definitions (plan of record):
* Tracking T (per sample): 1 if COMPLETE and graded correct against the cell's own certified answer under the primary
  view (`grade_declared`, protocol 4b), else 0, over all attempted samples. Complete-case and other views are
  sensitivity analyses.
* F1 (inappropriate dependence, co-primary): per structure, T̄_N - T̄_D (non-numeric sentence minus the D cells,
  averaged over values, phrasings and samples); one-sided (a loss), SESOI 0.10. The loss against the no-cue prompt is
  reported beside it.
* F2 (inadequate responsiveness, co-primary): per structure, the R neglect share minus the R placebo match rate;
  one-sided, SESOI 0.10.
* F3 (role x value interaction, co-primary): per structure, the difference between the R and D least-squares slopes of
  the empirical logit of tracking across the value index; two-sided, SESOI log(1.5) per value step. Primary analysis is
  the paired analysis of the J structure-level estimates (the plan's rule for every primary contrast); the
  mixed-effects logistic model is a complementary view, reported beside it.
* Design rule for F1 (frozen from the null simulations): N is sampled as often as all D cells of the structure
  together; the sign-flip test is primary (the t-test over-rejected more under the imbalanced design).
* Structure-level differences: t-interval with J-1 df, a sign-flip randomisation test (exact up to J = 16, else 20,000
  flips, seed 42) with its symmetry check reported, and a bootstrap over structures (2,000 resamples, seed 42).
* Equivalence by two one-sided tests within the SESOI (alpha 0.05 each, i.e. the 90% interval inside the margin).
  Four outcomes: EFFECT (the interval excludes zero and extends beyond the margin), TRIVIAL_EFFECT (excludes zero,
  inside the margin), EQUIVALENT (TOST passes and the interval includes zero), INCONCLUSIVE (none of these). The
  interval is the two-sided 95% one for the two-sided F3 and the two-sided 90% one for the one-sided F1 and F2, whose
  lower bound is the one-sided 95% bound, so a label never contradicts its test.
  "No effect" is never an outcome.
* F1-F3 are Holm-corrected at family-wise alpha 0.05.
* Rare shares: Jeffreys Beta(0.5, 0.5) per structure; combined by a Beta-Binomial model fitted by maximum likelihood,
  with a bootstrap-over-structures interval.
* Misuse support: a misuse curve h is supported in a D/C/K cell family only when its share exceeds the N-cell rate of
  the same value at two or more of at least three values.
* lambda (descriptive): Hodges-Lehmann location of COMPLETE answers per cell, scaled by the R twin's certified change;
  flagged MULTIMODAL when two or more answer modes each hold at least 20% of the cell's complete answers.

G1 decisions of 2026-11-13 (`docs/registry/v2/g1/decisions_2026-11-13.md`) implemented here:
* Decision 4: no status below 6 evaluable structures (`MIN_EVALUABLE_STRUCTURES`): below J = 6 the exact two-sided
  sign-flip test cannot reach p < 0.05 (2/2^5 = 0.0625). Such a contrast is NOT_EVALUATED, never a zero.
* Decision 5: method agreement (`method_agreement`: t, sign-flip, bootstrap decide; the hierarchical model of
  `hierarchical_view` is complementary and never the decision) and leave-1-to-3-structures-out robustness
  (`leave_k_out`, with the extreme-deletion rule of `g3_scorecard_thresholds.md` section 1.5).
* Population-level misuse excess and attribution (`misuse_attribution`, decision 13), copy excess in R
  (`copy_excess_r`), O5 cost contrasts (`cost_contrasts`, decisions 10 and 11), C/K versions of F1 and of the value
  slope (`ck_family`), and the joint-TOST power simulator for F1-F3 (`joint_tost_power`, decision 21).
"""

from __future__ import annotations

import itertools
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import optimize, stats

from physmon.scoring import grading_views as gv

ALPHA = 0.05
SEED = 42
N_BOOT = 2000
N_FLIPS = 20000
EXACT_FLIP_MAX_J = 16
SESOI = {
    "F1": 0.10,  # a tenth of answers lost to an irrelevant quantity before it matters (behavioural)
    "F2": 0.10,  # a tenth of R answers ignoring a quantity that matters
    "F3": math.log(1.5),  # odds ratio 1.5 per value step: smaller value dependence would not change a reading of any item
    "lambda_D": 0.10,  # a leak of a tenth of the relevant-role response (descriptive)
}
SESOI_REASONS = {
    "F1": "behavioural: the share of answers that may be lost to an irrelevant quantity before it matters "
          "(plan of record planning value 0.10 in tracking)",
    "F2": "behavioural: a tenth of R answers ignoring a quantity that matters (plan of record 0.10)",
    "F3": "an odds ratio of 1.5 per value step on tracking (plan of record): a smaller value dependence would not change "
          "the reading of any single item",
    "lambda_D": "descriptive: a leak of a tenth of the relevant-role response",
}
SESOI.update({
    "M": 0.10,  # misuse excess over N, per curve class (plan: "for the D tracking loss and misuse shares ... 0.10")
    "CR": 0.10,  # copy excess in R over N
    "L5": math.log(1.2),  # O5 response length, log ratio D / N (decision 10)
    "B5": 0.05,  # O5 budget exhaustion share, D - N (decision 10)
})
SESOI_REASONS.update({
    "M": "behavioural: the share of answers that may be lost to an irrelevant quantity before it matters (plan of record "
         "planning value 0.10 for the D tracking loss and misuse shares)",
    "CR": "same reason as the misuse shares (g3_scorecard_thresholds.md section 2)",
    "L5": "a fifth longer response is a practical cost at a fixed budget (decision 10)",
    "B5": "five more exhausted budgets per hundred is a practical cost (decision 10)",
})
PRIMARY_VIEW = "grade_declared"
MULTIMODAL_SHARE = 0.20
# Decision 4 (G1, 2026-11-13): below 6 evaluable structures no contrast gets a status; the exact two-sided sign-flip test
# cannot reach p < 0.05 with J < 6 (minimum p = 2/2^J; J = 5 gives 0.0625).
MIN_EVALUABLE_STRUCTURES = 6
# Samples per R, D, C and K cell in G3/G4 role-by-value runs; N and no-cue cells are sampled 6x this (balanced design).
# Amended 2026-11-14 by plan_revision_v2.2, section E: k = 24 (was 8, decision 16). Applies to future runs only; the
# registered run specs under data/v2/runs/ are immutable records.
SAMPLES_PER_CELL = 24
BALANCED_CELL_MULTIPLIER = 6
ROBUSTNESS_KS = (1, 2, 3)  # decision 5 / plan P4.6: effects must survive dropping one to three structures
ROBUSTNESS_MAX_SUBSETS = 1000  # all subsets when there are at most this many, else a seeded sample of this many


# --- per-sample quantities ---------------------------------------------------------------------------------------------

def cell_key(record: Mapping[str, Any]) -> str:
    """The cell a record belongs to (its job id without the sample suffix)."""

    job = str(record["job_id"])
    return job.rsplit(":s", 1)[0] if ":s" in job else job


def tracking(record: Mapping[str, Any], view: str = PRIMARY_VIEW) -> int:
    return int(record.get("completion_status") == "COMPLETE" and record.get(view) == "correct")


def matches_value(record: Mapping[str, Any], target: float | None) -> bool:
    """Whether a COMPLETE record's value matches `target` under the foil-matching rule (the same rule for every foil,
    the neglect value and the placebo, so their rates are comparable)."""

    if target is None or record.get("completion_status") != "COMPLETE":
        return False
    value = record.get("value_in_gold_unit")
    if value is None:
        return False
    return bool(gv.match_foils(float(value), {"t": float(target)})["matches"])


@dataclass
class Cell:
    key: str
    structure_id: str
    stratum: str
    value_index: int | None
    phrasing_id: str | None
    gold: float
    foils: dict[str, float]
    placebo: float | None
    confounded: list[str]
    heldout: bool = False  # held-out values (m >= 5) are not part of F1-F3 (decision 17: a G4 committed prediction)


def cells_from_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Cell]:
    out = {}
    for r in rows:
        role = r.get("role") or {}
        out[r["job_id"]] = Cell(r["job_id"], r["structure_id"], role.get("stratum", r.get("cue_semantic_role") or "none"),
                                role.get("value_index"), role.get("phrasing_id"), float(r["gold_value"]),
                                dict(r.get("foils") or {}), role.get("placebo"), list(role.get("confounded") or []),
                                bool(role.get("heldout", False)))
    return out


def group_records(records: Iterable[Mapping[str, Any]], cells: Mapping[str, Cell]) -> dict[str, list[Mapping[str, Any]]]:
    by_cell: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for r in records:
        key = cell_key(r)
        if key not in cells:
            raise KeyError(f"record {r.get('job_id')} has no cell row")
        by_cell[key].append(r)
    return by_cell


# --- structure-level estimates ------------------------------------------------------------------------------------------

def _mean(xs: Sequence[float]) -> float | None:
    return float(np.mean(xs)) if len(xs) else None


def phrasing_indices(cells: Mapping[str, Cell]) -> dict[str, int]:
    """Phrasing index of every R/D/C/K cell: the position of its phrasing id among the sorted phrasing ids of the same
    structure and stratum (R phrasings r0, r1 and D phrasings d0, d1 both map to 0, 1), so per-phrasing analyses pair
    the first R phrasing with the first D phrasing."""

    ids: dict[tuple[str, str], set[str]] = defaultdict(set)
    for c in cells.values():
        if c.phrasing_id is not None and c.stratum in ("R", "D", "C", "K"):
            ids[(c.structure_id, c.stratum)].add(c.phrasing_id)
    order = {k: sorted(v) for k, v in ids.items()}
    return {key: order[(c.structure_id, c.stratum)].index(c.phrasing_id) for key, c in cells.items()
            if c.phrasing_id is not None and c.stratum in ("R", "D", "C", "K")}


def structure_estimates(records: Iterable[Mapping[str, Any]], cells: Mapping[str, Cell], view: str = PRIMARY_VIEW,
                        phrasing: int | str | None = None) -> dict[str, dict[str, Any]]:
    """Per structure: T̄ by stratum, the F1/F2/F3 estimates, and their inputs; for C and K cells (targeted ablations)
    also F1_C = T̄_N - T̄_C, F1_K = T̄_N - T̄_K and the stratum's own value slope (target 0). `phrasing` restricts R/D
    cells to one phrasing: an int is the phrasing index of `phrasing_indices` (0 or 1 by position in the cell's role), a
    str an exact phrasing id. Held-out-value cells are excluded."""

    by_cell = group_records(records, cells)
    index = phrasing_indices(cells)
    out: dict[str, dict[str, Any]] = {}
    per_s: dict[str, dict[str, Any]] = defaultdict(lambda: {"T": defaultdict(list), "T_by_z": defaultdict(list),
                                                            "neglect": [], "placebo": []})
    for key, recs in by_cell.items():
        cell = cells[key]
        if cell.heldout:
            continue
        if phrasing is not None and cell.stratum in ("R", "D"):
            if isinstance(phrasing, int) and index.get(key) != phrasing:
                continue
            if isinstance(phrasing, str) and cell.phrasing_id != phrasing:
                continue
        s = per_s[cell.structure_id]
        ts = [tracking(r, view) for r in recs]
        s["T"][cell.stratum].extend(ts)
        if cell.stratum in ("R", "D", "C", "K") and cell.value_index is not None:
            s["T_by_z"][(cell.stratum, cell.value_index)].extend(ts)
        if cell.stratum == "R":
            s["neglect"].extend(int(matches_value(r, cell.foils.get("neglect"))) for r in recs)
            s["placebo"].extend(int(matches_value(r, cell.placebo)) for r in recs)
    for sid, s in per_s.items():
        t = {k: _mean(v) for k, v in s["T"].items()}

        def loss(a: str, b: str) -> float | None:
            return (t[a] - t[b]) if t.get(a) is not None and t.get(b) is not None else None

        f2 = (_mean(s["neglect"]) - _mean(s["placebo"])) if s["neglect"] else None
        values = {r: len({z for (rr, z), v in s["T_by_z"].items() if rr == r and len(v)}) for r in ("R", "D", "C", "K")}
        out[sid] = {"T": t, "F1": loss("N", "D"), "F1_vs_no_cue": loss("none", "D"), "F2": f2,
                    "F3": f3_estimate(s["T_by_z"]), "F1_C": loss("N", "C"), "F1_K": loss("N", "K"),
                    "slope_C": stratum_slope(s["T_by_z"], "C"), "slope_K": stratum_slope(s["T_by_z"], "K"),
                    "neglect_share": _mean(s["neglect"]), "placebo_rate": _mean(s["placebo"]),
                    "n_samples": {k: len(v) for k, v in s["T"].items()},
                    "n_values": {k: v for k, v in values.items() if v}}
    return out


def empirical_logit(successes: int, n: int) -> float:
    return math.log((successes + 0.5) / (n - successes + 0.5))


def _slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    x = np.asarray(xs, float)
    y = np.asarray(ys, float)
    return float(((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum())


def stratum_slope(t_by_z: Mapping[tuple[str, int], Sequence[int]], role: str) -> float | None:
    """Least-squares slope of the empirical logit of tracking across the value index for one stratum (needs >= 2
    values); for C and K the target is 0 (g3_scorecard_thresholds.md, H6-extended)."""

    zs = sorted(z for (r, z) in t_by_z if r == role and len(t_by_z[(r, z)]))
    if len(zs) < 2:
        return None
    return _slope(zs, [empirical_logit(sum(t_by_z[(role, z)]), len(t_by_z[(role, z)])) for z in zs])


def f3_estimate(t_by_z: Mapping[tuple[str, int], Sequence[int]]) -> float | None:
    """R slope minus D slope of the empirical logit of tracking across the value index (needs >= 2 values in each)."""

    r, d = stratum_slope(t_by_z, "R"), stratum_slope(t_by_z, "D")
    return None if r is None or d is None else r - d


# --- inference on structure-level differences ----------------------------------------------------------------------------

def sign_flip_p(diffs: Sequence[float], alternative: str) -> float:
    """Sign-flip randomisation p for the mean (valid under symmetry of the paired differences)."""

    d = np.asarray(diffs, float)
    observed = d.mean()
    if len(d) <= EXACT_FLIP_MAX_J:
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=len(d))))
    else:
        signs = np.random.default_rng(SEED).choice((1.0, -1.0), size=(N_FLIPS, len(d)))
    means = (signs * d).mean(axis=1)
    if alternative == "greater":
        return float(np.mean(means >= observed - 1e-12))
    if alternative == "less":
        return float(np.mean(means <= observed + 1e-12))
    return float(np.mean(np.abs(means) >= abs(observed) - 1e-12))


def _bootstrap_means(diffs: Sequence[float]) -> np.ndarray:
    d = np.asarray(diffs, float)
    rng = np.random.default_rng(SEED)
    return np.sort(d[rng.integers(0, len(d), size=(N_BOOT, len(d)))].mean(axis=1))


def _quantile_interval(means: np.ndarray, level: float) -> list[float]:
    lo = (1 - level) / 2
    return [float(np.quantile(means, lo)), float(np.quantile(means, 1 - lo))]


def bootstrap_ci(diffs: Sequence[float], level: float = 0.95) -> list[float]:
    return _quantile_interval(_bootstrap_means(diffs), level)


def t_interval(diffs: Sequence[float], level: float) -> list[float]:
    d = np.asarray(diffs, float)
    se = d.std(ddof=1) / math.sqrt(len(d))
    half = stats.t.ppf(1 - (1 - level) / 2, len(d) - 1) * se
    return [float(d.mean() - half), float(d.mean() + half)]


def tost_p(diffs: Sequence[float], margin: float) -> float:
    """The larger of the two one-sided t-test p values against -margin and +margin."""

    d = np.asarray(diffs, float)
    se = d.std(ddof=1) / math.sqrt(len(d))
    if se == 0:
        return 0.0 if abs(d.mean()) < margin else 1.0
    p_low = 1 - stats.t.cdf((d.mean() + margin) / se, len(d) - 1)
    p_high = stats.t.cdf((d.mean() - margin) / se, len(d) - 1)
    return float(max(p_low, p_high))


def classify(ci95: Sequence[float], tost: float, margin: float) -> str:
    lo, hi = ci95
    excludes_zero = lo > 0 or hi < 0
    if excludes_zero and (hi > margin or lo < -margin):
        return "EFFECT"
    if excludes_zero:
        return "TRIVIAL_EFFECT"
    if tost < ALPHA:
        return "EQUIVALENT"
    return "INCONCLUSIVE"


def paired_summary(diffs: Sequence[float | None], margin: float, alternative: str) -> dict[str, Any]:
    d = [float(x) for x in diffs if x is not None and math.isfinite(x)]
    if len(d) < MIN_EVALUABLE_STRUCTURES:
        return {"J": len(d), "outcome": "NOT_EVALUATED", "alternative": alternative, "sesoi": margin,
                "reason": f"fewer than {MIN_EVALUABLE_STRUCTURES} evaluable structures (decision 4)"}
    arr = np.asarray(d)
    if arr.std(ddof=1) > 0:
        t_stat = arr.mean() / (arr.std(ddof=1) / math.sqrt(len(d)))
    else:  # no spread: an infinite statistic in the direction of a non-zero mean, 0 for an all-zero set
        t_stat = math.copysign(math.inf, arr.mean()) if arr.mean() != 0 else 0.0
    if alternative == "greater":
        p_t = float(1 - stats.t.cdf(t_stat, len(d) - 1))
    elif alternative == "less":
        p_t = float(stats.t.cdf(t_stat, len(d) - 1))
    else:
        p_t = float(2 * (1 - stats.t.cdf(abs(t_stat), len(d) - 1)))
    ci95 = t_interval(d, 0.95)
    ci90 = t_interval(d, 0.90)
    tost = tost_p(d, margin)
    label_interval = ci95 if alternative == "two-sided" else ci90  # one-sided 95% bound for one-sided contrasts
    boot = _bootstrap_means(d)
    return {"J": len(d), "mean": float(arr.mean()), "sd": float(arr.std(ddof=1)), "ci95_t": ci95,
            "ci90_t": ci90, "ci95_bootstrap": _quantile_interval(boot, 0.95),
            "ci90_bootstrap": _quantile_interval(boot, 0.90), "p_t": p_t,
            "p_sign_flip": sign_flip_p(d, alternative), "alternative": alternative, "sesoi": margin, "p_tost": tost,
            "classification_interval": "ci95_t" if alternative == "two-sided" else "ci90_t",
            "outcome": classify(label_interval, tost, margin),
            "symmetry_check": {"skewness": float(stats.skew(arr)), "mean_minus_median": float(arr.mean() - np.median(arr))}}


def holm(pvalues: Mapping[str, float]) -> dict[str, dict[str, Any]]:
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    out, running = {}, 0.0
    m = len(items)
    for i, (name, p) in enumerate(items):
        adjusted = min(1.0, max(running, (m - i) * p))
        running = adjusted
        out[name] = {"p": p, "p_holm": adjusted, "reject": adjusted < ALPHA}
    return out


def _excludes_zero_on(interval: Sequence[float], sign: int) -> bool:
    return bool(interval[0] > 0) if sign > 0 else bool(interval[1] < 0)


def method_agreement(diffs: Sequence[float | None], summary: Mapping[str, Any],
                     hierarchical: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Decision 5 / plan B6.4: do the paired t-interval, the bootstrap over structures and the sign-flip test agree on
    the sign of the effect and on excluding zero? Each method is read at the level of the label interval (the
    one-sided 95% bound, i.e. the 90% two-sided interval, for one-sided contrasts; the 95% interval for two-sided ones),
    in the observed direction of the mean (for a one-sided contrast whose mean is on the untested side, the sign-flip
    p is computed in the observed direction). `decision_methods_agree` uses t, sign-flip and bootstrap
    (g3_scorecard_thresholds.md section 1.4); the hierarchical model is complementary, reported beside, never the
    decision."""

    if summary.get("outcome") == "NOT_EVALUATED":
        return {"assessable": False, "reason": summary.get("reason")}
    d = [float(x) for x in diffs if x is not None and math.isfinite(x)]
    mean = float(np.mean(d))
    sign = 1 if mean > 0 else (-1 if mean < 0 else 0)
    direction = sign or 1
    two_sided = summary["alternative"] == "two-sided"
    label_t = summary["ci95_t"] if two_sided else summary["ci90_t"]
    label_boot = summary["ci95_bootstrap"] if two_sided else summary["ci90_bootstrap"]
    # two-sided contrasts: the two-sided p; one-sided ones: the one-sided p in the observed direction (alpha 0.05 each)
    p_flip = summary["p_sign_flip"] if two_sided else sign_flip_p(d, "greater" if direction > 0 else "less")
    boot_mid = float(np.median(label_boot))
    methods: dict[str, Any] = {
        "t": {"sign": sign, "interval": label_t, "excludes_zero": _excludes_zero_on(label_t, direction)},
        "bootstrap": {"sign": (1 if boot_mid > 0 else -1 if boot_mid < 0 else 0), "interval": label_boot,
                      "excludes_zero": _excludes_zero_on(label_boot, direction)},
        "sign_flip": {"sign": sign, "p": p_flip, "direction": direction, "excludes_zero": bool(p_flip < ALPHA)},
    }
    decision = ("t", "bootstrap", "sign_flip")
    out: dict[str, Any] = {"assessable": True, "direction": direction, "methods": methods,
                           "decision_methods": list(decision),
                           "decision_methods_agree": len({methods[m]["excludes_zero"] for m in decision}) == 1
                           and len({methods[m]["sign"] for m in decision}) == 1}
    if hierarchical is not None and hierarchical.get("status") == "OK":
        h_sign = 1 if hierarchical["estimate"] > 0 else (-1 if hierarchical["estimate"] < 0 else 0)
        methods["hierarchical"] = {"sign": h_sign, "interval": hierarchical["interval"],
                                   "excludes_zero": _excludes_zero_on(hierarchical["interval"], direction),
                                   "method": hierarchical["method"]}
        out["hierarchical_agrees_in_sign"] = h_sign == sign
        out["hierarchical_agrees_in_excluding_zero"] = methods["hierarchical"]["excludes_zero"] == methods["t"]["excludes_zero"]
    elif hierarchical is not None:
        out["hierarchical_not_available"] = hierarchical.get("reason")
    out["all_agree_in_sign"] = len({m["sign"] for m in methods.values()}) == 1
    out["all_agree_in_excluding_zero"] = len({m["excludes_zero"] for m in methods.values()}) == 1
    return out


def _labels_after_deletion(d: np.ndarray, dropped: np.ndarray, margin: float, alternative: str) -> dict[str, np.ndarray]:
    """Vectorised `paired_summary` label and mean for each row of `dropped` (index sets removed from `d`)."""

    n = len(d) - dropped.shape[1]
    total, total_sq = d.sum(), (d ** 2).sum()
    mean = (total - d[dropped].sum(axis=1)) / n
    ss = (total_sq - (d[dropped] ** 2).sum(axis=1)) - n * mean ** 2
    sd = np.sqrt(np.clip(ss, 0, None) / (n - 1))
    se = sd / math.sqrt(n)
    level = 0.95 if alternative == "two-sided" else 0.90
    half = stats.t.ppf(1 - (1 - level) / 2, n - 1) * se
    lo, hi = mean - half, mean + half
    with np.errstate(divide="ignore", invalid="ignore"):
        p_low = 1 - stats.t.cdf((mean + margin) / se, n - 1)
        p_high = stats.t.cdf((mean - margin) / se, n - 1)
    tost = np.where(se == 0, np.where(np.abs(mean) < margin, 0.0, 1.0), np.maximum(p_low, p_high))
    excludes = (lo > 0) | (hi < 0)
    beyond = (hi > margin) | (lo < -margin)
    label = np.where(excludes & beyond, "EFFECT", np.where(excludes, "TRIVIAL_EFFECT",
                                                            np.where(tost < ALPHA, "EQUIVALENT", "INCONCLUSIVE")))
    if n < MIN_EVALUABLE_STRUCTURES:
        label = np.full(len(mean), "NOT_EVALUATED")
    return {"label": label, "mean": mean, "lo": lo, "hi": hi}


def leave_k_out(diffs: Sequence[float | None], margin: float, alternative: str, ks: Sequence[int] = ROBUSTNESS_KS,
                max_subsets: int = ROBUSTNESS_MAX_SUBSETS, seed: int = SEED) -> dict[str, Any]:
    """Decision 5 / plan P4.6: leave-k-structures-out robustness for k = 1, 2, 3. For each k, the structures are deleted
    in every subset when there are at most `max_subsets` subsets (always for k = 1 at J <= 1000), else in a seeded
    sample of `max_subsets` distinct subsets that always contains the extreme subset below; reported: the share of
    subsets in which the outcome label and the sign of the mean are unchanged. A deletion that leaves fewer than 6
    structures has no label (decision 4) and so counts as a change. FRAGILE: any deletion with k <= 3 changes the label.

    Extreme-deletion rule (g3_scorecard_thresholds.md section 1.5): when the label interval excludes zero, delete the
    1, 2 and 3 structures with the largest estimates in the direction of the effect; the label interval (one-sided 95%
    bound for one-sided contrasts, by decision 2; 95% two-sided otherwise) must still exclude zero in that direction
    each time, else NOT_ROBUST."""

    d = np.asarray([float(x) for x in diffs if x is not None and math.isfinite(x)])
    J = len(d)
    if J < MIN_EVALUABLE_STRUCTURES:
        return {"assessable": False, "J": J, "reason": f"fewer than {MIN_EVALUABLE_STRUCTURES} evaluable structures"}
    full = _labels_after_deletion(d, np.zeros((1, 0), dtype=int), margin, alternative)
    full_label, full_mean = str(full["label"][0]), float(full["mean"][0])
    full_sign = int(np.sign(full_mean))
    direction = 1 if full_mean >= 0 else -1
    excludes = bool(full["lo"][0] > 0 or full["hi"][0] < 0)
    order = np.argsort(-direction * d, kind="stable")  # most extreme in the direction of the effect first
    rng = np.random.default_rng(seed)
    by_k: dict[str, Any] = {}
    extreme: dict[str, Any] = {}
    fragile = False
    for k in ks:
        if J - k < 2:
            by_k[str(k)] = {"assessable": False, "reason": f"J - k = {J - k} leaves no interval"}
            continue
        n_all = math.comb(J, k)
        extreme_set = tuple(sorted(int(i) for i in order[:k]))
        if n_all <= max_subsets:
            subsets = list(itertools.combinations(range(J), k))
            exhaustive = True
        else:
            chosen = {extreme_set}
            while len(chosen) < max_subsets:
                chosen.add(tuple(sorted(int(i) for i in rng.choice(J, size=k, replace=False))))
            subsets = sorted(chosen)
            exhaustive = False
        res = _labels_after_deletion(d, np.asarray(subsets, dtype=int), margin, alternative)
        label_same = res["label"] == full_label
        sign_same = np.sign(res["mean"]) == full_sign
        labels, counts = np.unique(res["label"], return_counts=True)
        by_k[str(k)] = {"assessable": True, "n_subsets": len(subsets), "n_possible": n_all, "exhaustive": exhaustive,
                        "share_label_unchanged": float(label_same.mean()), "share_sign_unchanged": float(sign_same.mean()),
                        "labels": {str(a): int(b) for a, b in zip(labels, counts)}, "J_after": J - k}
        fragile = fragile or not bool(label_same.all())
        ext = _labels_after_deletion(d, np.asarray([extreme_set], dtype=int), margin, alternative)
        lo, hi = float(ext["lo"][0]), float(ext["hi"][0])
        extreme[str(k)] = {"dropped_index": list(extreme_set), "dropped_estimates": [float(d[i]) for i in extreme_set],
                           "interval": [lo, hi], "label": str(ext["label"][0]),
                           "still_excludes_zero": bool(lo > 0) if direction > 0 else bool(hi < 0)}
    not_robust = excludes and any(not v["still_excludes_zero"] for v in extreme.values())
    return {"assessable": True, "J": J, "full_label": full_label, "full_sign": full_sign, "direction": direction,
            "by_k": by_k, "fragile": fragile, "extreme_deletion": extreme if excludes else None,
            "not_robust": bool(not_robust), "max_subsets": max_subsets, "seed": seed}


def diagnosed_summary(diffs: Sequence[float | None], margin: float, alternative: str,
                      hierarchical: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """`paired_summary` plus `method_agreement` and `leave_k_out` (decision 5)."""

    summary = paired_summary(diffs, margin, alternative)
    if summary["outcome"] != "NOT_EVALUATED":
        summary["method_agreement"] = method_agreement(diffs, summary, hierarchical)
        summary["robustness"] = leave_k_out(diffs, margin, alternative)
    if hierarchical is not None:
        summary["hierarchical"] = dict(hierarchical)
    return summary


PRIMARY = {"F1": ("F1", "greater"), "F2": ("F2", "greater"), "F3": ("F3", "two-sided")}


def primary_family(estimates: Mapping[str, Mapping[str, Any]], diagnostics: bool = True,
                   hierarchical: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """F1 (one-sided, loss > 0), F2 (one-sided, excess > 0), F3 (two-sided), Holm-corrected on the sign-flip p values.
    With `diagnostics`, each evaluable contrast also carries `method_agreement` and `robustness` (decision 5);
    `hierarchical` (the output of `hierarchical_view`) is attached beside, complementary only."""

    res: dict[str, Any] = {}
    for name, (key, alternative) in PRIMARY.items():
        diffs = [e[key] for e in estimates.values()]
        hier = (hierarchical or {}).get(name)
        res[name] = (diagnosed_summary(diffs, SESOI[name], alternative, hier) if diagnostics
                     else paired_summary(diffs, SESOI[name], alternative))
    evaluable = {k: v["p_sign_flip"] for k, v in res.items() if "p_sign_flip" in v}
    res["holm"] = holm(evaluable) if evaluable else {}
    return res


def phrasing_agreement_rule_a(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell],
                              phrasings: Sequence[int | str] = (0, 1), view: str = PRIMARY_VIEW) -> dict[str, Any]:
    """RULE A, kept for the record and no longer used by the scorecard (superseded 2026-11-14 by rule B,
    `phrasing_agreement`; plan_revision_v2.2 section E). Per-phrasing F1-F3 and the phrasing-by-role check: the
    per-structure difference between two phrasings' estimates must be equivalent to zero within the SESOI (TOST), or both phrasings' estimates exceed the SESOI in one direction.
    Phrasings are indices (`phrasing_indices`: the first R phrasing with the first D phrasing) or exact ids."""

    per = {p: structure_estimates(records, cells, view, phrasing=p) for p in phrasings}
    out: dict[str, Any] = {"phrasings": list(phrasings),
                           "per_phrasing": {str(p): primary_family(e) for p, e in per.items()}}
    if len(phrasings) == 2:
        a, b = phrasings
        for f in ("F1", "F2", "F3"):
            diffs = [per[a][s][f] - per[b][s][f] for s in per[a] if s in per[b]
                     and per[a][s][f] is not None and per[b][s][f] is not None]
            summary = paired_summary(diffs, SESOI[f], "two-sided")
            same_side = all(out["per_phrasing"][str(p)][f].get("ci95_t", [0, 0])[0] > SESOI[f] for p in phrasings) or all(
                out["per_phrasing"][str(p)][f].get("ci95_t", [0, 0])[1] < -SESOI[f] for p in phrasings)
            summary["agree"] = summary.get("outcome") == "EQUIVALENT" or same_side
            summary["same_side_beyond_sesoi"] = same_side
            out[f"phrasing_by_role_{f}"] = summary
    return out


# --- hierarchical view (complementary, decision 5) ---------------------------------------------------------------------------

HIER_FE_PRIOR_SD = 5.0  # weakly informative N(0, 5^2) on fixed effects (logit scale): covers rates 0.007-0.993 at 1 SD
HIER_VC_PRIOR_SD = 1.0  # statsmodels default prior SD of the log variance-component SDs
HIER_MAX_ABS_LOGIT = 10.0  # |coefficient| above this is read as (quasi-)separation, i.e. an unstable fit


def _hier_rows(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell], contrast: str,
               view: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[str]]:
    """Per-sample rows (y, fixed-effect design, structure index, fixed-effect names, random-slope names)."""

    by_cell = group_records(records, cells)
    ys: list[int] = []
    xs: list[list[float]] = []
    groups: list[str] = []
    for key, recs in by_cell.items():
        cell = cells[key]
        if cell.heldout:
            continue
        if contrast == "F1" and cell.stratum in ("N", "D"):
            for r in recs:
                ys.append(tracking(r, view))
                xs.append([1.0, float(cell.stratum == "D")])
                groups.append(cell.structure_id)
        elif contrast == "F2" and cell.stratum == "R":
            for r in recs:
                for is_neglect, target in ((1.0, cell.foils.get("neglect")), (0.0, cell.placebo)):
                    ys.append(int(matches_value(r, target)))
                    xs.append([1.0, is_neglect])
                    groups.append(cell.structure_id)
        elif contrast == "F3" and cell.stratum in ("R", "D") and cell.value_index is not None:
            for r in recs:
                is_r = float(cell.stratum == "R")
                ys.append(tracking(r, view))
                xs.append([1.0, is_r, float(cell.value_index), is_r * float(cell.value_index)])
                groups.append(cell.structure_id)
    names = {"F1": ["intercept", "D"], "F2": ["intercept", "neglect"], "F3": ["intercept", "R", "z", "R:z"]}[contrast]
    x = np.asarray(xs, float) if xs else np.zeros((0, len(names)))
    if contrast == "F3" and len(x):
        x[:, 2] -= x[:, 2].mean()  # centre the value index; the interaction is unchanged
        x[:, 3] = x[:, 1] * x[:, 2]
    slopes = {"F1": ["D"], "F2": ["neglect"], "F3": ["R", "R:z"]}[contrast]
    return np.asarray(ys, float), x, np.asarray(groups), names, slopes


def _hier_fit_one(y: np.ndarray, x: np.ndarray, groups: np.ndarray, names: list[str], slopes: list[str],
                  term: str, sign: int, level: float) -> dict[str, Any]:
    import warnings

    import scipy.sparse as sparse
    import statsmodels.api as sm
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    levels, g = np.unique(groups, return_inverse=True)
    J = len(levels)
    base = {"term": term, "J": int(J), "n_rows": int(len(y)), "level": level}
    if J < MIN_EVALUABLE_STRUCTURES:
        return {**base, "status": "NOT_EVALUATED", "reason": f"fewer than {MIN_EVALUABLE_STRUCTURES} structures"}
    if y.min() == y.max():
        return {**base, "status": "NOT_EVALUATED", "reason": "the outcome does not vary"}
    j = names.index(term)
    z = stats.norm.ppf(1 - (1 - level) / 2)
    reasons = []
    # 1) Bayesian mixed logistic model: structure random intercept and random slope(s) of the contrast term(s), each
    #    with its own variance component; posterior mode and Laplace SD (fit_map, Newton-CG, which converged where BFGS
    #    stopped on precision loss at the same optimum). Mean-field VB (fit_vb) understates posterior SDs (by 40-60% in
    #    the G1 prototype), so the Laplace approximation is used.
    columns = [np.ones(len(y))] + [x[:, names.index(t)] for t in slopes]
    rows = np.concatenate([np.arange(len(y))] * len(columns))
    cols = np.concatenate([g + i * J for i in range(len(columns))])
    vals = np.concatenate(columns)
    keep = vals != 0
    exog_vc = sparse.csr_matrix((vals[keep], (rows[keep], cols[keep])), shape=(len(y), J * len(columns)))
    ident = np.repeat(np.arange(len(columns)), J)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = BinomialBayesMixedGLM(y, x, exog_vc, ident, vcp_p=HIER_VC_PRIOR_SD, fe_p=HIER_FE_PRIOR_SD)
            # statsmodels draws the random-effect start values from the global numpy RNG; a fixed start keeps the fit
            # reproducible and leaves the global RNG alone
            model._get_start = lambda: np.concatenate((np.zeros(model.k_fep), np.ones(model.k_vcp),  # noqa: SLF001
                                                      np.zeros(model.k_vc)))
            fit = model.fit_map(method="Newton-CG")
        est, sd = float(fit.fe_mean[j]), float(fit.fe_sd[j])
        retvals = getattr(fit, "optim_retvals", None)
        converged = bool(retvals.get("success", False)) if isinstance(retvals, dict) else True
        if converged and math.isfinite(est) and math.isfinite(sd) and sd > 0 and abs(est) <= HIER_MAX_ABS_LOGIT:
            e = sign * est
            return {**base, "status": "OK", "method": "BinomialBayesMixedGLM.fit_map (structure random intercept and "
                    f"random slope of {', '.join(slopes)})", "estimate": e, "sd": sd,
                    "interval": [float(e - z * sd), float(e + z * sd)],
                    "vc_sd_log_mean": [float(v) for v in fit.vcp_mean]}
        reasons.append(f"Bayesian fit unstable (converged={converged}, estimate={est}, sd={sd})")
    except Exception as exc:  # noqa: BLE001 - any failure of the complementary fit falls back, never crashes the analysis
        reasons.append(f"Bayesian fit failed: {exc!r}")
    # 2) fallback: GEE (binomial, exchangeable within structure) with the robust sandwich SE clustered by structure
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gee = sm.GEE(y, x, groups=g, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
        est, sd = float(gee.params[j]), float(gee.bse[j])
        if math.isfinite(est) and math.isfinite(sd) and sd > 0 and abs(est) <= HIER_MAX_ABS_LOGIT:
            e = sign * est
            return {**base, "status": "OK", "method": "GEE (binomial, exchangeable, robust SE clustered by structure)",
                    "estimate": e, "sd": sd, "interval": [float(e - z * sd), float(e + z * sd)],
                    "fallback_reason": "; ".join(reasons)}
        reasons.append(f"GEE unstable (estimate={est}, sd={sd})")
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"GEE failed: {exc!r}")
    return {**base, "status": "NOT_EVALUATED", "reason": "; ".join(reasons)}


def hierarchical_view(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell],
                      view: str = PRIMARY_VIEW) -> dict[str, dict[str, Any]]:
    """Decision 5: the mixed-effects logistic view of F1-F3 on per-sample outcomes (plan `sec:statistics`: hierarchical
    models are complementary views, not a ranking; the paired analysis of structure-level estimates decides).

    * F1: tracking ~ D (N and D samples); estimate = -beta_D (positive = a loss in D, the sign of F1).
    * F2: match ~ neglect (each R sample gives a neglect-match row and a placebo-match row); estimate = beta_neglect.
    * F3: tracking ~ R + z + R:z (R and D samples, z = value index, centred); estimate = beta_R:z, the R minus D slope.
    Each has a structure random intercept and structure random slope(s) of its contrast term(s). Fit: the Bayesian
    mixed GLM (posterior mode, Laplace SD); if it fails to converge, gives a non-finite or non-positive SD or a
    coefficient beyond |10| logits (separation), a GEE clustered by structure is used instead and the reason is
    recorded; if both fail, NOT_EVALUATED. The coefficient is on the logit scale, so only its sign and whether its
    interval excludes zero are compared with the paired analysis (at the same level: 90% for F1, F2; 95% for F3)."""

    out = {}
    for contrast, term, sign, level in (("F1", "D", -1, 0.90), ("F2", "neglect", 1, 0.90), ("F3", "R:z", 1, 0.95)):
        y, x, groups, names, slopes = _hier_rows(records, cells, contrast, view)
        out[contrast] = _hier_fit_one(y, x, groups, names, slopes, term, sign, level)
    return out


# --- rare shares ----------------------------------------------------------------------------------------------------------

def jeffreys(successes: int, n: int, level: float = 0.95) -> dict[str, float]:
    a, b = successes + 0.5, n - successes + 0.5
    return {"rate": a / (a + b), "lo": float(stats.beta.ppf((1 - level) / 2, a, b)),
            "hi": float(stats.beta.ppf(1 - (1 - level) / 2, a, b)), "x": successes, "n": n}


def beta_binomial_fit(counts: Sequence[tuple[int, int]], n_boot: int = 200) -> dict[str, Any]:
    """Maximum-likelihood Beta-Binomial over structures (x successes of n each): mean mu and overdispersion rho, with a
    bootstrap-over-structures interval for mu (`n_boot` resamples; 0 skips it). Zero totals give a finite estimate,
    never a reported zero."""

    data = [(int(x), int(n)) for x, n in counts if n > 0]
    if not data:
        return {"mu": None, "reason": "no samples"}

    def fit(sample: Sequence[tuple[int, int]]) -> tuple[float, float]:
        x = np.array([c[0] for c in sample])
        n = np.array([c[1] for c in sample])

        def nll(theta: np.ndarray) -> float:
            mu = 1 / (1 + math.exp(-theta[0]))
            phi = math.exp(theta[1])
            return -float(stats.betabinom.logpmf(x, n, mu * phi, (1 - mu) * phi).sum())

        start = np.array([math.log((x.sum() + 0.5) / (n.sum() - x.sum() + 0.5)), math.log(10.0)])
        r = optimize.minimize(nll, start, method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-9, "maxiter": 4000})
        return 1 / (1 + math.exp(-r.x[0])), 1 / (1 + math.exp(r.x[1]))

    mu, rho = fit(data)
    out = {"mu": mu, "rho": rho, "J": len(data), "x_total": sum(c[0] for c in data), "n_total": sum(c[1] for c in data)}
    if n_boot:
        rng = np.random.default_rng(SEED)
        boots = np.sort([fit([data[i] for i in rng.integers(0, len(data), len(data))])[0] for _ in range(n_boot)])
        out["ci95_bootstrap"] = [float(boots[max(0, int(0.025 * n_boot) - 1)]),
                                 float(boots[min(n_boot - 1, int(0.975 * n_boot) - 1)])]
    return out


# --- misuse support and lambda ---------------------------------------------------------------------------------------------

def misuse_support(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell], structure_id: str,
                   stratum: str = "D") -> dict[str, Any]:
    """For each misuse curve h of the stratum's cells: per value, its share in the stratum and the share of N answers at
    the same value; supported when the stratum share exceeds the N rate at >= 2 of >= 3 values. Confounded curves are
    listed, not attributed."""

    by_cell = group_records(records, cells)
    n_recs = [r for k, rs in by_cell.items() if cells[k].structure_id == structure_id and cells[k].stratum == "N" for r in rs]
    per_h: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    confounded: set[str] = set()
    for key, recs in by_cell.items():
        cell = cells[key]
        if cell.structure_id != structure_id or cell.stratum != stratum or cell.value_index is None:
            continue
        confounded.update(cell.confounded)
        for h, target in cell.foils.items():
            if h in ("relevant_twin", "neglect"):
                continue
            slot = per_h[h].setdefault(cell.value_index, {"x": 0, "n": 0, "n_x": 0, "n_n": 0})
            slot["x"] += sum(matches_value(r, target) for r in recs)
            slot["n"] += len(recs)
            slot["n_x"] = sum(matches_value(r, target) for r in n_recs)
            slot["n_n"] = len(n_recs)
    out = {}
    for h, by_z in per_h.items():
        wins = sum(1 for v in by_z.values() if v["n"] and v["n_n"] and v["x"] / v["n"] > v["n_x"] / v["n_n"])
        out[h] = {"by_value": by_z, "values": len(by_z), "values_above_N": wins,
                  "supported": len(by_z) >= 3 and wins >= 2,
                  "confounded": any(h in c for c in confounded)}
    return out


def curve_class(name: str) -> str:
    """The population-level misuse curve of a per-structure foil name: `add:m2` and `add:M` are both `add`; foils
    without a node (`copy`, `digit_copy`, `relevant_twin`, `wrong_law`, `out_of_regime`) are their own class."""

    return name.split(":", 1)[0]


ROUTE_CLASSES = {"D": ("replace", "add", "subtract", "relevant_twin"), "C": ("wrong_law",), "K": ("out_of_regime",)}
COPY_CLASSES = ("copy", "digit_copy")
MIN_MISUSE_MATCHES = 5  # decision 13: fewer D matches in total make attribution INCONCLUSIVE, not absent
NOT_MISUSE = ("neglect",)


def _confounded_names(cell: Cell) -> set[str]:
    return {part for pair in cell.confounded for part in pair.split("~") if part != "gold"}


def _class_shares(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell], stratum: str,
                  classes: Sequence[str] | None = None) -> dict[str, dict[str, Any]]:
    """Per class h and structure: per study value z, the stratum's samples matching any unconfounded member of h at z,
    and the N samples of the same structure matching the same targets; plus whether h is defined and confounded."""

    by_cell = group_records(records, cells)
    n_recs: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for key, recs in by_cell.items():
        if cells[key].stratum == "N":
            n_recs[cells[key].structure_id].extend(recs)
    defined: dict[tuple[str, str], set[str]] = defaultdict(set)
    confounded: dict[tuple[str, str], set[str]] = defaultdict(set)
    for c in cells.values():
        if c.stratum != stratum or c.heldout or c.value_index is None:
            continue
        for name in c.foils:
            if name in NOT_MISUSE or (classes is not None and curve_class(name) not in classes):
                continue
            defined[(curve_class(name), c.structure_id)].add(name)
        for name in _confounded_names(c):
            confounded[(curve_class(name), c.structure_id)].add(name)
    out: dict[str, dict[str, Any]] = defaultdict(dict)
    for (h, sid), members in defined.items():
        usable = members - confounded[(h, sid)]
        slot: dict[str, Any] = {"members": sorted(members), "usable": sorted(usable), "confounded": not usable,
                                "by_value": {}}
        out[h][sid] = slot
        if not usable:
            continue
        for key, recs in by_cell.items():
            c = cells[key]
            if c.structure_id != sid or c.stratum != stratum or c.heldout or c.value_index is None:
                continue
            targets = [c.foils[m] for m in usable if m in c.foils]
            v = slot["by_value"].setdefault(c.value_index, {"x": 0, "n": 0, "targets": set()})
            v["x"] += sum(any(matches_value(r, t) for t in targets) for r in recs)
            v["n"] += len(recs)
            v["targets"].update(targets)
        for v in slot["by_value"].values():
            nr = n_recs.get(sid, [])
            v["n_x"] = sum(any(matches_value(r, t) for t in v["targets"]) for r in nr)
            v["n_n"] = len(nr)
            v["targets"] = sorted(v["targets"])
    return out


def _excess(slot: Mapping[str, Any]) -> float | None:
    """Per structure: mean over the study values of (stratum share - N share) matching the curve."""

    vals = [v["x"] / v["n"] - v["n_x"] / v["n_n"] for v in slot["by_value"].values() if v["n"] and v["n_n"]]
    return float(np.mean(vals)) if vals else None


def misuse_attribution(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell],
                       stratum: str = "D") -> dict[str, Any]:
    """Population-level misuse excess M_h and attribution A_h per curve class (g3_scorecard_thresholds.md section 2 as
    amended by decision 13). Per structure, M_h = mean over the study values of (share of stratum samples matching
    f_h(z) - share of N samples matching f_h(z)), where a class's members confounded with the gold in that structure
    are not counted. M_h is summarised over structures like a primary contrast (one-sided, SESOI 0.10, with method
    agreement and robustness). Attribution of h:

    * NOT_EVALUATED: h defined (with an unconfounded member) in fewer than 6 structures;
    * NOT_ATTRIBUTED (CONFOUNDED): h confounded with the gold in more than half of the structures where it is defined;
    * INCONCLUSIVE: fewer than 5 stratum samples in total match h (rare categories; not absent);
    * ATTRIBUTED: M_h's interval excludes zero in the positive direction (EFFECT or TRIVIAL_EFFECT, with the decision
      methods agreeing and not NOT_ROBUST), and the Beta-Binomial pooled stratum share exceeds the pooled N rate at
      2 or more of at least 3 study values;
    * NOT_ATTRIBUTED otherwise."""

    shares = _class_shares(records, cells, stratum)
    out: dict[str, Any] = {}
    for h, per_s in sorted(shares.items()):
        n_defined = len(per_s)
        n_conf = sum(1 for v in per_s.values() if v["confounded"])
        usable = {sid: v for sid, v in per_s.items() if not v["confounded"]}
        diffs = {sid: _excess(v) for sid, v in usable.items()}
        summary = diagnosed_summary(list(diffs.values()), SESOI["M"], "greater")
        x_total = sum(b["x"] for v in usable.values() for b in v["by_value"].values())
        zs = sorted({z for v in usable.values() for z in v["by_value"]})
        pooled = {}
        for z in zs:
            d_counts = [(v["by_value"][z]["x"], v["by_value"][z]["n"]) for v in usable.values() if z in v["by_value"]]
            n_counts = [(v["by_value"][z]["n_x"], v["by_value"][z]["n_n"]) for v in usable.values() if z in v["by_value"]]
            mu_d = beta_binomial_fit(d_counts, n_boot=0).get("mu")
            mu_n = beta_binomial_fit(n_counts, n_boot=0).get("mu")
            x_d = sum(c[0] for c in d_counts)
            # with no stratum match at z the two fitted means differ only by optimiser artefacts: never "above"
            pooled[str(z)] = {"mu_stratum": mu_d, "mu_N": mu_n, "x_stratum": x_d,
                              "above_N": bool(x_d > 0 and mu_d is not None and mu_n is not None and mu_d > mu_n)}
        wins = sum(v["above_N"] for v in pooled.values())
        label = effective_label(summary)
        entry = {"class": h, "stratum": stratum, "structures_defined": n_defined, "structures_confounded": n_conf,
                 "J": summary["J"], "M": summary, "effective_label": label, "matches_total": int(x_total),
                 "pooled_by_value": pooled, "values": len(zs), "values_above_N": int(wins),
                 "per_structure": {sid: {"excess": diffs[sid], "members": v["usable"]} for sid, v in usable.items()}}
        if n_defined == 0 or (summary["outcome"] == "NOT_EVALUATED" and n_conf * 2 <= n_defined):
            entry["attribution"], entry["reason"] = "NOT_EVALUATED", (
                f"defined without confounding in {len(usable)} structures (< {MIN_EVALUABLE_STRUCTURES})")
        elif n_conf * 2 > n_defined:
            entry["attribution"], entry["reason"] = "NOT_ATTRIBUTED", (
                f"CONFOUNDED: confounded with the gold in {n_conf} of {n_defined} structures (more than half)")
        elif x_total < MIN_MISUSE_MATCHES:
            entry["attribution"], entry["reason"] = "INCONCLUSIVE", (
                f"{x_total} matching samples in total (< {MIN_MISUSE_MATCHES}): rare, not absent")
        elif label["label"] in ("EFFECT", "TRIVIAL_EFFECT") and label["sign"] > 0 and len(zs) >= 3 and wins >= 2:
            entry["attribution"], entry["reason"] = "ATTRIBUTED", (
                f"M_{h} {label['label']} positive and pooled share above N at {wins} of {len(zs)} values")
        else:
            entry["attribution"], entry["reason"] = "NOT_ATTRIBUTED", (
                f"M_{h} effective label {label['label']} (sign {label['sign']}); pooled share above N at {wins} of "
                f"{len(zs)} values")
        out[h] = entry
    return out


def copy_excess_r(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell]) -> dict[str, Any]:
    """CR: per structure, mean over values of (share of R samples matching the copy curve - share of N samples matching
    it), per copy class (`copy` where q has the target's dimension, `digit_copy` otherwise). N contains no numeral, so
    it is a valid comparator here. One-sided, SESOI 0.10."""

    shares = _class_shares(records, cells, "R", classes=COPY_CLASSES)
    out = {}
    for h in COPY_CLASSES:
        per_s = shares.get(h, {})
        diffs = [_excess(v) for v in per_s.values() if not v["confounded"]]
        summary = diagnosed_summary(diffs, SESOI["CR"], "greater")
        out[h] = {"class": h, "structures_defined": len(per_s), "CR": summary, "effective_label": effective_label(summary)}
    return out


def cost_contrasts(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell]) -> dict[str, Any]:
    """O5 (decisions 10, 11): per structure, L5 = log(mean generated tokens in D / mean in N) and B5 = BUDGET_EXHAUSTED
    share in D - share in N; N is the primary comparator, no-cue beside. One-sided (a rise), SESOI log(1.2) and 0.05.
    Records without `n_generated_tokens` do not enter L5."""

    by_cell = group_records(records, cells)
    tok: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    bud: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for key, recs in by_cell.items():
        c = cells[key]
        if c.heldout or c.stratum not in ("D", "N", "none"):
            continue
        for r in recs:
            if r.get("n_generated_tokens") is not None:
                tok[c.structure_id][c.stratum].append(float(r["n_generated_tokens"]))
            bud[c.structure_id][c.stratum].append(int(r.get("completion_status") == "BUDGET_EXHAUSTED"))

    def l5(sid: str, ref: str) -> float | None:
        a, b = tok[sid].get("D"), tok[sid].get(ref)
        return math.log(np.mean(a) / np.mean(b)) if a and b and np.mean(a) > 0 and np.mean(b) > 0 else None

    def b5(sid: str, ref: str) -> float | None:
        a, b = bud[sid].get("D"), bud[sid].get(ref)
        return float(np.mean(a) - np.mean(b)) if a and b else None

    sids = sorted(set(tok) | set(bud))
    return {"L5": diagnosed_summary([l5(s, "N") for s in sids], SESOI["L5"], "greater"),
            "B5": diagnosed_summary([b5(s, "N") for s in sids], SESOI["B5"], "greater"),
            "L5_vs_no_cue": paired_summary([l5(s, "none") for s in sids], SESOI["L5"], "greater"),
            "B5_vs_no_cue": paired_summary([b5(s, "none") for s in sids], SESOI["B5"], "greater")}


def ck_family(estimates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """C/K versions of F1 (T̄_N - T̄_C, one-sided, SESOI 0.10) and of the value dependence (the stratum's own slope of
    empirical-logit tracking per value step, two-sided, SESOI log(1.5), target 0), for H3 (C/K) and H6-extended."""

    out = {}
    for st in ("C", "K"):
        f1 = [e.get(f"F1_{st}") for e in estimates.values()]
        slope = [e.get(f"slope_{st}") for e in estimates.values()]
        run = any(x is not None for x in f1)
        out[st] = {"run": run, "F1": diagnosed_summary(f1, SESOI["F1"], "greater"),
                   "slope": diagnosed_summary(slope, SESOI["F3"], "two-sided")}
    return out


def effective_label(summary: Mapping[str, Any]) -> dict[str, Any]:
    """The label a scorecard reads (g3_scorecard_thresholds.md sections 1.4, 1.5): an EFFECT or TRIVIAL_EFFECT whose
    decision methods (t, sign-flip, bootstrap) disagree is read as INCONCLUSIVE flagged METHOD_DISAGREEMENT; one that
    does not survive the extreme deletion is INCONCLUSIVE flagged NOT_ROBUST. FRAGILE (any leave-k-out label change) is
    carried as a flag. `sign` is the sign of the mean (0 when not evaluated)."""

    raw = summary.get("outcome", "NOT_EVALUATED")
    flags: list[str] = []
    label = raw
    if raw == "NOT_EVALUATED":
        return {"label": raw, "raw": raw, "sign": 0, "flags": flags}
    agreement = summary.get("method_agreement") or {}
    robust = summary.get("robustness") or {}
    if raw in ("EFFECT", "TRIVIAL_EFFECT"):
        if agreement and not agreement.get("decision_methods_agree", True):
            label = "INCONCLUSIVE"
            flags.append("METHOD_DISAGREEMENT")
        if robust.get("not_robust"):
            label = "INCONCLUSIVE"
            flags.append("NOT_ROBUST")
    if robust.get("fragile"):
        flags.append("FRAGILE")
    mean = summary.get("mean", 0.0)
    return {"label": label, "raw": raw, "sign": 1 if mean > 0 else (-1 if mean < 0 else 0), "flags": flags}


def hodges_lehmann(values: Sequence[float]) -> float | None:
    v = list(values)
    if not v:
        return None
    walsh = [(v[i] + v[j]) / 2 for i in range(len(v)) for j in range(i, len(v))]
    return float(np.median(walsh))


def answer_modes(records: Sequence[Mapping[str, Any]], cell: Cell) -> dict[str, int]:
    modes: dict[str, int] = defaultdict(int)
    for r in records:
        if r.get("completion_status") != "COMPLETE":
            modes["non_complete"] += 1
            continue
        if matches_value(r, cell.gold):
            modes["correct"] += 1
            continue
        hits = [h for h, t in cell.foils.items() if matches_value(r, t)]
        modes[hits[0] if len(hits) == 1 else ("multi" if hits else "other")] += 1
    return dict(modes)


def lambdas(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell], structure_id: str) -> dict[str, Any]:
    """lambda_r for each value pair (a, b) and role, scaled by the R twin's certified change; flagged MULTIMODAL."""

    by_cell = group_records(records, cells)
    pooled: dict[tuple[str, int], list[float]] = defaultdict(list)  # complete answers over phrasings of a role-value cell
    multimodal: dict[tuple[str, int], bool] = {}
    gold_r: dict[int, float] = {}
    for key, recs in by_cell.items():
        cell = cells[key]
        if cell.structure_id != structure_id or cell.stratum not in ("R", "D", "C", "K") or cell.value_index is None:
            continue
        k = (cell.stratum, cell.value_index)
        pooled[k].extend(float(r["value_in_gold_unit"]) for r in recs
                         if r.get("completion_status") == "COMPLETE" and r.get("value_in_gold_unit") is not None)
        modes = answer_modes(recs, cell)
        n_complete = sum(v for m, v in modes.items() if m != "non_complete")
        big = [m for m, v in modes.items() if m != "non_complete" and n_complete and v / n_complete >= MULTIMODAL_SHARE]
        multimodal[k] = multimodal.get(k, False) or len(big) >= 2
        if cell.stratum == "R":
            gold_r[cell.value_index] = cell.gold
    loc = {k: hodges_lehmann(v) for k, v in pooled.items()}
    out = {}
    for role in ("R", "D", "C", "K"):
        zs = sorted(z for (r, z) in loc if r == role)
        for a, b in itertools.combinations(zs, 2):
            if a not in gold_r or b not in gold_r or loc[(role, a)] is None or loc[(role, b)] is None:
                out[f"{role}:{a}-{b}"] = {"lambda": None, "status": "NOT_EVALUATED"}
                continue
            lam = (loc[(role, b)] - loc[(role, a)]) / (gold_r[b] - gold_r[a])
            flag = multimodal.get((role, a)) or multimodal.get((role, b))
            out[f"{role}:{a}-{b}"] = {"lambda": lam, "status": "MULTIMODAL" if flag else "OK"}
    return out


# --- power simulation --------------------------------------------------------------------------------------------------------

@dataclass
class SimParams:
    base_logit: float = 1.0  # mean logit of tracking under N
    sd_structure: float = 1.0  # between-structure SD of the base logit
    sd_phrasing: float = 0.0  # logit noise on D phrasings only; > 0 lowers mean D tracking (Jensen), so it is not a null
    d_effect_logit: float = 0.0  # mean logit loss in D relative to N (0 = null)
    sd_d_effect: float = 0.5  # between-structure SD of the D effect
    n_values: int = 3
    n_phrasings: int = 2
    # Frozen design rule (G1, 2026-11-13): the non-numeric control N is sampled as often as all D cells of a structure
    # together (n_values x n_phrasings x k). With one N cell of k samples the one-sided F1 sign-flip test rejected a true
    # null at 0.059-0.074 when tracking is high (base logit 2.5-3.5); balanced, 0.032-0.043 (2,000 simulations each).
    n_n_cells: int = 6


def simulate_f1(params: SimParams, J: int, k: int, rng: np.random.Generator) -> list[float]:
    """Structure-level F1 estimates (T̄_N - T̄_D) for one simulated dataset, with the design's cell counts: k samples in
    each of `n_n_cells` N cells, k samples in each of n_values x n_phrasings D cells."""

    out = []
    for _ in range(J):
        base = rng.normal(params.base_logit, params.sd_structure)
        effect = rng.normal(params.d_effect_logit, params.sd_d_effect) if params.d_effect_logit else 0.0
        n_p = 1 / (1 + math.exp(-base))
        t_n = rng.binomial(k * params.n_n_cells, n_p) / (k * params.n_n_cells)
        hits = 0
        for _p in range(params.n_phrasings):
            ph = rng.normal(0, params.sd_phrasing) if params.sd_phrasing else 0.0
            p = 1 / (1 + math.exp(-(base - effect + ph)))
            hits += rng.binomial(k * params.n_values, p)
        out.append(t_n - hits / (k * params.n_values * params.n_phrasings))
    return out


def power_f1(params: SimParams, J: int, k: int, n_sims: int = 1000, seed: int = SEED) -> dict[str, float]:
    """Rejection rate of the one-sided F1 sign-flip test (alpha 0.05) and TOST-equivalence rate over simulated datasets."""

    rng = np.random.default_rng(seed)
    rej_flip = rej_t = equivalences = 0
    for _ in range(n_sims):
        diffs = simulate_f1(params, J, k, rng)
        summary = paired_summary(diffs, SESOI["F1"], "greater")
        rej_flip += summary.get("p_sign_flip", 1.0) < ALPHA
        rej_t += summary.get("p_t", 1.0) < ALPHA
        equivalences += summary.get("outcome") == "EQUIVALENT"
    return {"J": J, "k": k, "n_sims": n_sims, "rejection_rate_sign_flip": rej_flip / n_sims,
            "rejection_rate_t": rej_t / n_sims, "equivalence_rate": equivalences / n_sims}


@dataclass
class SimParamsF2:
    placebo_rate: float = 0.02  # mean share of R samples equal to the placebo value
    sd_structure_logit: float = 0.7
    neglect_excess_logit: float = 0.0  # logit increase of the neglect share over the placebo rate (0 = null)
    n_values: int = 3
    n_phrasings: int = 2


def simulate_f2(params: SimParamsF2, J: int, k: int, rng: np.random.Generator) -> list[float]:
    """Structure-level F2 estimates (neglect share - placebo rate) over k x n_values x n_phrasings R samples, where each
    sample is neglect, placebo or neither (a multinomial draw)."""

    n = k * params.n_values * params.n_phrasings
    base = math.log(params.placebo_rate / (1 - params.placebo_rate))
    out = []
    for _ in range(J):
        b = rng.normal(base, params.sd_structure_logit)
        p_plac = 1 / (1 + math.exp(-b))
        p_neg = 1 / (1 + math.exp(-(b + params.neglect_excess_logit)))
        if p_neg + p_plac > 0.95:
            p_neg, p_plac = 0.95 * p_neg / (p_neg + p_plac), 0.95 * p_plac / (p_neg + p_plac)
        neg, plac, _ = rng.multinomial(n, [p_neg, p_plac, 1 - p_neg - p_plac])
        out.append((neg - plac) / n)
    return out


@dataclass
class SimParamsF3:
    base_logit: float = 1.0
    sd_structure: float = 1.0
    slope_r: float = 0.0  # logit change of R tracking per value step
    slope_d: float = 0.0  # logit change of D tracking per value step (null: equal slopes)
    sd_slope: float = 0.2  # between-structure SD of each slope
    n_values: int = 3
    n_phrasings: int = 2


def simulate_f3(params: SimParamsF3, J: int, k: int, rng: np.random.Generator) -> list[float | None]:
    out = []
    for _ in range(J):
        base = rng.normal(params.base_logit, params.sd_structure)
        t_by_z: dict[tuple[str, int], list[int]] = {}
        for role, slope in (("R", params.slope_r), ("D", params.slope_d)):
            s = rng.normal(slope, params.sd_slope) if params.sd_slope else slope
            for z in range(params.n_values):
                p = 1 / (1 + math.exp(-(base + s * (z - (params.n_values - 1) / 2))))
                hits = int(rng.binomial(k * params.n_phrasings, p))
                t_by_z[(role, z)] = [1] * hits + [0] * (k * params.n_phrasings - hits)
        out.append(f3_estimate(t_by_z))
    return out


def power_generic(simulate, params, J: int, k: int, margin: float, alternative: str, n_sims: int = 1000,
                  seed: int = SEED) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    rej = eq = 0
    for _ in range(n_sims):
        summary = paired_summary(simulate(params, J, k, rng), margin, alternative)
        rej += summary.get("p_sign_flip", 1.0) < ALPHA
        eq += summary.get("outcome") == "EQUIVALENT"
    return {"J": J, "k": k, "n_sims": n_sims, "rejection_rate_sign_flip": rej / n_sims, "equivalence_rate": eq / n_sims}


def joint_tost_power(params_f1: SimParams, params_f2: SimParamsF2, params_f3: SimParamsF3, J: int, k: int,
                     n_sims: int = 1000, seed: int = SEED) -> dict[str, Any]:
    """Decision 21 (corrected 2026-11-14): power of the H6-RD route in G4. Two joint rates are reported: all of F1-F3
    EQUIVALENT (`joint_equivalence_rate`, TOST at alpha 0.05 each, an intersection-union test, no multiplicity
    correction; the earlier figure, capped near 0.73-0.79 at any J) and all EQUIVALENT or TRIVIAL_EFFECT
    (`joint_equivalent_or_trivial_rate`, the H6-RD criterion under decision 1 and the target of the curve), beside each single
    contrast's equivalence rate and the G4 rule (b) rate in which EQUIVALENT or TRIVIAL_EFFECT both count (decisions 1
    and 20). Each dataset draws F1, F2 and F3 for the same J structures from the existing simulators with the given
    variance components (from G2). The three contrasts are simulated independently given the parameters, so a
    correlation between them across structures is not modelled; with positive correlation the joint rate would be
    somewhat higher, so this is a conservative planning figure."""

    rng = np.random.default_rng(seed)
    single = {"F1": 0, "F2": 0, "F3": 0}
    single_or_trivial = {"F1": 0, "F2": 0, "F3": 0}
    joint = joint_or_trivial = 0
    for _ in range(n_sims):
        outcomes = {"F1": paired_summary(simulate_f1(params_f1, J, k, rng), SESOI["F1"], "greater")["outcome"],
                    "F2": paired_summary(simulate_f2(params_f2, J, k, rng), SESOI["F2"], "greater")["outcome"],
                    "F3": paired_summary(simulate_f3(params_f3, J, k, rng), SESOI["F3"], "two-sided")["outcome"]}
        for f, o in outcomes.items():
            single[f] += o == "EQUIVALENT"
            single_or_trivial[f] += o in ("EQUIVALENT", "TRIVIAL_EFFECT")
        joint += all(o == "EQUIVALENT" for o in outcomes.values())
        joint_or_trivial += all(o in ("EQUIVALENT", "TRIVIAL_EFFECT") for o in outcomes.values())
    return {"J": J, "k": k, "n_sims": n_sims, "seed": seed,
            "single_equivalence_rate": {f: v / n_sims for f, v in single.items()},
            "single_equivalent_or_trivial_rate": {f: v / n_sims for f, v in single_or_trivial.items()},
            "joint_equivalence_rate": joint / n_sims, "joint_equivalent_or_trivial_rate": joint_or_trivial / n_sims}


def joint_tost_power_curve(params_f1: SimParams, params_f2: SimParamsF2, params_f3: SimParamsF3,
                           Js: Sequence[int], k: int, n_sims: int = 1000, seed: int = SEED,
                           target: float = 0.80) -> dict[str, Any]:
    """`joint_tost_power` over a grid of J. Decision 21 as corrected 2026-11-14 (plan_revision_v2.2 section E): the target
    applies to the joint EQUIVALENT-or-TRIVIAL_EFFECT rate (the H6-RD criterion under decision 1); `J_for_target` is the
    smallest J in the grid reaching it (None if none does: open more sealed structures). The all-EQUIVALENT rate (the
    earlier target, capped near 0.73-0.79 because the label needs the interval to include zero) stays in every row and in
    `J_for_target_all_equivalent`."""

    rows = [joint_tost_power(params_f1, params_f2, params_f3, J, k, n_sims, seed) for J in Js]
    hit = [r["J"] for r in rows if r["joint_equivalent_or_trivial_rate"] >= target]
    hit_eq = [r["J"] for r in rows if r["joint_equivalence_rate"] >= target]
    return {"rows": rows, "target": target, "target_applies_to": "joint_equivalent_or_trivial_rate",
            "J_for_target": min(hit) if hit else None,
            "J_for_target_all_equivalent": min(hit_eq) if hit_eq else None}


# --- phrasing-agreement rules (G1 design study, 2026-11-14; rule B adopted as operative by plan_revision_v2.2 section E) -------

AGREE, DISAGREE, UNRESOLVED = "AGREE", "DISAGREE", "UNRESOLVED"
AGREEMENT_RULES = ("A", "B", "C", "D")
AGREEMENT_RULE_TEXT = {
    "A": "as implemented: per-structure phrasing difference two-sided summary; AGREE iff its label is EQUIVALENT (TOST passes "
         "and the 95% interval includes zero) or both per-phrasing 95% intervals lie beyond the SESOI on the same side",
    "B": "plan's first clause: per-structure phrasing difference; AGREE iff TOST within the SESOI passes, DISAGREE iff its 95% "
         "interval excludes zero and extends beyond the SESOI, else UNRESOLVED",
    "C": "as B with margin SESOI for F1/F2 and 2 x SESOI for F3 (sensitivity only)",
    "D": "pooled label decides; phrasings count as agreeing unless the B-difference is DISAGREE (wording-dependence must be "
         "demonstrated; UNRESOLVED is shown but does not demote)",
}


def agreement_margin(contrast: str, rule: str) -> float:
    """Equivalence margin of the phrasing difference: the contrast's SESOI, except 2 x SESOI for F3 under rule C."""

    return 2 * SESOI[contrast] if (rule == "C" and contrast == "F3") else SESOI[contrast]


def batch_paired_labels(estimates: np.ndarray, margin: float, alternative: str) -> dict[str, np.ndarray]:
    """Vectorised t-based version of `paired_summary`'s label for many simulated datasets at once (rows of `estimates`,
    shape (n_datasets, J)): the mean, the 90% and 95% t intervals, whether TOST passes (alpha 0.05) and the
    EFFECT / TRIVIAL_EFFECT / EQUIVALENT / INCONCLUSIVE label read on the same interval as `paired_summary` (the 90%
    interval for one-sided contrasts, 95% otherwise). Sign-flip and bootstrap are not computed, so method agreement and
    leave-k-out are not applied."""

    d = np.asarray(estimates, float)
    n, J = d.shape
    mean = d.mean(axis=1)
    sd = d.std(axis=1, ddof=1)
    se = sd / math.sqrt(J)
    t95, t90 = stats.t.ppf(0.975, J - 1), stats.t.ppf(0.95, J - 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        p_low = 1 - stats.t.cdf((mean + margin) / se, J - 1)
        p_high = stats.t.cdf((mean - margin) / se, J - 1)
    tost = np.where(se == 0, np.where(np.abs(mean) < margin, 0.0, 1.0), np.maximum(p_low, p_high))
    lo95, hi95, lo90, hi90 = mean - t95 * se, mean + t95 * se, mean - t90 * se, mean + t90 * se
    lo, hi = (lo95, hi95) if alternative == "two-sided" else (lo90, hi90)
    excludes = (lo > 0) | (hi < 0)
    beyond = (hi > margin) | (lo < -margin)
    label = np.where(excludes & beyond, "EFFECT", np.where(excludes, "TRIVIAL_EFFECT",
                                                            np.where(tost < ALPHA, "EQUIVALENT", "INCONCLUSIVE")))
    return {"mean": mean, "lo95": lo95, "hi95": hi95, "lo90": lo90, "hi90": hi90, "p_tost": tost,
            "tost_pass": tost < ALPHA, "label": label}


def batch_agreement_labels(est_a: np.ndarray, est_b: np.ndarray, contrast: str, rule: str) -> np.ndarray:
    """AGREE / DISAGREE / UNRESOLVED per simulated dataset for one contrast and one rule, from the per-structure estimates
    under phrasing pair 0 (`est_a`) and pair 1 (`est_b`), each of shape (n_datasets, J). Rule D uses rule B's labels (the
    difference is the same; only what a non-AGREE does to the pooled claim differs, see `agreement_demotes`)."""

    margin = agreement_margin(contrast, rule)
    diff = batch_paired_labels(est_a - est_b, margin, "two-sided")
    effect = diff["label"] == "EFFECT"
    if rule == "A":
        equivalent = diff["label"] == "EQUIVALENT"
        pa, pb = (batch_paired_labels(e, SESOI[contrast], "two-sided") for e in (est_a, est_b))
        same_side = ((pa["lo95"] > SESOI[contrast]) & (pb["lo95"] > SESOI[contrast])) | (
            (pa["hi95"] < -SESOI[contrast]) & (pb["hi95"] < -SESOI[contrast]))
        agree = equivalent | same_side
        return np.where(agree, AGREE, np.where(effect, DISAGREE, UNRESOLVED))
    return np.where(effect, DISAGREE, np.where(diff["tost_pass"], AGREE, UNRESOLVED))


def agreement_demotes(labels: Mapping[str, np.ndarray], rule: str) -> np.ndarray:
    """Whether the rule demotes the pooled claim (WORDING_DEPENDENT): rules A-C when any of F1-F3 is not AGREE, rule D only
    when any is DISAGREE."""

    stacked = np.stack([np.asarray(labels[f]) for f in ("F1", "F2", "F3")])
    return (stacked == DISAGREE).any(axis=0) if rule == "D" else (stacked != AGREE).any(axis=0)


def phrasing_difference_agreement(diffs: Sequence[float | None], margin: float) -> dict[str, Any]:
    """Rule B for one contrast on real structure-level phrasing differences (estimate under phrasing 0 minus phrasing 1):
    the paired two-sided summary with `margin`, read as AGREE (TOST passes), DISAGREE (95% interval excludes zero and
    extends beyond the margin; EFFECT takes precedence, as in `classify`) or UNRESOLVED; NOT_EVALUATED below
    MIN_EVALUABLE_STRUCTURES."""

    s = paired_summary(diffs, margin, "two-sided")
    if s["outcome"] == "NOT_EVALUATED":
        return {**s, "agreement": "NOT_EVALUATED"}
    if s["outcome"] == "EFFECT":
        agreement = DISAGREE
    elif s["p_tost"] < ALPHA:
        agreement = AGREE
    else:
        agreement = UNRESOLVED
    return {**s, "agreement": agreement}


def phrasing_agreement_rules(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell],
                             phrasings: Sequence[int | str] = (0, 1), view: str = PRIMARY_VIEW) -> dict[str, Any]:
    """Rules A-D (`AGREEMENT_RULE_TEXT`) per contrast on real records, for comparison on a dataset. Rule A is
    `phrasing_agreement_rule_a` unchanged; B, C (F3 margin doubled) and D use `phrasing_difference_agreement`. Returns per rule
    the per-contrast label and `demotes` (see `agreement_demotes`)."""

    if len(phrasings) != 2:
        raise ValueError("the agreement rules compare exactly two phrasings")
    base = phrasing_agreement_rule_a(records, cells, phrasings, view)
    per = {p: structure_estimates(records, cells, view, phrasing=p) for p in phrasings}
    a, b = phrasings
    out: dict[str, Any] = {"rules": {}, "phrasings": list(phrasings)}
    diffs = {f: [per[a][s][f] - per[b][s][f] for s in per[a] if s in per[b] and per[a][s][f] is not None
                 and per[b][s][f] is not None] for f in ("F1", "F2", "F3")}
    for rule in AGREEMENT_RULES:
        labels = {}
        for f in ("F1", "F2", "F3"):
            if rule == "A":
                s = base.get(f"phrasing_by_role_{f}", {})
                if s.get("outcome") == "NOT_EVALUATED" and not s.get("same_side_beyond_sesoi"):
                    labels[f] = "NOT_EVALUATED"
                else:
                    labels[f] = AGREE if s.get("agree") else (DISAGREE if s.get("outcome") == "EFFECT" else UNRESOLVED)
            else:
                labels[f] = phrasing_difference_agreement(diffs[f], agreement_margin(f, rule))["agreement"]
        evaluable = all(v != "NOT_EVALUATED" for v in labels.values())
        demotes = None
        if evaluable:
            demotes = (any(v == DISAGREE for v in labels.values()) if rule == "D"
                       else any(v != AGREE for v in labels.values()))
        out["rules"][rule] = {"labels": labels, "demotes": demotes, "text": AGREEMENT_RULE_TEXT[rule]}
    return out


def phrasing_agreement(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell],
                       phrasings: Sequence[int | str] = (0, 1), view: str = PRIMARY_VIEW) -> dict[str, Any]:
    """The operative phrasing-agreement check (RULE B, adopted 2026-11-14, plan_revision_v2.2 section E). Per-phrasing
    F1-F3 and, per contrast, the per-structure difference between the two phrasings' estimates read in three states:
    AGREE when its TOST inside the contrast's SESOI passes (whether or not the interval includes zero) or both
    phrasings' 95% intervals lie beyond the SESOI on the same side (the plan's second clause); DISAGREE when the
    difference's 95% interval excludes zero and extends beyond the SESOI; otherwise UNRESOLVED; NOT_EVALUATED below
    MIN_EVALUABLE_STRUCTURES. Phrasings are indices (`phrasing_indices`) or exact ids. Each `phrasing_by_role_F*` entry
    is the paired summary of the difference plus `agreement` (the state), `agree` (state == AGREE) and
    `same_side_beyond_sesoi`. Rule A is `phrasing_agreement_rule_a`."""

    per = {p: structure_estimates(records, cells, view, phrasing=p) for p in phrasings}
    out: dict[str, Any] = {"rule": "B", "rule_text": AGREEMENT_RULE_TEXT["B"] + "; or both phrasings' 95% intervals beyond "
                           "the SESOI on the same side (second clause)", "phrasings": list(phrasings),
                           "per_phrasing": {str(p): primary_family(e) for p, e in per.items()}}
    if len(phrasings) == 2:
        a, b = phrasings
        states = {}
        for f in ("F1", "F2", "F3"):
            diffs = [per[a][s][f] - per[b][s][f] for s in per[a] if s in per[b]
                     and per[a][s][f] is not None and per[b][s][f] is not None]
            res = phrasing_difference_agreement(diffs, SESOI[f])
            same_side = all(out["per_phrasing"][str(p)][f].get("ci95_t", [0, 0])[0] > SESOI[f] for p in phrasings) or all(
                out["per_phrasing"][str(p)][f].get("ci95_t", [0, 0])[1] < -SESOI[f] for p in phrasings)
            if same_side:
                res["agreement"] = AGREE
            res["same_side_beyond_sesoi"] = same_side
            res["agree"] = res["agreement"] == AGREE
            out[f"phrasing_by_role_{f}"] = res
            states[f] = res["agreement"]
        out["states"] = states
    return out
