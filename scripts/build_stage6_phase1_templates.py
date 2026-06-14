#!/usr/bin/env python3
"""Build Stage 6 Phase 1 unit-matched Cue B templates.

Reference:
    Stage 6 brief v6.0 Part B.2 and Stage 6 GO brief v6.1.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import argparse
import math

import yaml

from physmon.benchmark.verifier import SymbolicVerifier
from physmon.utils.io import write_json


DEFAULT_OUTPUT_DIR = Path("data/raw/templates")
DEFAULT_VERIFICATION_DIR = Path("results/stage6/verification")
CREATED_DATE = "2026-06-15"
CREATED_BY = "agent"
GRAVITY = 9.8
WATER_DENSITY = 1000.0


def exact_float_string(value: float) -> str:
    """Return a stable Python-literal float string."""

    if float(value).is_integer():
        return f"{value:.1f}"
    return repr(float(value))


def build_sympy_check_code(
    parameters: Mapping[str, dict[str, Any]],
    expression: str,
    expected: float,
    tolerance: float | None = None,
) -> str:
    """Create executable verification code for one template."""

    assignment_lines = [
        f"{parameter_name} = {exact_float_string(float(parameter_spec['value']))}"
        for parameter_name, parameter_spec in parameters.items()
    ]
    if tolerance is None:
        tolerance = 1e-6 * abs(expected) if expected != 0 else 1e-6
    assignment_lines.extend(
        [
            f"result = {expression}",
            f"assert abs(result - {exact_float_string(expected)}) < {tolerance}, f\"Answer check failed: {{result}}\"",
        ]
    )
    return "\n".join(assignment_lines)


def cue_b_slot(
    *,
    name: str,
    description: str,
    distractor_symbol: str,
    distractor_units: str,
    value_labels: list[str],
    proof: str,
) -> dict[str, Any]:
    """Build a Cue B cue-slot specification."""

    return {
        "name": name,
        "description": description,
        "type": "numerical",
        "irrelevance_proof": None,
        "distractor_symbol": distractor_symbol,
        "distractor_units": distractor_units,
        "nongoverning_proof": proof,
        "values": [{"id": index, "value": label, "display": label} for index, label in enumerate(value_labels)],
        "base_variant_id": 0,
    }


def build_common_template(
    *,
    template_id: str,
    domain: str = "mechanics",
    sequence: int,
    governing_law: str,
    governing_equation_latex: str,
    governing_equation_sympy: str,
    target_quantity: str,
    parameters: dict[str, dict[str, Any]],
    correct_answer_value: float,
    cue_slot: dict[str, Any],
    prompt_context: str,
    prompt_question: str,
    cue_sentence: str,
    topic_tags: list[str],
    target_units: str = "N",
    correct_answer_display: str | None = None,
    verification_tolerance: float | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Assemble one Stage 6 YAML template payload."""

    if correct_answer_display is None:
        correct_answer_display = (
            f"{correct_answer_value:.4f}".rstrip("0").rstrip(".") + f" {target_units}"
        )
    if verification_tolerance is None:
        verification_tolerance = 1e-6 * abs(correct_answer_value) if correct_answer_value != 0 else 1e-6
    return {
        "template_id": template_id,
        "domain": domain,
        "cue_type": "nongoverning_distractor",
        "sequence": sequence,
        "created_date": CREATED_DATE,
        "created_by": CREATED_BY,
        "governing_law": governing_law,
        "governing_equation_latex": governing_equation_latex,
        "governing_equation_sympy": governing_equation_sympy,
        "target_quantity": target_quantity,
        "target_units": target_units,
        "parameters": parameters,
        "correct_answer": {
            "value": float(correct_answer_value),
            "units": target_units,
            "display": correct_answer_display,
            "sympy_check": (
                f"abs(({governing_equation_sympy}) - {exact_float_string(correct_answer_value)}) "
                f"< {exact_float_string(verification_tolerance)}"
            ),
        },
        "cue_slot": cue_slot,
        "prompt_template": {
            "context": prompt_context,
            "question": prompt_question,
            "full_template": f"{prompt_context}\n\n{prompt_question}",
            "cue_span_is_whole_sentence": False,
            "cue_sentence": cue_sentence,
        },
        "verifier": {
            "method": "sympy_numeric",
            "sympy_check_code": build_sympy_check_code(
                parameters,
                governing_equation_sympy,
                correct_answer_value,
                verification_tolerance,
            ),
            "cue_independence_method": "sympy_free_symbols",
        },
        "validation": {
            "verifier_certified": False,
            "pi_validated": False,
            "v2_validated": False,
            "kappa_contribution": None,
            "exclusion_flags": [],
            "notes": "",
        },
        "topic_tags": topic_tags,
        "difficulty": "introductory",
        "notes": notes,
    }


