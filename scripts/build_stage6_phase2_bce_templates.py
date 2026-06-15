#!/usr/bin/env python3
"""Build Stage 6 Phase 2 Parts B, C, and E template YAML files.

Reference:
    PhysMon Stage 6 Phase 2 Construction Brief v6.4 and the 2026-06-15
    correction follow-up v6.5.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import argparse

import yaml

from physmon.benchmark.verifier import SymbolicVerifier
from physmon.utils.io import write_json


DEFAULT_OUTPUT_DIR = Path("data/raw/templates")
DEFAULT_VERIFICATION_DIR = Path("results/stage6/verification_phase2_bce")
CREATED_DATE = "2026-06-15"
CREATED_BY = "agent"
G_STANDARD = 9.8
K_COULOMB = 8.99e9
R_GAS = 8.314


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
            (
                f"assert abs(result - {exact_float_string(expected)}) < "
                f"{exact_float_string(tolerance)}, f\"Answer check failed: {{result}}\""
            ),
        ]
    )
    return "\n".join(assignment_lines)


def build_value_specs(
    values: list[str],
    *,
    renders: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Build the cue-slot value rows."""

    rows: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        row: dict[str, Any] = {"id": index, "value": value, "display": value}
        if renders is not None:
            row["render"] = renders[index]
        rows.append(row)
    return rows


