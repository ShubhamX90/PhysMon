"""Tests for the Stage 14.13 reasoning analysis on synthetic records with known answers."""

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
    spec = importlib.util.spec_from_file_location("s153", REPO_ROOT / "scripts/v2/s153_reasoning_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s153 = _load()
s148 = s153.s148
NEAR, FAR = s148.NEAR, s148.FAR
MODEL = "M/test"


def rec(structure, instance, cell, label, gen=None, cue=None, status="OK", tokens=100, parse=None):
    parse = parse or ("PARSED" if label in ("correct", "wrong") else label)
    return {"model_id": MODEL, "structure_id": structure, "instance": instance, "cell_id": cell, "status": status,
            "correctness": label, "parse_status": parse, "cue_numeric_value": cue, "n_generated_tokens": tokens,
            "parsed_answer": None if gen is None else {"value": gen, "unit": "m"}}


def run(anchor_correct=True):
    """Ten structures x two instantiations; the near cell flips to wrong in half of the base-correct items, the far cell never."""

    rows = []
    for s in range(10):
        for i in (0, 1):
            sid = f"S{s:02d}"
            rows.append(rec(sid, i, "no_cue", "correct" if anchor_correct else "wrong"))
            rows.append(rec(sid, i, NEAR, "wrong" if i == 0 else "correct", gen=2.17 if i == 0 else 5.0, cue=2.17))
            rows.append(rec(sid, i, FAR, "correct", gen=5.0, cue=10.9))
            rows.append(rec(sid, i, "relevant_edit", "correct"))
    return rows


def test_gate_met_gives_flip_shares_by_structure_with_a_cluster_bootstrap():
    result = s153.analyse_model(run(), np.random.default_rng(42))
    assert result["gate_met"] is True and result["eligibility"]["base_correct_anchors"] == 20
    near = result["correctness_transitions"][f"flip_to_wrong_given_base_correct[{NEAR}]"]
    assert near["n_graded"] == 20 and near["n_hit"] == 10 and near["n_structures"] == 10
    assert near["mean"] == pytest.approx(0.5) and near["ci95"] == [pytest.approx(0.5), pytest.approx(0.5)]
    far = result["correctness_transitions"][f"flip_to_wrong_given_base_correct[{FAR}]"]
    assert far["n_hit"] == 0 and far["mean"] == 0.0
    # No anchor is wrong, so the reverse transition has no graded item: NOT_EVALUATED, never 0.
    rescue = result["correctness_transitions"][f"rescue_to_correct_given_base_wrong[{NEAR}]"]
    assert rescue["n_graded"] == 0 and rescue["mean"] is None and rescue["ci95"] is None


def test_the_gate_below_eight_base_correct_anchors_makes_the_endpoint_not_evaluated():
    result = s153.analyse_model(run(anchor_correct=False), np.random.default_rng(42))
    assert result["gate_met"] is False and result["eligibility"]["base_correct_anchors"] == 0
    assert isinstance(result["correctness_transitions"], str) and result["correctness_transitions"].startswith("NOT_EVALUATED")
    assert "floor persists" in result["correctness_transitions"]
    # With exactly eight correct anchors the gate is met.
    rows = run(anchor_correct=False)
    flipped = 0
    for r in rows:
        if r["cell_id"] == "no_cue" and flipped < 8:
            r["correctness"], flipped = "correct", flipped + 1
    assert s153.analyse_model(rows, np.random.default_rng(42))["gate_met"] is True


def test_ungraded_outcomes_are_in_neither_the_numerator_nor_the_denominator_and_are_counted():
    rows = run()
    for r in rows:
        if r["cell_id"] == NEAR and r["structure_id"] == "S00":
            r["correctness"], r["parse_status"], r["parsed_answer"] = "TRUNCATED", "TRUNCATED", None
    result = s153.analyse_model(rows, np.random.default_rng(42))
    near = result["correctness_transitions"][f"flip_to_wrong_given_base_correct[{NEAR}]"]
    assert near["n_not_graded"] == 2 and near["n_graded"] == 18 and near["n_hit"] == 9
    outcomes = result["cell_outcomes"][NEAR]
    assert outcomes["parse_status_counts"]["TRUNCATED"] == 2 and outcomes["n_graded"] == 18


def test_copy_rate_and_relevant_edit_assay_and_duplicates():
    result = s153.analyse_model(run(), np.random.default_rng(42))
    copies = result["copy_rate_of_cue_numeral"]
    assert copies[NEAR]["n_equal_to_cue_numeral"] == 10 and copies[NEAR]["n_parsed"] == 20 and copies[FAR]["n_equal_to_cue_numeral"] == 0
    assert result["relevant_edit_assay"]["n_correct_under_edit"] == 20
    rows = run()
    with pytest.raises(ValueError, match="duplicate"):
        s153.index(rows + [rows[0]])


def test_main_writes_outputs_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    records = tmp_path / "raw_records.jsonl"
    records.write_text("".join(json.dumps(r) + "\n" for r in run()), encoding="utf-8")
    argv = ["s153", "--records", str(records), "--out-root", str(tmp_path / "out"), "--attempt-id", "t1"]
    monkeypatch.setattr(sys, "argv", argv)
    assert s153.main() == 0
    out = tmp_path / "out" / "t1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["gate_min_base_correct"] == 8 and summary["evidence_class"].startswith("exploratory")
    text = (out / "report.md").read_text(encoding="utf-8")
    assert "nothing here is a confirmation" in text and "J14.13-002" in text
    assert (out / "cell_outcomes.csv").stat().st_size > 0
    monkeypatch.setattr(sys, "argv", argv)
    assert s153.main() == 2
