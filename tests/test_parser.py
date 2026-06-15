"""Unit tests for the deterministic Stage 1 answer parser."""

from __future__ import annotations

import logging

import pytest

from physmon.benchmark.parser import parse_answer


@pytest.mark.parametrize(
    ("raw_output", "expected_answer", "expected_type"),
    [
        ("9.8", "9.8", "numeric"),
        ("9.8 m/s^2", "9.8 m/s^2", "numeric"),
        ("9.8 m s^{-2}", "9.8 ms^-2", "numeric"),
        ("≈ 9.8", "9.8", "numeric"),
        ("~9.8", "9.8", "numeric"),
        ("-3.20e-1 N", "-0.32 N", "numeric"),
        ("42.", "42", "numeric"),
        ("\\boxed{9.8}", "9.8", "numeric"),
        ("\\boxed{mv^2/2r}", "mv^2/2r", "symbolic"),
        ("The answer is 9.8 m/s^2.", "9.8 m/s^2", "numeric"),
        ("Final answer: 9.8", "9.8", "numeric"),
        ("Answer = 9.8", "9.8", "numeric"),
        ("Thus, 9.8 m/s^2", "9.8 m/s^2", "numeric"),
        ("Therefore, mv^2/(2r)", "mv^2/(2r)", "symbolic"),
        ("We compute many steps.\nFinal answer: \\boxed{9.8}", "9.8", "numeric"),
        ("Some reasoning\n9.8 m/s^2", "9.8 m/s^2", "numeric"),
        ("v = 9.8 m/s^2", "9.8 m/s^2", "numeric"),
        ("F = ma", "ma", "symbolic"),
        ("mv²/2r", "mv^2/2r", "symbolic"),
        ("mv^2/(2r)", "mv^2/(2r)", "symbolic"),
        ("\\frac{mv^2}{2r}", "(mv^2)/(2r)", "symbolic"),
        ("\\left(\\frac{mv^2}{2r}\\right)", "(mv^2)/(2r)", "symbolic"),
        ("\\boxed{\\frac{1}{2}mv^2}", "(1)/(2)mv^2", "symbolic"),
        ("9.8000", "9.8", "numeric"),
        ("$9.8\\,\\mathrm{m/s^2}$", "9.8 m/s^2", "numeric"),
        ("  '9.8 m/s^2.'  ", "9.8 m/s^2", "numeric"),
        ("Answer: .25 A", "0.25 A", "numeric"),
        ("The final answer is 1E+03 J", "1000 J", "numeric"),
        ("Reasoning...\n\n\\boxed{12 kg}", "12 kg", "numeric"),
        ("There are steps here.\n\nmv^2/2r", "mv^2/2r", "symbolic"),
        ("Answer: x = .5", "0.5", "numeric"),
        ("Final answer: 1.23456", "1.235", "numeric"),
        ("Answer: 11.0 m/s", "11 m/s", "numeric"),
        ("answer: **11.0 m/s**.", "11 m/s", "numeric"),
        ("Work...\nAnswer: **1.2e-3 C**", "0.0012 C", "numeric"),
        ("Answer: 1.2 × 10^-3 C", "0.0012 C", "numeric"),
        ("Answer: 1.2×10⁻³ C", "0.0012 C", "numeric"),
        ("Answer: 8.99 × 10^9 N·m²/C²", "8.99e9 N*m^2/C^2", "numeric"),
        ("Some work\nAnswer: 11.0 m s^-1", "11 ms^-1", "numeric"),
        ("The final velocity is 11.0 m/s", "11 m/s", "numeric"),
        ("v_final = 11.0 m/s", "11 m/s", "numeric"),
        ("Answer: **50 μF**", "50 μF", "numeric"),
    ],
)
def test_parse_answer_success_cases(
    raw_output: str, expected_answer: str, expected_type: str
) -> None:
    """The parser should normalize the common answer patterns used in Stage 1."""
    result = parse_answer(raw_output)
    assert result.is_confident is True
    assert result.answer == expected_answer
    assert result.answer_type == expected_type


