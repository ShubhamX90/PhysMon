"""Tests for the frozen scoring contract (Stage 14.3): wrappers, spans, and special-token checks."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402

RECORDS = REPO_ROOT / "results/stage6/behavioural_full_rerun/prompt_records.jsonl"


def _answers() -> list[str]:
    seen = {}
    for line in RECORDS.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if int(record["variant_id"]) == 0:
            seen[record["template_id"]] = record["correct_answer"]
    return sorted(set(seen.values()))


def test_every_committed_reference_answer_splits_into_value_and_unit():
    answers = _answers()
    assert len(answers) > 50
    for answer in answers:
        value, unit = sc.split_answer(answer)
        assert float(value) == float(value) and unit


def test_all_wrappers_are_equal_in_meaning_for_every_committed_answer():
    for answer in _answers():
        value_text, unit = sc.split_answer(answer)
        reference = float(value_text)
        for wrapper_id in sc.WRAPPERS:
            target = sc.render_target(wrapper_id, value_text, unit)
            value, parsed_unit = sc.parse_target(wrapper_id, target)
            assert math.isclose(value, reference, rel_tol=1e-12), (wrapper_id, answer, target)
            assert parsed_unit == unit, (wrapper_id, answer, target)


def test_notation_wrappers_preserve_the_value():
    assert sc.render_target("decimal_plain", "1.124e6", "Pa") == "Answer: 1124000 Pa"
    assert sc.render_target("decimal_plain", "3.0e-4", "C") == "Answer: 0.00030 C"
    assert sc.render_target("scientific", "6.928", "N*m") == "Answer: 6.928e0 N*m"
    assert sc.render_target("scientific", "0.4495", "m") == "Answer: 4.495e-1 m"
    assert sc.render_target("scientific", "10.0", "J") == "Answer: 1e1 J"
    assert sc.render_target("plain", "6.928", "N*m") == "6.928 N*m"
    assert sc.render_target("boxed", "6.928", "N*m") == "\\boxed{6.928 N*m}"
    assert sc.render_target("json", "6.928", "N*m") == '{"value": 6.928, "unit": "N*m"}'


def test_malformed_answers_are_rejected_not_guessed():
    for bad in ("6.928", "N*m", "about 7 N", ""):
        with pytest.raises(ValueError):
            sc.split_answer(bad)
    with pytest.raises(ValueError):
        sc.parse_target("boxed", "Answer: 6.928 N*m")


def test_answer_line_wrapper_is_exactly_the_stage_6_system_prompt():
    spec = importlib.util.spec_from_file_location("rb", REPO_ROOT / "scripts/run_behavioural.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert sc.instruction_for("answer_line") == module.SYSTEM_PROMPT


def test_each_wrapper_has_a_distinct_instruction_that_names_its_format():
    instructions = {wid: sc.instruction_for(wid) for wid in sc.WRAPPERS}
    assert len(set(instructions.values())) == len(sc.WRAPPERS)
    for wid, text in instructions.items():
        assert sc.WRAPPERS[wid].format_line in text


def test_fingerprint_is_stable_and_sensitive_to_the_frozen_strings(monkeypatch):
    first = sc.contract_fingerprint()
    assert first == sc.contract_fingerprint() and len(first) == 64
    monkeypatch.setattr(sc, "INSTRUCTION_TEMPLATE", sc.INSTRUCTION_TEMPLATE + " ")
    assert sc.contract_fingerprint() != first


def test_answer_span_covers_only_answer_tokens():
    span = sc.answer_span(n_prompt_tokens=128, n_answer_tokens=7)
    assert span == {"start": 128, "end": 135, "logit_start": 127, "logit_end": 134}
    # The scored logit positions count equals the answer length, and none lies before the prompt end - 1.
    assert span["logit_end"] - span["logit_start"] == 7
    with pytest.raises(ValueError):
        sc.answer_span(0, 3)
    with pytest.raises(ValueError):
        sc.answer_span(10, 0)


def test_leading_special_count_detects_a_duplicated_bos():
    assert sc.leading_special_count([128000, 128000, 128006], 128000) == 2
    assert sc.leading_special_count([128000, 128006], 128000) == 1
    assert sc.leading_special_count([151644, 8948], None) == 0
    assert sc.leading_special_count([], 128000) == 0
