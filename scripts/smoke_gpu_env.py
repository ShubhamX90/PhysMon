#!/usr/bin/env python3
"""Minimal GPU environment smoke test for Sharanga Slurm templates.

This script verifies that the `physmon` environment loads correctly on a GPU node and
reports basic CUDA device metadata for infrastructure validation.
"""

from __future__ import annotations

import json
from pathlib import Path

import torch

from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 1
DEFAULT_JSONL_PATH = "results/infrastructure/smoke_gpu_env_events.jsonl"


def main() -> None:
    """Print a compact JSON payload describing the active Torch/CUDA environment."""
    logger = ExperimentLogger(
        script_name="smoke_gpu_env.py",
        stage=DEFAULT_STAGE,
        jsonl_path=Path(DEFAULT_JSONL_PATH),
        repo_root=Path(__file__).resolve().parents[1],
    )
    payload = {
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "torch_cuda": torch.version.cuda,
        "device_count": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    logger.log_event("GPU_ENV_SMOKE_COMPLETE", **payload)
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
