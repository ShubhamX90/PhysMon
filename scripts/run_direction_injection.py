#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 9 sufficiency test via direction injection at the last prompt token."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.models.hooks import set_global_seed  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402

from run_behavioural import format_prompt_with_chat_template, load_rendered_families  # noqa: E402
from run_causal_patching import (  # noqa: E402
    DEFAULT_BEHAVIOURAL_JSONL,
    DEFAULT_JSONL_NAME,
    compute_answer_logprob_from_logits,
)
from run_probing import load_site_tensors  # noqa: E402


DEFAULT_STAGE = 9
DEFAULT_SEED = 42
DEFAULT_SCALES = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", required=True)
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--activation-dir", required=True)
    parser.add_argument("--slp-csv", required=True)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--inject-layer", type=int, default=16)
    parser.add_argument("--site", default="resid_post_last_prompt")
    parser.add_argument("--injection-scales", nargs="+", type=float, default=list(DEFAULT_SCALES))
    parser.add_argument("--n-pos-direction-families", type=int, default=20)
    parser.add_argument("--n-neg-target-families", type=int, default=30)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def load_family_slp_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_variant_logprobs(path: Path, *, model_role: str) -> dict[str, dict[int, float]]:
    table: dict[str, dict[int, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") != "variant_record":
                continue
            if str(record.get("model_role")) != model_role:
                continue
            table.setdefault(str(record["template_id"]), {})[int(record["variant_id"])] = float(
                record["logprob_correct_answer"]
            )
    return table


def group_activations_by_family(entries: list[dict[str, Any]], tensors: np.ndarray) -> dict[str, np.ndarray]:
    grouped: dict[str, list[tuple[int, int]]] = {}
    for index, entry in enumerate(entries):
        grouped.setdefault(str(entry["template_id"]), []).append((index, int(entry["variant_id"])))
    family_tensors: dict[str, np.ndarray] = {}
    for family_id, positions in grouped.items():
        positions.sort(key=lambda item: item[1])
        family_tensors[family_id] = np.stack([tensors[position] for position, _ in positions], axis=0)
    return family_tensors


def build_injection_hook(direction: torch.Tensor, *, position: int):
    def hook(value: torch.Tensor, hook: Any | None = None) -> torch.Tensor:
        del hook
        patched = value.clone()
        patched[:, position, :] = patched[:, position, :] + direction.unsqueeze(0)
        return patched

    return hook


def plot_dose_response(summary_rows: list[dict[str, Any]], output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    scales = [row["alpha"] for row in summary_rows]
    low = [row["low_family_mean_slp"] for row in summary_rows]
    high = [row["high_family_mean_slp"] for row in summary_rows]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(scales, low, marker="o", label="Low-sensitivity targets")
    axis.plot(scales, high, marker="s", label="High-sensitivity controls")
    axis.set_xlabel("Injection scale alpha")
    axis.set_ylabel("Mean max S_lp")
    axis.set_title("Stage 9 Direction Injection Dose Response")
    axis.legend(loc="best")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role) if args.model_role else resolve_model_spec(role=args.model_role)
    logger = ExperimentLogger(
        script_name="run_direction_injection.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    rows = load_family_slp_rows(Path(args.slp_csv))
    usable_rows = [row for row in rows if row.get("qwen_S_lp", "") not in ("", None)]
    usable_rows.sort(key=lambda row: float(row["qwen_S_lp"]), reverse=True)
    high_rows = usable_rows[: args.n_pos_direction_families]
    low_rows = sorted(usable_rows, key=lambda row: float(row["qwen_S_lp"]))[: args.n_neg_target_families]

    activation_entries, activation_tensors = load_site_tensors(Path(args.activation_dir), args.site)
    activations_by_family = group_activations_by_family(activation_entries, activation_tensors)
    high_mean = np.mean(
        [activations_by_family[row["template_id"]][:, args.inject_layer, :].mean(axis=0) for row in high_rows],
        axis=0,
    )
    low_mean = np.mean(
        [activations_by_family[row["template_id"]][:, args.inject_layer, :].mean(axis=0) for row in low_rows],
        axis=0,
    )
    sensitivity_direction = torch.tensor(high_mean - low_mean, dtype=torch.float32)
    sensitivity_direction = sensitivity_direction / (sensitivity_direction.norm() + 1e-12)

    target_family_ids = [row["template_id"] for row in low_rows]
    control_family_ids = [row["template_id"] for row in high_rows[: min(5, len(high_rows))]]
    all_needed_ids = sorted(set(target_family_ids + control_family_ids))
    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, all_needed_ids)
    }
    behavioural_table = load_variant_logprobs(Path(args.behavioural_jsonl), model_role=resolved_spec.role)

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Direction injection currently requires TransformerLens support.")
    model_device = next(bundle.hooked_model.parameters()).device

    results: list[dict[str, Any]] = []
    for family_id in all_needed_ids:
        family_payload = family_payloads[family_id]
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload for variant_payload in family_payload["variants"]
        }
        variant_logprobs = behavioural_table[family_id]
        answer_ids = bundle.tokenizer(
            str(family_payload["correct_answer"]),
            return_tensors="pt",
            add_special_tokens=False,
        ).input_ids.to(model_device)
        base_variant = variants_by_id[0]
        base_prompt = format_prompt_with_chat_template(str(base_variant["prompt"]), bundle.tokenizer)
        base_prompt_ids = bundle.tokenizer(base_prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(
            model_device
        )
        last_prompt_position = int(base_prompt_ids.shape[1] - 1)
        base_full_ids = torch.cat([base_prompt_ids, answer_ids], dim=1)
        base_logits = bundle.hooked_model(base_full_ids)
        base_logprob = compute_answer_logprob_from_logits(
            full_ids=base_full_ids,
            prompt_length=int(base_prompt_ids.shape[1]),
            logits=base_logits,
        )

        for alpha in args.injection_scales:
            scale_direction = (float(alpha) * sensitivity_direction).to(model_device)
            per_variant_slps: list[float] = []
            for variant_id in sorted(variant_logprobs):
                if variant_id == 0:
                    continue
                variant_payload = variants_by_id[variant_id]
                prompt = format_prompt_with_chat_template(str(variant_payload["prompt"]), bundle.tokenizer)
                prompt_ids = bundle.tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(
                    model_device
                )
                full_ids = torch.cat([prompt_ids, answer_ids], dim=1)
                if alpha == 0.0:
                    logits = bundle.hooked_model(full_ids)
                else:
                    logits = bundle.hooked_model.run_with_hooks(
                        full_ids,
                        fwd_hooks=[
                            (
                                f"blocks.{args.inject_layer}.hook_resid_post",
                                build_injection_hook(scale_direction, position=last_prompt_position),
                            )
                        ],
                    )
                injected_logprob = compute_answer_logprob_from_logits(
                    full_ids=full_ids,
                    prompt_length=int(prompt_ids.shape[1]),
                    logits=logits,
                )
                per_variant_slps.append(float(base_logprob - injected_logprob))
            max_slp = float(max(per_variant_slps)) if per_variant_slps else 0.0
            original_max_slp = float(max(base_logprob - lp for vid, lp in variant_logprobs.items() if vid != 0))
            results.append(
                {
                    "family_id": family_id,
                    "is_low_sensitivity": family_id in set(target_family_ids),
                    "alpha": float(alpha),
                    "S_lp_injected": max_slp,
                    "delta_S_lp": float(max_slp - original_max_slp),
                }
            )

    summary_rows: list[dict[str, Any]] = []
    for alpha in args.injection_scales:
        alpha_rows = [row for row in results if float(row["alpha"]) == float(alpha)]
        low_alpha = [row["S_lp_injected"] for row in alpha_rows if row["is_low_sensitivity"]]
        high_alpha = [row["S_lp_injected"] for row in alpha_rows if not row["is_low_sensitivity"]]
        summary_rows.append(
            {
                "alpha": float(alpha),
                "low_family_mean_slp": float(np.mean(low_alpha)) if low_alpha else 0.0,
                "high_family_mean_slp": float(np.mean(high_alpha)) if high_alpha else 0.0,
                "low_family_fraction_ge_0_5": float(np.mean(np.asarray(low_alpha) >= 0.5)) if low_alpha else 0.0,
            }
        )

    monotonic = all(
        summary_rows[idx + 1]["low_family_mean_slp"] >= summary_rows[idx]["low_family_mean_slp"] - 1e-6
        for idx in range(len(summary_rows) - 1)
    )
    summary = {
        "inject_layer": int(args.inject_layer),
        "n_low_families": len(target_family_ids),
        "n_high_controls": len(control_family_ids),
        "dose_response": summary_rows,
        "sufficiency_verdict": (
            "SUFFICIENCY_CONFIRMED"
            if monotonic and summary_rows[-1]["low_family_fraction_ge_0_5"] >= 0.5
            else "NO_SUFFICIENCY"
        ),
    }

    with (output_dir / "injection_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["family_id", "is_low_sensitivity", "alpha", "S_lp_injected", "delta_S_lp"],
        )
        writer.writeheader()
        writer.writerows(results)
    write_json(output_dir / "injection_summary.json", summary)
    plot_dose_response(summary_rows, output_dir / "dose_response_curve.png")
    logger.log_event("DIRECTION_INJECTION_COMPLETE", **summary)


if __name__ == "__main__":
    main()