def force_force_templates() -> list[dict[str, Any]]:
    """Return the first Stage 6 Force/Force unit-matched family block (8 templates)."""

    families: list[dict[str, Any]] = []

    families.append(
        build_common_template(
            template_id="CM_B_UM_001",
            sequence=1,
            governing_law="hooke_law_force",
            governing_equation_latex="F_A = k_A x_A",
            governing_equation_sympy="k_A * x_A",
            target_quantity="spring_force_on_object_A",
            parameters={
                "k_A": {"value": 120.0, "units": "N/m", "description": "spring constant of spring A"},
                "x_A": {"value": 0.15, "units": "m", "description": "extension of spring A"},
            },
            correct_answer_value=18.0,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Weight force acting on unrelated object B, unit-matched with the target force",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["8.0", "12.0", "18.0", "24.0"],
                proof=(
                    'The governing expression "k_A * x_A" has free symbols {k_A, x_A}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is expressed in Newtons, matching the target force units, "
                    "but it acts on a separate hanging object B that never interacts with spring A."
                ),
            ),
            prompt_context=(
                "Spring A has spring constant {k_A} N/m and is stretched by {x_A} m from equilibrium. "
                "In a separate corner of the lab, object B experiences a downward weight force of "
                "{F_B_display} N, but object B never interacts with spring A or the attached object."
            ),
            prompt_question="What is the force exerted by spring A?",
            cue_sentence=(
                "In a separate corner of the lab, object B experiences a downward weight force of "
                "{F_B_display} N, but object B never interacts with spring A or the attached object."
            ),
            topic_tags=["mechanics", "force", "hooke_law", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_002",
            sequence=2,
            governing_law="newton_second_law_force",
            governing_equation_latex="F_A = m_A a_A",
            governing_equation_sympy="m_A * a_A",
            target_quantity="net_force_on_cart_A",
            parameters={
                "m_A": {"value": 4.0, "units": "kg", "description": "mass of cart A"},
                "a_A": {"value": 3.0, "units": "m/s^2", "description": "measured acceleration of cart A"},
            },
            correct_answer_value=12.0,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Spring force measured on unrelated cart B, unit-matched with the target force",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["6.0", "10.0", "14.0", "20.0"],
                proof=(
                    'The governing expression "m_A * a_A" has free symbols {m_A, a_A}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is another force in Newtons, but it belongs to an unrelated cart B "
                    "on a disconnected track and does not contribute to cart A's dynamics."
                ),
            ),
            prompt_context=(
                "Cart A has mass {m_A} kg and its measured acceleration is {a_A} m/s² on a frictionless track. "
                "On a completely separate track, a spring exerts a force of {F_B_display} N on cart B, "
                "and cart B does not interact with cart A."
            ),
            prompt_question="What is the net force acting on cart A?",
            cue_sentence=(
                "On a completely separate track, a spring exerts a force of {F_B_display} N on cart B, "
                "and cart B does not interact with cart A."
            ),
            topic_tags=["mechanics", "force", "newton_second_law", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_003",
            sequence=3,
            governing_law="normal_force_static_equilibrium",
            governing_equation_latex="N_A = m_A g",
            governing_equation_sympy="m_A * g",
            target_quantity="normal_force_on_block_A",
            parameters={
                "m_A": {"value": 2.5, "units": "kg", "description": "mass of block A"},
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
            },
            correct_answer_value=24.5,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Tension force in unrelated rope B, unit-matched with the target force",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["10.0", "18.0", "24.5", "32.0"],
                proof=(
                    'The governing expression "m_A * g" has free symbols {m_A, g}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is a separate rope tension in Newtons, matching the target units, "
                    "but rope B is disconnected from block A and cannot change its normal force."
                ),
            ),
            prompt_context=(
                "Block A of mass {m_A} kg rests motionless on a horizontal table where g = {g} m/s². "
                "Elsewhere in the room, rope B carries a tension force of {F_B_display} N while supporting "
                "a different object, and it never touches block A."
            ),
            prompt_question="What is the normal force exerted by the table on block A?",
            cue_sentence=(
                "Elsewhere in the room, rope B carries a tension force of {F_B_display} N while supporting "
                "a different object, and it never touches block A."
            ),
            topic_tags=["mechanics", "force", "normal_force", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_004",
            sequence=4,
            governing_law="kinetic_friction_force",
            governing_equation_latex="f_k = \\mu_k m_A g",
            governing_equation_sympy="mu_k * m_A * g",
            target_quantity="kinetic_friction_on_block_A",
            parameters={
                "mu_k": {"value": 0.3, "units": "dimensionless", "description": "kinetic friction coefficient"},
                "m_A": {"value": 5.0, "units": "kg", "description": "mass of block A"},
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
            },
            correct_answer_value=14.7,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Thrust force on unrelated glider B, unit-matched with the target force",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["7.0", "14.0", "21.0", "28.0"],
                proof=(
                    'The governing expression "mu_k * m_A * g" has free symbols {mu_k, m_A, g}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is another force in Newtons applied to glider B on a separate track, "
                    "so it cannot affect the friction force on block A."
                ),
            ),
            prompt_context=(
                "Block A of mass {m_A} kg slides across a horizontal surface with kinetic friction coefficient "
                "{mu_k}. Take g = {g} m/s². On an isolated air track, glider B is pushed by a thrust force "
                "of {F_B_display} N and never interacts with block A."
            ),
            prompt_question="What is the kinetic friction force acting on block A?",
            cue_sentence=(
                "On an isolated air track, glider B is pushed by a thrust force of {F_B_display} N "
                "and never interacts with block A."
            ),
            topic_tags=["mechanics", "force", "friction", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_005",
            sequence=5,
            governing_law="tension_static_support",
            governing_equation_latex="T_A = m_A g",
            governing_equation_sympy="m_A * g",
            target_quantity="tension_in_rope_A",
            parameters={
                "m_A": {"value": 3.0, "units": "kg", "description": "mass supported by rope A"},
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
            },
            correct_answer_value=29.4,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Push force on unrelated crate B, unit-matched with the target tension",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["9.8", "19.6", "29.4", "39.2"],
                proof=(
                    'The governing expression "m_A * g" has free symbols {m_A, g}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is another force in Newtons applied to crate B in a separate experiment, "
                    "so it does not influence the tension in rope A."
                ),
            ),
            prompt_context=(
                "A bucket of mass {m_A} kg hangs motionless from rope A. Take g = {g} m/s². "
                "On another bench, crate B is pushed with a horizontal force of {F_B_display} N, "
                "and that setup never interacts with rope A or the bucket."
            ),
            prompt_question="What is the tension in rope A?",
            cue_sentence=(
                "On another bench, crate B is pushed with a horizontal force of {F_B_display} N, "
                "and that setup never interacts with rope A or the bucket."
            ),
            topic_tags=["mechanics", "force", "tension", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_006",
            sequence=6,
            governing_law="centripetal_force",
            governing_equation_latex="F_c = m v^2 / r",
            governing_equation_sympy="m_A * v_A**2 / r_A",
            target_quantity="centripetal_force_on_object_A",
            parameters={
                "m_A": {"value": 1.5, "units": "kg", "description": "mass of object A"},
                "v_A": {"value": 6.0, "units": "m/s", "description": "speed of object A"},
                "r_A": {"value": 3.0, "units": "m", "description": "circular path radius"},
            },
            correct_answer_value=18.0,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Magnetic force on unrelated charged bead B, unit-matched with the target force",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["5.0", "12.0", "18.0", "26.0"],
                proof=(
                    'The governing expression "m_A * v_A**2 / r_A" has free symbols {m_A, v_A, r_A}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is a separate magnetic force in Newtons acting on bead B in another apparatus, "
                    "so it cannot change the centripetal force required for object A."
                ),
            ),
            prompt_context=(
                "Object A of mass {m_A} kg moves in a horizontal circle of radius {r_A} m at speed {v_A} m/s. "
                "In a different apparatus, a charged bead B experiences a magnetic force of {F_B_display} N, "
                "and bead B never interacts with object A."
            ),
            prompt_question="What centripetal force is required to keep object A moving in its circle?",
            cue_sentence=(
                "In a different apparatus, a charged bead B experiences a magnetic force of {F_B_display} N, "
                "and bead B never interacts with object A."
            ),
            topic_tags=["mechanics", "force", "centripetal_force", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_007",
            sequence=7,
            governing_law="incline_force_component",
            governing_equation_latex="F_{\\parallel} = m_A g \\sin\\theta",
            governing_equation_sympy="m_A * g * sin(theta)",
            target_quantity="downslope_force_on_block_A",
            parameters={
                "m_A": {"value": 2.0, "units": "kg", "description": "mass of block A"},
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "theta": {"value": math.pi / 6.0, "units": "rad", "display": "30", "description": "incline angle"},
            },
            correct_answer_value=9.8,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Fan force on unrelated cart B, unit-matched with the target force",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["4.9", "9.8", "14.7", "19.6"],
                proof=(
                    'The governing expression "m_A * g * sin(theta)" has free symbols {m_A, g, theta}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is another force in Newtons applied to cart B on a separate incline, "
                    "so it does not affect the downslope component of the weight on block A."
                ),
            ),
            prompt_context=(
                "Block A of mass {m_A} kg rests on a frictionless incline at {theta} degrees. "
                "Take g = {g} m/s². In a separate setup, a fan exerts a force of {F_B_display} N on cart B, "
                "and cart B never interacts with block A."
            ),
            prompt_question="What is the component of block A's weight acting down the incline?",
            cue_sentence=(
                "In a separate setup, a fan exerts a force of {F_B_display} N on cart B, "
                "and cart B never interacts with block A."
            ),
            topic_tags=["mechanics", "force", "incline", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_008",
            sequence=8,
            governing_law="buoyant_force",
            governing_equation_latex="F_b = \\rho V g",
            governing_equation_sympy="rho * V * g",
            target_quantity="buoyant_force_on_object_A",
            parameters={
                "rho": {"value": WATER_DENSITY, "units": "kg/m^3", "description": "fluid density"},
                "V": {"value": 0.002, "units": "m^3", "description": "displaced volume"},
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
            },
            correct_answer_value=19.6,
            cue_slot=cue_b_slot(
                name="F_B_display",
                description="Normal force on unrelated crate B, unit-matched with the target buoyant force",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["9.8", "14.7", "19.6", "29.4"],
                proof=(
                    'The governing expression "rho * V * g" has free symbols {rho, V, g}; '
                    'the distractor symbol F_B is absent from the governing equation. '
                    "The distractor is a separate contact force in Newtons acting on crate B elsewhere in the lab, "
                    "so it cannot affect the buoyant force on object A."
                ),
            ),
            prompt_context=(
                "Object A is fully submerged in water of density {rho} kg/m³ and displaces {V} m³ of fluid. "
                "Take g = {g} m/s². Elsewhere in the lab, crate B experiences a normal force of {F_B_display} N, "
                "and crate B never interacts with object A or the fluid."
            ),
            prompt_question="What buoyant force acts on object A?",
            cue_sentence=(
                "Elsewhere in the lab, crate B experiences a normal force of {F_B_display} N, "
                "and crate B never interacts with object A or the fluid."
            ),
            topic_tags=["mechanics", "force", "buoyancy", "unit_matched_cue_b"],
        )
    )

    return families


