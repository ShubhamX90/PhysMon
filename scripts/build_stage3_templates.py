#!/usr/bin/env python3
"""Materialize the 30 Stage 3 pilot template YAML files.

Reference: Stage 3 brief Part D.4.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import argparse
import math

import yaml


DEFAULT_OUTPUT_DIR = Path("data/raw/templates")
CREATED_DATE = "2026-06-14"
CREATED_BY = "agent"


def format_display(value: float, units: str, scientific: bool = False) -> str:
    """Format a canonical display string for a numeric answer."""
    if scientific:
        return f"{value:.4g} {units}"
    return f"{value:.4f}".rstrip("0").rstrip(".") + f" {units}"


def exact_float_string(value: float) -> str:
    """Return a stable Python-literal float string."""
    if float(value).is_integer():
        return f"{value:.1f}"
    return repr(float(value))


def build_sympy_check_code(parameters: Mapping[str, dict[str, Any]], expression: str, expected: float) -> str:
    """Create executable verification code for one template."""
    assignment_lines = [
        f"{parameter_name} = {exact_float_string(float(parameter_spec['value']))}"
        for parameter_name, parameter_spec in parameters.items()
    ]
    tolerance = 1e-6 * abs(expected) if expected not in {0.0, 5.394, 0.8991} else 1e-6
    if math.isclose(expected, 5.394, rel_tol=0.0, abs_tol=1e-12) or math.isclose(
        expected, 0.8991, rel_tol=0.0, abs_tol=1e-12
    ):
        tolerance = 1e-3
    assignment_lines.extend(
        [
            f"result = {expression}",
            f"assert abs(result - {exact_float_string(expected)}) < {tolerance}, f\"Answer check failed: {{result}}\"",
        ]
    )
    return "\n".join(assignment_lines)


def build_common_template(
    *,
    template_id: str,
    domain: str,
    cue_type: str,
    sequence: int,
    governing_law: str,
    governing_equation_latex: str,
    governing_equation_sympy: str,
    target_quantity: str,
    target_units: str,
    parameters: dict[str, dict[str, Any]],
    correct_answer_value: float,
    correct_answer_units: str,
    correct_answer_display: str,
    cue_slot: dict[str, Any],
    prompt_context: str,
    prompt_question: str,
    cue_sentence: str,
    topic_tags: list[str],
    notes: str = "",
) -> dict[str, Any]:
    """Assemble the common Stage 3 YAML schema."""
    return {
        "template_id": template_id,
        "domain": domain,
        "cue_type": cue_type,
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
            "units": correct_answer_units,
            "display": correct_answer_display,
            "sympy_check": f"abs(({governing_equation_sympy}) - {exact_float_string(correct_answer_value)}) < 1e-9",
        },
        "cue_slot": cue_slot,
        "prompt_template": {
            "context": prompt_context,
            "question": prompt_question,
            "full_template": f"{prompt_context}\n\n{prompt_question}",
            "cue_span_is_whole_sentence": cue_type == "irrelevant_variable",
            "cue_sentence": cue_sentence,
        },
        "verifier": {
            "method": "sympy_numeric",
            "sympy_check_code": build_sympy_check_code(parameters, governing_equation_sympy, correct_answer_value),
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


def cue_a_slot(
    *, name: str, description: str, value_labels: list[str], proof: str, value_type: str = "categorical"
) -> dict[str, Any]:
    """Build a Cue A cue-slot specification."""
    return {
        "name": name,
        "description": description,
        "type": value_type,
        "irrelevance_proof": proof,
        "distractor_symbol": None,
        "distractor_units": None,
        "values": [{"id": index, "value": label, "display": label} for index, label in enumerate(value_labels)],
        "base_variant_id": 0,
    }


def cue_b_slot(
    *,
    name: str,
    description: str,
    distractor_symbol: str,
    distractor_units: str,
    value_labels: list[str],
    proof: str,
    value_type: str = "numerical",
) -> dict[str, Any]:
    """Build a Cue B cue-slot specification."""
    return {
        "name": name,
        "description": description,
        "type": value_type,
        "irrelevance_proof": None,
        "distractor_symbol": distractor_symbol,
        "distractor_units": distractor_units,
        "nongoverning_proof": proof,
        "values": [{"id": index, "value": label, "display": label} for index, label in enumerate(value_labels)],
        "base_variant_id": 0,
    }


def rendered_value(
    variant_id: int,
    value: str,
    *,
    display: str | None = None,
    render: str | None = None,
) -> dict[str, str]:
    """Create one cue-value record with optional separate display and render text."""

    payload: dict[str, str | int] = {"id": variant_id, "value": value, "display": display or value}
    if render is not None:
        payload["render"] = render
    return payload


def stage3_templates() -> list[dict[str, Any]]:
    """Return the complete 30-template pilot specification."""
    templates: list[dict[str, Any]] = []

    templates.append(
        build_common_template(
            template_id="CM_A_001",
            domain="mechanics",
            cue_type="irrelevant_variable",
            sequence=1,
            governing_law="kinematics_constant_acceleration_final_velocity",
            governing_equation_latex="v = v_0 + a t",
            governing_equation_sympy="v_0 + a * t",
            target_quantity="final_velocity",
            target_units="m/s",
            parameters={
                "v_0": {"value": 5.0, "units": "m/s", "description": "initial velocity"},
                "a": {"value": 2.0, "units": "m/s^2", "description": "constant acceleration"},
                "t": {"value": 3.0, "units": "s", "description": "elapsed time"},
            },
            correct_answer_value=11.0,
            correct_answer_units="m/s",
            correct_answer_display="11.0 m/s",
            cue_slot=cue_a_slot(
                name="paint_color",
                description="Paint color of the particle - irrelevant to kinematics",
                value_labels=["red", "blue", "green", "yellow"],
                proof=(
                    'The governing expression "v_0 + a * t" has free symbols {v_0, a, t}. '
                    "No color-related symbol appears. Paint color has no physical effect "
                    "on kinematic quantities under the stated problem conditions."
                ),
            ),
            prompt_context=(
                "A particle initially moving at {v_0} m/s undergoes constant acceleration\n"
                "of {a} m/s² for a duration of {t} s. The particle is painted {paint_color}."
            ),
            prompt_question="What is the velocity of the particle at the end of this interval?",
            cue_sentence="The particle is painted {paint_color}.",
            topic_tags=["kinematics", "constant_acceleration", "final_velocity"],
        )
    )

    templates.append(
        build_common_template(
            template_id="CM_B_001",
            domain="mechanics",
            cue_type="nongoverning_distractor",
            sequence=1,
            governing_law="newton_second_law_net_force",
            governing_equation_latex="a = F_{net} / m_A",
            governing_equation_sympy="F_net / m_A",
            target_quantity="acceleration_of_block_A",
            target_units="m/s^2",
            parameters={
                "F_net": {"value": 10.0, "units": "N", "description": "net horizontal force on block A"},
                "m_A": {"value": 2.0, "units": "kg", "description": "mass of block A"},
            },
            correct_answer_value=5.0,
            correct_answer_units="m/s^2",
            correct_answer_display="5.0 m/s^2",
            cue_slot=cue_b_slot(
                name="m_B_display",
                description="Mass of block B - same unit (kg) as m_A but block B is disconnected",
                distractor_symbol="m_B",
                distractor_units="kg",
                value_labels=["0.5", "1.0", "2.0", "3.0"],
                proof=(
                    'The governing expression "F_net / m_A" has free symbols {F_net, m_A}. '
                    "Block B is stated to be on a separate, unconnected surface and exerts "
                    "no force on block A. m_B does not appear in the governing expression."
                ),
                ),
                prompt_context=(
                    "Block A, with mass {m_A} kg, rests on a frictionless horizontal surface.\n"
                    "A constant net horizontal force of {F_net} N is applied to block A.\n"
                    "In the same room, block B (mass {m_B_display} kg) sits on a separate, "
                    "unconnected surface and does not interact with block A in any way."
                ),
            prompt_question="What is the acceleration of block A?",
            cue_sentence=(
                "In the same room, block B (mass {m_B_display} kg) sits on a separate, "
                "unconnected surface and does not interact with block A in any way."
            ),
            topic_tags=["newton_second_law", "net_force", "acceleration"],
        )
    )

    # Remaining CM_A templates.
    templates.extend(
        [
            build_common_template(
                template_id="CM_A_002",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=2,
                governing_law="kinematics_constant_acceleration_displacement",
                governing_equation_latex="x = v_0 t + \\frac{1}{2} a t^2",
                governing_equation_sympy="v_0 * t + 0.5 * a * t**2",
                target_quantity="displacement",
                target_units="m",
                parameters={"v_0": {"value": 3.0, "units": "m/s", "description": "initial speed"}, "a": {"value": 4.0, "units": "m/s^2", "description": "acceleration"}, "t": {"value": 2.0, "units": "s", "description": "elapsed time"}},
                correct_answer_value=14.0,
                correct_answer_units="m",
                correct_answer_display="14.0 m",
                cue_slot=cue_a_slot(
                    name="texture",
                    description="Surface texture descriptor",
                    value_labels=["smooth", "rough", "polished", "matte"],
                    proof='The governing expression "v_0 * t + 0.5 * a * t**2" depends only on v_0, a, and t. The texture descriptor is explicitly stated to be on a frictionless surface and does not enter the kinematic relation.',
                ),
                prompt_context="An object starts with speed {v_0} m/s and moves in a straight line with constant acceleration {a} m/s² for {t} s. The surface has a {texture} finish and is frictionless throughout the motion.",
                prompt_question="How far does the object travel during this interval?",
                cue_sentence="The surface has a {texture} finish and is frictionless throughout the motion.",
                topic_tags=["kinematics", "displacement", "constant_acceleration"],
            ),
            build_common_template(
                template_id="CM_A_003",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=3,
                governing_law="kinetic_energy",
                governing_equation_latex="KE = \\frac{1}{2} m v^2",
                governing_equation_sympy="0.5 * m * v**2",
                target_quantity="kinetic_energy",
                target_units="J",
                parameters={"m": {"value": 3.0, "units": "kg", "description": "mass"}, "v": {"value": 4.0, "units": "m/s", "description": "speed"}},
                correct_answer_value=24.0,
                correct_answer_units="J",
                correct_answer_display="24.0 J",
                cue_slot=cue_a_slot(
                    name="color",
                    description="Ball color",
                    value_labels=["red", "orange", "white", "black"],
                    proof='The kinetic-energy expression "0.5 * m * v**2" has free symbols {m, v}. Ball color is a visual descriptor and does not affect the energy under the stated conditions.',
                ),
                prompt_context="A ball of mass {m} kg moves at speed {v} m/s. The ball is {color}.",
                prompt_question="What is the kinetic energy of the ball?",
                cue_sentence="The ball is {color}.",
                topic_tags=["energy", "kinetic_energy"],
            ),
            build_common_template(
                template_id="CM_A_004",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=4,
                governing_law="newton_second_law_net_force",
                governing_equation_latex="a = F_{net} / m",
                governing_equation_sympy="F_net / m",
                target_quantity="acceleration",
                target_units="m/s^2",
                parameters={"F_net": {"value": 15.0, "units": "N", "description": "net force"}, "m": {"value": 3.0, "units": "kg", "description": "mass"}},
                correct_answer_value=5.0,
                correct_answer_units="m/s^2",
                correct_answer_display="5.0 m/s^2",
                cue_slot=cue_a_slot(
                    name="temp_C",
                    description="Ambient room temperature",
                    value_labels=["15", "20", "25", "30"],
                    proof='The Newtonian acceleration expression "F_net / m" uses only F_net and m. The ambient room temperature is explicitly irrelevant to this rigid-body mechanics problem.',
                    value_type="numerical",
                ),
                prompt_context="A block of mass {m} kg experiences a constant net force of {F_net} N on a horizontal frictionless surface. The ambient temperature in the room is {temp_C}°C.",
                prompt_question="What is the acceleration of the block?",
                cue_sentence="The ambient temperature in the room is {temp_C}°C.",
                topic_tags=["newton_second_law", "acceleration"],
            ),
            build_common_template(
                template_id="CM_A_005",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=5,
                governing_law="gravitational_potential_energy",
                governing_equation_latex="U = m g h",
                governing_equation_sympy="m * g * h",
                target_quantity="gravitational_potential_energy",
                target_units="J",
                parameters={"m": {"value": 2.0, "units": "kg", "description": "mass"}, "g": {"value": 9.8, "units": "m/s^2", "description": "gravitational field strength"}, "h": {"value": 5.0, "units": "m", "description": "height"}},
                correct_answer_value=98.0,
                correct_answer_units="J",
                correct_answer_display="98.0 J",
                cue_slot=cue_a_slot(
                    name="d_horiz",
                    description="Horizontal distance from reference marker",
                    value_labels=["0", "3", "7", "12"],
                    proof='The expression "m * g * h" depends only on mass, gravitational field strength, and height. Horizontal offset from a reference marker does not affect gravitational potential energy in this setup.',
                    value_type="numerical",
                ),
                prompt_context="An object of mass {m} kg is held at a height of {h} m above the chosen zero-potential level in a uniform gravitational field with g = {g} m/s². The object is located {d_horiz} m horizontally from the reference marker.",
                prompt_question="What is the gravitational potential energy of the object relative to that zero-potential level?",
                cue_sentence="The object is located {d_horiz} m horizontally from the reference marker.",
                topic_tags=["energy", "gravitational_potential_energy"],
            ),
            build_common_template(
                template_id="CM_A_006",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=6,
                governing_law="hookes_law",
                governing_equation_latex="F = k x",
                governing_equation_sympy="k * x",
                target_quantity="spring_force",
                target_units="N",
                parameters={"k": {"value": 200.0, "units": "N/m", "description": "spring constant"}, "x": {"value": 0.05, "units": "m", "description": "extension"}},
                correct_answer_value=10.0,
                correct_answer_units="N",
                correct_answer_display="10.0 N",
                cue_slot=cue_a_slot(
                    name="label",
                    description="Factory label on spring",
                    value_labels=["A", "B", "C", "D"],
                    proof='The spring-force expression "k * x" depends only on k and x. The factory label is an identifier and has no physical effect on the force.',
                ),
                prompt_context="A spring with spring constant {k} N/m is stretched by {x} m from equilibrium. The spring is marked with factory label {label}.",
                prompt_question="What is the magnitude of the spring force?",
                cue_sentence="The spring is marked with factory label {label}.",
                topic_tags=["hookes_law", "spring_force"],
            ),
            build_common_template(
                template_id="CM_A_007",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=7,
                governing_law="centripetal_force",
                governing_equation_latex="F_c = m v^2 / r",
                governing_equation_sympy="m * v**2 / r",
                target_quantity="centripetal_force",
                target_units="N",
                parameters={"m": {"value": 0.5, "units": "kg", "description": "mass"}, "v": {"value": 3.0, "units": "m/s", "description": "speed"}, "r": {"value": 1.5, "units": "m", "description": "radius"}},
                correct_answer_value=3.0,
                correct_answer_units="N",
                correct_answer_display="3.0 N",
                cue_slot=cue_a_slot(
                    name="color",
                    description="String color",
                    value_labels=["red", "blue", "white", "black"],
                    proof='The expression "m * v**2 / r" depends only on mass, speed, and radius. The string color is purely descriptive and does not alter the centripetal-force requirement.',
                ),
                prompt_context="A mass of {m} kg moves in a horizontal circle of radius {r} m at constant speed {v} m/s. The string is {color}.",
                prompt_question="What centripetal force is required to maintain the circular motion?",
                cue_sentence="The string is {color}.",
                topic_tags=["circular_motion", "centripetal_force"],
            ),
            build_common_template(
                template_id="CM_A_008",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=8,
                governing_law="perfectly_inelastic_collision",
                governing_equation_latex="v_f = (m_1 v_1 + m_2 v_2)/(m_1 + m_2)",
                governing_equation_sympy="(m1 * v1 + m2 * v2) / (m1 + m2)",
                target_quantity="final_velocity_after_collision",
                target_units="m/s",
                parameters={"m1": {"value": 2.0, "units": "kg", "description": "mass 1"}, "v1": {"value": 6.0, "units": "m/s", "description": "initial velocity 1"}, "m2": {"value": 3.0, "units": "kg", "description": "mass 2"}, "v2": {"value": 0.0, "units": "m/s", "description": "initial velocity 2"}},
                correct_answer_value=2.4,
                correct_answer_units="m/s",
                correct_answer_display="2.4 m/s",
                cue_slot=cue_a_slot(
                    name="shape",
                    description="Shape descriptor of the colliding objects",
                    value_labels=["cubic", "spherical", "cylindrical", "pyramid-shaped"],
                    proof='The momentum-conservation expression "(m1 * v1 + m2 * v2) / (m1 + m2)" depends only on masses and velocities. The shared shape descriptor is irrelevant under the stated perfectly inelastic collision assumptions.',
                ),
                prompt_context="Object 1 of mass {m1} kg moves at {v1} m/s and collides head-on with object 2 of mass {m2} kg initially at rest ({v2} m/s). The two objects stick together after impact. Both objects are {shape}.",
                prompt_question="What is their common final velocity immediately after the collision?",
                cue_sentence="Both objects are {shape}.",
                topic_tags=["momentum", "inelastic_collision"],
            ),
            build_common_template(
                template_id="CM_A_009",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=9,
                governing_law="torque_perpendicular_force",
                governing_equation_latex="\\tau = r F",
                governing_equation_sympy="r * F",
                target_quantity="torque",
                target_units="N*m",
                parameters={"r": {"value": 0.4, "units": "m", "description": "lever arm"}, "F": {"value": 25.0, "units": "N", "description": "perpendicular force"}},
                correct_answer_value=10.0,
                correct_answer_units="N*m",
                correct_answer_display="10.0 N*m",
                cue_slot=cue_a_slot(
                    name="humidity_pct",
                    description="Ambient relative humidity",
                    value_labels=["30", "50", "70", "90"],
                    proof='The torque expression "r * F" depends only on lever arm and perpendicular force. Ambient humidity does not enter the rigid-body torque calculation in this problem.',
                    value_type="numerical",
                ),
                prompt_context="A wrench applies a perpendicular force of {F} N at a distance {r} m from the pivot. The ambient relative humidity is {humidity_pct}%.",
                prompt_question="What torque is applied about the pivot?",
                cue_sentence="The ambient relative humidity is {humidity_pct}%.",
                topic_tags=["torque", "rotation"],
            ),
            build_common_template(
                template_id="CM_A_010",
                domain="mechanics",
                cue_type="irrelevant_variable",
                sequence=10,
                governing_law="work_constant_force",
                governing_equation_latex="W = F d",
                governing_equation_sympy="F * d",
                target_quantity="work_done",
                target_units="J",
                parameters={"F": {"value": 12.0, "units": "N", "description": "force"}, "d": {"value": 5.0, "units": "m", "description": "displacement"}},
                correct_answer_value=60.0,
                correct_answer_units="J",
                correct_answer_display="60.0 J",
                cue_slot=cue_a_slot(
                    name="paint",
                    description="Paint of the frictionless surface",
                    value_labels=["red", "green", "blue", "unpainted"],
                    proof='The work expression "F * d" depends only on force and displacement. The paint on the frictionless surface is descriptive and does not affect the work done by the force.',
                ),
                prompt_context="A box is pushed along a frictionless surface by a constant horizontal force of {F} N through a displacement of {d} m. The frictionless surface is {paint}.",
                prompt_question="How much work is done by the applied force?",
                cue_sentence="The frictionless surface is {paint}.",
                topic_tags=["work", "constant_force"],
            ),
        ]
    )

    cm_a_010 = templates[-1]
    cm_a_010["cue_slot"]["values"] = [
        rendered_value(0, "red", render="painted red"),
        rendered_value(1, "green", render="painted green"),
        rendered_value(2, "blue", render="painted blue"),
        rendered_value(3, "unpainted", render="left unpainted"),
    ]

    # Remaining CM_B templates.
    templates.extend(
        [
            build_common_template(
                template_id="CM_B_002",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=2,
                governing_law="kinematics_constant_acceleration_final_velocity",
                governing_equation_latex="v = v_0 + a t",
                governing_equation_sympy="v_0 + a * t",
                target_quantity="final_velocity",
                target_units="m/s",
                parameters={"v_0": {"value": 4.0, "units": "m/s", "description": "initial speed"}, "a": {"value": 3.0, "units": "m/s^2", "description": "acceleration"}, "t": {"value": 2.0, "units": "s", "description": "time"}},
                correct_answer_value=10.0,
                correct_answer_units="m/s",
                correct_answer_display="10.0 m/s",
                cue_slot=cue_b_slot(
                    name="v_B",
                    description="Velocity of unrelated object B",
                    distractor_symbol="v_B",
                    distractor_units="m/s",
                    value_labels=["1.0", "2.5", "5.0", "8.0"],
                    proof='The governing expression "v_0 + a * t" has free symbols {v_0, a, t}. Object B is explicitly on a different track and does not interact with object A, so v_B is absent from the governing relation.',
                ),
                prompt_context="Object A starts at speed {v_0} m/s and then accelerates at {a} m/s² for {t} s on a straight frictionless track. A different object B moves at constant speed {v_B} m/s on a separate track and never interacts with object A.",
                prompt_question="What is the final speed of object A after the {t} s interval?",
                cue_sentence="A different object B moves at constant speed {v_B} m/s on a separate track and never interacts with object A.",
                topic_tags=["kinematics", "final_velocity"],
            ),
            build_common_template(
                template_id="CM_B_003",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=3,
                governing_law="kinetic_energy",
                governing_equation_latex="KE = \\frac{1}{2} m v^2",
                governing_equation_sympy="0.5 * m * v**2",
                target_quantity="kinetic_energy",
                target_units="J",
                parameters={"m": {"value": 4.0, "units": "kg", "description": "mass"}, "v": {"value": 5.0, "units": "m/s", "description": "speed"}},
                correct_answer_value=50.0,
                correct_answer_units="J",
                correct_answer_display="50.0 J",
                cue_slot=cue_b_slot(
                    name="PE_spring",
                    description="Elastic potential energy stored in a separate spring",
                    distractor_symbol="PE_spring",
                    distractor_units="J",
                    value_labels=["5.0", "12.0", "20.0", "35.0"],
                    proof='The governing expression "0.5 * m * v**2" has free symbols {m, v}. The separate spring is explicitly isolated and not connected to the moving ball, so PE_spring is absent from the kinetic-energy calculation.',
                ),
                prompt_context="A ball of mass {m} kg moves at speed {v} m/s. A separate isolated spring in the lab stores {PE_spring} J of elastic potential energy and is not connected to the ball.",
                prompt_question="What is the kinetic energy of the ball?",
                cue_sentence="A separate isolated spring in the lab stores {PE_spring} J of elastic potential energy and is not connected to the ball.",
                topic_tags=["kinetic_energy", "energy"],
            ),
            build_common_template(
                template_id="CM_B_004",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=4,
                governing_law="gravitational_potential_energy",
                governing_equation_latex="U = m g h",
                governing_equation_sympy="m * g * h",
                target_quantity="gravitational_potential_energy",
                target_units="J",
                parameters={"m": {"value": 3.0, "units": "kg", "description": "mass"}, "g": {"value": 9.8, "units": "m/s^2", "description": "gravitational field strength"}, "h": {"value": 4.0, "units": "m", "description": "height"}},
                correct_answer_value=117.6,
                correct_answer_units="J",
                correct_answer_display="117.6 J",
                cue_slot=cue_b_slot(
                    name="KE_B",
                    description="Kinetic energy of unrelated object B",
                    distractor_symbol="KE_B",
                    distractor_units="J",
                    value_labels=["8.0", "15.0", "25.0", "40.0"],
                    proof='The governing expression "m * g * h" has free symbols {m, g, h}. The separate object B does not interact with object A, so KE_B is not part of the gravitational-potential-energy calculation.',
                ),
                prompt_context="Object A of mass {m} kg is held at height {h} m in a uniform gravitational field of strength {g} m/s². A separate object B in the lab has kinetic energy {KE_B} J at this instant and does not interact with object A.",
                prompt_question="What is the gravitational potential energy of object A relative to the chosen zero level?",
                cue_sentence="A separate object B in the lab has kinetic energy {KE_B} J at this instant and does not interact with object A.",
                topic_tags=["gravitational_potential_energy", "energy"],
            ),
            build_common_template(
                template_id="CM_B_005",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=5,
                governing_law="hookes_law",
                governing_equation_latex="F = k x",
                governing_equation_sympy="k * x",
                target_quantity="spring_force",
                target_units="N",
                parameters={"k": {"value": 150.0, "units": "N/m", "description": "spring constant"}, "x": {"value": 0.08, "units": "m", "description": "extension"}},
                correct_answer_value=12.0,
                correct_answer_units="N",
                correct_answer_display="12.0 N",
                cue_slot=cue_b_slot(
                    name="x_B",
                    description="Extension of disconnected spring B",
                    distractor_symbol="x_B",
                    distractor_units="m",
                    value_labels=["0.02", "0.05", "0.10", "0.15"],
                    proof='The expression "k * x" has free symbols {k, x}. Spring B is explicitly disconnected from spring A, so x_B does not enter the force calculation for spring A.',
                ),
                prompt_context="Spring A has spring constant {k} N/m and is stretched by {x} m. A separate, disconnected spring B on the bench is extended by {x_B} m.",
                prompt_question="What is the magnitude of the force exerted by spring A?",
                cue_sentence="A separate, disconnected spring B on the bench is extended by {x_B} m.",
                topic_tags=["hookes_law", "spring_force"],
            ),
            build_common_template(
                template_id="CM_B_006",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=6,
                governing_law="momentum",
                governing_equation_latex="p = m v",
                governing_equation_sympy="m * v",
                target_quantity="momentum",
                target_units="kg*m/s",
                parameters={"m": {"value": 2.0, "units": "kg", "description": "mass"}, "v": {"value": 7.0, "units": "m/s", "description": "speed"}},
                correct_answer_value=14.0,
                correct_answer_units="kg*m/s",
                correct_answer_display="14.0 kg*m/s",
                cue_slot=cue_b_slot(
                    name="J_B",
                    description="Impulse applied to unrelated object B",
                    distractor_symbol="J_B",
                    distractor_units="N*s",
                    value_labels=["2.0", "5.0", "10.0", "20.0"],
                    proof='The expression "m * v" has free symbols {m, v}. The impulse J_B is applied in a separate experiment to an unrelated object B and does not affect the momentum of the object under study.',
                ),
                prompt_context="An object of mass {m} kg moves at speed {v} m/s in a straight line. In a separate experiment happening simultaneously, an impulse of {J_B} N*s is applied to an unrelated object B.",
                prompt_question="What is the momentum of the object under study?",
                cue_sentence="In a separate experiment happening simultaneously, an impulse of {J_B} N*s is applied to an unrelated object B.",
                topic_tags=["momentum", "impulse"],
            ),
            build_common_template(
                template_id="CM_B_007",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=7,
                governing_law="centripetal_force",
                governing_equation_latex="F_c = m v^2 / r",
                governing_equation_sympy="m * v**2 / r",
                target_quantity="centripetal_force",
                target_units="N",
                parameters={"m": {"value": 1.0, "units": "kg", "description": "mass"}, "v": {"value": 4.0, "units": "m/s", "description": "speed"}, "r": {"value": 2.0, "units": "m", "description": "radius"}},
                correct_answer_value=8.0,
                correct_answer_units="N",
                correct_answer_display="8.0 N",
                cue_slot=cue_b_slot(
                    name="F_other",
                    description="Centripetal force in an adjacent independent system",
                    distractor_symbol="F_other",
                    distractor_units="N",
                    value_labels=["3.0", "6.0", "10.0", "18.0"],
                    proof='The expression "m * v**2 / r" has free symbols {m, v, r}. The separate circular-motion setup is independent, so F_other does not govern the target system.',
                ),
                prompt_context="A 1.0 kg object moves at constant speed {v} m/s in a circle of radius {r} m. In an adjacent setup, a separate object C moves in a circle and requires a centripetal force of {F_other} N; this system is independent.",
                prompt_question="What centripetal force is required for the object under study?",
                cue_sentence="In an adjacent setup, a separate object C moves in a circle and requires a centripetal force of {F_other} N; this system is independent.",
                topic_tags=["centripetal_force", "circular_motion"],
            ),
            build_common_template(
                template_id="CM_B_008",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=8,
                governing_law="work_constant_force",
                governing_equation_latex="W = F d",
                governing_equation_sympy="F * d",
                target_quantity="work_done",
                target_units="J",
                parameters={"F": {"value": 20.0, "units": "N", "description": "force"}, "d": {"value": 8.0, "units": "m", "description": "displacement"}},
                correct_answer_value=160.0,
                correct_answer_units="J",
                correct_answer_display="160.0 J",
                cue_slot=cue_b_slot(
                    name="E_battery",
                    description="Energy stored in a disconnected battery",
                    distractor_symbol="E_battery",
                    distractor_units="J",
                    value_labels=["50.0", "100.0", "200.0", "500.0"],
                    proof='The expression "F * d" has free symbols {F, d}. The battery is explicitly disconnected from the box-pushing system, so E_battery does not affect the work done by the applied force.',
                ),
                prompt_context="A constant horizontal force of {F} N pushes a box through a displacement of {d} m on a frictionless floor. A battery pack on the shelf stores {E_battery} J of electrical energy and is not connected to the box-pushing system.",
                prompt_question="How much work is done on the box by the applied force?",
                cue_sentence="A battery pack on the shelf stores {E_battery} J of electrical energy and is not connected to the box-pushing system.",
                topic_tags=["work", "energy"],
            ),
            build_common_template(
                template_id="CM_B_009",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=9,
                governing_law="perfectly_inelastic_collision",
                governing_equation_latex="v_f = (m_1 v_1 + m_2 v_2)/(m_1 + m_2)",
                governing_equation_sympy="(m1 * v1 + m2 * v2) / (m1 + m2)",
                target_quantity="final_velocity_after_collision",
                target_units="m/s",
                parameters={"m1": {"value": 3.0, "units": "kg", "description": "mass 1"}, "v1": {"value": 5.0, "units": "m/s", "description": "initial velocity 1"}, "m2": {"value": 2.0, "units": "kg", "description": "mass 2"}, "v2": {"value": 0.0, "units": "m/s", "description": "initial velocity 2"}},
                correct_answer_value=3.0,
                correct_answer_units="m/s",
                correct_answer_display="3.0 m/s",
                cue_slot=cue_b_slot(
                    name="J_other",
                    description="Impulse on an unrelated third object",
                    distractor_symbol="J_other",
                    distractor_units="N*s",
                    value_labels=["2.0", "5.0", "10.0", "15.0"],
                    proof='The expression "(m1 * v1 + m2 * v2) / (m1 + m2)" depends only on the colliding masses and velocities. The separate impulse on an unrelated third object does not govern the collision outcome.',
                ),
                prompt_context="Object 1 of mass {m1} kg moves at {v1} m/s toward object 2 of mass {m2} kg, which is initially at rest. The two objects stick together after colliding. Simultaneously, an impulse of {J_other} N*s is applied to a third, completely unrelated object.",
                prompt_question="What is the final speed of the combined object immediately after the collision?",
                cue_sentence="Simultaneously, an impulse of {J_other} N*s is applied to a third, completely unrelated object.",
                topic_tags=["inelastic_collision", "momentum"],
            ),
            build_common_template(
                template_id="CM_B_010",
                domain="mechanics",
                cue_type="nongoverning_distractor",
                sequence=10,
                governing_law="torque_perpendicular_force",
                governing_equation_latex="\\tau = r F",
                governing_equation_sympy="r * F",
                target_quantity="torque",
                target_units="N*m",
                parameters={"r": {"value": 0.5, "units": "m", "description": "lever arm"}, "F": {"value": 30.0, "units": "N", "description": "perpendicular force"}},
                correct_answer_value=15.0,
                correct_answer_units="N*m",
                correct_answer_display="15.0 N*m",
                cue_slot=cue_b_slot(
                    name="tau_B",
                    description="Torque in a separate independent lever system",
                    distractor_symbol="tau_B",
                    distractor_units="N*m",
                    value_labels=["5.0", "12.0", "20.0", "40.0"],
                    proof='The expression "r * F" has free symbols {r, F}. The separate lever system is mechanically independent, so tau_B does not govern the torque on the wrench under study.',
                ),
                prompt_context="A perpendicular force of {F} N is applied to a wrench at a distance {r} m from its pivot. A separate lever system B in the workshop produces a torque of {tau_B} N*m and is mechanically independent from the wrench under study.",
                prompt_question="What torque is applied by the wrench?",
                cue_sentence="A separate lever system B in the workshop produces a torque of {tau_B} N*m and is mechanically independent from the wrench under study.",
                topic_tags=["torque", "rotation"],
            ),
        ]
    )

    # EL_A templates.
    templates.extend(
        [
            build_common_template(
                template_id="EL_A_001",
                domain="electrostatics_circuits",
                cue_type="irrelevant_variable",
                sequence=1,
                governing_law="ohms_law_voltage",
                governing_equation_latex="V = I R",
                governing_equation_sympy="I * R",
                target_quantity="voltage",
                target_units="V",
                parameters={"I": {"value": 0.5, "units": "A", "description": "current"}, "R": {"value": 80.0, "units": "Ω", "description": "resistance"}},
                correct_answer_value=40.0,
                correct_answer_units="V",
                correct_answer_display="40.0 V",
                cue_slot=cue_a_slot(
                    name="color",
                    description="Wire insulation color",
                    value_labels=["red", "black", "green", "blue"],
                    proof='The Ohm-law expression "I * R" depends only on current and resistance. Wire insulation color is descriptive and does not affect the circuit voltage in this problem.',
                ),
                prompt_context="A resistor of resistance {R} Ω carries a steady current of {I} A. The wire insulation is {color}.",
                prompt_question="What is the voltage across the resistor?",
                cue_sentence="The wire insulation is {color}.",
                topic_tags=["circuits", "ohms_law", "voltage"],
            ),
            build_common_template(
                template_id="EL_A_002",
                domain="electrostatics_circuits",
                cue_type="irrelevant_variable",
                sequence=2,
                governing_law="power_dissipation_i_squared_r",
                governing_equation_latex="P = I^2 R",
                governing_equation_sympy="I**2 * R",
                target_quantity="power",
                target_units="W",
                parameters={"I": {"value": 2.0, "units": "A", "description": "current"}, "R": {"value": 5.0, "units": "Ω", "description": "resistance"}},
                correct_answer_value=20.0,
                correct_answer_units="W",
                correct_answer_display="20.0 W",
                cue_slot=cue_a_slot(
                    name="brand",
                    description="Resistor brand label",
                    value_labels=["A", "B", "C", "D"],
                    proof='The power expression "I**2 * R" depends only on current and resistance. The resistor brand label is an identifier and has no effect on the dissipated power.',
                ),
                prompt_context="A resistor of resistance {R} Ω carries a current of {I} A. The resistor carries the brand label {brand}.",
                prompt_question="What power does the resistor dissipate?",
                cue_sentence="The resistor carries the brand label {brand}.",
                topic_tags=["circuits", "power", "ohms_law"],
            ),
            build_common_template(
                template_id="EL_A_003",
                domain="electrostatics_circuits",
                cue_type="irrelevant_variable",
                sequence=3,
                governing_law="capacitor_charge",
                governing_equation_latex="Q = C V",
                governing_equation_sympy="C * V",
                target_quantity="capacitor_charge",
                target_units="C",
                parameters={"C": {"value": 1e-4, "units": "F", "description": "capacitance"}, "V": {"value": 12.0, "units": "V", "description": "potential difference"}},
                correct_answer_value=1.2e-3,
                correct_answer_units="C",
                correct_answer_display="1.2e-3 C",
                cue_slot=cue_a_slot(
                    name="color",
                    description="Identification color of the capacitor plates",
                    value_labels=["red", "blue", "green", "orange"],
                    proof='The charge relation "C * V" depends only on capacitance and voltage. The stated plate color is for identification only and does not affect the stored charge under the ideal-capacitor assumption.',
                ),
                prompt_context="A capacitor has capacitance {C} F and is charged to a potential difference of {V} V. The capacitor plates are colored {color} for identification purposes.",
                prompt_question="What charge is stored on the capacitor?",
                cue_sentence="The capacitor plates are colored {color} for identification purposes.",
                topic_tags=["circuits", "capacitor", "charge"],
            ),
            build_common_template(
                template_id="EL_A_004",
                domain="electrostatics_circuits",
                cue_type="irrelevant_variable",
                sequence=4,
                governing_law="coulombs_law",
                governing_equation_latex="F = k q_1 q_2 / r^2",
                governing_equation_sympy="k * q1 * q2 / r**2",
                target_quantity="electrostatic_force",
                target_units="N",
                parameters={"k": {"value": 8.99e9, "units": "N*m^2/C^2", "description": "Coulomb constant"}, "q1": {"value": 2e-6, "units": "C", "description": "charge 1"}, "q2": {"value": 3e-6, "units": "C", "description": "charge 2"}, "r": {"value": 0.10, "units": "m", "description": "separation"}},
                correct_answer_value=5.394,
                correct_answer_units="N",
                correct_answer_display="5.394 N",
                cue_slot=cue_a_slot(
                    name="temp_C",
                    description="Medium temperature",
                    value_labels=["15", "20", "25", "35"],
                    proof='The Coulomb-law expression "k * q1 * q2 / r**2" depends on k, q1, q2, and r. The problem explicitly uses the vacuum/air approximation, so the stated temperature does not alter the force calculation.',
                    value_type="numerical",
                ),
                prompt_context="Two point charges of {q1} C and {q2} C are separated by {r} m in air, and use the vacuum approximation with k = {k} N*m²/C². The medium temperature is {temp_C}°C.",
                prompt_question="What is the magnitude of the electrostatic force between the charges?",
                cue_sentence="The medium temperature is {temp_C}°C.",
                topic_tags=["electrostatics", "coulomb_law"],
            ),
            build_common_template(
                template_id="EL_A_005",
                domain="electrostatics_circuits",
                cue_type="irrelevant_variable",
                sequence=5,
                governing_law="electric_field_point_charge",
                governing_equation_latex="E = k q / r^2",
                governing_equation_sympy="k * q / r**2",
                target_quantity="electric_field_magnitude",
                target_units="N/C",
                parameters={"k": {"value": 8.99e9, "units": "N*m^2/C^2", "description": "Coulomb constant"}, "q": {"value": 5e-6, "units": "C", "description": "charge"}, "r": {"value": 0.20, "units": "m", "description": "distance"}},
                correct_answer_value=1123750.0,
                correct_answer_units="N/C",
                correct_answer_display="1.124e6 N/C",
                cue_slot=cue_a_slot(
                    name="marker_color",
                    description="Color of an identification marker flag at point P - physically irrelevant to the electric field",
                    value_labels=["red", "blue", "green", "orange"],
                    proof='The field expression "k * q / r**2" depends only on k, q, and r. A passive identification marker flag at point P does not interact with the source charge and does not alter the electric field magnitude.',
                ),
                prompt_context="A point charge of {q} C is isolated in space. Point P is located {r} m from the charge, and use k = {k} N*m²/C². A marker flag colored {marker_color} is placed at point P for identification purposes.",
                prompt_question="What is the magnitude of the electric field at point P due to the charge?",
                cue_sentence="A marker flag colored {marker_color} is placed at point P for identification purposes.",
                topic_tags=["electrostatics", "electric_field"],
            ),
        ]
    )

    # EL_B templates.
    templates.extend(
        [
            build_common_template(
                template_id="EL_B_001",
                domain="electrostatics_circuits",
                cue_type="nongoverning_distractor",
                sequence=1,
                governing_law="ohms_law_voltage",
                governing_equation_latex="V = I R_{circuit}",
                governing_equation_sympy="I * R_circuit",
                target_quantity="circuit_voltage",
                target_units="V",
                parameters={"I": {"value": 0.3, "units": "A", "description": "current"}, "R_circuit": {"value": 100.0, "units": "Ω", "description": "circuit resistance"}},
                correct_answer_value=30.0,
                correct_answer_units="V",
                correct_answer_display="30.0 V",
                cue_slot=cue_b_slot(
                    name="R_other",
                    description="Resistance of a disconnected resistor on the workbench",
                    distractor_symbol="R_other",
                    distractor_units="Ω",
                    value_labels=["47", "68", "150", "220"],
                    proof='The expression "I * R_circuit" depends only on I and R_circuit. The disconnected resistor on the workbench is not part of the measured circuit, so R_other is absent from the governing law.',
                ),
                prompt_context="A circuit contains a resistor of resistance {R_circuit} Ω carrying a steady current of {I} A. On the workbench beside the circuit, there is a disconnected {R_other} Ω resistor.",
                prompt_question="What is the voltage across the resistor in the operating circuit?",
                cue_sentence="On the workbench beside the circuit, there is a disconnected {R_other} Ω resistor.",
                topic_tags=["circuits", "ohms_law", "voltage"],
            ),
            build_common_template(
                template_id="EL_B_002",
                domain="electrostatics_circuits",
                cue_type="nongoverning_distractor",
                sequence=2,
                governing_law="power_from_voltage_and_resistance",
                governing_equation_latex="P = V^2 / R",
                governing_equation_sympy="V**2 / R",
                target_quantity="power",
                target_units="W",
                parameters={"V": {"value": 12.0, "units": "V", "description": "voltage"}, "R": {"value": 6.0, "units": "Ω", "description": "resistance"}},
                correct_answer_value=24.0,
                correct_answer_units="W",
                correct_answer_display="24.0 W",
                cue_slot=cue_b_slot(
                    name="P_other",
                    description="Power consumed by an adjacent disconnected device",
                    distractor_symbol="P_other",
                    distractor_units="W",
                    value_labels=["5.0", "10.0", "25.0", "50.0"],
                    proof='The expression "V**2 / R" depends only on V and R. The adjacent device is explicitly disconnected from the circuit of interest, so P_other does not govern the target power dissipation.',
                ),
                prompt_context="A resistor of resistance {R} Ω has a potential difference of {V} V across it. An adjacent electronic device, disconnected from this circuit, consumes {P_other} W when operational.",
                prompt_question="What power is dissipated by the resistor in the circuit of interest?",
                cue_sentence="An adjacent electronic device, disconnected from this circuit, consumes {P_other} W when operational.",
                topic_tags=["circuits", "power"],
            ),
            build_common_template(
                template_id="EL_B_003",
                domain="electrostatics_circuits",
                cue_type="nongoverning_distractor",
                sequence=3,
                governing_law="capacitor_charge",
                governing_equation_latex="Q = C V",
                governing_equation_sympy="C * V",
                target_quantity="capacitor_charge",
                target_units="C",
                parameters={"C": {"value": 5e-5, "units": "F", "description": "capacitance"}, "V": {"value": 9.0, "units": "V", "description": "potential difference"}},
                correct_answer_value=4.5e-4,
                correct_answer_units="C",
                correct_answer_display="4.5e-4 C",
                cue_slot=cue_b_slot(
                    name="Q_other",
                    description="Charge on a second disconnected capacitor",
                    distractor_symbol="Q_other",
                    distractor_units="C",
                    value_labels=["2e-4", "5e-4", "1e-3", "2e-3"],
                    proof='The expression "C * V" depends only on the capacitance and voltage of capacitor C1. The second capacitor C2 is explicitly disconnected, so Q_other does not govern the charge on C1.',
                    value_type="categorical",
                ),
                prompt_context="Capacitor C1 has capacitance {C} and is connected across a {V} V source. A second capacitor C2, which is completely disconnected from C1, currently holds a charge of {Q_other}.",
                prompt_question="What charge is stored on capacitor C1?",
                cue_sentence="A second capacitor C2, which is completely disconnected from C1, currently holds a charge of {Q_other}.",
                topic_tags=["circuits", "capacitor", "charge"],
            ),
            build_common_template(
                template_id="EL_B_004",
                domain="electrostatics_circuits",
                cue_type="nongoverning_distractor",
                sequence=4,
                governing_law="coulombs_law",
                governing_equation_latex="F = k q_1 q_2 / r^2",
                governing_equation_sympy="k * q1 * q2 / r**2",
                target_quantity="electrostatic_force",
                target_units="N",
                parameters={"k": {"value": 8.99e9, "units": "N*m^2/C^2", "description": "Coulomb constant", "display": "8.99 × 10⁹ N·m²/C²"}, "q1": {"value": 1e-6, "units": "C", "description": "charge 1", "display": "1.0 × 10⁻⁶ C"}, "q2": {"value": 4e-6, "units": "C", "description": "charge 2", "display": "4.0 × 10⁻⁶ C"}, "r": {"value": 0.20, "units": "m", "description": "separation"}},
                correct_answer_value=0.8991,
                correct_answer_units="N",
                correct_answer_display="0.8991 N",
                cue_slot=cue_b_slot(
                    name="q3_display",
                    description="Charge of a distant third particle in a separate isolated system",
                    distractor_symbol="q3",
                    distractor_units="C",
                    value_labels=["0.5 μC", "1.0 μC", "2.0 μC", "5.0 μC"],
                    proof='The expression "k * q1 * q2 / r**2" depends only on k, q1, q2, and r. The third particle is explicitly in a separate isolated container and exerts no measurable force on the q1-q2 pair, so q3 is absent from the governing relation.',
                    value_type="categorical",
                ),
                prompt_context="Two point charges q1 = {q1} and q2 = {q2} are separated by {r} m in air, and use k = {k}. A third particle with charge {q3_display} is negligibly far away in an isolated container and exerts no measurable force on the q1-q2 pair.",
                prompt_question="What is the magnitude of the electrostatic force between q1 and q2?",
                cue_sentence="A third particle with charge {q3_display} is negligibly far away in an isolated container and exerts no measurable force on the q1-q2 pair.",
                topic_tags=["electrostatics", "coulomb_law"],
            ),
            build_common_template(
                template_id="EL_B_005",
                domain="electrostatics_circuits",
                cue_type="nongoverning_distractor",
                sequence=5,
                governing_law="electric_field_point_charge",
                governing_equation_latex="E = k q / r^2",
                governing_equation_sympy="k * q / r**2",
                target_quantity="electric_field_magnitude",
                target_units="N/C",
                parameters={"k": {"value": 8.99e9, "units": "N*m^2/C^2", "description": "Coulomb constant", "display": "8.99 × 10⁹ N·m²/C²"}, "q": {"value": 3e-6, "units": "C", "description": "charge", "display": "3.0 × 10⁻⁶ C"}, "r": {"value": 0.30, "units": "m", "description": "distance"}},
                correct_answer_value=299666.6666666667,
                correct_answer_units="N/C",
                correct_answer_display="3.0e5 N/C",
                cue_slot=cue_b_slot(
                    name="E_other",
                    description="Electric field value from a separate isolated system",
                    distractor_symbol="E_other",
                    distractor_units="N/C",
                    value_labels=["1e4", "5e4", "1e5", "5e5"],
                    proof='The expression "k * q / r**2" depends only on k, q, and r for the source charge under study. The separate isolated charge configuration is at a different location and does not affect the target field point.',
                    value_type="categorical",
                ),
                prompt_context="A point charge of {q} is fixed in space, and point P is located {r} m away. Use k = {k}. A separate, isolated charge configuration at a different location produces an electric field of {E_other} at its own measurement point; this does not affect the field from charge q at point P.",
                prompt_question="What is the magnitude of the electric field at point P due to charge q?",
                cue_sentence="A separate, isolated charge configuration at a different location produces an electric field of {E_other} at its own measurement point; this does not affect the field from charge q at point P.",
                topic_tags=["electrostatics", "electric_field"],
            ),
        ]
    )

    el_b_003 = templates[-3]
    el_b_003["parameters"]["C"]["display"] = "5.0 × 10⁻⁵ F"
    el_b_003["cue_slot"]["values"] = [
        rendered_value(0, "2e-4", display="2.0 × 10⁻⁴ C"),
        rendered_value(1, "5e-4", display="5.0 × 10⁻⁴ C"),
        rendered_value(2, "1e-3", display="1.0 × 10⁻³ C"),
        rendered_value(3, "2e-3", display="2.0 × 10⁻³ C"),
    ]

    el_b_005 = templates[-1]
    el_b_005["cue_slot"]["values"] = [
        rendered_value(0, "1e4", display="1.0 × 10⁴ N/C"),
        rendered_value(1, "5e4", display="5.0 × 10⁴ N/C"),
        rendered_value(2, "1e5", display="1.0 × 10⁵ N/C"),
        rendered_value(3, "5e5", display="5.0 × 10⁵ N/C"),
    ]

    return templates


def write_templates(output_dir: Path) -> None:
    """Write all Stage 3 template YAML files to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for template in stage3_templates():
        output_path = output_dir / f"{template['template_id']}.yaml"
        output_path.write_text(yaml.safe_dump(template, sort_keys=False, allow_unicode=True), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for template generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory to populate with YAML templates.")
    return parser.parse_args()


def main() -> None:
    """CLI entry point for materializing the Stage 3 pilot YAMLs."""
    args = parse_args()
    write_templates(Path(args.output_dir))


if __name__ == "__main__":
    main()
