"""Tests for the Stage 14.9 dtype-noise and anchor-matched analysis, on synthetic runs with known answers."""

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
    spec = importlib.util.spec_from_file_location("s149", REPO_ROOT / "scripts/v2/s149_noise_and_anchor_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s149 = _load()
s148 = s149.s148
MODEL = "M/test"
NEAR, FAR = s148.NEAR, s148.FAR


def rec(structure, cell, gold, decoy=None, decoy_anchor=None, gen=5.0, label="wrong", instance=0):
    alt = None
    if decoy is not None:
        alt = {"decoy": {"status": "OK", "logprob_raw": decoy},
               "decoy_under_anchor_prompt": None if decoy_anchor is None else {"status": "OK", "logprob_raw": decoy_anchor}}
    return {"model_id": MODEL, "structure_id": structure, "instance": instance, "cell_id": cell, "status": "OK",
            "job_id": f"m:{structure}:{instance}:{cell}", "gold_logprob_raw": gold, "gold_value": 10.0,
            "cue_numeric_value": None, "alternative_scores": alt, "parse_status": "PARSED",
            "parsed_answer": {"value": gen, "unit": "m"}, "correctness": label}


def run(noise_near=0.0):
    rows = []
    for s, g0 in (("S1", -10.0), ("S2", -20.0), ("S3", -30.0)):
        rows += [rec(s, "no_cue", g0),
                 rec(s, NEAR, g0 + 2.0 + noise_near, decoy=-5.0, decoy_anchor=-9.0),
                 rec(s, FAR, g0 + 0.5, decoy=-8.0, decoy_anchor=-8.5),
                 rec(s, "nongov_incompatible_unit_near", g0 - 1.0, decoy=-12.0, decoy_anchor=-11.0)]
    return rows


def test_anchor_shifts_are_the_change_of_gold_and_decoy_from_the_no_cue_prompt():
    shifts = s149.anchor_shifts(run())
    near = shifts[("S2", 0, NEAR)]
    assert near["gold_shift"] == pytest.approx(2.0) and near["decoy_shift"] == pytest.approx(4.0)
    assert near["r_alt_shift"] == pytest.approx(-2.0)  # (gold - decoy) shifts from -11 + ... : +2 gold, +4 decoy
    far = shifts[("S2", 0, FAR)]
    assert far["r_alt_shift"] == pytest.approx(0.5 - 0.5)
    incompat = shifts[("S2", 0, "nongov_incompatible_unit_near")]
    assert incompat["r_alt_shift"] == pytest.approx(-1.0 - (-1.0))
    # No-cue records have no decoy and produce no shift; a missing anchor-prompt score is dropped, never zero.
    assert not [k for k in shifts if k[2] == "no_cue"]
    broken = run()
    broken[1]["alternative_scores"]["decoy_under_anchor_prompt"] = None
    assert ("S1", 0, NEAR) not in s149.anchor_shifts(broken)


def test_anchor_summary_is_by_structure_with_a_deterministic_bootstrap_and_cell_differences():
    summary = s149.anchor_summary(s149.anchor_shifts(run()), np.random.default_rng(42))
    near = summary[f"r_alt_shift[{NEAR}]"]
    assert near["n_structures"] == 3 and near["mean"] == pytest.approx(-2.0) and near["n_negative"] == 3
    diff = summary[f"r_alt_shift[{NEAR}] - r_alt_shift[{FAR}]"]
    assert diff["mean"] == pytest.approx(-2.0)
    assert summary == s149.anchor_summary(s149.anchor_shifts(run()), np.random.default_rng(42))
    empty = summary["gold_shift[nongov_same_unit_moderate]"]
    assert empty["n_structures"] == 0 and empty["ci95"] is None


def test_dtype_noise_is_the_per_record_difference_of_the_gold_log_probability():
    rows, stats = s149.paired_gold_deltas(run(), run(noise_near=0.1))
    assert len(rows) == 12
    d = stats["gold_logprob_difference"]
    assert d["n"] == 12 and d["max_abs"] == pytest.approx(0.1) and d["mean"] == pytest.approx(-0.1 * 3 / 12)
    assert d["median_abs"] == 0.0
    agreement = stats["generation_agreement"]
    assert agreement["same_parsed_answer"] == agreement["n_both_parsed"] == 12
    assert agreement["unmatched_first"] == agreement["unmatched_second"] == 0
    assert s149.abs_stats([])["status"].startswith("NOT_EVALUATED")


def test_a_changed_generation_or_label_is_counted_as_disagreement():
    changed = run()
    changed[0]["parsed_answer"] = {"value": 6.0, "unit": "m"}
    changed[1]["correctness"] = "correct"
    _, stats = s149.paired_gold_deltas(run(), changed)
    agreement = stats["generation_agreement"]
    assert agreement["same_parsed_answer"] == 11 and agreement["same_correctness_label"] == 11


def test_contrast_noise_reads_each_contrast_against_its_own_dtype_difference():
    noise = s149.contrast_noise(run(), run(noise_near=0.1), MODEL)
    near_vs_anchor = noise[f"gold_lp[{NEAR}] - gold_lp[no_cue]"]
    assert near_vs_anchor["n"] == 3 and near_vs_anchor["p95_abs"] == pytest.approx(0.1)
    assert near_vs_anchor["sd"] == pytest.approx(0.0, abs=1e-12)
    far_vs_anchor = noise[f"gold_lp[{FAR}] - gold_lp[no_cue]"]
    assert far_vs_anchor["max_abs"] == 0.0


def test_main_writes_outputs_pairs_runs_by_dtype_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    def write(name, rows, dtype):
        directory = tmp_path / name
        directory.mkdir()
        (directory / "raw_records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        (directory / "run_summary.json").write_text(json.dumps({"model_key": "qwen_primary", "dtype": dtype}), encoding="utf-8")
        return str(directory / "raw_records.jsonl")

    bf16, fp32 = write("bf16", run(), "bfloat16"), write("fp32", run(noise_near=0.1), "float32")
    earlier = write("earlier", run(), "bfloat16")
    argv = ["s149", "--records", bf16, fp32, "--earlier-bf16", earlier, "--out-root", str(tmp_path / "out"), "--attempt-id", "t1"]
    monkeypatch.setattr(sys, "argv", argv)
    assert s149.main() == 0
    out = tmp_path / "out" / "t1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    model = summary["models"]["qwen_primary"]
    assert model["dtype_noise"]["gold_logprob_difference"]["n"] == 12
    assert model["reproducibility"]["gold_logprob_difference"]["max_abs"] == 0.0
    assert summary["evidence_class"].startswith("exploratory")
    text = (out / "report.md").read_text(encoding="utf-8")
    assert "nothing here is a confirmation" in text and "dtype noise" in text
    assert (out / "dtype_noise_by_record.csv").stat().st_size > 0 and (out / "anchor_shifts_by_item.csv").stat().st_size > 0
    monkeypatch.setattr(sys, "argv", argv)
    assert s149.main() == 2
