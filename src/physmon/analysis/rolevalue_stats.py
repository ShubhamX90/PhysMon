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
PRIMARY_VIEW = "grade_declared"
MULTIMODAL_SHARE = 0.20


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


def cells_from_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Cell]:
    out = {}
    for r in rows:
        role = r.get("role") or {}
        out[r["job_id"]] = Cell(r["job_id"], r["structure_id"], role.get("stratum", r.get("cue_semantic_role") or "none"),
                                role.get("value_index"), role.get("phrasing_id"), float(r["gold_value"]),
                                dict(r.get("foils") or {}), role.get("placebo"), list(role.get("confounded") or []))
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


def structure_estimates(records: Iterable[Mapping[str, Any]], cells: Mapping[str, Cell], view: str = PRIMARY_VIEW,
                        phrasing: str | None = None) -> dict[str, dict[str, Any]]:
    """Per structure: T̄ by stratum, the F1/F2/F3 estimates, and their inputs. `phrasing` restricts R/D cells to one
    phrasing index (0 or 1 by position in the cell's role), for the per-phrasing analyses."""

    by_cell = group_records(records, cells)
    out: dict[str, dict[str, Any]] = {}
    per_s: dict[str, dict[str, Any]] = defaultdict(lambda: {"T": defaultdict(list), "T_by_z": defaultdict(list),
                                                            "neglect": [], "placebo": []})
    for key, recs in by_cell.items():
        cell = cells[key]
        if phrasing is not None and cell.stratum in ("R", "D") and cell.phrasing_id != phrasing:
            continue
        s = per_s[cell.structure_id]
        ts = [tracking(r, view) for r in recs]
        s["T"][cell.stratum].extend(ts)
        if cell.stratum in ("R", "D") and cell.value_index is not None:
            s["T_by_z"][(cell.stratum, cell.value_index)].extend(ts)
        if cell.stratum == "R":
            s["neglect"].extend(int(matches_value(r, cell.foils.get("neglect"))) for r in recs)
            s["placebo"].extend(int(matches_value(r, cell.placebo)) for r in recs)
    for sid, s in per_s.items():
        t = {k: _mean(v) for k, v in s["T"].items()}
        f1 = (t["N"] - t["D"]) if t.get("N") is not None and t.get("D") is not None else None
        f1_nocue = (t["none"] - t["D"]) if t.get("none") is not None and t.get("D") is not None else None
        f2 = (_mean(s["neglect"]) - _mean(s["placebo"])) if s["neglect"] else None
        out[sid] = {"T": t, "F1": f1, "F1_vs_no_cue": f1_nocue, "F2": f2, "F3": f3_estimate(s["T_by_z"]),
                    "neglect_share": _mean(s["neglect"]), "placebo_rate": _mean(s["placebo"]),
                    "n_samples": {k: len(v) for k, v in s["T"].items()}}
    return out


def empirical_logit(successes: int, n: int) -> float:
    return math.log((successes + 0.5) / (n - successes + 0.5))


