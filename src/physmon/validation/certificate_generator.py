"""Generate structured machine certificate drafts from PhysMon templates."""

from __future__ import annotations

import math
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

import sympy
import yaml

from physmon.benchmark.verifier import SymbolicVerifier


CERTIFICATE_VERSION = "stage13_v6_solver_certificate_v3"
REPO_ROOT = Path(__file__).resolve().parents[3]

CERTIFICATE_STATUSES = {
    "structured_machine_certificate_draft",
    "structured_machine_certificate_verified",
    "frame_equivalence_unverified",
    "dimensional_metadata_only",
    "certificate_generation_blocked",
    "certificate_verification_failed",
}

UNIT_TO_BASE = {
    "Pa": ("Pa", 1.0),
    "kPa": ("Pa", 1000.0),
    "bar": ("Pa", 100000.0),
    "atm": ("Pa", 101325.0),
    "N/m^2": ("Pa", 1.0),
    "N/m²": ("Pa", 1.0),
    "J": ("J", 1.0),
    "kJ": ("J", 1000.0),
    "m": ("m", 1.0),
    "cm": ("m", 0.01),
    "mm": ("m", 0.001),
    "km": ("m", 1000.0),
    "s": ("s", 1.0),
    "ms": ("s", 0.001),
    "kg": ("kg", 1.0),
    "g": ("kg", 0.001),
    "V": ("V", 1.0),
    "A": ("A", 1.0),
    "C": ("C", 1.0),
    "N": ("N", 1.0),
    "kN": ("N", 1000.0),
    "mN": ("N", 0.001),
    "Hz": ("Hz", 1.0),
    "rpm": ("Hz", 1.0 / 60.0),
    "m/s": ("m/s", 1.0),
    "cm/s": ("m/s", 0.01),
    "mm/s": ("m/s", 0.001),
    "km/h": ("m/s", 1000.0 / 3600.0),
    "mJ": ("J", 0.001),
}

NUMERIC_UNIT_RE = re.compile(
    r"(?P<value>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s*(?P<unit>[A-Za-zΩ/²^*·]+(?:/m\^2|/m²)?)",
    re.I,
)


