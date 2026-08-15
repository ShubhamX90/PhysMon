#!/usr/bin/env python3
"""Validate Stage 13 experiment cards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from governance_utils import write_json


REQUIRED = [
    "experiment_id",
    "scientific_question",
    "discovery_or_confirmation",
    "partition",
    "primary_metric",
    "stop_rules",
    "raw_outputs",
    "negative_result_policy",
    "paper_eligibility_rule",
]


def parse_card(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    data: dict[str, object] = {}
    for line in text.splitlines():
        if ":" not in line or line.startswith("#"):
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        if key in REQUIRED:
            data[key] = value.strip()
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cards", nargs="+")
    parser.add_argument("--output", default="results/stage13/wave0/experiment_card_validation.json")
    args = parser.parse_args()

    results = []
    for card in args.cards:
        path = Path(card)
        data = parse_card(path)
        missing = [field for field in REQUIRED if not data.get(field)]
        results.append({"card": card, "missing": missing, "status": "PASS" if not missing else "FAIL"})
    write_json(
        args.output,
        {
            "n_cards": len(results),
            "n_failed": sum(1 for row in results if row["status"] != "PASS"),
            "results": results,
            "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
        },
    )


if __name__ == "__main__":
    main()

