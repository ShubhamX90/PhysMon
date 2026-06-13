#!/usr/bin/env python3
"""Estimate PhysMon Stage 2 storage and compute requirements.

Reference: Part IV.3 of the implementation brief and the compute-planning material in
`physmon_proposal.pdf` §11.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from physmon.utils.io import write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 2
DEFAULT_PILOT_FAMILIES = 30
DEFAULT_FULL_FAMILIES = 150
DEFAULT_NUM_MODELS = 2
DEFAULT_TOKENS_PER_PROBLEM = 2000
DEFAULT_PROMPT_POSITIONS = 2
DEFAULT_EXHAUSTIVE_ACTIVATION_SITES = 80
DEFAULT_PER_FORWARD_SECONDS = 2.0
DEFAULT_SCRATCH_AVAILABLE_GB = 175000.0
DEFAULT_JSONL_NAME = "compute_estimate_events.jsonl"
BYTES_PER_DTYPE = {"float16": 2, "float32": 4}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the compute estimator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-families", type=int, default=DEFAULT_PILOT_FAMILIES)
    parser.add_argument("--full-families", type=int, default=DEFAULT_FULL_FAMILIES)
    parser.add_argument("--num-variants", type=int, required=True)
    parser.add_argument("--num-layers", type=int, required=True)
    parser.add_argument("--hidden-dim", type=int, required=True)
    parser.add_argument("--num-models", type=int, default=DEFAULT_NUM_MODELS)
    parser.add_argument("--activation-dtype", choices=sorted(BYTES_PER_DTYPE), default="float16")
    parser.add_argument("--tokens-per-problem", type=int, default=DEFAULT_TOKENS_PER_PROBLEM)
    parser.add_argument("--prompt-positions", type=int, default=DEFAULT_PROMPT_POSITIONS)
    parser.add_argument(
        "--exhaustive-activation-sites",
        type=int,
        default=DEFAULT_EXHAUSTIVE_ACTIVATION_SITES,
        help="Upper-bound count of activation sites for exhaustive extraction estimates.",
    )
    parser.add_argument("--time-per-forward-seconds", type=float, default=DEFAULT_PER_FORWARD_SECONDS)
    parser.add_argument("--scratch-available-gb", type=float, default=DEFAULT_SCRATCH_AVAILABLE_GB)
    parser.add_argument(
        "--output-path",
        default="results/stage2/compute_estimate.json",
        help="Output JSON path.",
    )
    return parser.parse_args()


def compute_storage_profile(
    *,
    per_variant_bytes: int,
    num_variants: int,
    pilot_families: int,
    full_families: int,
    num_models: int,
) -> dict[str, float]:
    """Convert one per-variant activation budget into family/pilot/full estimates."""
    storage_per_family_per_model_bytes = per_variant_bytes * num_variants
    pilot_storage_bytes = storage_per_family_per_model_bytes * pilot_families * num_models
    full_storage_bytes = storage_per_family_per_model_bytes * full_families * num_models
    return {
        "storage_per_family_per_model_mb": round(_bytes_to_mb(storage_per_family_per_model_bytes), 3),
        "total_pilot_storage_gb": round(_bytes_to_gb(pilot_storage_bytes), 3),
        "total_full_storage_gb": round(_bytes_to_gb(full_storage_bytes), 3),
    }


def main() -> None:
    """Compute and save the Stage 2 storage/compute estimate."""
    args = parse_args()
    output_path = Path(args.output_path)
    logger = ExperimentLogger(
        script_name="estimate_compute.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_path.parent / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )
    bytes_per_element = BYTES_PER_DTYPE[args.activation_dtype]

    exhaustive_per_variant_bytes = (
        args.exhaustive_activation_sites
        * args.tokens_per_problem
        * args.hidden_dim
        * bytes_per_element
    )
    targeted_per_variant_bytes = (
        args.num_layers * args.prompt_positions * args.hidden_dim * bytes_per_element
    )

    exhaustive_profile = compute_storage_profile(
        per_variant_bytes=exhaustive_per_variant_bytes,
        num_variants=args.num_variants,
        pilot_families=args.pilot_families,
        full_families=args.full_families,
        num_models=args.num_models,
    )
    targeted_profile = compute_storage_profile(
        per_variant_bytes=targeted_per_variant_bytes,
        num_variants=args.num_variants,
        pilot_families=args.pilot_families,
        full_families=args.full_families,
        num_models=args.num_models,
    )

    pilot_forward_passes = args.pilot_families * args.num_variants * args.num_models
    full_forward_passes = args.full_families * args.num_variants * args.num_models
    pilot_gpu_hours = pilot_forward_passes * args.time_per_forward_seconds / 3600.0
    full_activation_gpu_hours = full_forward_passes * args.time_per_forward_seconds / 3600.0

    scratch_threshold_gb = args.scratch_available_gb * 0.8
    exhaustive_full_storage_gb = exhaustive_profile["total_full_storage_gb"]
    targeted_full_storage_gb = targeted_profile["total_full_storage_gb"]

    payload = {
        "stage": DEFAULT_STAGE,
        "inputs": {
            "pilot_families": args.pilot_families,
            "full_families": args.full_families,
            "num_variants": args.num_variants,
            "num_layers": args.num_layers,
            "hidden_dim": args.hidden_dim,
            "num_models": args.num_models,
            "activation_dtype": args.activation_dtype,
            "tokens_per_problem": args.tokens_per_problem,
            "prompt_positions": args.prompt_positions,
            "exhaustive_activation_sites": args.exhaustive_activation_sites,
            "time_per_forward_seconds": args.time_per_forward_seconds,
            "scratch_available_gb": args.scratch_available_gb,
        },
        "exhaustive_upper_bound": exhaustive_profile,
        "targeted_stage5": targeted_profile,
        "estimated_pilot_gpu_hours": round(pilot_gpu_hours, 3),
        "estimated_full_activation_gpu_hours": round(full_activation_gpu_hours, 3),
        "exceeds_80_percent_scratch_capacity": {
            "exhaustive_upper_bound": exhaustive_full_storage_gb > scratch_threshold_gb,
            "targeted_stage5": targeted_full_storage_gb > scratch_threshold_gb,
        },
    }

    write_json(output_path, payload)
    logger.log_event("COMPUTE_ESTIMATE_COMPLETE", **payload)
    print(payload)


def _bytes_to_mb(value: int) -> float:
    """Convert bytes to decimal megabytes."""
    return value / 1_000_000.0


def _bytes_to_gb(value: int) -> float:
    """Convert bytes to decimal gigabytes."""
    return value / 1_000_000_000.0


if __name__ == "__main__":
    main()
