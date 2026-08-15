#!/usr/bin/env python3
"""Build candidate Stage 10 benchmark-expansion templates.

This first expansion tranche focuses on:
1. Additional Cue C exact-rendering families.
2. Additional extreme near-match Cue B families.

The script writes template YAML files and local verifier reports so the new
families can move into review/rendering without being hand-authored later.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from build_stage6_phase2_bce_templates import (  # type: ignore
    cue_b_slot,
    cue_c_slot,
    build_template,
    write_template,
    verify_template,
    set_verifier_certified,
)


DEFAULT_OUTPUT_DIR = Path("data/raw/templates/stage10_expansion")
DEFAULT_VERIFICATION_DIR = Path("results/stage10/benchmark_expansion/verification")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--verification-dir", type=Path, default=DEFAULT_VERIFICATION_DIR)
    return parser.parse_args()


def cue_c_expansion_templates() -> list[dict[str, Any]]:
    specs = [
        {
            "template_id": "CM_C_006",
            "domain": "electrostatics_circuits",
            "governing_law": "unit_rendering_charge",
            "equation_latex": r"q = q_{\mathrm{base}}",
            "equation_sympy": "q_base",
            "target_quantity": "charge_in_coulombs",
            "target_units": "C",
            "parameters": {"q_base": {"value": 2.0, "units": "C", "description": "base charge"}},
            "answer": 2.0,
            "display": "2.0 C",
            "cue_name": "charge_render",
            "cue_desc": "Equivalent rendering of the same charge quantity",
            "cue_values": ["2 C", "2000 mC", "2000000 μC", "2 A*s"],
            "cue_proof": 'Each rendering denotes the same charge value; the governing expression remains "q_base".',
            "context": "A charge standard is labelled as {charge_render}.",
            "question": "What is that charge in coulombs?",
            "cue_sentence": "A charge standard is labelled as {charge_render}.",
            "tags": ["circuits", "frame_rendering", "charge_units"],
        },
        {
            "template_id": "CM_C_007",
            "domain": "thermodynamics",
            "governing_law": "unit_rendering_pressure",
            "equation_latex": r"P = P_{\mathrm{base}}",
            "equation_sympy": "P_base",
            "target_quantity": "pressure_in_pascals",
            "target_units": "Pa",
            "parameters": {"P_base": {"value": 101325.0, "units": "Pa", "description": "base pressure"}},
            "answer": 101325.0,
            "display": "101325 Pa",
            "cue_name": "pressure_render",
            "cue_desc": "Equivalent rendering of the same pressure quantity",
            "cue_values": ["101325 Pa", "101.325 kPa", "1.01325 bar", "101325 N/m^2"],
            "cue_proof": 'Each rendering denotes the same pressure value; the governing expression remains "P_base".',
            "context": "A sealed vessel gauge reports the pressure as {pressure_render}.",
            "question": "What is that pressure in pascals?",
            "cue_sentence": "A sealed vessel gauge reports the pressure as {pressure_render}.",
            "tags": ["thermodynamics", "frame_rendering", "pressure_units"],
        },
        {
            "template_id": "CM_C_008",
            "domain": "electrostatics_circuits",
            "governing_law": "unit_rendering_current",
            "equation_latex": r"I = I_{\mathrm{base}}",
            "equation_sympy": "I_base",
            "target_quantity": "current_in_amperes",
            "target_units": "A",
            "parameters": {"I_base": {"value": 0.75, "units": "A", "description": "base current"}},
            "answer": 0.75,
            "display": "0.75 A",
            "cue_name": "current_render",
            "cue_desc": "Equivalent rendering of the same current quantity",
            "cue_values": ["0.75 A", "750 mA", "750000 μA", "0.00075 kA"],
            "cue_proof": 'Each rendering denotes the same current value; the governing expression remains "I_base".',
            "context": "Meter A displays the current as {current_render}.",
            "question": "What is that current in amperes?",
            "cue_sentence": "Meter A displays the current as {current_render}.",
            "tags": ["circuits", "frame_rendering", "current_units"],
        },
        {
            "template_id": "CM_C_009",
            "domain": "electrostatics_circuits",
            "governing_law": "unit_rendering_voltage",
            "equation_latex": r"V = V_{\mathrm{base}}",
            "equation_sympy": "V_base",
            "target_quantity": "voltage_in_volts",
            "target_units": "V",
            "parameters": {"V_base": {"value": 12.0, "units": "V", "description": "base voltage"}},
            "answer": 12.0,
            "display": "12.0 V",
            "cue_name": "voltage_render",
            "cue_desc": "Equivalent rendering of the same voltage quantity",
            "cue_values": ["12 V", "12000 mV", "0.012 kV", "12 J/C"],
            "cue_proof": 'Each rendering denotes the same voltage value; the governing expression remains "V_base".',
            "context": "A source is rated at {voltage_render}.",
            "question": "What is that voltage in volts?",
            "cue_sentence": "A source is rated at {voltage_render}.",
            "tags": ["circuits", "frame_rendering", "voltage_units"],
        },
        {
            "template_id": "CM_C_010",
            "domain": "electrostatics_circuits",
            "governing_law": "unit_rendering_capacitance",
            "equation_latex": r"C = C_{\mathrm{base}}",
            "equation_sympy": "C_base",
            "target_quantity": "capacitance_in_farads",
            "target_units": "F",
            "parameters": {"C_base": {"value": 0.002, "units": "F", "description": "base capacitance"}},
            "answer": 0.002,
            "display": "0.002 F",
            "cue_name": "capacitance_render",
            "cue_desc": "Equivalent rendering of the same capacitance quantity",
            "cue_values": ["0.002 F", "2 mF", "2000 μF", "2000000 nF"],
            "cue_proof": 'Each rendering denotes the same capacitance value; the governing expression remains "C_base".',
            "context": "A capacitor is labelled {capacitance_render}.",
            "question": "What is that capacitance in farads?",
            "cue_sentence": "A capacitor is labelled {capacitance_render}.",
            "tags": ["circuits", "frame_rendering", "capacitance_units"],
        },
        {
            "template_id": "CM_C_011",
            "domain": "electrostatics_circuits",
            "governing_law": "unit_rendering_resistance",
            "equation_latex": r"R = R_{\mathrm{base}}",
            "equation_sympy": "R_base",
            "target_quantity": "resistance_in_ohms",
            "target_units": "ohm",
            "parameters": {"R_base": {"value": 500.0, "units": "ohm", "description": "base resistance"}},
            "answer": 500.0,
            "display": "500 ohm",
            "cue_name": "resistance_render",
            "cue_desc": "Equivalent rendering of the same resistance quantity",
            "cue_values": ["500 ohm", "0.5 kohm", "500000 mohm", "0.0005 Mohm"],
            "cue_proof": 'Each rendering denotes the same resistance value; the governing expression remains "R_base".',
            "context": "The resistor body is marked as {resistance_render}.",
            "question": "What is that resistance in ohms?",
            "cue_sentence": "The resistor body is marked as {resistance_render}.",
            "tags": ["circuits", "frame_rendering", "resistance_units"],
        },
        {
            "template_id": "CM_C_012",
            "domain": "mechanics",
            "governing_law": "unit_rendering_momentum",
            "equation_latex": r"p = p_{\mathrm{base}}",
            "equation_sympy": "p_base",
            "target_quantity": "momentum_in_kg_m_per_s",
            "target_units": "kg*m/s",
            "parameters": {"p_base": {"value": 12.0, "units": "kg*m/s", "description": "base momentum"}},
            "answer": 12.0,
            "display": "12.0 kg*m/s",
            "cue_name": "momentum_render",
            "cue_desc": "Equivalent rendering of the same momentum quantity",
            "cue_values": ["12 kg*m/s", "12 N*s", "12000 g*m/s", "0.012 kN*s"],
            "cue_proof": 'Each rendering denotes the same momentum value; the governing expression remains "p_base".',
            "context": "The trolley momentum is recorded as {momentum_render}.",
            "question": "What is that momentum in kg*m/s?",
            "cue_sentence": "The trolley momentum is recorded as {momentum_render}.",
            "tags": ["mechanics", "frame_rendering", "momentum_units"],
        },
        {
            "template_id": "CM_C_013",
            "domain": "mechanics",
            "governing_law": "unit_rendering_acceleration",
            "equation_latex": r"a = a_{\mathrm{base}}",
            "equation_sympy": "a_base",
            "target_quantity": "acceleration_in_m_per_s2",
            "target_units": "m/s^2",
            "parameters": {"a_base": {"value": 9.8, "units": "m/s^2", "description": "base acceleration"}},
            "answer": 9.8,
            "display": "9.8 m/s^2",
            "cue_name": "acceleration_render",
            "cue_desc": "Equivalent rendering of the same acceleration quantity",
            "cue_values": ["9.8 m/s^2", "980 cm/s^2", "0.0098 km/s^2", "9.8 N/kg"],
            "cue_proof": 'Each rendering denotes the same acceleration value; the governing expression remains "a_base".',
            "context": "An inertial sensor reports the acceleration as {acceleration_render}.",
            "question": "What is that acceleration in m/s^2?",
            "cue_sentence": "An inertial sensor reports the acceleration as {acceleration_render}.",
            "tags": ["mechanics", "frame_rendering", "acceleration_units"],
        },
        {
            "template_id": "CM_C_014",
            "domain": "electrostatics_circuits",
            "governing_law": "unit_rendering_electric_field",
            "equation_latex": r"E = E_{\mathrm{base}}",
            "equation_sympy": "E_base",
            "target_quantity": "electric_field_in_n_per_c",
            "target_units": "N/C",
            "parameters": {"E_base": {"value": 250.0, "units": "N/C", "description": "base electric field"}},
            "answer": 250.0,
            "display": "250 N/C",
            "cue_name": "efield_render",
            "cue_desc": "Equivalent rendering of the same electric-field quantity",
            "cue_values": ["250 N/C", "250 V/m", "0.25 kV/m", "250000 mV/m"],
            "cue_proof": 'Each rendering denotes the same electric-field value; the governing expression remains "E_base".',
            "context": "The field meter reports the electric field as {efield_render}.",
            "question": "What is that electric field in N/C?",
            "cue_sentence": "The field meter reports the electric field as {efield_render}.",
            "tags": ["circuits", "frame_rendering", "electric_field_units"],
        },
        {
            "template_id": "CM_C_015",
            "domain": "thermodynamics",
            "governing_law": "unit_rendering_temperature_difference",
            "equation_latex": r"\Delta T = \Delta T_{\mathrm{base}}",
            "equation_sympy": "deltaT_base",
            "target_quantity": "temperature_change_in_kelvin",
            "target_units": "K",
            "parameters": {"deltaT_base": {"value": 25.0, "units": "K", "description": "base temperature change"}},
            "answer": 25.0,
            "display": "25 K",
            "cue_name": "deltaT_render",
            "cue_desc": "Equivalent rendering of the same temperature-change quantity",
            "cue_values": ["25 K", "25 degC rise", "25000 mK", "0.025 kK"],
            "cue_proof": 'Each rendering denotes the same temperature change; the governing expression remains "deltaT_base".',
            "context": "The reported temperature rise is {deltaT_render}.",
            "question": "What is that temperature rise in kelvin?",
            "cue_sentence": "The reported temperature rise is {deltaT_render}.",
            "tags": ["thermodynamics", "frame_rendering", "temperature_difference_units"],
        },
    ]

    templates = []
    for index, spec in enumerate(specs, start=6):
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


def extreme_cue_b_templates() -> list[dict[str, Any]]:
    specs = [
        {
            "template_id": "CM_B_UM_061",
            "domain": "mechanics",
            "governing_law": "rotational_dynamics_torque_extreme_nearmatch",
            "equation_latex": r"\tau = rF",
            "equation_sympy": "r * F",
            "target_quantity": "torque_in_n_m",
            "target_units": "N*m",
            "parameters": {
                "r": {"value": 0.32, "units": "m", "description": "lever arm"},
                "F": {"value": 21.65, "units": "N", "description": "perpendicular force"},
            },
            "answer": 6.928,
            "display": "6.928 N*m",
            "cue_name": "torque_reading_B",
            "cue_desc": "Torque reading from an unrelated calibration rig",
            "cue_values": ["6.90", "6.92", "6.94", "6.96"],
            "cue_proof": "The calibration rig B torque is from a separate system and does not enter tau = rF for system A.",
            "context": "A wrench applies a perpendicular force of {F} N at a lever arm of {r} m. A separate calibration rig B lists an unrelated torque reading of {torque_reading_B} N*m.",
            "question": "What torque does the wrench exert on system A?",
            "cue_sentence": "A separate calibration rig B lists an unrelated torque reading of {torque_reading_B} N*m.",
            "tags": ["mechanics", "nongoverning_distractor", "torque", "extreme_nearmatch"],
        },
        {
            "template_id": "CM_B_UM_062",
            "domain": "mechanics",
            "governing_law": "hooke_force_extreme_nearmatch",
            "equation_latex": r"F = kx",
            "equation_sympy": "k * x",
            "target_quantity": "spring_force_in_n",
            "target_units": "N",
            "parameters": {
                "k": {"value": 204.0, "units": "N/m", "description": "spring constant"},
                "x": {"value": 0.12, "units": "m", "description": "extension"},
            },
            "answer": 24.48,
            "display": "24.48 N",
            "cue_name": "force_probe_B",
            "cue_desc": "Force reading from a separate load cell",
            "cue_values": ["24.42", "24.45", "24.50", "24.54"],
            "cue_proof": "The load-cell reading belongs to setup B and does not affect Hooke's law for spring A.",
            "context": "Spring A has spring constant {k} N/m and is stretched by {x} m. A separate load cell B reports {force_probe_B} N in an unrelated setup.",
            "question": "What is the restoring force magnitude for spring A?",
            "cue_sentence": "A separate load cell B reports {force_probe_B} N in an unrelated setup.",
            "tags": ["mechanics", "nongoverning_distractor", "hookes_law", "extreme_nearmatch"],
        },
        {
            "template_id": "CM_B_UM_063",
            "domain": "mechanics",
            "governing_law": "work_extreme_nearmatch",
            "equation_latex": r"W = Fd",
            "equation_sympy": "F * d",
            "target_quantity": "work_in_joules",
            "target_units": "J",
            "parameters": {
                "F": {"value": 7.8, "units": "N", "description": "constant force"},
                "d": {"value": 2.4, "units": "m", "description": "displacement"},
            },
            "answer": 18.72,
            "display": "18.72 J",
            "cue_name": "energy_meter_B",
            "cue_desc": "Energy readout from a separate meter",
            "cue_values": ["18.68", "18.70", "18.75", "18.80"],
            "cue_proof": "The separate meter reading belongs to system B and does not enter W = Fd for system A.",
            "context": "A constant force of {F} N acts parallel to a displacement of {d} m. A separate energy meter B displays {energy_meter_B} J for an unrelated process.",
            "question": "How much work is done on system A?",
            "cue_sentence": "A separate energy meter B displays {energy_meter_B} J for an unrelated process.",
            "tags": ["mechanics", "nongoverning_distractor", "work", "extreme_nearmatch"],
        },
        {
            "template_id": "TH_B_UM_011",
            "domain": "thermodynamics",
            "governing_law": "heat_transfer_extreme_nearmatch",
            "equation_latex": r"Q = mc\Delta T",
            "equation_sympy": "m * c * delta_T",
            "target_quantity": "heat_in_joules",
            "target_units": "J",
            "parameters": {
                "m": {"value": 0.2, "units": "kg", "description": "mass"},
                "c": {"value": 4186.0, "units": "J/(kg*K)", "description": "specific heat"},
                "delta_T": {"value": 2.0, "units": "K", "description": "temperature rise"},
            },
            "answer": 1674.4,
            "display": "1674.4 J",
            "cue_name": "heater_B",
            "cue_desc": "Heat readout from a separate insulated vessel",
            "cue_values": ["1670", "1672", "1676", "1680"],
            "cue_proof": "The separate vessel heat readout does not affect Q = mcΔT for system A.",
            "context": "Water sample A has mass {m} kg, specific heat {c} J/(kg*K), and temperature rise {delta_T} K. A separate insulated vessel B records {heater_B} J.",
            "question": "How much heat is added to sample A?",
            "cue_sentence": "A separate insulated vessel B records {heater_B} J.",
            "tags": ["thermodynamics", "nongoverning_distractor", "heat_transfer", "extreme_nearmatch"],
        },
        {
            "template_id": "TH_B_UM_012",
            "domain": "thermodynamics",
            "governing_law": "hydrostatic_pressure_extreme_nearmatch",
            "equation_latex": r"P = \rho g h",
            "equation_sympy": "rho * g * h",
            "target_quantity": "pressure_in_pascals",
            "target_units": "Pa",
            "parameters": {
                "rho": {"value": 1000.0, "units": "kg/m^3", "description": "fluid density"},
                "g": {"value": 9.8, "units": "m/s^2", "description": "gravitational acceleration"},
                "h": {"value": 0.12, "units": "m", "description": "depth"},
            },
            "answer": 1176.0,
            "display": "1176 Pa",
            "cue_name": "pressure_probe_B",
            "cue_desc": "Pressure from a separate reference column",
            "cue_values": ["1170", "1174", "1178", "1180"],
            "cue_proof": "The reference column belongs to system B and does not affect rho g h for fluid A.",
            "context": "Fluid A has density {rho} kg/m^3 and depth {h} m. A separate reference column B reports {pressure_probe_B} Pa.",
            "question": "What is the hydrostatic pressure of fluid A due to this depth?",
            "cue_sentence": "A separate reference column B reports {pressure_probe_B} Pa.",
            "tags": ["thermodynamics", "nongoverning_distractor", "pressure", "extreme_nearmatch"],
        },
    ]

    templates = []
    for index, spec in enumerate(specs, start=61):
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
                cue_slot=cue_b_slot(
                    name=spec["cue_name"],
                    description=spec["cue_desc"],
                    distractor_symbol=spec["cue_name"],
                    distractor_units=spec["target_units"],
                    value_labels=spec["cue_values"],
                    proof=spec["cue_proof"],
                ),
                prompt_context=spec["context"],
                prompt_question=spec["question"],
                cue_sentence=spec["cue_sentence"],
                topic_tags=spec["tags"],
                verification_tolerance=1e-3,
            )
        )
    return templates


def write_and_verify(templates: list[dict[str, Any]], output_dir: Path, verification_dir: Path) -> None:
    for payload in templates:
        domain = str(payload["domain"])
        cue_type = str(payload["cue_type"])
        template_id = str(payload["template_id"])
        template_path = output_dir / cue_type / domain / f"{template_id}.yaml"
        write_template(template_path, payload)
        verification = verify_template(template_path, verification_dir)
        set_verifier_certified(template_path, bool(verification["all_passed"]))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.verification_dir.mkdir(parents=True, exist_ok=True)

    cue_c_templates = cue_c_expansion_templates()
    cue_b_templates = extreme_cue_b_templates()
    write_and_verify(cue_c_templates, args.output_dir, args.verification_dir)
    write_and_verify(cue_b_templates, args.output_dir, args.verification_dir)
    summary = {
        "cue_c_candidate_count": len(cue_c_templates),
        "extreme_cue_b_candidate_count": len(cue_b_templates),
        "output_dir": str(args.output_dir),
        "verification_dir": str(args.verification_dir),
        "cue_c_template_ids": [payload["template_id"] for payload in cue_c_templates],
        "extreme_cue_b_template_ids": [payload["template_id"] for payload in cue_b_templates],
    }
    summary_path = args.verification_dir.parent / "expansion_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {len(cue_c_templates)} Cue C expansion templates and {len(cue_b_templates)} extreme Cue B templates.")


if __name__ == "__main__":
    main()