def velocity_velocity_templates() -> list[dict[str, Any]]:
    """Return the Stage 6 Velocity/Velocity unit-matched family block (6 templates)."""

    families: list[dict[str, Any]] = []

    families.append(
        build_common_template(
            template_id="CM_B_UM_009",
            sequence=9,
            governing_law="constant_acceleration_velocity",
            governing_equation_latex="v_A = u_A + a_A t_A",
            governing_equation_sympy="u_A + a_A * t_A",
            target_quantity="final_velocity_of_cart_A",
            target_units="m/s",
            parameters={
                "u_A": {"value": 3.0, "units": "m/s", "description": "initial speed of cart A"},
                "a_A": {"value": 2.0, "units": "m/s^2", "description": "constant acceleration of cart A"},
                "t_A": {"value": 4.0, "units": "s", "description": "elapsed time for cart A"},
            },
            correct_answer_value=11.0,
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of unrelated scooter B, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["5.0", "8.0", "11.0", "16.0"],
                proof=(
                    'The governing expression "u_A + a_A * t_A" has free symbols {u_A, a_A, t_A}; '
                    "the distractor symbol v_B is absent from the governing equation. "
                    "The distractor is another speed in m/s, but scooter B moves on a disconnected path "
                    "and never interacts with cart A."
                ),
            ),
            prompt_context=(
                "Cart A starts at {u_A} m/s and accelerates uniformly at {a_A} m/s² for {t_A} s. "
                "On a separate path, scooter B moves at {v_B_display} m/s and never interacts with cart A."
            ),
            prompt_question="What is the final velocity of cart A?",
            cue_sentence=(
                "On a separate path, scooter B moves at {v_B_display} m/s and never interacts with cart A."
            ),
            topic_tags=["mechanics", "velocity", "kinematics", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_010",
            sequence=10,
            governing_law="average_velocity_uniform_motion",
            governing_equation_latex="v_A = d_A / t_A",
            governing_equation_sympy="d_A / t_A",
            target_quantity="uniform_velocity_of_runner_A",
            target_units="m/s",
            parameters={
                "d_A": {"value": 120.0, "units": "m", "description": "distance travelled by runner A"},
                "t_A": {"value": 15.0, "units": "s", "description": "time taken by runner A"},
            },
            correct_answer_value=8.0,
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of unrelated conveyor belt B, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["4.0", "8.0", "12.0", "18.0"],
                proof=(
                    'The governing expression "d_A / t_A" has free symbols {d_A, t_A}; '
                    "the distractor symbol v_B is absent from the governing equation. "
                    "The distractor is another speed in m/s on conveyor belt B, which is a separate system."
                ),
            ),
            prompt_context=(
                "Runner A covers {d_A} m in {t_A} s at uniform speed. "
                "Elsewhere, conveyor belt B moves at {v_B_display} m/s and never interacts with runner A."
            ),
            prompt_question="What is the speed of runner A?",
            cue_sentence=(
                "Elsewhere, conveyor belt B moves at {v_B_display} m/s and never interacts with runner A."
            ),
            topic_tags=["mechanics", "velocity", "uniform_motion", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_011",
            sequence=11,
            governing_law="free_fall_velocity",
            governing_equation_latex="v_A = g t_A",
            governing_equation_sympy="g * t_A",
            target_quantity="downward_velocity_of_ball_A",
            target_units="m/s",
            parameters={
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "t_A": {"value": 1.5, "units": "s", "description": "free-fall time of ball A"},
            },
            correct_answer_value=14.7,
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of unrelated drone B, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["6.0", "10.0", "14.7", "20.0"],
                proof=(
                    'The governing expression "g * t_A" has free symbols {g, t_A}; '
                    "the distractor symbol v_B is absent from the governing equation. "
                    "The distractor is another speed in m/s, but drone B is a separate moving object."
                ),
            ),
            prompt_context=(
                "Ball A is dropped from rest and falls freely for {t_A} s. Take g = {g} m/s². "
                "At the same moment, drone B moves elsewhere at {v_B_display} m/s and never interacts with ball A."
            ),
            prompt_question="What is the downward velocity of ball A after {t_A} s?",
            cue_sentence=(
                "At the same moment, drone B moves elsewhere at {v_B_display} m/s and never interacts with ball A."
            ),
            topic_tags=["mechanics", "velocity", "free_fall", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_012",
            sequence=12,
            governing_law="wave_speed",
            governing_equation_latex="v_A = f_A \\lambda_A",
            governing_equation_sympy="f_A * lambda_A",
            target_quantity="wave_speed_on_string_A",
            target_units="m/s",
            parameters={
                "f_A": {"value": 5.0, "units": "Hz", "description": "frequency of the wave on string A"},
                "lambda_A": {"value": 2.4, "units": "m", "description": "wavelength on string A"},
            },
            correct_answer_value=12.0,
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of unrelated cart B, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["3.0", "7.5", "12.0", "18.0"],
                proof=(
                    'The governing expression "f_A * lambda_A" has free symbols {f_A, lambda_A}; '
                    "the distractor symbol v_B is absent from the governing equation. "
                    "The distractor is another speed in m/s, but it belongs to cart B and not to the wave on string A."
                ),
            ),
            prompt_context=(
                "A wave on string A has frequency {f_A} Hz and wavelength {lambda_A} m. "
                "In another experiment, cart B moves at {v_B_display} m/s and never affects string A."
            ),
            prompt_question="What is the speed of the wave on string A?",
            cue_sentence=(
                "In another experiment, cart B moves at {v_B_display} m/s and never affects string A."
            ),
            topic_tags=["mechanics", "velocity", "waves", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_013",
            sequence=13,
            governing_law="circular_speed",
            governing_equation_latex="v_A = 2\\pi r_A / T_A",
            governing_equation_sympy="2 * pi * r_A / T_A",
            target_quantity="speed_of_object_A_in_uniform_circular_motion",
            target_units="m/s",
            parameters={
                "r_A": {"value": 1.5, "units": "m", "description": "radius of circular path"},
                "T_A": {"value": 3.0, "units": "s", "description": "period of revolution"},
            },
            correct_answer_value=math.pi,
            correct_answer_display="3.1416 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of unrelated skater B, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["1.5", "3.1", "4.5", "6.0"],
                proof=(
                    'The governing expression "2 * pi * r_A / T_A" has free symbols {r_A, T_A}; '
                    "the distractor symbol v_B is absent from the governing equation. "
                    "The distractor is another speed in m/s for skater B on a separate track."
                ),
            ),
            prompt_context=(
                "Object A moves in a circle of radius {r_A} m and completes one revolution every {T_A} s. "
                "On another rink, skater B travels at {v_B_display} m/s and never interacts with object A."
            ),
            prompt_question="What is the speed of object A?",
            cue_sentence=(
                "On another rink, skater B travels at {v_B_display} m/s and never interacts with object A."
            ),
            topic_tags=["mechanics", "velocity", "circular_motion", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_014",
            sequence=14,
            governing_law="projectile_horizontal_velocity",
            governing_equation_latex="v_{x,A} = R_A / t_A",
            governing_equation_sympy="R_A / t_A",
            target_quantity="horizontal_velocity_of_projectile_A",
            target_units="m/s",
            parameters={
                "R_A": {"value": 18.0, "units": "m", "description": "horizontal range of projectile A"},
                "t_A": {"value": 2.0, "units": "s", "description": "flight time of projectile A"},
            },
            correct_answer_value=9.0,
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of unrelated robot B, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["4.5", "9.0", "13.5", "18.0"],
                proof=(
                    'The governing expression "R_A / t_A" has free symbols {R_A, t_A}; '
                    "the distractor symbol v_B is absent from the governing equation. "
                    "The distractor is another speed in m/s for robot B moving independently."
                ),
            ),
            prompt_context=(
                "Projectile A travels a horizontal range of {R_A} m in a flight time of {t_A} s. "
                "On a different platform, robot B moves at {v_B_display} m/s and never interacts with projectile A."
            ),
            prompt_question="What is the horizontal velocity of projectile A?",
            cue_sentence=(
                "On a different platform, robot B moves at {v_B_display} m/s and never interacts with projectile A."
            ),
            topic_tags=["mechanics", "velocity", "projectile_motion", "unit_matched_cue_b"],
        )
    )

    return families


