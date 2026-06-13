#!/usr/bin/env python3
"""Stage 2 hook-support validation for one candidate PhysMon model.

Reference: Part IV.1 of the implementation brief and `physmon_proposal.pdf` §9.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import time

import torch

from physmon.models.hooks import (
    compare_activation_runs,
    extract_prompt_side_activations,
    run_zero_ablation_check,
    set_global_seed,
)
from physmon.models.loader import ModelSpec, load_model_from_spec
from physmon.utils.io import write_json
from physmon.utils.logging import ExperimentLogger


DEFAULT_SEED = 42
DEFAULT_STAGE = 2
DEFAULT_PROMPT = (
    "A cart starts from rest and accelerates at 2 m/s^2 for 5 s on a frictionless track. "
    "An irrelevant label called cue_value is 17. What is the final speed? "
    "Answer with only the value and units."
)
DEFAULT_CUE_SUBSTRING = "17"
DEFAULT_JSONL_NAME = "validate_hooks_events.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for hook validation."""
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
    """Run Stage 2 hook validation and save a structured JSON report."""
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = ExperimentLogger(
        script_name="validate_hooks.py",
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
        notes="Ad hoc Stage 2 hook validation run.",
    )

    report = {
        "model": args.model_name,
        "hook_backend": args.hook_backend,
        "layers": None,
        "hidden_dim": None,
        "extraction_ok": False,
        "patching_ok": False,
        "determinism_ok": False,
        "notes": [],
        "timing_seconds": {},
    }

    try:
        bundle = load_model_from_spec(spec=spec, device=args.device)
        extraction_start = time.perf_counter()
        first_run = extract_prompt_side_activations(bundle, DEFAULT_PROMPT, DEFAULT_CUE_SUBSTRING)
        second_run = extract_prompt_side_activations(bundle, DEFAULT_PROMPT, DEFAULT_CUE_SUBSTRING)
        extraction_elapsed = time.perf_counter() - extraction_start

        _validate_activation_shapes(first_run)

        report["layers"] = first_run["layers"]
        report["hidden_dim"] = first_run["hidden_dim"]
        report["extraction_ok"] = True
        report["determinism_ok"] = compare_activation_runs(first_run, second_run)
        report["timing_seconds"]["total"] = round(time.perf_counter() - start_time, 3)
        report["timing_seconds"]["extraction"] = round(extraction_elapsed, 3)
        report["timing_seconds"]["forward_pass"] = round(extraction_elapsed / 2.0, 3)
        report["notes"].append(
            f"cue_token_index={first_run['cue_token_index']}, last_prompt_index={first_run['last_prompt_token_index']}"
        )
        patch_result = run_zero_ablation_check(bundle, DEFAULT_PROMPT)
        report["patching_ok"] = patch_result["patching_ok"]
        report["notes"].append(f"patch_max_logit_difference={patch_result['max_logit_difference']:.6f}")
        logger.log_event("HOOK_VALIDATION_COMPLETE", **report)
    except Exception as error:  # noqa: BLE001
        report["notes"].append(str(error))
        report["timing_seconds"]["total"] = round(time.perf_counter() - start_time, 3)
        logger.log_error(str(error), report=report)
    finally:
        report_path = output_dir / f"{args.model_key}_hook_validation.json"
        write_json(report_path, report)


def _validate_activation_shapes(activation_payload: dict[str, object]) -> None:
    """Validate the extracted activation tensor shapes against the model metadata."""
    layers = int(activation_payload["layers"])
    hidden_dim = int(activation_payload["hidden_dim"])
    sites = activation_payload["sites"]
    if not isinstance(sites, dict):
        raise TypeError("Activation payload 'sites' must be a dictionary.")

    for site_name, site_payload in sites.items():
        if not isinstance(site_payload, dict):
            raise TypeError(f"Site payload for '{site_name}' must be a dictionary.")
        for position_name in ("cue_token", "last_prompt_token"):
            tensor = site_payload[position_name]
            if not isinstance(tensor, torch.Tensor):
                raise TypeError(f"Expected a tensor at {site_name}.{position_name}.")
            expected_shape = (layers, 1, hidden_dim)
            if tuple(tensor.shape) != expected_shape:
                raise ValueError(
                    f"Unexpected tensor shape at {site_name}.{position_name}: "
                    f"{tuple(tensor.shape)} != {expected_shape}"
                )


if __name__ == "__main__":
    main()
