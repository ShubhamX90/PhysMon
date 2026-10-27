"""Tests for the Stage 14.20 thinking-run analysis on synthetic records with known outcomes."""

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
    spec = importlib.util.spec_from_file_location("s165", REPO_ROOT / "scripts/v2/s165_thinking_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s165 = _load()


def rec(structure, instance, sample, correctness, parse="PARSED", tokens=1000, closed=True, wall=10.0):
    return {"structure_id": structure, "instance": instance, "sample_index": sample, "correctness": correctness, "parse_status": parse,
            "n_generated_tokens": tokens, "thinking_closed": closed, "wall_time": wall, "batch_size": 2, "model_id": "Qwen/Qwen3-32B",
            "sampling": {"do_sample": True, "temperature": 0.6, "top_p": 0.95, "top_k": 20}}


def build():
    records = []
    records += [rec("S1", 0, k, "correct") for k in range(4)]  # consistent anchor
    records += [rec("S2", 0, k, "correct" if k < 2 else "wrong") for k in range(4)]  # unstable
    records += [rec("S3", 0, k, "wrong") for k in range(4)]  # failed
    records += [rec("S4", 0, k, "correct") for k in range(3)] + [rec("S4", 0, 3, "TRUNCATED", parse="TRUNCATED", tokens=8192, closed=False)]  # incomplete
    records += [rec("S5", 0, k, "correct") for k in range(3)]  # too few samples
    dataset = [{"structure_id": s, "instance": 0, "level": lv, "domain": dm}
               for s, lv, dm in (("S1", "high_school", "mechanics"), ("S2", "high_school", "mechanics"), ("S3", "intro_university", "optics"),
                                 ("S4", "intro_university", "optics"), ("S5", "upper_university", "quantum"))]
    return records, dataset


def test_problems_are_classified_by_their_samples_and_ungraded_outcomes_are_never_wrong():
    records, _ = build()
    classes = {k: p["class"] for k, p in s165.per_problem(records, 4).items()}
    assert classes == {"S1:0": "CONSISTENT_ANCHOR", "S2:0": "UNSTABLE", "S3:0": "FAILED", "S4:0": "INCOMPLETE", "S5:0": "INCOMPLETE"}
    s4 = s165.per_problem(records, 4)["S4:0"]
    assert s4["n_graded"] == 3 and s4["n_correct"] == 3  # the truncated sample is not counted as wrong
    assert s165.per_problem(records, 3)["S5:0"]["class"] == "CONSISTENT_ANCHOR"  # the sample threshold is a parameter


def test_throughput_and_outcomes_are_computed_from_the_records():
    records, _ = build()
    t = s165.throughput(records)
    assert t["n_records"] == 19 and t["generated_tokens_total"] == 18 * 1000 + 8192 and t["aggregate_tokens_per_s"] == pytest.approx((18000 + 8192) / 190.0, rel=1e-3)
    assert t["tokens_max"] == 8192 and t["batch_size"] == [2]
    o = s165.outcomes(records)
    assert o["parse_status"]["TRUNCATED"] == 1 and o["truncated_share"] == pytest.approx(1 / 19) and o["thinking_closed_share"] == pytest.approx(18 / 19)
    assert o["n_graded"] == 18 and o["n_correct"] == 12 and o["correct_share_of_graded"] == pytest.approx(12 / 18)
    assert o["correct_share_of_all"] == pytest.approx(12 / 19)


def test_the_anchor_gate_needs_enough_structures_and_says_not_evaluated_below_it():
    records, dataset = build()
    result = s165.analyse(records, dataset, 4, np.random.default_rng(1))
    assert result["anchors"]["keys"] == ["S1:0"] and result["anchors"]["n_structures"] == 1
    assert result["anchors"]["distractor_endpoint"].startswith("NOT_EVALUATED")
    many = [rec(f"T{i}", 0, k, "correct") for i in range(20) for k in range(4)]
    meta = [{"structure_id": f"T{i}", "instance": 0, "level": "high_school", "domain": "mechanics"} for i in range(20)]
    assert s165.analyse(many, meta, 4, np.random.default_rng(1))["anchors"]["distractor_endpoint"] == "estimable"


def test_levels_and_domains_are_summarised_by_structure_and_a_single_structure_group_is_not_evaluated():
    records, dataset = build()
    result = s165.analyse(records, dataset, 4, np.random.default_rng(1))
    mech = result["by_domain"]["mechanics"]
    assert mech["n_problems"] == 2 and mech["classes"] == {"CONSISTENT_ANCHOR": 1, "UNSTABLE": 1}
    assert mech["correct_rate_by_structure"]["mean"] == pytest.approx((1.0 + 0.5) / 2) and mech["correct_rate_by_structure"]["n_structures"] == 2
    assert result["by_domain"]["quantum"]["correct_rate_by_structure"]["status"] == "NOT_EVALUATED"
    assert result["by_level"]["high_school"]["n_problems"] == 2
    assert result["overall_correct_rate_by_structure"]["n_structures"] == 5


def test_main_writes_the_report_the_anchors_file_and_the_summary_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    records, dataset = build()
    run = tmp_path / "run"
    run.mkdir()
    (run / "raw_records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    ds = tmp_path / "dataset.jsonl"
    ds.write_text("".join(json.dumps(d) + "\n" for d in dataset), encoding="utf-8")
    monkeypatch.setattr(s165, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["s165", "--records", str(run / "raw_records.jsonl"), "--dataset", "dataset.jsonl", "--out-root", "out", "--attempt-id", "a1"])
    assert s165.main() == 0
    out = tmp_path / "out" / "a1"
    assert json.loads((out / "Qwen_Qwen3-32B_anchors.json").read_text(encoding="utf-8")) == ["S1:0"]
    report = (out / "Qwen_Qwen3-32B_report.md").read_text(encoding="utf-8")
    assert "not paper-eligible" in report and "NOT_EVALUATED" in report
    assert "models" in json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert s165.main() == 2
