"""Smoke-test the Slurm runtime environment for PhysMon GPU jobs."""

from __future__ import annotations

import json
import socket

import torch


def main() -> None:
    """Print a small JSON payload describing CUDA visibility inside a job."""
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
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
