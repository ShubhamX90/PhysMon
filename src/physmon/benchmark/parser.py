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
BARE_NUMERIC_CONFIDENCE = 0.80
ASSIGNMENT_CONFIDENCE = 0.88
PRIMARY_ANSWER_CONFIDENCE = 0.98

SUPERSCRIPT_TRANSLATION = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")

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
MARKDOWN_BOLD_PATTERN = re.compile(r"\*\*(?P<content>.*?)\*\*")
NUMERIC_PATTERN = re.compile(
    r"^[~=≈\s]*"
    r"(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?:\s*(?P<unit>.*))?$"
)
ASSIGNMENT_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*\s*=\s*(?P<rhs>.+)$")
UNIT_LATEX_PATTERN = re.compile(r"\\(?:mathrm|text)\{([^{}]+)\}")
PRIMARY_ANSWER_PATTERN = re.compile(
    r"[Aa]nswer\s*:\s*(?P<answer>.+)",
    re.IGNORECASE,
)
EQUALS_ANSWER_PATTERN = re.compile(
    r"=\s*(?P<answer>[^\n]+?)\s*$",
)
FLOAT_LIKE_PATTERN = re.compile(
    r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
)
EMBEDDED_NUMERIC_WITH_UNIT_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_/^])"
    r"(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"\s*(?P<unit>[A-Za-zµμΩ/²³\*·\^\-][A-Za-z0-9µμΩ/²³\*·\^\-\s{}]*)"
)
BOUNDARY_PUNCTUATION = " \t\n\r,;:!?\"'`"
MULTI_ANSWER_SEPARATORS = (" or ", ";", "\n\n")


