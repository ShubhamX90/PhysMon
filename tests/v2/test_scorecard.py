"""Tests of the G3 hypothesis scorecard (`physmon.analysis.scorecard`): synthetic worlds in which each hypothesis should
be SUPPORTED, CONTRADICTED, INCONCLUSIVE or NOT_EVALUATED under `g3_scorecard_thresholds.md` as amended by
`decisions_2026-11-13.md`. End-to-end worlds run the whole analysis on simulated records; rule edge cases use
structure-level estimates with known values."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rolevalue_worlds as worlds  # noqa: E402

from physmon.analysis import rolevalue_stats as rs  # noqa: E402
from physmon.analysis import scorecard as sc  # noqa: E402

K = 40  # large k so that the per-phrasing F3 TOST can pass (see test_phrasing_agreement_on_f3_needs_samples)
J = 30


def card_for(probs, n=J, k=K, seed=0, **kw):
    cells, records = worlds.simulate(n, k, probs, seed=seed, **{k_: v for k_, v in kw.items() if k_ in (
        "unit", "with_ck", "tokens", "budget")})
    inputs = sc.build_inputs(records, cells, hierarchical=False, with_lambdas=False)
    card = sc.scorecard(inputs)
    json.dumps(card, allow_nan=False)  # JSON-serialisable, no NaN
    assert set(card["summary"]) == set(sc.HYPOTHESES)
    for h, res in card["hypotheses"].items():
        assert res["status"] in sc.STATUSES and res["rule"] and res["reason"], h
    return card


@pytest.fixture(scope="module")
def effect_card():
    """D loses 35 points to add:x; R tracks at 0.55 and never answers the neglect value."""

    return card_for(lambda c, j: {"correct": 0.5, "add:x": 0.35} if c.stratum == "D" else (
        {"correct": 0.55} if c.stratum == "R" else {"correct": 0.85}), seed=1)


@pytest.fixture(scope="module")
def equivalent_card():
    """Every stratum tracks at 0.6; equal response lengths; nothing matches a foil."""

    return card_for(lambda c, j: {"correct": 0.6}, seed=2, tokens=lambda c, j: 800.0)


# --- end-to-end worlds ----------------------------------------------------------------------------------------------------

def test_a_d_loss_attributed_to_a_route_supports_h3_and_contradicts_h0_and_h6(effect_card):
    s = effect_card["summary"]
    assert s["H3-D"] == "SUPPORTED" and "add" in effect_card["hypotheses"]["H3-D"]["reason"]
    assert s["H0"] == "CONTRADICTED" and s["H6-RD"] == "CONTRADICTED"
    assert s["H3-R"] == "CONTRADICTED"  # F2 equivalent: R never neglects
    assert s["H5"] == "CONTRADICTED"  # departures in O1/O4
    assert s["H1"] == "CONTRADICTED"  # copy absent in D (M_copy equivalent)
    for h in ("H2", "H4", "H3-C", "H3-K", "H6-extended"):  # not run / not computable: never a zero
        assert s[h] == "NOT_EVALUATED"
    assert "decision 12" in effect_card["hypotheses"]["H4"]["reason"]
    assert effect_card["r_tracking"]["status"] == "MEETS" and effect_card["misuse"]["D"]["add"]["attribution"] == "ATTRIBUTED"
    assert effect_card["hypotheses"]["H3-D"]["per_phrasing"] == {"0": "SUPPORTED", "1": "SUPPORTED"}


def test_an_invariant_world_supports_h0_and_h6_rd_and_contradicts_h3(equivalent_card):
    s = equivalent_card["summary"]
    assert s["H0"] == "SUPPORTED" and s["H6-RD"] == "SUPPORTED"  # co-scored (inconsistency H.4)
    assert s["H3-D"] == "CONTRADICTED" and s["H3-R"] == "CONTRADICTED"
    assert s["H5"] == "CONTRADICTED" and "no cost rise" in equivalent_card["hypotheses"]["H5"]["reason"]
    assert all(equivalent_card["contrasts"][f]["outcome"] == "EQUIVALENT" for f in ("F1", "F2", "F3"))


def test_r_neglect_supports_h3_r_and_contradicts_h6():
    card = card_for(lambda c, j: {"correct": 0.45, "neglect": 0.3} if c.stratum == "R" else {"correct": 0.6}, seed=3)
    s = card["summary"]
    assert s["H3-R"] == "SUPPORTED" and s["H6-RD"] == "CONTRADICTED" and s["H0"] == "CONTRADICTED"
    assert s["H3-D"] == "INCONCLUSIVE"  # F1 equivalent but F2 EFFECT: not the H3 pattern of evidence against


def test_a_loss_in_one_phrasing_only_is_wording_dependent():
    card = card_for(lambda c, j: ({"correct": 0.25, "add:x": 0.5} if c.phrasing_id == "d0" else {"correct": 0.85})
                    if c.stratum == "D" else ({"correct": 0.55} if c.stratum == "R" else {"correct": 0.85}), seed=4)
    h3 = card["hypotheses"]["H3-D"]
    assert h3["status"] == "INCONCLUSIVE" and "WORDING_DEPENDENT" in h3["flags"]
    assert h3["pooled_status_before_phrasing_rule"] == "SUPPORTED"
    assert h3["per_phrasing"] == {"0": "SUPPORTED", "1": "CONTRADICTED"}
    assert not h3["phrasing_agreement"]["per_contrast"]["F1"]["agree"]


def test_r_tracking_below_the_criterion_makes_role_hypotheses_not_evaluated_but_h0_is_scored():
    card = card_for(lambda c, j: {"correct": 0.3} if c.stratum == "R" else {"correct": 0.6}, n=20, k=8, seed=5)
    assert card["r_tracking"]["status"] == "BELOW" and card["r_tracking"]["T_R"] < sc.R_TRACKING_CRITERION
    for h in ("H3-D", "H3-R", "H6-RD", "H6-extended"):
        res = card["hypotheses"][h]
        assert res["status"] == "NOT_EVALUATED" and "uninterpretable for role" in res["reason"]
    assert card["summary"]["H0"] != "NOT_EVALUATED"


def test_a_heterogeneous_small_loss_is_inconclusive_not_no_effect():
    z = np.random.default_rng(6).normal(0, 1, 20)
    losses = 0.05 + 0.2 * (z - z.mean()) / z.std(ddof=1)  # per-structure loss with mean 0.05, SD 0.2 exactly
    card = card_for(lambda c, j: {"correct": 0.7 - losses[j]} if c.stratum == "D" else {"correct": 0.7}, n=20, k=8,
                    seed=6)
    assert card["contrasts"]["F1"]["outcome"] == "INCONCLUSIVE"
    assert card["summary"]["H0"] == "INCONCLUSIVE" and card["summary"]["H6-RD"] == "INCONCLUSIVE"
    assert card["summary"]["H3-D"] == "INCONCLUSIVE"


def test_copy_in_both_unit_classes_supports_h1():
    def copying(c, j):
        if c.stratum in ("R", "D"):
            return {"correct": 0.6, ("copy" if "copy" in c.foils else "digit_copy"): 0.25}
        return {"correct": 0.85}

    card = card_for(copying, n=24, k=8, seed=7, unit=lambda j: "copy" if j % 2 else "digit_copy")
    h1 = card["hypotheses"]["H1"]
    assert h1["status"] == "SUPPORTED" and "UNIT_PART_NOT_EVALUATED" not in h1["flags"]
    assert card["summary"]["H3-D"] == "INCONCLUSIVE" and "counts for H1" in card["hypotheses"]["H3-D"]["reason"]


def test_phrasing_agreement_on_f3_needs_samples():
    """At k = 8 the per-phrasing F3 difference is too noisy for its TOST at J = 30, so role statuses of an invariant
    world stay INCONCLUSIVE (WORDING_DEPENDENT): the rule of the plan, recorded here so it is not a surprise in G3."""

    card = card_for(lambda c, j: {"correct": 0.6}, k=8, seed=8)
    h6 = card["hypotheses"]["H6-RD"]
    assert h6["status"] == "INCONCLUSIVE" and "WORDING_DEPENDENT" in h6["flags"]
    assert h6["pooled_status_before_phrasing_rule"] == "SUPPORTED"
    assert not h6["phrasing_agreement"]["per_contrast"]["F3"]["agree"]


# --- rule edge cases on structure-level estimates -------------------------------------------------------------------------

def summary(mean, sd=0.02, n=30, margin=0.10, alternative="greater", seed=0):
    rng = np.random.default_rng(seed)
    d = rng.normal(0, 1, n)
    d = mean + sd * (d - d.mean()) / d.std(ddof=1)  # exact mean and SD
    return rs.diagnosed_summary(list(d), margin, alternative)


def family(f1=0.0, f2=0.0, f3=0.0, sd=0.02):
    return {"F1": summary(f1, sd, seed=1), "F2": summary(f2, sd, seed=2),
            "F3": summary(f3, sd * 4, margin=math.log(1.5), alternative="two-sided", seed=3)}


def estimates(t_r=0.6, n=20):
    return {f"S{j}": {"T": {"R": t_r}, "n_values": {"R": 3}, "F1_vs_no_cue": None} for j in range(n)}


AGREE = {f"phrasing_by_role_{f}": {"outcome": "EQUIVALENT", "agree": True} for f in ("F1", "F2", "F3")}


def misuse_entry(attribution, mean=0.0, sd=0.02, reason="test"):
    m = summary(mean, sd, seed=4)
    return {"attribution": attribution, "reason": reason, "M": m, "J": m["J"], "structures_defined": m["J"],
            "structures_confounded": 0, "matches_total": 100, "values_above_N": 3}


def inputs(**kw):
    base = {"estimates": estimates(), "family": family(), "phrasing": dict(AGREE)}
    base.update(kw)
    return sc.ScorecardInputs(**base)


def status(card, h):
    return card["hypotheses"][h]["status"]


def test_decision_1_trivial_effect_supports_h6_rd_but_not_h0():
    card = sc.scorecard(inputs(family=family(f1=0.04, sd=0.02), misuse={"D": {"add": misuse_entry("NOT_ATTRIBUTED")}}))
    assert card["contrasts"]["F1"]["outcome"] == "TRIVIAL_EFFECT"
    assert status(card, "H6-RD") == "SUPPORTED" and "TRIVIAL_DEPARTURE_WITHIN_SESOI" in card["hypotheses"]["H6-RD"]["flags"]
    assert status(card, "H0") == "INCONCLUSIVE" and "decision 1" in card["hypotheses"]["H0"]["reason"]


def test_method_disagreement_demotes_an_h3_effect():
    disagree = rs.diagnosed_summary([0.11, 0.18, 0.1, 0.01, 0.19, -0.04, 0.01, -0.03], 0.10, "greater")
    fam = {**family(), "F1": disagree}
    card = sc.scorecard(inputs(family=fam, misuse={"D": {"add": misuse_entry("ATTRIBUTED", 0.05, sd=0.3)}}))
    h3 = card["hypotheses"]["H3-D"]
    assert card["contrasts"]["F1"]["outcome"] == "EFFECT" and h3["status"] == "INCONCLUSIVE"
    assert "METHOD_DISAGREEMENT" in h3["flags"] and card["contrasts"]["F1"]["effective_label"] == "INCONCLUSIVE"
    assert status(card, "H0") == "INCONCLUSIVE"  # a departure the methods do not agree on does not contradict H0


def test_decision_8_r_tracking_criterion_boundaries():
    assert sc.r_tracking_check(estimates(0.40, 16))["status"] == "MEETS"
    assert sc.r_tracking_check(estimates(0.399, 16))["status"] == "BELOW"
    low_n = sc.r_tracking_check(estimates(0.9, 15))
    assert low_n["status"] == "NOT_EVALUATED" and "15" in low_n["reason"]
    two_values = {f"S{j}": {"T": {"R": 0.9}, "n_values": {"R": 2}} for j in range(20)}
    assert sc.r_tracking_check(two_values)["J"] == 0
    card = sc.scorecard(inputs(estimates=estimates(0.9, 15)))
    assert status(card, "H6-RD") == "NOT_EVALUATED" and "not evaluable" in card["hypotheses"]["H6-RD"]["reason"]


def test_missing_phrasing_agreement_blocks_a_role_claim():
    card = sc.scorecard(inputs(phrasing=None, misuse={"D": {"add": misuse_entry("NOT_ATTRIBUTED")}}))
    h6 = card["hypotheses"]["H6-RD"]
    assert h6["status"] == "INCONCLUSIVE" and "PHRASING_AGREEMENT_NOT_EVALUATED" in h6["flags"]
    assert status(card, "H0") == "SUPPORTED"  # H0 is not a role claim


def test_h1_rules():
    copy_r = {"copy": {"CR": summary(0.2, seed=5)}, "digit_copy": {"CR": summary(0.2, seed=6)}}
    only_same = sc.scorecard(inputs(misuse={"D": {"copy": misuse_entry("ATTRIBUTED", 0.2)}}, copy_r=copy_r))
    assert status(only_same, "H1") == "SUPPORTED" and "UNIT_PART_NOT_EVALUATED" in only_same["hypotheses"]["H1"]["flags"]
    confined = sc.scorecard(inputs(misuse={"D": {"copy": misuse_entry("ATTRIBUTED", 0.2),
                                                 "digit_copy": misuse_entry("INCONCLUSIVE", 0.0)}}, copy_r=copy_r))
    assert status(confined, "H1") == "CONTRADICTED" and "COPY_CONFINED_TO_SAME_UNIT" in confined["hypotheses"]["H1"]["flags"]
    unclear = sc.scorecard(inputs(misuse={"D": {"copy": misuse_entry("INCONCLUSIVE", 0.05, sd=0.3)}}, copy_r=copy_r))
    assert status(unclear, "H1") == "INCONCLUSIVE"
    assert status(sc.scorecard(inputs(misuse={"D": {"copy": misuse_entry("NOT_EVALUATED")}})), "H1") == "NOT_EVALUATED"


def test_h2_needs_the_unit_ablation():
    assert status(sc.scorecard(inputs()), "H2") == "NOT_EVALUATED"
    same, none = summary(0.3, seed=7), summary(0.0, seed=8)
    assert status(sc.scorecard(inputs(h2_ablation={"F1_same_unit": same, "F1_incompatible_unit": none})),
                  "H2") == "SUPPORTED"
    assert status(sc.scorecard(inputs(h2_ablation={"F1_same_unit": same, "F1_incompatible_unit": same})),
                  "H2") == "CONTRADICTED"
    assert status(sc.scorecard(inputs(h2_ablation={"F1_same_unit": same, "F1_incompatible_unit": summary(0.05, 0.3)})),
                  "H2") == "INCONCLUSIVE"


def test_h3_c_and_h6_extended_from_c_and_k_contrasts():
    within = {"run": True, "F1": summary(0.0, seed=9),
              "slope": summary(0.0, 0.08, margin=math.log(1.5), alternative="two-sided", seed=10)}
    loss = {"run": True, "F1": summary(0.3, seed=11), "slope": within["slope"]}
    card = sc.scorecard(inputs(ck={"C": loss, "K": within}, misuse={
        "D": {"add": misuse_entry("NOT_ATTRIBUTED")}, "C": {"wrong_law": misuse_entry("ATTRIBUTED", 0.3)}}))
    assert status(card, "H3-C") == "SUPPORTED" and status(card, "H3-K") == "CONTRADICTED"
    assert status(card, "H6-extended") == "CONTRADICTED"
    ok = sc.scorecard(inputs(ck={"C": within, "K": within}, misuse={"D": {"add": misuse_entry("NOT_ATTRIBUTED")}}))
    assert status(ok, "H6-extended") == "SUPPORTED"
    assert status(sc.scorecard(inputs()), "H6-extended") == "NOT_EVALUATED"


def test_h4_is_not_evaluated_without_the_frozen_extractor_and_scored_with_it():
    att = {"D": {"add": misuse_entry("ATTRIBUTED", 0.3)}}
    fam = family(f1=0.3)
    assert status(sc.scorecard(inputs(family=fam, misuse=att)), "H4") == "NOT_EVALUATED"
    frozen = {"extractor_frozen": True, "reasoning_trace": True}
    assert status(sc.scorecard(inputs(family=fam, misuse=att, trace={**frozen, "x": 45, "n": 60})), "H4") == "SUPPORTED"
    assert status(sc.scorecard(inputs(family=fam, misuse=att, trace={**frozen, "x": 10, "n": 60})), "H4") == "CONTRADICTED"
    assert status(sc.scorecard(inputs(family=fam, misuse=att, trace={**frozen, "x": 4, "n": 7})), "H4") == "INCONCLUSIVE"
    none_attr = {"D": {"add": misuse_entry("NOT_ATTRIBUTED")}}
    res = sc.scorecard(inputs(family=fam, misuse=none_attr, trace={**frozen, "x": 45, "n": 60}))["hypotheses"]["H4"]
    assert res["status"] == "NOT_EVALUATED" and "no attributed" in res["reason"]


def test_h5_cost_rules():
    longer = {"L5": summary(0.4, 0.05, margin=math.log(1.2), seed=12), "B5": summary(0.0, 0.01, margin=0.05, seed=13)}
    assert status(sc.scorecard(inputs(cost=longer)), "H5") == "SUPPORTED"
    same = {"L5": summary(0.0, 0.05, margin=math.log(1.2), seed=14), "B5": summary(0.0, 0.01, margin=0.05, seed=15)}
    assert status(sc.scorecard(inputs(cost=same)), "H5") == "CONTRADICTED"
    assert status(sc.scorecard(inputs(cost=longer, family=family(f1=0.3))), "H5") == "CONTRADICTED"
    unclear = {"L5": summary(0.05, 0.8, margin=math.log(1.2), seed=16), "B5": summary(0.0, 0.01, margin=0.05, seed=17)}
    assert status(sc.scorecard(inputs(cost=unclear)), "H5") == "INCONCLUSIVE"
    assert status(sc.scorecard(inputs()), "H5") == "NOT_EVALUATED"


def test_missingness_sensitivity_and_the_non_physics_control_are_flags_not_status_changes():
    base = inputs(family=family(f1=0.3), misuse={"D": {"add": misuse_entry("ATTRIBUTED", 0.3)}})
    alt = inputs(family=family(f1=0.0), misuse={"D": {"add": misuse_entry("NOT_ATTRIBUTED")}})
    card = sc.scorecard(base, sensitivity={"complete_case": alt}, control=family(f1=0.3))
    h3 = card["hypotheses"]["H3-D"]
    assert h3["status"] == "SUPPORTED" and "MISSINGNESS_SENSITIVE" in h3["flags"]
    assert h3["sensitivity"] == {"complete_case": "CONTRADICTED"}
    assert "GENERAL_NUMERIC_OR_DEPENDENCY" in card["flags"]
    json.dumps(card, allow_nan=False)


def test_f1_or_f2_not_evaluated_is_not_evaluated_never_a_zero():
    few = {"F1": rs.diagnosed_summary([0.0] * 4, 0.1, "greater"), "F2": summary(0.0), "F3": family()["F3"]}
    card = sc.scorecard(inputs(family=few))
    assert status(card, "H0") == "NOT_EVALUATED" and status(card, "H6-RD") == "NOT_EVALUATED"
    assert status(card, "H3-D") == "NOT_EVALUATED" and card["contrasts"]["F1"]["outcome"] == "NOT_EVALUATED"
