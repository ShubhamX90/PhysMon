"""Reasoning-allowed answer contract (Stage 14.13; v2 B1.4, B2.4, X03 follow-up).

The Stage 14.3 scoring contract has one frozen instruction family that forbids reasoning ("Solve the problem silently").
Under it both pilot models were almost never correct on the v2 structures (Stage 14.7, 14.8), so correctness-transition
endpoints could not be estimated. This module defines a separate, frozen contract that lets the model reason and then give
one final line, with its own version and fingerprint. It does NOT change the Stage 14.3 contract or its fingerprint: runs under
either contract keep the fingerprint of the one they used.

Only generation is graded under this contract. A gold string is not teacher-forced after a model's own reasoning, so no
log-probability is defined here (the record keeps the field as null, never zero).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from physmon.scoring.v2_scorer import ParsedOutput, normalise_unit

CONTRACT_VERSION = "reasoning-v1"
FINAL_LINE_FORMAT = "Final answer: [value] [unit]"
INSTRUCTION = (
    "You are a careful physics problem solver. "
    "Work through the problem step by step, then write the final result on the last line in exactly this format: "
    f"{FINAL_LINE_FORMAT}. "
    "Write the value as a plain decimal number and use only the symbol for the unit. "
    "Write nothing after the final line."
)
PARSE_STATUSES = ("PARSED", "UNPARSEABLE", "MULTIPLE_CANDIDATES", "EMPTY", "TRUNCATED")

_NUMBER = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
_FINAL = re.compile(rf"^[ \t*]*Final answer:[ \t*]*(?P<v>{_NUMBER})[ \t]+(?P<u>[^\n]*?)[ \t*]*\.?[ \t*]*$", re.M)


@dataclass(frozen=True)
class ReasoningParse:
    parsed: ParsedOutput
    n_final_lines: int


def parse_final(text: str, *, hit_token_limit: bool = False) -> ReasoningParse:
    """The value and unit of the final line. Several final lines with different answers are a status of their own;
    a generation cut off by the token limit without a final line is TRUNCATED, never a wrong answer."""

    if not text.strip():
        return ReasoningParse(ParsedOutput("EMPTY"), 0)
    matches = list(_FINAL.finditer(text))
    if not matches:
        return ReasoningParse(ParsedOutput("TRUNCATED" if hit_token_limit else "UNPARSEABLE"), 0)
    answers = {(m.group("v"), normalise_unit(m.group("u"))) for m in matches}
    if len(answers) > 1:
        return ReasoningParse(ParsedOutput("MULTIPLE_CANDIDATES"), len(matches))
    last = matches[-1]
    return ReasoningParse(ParsedOutput("PARSED", float(last.group("v")), normalise_unit(last.group("u")), last.group("v")),
                          len(matches))


def contract_fingerprint() -> str:
    payload = {"version": CONTRACT_VERSION, "instruction": INSTRUCTION, "final_line_format": FINAL_LINE_FORMAT,
               "parse_statuses": list(PARSE_STATUSES), "pattern": _FINAL.pattern}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
