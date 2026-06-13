#!/usr/bin/env python3
"""Run the Stage 4 behavioural sensitivity sweep over rendered benchmark families.

Reference: `physmon_proposal.pdf` §3.3, §10, and the Stage 3 brief Part D.10.
This runner loads one model once, iterates every rendered family JSON in a directory,
emits one prompt-level JSONL record immediately after each generation, and then emits one
family-level summary record after each family finishes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
from typing import Any

import numpy as np
import torch

from physmon.benchmark.parser import parse_answer
from physmon.models.loader import LoadedModelBundle, load_model, load_model_registry, resolve_model_spec
from physmon.models.logprob import compute_reference_answer_logprob
from physmon.utils.io import append_jsonl
from physmon.utils.logging import ExperimentLogger


DEFAULT_STAGE = 4
DEFAULT_SEED = 42
DEFAULT_MAX_NEW_TOKENS = 32
DEFAULT_JSONL_NAME = "run_behavioural_events.jsonl"
DEFAULT_PROMPT_RECORDS_NAME = "prompt_records.jsonl"
DEFAULT_FAMILY_SUMMARIES_NAME = "family_summaries.jsonl"
DEFAULT_TEMPERATURE = 1.0


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 4 behavioural sweep.

    Returns:
        Parsed `argparse.Namespace` for the behavioural runner.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-role",
        required=True,
        help=(
            "Model role or registry key. If the value matches a key in "
            "`docs/model_registry.yml`, that key is used directly."
        ),
    )
    parser.add_argument(
        "--model-key",
        default=None,
        help="Optional explicit registry key. Overrides any key-like `--model-role` value.",
    )
    parser.add_argument("--family-dir", required=True, help="Directory containing rendered family JSON files.")
    parser.add_argument("--output-dir", required=True, help="Directory for behavioural outputs.")
    parser.add_argument("--device", default="cuda", help="Torch device used for model loading.")
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=DEFAULT_MAX_NEW_TOKENS,
        help="Maximum deterministic continuation length per prompt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and emit planned workload metadata without loading a model.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed.")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    """Set Python, NumPy, and Torch RNG state.

    Args:
        seed: Deterministic seed value.

    Returns:
        `None`.
    """

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_registry_selection(model_role: str, model_key: str | None) -> tuple[str, str]:
    """Resolve the requested behavioural model to one registry key and one role label.

    Args:
        model_role: User-supplied model role or registry key.
        model_key: Optional explicit registry key.

    Returns:
        Tuple of `(resolved_model_key, resolved_role_label)`.
    """

    registry = load_model_registry()
    if model_key is not None:
        spec = resolve_model_spec(model_key=model_key)
        return spec.key, spec.role
    if model_role in registry:
        spec = registry[model_role]
        return spec.key, spec.role
    spec = resolve_model_spec(role=model_role)
    return spec.key, spec.role


def load_rendered_families(family_dir: str | Path) -> list[dict[str, Any]]:
    """Load all rendered family JSON payloads from disk.

    Args:
        family_dir: Directory containing one JSON file per rendered family.

    Returns:
        Ordered list of loaded family payloads.
    """

    directory = Path(family_dir)
    family_paths = sorted(directory.glob("*.json"))
    if not family_paths:
        raise FileNotFoundError(f"No rendered family JSON files found in {directory}.")
    return [json.loads(path.read_text(encoding="utf-8")) for path in family_paths]


def generate_completion(bundle: LoadedModelBundle, prompt: str, max_new_tokens: int) -> str:
    """Run deterministic greedy generation and return only the newly generated text.

    Args:
        bundle: Loaded model bundle.
        prompt: Prompt text to evaluate.
        max_new_tokens: Generation cap for the answer continuation.

    Returns:
        Decoded generated continuation string.
    """

    first_parameter = next(bundle.hf_model.parameters())
    prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(
        first_parameter.device
    )
    with torch.no_grad():
        generated_ids = bundle.hf_model.generate(
            prompt_ids,
            do_sample=False,
            temperature=DEFAULT_TEMPERATURE,
            max_new_tokens=max_new_tokens,
            pad_token_id=bundle.tokenizer.eos_token_id,
        )
    continuation_ids = generated_ids[:, prompt_ids.shape[1] :]
    return bundle.tokenizer.decode(continuation_ids[0], skip_special_tokens=True).strip()


def make_prompt_record(
    *,
    family_payload: dict[str, Any],
    variant_payload: dict[str, Any],
    generated_text: str | None,
    parsed_answer: str | None,
    parse_confidence: float | None,
    parse_confident: bool | None,
    logprob_correct_answer: float | None,
    git_commit: str,
    model_name: str,
    model_role: str,
    seed: int,
    dry_run: bool,
) -> dict[str, Any]:
    """Build one prompt-level behavioural result record.

    Args:
        family_payload: Loaded family JSON.
        variant_payload: One rendered variant payload.
        generated_text: Raw generated continuation or `None` in dry-run mode.
        parsed_answer: Canonical parsed answer, if any.
        parse_confidence: Parser confidence.
        parse_confident: Whether the parser accepted the answer.
        logprob_correct_answer: `log p_theta(y* | x)` for the family answer.
        git_commit: Git commit recorded for reproducibility.
        model_name: Canonical model name.
        model_role: Model role label.
        seed: Behavioural seed.
        dry_run: Whether this is a non-executing dry run.

    Returns:
        JSON-serializable prompt record.
    """

    return {
        "git_commit": git_commit,
        "script_name": "run_behavioural.py",
        "stage": DEFAULT_STAGE,
        "model_name": model_name,
        "model_role": model_role,
        "seed": seed,
        "dry_run": dry_run,
        "template_id": family_payload["template_id"],
        "domain": family_payload["domain"],
        "cue_type": family_payload["cue_type"],
        "variant_id": variant_payload["variant_id"],
        "cue_value": variant_payload["cue_value"],
        "correct_answer": family_payload["correct_answer"],
        "generated_text": generated_text,
        "parsed_answer": parsed_answer,
        "parse_confidence": parse_confidence,
        "parse_confident": parse_confident,
        "logprob_correct_answer": logprob_correct_answer,
    }


def summarize_family(
    family_payload: dict[str, Any],
    prompt_records: list[dict[str, Any]],
    *,
    git_commit: str,
    model_name: str,
    model_role: str,
    seed: int,
    dry_run: bool,
) -> dict[str, Any]:
    """Summarize one family's behavioural outputs for downstream sensitivity work.

    Args:
        family_payload: Loaded family JSON.
        prompt_records: Prompt-level records already emitted for this family.
        git_commit: Git commit recorded for reproducibility.
        model_name: Canonical model name.
        model_role: Model role label.
        seed: Behavioural seed.
        dry_run: Whether this is a dry run.

    Returns:
        JSON-serializable family summary.
    """

    parsed_answers = [record["parsed_answer"] for record in prompt_records if record["parsed_answer"] is not None]
    confident_records = [record for record in prompt_records if record["parse_confident"]]
    unique_parsed_answers = sorted(set(parsed_answers))
    answer_flip_rate = None
    if confident_records:
        parsed_by_variant = [record["parsed_answer"] for record in confident_records]
        comparisons = 0
        flips = 0
        for left_index in range(len(parsed_by_variant)):
            for right_index in range(left_index + 1, len(parsed_by_variant)):
                comparisons += 1
                flips += int(parsed_by_variant[left_index] != parsed_by_variant[right_index])
        answer_flip_rate = (flips / comparisons) if comparisons else 0.0

    return {
        "git_commit": git_commit,
        "script_name": "run_behavioural.py",
        "stage": DEFAULT_STAGE,
        "model_name": model_name,
        "model_role": model_role,
        "seed": seed,
        "dry_run": dry_run,
        "template_id": family_payload["template_id"],
        "domain": family_payload["domain"],
        "cue_type": family_payload["cue_type"],
        "num_variants": len(family_payload["variants"]),
        "num_confident_parses": len(confident_records),
        "unique_parsed_answers": unique_parsed_answers,
        "answer_flip_rate": answer_flip_rate,
    }


def main() -> None:
    """Load one model once, run all behavioural prompts, and emit JSONL outputs."""

    args = parse_args()
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_behavioural.py",
        stage=DEFAULT_STAGE,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
    )

    resolved_model_key, resolved_role = resolve_registry_selection(args.model_role, args.model_key)
    families = load_rendered_families(args.family_dir)
    bundle: LoadedModelBundle | None = None
    model_name = resolved_model_key
    model_role = resolved_role

    if not args.dry_run:
        bundle = load_model(model_key=resolved_model_key, device=args.device)
        model_name = bundle.spec.name
        model_role = bundle.spec.role
    else:
        spec = resolve_model_spec(model_key=resolved_model_key)
        model_name = spec.name

    logger.model_name = model_name
    logger.model_role = model_role
    prompt_records_path = output_dir / DEFAULT_PROMPT_RECORDS_NAME
    family_summaries_path = output_dir / DEFAULT_FAMILY_SUMMARIES_NAME

    logger.log_event(
        "BEHAVIOURAL_RUN_START",
        model_key=resolved_model_key,
        model_name=model_name,
        model_role=model_role,
        family_count=len(families),
        dry_run=args.dry_run,
        max_new_tokens=args.max_new_tokens,
        family_dir=str(Path(args.family_dir).resolve()),
    )

    for family_payload in families:
        family_prompt_records: list[dict[str, Any]] = []
        for variant_payload in family_payload["variants"]:
            if args.dry_run:
                prompt_record = make_prompt_record(
                    family_payload=family_payload,
                    variant_payload=variant_payload,
                    generated_text=None,
                    parsed_answer=None,
                    parse_confidence=None,
                    parse_confident=None,
                    logprob_correct_answer=None,
                    git_commit=logger.git_commit,
                    model_name=model_name,
                    model_role=model_role,
                    seed=args.seed,
                    dry_run=True,
                )
            else:
                assert bundle is not None
                generated_text = generate_completion(bundle, variant_payload["prompt"], args.max_new_tokens)
                parse_result = parse_answer(generated_text)
                logprob_correct_answer = compute_reference_answer_logprob(
                    bundle,
                    variant_payload["prompt"],
                    family_payload["correct_answer"],
                )
                prompt_record = make_prompt_record(
                    family_payload=family_payload,
                    variant_payload=variant_payload,
                    generated_text=generated_text,
                    parsed_answer=parse_result.answer,
                    parse_confidence=parse_result.confidence,
                    parse_confident=parse_result.is_confident,
                    logprob_correct_answer=logprob_correct_answer,
                    git_commit=logger.git_commit,
                    model_name=model_name,
                    model_role=model_role,
                    seed=args.seed,
                    dry_run=False,
                )

            append_jsonl(prompt_records_path, prompt_record)
            family_prompt_records.append(prompt_record)
            logger.log_event(
                "PROMPT_EVALUATED",
                template_id=family_payload["template_id"],
                variant_id=variant_payload["variant_id"],
                cue_value=variant_payload["cue_value"],
                parse_confident=prompt_record["parse_confident"],
                parsed_answer=prompt_record["parsed_answer"],
                dry_run=args.dry_run,
            )

        family_summary = summarize_family(
            family_payload,
            family_prompt_records,
            git_commit=logger.git_commit,
            model_name=model_name,
            model_role=model_role,
            seed=args.seed,
            dry_run=args.dry_run,
        )
        append_jsonl(family_summaries_path, family_summary)
        logger.log_event("FAMILY_COMPLETE", **family_summary)

    logger.log_event(
        "BEHAVIOURAL_RUN_COMPLETE",
        model_key=resolved_model_key,
        model_name=model_name,
        model_role=model_role,
        family_count=len(families),
        dry_run=args.dry_run,
        prompt_records_path=str(prompt_records_path.resolve()),
        family_summaries_path=str(family_summaries_path.resolve()),
    )


if __name__ == "__main__":
    main()
