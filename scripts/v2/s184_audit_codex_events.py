#!/usr/bin/env python3
"""Stage 15 (G1): audit the `codex exec --json` event logs of a GPT judge run for independence violations.

A judge call must consist of the model's own reasoning and final message. Any command execution, file read or change, tool
call or web search in the event stream is a violation (the judge was told to use none), as is any mention of the answer key
or the repository in the stream. A log with no events cannot show that a call was clean and is not clean. A flagged call
voids that item's reviews under the qualification protocol.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

BAD_TYPE_PARTS = ("command", "exec", "file", "patch", "mcp", "tool", "web", "search", "shell", "read", "write")
FORBIDDEN_TEXT = ("key_RESTRICTED", "packet_key", "PhysMons", "planted_defect", "rolevalue_bank", "bank_v3",
                  "llm_panel/bank", "roles_m0", "s178_")


def audit_file(path: Path) -> dict[str, Any]:
    kinds: Counter = Counter()
    violations = []
    n_events = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        n_events += 1
        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        kind = str(item.get("type") or event.get("type"))
        kinds[kind] += 1
        if item and any(part in str(item.get("type", "")).lower() for part in BAD_TYPE_PARTS):
            violations.append({"reason": "tool or file activity", "type": item.get("type"),
                               "detail": json.dumps(item, ensure_ascii=False)[:200]})
        if event.get("type") in ("error", "turn.failed"):
            violations.append({"reason": "error event", "detail": json.dumps(event, ensure_ascii=False)[:200]})
        text = json.dumps(event, ensure_ascii=False)
        hit = [p for p in FORBIDDEN_TEXT if p in text]
        if hit:
            violations.append({"reason": "forbidden text in the stream", "forbidden": hit, "detail": text[:200]})
    return {"file": path.name, "n_events": n_events, "event_kinds": dict(kinds), "violations": violations,
            "clean": n_events > 0 and not violations}


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--events", required=True, help="the run's events/ directory")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    reports = [audit_file(p) for p in sorted(Path(args.events).glob("*.jsonl"))]
    summary = {"n_files": len(reports), "n_clean": sum(r["clean"] for r in reports),
               "flagged": [r["file"] for r in reports if not r["clean"]],
               "event_kinds": dict(sum((Counter(r["event_kinds"]) for r in reports), Counter()))}
    result = {"summary": summary, "files": reports}
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if reports and not summary["flagged"] else 1


if __name__ == "__main__":
    sys.exit(main())
