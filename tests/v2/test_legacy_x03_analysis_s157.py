"""Tests for the Stage 14.16 legacy X03 analysis on synthetic jobs and records with known presence effects."""

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
    spec = importlib.util.spec_from_file_location("s157", REPO_ROOT / "scripts/v2/s157_legacy_x03_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s157 = _load()


def job(family, wrapper, kind, prompt_variant, source=None, text="1.0", in_prompt=None, role="nongoverning_distractor"):
    return {"job_id": f"q:{family}:{wrapper}:{kind}:v{prompt_variant}:c{source}", "model_key": "qwen_primary", "structure_id": family,
            "template_cluster_id": f"K_{family}", "wrapper_id": wrapper, "candidate_kind": kind, "candidate_text": text,
            "candidate_source_variant": source, "candidate_numeral_in_prompt": in_prompt, "prompt_variant": prompt_variant,
            "cue_semantic_role": role}


def build(diag_effect=4.0, wrappers=("answer_line", "boxed"), boxed_scale=1.0):
    """Two families (two clusters); 4 renderings; the candidate of rendering u scores -10 off the diagonal and -10+effect on it."""

    jobs, lp = [], {}
    for fam in ("F1", "F2"):
        for w in wrappers:
            scale = boxed_scale if w == "boxed" else 1.0
            for v in range(4):
                g = job(fam, w, "gold", v)
                jobs.append(g)
                lp[g["job_id"]] = -20.0 + 1.5 * v  # D_lp range 4.5
                for u in range(4):
                    c = job(fam, w, "cue_candidate", v, source=u, text=str(u + 1), in_prompt=(u == v))
                    jobs.append(c)
                    lp[c["job_id"]] = -10.0 + (diag_effect * scale if u == v else 0.0)
    return jobs, [{"job_id": j["job_id"], "status": "OK", "gold_logprob_raw": lp[j["job_id"]]} for j in jobs]


def test_presence_effect_is_the_diagonal_minus_the_mean_usable_off_diagonal():
    jobs, records = build()
    effects = s157.presence_effects(s157.join(records, jobs))
    assert effects[("F1", "answer_line", "nongoverning_distractor")] == pytest.approx(4.0)
    assert len(effects) == 4  # two families x two wrappers


def test_off_diagonal_cells_whose_numeral_is_in_the_prompt_are_excluded_and_a_candidate_without_any_is_not_evaluated():
    jobs, records = build()
    # Candidate 0 of F1 also appears in renderings 1 to 3 as a relevant input: no usable off-diagonal cell, so it is left out;
    # the family value then averages the other three candidates only.
    for j in jobs:
        if j["structure_id"] == "F1" and j["candidate_source_variant"] == 0 and j["prompt_variant"] != 0:
            j["candidate_numeral_in_prompt"] = True
    lp = {r["job_id"]: r["gold_logprob_raw"] for r in records}
    for j in jobs:  # make candidate 0's diagonal differ so that including it would change the mean
        if j["structure_id"] == "F1" and j["candidate_source_variant"] == 0 and j["prompt_variant"] == 0:
            lp[j["job_id"]] = 100.0
    records = [{"job_id": r["job_id"], "status": "OK", "gold_logprob_raw": lp[r["job_id"]]} for r in records]
    assert s157.presence_effects(s157.join(records, jobs))[("F1", "answer_line", "nongoverning_distractor")] == pytest.approx(4.0)


def test_a_failed_record_is_left_out_never_counted_as_zero():
    jobs, records = build()
    diag = next(r for r, j in zip(records, jobs, strict=True) if j["candidate_source_variant"] == 1 and j["prompt_variant"] == 1
                and j["structure_id"] == "F1" and j["wrapper_id"] == "answer_line")
    diag["status"] = "BOUNDARY_MISMATCH"
    effects = s157.presence_effects(s157.join(records, jobs))
    assert effects[("F1", "answer_line", "nongoverning_distractor")] == pytest.approx(4.0)  # the other three diagonals remain


def test_d_lp_is_the_range_of_the_gold_log_probability_across_renderings():
    jobs, records = build()
    ranges = s157.d_lp_ranges(s157.join(records, jobs))
    assert ranges[("F1", "boxed", "nongoverning_distractor")] == pytest.approx(4.5)


def test_clusters_are_the_unit_and_the_wrapper_difference_follows_the_frozen_dominance_rule():
    jobs, records = build(boxed_scale=2.0)  # the boxed effect is 8 against 4 for answer_line
    cluster_of = {"F1": "K_F1", "F2": "K_F2"}
    result = s157.analyse_model(s157.join(records, jobs), cluster_of, np.random.default_rng(42))
    ref = result["wrappers"]["answer_line"]["presence_effect"]["all numeral-cue families"]
    assert ref["mean"] == pytest.approx(4.0) and ref["n_structures"] == 2  # two clusters
    boxed = result["wrappers"]["boxed"]["interaction_vs_reference"]["all numeral-cue families"]
    assert boxed["mean"] == pytest.approx(4.0) and boxed["excludes_zero"] is True and boxed["dominates"] is True
    assert result["overall"]["wrappers_that_dominate"] == ["boxed"] and result["overall"]["invariance"] is False
    assert result["wrappers"]["answer_line"]["interaction_vs_reference"] == {}


def test_identical_wrappers_are_invariant_and_the_rule_reports_not_evaluated_without_data():
    jobs, records = build()
    result = s157.analyse_model(s157.join(records, jobs), {"F1": "K1", "F2": "K2"}, np.random.default_rng(42))
    assert result["overall"]["invariance"] is True and result["overall"]["wrappers_that_dominate"] == []
    assert s157.classify({"ci95": None, "mean": None}, 4.0)["status"] == "NOT_EVALUATED"
    assert s157.classify({"ci95": [1.0, 3.0], "mean": 2.0}, 4.0)["dominates"] is True
    assert s157.classify({"ci95": [1.0, 3.0], "mean": 1.9}, 4.0)["dominates"] is False


def test_a_record_outside_the_plan_or_a_duplicate_is_an_error_and_main_writes_outputs(tmp_path, monkeypatch):
    jobs, records = build()
    with pytest.raises(ValueError, match="not in the plan"):
        s157.join(records + [{"job_id": "x", "status": "OK", "gold_logprob_raw": 0.0}], jobs)
    with pytest.raises(ValueError, match="duplicate"):
        s157.join(records + [records[0]], jobs)
    plan = tmp_path / "plan"
    plan.mkdir()
    (plan / "job_manifest.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs), encoding="utf-8")
    for r in records:
        r["model_id"] = "M/test"
    rec = tmp_path / "raw_records.jsonl"
    rec.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    argv = ["s157", "--plan-dir", str(plan), "--records", str(rec), "--out-root", str(tmp_path / "out"), "--attempt-id", "t1"]
    monkeypatch.setattr(sys, "argv", argv)
    assert s157.main() == 0
    out = tmp_path / "out" / "t1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert "M/test" in summary["models"] and summary["evidence_class"].startswith("exploratory")
    assert "nothing here is a confirmation" in (out / "report.md").read_text(encoding="utf-8")
    assert (out / "presence_effects_by_wrapper.csv").stat().st_size > 0
    monkeypatch.setattr(sys, "argv", argv)
    assert s157.main() == 2
