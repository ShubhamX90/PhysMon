#!/usr/bin/env python3
"""Stage 2 log-probability validation for one candidate PhysMon model.

Reference: Part IV.2 of the implementation brief.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import math
import time

from physmon.models.hooks import set_global_seed
from physmon.models.loader import ModelSpec, load_model_from_spec
from physmon.models.logprob import (
    compute_reference_answer_logprob,
    get_next_token_topk,
    run_deterministic_generation,
)
from physmon.utils.io import write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_SEED = 42
DEFAULT_STAGE = 2
DEFAULT_PROMPT = (
    "A cart starts from rest and accelerates at 2 m/s^2 for 5 s on a frictionless track. "
    "What is the final speed? Answer with only the value and units."
)
DEFAULT_ALTERED_PROMPT = (
    "A cart starts from rest and accelerates at 2 m/s^2 for 6 s on a frictionless track. "
    "What is the final speed? Answer with only the value and units."
)
DEFAULT_REFERENCE_ANSWER = "10 m/s"
DEFAULT_JSONL_NAME = "validate_logprob_events.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for log-probability validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", required=True, help="Absolute path to local model weights.")
    parser.add_argument("--model-name", required=True, help="Canonical model name or HF identifier.")
    parser.add_argument("--output-dir", required=True, help="Directory for reports and logs.")
    parser.add_argument("--device", default="cuda", help="Torch device, typically cuda or cpu.")
    parser.add_argument("--model-key", default="adhoc_validation", help="Registry-style key for logging.")
    parser.add_argument("--model-role", default="PRIMARY_DENSE", help="Role label for structured logs.")
    parser.add_argument("--model-family", default="unknown", help="Family label for structured logs.")
    parser.add_argument("--hook-backend", default="transformer_lens", help="Hook backend to use.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed.")
    return parser.parse_args()


def main() -> None:
    """Run Stage 2 log-probability validation and save a structured JSON report."""
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = ExperimentLogger(
        script_name="validate_logprob.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
        model_name=args.model_name,
        model_role=args.model_role,
    )

    set_global_seed(args.seed)
    start_time = time.perf_counter()
    spec = ModelSpec(
        key=args.model_key,
        name=args.model_name,
        path=args.model_path,
        role=args.model_role,
        family=args.model_family,
        hook_backend=args.hook_backend,
        hook_validated=False,
        logprob_validated=False,
        hidden_dim=None,
        num_layers=None,
        notes="Ad hoc Stage 2 log-prob validation run.",
    )

    report = {
        "model": args.model_name,
        "hook_backend": args.hook_backend,
        "reference_answer": DEFAULT_REFERENCE_ANSWER,
        "reference_logprob": None,
        "altered_prompt_logprob": None,
        "top_k_distribution": [],
        "logprob_finite": False,
        "logprob_changes_with_input": False,
        "generation_determinism_ok": False,
        "notes": [],
        "timing_seconds": {},
    }

    try:
        bundle = load_model_from_spec(spec=spec, device=args.device)
        reference_logprob = compute_reference_answer_logprob(bundle, DEFAULT_PROMPT, DEFAULT_REFERENCE_ANSWER)
        altered_logprob = compute_reference_answer_logprob(bundle, DEFAULT_ALTERED_PROMPT, DEFAULT_REFERENCE_ANSWER)
        top_k_distribution = get_next_token_topk(bundle, DEFAULT_PROMPT)

        set_global_seed(args.seed)
        first_generation = run_deterministic_generation(bundle, DEFAULT_PROMPT)
        set_global_seed(args.seed)
        second_generation = run_deterministic_generation(bundle, DEFAULT_PROMPT)

        report["reference_logprob"] = reference_logprob
        report["altered_prompt_logprob"] = altered_logprob
        report["top_k_distribution"] = top_k_distribution
        report["logprob_finite"] = math.isfinite(reference_logprob) and math.isfinite(altered_logprob)
        report["logprob_changes_with_input"] = abs(reference_logprob - altered_logprob) > 1e-6
        report["generation_determinism_ok"] = first_generation == second_generation
        report["notes"].append(f"first_generation={first_generation}")
        report["timing_seconds"]["total"] = round(time.perf_counter() - start_time, 3)
        logger.log_event("LOGPROB_VALIDATION_COMPLETE", **report)
    except Exception as error:  # noqa: BLE001
        report["notes"].append(str(error))
        report["timing_seconds"]["total"] = round(time.perf_counter() - start_time, 3)
        logger.log_error(str(error), report=report)
    finally:
        report_path = output_dir / f"{args.model_key}_logprob_validation.json"
        write_json(report_path, report)


if __name__ == "__main__":
    main()
