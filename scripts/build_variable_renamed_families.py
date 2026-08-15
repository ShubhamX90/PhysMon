#!/usr/bin/env python3
"""Create a variable-renamed benchmark slice from high-S_lp Cue B families."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re

from physmon.utils.io import write_json


REPLACEMENTS = (
    (r"\btorque\b", "tau-quantity"),
    (r"\blever arm\b", "lambda-arm"),
    (r"\bforce\b", "psi-quantity"),
    (r"\bmass\b", "kappa-quantity"),
    (r"\bvelocity\b", "xi-quantity"),
    (r"\bspeed\b", "xi-quantity"),
    (r"\bacceleration\b", "alpha-quantity"),
    (r"\bcurrent\b", "iota-quantity"),
    (r"\bcharge\b", "chi-quantity"),
    (r"\bvoltage\b", "upsilon-quantity"),
    (r"\bpotential difference\b", "upsilon-gap"),
    (r"\bresistance\b", "rho-quantity"),
    (r"\btemperature\b", "theta-quantity"),
    (r"\bpressure\b", "phi-quantity"),
    (r"\bvolume\b", "nu-quantity"),
    (r"\bheat\b", "eta-quantity"),
    (r"\bfrequency\b", "zeta-quantity"),
    (r"\bperiod\b", "beta-quantity"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family-csv",
        default="results/stage6/analysis_d2/stage6_d1_per_family.csv",
    )
    parser.add_argument(
        "--family-dir",
        default="results/stage6/generated_full_benchmark",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
    )
    return parser.parse_args()


def rename_prompt(prompt: str) -> str:
    updated = prompt
    for pattern, repl in REPLACEMENTS:
        updated = re.sub(pattern, repl, updated, flags=re.IGNORECASE)
    return updated


def main() -> None:
    args = parse_args()
    family_rows = list(csv.DictReader(open(args.family_csv, "r", encoding="utf-8")))
    cue_b_rows = [
        row
        for row in family_rows
        if row.get("cue_type") == "nongoverning_distractor"
    ]
    cue_b_rows.sort(key=lambda row: float(row.get("qwen_S_lp", "0") or "0"), reverse=True)
    selected = cue_b_rows[: args.top_k]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for row in selected:
        template_id = row["template_id"]
        payload = json.loads(Path(args.family_dir, f"{template_id}.json").read_text(encoding="utf-8"))
        renamed_payload = {
            **payload,
            "template_id": f"{template_id}_RENAME",
            "source_template_id": template_id,
            "renaming_scheme": {pattern: repl for pattern, repl in REPLACEMENTS},
            "variants": [],
        }
        for variant in payload["variants"]:
            renamed_variant = {
                **variant,
                "prompt": rename_prompt(str(variant["prompt"])),
                "cue_sentence": rename_prompt(str(variant["cue_sentence"])),
            }
            renamed_payload["variants"].append(renamed_variant)
        write_json(output_dir / f"{renamed_payload['template_id']}.json", renamed_payload)
        manifest.append(
            {
                "source_template_id": template_id,
                "renamed_template_id": renamed_payload["template_id"],
                "qwen_S_lp": float(row.get("qwen_S_lp", "0") or "0"),
            }
        )

    write_json(output_dir / "renamed_manifest.json", {"families": manifest, "top_k": int(args.top_k)})


if __name__ == "__main__":
    main()
