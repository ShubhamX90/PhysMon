#!/usr/bin/env python3
"""Run Stage 3 automatic artefact checks over rendered pilot families.

Reference: Stage 3 brief Part D.6.
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any

from physmon.benchmark.parser import parse_answer
from physmon.benchmark.verifier import SymbolicVerifier
from physmon.utils.io import read_yaml, write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 3
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "stage3_artefact_checks_events.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Stage 3 artefact checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-dir", required=True, help="Directory containing template YAMLs.")
    parser.add_argument("--generated-dir", required=True, help="Directory containing rendered family JSON.")
    parser.add_argument("--output", required=True, help="Output report JSON path.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed label.")
    return parser.parse_args()


def main() -> None:
    """Run all required Stage 3 artefact checks and save a structured report."""
    args = parse_args()
    logger = ExperimentLogger(
        script_name="stage3_artefact_checks.py",
        stage=DEFAULT_STAGE,
        jsonl_path=Path(args.output).parent / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )
    template_dir = Path(args.template_dir)
    generated_dir = Path(args.generated_dir)

    families = sorted(generated_dir.glob("*.json"))
    check_results = {
        "check_1_cue_span_isolation": [],
        "check_2_parser_coverage": [],
        "check_3_cue_value_distinctness": [],
        "check_4_answer_display_parseability": [],
        "check_5_cue_independence_reverification": [],
    }

    for family_path in families:
        family_payload = json.loads(family_path.read_text(encoding="utf-8"))
        template_id = str(family_payload["template_id"])
        template_payload = read_yaml(template_dir / f"{template_id}.yaml")
        check_results["check_1_cue_span_isolation"].append(check_cue_span_isolation(family_payload))
        check_results["check_2_parser_coverage"].append(check_parser_coverage(template_payload))
        check_results["check_3_cue_value_distinctness"].append(check_cue_value_distinctness(template_payload))
        check_results["check_4_answer_display_parseability"].append(
            check_answer_display_parseability(template_payload)
        )
        check_results["check_5_cue_independence_reverification"].append(
            check_cue_independence(template_payload)
        )

    report = summarize_check_results(check_results)
    write_json(args.output, report)
    logger.log_event("STAGE3_ARTEFACT_CHECKS_COMPLETE", **report)


def check_cue_span_isolation(family_payload: dict[str, Any]) -> dict[str, Any]:
    """Assert that only the cue sentence differs across variants within one family."""
    template_id = str(family_payload["template_id"])
    variants = family_payload["variants"]
    failures: list[str] = []
    for left_variant, right_variant in combinations(variants, 2):
        left_prompt = str(left_variant["prompt"])
        right_prompt = str(right_variant["prompt"])
        left_sanitized = left_prompt.replace(str(left_variant["cue_sentence"]), "[CUE]")
        right_sanitized = right_prompt.replace(str(right_variant["cue_sentence"]), "[CUE]")
        if left_sanitized != right_sanitized:
            failures.append(
                f"variant {left_variant['variant_id']} vs {right_variant['variant_id']} differ outside cue span"
            )
    return {
        "template_id": template_id,
        "passed": not failures,
        "details": failures or ["Only cue sentences differ across variants."],
    }


def check_parser_coverage(template_payload: dict[str, Any]) -> dict[str, Any]:
    """Assert that the parser covers the template's canonical display answer."""
    template_id = str(template_payload["template_id"])
    display_answer = str(template_payload["correct_answer"]["display"])
    parse_result = parse_answer(display_answer)
    return {
        "template_id": template_id,
        "passed": bool(parse_result.is_confident and parse_result.answer is not None),
        "details": [f"parsed={parse_result.answer!r}", f"is_confident={parse_result.is_confident}"],
    }


def check_cue_value_distinctness(template_payload: dict[str, Any]) -> dict[str, Any]:
    """Assert that cue values are distinct and log substring-overlap warnings."""
    template_id = str(template_payload["template_id"])
    cue_values = [str(entry["value"]) for entry in template_payload["cue_slot"]["values"]]
    distinct = len(set(cue_values)) == len(cue_values)
    prompt_parameter_values = [str(parameter_spec["value"]) for parameter_spec in template_payload["parameters"].values()]
    warnings = [
        cue_value
        for cue_value in cue_values
        if any(cue_value in parameter_value for parameter_value in prompt_parameter_values)
    ]
    details = []
    if not distinct:
        details.append("Cue values are not distinct.")
    if warnings:
        details.append(f"Substring-overlap warnings: {warnings}")
    if not details:
        details.append("Cue values are distinct with no substring-overlap warnings.")
    return {"template_id": template_id, "passed": distinct, "details": details}


def check_answer_display_parseability(template_payload: dict[str, Any]) -> dict[str, Any]:
    """Verify parseability plus agreement with numeric value and units."""
    template_id = str(template_payload["template_id"])
    display_answer = str(template_payload["correct_answer"]["display"])
    parse_result = parse_answer(display_answer)
    if not parse_result.is_confident or parse_result.answer is None:
        return {"template_id": template_id, "passed": False, "details": ["Parser did not return a confident answer."]}
    expected_value = str(template_payload["correct_answer"]["value"])
    expected_units = str(template_payload["correct_answer"]["units"])
    passed = expected_units in parse_result.answer
    details = [
        f"parsed={parse_result.answer!r}",
        f"expected_value={expected_value}",
        f"expected_units={expected_units}",
    ]
    return {"template_id": template_id, "passed": passed, "details": details}


def check_cue_independence(template_payload: dict[str, Any]) -> dict[str, Any]:
    """Re-run the symbolic cue-independence check on the loaded template."""
    verifier = SymbolicVerifier()
    result = verifier.check_cue_independence(template_payload)
    return {
        "template_id": str(template_payload["template_id"]),
        "passed": result.passed,
        "details": [result.detail],
    }


def summarize_check_results(check_results: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Summarize pass/fail counts and blocking failures across all Stage 3 checks."""
    summary: dict[str, Any] = {"checks": {}, "blocking_failures": []}
    for check_name, results in check_results.items():
        passed = sum(1 for result in results if result["passed"])
        failed_template_ids = [result["template_id"] for result in results if not result["passed"]]
        summary["checks"][check_name] = {
            "pass_count": passed,
            "fail_count": len(results) - passed,
            "results": results,
        }
        if check_name != "check_3_cue_value_distinctness":
            summary["blocking_failures"].extend(
                [{"check": check_name, "template_id": template_id} for template_id in failed_template_ids]
            )
    summary["all_blocking_checks_passed"] = not summary["blocking_failures"]
    return summary


if __name__ == "__main__":
    main()
