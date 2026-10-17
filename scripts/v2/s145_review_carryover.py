#!/usr/bin/env python3
"""Stage 14.5: carry a recorded bank review from one materials version to the next, exactly where nothing changed.

A v2 bank item inherits the v1 verdict only if its (family, defect type) was reviewed in v1 and its edited prompt, equation
and answer are byte-identical; anything else is NEEDS_REVIEW. Item ids are reshuffled between versions, so both ids are
recorded. Reads committed files only; writes `bank_review_status.json` next to the new bank. It never invents a verdict.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-dir", required=True)
    parser.add_argument("--new-dir", required=True)
    parser.add_argument("--old-review", required=True, help="bank_confirmation_*.json for the old version")
    args = parser.parse_args()
    bank = "planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl"
    old = {(r["family"], r["defect_type"]): r for r in rows(Path(args.old_dir) / bank)}
    new = rows(Path(args.new_dir) / bank)
    review = json.loads(Path(args.old_review).read_text(encoding="utf-8"))
    verdicts = {(i["family"], i["defect_type"]): i for i in review["items"]}
    out = []
    for row in sorted(new, key=lambda r: r["item_id"]):
        key = (row["family"], row["defect_type"])
        before = old.get(key)
        fields = ("edited_variant0_prompt", "edited_equation", "edited_answer")
        entry = {"item_id": row["item_id"], "family": row["family"], "defect_type": row["defect_type"]}
        if before and all(before[f] == row[f] for f in fields):
            entry.update(status="CARRIED_FROM_REVIEW", old_item_id=before["item_id"],
                         old_verdict=verdicts[key]["verdict"], old_note=verdicts[key]["note"])
        else:
            entry.update(status="NEEDS_REVIEW", reason="new item" if before is None else "edited text changed")
            if before:
                entry.update(old_item_id=before["item_id"], old_verdict=verdicts[key]["verdict"])
        out.append(entry)
    counts: dict[str, int] = {}
    for entry in out:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    doc = {"old_dir": args.old_dir, "new_dir": args.new_dir, "old_review": args.old_review,
           "reviewer_note": review["reviewer"], "reviewer_is_a_physicist": review["reviewer_is_a_physicist"],
           "counts": counts, "items": out}
    (Path(args.new_dir) / "bank_review_status.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                                                                 encoding="utf-8")
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
