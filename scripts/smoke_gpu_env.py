#!/usr/bin/env python3
"""Minimal GPU environment smoke test for Sharanga Slurm templates.

This script verifies that the `physmon` environment loads correctly on a GPU node and
reports basic CUDA device metadata for infrastructure validation.
"""

from __future__ import annotations

import json

import torch


def main() -> None:
    """Print a compact JSON payload describing the active Torch/CUDA environment."""
    payload = {
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "torch_cuda": torch.version.cuda,
        "device_count": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
