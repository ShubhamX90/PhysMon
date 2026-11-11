"""Tests for the reasoning-v2 answer contract and its O2 recovery rule (Stage 15)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract as v1  # noqa: E402
from physmon.benchmark import reasoning_contract_v2 as rc2  # noqa: E402

# Answer endings of real Stage 14.20 records that version 1 graded UNPARSEABLE (jobs 425243 and 435605), with their gold values.
REAL_LATEX_ENDINGS = [
    ("### Final Answer:\n\n$$\n\\text{Final answer: } 223.253 \\, \\text{s}\n$$", 223.253, "s"),
    ("### Final Answer:\n\n$$\n\\boxed{13.43} \\, \\text{m}\n$$", 13.43, "m"),
    ("### Final Answer\n\n$$\n\\text{Final answer: } 1.68\\,\\text{s}\n$$", 1.68, "s"),
    ("### Final Answer:\n\n$$\n\\boxed{4.789} \\text{MeV}\n$$", 4.789, "MeV"),
    ("**Final Answer:**\n\n$$\n\\boxed{100} \\, \\text{pm}\n$$", 100.0, "pm"),
    ("### Final Answer (Rounded to Four Significant Figures)\n\n$$\n\\text{Final answer: } 1368 \\, \\text{m/s}\n$$", 1368.0, "m/s"),
    ("### **Final Answer:**\n\n$$\n\\text{Final answer: } -0.614 \\, \\text{s}\n$$", -0.614, "s"),
]


def test_instruction_and_final_line_are_identical_to_version_1_but_the_fingerprint_differs():
    assert rc2.INSTRUCTION == v1.INSTRUCTION and rc2.FINAL_LINE_FORMAT == v1.FINAL_LINE_FORMAT
    assert rc2.contract_fingerprint() != v1.contract_fingerprint()
    assert rc2.contract_fingerprint() == rc2.contract_fingerprint()


def test_thinking_mode_grades_only_the_text_after_the_last_closing_tag():
    text = "Final answer: 5 m\nwait, no.\n</think>\nWork.\nFinal answer: 40.8 m"
    c = rc2.assess(text, hit_token_limit=False, thinking_expected=True)
    assert c.status == "COMPLETE" and c.parsed.value == pytest.approx(40.8) and c.thinking_closed
    inside_only = rc2.assess("Final answer: 5 m\n</think>\nI cannot decide.", hit_token_limit=False, thinking_expected=True)
    assert inside_only.status == "UNPARSEABLE"


def test_missing_marker_is_format_invalid_unless_the_budget_was_exhausted():
    assert rc2.assess("thinking ... Final answer: 3 m", hit_token_limit=False, thinking_expected=True).status == "FORMAT_INVALID"
    assert rc2.assess("thinking that never ends", hit_token_limit=True, thinking_expected=True).status == "BUDGET_EXHAUSTED"
    assert rc2.assess("   ", hit_token_limit=False, thinking_expected=True).status == "EMPTY"
    closed_cut = rc2.assess("t\n</think>\nStill writing", hit_token_limit=True, thinking_expected=True)
    assert closed_cut.status == "BUDGET_EXHAUSTED"


def test_non_thinking_mode_reads_the_whole_text_and_keeps_statuses_distinct():
    assert rc2.assess("Steps.\nFinal answer: 3 m/s", hit_token_limit=False, thinking_expected=False).status == "COMPLETE"
    assert rc2.assess("Steps without a final line.", hit_token_limit=False, thinking_expected=False).status == "UNPARSEABLE"
    assert rc2.assess("Steps without a final line.", hit_token_limit=True, thinking_expected=False).status == "BUDGET_EXHAUSTED"
    two = rc2.assess("Final answer: 3 m\nFinal answer: 4 m", hit_token_limit=False, thinking_expected=False)
    assert two.status == "MULTIPLE_CANDIDATES"
    assert rc2.assess("", hit_token_limit=False, thinking_expected=False).status == "EMPTY"
    assert set(rc2.COMPLETION_STATUSES) == {"COMPLETE", "BUDGET_EXHAUSTED", "FORMAT_INVALID", "UNPARSEABLE",
                                             "MULTIPLE_CANDIDATES", "EMPTY"}


@pytest.mark.parametrize("ending,value,unit", REAL_LATEX_ENDINGS)
def test_the_contract_does_not_read_latex_but_the_recovery_rule_does(ending, value, unit):
    assert rc2.assess(f"t\n</think>\n{ending}", hit_token_limit=False, thinking_expected=True).status == "UNPARSEABLE"
    rec = rc2.recover_final(ending)
    assert rec.status == "RECOVERED" and rec.parsed.value == pytest.approx(value) and rec.parsed.unit == unit


def test_recovery_refuses_prose_disagreement_and_empty_text():
    assert rc2.recover_final("The final answer is clear from the above.").status == "NOT_RECOVERED"
    assert rc2.recover_final("Final answer: 3 m\n\nFinal answer: 4 m").status == "NOT_RECOVERED"
    assert rc2.recover_final("").status == "NOT_RECOVERED"
    sci = rc2.recover_final("Final answer: $3.2 \\times 10^{-5} \\, \\text{C}$")
    assert sci.status == "RECOVERED" and sci.parsed.value == pytest.approx(3.2e-5) and sci.parsed.unit == "C"
    deg = rc2.recover_final("Final answer: $30^\\circ$")
    assert deg.status == "RECOVERED" and deg.parsed.unit == "deg"


def test_user_turn_states_the_unit_when_asked():
    assert rc2.user_turn("A car.", "m/s^2").endswith("Give the final answer in m/s\u00b2.")
    assert rc2.user_turn("A car.", None).endswith("A car.")
