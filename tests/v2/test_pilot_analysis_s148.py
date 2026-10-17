"""Tests for the Stage 14.8 descriptive pilot analysis, on synthetic records with known answers."""

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
    spec = importlib.util.spec_from_file_location("s148", REPO_ROOT / "scripts/v2/s148_pilot_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s148 = _load()
MODEL = "M/test"


def record(structure, instance, cell, gold_lp, decoy=None, gen=None, gold_value=10.0, cue=None, status="OK"):
    parsed = None if gen is None else {"value": gen, "unit": "m"}
    return {"model_id": MODEL, "structure_id": structure, "instance": instance, "cell_id": cell, "status": status,
            "gold_logprob_raw": gold_lp, "gold_value": gold_value, "cue_numeric_value": cue,
            "alternative_scores": None if decoy is None else {"decoy": {"status": "OK", "logprob_raw": decoy}},
            "parse_status": "PARSED" if gen is not None else "UNPARSEABLE", "parsed_answer": parsed,
            "correctness": "wrong"}


def synthetic():
    """Three structures, two instantiations. Near cue raises the gold log-probability by 2 nats over the anchor, far by 0.5."""

    rows = []
    for s, base in (("S1", -10.0), ("S2", -20.0), ("S3", -30.0)):
        for i in (0, 1):
            rows += [record(s, i, "no_cue", base, gen=5.0),
                     record(s, i, s148.NEAR, base + 2.0, decoy=base + 6.0, gen=9.5, cue=9.5),
                     record(s, i, s148.FAR, base + 0.5, decoy=base + 1.0, gen=7.0, cue=7.0),
                     record(s, i, "relevant_edit", base, gen=8.0, gold_value=12.0)]
    return rows


def test_contrasts_are_differences_of_the_gold_log_probability_against_the_same_anchor():
    index = s148.index_records(synthetic())
    cells = {c: index[(MODEL, "S2", 0, c)] for c in ("no_cue", s148.NEAR, s148.FAR, "relevant_edit")}
    contrasts = s148.item_contrasts(cells)
    assert contrasts[f"gold_lp[{s148.NEAR}] - gold_lp[no_cue]"] == pytest.approx(2.0)
    assert contrasts[f"gold_lp[{s148.FAR}] - gold_lp[no_cue]"] == pytest.approx(0.5)
    assert contrasts["gold_lp[near_high_overlap] - gold_lp[far]"] == pytest.approx(1.5)
    # R_alt = gold - decoy: near is -4, far is -0.5, so the difference is -3.5.
    assert contrasts["R_alt[near_high_overlap] - R_alt[far]"] == pytest.approx(-3.5)


def test_a_missing_cell_is_not_evaluated_and_never_zero():
    index = s148.index_records(synthetic())
    cells = {c: index[(MODEL, "S1", 0, c)] for c in ("no_cue", s148.NEAR)}  # no far, no moderate, no decoys elsewhere
    contrasts = s148.item_contrasts(cells)
    assert contrasts["gold_lp[near_high_overlap] - gold_lp[far]"] is None
    assert contrasts[f"gold_lp[{s148.CONVERT}] - gold_lp[no_cue]"] is None
    assert contrasts["R_alt[near_high_overlap] - R_alt[moderate]"] is None
    # An anchor cell with no decoy has no R_alt at all.
    assert s148.r_alt(index[(MODEL, "S1", 0, "no_cue")]) is None
    failed = record("S1", 0, s148.NEAR, None, status="BOUNDARY_MISMATCH")
    assert s148.gold_lp(failed) is None and s148.r_alt(failed) is None


def test_structure_level_means_and_a_deterministic_cluster_bootstrap_over_structures():
    result = s148.analyse_model(synthetic(), MODEL, np.random.default_rng(42))
    contrast = result["contrasts"][f"gold_lp[{s148.NEAR}] - gold_lp[no_cue]"]
    assert contrast["n_structures"] == 3 and contrast["mean"] == pytest.approx(2.0)
    assert contrast["n_positive"] == 3 and contrast["n_negative"] == 0
    assert contrast["ci95"] == [pytest.approx(2.0), pytest.approx(2.0)]  # every structure has the same effect
    again = s148.analyse_model(synthetic(), MODEL, np.random.default_rng(42))
    assert again["contrasts"] == result["contrasts"]
    spread = s148.cluster_bootstrap([1.0, 2.0, 3.0], np.random.default_rng(42))
    assert spread["ci95"][0] < spread["mean"] < spread["ci95"][1]
    one = s148.cluster_bootstrap([1.0], np.random.default_rng(42))
    assert one["ci95"] is None and one["status"].startswith("NOT_EVALUATED")


def test_d_lp_is_the_range_sd_and_mad_over_cells_that_share_the_gold_string():
    index = s148.index_records(synthetic())
    cells = {c: index[(MODEL, "S1", 0, c)] for c in ("no_cue", s148.NEAR, s148.FAR, "relevant_edit")}
    result = s148.d_lp(cells)
    assert result["n_cells"] == 3  # the relevant edit has a different gold and is excluded
    assert result["range"] == pytest.approx(2.0)
    assert result["mad"] == pytest.approx(0.5)  # values -10, -8, -9.5: median -9.5, absolute deviations 0.5, 1.5, 0
    assert s148.d_lp({"no_cue": cells["no_cue"]})["range"] is None


def test_assay_response_counts_changes_direction_and_movement_toward_the_new_gold():
    rows = synthetic()
    summary = s148.assay_response(s148.index_records(rows), MODEL, ["S1", "S2", "S3"])
    # Anchor generation 5.0, edited generation 8.0, gold 10 -> 12: always up, closer to 12, six pairs.
    assert summary["n_pairs"] == summary["n_evaluable"] == 6
    assert summary["n_generation_changed"] == 6 == summary["n_changed_in_the_direction_of_the_gold"]
    assert summary["n_moved_toward_new_gold"] == 6
    rows[3]["parse_status"], rows[3]["parsed_answer"] = "UNPARSEABLE", None  # S1 instance 0 edit unparseable
    summary = s148.assay_response(s148.index_records(rows), MODEL, ["S1", "S2", "S3"])
    assert summary["n_pairs"] == 6 and summary["n_evaluable"] == 5


def test_copy_rate_counts_generations_equal_to_the_cue_numeral_among_parsed_ones():
    rates = s148.copy_rates(synthetic())
    assert rates[s148.NEAR] == {"n_parsed": 6, "n_equal_to_cue_numeral": 6, "n_records": 6}
    assert rates[s148.FAR]["n_equal_to_cue_numeral"] == 6
    assert rates["nongov_same_unit_moderate"]["n_parsed"] == 0


def test_duplicate_records_are_an_error_not_a_silent_overwrite():
    rows = synthetic()
    with pytest.raises(ValueError, match="duplicate"):
        s148.index_records(rows + [rows[0]])


def test_main_writes_the_report_and_tables_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    records = tmp_path / "raw_records.jsonl"
    records.write_text("".join(json.dumps(r) + "\n" for r in synthetic()), encoding="utf-8")
    argv = ["s148", "--records", str(records), "--out-root", str(tmp_path / "out"), "--attempt-id", "t1"]
    monkeypatch.setattr(sys, "argv", argv)
    assert s148.main() == 0
    out = tmp_path / "out" / "t1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["evidence_class"].startswith("exploratory") and "presentation-noise floor (P1.7)" in summary["not_evaluated"]
    assert summary["inputs"][str(records)]["n_records"] == 24
    text = (out / "report.md").read_text(encoding="utf-8")
    assert "precision-limited" in text and "nothing here is a confirmation" in text and "NOT_EVALUATED" in text
    for name in ("contrasts_structure_level.csv", "contrasts_by_item.csv"):
        assert (out / name).stat().st_size > 0
    monkeypatch.setattr(sys, "argv", argv)
    assert s148.main() == 2
