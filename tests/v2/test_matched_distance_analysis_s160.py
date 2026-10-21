"""Tests for the Stage 14.17 plausibility-matched analysis on synthetic jobs and records with known effects."""

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
    spec = importlib.util.spec_from_file_location("s160", REPO_ROOT / "scripts/v2/s160_matched_distance_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s160 = _load()
NEAR = s160.s148.NEAR


def job(structure, cell, kind, text, role, matched=None, ratio=None, control_prefix=None, own_prefix=None, unit_type="same", instance=0):
    return {"job_id": f"q:{structure}:{instance}:{cell}:cand:{kind}:{matched or ''}:{text}", "model_key": "qwen_primary",
            "structure_id": structure, "instance": instance, "cell_id": cell, "candidate_kind": kind, "candidate_text": text,
            "candidate_matched_to": matched, "candidate_role": role, "unit_type": unit_type, "control_distance_ratio": ratio,
            "control_prefix_overlap": control_prefix, "own_prefix_overlap": own_prefix}


def build(structures=("S1", "S2", "S3"), cue_lp=-4.0, control_lps=(-10.0, -8.0, -9.0, -9.0), ratios=(1.0, 1.5, 3.0, 0.9),
          control_prefixes=(2, 2, 0, 2)):
    """One cue numeral per structure with four matched controls, plus one relevant input with two controls."""

    jobs, lps = [], {}
    for s in structures:
        cue = job(s, NEAR, "present", "2.17", "cue_nongoverning_isolated", own_prefix=2)
        jobs.append(cue)
        lps[cue["job_id"]] = cue_lp
        for i, (lp, r, p) in enumerate(zip(control_lps, ratios, control_prefixes, strict=True)):
            c = job(s, NEAR, "matched_control", f"2.1{i}", "absent", matched="2.17", ratio=r, control_prefix=p, own_prefix=2)
            jobs.append(c)
            lps[c["job_id"]] = lp
        rel = job(s, NEAR, "present", "5", "relevant_input", own_prefix=0)
        jobs.append(rel)
        lps[rel["job_id"]] = -7.0
        for i, lp in enumerate((-9.0, -9.0)):
            c = job(s, NEAR, "matched_control", f"{i}", "absent", matched="5", ratio=1.0, control_prefix=0, own_prefix=0)
            jobs.append(c)
            lps[c["job_id"]] = lp
    records = [{"job_id": j["job_id"], "status": "OK", "gold_logprob_raw": lps[j["job_id"]]} for j in jobs]
    return jobs, records


def test_the_adjusted_effect_is_the_present_log_probability_minus_the_mean_of_its_matched_controls():
    jobs, records = build()
    effects = s160.adjusted_effects(s160.join(records, jobs))
    cue = next(e for e in effects if e["text"] == "2.17" and e["structure"] == "S1")
    assert cue["n_controls"] == 4 and cue["effect"] == pytest.approx(-4.0 - np.mean([-10.0, -8.0, -9.0, -9.0]))
    rel = next(e for e in effects if e["text"] == "5" and e["structure"] == "S1")
    assert rel["effect"] == pytest.approx(2.0)


def test_the_sensitivity_variants_keep_only_controls_within_a_factor_of_two_or_with_the_same_prefix_overlap():
    jobs, records = build()
    rows = s160.join(records, jobs)
    within = next(e for e in s160.adjusted_effects(rows, "within_factor_2") if e["text"] == "2.17" and e["structure"] == "S1")
    assert within["n_controls"] == 3 and within["effect"] == pytest.approx(-4.0 - np.mean([-10.0, -8.0, -9.0]))
    same = next(e for e in s160.adjusted_effects(rows, "same_prefix_overlap") if e["text"] == "2.17" and e["structure"] == "S1")
    assert same["n_controls"] == 3 and same["effect"] == pytest.approx(-4.0 - np.mean([-10.0, -8.0, -9.0]))


def test_a_numeral_without_an_ok_control_or_with_a_failed_record_is_not_evaluated_and_never_zero():
    jobs, records = build(structures=("S1",))
    controls = [j["job_id"] for j in jobs if j["candidate_kind"] == "matched_control" and j["candidate_matched_to"] == "2.17"]
    for r in records:
        if r["job_id"] in controls:
            r["status"] = "CANDIDATE_TOKENIZATION_FAILED"
    effects = s160.adjusted_effects(s160.join(records, jobs))
    cue = next(e for e in effects if e["text"] == "2.17")
    assert cue["effect"] is None and cue["n_controls"] == 0
    rel = next(e for e in effects if e["text"] == "5")
    assert rel["effect"] == pytest.approx(2.0)  # other numerals are unaffected
    result = s160.analyse(s160.join(records, jobs), np.random.default_rng(1))
    assert result["primary"]["A"]["n_numerals_without_effect"] == 1


def test_the_reading_rule_needs_an_interval_above_zero_and_a_mean_of_at_least_the_noise_threshold():
    assert s160.reading({"mean": 3.0, "ci95": [1.0, 5.0]}) == "above plausibility"
    assert s160.reading({"mean": 0.3, "ci95": [0.1, 0.5]}).startswith("not distinguishable")
    assert s160.reading({"mean": 2.0, "ci95": [-0.1, 4.0]}).startswith("not distinguishable")
    assert s160.reading({"mean": None, "ci95": None}) == "NOT_EVALUATED"


def test_groups_are_the_two_batches_and_their_descriptive_pooling():
    jobs, records = build(structures=("S1", "S2", "S11", "S12"))
    result = s160.analyse(s160.join(records, jobs), np.random.default_rng(2))
    assert set(result["primary"]) == {"A", "B", "A+B (descriptive pooling)"}
    cue = result["primary"]["A"]["role_presence_effect"]["cue_nongoverning_isolated[same]"]
    assert cue["n_structures"] == 2 and cue["mean"] == pytest.approx(5.0) and cue["reading"] == "above plausibility"
    assert result["primary"]["A+B (descriptive pooling)"]["role_presence_effect"]["relevant_input"]["n_structures"] == 4


def test_the_join_rejects_a_record_outside_the_plan_a_duplicate_record_and_a_plan_with_duplicate_ids():
    jobs, records = build(structures=("S1",))
    with pytest.raises(ValueError, match="not in the plan"):
        s160.join(records + [{"job_id": "x", "status": "OK", "gold_logprob_raw": 0.0}], jobs)
    with pytest.raises(ValueError, match="duplicate record"):
        s160.join(records + [records[0]], jobs)
    with pytest.raises(ValueError, match="duplicate job ids"):
        s160.join(records, jobs + [jobs[0]])


def test_the_unadjusted_comparison_and_the_reproducibility_check_use_the_same_numerals():
    jobs, records = build(structures=("S1", "S2"))
    rows = s160.join(records, jobs)
    earlier = [{"structure": r["structure"], "instance": r["instance"], "cell": r["cell"], "kind": "present", "text": r["text"],
                "role": r["role"], "unit_type": r["unit_type"], "matched_to": None, "lp": r["lp"] + 0.25}
               for r in rows if r["kind"] == "present"]
    rep = s160.reproducibility(rows, earlier)
    assert rep["n"] == 4 and rep["max_abs_difference"] == pytest.approx(0.25) and rep["n_exactly_equal"] == 0
    assert s160.reproducibility(rows, [])["status"] == "NOT_EVALUATED"


def test_main_writes_outputs_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    jobs, records = build()
    plan = tmp_path / "plan"
    plan.mkdir()
    (plan / "job_manifest.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs), encoding="utf-8")
    run = tmp_path / "run"
    run.mkdir()
    recs = [dict(r, model_id="Qwen/Qwen2.5-7B-Instruct") for r in records]
    (run / "raw_records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["s160", "--plan-dir", str(plan), "--records", str(run / "raw_records.jsonl"),
                                      "--out-root", str(tmp_path / "out"), "--attempt-id", "a1"])
    assert s160.main() == 0
    out = tmp_path / "out" / "a1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert "Qwen/Qwen2.5-7B-Instruct" in summary["models"] and (out / "report.md").exists() and (out / "adjusted_presence_effects.csv").exists()
    assert "not paper-eligible" in (out / "report.md").read_text(encoding="utf-8")
    assert s160.main() == 2
