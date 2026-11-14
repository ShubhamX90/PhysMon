"""G3 hypothesis scorecard as code (G1 element "the scorecard criteria of G3 with numeric thresholds").

Implements `docs/registry/v2/g1/g3_scorecard_thresholds.md` as amended by `docs/registry/v2/g1/decisions_2026-11-13.md`
(the decisions file governs where they conflict). Plan of record: `sec:hypotheses`, `sec:gates` (G3 item 3),
`sec:statistics`, `sec:rolevalue`.

Statuses: SUPPORTED, CONTRADICTED, INCONCLUSIVE, NOT_EVALUATED. Several hypotheses may be SUPPORTED at once; rows are
not read by first match. G3 is estimation, not a test: no Holm correction is read here.

Rules common to every row (scorecard section 1, decisions):
* Contrast labels come from `rolevalue_stats.paired_summary` (decision 2: one-sided bound for F1/F2), with no status
  below 6 evaluable structures (decision 4).
* An EFFECT or TRIVIAL_EFFECT counts only if t, sign-flip and bootstrap agree (else INCONCLUSIVE flagged
  METHOD_DISAGREEMENT) and it survives deleting the 1-3 most extreme structures (else INCONCLUSIVE flagged NOT_ROBUST);
  the mixed model is reported beside, never the decision; FRAGILE (any leave-k-out label change) is a flag
  (`rolevalue_stats.effective_label`, decision 5).
* An EFFECT counts for a hypothesis only in the direction it predicts (F1 > 0 loss, F2 > 0 excess neglect, misuse
  excess > 0); H0 is contradicted by a reliable departure in any direction.
* TRIVIAL_EFFECT supports H6-RD (reported as a trivial departure within the SESOI); only EQUIVALENT supports H0
  (decision 1).
* Role statuses (H3, H3-R, H6) need phrasing agreement on F1-F3; otherwise INCONCLUSIVE flagged WORDING_DEPENDENT with
  per-phrasing statuses beside (decision 6).
* R tracking (decision 8): T_R >= 0.40 (point estimate) on >= 16 evaluable structures (each with R cells at 3 values);
  below it H3, H3-R and H6 are NOT_EVALUATED ("uninterpretable for role", itself a finding); H0, H1, H2, H4, H5 are
  still scored.
* Misuse attribution (decision 13): `rolevalue_stats.misuse_attribution`.
* Missingness: statuses come from the all-attempted analysis; when sensitivity inputs (complete-case,
  budget-exhausted-as-wrong) are given and change a status, the status is kept and flagged MISSINGNESS_SENSITIVE.
* Anything whose estimand cannot be computed yet is NOT_EVALUATED with the reason (H4 until the frozen trace
  extractor of decision 12 exists; H2 until the unit/plausibility ablation runs; C/K rows until those strata run).

Added to the plan's table: H3-R (decision 25), selection failure by over-ignoring relevant quantities, scored by F2.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from physmon.analysis import rolevalue_stats as rvs

SCHEMA = "physmon.g3_scorecard.v1"
STATUSES = ("SUPPORTED", "CONTRADICTED", "INCONCLUSIVE", "NOT_EVALUATED")
SUPPORTED, CONTRADICTED, INCONCLUSIVE, NOT_EVALUATED = STATUSES
R_TRACKING_CRITERION = 0.40  # decision 8 (departs from the draft 0.50)
R_TRACKING_MIN_STRUCTURES = 16  # decision 8 / r_tracking_criterion.md: 20 x 0.8
R_TRACKING_MIN_VALUES = 3
TRACE_CORRECT_THRESHOLD = 0.50  # decision 12
HYPOTHESES = ("H0", "H1", "H2", "H3-D", "H3-C", "H3-K", "H3-R", "H4", "H5", "H6-RD", "H6-extended")
SOURCES = ("docs/registry/v2/g1/g3_scorecard_thresholds.md", "docs/registry/v2/g1/decisions_2026-11-13.md")


@dataclass
class ScorecardInputs:
    """Outputs of `rolevalue_stats` for one population of one model configuration."""

    estimates: Mapping[str, Mapping[str, Any]]  # structure_estimates
    family: Mapping[str, Any]  # primary_family(..., diagnostics=True)
    phrasing: Mapping[str, Any] | None = None  # phrasing_agreement
    misuse: Mapping[str, Mapping[str, Any]] | None = None  # {"D": misuse_attribution(...), "C": ..., "K": ...}
    copy_r: Mapping[str, Any] | None = None  # copy_excess_r
    cost: Mapping[str, Any] | None = None  # cost_contrasts
    ck: Mapping[str, Any] | None = None  # ck_family
    h2_ablation: Mapping[str, Any] | None = None  # {"F1_same_unit", "F1_incompatible_unit", "F1_implausible"}: summaries
    trace: Mapping[str, Any] | None = None  # {"extractor_frozen", "reasoning_trace", "x", "n", "relevance_delta"}
    lambdas: Mapping[str, Any] | None = None  # {structure_id: lambdas(...)}, descriptive
    population: str = "calibrated_in_band_complete"
    configuration: str | None = None
    notes: list[str] = field(default_factory=list)


def build_inputs(records: Sequence[Mapping[str, Any]], cells: Mapping[str, rvs.Cell], *, view: str = rvs.PRIMARY_VIEW,
                 phrasings: Sequence[int | str] = (0, 1), hierarchical: bool = True,
                 population: str = "calibrated_in_band_complete", configuration: str | None = None,
                 h2_ablation: Mapping[str, Any] | None = None, trace: Mapping[str, Any] | None = None,
                 with_lambdas: bool = True) -> ScorecardInputs:
    """Run every `rolevalue_stats` analysis the scorecard reads on one record set."""

    est = rvs.structure_estimates(records, cells, view)
    hier = rvs.hierarchical_view(records, cells, view) if hierarchical else None
    strata = {c.stratum for c in cells.values()}
    return ScorecardInputs(
        estimates=est, family=rvs.primary_family(est, diagnostics=True, hierarchical=hier),
        phrasing=rvs.phrasing_agreement(records, cells, phrasings, view),
        misuse={st: rvs.misuse_attribution(records, cells, st) for st in ("D", "C", "K") if st in strata},
        copy_r=rvs.copy_excess_r(records, cells), cost=rvs.cost_contrasts(records, cells), ck=rvs.ck_family(est),
        h2_ablation=h2_ablation, trace=trace,
        lambdas={sid: rvs.lambdas(records, cells, sid) for sid in est} if with_lambdas else None,
        population=population, configuration=configuration)


# --- helpers -------------------------------------------------------------------------------------------------------------

def _eff(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    if summary is None:
        return {"label": NOT_EVALUATED, "raw": NOT_EVALUATED, "sign": 0, "flags": [], "missing": True}
    return rvs.effective_label(summary)


def _numbers(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    if summary is None:
        return {"outcome": NOT_EVALUATED, "reason": "not computed"}
    keys = ("J", "mean", "sd", "ci90_t", "ci95_t", "ci95_bootstrap", "ci90_bootstrap", "p_t", "p_sign_flip", "p_tost",
            "sesoi", "alternative", "outcome", "classification_interval", "reason")
    out = {k: summary[k] for k in keys if k in summary}
    eff = rvs.effective_label(summary)
    out["effective_label"], out["flags"] = eff["label"], eff["flags"]
    if "method_agreement" in summary:
        ma = summary["method_agreement"]
        out["decision_methods_agree"] = ma.get("decision_methods_agree")
        out["hierarchical_agrees_in_sign"] = ma.get("hierarchical_agrees_in_sign")
        out["hierarchical_agrees_in_excluding_zero"] = ma.get("hierarchical_agrees_in_excluding_zero")
    if "robustness" in summary and summary["robustness"].get("assessable"):
        rb = summary["robustness"]
        out["robustness"] = {"fragile": rb["fragile"], "not_robust": rb["not_robust"],
                             "share_label_unchanged": {k: v.get("share_label_unchanged") for k, v in rb["by_k"].items()},
                             "share_sign_unchanged": {k: v.get("share_sign_unchanged") for k, v in rb["by_k"].items()}}
    if "hierarchical" in summary:
        h = summary["hierarchical"]
        out["hierarchical"] = {k: h.get(k) for k in ("status", "method", "estimate", "interval", "reason")}
    return out


def _is(e: Mapping[str, Any], label: str, sign: int | None = None) -> bool:
    return e["label"] == label and (sign is None or e["sign"] == sign)


def _result(status: str, rule: str, reason: str, numbers: Mapping[str, Any] | None = None,
            flags: Sequence[str] = ()) -> dict[str, Any]:
    assert status in STATUSES
    return {"status": status, "rule": rule, "reason": reason, "numbers": dict(numbers or {}), "flags": sorted(set(flags))}


def _flags_of(*effs: Mapping[str, Any]) -> list[str]:
    return sorted({f for e in effs for f in e.get("flags", [])})


def r_tracking_check(estimates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Decision 8: T_R = unweighted mean over evaluable structures (R cells at >= 3 values) of the structure-level R
    tracking share; MEETS if T_R >= 0.40 on >= 16 structures, BELOW if T_R < 0.40, NOT_EVALUATED below 16 structures.
    The bootstrap interval is reported beside, never used for the decision."""

    shares = [e["T"]["R"] for e in estimates.values() if e.get("T", {}).get("R") is not None
              and e.get("n_values", {}).get("R", R_TRACKING_MIN_VALUES) >= R_TRACKING_MIN_VALUES]
    out: dict[str, Any] = {"criterion": R_TRACKING_CRITERION, "min_structures": R_TRACKING_MIN_STRUCTURES,
                           "J": len(shares), "rule": "decision 8: T_R >= 0.40 (point estimate) on >= 16 evaluable "
                                                     "structures, absolute"}
    if len(shares) < R_TRACKING_MIN_STRUCTURES:
        out.update(status=NOT_EVALUATED, T_R=float(np.mean(shares)) if shares else None,
                   reason=f"{len(shares)} evaluable structures (< {R_TRACKING_MIN_STRUCTURES})")
        return out
    t_r = float(np.mean(shares))
    out.update(T_R=t_r, ci95_bootstrap=rvs.bootstrap_ci(shares), status="MEETS" if t_r >= R_TRACKING_CRITERION else "BELOW")
    return out


