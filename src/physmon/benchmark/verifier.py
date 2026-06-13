"""Symbolic verification for Stage 3 pilot benchmark templates.

Reference: `physmon_proposal.pdf` §3.2, §5.2, and the Stage 3 brief Part D.3.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import argparse
import math

import sympy

from physmon.benchmark.parser import parse_answer
from physmon.utils.io import read_yaml, write_json


VALIDATION_OUTPUT_DIR = Path("results/stage3/verification")
RELATIVE_TOLERANCE = 1e-6
COULOMB_ABSOLUTE_TOLERANCE = 1e-3
PHYSICALLY_POSITIVE_KEYWORDS = ("mass", "distance", "radius", "resistance", "capacitance", "time")


@dataclass(frozen=True)
class CheckResult:
    """One structured verifier check outcome.

    Args:
        passed: Whether the check succeeded.
        check_name: Stable check identifier.
        detail: Human-readable pass/fail explanation.

    Returns:
        Immutable check-result record.
    """

    passed: bool
    check_name: str
    detail: str


@dataclass(frozen=True)
class VerificationResult:
    """Structured verification report for one template.

    Args:
        template_id: Verified template identifier.
        all_passed: Whether every check passed.
        checks: All executed `CheckResult` entries.

    Returns:
        Immutable verification summary suitable for JSON export.
    """

    template_id: str
    all_passed: bool
    checks: list[CheckResult]


class SymbolicVerifier:
    """Run all Stage 3 symbolic and parser-backed checks on one template YAML."""

    def verify(self, template_yaml_path: str) -> VerificationResult:
        """Load a YAML template, run all checks, and return a structured report.

        Args:
            template_yaml_path: Path to one Stage 3 template YAML.

        Returns:
            `VerificationResult` with all executed checks.
        """

        template = read_yaml(template_yaml_path)
        checks = [
            self.check_answer_correctness(template),
            self.check_cue_independence(template),
            self.check_physical_plausibility(template),
            self.check_correct_answer_parseable(template),
        ]
        return VerificationResult(
            template_id=str(template["template_id"]),
            all_passed=all(check.passed for check in checks),
            checks=checks,
        )

    def check_answer_correctness(self, template: dict[str, Any]) -> CheckResult:
        """Evaluate `governing_equation_sympy` and compare it to `correct_answer.value`.

        Args:
            template: Loaded template mapping.

        Returns:
            `CheckResult` describing the numeric correctness check.
        """

        expression = self._sympify_expression(template)
        substitutions = self._parameter_substitutions(template)
        evaluated_expression = expression.evalf(subs=substitutions)
        if evaluated_expression.free_symbols:
            return CheckResult(
                passed=False,
                check_name="answer_correctness",
                detail=f"Unresolved symbols remain after substitution: {sorted(symbol.name for symbol in evaluated_expression.free_symbols)}",
            )
        if not bool(evaluated_expression.is_real):
            return CheckResult(
                passed=False,
                check_name="answer_correctness",
                detail=f"Expression did not evaluate to a real scalar: {evaluated_expression}",
            )
        evaluated = float(evaluated_expression)
        expected = float(template["correct_answer"]["value"])
        tolerance = self._answer_tolerance(template, expected)
        passed = abs(evaluated - expected) <= tolerance
        detail = (
            f"evaluated={evaluated}, expected={expected}, tolerance={tolerance}"
            if passed
            else f"Mismatch: evaluated={evaluated}, expected={expected}, tolerance={tolerance}"
        )
        return CheckResult(passed=passed, check_name="answer_correctness", detail=detail)

    def check_cue_independence(self, template: dict[str, Any]) -> CheckResult:
        """Verify that the cue symbol is absent from the governing equation.

        Args:
            template: Loaded template mapping.

        Returns:
            `CheckResult` describing the free-symbol independence test.
        """

        expression = self._sympify_expression(template)
        free_symbol_names = {symbol.name for symbol in expression.free_symbols}
        cue_type = str(template["cue_type"])
        cue_slot = template["cue_slot"]

        if cue_type == "irrelevant_variable":
            blocked_symbols = {str(cue_slot["name"])}
            detail_label = "cue_slot.name"
        elif cue_type == "nongoverning_distractor":
            distractor_symbol = cue_slot.get("distractor_symbol")
            if distractor_symbol is None:
                return CheckResult(
                    passed=False,
                    check_name="cue_independence",
                    detail="Cue B template is missing cue_slot.distractor_symbol.",
                )
            blocked_symbols = {str(distractor_symbol)}
            detail_label = "cue_slot.distractor_symbol"
        else:
            blocked_symbols = {str(cue_slot["name"])}
            detail_label = "cue symbol"

        overlapping = sorted(free_symbol_names & blocked_symbols)
        passed = not overlapping
        detail = (
            f"{detail_label} absent from governing-equation free symbols {sorted(free_symbol_names)}"
            if passed
            else f"Blocked cue symbols appear in free symbols: {overlapping}"
        )
        return CheckResult(passed=passed, check_name="cue_independence", detail=detail)

    def check_physical_plausibility(self, template: dict[str, Any]) -> CheckResult:
        """Check that template parameters are finite and physically plausible.

        Args:
            template: Loaded template mapping.

        Returns:
            `CheckResult` describing the plausibility scan.
        """

        failures: list[str] = []
        for parameter_name, parameter_spec in template["parameters"].items():
            value = float(parameter_spec["value"])
            units = str(parameter_spec.get("units", ""))
            if not math.isfinite(value):
                failures.append(f"{parameter_name} is not finite")
                continue
            if any(keyword in parameter_name.lower() for keyword in PHYSICALLY_POSITIVE_KEYWORDS) and value <= 0:
                failures.append(f"{parameter_name} must be positive, got {value}")
            if units in {"kg", "m", "s", "Ω", "F"} and value <= 0:
                failures.append(f"{parameter_name} with units {units} must be positive, got {value}")

        passed = not failures
        detail = "all parameter values are finite and plausible" if passed else "; ".join(failures)
        return CheckResult(passed=passed, check_name="physical_plausibility", detail=detail)

    def check_correct_answer_parseable(self, template: dict[str, Any]) -> CheckResult:
        """Verify that `correct_answer.display` is accepted by the deterministic parser.

        Args:
            template: Loaded template mapping.

        Returns:
            `CheckResult` describing parser coverage on the canonical answer string.
        """

        display_answer = str(template["correct_answer"]["display"])
        parse_result = parse_answer(display_answer)
        if not parse_result.is_confident or parse_result.answer is None:
            return CheckResult(
                passed=False,
                check_name="correct_answer_parseable",
                detail=f"Parser could not confidently parse correct_answer.display={display_answer!r}.",
            )

        detail = f"Parsed canonical answer as {parse_result.answer!r}."
        return CheckResult(passed=True, check_name="correct_answer_parseable", detail=detail)

    @staticmethod
    def _parameter_substitutions(template: dict[str, Any]) -> dict[sympy.Symbol, float]:
        """Convert template parameters into SymPy substitution values."""
        substitutions: dict[sympy.Symbol, float] = {}
        for parameter_name, parameter_spec in template["parameters"].items():
            substitutions[sympy.Symbol(parameter_name)] = float(parameter_spec["value"])
        return substitutions

    @staticmethod
    def _sympify_expression(template: dict[str, Any]) -> sympy.Expr:
        """Parse the governing expression with explicit symbol locals."""
        local_symbols = {
            parameter_name: sympy.Symbol(parameter_name)
            for parameter_name in template["parameters"]
        }
        cue_slot = template.get("cue_slot", {})
        cue_name = cue_slot.get("name")
        if cue_name is not None:
            local_symbols[str(cue_name)] = sympy.Symbol(str(cue_name))
        distractor_symbol = cue_slot.get("distractor_symbol")
        if distractor_symbol is not None:
            local_symbols[str(distractor_symbol)] = sympy.Symbol(str(distractor_symbol))
        return sympy.sympify(template["governing_equation_sympy"], locals=local_symbols)

    @staticmethod
    def _answer_tolerance(template: dict[str, Any], expected: float) -> float:
        """Return a scale-aware numeric tolerance for answer verification."""
        topic_tags = template.get("topic_tags", [])
        if "coulomb_law" in topic_tags or "electric_field" in topic_tags:
            return COULOMB_ABSOLUTE_TOLERANCE
        scale = abs(expected) if expected != 0 else 1.0
        return RELATIVE_TOLERANCE * scale


def _verification_to_json_payload(result: VerificationResult) -> dict[str, Any]:
    """Convert a verification result into a JSON-serializable mapping."""
    return {
        "template_id": result.template_id,
        "all_passed": result.all_passed,
        "checks": [asdict(check) for check in result.checks],
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the verifier module."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", help="Verify one template YAML.")
    parser.add_argument("--all", dest="template_dir", help="Verify all YAML files in a directory.")
    parser.add_argument(
        "--output",
        default=str(VALIDATION_OUTPUT_DIR),
        help="Output directory for per-template verification JSON.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for verifying one or many Stage 3 templates."""
    args = parse_args()
    verifier = SymbolicVerifier()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if bool(args.template) == bool(args.template_dir):
        raise ValueError("Provide exactly one of --template or --all.")

    if args.template:
        result = verifier.verify(args.template)
        output_path = output_dir / f"{result.template_id}.json"
        write_json(output_path, _verification_to_json_payload(result))
        print(output_path)
        return

    template_dir = Path(args.template_dir)
    summary_failures: list[str] = []
    verified_paths = sorted(template_dir.glob("*.yaml"))
    for template_path in verified_paths:
        result = verifier.verify(str(template_path))
        output_path = output_dir / f"{result.template_id}.json"
        write_json(output_path, _verification_to_json_payload(result))
        if not result.all_passed:
            summary_failures.append(result.template_id)

    summary_payload = {
        "total_templates": len(verified_paths),
        "verification_pass": len(verified_paths) - len(summary_failures),
        "verification_fail": len(summary_failures),
        "failures": summary_failures,
    }
    write_json(output_dir / "verification_summary.json", summary_payload)
    print(output_dir / "verification_summary.json")


if __name__ == "__main__":
    main()
