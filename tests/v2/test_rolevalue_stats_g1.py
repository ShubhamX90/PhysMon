"""Tests of the G1-decision extensions of the role-by-value analysis (decisions 4, 5, 13, 21 of
`docs/registry/v2/g1/decisions_2026-11-13.md`) on synthetic records and structure-level estimates with known truth."""

from __future__ import annotations

import itertools
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


def effect_world(cell, j):
    """D loses 30 points to the add:x curve; R answers the neglect value 20% of the time, the placebo 1%."""

    if cell.stratum == "D":
        return {"correct": 0.55, "add:x": 0.30}
    if cell.stratum == "R":
        return {"correct": 0.70, "neglect": 0.20, "placebo": 0.01}
    return {"correct": 0.85}


def null_world(cell, j):
    if cell.stratum == "R":
        return {"correct": 0.80, "neglect": 0.02, "placebo": 0.02}
    return {"correct": 0.80}


@pytest.fixture(scope="module")
def effect_data():
    return worlds.simulate(24, 8, effect_world, seed=1)


@pytest.fixture(scope="module")
def null_data():
    return worlds.simulate(24, 8, null_world, seed=2)


# --- decision 4 ----------------------------------------------------------------------------------------------------------

def test_no_status_below_six_structures_because_the_sign_flip_test_cannot_speak():
    assert rs.MIN_EVALUABLE_STRUCTURES == 6
    assert 2 / 2 ** 5 > rs.ALPHA >= 2 / 2 ** 6  # two-sided minimum sign-flip p at J = 5 and J = 6
    est = {f"S{j}": {"F1": 0.3, "F2": 0.2, "F3": 1.0} for j in range(5)}
    fam = rs.primary_family(est)
    assert all(fam[f]["outcome"] == "NOT_EVALUATED" and "mean" not in fam[f] for f in ("F1", "F2", "F3"))
    assert fam["holm"] == {} and "robustness" not in fam["F1"]
    assert rs.leave_k_out([0.1] * 5, 0.1, "greater")["assessable"] is False


# --- decision 5: leave-k-out robustness ------------------------------------------------------------------------------------

def test_vectorised_deletion_labels_equal_paired_summary_labels():
    rng = np.random.default_rng(5)
    for alternative, margin in (("greater", 0.10), ("two-sided", math.log(1.5))):
        d = rng.normal(0.08, 0.12, 12)
        subsets = list(itertools.combinations(range(12), 2))[:40]
        fast = rs._labels_after_deletion(d, np.asarray(subsets), margin, alternative)
        for i, drop in enumerate(subsets):
            kept = [x for j, x in enumerate(d) if j not in drop]
            assert fast["label"][i] == rs.paired_summary(kept, margin, alternative)["outcome"]
            assert fast["mean"][i] == pytest.approx(np.mean(kept))


def test_leave_k_out_enumerates_or_samples_subsets_and_keeps_a_strong_effect():
    rng = np.random.default_rng(6)
    d = rng.normal(0.40, 0.05, 40)  # every structure shows a large loss
    rob = rs.leave_k_out(d, 0.10, "greater")
    assert rob["full_label"] == "EFFECT" and not rob["fragile"] and not rob["not_robust"]
    assert rob["by_k"]["1"]["n_subsets"] == 40 and rob["by_k"]["1"]["exhaustive"]
    assert rob["by_k"]["2"]["n_subsets"] == math.comb(40, 2) and rob["by_k"]["2"]["exhaustive"]  # 780 <= 1,000
    assert rob["by_k"]["3"]["n_subsets"] == 1000 and not rob["by_k"]["3"]["exhaustive"]  # 9,880 > 1,000: sampled
    assert all(rob["by_k"][k]["share_label_unchanged"] == 1.0 and rob["by_k"][k]["share_sign_unchanged"] == 1.0
               for k in ("1", "2", "3"))
    assert rs.leave_k_out(d, 0.10, "greater") == rob  # seeded


