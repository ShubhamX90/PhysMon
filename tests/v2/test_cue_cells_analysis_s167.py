"""Stage 14.20: the cue-cell analysis on synthetic records (no model, no GPU)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location("s167", Path(__file__).resolve().parents[2] / "scripts/v2/s167_cue_cells_analysis.py")
s167 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s167)


def rec(s, correctness, role=None, tokens=100, conv=None):
    return {"structure_id": s, "instance": 0, "correctness": correctness, "cue_semantic_role": role, "n_generated_tokens": tokens,
            "correct_if_units_convertible": conv, "expected_effect": "invariant"}


def test_contrast_and_not_evaluated_are_separate():
    anchors = [f"S{i:02d}:0" for i in range(1, 7)]
    base = [rec(f"S{i:02d}", "correct") for i in range(1, 7)]
    cells = [rec(f"S{i:02d}", "wrong", "irrelevant_text") for i in range(1, 7)] + [rec("S01", "TRUNCATED", "irrelevant_text", 12288)]
    res = s167.analyse(base, cells, anchors, np.random.default_rng(1))
    role = res["roles"]["irrelevant_text"]
    assert role["contrast_vs_baseline"]["mean"] == -1.0
    assert role["outcomes"]["n_not_evaluated"] == 1 and role["outcomes"]["share_truncated"] == 1 / 7
    assert role["reading"] == "distinguishable from sampling noise"


def test_all_ungraded_structure_is_dropped_not_zero():
    anchors = ["S01:0", "S02:0", "S03:0"]
    base = [rec(s, "correct") for s in ("S01", "S02", "S03")]
    cells = [rec("S01", "correct", "role_reversed"), rec("S02", "correct", "role_reversed"), rec("S03", "TRUNCATED", "role_reversed")]
    role = s167.analyse(base, cells, anchors, np.random.default_rng(1))["roles"]["role_reversed"]
    assert role["n_paired_structures"] == 2 and role["contrast_vs_baseline"]["mean"] == 0.0
    assert role["reading"] == "not distinguishable from sampling noise"


def test_convertible_sensitivity_and_anchor_restriction():
    anchors = ["S01:0", "S02:0"]
    base = [rec("S01", "correct"), rec("S02", "correct"), rec("S09", "wrong")]
    cells = [rec("S01", "wrong", "irrelevant_metadata", conv=True), rec("S02", "correct", "irrelevant_metadata"), rec("S09", "wrong", "irrelevant_metadata")]
    declared = s167.analyse(base, cells, anchors, np.random.default_rng(1), False)
    loose = s167.analyse(base, cells, anchors, np.random.default_rng(1), True)
    assert declared["n_cell_records"] == 2 and declared["roles"]["irrelevant_metadata"]["cue_correct_share_by_structure"]["mean"] == 0.5
    assert loose["roles"]["irrelevant_metadata"]["cue_correct_share_by_structure"]["mean"] == 1.0
