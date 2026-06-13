"""Prompt-side activation extraction helpers for Stage 2 validation.

Reference: `physmon_proposal.pdf` §9 and Part IV.1 of the implementation brief.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import random

import numpy as np
import torch

if TYPE_CHECKING:
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
DEFAULT_TARGET_SITES = ("resid_post", "attn_out", "mlp_out")
DTYPE_NAME_TO_TORCH = {
    "float16": torch.float16,
    "float32": torch.float32,
    "bfloat16": torch.bfloat16,
}


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


def extract_targeted_activations(
    model: Any,
    prompt: str,
    prompt_token_ids: list[int],
    cue_span_token_ids: list[int],
    layers: list[int] | None = None,
    sites: list[str] = list(DEFAULT_TARGET_SITES),
    dtype: str = "float16",
) -> dict[str, torch.Tensor]:
    """Extract prompt-side activations at only the scientifically targeted positions.

    Args:
        model: TransformerLens-compatible model supporting `run_with_cache(tokens, ...)`.
        prompt: Original prompt text, used for validation messages and auditability.
        prompt_token_ids: Token ids for the prompt exactly as provided to the model.
        cue_span_token_ids: Prompt-side token indices covering the cue span.
        layers: Optional explicit layer indices. `None` means all model layers.
        sites: Activation sites to extract. Supported values are `resid_post`,
            `attn_out`, and `mlp_out`.
        dtype: Output tensor dtype name. One of `float16`, `float32`, or `bfloat16`.

    Returns:
        Flat mapping from stable activation names such as
        `resid_post_last_prompt_layer0` or `mlp_out_cue_token1_layer12`
        to 1D hidden-state tensors on CPU.

    Reference:
        `physmon_proposal.pdf` §9 and the Stage 4/5 targeted extraction plan.
    """

    if not prompt_token_ids:
        raise ValueError("prompt_token_ids must be non-empty for prompt-side extraction.")
    if not cue_span_token_ids:
        raise ValueError("cue_span_token_ids must identify at least one prompt-side cue token.")
    if not prompt.strip():
        raise ValueError("prompt must be non-empty for targeted activation extraction.")

    prompt_length = len(prompt_token_ids)
    last_prompt_index = prompt_length - 1
    normalized_sites = _normalize_sites(sites)
    validated_layers = _validate_layers(model, layers)
    validated_cue_indices = _validate_prompt_indices(cue_span_token_ids, prompt_length)
    target_dtype = _resolve_output_dtype(dtype)
    token_tensor = torch.tensor(
        [prompt_token_ids],
        dtype=torch.long,
        device=_infer_model_device(model),
    )

    def names_filter(name: str) -> bool:
        return any(name.endswith(EXTRACTION_SITE_TO_HOOK[site_name]) for site_name in normalized_sites)

    _, cache = model.run_with_cache(token_tensor, names_filter=names_filter)
    extracted: dict[str, torch.Tensor] = {}

    for site_name in normalized_sites:
        hook_name = EXTRACTION_SITE_TO_HOOK[site_name]
        for layer_index in validated_layers:
            cache_key = f"blocks.{layer_index}.{hook_name}"
            if cache_key not in cache:
                raise KeyError(f"Activation cache is missing expected key '{cache_key}' for prompt {prompt!r}.")
            cached_tensor = cache[cache_key]
            if cached_tensor.ndim != 3 or cached_tensor.shape[1] < prompt_length:
                raise ValueError(
                    f"Cached tensor '{cache_key}' has shape {tuple(cached_tensor.shape)}, "
                    f"which is incompatible with prompt length {prompt_length}."
                )
            extracted[f"{site_name}_last_prompt_layer{layer_index}"] = _slice_hidden_state(
                cached_tensor,
                token_index=last_prompt_index,
                output_dtype=target_dtype,
            )
            for cue_offset, cue_index in enumerate(validated_cue_indices):
                extracted[f"{site_name}_cue_token{cue_offset}_layer{layer_index}"] = _slice_hidden_state(
                    cached_tensor,
                    token_index=cue_index,
                    output_dtype=target_dtype,
                )

    return extracted


def _normalize_sites(sites: list[str]) -> list[str]:
    """Validate extraction-site names and preserve caller order without duplicates."""

    if not sites:
        raise ValueError("sites must contain at least one supported activation site.")
    normalized: list[str] = []
    for site_name in sites:
        if site_name not in EXTRACTION_SITE_TO_HOOK:
            raise ValueError(
                f"Unsupported activation site '{site_name}'. Expected one of "
                f"{sorted(EXTRACTION_SITE_TO_HOOK)}."
            )
        if site_name not in normalized:
            normalized.append(site_name)
    return normalized


def _validate_layers(model: Any, layers: list[int] | None) -> list[int]:
    """Resolve and validate the requested layer indices."""

    total_layers = int(model.cfg.n_layers)
    if layers is None:
        return list(range(total_layers))
    if not layers:
        raise ValueError("layers must be non-empty when provided explicitly.")
    validated: list[int] = []
    for layer_index in layers:
        if layer_index < 0 or layer_index >= total_layers:
            raise ValueError(
                f"Layer index {layer_index} is out of range for a model with {total_layers} layers."
            )
        if layer_index not in validated:
            validated.append(layer_index)
    return validated


def _validate_prompt_indices(token_indices: list[int], prompt_length: int) -> list[int]:
    """Validate prompt-side token indices against the prompt length."""

    validated: list[int] = []
    for token_index in token_indices:
        if token_index < 0 or token_index >= prompt_length:
            raise ValueError(
                f"Prompt-side token index {token_index} is invalid for prompt length {prompt_length}."
            )
        validated.append(token_index)
    return validated


def _resolve_output_dtype(dtype_name: str) -> torch.dtype:
    """Resolve a human-readable dtype name into a Torch dtype."""

    try:
        return DTYPE_NAME_TO_TORCH[dtype_name]
    except KeyError as error:
        raise ValueError(
            f"Unsupported output dtype '{dtype_name}'. Expected one of {sorted(DTYPE_NAME_TO_TORCH)}."
        ) from error


def _infer_model_device(model: Any) -> torch.device:
    """Infer the device for prompt-token tensors from a model-like object."""

    if hasattr(model, "parameters"):
        try:
            return next(model.parameters()).device
        except (StopIteration, TypeError):
            pass
    return torch.device("cpu")


def _slice_hidden_state(
    cached_tensor: torch.Tensor,
    *,
    token_index: int,
    output_dtype: torch.dtype,
) -> torch.Tensor:
    """Extract one hidden-state vector and move it to CPU in the requested dtype."""

    return cached_tensor[0, token_index, :].detach().to(dtype=output_dtype).cpu()
