"""Tests for the Stage 14.16 legacy-family X03 plan (tokenizers only; no model, no GPU, nothing submitted)."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location("s156", REPO_ROOT / "scripts/v2/s156_legacy_x03_plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s156 = _load()


def cohort():
    with (REPO_ROOT / s156.CLUSTERS).open(newline="", encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r["in_135_cohort"] == "1"]


def test_allocation_gives_every_stratum_one_family_sums_to_the_total_and_respects_stratum_sizes():
    strata = {("a", "x"): list("abcdefghij"), ("a", "y"): list("klmn"), ("b", "x"): ["o"], ("c", "z"): list("pq")}
    counts = s156.allocate(strata, 8)
    assert sum(counts.values()) == 8 and all(c >= 1 for c in counts.values())
    assert all(counts[k] <= len(strata[k]) for k in strata) and counts[("b", "x")] == 1
    with pytest.raises(ValueError):
        s156.allocate(strata, 3)


def test_the_real_sample_is_60_distinct_cohort_families_covering_every_stratum_and_is_deterministic():
    rows = cohort()
    sample = s156.draw_sample(rows)
    assert len(sample) == 60 == len(set(sample)) and set(sample) <= {r["family"] for r in rows}
    by_family = {r["family"]: r for r in rows}
    drawn = {(by_family[f]["cue_type"], by_family[f]["domain"]) for f in sample}
    assert drawn == {(r["cue_type"], r["domain"]) for r in rows}  # every non-empty stratum is represented
    assert s156.draw_sample(rows) == sample and s156.draw_sample(rows, seed=7) != sample


def test_the_answer_text_is_split_into_value_and_unit():
    assert s156.parse_answer("5.0 m/s^2") == ("5.0", "m/s^2")
    assert s156.parse_answer("0.8991 N") == ("0.8991", "N")
    with pytest.raises(ValueError):
        s156.parse_answer("five metres")


@pytest.fixture(scope="module")
def plan(tmp_path_factory, llama_tokenizer):
    base = tmp_path_factory.mktemp("s156")
    argv = sys.argv
    sys.argv = ["s156", "--out-root", str(base), "--attempt-id", "p1", "--models", "llama_primary", "--wrappers", "answer_line",
                "boxed", "--families", "CM_B_001", "CM_C_002", "CM_A_001", "CM_A_004"]
    try:
        assert s156.main() == 0
    finally:
        sys.argv = argv
    jobs = [json.loads(line) for line in (base / "p1" / "job_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads((base / "p1" / "plan.json").read_text(encoding="utf-8")), jobs


def test_the_plan_is_a_dry_run_and_the_candidate_matrix_is_complete(plan):
    meta, jobs = plan
    assert meta["authorized_to_run"] is False and "not run" in meta["evidence_class"] and meta["wrapper_ids"] == ["answer_line", "boxed"]
    assert len({j["job_id"] for j in jobs}) == len(jobs) == meta["n_jobs"]
    # CM_B_001 and CM_A_004 have a numeric cue: 4 renderings x (1 gold + 4 cue candidates). CM_C_002 (frame rendering) and CM_A_001
    # (a colour) have no numeric cue: gold only.
    for wrapper in ("answer_line", "boxed"):
        by_family = {}
        for j in (j for j in jobs if j["wrapper_id"] == wrapper):
            by_family.setdefault(j["structure_id"], []).append(j)
        assert len(by_family["CM_B_001"]) == 20 and len(by_family["CM_A_004"]) == 20
        assert len(by_family["CM_C_002"]) == 4 and len(by_family["CM_A_001"]) == 4
    assert all(j["candidate_kind"] == "gold" for j in jobs if j["structure_id"] in ("CM_C_002", "CM_A_001"))
    assert all(j["cue_numeric_value"] is None for j in jobs if j["structure_id"] in ("CM_C_002", "CM_A_001"))


def test_the_diagonal_is_the_candidate_in_its_own_prompt_and_foreign_numerals_are_flagged(plan):
    _, jobs = plan
    cm = [j for j in jobs if j["structure_id"] == "CM_B_001" and j["wrapper_id"] == "answer_line" and j["candidate_kind"] == "cue_candidate"]
    assert len(cm) == 16 and sum(j["candidate_in_own_prompt"] for j in cm) == 4
    assert all(j["candidate_numeral_in_prompt"] for j in cm if j["candidate_in_own_prompt"])
    # CM_B_001 states 'mass 2.0 kg' for block A, so the numeral 2.0 is in every prompt as a relevant input.
    foreign_two = [j for j in cm if not j["candidate_in_own_prompt"] and j["candidate_text"] == "2.0"]
    assert foreign_two and all(j["candidate_numeral_in_prompt"] for j in foreign_two)
    foreign_other = [j for j in cm if not j["candidate_in_own_prompt"] and j["candidate_text"] == "3.0"]
    assert foreign_other and not any(j["candidate_numeral_in_prompt"] for j in foreign_other if j["prompt_variant"] != 3)


def test_candidates_keep_the_stored_unit_and_value_text_and_the_real_gold_is_recorded(plan):
    _, jobs = plan
    gold = next(j for j in jobs if j["structure_id"] == "CM_B_001" and j["candidate_kind"] == "gold" and j["wrapper_id"] == "answer_line")
    assert gold["gold_text"] == "Answer: 5.0 m/s^2" and gold["true_gold_value"] == 5.0
    boxed = next(j for j in jobs if j["structure_id"] == "CM_B_001" and j["candidate_kind"] == "gold" and j["wrapper_id"] == "boxed")
    assert boxed["gold_text"] == "\\boxed{5.0 m/s^2}"
    assert all("CANDIDATE" in j["candidate_note"] and j["decoy_text"] is None and j["gold_tokenization_status"] == "OK" for j in jobs)


def test_the_plan_refuses_to_reuse_a_directory(tmp_path, llama_tokenizer, monkeypatch):
    used = tmp_path / "p2"
    used.mkdir()
    (used / "keep.txt").write_text("evidence", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["s156", "--out-root", str(tmp_path), "--attempt-id", "p2", "--models", "llama_primary", "--families", "CM_B_001"])
    assert s156.main() == 2 and (used / "keep.txt").read_text(encoding="utf-8") == "evidence"