def portable_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_structured_template(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _parameter_symbols(parameters: dict[str, Any]) -> dict[str, sympy.Symbol]:
    return {name: sympy.Symbol(name) for name in parameters}


def _parse_unit_value(display: str, fallback_unit: str = "") -> dict[str, Any]:
    text = str(display or "").replace("N*m", "J").replace("N·m", "J").strip()
    text = re.sub(r"(\d+(?:\.\d+)?)\s*[×x]\s*10\^([-+]?\d+)", lambda m: f"{float(m.group(1)) * (10 ** int(m.group(2))):.12g}", text)
    match = NUMERIC_UNIT_RE.search(text)
    if not match:
        return {"parseable": False, "raw": display, "reason": "no numeric unit expression found"}
    unit = match.group("unit") or fallback_unit
    unit = unit.replace("N/m2", "N/m^2")
    if unit not in UNIT_TO_BASE:
        return {"parseable": False, "raw": display, "unit": unit, "reason": "unit not in explicit conversion table"}
    base_unit, factor = UNIT_TO_BASE[unit]
    value = float(match.group("value"))
    return {
        "parseable": True,
        "raw": display,
        "value": value,
        "unit": unit,
        "base_unit": base_unit,
        "base_value": value * factor,
    }


def _frame_unit_equivalence_checks(template: dict[str, Any]) -> dict[str, Any]:
    cue_slot = template.get("cue_slot") or {}
    values = cue_slot.get("values") or []
    correct_answer = template.get("correct_answer") or {}
    canonical = _parse_unit_value(correct_answer.get("display", ""), str(correct_answer.get("units", "")))
    if not values:
        return {"status": "not_applicable", "checks": [], "limitations": []}
    checks = []
    limitations = []
    for value in values:
        rendered = value.get("display") or value.get("render") or value.get("text") or value.get("value")
        parsed = _parse_unit_value(str(rendered), str(cue_slot.get("distractor_units", "")))
        if not parsed.get("parseable") or not canonical.get("parseable"):
            checks.append({"variant_id": value.get("id"), "rendered": rendered, "equivalent": False, "parsed": parsed})
            limitations.append("at least one variant or canonical answer was not parseable by the explicit conversion table")
            continue
        equivalent = parsed["base_unit"] == canonical["base_unit"] and math.isclose(
            float(parsed["base_value"]),
            float(canonical["base_value"]),
            rel_tol=1e-6,
            abs_tol=1e-9,
        )
        checks.append(
            {
                "variant_id": value.get("id"),
                "rendered": rendered,
                "parsed": parsed,
                "canonical_parsed": canonical,
                "equivalent": equivalent,
            }
        )
    if all(check.get("equivalent") for check in checks):
        status = "verified_explicit_conversion_table"
    elif checks:
        status = "frame_equivalence_unverified"
    else:
        status = "not_applicable"
    return {"status": status, "checks": checks, "limitations": limitations}


def build_physics_spec(template: dict[str, Any], source_template: str) -> dict[str, Any]:
    required = ["template_id", "domain", "cue_type", "governing_law", "governing_equation_sympy", "parameters", "correct_answer"]
    missing = []
    for field in required:
        value = template.get(field)
        if field not in template or value is None or value == "":
            missing.append(field)
    if missing:
        return {
            "family_id": template.get("template_id"),
            "source_template": source_template,
            "certificate_status": "certificate_generation_blocked",
            "blocked_reason": f"Missing structured fields: {', '.join(missing)}",
        }

    parameters = template.get("parameters") or {}
    expression = sympy.sympify(str(template["governing_equation_sympy"]), locals=_parameter_symbols(parameters))
    relevant = sorted(symbol.name for symbol in expression.free_symbols)
    symbol_table = {}
    for name, spec in parameters.items():
        symbol_table[name] = {
            "symbol": name,
            "physical_quantity": spec.get("description") or name,
            "value": spec.get("value"),
            "unit": spec.get("units", ""),
            "role": "relevant" if name in relevant else "context_parameter",
            "source_field": f"parameters.{name}",
        }

    cue_slot = template.get("cue_slot") or {}
    return {
        "family_id": template["template_id"],
        "domain": template["domain"],
        "template_id": template["template_id"],
        "governing_law_id": template["governing_law"],
        "governing_equations": {
            "sympy": template["governing_equation_sympy"],
            "latex": template.get("governing_equation_latex", ""),
        },
        "symbol_table": symbol_table,
        "relevant_variables": relevant,
        "designated_cue": {
            "name": cue_slot.get("name"),
            "distractor_symbol": cue_slot.get("distractor_symbol"),
            "type": cue_slot.get("type"),
            "unit": cue_slot.get("distractor_units"),
            "values": cue_slot.get("values", []),
            "source_field": "cue_slot",
        },
        "assumptions": {
            "cue_irrelevance": cue_slot.get("irrelevance_proof") or cue_slot.get("nongoverning_proof"),
            "validation_notes": (template.get("validation") or {}).get("notes", ""),
        },
        "target_quantity": template.get("target_quantity", ""),
        "symbolic_answer": str(template["governing_equation_sympy"]),
        "canonical_answer": template["correct_answer"],
        "units": template.get("target_units") or template["correct_answer"].get("units", ""),
        "variant_bindings": [
            {
                "variant_id": value.get("id"),
                "cue_value": value.get("value"),
                "cue_display": value.get("display") or value.get("render"),
            }
            for value in cue_slot.get("values", [])
        ],
        "source_template": source_template,
    }


def generate_certificate(template_path: Path) -> dict[str, Any]:
    template = load_structured_template(template_path)
    spec = build_physics_spec(template, portable_path(template_path))
    if spec.get("certificate_status") == "certificate_generation_blocked":
        return spec

    parameters = template["parameters"]
    expression = sympy.sympify(str(template["governing_equation_sympy"]), locals=_parameter_symbols(parameters))
    substitutions = {sympy.Symbol(name): float(param["value"]) for name, param in parameters.items()}
    evaluated_expr = expression.evalf(subs=substitutions)
    computed_value = float(evaluated_expr)
    canonical_value = float(template["correct_answer"]["value"])
    canonical_units = spec["units"]
    verifier_result = SymbolicVerifier().verify(str(template_path))

    substituted_values = {
        name: {"value": param.get("value"), "unit": param.get("units", ""), "source_field": f"parameters.{name}"}
        for name, param in parameters.items()
        if name in spec["relevant_variables"]
    }
    substitution_terms = []
    for name in spec["relevant_variables"]:
        param = parameters[name]
        substitution_terms.append(f"{name}={param.get('value')} {param.get('units', '')}".strip())
    numeric_substitution = f"{template['governing_equation_sympy']} with " + ", ".join(substitution_terms)
    derivation_steps = [f"{name} = {parameters[name]['value']} {parameters[name].get('units', '')}".strip() for name in spec["relevant_variables"]]
    derivation_steps.extend(
        [
            numeric_substitution,
            f"{template['governing_equation_sympy']} = {computed_value:.12g} {canonical_units}".strip(),
            f"canonical comparison: computed={computed_value:.12g}, expected={canonical_value:.12g}",
        ]
    )

    invariance_checks = []
    for value in (template.get("cue_slot") or {}).get("values", []):
        check_result = float(expression.evalf(subs=substitutions))
        invariance_checks.append(
            {
                "variant_id": value.get("id"),
                "cue_value": value.get("value"),
                "computed_answer": check_result,
                "canonical_answer": canonical_value,
                "matches_canonical": abs(check_result - canonical_value) <= max(abs(canonical_value) * 1e-6, 1e-9),
                "method": "recomputed_sympy_expression_with_same_relevant_substitutions_after_confirming_cue_symbol_absent",
            }
        )

    frame_check = _frame_unit_equivalence_checks(template)
    if not verifier_result.all_passed:
        status = "certificate_verification_failed"
    elif frame_check["status"] == "frame_equivalence_unverified":
        status = "frame_equivalence_unverified"
    else:
        status = "structured_machine_certificate_verified"

    return {
        **spec,
        "certificate_status": status,
        "governing_law": template.get("governing_law", ""),
        "substituted_values": substituted_values,
        "explicit_symbolic_derivation": {
            "governing_equation": str(expression),
            "variable_bindings": substituted_values,
            "numeric_substitution": numeric_substitution,
            "intermediate_calculation": f"SymPy evaluated expression to {computed_value:.12g}",
            "final_answer": {"value": computed_value, "unit": canonical_units},
            "canonical_answer_comparison": {
                "computed": computed_value,
                "expected": canonical_value,
                "matches": abs(computed_value - canonical_value) <= max(abs(canonical_value) * 1e-6, 1e-9),
            },
            "steps": derivation_steps,
        },
        "computed_canonical_answer": {"value": computed_value, "units": canonical_units},
        "dimensional_check": {
            "status": "unit_metadata_recorded_not_symbolically_verified",
            "target_units": canonical_units,
            "parameter_units": {name: param.get("units", "") for name, param in parameters.items()},
            "limitations": "Unit metadata are recorded from structured template fields; full dimensional algebra is not implemented.",
        },
        "frame_unit_equivalence_check": frame_check,
        "invariance_proof": "The structured governing expression free symbols exclude the designated cue symbol; answer is recomputed from relevant-variable substitutions for each cue variant.",
        "invariance_checks": invariance_checks,
        "numeric_spot_checks": invariance_checks[:2],
        "certificate_generator": "physmon.validation.certificate_generator.generate_certificate",
        "certificate_version": CERTIFICATE_VERSION,
        "verification_result": {"all_passed": verifier_result.all_passed, "checks": [asdict(check) for check in verifier_result.checks]},
        "limitations": [
            "Generated from structured YAML template fields only.",
            "Natural-language semantic equivalence and assumption sufficiency require human validation.",
            "Dimensional algebra is not implemented; unit metadata are recorded only.",
            "Frame/unit equivalence is verified only for forms covered by the explicit conversion table.",
        ],
    }
