"""Family rendering from canonical Stage 3 YAML templates.

Reference: `physmon_proposal.pdf` §3.2 and the Stage 3 brief Part D.5.
"""

from __future__ import annotations

from typing import Any

from physmon.benchmark.verifier import SymbolicVerifier
from physmon.formal.constructs import CounterfactualFamily, PhysicsTemplate
from physmon.utils.io import read_yaml


def render_family(template_path: str, verify: bool = True) -> CounterfactualFamily:
    """Load a template YAML, optionally verify it, and render its 4 variants.

    Args:
        template_path: Path to one template YAML.
        verify: Whether to run symbolic verification before rendering.

    Returns:
        `CounterfactualFamily` whose variants contain rendered prompts and cue metadata.

    Raises:
        ValueError: If verification is requested and any required check fails.
    """

    template_payload = read_yaml(template_path)
    verification_result = None
    if verify:
        verification_result = SymbolicVerifier().verify(template_path)
        if not verification_result.all_passed:
            failed_checks = [
                f"{check.check_name}: {check.detail}"
                for check in verification_result.checks
                if not check.passed
            ]
            raise ValueError(
                f"Verification failed for {template_payload['template_id']}: " + " | ".join(failed_checks)
            )

    physics_template = _build_physics_template(template_payload)
    rendered_variants = _render_variants(template_payload)
    family = CounterfactualFamily(
        template=physics_template,
        variants=rendered_variants,
        correct_answer=str(template_payload["correct_answer"]["display"]),
        verifier_certified=bool(verification_result.all_passed) if verification_result else False,
    )
    return family


def _build_physics_template(template_payload: dict[str, Any]) -> PhysicsTemplate:
    """Convert one Stage 3 YAML payload into the formal template dataclass."""
    cue_slot = template_payload["cue_slot"]
    return PhysicsTemplate(
        template_id=str(template_payload["template_id"]),
        domain=str(template_payload["domain"]),
        cue_type=str(template_payload["cue_type"]),
        governing_relation=str(template_payload["governing_law"]),
        cue_variable=str(cue_slot["name"]),
        auxiliary_assumptions=str(template_payload["prompt_template"]["context"]),
        governing_equation=str(template_payload["governing_equation_sympy"]),
        correct_answer_template=str(template_payload["correct_answer"]["display"]),
        num_variants=len(cue_slot["values"]),
        notes=str(template_payload.get("notes", "")),
    )


def _render_variants(template_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Render all cue variants for one template YAML."""
    prompt_template = template_payload["prompt_template"]
    parameters = {
        parameter_name: parameter_spec.get("display", parameter_spec["value"])
        for parameter_name, parameter_spec in template_payload["parameters"].items()
    }
    cue_slot = template_payload["cue_slot"]
    rendered_variants: list[dict[str, Any]] = []
    for cue_value_spec in cue_slot["values"]:
        format_values = {
            **parameters,
            str(cue_slot["name"]): cue_value_spec.get("render", cue_value_spec["display"]),
        }
        rendered_variants.append(
            {
                "variant_id": int(cue_value_spec["id"]),
                "cue_value": str(cue_value_spec["display"]),
                "prompt": str(prompt_template["full_template"]).format(**format_values),
                "correct_answer": str(template_payload["correct_answer"]["display"]),
                "cue_sentence": str(prompt_template["cue_sentence"]).format(**format_values),
            }
        )
    return rendered_variants
