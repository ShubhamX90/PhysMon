"""Tests for the Stage 14.14 numeral-presence plan (tokenizers only; no model, no GPU, nothing submitted)."""

from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location("s154", REPO_ROOT / "scripts/v2/s154_numeral_presence_plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s154 = _load()


def test_numerals_are_the_distinct_numbers_of_the_prompt_as_written_and_exclude_unit_exponents():
    prompt = "A capacitor of 20 μF is in series with a 5 kΩ resistor and a battery of 12 V; g = 9.8 m/s². After 0.5 s and 20 ms."
    assert s154.numerals_in(prompt) == ["20", "5", "12", "9.8", "0.5"]


def test_a_control_has_the_same_shape_is_not_in_the_prompt_and_is_far_from_the_gold():
    present = {20.0, 5.0, 12.0, 9.8}
    for text in ("20", "5", "9.8", "0.5", "4186"):
        control = s154.control_for(text, present, 2.178, random.Random(f"x:{text}"))
        assert control is not None and control != text
        assert len(control) == len(text) and [c == "." for c in control] == [c == "." for c in text]
        assert float(control) not in present and abs(float(control) - 2.178) / 2.178 > 0.01
        assert control[0] != "0" or text[0] == "0"  # no new leading zero


def test_control_is_deterministic_and_may_be_absent_when_none_exists():
    a = s154.control_for("9.8", {9.8}, 2.0, random.Random("same"))
    b = s154.control_for("9.8", {9.8}, 2.0, random.Random("same"))
    assert a == b
    # Every one-digit numeral 1-9 is present or within 1% of the gold, so no control exists.
    assert s154.control_for("3", {float(d) for d in range(1, 10)}, 5.0, random.Random("y")) is None


@pytest.fixture(scope="module")
def plan(tmp_path_factory, llama_tokenizer):
    base = tmp_path_factory.mktemp("s154")
    argv = sys.argv
    sys.argv = ["s154", "--out-root", str(base), "--attempt-id", "p1", "--structures", "S06", "--models", "llama_primary"]
    try:
        assert s154.main() == 0
    finally:
        sys.argv = argv
    jobs = [json.loads(line) for line in (base / "p1" / "job_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads((base / "p1" / "plan.json").read_text(encoding="utf-8")), jobs


def test_the_plan_is_a_dry_run_with_unique_ids_no_decoys_and_matched_controls(plan):
    meta, jobs = plan
    assert meta["authorized_to_run"] is False and meta["data_role"] == "EXPLORATION" and "not run" in meta["evidence_class"]
    assert len({j["job_id"] for j in jobs}) == len(jobs) == meta["n_jobs"]
    assert all(j["decoy_text"] is None and j["decoy_defined"] is False for j in jobs)
    present = [j for j in jobs if j["candidate_kind"] == "present"]
    controls = [j for j in jobs if j["candidate_kind"] == "absent_control"]
    assert len(controls) == len(present) > 0  # one matched control per present numeral
    by_prompt = {}
    for j in jobs:
        by_prompt.setdefault((j["instance"], j["cell_id"]), []).append(j)
    for group in by_prompt.values():
        texts = {j["candidate_text"] for j in group if j["candidate_kind"] == "present"}
        for j in group:
            if j["candidate_kind"] == "absent_control":
                assert j["candidate_matched_to"] in texts and j["candidate_text"] not in texts
    assert all(j["gold_text"].startswith("Answer: ") and j["candidate_text"] in j["gold_text"] for j in jobs)
    assert all("CANDIDATE" in j["candidate_note"] and j["true_gold_value"] == j["gold_value"] for j in jobs)


def test_the_cue_numeral_is_tagged_by_role_and_relevant_inputs_are_tagged_separately(plan):
    _, jobs = plan
    roles = {j["candidate_role"] for j in jobs if j["candidate_kind"] == "present"}
    assert "relevant_input" in roles and any(r.startswith("cue_") for r in roles)
    near = [j for j in jobs if j["cell_id"] == "nongov_same_unit_near_high_overlap" and j["candidate_kind"] == "present"]
    cue_rows = [j for j in near if j["candidate_role"].startswith("cue_")]
    assert len(cue_rows) == 2 and all(abs(float(j["candidate_text"]) - float(j["cue_numeric_value"])) < 1e-9 for j in cue_rows)
    no_cue = [j for j in jobs if j["cell_id"] == "no_cue" and j["candidate_kind"] == "present"]
    assert no_cue and all(j["candidate_role"] == "relevant_input" for j in no_cue)


def test_the_plan_refuses_to_reuse_a_directory(tmp_path, llama_tokenizer, monkeypatch):
    used = tmp_path / "p2"
    used.mkdir()
    (used / "keep.txt").write_text("evidence", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["s154", "--out-root", str(tmp_path), "--attempt-id", "p2", "--structures", "S06", "--models", "llama_primary"])
    assert s154.main() == 2 and (used / "keep.txt").read_text(encoding="utf-8") == "evidence"