@pytest.mark.parametrize(
    "raw_output",
    [
        "",
        "   ",
        "I don't know.",
        "Cannot determine from the prompt.",
        "Sorry, I can't answer that.",
        "The values could be 9.8 or 10.1 depending on interpretation.",
        "Answers: 9.8; 10.1",
        "This problem discusses acceleration, force, and units but never commits to a final answer.",
        "Final line is a long prose summary rather than an answer to extract reliably.",
        "The quantities are 5 m and 7 s.",
    ],
)
def test_parse_answer_failure_cases(raw_output: str) -> None:
    """Ambiguous or refusal-like generations should not produce canonical answers."""
    result = parse_answer(raw_output)
    assert result.answer is None
    assert result.is_confident is False


def test_failed_parse_logs_raw_output_snippet(caplog: pytest.LogCaptureFixture) -> None:
    """Failed parses must be logged for later audit."""
    caplog.set_level(logging.WARNING)
    result = parse_answer("This prose never provides a clean final answer at all.")
    assert result.answer is None
    assert "Failed to parse answer" in caplog.text


def test_scientific_notation_is_not_treated_as_multi_answer() -> None:
    """Scientific notation should remain a single numeric answer."""
    result = parse_answer("Final answer: 1.2e-3 A")
    assert result.answer == "0.0012 A"
    assert result.is_confident is True


def test_low_confidence_final_line_is_rejected() -> None:
    """Long fallback lines should stay below the confidence threshold."""
    result = parse_answer(
        "After a long derivation, the final quantity should be approximately the usual result for acceleration."
    )
    assert result.answer is None
    assert result.is_confident is False


def test_bare_numeric_fallback_uses_expected_unit() -> None:
    """A unique bare number on the final line can inherit units from template metadata."""
    result = parse_answer("After solving the problem carefully,\nAnswer: 11.0", expected_unit="m/s")
    assert result.answer == "11 m/s"
    assert result.is_confident is True


def test_bare_numeric_fallback_rejects_multiple_last_line_numbers() -> None:
    """The expected-unit fallback should refuse ambiguous final lines."""
    result = parse_answer("Final values: 11.0 and 12.0", expected_unit="m/s")
    assert result.answer is None
    assert result.is_confident is False


def test_latex_wrapped_numeric_answer_gets_canonicalized() -> None:
    """LaTeX-wrapped numeric answers should compare canonically with plain-text equivalents."""
    result = parse_answer("\\(5.0m/s^2\\)")
    assert result.display_answer == "5.0 m/s^2"
    assert result.answer == "5 m/s^2"
    assert result.is_confident is True


@pytest.mark.parametrize("raw_output", ["themagnitude", "thevelocity is high"])
def test_digit_free_garbage_is_rejected(raw_output: str) -> None:
    """Digit-free garbage spans must not survive the parser fallback path."""
    result = parse_answer(raw_output)
    assert result.answer is None
    assert result.is_confident is False


def test_latex_text_and_cdot_display_answer_normalization() -> None:
    """LaTeX text/unit wrappers should collapse into a readable display answer."""
    result = parse_answer("the answer is \\[14\\, \\text{kg}\\cdot\\text{m/s}\\]")
    assert result.display_answer == "14 kg*m/s"
    assert result.answer == "14 kg*m/s"
    assert result.is_confident is True


@pytest.mark.parametrize(
    ("raw_output", "expected_unit"),
    [
        ("2.0 A (this does not affect the calculation for circuit A)", "A"),
        ("\\(\\sin(90^\\circ)=1\\).", "N*m"),
        ("\\frac{1}{2\\pi}", "Hz"),
        ("v/\\lambda", "Hz"),
    ],
)
def test_expected_unit_rejects_intermediate_math_or_prose(
    raw_output: str, expected_unit: str
) -> None:
    """Template metadata with expected units should not let formula fragments pass as answers."""
    result = parse_answer(raw_output, expected_unit=expected_unit)
    assert result.answer is None
    assert result.is_confident is False
