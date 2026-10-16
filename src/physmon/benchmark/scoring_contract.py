"""Frozen scoring-interface contract for Research v2.0 (Stage 14.3).

This module fixes, as pure functions with no model or tokenizer dependency, the pieces of the scoring
interface that v2 requires to be explicit before any new log-probability is measured:

- the output-wrapper multiverse (v2 P1.3, p.17; card X03, p.39): seven equal-meaning serialisations of one
  physical answer, each paired with the instruction line that asks the model to produce exactly that
  format, so the string that is scored is the string the model is told to emit;
- the answer-span arithmetic for teacher-forced scoring (v2 B1.4, p.7; C05, p.33): which positions of the
  concatenated sequence carry the scored log-probability, so that no prompt or padding token is included;
- a duplicate-special-token check for chat prompts (a finding of the Stage 14.3 audit).

It does not load a tokenizer. `scripts/v2/s143_scoring_audit.py` applies it with real tokenizers.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

_VALUE_UNIT = re.compile(r"^(?P<value>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s+(?P<unit>\S.*)$")

CONTRACT_VERSION = "v2-scoring-contract-1"


def split_answer(answer: str) -> tuple[str, str]:
    """Split a stored reference answer such as `6.928 N*m` into (value text, unit text).

    Raises ValueError for anything that is not `<number> <unit>`; the caller must record such a family
    as NOT_EVALUATED for wrapper scoring rather than guess.
    """

    match = _VALUE_UNIT.match(answer.strip())
    if not match:
        raise ValueError(f"reference answer is not '<value> <unit>': {answer!r}")
    return match.group("value"), match.group("unit")


def _plain_decimal(value_text: str) -> str:
    """The same number written as a plain decimal with no exponent (value-preserving)."""

    text = format(Decimal(value_text), "f")
    return text


def _scientific(value_text: str) -> str:
    """The same number in scientific notation `d.ddde[+-]x` (value-preserving)."""

    decimal = Decimal(value_text)
    if decimal == 0:
        return "0e0"
    sign, digits, exponent = decimal.as_tuple()
    digit_text = "".join(str(d) for d in digits).rstrip("0") or "0"
    adjusted = decimal.adjusted()
    mantissa = digit_text[0] + (("." + digit_text[1:]) if len(digit_text) > 1 else "")
    return f"{'-' if sign else ''}{mantissa}e{adjusted}"


@dataclass(frozen=True)
class WrapperSpec:
    """One output wrapper: how the target is written and how the model is told to write it."""

    wrapper_id: str
    description: str
    format_line: str  # shown to the model inside the instruction
    notation: str  # 'as_stored', 'plain_decimal' or 'scientific'


# The model-facing instruction is the existing Stage 6 system prompt with only the format line replaced.
INSTRUCTION_TEMPLATE = (
    "You are a precise physics problem solver. "
    "Solve the problem silently and return exactly one line in this format: "
    "{format_line}. "
    "Do not include reasoning, derivations, equations, or any extra text."
)

WRAPPERS: dict[str, WrapperSpec] = {
    spec.wrapper_id: spec
    for spec in (
        WrapperSpec("plain", "digits and unit only", "[value] [unit]", "as_stored"),
        WrapperSpec("answer_line", "Stage 6 format (Answer: prefix)", "Answer: [value] [unit]",
                    "as_stored"),
        WrapperSpec("boxed", "LaTeX boxed answer", "\\boxed{[value] [unit]}", "as_stored"),
        WrapperSpec("json", "JSON scalar with unit", '{"value": [value], "unit": "[unit]"}',
                    "as_stored"),
        WrapperSpec("sentence", "short natural-language answer", "The answer is [value] [unit].",
                    "as_stored"),
        WrapperSpec("decimal_plain", "Answer line, value as a plain decimal",
                    "Answer: [value] [unit], with the value written as a plain decimal number "
                    "without scientific notation", "plain_decimal"),
        WrapperSpec("scientific", "Answer line, value in scientific notation",
                    "Answer: [value] [unit], with the value written in scientific notation",
                    "scientific"),
    )
}


def instruction_for(wrapper_id: str) -> str:
    """The frozen system instruction that asks for exactly this wrapper's format."""

    return INSTRUCTION_TEMPLATE.format(format_line=WRAPPERS[wrapper_id].format_line)


def render_target(wrapper_id: str, value_text: str, unit_text: str) -> str:
    """The exact string to score for a physical answer under a wrapper."""

    spec = WRAPPERS[wrapper_id]
    if spec.notation == "plain_decimal":
        value_text = _plain_decimal(value_text)
    elif spec.notation == "scientific":
        value_text = _scientific(value_text)
    templates = {
        "plain": "{v} {u}",
        "answer_line": "Answer: {v} {u}",
        "boxed": "\\boxed{{{v} {u}}}",
        "json": '{{"value": {v}, "unit": "{u}"}}',
        "sentence": "The answer is {v} {u}.",
        "decimal_plain": "Answer: {v} {u}",
        "scientific": "Answer: {v} {u}",
    }
    return templates[wrapper_id].format(v=value_text, u=unit_text)


_PARSERS = {
    "plain": re.compile(r"^(?P<v>\S+) (?P<u>.+)$"),
    "answer_line": re.compile(r"^Answer: (?P<v>\S+) (?P<u>.+)$"),
    "boxed": re.compile(r"^\\boxed\{(?P<v>\S+) (?P<u>.+)\}$"),
    "json": re.compile(r'^\{"value": (?P<v>\S+), "unit": "(?P<u>.+)"\}$'),
    "sentence": re.compile(r"^The answer is (?P<v>\S+) (?P<u>.+)\.$"),
    "decimal_plain": re.compile(r"^Answer: (?P<v>\S+) (?P<u>.+)$"),
    "scientific": re.compile(r"^Answer: (?P<v>\S+) (?P<u>.+)$"),
}


def parse_target(wrapper_id: str, target: str) -> tuple[float, str]:
    """Recover (numeric value, unit) from a wrapped target; used to prove the wrappers are equivalent."""

    match = _PARSERS[wrapper_id].match(target)
    if not match:
        raise ValueError(f"target does not match wrapper {wrapper_id!r}: {target!r}")
    return float(Decimal(match.group("v"))), match.group("u")


def contract_fingerprint() -> str:
    """A hash of every frozen string, so a later run can prove it used this exact contract."""

    payload = {
        "version": CONTRACT_VERSION,
        "template": INSTRUCTION_TEMPLATE,
        "wrappers": {k: [v.description, v.format_line, v.notation] for k, v in WRAPPERS.items()},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def answer_span(n_prompt_tokens: int, n_answer_tokens: int) -> dict[str, int]:
    """Positions for teacher-forced scoring of `answer` appended to `prompt`.

    In the concatenated sequence the answer occupies `[start, end)`. Logits at position `i` predict the
    token at `i + 1`, so the scored logits are at `[start - 1, end - 1)`. Nothing from the prompt and no
    padding is included.
    """

    if n_prompt_tokens < 1 or n_answer_tokens < 1:
        raise ValueError("prompt and answer must each have at least one token")
    start = n_prompt_tokens
    end = n_prompt_tokens + n_answer_tokens
    return {"start": start, "end": end, "logit_start": start - 1, "logit_end": end - 1}


def leading_special_count(token_ids: Sequence[int], special_id: int | None) -> int:
    """How many copies of a special token (for example BOS) start the sequence."""

    if special_id is None:
        return 0
    count = 0
    for token in token_ids:
        if token != special_id:
            break
        count += 1
    return count
