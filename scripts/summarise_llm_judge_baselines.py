#!/usr/bin/env python3
# ruff: noqa: E402
"""Summarise Stage 9 LLM judge baseline settings into one ensemble report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="results/stage9/baselines/llm_judge/judge_ensemble_summary.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = REPO_ROOT / "results/stage9/baselines/llm_judge"
    settings = {
        "deepseek_setting_a": base / "deepseek_setting_a/judge_auroc.json",
        "llama_setting_a": base / "llama_setting_a/judge_auroc.json",
        "llama_setting_b": base / "llama_setting_b/judge_auroc.json",
    }

    metrics: dict[str, dict[str, float | int]] = {}
    zero_shot_scores: list[float] = []
    loo_scores: list[float] = []
    for name, path in settings.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        metrics[name] = {
            "zero_shot_auroc": float(payload["zero_shot_auroc"]),
            "loo_probe_auroc": float(payload["loo_probe_auroc"]),
            "auprc": float(payload["auprc"]),
            "brier": float(payload["brier"]),
            "n_parsed": int(payload["n_parsed"]),
        }
        zero_shot_scores.append(float(payload["zero_shot_auroc"]))
        loo_scores.append(float(payload["loo_probe_auroc"]))

    zero_shot_mean = sum(zero_shot_scores) / len(zero_shot_scores)
    zero_shot_min = min(zero_shot_scores)
    zero_shot_max = max(zero_shot_scores)
    zero_shot_range = zero_shot_max - zero_shot_min

    if zero_shot_range < 0.05:
        sensitivity_band = "low"
    elif zero_shot_range < 0.15:
        sensitivity_band = "moderate"
    else:
        sensitivity_band = "high"

    payload = {
        "settings": list(settings.keys()),
        "metrics_by_setting": metrics,
        "zero_shot_auroc_by_setting": {
            name: values["zero_shot_auroc"] for name, values in metrics.items()
        },
        "loo_auroc_by_setting": {
            name: values["loo_probe_auroc"] for name, values in metrics.items()
        },
        "zero_shot_auroc_mean": zero_shot_mean,
        "zero_shot_auroc_min": zero_shot_min,
        "zero_shot_auroc_max": zero_shot_max,
        "zero_shot_auroc_range": zero_shot_range,
        "judge_sensitivity_interpretation": (
            f"Range across settings = {zero_shot_range:.4f}, indicating {sensitivity_band} "
            "judge-choice sensitivity. No single judge treats sensitivity consistently as a "
            "ground truth."
        ),
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
