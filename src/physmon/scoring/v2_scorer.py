"""Teacher-forced scoring and output parsing that obey the Stage 14.3 scoring contract (Stage 14.7).

Rules implemented (docs/stage14/scoring_contract.md, section 4):
  1. the instruction is `instruction_for(wrapper)` and the scored string is `render_target(wrapper, ...)`, so the
     scored string is the string the model is told to emit;
  2. a chat-templated prompt is tokenized with `add_special_tokens=False` so BOS appears exactly once, and a prompt
     that starts with more than one is a failed record, not a warning;
  3. only `answer_span(n_prompt, n_target)` is scored, and separate tokenization must equal joint tokenization;
  5. every score carries its fingerprint, wrapper, prompt hash, token ids and span;
  7. a generation that does not parse is a recorded outcome, never a zero.

The model is abstracted as a callable returning log-probabilities, so the logic is tested with stubs and with tiny
randomly initialised models on CPU; no real checkpoint is needed to test it.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from physmon.benchmark import scoring_contract as sc

LogprobFn = Callable[[Sequence[int]], np.ndarray]  # ids -> array (len(ids), vocab) of log-probabilities


@dataclass
class TokenizedPair:
    prompt_ids: list[int]
    target_ids: list[int]
    formatted_prompt: str
    prompt_sha256: str
    n_leading_special: int
    boundary_ok: bool
    span: dict[str, int] = field(default_factory=dict)
    status: str = "OK"  # OK | DUPLICATE_SPECIAL_TOKEN | BOUNDARY_MISMATCH


@dataclass
class ScoreRecord:
    status: str
    wrapper_id: str
    contract_fingerprint: str
    prompt_sha256: str
    target_text: str
    target_ids: list[int]
    span_start: int | None = None
    span_end: int | None = None
    gold_logprob_raw: float | None = None  # the summed log-probability of the target string
    gold_logprob_per_token: list[float] | None = None
    n_prompt_tokens: int | None = None
    detail: str = ""


def build_chat_prompt(tokenizer: Any, system: str, user: str) -> str:
    """The model's native chat template with the generation prompt, as a string."""

    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def tokenize_pair(tokenizer: Any, formatted_prompt: str, target_text: str) -> TokenizedPair:
    """Tokenize a chat-templated prompt and a target string under the contract (BOS once, exact boundary)."""

    prompt_ids = list(tokenizer(formatted_prompt, add_special_tokens=False).input_ids)
    target_ids = list(tokenizer(target_text, add_special_tokens=False).input_ids)
    joint = list(tokenizer(formatted_prompt + target_text, add_special_tokens=False).input_ids)
    bos = getattr(tokenizer, "bos_token_id", None)
    leading = sc.leading_special_count(prompt_ids, bos)
    boundary_ok = prompt_ids + target_ids == joint
    status = "OK"
    if leading > 1:
        status = "DUPLICATE_SPECIAL_TOKEN"
    elif not boundary_ok:
        status = "BOUNDARY_MISMATCH"
    pair = TokenizedPair(prompt_ids, target_ids, formatted_prompt,
                         hashlib.sha256(formatted_prompt.encode("utf-8")).hexdigest(), leading, boundary_ok,
                         status=status)
    if prompt_ids and target_ids:
        pair.span = sc.answer_span(len(prompt_ids), len(target_ids))
    return pair


def score_pair(logprobs: LogprobFn, pair: TokenizedPair, wrapper_id: str, target_text: str) -> ScoreRecord:
    """Summed teacher-forced log-probability of the target over exactly the contract span."""

    record = ScoreRecord(status=pair.status, wrapper_id=wrapper_id, contract_fingerprint=sc.contract_fingerprint(),
                         prompt_sha256=pair.prompt_sha256, target_text=target_text, target_ids=pair.target_ids,
                         n_prompt_tokens=len(pair.prompt_ids))
    if pair.status != "OK" or not pair.span:
        record.detail = ("a failed tokenization record is not scored" if not pair.span or pair.status != "OK" else "")
        record.status = pair.status if pair.status != "OK" else "NOT_EVALUATED"
        return record
    ids = pair.prompt_ids + pair.target_ids
    table = np.asarray(logprobs(ids), dtype=float)
    if table.shape[0] != len(ids):
        raise ValueError(f"log-probability table has {table.shape[0]} rows for {len(ids)} tokens")
    start, end = pair.span["start"], pair.span["end"]
    per_token = [float(table[position - 1, ids[position]]) for position in range(start, end)]
    record.span_start, record.span_end = start, end
    record.gold_logprob_per_token = per_token
    record.gold_logprob_raw = float(sum(per_token))
    return record


def make_hf_logprob_fn(model: Any, device: str | None = None) -> LogprobFn:
    """Wrap a Hugging Face causal LM as a log-probability callable (torch imported lazily)."""

    import torch

    target_device = device or str(next(model.parameters()).device)

    def run(ids: Sequence[int]) -> np.ndarray:
        with torch.no_grad():
            tensor = torch.tensor([list(ids)], device=target_device)
            logits = model(tensor).logits[0].float()
            return torch.log_softmax(logits, dim=-1).cpu().numpy()

    return run


