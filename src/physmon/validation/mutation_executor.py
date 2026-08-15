"""Execute Stage 13 mutations through the actual PhysMon symbolic verifier."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from physmon.benchmark.verifier import SymbolicVerifier
from physmon.validation.mutation_operators import MutationOperator

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class MutationExecutionRecord:
    family_id: str
    source_template_path: str
    operator_id: str
    operator_type: str
    expected_verifier_result: str
    mutation_applied: bool
    object_differs_from_original: bool
    verifier_invoked: bool
    actual_verifier_passed: bool | None
    expected_matches_actual: bool | None
    coverage_status: str
    changed_fields: list[str]
    verifier_checks: list[dict[str, Any]]
    mutation_path: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_template(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_template(path: Path, template: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(template, sort_keys=False, allow_unicode=True), encoding="utf-8")


def portable_path(path: Path) -> str:
    """Return a repository-relative path when possible."""

    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def execute_operator(template_path: Path, operator: MutationOperator, work_dir: Path | None = None) -> MutationExecutionRecord:
    """Apply one mutation and verify the mutated object with `SymbolicVerifier`."""

    original = load_template(template_path)
    family_id = str(original.get("template_id", template_path.stem))
    application = operator.apply(original)
    if not application.mutation_applied or application.mutated_template is None:
        return MutationExecutionRecord(
            family_id=family_id,
            source_template_path=portable_path(template_path),
            operator_id=operator.operator_id,
            operator_type=operator.operator_type,
            expected_verifier_result=operator.expected_verifier_result,
            mutation_applied=False,
            object_differs_from_original=False,
            verifier_invoked=False,
            actual_verifier_passed=None,
            expected_matches_actual=None,
            coverage_status=application.coverage_status,
            changed_fields=application.changed_fields or [],
            verifier_checks=[],
            mutation_path=None,
            reason=application.reason,
        )

    object_differs = application.mutated_template != original
    if not object_differs:
        return MutationExecutionRecord(
            family_id=family_id,
            source_template_path=portable_path(template_path),
            operator_id=operator.operator_id,
            operator_type=operator.operator_type,
            expected_verifier_result=operator.expected_verifier_result,
            mutation_applied=True,
            object_differs_from_original=False,
            verifier_invoked=False,
            actual_verifier_passed=None,
            expected_matches_actual=None,
            coverage_status="mutation_no_effect",
            changed_fields=application.changed_fields or [],
            verifier_checks=[],
            mutation_path=None,
            reason="Mutation application returned an object identical to the original.",
        )

    if work_dir is None:
        with TemporaryDirectory() as temp:
            return _verify_mutation(template_path, operator, application, family_id, Path(temp))
    return _verify_mutation(template_path, operator, application, family_id, work_dir)


def _verify_mutation(
    template_path: Path,
    operator: MutationOperator,
    application: Any,
    family_id: str,
    work_dir: Path,
) -> MutationExecutionRecord:
    work_dir.mkdir(parents=True, exist_ok=True)
    mutation_path = work_dir / f"{family_id}__{operator.operator_id}.yaml"
    dump_template(mutation_path, application.mutated_template)
    result = SymbolicVerifier().verify(str(mutation_path))
    actual_passed = bool(result.all_passed)
    expected_matches = actual_passed if operator.expected_verifier_result == "accept" else not actual_passed
    return MutationExecutionRecord(
        family_id=family_id,
        source_template_path=portable_path(template_path),
        operator_id=operator.operator_id,
        operator_type=operator.operator_type,
        expected_verifier_result=operator.expected_verifier_result,
        mutation_applied=True,
        object_differs_from_original=True,
        verifier_invoked=True,
        actual_verifier_passed=actual_passed,
        expected_matches_actual=expected_matches,
        coverage_status="verified",
        changed_fields=application.changed_fields or [],
        verifier_checks=[asdict(check) for check in result.checks],
        mutation_path=portable_path(mutation_path),
        reason="Actual verifier invoked on mutated YAML object.",
    )
