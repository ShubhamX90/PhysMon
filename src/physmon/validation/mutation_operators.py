"""Structured mutation operators for Stage 13 evidence-foundation audits.

These operators mutate template dictionaries that contain the PhysMon symbolic
template schema. They do not decide whether a mutation passed; the verifier must
be invoked on the mutated object by :mod:`physmon.validation.mutation_executor`.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import sympy


@dataclass(frozen=True)
class MutationApplication:
    """Result of applying one mutation operator to a structured template."""

    operator_id: str
    operator_type: str
    expected_verifier_result: str
    coverage_status: str
    mutation_applied: bool
    reason: str
    mutated_template: dict[str, Any] | None = None
    changed_fields: list[str] | None = None

    @property
    def status(self) -> str:
        """Backward-compatible alias used by earlier Stage 13 tests."""

        return self.coverage_status

    @property
    def expected_outcome(self) -> str:
        """Backward-compatible alias for the expected verifier result."""

        return self.expected_verifier_result


@dataclass(frozen=True)
class MutationOperator:
    """One concrete mutation that can be applied to a YAML template object."""

    operator_id: str
    operator_type: str
    description: str
    expected_verifier_result: str

    @property
    def expected_outcome(self) -> str:
        """Backward-compatible alias used by earlier Stage 13 tests."""

        return self.expected_verifier_result

    def apply(self, template: dict[str, Any]) -> MutationApplication:
        """Apply this operator if the template has the needed structure."""

        if self.operator_id == "sign_inversion_governing_expression":
            return self._sign_inversion(template)
        if self.operator_id == "replace_governing_variable_with_cue":
            return self._replace_governing_variable_with_cue(template)
        if self.operator_id == "negative_parameter_value":
            return self._negative_parameter_value(template)
        if self.operator_id == "incorrect_canonical_answer":
            return self._incorrect_canonical_answer(template)
        if self.operator_id == "cue_leakage_after_assumption_text_removal":
            return self._cue_leakage_after_assumption_text_removal(template)
        if self.operator_id == "true_unit_metadata_corruption":
            return self._true_unit_metadata_corruption(template)
        if self.operator_id == "algebraically_equivalent_expression":
            return self._algebraically_equivalent_expression(template)
        if self.operator_id == "semantics_preserving_variable_renaming":
            return self._variable_renaming(template)
        if self.operator_id == "equivalent_unit_formatting":
            return self._equivalent_unit_formatting(template)
        if self.operator_id == "harmless_serialization_formatting":
            return self._harmless_formatting(template)
        if self.operator_id == "exact_noop_control":
            mutated = self._base(template)
            return MutationApplication(
                self.operator_id,
                self.operator_type,
                self.expected_verifier_result,
                "executed_control",
                True,
                "Exact no-op control copied the structured object with metadata only.",
                mutated,
                ["stage13_mutation"],
            )
        return MutationApplication(
            self.operator_id,
            self.operator_type,
            self.expected_verifier_result,
            "coverage_not_supported",
            False,
            "Unknown mutation operator.",
        )

    def _base(self, template: dict[str, Any]) -> dict[str, Any]:
        mutated = deepcopy(template)
        mutated["stage13_mutation"] = {
            "operator_id": self.operator_id,
            "operator_type": self.operator_type,
            "description": self.description,
        }
        return mutated

    def _requires_equation(self, template: dict[str, Any]) -> str | None:
        expression = template.get("governing_equation_sympy")
        return str(expression) if expression not in {None, ""} else None

    def _sign_inversion(self, template: dict[str, Any]) -> MutationApplication:
        expression = self._requires_equation(template)
        if not expression:
            return self._unsupported("No governing_equation_sympy field.")
        mutated = self._base(template)
        mutated["governing_equation_sympy"] = f"-({expression})"
        return self._applied(mutated, ["governing_equation_sympy"])

    def _replace_governing_variable_with_cue(self, template: dict[str, Any]) -> MutationApplication:
        expression = self._requires_equation(template)
        cue_slot = template.get("cue_slot") or {}
        cue_symbol = cue_slot.get("distractor_symbol") or cue_slot.get("name")
        params = template.get("parameters") or {}
        if not expression or not cue_symbol or not params:
            return self._unsupported("Needs governing equation, cue symbol, and parameters.")
        parsed = sympy.sympify(expression, locals={name: sympy.Symbol(name) for name in params})
        symbols = sorted(symbol.name for symbol in parsed.free_symbols if symbol.name in params)
        if not symbols:
            return self._unsupported("No governing parameter symbols found in equation.")
        mutated = self._base(template)
        replaced = expression.replace(symbols[0], str(cue_symbol), 1)
        mutated.setdefault("parameters", deepcopy(params))[str(cue_symbol)] = {"value": "1.0", "units": cue_slot.get("distractor_units", ""), "description": "introduced cue parameter"}
        mutated["governing_equation_sympy"] = replaced
        return self._applied(mutated, ["governing_equation_sympy", f"parameters.{cue_symbol}"])

    def _negative_parameter_value(self, template: dict[str, Any]) -> MutationApplication:
        params = template.get("parameters") or {}
        if not params:
            return self._unsupported("No parameter table available.")
        name = next(iter(params))
        mutated = self._base(template)
        mutated["parameters"][name]["value"] = -abs(float(mutated["parameters"][name]["value"]))
        return self._applied(mutated, [f"parameters.{name}.value"])

    def _incorrect_canonical_answer(self, template: dict[str, Any]) -> MutationApplication:
        if "correct_answer" not in template or not isinstance(template["correct_answer"], dict):
            return self._unsupported("No structured correct_answer field.")
        value = template["correct_answer"].get("value")
        if value in {None, ""}:
            return self._unsupported("No numeric correct_answer.value field.")
        mutated = self._base(template)
        mutated["target_quantity"] = f"{template.get('target_quantity', 'target')}_changed"
        mutated["correct_answer"]["value"] = float(value) + 1.0
        mutated["correct_answer"]["display"] = f"{mutated['correct_answer']['value']} {mutated['correct_answer'].get('units', '')}".strip()
        return self._applied(mutated, ["target_quantity", "correct_answer.value", "correct_answer.display"])

    def _cue_leakage_after_assumption_text_removal(self, template: dict[str, Any]) -> MutationApplication:
        cue_slot = template.get("cue_slot") or {}
        proof_key = "nongoverning_proof" if cue_slot.get("nongoverning_proof") else "irrelevance_proof"
        if not cue_slot.get(proof_key):
            return self._unsupported("No explicit cue irrelevance/nongoverning proof field.")
        mutated = self._base(template)
        mutated["cue_slot"][proof_key] = ""
        # This deliberately also leaks the cue to make the loss of the assumption
        # machine-verifiable through the existing free-symbol checker.
        cue_symbol = cue_slot.get("distractor_symbol") or cue_slot.get("name")
        if cue_symbol:
            mutated.setdefault("parameters", {})[str(cue_symbol)] = {"value": "1.0", "units": cue_slot.get("distractor_units", ""), "description": "introduced cue after assumption removal"}
            mutated["governing_equation_sympy"] = f"({mutated['governing_equation_sympy']}) + {cue_symbol}"
        return self._applied(mutated, [f"cue_slot.{proof_key}", "governing_equation_sympy"])

    def _true_unit_metadata_corruption(self, template: dict[str, Any]) -> MutationApplication:
        params = template.get("parameters") or {}
        unit_swaps = {"kg": "s", "m": "kg", "V": "A", "J": "C", "Pa": "A", "N": "C", "s": "kg"}
        for name, spec in params.items():
            units = str(spec.get("units", ""))
            if units in unit_swaps:
                mutated = self._base(template)
                mutated["parameters"][name]["units"] = unit_swaps[units]
                return MutationApplication(
                    self.operator_id,
                    self.operator_type,
                    self.expected_verifier_result,
                    "unsupported_no_dimensional_checker",
                    False,
                    "Structured unit metadata can be altered, but the current SymbolicVerifier has no dimensional algebra checker to invoke; v6 records this as unsupported rather than a measured rejection.",
                    mutated,
                    [f"parameters.{name}.units"],
                )
        return MutationApplication(
            self.operator_id,
            self.operator_type,
            self.expected_verifier_result,
            "unsupported_no_dimensional_checker",
            False,
            "No supported structured unit field found, and no dimensional checker exists in SymbolicVerifier.",
        )

    def _algebraically_equivalent_expression(self, template: dict[str, Any]) -> MutationApplication:
        expression = self._requires_equation(template)
        if not expression:
            return self._unsupported("No governing_equation_sympy field.")
        mutated = self._base(template)
        mutated["governing_equation_sympy"] = f"({expression}) + 0"
        return self._applied(mutated, ["governing_equation_sympy"])

    def _variable_renaming(self, template: dict[str, Any]) -> MutationApplication:
        expression = self._requires_equation(template)
        params = template.get("parameters") or {}
        if not expression or not params:
            return self._unsupported("Needs equation and parameters.")
        first = next(iter(params))
        renamed = f"{first}_renamed"
        mutated = self._base(template)
        mutated["governing_equation_sympy"] = expression.replace(first, renamed)
        mutated["parameters"][renamed] = mutated["parameters"].pop(first)
        return self._applied(mutated, ["governing_equation_sympy", "parameters"])

    def _equivalent_unit_formatting(self, template: dict[str, Any]) -> MutationApplication:
        if "correct_answer" not in template or not isinstance(template["correct_answer"], dict):
            return self._unsupported("No structured correct_answer field.")
        units = str(template["correct_answer"].get("units", ""))
        mutated = self._base(template)
        mutated["correct_answer"]["display"] = f"{template['correct_answer'].get('value')} {units}".strip()
        return self._applied(mutated, ["correct_answer.display"])

    def _harmless_formatting(self, template: dict[str, Any]) -> MutationApplication:
        prompt_template = template.get("prompt_template")
        if not isinstance(prompt_template, dict) or "full_template" not in prompt_template:
            return self._unsupported("No prompt_template.full_template field.")
        mutated = self._base(template)
        mutated["prompt_template"]["full_template"] = str(mutated["prompt_template"]["full_template"]).replace("\n\n", "\n \n", 1)
        return self._applied(mutated, ["prompt_template.full_template"])

    def _unsupported(self, reason: str) -> MutationApplication:
        return MutationApplication(
            self.operator_id,
            self.operator_type,
            self.expected_verifier_result,
            "coverage_not_supported",
            False,
            reason,
        )

    def _applied(self, mutated: dict[str, Any], changed_fields: list[str]) -> MutationApplication:
        return MutationApplication(
            self.operator_id,
            self.operator_type,
            self.expected_verifier_result,
            "mutation_applied",
            True,
            "Structured object mutated; verifier execution required.",
            mutated,
            changed_fields,
        )


def default_mutation_operators() -> list[MutationOperator]:
    """Return the v6 operator set with names matching actual semantics."""

    return [
        MutationOperator("sign_inversion_governing_expression", "negative", "Invert the governing expression sign.", "reject"),
        MutationOperator("replace_governing_variable_with_cue", "negative", "Replace one governing variable with the cue symbol.", "reject"),
        MutationOperator("negative_parameter_value", "negative", "Negate one structured parameter value.", "reject"),
        MutationOperator("incorrect_canonical_answer", "negative", "Corrupt the stored canonical answer without changing prompt semantics.", "reject"),
        MutationOperator("cue_leakage_after_assumption_text_removal", "negative", "Remove cue proof text and leak cue into the expression; this tests cue leakage, not assumption sufficiency.", "reject"),
        MutationOperator("true_unit_metadata_corruption", "negative", "Attempt a true unit metadata corruption; unsupported without dimensional checker.", "reject"),
        MutationOperator("algebraically_equivalent_expression", "positive", "Add a neutral algebraic zero.", "accept"),
        MutationOperator("semantics_preserving_variable_renaming", "positive", "Rename one symbol consistently.", "accept"),
        MutationOperator("equivalent_unit_formatting", "positive", "Rewrite answer display while preserving value/unit.", "accept"),
        MutationOperator("harmless_serialization_formatting", "positive", "Change prompt serialization only.", "accept"),
        MutationOperator("exact_noop_control", "positive", "Exact no-op metadata-only control.", "accept"),
    ]
