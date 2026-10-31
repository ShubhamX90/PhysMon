#!/usr/bin/env python3
"""Stage 14.20: re-grade the answers of a thinking run with the unit-convertible sensitivity label (CPU only).

Reads raw records, re-parses each generation with the thinking parser and grades it twice: with the declared rule (unit must match) and
with `unit_convertible.classify_convertible`. Writes a per-record CSV and a summary to a new attempt directory; the raw records are not
touched. It exists to quantify, for a run made before the label existed, how many answers were wrong only by a unit of the same quantity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.scoring import unit_convertible as uc  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402

OUT_ROOT = "results/stage14/s166_regrade_units"


def _load_runner():
    spec = importlib.util.spec_from_file_location("s164_thinking_run", REPO_ROOT / "scripts/v2/s164_thinking_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def regrade(records: list[dict], runner) -> list[dict]:
    rows = []
    for r in records:
        result, _, _, _ = runner.parse_thinking_output(r["generated_answer_raw"], r["hit_token_limit"])
        parsed = result.parsed
        declared = vs.classify_answer(parsed, float(r["gold_value"]), r["gold_unit"])
        convertible = uc.classify_convertible(parsed, float(r["gold_value"]), r["gold_unit"])
        rows.append({"job_id": r["job_id"], "structure_id": r["structure_id"], "instance": r["instance"], "stored_correctness": r["correctness"],
                     "declared": declared, "convertible": convertible,
                     "answer": "" if parsed.status != "PARSED" else f"{parsed.value_text} {parsed.unit}", "gold": f"{r['gold_value']:.6g} {r['gold_unit']}",
                     "changed": declared != convertible})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--out-root", default=OUT_ROOT)
    args = parser.parse_args()
    out_dir = (REPO_ROOT / args.out_root / args.attempt_id).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2
    records = [json.loads(line) for line in Path(args.records).read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = regrade(records, _load_runner())
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "regrade.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["job_id"])
        writer.writeheader()
        writer.writerows(rows)
    summary = {"stage": "14.20", "records": args.records, "records_sha256": hashlib.sha256(Path(args.records).read_bytes()).hexdigest(),
               "n": len(rows), "declared": dict(Counter(r["declared"] for r in rows)), "convertible": dict(Counter(r["convertible"] for r in rows)),
               "n_changed": sum(r["changed"] for r in rows), "changed": [r for r in rows if r["changed"]],
               "stored_matches_declared": all(r["stored_correctness"] == r["declared"] for r in rows),
               "note": "sensitivity label only; the declared rule remains the primary grade; ungraded outcomes are unchanged"}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n", "declared", "convertible", "n_changed", "stored_matches_declared")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
