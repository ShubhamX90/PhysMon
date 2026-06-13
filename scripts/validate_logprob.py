#!/usr/bin/env python3
"""Stage 2 log-probability validation for one candidate PhysMon model.

Reference: Part IV.2 of the implementation brief.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import math
import time
import traceback

import torch

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
DEFAULT_DETERMINISM_RUNS = 2


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
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Reference prompt for validation.")
    parser.add_argument(
        "--altered-prompt",
        default=DEFAULT_ALTERED_PROMPT,
        help="Slightly altered prompt used for log-prob sensitivity validation.",
    )
    parser.add_argument(
        "--reference-answer",
        default=DEFAULT_REFERENCE_ANSWER,
        help="Reference answer string whose log-probability will be evaluated.",
    )
    parser.add_argument(
        "--expect-think-tags",
        action="store_true",
        help="Require the generated output to contain a <think>...</think> block.",
    )
    parser.add_argument(
        "--determinism-runs",
        type=int,
        default=DEFAULT_DETERMINISM_RUNS,
        help="Number of repeated greedy generations used for the determinism check.",
    )
    parser.add_argument(
        "--device-map",
        default=None,
        help='Optional Hugging Face device map such as "auto" for multi-GPU sharding.',
    )
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
        "reference_answer": args.reference_answer,
        "reference_logprob": None,
        "altered_prompt_logprob": None,
        "top_k_distribution": [],
        "logprob_finite": False,
        "logprob_changes_with_input": False,
        "generation_determinism_ok": False,
        "determinism_runs": args.determinism_runs,
        "deterministic_generation": None,
        "has_think_tags": None,
        "peak_vram_usage_mb": {},
        "notes": [],
        "timing_seconds": {},
    }

    try:
        reset_peak_vram_stats()
        bundle = load_model_from_spec(
            spec=spec,
            device=args.device,
            device_map=args.device_map,
            torch_dtype=None if args.device == "cpu" else torch.bfloat16,
        )
        reference_logprob = compute_reference_answer_logprob(bundle, args.prompt, args.reference_answer)
        altered_logprob = compute_reference_answer_logprob(
            bundle,
            args.altered_prompt,
            args.reference_answer,
        )
        top_k_distribution = get_next_token_topk(bundle, args.prompt)

        deterministic_generations: list[str] = []
        generation_start = time.perf_counter()
        for _ in range(args.determinism_runs):
            set_global_seed(args.seed)
            deterministic_generations.append(run_deterministic_generation(bundle, args.prompt))
        generation_elapsed = time.perf_counter() - generation_start

        report["reference_logprob"] = reference_logprob
        report["altered_prompt_logprob"] = altered_logprob
        report["top_k_distribution"] = top_k_distribution
        report["logprob_finite"] = math.isfinite(reference_logprob) and math.isfinite(altered_logprob)
        report["logprob_changes_with_input"] = abs(reference_logprob - altered_logprob) > 1e-6
        report["generation_determinism_ok"] = len(set(deterministic_generations)) == 1
        report["deterministic_generation"] = deterministic_generations[0]
        report["has_think_tags"] = (
            "<think>" in deterministic_generations[0] and "</think>" in deterministic_generations[0]
        )
        if args.expect_think_tags and not report["has_think_tags"]:
            report["notes"].append("Expected <think>...</think> tags but did not observe them.")
        report["notes"].append(f"deterministic_generation={deterministic_generations[0]}")
        report["peak_vram_usage_mb"] = collect_peak_vram_usage_mb()
        report["timing_seconds"]["total"] = round(time.perf_counter() - start_time, 3)
        report["timing_seconds"]["generation"] = round(generation_elapsed, 3)
        logger.log_event("LOGPROB_VALIDATION_COMPLETE", **report)
    except Exception as error:  # noqa: BLE001
        report["notes"].append(str(error))
        report["notes"].append(traceback.format_exc())
        report["timing_seconds"]["total"] = round(time.perf_counter() - start_time, 3)
        logger.log_error(str(error), report=report)
    finally:
        report_path = output_dir / f"{args.model_key}_logprob_validation.json"
        write_json(report_path, report)


def collect_peak_vram_usage_mb() -> dict[str, float]:
    """Collect peak PyTorch-tracked GPU memory usage in MB.

    Returns:
        Mapping from GPU index string to peak memory-used values in MB.
    """

    if not torch.cuda.is_available():
        return {}

    usage_by_gpu: dict[str, float] = {}
    for device_index in range(torch.cuda.device_count()):
        usage_by_gpu[str(device_index)] = round(
            torch.cuda.max_memory_allocated(device_index) / (1024 ** 2),
            3,
        )
    return usage_by_gpu


def reset_peak_vram_stats() -> None:
    """Best-effort reset of PyTorch peak-memory counters on visible CUDA devices.

    Returns:
        `None`.
    """

    if not torch.cuda.is_available():
        return
    for device_index in range(torch.cuda.device_count()):
        try:
            torch.cuda.reset_peak_memory_stats(device_index)
        except Exception:  # noqa: BLE001
            continue


if __name__ == "__main__":
    main()
