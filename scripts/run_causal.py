#!/usr/bin/env python3
"""Stage 8+ causal intervention runner entry point.

Reference: `physmon_proposal.pdf` §9 and §11, plus Part V.4 rule 5.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import random

import numpy as np
import torch

from physmon.causal.patching import validate_prompt_side_positions
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 8
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_causal_events.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 8 causal runner scaffold."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="results/causal",
        help="Directory for Stage 8 causal artifacts.",
    )
    parser.add_argument(
        "--prompt-length",
        type=int,
        required=True,
        help="Prompt-token length used to define the prompt-side boundary.",
    )
    parser.add_argument(
        "--token-positions",
        type=int,
        nargs="+",
        required=True,
        help="Prompt-side token positions requested for intervention.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed.")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    """Set reproducibility seeds for causal experiments."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main() -> None:
    """Validate prompt-side intervention sites and log the causal-run scaffold."""
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_causal.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )
    set_seed(args.seed)

    try:
        validated_positions = validate_prompt_side_positions(
            prompt_length=args.prompt_length,
            token_positions=args.token_positions,
        )
    except Exception as error:  # noqa: BLE001
        logger.log_error(
            str(error),
            seed=args.seed,
            prompt_length=args.prompt_length,
            token_positions=args.token_positions,
        )
        raise

    logger.log_event(
        "CAUSAL_RUN_READY",
        seed=args.seed,
        prompt_length=args.prompt_length,
        token_positions=list(validated_positions),
        status="Prompt-side intervention sites validated; Stage 8 runner scaffolded.",
    )


if __name__ == "__main__":
    main()