def test_an_effect_carried_by_three_structures_is_not_robust_and_fragile():
    d = [1.0, 0.9, 0.8] + [0.02, -0.01, 0.0, 0.01, -0.02, 0.0, 0.01, 0.0, -0.01]
    s = rs.diagnosed_summary(d, 0.10, "greater")
    assert s["outcome"] == "EFFECT"
    rob = s["robustness"]
    assert rob["not_robust"] and rob["fragile"]
    assert not rob["extreme_deletion"]["3"]["still_excludes_zero"]
    assert sorted(rob["extreme_deletion"]["3"]["dropped_estimates"]) == [0.8, 0.9, 1.0]
    eff = rs.effective_label(s)
    assert eff["label"] == "INCONCLUSIVE" and "NOT_ROBUST" in eff["flags"] and "FRAGILE" in eff["flags"]


def test_deletions_that_leave_fewer_than_six_structures_count_as_label_changes():
    rob = rs.leave_k_out([0.4, 0.42, 0.38, 0.41, 0.39, 0.40, 0.43], 0.10, "greater")  # J = 7: k = 2, 3 leave 5, 4
    assert rob["by_k"]["1"]["share_label_unchanged"] == 1.0
    assert rob["by_k"]["2"]["labels"] == {"NOT_EVALUATED": math.comb(7, 2)} and rob["fragile"]
    assert not rob["not_robust"]  # the extreme-deletion t-interval still excludes zero


# --- decision 5: method agreement -----------------------------------------------------------------------------------------

def test_methods_agree_on_a_clear_effect_and_disagreement_demotes_an_effect():
    clear = rs.diagnosed_summary(np.random.default_rng(7).normal(0.3, 0.1, 30), 0.10, "greater")
    assert clear["method_agreement"]["decision_methods_agree"] and rs.effective_label(clear)["label"] == "EFFECT"
    # t and bootstrap exclude zero, the exact sign-flip p is 0.051
    d = [0.11, 0.18, 0.1, 0.01, 0.19, -0.04, 0.01, -0.03]
    s = rs.diagnosed_summary(d, 0.10, "greater")
    ma = s["method_agreement"]
    assert s["outcome"] == "EFFECT" and ma["methods"]["t"]["excludes_zero"] and ma["methods"]["bootstrap"]["excludes_zero"]
    assert not ma["methods"]["sign_flip"]["excludes_zero"] and not ma["decision_methods_agree"]
    eff = rs.effective_label(s)
    assert eff["label"] == "INCONCLUSIVE" and "METHOD_DISAGREEMENT" in eff["flags"] and eff["raw"] == "EFFECT"


def test_a_one_sided_contrast_in_the_untested_direction_is_read_in_its_own_direction():
    d = np.random.default_rng(8).normal(-0.3, 0.1, 20)  # D tracks better than N
    s = rs.diagnosed_summary(d, 0.10, "greater")
    assert s["outcome"] == "EFFECT" and s["method_agreement"]["direction"] == -1
    assert s["method_agreement"]["decision_methods_agree"] and rs.effective_label(s)["sign"] == -1


# --- decision 5: hierarchical view ----------------------------------------------------------------------------------------

def test_hierarchical_view_agrees_with_the_paired_analysis_on_known_effects(effect_data):
    cells, records = effect_data
    hier = rs.hierarchical_view(records, cells)
    assert all(h["status"] == "OK" and h["method"].startswith("BinomialBayesMixedGLM") for h in hier.values())
    true_f1 = math.log(0.85 / 0.15) - math.log(0.55 / 0.45)  # logit loss of D against N
    assert hier["F1"]["estimate"] == pytest.approx(true_f1, abs=0.25) and hier["F1"]["interval"][0] > 0
    assert hier["F2"]["estimate"] > 0 and hier["F2"]["interval"][0] > 0
    fam = rs.primary_family(rs.structure_estimates(records, cells), hierarchical=hier)
    for f in ("F1", "F2"):
        ma = fam[f]["method_agreement"]
        assert ma["hierarchical_agrees_in_sign"] and ma["hierarchical_agrees_in_excluding_zero"]
        assert ma["all_agree_in_sign"] and fam[f]["hierarchical"]["status"] == "OK"
    assert hier == rs.hierarchical_view(records, cells)  # reproducible: no global RNG in the fit


