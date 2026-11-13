"""Tests for the judge-transcript independence audit."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("s180", REPO_ROOT / "scripts/v2/s180_audit_judge_transcripts.py")
s180 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s180)


def _t(path, uses):
    lines = [{"message": {"content": [{"type": "tool_use", "name": n, "input": i} for n, i in uses]}}]
    path.write_text("\n".join(json.dumps(x) for x in lines))
    return path


def test_clean_and_dirty_transcripts(tmp_path):
    d = "/scratch/pabitra/physmon/judge/r1/b01"
    clean = _t(tmp_path / "c.jsonl", [("Read", {"file_path": f"{d}/R-123_pass1.json"}),
                                      ("Write", {"file_path": f"{d}/out/R-123_pass1.json", "content": "{}"})])
    assert s180.audit(clean, d)["clean"]
    peek = _t(tmp_path / "p.jsonl", [("Read", {"file_path": f"{d}/R-123_pass1.json"}),
                                     ("Bash", {"command": "cat /home/pabitra/PhysMons/docs/x/key_RESTRICTED.json"})])
    r = s180.audit(peek, d)
    assert not r["clean"] and "key_RESTRICTED" in r["violations"][0]["forbidden"]
    web = _t(tmp_path / "w.jsonl", [("WebSearch", {"query": "atwood"})])
    assert not s180.audit(web, d)["clean"]
    assert not s180.audit(_t(tmp_path / "e.jsonl", []), d)["clean"]  # no tool calls: nothing to show it worked
