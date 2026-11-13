"""Batched, sampled generation behind one interface, with a Hugging Face backend and a vLLM backend (Stage 15).

Lifted from `scripts/v2/s164_thinking_run.py` (left-padded batched generation, cut at the first end-of-sequence token, out-of-
memory fallback) so runners stop loading each other by file path. Both backends take prompts as token ids produced here with
`add_special_tokens=False`, so a chat template's own beginning-of-sequence token appears exactly once (the Stage 14.3 double-BOS
finding), and both report, per request, the decoded text, the number of new tokens and whether the token limit was hit.

Sampling defaults come from each model's published `generation_config.json`; Qwen3 in non-thinking mode uses the model card's
non-thinking values. The vLLM backend sets a per-request seed, but its samples are not bit-reproducible: batch-invariant kernels
are off and prefix caching is on, so logits can change with batch composition (recorded as `seed_scope`
"request_not_batch_invariant"); the Hugging Face backend seeds per batch (`seed_scope` "batch").
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

QWEN3_NON_THINKING = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0}  # Qwen3 model card, non-thinking mode
QWEN3_THINKING = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0}  # Qwen3 model card, thinking mode


@dataclass(frozen=True)
class SamplingSpec:
    do_sample: bool = True
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 0  # 0 = off
    min_p: float = 0.0
    repetition_penalty: float = 1.0
    source: str = "explicit"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenRequest:
    request_id: str
    prompt_ids: list[int]
    seed: int


@dataclass
class GenResult:
    request_id: str
    text: str
    n_new_tokens: int
    hit_limit: bool
    finish_reason: str
    oom_fallback: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


def sampling_from_generation_config(model_dir: str | Path, *, thinking: bool | None = None, family: str = "") -> SamplingSpec:
    """The model's published sampling defaults (generation_config.json); Qwen3 uses its card's values for the chosen mode."""

    if family == "qwen3":
        values = QWEN3_THINKING if thinking else QWEN3_NON_THINKING
        return SamplingSpec(True, values["temperature"], values["top_p"], values["top_k"], values["min_p"], 1.0,
                            f"qwen3-model-card:{'thinking' if thinking else 'non-thinking'}")
    config = json.loads((Path(model_dir) / "generation_config.json").read_text(encoding="utf-8"))
    return SamplingSpec(
        do_sample=bool(config.get("do_sample", True)),
        temperature=float(config.get("temperature", 1.0)),
        top_p=float(config.get("top_p", 1.0)),
        top_k=int(config.get("top_k", 0) or 0),
        min_p=float(config.get("min_p", 0.0) or 0.0),
        repetition_penalty=float(config.get("repetition_penalty", 1.0) or 1.0),
        source="generation_config.json",
    )


def chat_prompt_ids(tokenizer: Any, user_text: str, *, enable_thinking: bool | None = None) -> tuple[str, list[int]]:
    """The chat-templated prompt (user turn only, generation prompt added) as text and as token ids, BOS at most once."""

    kwargs: dict[str, Any] = {}
    if enable_thinking is not None:
        kwargs["enable_thinking"] = enable_thinking
    text = tokenizer.apply_chat_template([{"role": "user", "content": user_text}], tokenize=False, add_generation_prompt=True,
                                         **kwargs)
    ids = list(tokenizer(text, add_special_tokens=False).input_ids)
    bos = getattr(tokenizer, "bos_token_id", None)
    if bos is not None and len(ids) > 1 and ids[0] == bos and ids[1] == bos:
        raise ValueError("chat prompt starts with a duplicated beginning-of-sequence token")
    return text, ids


def eos_ids(generation_config: Any, tokenizer: Any) -> set[int]:
    raw = getattr(generation_config, "eos_token_id", None) if generation_config is not None else None
    if raw is None:
        raw = tokenizer.eos_token_id
    return set(raw) if isinstance(raw, (list, tuple)) else {int(raw)}


class HFBackend:
    """Hugging Face `generate`, left-padded batches of `batch_size`, out-of-memory fallback to single sequences."""

    name = "hf"

    def __init__(self, model: Any, tokenizer: Any, batch_size: int = 8):
        self.model = model
        self.tokenizer = tokenizer
        self.batch_size = batch_size
        if tokenizer.pad_token_id is None:  # Llama-3 tokenizers have no padding token
            tokenizer.pad_token = tokenizer.eos_token
        self.stops = eos_ids(getattr(model, "generation_config", None), tokenizer)

    def _batch(self, requests: Sequence[GenRequest], max_new_tokens: int, sampling: SamplingSpec) -> list[GenResult]:
        import torch

        pad = self.tokenizer.pad_token_id
        width = max(len(r.prompt_ids) for r in requests)
        ids = torch.full((len(requests), width), pad, dtype=torch.long)
        mask = torch.zeros((len(requests), width), dtype=torch.long)
        for i, r in enumerate(requests):
            ids[i, width - len(r.prompt_ids):] = torch.tensor(r.prompt_ids, dtype=torch.long)
            mask[i, width - len(r.prompt_ids):] = 1
        device = next(self.model.parameters()).device
        ids, mask = ids.to(device), mask.to(device)
        torch.manual_seed(requests[0].seed)
        kwargs: dict[str, Any] = {"max_new_tokens": max_new_tokens, "pad_token_id": pad, "attention_mask": mask}
        # Every sampling field is passed explicitly: transformers otherwise fills unset fields from global defaults
        # (top_k=50), and the record would claim settings that were not used. top_k=0 disables top-k.
        if sampling.do_sample:
            kwargs.update(do_sample=True, temperature=sampling.temperature, top_p=sampling.top_p, top_k=sampling.top_k,
                          min_p=sampling.min_p if sampling.min_p else None, repetition_penalty=sampling.repetition_penalty)
        else:
            kwargs.update(do_sample=False, temperature=None, top_p=None, top_k=None, min_p=None, repetition_penalty=1.0)
        with torch.no_grad():
            out = self.model.generate(input_ids=ids, **kwargs)
        results = []
        for i, r in enumerate(requests):
            generated = out[i, width:].tolist()
            cut = next((j for j, t in enumerate(generated) if t in self.stops), None)
            used = generated if cut is None else generated[:cut]
            results.append(GenResult(r.request_id, self.tokenizer.decode(used, skip_special_tokens=False),
                                     len(used) + (0 if cut is None else 1), cut is None, "length" if cut is None else "stop",
                                     extra={"seed_scope": "batch"}))
        return results

    def generate(self, requests: Sequence[GenRequest], max_new_tokens: int, sampling: SamplingSpec) -> list[GenResult]:
        import torch

        ordered = sorted(requests, key=lambda r: (len(r.prompt_ids), r.request_id))
        results: dict[str, GenResult] = {}
        for start in range(0, len(ordered), self.batch_size):
            batch = ordered[start:start + self.batch_size]
            try:
                outputs = self._batch(batch, max_new_tokens, sampling)
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                outputs = []
                for r in batch:
                    single = self._batch([r], max_new_tokens, sampling)[0]
                    single.oom_fallback = True
                    outputs.append(single)
            for o in outputs:
                results[o.request_id] = o
        return [results[r.request_id] for r in requests]


class VLLMBackend:
    """vLLM offline generation from token ids, per-request seeds, special tokens kept in the text (so `</think>` survives)."""

    name = "vllm"

    def __init__(self, model_dir: str | Path, *, dtype: str = "bfloat16", max_model_len: int = 16384,
                 gpu_memory_utilization: float = 0.88, seed: int = 0, enforce_eager: bool = False):
        import os

        os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"  # never fork the engine (jobs 444874-444879); hard-set
        from vllm import LLM

        self.llm = LLM(model=str(model_dir), tokenizer=str(model_dir), dtype=dtype, max_model_len=max_model_len,
                       gpu_memory_utilization=gpu_memory_utilization, seed=seed, trust_remote_code=False,
                       enforce_eager=enforce_eager, generation_config="vllm")
        self.config = {"dtype": dtype, "max_model_len": max_model_len, "gpu_memory_utilization": gpu_memory_utilization,
                       "enforce_eager": enforce_eager}

    def generate(self, requests: Sequence[GenRequest], max_new_tokens: int, sampling: SamplingSpec) -> list[GenResult]:
        from vllm import SamplingParams
        from vllm.inputs import TokensPrompt

        prompts = [TokensPrompt(prompt_token_ids=list(r.prompt_ids)) for r in requests]
        params = []
        for r in requests:
            if sampling.do_sample:
                params.append(SamplingParams(n=1, temperature=sampling.temperature, top_p=sampling.top_p,
                                             top_k=sampling.top_k if sampling.top_k else -1, min_p=sampling.min_p,
                                             repetition_penalty=sampling.repetition_penalty, seed=r.seed,
                                             max_tokens=max_new_tokens, skip_special_tokens=False))
            else:
                params.append(SamplingParams(n=1, temperature=0.0, max_tokens=max_new_tokens, skip_special_tokens=False,
                                             seed=r.seed))
        outputs = self.llm.generate(prompts, params, use_tqdm=False)
        results = []
        for r, out in zip(requests, outputs, strict=True):
            completion = out.outputs[0]
            hit = completion.finish_reason == "length"
            results.append(GenResult(r.request_id, completion.text, len(completion.token_ids), hit,
                                     str(completion.finish_reason), extra={"seed_scope": "request_not_batch_invariant"}))
        return results
