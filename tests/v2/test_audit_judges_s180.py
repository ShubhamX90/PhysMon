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


def test_written_content_with_units_is_not_an_access_but_other_tools_are(tmp_path):
    d = "/scratch/pabitra/physmon/judge/r1/b01"
    units = _t(tmp_path / "u.jsonl", [("Write", {"file_path": f"{d}/out/R-1_pass1.json",
                                                  "content": '{"unit": "m/s", "notes": "kg/m^3 and 9.8/2"}'})])
    assert s180.audit(units, d)["clean"]
    glob = _t(tmp_path / "g.jsonl", [("Glob", {"pattern": f"{d}/*"})])
    assert not s180.audit(glob, d)["clean"]  # inside the directory, but not an allowed tool


def test_pass2_opened_before_pass1_was_saved_is_a_violation(tmp_path):
    d = "/scratch/pabitra/physmon/judge/r1/b01"
    early = _t(tmp_path / "o.jsonl", [("Read", {"file_path": f"{d}/R-1_pass1_packet.json"}),
                                      ("Read", {"file_path": f"{d}/R-1_pass2_packet.json"}),
                                      ("Write", {"file_path": f"{d}/out/R-1_pass1.json", "content": "{}"})])
    r = s180.audit(early, d)
    assert not r["clean"] and r["pass2_opened_before_pass1_saved"] == ["R-1"]
