"""Reasoning-allowed answer contract, version 2 (Stage 15; plan of record Section 4.5 "Outcomes").

Version 1 (`reasoning_contract.py`, Stage 14.13) is unchanged and keeps its fingerprint; runs under it keep theirs.
Version 2 keeps the same instruction and final-line format, so prompts stay comparable, and changes what is recorded:

* Completion statuses (outcome O3). `COMPLETE` (one final answer), `BUDGET_EXHAUSTED` (the generation stopped at the token
  limit and no answer was given; the only status that means truncation), `FORMAT_INVALID` (a thinking-mode generation that
  stopped by itself without closing its thinking: the end-of-thinking marker is missing although the budget was not exhausted),
  `UNPARSEABLE` (an answer part without a contract final line), `MULTIPLE_CANDIDATES` (final lines that disagree) and `EMPTY`.
  None of these is ever relabelled `WRONG`.
* Only the text after the end-of-thinking marker is graded in thinking mode; a final-line phrase inside the thinking is not an
  answer.
* A frozen recovery rule (`recover_final`) reads a final line wrapped in LaTeX or Markdown (for example
  `\\text{Final answer: } 223.253 \\, \\text{s}` or `\\boxed{13.43} \\, \\text{m}`, which cost 5 of 78 Stage A records). It feeds
  only the separate semantic-correctness outcome (O2); the contract status and the contract grade never use it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from physmon.benchmark import reasoning_contract as v1
from physmon.scoring.v2_scorer import ParsedOutput, normalise_unit

CONTRACT_VERSION = "reasoning-v2"
INSTRUCTION = v1.INSTRUCTION  # identical text to version 1, so prompts stay comparable
FINAL_LINE_FORMAT = v1.FINAL_LINE_FORMAT
THINK_CLOSE = "</think>"
COMPLETION_STATUSES = ("COMPLETE", "BUDGET_EXHAUSTED", "FORMAT_INVALID", "UNPARSEABLE", "MULTIPLE_CANDIDATES", "EMPTY")
RECOVERY_STATUSES = ("RECOVERED", "NOT_RECOVERED")
RECOVERY_RULE = "latex-markdown-final-line-v1"

_FINAL = v1._FINAL  # the version-1 final-line pattern, unchanged


@dataclass(frozen=True)
class Completion:
    """The contract reading of one generation."""

    status: str  # one of COMPLETION_STATUSES
    parsed: ParsedOutput  # status PARSED with value and unit when `status` is COMPLETE, otherwise the completion status
    n_final_lines: int
    thinking_closed: bool | None  # None when thinking was not expected
    thinking_text: str
    answer_text: str
    hit_token_limit: bool


def user_turn(problem: str, unit: str | None) -> str:
    """The instruction and the problem in one user message; with `unit`, the requested answer unit is stated."""

    stated = f"\n\nGive the final answer in {display_unit(unit)}." if unit else ""
    return f"{INSTRUCTION}\n\n{problem}{stated}"


def display_unit(unit: str) -> str:
    return unit.replace("^2", "\u00b2").replace("^3", "\u00b3")


def _parse_answer(answer: str, hit_token_limit: bool) -> tuple[str, ParsedOutput, int]:
    if not answer.strip():
        status = "BUDGET_EXHAUSTED" if hit_token_limit else "EMPTY"
        return status, ParsedOutput(status), 0
    matches = list(_FINAL.finditer(answer))
    if not matches:
        status = "BUDGET_EXHAUSTED" if hit_token_limit else "UNPARSEABLE"
        return status, ParsedOutput(status), 0
    answers = {(m.group("v"), normalise_unit(m.group("u"))) for m in matches}
    if len(answers) > 1:
        return "MULTIPLE_CANDIDATES", ParsedOutput("MULTIPLE_CANDIDATES"), len(matches)
    last = matches[-1]
    parsed = ParsedOutput("PARSED", float(last.group("v")), normalise_unit(last.group("u")), last.group("v"))
    return "COMPLETE", parsed, len(matches)


def assess(text: str, *, hit_token_limit: bool, thinking_expected: bool) -> Completion:
    """Read one generation under the contract.

    In thinking mode the answer is the text after the last end-of-thinking marker. A generation without the marker is
    `BUDGET_EXHAUSTED` if it stopped at the token limit and `FORMAT_INVALID` if it stopped by itself (`EMPTY` if blank). Without
    thinking the whole text is the answer part.
    """

    if thinking_expected:
        if THINK_CLOSE in text:
            thinking, _, answer = text.rpartition(THINK_CLOSE)
            status, parsed, n = _parse_answer(answer, hit_token_limit)
            return Completion(status, parsed, n, True, thinking, answer, hit_token_limit)
        if not text.strip():
            return Completion("EMPTY", ParsedOutput("EMPTY"), 0, False, text, "", hit_token_limit)
        status = "BUDGET_EXHAUSTED" if hit_token_limit else "FORMAT_INVALID"
        return Completion(status, ParsedOutput(status), 0, False, text, "", hit_token_limit)
    status, parsed, n = _parse_answer(text, hit_token_limit)
    return Completion(status, parsed, n, None, "", text, hit_token_limit)


# --- recovery for the semantic-correctness outcome (O2) -------------------------------------------------------------------

_LATEX_WRAPPERS = re.compile(r"\\(?:text|mathrm|textrm|textbf|mathbf|operatorname|boxed|mbox)\s*\{([^{}]*)\}")
_SCI = re.compile(r"(?P<m>[-+]?\d+(?:\.\d+)?)\s*(?:\\times|\\cdot|×|x)\s*10\s*\^\s*\{?\s*(?P<e>[-+−]?\d+)\s*\}?")
_SUPERSCRIPT = re.compile(r"\^\s*\{\s*([-+]?\d+)\s*\}")
_RECOVER_LINE = re.compile(r"final\s+answer\s*[:=]\s*(?P<v>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*(?P<u>[^\n]*?)\s*\.?\s*$",
                           re.I | re.M)


@dataclass(frozen=True)
class Recovery:
    status: str  # RECOVERED | NOT_RECOVERED
    parsed: ParsedOutput  # PARSED with value and unit when recovered
    rule: str = RECOVERY_RULE


def normalise_markup(text: str) -> str:
    """Strip Markdown emphasis and the common LaTeX wrappers so a final line written in markup reads as plain text."""

    out = text.replace("**", "").replace("__", "").replace("`", "")
    for token in ("\\(", "\\)", "\\[", "\\]", "$"):
        out = out.replace(token, " ")
    for token in ("\\,", "\\;", "\\:", "\\!", "\\ ", "~"):
        out = out.replace(token, " ")
    out = out.replace("\\mu", "μ").replace("\\Omega", "Ω").replace("\\cdot", "*").replace("−", "-").replace("\\%", "%")
    out = re.sub(r"\^\s*\{?\s*\\circ\s*\}?", " deg", out)
    previous = None
    while previous != out:  # unwrap nested \text{...} and \boxed{...}
        previous = out
        out = _LATEX_WRAPPERS.sub(lambda m: m.group(1), out)
    out = _SCI.sub(lambda m: f"{m.group('m')}e{m.group('e').replace('−', '-')}", out)
    out = _SUPERSCRIPT.sub(lambda m: f"^{m.group(1)}", out)
    out = out.replace("{", "").replace("}", "")
    return re.sub(r"[ \t]+", " ", out)


def recover_final(answer_text: str) -> Recovery:
    """The frozen O2 recovery rule: the last `final answer: <number> <unit>` line after markup is normalised.

    Several recovered final lines that disagree are not recovered. The rule is applied only to the answer part (after the
    end-of-thinking marker in thinking mode), never to the thinking.
    """

    if not answer_text.strip():
        return Recovery("NOT_RECOVERED", ParsedOutput("EMPTY"))
    normalised = normalise_markup(answer_text)
    matches = list(_RECOVER_LINE.finditer(normalised))
    if not matches:
        return Recovery("NOT_RECOVERED", ParsedOutput("UNPARSEABLE"))
    answers = {(m.group("v"), normalise_unit(m.group("u"))) for m in matches}
    if len(answers) > 1:
        return Recovery("NOT_RECOVERED", ParsedOutput("MULTIPLE_CANDIDATES"))
    last = matches[-1]
    return Recovery("RECOVERED", ParsedOutput("PARSED", float(last.group("v")), normalise_unit(last.group("u")), last.group("v")))


def contract_fingerprint() -> str:
    payload = {"version": CONTRACT_VERSION, "instruction": INSTRUCTION, "final_line_format": FINAL_LINE_FORMAT,
               "completion_statuses": list(COMPLETION_STATUSES), "pattern": _FINAL.pattern, "think_close": THINK_CLOSE,
               "recovery_rule": RECOVERY_RULE, "recovery_pattern": _RECOVER_LINE.pattern, "latex_wrappers": _LATEX_WRAPPERS.pattern,
               "sci_pattern": _SCI.pattern}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
