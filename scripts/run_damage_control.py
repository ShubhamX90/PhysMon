#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 9 damage-control check for the 4-head layer-16 intervention."""

from __future__ import annotations

import argparse
import csv
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


DEFAULT_STAGE = 9
DEFAULT_SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", required=True)
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


def load_negative_family_ids(path: Path, n_negative_families: int) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    candidates = [
        row for row in rows
        if row.get("qwen_S_lp", "") not in ("", None) and float(row["qwen_S_lp"]) < 0.5
    ]
    candidates.sort(key=lambda row: float(row["qwen_S_lp"]))
    return [row["template_id"] for row in candidates[:n_negative_families]]


def canonicalize_answer(answer: str) -> str | None:
    parsed = parse_answer(str(answer))
    return parsed.answer if parsed.is_confident else None


def build_head_knockout_hook(*, position: int, head_indices: list[int]):
    def hook(value: torch.Tensor, hook: Any | None = None) -> torch.Tensor:
        del hook
        patched = value.clone()
        for head_index in head_indices:
            patched[:, position, head_index, :] = 0.0
        return patched

    return hook


def greedy_generate_with_optional_hook(
    model: Any,
    tokenizer: Any,
    prompt_ids: torch.Tensor,
    *,
    hook_name: str | None,
    hook_fn,
    max_new_tokens: int,
) -> str:
    """Simple greedy generation loop that can run with one forward hook."""

    generated = prompt_ids.clone()
    eos_token_id = tokenizer.eos_token_id
    for _ in range(max_new_tokens):
        if hook_name is None:
            logits = model(generated)
        else:
            logits = model.run_with_hooks(generated, fwd_hooks=[(hook_name, hook_fn)])
        next_token = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
        generated = torch.cat([generated, next_token], dim=1)
        if eos_token_id is not None and int(next_token.item()) == int(eos_token_id):
            break
    continuation_ids = generated[:, prompt_ids.shape[1] :]
    return tokenizer.decode(continuation_ids[0], skip_special_tokens=True).strip()


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role) if args.model_role else resolve_model_spec(role=args.model_role)
    logger = ExperimentLogger(
        script_name="run_damage_control.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    negative_family_ids = load_negative_family_ids(Path(args.negative_families_csv), args.n_negative_families)
    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, negative_family_ids)
    }
    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Damage control currently requires TransformerLens support.")
    bundle.hooked_model.set_use_attn_result(True)
    model_device = next(bundle.hooked_model.parameters()).device

    rows: list[dict[str, Any]] = []
    for family_id in negative_family_ids:
        family_payload = family_payloads[family_id]
        expected_answer = canonicalize_answer(str(family_payload["correct_answer"]))
        for variant in family_payload["variants"]:
            prompt = format_prompt_with_chat_template(str(variant["prompt"]), bundle.tokenizer)
            prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(model_device)
            last_prompt_position = int(prompt_ids.shape[1] - 1)
            clean_text = greedy_generate_with_optional_hook(
                bundle.hooked_model,
                bundle.tokenizer,
                prompt_ids,
                hook_name=None,
                hook_fn=None,
                max_new_tokens=args.max_new_tokens,
            )
            knocked_text = greedy_generate_with_optional_hook(
                bundle.hooked_model,
                bundle.tokenizer,
                prompt_ids,
                hook_name=f"blocks.{args.knockout_layer}.attn.hook_result",
                hook_fn=build_head_knockout_hook(
                    position=last_prompt_position,
                    head_indices=list(args.knockout_heads),
                ),
                max_new_tokens=args.max_new_tokens,
            )
            clean_parsed = parse_answer(clean_text).answer
            knocked_parsed = parse_answer(knocked_text).answer
            rows.append(
                {
                    "family_id": family_id,
                    "variant_id": int(variant["variant_id"]),
                    "correct_without_knockout": int(clean_parsed == expected_answer),
                    "correct_with_knockout": int(knocked_parsed == expected_answer),
                }
            )

    clean_accuracy = float(np.mean([row["correct_without_knockout"] for row in rows])) if rows else 0.0
    knocked_accuracy = float(np.mean([row["correct_with_knockout"] for row in rows])) if rows else 0.0
    summary = {
        "n_families_tested": len(negative_family_ids),
        "n_variants_tested": len(rows),
        "accuracy_without_knockout": clean_accuracy,
        "accuracy_with_knockout": knocked_accuracy,
        "accuracy_delta": float(knocked_accuracy - clean_accuracy),
        "verdict": "ACCEPTABLE (< 5% drop)" if clean_accuracy - knocked_accuracy < 0.05 else "UNACCEPTABLE (>= 5% drop)",
    }

    with (output_dir / "damage_control_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "family_id",
                "variant_id",
                "correct_without_knockout",
                "correct_with_knockout",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    write_json(output_dir / "damage_control_summary.json", summary)
    logger.log_event("DAMAGE_CONTROL_COMPLETE", **summary)


if __name__ == "__main__":
    main()
