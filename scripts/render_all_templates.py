#!/usr/bin/env python3
"""Render all Stage 3 pilot templates into invariant counterfactual families.

Reference: Stage 3 brief Part D.5.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from physmon.benchmark.generator import render_family
from physmon.utils.io import write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 3
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "render_all_templates_events.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for batch family rendering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-dir", required=True, help="Directory containing Stage 3 YAML templates.")
    parser.add_argument("--output-dir", required=True, help="Directory for rendered family JSON.")
    parser.add_argument("--report", required=True, help="Path to the render-summary JSON.")
    parser.add_argument("--verify", action="store_true", help="Run symbolic verification before rendering.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed label.")
    return parser.parse_args()


def main() -> None:
    """Render every template YAML and save per-family JSON plus a summary report."""
    args = parse_args()
    template_dir = Path(args.template_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="render_all_templates.py",
        stage=DEFAULT_STAGE,
        jsonl_path=Path(args.report).parent / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )

    failures: list[dict[str, str]] = []
    families_with_exclusion_flags: list[str] = []
    total_templates = 0
    verification_pass = 0

    for template_path in sorted(template_dir.glob("*.yaml")):
        total_templates += 1
        try:
            family = render_family(str(template_path), verify=args.verify)
            payload = {
                "template_id": family.template.template_id,
                "domain": family.template.domain,
                "cue_type": family.template.cue_type,
                "correct_answer": family.correct_answer,
                "verifier_certified": family.verifier_certified,
                "variants": family.variants,
            }
            write_json(output_dir / f"{family.template.template_id}.json", payload)
            verification_pass += int(family.verifier_certified)
            logger.log_event(
                "FAMILY_RENDERED",
                template_id=family.template.template_id,
                verifier_certified=family.verifier_certified,
            )
        except Exception as error:  # noqa: BLE001
            failures.append({"template_path": str(template_path), "error": str(error)})
            logger.log_error(str(error), template_path=str(template_path))

    report_payload = {
        "total_templates": total_templates,
        "verification_pass": verification_pass,
        "verification_fail": len(failures),
        "families_with_exclusion_flags": families_with_exclusion_flags,
        "failures": failures,
    }
    write_json(args.report, report_payload)
    logger.log_event("RENDER_SUMMARY_COMPLETE", **report_payload)


if __name__ == "__main__":
    main()
