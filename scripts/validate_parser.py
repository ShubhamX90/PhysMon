#!/usr/bin/env python3
"""Stage 2 answer parser validation entry point.

Reference: Part III.3 and Part V of the implementation brief.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from physmon.benchmark.parser import parse_answer
from physmon.utils.io import write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 2
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "validate_parser_events.jsonl"
DEFAULT_CASES = (
    {"raw_output": "\\boxed{9.8 m/s^2}", "expected_answer": "9.8 m/s^2", "should_parse": True},
    {"raw_output": "Final answer: mv^2/(2r)", "expected_answer": "mv^2/(2r)", "should_parse": True},
    {"raw_output": "I don't know.", "expected_answer": None, "should_parse": False},
    {"raw_output": "The values are 9.8 or 10.1.", "expected_answer": None, "should_parse": False},
    {"raw_output": "Answer: .25 A", "expected_answer": "0.25 A", "should_parse": True},
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for parser validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="results/stage2/parser_validation",
        help="Directory for structured parser-validation artifacts.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed label.")
    return parser.parse_args()


def main() -> None:
    """Run a deterministic parser smoke suite and persist a structured report."""
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="validate_parser.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )

    case_results: list[dict[str, object]] = []
    failures = 0
    for case_index, case in enumerate(DEFAULT_CASES):
        result = parse_answer(case["raw_output"])
        passed = result.answer == case["expected_answer"] and result.is_confident == case["should_parse"]
        if not passed:
            failures += 1
        case_results.append(
            {
                "case_index": case_index,
                "raw_output": case["raw_output"],
                "expected_answer": case["expected_answer"],
                "should_parse": case["should_parse"],
                "actual_answer": result.answer,
                "is_confident": result.is_confident,
                "passed": passed,
            }
        )

    payload = {
        "seed": args.seed,
        "num_cases": len(DEFAULT_CASES),
        "num_failures": failures,
        "all_passed": failures == 0,
        "cases": case_results,
    }
    write_json(output_dir / "parser_validation_report.json", payload)
    logger.log_event("PARSER_VALIDATION_COMPLETE", **payload)


if __name__ == "__main__":
    main()
