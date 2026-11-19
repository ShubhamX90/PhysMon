#!/usr/bin/env python3
"""Stage 15: build M0 v2.5 (`data/v2/dataset/m0_v25/`): M0 v2.4 with two N sentences rewritten after the naturalness review (J15.1-051).

The builder logic is exactly `s192_build_m0_v21.py` (loaded and run with the M0 v2.5 specs, `roles_m0v25.py`, as `s202` does for
v2.4); `m0_v21` to `m0_v24` stay unchanged as the record of the reviews. What changes (reasons and old -> new wording in
`roles_m0v25.py`):

* S26 D0/N0: the camera is tilted "farther from the vertical to keep the ray in view" (an ordinary purposeful action, rule 3);
* S55 pair 1: no "Once the sample was in equilibrium"; R1 "Just before the molecular speeds are measured, a heater warmed this gas
  sample by ...", D1 "In an earlier experiment, a heater warmed this gas sample by ...".

The build refuses any spec whose `version` is not the full-rule-set certificate version ("v2.1"): a spec outside it would be
certified with the weaker rule set. Deterministic; refuses to overwrite. Status: solver-certified; not yet re-reviewed by the
two-judge panel. Data role: EXPLORATION.
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

from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m0v25  # noqa: E402


def _load_s192():
    spec = importlib.util.spec_from_file_location("s192_build_m0_v21", REPO_ROOT / "scripts/v2/s192_build_m0_v21.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["s192_build_m0_v21"] = module
    spec.loader.exec_module(module)
    return module


s192 = _load_s192()
s192.roles_m0v21 = roles_m0v25  # the builder reads ROLE_SPECS and structure() from this name at call time
s192.VERSION = VERSION = "m0_v2.5"
s192.STATUS = STATUS = ("solver-certified; M0 v2.4 with two N sentences rewritten after the naturalness review (S26 D0/N0, S55 "
                        "pair 1; J15.1-051); S26 and S55 not yet re-reviewed by the two-judge panel")


def check_versions() -> None:
    """Refuse to build when any spec would be certified without the full rule set (`certify_v2` keys it on `version == v2.1`)."""

    wrong = sorted(sid for sid, spec in roles_m0v25.ROLE_SPECS.items() if spec.version != r2.VERSION_V21)
    if wrong:
        raise SystemExit(f"specs {wrong} are not version {r2.VERSION_V21!r}: they would skip the full certificate rule set")


def readme(counts: dict[str, Any], certificates: dict[str, Any], excluded: list, rows: list[dict[str, Any]]) -> str:
    kinds = counts["by_d_kind_d_cells"]
    changes = [f"* **{sid}**: " + "; ".join(f"`{old}` -> `{new}`" for old, new in pairs)
               for sid, pairs in sorted(roles_m0v25.CHANGES.items())]
    lines = [
        "# M0 v2.5: M0 v2.4 with two N sentences rewritten after the naturalness review", "",
        f"Data role: **{s192.DATA_ROLE}**. Status: **{STATUS}**.", "",
        f"{counts['n_cells']} cells on {counts['n_structures']} structures (instance 0 of each), a gold solving trace for every "
        "cell. Built by `scripts/v2/s204_build_m0_v25.py` (the M0 v2.1 builder run with `src/physmon/benchmark/v2/roles_m0v25.py`). "
        "`m0_v21` to `m0_v24` are unchanged and are the record of the earlier reviews "
        "(`docs/validation/v2/llm_panel/admission_m0v21/` ... `admission_m0v24/`).", "",
        "## What changed against M0 v2.4, and why (journal J15.1-051)", "",
        "Both qualified judges admitted the four changed structures of M0 v2.4; the naturalness rater rated S26 N0 and S55 N1 "
        "artificial. No model has seen any M0 cell. Old -> new wording (templates; `{v}` is the study value; N is the numeral-free "
        "control):", "", *changes, "",
        "The other nine structures are the M0 v2.4 specs unchanged.", "",
        f"D cells by kind: {kinds}. By stratum: {counts['by_stratum']}.", "",
        "## What has not been done", "",
        "S26 and S55 have not been re-reviewed by the two-judge panel; no model has seen the cells.", ""]
    if excluded:
        lines += ["## Excluded structures", "", json.dumps(excluded), ""]
    return "\n".join(lines)


s192.readme = readme
_build_v21 = s192.build


def build(out: Path, dataset: Path) -> dict[str, Any]:
    check_versions()
    return _build_v21(out, dataset)


s192.build = build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/v2/dataset/m0_v25")
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