def greedy_generate_counted(model: Any, tokenizer: Any, formatted_prompt: str, max_new_tokens: int = 40) -> tuple[str, int, bool]:
    """Deterministic greedy continuation of a chat-templated prompt (BOS once): (text, new tokens, hit the token limit).

    The limit counts as hit when the model produced `max_new_tokens` tokens without an end-of-sequence token.
    """

    import torch

    ids = tokenizer(formatted_prompt, add_special_tokens=False, return_tensors="pt").input_ids
    ids = ids.to(next(model.parameters()).device)
    with torch.no_grad():
        output = model.generate(ids, attention_mask=torch.ones_like(ids), do_sample=False,
                                max_new_tokens=max_new_tokens, pad_token_id=getattr(tokenizer, "eos_token_id", None))
    new_tokens = output[0][ids.shape[1]:]
    eos = getattr(tokenizer, "eos_token_id", None)
    ended = eos is not None and bool((new_tokens == eos).any().item())
    return tokenizer.decode(new_tokens, skip_special_tokens=True), int(new_tokens.shape[0]), (
        int(new_tokens.shape[0]) >= max_new_tokens and not ended)


def greedy_generate(model: Any, tokenizer: Any, formatted_prompt: str, max_new_tokens: int = 40) -> str:
    """Deterministic greedy continuation of a chat-templated prompt (BOS once)."""

    return greedy_generate_counted(model, tokenizer, formatted_prompt, max_new_tokens)[0]


# --- parsing --------------------------------------------------------------------------------------

_NUMBER = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
_FIND = {
    "plain": re.compile(rf"^\s*(?P<v>{_NUMBER}) (?P<u>[^\s.][^\n]*?)\.?\s*$", re.M),
    "answer_line": re.compile(rf"Answer: (?P<v>{_NUMBER}) (?P<u>[^\n]*?)\.?\s*$", re.M),
    "boxed": re.compile(rf"\\boxed\{{(?P<v>{_NUMBER}) (?P<u>[^}}\n]*)\}}"),
    "json": re.compile(rf'\{{"value": (?P<v>{_NUMBER}), "unit": "(?P<u>[^"\n]*)"\}}'),
    "sentence": re.compile(rf"The answer is (?P<v>{_NUMBER}) (?P<u>[^\n]*?)\.?\s*$", re.M),
}
_FIND["decimal_plain"] = _FIND["answer_line"]
_FIND["scientific"] = _FIND["answer_line"]


@dataclass
class ParsedOutput:
    status: str  # PARSED | UNPARSEABLE | MULTIPLE_CANDIDATES | EMPTY
    value: float | None = None
    unit: str | None = None
    value_text: str | None = None  # the number exactly as printed, for its precision


def normalise_unit(text: str) -> str:
    return (text.strip().rstrip(".").replace("\u00b7", "*").replace("\u00b2", "^2").replace("\u00b3", "^3")
            .replace(" ", ""))


def parse_wrapped(wrapper_id: str, text: str) -> ParsedOutput:
    """Parse a generation under its wrapper. Zero or several candidates are outcomes of their own."""

    if not text.strip():
        return ParsedOutput("EMPTY")
    matches = list(_FIND[wrapper_id].finditer(text))
    if not matches:
        return ParsedOutput("UNPARSEABLE")
    if len(matches) > 1:
        return ParsedOutput("MULTIPLE_CANDIDATES")
    return ParsedOutput("PARSED", float(matches[0].group("v")), normalise_unit(matches[0].group("u")),
                        matches[0].group("v"))


CORRECTNESS_RULE = ("unit matches; the answer equals the gold at the answer's own printed precision (|a - g| is at most "
                    "half a unit in the last printed place) and is within 0.5% of the gold")
COARSE_REL_TOL = 5e-3  # guard so that a very coarse answer ("2" for 2.178) is not accepted by the rounding test
STRICT_REL_TOL = 1e-3  # sensitivity rule: the relative tolerance the code used before the rule was declared


def half_unit_in_last_place(text: str) -> float:
    """Half a unit of the last printed digit: 0.005 for '2.18', 0.5 for '36', 5 for '5e1'."""

    from decimal import Decimal

    return float(Decimal("0.5") * Decimal(10) ** Decimal(text).as_tuple().exponent)


def relative_error(parsed: ParsedOutput, gold_value: float) -> float | None:
    """|answer - gold| / |gold| for a parsed answer, else None (nothing to compare)."""

    if parsed.status != "PARSED":
        return None
    return abs(parsed.value - gold_value) / max(abs(gold_value), 1e-300)


def classify_answer(parsed: ParsedOutput, gold_value: float, gold_unit: str, rel_tol: float | None = None) -> str:
    """`correct`, `wrong`, or the parse status when there is nothing to compare (never `wrong` by default).

    Without `rel_tol` the declared rule (`CORRECTNESS_RULE`) applies. With `rel_tol` a plain relative tolerance is used
    (the strict sensitivity rule). The declared rule is post hoc relative to job 399539 (journal J14.7-020), chosen because
    a plain relative tolerance either rejects a correctly rounded answer (0.1%) or accepts a copy of the near-match cue (0.5%).
    """

    if parsed.status != "PARSED":
        return parsed.status
    right_unit = parsed.unit == normalise_unit(gold_unit)
    error = abs(parsed.value - gold_value)
    if rel_tol is not None:
        right_value = error <= rel_tol * max(abs(gold_value), 1e-300)
    else:
        right_value = (error <= half_unit_in_last_place(parsed.value_text) * (1 + 1e-9)
                       and error <= COARSE_REL_TOL * max(abs(gold_value), 1e-300))
    return "correct" if right_unit and right_value else "wrong"