def test_hierarchical_f3_is_the_role_by_value_term_and_null_f1_includes_zero(null_data):
    cells, records = worlds.simulate(24, 8, lambda c, j: {"correct": (0.9, 0.6, 0.3)[c.value_index]}
                                     if c.stratum == "R" else {"correct": 0.8}, seed=3)
    hier = rs.hierarchical_view(records, cells)
    true_slope = (math.log(0.3 / 0.7) - math.log(0.9 / 0.1)) / 2  # R slope per value step; D slope 0
    assert hier["F3"]["estimate"] == pytest.approx(true_slope, abs=0.3) and hier["F3"]["interval"][1] < 0
    assert hier["F2"]["status"] == "NOT_EVALUATED" and "does not vary" in hier["F2"]["reason"]  # never a zero
    null_cells, null_records = null_data
    h0 = rs.hierarchical_view(null_records, null_cells)
    assert h0["F1"]["interval"][0] < 0 < h0["F1"]["interval"][1]


def test_hierarchical_view_falls_back_to_gee_when_the_bayesian_fit_fails(effect_data, monkeypatch):
    from statsmodels.genmod import bayes_mixed_glm

    def boom(self, *a, **k):
        raise np.linalg.LinAlgError("singular")

    monkeypatch.setattr(bayes_mixed_glm.BinomialBayesMixedGLM, "fit_map", boom)
    cells, records = effect_data
    hier = rs.hierarchical_view(records, cells)
    assert hier["F1"]["method"].startswith("GEE") and "singular" in hier["F1"]["fallback_reason"]
    assert hier["F1"]["interval"][0] > 0


# --- misuse attribution (decision 13), copy, cost, C/K ---------------------------------------------------------------------

def test_misuse_attribution_recovers_the_simulated_curve_and_keeps_rare_curves_inconclusive(effect_data):
    cells, records = effect_data
    att = rs.misuse_attribution(records, cells, "D")
    assert att["add"]["attribution"] == "ATTRIBUTED" and att["add"]["values_above_N"] == 3
    assert att["add"]["M"]["mean"] == pytest.approx(0.30, abs=0.05)
    for h in ("subtract", "relevant_twin", "copy"):  # never answered: fewer than 5 matches is INCONCLUSIVE, not absent
        assert att[h]["attribution"] == "INCONCLUSIVE" and att[h]["matches_total"] == 0


def test_misuse_needs_two_of_three_values_and_unconfounded_structures():
    # the curve is followed only at the first value: M_h is positive, but the 2-of-3 rule fails
    one_value = worlds.simulate(24, 8, lambda c, j: {"correct": 0.5, "add:x": 0.4}
                                if c.stratum == "D" and c.value_index == 0 else {"correct": 0.85}, seed=4)
    att = rs.misuse_attribution(one_value[1], one_value[0], "D")["add"]
    assert att["M"]["mean"] > 0.1 and att["values_above_N"] == 1 and att["attribution"] == "NOT_ATTRIBUTED"
    cells, records = worlds.simulate(24, 8, effect_world, seed=5)
    for c in cells.values():  # add:x confounded with the gold in 13 of 24 structures
        if c.stratum == "D" and int(c.structure_id[1:]) < 13:
            c.confounded.append("add:x~gold")
    att = rs.misuse_attribution(records, cells, "D")["add"]
    assert att["attribution"] == "NOT_ATTRIBUTED" and "CONFOUNDED" in att["reason"]
    few = {k: c for k, c in cells.items() if int(c.structure_id[1:]) >= 19}  # 5 structures
    few_records = [r for r in records if rs.cell_key(r) in few]
    assert rs.misuse_attribution(few_records, few, "D")["add"]["attribution"] == "NOT_EVALUATED"


def test_copy_classes_follow_the_unit_and_copy_excess_in_r_is_estimated():
    def copying(cell, j):
        if cell.stratum in ("R", "D"):
            name = "copy" if "copy" in cell.foils else "digit_copy"
            return {"correct": 0.6, name: 0.25}
        return {"correct": 0.85}

    cells, records = worlds.simulate(24, 8, copying, seed=9, unit=lambda j: "copy" if j % 2 else "digit_copy")
    att = rs.misuse_attribution(records, cells, "D")
    assert att["copy"]["attribution"] == att["digit_copy"]["attribution"] == "ATTRIBUTED"
    assert att["copy"]["J"] == att["digit_copy"]["J"] == 12
    cr = rs.copy_excess_r(records, cells)
    assert cr["copy"]["CR"]["outcome"] == "EFFECT" and cr["digit_copy"]["CR"]["mean"] == pytest.approx(0.25, abs=0.05)


