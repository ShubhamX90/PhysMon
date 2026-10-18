"""Tests for the Stage 14.10 X03 wrapper analysis, on synthetic runs with known shifts."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location("s150", REPO_ROOT / "scripts/v2/s150_x03_wrapper_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s150 = _load()
s148 = s150.s148
NEAR, FAR, INCOMPAT = s148.NEAR, s148.FAR, s148.INCOMPAT
MODEL = "M/test"


def rec(wrapper, structure, instance, cell, gold, decoy=None, decoy_anchor=None):
    alt = None
    if decoy is not None:
        alt = {"decoy": {"status": "OK", "logprob_raw": decoy},
               "decoy_under_anchor_prompt": {"status": "OK", "logprob_raw": decoy_anchor}}
    return {"model_id": MODEL, "answer_wrapper_id": wrapper, "structure_id": structure, "instance": instance,
            "cell_id": cell, "status": "OK", "job_id": f"m:{structure}:{instance}:{cell}:{wrapper}",
            "gold_logprob_raw": gold, "gold_value": 10.0, "cue_numeric_value": None, "alternative_scores": alt,
            "parse_status": "PARSED", "parsed_answer": {"value": 5.0, "unit": "m"}, "correctness": "wrong",
            "target_answer_ids": [1, 2, 3, 4]}


def run(near_decoy_shift: dict[str, float]):
    """Gold shifts +2 under every wrapper; the near-cell decoy shift differs by wrapper, so R_alt shift = 2 - decoy shift."""

    rows = []
    for wrapper, decoy_shift in near_decoy_shift.items():
        for s, g0 in (("S1", -10.0), ("S2", -20.0), ("S3", -30.0)):
            for i in (0, 1):
                rows += [rec(wrapper, s, i, "no_cue", g0),
                         rec(wrapper, s, i, NEAR, g0 + 2.0, decoy=-5.0, decoy_anchor=-5.0 - decoy_shift),
                         rec(wrapper, s, i, FAR, g0 + 0.5, decoy=-8.0, decoy_anchor=-8.5),
                         rec(wrapper, s, i, INCOMPAT, g0 - 1.0, decoy=-12.0, decoy_anchor=-11.0)]
    return rows


def test_a_wrapper_with_a_much_larger_near_shift_dominates_and_a_tiny_difference_does_not():
    rows = run({"answer_line": 4.0, "boxed": 7.0, "json": 4.1})
    result = s150.analyse_model(rows, np.random.default_rng(42))
    wr = result["wrappers"]
    assert wr["answer_line"]["shift_by_structure"][NEAR]["mean"] == pytest.approx(-2.0)
    assert wr["boxed"]["shift_by_structure"][NEAR]["mean"] == pytest.approx(-5.0)
    boxed = wr["boxed"]["interaction_vs_reference"][NEAR]
    assert boxed["mean"] == pytest.approx(-3.0) and boxed["n_structures"] == 3
    assert wr["boxed"]["near_cell_verdict"] == {"excludes_zero": True, "dominates": True, "status": "evaluated"}
    # json differs by 0.1 nats: its (degenerate) interval excludes zero but the size is far below half of the 2-nat reference.
    assert wr["json"]["near_cell_verdict"]["excludes_zero"] is True and wr["json"]["near_cell_verdict"]["dominates"] is False
    assert result["overall"]["wrappers_that_dominate"] == ["boxed"] and result["overall"]["invariance"] is False
    assert "interaction_vs_reference" in wr["json"] and wr["answer_line"]["interaction_vs_reference"] == {}


def test_identical_wrappers_are_invariant_and_nothing_dominates():
    result = s150.analyse_model(run({"answer_line": 4.0, "plain": 4.0}), np.random.default_rng(42))
    v = result["wrappers"]["plain"]["near_cell_verdict"]
    assert v["excludes_zero"] is False and v["dominates"] is False
    assert result["overall"]["invariance"] is True and result["overall"]["wrappers_that_dominate"] == []


def test_classify_applies_the_frozen_rule_and_reports_not_evaluated_without_data():
    assert s150.classify({"ci95": [0.5, 2.0], "mean": 1.0}, 2.0)["dominates"] is True  # exactly half the reference
    assert s150.classify({"ci95": [0.5, 2.0], "mean": 0.9}, 2.0)["dominates"] is False  # below half
    assert s150.classify({"ci95": [-1.0, 2.0], "mean": 1.5}, 2.0) == {"excludes_zero": False, "dominates": False, "status": "evaluated"}
    assert s150.classify({"ci95": None, "mean": None}, 2.0)["status"] == "NOT_EVALUATED"
    assert s150.classify({"ci95": [1, 2], "mean": 1.5}, None)["status"] == "NOT_EVALUATED"


def test_parse_and_correctness_counts_and_answer_length_are_reported_per_wrapper():
    rows = run({"answer_line": 4.0, "boxed": 4.0})
    for r in rows:
        if r["answer_wrapper_id"] == "boxed" and r["cell_id"] == FAR:
            r["parse_status"], r["parsed_answer"], r["correctness"] = "UNPARSEABLE", None, "UNPARSEABLE"
    result = s150.analyse_model(rows, np.random.default_rng(42))
    boxed = result["wrappers"]["boxed"]
    assert boxed["n_records"] == 24 and boxed["n_parsed"] == 18
    assert boxed["parse_status_counts"] == {"PARSED": 18, "UNPARSEABLE": 6}
    assert boxed["mean_gold_answer_tokens"] == 4.0
    assert result["wrappers"]["answer_line"]["n_parsed"] == 24


def test_main_writes_outputs_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    records = tmp_path / "raw_records.jsonl"
    records.write_text("".join(json.dumps(r) + "\n" for r in run({"answer_line": 4.0, "boxed": 7.0})), encoding="utf-8")
    argv = ["s150", "--records", str(records), "--out-root", str(tmp_path / "out"), "--attempt-id", "t1"]
    monkeypatch.setattr(sys, "argv", argv)
    assert s150.main() == 0
    out = tmp_path / "out" / "t1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["models"][MODEL]["overall"]["wrappers_that_dominate"] == ["boxed"]
    assert summary["evidence_class"].startswith("exploratory")
    text = (out / "report.md").read_text(encoding="utf-8")
    assert "nothing here is a confirmation" in text and "frozen in J14.10-001" in text
    assert (out / "wrapper_minus_reference_shift.csv").stat().st_size > 0
    monkeypatch.setattr(sys, "argv", argv)
    assert s150.main() == 2
