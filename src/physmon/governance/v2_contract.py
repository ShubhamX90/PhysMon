"""Vocabularies and record contracts for PhysMon Research Redesign v2.0 (Stage 14 onwards).

Plan of record: `docs/proposals/PhysMon_Research_v2.pdf`. Section and page numbers below refer to
that PDF. This module is deliberately stdlib-only so governance checks run on a login node with
no model stack. It does not replace the Stage 13 registry vocabularies; the v2 claim ledger
(`docs/registry/v2/claim_ledger.jsonl`) is a separate artifact family that Stage 14.1 populates.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

# Evidence status. A zero-row job, failed hook, timeout, parse failure, ineligible family, or
# untested control is NOT_EVALUATED, never a null effect (v2 §8.4, p.42).
EVIDENCE_STATUSES = (
    "NOT_EVALUATED",
    "exploratory",
    "confirmatory",
    "diagnostic_only",
    "partial_not_reportable",
    "failed",
    "superseded",
)

# Five disjoint data roles (v2 B6.3, p.12). Phase-I data never received a role, so it is labelled
# explicitly rather than back-filled.
DATA_ROLES = (
    "EXPLORATION",
    "GENERATOR_TUNING",
    "INTERNAL_CONFIRMATION",
    "EPC_CONFIRMATION",
    "ADVERSARIAL_CHALLENGE",
    "UNASSIGNED_LEGACY",
)
CONFIRMATORY_ROLES = ("INTERNAL_CONFIRMATION", "EPC_CONFIRMATION")

# Labels for every value taken from the submitted paper (v2 P0.2, p.16).
VERIFICATION_LABELS = (
    "not_yet_checked",
    "verified",
    "different_but_explained",
    "unreproducible",
    "not_enough_source_data",
)

# Source tags (v2 §1, p.3).
SOURCE_TAGS = ("SUBMITTED", "REVIEW", "LITERATURE", "PROPOSAL", "REPO")

# Severity order used when a row has several components: the row takes the most conservative
# component label, so a partly reproducible row can never read as fully verified.
LABEL_SEVERITY = {
    "verified": 0,
    "different_but_explained": 1,
    "not_enough_source_data": 2,
    "unreproducible": 3,
}

ROW_TYPES = ("phase1_ledger_item", "audit_alert", "claim_level")

# Claim hierarchy (v2 §4.2, p.15). A claim only advances when its own tests pass.
CLAIM_LEVELS = ("C1", "C2", "C3", "C4", "C5", "C6")
GATE_STATUSES = ("not_passed", "passed")

# Admission categories for benchmark families (v2 B4.5, p.10).
ADMISSION_CATEGORIES = (
    "CERTIFIED_AND_VALIDATED",
    "SOLVER_VALID_LANGUAGE_AMBIGUOUS",
    "SOLVER_INVALID",
    "ANSWER_AMBIGUOUS",
    "NATURALNESS_FLAG",
    "REVISED_REVALIDATED",
    "EXCLUDED",
    "UNREVIEWED",
)

LEDGER_REQUIRED_FIELDS = (
    "claim_id",
    "row_type",
    "source_tag",
    "source_ref",
    "statement",
    "reported_value",
    "verification_label",
    "evidence_status",
    "data_role",
    "artifacts",
    "checking_task",
    "paper_eligibility",
)

# Every raw record (v2 §9.1, p.43).
RAW_RECORD_FIELDS = (
    "run_id",
    "phase_id",
    "exploratory_or_confirmatory",
    "structure_uuid",
    "template_cluster_id",
    "symbolic_program_hash",
    "cue_type",
    "cue_semantic_role",
    "cue_numeric_value",
    "unit_type",
    "numeric_proximity",
    "digit_overlap",
    "cue_position",
    "isolation_condition",
    "model_id",
    "model_commit",
    "tokenizer_commit",
    "chat_template",
    "answer_wrapper_id",
    "target_answer_ids",
    "target_span_start",
    "target_span_end",
    "generated_answer_raw",
    "parsed_answer",
    "parse_status",
    "gold_logprob_raw",
    "gold_logprob_per_token",
    "alternative_scores",
    "correctness",
    "seed",
    "dtype",
    "wall_time",
    "artifact_checksum",
)

# Additional fields for causal results (v2 §9.1, p.43).
CAUSAL_RECORD_EXTRA_FIELDS = (
    "receiver_id",
    "donor_id",
    "edit_site",
    "edit_semantics",
    "scale",
    "clean_corrupt_definition",
    "hook_tensor_shape",
    "absolute_Y_control",
    "absolute_Y_intervened",
    "KL_damage",
    "model_positive_eligibility",
    "recipient_generation_outcomes",
)


def missing_record_fields(record: Mapping[str, Any], *, causal: bool = False) -> list[str]:
    """Return the contract fields absent from a raw (or causal) record.

    A field whose value is `None` counts as present: the contract requires the key so that a
    missing value is an explicit, reasoned gap and not a silent omission.
    """

    required = RAW_RECORD_FIELDS + (CAUSAL_RECORD_EXTRA_FIELDS if causal else ())
    return [name for name in required if name not in record]


def validate_ledger_rows(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    """Validate claim-ledger rows and return a list of human-readable errors (empty if valid)."""

    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        claim_id = str(row.get("claim_id", f"<row {index}>"))
        prefix = f"{claim_id}:"
        for name in LEDGER_REQUIRED_FIELDS:
            if name not in row:
                errors.append(f"{prefix} missing required field '{name}'")
        if claim_id in seen:
            errors.append(f"{prefix} duplicate claim_id")
        seen.add(claim_id)
        if not str(row.get("statement", "")).strip():
            errors.append(f"{prefix} statement is empty")
        _check_choice(errors, prefix, row, "row_type", ROW_TYPES)
        _check_choice(errors, prefix, row, "source_tag", SOURCE_TAGS)
        _check_choice(errors, prefix, row, "verification_label", VERIFICATION_LABELS)
        _check_choice(errors, prefix, row, "evidence_status", EVIDENCE_STATUSES)
        _check_choice(errors, prefix, row, "data_role", DATA_ROLES)
        if not isinstance(row.get("artifacts", []), list):
            errors.append(f"{prefix} artifacts must be a list of repo-relative paths")
        errors.extend(_check_row_rules(prefix, row))
    return errors


def worst_label(outcomes: Iterable[str]) -> str:
    """Return the most conservative verification label among component outcomes."""

    outcome_list = list(outcomes)
    if not outcome_list:
        raise ValueError("worst_label needs at least one component outcome.")
    return max(outcome_list, key=lambda name: LABEL_SEVERITY[name])


def missing_artifact_paths(rows: Iterable[Mapping[str, Any]], repo_root: Path) -> list[str]:
    """Return errors for artifact paths that do not exist (checked for every row that lists any)."""

    errors: list[str] = []
    for row in rows:
        for rel_path in row.get("artifacts", []) or []:
            if not (repo_root / str(rel_path)).exists():
                errors.append(f"{row.get('claim_id')}: artifact path does not exist: {rel_path}")
    return errors


def _check_choice(
    errors: list[str], prefix: str, row: Mapping[str, Any], field: str, allowed: tuple[str, ...]
) -> None:
    if field in row and row[field] not in allowed:
        errors.append(f"{prefix} {field}={row[field]!r} is not one of {list(allowed)}")


def _check_components(prefix: str, label: Any, components: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(components, list) or not components:
        return [f"{prefix} components must be a non-empty list"]
    outcomes: list[str] = []
    for position, component in enumerate(components):
        if not isinstance(component, dict) or not str(component.get("name", "")).strip():
            errors.append(f"{prefix} component {position} needs a 'name'")
            continue
        outcome = component.get("outcome")
        if outcome not in LABEL_SEVERITY:
            errors.append(f"{prefix} component '{component['name']}' outcome {outcome!r} is invalid")
            continue
        outcomes.append(outcome)
        if outcome != "verified" and not str(component.get("detail", "")).strip():
            errors.append(f"{prefix} component '{component['name']}' needs a 'detail'")
    if outcomes and label != "not_yet_checked" and label != worst_label(outcomes):
        errors.append(f"{prefix} label '{label}' must equal the most conservative component outcome")
    return errors


def _check_row_rules(prefix: str, row: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    label = row.get("verification_label")
    status = row.get("evidence_status")
    artifacts = row.get("artifacts") or []

    if label not in (None, "not_yet_checked"):
        if not row.get("verified_in_stage") or not row.get("journal_ref"):
            errors.append(f"{prefix} a checked label needs 'verified_in_stage' and 'journal_ref'")
    if label in ("verified", "different_but_explained") and not artifacts:
        errors.append(f"{prefix} label '{label}' needs at least one artifact path")
    if label in ("different_but_explained", "unreproducible", "not_enough_source_data"):
        if not str(row.get("explanation", "")).strip():
            errors.append(f"{prefix} label '{label}' needs an 'explanation'")

    components = row.get("components")
    if components is not None:
        errors.extend(_check_components(prefix, label, components))

    if status == "confirmatory":
        if row.get("data_role") not in CONFIRMATORY_ROLES:
            errors.append(f"{prefix} confirmatory status needs a confirmatory data_role")
        if not str(row.get("preregistration_ref", "")).strip():
            errors.append(f"{prefix} confirmatory status needs 'preregistration_ref'")

    if row.get("paper_eligibility") is True:
        if status != "confirmatory" or label != "verified":
            errors.append(f"{prefix} paper_eligibility needs confirmatory status and verified label")

    # A zero-row result is never a measured null (v2 §8.4, p.42).
    if row.get("observed_rows") == 0:
        if status not in ("NOT_EVALUATED", "failed"):
            errors.append(f"{prefix} zero observed rows must be NOT_EVALUATED or failed")
        if row.get("scientific_null") is True:
            errors.append(f"{prefix} zero observed rows cannot be recorded as a scientific null")

    if row.get("row_type") == "claim_level":
        if row.get("claim_id") not in CLAIM_LEVELS:
            errors.append(f"{prefix} claim_level rows must use claim_id in {list(CLAIM_LEVELS)}")
        gate = row.get("gate_status")
        if gate not in GATE_STATUSES:
            errors.append(f"{prefix} claim_level rows need gate_status in {list(GATE_STATUSES)}")
        if gate == "passed" and not str(row.get("gate_evidence", "")).strip():
            errors.append(f"{prefix} a passed gate needs 'gate_evidence'")
    return errors
