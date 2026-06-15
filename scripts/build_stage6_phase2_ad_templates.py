#!/usr/bin/env python3
"""Build Stage 6 Phase 2 Part A and Part D templates.

Reference:
    Stage 6 Phase 2 construction brief v6.4.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import math

import yaml

from build_stage6_phase1_templates import (
    DEFAULT_OUTPUT_DIR,
    GRAVITY,
    build_common_template,
    cue_b_slot,
    verify_template,
    write_template,
)


DEFAULT_VERIFICATION_DIR = Path("results/stage6/verification_phase2_ad")
PI = math.pi
WATER_HEAT_CAPACITY = 4186.0
IDEAL_GAS_R = 8.314


def _display_number(value: float, digits: int = 3) -> str:
    """Format one scalar for prompt display."""

    if abs(value) >= 1000 or (0 < abs(value) < 1e-2):
        return f"{value:.3g}"
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def velocity_velocity_extension_templates() -> list[dict[str, Any]]:
    """Build CM_B_UM_041-048."""

    return [
        build_common_template(
            template_id="CM_B_UM_041",
            sequence=41,
            governing_law="momentum_transfer_velocity",
            governing_equation_latex="v_A = p_A / m_A",
            governing_equation_sympy="p_A / m_A",
            target_quantity="final_velocity_of_object_A",
            target_units="m/s",
            parameters={
                "p_A": {"value": 0.5, "units": "kg*m/s", "description": "momentum of object A"},
                "m_A": {"value": 0.05, "units": "kg", "description": "mass of object A"},
            },
            correct_answer_value=10.0,
            correct_answer_display="10.0 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Velocity of a separate object B, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["6.0", "9.0", "10.0", "14.0"],
                proof=(
                    'The governing expression "p_A / m_A" has free symbols {p_A, m_A}; '
                    "the distractor symbol v_B is absent from the governing equation. "
                    "Object B moves separately and never exchanges momentum with object A."
                ),
            ),
            prompt_context=(
                "Object A has momentum {p_A} kg·m/s and mass {m_A} kg after a transfer event. "
                "Elsewhere in the lab, object B moves at {v_B_display} m/s, but object B never "
                "interacts with object A."
            ),
            prompt_question="What is the final velocity of object A?",
            cue_sentence=(
                "Elsewhere in the lab, object B moves at {v_B_display} m/s, but object B never "
                "interacts with object A."
            ),
            topic_tags=["mechanics", "velocity", "momentum", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_042",
            sequence=42,
            governing_law="relative_velocity_difference",
            governing_equation_latex="v_{rel} = v_A - v_B",
            governing_equation_sympy="v_A - v_base",
            target_quantity="relative_velocity",
            target_units="m/s",
            parameters={
                "v_A": {"value": 25.0, "units": "m/s", "description": "velocity of object A"},
                "v_base": {"value": 10.0, "units": "m/s", "description": "velocity of base frame object"},
            },
            correct_answer_value=15.0,
            correct_answer_display="15.0 m/s",
            cue_slot=cue_b_slot(
                name="v_C_display",
                description="Velocity of unrelated object C, unit-matched with the target velocity",
                distractor_symbol="v_C",
                distractor_units="m/s",
                value_labels=["10.0", "13.0", "15.0", "20.0"],
                proof=(
                    'The governing expression "v_A - v_base" has free symbols {v_A, v_base}; '
                    "the distractor symbol v_C is absent from the governing equation. "
                    "Object C moves on a separate track and does not affect the relative velocity in the stated frame."
                ),
            ),
            prompt_context=(
                "Object A moves at {v_A} m/s while the reference cart defining the frame moves at {v_base} m/s. "
                "On a separate track, object C travels at {v_C_display} m/s, but object C never interacts with the frame-defining cart or object A."
            ),
            prompt_question="What is the relative velocity of object A in that frame?",
            cue_sentence=(
                "On a separate track, object C travels at {v_C_display} m/s, but object C never interacts with the frame-defining cart or object A."
            ),
            topic_tags=["mechanics", "velocity", "relative_motion", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_043",
            sequence=43,
            governing_law="escape_speed_simplified",
            governing_equation_latex="v = \\sqrt{2 G M / r}",
            governing_equation_sympy="sqrt(2 * G_planet * M_planet / r_surface)",
            target_quantity="escape_speed",
            target_units="m/s",
            parameters={
                "G_planet": {"value": 1.0, "units": "N*m^2/kg^2", "description": "toy-model gravitational constant"},
                "M_planet": {"value": 8.0, "units": "kg", "description": "toy-model planetary mass"},
                "r_surface": {"value": 1.0, "units": "m", "description": "toy-model planetary radius"},
            },
            correct_answer_value=4.0,
            correct_answer_display="4.0 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Velocity of a separate probe, unit-matched with the target velocity",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["2.0", "3.8", "4.0", "6.0"],
                proof=(
                    'The governing expression "sqrt(2 * G_planet * M_planet / r_surface)" has free symbols '
                    "{G_planet, M_planet, r_surface}; the distractor symbol v_B is absent from the governing equation. "
                    "The probe B is in a different simulation and never affects the escape-speed calculation."
                ),
            ),
            prompt_context=(
                "In a toy gravity model, a planet has gravitational constant {G_planet}, mass {M_planet} kg, "
                "and surface radius {r_surface} m. In a separate simulation, probe B is reported to move at {v_B_display} m/s, "
                "but that probe never interacts with the planet in this problem."
            ),
            prompt_question="What is the escape speed from the planet's surface?",
            cue_sentence=(
                "In a separate simulation, probe B is reported to move at {v_B_display} m/s, "
                "but that probe never interacts with the planet in this problem."
            ),
            topic_tags=["mechanics", "velocity", "escape_speed", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_044",
            sequence=44,
            governing_law="projectile_vertical_component",
            governing_equation_latex="v_y = v_0 \\sin\\theta",
            governing_equation_sympy="v_0 * sin(theta_deg * pi / 180)",
            target_quantity="initial_vertical_velocity_component",
            target_units="m/s",
            parameters={
                "v_0": {"value": 20.0, "units": "m/s", "description": "launch speed"},
                "theta_deg": {"value": 30.0, "units": "deg", "description": "launch angle"},
            },
            correct_answer_value=10.0,
            correct_answer_display="10.0 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of separate projectile B, unit-matched with the target velocity component",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["6.0", "9.0", "10.0", "14.0"],
                proof=(
                    'The governing expression "v_0 * sin(theta_deg * pi / 180)" has free symbols {v_0, theta_deg}; '
                    "the distractor symbol v_B is absent from the governing equation. Projectile B follows an unrelated launch path."
                ),
            ),
            prompt_context=(
                "Projectile A is launched at speed {v_0} m/s at an angle of {theta_deg} degrees above the horizontal. "
                "In another test range, projectile B travels at {v_B_display} m/s, but projectile B never interacts with projectile A."
            ),
            prompt_question="What is the initial vertical component of projectile A's velocity?",
            cue_sentence=(
                "In another test range, projectile B travels at {v_B_display} m/s, but projectile B never interacts with projectile A."
            ),
            topic_tags=["mechanics", "velocity", "projectile_motion", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_045",
            sequence=45,
            governing_law="elastic_collision_equal_mass",
            governing_equation_latex="v_f = \\frac{2 m_1}{m_1 + m_2} v_i",
            governing_equation_sympy="(2 * m_1 / (m_1 + m_2)) * v_i",
            target_quantity="post_collision_speed_of_cart_C",
            target_units="m/s",
            parameters={
                "m_1": {"value": 1.0, "units": "kg", "description": "incoming mass"},
                "m_2": {"value": 1.0, "units": "kg", "description": "target mass"},
                "v_i": {"value": 6.0, "units": "m/s", "description": "incoming speed"},
            },
            correct_answer_value=6.0,
            correct_answer_display="6.0 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of a separate cart B, unit-matched with the target speed",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["3.0", "5.0", "6.0", "8.0"],
                proof=(
                    'The governing expression "(2 * m_1 / (m_1 + m_2)) * v_i" has free symbols {m_1, m_2, v_i}; '
                    "the distractor symbol v_B is absent from the governing equation. Cart B is in a different collision lane."
                ),
            ),
            prompt_context=(
                "In a one-dimensional elastic collision, cart A of mass {m_1} kg strikes cart C of mass {m_2} kg while moving at {v_i} m/s. "
                "In a different lane, cart B is measured at {v_B_display} m/s, but cart B never interacts with carts A or C."
            ),
            prompt_question="What is cart C's post-collision speed after the collision?",
            cue_sentence=(
                "In a different lane, cart B is measured at {v_B_display} m/s, but cart B never interacts with carts A or C."
            ),
            topic_tags=["mechanics", "velocity", "collision", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_046",
            sequence=46,
            governing_law="rolling_without_slip",
            governing_equation_latex="v_{cm} = R \\omega",
            governing_equation_sympy="R_wheel * omega",
            target_quantity="rolling_center_of_mass_speed",
            target_units="m/s",
            parameters={
                "R_wheel": {"value": 0.5, "units": "m", "description": "wheel radius"},
                "omega": {"value": 12.0, "units": "rad/s", "description": "angular speed"},
            },
            correct_answer_value=6.0,
            correct_answer_display="6.0 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of a separate conveyor belt, unit-matched with the target speed",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["3.0", "5.0", "6.0", "9.0"],
                proof=(
                    'The governing expression "R_wheel * omega" has free symbols {R_wheel, omega}; '
                    "the distractor symbol v_B is absent from the governing equation. The conveyor belt is in a separate apparatus."
                ),
            ),
            prompt_context=(
                "Wheel A rolls without slipping with radius {R_wheel} m and angular speed {omega} rad/s. "
                "In another apparatus, a conveyor belt moves at {v_B_display} m/s, but it never contacts wheel A."
            ),
            prompt_question="What is the center-of-mass speed of wheel A?",
            cue_sentence=(
                "In another apparatus, a conveyor belt moves at {v_B_display} m/s, but it never contacts wheel A."
            ),
            topic_tags=["mechanics", "velocity", "rolling_motion", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_047",
            sequence=47,
            governing_law="ramp_energy_speed",
            governing_equation_latex="v = \\sqrt{2 g h}",
            governing_equation_sympy="sqrt(2 * g * h_drop)",
            target_quantity="speed_at_bottom_of_ramp",
            target_units="m/s",
            parameters={
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "h_drop": {"value": 5.0, "units": "m", "description": "vertical drop"},
            },
            correct_answer_value=math.sqrt(2 * GRAVITY * 5.0),
            correct_answer_display="9.899 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of a separate cart B, unit-matched with the target speed",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["7.0", "9.5", "9.9", "12.0"],
                proof=(
                    'The governing expression "sqrt(2 * g * h_drop)" has free symbols {g, h_drop}; '
                    "the distractor symbol v_B is absent from the governing equation. Cart B is on a different ramp."
                ),
            ),
            prompt_context=(
                "Cart A starts from rest and descends a frictionless ramp through a vertical drop of {h_drop} m. "
                "A different cart B elsewhere in the building is reported moving at {v_B_display} m/s, but it never interacts with cart A."
            ),
            prompt_question="What is cart A's speed at the bottom of the ramp?",
            cue_sentence=(
                "A different cart B elsewhere in the building is reported moving at {v_B_display} m/s, but it never interacts with cart A."
            ),
            topic_tags=["mechanics", "velocity", "energy", "unit_matched_cue_b", "near_match"],
            notes="One distractor rounds the irrational answer 9.899... m/s to 9.9 m/s.",
        ),
        build_common_template(
            template_id="CM_B_UM_048",
            sequence=48,
            governing_law="center_of_mass_velocity",
            governing_equation_latex="v_{cm} = \\frac{m_1 v_1 + m_2 v_2}{m_1 + m_2}",
            governing_equation_sympy="(m_1 * v_1 + m_2 * v_2) / (m_1 + m_2)",
            target_quantity="center_of_mass_velocity",
            target_units="m/s",
            parameters={
                "m_1": {"value": 2.0, "units": "kg", "description": "mass of object 1"},
                "v_1": {"value": 8.0, "units": "m/s", "description": "velocity of object 1"},
                "m_2": {"value": 3.0, "units": "kg", "description": "mass of object 2"},
                "v_2": {"value": 2.0, "units": "m/s", "description": "velocity of object 2"},
            },
            correct_answer_value=4.4,
            correct_answer_display="4.4 m/s",
            cue_slot=cue_b_slot(
                name="v_B_display",
                description="Speed of a separate lab cart, unit-matched with the target speed",
                distractor_symbol="v_B",
                distractor_units="m/s",
                value_labels=["2.0", "4.0", "4.4", "6.0"],
                proof=(
                    'The governing expression "(m_1 * v_1 + m_2 * v_2) / (m_1 + m_2)" has free symbols '
                    "{m_1, v_1, m_2, v_2}; the distractor symbol v_B is absent from the governing equation. "
                    "The lab cart is disconnected from the center-of-mass system."
                ),
            ),
            prompt_context=(
                "Object 1 has mass {m_1} kg and velocity {v_1} m/s, while object 2 has mass {m_2} kg and velocity {v_2} m/s. "
                "A separate lab cart is measured at {v_B_display} m/s, but it never interacts with the two-object system."
            ),
            prompt_question="What is the velocity of the two-object system's center of mass?",
            cue_sentence=(
                "A separate lab cart is measured at {v_B_display} m/s, but it never interacts with the two-object system."
            ),
            topic_tags=["mechanics", "velocity", "center_of_mass", "unit_matched_cue_b", "near_match"],
        ),
    ]


def frequency_frequency_extension_templates() -> list[dict[str, Any]]:
    """Build CM_B_UM_049-056."""

    return [
        build_common_template(
            template_id="CM_B_UM_049",
            sequence=49,
            governing_law="spring_mass_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{k_A / m_A}",
            governing_equation_sympy="sqrt(k_A / m_A) / (2 * pi)",
            target_quantity="spring_mass_frequency_A",
            target_units="Hz",
            parameters={
                "k_A": {"value": 400.0, "units": "N/m", "description": "spring constant"},
                "m_A": {"value": 4.0, "units": "kg", "description": "attached mass"},
            },
            correct_answer_value=math.sqrt(400.0 / 4.0) / (2 * PI),
            correct_answer_display="1.592 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate oscillator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.8", "1.6", "2.4", "3.2"],
                proof=(
                    'The governing expression "sqrt(k_A / m_A) / (2 * pi)" has free symbols {k_A, m_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Oscillator B is physically separate."
                ),
            ),
            prompt_context=(
                "Spring-mass system A has spring constant {k_A} N/m and mass {m_A} kg. "
                "In an adjacent bay, oscillator B runs at {f_B_display} Hz, but oscillator B never interacts with system A."
            ),
            prompt_question="What is the oscillation frequency of system A?",
            cue_sentence=(
                "In an adjacent bay, oscillator B runs at {f_B_display} Hz, but oscillator B never interacts with system A."
            ),
            topic_tags=["mechanics", "frequency", "oscillation", "unit_matched_cue_b", "near_match"],
            notes="Near-match distractor 1.6 Hz vs correct answer 1.592 Hz.",
        ),
        build_common_template(
            template_id="CM_B_UM_050",
            sequence=50,
            governing_law="spring_mass_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{k_A / m_A}",
            governing_equation_sympy="sqrt(k_A / m_A) / (2 * pi)",
            target_quantity="spring_mass_frequency_A",
            target_units="Hz",
            parameters={
                "k_A": {"value": 50.0, "units": "N/m", "description": "spring constant"},
                "m_A": {"value": 2.0, "units": "kg", "description": "attached mass"},
            },
            correct_answer_value=math.sqrt(50.0 / 2.0) / (2 * PI),
            correct_answer_display="0.796 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate oscillator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.4", "0.8", "1.2", "2.0"],
                proof=(
                    'The governing expression "sqrt(k_A / m_A) / (2 * pi)" has free symbols {k_A, m_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Oscillator B is physically separate."
                ),
            ),
            prompt_context=(
                "Spring-mass system A has spring constant {k_A} N/m and mass {m_A} kg. "
                "In another test rig, oscillator B runs at {f_B_display} Hz, but it never interacts with system A."
            ),
            prompt_question="What is the oscillation frequency of system A?",
            cue_sentence=(
                "In another test rig, oscillator B runs at {f_B_display} Hz, but it never interacts with system A."
            ),
            topic_tags=["mechanics", "frequency", "oscillation", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_051",
            sequence=51,
            governing_law="pendulum_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{g / L_A}",
            governing_equation_sympy="sqrt(g / L_A) / (2 * pi)",
            target_quantity="pendulum_frequency_A",
            target_units="Hz",
            parameters={
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "L_A": {"value": 0.5, "units": "m", "description": "pendulum length"},
            },
            correct_answer_value=math.sqrt(GRAVITY / 0.5) / (2 * PI),
            correct_answer_display="0.705 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate pendulum B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.35", "0.7", "1.05", "1.4"],
                proof=(
                    'The governing expression "sqrt(g / L_A) / (2 * pi)" has free symbols {g, L_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Pendulum B is separate."
                ),
            ),
            prompt_context=(
                "Pendulum A has length {L_A} m in a lab where g = {g} m/s². "
                "In the next room, pendulum B oscillates at {f_B_display} Hz, but pendulum B never interacts with pendulum A."
            ),
            prompt_question="What is the oscillation frequency of pendulum A?",
            cue_sentence=(
                "In the next room, pendulum B oscillates at {f_B_display} Hz, but pendulum B never interacts with pendulum A."
            ),
            topic_tags=["mechanics", "frequency", "pendulum", "unit_matched_cue_b", "near_match"],
            notes="Near-match distractor 0.7 Hz vs correct answer 0.705 Hz.",
        ),
        build_common_template(
            template_id="CM_B_UM_052",
            sequence=52,
            governing_law="pendulum_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{g / L_A}",
            governing_equation_sympy="sqrt(g / L_A) / (2 * pi)",
            target_quantity="pendulum_frequency_A",
            target_units="Hz",
            parameters={
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "L_A": {"value": 2.0, "units": "m", "description": "pendulum length"},
            },
            correct_answer_value=math.sqrt(GRAVITY / 2.0) / (2 * PI),
            correct_answer_display="0.352 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate pendulum B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.175", "0.35", "0.7", "1.05"],
                proof=(
                    'The governing expression "sqrt(g / L_A) / (2 * pi)" has free symbols {g, L_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Pendulum B is separate."
                ),
            ),
            prompt_context=(
                "Pendulum A has length {L_A} m in a lab where g = {g} m/s². "
                "In a neighboring station, pendulum B oscillates at {f_B_display} Hz, but pendulum B never interacts with pendulum A."
            ),
            prompt_question="What is the oscillation frequency of pendulum A?",
            cue_sentence=(
                "In a neighboring station, pendulum B oscillates at {f_B_display} Hz, but pendulum B never interacts with pendulum A."
            ),
            topic_tags=["mechanics", "frequency", "pendulum", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_053",
            sequence=53,
            governing_law="spring_mass_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{k_A / m_A}",
            governing_equation_sympy="sqrt(k_A / m_A) / (2 * pi)",
            target_quantity="spring_mass_frequency_A",
            target_units="Hz",
            parameters={
                "k_A": {"value": 25.0, "units": "N/m", "description": "spring constant"},
                "m_A": {"value": 0.25, "units": "kg", "description": "attached mass"},
            },
            correct_answer_value=math.sqrt(25.0 / 0.25) / (2 * PI),
            correct_answer_display="1.592 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate oscillator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.8", "1.6", "2.4", "3.2"],
                proof=(
                    'The governing expression "sqrt(k_A / m_A) / (2 * pi)" has free symbols {k_A, m_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Oscillator B is physically separate."
                ),
            ),
            prompt_context=(
                "Spring-mass system A has spring constant {k_A} N/m and mass {m_A} kg. "
                "In a different apparatus, oscillator B runs at {f_B_display} Hz, but oscillator B never interacts with system A."
            ),
            prompt_question="What is the oscillation frequency of system A?",
            cue_sentence=(
                "In a different apparatus, oscillator B runs at {f_B_display} Hz, but oscillator B never interacts with system A."
            ),
            topic_tags=["mechanics", "frequency", "oscillation", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_054",
            domain="electrostatics_circuits",
            sequence=54,
            governing_law="lc_resonance_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi\\sqrt{L_A C_A}}",
            governing_equation_sympy="1 / (2 * pi * sqrt(L_A * C_A))",
            target_quantity="lc_resonance_frequency_A",
            target_units="Hz",
            parameters={
                "L_A": {"value": 0.1, "units": "H", "description": "inductance"},
                "C_A": {"value": 10e-6, "units": "F", "description": "capacitance", "display": "1.0e-5 F"},
            },
            correct_answer_value=1 / (2 * PI * math.sqrt(0.1 * 10e-6)),
            correct_answer_display="159.155 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of a separate resonator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["80", "159", "240", "320"],
                proof=(
                    'The governing expression "1 / (2 * pi * sqrt(L_A * C_A))" has free symbols {L_A, C_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Resonator B is electrically isolated."
                ),
            ),
            prompt_context=(
                "LC circuit A has inductance {L_A} H and capacitance {C_A}. "
                "A separate resonator B elsewhere in the lab runs at {f_B_display} Hz, but it is electrically isolated from circuit A."
            ),
            prompt_question="What is the resonance frequency of LC circuit A?",
            cue_sentence=(
                "A separate resonator B elsewhere in the lab runs at {f_B_display} Hz, but it is electrically isolated from circuit A."
            ),
            topic_tags=["circuits", "frequency", "lc_resonance", "unit_matched_cue_b", "near_match"],
            notes="Uses a rounded near-match distractor of 159 Hz for the 159.155 Hz resonance.",
        ),
        build_common_template(
            template_id="CM_B_UM_055",
            sequence=55,
            governing_law="pendulum_frequency",
            governing_equation_latex="f_A = \\frac{1}{2\\pi}\\sqrt{g / L_A}",
            governing_equation_sympy="sqrt(g / L_A) / (2 * pi)",
            target_quantity="pendulum_frequency_A",
            target_units="Hz",
            parameters={
                "g": {"value": GRAVITY, "units": "m/s^2", "description": "gravitational acceleration"},
                "L_A": {"value": 4.0, "units": "m", "description": "pendulum length"},
            },
            correct_answer_value=math.sqrt(GRAVITY / 4.0) / (2 * PI),
            correct_answer_display="0.249 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate pendulum B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["0.125", "0.25", "0.5", "1.0"],
                proof=(
                    'The governing expression "sqrt(g / L_A) / (2 * pi)" has free symbols {g, L_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Pendulum B is separate."
                ),
            ),
            prompt_context=(
                "Pendulum A has length {L_A} m in a lab where g = {g} m/s². "
                "In another station, pendulum B oscillates at {f_B_display} Hz, but pendulum B never interacts with pendulum A."
            ),
            prompt_question="What is the oscillation frequency of pendulum A?",
            cue_sentence=(
                "In another station, pendulum B oscillates at {f_B_display} Hz, but pendulum B never interacts with pendulum A."
            ),
            topic_tags=["mechanics", "frequency", "pendulum", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="CM_B_UM_056",
            sequence=56,
            governing_law="string_fundamental_frequency",
            governing_equation_latex="f_A = v_A / (2 L_A)",
            governing_equation_sympy="v_A / (2 * L_A)",
            target_quantity="string_fundamental_frequency_A",
            target_units="Hz",
            parameters={
                "v_A": {"value": 120.0, "units": "m/s", "description": "wave speed on string A"},
                "L_A": {"value": 0.75, "units": "m", "description": "string length"},
            },
            correct_answer_value=80.0,
            correct_answer_display="80.0 Hz",
            cue_slot=cue_b_slot(
                name="f_B_display",
                description="Frequency of separate oscillator B, unit-matched with the target frequency",
                distractor_symbol="f_B",
                distractor_units="Hz",
                value_labels=["40", "75", "80", "120"],
                proof=(
                    'The governing expression "v_A / (2 * L_A)" has free symbols {v_A, L_A}; '
                    "the distractor symbol f_B is absent from the governing equation. Oscillator B is unrelated to string A."
                ),
            ),
            prompt_context=(
                "String A supports waves with speed {v_A} m/s and has length {L_A} m. "
                "A separate oscillator B in the same lab runs at {f_B_display} Hz, but it never drives string A."
            ),
            prompt_question="What is the fundamental frequency of string A?",
            cue_sentence=(
                "A separate oscillator B in the same lab runs at {f_B_display} Hz, but it never drives string A."
            ),
            topic_tags=["mechanics", "frequency", "waves", "unit_matched_cue_b", "near_match"],
        ),
    ]


def torque_torque_redesign_templates() -> list[dict[str, Any]]:
    """Build CM_B_UM_057-060."""

    specs = [
        ("CM_B_UM_057", 57, 0.6, 20.0, 12.0, ["6.0", "11.0", "12.0", "18.0"]),
        ("CM_B_UM_058", 58, 0.3, 50.0, 15.0, ["7.5", "14.0", "15.0", "22.0"]),
        ("CM_B_UM_059", 59, 0.4, 20.0, 0.8660254037844386 * 8.0, ["3.5", "6.9", "10.0", "14.0"]),
        ("CM_B_UM_060", 60, 1.0, 8.0, 8.0, ["4.0", "7.5", "8.0", "12.0"]),
    ]
    families: list[dict[str, Any]] = []
    for template_id, sequence, lever_arm, force, answer, cue_values in specs:
        angle_note = " at 60 degrees to the lever arm" if template_id == "CM_B_UM_059" else " perpendicular to the lever arm"
        equation = "r_A * F_A * sin(theta_deg * pi / 180)" if template_id == "CM_B_UM_059" else "r_A * F_A"
        parameters: dict[str, dict[str, Any]] = {
            "r_A": {"value": lever_arm, "units": "m", "description": "lever arm length"},
            "F_A": {"value": force, "units": "N", "description": "applied force"},
        }
        if template_id == "CM_B_UM_059":
            parameters["theta_deg"] = {"value": 60.0, "units": "deg", "description": "force angle"}
        families.append(
            build_common_template(
                template_id=template_id,
                sequence=sequence,
                governing_law="torque_magnitude",
                governing_equation_latex="\\tau_A = r_A F_A" if template_id != "CM_B_UM_059" else "\\tau_A = r_A F_A \\sin\\theta",
                governing_equation_sympy=equation,
                target_quantity="torque_on_system_A",
                target_units="N*m",
                parameters=parameters,
                correct_answer_value=answer,
                correct_answer_display=f"{_display_number(answer)} N*m",
                cue_slot=cue_b_slot(
                    name="tau_B_display",
                    description="Torque of separate system B, unit-matched with the target torque",
                    distractor_symbol="tau_B",
                    distractor_units="N*m",
                    value_labels=cue_values,
                    proof=(
                        f'The governing expression "{equation}" has free symbols '
                        f"{{{', '.join(parameters)}}}; the distractor symbol tau_B is absent from the governing equation. "
                        "System B is mechanically isolated from system A."
                    ),
                ),
                prompt_context=(
                    f"System A has a lever arm of {{r_A}} m with a force of {{F_A}} N applied{angle_note}. "
                    "In an adjacent workshop, a separate wrench system B produces a torque of {tau_B_display} N·m, "
                    "but it is mechanically isolated from system A."
                ),
                prompt_question="What torque acts on system A?",
                cue_sentence=(
                    "In an adjacent workshop, a separate wrench system B produces a torque of {tau_B_display} N·m, "
                    "but it is mechanically isolated from system A."
                ),
                topic_tags=["mechanics", "torque", "rotation", "unit_matched_cue_b", "near_match"],
            )
        )
    return families


def thermodynamics_unit_matched_templates() -> list[dict[str, Any]]:
    """Build TH_B_UM_001-010."""

    return [
        build_common_template(
            template_id="TH_B_UM_001",
            domain="thermodynamics",
            sequence=1,
            governing_law="heat_capacity",
            governing_equation_latex="Q_A = m_A c_A \\Delta T_A",
            governing_equation_sympy="m_A * c_A * delta_T_A",
            target_quantity="heat_added_to_system_A",
            target_units="J",
            parameters={
                "m_A": {"value": 2.0, "units": "kg", "description": "mass of water"},
                "c_A": {"value": WATER_HEAT_CAPACITY, "units": "J/(kg*K)", "description": "specific heat capacity"},
                "delta_T_A": {"value": 5.0, "units": "K", "description": "temperature increase"},
            },
            correct_answer_value=2.0 * WATER_HEAT_CAPACITY * 5.0,
            correct_answer_display="41860 J",
            cue_slot=cue_b_slot(
                name="Q_B_display",
                description="Heat absorbed by separate system B, unit-matched with the target heat",
                distractor_symbol="Q_B",
                distractor_units="J",
                value_labels=["20000", "40000", "41860", "60000"],
                proof=(
                    'The governing expression "m_A * c_A * delta_T_A" has free symbols {m_A, c_A, delta_T_A}; '
                    "the distractor symbol Q_B is absent from the governing equation. System B is thermally isolated."
                ),
            ),
            prompt_context=(
                "System A contains {m_A} kg of water with specific heat capacity {c_A} J/(kg·K) and warms by {delta_T_A} K. "
                "A separate insulated container B absorbs {Q_B_display} J, but container B is thermally isolated from system A."
            ),
            prompt_question="How much heat is added to system A?",
            cue_sentence=(
                "A separate insulated container B absorbs {Q_B_display} J, but container B is thermally isolated from system A."
            ),
            topic_tags=["thermodynamics", "heat", "specific_heat", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_002",
            domain="thermodynamics",
            sequence=2,
            governing_law="heat_capacity",
            governing_equation_latex="Q_A = m_A c_A \\Delta T_A",
            governing_equation_sympy="m_A * c_A * delta_T_A",
            target_quantity="heat_added_to_system_A",
            target_units="J",
            parameters={
                "m_A": {"value": 1.0, "units": "kg", "description": "mass of water"},
                "c_A": {"value": WATER_HEAT_CAPACITY, "units": "J/(kg*K)", "description": "specific heat capacity"},
                "delta_T_A": {"value": 10.0, "units": "K", "description": "temperature increase"},
            },
            correct_answer_value=WATER_HEAT_CAPACITY * 10.0,
            correct_answer_display="41860 J",
            cue_slot=cue_b_slot(
                name="Q_B_display",
                description="Heat absorbed by separate system B, unit-matched with the target heat",
                distractor_symbol="Q_B",
                distractor_units="J",
                value_labels=["22000", "41000", "42000", "65000"],
                proof=(
                    'The governing expression "m_A * c_A * delta_T_A" has free symbols {m_A, c_A, delta_T_A}; '
                    "the distractor symbol Q_B is absent from the governing equation. System B is thermally isolated."
                ),
            ),
            prompt_context=(
                "System A contains {m_A} kg of water with specific heat capacity {c_A} J/(kg·K) and warms by {delta_T_A} K. "
                "A different insulated calorimeter B absorbs {Q_B_display} J, but it is thermally isolated from system A."
            ),
            prompt_question="How much heat is added to system A?",
            cue_sentence=(
                "A different insulated calorimeter B absorbs {Q_B_display} J, but it is thermally isolated from system A."
            ),
            topic_tags=["thermodynamics", "heat", "specific_heat", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_003",
            domain="thermodynamics",
            sequence=3,
            governing_law="heat_capacity",
            governing_equation_latex="Q_A = m_A c_A \\Delta T_A",
            governing_equation_sympy="m_A * c_A * delta_T_A",
            target_quantity="heat_added_to_system_A",
            target_units="J",
            parameters={
                "m_A": {"value": 0.5, "units": "kg", "description": "mass of water"},
                "c_A": {"value": WATER_HEAT_CAPACITY, "units": "J/(kg*K)", "description": "specific heat capacity"},
                "delta_T_A": {"value": 20.0, "units": "K", "description": "temperature increase"},
            },
            correct_answer_value=0.5 * WATER_HEAT_CAPACITY * 20.0,
            correct_answer_display="41860 J",
            cue_slot=cue_b_slot(
                name="Q_B_display",
                description="Heat absorbed by separate system B, unit-matched with the target heat",
                distractor_symbol="Q_B",
                distractor_units="J",
                value_labels=["25000", "40000", "41860", "70000"],
                proof=(
                    'The governing expression "m_A * c_A * delta_T_A" has free symbols {m_A, c_A, delta_T_A}; '
                    "the distractor symbol Q_B is absent from the governing equation. System B is thermally isolated."
                ),
            ),
            prompt_context=(
                "System A contains {m_A} kg of water with specific heat capacity {c_A} J/(kg·K) and warms by {delta_T_A} K. "
                "Another insulated vessel B absorbs {Q_B_display} J, but it is thermally isolated from system A."
            ),
            prompt_question="How much heat is added to system A?",
            cue_sentence=(
                "Another insulated vessel B absorbs {Q_B_display} J, but it is thermally isolated from system A."
            ),
            topic_tags=["thermodynamics", "heat", "specific_heat", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_004",
            domain="thermodynamics",
            sequence=4,
            governing_law="work_force_displacement",
            governing_equation_latex="W_A = F_A \\Delta x_A",
            governing_equation_sympy="F_A * delta_x_A",
            target_quantity="work_done_on_system_A",
            target_units="J",
            parameters={
                "F_A": {"value": 600.0, "units": "N", "description": "applied force"},
                "delta_x_A": {"value": 70.0, "units": "m", "description": "displacement"},
            },
            correct_answer_value=42000.0,
            correct_answer_display="42000 J",
            cue_slot=cue_b_slot(
                name="Q_B_display",
                description="Heat absorbed by separate system B, unit-matched with the target work",
                distractor_symbol="Q_B",
                distractor_units="J",
                value_labels=["20000", "41000", "42000", "65000"],
                proof=(
                    'The governing expression "F_A * delta_x_A" has free symbols {F_A, delta_x_A}; '
                    "the distractor symbol Q_B is absent from the governing equation. System B is thermally isolated and not mechanically connected."
                ),
            ),
            prompt_context=(
                "A constant force of {F_A} N pushes system A through a displacement of {delta_x_A} m. "
                "Separately, calorimeter B absorbs {Q_B_display} J of heat, but B is thermally isolated and not mechanically connected to system A."
            ),
            prompt_question="How much work is done on system A?",
            cue_sentence=(
                "Separately, calorimeter B absorbs {Q_B_display} J of heat, but B is thermally isolated and not mechanically connected to system A."
            ),
            topic_tags=["thermodynamics", "work", "energy", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_005",
            domain="thermodynamics",
            sequence=5,
            governing_law="work_force_displacement",
            governing_equation_latex="W_A = F_A \\Delta x_A",
            governing_equation_sympy="F_A * delta_x_A",
            target_quantity="work_done_on_system_A",
            target_units="J",
            parameters={
                "F_A": {"value": 350.0, "units": "N", "description": "applied force"},
                "delta_x_A": {"value": 120.0, "units": "m", "description": "displacement"},
            },
            correct_answer_value=42000.0,
            correct_answer_display="42000 J",
            cue_slot=cue_b_slot(
                name="Q_B_display",
                description="Heat absorbed by separate system B, unit-matched with the target work",
                distractor_symbol="Q_B",
                distractor_units="J",
                value_labels=["18000", "40000", "42000", "52000"],
                proof=(
                    'The governing expression "F_A * delta_x_A" has free symbols {F_A, delta_x_A}; '
                    "the distractor symbol Q_B is absent from the governing equation. System B is thermally isolated and not mechanically connected."
                ),
            ),
            prompt_context=(
                "A constant force of {F_A} N pushes system A through a displacement of {delta_x_A} m. "
                "In a separate thermal experiment, system B absorbs {Q_B_display} J of heat, but B is isolated from system A."
            ),
            prompt_question="How much work is done on system A?",
            cue_sentence=(
                "In a separate thermal experiment, system B absorbs {Q_B_display} J of heat, but B is isolated from system A."
            ),
            topic_tags=["thermodynamics", "work", "energy", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_006",
            domain="thermodynamics",
            sequence=6,
            governing_law="ideal_gas_pressure",
            governing_equation_latex="P_A = \\frac{n_A R T_A}{V_A}",
            governing_equation_sympy="n_A * R_gas * T_A / V_A",
            target_quantity="pressure_of_gas_A",
            target_units="Pa",
            parameters={
                "n_A": {"value": 1.0, "units": "mol", "description": "amount of gas"},
                "R_gas": {"value": IDEAL_GAS_R, "units": "J/(mol*K)", "description": "ideal gas constant"},
                "T_A": {"value": 300.0, "units": "K", "description": "temperature"},
                "V_A": {"value": 0.02494, "units": "m^3", "description": "volume"},
            },
            correct_answer_value=(IDEAL_GAS_R * 300.0) / 0.02494,
            correct_answer_display="100000 Pa",
            cue_slot=cue_b_slot(
                name="P_B_display",
                description="Pressure of separate gas container B, unit-matched with the target pressure",
                distractor_symbol="P_B",
                distractor_units="Pa",
                value_labels=["50000", "98000", "100000", "150000"],
                proof=(
                    'The governing expression "n_A * R_gas * T_A / V_A" has free symbols {n_A, R_gas, T_A, V_A}; '
                    "the distractor symbol P_B is absent from the governing equation. Container B is unconnected."
                ),
            ),
            prompt_context=(
                "Gas container A holds {n_A} mol of ideal gas at temperature {T_A} K in volume {V_A} m^3. "
                "A separate sealed container B has pressure {P_B_display} Pa, but it is completely unconnected to container A."
            ),
            prompt_question="What is the pressure of gas in container A?",
            cue_sentence=(
                "A separate sealed container B has pressure {P_B_display} Pa, but it is completely unconnected to container A."
            ),
            topic_tags=["thermodynamics", "pressure", "ideal_gas", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_007",
            domain="thermodynamics",
            sequence=7,
            governing_law="ideal_gas_pressure",
            governing_equation_latex="P_A = \\frac{n_A R T_A}{V_A}",
            governing_equation_sympy="n_A * R_gas * T_A / V_A",
            target_quantity="pressure_of_gas_A",
            target_units="Pa",
            parameters={
                "n_A": {"value": 2.0, "units": "mol", "description": "amount of gas"},
                "R_gas": {"value": IDEAL_GAS_R, "units": "J/(mol*K)", "description": "ideal gas constant"},
                "T_A": {"value": 300.0, "units": "K", "description": "temperature"},
                "V_A": {"value": 0.049884, "units": "m^3", "description": "volume"},
            },
            correct_answer_value=(2.0 * IDEAL_GAS_R * 300.0) / 0.049884,
            correct_answer_display="100000 Pa",
            cue_slot=cue_b_slot(
                name="P_B_display",
                description="Pressure of separate gas container B, unit-matched with the target pressure",
                distractor_symbol="P_B",
                distractor_units="Pa",
                value_labels=["40000", "99000", "100000", "140000"],
                proof=(
                    'The governing expression "n_A * R_gas * T_A / V_A" has free symbols {n_A, R_gas, T_A, V_A}; '
                    "the distractor symbol P_B is absent from the governing equation. Container B is unconnected."
                ),
            ),
            prompt_context=(
                "Gas container A holds {n_A} mol of ideal gas at temperature {T_A} K in volume {V_A} m^3. "
                "A separate sealed container B has pressure {P_B_display} Pa, but it is completely unconnected to container A."
            ),
            prompt_question="What is the pressure of gas in container A?",
            cue_sentence=(
                "A separate sealed container B has pressure {P_B_display} Pa, but it is completely unconnected to container A."
            ),
            topic_tags=["thermodynamics", "pressure", "ideal_gas", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_008",
            domain="thermodynamics",
            sequence=8,
            governing_law="ideal_gas_pressure",
            governing_equation_latex="P_A = \\frac{n_A R T_A}{V_A}",
            governing_equation_sympy="n_A * R_gas * T_A / V_A",
            target_quantity="pressure_of_gas_A",
            target_units="Pa",
            parameters={
                "n_A": {"value": 0.5, "units": "mol", "description": "amount of gas"},
                "R_gas": {"value": IDEAL_GAS_R, "units": "J/(mol*K)", "description": "ideal gas constant"},
                "T_A": {"value": 500.0, "units": "K", "description": "temperature"},
                "V_A": {"value": 0.020785, "units": "m^3", "description": "volume"},
            },
            correct_answer_value=(0.5 * IDEAL_GAS_R * 500.0) / 0.020785,
            correct_answer_display="100000 Pa",
            cue_slot=cue_b_slot(
                name="P_B_display",
                description="Pressure of separate gas container B, unit-matched with the target pressure",
                distractor_symbol="P_B",
                distractor_units="Pa",
                value_labels=["45000", "97000", "100000", "130000"],
                proof=(
                    'The governing expression "n_A * R_gas * T_A / V_A" has free symbols {n_A, R_gas, T_A, V_A}; '
                    "the distractor symbol P_B is absent from the governing equation. Container B is unconnected."
                ),
            ),
            prompt_context=(
                "Gas container A holds {n_A} mol of ideal gas at temperature {T_A} K in volume {V_A} m^3. "
                "A separate sealed container B has pressure {P_B_display} Pa, but it is completely unconnected to container A."
            ),
            prompt_question="What is the pressure of gas in container A?",
            cue_sentence=(
                "A separate sealed container B has pressure {P_B_display} Pa, but it is completely unconnected to container A."
            ),
            topic_tags=["thermodynamics", "pressure", "ideal_gas", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_009",
            domain="thermodynamics",
            sequence=9,
            governing_law="thermal_expansion_length_change",
            governing_equation_latex="\\Delta L_A = \\alpha_A L_A \\Delta T_A",
            governing_equation_sympy="alpha_A * L_A * delta_T_A",
            target_quantity="thermal_expansion_of_rod_A",
            target_units="m",
            parameters={
                "alpha_A": {"value": 2.0e-5, "units": "1/K", "description": "expansion coefficient"},
                "L_A": {"value": 5.0, "units": "m", "description": "initial rod length"},
                "delta_T_A": {"value": 100.0, "units": "K", "description": "temperature increase"},
            },
            correct_answer_value=0.01,
            correct_answer_display="0.010 m",
            cue_slot=cue_b_slot(
                name="delta_L_B_display",
                description="Expansion of separate rod B, unit-matched with the target expansion",
                distractor_symbol="delta_L_B",
                distractor_units="m",
                value_labels=["0.004", "0.0098", "0.010", "0.015"],
                proof=(
                    'The governing expression "alpha_A * L_A * delta_T_A" has free symbols {alpha_A, L_A, delta_T_A}; '
                    "the distractor symbol delta_L_B is absent from the governing equation. Rod B is separate."
                ),
            ),
            prompt_context=(
                "Rod A has expansion coefficient {alpha_A}, initial length {L_A} m, and undergoes a temperature increase of {delta_T_A} K. "
                "A separate rod B expands by {delta_L_B_display} m, but rod B never interacts thermally or mechanically with rod A."
            ),
            prompt_question="What is the length change of rod A?",
            cue_sentence=(
                "A separate rod B expands by {delta_L_B_display} m, but rod B never interacts thermally or mechanically with rod A."
            ),
            topic_tags=["thermodynamics", "expansion", "thermal_expansion", "unit_matched_cue_b", "near_match"],
        ),
        build_common_template(
            template_id="TH_B_UM_010",
            domain="thermodynamics",
            sequence=10,
            governing_law="thermal_expansion_length_change",
            governing_equation_latex="\\Delta L_A = \\alpha_A L_A \\Delta T_A",
            governing_equation_sympy="alpha_A * L_A * delta_T_A",
            target_quantity="thermal_expansion_of_rod_A",
            target_units="m",
            parameters={
                "alpha_A": {"value": 1.5e-5, "units": "1/K", "description": "expansion coefficient"},
                "L_A": {"value": 4.0, "units": "m", "description": "initial rod length"},
                "delta_T_A": {"value": 200.0, "units": "K", "description": "temperature increase"},
            },
            correct_answer_value=0.012,
            correct_answer_display="0.012 m",
            cue_slot=cue_b_slot(
                name="delta_L_B_display",
                description="Expansion of separate rod B, unit-matched with the target expansion",
                distractor_symbol="delta_L_B",
                distractor_units="m",
                value_labels=["0.005", "0.0115", "0.012", "0.018"],
                proof=(
                    'The governing expression "alpha_A * L_A * delta_T_A" has free symbols {alpha_A, L_A, delta_T_A}; '
                    "the distractor symbol delta_L_B is absent from the governing equation. Rod B is separate."
                ),
            ),
            prompt_context=(
                "Rod A has expansion coefficient {alpha_A}, initial length {L_A} m, and undergoes a temperature increase of {delta_T_A} K. "
                "A separate rod B expands by {delta_L_B_display} m, but rod B never interacts thermally or mechanically with rod A."
            ),
            prompt_question="What is the length change of rod A?",
            cue_sentence=(
                "A separate rod B expands by {delta_L_B_display} m, but rod B never interacts thermally or mechanically with rod A."
            ),
            topic_tags=["thermodynamics", "expansion", "thermal_expansion", "unit_matched_cue_b", "near_match"],
        ),
    ]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Stage 6 Phase 2 Part A/D template construction."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--verification-dir", default=str(DEFAULT_VERIFICATION_DIR))
    parser.add_argument(
        "--class-filter",
        choices=(
            "velocity_velocity_extension",
            "frequency_frequency_extension",
            "torque_torque_redesign",
            "thermodynamics_unit_matched",
            "all",
        ),
        default="all",
        help="Which Phase 2 block to build in this run.",
    )
    return parser.parse_args()


def main() -> None:
    """Build the requested Stage 6 Phase 2 Part A/D templates and verify them."""

    args = parse_args()
    output_dir = Path(args.output_dir)
    verification_dir = Path(args.verification_dir)
    class_builders = {
        "velocity_velocity_extension": velocity_velocity_extension_templates,
        "frequency_frequency_extension": frequency_frequency_extension_templates,
        "torque_torque_redesign": torque_torque_redesign_templates,
        "thermodynamics_unit_matched": thermodynamics_unit_matched_templates,
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
        verification_payload = verify_template(template_path, verification_dir)
        stored_payload = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        stored_payload.setdefault("validation", {})
        stored_payload["validation"]["verifier_certified"] = bool(
            verification_payload["all_passed"]
        )
        template_path.write_text(
            yaml.safe_dump(stored_payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    print(f"Built and verified {len(templates)} Stage 6 Phase 2 Part A/D templates.")


if __name__ == "__main__":
    main()
