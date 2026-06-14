"""Unit tests for prompt-side hook and patching utilities."""

from __future__ import annotations

import pytest
import torch

from physmon.causal.patching import (
    validate_prompt_side_positions,
    zero_ablate_prompt_positions,
)
from physmon.models.hooks import (
    compare_activation_runs,
    extract_targeted_activations,
    find_cue_token_index,
)


def test_validate_prompt_side_positions_accepts_in_range_indices() -> None:
    """Prompt-side patching should accept positions strictly inside the prompt."""
    assert validate_prompt_side_positions(prompt_length=5, token_positions=[0, 2, 4]) == (0, 2, 4)


def test_validate_prompt_side_positions_rejects_generated_token_indices() -> None:
    """Generated-token indices must be rejected by the prompt-side guard."""
    with pytest.raises(ValueError):
        validate_prompt_side_positions(prompt_length=5, token_positions=[5])


def test_zero_ablate_prompt_positions_zeros_only_requested_positions() -> None:
    """Zero-ablation should touch only the approved prompt-side token positions."""
    activations = torch.ones(2, 6, 4)
    ablated = zero_ablate_prompt_positions(
        activations=activations,
        prompt_length=5,
        token_positions=[1, 3],
    )

    assert torch.all(ablated[:, 1, :] == 0)
    assert torch.all(ablated[:, 3, :] == 0)
    assert torch.all(ablated[:, 0, :] == 1)
    assert torch.all(ablated[:, 2, :] == 1)
    assert torch.all(ablated[:, 4, :] == 1)
    assert torch.all(ablated[:, 5, :] == 1)
    assert torch.all(activations == 1)


def test_compare_activation_runs_detects_tensor_differences() -> None:
    """Determinism comparisons should fail when any extracted tensor changes."""
    first_run = {
        "sites": {
            "resid_post": {
                "cue_token": torch.zeros(1, 1, 2),
                "last_prompt_token": torch.zeros(1, 1, 2),
            },
            "attn_out": {
                "cue_token": torch.zeros(1, 1, 2),
                "last_prompt_token": torch.zeros(1, 1, 2),
            },
            "mlp_out": {
                "cue_token": torch.zeros(1, 1, 2),
                "last_prompt_token": torch.zeros(1, 1, 2),
            },
        }
    }
    second_run = {
        "sites": {
            "resid_post": {
                "cue_token": torch.zeros(1, 1, 2),
                "last_prompt_token": torch.zeros(1, 1, 2),
            },
            "attn_out": {
                "cue_token": torch.zeros(1, 1, 2),
                "last_prompt_token": torch.ones(1, 1, 2),
            },
            "mlp_out": {
                "cue_token": torch.zeros(1, 1, 2),
                "last_prompt_token": torch.zeros(1, 1, 2),
            },
        }
    }

    assert compare_activation_runs(first_run, second_run) is False


class _MockCfg:
    """Minimal config stub for targeted-activation tests."""

    def __init__(self, n_layers: int, d_model: int) -> None:
        self.n_layers = n_layers
        self.d_model = d_model


class _MockHookedTransformer:
    """Tiny TransformerLens-like stub used for targeted extraction tests."""

    def __init__(self, n_layers: int = 2, d_model: int = 64) -> None:
        self.cfg = _MockCfg(n_layers=n_layers, d_model=d_model)
        self._parameter = torch.nn.Parameter(torch.zeros(1))

    def parameters(self):  # noqa: ANN202
        """Yield one CPU parameter so device inference works."""

        yield self._parameter

    def run_with_cache(self, tokens: torch.Tensor, names_filter=None):  # noqa: ANN001
        """Return deterministic cache tensors for each supported activation site."""

        batch_size, prompt_length = tokens.shape
        cache: dict[str, torch.Tensor] = {}
        site_order = ("hook_resid_post", "hook_attn_out", "hook_mlp_out")
        for layer_index in range(self.cfg.n_layers):
            for site_offset, hook_name in enumerate(site_order):
                cache_key = f"blocks.{layer_index}.{hook_name}"
                if names_filter is not None and not names_filter(cache_key):
                    continue
                base = (layer_index + 1) * 1000 + site_offset * 100
                values = torch.arange(
                    batch_size * prompt_length * self.cfg.d_model,
                    dtype=torch.float32,
                ).reshape(batch_size, prompt_length, self.cfg.d_model)
                cache[cache_key] = values + base
        return None, cache


def test_extract_targeted_activations_returns_only_requested_positions() -> None:
    """Targeted extraction should return only cue-span and last-prompt activations."""

    model = _MockHookedTransformer()
    activations = extract_targeted_activations(
        model=model,
        prompt="dummy prompt",
        prompt_token_ids=[11, 22, 33, 44, 55],
        cue_span_token_ids=[1, 3],
        layers=[0, 1],
        sites=["resid_post", "mlp_out"],
        dtype="float16",
    )

    expected_keys = {
        "resid_post_last_prompt_layer0",
        "resid_post_cue_token0_layer0",
        "resid_post_cue_token1_layer0",
        "resid_post_last_prompt_layer1",
        "resid_post_cue_token0_layer1",
        "resid_post_cue_token1_layer1",
        "mlp_out_last_prompt_layer0",
        "mlp_out_cue_token0_layer0",
        "mlp_out_cue_token1_layer0",
        "mlp_out_last_prompt_layer1",
        "mlp_out_cue_token0_layer1",
        "mlp_out_cue_token1_layer1",
    }
    assert set(activations) == expected_keys
    assert all(tensor.shape == (64,) for tensor in activations.values())
    assert all(tensor.dtype == torch.float16 for tensor in activations.values())


def test_extract_targeted_activations_rejects_non_prompt_indices() -> None:
    """Targeted extraction should reject indices outside the prompt span."""

    model = _MockHookedTransformer()
    with pytest.raises(ValueError):
        extract_targeted_activations(
            model=model,
            prompt="dummy prompt",
            prompt_token_ids=[1, 2, 3],
            cue_span_token_ids=[3],
        )


class _MockTokenizer:
    """Tiny tokenizer stub exposing offset mappings for cue-index tests."""

    def __call__(
        self,
        text: str,
        add_special_tokens: bool = False,
        return_offsets_mapping: bool = False,
    ):  # noqa: ANN001, D401
        del add_special_tokens
        words = []
        offsets = []
        cursor = 0
        for token in text.split():
            start = text.index(token, cursor)
            end = start + len(token)
            cursor = end
            words.append(token)
            offsets.append((start, end))
        if return_offsets_mapping:
            return {"input_ids": list(range(len(words))), "offset_mapping": offsets}
        return type("TokenOutput", (), {"input_ids": list(range(len(words)))})()


def test_find_cue_token_index_uses_offset_mapping() -> None:
    """Cue-token lookup should return the first token that begins inside the cue sentence."""

    tokenizer = _MockTokenizer()
    prompt = "System wrapper User: A block slides. The cue sentence begins here."
    cue_sentence = "The cue sentence begins here."
    assert find_cue_token_index(prompt, cue_sentence, tokenizer) == 6
