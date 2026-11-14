"""Tests of the candidate phrasing-agreement rules (G1 design study) on small synthetic inputs."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from physmon.analysis import rolevalue_stats as rs  # noqa: E402
import rolevalue_worlds as rw  # noqa: E402


def _est(seed, mean, sd, J=30, n=1):
    return np.random.default_rng(seed).normal(mean, sd, (n, J))


def test_batch_labels_match_paired_summary():
    rng = np.random.default_rng(0)
    for margin, alt in ((0.10, "greater"), (0.10, "two-sided"), (math.log(1.5), "two-sided")):
        for mean, sd in ((0.0, 0.05), (0.05, 0.1), (0.3, 0.1), (0.0, 0.5), (-0.2, 0.05)):
            x = rng.normal(mean, sd, (40, 20))
            batch = rs.batch_paired_labels(x, margin, alt)
            for i in range(len(x)):
                assert batch["label"][i] == rs.paired_summary(list(x[i]), margin, alt)["outcome"]


def test_agreeing_phrasings_agree_and_disagreeing_disagree():
    a = _est(1, 0.0, 0.03, n=200)
    b = _est(2, 0.0, 0.03, n=200)
    lab = rs.batch_agreement_labels(a, b, "F1", "B")
    assert (lab == rs.AGREE).mean() > 0.9
    far = rs.batch_agreement_labels(a + 0.3, b, "F1", "B")
    assert (far == rs.DISAGREE).all()
    # rule A: both phrasings beyond the SESOI on the same side agree even though the difference is not equivalent
    same = rs.batch_agreement_labels(a + 0.5, b + 0.2, "F1", "A")
    assert (same == rs.AGREE).all()
    assert (rs.batch_agreement_labels(a + 0.5, b + 0.2, "F1", "B") == rs.DISAGREE).all()


def test_unresolved_when_noisy_and_rule_c_margin():
    a = _est(3, 0.0, 0.6, J=12, n=300)
    b = _est(4, 0.0, 0.6, J=12, n=300)
    assert rs.agreement_margin("F3", "C") == 2 * rs.SESOI["F3"] and rs.agreement_margin("F1", "C") == rs.SESOI["F1"]
    b_lab = rs.batch_agreement_labels(a, b, "F3", "B")
    c_lab = rs.batch_agreement_labels(a, b, "F3", "C")
    assert (b_lab == rs.UNRESOLVED).mean() > 0.5
    assert (c_lab == rs.AGREE).mean() >= (b_lab == rs.AGREE).mean()


def test_demotion_rules():
    labels = {"F1": np.array([rs.AGREE, rs.AGREE, rs.DISAGREE]), "F2": np.array([rs.AGREE, rs.UNRESOLVED, rs.AGREE]),
              "F3": np.array([rs.AGREE, rs.AGREE, rs.AGREE])}
    assert list(rs.agreement_demotes(labels, "B")) == [False, True, True]
    assert list(rs.agreement_demotes(labels, "D")) == [False, False, True]


def test_scalar_difference_agreement_and_not_evaluated():
    rng = np.random.default_rng(5)
    assert rs.phrasing_difference_agreement(list(rng.normal(0, 0.02, 30)), 0.10)["agreement"] == rs.AGREE
    assert rs.phrasing_difference_agreement(list(rng.normal(0.4, 0.05, 30)), 0.10)["agreement"] == rs.DISAGREE
    assert rs.phrasing_difference_agreement(list(rng.normal(0, 0.8, 8)), 0.10)["agreement"] == rs.UNRESOLVED
    assert rs.phrasing_difference_agreement([0.0, 0.1, 0.2], 0.10)["agreement"] == "NOT_EVALUATED"


def _probs_for(effect_p0, effect_p1):
    def probs(cell, j):
        eff = effect_p0 if cell.phrasing_id in ("r0", "d0") else effect_p1
        if cell.stratum == "D":
            return {"correct": 0.7 - eff}
        if cell.stratum == "R":
            return {"correct": 0.7, "neglect": 0.02, "placebo": 0.02}
        return {"correct": 0.7}
    return probs


def test_rules_on_records_agree_and_disagree_deterministic():
    cells, rec = rw.simulate(20, 20, _probs_for(0.0, 0.0), seed=3)
    out = rs.phrasing_agreement_rules(rec, cells)
    assert out["rules"]["B"]["labels"]["F1"] == rs.AGREE
    assert out["rules"]["D"]["demotes"] in (False, True)
    again = rs.phrasing_agreement_rules(rec, cells)
    assert again["rules"] == out["rules"]
    cells2, rec2 = rw.simulate(20, 20, _probs_for(0.30, 0.0), seed=3)
    out2 = rs.phrasing_agreement_rules(rec2, cells2)
    for rule in ("A", "B", "C", "D"):
        assert out2["rules"][rule]["labels"]["F1"] == rs.DISAGREE
        assert out2["rules"][rule]["demotes"] is True
    assert out2["rules"]["A"]["labels"]["F1"] == rs.DISAGREE


def test_rule_a_matches_phrasing_agreement_rule_a():
    cells, rec = rw.simulate(16, 12, _probs_for(0.0, 0.0), seed=8)
    base = rs.phrasing_agreement_rule_a(rec, cells)
    out = rs.phrasing_agreement_rules(rec, cells)
    for f in ("F1", "F2", "F3"):
        assert (out["rules"]["A"]["labels"][f] == rs.AGREE) == bool(base[f"phrasing_by_role_{f}"]["agree"])


def test_two_phrasings_required():
    cells, rec = rw.simulate(6, 4, _probs_for(0.0, 0.0), seed=1)
    with pytest.raises(ValueError):
        rs.phrasing_agreement_rules(rec, cells, phrasings=(0, 1, 2))


def test_simulation_script_point_is_deterministic():
    import importlib.util
    path = Path(__file__).resolve().parents[2] / "scripts" / "v2" / "s189_phrasing_agreement_power.py"
    spec = importlib.util.spec_from_file_location("s189", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    args = ("W2", 30, 8, "default_0.58", 0.2, 0.0, 200)
    r1, r2 = mod.evaluate_point(args), mod.evaluate_point(args)
    assert r1 == r2
    assert r1["rules"]["B"]["p_demonstrated_relevant"] > 0.9  # F1 0.2 vs 0 at J = 30 is found
    w0 = mod.evaluate_point(("W0", 30, 40, "default_0.58", 0.2, 0.0, 200))
    assert w0["rules"]["C"]["p_correct"] > 0.9
