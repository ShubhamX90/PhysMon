"""Prompt-side activation patching guards and helpers for PhysMon.

Reference: `physmon_proposal.pdf` §9 and §11, plus Part V.4 rule 5 of the
implementation brief. Causal interventions are permitted only on prompt-side
token positions, never on generated tokens.
"""

from __future__ import annotations

from collections.abc import Sequence

import torch


def validate_prompt_side_positions(prompt_length: int, token_positions: Sequence[int]) -> tuple[int, ...]:
    """Validate that all patch sites lie strictly inside the prompt prefix.

    Args:
        prompt_length: Number of prompt tokens available before generation.
        token_positions: Token indices requested for intervention.

    Returns:
        Tuple of validated token positions in the original order.

    Reference:
        Part V.4 rule 5 and `physmon_proposal.pdf` §9.
    """

    if prompt_length <= 0:
        raise ValueError("prompt_length must be positive for prompt-side activation patching.")
    if not token_positions:
        raise ValueError("token_positions must contain at least one prompt-side index.")

    validated_positions: list[int] = []
    for position in token_positions:
        if position < 0:
            raise ValueError(f"Prompt-side token positions must be non-negative, got {position}.")
        if position >= prompt_length:
            raise ValueError(
                "Activation patching is restricted to prompt-side tokens. "
                f"Received position {position} for prompt length {prompt_length}."
            )
        validated_positions.append(position)
    return tuple(validated_positions)


def zero_ablate_prompt_positions(
    activations: torch.Tensor,
    prompt_length: int,
    token_positions: Sequence[int],
) -> torch.Tensor:
    """Zero-ablate selected prompt-side token positions in an activation tensor.

    Args:
        activations: Tensor whose penultimate dimension indexes token positions.
        prompt_length: Number of prompt tokens available before generation.
        token_positions: Prompt-side token positions to ablate.

    Returns:
        A cloned tensor with the selected prompt-side positions zeroed.

    Reference:
        Part V.4 rule 5 and the prompt-side intervention plan in
        `physmon_proposal.pdf` §11 Stage 8.
    """

    validated_positions = validate_prompt_side_positions(prompt_length, token_positions)
    if activations.ndim < 2:
        raise ValueError(
            "Activation tensors must expose a token dimension in the penultimate axis."
        )
    if activations.shape[-2] < prompt_length:
        raise ValueError(
            "Activation tensor token dimension is shorter than the declared prompt length."
        )

    ablated = activations.clone()
    for position in validated_positions:
        ablated[..., position, :] = 0
    return ablated
