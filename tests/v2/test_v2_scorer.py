"""Tests for the contract-compliant scorer and parser (Stage 14.7). No real checkpoint is loaded."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402


class FakeTokenizer:
    """Character tokenizer: '<s>' is one special id (1); optionally merges '\\n' with a following digit."""

    bos_token_id = 1

    def __init__(self, merge_newline_digit=False, add_bos=True):
        self.merge = merge_newline_digit
        self.add_bos = add_bos

    def _ids(self, text):
        ids, i = [], 0
        while i < len(text):
            if text.startswith("<s>", i):
                ids.append(1)
                i += 3
            elif self.merge and text[i] == "\n" and i + 1 < len(text) and text[i + 1].isdigit():
                ids.append(1000 + ord(text[i + 1]))
                i += 2
            else:
                ids.append(10 + ord(text[i]))
                i += 1
        return ids

    def __call__(self, text, add_special_tokens=True):
        ids = self._ids(text)
        if add_special_tokens and self.add_bos:
            ids = [1] + ids
        return SimpleNamespace(input_ids=ids)


def stub_logprobs(ids):
    table = np.zeros((len(ids), 2000))
    for position in range(len(ids)):
        for token in range(2000):
            table[position, token] = -((token % 7) + (position % 3) + 1) / 10.0
    return table


def test_score_covers_exactly_the_answer_span_and_nothing_from_the_prompt():
    tok = FakeTokenizer()
    pair = vs.tokenize_pair(tok, "<s>Q?\n", "6.9")
    assert pair.status == "OK" and pair.n_leading_special == 1 and pair.boundary_ok
    record = vs.score_pair(stub_logprobs, pair, "plain", "6.9")
    ids = pair.prompt_ids + pair.target_ids
    expected = [-(((ids[p] % 7) + ((p - 1) % 3) + 1) / 10.0) for p in range(len(pair.prompt_ids), len(ids))]
    assert record.status == "OK"
    assert record.gold_logprob_per_token == pytest.approx(expected)
    assert record.gold_logprob_raw == pytest.approx(sum(expected))
    assert (record.span_start, record.span_end) == (len(pair.prompt_ids), len(ids))
    assert len(record.gold_logprob_per_token) == len(pair.target_ids)
    assert record.contract_fingerprint == sc.contract_fingerprint()


def test_a_duplicated_leading_bos_is_a_failed_record_not_a_score():
    pair = vs.tokenize_pair(FakeTokenizer(), "<s><s>Q?\n", "6.9")
    assert pair.status == "DUPLICATE_SPECIAL_TOKEN" and pair.n_leading_special == 2
    record = vs.score_pair(stub_logprobs, pair, "plain", "6.9")
    assert record.status == "DUPLICATE_SPECIAL_TOKEN" and record.gold_logprob_raw is None


def test_a_prompt_target_boundary_that_tokenizes_differently_is_not_scored():
    pair = vs.tokenize_pair(FakeTokenizer(merge_newline_digit=True), "<s>Q?\n", "6.9")
    assert pair.status == "BOUNDARY_MISMATCH" and not pair.boundary_ok
    record = vs.score_pair(stub_logprobs, pair, "plain", "6.9")
    assert record.status == "BOUNDARY_MISMATCH" and record.gold_logprob_raw is None


def test_a_table_with_the_wrong_number_of_rows_is_an_error_not_a_silent_score():
    pair = vs.tokenize_pair(FakeTokenizer(), "<s>Q?\n", "6.9")
    with pytest.raises(ValueError):
        vs.score_pair(lambda ids: np.zeros((len(ids) - 1, 2000)), pair, "plain", "6.9")


def _tiny_model(kind, vocab_size):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    if kind == "llama":
        config = transformers.LlamaConfig(vocab_size=vocab_size, hidden_size=16, intermediate_size=32,
                                          num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
                                          max_position_embeddings=1024)
        model = transformers.LlamaForCausalLM(config)
    else:
        config = transformers.Qwen2Config(vocab_size=vocab_size, hidden_size=16, intermediate_size=32,
                                          num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
                                          max_position_embeddings=1024)
        model = transformers.Qwen2ForCausalLM(config)
    return model.eval()


@pytest.mark.parametrize("kind", ["llama", "qwen"])
def test_real_tokenizer_and_a_tiny_random_model_score_the_contract_span_exactly(kind, tokenizer_for):
    torch = pytest.importorskip("torch")
    tok = tokenizer_for[kind]
    model = _tiny_model(kind, len(tok))
    system = sc.instruction_for("answer_line")
    prompt = vs.build_chat_prompt(tok, system, "A block has mass 2 kg and acceleration 3 m/s². What is the net force?")
    target = sc.render_target("answer_line", "6", "N")
    pair = vs.tokenize_pair(tok, prompt, target)
    assert pair.status == "OK" and pair.n_leading_special <= 1 and pair.boundary_ok
    record = vs.score_pair(vs.make_hf_logprob_fn(model, "cpu"), pair, "answer_line", target)
    # Independent recomputation straight from the model's logits.
    ids = torch.tensor([pair.prompt_ids + pair.target_ids])
    with torch.no_grad():
        table = torch.log_softmax(model(ids).logits[0].float(), dim=-1)
    expected = sum(float(table[p - 1, ids[0, p]]) for p in range(len(pair.prompt_ids), ids.shape[1]))
    assert record.gold_logprob_raw == pytest.approx(expected, abs=1e-5)
    assert len(record.gold_logprob_per_token) == len(pair.target_ids)
    assert isinstance(vs.greedy_generate(model, tok, prompt, max_new_tokens=4), str)


def test_llama_prompts_have_exactly_one_bos_under_the_new_path_and_two_under_the_legacy_path(llama_tokenizer):
    tok = llama_tokenizer
    prompt = vs.build_chat_prompt(tok, sc.instruction_for("answer_line"), "What is 2 plus 2?")
    new = vs.tokenize_pair(tok, prompt, "4")
    legacy = list(tok(prompt, add_special_tokens=True).input_ids)
    assert new.n_leading_special == 1 and sc.leading_special_count(legacy, tok.bos_token_id) == 2
    assert len(legacy) == len(new.prompt_ids) + 1


def test_every_wrapper_round_trips_through_the_parser_for_committed_answers():
    answers = set()
    for line in (REPO_ROOT / "results/stage6/behavioural_full_rerun/prompt_records.jsonl").read_text(
            encoding="utf-8").splitlines():
        answers.add(json.loads(line)["correct_answer"])
    for answer in sorted(answers):
        value_text, unit = sc.split_answer(answer)
        for wrapper_id in sc.WRAPPERS:
            parsed = vs.parse_wrapped(wrapper_id, sc.render_target(wrapper_id, value_text, unit))
            assert parsed.status == "PARSED", (wrapper_id, answer)
            assert vs.classify_answer(parsed, float(value_text), unit) == "correct", (wrapper_id, answer)


def test_parser_handles_stage_6_style_outputs_and_keeps_failures_as_outcomes():
    assert vs.classify_answer(vs.parse_wrapped("answer_line", "Answer: 6.928 N·m."), 6.928, "N*m") == "correct"
    assert vs.classify_answer(vs.parse_wrapped("answer_line", "Answer: 8 N·m."), 6.928, "N*m") == "wrong"
    assert vs.classify_answer(vs.parse_wrapped("answer_line", "Answer: 6.928 J"), 6.928, "N*m") == "wrong"
    assert vs.parse_wrapped("answer_line", "I think the torque is about seven.").status == "UNPARSEABLE"
    assert vs.parse_wrapped("answer_line", "Answer: 6.9 N*m\nAnswer: 8 N*m").status == "MULTIPLE_CANDIDATES"
    assert vs.parse_wrapped("answer_line", "   ").status == "EMPTY"
    # Nothing to compare is never classified as wrong or as a null.
    assert vs.classify_answer(vs.parse_wrapped("boxed", "no box here"), 1.0, "m") == "UNPARSEABLE"


def test_the_declared_rule_accepts_a_correctly_rounded_answer_and_rejects_a_copy_of_the_near_cue():
    # Job 399539 gold 2.1778 (instance 0) and 3.3011 (instance 1); the near-match cues were 2.17 and 3.31.
    def grade(text, gold, rel_tol=None):
        return vs.classify_answer(vs.parse_wrapped("answer_line", text), gold, "m/s^2", rel_tol=rel_tol)

    assert grade("Answer: 2.18 m/s^2", 2.1777777) == "correct"  # correctly rounded to 3 significant figures
    assert grade("Answer: 2.18 m/s^2", 2.1777777, rel_tol=vs.STRICT_REL_TOL) == "wrong"  # the old rule's miss
    assert grade("Answer: 2.17 m/s^2", 2.1777777) == "wrong"  # a copy of the near cue is not the answer
    assert grade("Answer: 3.31 m/s^2", 3.3011) == "wrong" and grade("Answer: 3.3 m/s^2", 3.3011) == "correct"
    assert grade("Answer: 2.2 m/s^2", 2.1777777) == "wrong"  # 1.0% off: rounding to one decimal is too coarse
    assert grade("Answer: 2 m/s^2", 2.1777777) == "wrong"
    assert grade("Answer: 2.178 m/s^2", 2.1777777) == "correct" and grade("Answer: 2.178 m/s", 2.1777777) == "wrong"
    assert grade("Answer: 2.45 m/s^2", 2.1777777) == "wrong"
    assert vs.half_unit_in_last_place("2.18") == pytest.approx(0.005)
    assert vs.half_unit_in_last_place("36") == pytest.approx(0.5)
    assert vs.half_unit_in_last_place("5e1") == pytest.approx(5.0)
    assert 0.0009 < vs.relative_error(vs.parse_wrapped("answer_line", "Answer: 2.18 m/s^2"), 2.1777777) < 0.0011
    assert vs.relative_error(vs.parse_wrapped("boxed", "no box"), 1.0) is None
