#!/usr/bin/env python3
"""Stage 15 (G1): audit judge-instance transcripts for independence violations.

A judge instance may touch only its own packet directory (read packets, write reviews). This script reads each
transcript (JSONL of the agent's messages and tool calls), extracts every file path and shell command the judge used,
and flags any access outside the allowed directory, any mention of the restricted key or the repository, and any web
access. A flagged judge's reviews are void under the qualification protocol.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

FORBIDDEN_PATTERNS = ("key_RESTRICTED", "packet_key", "PhysMons", "planted_defect", "rolevalue_bank", "s178_",
                      "llm_panel/bank", "roles_m0")
WEB_TOOLS = ("WebFetch", "WebSearch", "web-fetch")
ACCESS_FIELDS = ("file_path", "path", "pattern", "command", "notebook_path", "url")
ALLOWED_TOOLS = ("Read", "Write", "SubagentHandback")  # the assignment allows Read and Write; the last returns the report


def _tool_uses(obj: Any) -> list[dict[str, Any]]:
    """Every tool_use block anywhere in a transcript line."""

    found = []
    if isinstance(obj, dict):
        if obj.get("type") == "tool_use":
            found.append(obj)
        for v in obj.values():
            found.extend(_tool_uses(v))
    elif isinstance(obj, list):
        for v in obj:
            found.extend(_tool_uses(v))
    return found


def audit(transcript: Path, allowed_dir: str) -> dict[str, Any]:
    violations, n_calls, sequence = [], 0, []
    allowed = allowed_dir.rstrip("/")
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for use in _tool_uses(obj):
            n_calls += 1
            name = str(use.get("name", ""))
            inp = use.get("input", {}) if isinstance(use.get("input"), dict) else {}
            if name in WEB_TOOLS:
                violations.append({"tool": name, "reason": "web access", "input": json.dumps(inp)[:300]})
                continue
            # only the fields that name what is accessed; written content (which contains units such as "m/s") is not
            # an access and is never scanned
            accessed = {k: str(v) for k, v in inp.items() if k in ACCESS_FIELDS}
            if "file_path" in accessed:
                sequence.append((name, Path(accessed["file_path"]).name))
            text = json.dumps(accessed, ensure_ascii=False)
            hit = [p for p in FORBIDDEN_PATTERNS if p in text]
            outside = []
            for key, value in accessed.items():
                if key == "command":  # a shell command: every absolute path in it
                    outside += [p for p in re.findall(r"(?:^|\s)(/[A-Za-z0-9_.\-/]+)", value) if not p.startswith(allowed)]
                elif not value.startswith(allowed):
                    outside.append(value)
            if name not in ALLOWED_TOOLS:
                outside.append(f"<tool {name} not allowed>")
            if hit or outside:
                violations.append({"tool": name, "forbidden": hit, "outside_paths": outside[:5], "input": text[:300]})
    # blind pass 1: each item's pass-1 review is written before its pass-2 packet is first read
    order = {}
    for i, (tool, name) in enumerate(sequence):
        if tool == "Write" and name.endswith("_pass1.json"):
            order.setdefault(name[: -len("_pass1.json")], {})["pass1_written"] = i
        if tool == "Read" and name.endswith("_pass2_packet.json"):
            order.setdefault(name[: -len("_pass2_packet.json")], {}).setdefault("pass2_read", i)
    order_violations = sorted(item for item, o in order.items()
                              if "pass2_read" in o and o.get("pass1_written", 10**9) > o["pass2_read"])
    return {"transcript": str(transcript), "allowed_dir": allowed, "n_tool_calls": n_calls,
            "violations": violations, "pass2_opened_before_pass1_saved": order_violations,
            "clean": not violations and not order_violations and n_calls > 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--transcript", required=True, action="append")
    parser.add_argument("--allowed-dir", required=True, action="append",
                        help="one per transcript, in the same order")
    args = parser.parse_args(argv)
    if len(args.transcript) != len(args.allowed_dir):
        raise SystemExit("give one --allowed-dir per --transcript")
    reports = [audit(Path(t), d) for t, d in zip(args.transcript, args.allowed_dir, strict=True)]
    print(json.dumps(reports, indent=2))
    return 0 if all(r["clean"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