def cue_a_slot(
    *,
    name: str,
    description: str,
    value_labels: list[str],
    proof: str,
    value_type: str = "numerical",
) -> dict[str, Any]:
    """Build a Cue A numeric-irrelevance slot."""

    return {
        "name": name,
        "description": description,
        "type": value_type,
        "irrelevance_proof": proof,
        "distractor_symbol": None,
        "distractor_units": None,
        "values": build_value_specs(value_labels),
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
    """Build a Cue B slot."""

    return {
        "name": name,
        "description": description,
        "type": value_type,
        "irrelevance_proof": None,
        "distractor_symbol": distractor_symbol,
        "distractor_units": distractor_units,
        "nongoverning_proof": proof,
        "values": build_value_specs(value_labels),
        "base_variant_id": 0,
    }


def cue_c_slot(
    *,
    name: str,
    description: str,
    display_labels: list[str],
    proof: str,
) -> dict[str, Any]:
    """Build a Cue C representation/rendering slot."""

    return {
        "name": name,
        "description": description,
        "type": "rendering",
        "irrelevance_proof": proof,
        "distractor_symbol": None,
        "distractor_units": None,
        "values": build_value_specs(display_labels, renders=display_labels),
        "base_variant_id": 0,
    }


def build_template(
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
    correct_answer_display: str,
    cue_slot: dict[str, Any],
    prompt_context: str,
    prompt_question: str,
    cue_sentence: str,
    topic_tags: list[str],
    verification_tolerance: float | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Assemble one Stage 6 template payload."""

    if verification_tolerance is None:
        verification_tolerance = 1e-6 * abs(correct_answer_value) if correct_answer_value != 0 else 1e-6

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
            "cue_span_is_whole_sentence": cue_type != "nongoverning_distractor",
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


def standard_cue_b_templates() -> list[dict[str, Any]]:
    """Return the 15 Phase 2 standard Cue B families."""

    templates: list[dict[str, Any]] = []
    specs = [
        {
            "template_id": "CM_B_STD_001",
            "domain": "mechanics",
            "governing_law": "rotational_dynamics_angular_acceleration",
            "equation_latex": r"\alpha = \tau_A / I_A",
            "equation_sympy": "tau_A / I_A",
            "target_quantity": "angular_acceleration_of_disk_A",
            "target_units": "rad/s^2",
            "parameters": {
                "tau_A": {"value": 12.0, "units": "N*m", "description": "net torque on disk A"},
                "I_A": {"value": 3.0, "units": "kg*m^2", "description": "moment of inertia of disk A"},
            },
            "answer": 4.0,
            "display": "4.0 rad/s^2",
            "cue_slot": cue_b_slot(
                name="F_B_display",
                description="Tangential force applied to a separate rotor B",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["2.0", "4.0", "6.0", "8.0"],
                proof=(
                    'The governing expression "tau_A / I_A" has free symbols {tau_A, I_A}; '
                    "the distractor force F_B belongs to a mechanically isolated rotor B."
                ),
            ),
            "context": (
                "Disk A experiences a net torque of {tau_A} N·m and has moment of inertia {I_A} kg·m². "
                "In another apparatus, a separate rotor B feels a tangential force of {F_B_display} N, "
                "but rotor B is mechanically isolated from disk A."
            ),
            "question": "What is the angular acceleration of disk A?",
            "cue_sentence": (
                "In another apparatus, a separate rotor B feels a tangential force of {F_B_display} N, "
                "but rotor B is mechanically isolated from disk A."
            ),
            "tags": ["mechanics", "rotational_dynamics", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_002",
            "domain": "mechanics",
            "governing_law": "rotational_dynamics_from_force",
            "equation_latex": r"\alpha = r_A F_A / I_A",
            "equation_sympy": "(r_A * F_A) / I_A",
            "target_quantity": "angular_acceleration_of_wheel_A",
            "target_units": "rad/s^2",
            "parameters": {
                "r_A": {"value": 0.5, "units": "m", "description": "radius where force is applied"},
                "F_A": {"value": 16.0, "units": "N", "description": "force on wheel A"},
                "I_A": {"value": 2.0, "units": "kg*m^2", "description": "moment of inertia of wheel A"},
            },
            "answer": 4.0,
            "display": "4.0 rad/s^2",
            "cue_slot": cue_b_slot(
                name="F_B_display",
                description="Tangential force applied to a separate rotor B",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["6.0", "15.0", "16.0", "24.0"],
                proof=(
                    'The governing expression "(r_A * F_A) / I_A" has free symbols {r_A, F_A, I_A}; '
                    "the distractor force F_B belongs to a disconnected rotor B and never enters wheel A's torque balance."
                ),
            ),
            "context": (
                "A force of {F_A} N is applied tangentially at radius {r_A} m on wheel A, whose moment of inertia is {I_A} kg·m². "
                "A separate rotor B feels a tangential force of {F_B_display} N, but rotor B is disconnected from wheel A."
            ),
            "question": "What is the angular acceleration of wheel A?",
            "cue_sentence": (
                "A separate rotor B feels a tangential force of {F_B_display} N, but rotor B is disconnected from wheel A."
            ),
            "tags": ["mechanics", "rotational_dynamics", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_003",
            "domain": "mechanics",
            "governing_law": "rotational_dynamics_braking",
            "equation_latex": r"\alpha = \tau_A / I_A",
            "equation_sympy": "tau_A / I_A",
            "target_quantity": "angular_deceleration_magnitude",
            "target_units": "rad/s^2",
            "parameters": {
                "tau_A": {"value": 9.0, "units": "N*m", "description": "braking torque magnitude"},
                "I_A": {"value": 1.5, "units": "kg*m^2", "description": "moment of inertia of flywheel A"},
            },
            "answer": 6.0,
            "display": "6.0 rad/s^2",
            "cue_slot": cue_b_slot(
                name="F_B_display",
                description="Force in a separate lever rig",
                distractor_symbol="F_B",
                distractor_units="N",
                value_labels=["2.0", "5.8", "6.0", "9.0"],
                proof=(
                    'The governing expression "tau_A / I_A" has free symbols {tau_A, I_A}; '
                    "the distractor force F_B acts only in the separate lever rig B."
                ),
            ),
            "context": (
                "Flywheel A experiences a braking torque of {tau_A} N·m and has moment of inertia {I_A} kg·m². "
                "Elsewhere, a separate lever system B carries a force of {F_B_display} N, but it never couples to flywheel A."
            ),
            "question": "What is the magnitude of flywheel A's angular deceleration?",
            "cue_sentence": (
                "Elsewhere, a separate lever system B carries a force of {F_B_display} N, but it never couples to flywheel A."
            ),
            "tags": ["mechanics", "rotational_dynamics", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_004",
            "domain": "mechanics",
            "governing_law": "fluid_static_pressure_depth",
            "equation_latex": r"P = \rho_A g h_A",
            "equation_sympy": "rho_A * g * h_A",
            "target_quantity": "hydrostatic_pressure_of_column_A",
            "target_units": "Pa",
            "parameters": {
                "rho_A": {"value": 1000.0, "units": "kg/m^3", "description": "density of fluid A"},
                "g": {"value": G_STANDARD, "units": "m/s^2", "description": "gravitational acceleration"},
                "h_A": {"value": 2.0, "units": "m", "description": "depth in fluid A"},
            },
            "answer": 19600.0,
            "display": "19600 Pa",
            "cue_slot": cue_b_slot(
                name="h_B_display",
                description="Depth of a separate tank B",
                distractor_symbol="h_B",
                distractor_units="m",
                value_labels=["1.0", "1.9", "2.0", "3.0"],
                proof=(
                    'The governing expression "rho_A * g * h_A" has free symbols {rho_A, g, h_A}; '
                    "h_B belongs to a different tank and does not affect column A."
                ),
            ),
            "context": (
                "Fluid A has density {rho_A} kg/m³ and the point of interest is {h_A} m below its surface. "
                "A separate tank B has a depth of {h_B_display} m, but tank B is not connected to fluid A."
            ),
            "question": "What is the hydrostatic pressure contribution from fluid A at the point of interest?",
            "cue_sentence": (
                "A separate tank B has a depth of {h_B_display} m, but tank B is not connected to fluid A."
            ),
            "tags": ["mechanics", "fluids", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_005",
            "domain": "mechanics",
            "governing_law": "fluid_static_pressure_density",
            "equation_latex": r"P = \rho_A g h_A",
            "equation_sympy": "rho_A * g * h_A",
            "target_quantity": "hydrostatic_pressure_of_oil_A",
            "target_units": "Pa",
            "parameters": {
                "rho_A": {"value": 800.0, "units": "kg/m^3", "description": "density of fluid A"},
                "g": {"value": G_STANDARD, "units": "m/s^2", "description": "gravitational acceleration"},
                "h_A": {"value": 5.0, "units": "m", "description": "depth in fluid A"},
            },
            "answer": 39200.0,
            "display": "39200 Pa",
            "cue_slot": cue_b_slot(
                name="rho_B_display",
                description="Density of a separate fluid sample B",
                distractor_symbol="rho_B",
                distractor_units="kg/m^3",
                value_labels=["600", "780", "800", "1000"],
                proof=(
                    'The governing expression "rho_A * g * h_A" has free symbols {rho_A, g, h_A}; '
                    "rho_B belongs to a separate sample and never enters the pressure calculation for fluid A."
                ),
            ),
            "context": (
                "Fluid A has density {rho_A} kg/m³ and the point of interest is {h_A} m below the surface. "
                "A separate calibration sample B has density {rho_B_display} kg/m³, but it is not part of fluid A's column."
            ),
            "question": "What is the hydrostatic pressure contribution from fluid A at the point of interest?",
            "cue_sentence": (
                "A separate calibration sample B has density {rho_B_display} kg/m³, but it is not part of fluid A's column."
            ),
            "tags": ["mechanics", "fluids", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_006",
            "domain": "mechanics",
            "governing_law": "fluid_static_pressure_short_column",
            "equation_latex": r"P = \rho_A g h_A",
            "equation_sympy": "rho_A * g * h_A",
            "target_quantity": "hydrostatic_pressure_of_mercury_A",
            "target_units": "Pa",
            "parameters": {
                "rho_A": {"value": 13600.0, "units": "kg/m^3", "description": "density of mercury"},
                "g": {"value": G_STANDARD, "units": "m/s^2", "description": "gravitational acceleration"},
                "h_A": {"value": 0.1, "units": "m", "description": "depth in mercury"},
            },
            "answer": 13328.0,
            "display": "13328 Pa",
            "cue_slot": cue_b_slot(
                name="h_B_display",
                description="Height of an unrelated fluid column B",
                distractor_symbol="h_B",
                distractor_units="m",
                value_labels=["0.05", "0.09", "0.10", "0.15"],
                proof=(
                    'The governing expression "rho_A * g * h_A" has free symbols {rho_A, g, h_A}; '
                    "h_B refers to a different column and is absent from the governing law."
                ),
            ),
            "context": (
                "Mercury column A has density {rho_A} kg/m³ and the point of interest is {h_A} m below the surface. "
                "A separate column B has height {h_B_display} m, but it is disconnected from column A."
            ),
            "question": "What is the hydrostatic pressure contribution from mercury column A at that depth?",
            "cue_sentence": "A separate column B has height {h_B_display} m, but it is disconnected from column A.",
            "tags": ["mechanics", "fluids", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_007",
            "domain": "thermodynamics",
            "governing_law": "heat_energy_capacity",
            "equation_latex": r"Q = m_A c_A \Delta T_A",
            "equation_sympy": "m_A * c_A * delta_T_A",
            "target_quantity": "heat_added_to_water_A",
            "target_units": "J",
            "parameters": {
                "m_A": {"value": 2.0, "units": "kg", "description": "mass of water A"},
                "c_A": {"value": 4200.0, "units": "J/(kg*K)", "description": "specific heat of water"},
                "delta_T_A": {"value": 5.0, "units": "K", "description": "temperature rise of water A"},
            },
            "answer": 42000.0,
            "display": "42000 J",
            "cue_slot": cue_b_slot(
                name="delta_T_B_display",
                description="Temperature rise of a separate sample B",
                distractor_symbol="delta_T_B",
                distractor_units="K",
                value_labels=["2.0", "4.8", "5.0", "8.0"],
                proof=(
                    'The governing expression "m_A * c_A * delta_T_A" has free symbols {m_A, c_A, delta_T_A}; '
                    "delta_T_B describes a separate sample B and is absent from the governing law."
                ),
            ),
            "context": (
                "Water sample A has mass {m_A} kg, specific heat capacity {c_A} J/(kg·K), and temperature increase {delta_T_A} K. "
                "A separate sample B warms by {delta_T_B_display} K, but sample B never exchanges heat with sample A."
            ),
            "question": "How much heat is added to sample A?",
            "cue_sentence": (
                "A separate sample B warms by {delta_T_B_display} K, but sample B never exchanges heat with sample A."
            ),
            "tags": ["thermodynamics", "heat_capacity", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_008",
            "domain": "thermodynamics",
            "governing_law": "heat_energy_aluminum_block",
            "equation_latex": r"Q = m_A c_A \Delta T_A",
            "equation_sympy": "m_A * c_A * delta_T_A",
            "target_quantity": "heat_added_to_block_A",
            "target_units": "J",
            "parameters": {
                "m_A": {"value": 1.5, "units": "kg", "description": "mass of block A"},
                "c_A": {"value": 900.0, "units": "J/(kg*K)", "description": "specific heat of block A"},
                "delta_T_A": {"value": 20.0, "units": "K", "description": "temperature rise of block A"},
            },
            "answer": 27000.0,
            "display": "27000 J",
            "cue_slot": cue_b_slot(
                name="m_B_display",
                description="Mass of an isolated block B",
                distractor_symbol="m_B",
                distractor_units="kg",
                value_labels=["0.5", "1.4", "1.5", "2.5"],
                proof=(
                    'The governing expression "m_A * c_A * delta_T_A" has free symbols {m_A, c_A, delta_T_A}; '
                    "m_B belongs to a separate block B and is absent from the heat law for block A."
                ),
            ),
            "context": (
                "Block A has mass {m_A} kg, specific heat capacity {c_A} J/(kg·K), and temperature increase {delta_T_A} K. "
                "A separate block B has mass {m_B_display} kg, but block B never exchanges heat with block A."
            ),
            "question": "How much heat is added to block A?",
            "cue_sentence": (
                "A separate block B has mass {m_B_display} kg, but block B never exchanges heat with block A."
            ),
            "tags": ["thermodynamics", "heat_capacity", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_009",
            "domain": "thermodynamics",
            "governing_law": "heat_energy_generic_capacity",
            "equation_latex": r"Q = m_A c_A \Delta T_A",
            "equation_sympy": "m_A * c_A * delta_T_A",
            "target_quantity": "heat_added_to_system_A",
            "target_units": "J",
            "parameters": {
                "m_A": {"value": 4.0, "units": "kg", "description": "mass of system A"},
                "c_A": {"value": 1000.0, "units": "J/(kg*K)", "description": "specific heat of system A"},
                "delta_T_A": {"value": 15.0, "units": "K", "description": "temperature rise of system A"},
            },
            "answer": 60000.0,
            "display": "60000 J",
            "cue_slot": cue_b_slot(
                name="c_B_display",
                description="Specific heat capacity of separate material B",
                distractor_symbol="c_B",
                distractor_units="J/(kg*K)",
                value_labels=["500", "900", "1000", "1500"],
                proof=(
                    'The governing expression "m_A * c_A * delta_T_A" has free symbols {m_A, c_A, delta_T_A}; '
                    "c_B belongs to a separate material sample B and never enters system A's heat calculation."
                ),
            ),
            "context": (
                "System A has mass {m_A} kg, specific heat capacity {c_A} J/(kg·K), and temperature increase {delta_T_A} K. "
                "A separate material B has specific heat capacity {c_B_display} J/(kg·K), but it is not part of system A."
            ),
            "question": "How much heat is added to system A?",
            "cue_sentence": (
                "A separate material B has specific heat capacity {c_B_display} J/(kg·K), but it is not part of system A."
            ),
            "tags": ["thermodynamics", "heat_capacity", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_010",
            "domain": "electrostatics_circuits",
            "governing_law": "electric_field_point_charge",
            "equation_latex": r"E = k q_A / r_A^2",
            "equation_sympy": "k_const * q_A / r_A**2",
            "target_quantity": "electric_field_due_to_charge_A",
            "target_units": "N/C",
            "parameters": {
                "k_const": {"value": K_COULOMB, "units": "N*m^2/C^2", "description": "Coulomb constant"},
                "q_A": {"value": 4e-6, "units": "C", "description": "charge A"},
                "r_A": {"value": 0.3, "units": "m", "description": "distance from charge A"},
            },
            "answer": K_COULOMB * 4e-6 / (0.3**2),
            "display": "399555.6 N/C",
            "cue_slot": cue_b_slot(
                name="q_B_display",
                description="Charge on separate source B",
                distractor_symbol="q_B",
                distractor_units="C",
                value_labels=["1.0e-6", "3.8e-6", "4.0e-6", "6.0e-6"],
                proof=(
                    'The governing expression "k_const * q_A / r_A**2" has free symbols {k_const, q_A, r_A}; '
                    "q_B is a charge in a separate isolated setup."
                ),
            ),
            "context": (
                "Charge A has magnitude {q_A} C and the field point is {r_A} m away. Use k = {k_const} N·m²/C². "
                "A separate source B carries charge {q_B_display} C, but source B never interacts with charge A or the field point."
            ),
            "question": "What is the electric field magnitude due to charge A at the field point?",
            "cue_sentence": (
                "A separate source B carries charge {q_B_display} C, but source B never interacts with charge A or the field point."
            ),
            "tags": ["electrostatics", "electric_field", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_011",
            "domain": "electrostatics_circuits",
            "governing_law": "electric_field_distance_distractor",
            "equation_latex": r"E = k q_A / r_A^2",
            "equation_sympy": "k_const * q_A / r_A**2",
            "target_quantity": "electric_field_due_to_charge_A",
            "target_units": "N/C",
            "parameters": {
                "k_const": {"value": K_COULOMB, "units": "N*m^2/C^2", "description": "Coulomb constant"},
                "q_A": {"value": 2e-6, "units": "C", "description": "charge A"},
                "r_A": {"value": 0.2, "units": "m", "description": "distance from charge A"},
            },
            "answer": K_COULOMB * 2e-6 / (0.2**2),
            "display": "449500 N/C",
            "cue_slot": cue_b_slot(
                name="r_B_display",
                description="Distance in a separate field-measurement setup B",
                distractor_symbol="r_B",
                distractor_units="m",
                value_labels=["0.10", "0.19", "0.20", "0.30"],
                proof=(
                    'The governing expression "k_const * q_A / r_A**2" has free symbols {k_const, q_A, r_A}; '
                    "r_B belongs to a separate setup and is absent from charge A's field law."
                ),
            ),
            "context": (
                "Charge A has magnitude {q_A} C and the field point is {r_A} m away. Use k = {k_const} N·m²/C². "
                "In a separate setup B, another field point is {r_B_display} m from its own charge, but setup B is isolated."
            ),
            "question": "What is the electric field magnitude due to charge A at the field point?",
            "cue_sentence": (
                "In a separate setup B, another field point is {r_B_display} m from its own charge, but setup B is isolated."
            ),
            "tags": ["electrostatics", "electric_field", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_012",
            "domain": "electrostatics_circuits",
            "governing_law": "electric_field_second_charge_scale",
            "equation_latex": r"E = k q_A / r_A^2",
            "equation_sympy": "k_const * q_A / r_A**2",
            "target_quantity": "electric_field_due_to_charge_A",
            "target_units": "N/C",
            "parameters": {
                "k_const": {"value": K_COULOMB, "units": "N*m^2/C^2", "description": "Coulomb constant"},
                "q_A": {"value": 6e-6, "units": "C", "description": "charge A"},
                "r_A": {"value": 0.6, "units": "m", "description": "distance from charge A"},
            },
            "answer": K_COULOMB * 6e-6 / (0.6**2),
            "display": "149833.3 N/C",
            "cue_slot": cue_b_slot(
                name="q_B_display",
                description="Charge in a separate calibration setup B",
                distractor_symbol="q_B",
                distractor_units="C",
                value_labels=["2.0e-6", "5.8e-6", "6.0e-6", "9.0e-6"],
                proof=(
                    'The governing expression "k_const * q_A / r_A**2" has free symbols {k_const, q_A, r_A}; '
                    "q_B belongs to a separate calibration setup and is absent from the field law."
                ),
            ),
            "context": (
                "Charge A has magnitude {q_A} C and the field point is {r_A} m away. Use k = {k_const} N·m²/C². "
                "A separate calibration source B carries charge {q_B_display} C, but it is isolated from charge A."
            ),
            "question": "What is the electric field magnitude due to charge A at the field point?",
            "cue_sentence": (
                "A separate calibration source B carries charge {q_B_display} C, but it is isolated from charge A."
            ),
            "tags": ["electrostatics", "electric_field", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_013",
            "domain": "mechanics",
            "governing_law": "gravitational_force_satellite",
            "equation_latex": r"F = G M_A m_A / r_A^2",
            "equation_sympy": "G_const * M_A * m_A / r_A**2",
            "target_quantity": "gravitational_force_on_satellite_A",
            "target_units": "N",
            "parameters": {
                "G_const": {"value": 6.67e-11, "units": "N*m^2/kg^2", "description": "gravitational constant"},
                "M_A": {"value": 6.0e24, "units": "kg", "description": "planet mass"},
                "m_A": {"value": 10.0, "units": "kg", "description": "satellite mass"},
                "r_A": {"value": 2.0e7, "units": "m", "description": "orbital radius"},
            },
            "answer": 6.67e-11 * 6.0e24 * 10.0 / (2.0e7**2),
            "display": "10.005 N",
            "cue_slot": cue_b_slot(
                name="m_B_display",
                description="Mass of a separate moon B",
                distractor_symbol="m_B",
                distractor_units="kg",
                value_labels=["4.0", "9.8", "10.0", "15.0"],
                proof=(
                    'The governing expression "G_const * M_A * m_A / r_A**2" has free symbols {G_const, M_A, m_A, r_A}; '
                    "m_B is the mass of a separate moon B in another orbit and never enters satellite A's force law."
                ),
            ),
            "context": (
                "Satellite A of mass {m_A} kg orbits a planet of mass {M_A} kg at radius {r_A} m. Use G = {G_const} N·m²/kg². "
                "A separate moon B has mass {m_B_display} kg, but moon B never interacts with satellite A."
            ),
            "question": "What gravitational force magnitude acts on satellite A?",
            "cue_sentence": (
                "A separate moon B has mass {m_B_display} kg, but moon B never interacts with satellite A."
            ),
            "tags": ["mechanics", "gravitation", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_014",
            "domain": "mechanics",
            "governing_law": "gravitational_force_distance_distractor",
            "equation_latex": r"F = G M_A m_A / r_A^2",
            "equation_sympy": "G_const * M_A * m_A / r_A**2",
            "target_quantity": "gravitational_force_on_probe_A",
            "target_units": "N",
            "parameters": {
                "G_const": {"value": 6.67e-11, "units": "N*m^2/kg^2", "description": "gravitational constant"},
                "M_A": {"value": 5.0e11, "units": "kg", "description": "central mass"},
                "m_A": {"value": 4.0, "units": "kg", "description": "probe mass"},
                "r_A": {"value": 10.0, "units": "m", "description": "distance from central mass"},
            },
            "answer": 6.67e-11 * 5.0e11 * 4.0 / (10.0**2),
            "display": "1.334 N",
            "cue_slot": cue_b_slot(
                name="r_B_display",
                description="Distance in a separate gravitational setup B",
                distractor_symbol="r_B",
                distractor_units="m",
                value_labels=["5.0", "9.5", "10.0", "14.0"],
                proof=(
                    'The governing expression "G_const * M_A * m_A / r_A**2" has free symbols {G_const, M_A, m_A, r_A}; '
                    "r_B belongs to a different gravitational setup and is absent from probe A's force law."
                ),
            ),
            "context": (
                "Probe A of mass {m_A} kg is {r_A} m from a central mass of {M_A} kg. Use G = {G_const} N·m²/kg². "
                "In a separate experiment, another probe sits {r_B_display} m from its own source, but that setup is isolated."
            ),
            "question": "What gravitational force magnitude acts on probe A?",
            "cue_sentence": (
                "In a separate experiment, another probe sits {r_B_display} m from its own source, but that setup is isolated."
            ),
            "tags": ["mechanics", "gravitation", "cue_b_standard", "near_match"],
        },
        {
            "template_id": "CM_B_STD_015",
            "domain": "mechanics",
            "governing_law": "gravitational_force_mass_distractor",
            "equation_latex": r"F = G M_A m_A / r_A^2",
            "equation_sympy": "G_const * M_A * m_A / r_A**2",
            "target_quantity": "gravitational_force_on_object_A",
            "target_units": "N",
            "parameters": {
                "G_const": {"value": 6.67e-11, "units": "N*m^2/kg^2", "description": "gravitational constant"},
                "M_A": {"value": 8.0e12, "units": "kg", "description": "central mass"},
                "m_A": {"value": 3.0, "units": "kg", "description": "object A mass"},
                "r_A": {"value": 20.0, "units": "m", "description": "distance from central mass"},
            },
            "answer": 6.67e-11 * 8.0e12 * 3.0 / (20.0**2),
            "display": "4.002 N",
            "cue_slot": cue_b_slot(
                name="M_B_display",
                description="Mass of a separate source B",
                distractor_symbol="M_B",
                distractor_units="kg",
                value_labels=["2.0e12", "7.5e12", "8.0e12", "1.2e13"],
                proof=(
                    'The governing expression "G_const * M_A * m_A / r_A**2" has free symbols {G_const, M_A, m_A, r_A}; '
                    "M_B belongs to a separate source B and is absent from object A's force law."
                ),
            ),
            "context": (
                "Object A of mass {m_A} kg is {r_A} m from a source of mass {M_A} kg. Use G = {G_const} N·m²/kg². "
                "A separate source B has mass {M_B_display} kg, but it never interacts with object A."
            ),
            "question": "What gravitational force magnitude acts on object A?",
            "cue_sentence": "A separate source B has mass {M_B_display} kg, but it never interacts with object A.",
            "tags": ["mechanics", "gravitation", "cue_b_standard", "near_match"],
        },
    ]

    for index, spec in enumerate(specs, start=1):
        templates.append(
            build_template(
                template_id=spec["template_id"],
                domain=spec["domain"],
                cue_type="nongoverning_distractor",
                sequence=index,
                governing_law=spec["governing_law"],
                governing_equation_latex=spec["equation_latex"],
                governing_equation_sympy=spec["equation_sympy"],
                target_quantity=spec["target_quantity"],
                target_units=spec["target_units"],
                parameters=spec["parameters"],
                correct_answer_value=spec["answer"],
                correct_answer_display=spec["display"],
                cue_slot=spec["cue_slot"],
                prompt_context=spec["context"],
                prompt_question=spec["question"],
                cue_sentence=spec["cue_sentence"],
                topic_tags=spec["tags"],
                verification_tolerance=1e-3 if spec["target_units"] in {"N/C", "Pa"} else None,
            )
        )
    return templates


def standard_cue_a_templates() -> list[dict[str, Any]]:
    """Return the 20 Phase 2 standard Cue A families."""

    templates: list[dict[str, Any]] = []
    specs = [
        {
            "template_id": "CM_A_STD_001",
            "domain": "mechanics",
            "governing_law": "kinematics_final_velocity",
            "equation_latex": r"v = v_0 + a t",
            "equation_sympy": "v_0 + a * t",
            "target_quantity": "final_velocity_of_cart_A",
            "target_units": "m/s",
            "parameters": {
                "v_0": {"value": 4.0, "units": "m/s", "description": "initial velocity"},
                "a": {"value": 2.0, "units": "m/s^2", "description": "acceleration"},
                "t": {"value": 4.0, "units": "s", "description": "elapsed time"},
            },
            "answer": 12.0,
            "display": "12.0 m/s",
            "cue_name": "ambient_temp_c",
            "cue_desc": "Ambient laboratory temperature - irrelevant to the kinematics target",
            "cue_values": ["18", "24", "36", "60"],
            "cue_proof": 'The governing expression "v_0 + a * t" depends only on v_0, a, and t; ambient temperature is absent.',
            "context": (
                "Cart A starts at {v_0} m/s and accelerates at {a} m/s² for {t} s on a frictionless track. "
                "The ambient laboratory temperature is {ambient_temp_c} °C."
            ),
            "question": "What is the final velocity of cart A?",
            "cue_sentence": "The ambient laboratory temperature is {ambient_temp_c} °C.",
            "tags": ["mechanics", "kinematics", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_002",
            "domain": "mechanics",
            "governing_law": "kinematics_displacement",
            "equation_latex": r"x = v_0 t + \frac{1}{2} a t^2",
            "equation_sympy": "v_0 * t + 0.5 * a * t**2",
            "target_quantity": "displacement_of_cart_A",
            "target_units": "m",
            "parameters": {
                "v_0": {"value": 3.0, "units": "m/s", "description": "initial velocity"},
                "a": {"value": 2.0, "units": "m/s^2", "description": "acceleration"},
                "t": {"value": 3.0, "units": "s", "description": "elapsed time"},
            },
            "answer": 18.0,
            "display": "18.0 m",
            "cue_name": "total_trip_minutes",
            "cue_desc": "Total time spent later transporting the apparatus - irrelevant to the target displacement",
            "cue_values": ["5", "10", "20", "50"],
            "cue_proof": 'The governing expression "v_0 * t + 0.5 * a * t**2" depends only on v_0, a, and t.',
            "context": (
                "Cart A begins at {v_0} m/s and accelerates at {a} m/s² for {t} s. "
                "Later that day, the apparatus is transported for {total_trip_minutes} minutes."
            ),
            "question": "What displacement does cart A cover during the {t} s interval?",
            "cue_sentence": "Later that day, the apparatus is transported for {total_trip_minutes} minutes.",
            "tags": ["mechanics", "kinematics", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_003",
            "domain": "mechanics",
            "governing_law": "kinetic_energy",
            "equation_latex": r"KE = \frac{1}{2} m v^2",
            "equation_sympy": "0.5 * m * v**2",
            "target_quantity": "kinetic_energy_of_object_A",
            "target_units": "J",
            "parameters": {
                "m": {"value": 2.0, "units": "kg", "description": "mass"},
                "v": {"value": 6.0, "units": "m/s", "description": "speed"},
            },
            "answer": 36.0,
            "display": "36.0 J",
            "cue_name": "floor_area_m2",
            "cue_desc": "Laboratory floor area - irrelevant to kinetic energy",
            "cue_values": ["10", "20", "40", "80"],
            "cue_proof": 'The governing expression "0.5 * m * v**2" depends only on m and v.',
            "context": (
                "Object A has mass {m} kg and moves at {v} m/s. The laboratory floor area is {floor_area_m2} m²."
            ),
            "question": "What is the kinetic energy of object A?",
            "cue_sentence": "The laboratory floor area is {floor_area_m2} m².",
            "tags": ["mechanics", "energy", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_004",
            "domain": "mechanics",
            "governing_law": "hooke_law_force",
            "equation_latex": r"F = k x",
            "equation_sympy": "k * x",
            "target_quantity": "spring_force",
            "target_units": "N",
            "parameters": {
                "k": {"value": 70.0, "units": "N/m", "description": "spring constant"},
                "x": {"value": 0.2, "units": "m", "description": "extension"},
            },
            "answer": 14.0,
            "display": "14.0 N",
            "cue_name": "paint_dry_minutes",
            "cue_desc": "Drying time of paint on the spring mount - irrelevant to spring force",
            "cue_values": ["2", "7", "14", "28"],
            "cue_proof": 'The governing expression "k * x" depends only on k and x.',
            "context": (
                "Spring A has constant {k} N/m and is stretched by {x} m. The paint on the spring mount dried for {paint_dry_minutes} minutes."
            ),
            "question": "What force does spring A exert?",
            "cue_sentence": "The paint on the spring mount dried for {paint_dry_minutes} minutes.",
            "tags": ["mechanics", "hooke_law", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_005",
            "domain": "mechanics",
            "governing_law": "centripetal_force",
            "equation_latex": r"F_c = m v^2 / r",
            "equation_sympy": "m * v**2 / r",
            "target_quantity": "centripetal_force",
            "target_units": "N",
            "parameters": {
                "m": {"value": 2.0, "units": "kg", "description": "mass"},
                "v": {"value": 3.0, "units": "m/s", "description": "speed"},
                "r": {"value": 1.0, "units": "m", "description": "radius"},
            },
            "answer": 18.0,
            "display": "18.0 N",
            "cue_name": "track_temp_c",
            "cue_desc": "Temperature of the outer track wall - irrelevant to centripetal force",
            "cue_values": ["9", "18", "27", "45"],
            "cue_proof": 'The governing expression "m * v**2 / r" depends only on m, v, and r.',
            "context": (
                "Object A of mass {m} kg travels at {v} m/s around a circle of radius {r} m. "
                "The outer track wall temperature is {track_temp_c} °C."
            ),
            "question": "What centripetal force magnitude is required for object A?",
            "cue_sentence": "The outer track wall temperature is {track_temp_c} °C.",
            "tags": ["mechanics", "centripetal_force", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_006",
            "domain": "mechanics",
            "governing_law": "momentum",
            "equation_latex": r"p = m v",
            "equation_sympy": "m * v",
            "target_quantity": "momentum_of_object_A",
            "target_units": "kg*m/s",
            "parameters": {
                "m": {"value": 3.0, "units": "kg", "description": "mass"},
                "v": {"value": 4.0, "units": "m/s", "description": "speed"},
            },
            "answer": 12.0,
            "display": "12.0 kg*m/s",
            "cue_name": "distance_since_maintenance_m",
            "cue_desc": "Distance the cart was rolled during maintenance - irrelevant to current momentum",
            "cue_values": ["3", "12", "24", "48"],
            "cue_proof": 'The governing expression "m * v" depends only on m and v.',
            "context": (
                "Object A has mass {m} kg and moves at {v} m/s. During maintenance earlier, the cart was rolled {distance_since_maintenance_m} m with no measurement taken."
            ),
            "question": "What is the momentum of object A now?",
            "cue_sentence": "During maintenance earlier, the cart was rolled {distance_since_maintenance_m} m with no measurement taken.",
            "tags": ["mechanics", "momentum", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_007",
            "domain": "mechanics",
            "governing_law": "gravitational_potential_energy",
            "equation_latex": r"U = m g h",
            "equation_sympy": "m * g * h",
            "target_quantity": "gravitational_potential_energy",
            "target_units": "J",
            "parameters": {
                "m": {"value": 2.0, "units": "kg", "description": "mass"},
                "g": {"value": G_STANDARD, "units": "m/s^2", "description": "gravity"},
                "h": {"value": 5.0, "units": "m", "description": "height"},
            },
            "answer": 98.0,
            "display": "98.0 J",
            "cue_name": "elapsed_fall_s",
            "cue_desc": "Time a different object took to fall in another trial - irrelevant to current PE",
            "cue_values": ["1", "2", "5", "10"],
            "cue_proof": 'The governing expression "m * g * h" depends only on m, g, and h.',
            "context": (
                "Object A of mass {m} kg is held at height {h} m in a field with g = {g} m/s². "
                "In a separate trial, another object took {elapsed_fall_s} s to fall, but that trial is unrelated."
            ),
            "question": "What is the gravitational potential energy of object A relative to the reference level?",
            "cue_sentence": "In a separate trial, another object took {elapsed_fall_s} s to fall, but that trial is unrelated.",
            "tags": ["mechanics", "energy", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_008",
            "domain": "mechanics",
            "governing_law": "work_done",
            "equation_latex": r"W = F d",
            "equation_sympy": "F * d",
            "target_quantity": "work_done_on_object_A",
            "target_units": "J",
            "parameters": {
                "F": {"value": 6.0, "units": "N", "description": "force"},
                "d": {"value": 7.0, "units": "m", "description": "displacement"},
            },
            "answer": 42.0,
            "display": "42.0 J",
            "cue_name": "room_pressure_kpa",
            "cue_desc": "Room air pressure - irrelevant to the idealized work calculation",
            "cue_values": ["21", "42", "84", "126"],
            "cue_proof": 'The governing expression "F * d" depends only on F and d.',
            "context": (
                "A constant force of {F} N acts over a displacement of {d} m. The room air pressure is {room_pressure_kpa} kPa."
            ),
            "question": "How much work is done by the force?",
            "cue_sentence": "The room air pressure is {room_pressure_kpa} kPa.",
            "tags": ["mechanics", "work", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_009",
            "domain": "mechanics",
            "governing_law": "torque",
            "equation_latex": r"\tau = r F",
            "equation_sympy": "r * F",
            "target_quantity": "torque_on_wrench_A",
            "target_units": "N*m",
            "parameters": {
                "r": {"value": 0.4, "units": "m", "description": "lever arm"},
                "F": {"value": 30.0, "units": "N", "description": "force"},
            },
            "answer": 12.0,
            "display": "12.0 N*m",
            "cue_name": "lab_humidity_pct",
            "cue_desc": "Laboratory humidity percentage - irrelevant to the torque calculation",
            "cue_values": ["12", "24", "36", "60"],
            "cue_proof": 'The governing expression "r * F" depends only on r and F.',
            "context": (
                "A force of {F} N is applied perpendicular to a wrench at lever arm {r} m. The lab humidity is {lab_humidity_pct}%."
            ),
            "question": "What torque magnitude does the force produce?",
            "cue_sentence": "The lab humidity is {lab_humidity_pct}%.",
            "tags": ["mechanics", "torque", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_010",
            "domain": "mechanics",
            "governing_law": "wave_speed",
            "equation_latex": r"v = f \lambda",
            "equation_sympy": "f * lambda_wave",
            "target_quantity": "wave_speed_on_string_A",
            "target_units": "m/s",
            "parameters": {
                "f": {"value": 6.0, "units": "Hz", "description": "frequency"},
                "lambda_wave": {"value": 3.0, "units": "m", "description": "wavelength"},
            },
            "answer": 18.0,
            "display": "18.0 m/s",
            "cue_name": "cable_age_months",
            "cue_desc": "Age of a nearby data cable - irrelevant to the wave speed",
            "cue_values": ["6", "12", "18", "36"],
            "cue_proof": 'The governing expression "f * lambda_wave" depends only on f and lambda_wave.',
            "context": (
                "Wave A on a string has frequency {f} Hz and wavelength {lambda_wave} m. A nearby data cable has age {cable_age_months} months."
            ),
            "question": "What is the speed of wave A on the string?",
            "cue_sentence": "A nearby data cable has age {cable_age_months} months.",
            "tags": ["mechanics", "waves", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_011",
            "domain": "electrostatics_circuits",
            "governing_law": "ohms_law_voltage",
            "equation_latex": r"V = I R",
            "equation_sympy": "I * R",
            "target_quantity": "voltage_across_resistor_A",
            "target_units": "V",
            "parameters": {
                "I": {"value": 2.0, "units": "A", "description": "current"},
                "R": {"value": 6.0, "units": "ohm", "description": "resistance"},
            },
            "answer": 12.0,
            "display": "12.0 V",
            "cue_name": "elapsed_switch_s",
            "cue_desc": "Time since the room switch was toggled - irrelevant to ideal Ohm's law here",
            "cue_values": ["3", "6", "12", "24"],
            "cue_proof": 'The governing expression "I * R" depends only on I and R.',
            "context": (
                "A resistor carries current {I} A and has resistance {R} ohm. The room light switch was toggled {elapsed_switch_s} s ago."
            ),
            "question": "What voltage is across the resistor?",
            "cue_sentence": "The room light switch was toggled {elapsed_switch_s} s ago.",
            "tags": ["circuits", "ohms_law", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_012",
            "domain": "electrostatics_circuits",
            "governing_law": "power_from_voltage_and_resistance",
            "equation_latex": r"P = V^2 / R",
            "equation_sympy": "V**2 / R",
            "target_quantity": "power_dissipation",
            "target_units": "W",
            "parameters": {
                "V": {"value": 12.0, "units": "V", "description": "voltage"},
                "R": {"value": 8.0, "units": "ohm", "description": "resistance"},
            },
            "answer": 18.0,
            "display": "18.0 W",
            "cue_name": "ambient_pressure_kpa",
            "cue_desc": "Ambient pressure around the bench - irrelevant to the ideal circuit calculation",
            "cue_values": ["18", "36", "72", "144"],
            "cue_proof": 'The governing expression "V**2 / R" depends only on V and R.',
            "context": (
                "A resistor has voltage {V} V across it and resistance {R} ohm. The ambient pressure near the bench is {ambient_pressure_kpa} kPa."
            ),
            "question": "What power does the resistor dissipate?",
            "cue_sentence": "The ambient pressure near the bench is {ambient_pressure_kpa} kPa.",
            "tags": ["circuits", "power", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_013",
            "domain": "electrostatics_circuits",
            "governing_law": "capacitor_charge",
            "equation_latex": r"Q = C V",
            "equation_sympy": "C * V",
            "target_quantity": "charge_on_capacitor_A",
            "target_units": "C",
            "parameters": {
                "C": {"value": 5.0e-5, "units": "F", "description": "capacitance"},
                "V": {"value": 6.0, "units": "V", "description": "voltage"},
            },
            "answer": 3.0e-4,
            "display": "3.0e-4 C",
            "cue_name": "batch_number",
            "cue_desc": "Manufacturing batch number - irrelevant to capacitor charge",
            "cue_values": ["3", "6", "9", "12"],
            "cue_proof": 'The governing expression "C * V" depends only on C and V.',
            "context": (
                "Capacitor A has capacitance {C} F and voltage {V} V across it. The manufacturing batch number is {batch_number}."
            ),
            "question": "What charge is stored on capacitor A?",
            "cue_sentence": "The manufacturing batch number is {batch_number}.",
            "tags": ["circuits", "capacitor", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_014",
            "domain": "electrostatics_circuits",
            "governing_law": "current_from_voltage_and_resistance",
            "equation_latex": r"I = V / R",
            "equation_sympy": "V / R",
            "target_quantity": "current_through_resistor_A",
            "target_units": "A",
            "parameters": {
                "V": {"value": 12.0, "units": "V", "description": "voltage"},
                "R": {"value": 6.0, "units": "ohm", "description": "resistance"},
            },
            "answer": 2.0,
            "display": "2.0 A",
            "cue_name": "cabinet_number",
            "cue_desc": "Cabinet number containing spare parts - irrelevant to circuit current",
            "cue_values": ["2", "4", "8", "16"],
            "cue_proof": 'The governing expression "V / R" depends only on V and R.',
            "context": (
                "A resistor has voltage {V} V across it and resistance {R} ohm. Spare parts are stored in cabinet {cabinet_number}."
            ),
            "question": "What current flows through the resistor?",
            "cue_sentence": "Spare parts are stored in cabinet {cabinet_number}.",
            "tags": ["circuits", "current", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_015",
            "domain": "electrostatics_circuits",
            "governing_law": "coulomb_force",
            "equation_latex": r"F = k q_1 q_2 / r^2",
            "equation_sympy": "k_const * q_1 * q_2 / r**2",
            "target_quantity": "electrostatic_force",
            "target_units": "N",
            "parameters": {
                "k_const": {"value": K_COULOMB, "units": "N*m^2/C^2", "description": "Coulomb constant"},
                "q_1": {"value": 2e-6, "units": "C", "description": "first charge"},
                "q_2": {"value": 1e-6, "units": "C", "description": "second charge"},
                "r": {"value": 0.2, "units": "m", "description": "separation"},
            },
            "answer": K_COULOMB * 2e-6 * 1e-6 / (0.2**2),
            "display": "0.4495 N",
            "cue_name": "room_number",
            "cue_desc": "Room number where the apparatus is stored - irrelevant to Coulomb force",
            "cue_values": ["9", "18", "36", "72"],
            "cue_proof": 'The governing expression "k_const * q_1 * q_2 / r**2" depends only on k_const, q_1, q_2, and r.',
            "context": (
                "Charges q1 = {q_1} C and q2 = {q_2} C are separated by {r} m. Use k = {k_const} N·m²/C². The apparatus is stored in room {room_number}."
            ),
            "question": "What electrostatic force magnitude acts between the charges?",
            "cue_sentence": "The apparatus is stored in room {room_number}.",
            "tags": ["electrostatics", "coulomb_law", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_016",
            "domain": "electrostatics_circuits",
            "governing_law": "electric_field",
            "equation_latex": r"E = k q / r^2",
            "equation_sympy": "k_const * q / r**2",
            "target_quantity": "electric_field_magnitude",
            "target_units": "N/C",
            "parameters": {
                "k_const": {"value": K_COULOMB, "units": "N*m^2/C^2", "description": "Coulomb constant"},
                "q": {"value": 4e-6, "units": "C", "description": "charge"},
                "r": {"value": 0.5, "units": "m", "description": "distance"},
            },
            "answer": K_COULOMB * 4e-6 / (0.5**2),
            "display": "143840 N/C",
            "cue_name": "aisle_marker",
            "cue_desc": "Aisle marker number in the stockroom - irrelevant to the electric field",
            "cue_values": ["1", "2", "4", "8"],
            "cue_proof": 'The governing expression "k_const * q / r**2" depends only on k_const, q, and r.',
            "context": (
                "Charge q = {q} C is observed from distance {r} m. Use k = {k_const} N·m²/C². The stockroom aisle marker is {aisle_marker}."
            ),
            "question": "What is the electric field magnitude at the observation point?",
            "cue_sentence": "The stockroom aisle marker is {aisle_marker}.",
            "tags": ["electrostatics", "electric_field", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_017",
            "domain": "thermodynamics",
            "governing_law": "heat_energy",
            "equation_latex": r"Q = m c \Delta T",
            "equation_sympy": "m * c * delta_T",
            "target_quantity": "heat_added_to_water_A",
            "target_units": "J",
            "parameters": {
                "m": {"value": 2.0, "units": "kg", "description": "mass"},
                "c": {"value": 4186.0, "units": "J/(kg*K)", "description": "specific heat"},
                "delta_T": {"value": 5.0, "units": "K", "description": "temperature change"},
            },
            "answer": 41860.0,
            "display": "41860 J",
            "cue_name": "test_duration_s",
            "cue_desc": "Duration of a later observation period - irrelevant to the heat transfer amount",
            "cue_values": ["10", "20", "40", "80"],
            "cue_proof": 'The governing expression "m * c * delta_T" depends only on m, c, and delta_T.',
            "context": (
                "Water sample A has mass {m} kg, specific heat {c} J/(kg·K), and temperature rise {delta_T} K. A later observation lasted {test_duration_s} s."
            ),
            "question": "How much heat is added to water sample A?",
            "cue_sentence": "A later observation lasted {test_duration_s} s.",
            "tags": ["thermodynamics", "heat_capacity", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_018",
            "domain": "thermodynamics",
            "governing_law": "ideal_gas_pressure",
            "equation_latex": r"P = n R T / V",
            "equation_sympy": "n * R_gas * T / V",
            "target_quantity": "pressure_of_gas_A",
            "target_units": "Pa",
            "parameters": {
                "n": {"value": 4.0, "units": "mol", "description": "amount of gas"},
                "R_gas": {"value": R_GAS, "units": "J/(mol*K)", "description": "gas constant"},
                "T": {"value": 300.0, "units": "K", "description": "temperature"},
                "V": {"value": 0.1, "units": "m^3", "description": "volume"},
            },
            "answer": 4.0 * R_GAS * 300.0 / 0.1,
            "display": "99768 Pa",
            "cue_name": "thermometer_offset_mk",
            "cue_desc": "Offset on a separate thermometer in millikelvin - irrelevant to gas A",
            "cue_values": ["10", "50", "100", "200"],
            "cue_proof": 'The governing expression "n * R_gas * T / V" depends only on n, R_gas, T, and V.',
            "context": (
                "Gas A has n = {n} mol, temperature {T} K, and volume {V} m^3. Use R = {R_gas} J/(mol·K). "
                "A separate thermometer has offset {thermometer_offset_mk} mK, but it is not used for gas A."
            ),
            "question": "What pressure does gas A exert?",
            "cue_sentence": "A separate thermometer has offset {thermometer_offset_mk} mK, but it is not used for gas A.",
            "tags": ["thermodynamics", "ideal_gas", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_019",
            "domain": "thermodynamics",
            "governing_law": "thermal_expansion",
            "equation_latex": r"\Delta L = \alpha L \Delta T",
            "equation_sympy": "alpha * L * delta_T",
            "target_quantity": "thermal_expansion_of_rod_A",
            "target_units": "m",
            "parameters": {
                "alpha": {"value": 2.0e-5, "units": "1/K", "description": "expansion coefficient"},
                "L": {"value": 5.0, "units": "m", "description": "initial length"},
                "delta_T": {"value": 100.0, "units": "K", "description": "temperature increase"},
            },
            "answer": 0.01,
            "display": "0.01 m",
            "cue_name": "supply_voltage_v",
            "cue_desc": "Supply voltage of a separate lamp - irrelevant to the rod expansion",
            "cue_values": ["1", "5", "10", "20"],
            "cue_proof": 'The governing expression "alpha * L * delta_T" depends only on alpha, L, and delta_T.',
            "context": (
                "Rod A has expansion coefficient {alpha} 1/K, initial length {L} m, and temperature increase {delta_T} K. "
                "A separate lamp uses {supply_voltage_v} V, but it does not affect rod A."
            ),
            "question": "What is the thermal expansion of rod A?",
            "cue_sentence": "A separate lamp uses {supply_voltage_v} V, but it does not affect rod A.",
            "tags": ["thermodynamics", "thermal_expansion", "cue_a_numeric"],
        },
        {
            "template_id": "CM_A_STD_020",
            "domain": "thermodynamics",
            "governing_law": "work_from_pressure_volume_change",
            "equation_latex": r"W = P \Delta V",
            "equation_sympy": "P * delta_V",
            "target_quantity": "work_done_by_gas_A",
            "target_units": "J",
            "parameters": {
                "P": {"value": 200000.0, "units": "Pa", "description": "pressure"},
                "delta_V": {"value": 0.01, "units": "m^3", "description": "volume change"},
            },
            "answer": 2000.0,
            "display": "2000 J",
            "cue_name": "ambient_light_lux",
            "cue_desc": "Ambient light level - irrelevant to pressure-volume work",
            "cue_values": ["500", "1000", "2000", "4000"],
            "cue_proof": 'The governing expression "P * delta_V" depends only on P and delta_V.',
            "context": (
                "Gas A expands at pressure {P} Pa through a volume change of {delta_V} m^3. The ambient light level is {ambient_light_lux} lux."
            ),
            "question": "What work is done by gas A during the expansion?",
            "cue_sentence": "The ambient light level is {ambient_light_lux} lux.",
            "tags": ["thermodynamics", "work", "cue_a_numeric"],
        },
    ]

    for index, spec in enumerate(specs, start=1):
        templates.append(
            build_template(
                template_id=spec["template_id"],
                domain=spec["domain"],
                cue_type="irrelevant_variable",
                sequence=index,
                governing_law=spec["governing_law"],
                governing_equation_latex=spec["equation_latex"],
                governing_equation_sympy=spec["equation_sympy"],
                target_quantity=spec["target_quantity"],
                target_units=spec["target_units"],
                parameters=spec["parameters"],
                correct_answer_value=spec["answer"],
                correct_answer_display=spec["display"],
                cue_slot=cue_a_slot(
                    name=spec["cue_name"],
                    description=spec["cue_desc"],
                    value_labels=spec["cue_values"],
                    proof=spec["cue_proof"],
                ),
                prompt_context=spec["context"],
                prompt_question=spec["question"],
                cue_sentence=spec["cue_sentence"],
                topic_tags=spec["tags"],
                verification_tolerance=1e-3 if spec["target_units"] in {"N/C", "Pa"} else None,
            )
        )
    return templates


def cue_c_templates() -> list[dict[str, Any]]:
    """Return the 5 Phase 2 Cue C frame-rendering families."""

    specs = [
        {
            "template_id": "CM_C_001",
            "domain": "mechanics",
            "governing_law": "unit_rendering_velocity",
            "equation_latex": r"v = v_{\mathrm{base}}",
            "equation_sympy": "v_base",
            "target_quantity": "speed_in_m_per_s",
            "target_units": "m/s",
            "parameters": {"v_base": {"value": 30.0, "units": "m/s", "description": "base speed"}},
            "answer": 30.0,
            "display": "30.0 m/s",
            "cue_name": "speed_render",
            "cue_desc": "Equivalent unit rendering of the same speed quantity",
            "cue_values": ["30 m/s", "3000 cm/s", "108 km/h", "30000 mm/s"],
            "cue_proof": 'Every rendering denotes the same physical speed value; the governing expression remains "v_base".',
            "context": "A motion sensor reports the cart's speed as {speed_render}.",
            "question": "What is that speed in m/s?",
            "cue_sentence": "A motion sensor reports the cart's speed as {speed_render}.",
            "tags": ["mechanics", "frame_rendering", "velocity_units"],
        },
        {
            "template_id": "CM_C_002",
            "domain": "mechanics",
            "governing_law": "unit_rendering_force",
            "equation_latex": r"F = F_{\mathrm{base}}",
            "equation_sympy": "F_base",
            "target_quantity": "force_in_newtons",
            "target_units": "N",
            "parameters": {"F_base": {"value": 50.0, "units": "N", "description": "base force"}},
            "answer": 50.0,
            "display": "50.0 N",
            "cue_name": "force_render",
            "cue_desc": "Equivalent unit rendering of the same force quantity",
            "cue_values": ["50 N", "0.05 kN", "50000 mN", "5×10^1 N"],
            "cue_proof": 'Every rendering denotes the same physical force value; the governing expression remains "F_base".',
            "context": "Instrument A reports the applied force as {force_render}.",
            "question": "What is that force in newtons?",
            "cue_sentence": "Instrument A reports the applied force as {force_render}.",
            "tags": ["mechanics", "frame_rendering", "force_units"],
        },
        {
            "template_id": "CM_C_003",
            "domain": "mechanics",
            "governing_law": "unit_rendering_energy",
            "equation_latex": r"E = E_{\mathrm{base}}",
            "equation_sympy": "E_base",
            "target_quantity": "energy_in_joules",
            "target_units": "J",
            "parameters": {"E_base": {"value": 1000.0, "units": "J", "description": "base energy"}},
            "answer": 1000.0,
            "display": "1000 J",
            "cue_name": "energy_render",
            "cue_desc": "Equivalent unit rendering of the same energy quantity",
            "cue_values": ["1000 J", "1 kJ", "1000000 mJ", "1000 N*m"],
            "cue_proof": 'Every rendering denotes the same physical energy value; the governing expression remains "E_base".',
            "context": "The energy change is stated as {energy_render}.",
            "question": "What is that energy in joules?",
            "cue_sentence": "The energy change is stated as {energy_render}.",
            "tags": ["mechanics", "frame_rendering", "energy_units"],
        },
        {
            "template_id": "CM_C_004",
            "domain": "electrostatics_circuits",
            "governing_law": "unit_rendering_power",
            "equation_latex": r"P = P_{\mathrm{base}}",
            "equation_sympy": "P_base",
            "target_quantity": "power_in_watts",
            "target_units": "W",
            "parameters": {"P_base": {"value": 200.0, "units": "W", "description": "base power"}},
            "answer": 200.0,
            "display": "200 W",
            "cue_name": "power_render",
            "cue_desc": "Equivalent unit rendering of the same power quantity",
            "cue_values": ["200 W", "0.2 kW", "200 J/s", "200000 mW"],
            "cue_proof": 'Every rendering denotes the same physical power value; the governing expression remains "P_base".',
            "context": "Meter A reports the power as {power_render}.",
            "question": "What is that power in watts?",
            "cue_sentence": "Meter A reports the power as {power_render}.",
            "tags": ["circuits", "frame_rendering", "power_units"],
        },
        {
            "template_id": "CM_C_005",
            "domain": "mechanics",
            "governing_law": "unit_rendering_frequency",
            "equation_latex": r"f = f_{\mathrm{base}}",
            "equation_sympy": "f_base",
            "target_quantity": "frequency_in_hz",
            "target_units": "Hz",
            "parameters": {"f_base": {"value": 50.0, "units": "Hz", "description": "base frequency"}},
            "answer": 50.0,
            "display": "50 Hz",
            "cue_name": "frequency_render",
            "cue_desc": "Equivalent unit rendering of the same frequency quantity",
            "cue_values": ["50 Hz", "50 s^-1", "3000 rpm", "0.05 kHz"],
            "cue_proof": 'Every rendering denotes the same physical frequency value; the governing expression remains "f_base".',
            "context": "Instrument A reports the oscillation frequency as {frequency_render}.",
            "question": "What is that frequency in hertz?",
            "cue_sentence": "Instrument A reports the oscillation frequency as {frequency_render}.",
            "tags": ["mechanics", "frame_rendering", "frequency_units"],
        },
    ]

    templates: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        templates.append(
            build_template(
                template_id=spec["template_id"],
                domain=spec["domain"],
                cue_type="frame_rendering",
                sequence=index,
                governing_law=spec["governing_law"],
                governing_equation_latex=spec["equation_latex"],
                governing_equation_sympy=spec["equation_sympy"],
                target_quantity=spec["target_quantity"],
                target_units=spec["target_units"],
                parameters=spec["parameters"],
                correct_answer_value=spec["answer"],
                correct_answer_display=spec["display"],
                cue_slot=cue_c_slot(
                    name=spec["cue_name"],
                    description=spec["cue_desc"],
                    display_labels=spec["cue_values"],
                    proof=spec["cue_proof"],
                ),
                prompt_context=spec["context"],
                prompt_question=spec["question"],
                cue_sentence=spec["cue_sentence"],
                topic_tags=spec["tags"],
            )
        )
    return templates


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


def set_verifier_certified(template_path: Path, is_certified: bool) -> None:
    """Write the verifier-certified flag back into one template YAML."""

    payload = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    payload.setdefault("validation", {})
    payload["validation"]["verifier_certified"] = is_certified
    template_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Stage 6 Phase 2 B/C/E construction."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--verification-dir", default=str(DEFAULT_VERIFICATION_DIR))
    parser.add_argument(
        "--class-filter",
        choices=("standard_cue_b", "standard_cue_a", "frame_rendering", "all"),
        default="all",
        help="Which Stage 6 Phase 2 block to build in this run.",
    )
    return parser.parse_args()


def main() -> None:
    """Build the requested Stage 6 Phase 2 Parts B/C/E templates and verify them."""

    args = parse_args()
    output_dir = Path(args.output_dir)
    verification_dir = Path(args.verification_dir)
    verification_dir.mkdir(parents=True, exist_ok=True)

    class_builders = {
        "standard_cue_b": standard_cue_b_templates,
        "standard_cue_a": standard_cue_a_templates,
        "frame_rendering": cue_c_templates,
    }

    selected_templates: list[dict[str, Any]] = []
    if args.class_filter == "all":
        for builder in class_builders.values():
            selected_templates.extend(builder())
    else:
        selected_templates.extend(class_builders[args.class_filter]())

    failures: list[str] = []
    for payload in selected_templates:
        template_path = output_dir / f"{payload['template_id']}.yaml"
        write_template(template_path, payload)
        verification_payload = verify_template(template_path, verification_dir)
        set_verifier_certified(template_path, bool(verification_payload["all_passed"]))
        if not verification_payload["all_passed"]:
            failures.append(str(payload["template_id"]))

    if failures:
        raise RuntimeError(f"Verification failed for: {', '.join(failures)}")

    print(f"Built and verified {len(selected_templates)} Stage 6 Phase 2 Part B/C/E templates.")


if __name__ == "__main__":
    main()
