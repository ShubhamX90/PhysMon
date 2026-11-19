#!/usr/bin/env python3
"""G1: panel packets for the four structures of M0 v2.4 that changed after the M0 v2.3 review (S26, S55, S72, S92; J15.1-048).

Exactly `s193_m0v21_panel_packets.py` (loaded and run) with: the committed `data/v2/dataset/m0_v24/` as input (or `--data-dir`), only
the changed structures as items (`M0V24-<structure_id>`, admission batches of 2), run ids `m0v24_admission` / `m0v24_naturalness`
(scratch: `/scratch/pabitra/physmon/judge/m0v24_*`) and output `docs/validation/v2/llm_panel/admission_m0v24/`. Every role sentence of a
changed structure is re-rated for naturalness. The seven unchanged structures keep their M0 v2.3 verdicts (spec objects identical).
As in s201, the pass-2 claim of every numeral-free N sentence carries `numeral_free_note`. Deterministic; refuses to overwrite.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import roles_m0v24  # noqa: E402

CHANGED = roles_m0v24.CHANGED
N_NOTE = ("This sentence is the numeral-free control by design: it deliberately carries no number; the matching D sentence "
          "carries the number.")


def _load_s193():
    spec = importlib.util.spec_from_file_location("s193_m0v21_panel_packets", REPO_ROOT / "scripts/v2/s193_m0v21_panel_packets.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["s193_m0v21_panel_packets"] = module
    spec.loader.exec_module(module)
    return module


s193 = _load_s193()
s193.roles_m0v21 = SimpleNamespace(
    ROLE_SPECS={sid: roles_m0v24.ROLE_SPECS[sid] for sid in CHANGED},
    structure=roles_m0v24.structure,
    RELATION_NOTES=roles_m0v24.RELATION_NOTES,
)
s193.ITEM_PREFIX = "M0V24-"
s193.CELLS = "data/v2/dataset/m0_v24/cells.jsonl"
s193.CERTIFICATES = "data/v2/dataset/m0_v24/certificates.json"
s193.OUT_DIR = "docs/validation/v2/llm_panel/admission_m0v24"
s193.ADMISSION_RUN, s193.NATURALNESS_RUN = "m0v24_admission", "m0v24_naturalness"

_build_item_v21 = s193.build_item


def build_item(structure_id: str, cells: list[dict[str, Any]]) -> dict[str, Any]:
    """The s193 item with the numeral-free note added to the claim of every N sentence."""

    item = _build_item_v21(structure_id, cells)
    for sentence in item["sentences"]:
        if sentence["stratum"] == "N":
            sentence["claim"]["numeral_free_note"] = N_NOTE
    return item


s193.build_item = build_item


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=s193.OUT_DIR)
    parser.add_argument("--scratch", default=s193.SCRATCH)
    parser.add_argument("--data-dir", default="data/v2/dataset/m0_v24", help="the built M0 v2.4 directory")
    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir) if Path(args.data_dir).is_absolute() else REPO_ROOT / args.data_dir
    s193.CELLS, s193.CERTIFICATES = str(data_dir / "cells.jsonl"), str(data_dir / "certificates.json")
    return s193.main(["--out", args.out, "--scratch", args.scratch])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
