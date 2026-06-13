"""Prompt-side activation extraction helpers for Stage 2 validation.

Reference: `physmon_proposal.pdf` §9 and Part IV.1 of the implementation brief.
"""

from __future__ import annotations

from typing import Any
import random

import numpy as np
import torch

from physmon.models.loader import LoadedModelBundle


HOOK_RESID_POST = "hook_resid_post"
HOOK_ATTN_OUT = "hook_attn_out"
HOOK_MLP_OUT = "hook_mlp_out"
EXTRACTION_SITE_TO_HOOK = {
    "resid_post": HOOK_RESID_POST,
    "attn_out": HOOK_ATTN_OUT,
    "mlp_out": HOOK_MLP_OUT,
}
ACTIVATION_SITES = ("resid_post", "attn_out", "mlp_out")


def set_global_seed(seed: int) -> None:
    """Set Python, NumPy, and Torch RNG state for deterministic validation.

    Args:
        seed: Seed value.

    Returns:
        `None`.
    """

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def find_token_positions(
    bundle: LoadedModelBundle, prompt: str, cue_substring: str
) -> tuple[torch.Tensor, int, int]:
    """Tokenize a prompt and locate the cue token and last prompt token positions.

    Args:
        bundle: Loaded model bundle with tokenizer/model.
        prompt: Prompt text used for validation.
        cue_substring: Substring used to locate the cue token.

    Returns:
        Tuple of `(tokens, cue_token_index, last_prompt_token_index)`.
    """

    if bundle.hooked_model is None:
        raise NotImplementedError("Prompt-side hook extraction is only implemented for TransformerLens.")

    tokens = bundle.hooked_model.to_tokens(prompt)
    token_values = tokens[0].tolist()
    cue_token_ids = bundle.tokenizer(cue_substring, add_special_tokens=False).input_ids
    if not cue_token_ids:
        raise ValueError(f"Tokenization produced no ids for cue substring '{cue_substring}'.")

    cue_start_index = None
    window_size = len(cue_token_ids)
    for index in range(len(token_values) - window_size + 1):
        if token_values[index : index + window_size] == cue_token_ids:
            cue_start_index = index
    if cue_start_index is None:
        raise ValueError(f"Could not locate cue substring '{cue_substring}' in tokenized prompt.")
    cue_token_index = cue_start_index + window_size - 1
    last_prompt_token_index = tokens.shape[1] - 1
    return tokens, cue_token_index, last_prompt_token_index


def extract_prompt_side_activations(
    bundle: LoadedModelBundle,
    prompt: str,
    cue_substring: str,
) -> dict[str, Any]:
    """Extract prompt-side activations for all layers at cue and final positions.

    Args:
        bundle: Loaded model bundle.
        prompt: Validation prompt text.
        cue_substring: Cue marker substring used to locate the prompt-side cue token.

    Returns:
        Dictionary containing activation tensors and metadata.
    """

    if bundle.hooked_model is None:
        raise NotImplementedError("Prompt-side hook extraction is only implemented for TransformerLens.")

    tokens, cue_token_index, last_prompt_token_index = find_token_positions(bundle, prompt, cue_substring)
    def names_filter(name: str) -> bool:
        return any(name.endswith(hook_name) for hook_name in EXTRACTION_SITE_TO_HOOK.values())

    _, cache = bundle.hooked_model.run_with_cache(tokens, names_filter=names_filter)

    activations: dict[str, Any] = {
        "prompt_length": int(tokens.shape[1]),
        "cue_token_index": cue_token_index,
        "last_prompt_token_index": last_prompt_token_index,
        "layers": bundle.hooked_model.cfg.n_layers,
        "hidden_dim": bundle.hooked_model.cfg.d_model,
        "sites": {},
    }

    for site_name, hook_name in EXTRACTION_SITE_TO_HOOK.items():
        cue_activations = []
        last_prompt_activations = []
        for layer_index in range(bundle.hooked_model.cfg.n_layers):
            cache_key = f"blocks.{layer_index}.{hook_name}"
            tensor = cache[cache_key].detach().cpu()
            cue_activations.append(tensor[:, cue_token_index, :])
            last_prompt_activations.append(tensor[:, last_prompt_token_index, :])
        activations["sites"][site_name] = {
            "cue_token": torch.stack(cue_activations),
            "last_prompt_token": torch.stack(last_prompt_activations),
        }
    return activations


def run_zero_ablation_check(
    bundle: LoadedModelBundle,
    prompt: str,
    layer_index: int = 0,
) -> dict[str, Any]:
    """Apply a simple zero ablation at one residual-stream hook and compare logits.

    Args:
        bundle: Loaded model bundle.
        prompt: Validation prompt text.
        layer_index: Layer index whose residual stream is zero-ablated.

    Returns:
        Dictionary describing the observed logit difference.
    """

    if bundle.hooked_model is None:
        raise NotImplementedError("Zero-ablation validation is only implemented for TransformerLens.")

    tokens = bundle.hooked_model.to_tokens(prompt)
    clean_logits = bundle.hooked_model(tokens)

    def zero_hook(activation: torch.Tensor, hook: Any | None = None) -> torch.Tensor:
        del hook
        return torch.zeros_like(activation)

    ablated_logits = bundle.hooked_model.run_with_hooks(
        tokens,
        fwd_hooks=[(f"blocks.{layer_index}.{HOOK_RESID_POST}", zero_hook)],
    )
    max_logit_difference = torch.max(torch.abs(clean_logits - ablated_logits)).item()
    return {
        "patching_ok": bool(max_logit_difference > 0.0),
        "max_logit_difference": max_logit_difference,
        "layer_index": layer_index,
    }


def compare_activation_runs(
    first_run: dict[str, Any], second_run: dict[str, Any], tolerance: float = 1e-6
) -> bool:
    """Compare two activation-extraction runs for deterministic equality.

    Args:
        first_run: First extraction payload.
        second_run: Second extraction payload.
        tolerance: Absolute tolerance for tensor equality.

    Returns:
        `True` if all extracted tensors match within tolerance.
    """

    for site_name in ACTIVATION_SITES:
        first_site = first_run["sites"][site_name]
        second_site = second_run["sites"][site_name]
        for position_name in ("cue_token", "last_prompt_token"):
            if not torch.allclose(
                first_site[position_name], second_site[position_name], atol=tolerance, rtol=0.0
            ):
                return False
    return True
