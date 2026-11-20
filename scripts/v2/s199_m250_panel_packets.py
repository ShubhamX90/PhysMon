#!/usr/bin/env python3
"""G1: judge-panel packets for the machine-admitted M250 structures (admission standard sections 5 and 6).

Exactly `s193_m0v21_panel_packets.py` (loaded and run, by the same patching pattern as `s196_m0v22_panel_packets.py`) with:

* the input `data/v2/dataset/m250_explore_v1/` (built by `s198_build_m250_exploration.py`; read-only): the items are the structures whose
  `admission/<id>.json` has status MACHINE_ADMITTED and a panel status that is not already ADMITTED (the M0 v2.5 structures were reviewed by the two-judge panel and are skipped), item prefix `M250-`;
* run ids `m250_admission` and `m250_naturalness`; admission batches of 4 items; naturalness batches of up to 24 sentences, at most 2
  per structure and never two sentences of one group in one structure;
* output `docs/validation/v2/llm_panel/admission_m250/` and scratch `/scratch/pabitra/physmon/judge/m250_*`.

The restricted key files hold roles and never go to a judge; every packet is leak-scanned. Deterministic; refuses to overwrite.
Repair rounds: `--round r1 --ids S03,... --run-prefix m250r1 --dataset data/v2/dataset/m250_explore_v2 --out <dir>` packages only the
changed structures with the r1 spec modules.
Usage: s199_m250_panel_packets.py [--dataset DIR] [--out DIR] [--scratch DIR] [--round v1|r1] [--ids S..,S..] [--run-prefix P]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

DATASET = "data/v2/dataset/m250_explore_v1"
OUT_DIR = "docs/validation/v2/llm_panel/admission_m250"
SCRATCH = "/scratch/pabitra/physmon/judge"
ITEM_PREFIX = "M250-"
ADMISSION_BATCH = 4
NATURALNESS_BATCH = 24


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


s193 = _load("s193_m0v21_panel_packets", "scripts/v2/s193_m0v21_panel_packets.py")
s198 = _load("s198_build_m250_exploration", "scripts/v2/s198_build_m250_exploration.py")
leak_scan = s193.leak_scan


def packet_structures(dataset: Path) -> list[str]:
    """Structure ids with a MACHINE_ADMITTED record and no panel admission yet (M0 v2.5 is skipped), sorted by number."""

    ids = []
    for path in sorted((dataset / "admission").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") == s198.ADMITTED and record.get("panel", {}).get("status") != "ADMITTED":
            ids.append(record["structure_id"])
    return sorted(ids, key=s198.sid_key)


N_NOTE = ("This sentence is the numeral-free control by design: it deliberately carries no number; the matching D sentence carries "
          "the number.")


def with_n_note(build_item):
    """Wrap `s193.build_item` so that the claim of every N sentence carries the note (the GPT judge misread N sentences)."""

    def wrapped(structure_id, cells):
        item = build_item(structure_id, cells)
        for sentence in item["sentences"]:
            if sentence["stratum"] == "N":
                sentence["claim"]["note"] = N_NOTE
        return item

    return wrapped


def configure(dataset: Path, ids: list[str], sources: list, run_prefix: str = "m250") -> None:
    """Point the M0 v2.1 packet script at the M250 dataset and the specs of `ids` (the same patching pattern as s196)."""

    by_id = {sid: source for source in sources if not source.error for sid in source.specs if sid in ids}
    missing = sorted(set(ids) - set(by_id))
    if missing:
        raise SystemExit(f"no spec module provides {missing}")
    s193.roles_m0v21 = SimpleNamespace(
        ROLE_SPECS={sid: by_id[sid].specs[sid] for sid in ids}, structure=lambda sid: by_id[sid].structure(sid),
        RELATION_NOTES={})
    if not getattr(s193.build_item, "n_note", False):
        s193.build_item = with_n_note(s193.build_item)
        s193.build_item.n_note = True
    s193.ITEM_PREFIX = ITEM_PREFIX
    s193.CELLS = str(dataset / "cells.jsonl")
    s193.CERTIFICATES = str(dataset / "certificates.json")
    s193.OUT_DIR = OUT_DIR
    s193.ADMISSION_RUN, s193.NATURALNESS_RUN = f"{run_prefix}_admission", f"{run_prefix}_naturalness"
    s193.ADMISSION_BATCH, s193.NATURALNESS_BATCH = ADMISSION_BATCH, NATURALNESS_BATCH


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default=DATASET)
    parser.add_argument("--out", default=OUT_DIR)
    parser.add_argument("--scratch", default=SCRATCH)
    parser.add_argument("--round", choices=sorted(s198.ROUNDS), default="v1", help="spec modules of the build (s198 --round)")
    parser.add_argument("--ids", default="", help="comma-separated structure ids: package only these (a re-review of changed structures)")
    parser.add_argument("--run-prefix", default="m250", help="run ids <prefix>_admission / <prefix>_naturalness (scratch dirs)")
    args = parser.parse_args(argv)
    dataset = Path(args.dataset) if Path(args.dataset).is_absolute() else REPO_ROOT / args.dataset
    if not (dataset / "admission").is_dir():
        print(f"No built M250 dataset at {dataset}", file=sys.stderr)
        return 2
    ids = packet_structures(dataset)
    wanted = [x.strip() for x in args.ids.split(",") if x.strip()]
    if wanted:
        unknown = sorted(set(wanted) - set(ids))
        if unknown:
            print(f"--ids not machine-admitted (or already panel-admitted) in {dataset}: {unknown}", file=sys.stderr)
            return 2
        ids = [sid for sid in ids if sid in set(wanted)]
    if not ids:
        print("No machine-admitted non-M0 structure to review", file=sys.stderr)
        return 2
    configure(dataset, ids, s198.discover(s198.ROUNDS[args.round][0]), args.run_prefix)
    return s193.main(["--out", args.out, "--scratch", args.scratch])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
