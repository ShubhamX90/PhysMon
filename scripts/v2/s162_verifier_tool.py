#!/usr/bin/env python3
"""Stage 14.19: blind-verification tool for the gold dataset (CPU only).

`packet` writes the problems of a domain module (new structures and any existing ones named by `--ids`) as opaque items WITHOUT gold
answers or traces, so a separate agent can solve them blind; the key that maps items back to structures goes to a separate file.
`compare` reads the blind answers and the key and reports, for each item, the gold answer, the blind answer, the relative error and
whether the unit and the value (within 0.5%) match. A mismatch is a lead for review, not a verdict: either side may be wrong.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import design as dg  # noqa: E402

EXISTING = ("library", "library_b", "library_c")
TOLERANCE = 5e-3


def structures_of(module_name: str, ids: list[str] | None, extra: list[str] | None = None) -> list:
    """The module's own structures (or exactly `ids` if given) plus the existing ones named by `extra`."""

    pool = {}
    for name in EXISTING:
        for s in importlib.import_module(f"physmon.benchmark.v2.{name}").all_structures():
            pool[s.structure_id] = s
    module = importlib.import_module(module_name)
    if hasattr(module, "all_structures"):
        for s in module.all_structures():
            pool[s.structure_id] = s
    own = [s.structure_id for s in (module.all_structures() if hasattr(module, "all_structures") else [])]
    wanted = list(ids) if ids else own + [e for e in (extra or []) if e not in own]
    return [pool[i] for i in wanted]


def prompt_of(structure, instance: int) -> str:
    display = dict(structure.instances[instance])
    return f"{dg.context_text(structure, display)} {dg.question_text(structure, display)}"


def cmd_packet(args) -> int:
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    items, key = [], []
    n = 0
    for s in structures_of(args.module, args.only, args.ids):
        for i in range(len(s.instances)):
            n += 1
            item = f"q{n:03d}"
            items.append({"item": item, "problem": prompt_of(s, i), "answer_unit": dg.display_unit(s.render.target_unit)})
            key.append({"item": item, "structure_id": s.structure_id, "instance": i})
    (out / "packet.json").write_text(json.dumps(items, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    key_path = Path(args.key_out) if args.key_out else out / "key.json"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(items)} items to {out}/packet.json and the private key elsewhere (do not look for it when solving)")
    return 0


def cmd_compare(args) -> int:
    key = {k["item"]: k for k in json.loads(Path(args.key).read_text(encoding="utf-8"))}
    answers = {a["item"]: a for a in json.loads(Path(args.answers).read_text(encoding="utf-8"))}
    by_id = {s.structure_id: s for s in structures_of(args.module, sorted({k["structure_id"] for k in key.values()}))}
    mismatches = 0
    print("item  structure#inst  gold  blind  rel_err  unit  status")
    for item, k in sorted(key.items()):
        s = by_id[k["structure_id"]]
        gold = dg.gold_for(s, dict(s.instances[k["instance"]]))
        unit = dg.display_unit(s.render.target_unit)
        a = answers.get(item)
        if a is None:
            print(f"{item} {k['structure_id']}#{k['instance']} {gold:.6g} - - - NO_ANSWER")
            mismatches += 1
            continue
        err = abs(a["value"] - gold) / abs(gold) if gold else abs(a["value"])
        unit_ok = str(a.get("unit", "")).strip() == unit
        status = "MATCH" if err <= TOLERANCE and unit_ok else "MISMATCH"
        mismatches += status != "MATCH"
        print(f"{item} {k['structure_id']}#{k['instance']} gold={gold:.6g} {unit} blind={a['value']:.6g} {a.get('unit', '')} err={err:.3g} {status}")
    print(f"SUMMARY items={len(key)} mismatches={mismatches}")
    return 0 if mismatches == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("packet")
    p.add_argument("--module", required=True)
    p.add_argument("--ids", nargs="*", default=None, help="existing structures to include besides the module's own")
    p.add_argument("--only", nargs="*", default=None, help="exactly these structures (new or existing)")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--key-out", default=None, help="where to write the private key (default: next to the packet)")
    c = sub.add_parser("compare")
    c.add_argument("--module", required=True)
    c.add_argument("--key", required=True)
    c.add_argument("--answers", required=True)
    args = parser.parse_args()
    return cmd_packet(args) if args.cmd == "packet" else cmd_compare(args)


if __name__ == "__main__":
    raise SystemExit(main())
