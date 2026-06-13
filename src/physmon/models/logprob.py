"""Log-probability helpers for PhysMon Stage 2 validation.

Reference: `physmon_proposal.pdf` §3.3 and Part IV.2 of the implementation brief.
"""

from __future__ import annotations

from typing import Any

import torch

from physmon.models.loader import LoadedModelBundle


DEFAULT_TOP_K = 10


def compute_reference_answer_logprob(
    bundle: LoadedModelBundle,
    prompt: str,
    answer: str,
) -> float:
    """Compute log p_theta(answer | prompt) from the Hugging Face causal LM.

    Args:
        bundle: Loaded model bundle.
        prompt: Prompt text.
        answer: Reference answer string.

    Returns:
        Sum of token log-probabilities for the answer continuation.
    """

    device = next(bundle.hf_model.parameters()).device
    prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(device)
    answer_ids = bundle.tokenizer(answer, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
    full_ids = torch.cat([prompt_ids, answer_ids], dim=1)

    with torch.no_grad():
        logits = bundle.hf_model(full_ids).logits
    log_probs = torch.log_softmax(logits[:, :-1, :], dim=-1)

    answer_start = prompt_ids.shape[1] - 1
    answer_end = full_ids.shape[1] - 1
    answer_token_targets = full_ids[:, answer_start + 1 : answer_end + 1]
    answer_token_logprobs = log_probs[:, answer_start:answer_end, :].gather(
        dim=-1,
        index=answer_token_targets.unsqueeze(-1),
    )
    return float(answer_token_logprobs.sum().item())


def get_next_token_topk(
    bundle: LoadedModelBundle,
    prompt: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """Return the top-k next-token distribution after a prompt.

    Args:
        bundle: Loaded model bundle.
        prompt: Prompt text.
        top_k: Number of next-token entries to return.

    Returns:
        List of dictionaries with token ids, decoded strings, logits, and probabilities.
    """

    device = next(bundle.hf_model.parameters()).device
    prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(device)
    with torch.no_grad():
        logits = bundle.hf_model(prompt_ids).logits[:, -1, :]

    probabilities = torch.softmax(logits, dim=-1)
    topk = torch.topk(probabilities, k=top_k, dim=-1)

    results: list[dict[str, Any]] = []
    for token_id, probability in zip(topk.indices[0].tolist(), topk.values[0].tolist(), strict=True):
        results.append(
            {
                "token_id": token_id,
                "token_text": bundle.tokenizer.decode([token_id]),
                "probability": float(probability),
                "logit": float(logits[0, token_id].item()),
            }
        )
    return results


def run_deterministic_generation(bundle: LoadedModelBundle, prompt: str, max_new_tokens: int = 12) -> str:
    """Run deterministic greedy generation on the Hugging Face causal LM.

    Args:
        bundle: Loaded model bundle.
        prompt: Prompt text.
        max_new_tokens: Generation length.

    Returns:
        Decoded generated continuation including the prompt.
    """

    device = next(bundle.hf_model.parameters()).device
    prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(device)
    with torch.no_grad():
        generated = bundle.hf_model.generate(
            prompt_ids,
            do_sample=False,
            temperature=1.0,
            max_new_tokens=max_new_tokens,
        )
    return bundle.tokenizer.decode(generated[0], skip_special_tokens=True)
