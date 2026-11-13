#!/usr/bin/env python3
"""Stage 15 (G1): prepare judge batches for one qualification run under the frozen protocol.

Batches hold up to four items, never two of the same base structure or legacy family (so no judge can compare
variants). Each batch directory on scratch holds only `<item>_pass1_packet.json` and `<item>_pass2_packet.json` and an
empty `out/` for the reviews; the key never leaves the repository. The assignment (batch -> items, directory, reviewer
id) is written to <assignment>.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED = 42
BATCH = 4


def make_batches(items: list[str], group_of: dict[str, str], seed: int = SEED, size: int = BATCH) -> list[list[str]]:
    """Greedy first-fit over a seeded shuffle: each batch takes items whose group it does not already hold."""

    order = list(items)
    random.Random(seed).shuffle(order)
    batches: list[list[str]] = []
    for item in order:
        for batch in batches:
            if len(batch) < size and all(group_of[o] != group_of[item] for o in batch):
                batch.append(item)
                break
        else:
            batches.append([item])
    return batches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bank", default="docs/validation/v2/llm_panel/bank_v3")
    parser.add_argument("--split", default="qualification", choices=("qualification", "heldout"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", default="/scratch/pabitra/physmon/judge")
    parser.add_argument("--assignment", required=True)
    args = parser.parse_args(argv)
    bank = REPO_ROOT / args.bank
    key = json.loads((bank / "key_RESTRICTED.json").read_text(encoding="utf-8"))
    p1 = {json.loads(x)["item_id"]: json.loads(x) for x in (bank / "pass1_packets.jsonl").read_text().splitlines() if x}
    p2 = {json.loads(x)["item_id"]: json.loads(x) for x in (bank / "pass2_packets.jsonl").read_text().splitlines() if x}
    items = sorted(i for i, k in key.items() if k["split"] == args.split)
    groups = {i: key[i]["structure_id"] for i in items}
    batches = make_batches(items, groups)
    run_dir = Path(args.root) / args.run_id
    if run_dir.exists() or Path(args.assignment).exists():
        print(f"Refusing to overwrite {run_dir} or {args.assignment}", file=sys.stderr)
        return 2
    assignment = {"run_id": args.run_id, "bank": args.bank, "split": args.split, "seed": SEED, "batches": []}
    for n, batch in enumerate(batches, 1):
        d = run_dir / f"batch{n:02d}"
        (d / "out").mkdir(parents=True)
        for item in batch:
            (d / f"{item}_pass1_packet.json").write_text(json.dumps(p1[item], indent=2, ensure_ascii=False))
            (d / f"{item}_pass2_packet.json").write_text(json.dumps(p2[item], indent=2, ensure_ascii=False))
        assignment["batches"].append({"batch": f"batch{n:02d}", "dir": str(d), "items": batch,
                                      "reviewer_id": f"claude-opus-5-5:{args.run_id}:batch{n:02d}"})
    Path(args.assignment).parent.mkdir(parents=True, exist_ok=True)
    Path(args.assignment).write_text(json.dumps(assignment, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"n_items": len(items), "n_batches": len(batches),
                      "sizes": sorted(len(b) for b in batches)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
