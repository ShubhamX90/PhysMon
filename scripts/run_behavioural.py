#!/usr/bin/env python3
"""Stage 4+ behavioural sensitivity sweep entry point.

Reference: `physmon_proposal.pdf` §10-§11 and Part V of the implementation brief.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import random

import numpy as np
import torch

from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 4
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_behavioural_events.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 4 behavioural sweep scaffold."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="results/behavioural",
        help="Directory for Stage 4 behavioural artifacts.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed.")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    """Set reproducibility seeds for behavioural experiments."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main() -> None:
    """Log the behavioural sweep scaffold state and exit clearly."""
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_behavioural.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )
    set_seed(args.seed)
    logger.log_event(
        "BEHAVIOURAL_SCAFFOLD_READY",
        seed=args.seed,
        status="Behavioral sweep entry point scaffolded; benchmark runner not implemented yet.",
    )


if __name__ == "__main__":
    main()
