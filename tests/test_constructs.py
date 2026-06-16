"""Unit tests for Stage 1 formal constructs and sensitivity measures."""

from __future__ import annotations

from pathlib import Path
import math

import pytest

from physmon.benchmark.parser import ParseResult
from physmon.formal.constructs import (
    CounterfactualFamily,
    PhysicsTemplate,
    ProbeTarget,
    SensitivityRecord,
    STAGE5_POSITIVE_FAMILIES,
    STAGE6_DEGRADED_QWEN,
    STAGE6_EXCLUDE_FROM_PROBE,
    STAGE6_POSITIVE_FAMILIES,
    is_preregistration_complete,
    get_binary_slp_label,
)
from physmon.formal.sensitivity import (
    compute_all_sensitivity_measures,
    compute_answer_flip_sensitivity,
    compute_distribution_level_sensitivity,
    compute_logprob_drop_sensitivity,
    ensure_family_is_certified,
)


def make_template(num_variants: int = 3) -> PhysicsTemplate:
    """Build a small valid template for formal-layer tests."""
    return PhysicsTemplate(
        template_id="mechanics_irrelevant_variable_0001",
        domain="mechanics",
        cue_type="irrelevant_variable",
        governing_relation="constant-acceleration kinematics",
        cue_variable="paint color of the cart",
        auxiliary_assumptions="frictionless track",
        governing_equation="x - x0 - v0*t - a*t**2/2",
        correct_answer_template="v = v0 + a*t",
        num_variants=num_variants,
    )


def make_family(verifier_certified: bool = True) -> CounterfactualFamily:
    """Build a small counterfactual family with three rendered variants."""
    template = make_template()
    return CounterfactualFamily(
        template=template,
        variants=[
            {"variant_index": 0, "prompt": "Variant 0"},
            {"variant_index": 1, "prompt": "Variant 1"},
            {"variant_index": 2, "prompt": "Variant 2"},
        ],
        correct_answer="9.8 m/s^2",
        verifier_certified=verifier_certified,
    )


def test_physics_template_validates_id_domain_and_cue_type() -> None:
    """`PhysicsTemplate` should reject malformed IDs and unsupported labels."""
    with pytest.raises(ValueError):
        PhysicsTemplate(
            template_id="bad_id",
            domain="mechanics",
            cue_type="irrelevant_variable",
            governing_relation="law",
            cue_variable="cue",
            auxiliary_assumptions="assumptions",
            governing_equation="x",
            correct_answer_template="y",
            num_variants=2,
        )

    with pytest.raises(ValueError):
        PhysicsTemplate(
            template_id="mechanics_irrelevant_variable_0001",
            domain="optics",
            cue_type="irrelevant_variable",
            governing_relation="law",
            cue_variable="cue",
            auxiliary_assumptions="assumptions",
            governing_equation="x",
            correct_answer_template="y",
            num_variants=2,
        )


def test_physics_template_accepts_stage6_unit_matched_ids() -> None:
    """Stage 6 family IDs such as `CM_B_UM_001` should be accepted."""

    template = PhysicsTemplate(
        template_id="CM_B_UM_001",
        domain="mechanics",
        cue_type="nongoverning_distractor",
        governing_relation="hooke_law_force",
        cue_variable="force_on_object_b",
        auxiliary_assumptions="object B is disconnected from object A",
        governing_equation="k * x",
        correct_answer_template="F = k * x",
        num_variants=4,
    )
    assert template.template_id == "CM_B_UM_001"


def test_physics_template_accepts_stage6_standard_ids() -> None:
    """Stage 6 standard IDs such as `CM_B_STD_001` should be accepted."""

    template = PhysicsTemplate(
        template_id="CM_B_STD_001",
        domain="mechanics",
        cue_type="nongoverning_distractor",
        governing_relation="rotational_dynamics_alpha",
        cue_variable="separate_force_reading",
        auxiliary_assumptions="distractor system is mechanically isolated",
        governing_equation="tau_net / I",
        correct_answer_template="alpha = tau_net / I",
        num_variants=4,
    )
    assert template.template_id == "CM_B_STD_001"


def test_counterfactual_family_warns_when_uncertified() -> None:
    """`CounterfactualFamily` should warn when the solver certificate is absent."""
    template = make_template()
    with pytest.warns(UserWarning):
        CounterfactualFamily(
            template=template,
            variants=[{"variant_index": 0}, {"variant_index": 1}, {"variant_index": 2}],
            correct_answer="9.8",
            verifier_certified=False,
        )


def test_preregistration_status_and_binary_label_gate(tmp_path: Path) -> None:
    """Binary labels must remain blocked until the construct spec is completed."""
    placeholder_spec = tmp_path / "construct_spec.md"
    placeholder_spec.write_text(
        "## PRE-REGISTRATION\nSensitivity measure: [TO BE FILLED before Stage 5 begins]\n",
        encoding="utf-8",
    )
    assert not is_preregistration_complete(placeholder_spec)

    record = SensitivityRecord(template_id="mechanics_irrelevant_variable_0001", model_name="toy")
    record.answer_flip_rate = 0.5
    with pytest.raises(RuntimeError):
        record.set_binary_label(threshold=0.3, spec_path=placeholder_spec)

    completed_spec = tmp_path / "construct_spec_complete.md"
    completed_spec.write_text(
        "## PRE-REGISTRATION\nSensitivity measure: answer_flip_rate\n"
        "Binarisation threshold: 0.25\nRationale: fixed before Stage 5\n"
        "Date pre-registered: 2026-06-13\n",
        encoding="utf-8",
    )
    assert is_preregistration_complete(completed_spec)
    record.set_binary_label(threshold=0.3, spec_path=completed_spec)
    assert record.binary_sensitive is True
    assert record.binary_threshold_used == 0.3


