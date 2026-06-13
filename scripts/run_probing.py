#!/usr/bin/env python3
"""Stage 5+ probe training and evaluation entry point.

Reference: `physmon_proposal.pdf` §10-§11 and Part V.4 rule 2.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import random

import numpy as np
import torch

from physmon.utils.gates import require_stage_gate_pass
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 5
DEFAULT_REQUIRED_GATE = 3
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_probing_events.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 5 probing runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="results/probing",
        help="Directory for Stage 5 probing artifacts.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed.")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    """Set reproducibility seeds for probing experiments."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main() -> None:
    """Refuse to train probes until the Stage 3 artefact-control gate has passed."""
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_probing.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )
    set_seed(args.seed)

    try:
        require_stage_gate_pass(DEFAULT_REQUIRED_GATE)
    except Exception as error:  # noqa: BLE001
        logger.log_error(
            str(error),
            seed=args.seed,
            blocked_stage_gate=DEFAULT_REQUIRED_GATE,
        )
        raise

    logger.log_event(
        "PROBING_RUN_READY",
        seed=args.seed,
        status="Stage gate satisfied; probe training implementation pending.",
    )


if __name__ == "__main__":
    main()
