#!/usr/bin/env python3
"""Stage 15: build M0 v2.2 (`data/v2/dataset/m0_v22/`): M0 v2.1 revised after its LLM panel review (journal J15.1-038).

The builder logic is exactly `s192_build_m0_v21.py` (loaded and run with the M0 v2.2 specs, `roles_m0v22.py`); `m0_v21` stays
unchanged as the record of the review. What changes (reasons in `roles_m0v22.py`):

* S02 rejected by the panel and replaced: not in M0 v2.2 (11 structures);
* S92 pair 1 R states the change of liquid as an event in this tank, with the same string, before the measurement;
* S20 and S26 pair 0: co-present objects rated artificial (a stool pushed, a desk lamp tilted) replaced by a lamp that lights
  the object and a camera that films the interface.

Deterministic; refuses to overwrite. Status: solver-certified and admitted by the Claude judge (J15.1-038, J15.1-039). Data role: EXPLORATION.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import roles_m0v22  # noqa: E402


def _load_s192():
    spec = importlib.util.spec_from_file_location("s192_build_m0_v21", REPO_ROOT / "scripts/v2/s192_build_m0_v21.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["s192_build_m0_v21"] = module
    spec.loader.exec_module(module)
    return module


s192 = _load_s192()
s192.roles_m0v21 = roles_m0v22  # the builder reads ROLE_SPECS and structure() from this name at call time
s192.VERSION = VERSION = "m0_v2.2"
s192.STATUS = STATUS = ("solver-certified; all 11 structures ADMITTED by the qualified Claude judge (prompt v3) with no sentence "
                        "rated artificial (M0 v2.1 review, J15.1-038; S20, S26, S92 re-reviewed, J15.1-039); not yet reviewed by "
                        "GPT or a human")


def readme(counts: dict[str, Any], certificates: dict[str, Any], excluded: list, rows: list[dict[str, Any]]) -> str:
    kinds = counts["by_d_kind_d_cells"]
    lines = [
        "# M0 v2.2: M0 v2.1 revised after its LLM panel review", "",
        f"Data role: **{s192.DATA_ROLE}**. Status: **{STATUS}**.", "",
        f"{counts['n_cells']} cells on {counts['n_structures']} structures (instance 0 of each), a gold solving trace for every "
        "cell. Built by `scripts/v2/s195_build_m0_v22.py` (the M0 v2.1 builder run with `src/physmon/benchmark/v2/roles_m0v22.py`). "
        "`m0_v21` is unchanged and is the record of the review (`docs/validation/v2/llm_panel/admission_m0v21/`).", "",
        "## What changed against M0 v2.1, and why", "",
        "* **S02 rejected and replaced** (not in M0 v2.2): " + roles_m0v22.REJECTED["S02"],
        "* **S92 pair 1 R** reworded: the judge's high flag (the question's present tense left open whether the later liquid "
        "applies, and the sentence did not say the same string held the cube in this tank).",
        "* **S20 and S26 pair 0**: the co-present object is a lamp that lights the object (S20) and a camera that films the interface "
        "(S26), replacing a stool pushed and a desk lamp tilted, which blind raters called pointless actions (rated artificial).",
        "", f"D cells by kind: {kinds}. By stratum: {counts['by_stratum']}.", "",
        "## What has not been done", "",
        "No GPT or human review yet (evidence class LLM_PANEL, one judge); no model has seen the cells.",
        ""]
    if excluded:
        lines += ["## Excluded structures", "", json.dumps(excluded), ""]
    return "\n".join(lines)


s192.readme = readme


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/v2/dataset/m0_v22")
    parser.add_argument("--dataset", default="data/v2/dataset/v1/dataset.jsonl")
    args = parser.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else REPO_ROOT / args.out
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    summary = s192.build(out, REPO_ROOT / args.dataset)
    print(json.dumps({k: summary[k] for k in ("n_cells", "n_structures", "by_family", "by_stratum", "excluded")}, indent=2))
    return 0 if not summary["excluded"] else 1


if __name__ == "__main__":
    sys.exit(main())
