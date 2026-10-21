"""Tests for the Stage 14.17 plausibility-matched numeral-presence plan (tokenizers only; no model, no GPU, nothing submitted)."""

from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location("s159", REPO_ROOT / "scripts/v2/s159_matched_distance_plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s159 = _load()


def test_shape_distance_and_prefix_overlap_helpers():
    assert s159.shape_of("40.9") == (2, 1) and s159.shape_of("5") == (1, 0) and s159.shape_of("0.25") == (1, 2)
    assert abs(s159.log_distance(40.9, 40.82) - math.log(40.9 / 40.82)) < 1e-12
    assert s159.log_distance(0.0, 3.0) is None and s159.log_distance(3.0, 0.0) is None
    assert s159.log_distance(2.0, -4.0) == s159.log_distance(2.0, 4.0)  # a negative gold is compared by magnitude
    assert s159.prefix_overlap("40.9", 40.82) == 2 and s159.prefix_overlap("2.19", 2.1778) == 2 and s159.prefix_overlap("7", 2.1778) == 0


def test_matched_controls_have_the_same_shape_are_absent_and_lie_at_a_comparable_distance_from_the_gold():
    gold = 40.82
    present = {20.0, 5.0, 40.9, 9.8}
    found = s159.matched_controls("40.9", present, gold, random.Random("t"))
    assert found["controls"] and found["reason"] is None
    for c in found["controls"]:
        assert c["text"] != "40.9" and float(c["text"]) not in present
        assert s159.shape_of(c["text"]) == (2, 1)
        assert s159.log_distance(float(c["text"]), gold) >= s159.MIN_DISTANCE
        assert abs(math.log(c["ratio"])) <= math.log(found["factor"]) + 1e-9
        assert c["side"] in ("above", "below")


def test_two_controls_per_side_are_taken_when_both_sides_have_them():
    found = s159.matched_controls("212", {212.0}, 300.0, random.Random("u"))
    sides = [c["side"] for c in found["controls"]]
    assert sides.count("above") == sides.count("below") == s159.K_PER_SIDE


def test_a_numeral_that_is_a_correct_answer_or_has_no_control_is_reported_with_a_reason_and_never_matched_loosely():
    near = s159.matched_controls("2.178", {2.178}, 2.1778, random.Random("v"))
    assert near["controls"] == [] and "correct answer" in near["reason"]
    zero = s159.matched_controls("5", {5.0}, 0.0, random.Random("w"))
    assert zero["controls"] == [] and "zero" in zero["reason"]
    crowded = s159.matched_controls("3", {float(d) for d in range(1, 10)}, 5.0, random.Random("x"))
    assert crowded["controls"] == [] and "no numeral" in crowded["reason"]


def test_matching_is_deterministic_for_a_seed_and_does_not_start_a_number_with_a_new_leading_zero():
    a = s159.matched_controls("0.5", {0.5}, 0.9, random.Random("same"))
    b = s159.matched_controls("0.5", {0.5}, 0.9, random.Random("same"))
    assert a == b and a["controls"]
    c = s159.matched_controls("5", {5.0}, 0.9, random.Random("y"))
    assert all(not x["text"].startswith("0") for x in c["controls"])


def test_a_negative_gold_is_matched_by_magnitude():
    found = s159.matched_controls("3", {3.0}, -2.45, random.Random("neg"))
    assert found["controls"]
    for c in found["controls"]:
        assert s159.log_distance(float(c["text"]), -2.45) is not None


def test_the_plan_is_a_dry_run_with_unique_ids_and_controls_that_point_at_a_present_numeral(tmp_path, llama_tokenizer):
    argv = sys.argv
    sys.argv = ["s159", "--out-root", str(tmp_path), "--attempt-id", "p1", "--structures", "S06", "--models", "llama_primary"]
    try:
        assert s159.main() == 0
    finally:
        sys.argv = argv
    jobs = [json.loads(line) for line in (tmp_path / "p1" / "job_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    meta = json.loads((tmp_path / "p1" / "plan.json").read_text(encoding="utf-8"))
    assert meta["authorized_to_run"] is False and meta["data_role"] == "EXPLORATION" and "not run" in meta["evidence_class"]
    assert len({j["job_id"] for j in jobs}) == len(jobs) == meta["n_jobs"]
    assert all(j["decoy_text"] is None and j["true_gold_value"] == j["gold_value"] for j in jobs)
    by_prompt: dict = {}
    for j in jobs:
        by_prompt.setdefault((j["instance"], j["cell_id"]), []).append(j)
    for group in by_prompt.values():
        texts = {j["candidate_text"] for j in group if j["candidate_kind"] == "present"}
        for j in group:
            if j["candidate_kind"] == "matched_control":
                assert j["candidate_matched_to"] in texts and j["candidate_text"] not in texts
                assert j["control_side"] in ("above", "below") and j["own_distance"] >= s159.MIN_DISTANCE
    assert (tmp_path / "p1" / "unmatched_numerals.json").exists()


def test_the_plan_refuses_to_reuse_a_directory(tmp_path, llama_tokenizer, monkeypatch):
    used = tmp_path / "p2"
    used.mkdir()
    (used / "keep.txt").write_text("evidence", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["s159", "--out-root", str(tmp_path), "--attempt-id", "p2", "--structures", "S06", "--models", "llama_primary"])
    assert s159.main() == 2 and (used / "keep.txt").read_text(encoding="utf-8") == "evidence"