def _r_gate(rt: Mapping[str, Any], rule: str) -> dict[str, Any] | None:
    if rt["status"] == NOT_EVALUATED:
        return _result(NOT_EVALUATED, rule, f"R-tracking criterion not evaluable: {rt['reason']}", {"r_tracking": rt})
    if rt["status"] == "BELOW":
        return _result(NOT_EVALUATED, rule, f"uninterpretable for role: R tracking {rt['T_R']:.3f} below the criterion "
                       f"{R_TRACKING_CRITERION} (reported as a finding; scorecard 1.8)", {"r_tracking": rt},
                       ["R_TRACKING_BELOW_CRITERION"])
    return None


def _misuse(inputs: ScorecardInputs, stratum: str) -> Mapping[str, Any] | None:
    return (inputs.misuse or {}).get(stratum) if inputs.misuse is not None else None


# --- per-hypothesis rules ----------------------------------------------------------------------------------------------

def _h0(inputs: ScorecardInputs, rt: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H0: SUPPORTED iff F1, F2, F3 each EQUIVALENT and every evaluated misuse excess M_h EQUIVALENT (decision 1: "
            "TRIVIAL_EFFECT does not count); CONTRADICTED by any EFFECT of F1-F3 or an M_h in any direction; "
            "NOT_EVALUATED if F1 or F2 is")
    f = {k: _eff(inputs.family.get(k)) for k in ("F1", "F2", "F3")}
    nums: dict[str, Any] = {k: _numbers(inputs.family.get(k)) for k in f}
    if f["F1"]["label"] == NOT_EVALUATED or f["F2"]["label"] == NOT_EVALUATED:
        return _result(NOT_EVALUATED, rule, "F1 or F2 NOT_EVALUATED", nums)
    misuse = _misuse(inputs, "D")
    m = {h: _eff(v["M"]) for h, v in (misuse or {}).items()}
    m_eval = {h: e for h, e in m.items() if e["label"] != NOT_EVALUATED}
    nums["misuse_effective_labels"] = {h: e["label"] for h, e in m.items()}
    flags = _flags_of(*f.values(), *m_eval.values())
    effects = [k for k, e in {**f, **{f"M_{h}": e for h, e in m_eval.items()}}.items() if e["label"] == "EFFECT"]
    if effects:
        return _result(CONTRADICTED, rule, f"reliable departure(s): {', '.join(effects)} EFFECT", nums, flags)
    if f["F3"]["label"] == NOT_EVALUATED:
        return _result(INCONCLUSIVE, rule, "F3 NOT_EVALUATED: H0 needs F1-F3 all EQUIVALENT", nums, flags)
    if misuse is None or not m_eval:
        return _result(INCONCLUSIVE, rule, "no misuse excess evaluable: 'no misuse share above its N rate' unverified",
                       nums, flags)
    if all(e["label"] == "EQUIVALENT" for e in [*f.values(), *m_eval.values()]):
        not_eval = sorted(set(m) - set(m_eval))
        reason = "F1, F2, F3 and every evaluated M_h EQUIVALENT"
        return _result(SUPPORTED, rule, reason + (f"; not evaluable: {', '.join(not_eval)}" if not_eval else ""), nums,
                       flags)
    trivial = [k for k, e in {**f, **m_eval}.items() if e["label"] == "TRIVIAL_EFFECT"]
    reason = f"labels F1-F3 {[f[k]['label'] for k in f]}"
    if trivial:
        reason += f"; TRIVIAL_EFFECT ({', '.join(trivial)}) does not support H0 (decision 1)"
    return _result(INCONCLUSIVE, rule, reason, nums, flags)


def _h1(inputs: ScorecardInputs, rt: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H1: per copy class evaluable in >= 6 structures (`copy` where q has the target's dimension, `digit_copy` "
            "otherwise, decision 26): SUPPORTED iff every evaluable class is ATTRIBUTED in D and its R copy excess CR is "
            "EFFECT or TRIVIAL_EFFECT positive; CONTRADICTED iff any evaluable class has M EQUIVALENT in D (copy absent "
            "in that unit, or confined to the other); NOT_EVALUATED iff no class is evaluable")
    misuse = _misuse(inputs, "D") or {}
    classes = {h: misuse[h] for h in rvs.COPY_CLASSES if h in misuse}
    evaluable = {h: v for h, v in classes.items() if v["attribution"] != NOT_EVALUATED}
    nums: dict[str, Any] = {h: {"attribution": v["attribution"], "attribution_reason": v["reason"], "M": _numbers(v["M"]),
                                "CR": _numbers((inputs.copy_r or {}).get(h, {}).get("CR"))} for h, v in classes.items()}
    if not evaluable:
        return _result(NOT_EVALUATED, rule, "the copy foil is defined (unconfounded) in fewer than 6 evaluable "
                       "structures in every unit class", nums)
    flags = _flags_of(*[_eff(v["M"]) for v in evaluable.values()])
    equivalent = [h for h, v in evaluable.items() if _is(_eff(v["M"]), "EQUIVALENT")]
    if equivalent:
        reason = f"M_{'/'.join(equivalent)} EQUIVALENT in D"
        if "digit_copy" in equivalent and classes.get("copy", {}).get("attribution") == "ATTRIBUTED":
            reason += "; copy confined to same-dimension cells: counts for H2 (P4.7)"
            flags.append("COPY_CONFINED_TO_SAME_UNIT")
        return _result(CONTRADICTED, rule, reason, nums, flags)
    ok = {}
    for h, v in evaluable.items():
        cr = _eff((inputs.copy_r or {}).get(h, {}).get("CR"))
        ok[h] = v["attribution"] == "ATTRIBUTED" and cr["label"] in ("EFFECT", "TRIVIAL_EFFECT") and cr["sign"] > 0
        flags += cr["flags"]
    if all(ok.values()):
        missing = [h for h in rvs.COPY_CLASSES if h not in evaluable]
        if missing:
            flags.append("UNIT_PART_NOT_EVALUATED")
        return _result(SUPPORTED, rule, f"copy attributed in D and above N in R for {', '.join(sorted(ok))}"
                       + (f"; {', '.join(missing)} not evaluable" if missing else ""), nums, flags)
    return _result(INCONCLUSIVE, rule, f"copy evidence per class: {ok}", nums, flags)


def _h2(inputs: ScorecardInputs, rt: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H2: needs the unit/plausibility ablation; SUPPORTED iff F1_same_unit EFFECT (positive) and "
            "F1_incompatible_unit EQUIVALENT (and F1_implausible EQUIVALENT where run); CONTRADICTED iff "
            "F1_incompatible_unit or F1_implausible EFFECT (positive)")
    ab = inputs.h2_ablation
    if ab is None:
        return _result(NOT_EVALUATED, rule, "unit/plausibility ablation not run (expected unless the core shows a D loss)")
    s, u = _eff(ab.get("F1_same_unit")), _eff(ab.get("F1_incompatible_unit"))
    imp = _eff(ab["F1_implausible"]) if ab.get("F1_implausible") is not None else None
    nums = {k: _numbers(ab.get(k)) for k in ("F1_same_unit", "F1_incompatible_unit", "F1_implausible") if ab.get(k)}
    flags = _flags_of(s, u, *([imp] if imp else []))
    if s["label"] == NOT_EVALUATED or u["label"] == NOT_EVALUATED:
        return _result(NOT_EVALUATED, rule, "F1_same_unit or F1_incompatible_unit NOT_EVALUATED", nums, flags)
    if _is(u, "EFFECT", 1) or (imp is not None and _is(imp, "EFFECT", 1)):
        return _result(CONTRADICTED, rule, "departures with incompatible units or implausible values", nums, flags)
    if _is(s, "EFFECT", 1) and _is(u, "EQUIVALENT") and (imp is None or _is(imp, "EQUIVALENT")):
        return _result(SUPPORTED, rule, "loss only with same-unit values", nums, flags)
    return _result(INCONCLUSIVE, rule, f"same {s['label']}, incompatible {u['label']}"
                   + (f", implausible {imp['label']}" if imp else ""), nums, flags)


def _h3(inputs: ScorecardInputs, rt: Mapping[str, Any], stratum: str) -> dict[str, Any]:
    routes = rvs.ROUTE_CLASSES[stratum]
    rule = (f"H3 ({stratum}): SUPPORTED iff F1_{stratum} EFFECT (positive) and at least one of {', '.join(routes)} "
            f"ATTRIBUTED in {stratum} (copy alone counts for H1); CONTRADICTED iff F1_{stratum} EQUIVALENT, F2 not "
            "EFFECT and T_R meets the criterion; NOT_EVALUATED if R tracking is below or not evaluable, or the stratum "
            "was not run")
    gate = _r_gate(rt, rule)
    if gate:
        return gate
    if stratum == "D":
        f1_summary = inputs.family.get("F1")
    else:
        ck = (inputs.ck or {}).get(stratum)
        if not ck or not ck.get("run"):
            return _result(NOT_EVALUATED, rule, f"stratum {stratum} not run (targeted ablation)")
        f1_summary = ck["F1"]
    f1, f2 = _eff(f1_summary), _eff(inputs.family.get("F2"))
    misuse = _misuse(inputs, stratum) or {}
    attributed = [h for h in routes if misuse.get(h, {}).get("attribution") == "ATTRIBUTED"]
    nums = {f"F1_{stratum}" if stratum != "D" else "F1": _numbers(f1_summary), "F2": _numbers(inputs.family.get("F2")),
            "attribution": {h: {"status": v["attribution"], "reason": v["reason"]} for h, v in misuse.items()},
            "r_tracking": rt}
    flags = _flags_of(f1, f2)
    if f1["label"] == NOT_EVALUATED:
        return _result(NOT_EVALUATED, rule, f"F1 ({stratum}) NOT_EVALUATED", nums, flags)
    if _is(f1, "EFFECT", 1) and attributed:
        return _result(SUPPORTED, rule, f"loss attributed to {', '.join(attributed)}", nums, flags)
    if _is(f1, "EQUIVALENT") and f2["label"] not in ("EFFECT", NOT_EVALUATED):
        return _result(CONTRADICTED, rule, f"invariance in {stratum} while R responds (T_R {rt['T_R']:.3f})", nums, flags)
    if _is(f1, "EFFECT", 1):
        copy_only = [h for h in rvs.COPY_CLASSES if misuse.get(h, {}).get("attribution") == "ATTRIBUTED"]
        reason = "F1 EFFECT without an attributed route: a loss of unknown route (counts against H0, not for H3)"
        if copy_only:
            reason += f"; only {', '.join(copy_only)} attributed (counts for H1)"
        return _result(INCONCLUSIVE, rule, reason, nums, flags)
    return _result(INCONCLUSIVE, rule, f"F1 {f1['label']}, F2 {f2['label']}", nums, flags)


def _h3r(inputs: ScorecardInputs, rt: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H3-R (decision 25, an addition to the plan's table): SUPPORTED iff F2 EFFECT (positive); CONTRADICTED iff F2 "
            "EQUIVALENT; NOT_EVALUATED if R tracking is below or not evaluable, or F2 is NOT_EVALUATED")
    gate = _r_gate(rt, rule)
    if gate:
        return gate
    f2 = _eff(inputs.family.get("F2"))
    nums = {"F2": _numbers(inputs.family.get("F2")), "r_tracking": rt}
    if f2["label"] == NOT_EVALUATED:
        return _result(NOT_EVALUATED, rule, "F2 NOT_EVALUATED", nums)
    if _is(f2, "EFFECT", 1):
        return _result(SUPPORTED, rule, "R neglect share above the placebo rate beyond the SESOI", nums, f2["flags"])
    if _is(f2, "EQUIVALENT"):
        return _result(CONTRADICTED, rule, "R neglect share equivalent to the placebo rate", nums, f2["flags"])
    return _result(INCONCLUSIVE, rule, f"F2 {f2['label']}", nums, f2["flags"])


def _h4(inputs: ScorecardInputs, rt: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H4: SUPPORTED iff F1 EFFECT (positive), some curve attributed, trace-correct share TC Jeffreys 95% lower "
            "bound > 0.50 and (if run) the relevance-instruction change in F1 EQUIVALENT; CONTRADICTED iff TC upper "
            "bound < 0.50; NOT_EVALUATED without a frozen rule-based trace extractor (decision 12), a reasoning trace, "
            "or an attributed curve")
    tr = inputs.trace
    if tr is None or not tr.get("extractor_frozen"):
        return _result(NOT_EVALUATED, rule, "no frozen rule-based trace extractor tested on synthetic traces "
                       "(decision 12): the trace-correct share TC cannot be computed")
    if not tr.get("reasoning_trace", True):
        return _result(NOT_EVALUATED, rule, "no reasoning trace (non-reasoning output)")
    misuse = _misuse(inputs, "D") or {}
    attributed = [h for h, v in misuse.items() if v["attribution"] == "ATTRIBUTED"]
    if not attributed:
        return _result(NOT_EVALUATED, rule, "no attributed misuse curve")
    tc = rvs.jeffreys(int(tr["x"]), int(tr["n"]))
    f1 = _eff(inputs.family.get("F1"))
    delta = _eff(tr["relevance_delta"]) if tr.get("relevance_delta") is not None else None
    nums = {"TC": tc, "F1": _numbers(inputs.family.get("F1")), "attributed": attributed,
            "relevance_delta": _numbers(tr.get("relevance_delta")) if delta else None}
    if tc["hi"] < TRACE_CORRECT_THRESHOLD:
        return _result(CONTRADICTED, rule, "misuse values already computed in the trace", nums, f1["flags"])
    if _is(f1, "EFFECT", 1) and tc["lo"] > TRACE_CORRECT_THRESHOLD and (delta is None or _is(delta, "EQUIVALENT")):
        return _result(SUPPORTED, rule, "correct value in the trace, final answer moved", nums, f1["flags"])
    return _result(INCONCLUSIVE, rule, f"TC interval [{tc['lo']:.3f}, {tc['hi']:.3f}], F1 {f1['label']}", nums,
                   f1["flags"])


def _h5(inputs: ScorecardInputs, rt: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H5 (comparator N, decision 11; SESOIs log(1.2) and 0.05, decision 10): SUPPORTED iff (L5 or B5 EFFECT "
            "positive) and F1, F2 EQUIVALENT; CONTRADICTED iff L5 and B5 both EQUIVALENT, or F1 or F2 EFFECT (positive)")
    cost = inputs.cost
    if cost is None:
        return _result(NOT_EVALUATED, rule, "O5 contrasts not computed")
    l5, b5 = _eff(cost.get("L5")), _eff(cost.get("B5"))
    f1, f2 = _eff(inputs.family.get("F1")), _eff(inputs.family.get("F2"))
    nums = {"L5": _numbers(cost.get("L5")), "B5": _numbers(cost.get("B5")), "L5_vs_no_cue": _numbers(cost.get("L5_vs_no_cue")),
            "B5_vs_no_cue": _numbers(cost.get("B5_vs_no_cue")), "F1": _numbers(inputs.family.get("F1")),
            "F2": _numbers(inputs.family.get("F2"))}
    flags = _flags_of(l5, b5, f1, f2)
    if l5["label"] == NOT_EVALUATED and b5["label"] == NOT_EVALUATED:
        return _result(NOT_EVALUATED, rule, "L5 and B5 NOT_EVALUATED", nums, flags)
    if f1["label"] == NOT_EVALUATED or f2["label"] == NOT_EVALUATED:
        return _result(NOT_EVALUATED, rule, "F1 or F2 NOT_EVALUATED", nums, flags)
    if _is(f1, "EFFECT", 1) or _is(f2, "EFFECT", 1):
        return _result(CONTRADICTED, rule, "departures in O1/O4: H5 as 'cost only' fails (a cost rise may still be "
                       "reported)", nums, flags)
    if _is(l5, "EQUIVALENT") and _is(b5, "EQUIVALENT"):
        return _result(CONTRADICTED, rule, "no cost rise: L5 and B5 EQUIVALENT", nums, flags)
    if (_is(l5, "EFFECT", 1) or _is(b5, "EFFECT", 1)) and _is(f1, "EQUIVALENT") and _is(f2, "EQUIVALENT"):
        return _result(SUPPORTED, rule, "cost rises while tracking and responsiveness are unchanged", nums, flags)
    return _result(INCONCLUSIVE, rule, f"L5 {l5['label']}, B5 {b5['label']}, F1 {f1['label']}, F2 {f2['label']}", nums,
                   flags)


def _within(e: Mapping[str, Any]) -> bool:
    return e["raw"] in ("EQUIVALENT", "TRIVIAL_EFFECT")


def _h6rd(inputs: ScorecardInputs, rt: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H6-RD: SUPPORTED iff F1, F2, F3 each EQUIVALENT or TRIVIAL_EFFECT (decision 1: a trivial departure within "
            "the SESOI), T_R meets the criterion, and phrasings agree on F1-F3; CONTRADICTED iff F1 or F2 EFFECT "
            "(positive) or F3 EFFECT; NOT_EVALUATED if R tracking is below or not evaluable, or any of F1-F3 is")
    gate = _r_gate(rt, rule)
    if gate:
        return gate
    f = {k: _eff(inputs.family.get(k)) for k in ("F1", "F2", "F3")}
    nums: dict[str, Any] = {k: _numbers(inputs.family.get(k)) for k in f}
    nums["r_tracking"] = rt
    flags = _flags_of(*f.values())
    if any(e["label"] == NOT_EVALUATED for e in f.values()):
        return _result(NOT_EVALUATED, rule, "one of F1-F3 NOT_EVALUATED", nums, flags)
    if _is(f["F1"], "EFFECT", 1) or _is(f["F2"], "EFFECT", 1) or _is(f["F3"], "EFFECT"):
        return _result(CONTRADICTED, rule, "departure: " + ", ".join(k for k, e in f.items() if e["label"] == "EFFECT"),
                       nums, flags)
    if all(_within(e) for e in f.values()):
        trivial = [k for k, e in f.items() if e["raw"] == "TRIVIAL_EFFECT"]
        if trivial:
            flags.append("TRIVIAL_DEPARTURE_WITHIN_SESOI")
        return _result(SUPPORTED, rule, "F1-F3 within their SESOIs" + (
            f" (trivial departure within SESOI: {', '.join(trivial)})" if trivial else ""), nums, flags)
    return _result(INCONCLUSIVE, rule, f"labels {[e['label'] for e in f.values()]} (an underpowered null is "
                   "INCONCLUSIVE)", nums, flags)


def _h6ext(inputs: ScorecardInputs, rt: Mapping[str, Any], h6rd: Mapping[str, Any]) -> dict[str, Any]:
    rule = ("H6-extended: SUPPORTED iff H6-RD SUPPORTED and, for C and K, F1 and the stratum's own value slope each "
            "EQUIVALENT or TRIVIAL_EFFECT; CONTRADICTED iff H6-RD CONTRADICTED or a C/K F1 EFFECT (positive) or slope "
            "EFFECT; NOT_EVALUATED if R tracking is below or not evaluable, or C or K was not run")
    gate = _r_gate(rt, rule)
    if gate:
        return gate
    ck = inputs.ck or {}
    if not all(ck.get(st, {}).get("run") for st in ("C", "K")):
        return _result(NOT_EVALUATED, rule, "C or K stratum not run (targeted ablations)")
    e = {f"{k}_{st}": _eff(ck[st][k]) for st in ("C", "K") for k in ("F1", "slope")}
    nums = {k: _numbers(ck[k.split("_")[1]][k.split("_")[0]]) for k in e}
    flags = _flags_of(*e.values())
    if any(v["label"] == NOT_EVALUATED for v in e.values()):
        return _result(NOT_EVALUATED, rule, "a C/K contrast is NOT_EVALUATED", nums, flags)
    if h6rd["status"] == CONTRADICTED or _is(e["F1_C"], "EFFECT", 1) or _is(e["F1_K"], "EFFECT", 1) or _is(
            e["slope_C"], "EFFECT") or _is(e["slope_K"], "EFFECT"):
        return _result(CONTRADICTED, rule, "departure in R/D or C/K", nums, flags)
    if h6rd["status"] == SUPPORTED and all(_within(v) for v in e.values()):
        return _result(SUPPORTED, rule, "H6-RD supported and C/K invariant within SESOI", nums, flags)
    return _result(INCONCLUSIVE, rule, f"H6-RD {h6rd['status']}; C/K {[v['label'] for v in e.values()]}", nums, flags)


# --- phrasing agreement (decision 6) -------------------------------------------------------------------------------------

def _phrasing_state(inputs: ScorecardInputs) -> dict[str, Any]:
    ph = inputs.phrasing
    if ph is None:
        return {"assessable": False, "reason": "phrasing agreement not computed"}
    per = {}
    for f in ("F1", "F2", "F3"):
        s = ph.get(f"phrasing_by_role_{f}")
        if s is None:
            return {"assessable": False, "reason": f"phrasing-by-role {f} not computed"}
        if s.get("outcome") == NOT_EVALUATED and not s.get("same_side_beyond_sesoi"):
            return {"assessable": False, "reason": f"phrasing-by-role {f} NOT_EVALUATED ({s.get('reason')})"}
        per[f] = {"agree": bool(s.get("agree")), "outcome": s.get("outcome"), "mean": s.get("mean"),
                  "ci95_t": s.get("ci95_t")}
    return {"assessable": True, "per_contrast": per, "agree": all(v["agree"] for v in per.values())}


def _with_phrasing(inputs: ScorecardInputs, rt: Mapping[str, Any], result: dict[str, Any],
                   rule_fn: Callable[[ScorecardInputs, Mapping[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    """Decision 6: a role status needs agreement across phrasings on F1-F3; otherwise INCONCLUSIVE flagged
    WORDING_DEPENDENT, with per-phrasing statuses beside (computed with that phrasing's F1-F3 and the pooled misuse
    attribution)."""

    if result["status"] == NOT_EVALUATED:
        return result
    state = _phrasing_state(inputs)
    result["phrasing_agreement"] = state
    if inputs.phrasing is not None:
        result["per_phrasing"] = {p: rule_fn(replace(inputs, family=fam, phrasing=None), rt)["status"]
                                  for p, fam in inputs.phrasing.get("per_phrasing", {}).items()}
    if not state["assessable"]:
        if result["status"] in (SUPPORTED, CONTRADICTED):
            result["reason"] = f"pooled {result['status']} not confirmed across phrasings ({state['reason']}); " + result[
                "reason"]
            result["pooled_status_before_phrasing_rule"] = result["status"]
            result["status"] = INCONCLUSIVE
        result["flags"] = sorted(set(result["flags"]) | {"PHRASING_AGREEMENT_NOT_EVALUATED"})
    elif not state["agree"]:
        if result["status"] in (SUPPORTED, CONTRADICTED):
            result["pooled_status_before_phrasing_rule"] = result["status"]
            result["reason"] = f"phrasings disagree (pooled would be {result['status']}); " + result["reason"]
            result["status"] = INCONCLUSIVE
        result["flags"] = sorted(set(result["flags"]) | {"WORDING_DEPENDENT"})
    return result


# --- assembly ------------------------------------------------------------------------------------------------------------

def _statuses(inputs: ScorecardInputs) -> tuple[dict[str, Any], dict[str, Any]]:
    rt = r_tracking_check(inputs.estimates)
    out: dict[str, Any] = {"H0": _h0(inputs, rt), "H1": _h1(inputs, rt), "H2": _h2(inputs, rt)}
    out["H3-D"] = _with_phrasing(inputs, rt, _h3(inputs, rt, "D"), lambda i, r: _h3(i, r, "D"))
    out["H3-C"] = _h3(inputs, rt, "C")
    out["H3-K"] = _h3(inputs, rt, "K")
    out["H3-R"] = _with_phrasing(inputs, rt, _h3r(inputs, rt), _h3r)
    out["H4"] = _h4(inputs, rt)
    out["H5"] = _h5(inputs, rt)
    out["H6-RD"] = _with_phrasing(inputs, rt, _h6rd(inputs, rt), _h6rd)
    out["H6-extended"] = _h6ext(inputs, rt, out["H6-RD"])
    return out, rt


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(v) for v in (sorted(obj) if isinstance(obj, set) else obj)]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj) if math.isfinite(float(obj)) else None
    if isinstance(obj, np.ndarray):
        return _jsonable(obj.tolist())
    return obj


def scorecard(inputs: ScorecardInputs, sensitivity: Mapping[str, ScorecardInputs] | None = None,
              control: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The G3 scorecard: every status, the numbers behind it and the rule that produced it (JSON-serialisable).

    `sensitivity`: inputs of the complete-case and budget-exhausted-as-wrong analyses; a status they change is kept and
    flagged MISSINGNESS_SENSITIVE (scorecard 1.7). `control`: `primary_family` of the non-physics dependency control; a
    control F1 EFFECT in the core's direction flags GENERAL_NUMERIC_OR_DEPENDENCY without changing any status (section 4).
    """

    statuses, rt = _statuses(inputs)
    if sensitivity:
        for name, alt in sensitivity.items():
            alt_statuses, _ = _statuses(alt)
            for h, res in statuses.items():
                res.setdefault("sensitivity", {})[name] = alt_statuses[h]["status"]
                if alt_statuses[h]["status"] != res["status"]:
                    res["flags"] = sorted(set(res["flags"]) | {"MISSINGNESS_SENSITIVE"})
    global_flags: list[str] = []
    control_out = None
    if control is not None:
        control_out = {k: _numbers(control.get(k)) for k in ("F1", "F2", "F3")}
        core_f1, ctrl_f1 = _eff(inputs.family.get("F1")), _eff(control.get("F1"))
        if _is(core_f1, "EFFECT", 1) and _is(ctrl_f1, "EFFECT", 1):
            global_flags.append("GENERAL_NUMERIC_OR_DEPENDENCY")
        control_out["note"] = "a null on the control is INCONCLUSIVE unless powered and is not evidence of physics-specificity"
    contrasts = {k: _numbers(inputs.family.get(k)) for k in ("F1", "F2", "F3")}
    contrasts["F1_vs_no_cue"] = _numbers(rvs.paired_summary([e.get("F1_vs_no_cue") for e in inputs.estimates.values()],
                                                            rvs.SESOI["F1"], "greater"))
    if not all("method_agreement" in inputs.family.get(k, {}) for k in ("F1", "F2", "F3")
               if inputs.family.get(k, {}).get("outcome") != NOT_EVALUATED):
        global_flags.append("DIAGNOSTICS_MISSING")
    descriptive = None
    if inputs.lambdas is not None:
        flat = [v for per in inputs.lambdas.values() for v in per.values()]
        descriptive = {"lambda_cells": len(flat), "multimodal": sum(v["status"] == "MULTIMODAL" for v in flat),
                       "not_evaluated": sum(v["status"] == "NOT_EVALUATED" for v in flat),
                       "note": "lambda and Lambda are descriptive and gate nothing"}
    out = {"schema": SCHEMA, "sources": list(SOURCES), "population": inputs.population,
           "configuration": inputs.configuration, "statuses_allowed": list(STATUSES),
           "summary": {h: statuses[h]["status"] for h in HYPOTHESES}, "hypotheses": statuses, "r_tracking": rt,
           "contrasts": contrasts, "misuse": {st: {h: {k: v[k] for k in ("attribution", "reason", "J",
                                                                        "structures_defined", "structures_confounded",
                                                                        "matches_total", "values_above_N")}
                                                   | {"M": _numbers(v["M"])} for h, v in m.items()}
                                              for st, m in (inputs.misuse or {}).items()},
           "control": control_out, "descriptive": descriptive, "flags": global_flags,
           "notes": ["G3 is estimation: no Holm correction is read here", "strata are never pooled",
                     "the population-average analysis on the all-validated population is a separate scorecard, "
                     "reported beside and never substituted", *inputs.notes]}
    return _jsonable(out)
