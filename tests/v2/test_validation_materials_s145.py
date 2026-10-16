"""Tests for the Stage 14.5 validator-qualification materials (built from committed data only)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "s145_validation_materials", REPO_ROOT / "scripts/v2/s145_validation_materials.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s145 = _load()


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    base = tmp_path_factory.mktemp("s145")
    argv = sys.argv
    sys.argv = ["s145", "--out-base", str(base), "--version", "t1"]
    try:
        assert s145.main() == 0
    finally:
        sys.argv = argv
    return base / "t1"


def test_counts_and_disjointness(built):
    summary = json.loads((built / "summary.json").read_text(encoding="utf-8"))
    assert (summary["n_items"], summary["n_genuine"], summary["n_planted"]) == (73, 40, 33)
    assert summary["families_disjoint_between_planted_and_genuine"] is True
    assert summary["bank_shortfalls"] == {}
    counts = summary["planted_by_defect_type"]
    assert counts.pop("valid_equivalent_rewrite") == 6
    assert set(counts.values()) == {3} and len(counts) == 9
    assert sum(summary["genuine_by_stratum"].values()) == 40
    assert summary["status"].startswith("CANDIDATE")


def test_pass1_packets_leak_nothing_that_identifies_planted_items_or_outcomes(built):
    text = (built / "pass1_packets.jsonl").read_text(encoding="utf-8")
    for forbidden in ("defect", "planted", "CM_", "EL_", "TH_", "S_lp", "Qwen", "Llama", "logprob", "sensitive",
                      "equation", "certif", "expected", "stratum"):
        assert forbidden.lower() not in text.lower(), forbidden
    for packet in _jsonl(built / "pass1_packets.jsonl"):
        assert set(packet) == {"item_id", "variants"} and len(packet["variants"]) == 4


def test_item_ids_are_shuffled_so_planted_and_genuine_are_interleaved(built):
    key = json.loads((built / "packet_key_RESTRICTED.json").read_text(encoding="utf-8"))
    ordered = [key[f"Q{i:03d}"]["kind"] for i in range(1, 74)]
    first_half = ordered[:36]
    assert 0 < first_half.count("planted") < 36
    assert sorted(key) == [f"Q{i:03d}" for i in range(1, 74)]


def test_pass2_shows_the_equation_and_the_equation_defect_lives_only_there(built):
    key = json.loads((built / "packet_key_RESTRICTED.json").read_text(encoding="utf-8"))
    pass1 = {p["item_id"]: p for p in _jsonl(built / "pass1_packets.jsonl")}
    pass2 = {p["item_id"]: p for p in _jsonl(built / "pass2_packets.jsonl")}
    bank = {b["item_id"]: b for b in _jsonl(built / "planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl")}
    for item_id, entry in key.items():
        assert "governing_equation_sympy" in pass2[item_id] and "governing_equation_sympy" not in pass1[item_id]
        if entry["defect_type"] == "relevant_variable_removed_from_equation":
            assert pass2[item_id]["governing_equation_sympy"] == bank[item_id]["edited_equation"]
            assert pass2[item_id]["governing_equation_sympy"] != bank[item_id]["original_equation"]
            assert entry["detectable_in"] == "pass2"
            assert pass1[item_id]["variants"] == pass2[item_id]["variants"]
        if entry["defect_type"] == "invalid_numerical_precision":
            assert pass2[item_id]["certified_answer_display"] == bank[item_id]["edited_answer"]
            assert bank[item_id]["edited_answer"] != bank[item_id]["original_answer"]


def test_key_and_bank_agree_and_every_planted_item_really_differs_from_its_original(built):
    key = json.loads((built / "packet_key_RESTRICTED.json").read_text(encoding="utf-8"))
    bank = _jsonl(built / "planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl")
    assert len(bank) == 33
    for row in bank:
        entry = key[row["item_id"]]
        assert entry["defect_type"] == row["defect_type"] and entry["family"] == row["family"]
        assert entry["expected_verdict"] == ("valid" if row["defect_type"] == "valid_equivalent_rewrite" else "invalid")
        changed = (row["edited_variant0_prompt"] != row["original_variant0_prompt"]
                   or row["edited_equation"] or row["edited_answer"]
                   or row["defect_type"] == "failed_transformation_identity")
        assert changed, row["item_id"]
        assert row["physicist_confirmation"]["confirmed_by"] is None  # not confirmed by anyone yet


def test_genuine_sample_covers_every_cue_type_and_domain_and_a_timing_pilot_of_twenty(built):
    import csv

    with (built / "genuine_pilot_sample.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 40
    assert {r["cue_type"] for r in rows} == {"irrelevant_variable", "nongoverning_distractor", "frame_rendering"}
    assert {r["domain"] for r in rows} == {"mechanics", "electrostatics_circuits", "thermodynamics"}
    assert sum(int(r["in_timing_pilot_20"]) for r in rows) == 20
    assert any(r["selection_used_model_outcomes"] == "True" for r in rows)


def test_build_is_deterministic_and_refuses_to_overwrite(built, tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["s145", "--out-base", str(tmp_path), "--version", "t2"])
    assert s145.main() == 0
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "packet_key_RESTRICTED.json",
                 "planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl", "genuine_pilot_sample.csv"):
        assert (built / name).read_text(encoding="utf-8") == (tmp_path / "t2" / name).read_text(encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["s145", "--out-base", str(tmp_path), "--version", "t2"])
    assert s145.main() == 2
