"""Tests for the Stage 14.19 dataset assembler on real library structures with two small plans."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import library_b  # noqa: E402
from physmon.benchmark.v2 import trace as tr  # noqa: E402


def _load():
    spec = importlib.util.spec_from_file_location("s163", REPO_ROOT / "scripts/v2/s163_build_dataset.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s163 = _load()
PLAN = tr.Plan(
    approach="A sliding car decelerates at a constant rate set by friction, so use kinematics with that deceleration to find the stopping distance.",
    steps=(tr.Step("d", "Newton's second law with kinetic friction, then constant-deceleration kinematics v^2 = 2 a d",
                   "The friction force mu m g is the only horizontal force, so the deceleration is mu g; the car stops when v reaches zero."),),
    check="Doubling the speed quadruples the distance, as expected from v^2; the units are metres.")


def sources():
    structures = {s.structure_id: s for s in library_b.all_structures() if s.structure_id in ("S11", "S12")}
    return {"structures": structures, "origin": dict.fromkeys(structures, "library_b"), "plans": {"S11": PLAN}, "levels": {"S11": "high_school"},
            "topics": {"S11": "braking with friction"}, "plan_origin": {"S11": "lib_test"}}


def test_only_accepted_structures_with_a_plan_enter_and_exclusions_are_listed_with_reasons():
    samples, manifest, excluded = s163.build(sources(), {"S11": {"status": "accepted", "blind_match": True, "issues": []},
                                                         "S12": {"status": "accepted", "blind_match": True, "issues": []}}, certify=False)
    assert {s["structure_id"] for s in samples} == {"S11"} and len(samples) == 2
    assert [e["structure_id"] for e in excluded] == ["S12"] and excluded[0]["state"] == "no_plan"
    assert {r["structure_id"] for r in manifest} == {"S11"} and len(manifest) == 22
    samples2, _, excluded2 = s163.build(sources(), {"S11": {"status": "excluded", "issues": ["ambiguous"]}}, certify=False)
    assert samples2 == [] and {e["structure_id"] for e in excluded2} == {"S11", "S12"}
    assert next(e for e in excluded2 if e["structure_id"] == "S11")["issues"] == ["ambiguous"]


def test_a_sample_has_problem_answer_trace_and_the_unreviewed_statement():
    samples, _, _ = s163.build(sources(), {"S11": {"status": "accepted_after_repair", "blind_match": True, "issues": ["fixed wording"]}}, certify=True)
    sample = samples[0]
    assert sample["admission_category"] == "UNREVIEWED" and "No human expert" in sample["review_statement"]
    assert sample["certification"]["status"] == "SOLVER_CERTIFIED" and sample["level"] == "high_school"
    assert sample["gold_answer"]["unit"] == "m" and abs(sample["gold_answer"]["value"] - 40.8163) < 1e-3
    assert "Answer:" in sample["gold_trace"]["text"] and sample["gold_trace"]["kind"].startswith("solving technique")
    assert "40.8" in sample["gold_trace"]["text"]
    assert sample["problem"].endswith("How far does the car travel before it stops?") and sample["agent_verification"]["status"] == "accepted_after_repair"


def test_main_writes_the_dataset_and_refuses_to_reuse_a_directory(tmp_path, monkeypatch):
    status = tmp_path / "status.json"
    status.write_text(json.dumps({"S11": {"status": "accepted", "blind_match": True, "issues": []}}), encoding="utf-8")
    monkeypatch.setattr(s163, "load_sources", lambda base, domains: sources())
    monkeypatch.setattr(sys, "argv", ["s163", "--status", str(status), "--out-root", str(tmp_path / "out"), "--no-certify"])
    assert s163.main() == 0
    out = tmp_path / "out" / "v1"
    rows = [json.loads(line) for line in (out / "dataset.jsonl").read_text(encoding="utf-8").splitlines()]
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert len(rows) == 2 == summary["n_samples"] and summary["excluded"][0]["structure_id"] == "S12" and "UNREVIEWED" in summary["admission"]
    assert s163.main() == 2
