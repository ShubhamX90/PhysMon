"""Smoke-test the Slurm runtime environment for PhysMon GPU jobs."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import torch

from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 1
DEFAULT_JSONL_PATH = "results/infrastructure/slurm_smoke_cuda_events.jsonl"


def main() -> None:
    """Print a small JSON payload describing CUDA visibility inside a job."""
    logger = ExperimentLogger(
        script_name="slurm_smoke_cuda.py",
        stage=DEFAULT_STAGE,
        jsonl_path=Path(DEFAULT_JSONL_PATH),
        repo_root=Path(__file__).resolve().parents[1],
    )
    payload = {
        "hostname": socket.gethostname(),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_device_name_0": torch.cuda.get_device_name(0)
        if torch.cuda.is_available()
        else None,
    }
    logger.log_event("SLURM_SMOKE_COMPLETE", **payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