def test_probe_target_rejects_invalid_extraction_site() -> None:
    """`ProbeTarget` must restrict activation sites to prompt-side approved labels."""
    with pytest.raises(ValueError):
        ProbeTarget(
            template_id="mechanics_irrelevant_variable_0001",
            model_name="toy",
            extraction_site="bad_site",
            layer_index=0,
            activation_path="/tmp/act.pt",
            variant_index=0,
        )


def test_ensure_family_is_certified_raises_for_uncertified_family() -> None:
    """Behavioural sensitivity must be blocked on uncertified families."""
    with pytest.raises((AssertionError, ValueError)):
        ensure_family_is_certified(make_family(verifier_certified=False))


def test_compute_answer_flip_sensitivity_with_partial_parse_warning() -> None:
    """Answer-flip sensitivity should use valid parses and warn on dropped variants."""
    family = make_family()
    outputs = [
        {"parsed_answer": "9.8 m/s^2"},
        {"parsed_answer": "9.8 m/s^2"},
        {"parsed_answer": None},
    ]
    with pytest.warns(UserWarning):
        record = compute_answer_flip_sensitivity(family, outputs, model_name="toy")

    assert record.answer_flip_rate == 0.0
    assert record.num_valid_parses == 2
    assert record.num_variants_used == 3


def test_compute_distribution_level_sensitivity_returns_expected_jsd() -> None:
    """JSD sensitivity should average pairwise divergences across the family."""
    family = make_family()
    outputs = [
        {
            "parsed_answer": "a",
            "answer_distribution": {"a": 1.0},
            "reference_answer_logprob": -1.0,
        },
        {
            "parsed_answer": "b",
            "answer_distribution": {"b": 1.0},
            "reference_answer_logprob": -1.5,
        },
        {
            "parsed_answer": "a",
            "answer_distribution": {"a": 0.5, "b": 0.5},
            "reference_answer_logprob": -2.0,
        },
    ]
    record = compute_distribution_level_sensitivity(family, outputs, model_name="toy")
    assert record.num_variants_used == 3
    assert record.num_valid_parses == 3
    assert math.isclose(record.jsd_sensitivity or 0.0, 0.5408520829727552, rel_tol=1e-6)


def test_compute_logprob_drop_sensitivity_uses_marked_base_variant() -> None:
    """Log-prob drop should anchor on the designated base prompt."""
    family = make_family()
    outputs = [
        {"parsed_answer": "a", "reference_answer_logprob": -3.0},
        {"parsed_answer": "a", "reference_answer_logprob": -1.0, "is_base_variant": True},
        {"parsed_answer": "a", "reference_answer_logprob": -2.2},
    ]
    record = compute_logprob_drop_sensitivity(family, outputs, model_name="toy")
    assert math.isclose(record.logprob_drop or 0.0, 2.0, rel_tol=1e-6)


def test_compute_all_sensitivity_measures_populates_single_record() -> None:
    """Combined sensitivity computation should merge all three measures."""
    family = make_family()
    outputs = [
        {
            "parsed_answer": ParseResult(
                answer="a",
                display_answer="a",
                confidence=0.99,
                is_confident=True,
                answer_type="symbolic",
                extraction_method="boxed",
            ),
            "answer_distribution": {"a": 1.0},
            "reference_answer_logprob": -1.0,
            "variant_index": 0,
            "is_base_variant": True,
        },
        {
            "parsed_answer": "b",
            "answer_distribution": {"b": 1.0},
            "reference_answer_logprob": -2.0,
            "variant_index": 1,
        },
        {
            "parsed_answer": "a",
            "answer_distribution": {"a": 0.5, "b": 0.5},
            "reference_answer_logprob": -1.5,
            "variant_index": 2,
        },
    ]
    record = compute_all_sensitivity_measures(family, outputs, model_name="toy", generation_seed=42)
    assert math.isclose(record.answer_flip_rate or 0.0, 2.0 / 3.0, rel_tol=1e-6)
    assert math.isclose(record.jsd_sensitivity or 0.0, 0.5408520829727552, rel_tol=1e-6)
    assert math.isclose(record.logprob_drop or 0.0, 1.0, rel_tol=1e-6)


def test_stage6_positive_count() -> None:
    """Stage 6 positive-family set should match the frozen D2 benchmark count."""

    assert len(STAGE6_POSITIVE_FAMILIES) == 70


def test_stage6_positive_rate() -> None:
    """Stage 6 positive-family rate should be 50% on the 140-family benchmark."""

    total = 140
    assert len(STAGE6_POSITIVE_FAMILIES) / total == pytest.approx(0.50, abs=0.01)


def test_stage6_probe_exclusion_subset() -> None:
    """Stage 6 probe exclusions should be a strict subset of degraded Qwen families."""

    assert STAGE6_EXCLUDE_FROM_PROBE <= STAGE6_DEGRADED_QWEN
    assert len(STAGE6_EXCLUDE_FROM_PROBE) == 5


def test_stage5_positive_family_count() -> None:
    """The pre-registered Stage 5 positive family set should contain nine families."""
    assert len(STAGE5_POSITIVE_FAMILIES) == 9


def test_stage5_positive_positive_rate() -> None:
    """The pre-registered Stage 5 positive family rate should be 30% of the pilot."""
    total_families = 30
    assert len(STAGE5_POSITIVE_FAMILIES) / total_families == pytest.approx(0.3, abs=0.01)


def test_get_binary_slp_label_uses_preregistered_family_set() -> None:
    """Binary S_lp labels should come directly from the pre-registered family set."""
    assert get_binary_slp_label("CM_B_006") is True
    assert get_binary_slp_label("CM_A_001") is False
