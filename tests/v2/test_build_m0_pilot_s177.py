"""Tests for the M0 pilot builder: every structure certified, 14 core cells each, minimal pairs, runner job fields."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s177 = _load("s177", "scripts/v2/s177_build_m0_pilot.py")
s170 = _load("s170", "scripts/v2/s170_sampled_run.py")


def test_pilot_build(tmp_path):
    summary = s177.build(tmp_path / "m0", REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl")
    assert summary["excluded"] == [] and summary["no_cue_prompt_differs_from_v1"] == []
    assert 8 <= summary["n_structures"] <= 12
    rows = [json.loads(line) for line in (tmp_path / "m0" / "cells.jsonl").read_text().splitlines()]
    assert all(all(k in r for k in s170.JOB_FIELDS) for r in rows)
    core = Counter(r["structure_id"] for r in rows if r["cue_semantic_role"] in ("none", "N", "R", "D"))
    assert set(core.values()) == {14}
    by_id = {r["job_id"]: r for r in rows}
    for r in rows:
        if r["cue_semantic_role"] != "R":
            continue
        twin = r["job_id"].replace(":R:", ":D:").replace(f":{r['role']['phrasing_id']}:", ":d0:")
        d = by_id[twin]
        assert d["gold_value"] != r["gold_value"] and d["foils"]["relevant_twin"] == r["gold_value"]
        assert r["expected_effect"] == "changes" and d["expected_effect"] == "invariant"
    try:
        s177.build(tmp_path / "m0", REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl")
        raise AssertionError("must refuse to overwrite")
    except FileExistsError:
        pass