def current_current_templates() -> list[dict[str, Any]]:
    """Return the Stage 6 Current/Current unit-matched family block (6 templates)."""

    specs = [
        {
            "template_id": "CM_B_UM_015",
            "sequence": 15,
            "governing_law": "ohms_law_current",
            "equation_latex": "I_A = V_A / R_A",
            "equation_sympy": "V_A / R_A",
            "target_quantity": "current_through_resistor_A",
            "parameters": {
                "V_A": {"value": 12.0, "units": "V", "description": "voltage across resistor A"},
                "R_A": {"value": 4.0, "units": "Ω", "description": "resistance of resistor A"},
            },
            "answer": 3.0,
            "display": "3.0 A",
            "cue_values": ["1.0", "2.0", "3.0", "5.0"],
            "context": (
                "Circuit A has a {V_A} V source across resistor A of resistance {R_A} Ω. "
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from circuit A."
            ),
            "question": "What current flows through resistor A?",
            "cue_sentence": (
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from circuit A."
            ),
            "topic_tags": ["circuits", "current", "ohms_law", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "V_A / R_A" has free symbols {V_A, R_A}; '
                "the distractor symbol I_B is absent from the governing equation. "
                "The distractor is another current in amperes flowing in a separate isolated circuit."
            ),
        },
        {
            "template_id": "CM_B_UM_016",
            "sequence": 16,
            "governing_law": "power_voltage_current",
            "equation_latex": "I_A = P_A / V_A",
            "equation_sympy": "P_A / V_A",
            "target_quantity": "current_drawn_by_device_A",
            "parameters": {
                "P_A": {"value": 20.0, "units": "W", "description": "power of device A"},
                "V_A": {"value": 4.0, "units": "V", "description": "voltage across device A"},
            },
            "answer": 5.0,
            "display": "5.0 A",
            "cue_values": ["2.0", "3.0", "5.0", "8.0"],
            "context": (
                "Device A uses {P_A} W when connected across a {V_A} V supply. "
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from device A."
            ),
            "question": "What current does device A draw?",
            "cue_sentence": (
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from device A."
            ),
            "topic_tags": ["circuits", "current", "power", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "P_A / V_A" has free symbols {P_A, V_A}; '
                "the distractor symbol I_B is absent from the governing equation. "
                "The distractor current belongs to an isolated circuit and does not govern device A."
            ),
        },
        {
            "template_id": "CM_B_UM_017",
            "sequence": 17,
            "governing_law": "series_circuit_current",
            "equation_latex": "I = V_{total} / R_{total}",
            "equation_sympy": "V_total / R_total",
            "target_quantity": "series_circuit_current",
            "parameters": {
                "V_total": {"value": 15.0, "units": "V", "description": "battery voltage"},
                "R_total": {"value": 5.0, "units": "Ω", "description": "total series resistance"},
            },
            "answer": 3.0,
            "display": "3.0 A",
            "cue_values": ["1.0", "2.0", "3.0", "5.0"],
            "context": (
                "A series circuit has total supply voltage {V_total} V and total resistance {R_total} Ω. "
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from this series loop."
            ),
            "question": "What current flows in the series circuit?",
            "cue_sentence": (
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from this series loop."
            ),
            "topic_tags": ["circuits", "current", "series_circuit", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "V_total / R_total" has free symbols {V_total, R_total}; '
                "the distractor symbol I_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_018",
            "sequence": 18,
            "governing_law": "single_branch_current",
            "equation_latex": "I_A = V / R_A",
            "equation_sympy": "V / R_A",
            "target_quantity": "current_through_branch_A",
            "parameters": {
                "V": {"value": 18.0, "units": "V", "description": "supply voltage"},
                "R_A": {"value": 6.0, "units": "Ω", "description": "branch-A resistance"},
            },
            "answer": 3.0,
            "display": "3.0 A",
            "cue_values": ["1.0", "2.0", "3.0", "6.0"],
            "context": (
                "Circuit A places resistor A of {R_A} Ω across a {V} V source. "
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from resistor A."
            ),
            "question": "What current flows through resistor A?",
            "cue_sentence": (
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from resistor A."
            ),
            "topic_tags": ["circuits", "current", "branch_current", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "V / R_A" has free symbols {V, R_A}; '
                "the distractor symbol I_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_019",
            "sequence": 19,
            "governing_law": "battery_external_current",
            "equation_latex": "I = \\mathcal{E} / R_{ext}",
            "equation_sympy": "emf / R_ext",
            "target_quantity": "current_in_simple_battery_circuit",
            "parameters": {
                "emf": {"value": 6.0, "units": "V", "description": "battery emf"},
                "R_ext": {"value": 3.0, "units": "Ω", "description": "external resistance"},
            },
            "answer": 2.0,
            "display": "2.0 A",
            "cue_values": ["0.5", "1.0", "2.0", "4.0"],
            "context": (
                "A simple battery circuit has emf {emf} V, negligible internal resistance, and an external "
                "resistance of {R_ext} Ω. A different circuit in the same lab carries {I_B_display} A in its "
                "main branch, but that circuit is electrically isolated from this one."
            ),
            "question": "What current flows in the battery circuit?",
            "cue_sentence": (
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from this one."
            ),
            "topic_tags": ["circuits", "current", "battery_circuit", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "emf / R_ext" has free symbols {emf, R_ext}; '
                "the distractor symbol I_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_020",
            "sequence": 20,
            "governing_law": "kirchhoff_current_split",
            "equation_latex": "I_A = I_{total} - I_{known}",
            "equation_sympy": "I_total - I_known",
            "target_quantity": "unknown_branch_current_A",
            "parameters": {
                "I_total": {"value": 10.0, "units": "A", "description": "total current entering the node"},
                "I_known": {"value": 4.0, "units": "A", "description": "known current in branch B"},
            },
            "answer": 6.0,
            "display": "6.0 A",
            "cue_values": ["2.0", "4.0", "6.0", "8.0"],
            "context": (
                "At a junction in circuit A, a total current of {I_total} A enters and {I_known} A leaves "
                "through a known branch. A different circuit in the same lab carries {I_B_display} A in its "
                "main branch, but that circuit is electrically isolated from circuit A."
            ),
            "question": "What current flows in the remaining branch of circuit A?",
            "cue_sentence": (
                "A different circuit in the same lab carries {I_B_display} A in its main branch, "
                "but that circuit is electrically isolated from circuit A."
            ),
            "topic_tags": ["circuits", "current", "kirchhoff_current", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "I_total - I_known" has free symbols {I_total, I_known}; '
                "the distractor symbol I_B is absent from the governing equation."
            ),
        },
    ]

    return [
        build_common_template(
            template_id=spec["template_id"],
            domain="electrostatics_circuits",
            sequence=spec["sequence"],
            governing_law=spec["governing_law"],
            governing_equation_latex=spec["equation_latex"],
            governing_equation_sympy=spec["equation_sympy"],
            target_quantity=spec["target_quantity"],
            target_units="A",
            parameters=spec["parameters"],
            correct_answer_value=spec["answer"],
            correct_answer_display=spec["display"],
            cue_slot=cue_b_slot(
                name="I_B_display",
                description="Current in a separate isolated circuit, unit-matched with the target current",
                distractor_symbol="I_B",
                distractor_units="A",
                value_labels=spec["cue_values"],
                proof=spec["proof"],
            ),
            prompt_context=spec["context"],
            prompt_question=spec["question"],
            cue_sentence=spec["cue_sentence"],
            topic_tags=spec["topic_tags"],
        )
        for spec in specs
    ]


def voltage_voltage_templates() -> list[dict[str, Any]]:
    """Return the Stage 6 Voltage/Voltage unit-matched family block (6 templates)."""

    specs = [
        {
            "template_id": "CM_B_UM_021",
            "sequence": 21,
            "governing_law": "ohms_law_voltage",
            "equation_latex": "V_A = I_A R_A",
            "equation_sympy": "I_A * R_A",
            "target_quantity": "voltage_across_resistor_A",
            "parameters": {
                "I_A": {"value": 2.0, "units": "A", "description": "current through resistor A"},
                "R_A": {"value": 6.0, "units": "Ω", "description": "resistance of resistor A"},
            },
            "answer": 12.0,
            "display": "12.0 V",
            "cue_values": ["4.0", "8.0", "12.0", "18.0"],
            "context": (
                "Resistor A carries {I_A} A and has resistance {R_A} Ω. "
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the main loop."
            ),
            "question": "What is the voltage across resistor A?",
            "cue_sentence": (
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the main loop."
            ),
            "topic_tags": ["circuits", "voltage", "ohms_law", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "I_A * R_A" has free symbols {I_A, R_A}; '
                "the distractor symbol V_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_022",
            "sequence": 22,
            "governing_law": "power_current_voltage",
            "equation_latex": "V_A = P_A / I_A",
            "equation_sympy": "P_A / I_A",
            "target_quantity": "voltage_across_device_A",
            "parameters": {
                "P_A": {"value": 18.0, "units": "W", "description": "power of device A"},
                "I_A": {"value": 3.0, "units": "A", "description": "current through device A"},
            },
            "answer": 6.0,
            "display": "6.0 V",
            "cue_values": ["2.0", "4.0", "6.0", "10.0"],
            "context": (
                "Device A uses {P_A} W while carrying {I_A} A. "
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to device A."
            ),
            "question": "What voltage is across device A?",
            "cue_sentence": (
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to device A."
            ),
            "topic_tags": ["circuits", "voltage", "power", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "P_A / I_A" has free symbols {P_A, I_A}; '
                "the distractor symbol V_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_023",
            "sequence": 23,
            "governing_law": "series_voltage_drop",
            "equation_latex": "V_A = V_{total} \\frac{R_A}{R_A + R_B}",
            "equation_sympy": "V_total * R_A / (R_A + R_B)",
            "target_quantity": "voltage_drop_across_resistor_A",
            "parameters": {
                "V_total": {"value": 24.0, "units": "V", "description": "total supply voltage"},
                "R_A": {"value": 4.0, "units": "Ω", "description": "resistance of resistor A"},
                "R_B": {"value": 8.0, "units": "Ω", "description": "resistance of resistor B"},
            },
            "answer": 8.0,
            "display": "8.0 V",
            "cue_values": ["3.0", "6.0", "8.0", "12.0"],
            "context": (
                "A series circuit has supply voltage {V_total} V with resistor A = {R_A} Ω and resistor B = {R_B} Ω. "
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the loop."
            ),
            "question": "What is the voltage drop across resistor A?",
            "cue_sentence": (
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the loop."
            ),
            "topic_tags": ["circuits", "voltage", "series_circuit", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "V_total * R_A / (R_A + R_B)" has free symbols {V_total, R_A, R_B}; '
                "the distractor symbol V_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_024",
            "sequence": 24,
            "governing_law": "capacitor_voltage",
            "equation_latex": "V_A = Q_A / C_A",
            "equation_sympy": "Q_A / C_A",
            "target_quantity": "voltage_across_capacitor_A",
            "parameters": {
                "Q_A": {"value": 6e-4, "units": "C", "description": "charge on capacitor A", "display": "6.0 × 10⁻⁴ C"},
                "C_A": {"value": 100e-6, "units": "F", "description": "capacitance of capacitor A", "display": "100 × 10⁻⁶ F"},
            },
            "answer": 6.0,
            "display": "6.0 V",
            "cue_values": ["2.0", "4.0", "6.0", "9.0"],
            "context": (
                "Capacitor A stores charge {Q_A} and has capacitance {C_A}. "
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to capacitor A."
            ),
            "question": "What voltage is across capacitor A?",
            "cue_sentence": (
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to capacitor A."
            ),
            "topic_tags": ["circuits", "voltage", "capacitor", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "Q_A / C_A" has free symbols {Q_A, C_A}; '
                "the distractor symbol V_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_025",
            "sequence": 25,
            "governing_law": "terminal_voltage",
            "equation_latex": "V_{terminal} = \\mathcal{E} - I r",
            "equation_sympy": "emf - I * r",
            "target_quantity": "terminal_voltage_of_battery_A",
            "parameters": {
                "emf": {"value": 9.0, "units": "V", "description": "battery emf"},
                "I": {"value": 1.5, "units": "A", "description": "current supplied by the battery"},
                "r": {"value": 2.0, "units": "Ω", "description": "internal resistance"},
            },
            "answer": 6.0,
            "display": "6.0 V",
            "cue_values": ["3.0", "6.0", "9.0", "12.0"],
            "context": (
                "Battery A has emf {emf} V, internal resistance {r} Ω, and supplies current {I} A. "
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the main circuit."
            ),
            "question": "What is the terminal voltage of battery A?",
            "cue_sentence": (
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the main circuit."
            ),
            "topic_tags": ["circuits", "voltage", "battery", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "emf - I * r" has free symbols {emf, I, r}; '
                "the distractor symbol V_B is absent from the governing equation."
            ),
        },
        {
            "template_id": "CM_B_UM_026",
            "sequence": 26,
            "governing_law": "potential_divider",
            "equation_latex": "V_A = V_{in} \\frac{R_A}{R_A + R_B}",
            "equation_sympy": "V_in * R_A / (R_A + R_B)",
            "target_quantity": "divider_voltage_across_resistor_A",
            "parameters": {
                "V_in": {"value": 20.0, "units": "V", "description": "input voltage"},
                "R_A": {"value": 5.0, "units": "Ω", "description": "resistance of resistor A"},
                "R_B": {"value": 15.0, "units": "Ω", "description": "resistance of resistor B"},
            },
            "answer": 5.0,
            "display": "5.0 V",
            "cue_values": ["2.0", "4.0", "5.0", "8.0"],
            "context": (
                "A potential divider has input voltage {V_in} V with resistor A = {R_A} Ω and resistor B = {R_B} Ω. "
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the divider."
            ),
            "question": "What voltage appears across resistor A?",
            "cue_sentence": (
                "A disconnected battery elsewhere in the diagram has an emf of {V_B_display} V, "
                "but it is not connected to the divider."
            ),
            "topic_tags": ["circuits", "voltage", "potential_divider", "unit_matched_cue_b"],
            "proof": (
                'The governing expression "V_in * R_A / (R_A + R_B)" has free symbols {V_in, R_A, R_B}; '
                "the distractor symbol V_B is absent from the governing equation."
            ),
        },
    ]

    return [
        build_common_template(
            template_id=spec["template_id"],
            domain="electrostatics_circuits",
            sequence=spec["sequence"],
            governing_law=spec["governing_law"],
            governing_equation_latex=spec["equation_latex"],
            governing_equation_sympy=spec["equation_sympy"],
            target_quantity=spec["target_quantity"],
            target_units="V",
            parameters=spec["parameters"],
            correct_answer_value=spec["answer"],
            correct_answer_display=spec["display"],
            cue_slot=cue_b_slot(
                name="V_B_display",
                description="Voltage or emf in a separate isolated circuit, unit-matched with the target voltage",
                distractor_symbol="V_B",
                distractor_units="V",
                value_labels=spec["cue_values"],
                proof=spec["proof"],
            ),
            prompt_context=spec["context"],
            prompt_question=spec["question"],
            cue_sentence=spec["cue_sentence"],
            topic_tags=spec["topic_tags"],
        )
        for spec in specs
    ]


def torque_torque_templates() -> list[dict[str, Any]]:
    """Return the Stage 6 Torque/Torque unit-matched family block (5 templates)."""

    specs = [
        ("CM_B_UM_027", 27, 0.3, 20.0, 6.0, ["2.0", "4.0", "6.0", "10.0"]),
        ("CM_B_UM_028", 28, 0.5, 30.0, 15.0, ["5.0", "10.0", "15.0", "20.0"]),
        ("CM_B_UM_029", 29, 0.4, 25.0, 10.0, ["4.0", "7.0", "10.0", "14.0"]),
        ("CM_B_UM_030", 30, 0.8, 15.0, 12.0, ["4.0", "8.0", "12.0", "18.0"]),
        ("CM_B_UM_031", 31, 0.2, 50.0, 10.0, ["3.0", "6.0", "10.0", "15.0"]),
    ]
    families: list[dict[str, Any]] = []
    for template_id, sequence, radius, force, answer, cue_values in specs:
        families.append(
            build_common_template(
                template_id=template_id,
                sequence=sequence,
                governing_law="torque_from_perpendicular_force",
                governing_equation_latex="\\tau_A = r_A F_A",
                governing_equation_sympy="r_A * F_A",
                target_quantity="torque_on_system_A",
                target_units="N*m",
                correct_answer_display=f"{answer:.1f} N*m",
                parameters={
                    "r_A": {"value": radius, "units": "m", "description": "lever arm length for system A"},
                    "F_A": {"value": force, "units": "N", "description": "perpendicular force on system A"},
                },
                correct_answer_value=answer,
                cue_slot=cue_b_slot(
                    name="tau_B_display",
                    description="Torque in a separate isolated mechanical system, unit-matched with the target torque",
                    distractor_symbol="tau_B",
                    distractor_units="N*m",
                    value_labels=cue_values,
                    proof=(
                        'The governing expression "r_A * F_A" has free symbols {r_A, F_A}; '
                        "the distractor symbol tau_B is absent from the governing equation. "
                        "The distractor torque belongs to a mechanically separate system B."
                    ),
                ),
                prompt_context=(
                    "System A has a lever arm of {r_A} m and experiences a perpendicular force of {F_A} N. "
                    "In an adjacent workshop, a separate wrench system B produces a torque of {tau_B_display} N*m, "
                    "but it is mechanically isolated from system A."
                ),
                prompt_question="What torque acts on system A?",
                cue_sentence=(
                    "In an adjacent workshop, a separate wrench system B produces a torque of {tau_B_display} N*m, "
                    "but it is mechanically isolated from system A."
                ),
                topic_tags=["mechanics", "torque", "rotational_dynamics", "unit_matched_cue_b"],
            )
        )
    return families


def frequency_frequency_templates() -> list[dict[str, Any]]:
    """Return the Stage 6 Frequency/Frequency unit-matched family block (5 templates)."""

    families: list[dict[str, Any]] = []
    frequency_tolerance = 1e-3

    families.append(
        build_common_template(
            template_id="CM_B_UM_032",
            sequence=32,
            governing_law="spring_mass_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{k_A / m_A}",
            governing_equation_sympy="sqrt(k_A / m_A) / (2 * pi)",
            target_quantity="spring_mass_frequency_A",
            target_units="Hz",
            parameters={
                "k_A": {"value": 100.0, "units": "N/m", "description": "spring constant"},
                "m_A": {"value": 1.0, "units": "kg", "description": "mass on spring A"},
            },
            correct_answer_value=math.sqrt(100.0) / (2 * math.pi),
            correct_answer_display="1.592 Hz",
            verification_tolerance=frequency_tolerance,
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate oscillator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.5", "1.0", "1.6", "2.5"],
                proof=(
                    'The governing expression "sqrt(k_A / m_A) / (2 * pi)" has free symbols {k_A, m_A}; '
                    "the distractor symbol f_B is absent from the governing equation."
                ),
            ),
            prompt_context=(
                "Spring-mass system A has spring constant {k_A} N/m and attached mass {m_A} kg. "
                "In an adjacent part of the lab, oscillator B runs at {f_B_display} Hz, "
                "but oscillator B never interacts with system A."
            ),
            prompt_question="What is the oscillation frequency of system A?",
            cue_sentence=(
                "In an adjacent part of the lab, oscillator B runs at {f_B_display} Hz, "
                "but oscillator B never interacts with system A."
            ),
            topic_tags=["mechanics", "frequency", "oscillation", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_033",
            sequence=33,
            governing_law="pendulum_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{g / L_A}",
            governing_equation_sympy="sqrt(g / L_A) / (2 * pi)",
            target_quantity="pendulum_frequency_A",
            target_units="Hz",
            parameters={
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "L_A": {"value": 1.0, "units": "m", "description": "pendulum length"},
            },
            correct_answer_value=math.sqrt(GRAVITY / 1.0) / (2 * math.pi),
            correct_answer_display="0.498 Hz",
            verification_tolerance=frequency_tolerance,
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate pendulum B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.25", "0.5", "0.75", "1.0"],
                proof=(
                    'The governing expression "sqrt(g / L_A) / (2 * pi)" has free symbols {g, L_A}; '
                    "the distractor symbol f_B is absent from the governing equation."
                ),
            ),
            prompt_context=(
                "Pendulum A has length {L_A} m. Take g = {g} m/s². "
                "In an adjacent part of the lab, pendulum B oscillates at {f_B_display} Hz, "
                "but pendulum B never interacts with system A."
            ),
            prompt_question="What is the oscillation frequency of pendulum A?",
            cue_sentence=(
                "In an adjacent part of the lab, pendulum B oscillates at {f_B_display} Hz, "
                "but pendulum B never interacts with system A."
            ),
            topic_tags=["mechanics", "frequency", "pendulum", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_034",
            sequence=34,
            governing_law="spring_mass_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{k_A / m_A}",
            governing_equation_sympy="sqrt(k_A / m_A) / (2 * pi)",
            target_quantity="spring_mass_frequency_A",
            target_units="Hz",
            parameters={
                "k_A": {"value": 200.0, "units": "N/m", "description": "spring constant"},
                "m_A": {"value": 2.0, "units": "kg", "description": "mass on spring A"},
            },
            correct_answer_value=math.sqrt(200.0 / 2.0) / (2 * math.pi),
            correct_answer_display="1.592 Hz",
            verification_tolerance=frequency_tolerance,
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate oscillator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.5", "1.0", "1.6", "3.0"],
                proof=(
                    'The governing expression "sqrt(k_A / m_A) / (2 * pi)" has free symbols {k_A, m_A}; '
                    "the distractor symbol f_B is absent from the governing equation."
                ),
            ),
            prompt_context=(
                "Spring-mass system A has spring constant {k_A} N/m and attached mass {m_A} kg. "
                "In an adjacent part of the lab, oscillator B runs at {f_B_display} Hz, "
                "but oscillator B never interacts with system A."
            ),
            prompt_question="What is the oscillation frequency of system A?",
            cue_sentence=(
                "In an adjacent part of the lab, oscillator B runs at {f_B_display} Hz, "
                "but oscillator B never interacts with system A."
            ),
            topic_tags=["mechanics", "frequency", "oscillation", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_035",
            sequence=35,
            governing_law="pendulum_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{g / L_A}",
            governing_equation_sympy="sqrt(g / L_A) / (2 * pi)",
            target_quantity="pendulum_frequency_A",
            target_units="Hz",
            parameters={
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "L_A": {"value": 0.25, "units": "m", "description": "pendulum length"},
            },
            correct_answer_value=math.sqrt(GRAVITY / 0.25) / (2 * math.pi),
            correct_answer_display="0.997 Hz",
            verification_tolerance=frequency_tolerance,
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate pendulum B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.5", "1.0", "1.5", "2.0"],
                proof=(
                    'The governing expression "sqrt(g / L_A) / (2 * pi)" has free symbols {g, L_A}; '
                    "the distractor symbol f_B is absent from the governing equation."
                ),
            ),
            prompt_context=(
                "Pendulum A has length {L_A} m. Take g = {g} m/s². "
                "In an adjacent part of the lab, pendulum B oscillates at {f_B_display} Hz, "
                "but pendulum B never interacts with system A."
            ),
            prompt_question="What is the oscillation frequency of pendulum A?",
            cue_sentence=(
                "In an adjacent part of the lab, pendulum B oscillates at {f_B_display} Hz, "
                "but pendulum B never interacts with system A."
            ),
            topic_tags=["mechanics", "frequency", "pendulum", "unit_matched_cue_b"],
        )
    )

    families.append(
        build_common_template(
            template_id="CM_B_UM_036",
            sequence=36,
            governing_law="wave_frequency",
            governing_equation_latex="f_A = v_A / \\lambda_A",
            governing_equation_sympy="v_A / lambda_A",
            target_quantity="wave_frequency_A",
            target_units="Hz",
            parameters={
                "v_A": {"value": 6.0, "units": "m/s", "description": "wave speed on the string"},
                "lambda_A": {"value": 0.3, "units": "m", "description": "wavelength on the string"},
            },
            correct_answer_value=20.0,
            correct_answer_display="20.0 Hz",
            verification_tolerance=frequency_tolerance,
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate oscillator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["8.0", "15.0", "20.0", "30.0"],
                proof=(
                    'The governing expression "v_A / lambda_A" has free symbols {v_A, lambda_A}; '
                    "the distractor symbol f_B is absent from the governing equation."
                ),
            ),
            prompt_context=(
                "A wave on string A has speed {v_A} m/s and wavelength {lambda_A} m. "
                "In an adjacent part of the lab, oscillator B runs at {f_B_display} Hz, "
                "but it never interacts with string A."
            ),
            prompt_question="What is the wave frequency on string A?",
            cue_sentence=(
                "In an adjacent part of the lab, oscillator B runs at {f_B_display} Hz, "
                "but it never interacts with string A."
            ),
            topic_tags=["mechanics", "frequency", "waves", "unit_matched_cue_b"],
        )
    )

    return families


def charge_charge_templates() -> list[dict[str, Any]]:
    """Return the Stage 6 Charge/Charge unit-matched family block (4 templates)."""

    specs = [
        ("CM_B_UM_037", 37, 50e-6, 6.0, 3e-4, "3.0e-4 C", ["1e-4", "2e-4", "3e-4", "5e-4"]),
        ("CM_B_UM_038", 38, 100e-6, 9.0, 9e-4, "9.0e-4 C", ["3e-4", "6e-4", "9e-4", "1.2e-3"]),
        ("CM_B_UM_039", 39, 200e-6, 3.0, 6e-4, "6.0e-4 C", ["2e-4", "4e-4", "6e-4", "8e-4"]),
        ("CM_B_UM_040", 40, 10e-6, 5.0, 5e-5, "5.0e-5 C", ["1e-5", "3e-5", "5e-5", "8e-5"]),
    ]
    families: list[dict[str, Any]] = []
    for template_id, sequence, capacitance, voltage, answer, display, cue_values in specs:
        families.append(
            build_common_template(
                template_id=template_id,
                domain="electrostatics_circuits",
                sequence=sequence,
                governing_law="capacitor_charge",
                governing_equation_latex="Q_A = C_A V_A",
                governing_equation_sympy="C_A * V_A",
                target_quantity="charge_on_capacitor_A",
                target_units="C",
                correct_answer_display=display,
                parameters={
                    "C_A": {
                        "value": capacitance,
                        "units": "F",
                        "description": "capacitance of capacitor A",
                        "display": f"{capacitance:.1e} F",
                    },
                    "V_A": {"value": voltage, "units": "V", "description": "voltage across capacitor A"},
                },
                correct_answer_value=answer,
                cue_slot=cue_b_slot(
                    name="Q_B_display",
                    description="Charge on separate disconnected capacitor B, unit-matched with the target charge",
                    distractor_symbol="Q_B",
                    distractor_units="C",
                    value_labels=cue_values,
                    proof=(
                        'The governing expression "C_A * V_A" has free symbols {C_A, V_A}; '
                        "the distractor symbol Q_B is absent from the governing equation. "
                        "Capacitor B is fully disconnected from capacitor A and its circuit."
                    ),
                ),
                prompt_context=(
                    "Capacitor A has capacitance {C_A} and is connected across a {V_A} V source. "
                    "A separate capacitor C2 in an adjacent box holds a charge of {Q_B_display} C, "
                    "but C2 is fully disconnected from capacitor A and its circuit."
                ),
                prompt_question="What charge is stored on capacitor A?",
                cue_sentence=(
                    "A separate capacitor C2 in an adjacent box holds a charge of {Q_B_display} C, "
                    "but C2 is fully disconnected from capacitor A and its circuit."
                ),
                topic_tags=["circuits", "charge", "capacitor", "unit_matched_cue_b"],
            )
        )
    return families


def write_template(path: Path, payload: dict[str, Any]) -> None:
    """Write one template YAML to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def verify_template(template_path: Path, output_dir: Path) -> dict[str, Any]:
    """Run the symbolic verifier and persist one JSON report."""

    result = SymbolicVerifier().verify(str(template_path))
    payload = {
        "template_id": result.template_id,
        "all_passed": result.all_passed,
        "checks": [
            {"passed": check.passed, "check_name": check.check_name, "detail": check.detail}
            for check in result.checks
        ],
    }
    write_json(output_dir / f"{result.template_id}.json", payload)
    return payload


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Stage 6 Phase 1 template construction."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--verification-dir", default=str(DEFAULT_VERIFICATION_DIR))
    parser.add_argument(
        "--class-filter",
        choices=(
            "force_force",
            "velocity_velocity",
            "current_current",
            "voltage_voltage",
            "torque_torque",
            "frequency_frequency",
            "charge_charge",
            "all",
        ),
        default="force_force",
        help="Which Stage 6 class block to build in this run.",
    )
    return parser.parse_args()


def main() -> None:
    """Build the requested Stage 6 Phase 1 templates and run verifier checks."""

    args = parse_args()
    output_dir = Path(args.output_dir)
    verification_dir = Path(args.verification_dir)

    class_builders = {
        "force_force": force_force_templates,
        "velocity_velocity": velocity_velocity_templates,
        "current_current": current_current_templates,
        "voltage_voltage": voltage_voltage_templates,
        "torque_torque": torque_torque_templates,
        "frequency_frequency": frequency_frequency_templates,
        "charge_charge": charge_charge_templates,
    }

    if args.class_filter == "all":
        templates: list[dict[str, Any]] = []
        for builder in class_builders.values():
            templates.extend(builder())
    else:
        templates = class_builders[args.class_filter]()
    for payload in templates:
        template_path = output_dir / f"{payload['template_id']}.yaml"
        write_template(template_path, payload)
        verify_template(template_path, verification_dir)

    print(f"Built and verified {len(templates)} Stage 6 templates.")


if __name__ == "__main__":
    main()
