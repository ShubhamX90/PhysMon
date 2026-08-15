#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 10 token-level entropy baseline without oracle access to y*."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.formal.constructs import STAGE6_EXCLUDE_FROM_PROBE  # noqa: E402
from physmon.models.hooks import set_global_seed  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402

from run_behavioural import format_prompt_with_chat_template, load_rendered_families  # noqa: E402


DEFAULT_STAGE = 10
DEFAULT_SEED = 42
DEFAULT_FAMILY_DIR = "results/stage6/generated_full_benchmark/"
DEFAULT_OUTPUT_DIR = "results/stage10/baselines/token_entropy/"
DEFAULT_POSITIVES = "results/stage6/analysis_d2/stage6_positive_families.json"
DEFAULT_JSONL_NAME = "run_token_entropy_baseline_events.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", default="qwen_primary")
    parser.add_argument("--family-dir", default=DEFAULT_FAMILY_DIR)
    parser.add_argument("--positive-families-file", default=DEFAULT_POSITIVES)
    parser.add_argument("--topk", type=int, default=1000)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--cache-json",
        default=None,
        help="Optional cached token_entropy_per_family.json path. When provided, skips model inference and recomputes metrics from cached entropies.",
    )
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def compute_entropy_from_logits(logits: torch.Tensor, *, topk: int) -> float:
    next_token_logits = logits[:, -1, :]
    k = min(int(topk), int(next_token_logits.shape[-1]))
    top_values, _ = torch.topk(next_token_logits, k=k, dim=-1)
    log_probs = torch.log_softmax(top_values, dim=-1)
    probs = torch.softmax(top_values, dim=-1)
    entropy = -(probs * log_probs).sum(dim=-1)
    return float(entropy.item())


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    positives = set(json.loads(Path(args.positive_families_file).read_text())["positive_families"])
    resolved_spec = resolve_model_spec(model_key=args.model_role)
    logger = ExperimentLogger(
        script_name="run_token_entropy_baseline.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    if args.cache_json:
        per_family_rows = json.loads(Path(args.cache_json).read_text())
    else:
        rendered_files = sorted(
            path for path in Path(args.family_dir).glob("*.json") if path.stem not in STAGE6_EXCLUDE_FROM_PROBE
        )
        family_ids = [path.stem for path in rendered_files if path.stem != "assembly_summary"]
        family_payloads = {
            payload["template_id"]: payload
            for payload in load_rendered_families(args.family_dir, family_ids)
        }

        bundle = load_model(model_key=resolved_spec.key, device="cuda")
        model = bundle.hooked_model if bundle.hooked_model is not None else bundle.hf_model
        model_device = next(model.parameters()).device

        per_family_rows: list[dict[str, Any]] = []
        for family_id in sorted(family_payloads):
            payload = family_payloads[family_id]
            entropies: list[float] = []
            for variant in sorted(payload["variants"], key=lambda item: int(item["variant_id"])):
                prompt = format_prompt_with_chat_template(str(variant["prompt"]), bundle.tokenizer)
                prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(model_device)
                with torch.no_grad():
                    logits = model(prompt_ids)
                entropies.append(compute_entropy_from_logits(logits, topk=args.topk))
            entropy_std = float(np.std(entropies))
            entropy_mean = float(np.mean(entropies))
            per_family_rows.append(
                {
                    "template_id": family_id,
                    "entropy_std": entropy_std,
                    "entropy_mean": entropy_mean,
                    "variant_entropies": entropies,
                    "true_label": int(family_id in positives),
                }
            )

    y = np.asarray([int(row["true_label"]) for row in per_family_rows], dtype=int)
    std_scores = np.asarray([float(row["entropy_std"]) for row in per_family_rows], dtype=float)
    mean_scores = np.asarray([float(row["entropy_mean"]) for row in per_family_rows], dtype=float)

    # The Stage 10 brief defines token-level entropy spread itself as the sensitivity score.
    # We therefore report direct AUROC/AUPRC on entropy spread rather than a second learned wrapper.
    for row, score in zip(per_family_rows, std_scores, strict=True):
        row["prediction"] = float(score)

    summary = {
        "n_families": int(len(per_family_rows)),
        "feature_definition": f"token_entropy_topk_{args.topk}_std_across_4_variants",
        "auroc": float(roc_auc_score(y, std_scores)),
        "auprc": float(average_precision_score(y, std_scores)),
        "mean_entropy_auroc": float(roc_auc_score(y, mean_scores)),
        "mean_entropy_auprc": float(average_precision_score(y, mean_scores)),
        "mean_entropy_flipped_auroc": float(roc_auc_score(y, -mean_scores)),
        "mean_entropy_flipped_auprc": float(average_precision_score(y, -mean_scores)),
        "topk": int(args.topk),
    }
    write_json(output_dir / "token_entropy_summary.json", summary)
    write_json(output_dir / "token_entropy_per_family.json", per_family_rows)
    logger.log_event("TOKEN_ENTROPY_BASELINE_COMPLETE", **summary)


if __name__ == "__main__":
    main()
