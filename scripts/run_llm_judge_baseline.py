#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 9 LLM judge baseline for shortcut-sensitivity prediction."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.probing.metrics import compute_auprc, compute_auroc, compute_brier  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402

from run_behavioural import DEFAULT_MAX_NEW_TOKENS, format_prompt_with_chat_template, load_rendered_families, set_seed  # noqa: E402
from run_causal_patching import DEFAULT_BEHAVIOURAL_JSONL, DEFAULT_JSONL_NAME, locate_sensitive_variant  # noqa: E402
from run_probing import infer_positive_families  # noqa: E402


DEFAULT_STAGE = 9
DEFAULT_SEED = 42
THINK_CLOSE_TAG = "</think>"
CONFIDENCE_PATTERN = re.compile(r"CONFIDENCE:\s*([0-9.]+)", re.IGNORECASE)
PROB_PATTERN = re.compile(r"SENSITIVITY_PROBABILITY:\s*([0-9.]+)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge-model", required=True)
    parser.add_argument("--judge-setting", choices=("A", "B"), required=True)
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--slp-csv", required=True)
    parser.add_argument("--positive-families-file", required=True)
    parser.add_argument("--exclude-ids", nargs="*", default=())
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def load_variant_logprobs_unfiltered(path: Path) -> dict[str, dict[int, float]]:
    """Load per-family per-variant logprobs from a single-model behavioural JSONL."""

    table: dict[str, dict[int, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") != "variant_record":
                continue
            table.setdefault(str(record["template_id"]), {})[int(record["variant_id"])] = float(
                record["logprob_correct_answer"]
            )
    return table


def strip_thinking(text: str) -> str:
    return text.split(THINK_CLOSE_TAG)[-1].strip() if THINK_CLOSE_TAG in text else text.strip()


def build_judge_prompt(*, setting: str, base_prompt: str, sensitive_prompt: str, single_prompt: str, correct_answer: str) -> str:
    if setting == "A":
        return (
            "You are evaluating whether a physics problem is sensitive to an irrelevant variable.\n\n"
            "Problem A (base version):\n"
            f"{base_prompt}\n\n"
            "Problem B (modified version, one irrelevant detail changed):\n"
            f"{sensitive_prompt}\n\n"
            f"The correct answer to BOTH problems is: {correct_answer}\n\n"
            "Question: Is an AI language model likely to show significantly different internal confidence "
            "in the correct answer between these two versions?\n\n"
            "Respond exactly in this format:\n"
            "PREDICTION: [YES/NO]\n"
            "CONFIDENCE: [0.0-1.0]"
        )
    return (
        "A physics problem is given below. One variable in it is physically irrelevant to computing the answer.\n\n"
        f"Physics problem:\n{single_prompt}\n\n"
        f"The correct answer is: {correct_answer}\n\n"
        "Question: How likely is an AI language model to be internally sensitive to that irrelevant variable?\n\n"
        "Respond exactly in this format:\n"
        "SENSITIVITY_PROBABILITY: [0.0-1.0]"
    )


def sample_judge_response(bundle: Any, prompt: str, max_new_tokens: int) -> str:
    prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(bundle.hf_model.device)
    attention_mask = torch.ones_like(prompt_ids)
    outputs = bundle.hf_model.generate(
        input_ids=prompt_ids,
        attention_mask=attention_mask,
        do_sample=False,
        max_new_tokens=max_new_tokens,
        pad_token_id=bundle.tokenizer.eos_token_id,
    )
    continuation_ids = outputs[:, prompt_ids.shape[1] :]
    return bundle.tokenizer.decode(continuation_ids[0], skip_special_tokens=True).strip()


def parse_judge_response(response_text: str, setting: str) -> tuple[int, float]:
    text = strip_thinking(response_text)
    upper = text.upper()
    if setting == "A":
        prediction = 1 if "YES" in upper else 0
        match = CONFIDENCE_PATTERN.search(text)
        confidence = float(match.group(1)) if match else (0.8 if prediction else 0.2)
        return prediction, float(np.clip(confidence, 0.0, 1.0))
    match = PROB_PATTERN.search(text)
    probability = float(match.group(1)) if match else 0.5
    probability = float(np.clip(probability, 0.0, 1.0))
    return int(probability >= 0.5), probability


def fit_loo_logistic(scores: np.ndarray, labels: np.ndarray, family_ids: list[str]) -> float:
    preds: list[float] = []
    ordered_ids: list[str] = []
    for held_out_index, family_id in enumerate(family_ids):
        test_mask = np.asarray([index == held_out_index for index in range(len(family_ids))], dtype=bool)
        train_mask = ~test_mask
        model = LogisticRegression(class_weight="balanced", max_iter=2000, solver="liblinear", random_state=DEFAULT_SEED)
        model.fit(scores[train_mask].reshape(-1, 1), labels[train_mask])
        preds.append(float(model.predict_proba(scores[test_mask].reshape(-1, 1))[:, 1][0]))
        ordered_ids.append(family_id)
    return compute_auroc(labels, np.asarray(preds, dtype=float))


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        resolved_spec = resolve_model_spec(model_key=args.judge_model)
    except Exception:
        resolved_spec = resolve_model_spec(role=args.judge_model)
    logger = ExperimentLogger(
        script_name="run_llm_judge_baseline.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )
    positive_families, _ = infer_positive_families(
        family_csv=Path(args.slp_csv),
        positive_families_file=Path(args.positive_families_file),
    )
    payloads = [
        payload
        for payload in load_rendered_families(args.family_dir)
        if payload["template_id"] not in set(args.exclude_ids)
    ]
    behavioural_table = load_variant_logprobs_unfiltered(Path(args.behavioural_jsonl))
    bundle = load_model(model_key=resolved_spec.key, device="cuda", device_map="auto" if "deepseek" in resolved_spec.key else None)

    rows: list[dict[str, Any]] = []
    score_list: list[float] = []
    label_list: list[int] = []
    family_ids: list[str] = []
    for payload in payloads:
        family_id = str(payload["template_id"])
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload for variant_payload in payload["variants"]
        }
        _, sensitive_variant_id, _ = locate_sensitive_variant(behavioural_table[family_id])
        base_prompt = format_prompt_with_chat_template(str(variants_by_id[0]["prompt"]), bundle.tokenizer)
        sensitive_prompt = format_prompt_with_chat_template(str(variants_by_id[sensitive_variant_id]["prompt"]), bundle.tokenizer)
        judge_prompt = build_judge_prompt(
            setting=args.judge_setting,
            base_prompt=base_prompt,
            sensitive_prompt=sensitive_prompt,
            single_prompt=sensitive_prompt,
            correct_answer=str(payload["correct_answer"]),
        )
        raw_response = sample_judge_response(bundle, judge_prompt, args.max_new_tokens)
        parsed_prediction, confidence = parse_judge_response(raw_response, args.judge_setting)
        true_label = int(family_id in positive_families)
        rows.append(
            {
                "family_id": family_id,
                "true_label": true_label,
                "judge_prediction": parsed_prediction,
                "judge_confidence": confidence,
                "parsed_correctly": int(True),
            }
        )
        score_list.append(confidence)
        label_list.append(true_label)
        family_ids.append(family_id)

    labels = np.asarray(label_list, dtype=int)
    scores = np.asarray(score_list, dtype=float)
    zero_shot_auroc = compute_auroc(labels, scores)
    loo_probe_auroc = fit_loo_logistic(scores, labels, family_ids)
    summary = {
        "zero_shot_auroc": zero_shot_auroc,
        "loo_probe_auroc": loo_probe_auroc,
        "auprc": compute_auprc(labels, scores),
        "brier": compute_brier(labels, scores),
        "n_parsed": len(rows),
    }

    with (output_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["family_id", "true_label", "judge_prediction", "judge_confidence", "parsed_correctly"],
        )
        writer.writeheader()
        writer.writerows(rows)
    write_json(output_dir / "judge_auroc.json", summary)
    logger.log_event("LLM_JUDGE_COMPLETE", judge_model=args.judge_model, judge_setting=args.judge_setting, **summary)


if __name__ == "__main__":
    main()
