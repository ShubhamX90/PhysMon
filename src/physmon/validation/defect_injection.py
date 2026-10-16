"""Typed planted-defect injection for validator qualification (Stage 14.5; v2 B4.4, p.10).

Each rule edits a rendered DECOY-v1 family (or its encoded equation / displayed answer) in one declared way so a
reviewer's detection of that defect can be measured. The rules are deterministic text transformations. They are
candidates: a physicist must confirm that each planted item is actually defective for its declared reason and
that each control is actually valid before the bank is used (the agent cannot certify this).

Defect types are the predeclared list in v2 B4.4: hidden coupling, missing assumption, relevant variable removed
from the equation, failed transformation identity, inconsistent units, invalid parameter domain, insufficient
boundary condition, invalid numerical precision, contradictory distractor statement, and a valid equivalent
rewrite (the positive control). The planted bank never enters the benchmark as genuine physics.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

DEFECT_TYPES = (
    "hidden_coupling",
    "missing_assumption",
    "relevant_variable_removed_from_equation",
    "failed_transformation_identity",
    "inconsistent_units",
    "invalid_parameter_domain",
    "insufficient_boundary_condition",
    "invalid_numerical_precision",
    "contradictory_distractor_statement",
    "valid_equivalent_rewrite",
)
CONTROL = "valid_equivalent_rewrite"
# Defects a reviewer can only see when shown the encoded equation or the certified answer (Pass 2).
PASS2_ONLY = ("relevant_variable_removed_from_equation", "invalid_numerical_precision")


@dataclass
class Injection:
    """Result of applying one rule to one family."""

    defect_type: str
    applicable: bool
    edited_prompts: list[str] = field(default_factory=list)
    edited_equation: str | None = None
    edited_answer: str | None = None
    description: str = ""

    @property
    def expected_verdict(self) -> str:
        return "valid" if self.defect_type == CONTROL else "invalid"

    @property
    def detectable_in(self) -> str:
        return "pass2" if self.defect_type in PASS2_ONLY else "pass1"


def _not_applicable(defect_type: str, reason: str) -> Injection:
    return Injection(defect_type=defect_type, applicable=False, description=reason)


def _prompts(family: Mapping[str, Any]) -> list[str]:
    variants = sorted(family["variants"], key=lambda v: int(v["variant_id"]))
    return [str(v["prompt"]) for v in variants]


def _apply_all(prompts: Sequence[str], pattern: str, repl: str | Any, flags: int = 0) -> list[str] | None:
    """Apply a substitution to every variant; None unless every variant changes."""

    edited = [re.sub(pattern, repl, p, count=1, flags=flags) for p in prompts]
    return edited if all(a != b for a, b in zip(edited, prompts, strict=True)) else None


def hidden_coupling(family: Mapping[str, Any], template: Mapping[str, Any] | None = None) -> Injection:
    edited = _apply_all(_prompts(family), r"\bisolated from\b", "coupled to")
    if edited is None:
        return _not_applicable("hidden_coupling", "no 'isolated from' clause in every variant")
    return Injection("hidden_coupling", True, edited,
                     description="'isolated from' replaced by 'coupled to': the distractor subsystem now "
                                 "interacts with the target system")


# Templates where deleting the named idealisation makes the target underdetermined. Chosen by reading each
# governing equation (journal J14.5-003): the ramp speed sqrt(2 g h) needs a frictionless ramp, and the ideal-gas
# pressure needs an ideal gas. Elsewhere the prompt gives the acceleration or force directly, so deleting
# 'frictionless' would not make the problem unsolvable and would not be a real defect.
ASSUMPTION_CRITICAL: dict[str, str] = {
    "CM_B_UM_047": r"frictionless ",
    "TH_B_UM_006": r"ideal ",
    "TH_B_UM_007": r"ideal ",
    "TH_B_UM_008": r"ideal ",
}


def missing_assumption(family: Mapping[str, Any], template: Mapping[str, Any] | None = None) -> Injection:
    pattern = ASSUMPTION_CRITICAL.get(str(family.get("template_id")))
    if pattern is None:
        return _not_applicable("missing_assumption", "not a template where the assumption is needed")
    edited = _apply_all(_prompts(family), pattern, "")
    if edited is None:
        return _not_applicable("missing_assumption", "qualifier not present in every variant")
    return Injection("missing_assumption", True, edited,
                     description="a needed idealisation (frictionless ramp or ideal gas) was deleted, so the "
                                 "governing law no longer follows from the stated assumptions")


def relevant_variable_removed_from_equation(family, template=None) -> Injection:
    if not template:
        return _not_applicable("relevant_variable_removed_from_equation", "no template")
    import sympy

    equation = str(template["governing_equation_sympy"])
    parameters = {k: float(v["value"]) for k, v in template["parameters"].items()
                  if isinstance(v.get("value"), (int, float))}
    names = [n for n in parameters if re.search(rf"\b{re.escape(n)}\b", equation)]
    try:
        original_value = float(sympy.sympify(equation).subs(parameters))
    except (TypeError, sympy.SympifyError):
        return _not_applicable("relevant_variable_removed_from_equation",
                               "the equation does not evaluate to a number from the template parameters")
    for name in names:
        edited = re.sub(rf"\b{re.escape(name)}\b", "1", equation, count=1)
        try:
            edited_value = float(sympy.sympify(edited).subs({k: v for k, v in parameters.items() if k != name}))
        except (TypeError, sympy.SympifyError):
            continue
        if not math.isclose(original_value, edited_value, rel_tol=1e-6):
            return Injection(
                "relevant_variable_removed_from_equation", True, _prompts(family), edited_equation=edited,
                description=f"parameter '{name}' replaced by 1 in the displayed governing equation; the "
                            f"edited equation evaluates to {edited_value:.6g} against the certified "
                            f"{original_value:.6g}")
    return _not_applicable("relevant_variable_removed_from_equation",
                           "no parameter whose removal changes the evaluated answer")


def failed_transformation_identity(family, template=None) -> Injection:
    if str(family.get("cue_type")) != "frame_rendering":
        return _not_applicable("failed_transformation_identity", "not a frame/unit rendering family")
    variants = sorted(family["variants"], key=lambda v: int(v["variant_id"]))
    target = next((v for v in variants if int(v["variant_id"]) == 1), None)
    if target is None:
        return _not_applicable("failed_transformation_identity", "no rendering with id 1")
    cue, prompt = str(target.get("cue_sentence") or ""), str(target["prompt"])
    match = re.search(r"\d+(?:\.\d+)?", cue)
    if not cue or not match or cue not in prompt:
        return _not_applicable("failed_transformation_identity", "no numeric cue sentence in rendering 1")
    scaled = float(match.group()) * 1.1
    new_cue = cue[:match.start()] + f"{scaled:.4g}" + cue[match.end():]
    prompts = [str(v["prompt"]) for v in variants]
    prompts[variants.index(target)] = prompt.replace(cue, new_cue, 1)
    return Injection("failed_transformation_identity", True, prompts,
                     description="the number in rendering 1's cue sentence was multiplied by 1.1, so rendering 1 "
                                 "no longer denotes the same quantity as the other three")


def inconsistent_units(family, template=None) -> Injection:
    edited = _apply_all(_prompts(family), r"(\d+(?:\.\d+)?\s*)kg\b", r"\1m")
    if edited is None:
        return _not_applicable("inconsistent_units", "no '<number> kg' quantity in every variant")
    return Injection("inconsistent_units", True, edited,
                     description="the first '<number> kg' became '<number> m': a mass given in metres")


def invalid_parameter_domain(family, template=None) -> Injection:
    pattern = r"(?<![\w.\-])(\d+(?:\.\d+)?)(\s*(?:kg|mol)\b)"
    edited = _apply_all(_prompts(family), pattern, r"-\1\2")
    if edited is None:
        return _not_applicable("invalid_parameter_domain", "no mass or amount-of-substance quantity")
    return Injection("invalid_parameter_domain", True, edited,
                     description="the first mass or amount of substance was made negative (a temperature "
                                 "difference is deliberately not used: a negative change is valid)")


# Initial conditions that the governing law needs (journal J14.5-003). CM_A_008 is excluded on purpose: it restates
# 'initially at rest (0.0 m/s)', so deleting the words would leave the value in place and not be a defect.
BOUNDARY_EDITS: dict[str, tuple[str, str]] = {
    "CM_B_009": (r",\s*which is initially at rest", ""),
    "CM_B_UM_011": (r"dropped from rest and falls", "dropped and falls"),
    "CM_B_UM_047": (r"starts from rest and descends", "descends"),
}


def insufficient_boundary_condition(family, template=None) -> Injection:
    rule = BOUNDARY_EDITS.get(str(family.get("template_id")))
    if rule is None:
        return _not_applicable("insufficient_boundary_condition", "no needed initial condition to delete")
    edited = _apply_all(_prompts(family), rule[0], rule[1])
    if edited is None:
        return _not_applicable("insufficient_boundary_condition", "initial-condition phrase not in every variant")
    return Injection("insufficient_boundary_condition", True, edited,
                     description="a needed initial condition (the 'at rest' or 'from rest' statement) was deleted")


def invalid_numerical_precision(family, template=None) -> Injection:
    answer = str(family.get("correct_answer", ""))
    match = re.match(r"^(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s+(.+)$", answer)
    if not match:
        return _not_applicable("invalid_numerical_precision", "answer is not '<value> <unit>'")
    value = float(match.group(1))
    if value == 0:
        return _not_applicable("invalid_numerical_precision", "zero answer")
    rounded = float(f"{value:.1g}")
    if abs(rounded - value) / abs(value) < 0.05:
        return _not_applicable("invalid_numerical_precision",
                               "one significant figure is within 5%: not a clear defect")
    return Injection("invalid_numerical_precision", True, _prompts(family),
                     edited_answer=f"{rounded:g} {match.group(2)}",
                     description=f"the certified answer {answer} is shown rounded to one significant figure "
                                 f"({rounded:g}), a {abs(rounded - value) / abs(value):.1%} error")


def contradictory_distractor_statement(family, template=None) -> Injection:
    variants = sorted(family["variants"], key=lambda v: int(v["variant_id"]))
    prompts = []
    for variant in variants:
        cue, value, prompt = (str(variant.get("cue_sentence") or ""), str(variant.get("cue_value", "")),
                              str(variant["prompt"]))
        try:
            number = float(value)
        except ValueError:
            return _not_applicable("contradictory_distractor_statement", "non-numeric cue value")
        if not cue or cue not in prompt:
            return _not_applicable("contradictory_distractor_statement", "no cue sentence in every variant")
        unit_match = re.search(re.escape(value) + r"\s+([^\s,.;()]+)", cue)
        unit = f" {unit_match.group(1)}" if unit_match else ""
        extra = f" (A later note reports this same quantity as {number * 2:g}{unit} instead.)"
        prompts.append(prompt.replace(cue, cue + extra, 1))
    return Injection("contradictory_distractor_statement", True, prompts,
                     description="a later sentence restates the cue quantity, with its unit, at twice the value")


def valid_equivalent_rewrite(family, template=None) -> Injection:
    edited = _apply_all(_prompts(family), r"What is the (.+?)\?\s*$", r"Determine the \1.")
    if edited is None:
        return _not_applicable(CONTROL, "question is not of the form 'What is the ...?'")
    return Injection(CONTROL, True, edited,
                     description="'What is the X?' reworded as 'Determine the X.'; meaning, numbers and units "
                                 "are unchanged")


RULES = {
    "hidden_coupling": hidden_coupling,
    "missing_assumption": missing_assumption,
    "relevant_variable_removed_from_equation": relevant_variable_removed_from_equation,
    "failed_transformation_identity": failed_transformation_identity,
    "inconsistent_units": inconsistent_units,
    "invalid_parameter_domain": invalid_parameter_domain,
    "insufficient_boundary_condition": insufficient_boundary_condition,
    "invalid_numerical_precision": invalid_numerical_precision,
    "contradictory_distractor_statement": contradictory_distractor_statement,
    CONTROL: valid_equivalent_rewrite,
}


def inject(defect_type: str, family: Mapping[str, Any], template: Mapping[str, Any] | None = None) -> Injection:
    if defect_type not in RULES:
        raise KeyError(f"unknown defect type {defect_type!r}; expected one of {list(DEFECT_TYPES)}")
    return RULES[defect_type](family, template)


def numbers_in(text: str) -> list[str]:
    """All numeric tokens in a text, used to show a control preserves every number."""

    return re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)