@dataclass(frozen=True)
class ParseResult:
    """Structured parse output for a model generation.

    Args:
        answer: Canonicalized final answer string used for equality comparison.
        display_answer: Human-readable extracted answer used for logging/auditing.
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
    display_answer: str | None
    confidence: float
    is_confident: bool
    answer_type: str
    extraction_method: str


def parse_answer(
    raw_output: str,
    significant_figures: int = DEFAULT_SIGNIFICANT_FIGURES,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    expected_unit: str | None = None,
) -> ParseResult:
    """Parse a model generation into a canonical answer or `None`.

    Args:
        raw_output: Full free-text model generation.
        significant_figures: Significant figures used for numeric normalization.
        confidence_threshold: Minimum confidence required for a parse to count.
        expected_unit: Optional canonical unit from template metadata for bare-number fallback.

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
    cleaned_candidate = _strip_latex_and_normalise(candidate_text)
    if _looks_like_multi_answer(cleaned_candidate):
        return _failed_result(cleaned_output, "unknown", f"{method}_multi_answer")
    if _looks_truncated_candidate(cleaned_candidate):
        return _failed_result(cleaned_output, "unknown", f"{method}_truncated")
    display_answer = _normalize_display_answer(cleaned_candidate, expected_unit=expected_unit)
    cleaned_candidate_starts_numeric = NUMERIC_PATTERN.match(_normalize_scientific_notation(cleaned_candidate)) is not None
    symbolic_candidate = (
        (method == "equals_line" and not _is_valid_extracted_answer(cleaned_candidate))
        or _looks_symbolic_math(cleaned_candidate)
        or (_looks_symbolic_math(candidate_text) and not cleaned_candidate_starts_numeric)
    )
    if symbolic_candidate:
        symbolic_answer = _normalize_symbolic_answer(candidate_text)
        if symbolic_answer is not None:
            is_confident = base_confidence >= confidence_threshold
            if not is_confident:
                return _failed_result(cleaned_output, "symbolic", method)
            return ParseResult(
                answer=symbolic_answer,
                display_answer=display_answer,
                confidence=base_confidence,
                is_confident=True,
                answer_type="symbolic",
                extraction_method=method,
            )
    if _is_valid_extracted_answer(cleaned_candidate):
        numeric_result = _normalize_numeric_answer(
            cleaned_candidate,
            significant_figures,
            expected_unit=expected_unit,
        )
        if numeric_result is not None:
            answer, answer_type = numeric_result
            is_confident = base_confidence >= confidence_threshold
            if not is_confident:
                return _failed_result(cleaned_output, answer_type, method)
            return ParseResult(
                answer=answer,
                display_answer=display_answer,
                confidence=base_confidence,
                is_confident=True,
                answer_type=answer_type,
                extraction_method=method,
            )
    if not _is_valid_extracted_answer(cleaned_candidate):
        return _failed_result(cleaned_output, "unknown", f"{method}_invalid")

    symbolic_answer = _normalize_symbolic_answer(candidate_text)
    if symbolic_answer is not None:
        is_confident = base_confidence >= confidence_threshold
        if not is_confident:
            return _failed_result(cleaned_output, "symbolic", method)
        return ParseResult(
            answer=symbolic_answer,
            display_answer=display_answer,
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

    primary_answer_candidate = _extract_primary_answer(raw_output)
    if primary_answer_candidate is not None:
        return primary_answer_candidate, "answer_colon", PRIMARY_ANSWER_CONFIDENCE

    explicit_candidate = _extract_explicit_answer(raw_output)
    if explicit_candidate is not None:
        return explicit_candidate, "explicit", EXPLICIT_CONFIDENCE

    assignment_candidate = _extract_equals_answer(raw_output)
    if assignment_candidate is not None:
        return assignment_candidate, "equals_line", ASSIGNMENT_CONFIDENCE

    final_line_candidate = _extract_final_line(raw_output)
    if final_line_candidate is not None:
        normalized_final_line = _normalize_scientific_notation(_normalize_common_tokens(final_line_candidate))
        has_direct_numeric = NUMERIC_PATTERN.match(normalized_final_line) is not None
        has_embedded_numeric = _extract_embedded_numeric_with_unit(normalized_final_line) is not None
        confidence = (
            FINAL_LINE_CONFIDENCE
            if _looks_like_short_answer(final_line_candidate) or has_direct_numeric or has_embedded_numeric
            else LOW_CONFIDENCE_FALLBACK
        )
        return final_line_candidate, "final_line", confidence

    return None


def _extract_boxed(raw_output: str) -> str | None:
    """Extract the final boxed LaTeX answer, if present."""
    matches = list(BOXED_PATTERN.finditer(raw_output))
    if not matches:
        return None
    return _strip_boundaries(matches[-1].group("content"))


def _extract_primary_answer(raw_output: str) -> str | None:
    """Extract the requested `Answer: ...` format from any line."""
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    for line in reversed(lines):
        match = PRIMARY_ANSWER_PATTERN.search(line)
        if match is None:
            continue
        return _strip_boundaries(match.group("answer"))
    return None


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


def _extract_equals_answer(raw_output: str) -> str | None:
    """Extract a trailing `= value unit` fragment from the last matching line."""
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    for line in reversed(lines):
        match = EQUALS_ANSWER_PATTERN.search(line)
        if match is None:
            continue
        return _strip_boundaries(match.group("answer"))
    return None


def _extract_final_line(raw_output: str) -> str | None:
    """Extract the last non-empty line as a fallback candidate."""
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    if not lines:
        return None
    return _strip_boundaries(lines[-1])


def _normalize_numeric_answer(
    candidate_text: str,
    significant_figures: int,
    expected_unit: str | None = None,
) -> tuple[str, str] | None:
    """Normalize a numeric answer with optional units."""
    candidate_text = _normalize_common_tokens(candidate_text)
    normalized_text = _normalize_scientific_notation(candidate_text)
    match = NUMERIC_PATTERN.match(normalized_text)
    if match is None:
        embedded_match = _extract_embedded_numeric_with_unit(normalized_text)
        if embedded_match is not None:
            match = embedded_match
        else:
            return _normalize_bare_number_answer(
                normalized_text,
                significant_figures,
                expected_unit=expected_unit,
            )

    numeric_value = float(match.group("value"))
    unit_text = match.group("unit") or ""
    if _contains_additional_number(unit_text):
        return _normalize_bare_number_answer(
            normalized_text,
            significant_figures,
            expected_unit=expected_unit,
        )

    canonical_number = _format_significant_figures(numeric_value, significant_figures)
    canonical_unit = _normalize_unit_string(unit_text)
    if canonical_unit:
        return f"{canonical_number} {canonical_unit}", "numeric"
    if expected_unit is not None:
        return f"{canonical_number} {_normalize_unit_string(expected_unit)}", "numeric"
    return canonical_number, "numeric"


def _normalize_bare_number_answer(
    candidate_text: str,
    significant_figures: int,
    expected_unit: str | None = None,
) -> tuple[str, str] | None:
    """Normalize a unique bare number, optionally attaching an expected unit."""
    if expected_unit is None:
        return None

    last_line = _extract_final_line(candidate_text) or candidate_text
    bare_matches = FLOAT_LIKE_PATTERN.findall(_normalize_scientific_notation(last_line))
    if len(bare_matches) != 1:
        return None

    numeric_value = float(bare_matches[0])
    canonical_number = _format_significant_figures(numeric_value, significant_figures)
    canonical_unit = _normalize_unit_string(expected_unit)
    return f"{canonical_number} {canonical_unit}", "numeric"


def _extract_embedded_numeric_with_unit(text: str) -> re.Match[str] | None:
    """Find the final numeric-with-unit span inside a prose line."""
    matches = list(EMBEDDED_NUMERIC_WITH_UNIT_PATTERN.finditer(text))
    if not matches:
        return None
    return matches[-1]


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
    normalized = MARKDOWN_BOLD_PATTERN.sub(r"\g<content>", normalized)
    normalized = normalized.replace("\\left", "").replace("\\right", "")
    normalized = normalized.replace("\\boxed", "")
    normalized = normalized.replace("≈", "")
    normalized = normalized.replace("~", "")
    normalized = UNIT_LATEX_PATTERN.sub(r"\1", normalized)
    normalized = normalized.replace("**", "")
    assignment_match = ASSIGNMENT_PATTERN.match(normalized)
    if assignment_match is not None:
        normalized = assignment_match.group("rhs")
    return _strip_boundaries(normalized)


def _strip_latex_and_normalise(text: str) -> str:
    """Strip lightweight LaTeX wrappers from an extracted answer span."""
    normalized = _normalize_common_tokens(text)
    normalized = re.sub(r"\\\[|\\\]|\$\$", "", normalized)
    normalized = re.sub(r"\\\(|\\\)", "", normalized)
    normalized = re.sub(r"\\[,;:!]", " ", normalized)
    normalized = re.sub(r"\\text\{([^}]+)\}", r"\1", normalized)
    normalized = re.sub(r"\\cdot", "*", normalized)
    normalized = re.sub(r"\\[a-zA-Z]+", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return _strip_boundaries(normalized)


def _normalize_display_answer(candidate_text: str, expected_unit: str | None = None) -> str | None:
    """Create a human-readable extracted answer string for logs and JSONL records."""
    if not candidate_text:
        return None
    normalized_text = _normalize_scientific_notation(candidate_text)
    match = NUMERIC_PATTERN.match(normalized_text)
    if match is None:
        match = _extract_embedded_numeric_with_unit(normalized_text)
    if match is None:
        return _strip_boundaries(normalized_text) or None

    value_text = match.group("value")
    unit_text = match.group("unit") or ""
    canonical_unit = _normalize_unit_string(unit_text)
    if canonical_unit:
        return f"{value_text} {canonical_unit}"
    if expected_unit is not None:
        return f"{value_text} {_normalize_unit_string(expected_unit)}"
    return value_text


def _normalize_scientific_notation(text: str) -> str:
    """Normalize unicode multiplication and superscript scientific notation into `e` form."""
    normalized = text.translate(SUPERSCRIPT_TRANSLATION)
    normalized = normalized.replace("−", "-")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(
        r"(?P<mantissa>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*[×x]\s*10\^(?P<exponent>[+-]?\d+)",
        r"\g<mantissa>e\g<exponent>",
        normalized,
    )
    normalized = re.sub(
        r"(?P<mantissa>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*[×x]\s*10(?P<exponent>[+-]?\d+)",
        r"\g<mantissa>e\g<exponent>",
        normalized,
    )
    return normalized.strip()


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
    normalized = normalized.translate(SUPERSCRIPT_TRANSLATION)
    normalized = re.sub(r"(?<=[A-Za-zµμΩ])([23])(?=(?:/|$))", r"^\1", normalized)
    normalized = normalized.replace("s^-2", "s^-2")
    normalized = normalized.replace("s-2", "s^-2")
    normalized = normalized.replace("m/s^2", "m/s^2")
    normalized = normalized.replace("m*s^-1", "m/s^-1")
    normalized = normalized.replace("m*s^-2", "m/s^-2")
    normalized = normalized.replace("N*m^2/C^2", "N*m^2/C^2")
    normalized = normalized.strip(BOUNDARY_PUNCTUATION).rstrip(".")
    return normalized


def _format_significant_figures(value: float, significant_figures: int) -> str:
    """Format a number to a fixed number of significant figures."""
    formatted = f"{value:.{significant_figures}g}"
    if "e" in formatted or "E" in formatted:
        mantissa, exponent = re.split(r"[eE]", formatted)
        mantissa = mantissa.rstrip("0").rstrip(".")
        exponent = str(int(exponent))
        return f"{mantissa}e{exponent}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _is_valid_extracted_answer(extracted: str | None) -> bool:
    """Reject extracted answers that cannot be a valid numeric physics answer."""
    if extracted is None:
        return False
    stripped = extracted.strip().strip(BOUNDARY_PUNCTUATION)
    if not stripped:
        return False
    return re.search(r"\d", stripped) is not None


def _contains_additional_number(text: str) -> bool:
    """Return whether the trailing unit text includes another standalone number."""
    stripped_text = re.sub(r"\^\{?-?\d+\}?|\^\(-?\d+\)", "", text)
    stripped_text = re.sub(r"(?<=[A-Za-zµμΩ])\d+", "", stripped_text)
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


def _looks_truncated_candidate(text: str) -> bool:
    """Reject obviously truncated spans such as unfinished units or open delimiters."""
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.endswith(("(", "[", "{", "=", ":", "-", "/")):
        return True
    return stripped.count("(") > stripped.count(")") or stripped.count("[") > stripped.count("]")


def _looks_symbolic_math(text: str) -> bool:
    """Return whether a candidate is primarily an algebraic expression, not a numeric value."""
    stripped = _normalize_common_tokens(text)
    if not stripped:
        return False
    if re.match(r"^[~=≈\s]*[+-]?(?:\d+(?:\.\d*)?|\.\d+)", stripped):
        return False
    if re.search(r"\\frac|[A-Za-z][A-Za-z0-9_]*\^|\([A-Za-z0-9_]+\)", stripped):
        return True
    if re.search(r"[A-Za-z]", stripped) and any(operator in stripped for operator in ("/", "^")):
        if not re.search(r"\b(?:m|s|kg|N|J|V|W|C|A|F|Ω|Hz)\b", stripped):
            return True
    return False


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
        display_answer=None,
        confidence=0.0,
        is_confident=False,
        answer_type=answer_type,
        extraction_method=extraction_method,
    )
