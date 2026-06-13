"""Unit tests for the Stage 3 symbolic verifier."""

from __future__ import annotations

from pathlib import Path

from physmon.benchmark.verifier import SymbolicVerifier


def write_template(path: Path, *, answer_value: float = 5.0, answer_display: str = "5.0 m/s^2") -> None:
    """Write a minimal Stage 3 template YAML for verifier tests."""
    path.write_text(
        f"""
template_id: "CM_B_001"
domain: "mechanics"
cue_type: "nongoverning_distractor"
sequence: 1
governing_law: "newton_second_law_net_force"
governing_equation_latex: "a = F_{{net}} / m_A"
governing_equation_sympy: "F_net / m_A"
target_quantity: "acceleration_of_block_A"
target_units: "m/s^2"
parameters:
  F_net:
    value: 10.0
    units: "N"
    description: "net horizontal force on block A"
  m_A:
    value: 2.0
    units: "kg"
    description: "mass of block A"
correct_answer:
  value: {answer_value}
  units: "m/s^2"
  display: "{answer_display}"
  sympy_check: "abs((F_net / m_A) - 5.0) < 1e-9"
cue_slot:
  name: "m_B_display"
  description: "Mass of block B"
  type: "numerical"
  irrelevance_proof: null
  distractor_symbol: "m_B"
  distractor_units: "kg"
  nongoverning_proof: "m_B is absent from F_net / m_A."
  values:
    - id: 0
      value: "0.5"
      display: "0.5"
    - id: 1
      value: "1.0"
      display: "1.0"
    - id: 2
      value: "2.0"
      display: "2.0"
    - id: 3
      value: "3.0"
      display: "3.0"
  base_variant_id: 0
prompt_template:
  context: "Context"
  question: "Question"
  full_template: "Context\\n\\nQuestion"
  cue_span_is_whole_sentence: false
  cue_sentence: "Block B has mass {{m_B_display}} kg."
verifier:
  method: "sympy_numeric"
  sympy_check_code: "pass"
  cue_independence_method: "sympy_free_symbols"
validation:
  verifier_certified: false
  pi_validated: false
  v2_validated: false
  kappa_contribution: null
  exclusion_flags: []
  notes: ""
topic_tags: ["newton_second_law"]
difficulty: "introductory"
notes: ""
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_verifier_pass_template(tmp_path: Path) -> None:
    """A correct template should pass all verifier checks."""
    template_path = tmp_path / "pass.yaml"
    write_template(template_path)
    result = SymbolicVerifier().verify(str(template_path))
    assert result.all_passed is True


def test_verifier_detects_wrong_answer_value(tmp_path: Path) -> None:
    """A mismatched numeric answer should fail the correctness check."""
    template_path = tmp_path / "wrong_answer.yaml"
    write_template(template_path, answer_value=6.0)
    result = SymbolicVerifier().verify(str(template_path))
    failed_checks = {check.check_name for check in result.checks if not check.passed}
    assert "answer_correctness" in failed_checks


def test_verifier_detects_cue_symbol_leakage(tmp_path: Path) -> None:
    """Cue A/B independence should fail if the blocked symbol appears in the equation."""
    template_path = tmp_path / "cue_leak.yaml"
    write_template(template_path)
    text = template_path.read_text(encoding="utf-8").replace('"F_net / m_A"', '"F_net / m_A + m_B"')
    template_path.write_text(text, encoding="utf-8")
    result = SymbolicVerifier().verify(str(template_path))
    failed_checks = {check.check_name for check in result.checks if not check.passed}
    assert "cue_independence" in failed_checks


def test_verifier_detects_negative_mass(tmp_path: Path) -> None:
    """Negative masses should fail the physical plausibility check."""
    template_path = tmp_path / "negative_mass.yaml"
    write_template(template_path)
    text = template_path.read_text(encoding="utf-8").replace("value: 2.0\n    units: \"kg\"", "value: -2.0\n    units: \"kg\"", 1)
    template_path.write_text(text, encoding="utf-8")
    result = SymbolicVerifier().verify(str(template_path))
    failed_checks = {check.check_name for check in result.checks if not check.passed}
    assert "physical_plausibility" in failed_checks


def test_verifier_detects_unparseable_answer_string(tmp_path: Path) -> None:
    """An answer string outside parser coverage should fail parseability."""
    template_path = tmp_path / "bad_answer_string.yaml"
    write_template(template_path, answer_display="the acceleration is probably five")
    result = SymbolicVerifier().verify(str(template_path))
    failed_checks = {check.check_name for check in result.checks if not check.passed}
    assert "correct_answer_parseable" in failed_checks