def _slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    x = np.asarray(xs, float)
    y = np.asarray(ys, float)
    return float(((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum())


def f3_estimate(t_by_z: Mapping[tuple[str, int], Sequence[int]]) -> float | None:
    """R slope minus D slope of the empirical logit of tracking across the value index (needs >= 2 values in each)."""

    slopes = {}
    for role in ("R", "D"):
        zs = sorted(z for (r, z) in t_by_z if r == role and len(t_by_z[(r, z)]))
        if len(zs) < 2:
            return None
        slopes[role] = _slope(zs, [empirical_logit(sum(t_by_z[(role, z)]), len(t_by_z[(role, z)])) for z in zs])
    return slopes["R"] - slopes["D"]


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


def bootstrap_ci(diffs: Sequence[float], level: float = 0.95) -> list[float]:
    d = np.asarray(diffs, float)
    rng = np.random.default_rng(SEED)
    means = np.sort(d[rng.integers(0, len(d), size=(N_BOOT, len(d)))].mean(axis=1))
    lo = (1 - level) / 2
    return [float(np.quantile(means, lo)), float(np.quantile(means, 1 - lo))]


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
    if len(d) < 3:
        return {"J": len(d), "outcome": "NOT_EVALUATED", "reason": "fewer than 3 evaluable structures"}
    arr = np.asarray(d)
    t_stat = arr.mean() / (arr.std(ddof=1) / math.sqrt(len(d))) if arr.std(ddof=1) > 0 else math.inf * np.sign(arr.mean())
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
    return {"J": len(d), "mean": float(arr.mean()), "sd": float(arr.std(ddof=1)), "ci95_t": ci95,
            "ci90_t": ci90, "ci95_bootstrap": bootstrap_ci(d), "p_t": p_t,
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


def primary_family(estimates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """F1 (one-sided, loss > 0), F2 (one-sided, excess > 0), F3 (two-sided), Holm-corrected on the sign-flip p values."""

    res = {"F1": paired_summary([e["F1"] for e in estimates.values()], SESOI["F1"], "greater"),
           "F2": paired_summary([e["F2"] for e in estimates.values()], SESOI["F2"], "greater"),
           "F3": paired_summary([e["F3"] for e in estimates.values()], SESOI["F3"], "two-sided")}
    evaluable = {k: v["p_sign_flip"] for k, v in res.items() if "p_sign_flip" in v}
    res["holm"] = holm(evaluable) if evaluable else {}
    return res


def phrasing_agreement(records: Sequence[Mapping[str, Any]], cells: Mapping[str, Cell], phrasings: Sequence[str],
                       view: str = PRIMARY_VIEW) -> dict[str, Any]:
    """Per-phrasing F1-F3 and the phrasing-by-role check: the per-structure difference between two phrasings' estimates
    must be equivalent to zero within the SESOI (TOST), or both phrasings' estimates exceed the SESOI in one direction."""

    per = {p: structure_estimates(records, cells, view, phrasing=p) for p in phrasings}
    out: dict[str, Any] = {"per_phrasing": {p: primary_family(e) for p, e in per.items()}}
    if len(phrasings) == 2:
        a, b = phrasings
        for f in ("F1", "F2", "F3"):
            diffs = [per[a][s][f] - per[b][s][f] for s in per[a] if s in per[b]
                     and per[a][s][f] is not None and per[b][s][f] is not None]
            summary = paired_summary(diffs, SESOI[f], "two-sided")
            same_side = all(out["per_phrasing"][p][f].get("ci95_t", [0, 0])[0] > SESOI[f] for p in phrasings) or all(
                out["per_phrasing"][p][f].get("ci95_t", [0, 0])[1] < -SESOI[f] for p in phrasings)
            summary["agree"] = summary.get("outcome") == "EQUIVALENT" or same_side
            out[f"phrasing_by_role_{f}"] = summary
    return out


# --- rare shares ----------------------------------------------------------------------------------------------------------

def jeffreys(successes: int, n: int, level: float = 0.95) -> dict[str, float]:
    a, b = successes + 0.5, n - successes + 0.5
    return {"rate": a / (a + b), "lo": float(stats.beta.ppf((1 - level) / 2, a, b)),
            "hi": float(stats.beta.ppf(1 - (1 - level) / 2, a, b)), "x": successes, "n": n}


def beta_binomial_fit(counts: Sequence[tuple[int, int]]) -> dict[str, Any]:
    """Maximum-likelihood Beta-Binomial over structures (x successes of n each): mean mu and overdispersion rho, with a
    bootstrap-over-structures interval for mu. Zero totals give a finite estimate, never a reported zero."""

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
    rng = np.random.default_rng(SEED)
    boots = sorted(fit([data[i] for i in rng.integers(0, len(data), len(data))])[0] for _ in range(200))
    return {"mu": mu, "rho": rho, "ci95_bootstrap": [boots[4], boots[194]], "J": len(data),
            "x_total": sum(c[0] for c in data), "n_total": sum(c[1] for c in data)}


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
