#!/usr/bin/env python3
"""G1: panel packets for the items of M0 v2.2 that changed after the M0 v2.1 review (S20, S26, S92; journal J15.1-038).

Exactly `s193_m0v21_panel_packets.py` (loaded and run) with: the committed `data/v2/dataset/m0_v22/` as input, only the changed
structures as items (`M0V22-<structure_id>`), and run ids `m0v22_admission` / `m0v22_naturalness` on scratch. Every role sentence
of a changed structure is re-rated for naturalness (not only the rewritten ones), so each structure's 6.1 check rests on one run.
The eight unchanged structures keep their M0 v2.1 verdicts. Deterministic; refuses to overwrite.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import roles_m0v22  # noqa: E402


def _load_s193():
    spec = importlib.util.spec_from_file_location("s193_m0v21_panel_packets", REPO_ROOT / "scripts/v2/s193_m0v21_panel_packets.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["s193_m0v21_panel_packets"] = module
    spec.loader.exec_module(module)
    return module


CHANGED = ("S20", "S26", "S92")
s193 = _load_s193()
s193.roles_m0v21 = SimpleNamespace(
    ROLE_SPECS={sid: roles_m0v22.ROLE_SPECS[sid] for sid in CHANGED},
    structure=roles_m0v22.structure,
    RELATION_NOTES=roles_m0v22.RELATION_NOTES,
)
s193.ITEM_PREFIX = "M0V22-"
s193.CELLS = "data/v2/dataset/m0_v22/cells.jsonl"
s193.CERTIFICATES = "data/v2/dataset/m0_v22/certificates.json"
s193.OUT_DIR = "docs/validation/v2/llm_panel/admission_m0v22"
s193.ADMISSION_RUN, s193.NATURALNESS_RUN = "m0v22_admission", "m0v22_naturalness"


def configure(items: tuple[str, ...], tag: str) -> None:
    """Restrict the run to `items` under run tag `tag` (second round: `--items S26 --tag m0v22b`, journal J15.1-039)."""

    s193.roles_m0v21.ROLE_SPECS = {sid: roles_m0v22.ROLE_SPECS[sid] for sid in items}
    s193.ITEM_PREFIX = tag.upper() + "-"
    s193.OUT_DIR = f"docs/validation/v2/llm_panel/admission_{tag}"
    s193.ADMISSION_RUN, s193.NATURALNESS_RUN = f"{tag}_admission", f"{tag}_naturalness"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--items", nargs="+", default=list(CHANGED))
    parser.add_argument("--tag", default="m0v22")
    args = parser.parse_args(argv)
    configure(tuple(args.items), args.tag)
    return s193.main(["--out", s193.OUT_DIR])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
