"""Linear and MLP probe implementations for Stage 5+ monitoring.

Reference:
    `physmon_proposal.pdf` §9.2-§9.3 and the Stage 5 preparation brief.
"""

from __future__ import annotations

import torch
from torch import nn


DEFAULT_MIN_HIDDEN_WIDTH = 16


class LinearProbe(nn.Module):
    """L2-regularised logistic-style probe over one hidden state.

    Args:
        hidden_dim: Hidden-state dimensionality.

    Returns:
        Module whose `forward` method returns `P(sensitive)` in `[0, 1]`.

    Reference:
        `physmon_proposal.pdf` §9.2.
    """

    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        if hidden_dim <= 0:
            raise ValueError(f"hidden_dim must be positive, got {hidden_dim}.")
        self.hidden_dim = hidden_dim
        self.classifier = nn.Linear(hidden_dim, 1)

    def forward(self, hidden_state: torch.Tensor) -> torch.Tensor:
        """Map one hidden state or a batch of hidden states to sensitivity probabilities.

        Args:
            hidden_state: Tensor of shape `(hidden_dim,)` or `(..., hidden_dim)`.

        Returns:
            Tensor of probabilities with the same leading shape as the input.
        """

        logits = self.classifier(hidden_state).squeeze(-1)
        return torch.sigmoid(logits)


class MLPProbe(nn.Module):
    """Two-layer ReLU probe for non-linear sensitivity prediction.

    Args:
        hidden_dim: Hidden-state dimensionality.
        hidden_width: Optional hidden width for the intermediate layer.

    Returns:
        Module whose `forward` method returns `P(sensitive)` in `[0, 1]`.

    Reference:
        `physmon_proposal.pdf` §9.3.
    """

    def __init__(self, hidden_dim: int, hidden_width: int | None = None) -> None:
        super().__init__()
        if hidden_dim <= 0:
            raise ValueError(f"hidden_dim must be positive, got {hidden_dim}.")
        resolved_hidden_width = hidden_width or max(hidden_dim // 2, DEFAULT_MIN_HIDDEN_WIDTH)
        if resolved_hidden_width <= 0:
            raise ValueError(f"hidden_width must be positive, got {resolved_hidden_width}.")
        self.hidden_dim = hidden_dim
        self.hidden_width = resolved_hidden_width
        self.network = nn.Sequential(
            nn.Linear(hidden_dim, resolved_hidden_width),
            nn.ReLU(),
            nn.Linear(resolved_hidden_width, 1),
        )

    def forward(self, hidden_state: torch.Tensor) -> torch.Tensor:
        """Map one hidden state or a batch of hidden states to sensitivity probabilities.

        Args:
            hidden_state: Tensor of shape `(hidden_dim,)` or `(..., hidden_dim)`.

        Returns:
            Tensor of probabilities with the same leading shape as the input.
        """

        logits = self.network(hidden_state).squeeze(-1)
        return torch.sigmoid(logits)
