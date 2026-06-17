#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 9 self-consistency baseline over repeated sampled generations."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.benchmark.parser import parse_answer  # noqa: E402
from physmon.probing.metrics import compute_auprc, compute_auroc, compute_brier  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402

from run_behavioural import DEFAULT_MAX_NEW_TOKENS, format_prompt_with_chat_template, load_rendered_families, set_seed  # noqa: E402
from run_probing import infer_positive_families  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402


DEFAULT_STAGE = 9
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "run_self_consistency_baseline_events.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", required=True)
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--positive-families-file", required=True)
    parser.add_argument("--exclude-ids", nargs="*", default=())
    parser.add_argument("--n-samples", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def sample_completion(bundle: Any, prompt: str, *, n_samples: int, temperature: float, top_p: float, max_new_tokens: int) -> list[str]:
    prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(bundle.hf_model.device)
    attention_mask = torch.ones_like(prompt_ids)
    outputs = bundle.hf_model.generate(
        input_ids=prompt_ids,
        attention_mask=attention_mask,
        do_sample=True,
        temperature=temperature,
        top_p=top_p,
        num_return_sequences=n_samples,
        max_new_tokens=max_new_tokens,
        pad_token_id=bundle.tokenizer.eos_token_id,
    )
    continuation_ids = outputs[:, prompt_ids.shape[1] :]
    return [bundle.tokenizer.decode(ids, skip_special_tokens=True).strip() for ids in continuation_ids]


def modal_consistency(canonical_answers: list[str | None]) -> tuple[float, str | None]:
    normalized = [answer for answer in canonical_answers if answer is not None]
    if not normalized:
        return 0.0, None
    counter = Counter(normalized)
    modal_answer, modal_count = counter.most_common(1)[0]
    return modal_count / max(1, len(canonical_answers)), modal_answer


def fit_loo_logistic(features: np.ndarray, labels: np.ndarray, family_ids: list[str]) -> tuple[dict[str, float], list[dict[str, Any]]]:
    predictions: list[dict[str, Any]] = []
    for held_out_index, family_id in enumerate(family_ids):
        test_mask = np.asarray([index == held_out_index for index in range(len(family_ids))], dtype=bool)
        train_mask = ~test_mask
        model = LogisticRegression(class_weight="balanced", max_iter=2000, solver="liblinear", random_state=DEFAULT_SEED)
        model.fit(features[train_mask], labels[train_mask])
        score = float(model.predict_proba(features[test_mask])[:, 1][0])
        predictions.append({"template_id": family_id, "prediction": score, "true_label": int(labels[held_out_index])})
    ordered = sorted(predictions, key=lambda item: item["template_id"])
    y_true = np.asarray([row["true_label"] for row in ordered], dtype=int)
    y_score = np.asarray([row["prediction"] for row in ordered], dtype=float)
    summary = {
        "auroc": compute_auroc(y_true, y_score),
        "auprc": compute_auprc(y_true, y_score),
        "brier": compute_brier(y_true, y_score),
    }
    return summary, ordered


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role) if args.model_role else resolve_model_spec(role=args.model_role)
    logger = ExperimentLogger(
        script_name="run_self_consistency_baseline.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )
    positive_families, _ = infer_positive_families(
        family_csv=Path("results/stage6/analysis_d2/stage6_d1_per_family.csv"),
        positive_families_file=Path(args.positive_families_file),
    )
    payloads = [
        payload
        for payload in load_rendered_families(args.family_dir)
        if payload["template_id"] not in set(args.exclude_ids)
    ]
    bundle = load_model(model_key=resolved_spec.key, device="cuda")

    family_scores: list[dict[str, Any]] = []
    features: list[list[float]] = []
    labels: list[int] = []
    family_ids: list[str] = []
    for payload in payloads:
        family_id = str(payload["template_id"])
        variant_consistency: list[float] = []
        modal_answers: list[str | None] = []
        for variant in payload["variants"]:
            prompt = format_prompt_with_chat_template(str(variant["prompt"]), bundle.tokenizer)
            generations = sample_completion(
                bundle,
                prompt,
                n_samples=args.n_samples,
                temperature=args.temperature,
                top_p=args.top_p,
                max_new_tokens=args.max_new_tokens,
            )
            parsed = [parse_answer(text).answer for text in generations]
            consistency, modal = modal_consistency(parsed)
            variant_consistency.append(float(consistency))
            modal_answers.append(modal)
        family_min_consistency = float(min(variant_consistency))
        unique_modal_answers = len({answer for answer in modal_answers if answer is not None})
        family_cross_variant_diversity = float(unique_modal_answers / max(1, len(modal_answers)))
        family_scores.append(
            {
                "template_id": family_id,
                "family_min_consistency": family_min_consistency,
                "family_cross_variant_diversity": family_cross_variant_diversity,
                "variant_consistency": variant_consistency,
            }
        )
        features.append([family_min_consistency, family_cross_variant_diversity])
        labels.append(int(family_id in positive_families))
        family_ids.append(family_id)

    feature_array = np.asarray(features, dtype=float)
    label_array = np.asarray(labels, dtype=int)
    summary, loo_predictions = fit_loo_logistic(feature_array, label_array, family_ids)
    comparison = {
        "hidden_state_probe_auroc": 0.731,
        "self_consistency_probe_auroc": float(summary["auroc"]),
        "advantage_of_hidden_state_over_self_consistency": float(0.731 - summary["auroc"]),
    }

    write_json(output_dir / "family_consistency_scores.json", family_scores)
    write_json(output_dir / "self_consistency_probe.json", summary)
    write_json(output_dir / "loo_predictions_self_consistency.json", loo_predictions)
    write_json(output_dir / "comparison.json", comparison)
    logger.log_event("SELF_CONSISTENCY_COMPLETE", **summary)


if __name__ == "__main__":
    main()
