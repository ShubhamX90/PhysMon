"""Tests for the Stage 14.12 copying-versus-relevance analysis on synthetic records with known answers."""

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
    spec = importlib.util.spec_from_file_location("s151", REPO_ROOT / "scripts/v2/s151_copying_vs_relevance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s151 = _load()
s148 = s151.s148
NEAR, INCOMPAT = s148.NEAR, s148.INCOMPAT
MODEL = "M/test"


def rec(structure, cell, gold, decoy=None, decoy_anchor=None, cue=None, gen=None, gold_value=10.0, label="wrong", instance=0):
    alt = None
    if decoy is not None:
        alt = {"decoy": {"status": "OK", "logprob_raw": decoy},
               "decoy_under_anchor_prompt": {"status": "OK", "logprob_raw": decoy_anchor}}
    return {"model_id": MODEL, "structure_id": structure, "instance": instance, "cell_id": cell, "status": "OK",
            "job_id": f"m:{structure}:{instance}:{cell}", "gold_logprob_raw": gold, "gold_value": gold_value,
            "cue_numeric_value": cue, "alternative_scores": alt,
            "parse_status": "PARSED" if gen is not None else "UNPARSEABLE",
            "parsed_answer": None if gen is None else {"value": gen, "unit": "m"}, "correctness": label}


def run(near_cue=2.17, incompat_cue=2.17):
    rows = []
    for s, g0 in (("S1", -10.0), ("S2", -20.0), ("S3", -30.0)):
        rows += [rec(s, "no_cue", g0, gen=5.0),
                 rec(s, NEAR, g0 + 1.0, decoy=-4.0, decoy_anchor=-14.0, cue=near_cue, gen=near_cue),   # decoy +10, gold +1
                 rec(s, INCOMPAT, g0 + 1.0, decoy=-11.0, decoy_anchor=-14.0, cue=incompat_cue, gen=5.0),  # decoy +3, gold +1
                 rec(s, "role_reversal", g0, cue=2.83, gen=-0.17, gold_value=-0.65, label="wrong")]
    return rows


def test_unit_modulation_is_the_difference_of_shifts_between_two_cells_with_the_same_strings():
    result = s151.unit_modulation(run(), np.random.default_rng(42))
    assert result["n_items_excluded"] == 0
    assert result["decoy_shift"]["mean"] == pytest.approx(7.0) and result["decoy_shift"]["n_structures"] == 3
    assert result["gold_shift"]["mean"] == pytest.approx(0.0)
    assert result["r_alt_shift"]["mean"] == pytest.approx(-7.0)  # (gold - decoy) shift differs by gold 0 minus decoy 7
    assert result["decoy_shift"]["ci95"] == [pytest.approx(7.0), pytest.approx(7.0)]


def test_items_whose_cue_numerals_differ_are_excluded_and_counted_never_compared():
    result = s151.unit_modulation(run(incompat_cue=3.1), np.random.default_rng(42))
    assert result["n_items_excluded"] == 3
    assert result["decoy_shift"]["n_structures"] == 0 and result["decoy_shift"]["ci95"] is None


def test_copy_rates_count_generations_equal_to_the_cue_numeral_among_parsed_ones():
    rates = s151.copy_rates(run())
    assert rates[NEAR]["n_parsed"] == 3 and rates[NEAR]["n_equal_to_cue_numeral"] == 3
    assert rates[INCOMPAT]["n_equal_to_cue_numeral"] == 0
    assert rates[NEAR]["wilson95"][0] > 0.3 and rates[NEAR]["wilson95"][1] == pytest.approx(1.0)
    assert "no_cue" not in rates  # no cue numeral, so no copy rate is defined
    rows = run()
    rows[1]["parse_status"], rows[1]["parsed_answer"] = "UNPARSEABLE", None
    assert s151.copy_rates(rows)[NEAR]["n_parsed"] == 2


def test_wilson_interval_handles_the_edges_and_empty_input():
    assert s151.wilson(0, 0) is None
    low, high = s151.wilson(0, 10)
    assert low == 0.0 and 0.2 < high < 0.35
    low, high = s151.wilson(5, 10)
    assert low < 0.5 < high


def test_role_reversal_reports_copy_correct_and_sign_and_states_it_is_not_a_matched_control():
    result = s151.role_reversal(run())
    assert result["n_records"] == result["n_parsed"] == 3 and result["n_equal_to_cue_numeral"] == 0
    assert result["n_with_the_sign_of_the_gold"] == 3 and result["gold_is_negative_in"] == 3
    assert "not comparable" in result["limit"]


def test_main_writes_outputs_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    records = tmp_path / "raw_records.jsonl"
    records.write_text("".join(json.dumps(r) + "\n" for r in run()), encoding="utf-8")
    argv = ["s151", "--records", str(records), "--out-root", str(tmp_path / "out"), "--attempt-id", "t1"]
    monkeypatch.setattr(sys, "argv", argv)
    assert s151.main() == 0
    out = tmp_path / "out" / "t1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert "matched relevant-role control" in summary["not_evaluated"]
    text = (out / "report.md").read_text(encoding="utf-8")
    assert "nothing here is a confirmation" in text and "Unit modulation" in text
    assert (out / "copy_rates.csv").stat().st_size > 0
    monkeypatch.setattr(sys, "argv", argv)
    assert s151.main() == 2
