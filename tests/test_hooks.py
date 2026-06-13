"""Unit tests for prompt-side hook and patching utilities."""

from __future__ import annotations

import pytest
import torch

from physmon.causal.patching import (
    validate_prompt_side_positions,
    zero_ablate_prompt_positions,
)
from physmon.models.hooks import compare_activation_runs


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
