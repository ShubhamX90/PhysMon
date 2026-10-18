"""Tests for the Stage 14.14 numeral-presence analysis on synthetic jobs and records with known presence effects."""

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
    spec = importlib.util.spec_from_file_location("s155", REPO_ROOT / "scripts/v2/s155_numeral_presence_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s155 = _load()
NEAR, INCOMPAT = s155.s148.NEAR, s155.s148.INCOMPAT


def job(structure, cell, kind, text, role, matched=None, unit_type="not_applicable", instance=0):
    return {"job_id": f"q:{structure}:{instance}:{cell}:cand:{kind}:{text}", "model_key": "qwen_primary", "structure_id": structure,
            "instance": instance, "cell_id": cell, "candidate_kind": kind, "candidate_text": text, "candidate_matched_to": matched,
            "candidate_role": role, "unit_type": unit_type}


def build():
    """Per structure: relevant input presence effect +1; same-unit cue +6; incompatible-unit cue +2 (control lp is -10 everywhere)."""

    jobs, lps = [], {}
    for s in ("S1", "S2", "S3"):
        spec = (("no_cue", "relevant_input", "5", 1.0, "not_applicable"),
                (NEAR, "relevant_input", "5", 1.0, "same"), (NEAR, "cue_nongoverning_isolated", "2.17", 6.0, "same"),
                (INCOMPAT, "relevant_input", "5", 1.0, "incompatible"), (INCOMPAT, "cue_nongoverning_isolated", "2.17", 2.0, "incompatible"))
        for cell, role, text, effect, unit_type in spec:
            present = job(s, cell, "present", text, role, unit_type=unit_type)
            control = job(s, cell, "absent_control", "7" + text[1:], "absent", matched=text, unit_type=unit_type)
            jobs += [present, control]
            lps[control["job_id"]] = -10.0
            lps[present["job_id"]] = -10.0 + effect
    records = [{"job_id": j["job_id"], "status": "OK", "gold_logprob_raw": lps[j["job_id"]]} for j in jobs]
    return jobs, records


def test_presence_effect_is_present_minus_matched_control_under_the_same_prompt():
    jobs, records = build()
    effects = s155.presence_effects(s155.join(records, jobs))
    assert len(effects) == 15 and all(e["effect"] is not None for e in effects)
    cue = next(e for e in effects if e["structure"] == "S1" and e["cell"] == NEAR and e["role"].startswith("cue_"))
    assert cue["effect"] == pytest.approx(6.0)
    relevant = next(e for e in effects if e["structure"] == "S1" and e["cell"] == "no_cue")
    assert relevant["effect"] == pytest.approx(1.0)


def test_roles_are_summarised_by_structure_and_the_paired_contrasts_are_within_a_prompt():
    jobs, records = build()
    result = s155.analyse(s155.join(records, jobs), np.random.default_rng(42))
    roles = result["role_presence_effect"]
    assert roles["relevant_input"]["mean"] == pytest.approx(1.0) and roles["relevant_input"]["n_structures"] == 3
    assert roles["cue_nongoverning_isolated[same]"]["mean"] == pytest.approx(6.0)
    assert roles["cue_nongoverning_isolated[incompatible]"]["mean"] == pytest.approx(2.0)
    assert roles["relevant_input[no_cue prompt only]"]["mean"] == pytest.approx(1.0)
    paired = result["paired_contrasts"]
    assert paired["cue_nongoverning_isolated[same] minus relevant_input (same prompt)"]["mean"] == pytest.approx(5.0)
    assert paired["cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt)"]["mean"] == pytest.approx(1.0)
    assert paired["same-unit near cue minus incompatible-unit near cue"]["mean"] == pytest.approx(4.0)
    assert paired["same-unit near cue minus incompatible-unit near cue"]["ci95"] == [pytest.approx(4.0), pytest.approx(4.0)]


def test_a_failed_record_or_missing_control_is_not_evaluated_and_never_zero():
    jobs, records = build()
    records[0]["status"] = "BOUNDARY_MISMATCH"  # the first present numeral of S1/no_cue
    rows = s155.join(records, jobs)
    effects = s155.presence_effects(rows)
    assert sum(e["effect"] is None for e in effects) == 1
    result = s155.analyse(rows, np.random.default_rng(42))
    assert result["n_not_evaluated"] == 1
    # The S1 no-cue prompt has no evaluated relevant input, so S1 does not contribute to the no-cue-only role.
    assert result["role_presence_effect"]["relevant_input[no_cue prompt only]"]["n_structures"] == 2
    orphan = [j for j in jobs if not (j["candidate_kind"] == "absent_control" and j["structure_id"] == "S2" and j["cell_id"] == NEAR)]
    recs = [r for r in records if r["job_id"] in {j["job_id"] for j in orphan}]
    effects = s155.presence_effects(s155.join(recs, orphan))
    assert any(e["effect"] is None and e["structure"] == "S2" and e["cell"] == NEAR for e in effects)


def test_a_record_outside_the_plan_or_a_duplicate_is_an_error():
    jobs, records = build()
    with pytest.raises(ValueError, match="not in the plan"):
        s155.join(records + [{"job_id": "x", "status": "OK", "gold_logprob_raw": 0.0}], jobs)
    with pytest.raises(ValueError, match="duplicate"):
        s155.join(records + [records[0]], jobs)


def test_main_writes_outputs_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    jobs, records = build()
    for j in jobs:
        j["structure_uuid"] = "u"
    plan = tmp_path / "plan"
    plan.mkdir()
    (plan / "job_manifest.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs), encoding="utf-8")
    for r in records:
        r["model_id"] = "M/test"
    rec = tmp_path / "raw_records.jsonl"
    rec.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    argv = ["s155", "--plan-dir", str(plan), "--records", str(rec), "--out-root", str(tmp_path / "out"), "--attempt-id", "t1"]
    monkeypatch.setattr(sys, "argv", argv)
    assert s155.main() == 0
    out = tmp_path / "out" / "t1"
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["evidence_class"].startswith("exploratory") and "M/test" in summary["models"]
    assert "nothing here is a confirmation" in (out / "report.md").read_text(encoding="utf-8")
    assert (out / "presence_effects.csv").stat().st_size > 0
    monkeypatch.setattr(sys, "argv", argv)
    assert s155.main() == 2
