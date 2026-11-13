"""Tests of the frozen role-by-value analysis on synthetic records with known truth (G1: analysis scripts are tested on
synthetic records before any real role-cell record is analysed)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.analysis import rolevalue_stats as rs  # noqa: E402

GOLD_D, GOLD_R = 10.0, (12.0, 14.0, 16.0)


def make_cells(sid: str) -> dict[str, rs.Cell]:
    cells = {f"{sid}:none": rs.Cell(f"{sid}:none", sid, "none", None, None, GOLD_D, {}, None, []),
             f"{sid}:N": rs.Cell(f"{sid}:N", sid, "N", None, "d0", GOLD_D, {}, None, [])}
    for z in range(3):
        for p in ("r0", "r1"):
            cells[f"{sid}:R:z{z}:{p}"] = rs.Cell(f"{sid}:R:z{z}:{p}", sid, "R", z, p, GOLD_R[z],
                                                 {"neglect": GOLD_D, "add:x": GOLD_R[z] + 50}, 2 * GOLD_R[z] - GOLD_D, [])
        for p in ("d0", "d1"):
            cells[f"{sid}:D:z{z}:{p}"] = rs.Cell(f"{sid}:D:z{z}:{p}", sid, "D", z, p, GOLD_D,
                                                 {"relevant_twin": GOLD_R[z], "add:x": GOLD_D + 5 * (z + 1)}, None, [])
    return cells


def rec(key: str, i: int, value: float | None, correct: bool, status: str = "COMPLETE") -> dict:
    return {"job_id": f"{key}:s{i}", "completion_status": status, "grade_declared": "correct" if correct else "wrong",
            "value_in_gold_unit": value}


def records_for(cells: dict[str, rs.Cell], k: int, p_correct: dict[str, float], rng: np.random.Generator,
                wrong_value: dict[str, float] | None = None) -> list[dict]:
    """k samples per cell; a sample is correct with probability p_correct[stratum] (R cells may override by key), else
    answers `wrong_value[stratum]` (default gold + 1000)."""

    out = []
    for key, cell in cells.items():
        p = p_correct.get(key, p_correct.get(cell.stratum, 1.0))
        for i in range(k):
            ok = rng.random() < p
            wrong = (wrong_value or {}).get(cell.stratum, cell.gold + 1000)
            if callable(wrong):
                wrong = wrong(cell)
            out.append(rec(key, i, cell.gold if ok else wrong, ok))
    return out


def test_tracking_counts_only_complete_correct_samples():
    assert rs.tracking(rec("a", 0, 1.0, True)) == 1
    assert rs.tracking(rec("a", 0, 1.0, True, status="BUDGET_EXHAUSTED")) == 0
    assert rs.tracking(rec("a", 0, 1.0, False)) == 0


def test_f1_recovers_a_known_tracking_loss_and_f2_a_known_neglect_excess():
    rng = np.random.default_rng(0)
    cells, records = {}, []
    for j in range(30):
        c = make_cells(f"S{j}")
        cells.update(c)
        # D loses 30 points of tracking against N; R answers the neglect value (y*_D) 25% of the time, the placebo never
        records += records_for(c, 40, {"none": 0.9, "N": 0.9, "D": 0.6, "R": 0.75}, rng,
                               wrong_value={"R": GOLD_D, "D": lambda cell: cell.foils["add:x"]})
    est = rs.structure_estimates(records, cells)
    fam = rs.primary_family(est)
    assert fam["F1"]["mean"] == pytest.approx(0.30, abs=0.04) and fam["F1"]["outcome"] == "EFFECT"
    assert fam["F2"]["mean"] == pytest.approx(0.25, abs=0.04) and fam["F2"]["outcome"] == "EFFECT"
    assert fam["holm"]["F1"]["reject"] and fam["holm"]["F2"]["reject"]
    assert fam["F3"]["outcome"] in ("EQUIVALENT", "INCONCLUSIVE", "TRIVIAL_EFFECT")  # no value dependence was simulated
    support = rs.misuse_support(records, cells, "S0", "D")
    assert support["add:x"]["supported"] and not support["add:x"]["confounded"]


def test_an_equivalent_world_is_called_equivalent_not_no_effect():
    rng = np.random.default_rng(1)
    cells, records = {}, []
    for j in range(60):
        c = make_cells(f"S{j}")
        cells.update(c)
        records += records_for(c, 40, {"none": 0.8, "N": 0.8, "D": 0.8, "R": 0.8}, rng)
    fam = rs.primary_family(rs.structure_estimates(records, cells))
    assert fam["F1"]["outcome"] == "EQUIVALENT" and not fam["holm"]["F1"]["reject"]
    assert "NO_EFFECT" not in {v.get("outcome") for v in fam.values() if isinstance(v, dict)}


def test_f3_detects_value_dependent_tracking_in_one_role():
    rng = np.random.default_rng(2)
    cells, records = {}, []
    for j in range(40):
        c = make_cells(f"S{j}")
        cells.update(c)
        p = {"none": 0.8, "N": 0.8, "D": 0.8}
        for z, pr in enumerate((0.9, 0.6, 0.3)):  # R tracking falls with the value
            for ph in ("r0", "r1"):
                p[f"S{j}:R:z{z}:{ph}"] = pr
        records += records_for(c, 30, p, rng)
    fam = rs.primary_family(rs.structure_estimates(records, cells))
    assert fam["F3"]["mean"] < -rs.SESOI["F3"] and fam["F3"]["outcome"] == "EFFECT"


def test_four_outcome_classification_and_tost():
    assert rs.classify([0.2, 0.4], 1.0, 0.1) == "EFFECT"
    assert rs.classify([0.01, 0.05], 0.01, 0.1) == "TRIVIAL_EFFECT"
    assert rs.classify([-0.05, 0.05], 0.01, 0.1) == "EQUIVALENT"
    assert rs.classify([-0.3, 0.3], 0.6, 0.1) == "INCONCLUSIVE"
    tight = np.random.default_rng(3).normal(0, 0.05, 50)
    assert rs.tost_p(tight, 0.10) < 0.05 and rs.tost_p(tight, 0.001) > 0.05


def test_sign_flip_and_holm():
    assert rs.sign_flip_p([1.0, 1.0, 1.0, 1.0], "greater") == pytest.approx(1 / 16)
    assert rs.sign_flip_p([1.0, -1.0, 1.0, -1.0], "two-sided") == pytest.approx(1.0)
    h = rs.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert h["a"]["p_holm"] == pytest.approx(0.03) and h["c"]["p_holm"] == pytest.approx(0.06)
    assert h["b"]["p_holm"] == pytest.approx(0.06) and h["a"]["reject"] and not h["c"]["reject"]


def test_fewer_than_three_structures_is_not_evaluated_not_zero():
    out = rs.paired_summary([0.1, None, float("nan")], 0.1, "greater")
    assert out["outcome"] == "NOT_EVALUATED" and "mean" not in out


def test_rare_rates_give_finite_intervals_and_the_beta_binomial_recovers_the_mean():
    j = rs.jeffreys(0, 40)
    assert 0 < j["rate"] < 0.02 and 0 < j["lo"] < 1e-3 and j["hi"] > 0.01  # zero successes: a finite rate
    rng = np.random.default_rng(4)
    counts = [(int(rng.binomial(40, rng.beta(2, 38))), 40) for _ in range(60)]  # mean 0.05, overdispersed
    fit = rs.beta_binomial_fit(counts)
    assert fit["mu"] == pytest.approx(0.05, abs=0.015) and fit["ci95_bootstrap"][0] < 0.05 < fit["ci95_bootstrap"][1]
    assert rs.beta_binomial_fit([(0, 20)] * 10)["mu"] > 0


def test_lambda_pools_phrasings_and_flags_multimodal_cells():
    cells = make_cells("S0")
    records = []
    for key, cell in cells.items():
        for i in range(10):
            if cell.stratum == "D":  # half correct, half answering the relevant twin: two modes of 50%
                v = cell.gold if i < 5 else cell.foils["relevant_twin"]
            else:
                v = cell.gold
            records.append(rec(key, i, v, v == cell.gold))
    lam = rs.lambdas(records, cells, "S0")
    assert lam["R:0-2"]["lambda"] == pytest.approx(1.0) and lam["R:0-2"]["status"] == "OK"
    assert lam["D:0-2"]["status"] == "MULTIMODAL"


def test_power_simulation_is_calibrated_under_the_null_and_powerful_under_an_effect():
    # balanced design (the frozen rule): at high tracking the sign-flip test keeps its level
    null = rs.power_f1(rs.SimParams(base_logit=3.5), J=40, k=4, n_sims=1000)
    assert null["rejection_rate_sign_flip"] <= 0.065  # nominal 0.05; Monte Carlo SE about 0.007
    effect = rs.power_f1(rs.SimParams(base_logit=1.0, d_effect_logit=1.5, sd_d_effect=0.3), J=40, k=4, n_sims=200)
    assert effect["rejection_rate_sign_flip"] > 0.8


def test_the_unbalanced_design_over_rejects_which_is_why_n_is_balanced():
    unbalanced = rs.power_f1(rs.SimParams(base_logit=3.5, n_n_cells=1), J=24, k=4, n_sims=2000)
    balanced = rs.power_f1(rs.SimParams(base_logit=3.5), J=24, k=4, n_sims=2000)
    assert unbalanced["rejection_rate_sign_flip"] > balanced["rejection_rate_sign_flip"] + 0.015
