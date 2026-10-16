"""Tests for the Stage 14.2 / X02 base-rotation attack.

Includes the executable unit test for the CM_B_UM_059 example required by v2 B1.3 (p.8), computed from
the committed raw per-prompt records, and property tests for the structural identities of a base-relative
label.
"""

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
    spec = importlib.util.spec_from_file_location(
        "x02_base_rotation", REPO_ROOT / "scripts/v2/x02_base_rotation.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


x02 = _load()

PLAN_QWEN_059 = {0: -45.53125, 1: -55.5625, 2: -45.0, 3: -46.46875}


def test_cm_b_um_059_matches_the_plan_example_from_raw_records():
    grouped = x02.load_values(REPO_ROOT / x02.INPUTS["prompt_records"])
    raw = grouped[(x02.QWEN, "CM_B_UM_059")]
    assert {k: raw[k] for k in range(4)} == PLAN_QWEN_059
    row = x02.rotation_row({k: float(v) for k, v in raw.items()})
    # v2 B1.3: base 0 gives about +10.031, base 1 about -9.093 (signed form), range 10.562.
    assert row["S_plan_b0"] == pytest.approx(10.03125)
    assert row["S_plan_b1"] == pytest.approx(-9.09375)
    assert row["range"] == pytest.approx(10.5625)
    # The repo's form is clamped at zero, so it gives 0.0 at base 1 (journal J14.0-003).
    assert row["S_repo_b1"] == 0.0
    # The 0.5-nat label flips with the base although the underlying values are unchanged.
    assert [row[f"y_b{b}"] for b in range(4)] == [1, 0, 1, 1]
    assert row["label_differs_from_base0"] == 1
    assert row["range_label"] == 1


def test_labels_are_identical_under_the_two_legacy_forms():
    generator = np.random.default_rng(3)
    for _ in range(500):
        values = {b: float(v) for b, v in enumerate(generator.normal(-30, 5, 4))}
        x02.rotation_row(values)  # raises AssertionError if any label differs between the forms


def test_structural_identities_hold_for_random_families():
    generator = np.random.default_rng(5)
    rows = []
    for _ in range(400):
        values = {b: float(v) for b, v in enumerate(generator.normal(-30, 0.6, 4))}
        rows.append(x02.rotation_row(values))
    identities = x02.structural_identities(rows)
    assert identities["no_family_positive_under_all_four_bases"]
    assert identities["lowest_variant_as_base_is_always_negative"]
    assert identities["base_dependent_set_equals_range_positive_set"]
    assert identities["families_positive_at_base0_but_range_negative"] == 0


def test_a_flat_family_is_negative_under_every_base():
    row = x02.rotation_row({0: -20.0, 1: -20.1, 2: -20.2, 3: -20.3})
    assert row["n_positive_bases"] == 0
    assert row["range_label"] == 0
    assert row["label_stable"] == 1


def test_reclassification_matrix_accounts_for_every_family():
    rows = []
    generator = np.random.default_rng(9)
    for _ in range(60):
        values = {b: float(v) for b, v in enumerate(generator.normal(-30, 1.0, 4))}
        rows.append(x02.rotation_row(values))
    for base in (1, 2, 3):
        matrix = x02.reclassification(rows, base)
        assert sum(matrix.values()) == 60
        assert matrix["pos_to_pos"] + matrix["pos_to_neg"] == sum(r["y_b0"] for r in rows)


def test_a_family_with_a_missing_log_probability_is_not_evaluated_not_zero():
    grouped = {(x02.QWEN, "F1"): {0: -1.0, 1: None, 2: -2.0, 3: -3.0}}
    meta = {"F1": {"cue_type": "irrelevant_variable", "domain": "mechanics", "governing_law": "x"}}
    rows = x02.build_rows(grouped, meta, {"F1": "1 m"})
    qwen = next(r for r in rows if r["model"] == x02.QWEN)
    assert qwen["status"] == "NOT_EVALUATED"
    assert "S_repo_b0" not in qwen and "y_b0" not in qwen
    llama = next(r for r in rows if r["model"] == x02.LLAMA)
    assert llama["status"] == "NOT_EVALUATED"  # no records at all


def test_main_refuses_to_reuse_a_non_empty_attempt_directory(tmp_path, monkeypatch):
    attempt = tmp_path / "attempt_x"
    attempt.mkdir()
    (attempt / "keep.txt").write_text("existing evidence", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["x02", "--out-root", str(tmp_path), "--attempt-id", "attempt_x"])
    assert x02.main() == 2
    assert (attempt / "keep.txt").read_text(encoding="utf-8") == "existing evidence"


def test_end_to_end_on_committed_records(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x02", "--out-root", str(tmp_path), "--attempt-id", "t1"])
    assert x02.main() == 0
    result = json.loads((tmp_path / "t1" / "summary.json").read_text(encoding="utf-8"))
    per_model = result["summary"]["per_model"]
    qwen, llama = per_model[x02.QWEN], per_model[x02.LLAMA]
    # Legacy base-0 positives reproduce the Stage 14.1 counts (70 and 32 at 0.5 nat).
    assert qwen["overall"]["positive_under_base0"] == 70
    assert llama["overall"]["positive_under_base0"] == 32
    assert qwen["n_evaluated"] == 140 and not qwen["not_evaluated"]
    for model in (qwen, llama):
        identities = model["structural_identities"]
        assert identities["no_family_positive_under_all_four_bases"]
        assert identities["base_dependent_set_equals_range_positive_set"]
        assert identities["families_positive_at_base0_but_range_negative"] == 0
        assert model["overall"]["robust_positive_all_four_bases"] == 0
    assert result["summary"]["cross_model"]["shared_positive_by_base"]["base0"] == 22
    checks = result["plan_example"]["matches_plan_at_reported_precision"]
    assert checks["base0_signed"] and checks["base1_signed"] and checks["symmetric_range"]
    assert all(checks["gold_logprobs"])
    audit = (tmp_path / "t1" / "base_permutation_audit.csv").read_text(encoding="utf-8").splitlines()
    assert len(audit) == 1 + 280  # header + 140 families x 2 models
