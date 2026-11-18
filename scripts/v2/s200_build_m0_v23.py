#!/usr/bin/env python3
"""Stage 15: build M0 v2.3 (`data/v2/dataset/m0_v23/`): M0 v2.2 revised for the legitimate flags of the GPT judge (J15.1-046).

The builder logic is exactly `s192_build_m0_v21.py` (loaded and run with the M0 v2.3 specs, `roles_m0v23.py`, as `s195` does for v2.2);
`m0_v21` and `m0_v22` stay unchanged as the record of the reviews. What changes (reasons and old -> new wording in `roles_m0v23.py`):

* rule 7: pair-1 D events that attach or add something in an earlier experiment say "for an earlier experiment only" (S01, S07,
  S13, S15, S92);
* rule 6: answer-determining conditions stated in the scene clause (S07 leakage and ideal batteries and wires, S27 liquid at rest and
  open to the same air, S30 no heat loss and no boiling, S55 thermally insulated flasks);
* S07 K_out rationale corrected; S26 tilt starts from the stated angle; S27 C sentences name the first tank and vertical sides;
  S55 pair-1 R/D start from the stated temperature; S92 pours liquid into the empty second tank (rule 8).

Deterministic; refuses to overwrite. Status: solver-certified; not yet reviewed by the two-judge panel. Data role: EXPLORATION.
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

from physmon.benchmark.v2 import roles_m0v23  # noqa: E402


def _load_s192():
    spec = importlib.util.spec_from_file_location("s192_build_m0_v21", REPO_ROOT / "scripts/v2/s192_build_m0_v21.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["s192_build_m0_v21"] = module
    spec.loader.exec_module(module)
    return module


s192 = _load_s192()
s192.roles_m0v21 = roles_m0v23  # the builder reads ROLE_SPECS and structure() from this name at call time
s192.VERSION = VERSION = "m0_v2.3"
s192.STATUS = STATUS = ("solver-certified; M0 v2.2 revised for the GPT judge's legitimate flags (J15.1-046; wording rules 1-8); "
                        "not yet reviewed by the two-judge panel (Claude and GPT) or a human")


def readme(counts: dict[str, Any], certificates: dict[str, Any], excluded: list, rows: list[dict[str, Any]]) -> str:
    kinds = counts["by_d_kind_d_cells"]
    changes = [f"* **{sid}**: " + "; ".join(f"`{old}` -> `{new}`" for old, new in pairs)
               for sid, pairs in sorted(roles_m0v23.CHANGES.items())]
    lines = [
        "# M0 v2.3: M0 v2.2 revised for the GPT judge's flags", "",
        f"Data role: **{s192.DATA_ROLE}**. Status: **{STATUS}**.", "",
        f"{counts['n_cells']} cells on {counts['n_structures']} structures (instance 0 of each), a gold solving trace for every "
        "cell. Built by `scripts/v2/s200_build_m0_v23.py` (the M0 v2.1 builder run with `src/physmon/benchmark/v2/roles_m0v23.py`). "
        "`m0_v21` and `m0_v22` are unchanged and are the record of the earlier reviews "
        "(`docs/validation/v2/llm_panel/admission_m0v21/`, `admission_m0v22/`, `admission_m0v22b/`).", "",
        "## What changed against M0 v2.2, and why (journal J15.1-046)", "",
        "S02 stays rejected. The structures are fixed before any model run (no model output exists on M0 v2.2). Old -> new "
        "wording (templates; `{v}` is the study value):", "", *changes, "",
        "S72 and S20: no sentence changed (S72's numeral-free N sentences are explained as controls in the panel packets).", "",
        f"D cells by kind: {kinds}. By stratum: {counts['by_stratum']}.", "",
        "## What has not been done", "",
        "No review of M0 v2.3 yet (two-judge admission, Claude and GPT, is required); no model has seen the cells.", ""]
    if excluded:
        lines += ["## Excluded structures", "", json.dumps(excluded), ""]
    return "\n".join(lines)


s192.readme = readme


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/v2/dataset/m0_v23")
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
