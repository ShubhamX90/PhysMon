"""Tests for the Stage 15 batch-1 analyses on synthetic records (rules fixed before any real record exists)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("s176", REPO_ROOT / "scripts/v2/s176_batch1_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s176 = _load()


def rec(sid, inst, grade, status="COMPLETE", text="t", sample=0, level="high_school", domain="mechanics"):
    return {"structure_id": sid, "instance": inst, "cell_id": "no_cue", "grade_declared": grade, "completion_status": status,
            "generated_answer_raw": text, "sample_index": sample, "level": level, "domain": domain, "n_generated_tokens": 100,
            "grade_convertible": grade, "grade_rel1pct": grade, "o2_semantic_correct": grade}


def test_parity_passes_when_runs_agree_and_fails_on_a_systematic_gap():
    a = [rec(f"S{i}", 0, "correct" if i % 2 else "wrong") for i in range(40)]
    b = [rec(f"S{i}", 0, "correct" if i % 2 else "wrong", text="other") for i in range(40)]
    out = s176.parity(a, b)
    assert out["verdict"] == "PASS" and out["agreement_correctness"] == 1.0 and out["identical_text"] == 0.0
    worse = [rec(f"S{i}", 0, "wrong") for i in range(40)]
    assert s176.parity(a, worse)["verdict"] == "FAIL"
    assert s176.parity(a, [])["verdict"] == "NOT_EVALUATED"


def test_calibration_selects_on_samples_0_to_3_and_estimates_on_4_to_7():
    records = []
    for k in range(8):  # S1: correct on selection samples only -> in band by selection, estimate 0
        records.append(rec("S1", 0, "correct" if k in (0, 1) else "wrong", sample=k))
        records.append(rec("S2", 0, "correct", sample=k))  # always correct -> above the band
        records.append(rec("S3", 0, "wrong", status="BUDGET_EXHAUSTED" if k == 7 else "COMPLETE", sample=k))
    out = s176.calibration(records)
    s1 = out["per_structure"]["S1"]
    assert s1["selection_share"] == pytest.approx(0.5) and s1["estimation_share"] == 0.0 and s1["in_band"]
    assert not out["per_structure"]["S2"]["in_band"] and out["in_band"] == ["S1"]
    assert out["completion_status"]["BUDGET_EXHAUSTED"] == 1 and out["estimation_mean_in_band"] == 0.0
    assert out["by_group"]["level"]["high_school"]["n_structures"] == 3
