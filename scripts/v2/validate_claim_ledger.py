#!/usr/bin/env python3
"""Validate the Research v2.0 claim-to-artifact ledger.

Reads `docs/registry/v2/claim_ledger.jsonl` (or `--ledger`), applies the contract in
`physmon.governance.v2_contract`, and exits non-zero on any error. CPU only; stdlib only; writes
nothing unless `--output` is given. A missing or empty ledger is an error, never a pass.

Plan reference: v2 P0.1 (p.16), §8.4 (p.42), §9.1 (p.43).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance.v2_contract import (  # noqa: E402
    missing_artifact_paths,
    validate_ledger_rows,
)

DEFAULT_LEDGER = "docs/registry/v2/claim_ledger.jsonl"


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Ledger not found: {path}")
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON ({error})") from error
    if not rows:
        raise ValueError(f"Ledger has zero rows: {path}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=DEFAULT_LEDGER)
    parser.add_argument("--output", default=None, help="Optional JSON report path.")
    args = parser.parse_args()

    ledger_path = Path(args.ledger)
    if not ledger_path.is_absolute():
        ledger_path = REPO_ROOT / ledger_path
    rows = read_ledger(ledger_path)
    errors = validate_ledger_rows(rows) + missing_artifact_paths(rows, REPO_ROOT)

    counts: dict[str, int] = {}
    for row in rows:
        label = str(row.get("verification_label"))
        counts[label] = counts.get(label, 0) + 1
    report = {
        "ledger": str(ledger_path.relative_to(REPO_ROOT)) if ledger_path.is_relative_to(REPO_ROOT)
        else str(ledger_path),
        "n_rows": len(rows),
        "verification_label_counts": counts,
        "n_errors": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(report, indent=2))
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
