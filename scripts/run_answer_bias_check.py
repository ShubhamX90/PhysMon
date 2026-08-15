#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 10 answer-bias control for multi-head knockout."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.benchmark.parser import parse_answer  # noqa: E402
from physmon.models.hooks import set_global_seed  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402

from run_behavioural import DEFAULT_MAX_NEW_TOKENS, format_prompt_with_chat_template, load_rendered_families  # noqa: E402
from run_causal_patching import DEFAULT_JSONL_NAME  # noqa: E402
from run_damage_control import build_head_knockout_hook, greedy_generate_with_optional_hook, load_negative_family_ids  # noqa: E402


DEFAULT_STAGE = 10
DEFAULT_SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--negative-families-csv", required=True)
    parser.add_argument("--n-negative-families", type=int, default=40)
    parser.add_argument("--knockout-heads", nargs="+", type=int, required=True)
    parser.add_argument("--knockout-layer", type=int, default=16)
    parser.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_answer_bias_check.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    family_ids = load_negative_family_ids(Path(args.negative_families_csv), args.n_negative_families)
    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, family_ids)
    }
    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Answer bias control currently requires TransformerLens support.")
    bundle.hooked_model.set_use_attn_result(True)
    model_device = next(bundle.hooked_model.parameters()).device

    rows: list[dict[str, Any]] = []
    for family_id in family_ids:
        payload = family_payloads[family_id]
        base_variant = next(variant for variant in payload["variants"] if int(variant["variant_id"]) == 0)
        prompt = format_prompt_with_chat_template(str(base_variant["prompt"]), bundle.tokenizer)
        prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(model_device)
        position = int(prompt_ids.shape[1] - 1)
        clean_text = greedy_generate_with_optional_hook(
            bundle.hooked_model,
            bundle.tokenizer,
            prompt_ids,
            hook_name=None,
            hook_fn=None,
            max_new_tokens=args.max_new_tokens,
        )
        knockout_text = greedy_generate_with_optional_hook(
            bundle.hooked_model,
            bundle.tokenizer,
            prompt_ids,
            hook_name=f"blocks.{args.knockout_layer}.attn.hook_result",
            hook_fn=build_head_knockout_hook(position=position, head_indices=list(args.knockout_heads)),
            max_new_tokens=args.max_new_tokens,
        )
        rows.append(
            {
                "family_id": family_id,
                "clean_answer": parse_answer(clean_text).answer,
                "knockout_answer": parse_answer(knockout_text).answer,
            }
        )

    clean_answers = [row["clean_answer"] for row in rows if row["clean_answer"]]
    knockout_answers = [row["knockout_answer"] for row in rows if row["knockout_answer"]]
    clean_counter = Counter(clean_answers)
    knockout_counter = Counter(knockout_answers)
    dominant_answer, dominant_count = (knockout_counter.most_common(1)[0] if knockout_counter else ("", 0))
    summary = {
        "n_families": len(rows),
        "n_changed_answers": int(sum(row["clean_answer"] != row["knockout_answer"] for row in rows)),
        "dominant_knockout_answer": dominant_answer,
        "dominant_knockout_fraction": float(dominant_count / len(rows)) if rows else 0.0,
        "clean_answer_distribution": dict(clean_counter),
        "knockout_answer_distribution": dict(knockout_counter),
        "verdict": "NO_COLLAPSE" if rows and (dominant_count / len(rows)) <= 0.25 else "POSSIBLE_COLLAPSE",
    }

    with (output_dir / "answer_bias_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["family_id", "clean_answer", "knockout_answer"])
        writer.writeheader()
        writer.writerows(rows)
    write_json(output_dir / "answer_bias_summary.json", summary)
    logger.log_event("ANSWER_BIAS_COMPLETE", **summary)


if __name__ == "__main__":
    main()
