"""Deterministic answer parsing and normalization for PhysMon.

Reference: Part III.3 of the implementation brief and `physmon_proposal.pdf` §3.3,
where answer-flip sensitivity depends on canonicalized final answers.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re


LOGGER = logging.getLogger(__name__)

DEFAULT_SIGNIFICANT_FIGURES = 4
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
FAILED_PARSE_SNIPPET_LENGTH = 160
BOXED_CONFIDENCE = 0.99
EXPLICIT_CONFIDENCE = 0.96
FINAL_LINE_CONFIDENCE = 0.84
LOW_CONFIDENCE_FALLBACK = 0.60

EMPTY_OUTPUT_PATTERNS = (
    "",
    "n/a",
    "none",
)
REFUSAL_PATTERNS = (
    "i don't know",
    "i do not know",
    "cannot determine",
    "can't determine",
    "insufficient information",
    "cannot answer",
    "can't answer",
    "not enough information",
    "sorry",
)
EXPLICIT_ANSWER_PATTERNS = (
    r"(?:final\s+answer|answer)\s*(?:is|=|:)\s*(?P<answer>.+)",
    r"thus[, ]+(?P<answer>.+)",
    r"therefore[, ]+(?P<answer>.+)",
)
BOXED_PATTERN = re.compile(r"\\boxed\s*\{(?P<content>.+)\}", re.DOTALL)
LATEX_FRACTION_PATTERN = re.compile(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
NUMERIC_PATTERN = re.compile(
    r"^[~=≈\s]*"
    r"(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?:\s*(?P<unit>.*))?$"
)
ASSIGNMENT_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*\s*=\s*(?P<rhs>.+)$")
UNIT_LATEX_PATTERN = re.compile(r"\\(?:mathrm|text)\{([^{}]+)\}")
BOUNDARY_PUNCTUATION = " \t\n\r,;:!?\"'`"
MULTI_ANSWER_SEPARATORS = (" or ", ";", "\n\n")


@dataclass(frozen=True)
class ParseResult:
    """Structured parse output for a model generation.

    Args:
        answer: Canonicalized final answer string, or `None` when parsing fails.
        confidence: Deterministic parser confidence in `[0, 1]`.
        is_confident: Whether `confidence` exceeds the required threshold.
        answer_type: One of `numeric`, `symbolic`, `refusal`, or `unknown`.
        extraction_method: Name of the extraction rule that produced the answer.

    Returns:
        Immutable parse result for downstream sensitivity code.

    Reference:
        Part III.3 of the implementation brief.
    """

    answer: str | None
    confidence: float
    is_confident: bool
    answer_type: str
    extraction_method: str


def parse_answer(
    raw_output: str,
    significant_figures: int = DEFAULT_SIGNIFICANT_FIGURES,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> ParseResult:
    """Parse a model generation into a canonical answer or `None`.

    Args:
        raw_output: Full free-text model generation.
        significant_figures: Significant figures used for numeric normalization.
        confidence_threshold: Minimum confidence required for a parse to count.

    Returns:
        `ParseResult` containing the canonical answer and parser confidence.

    Reference:
        Part III.3 of the implementation brief.
    """

    cleaned_output = raw_output.strip()
    if _is_empty_or_refusal(cleaned_output):
        return _failed_result(cleaned_output, "refusal" if cleaned_output else "unknown", "empty_or_refusal")

    candidate_with_method = _extract_candidate(cleaned_output)
    if candidate_with_method is None:
        return _failed_result(cleaned_output, "unknown", "no_candidate")

    candidate_text, method, base_confidence = candidate_with_method
    if _looks_like_multi_answer(candidate_text):
        return _failed_result(cleaned_output, "unknown", f"{method}_multi_answer")

    numeric_result = _normalize_numeric_answer(candidate_text, significant_figures)
    if numeric_result is not None:
        answer, answer_type = numeric_result
        is_confident = base_confidence >= confidence_threshold
        if not is_confident:
            return _failed_result(cleaned_output, answer_type, method)
        return ParseResult(
            answer=answer,
            confidence=base_confidence,
            is_confident=True,
            answer_type=answer_type,
            extraction_method=method,
        )

    symbolic_answer = _normalize_symbolic_answer(candidate_text)
    if symbolic_answer is not None:
        is_confident = base_confidence >= confidence_threshold
        if not is_confident:
            return _failed_result(cleaned_output, "symbolic", method)
        return ParseResult(
            answer=symbolic_answer,
            confidence=base_confidence,
            is_confident=True,
            answer_type="symbolic",
            extraction_method=method,
        )

    return _failed_result(cleaned_output, "unknown", method)


def _is_empty_or_refusal(raw_output: str) -> bool:
    """Return whether the model output is empty or refusal-like."""
    lowered = raw_output.strip().lower()
    if lowered in EMPTY_OUTPUT_PATTERNS:
        return True
    return any(pattern in lowered for pattern in REFUSAL_PATTERNS)


def _extract_candidate(raw_output: str) -> tuple[str, str, float] | None:
    """Extract the most plausible final-answer span with a confidence prior."""
    boxed_candidate = _extract_boxed(raw_output)
    if boxed_candidate is not None:
        return boxed_candidate, "boxed", BOXED_CONFIDENCE

    explicit_candidate = _extract_explicit_answer(raw_output)
    if explicit_candidate is not None:
        return explicit_candidate, "explicit", EXPLICIT_CONFIDENCE

    final_line_candidate = _extract_final_line(raw_output)
    if final_line_candidate is not None:
        confidence = FINAL_LINE_CONFIDENCE if _looks_like_short_answer(final_line_candidate) else LOW_CONFIDENCE_FALLBACK
        return final_line_candidate, "final_line", confidence

    return None


def _extract_boxed(raw_output: str) -> str | None:
    """Extract the final boxed LaTeX answer, if present."""
    matches = list(BOXED_PATTERN.finditer(raw_output))
    if not matches:
        return None
    return _strip_boundaries(matches[-1].group("content"))


def _extract_explicit_answer(raw_output: str) -> str | None:
    """Extract explicit answer declarations like 'The answer is X'."""
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    for line in reversed(lines):
        lowered = line.lower()
        for pattern in EXPLICIT_ANSWER_PATTERNS:
            match = re.search(pattern, lowered, re.IGNORECASE)
            if match is None:
                continue
            start_index = match.start("answer")
            return _strip_boundaries(line[start_index:])
    return None


def _extract_final_line(raw_output: str) -> str | None:
    """Extract the last non-empty line as a fallback candidate."""
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    if not lines:
        return None
    return _strip_boundaries(lines[-1])


def _normalize_numeric_answer(
    candidate_text: str, significant_figures: int
) -> tuple[str, str] | None:
    """Normalize a numeric answer with optional units."""
    candidate_text = _normalize_common_tokens(candidate_text)
    match = NUMERIC_PATTERN.match(candidate_text)
    if match is None:
        return None

    numeric_value = float(match.group("value"))
    unit_text = match.group("unit") or ""
    if _contains_additional_number(unit_text):
        return None

    canonical_number = _format_significant_figures(numeric_value, significant_figures)
    canonical_unit = _normalize_unit_string(unit_text)
    if canonical_unit:
        return f"{canonical_number} {canonical_unit}", "numeric"
    return canonical_number, "numeric"


def _normalize_symbolic_answer(candidate_text: str) -> str | None:
    """Normalize a symbolic or algebraic answer string."""
    normalized = _normalize_common_tokens(candidate_text)
    if not normalized:
        return None
    if any(char.isdigit() for char in normalized) and _contains_sentence_text(normalized):
        return None
    if _contains_sentence_text(normalized) and "/" not in normalized and "^" not in normalized:
        return None

    normalized = _convert_latex_fraction(normalized)
    normalized = normalized.replace(" ", "")
    normalized = normalized.replace("{", "(").replace("}", ")")
    normalized = normalized.replace("^{", "^").replace("}", "")
    normalized = normalized.replace("**", "^")
    normalized = normalized.replace("\\cdot", "*")
    normalized = normalized.replace("\\,", "")
    normalized = normalized.replace("\\!", "")
    normalized = normalized.replace("²", "^2").replace("³", "^3")
    normalized = normalized.replace("−", "-")
    normalized = normalized.strip()
    normalized = _trim_redundant_outer_parentheses(normalized)
    return normalized or None


def _normalize_common_tokens(candidate_text: str) -> str:
    """Apply shared normalization for numeric and symbolic candidates."""
    normalized = candidate_text.strip().strip("$")
    normalized = normalized.replace("\\left", "").replace("\\right", "")
    normalized = normalized.replace("\\boxed", "")
    normalized = normalized.replace("≈", "")
    normalized = normalized.replace("~", "")
    normalized = UNIT_LATEX_PATTERN.sub(r"\1", normalized)
    assignment_match = ASSIGNMENT_PATTERN.match(normalized)
    if assignment_match is not None:
        normalized = assignment_match.group("rhs")
    return _strip_boundaries(normalized)


def _normalize_unit_string(unit_text: str) -> str:
    """Normalize units into a compact canonical representation."""
    normalized = unit_text.strip()
    normalized = normalized.replace("$", "")
    normalized = normalized.replace("·", "*")
    normalized = normalized.replace(" ", "")
    normalized = normalized.replace("\\cdot", "*")
    normalized = normalized.replace("\\,", "")
    normalized = normalized.replace("\\!", "")
    normalized = normalized.replace("\\/", "/")
    normalized = normalized.replace("^{", "^").replace("}", "")
    normalized = normalized.replace("{", "")
    normalized = normalized.replace("²", "^2").replace("³", "^3")
    normalized = normalized.replace("−", "-")
    normalized = normalized.replace("s^-2", "s^-2")
    normalized = normalized.replace("s-2", "s^-2")
    normalized = normalized.replace("m/s^2", "m/s^2")
    normalized = normalized.strip(BOUNDARY_PUNCTUATION).rstrip(".")
    return normalized


def _format_significant_figures(value: float, significant_figures: int) -> str:
    """Format a number to a fixed number of significant figures."""
    formatted = f"{value:.{significant_figures}g}"
    if "e" in formatted or "E" in formatted:
        mantissa, exponent = re.split(r"[eE]", formatted)
        mantissa = mantissa.rstrip("0").rstrip(".")
        exponent = exponent.lstrip("+")
        return f"{mantissa}e{exponent}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _contains_additional_number(text: str) -> bool:
    """Return whether the trailing unit text includes another standalone number."""
    stripped_text = re.sub(r"\^\{?-?\d+\}?|\^\(-?\d+\)", "", text)
    return bool(re.search(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", stripped_text))


def _contains_sentence_text(text: str) -> bool:
    """Detect long prose-like strings that should not count as answers."""
    tokens = re.findall(r"[A-Za-z]+", text)
    if len(tokens) >= 4:
        return True
    return any(token.lower() in {"because", "therefore", "answer", "final"} for token in tokens)


def _looks_like_short_answer(text: str) -> bool:
    """Heuristic for whether a fallback candidate looks like a concise answer."""
    return len(text.split()) <= 5 and len(text) <= 40


def _looks_like_multi_answer(text: str) -> bool:
    """Return whether the extracted candidate appears to contain multiple answers."""
    lowered = text.lower()
    if any(separator in lowered for separator in MULTI_ANSWER_SEPARATORS):
        return True
    return lowered.startswith("answers:")


def _convert_latex_fraction(text: str) -> str:
    """Convert simple LaTeX fractions into slash form."""
    previous = None
    converted = text
    while previous != converted:
        previous = converted
        converted = LATEX_FRACTION_PATTERN.sub(r"(\1)/(\2)", converted)
    return converted


def _strip_boundaries(text: str) -> str:
    """Strip boundary punctuation while preserving internal math syntax."""
    return text.strip(BOUNDARY_PUNCTUATION)


def _trim_redundant_outer_parentheses(text: str) -> str:
    """Trim one redundant outer parenthesis layer when it wraps the whole string."""
    if not (text.startswith("((") and text.endswith("))")):
        return text

    depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if depth == 0 and index != len(text) - 1:
            return text
    return text[1:-1]


def _failed_result(raw_output: str, answer_type: str, extraction_method: str) -> ParseResult:
    """Log a failed parse and return the corresponding low-confidence result."""
    snippet = raw_output[:FAILED_PARSE_SNIPPET_LENGTH].replace("\n", "\\n")
    LOGGER.warning("Failed to parse answer via %s: %s", extraction_method, snippet)
    return ParseResult(
        answer=None,
        confidence=0.0,
        is_confident=False,
        answer_type=answer_type,
        extraction_method=extraction_method,
    )