def test_cost_contrasts_detect_longer_answers_and_more_exhausted_budgets():
    cells, records = worlds.simulate(
        20, 8, lambda c, j: {"correct": 0.8}, seed=10, tokens=lambda c, j: 1500.0 if c.stratum == "D" else 1000.0,
        budget=lambda c, j: 0.2 if c.stratum == "D" else 0.02)
    cost = rs.cost_contrasts(records, cells)
    assert cost["L5"]["mean"] == pytest.approx(math.log(1.5), abs=0.03) and cost["L5"]["outcome"] == "EFFECT"
    assert cost["B5"]["mean"] == pytest.approx(0.18, abs=0.04) and cost["B5"]["outcome"] == "EFFECT"
    assert cost["L5_vs_no_cue"]["outcome"] == "EFFECT"


def test_ck_family_and_phrasing_indices_pair_r_and_d_phrasings():
    def world(cell, j):
        if cell.stratum == "C":
            return {"correct": 0.5, "wrong_law": 0.35}
        if cell.stratum == "D" and cell.phrasing_id == "d0":
            return {"correct": 0.4, "add:x": 0.45}
        return {"correct": 0.85}

    cells, records = worlds.simulate(20, 8, world, seed=11, with_ck=True)
    ck = rs.ck_family(rs.structure_estimates(records, cells))
    assert ck["C"]["run"] and ck["C"]["F1"]["outcome"] == "EFFECT" and ck["K"]["F1"]["outcome"] in (
        "EQUIVALENT", "INCONCLUSIVE")
    assert rs.misuse_attribution(records, cells, "C")["wrong_law"]["attribution"] == "ATTRIBUTED"
    idx = rs.phrasing_indices(cells)
    assert idx["S00:R:z0:r0"] == idx["S00:D:z0:d0"] == 0 and idx["S00:D:z2:d1"] == 1
    ph = rs.phrasing_agreement(records, cells)
    assert ph["per_phrasing"]["0"]["F1"]["mean"] == pytest.approx(0.45, abs=0.06)
    assert ph["per_phrasing"]["1"]["F1"]["mean"] == pytest.approx(0.0, abs=0.06)
    assert not ph["phrasing_by_role_F1"]["agree"]  # one phrasing loses, the other does not: wording-dependent


def test_heldout_value_cells_do_not_enter_the_primary_estimates(effect_data):
    cells, records = effect_data
    cells = dict(cells)
    extra = rs.Cell("S00:D:z5:d0", "S00", "D", 5, "d0", worlds.GOLD_D, {}, None, [], heldout=True)
    cells[extra.key] = extra
    wrong = [{"job_id": f"{extra.key}:s{i}", "completion_status": "COMPLETE", "grade_declared": "wrong",
              "value_in_gold_unit": 1.0} for i in range(50)]
    base = rs.structure_estimates(records, cells)["S00"]["F1"]
    assert rs.structure_estimates(records + wrong, cells)["S00"]["F1"] == base


# --- decision 21: joint TOST power ------------------------------------------------------------------------------------------

def test_joint_equivalence_power_is_below_every_single_contrast_power():
    out = rs.joint_tost_power(rs.SimParams(base_logit=1.0, sd_structure=0.8), rs.SimParamsF2(placebo_rate=0.03),
                              rs.SimParamsF3(sd_slope=0.1), J=40, k=8, n_sims=120)
    single = out["single_equivalence_rate"]
    assert 0 < out["joint_equivalence_rate"] < min(single.values())
    assert out["joint_equivalent_or_trivial_rate"] >= out["joint_equivalence_rate"]
    curve = rs.joint_tost_power_curve(rs.SimParams(), rs.SimParamsF2(), rs.SimParamsF3(), Js=(12, 40), k=8, n_sims=40)
    assert curve["rows"][0]["joint_equivalence_rate"] <= curve["rows"][1]["joint_equivalence_rate"]
