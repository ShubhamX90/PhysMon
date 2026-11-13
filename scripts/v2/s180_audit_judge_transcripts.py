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
    violations, n_calls = [], 0
    allowed = allowed_dir.rstrip("/")
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for use in _tool_uses(obj):
            n_calls += 1
            name = str(use.get("name", ""))
            text = json.dumps(use.get("input", {}), ensure_ascii=False)
            if name in WEB_TOOLS:
                violations.append({"tool": name, "reason": "web access", "input": text[:300]})
                continue
            hit = [p for p in FORBIDDEN_PATTERNS if p in text]
            paths = re.findall(r"(/[A-Za-z0-9_.\-/]+)", text)
            outside = [p for p in paths if not p.startswith(allowed) and not p.startswith(("/dev/null", "/tmp/claude"))]
            if hit or outside:
                violations.append({"tool": name, "forbidden": hit, "outside_paths": outside[:5], "input": text[:300]})
    return {"transcript": str(transcript), "allowed_dir": allowed, "n_tool_calls": n_calls,
            "violations": violations, "clean": not violations and n_calls > 0}


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
