#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 9 norm-matched random-direction control for the Stage 8 head circuit result."""

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
    load_variant_logprob_table,
    locate_sensitive_variant,
)


DEFAULT_STAGE = 9
DEFAULT_SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", required=True)
    parser.add_argument("--family-dir", required=True)
    parser.add_argument("--patch-families", nargs="+", required=True)
    parser.add_argument("--prior-mhk-results", required=True)
    parser.add_argument("--patch-layer", type=int, default=16)
    parser.add_argument("--head-indices", nargs="+", type=int, required=True)
    parser.add_argument("--n-random-directions", type=int, default=20)
    parser.add_argument("--behavioural-jsonl", default=DEFAULT_BEHAVIOURAL_JSONL)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def load_actual_recoveries(path: Path, *, patch_layer: int) -> dict[str, float]:
    """Load the actual multi-head knockout recoveries at the target patch layer."""

    recoveries: dict[str, float] = {}
    with (path / "patching_results.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if int(row["patch_layer"]) != patch_layer:
                continue
            recoveries[str(row["family_id"])] = float(row["recovery_fraction"])
    if not recoveries:
        raise FileNotFoundError(f"No patching results found for patch_layer={patch_layer} under {path}.")
    return recoveries


def build_residual_subtraction_hook(direction: torch.Tensor, *, position: int):
    """Subtract one direction from the residual stream at the last prompt token."""

    def hook(value: torch.Tensor, hook: Any | None = None) -> torch.Tensor:
        del hook
        patched = value.clone()
        patched[:, position, :] = patched[:, position, :] - direction.unsqueeze(0)
        return patched

    return hook


def capture_actual_intervention(
    model: Any,
    sensitive_full_ids: torch.Tensor,
    *,
    patch_layer: int,
    position: int,
    head_indices: list[int],
) -> torch.Tensor:
    """Capture the summed attention-head intervention vector at the requested site."""

    capture: dict[str, torch.Tensor] = {}

    def hook(value: torch.Tensor, hook: Any | None = None) -> torch.Tensor:
        del hook
        capture["vec"] = value[0, position, head_indices, :].detach().float().sum(dim=0).cpu()
        return value

    model.run_with_hooks(
        sensitive_full_ids,
        fwd_hooks=[(f"blocks.{patch_layer}.attn.hook_result", hook)],
    )
    if "vec" not in capture:
        raise RuntimeError("Failed to capture the actual intervention vector.")
    return capture["vec"]


def plot_comparison(results: list[dict[str, Any]], output_path: Path) -> None:
    """Render a compact actual-vs-random comparison plot."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    families = [row["family_id"] for row in results]
    actual = [row["actual_mhk_recovery"] for row in results]
    random_mean = [row["random_direction_mean_recovery"] for row in results]
    random_p95 = [row["random_direction_p95_recovery"] for row in results]

    x = np.arange(len(families))
    figure, axis = plt.subplots(figsize=(12, max(4.5, len(families) * 0.32)))
    axis.scatter(actual, x, label="Actual 4-head knockout", color="tab:blue")
    axis.scatter(random_mean, x, label="Random mean", color="tab:orange")
    axis.scatter(random_p95, x, label="Random p95", color="tab:red", marker="x")
    axis.set_yticks(x, families)
    axis.set_xlabel("Recovery fraction")
    axis.set_title("Stage 9 Random-Direction Control")
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
        script_name="run_random_direction_control.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_name=resolved_spec.name,
        model_role=resolved_spec.role,
    )

    family_payloads = {
        payload["template_id"]: payload
        for payload in load_rendered_families(args.family_dir, list(args.patch_families))
    }
    behavioural_table = load_variant_logprob_table(Path(args.behavioural_jsonl), model_role=resolved_spec.role)
    actual_recoveries = load_actual_recoveries(Path(args.prior_mhk_results), patch_layer=args.patch_layer)

    bundle = load_model(model_key=resolved_spec.key, device="cuda")
    if bundle.hooked_model is None:
        raise NotImplementedError("Random-direction control requires TransformerLens support.")
    bundle.hooked_model.set_use_attn_result(True)
    model_device = next(bundle.hooked_model.parameters()).device
    rng = np.random.default_rng(args.seed)

    results: list[dict[str, Any]] = []
    for family_id in args.patch_families:
        family_payload = family_payloads[family_id]
        variant_logprobs = behavioural_table[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(variant_logprobs)
        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload for variant_payload in family_payload["variants"]
        }
        sensitive_variant = variants_by_id[sensitive_variant_id]

        answer_ids = bundle.tokenizer(
            str(family_payload["correct_answer"]),
            return_tensors="pt",
            add_special_tokens=False,
        ).input_ids.to(model_device)
        sensitive_prompt = format_prompt_with_chat_template(str(sensitive_variant["prompt"]), bundle.tokenizer)
        sensitive_prompt_ids = bundle.tokenizer(
            sensitive_prompt,
            return_tensors="pt",
            add_special_tokens=True,
        ).input_ids.to(model_device)
        sensitive_full_ids = torch.cat([sensitive_prompt_ids, answer_ids], dim=1)
        last_prompt_position = int(sensitive_prompt_ids.shape[1] - 1)

        intervention = capture_actual_intervention(
            bundle.hooked_model,
            sensitive_full_ids,
            patch_layer=args.patch_layer,
            position=last_prompt_position,
            head_indices=list(args.head_indices),
        )
        intervention_norm = float(intervention.norm().item())
        random_recoveries: list[float] = []
        for _ in range(args.n_random_directions):
            direction = rng.normal(size=intervention.shape[0]).astype(np.float32)
            direction /= np.linalg.norm(direction) + 1e-12
            direction *= intervention_norm
            direction_tensor = torch.tensor(direction, device=model_device, dtype=torch.float32)
            patched_logits = bundle.hooked_model.run_with_hooks(
                sensitive_full_ids,
                fwd_hooks=[
                    (
                        f"blocks.{args.patch_layer}.hook_resid_post",
                        build_residual_subtraction_hook(direction_tensor, position=last_prompt_position),
                    )
                ],
            )
            patched_logprob = compute_answer_logprob_from_logits(
                full_ids=sensitive_full_ids,
                prompt_length=int(sensitive_prompt_ids.shape[1]),
                logits=patched_logits,
            )
            random_slp = float(variant_logprobs[base_variant_id] - patched_logprob)
            random_recovery = 0.0 if abs(original_slp) < 1e-6 else 1.0 - (random_slp / original_slp)
            random_recoveries.append(float(random_recovery))

        actual_recovery = float(actual_recoveries[family_id])
        random_mean = float(np.mean(random_recoveries))
        random_p95 = float(np.percentile(random_recoveries, 95))
        specificity_ratio = float("inf") if abs(random_mean) < 1e-8 else float(actual_recovery / random_mean)
        results.append(
            {
                "family_id": family_id,
                "original_S_lp": float(original_slp),
                "intervention_norm": intervention_norm,
                "actual_mhk_recovery": actual_recovery,
                "random_direction_mean_recovery": random_mean,
                "random_direction_std_recovery": float(np.std(random_recoveries)),
                "random_direction_p95_recovery": random_p95,
                "specificity_ratio": specificity_ratio,
                "interpretation": "SPECIFIC" if actual_recovery > random_p95 else "NOT_SPECIFIC",
                "random_recoveries": random_recoveries,
            }
        )

    summary = {
        "n_families": len(results),
        "n_random_directions": int(args.n_random_directions),
        "patch_layer": int(args.patch_layer),
        "head_indices": list(args.head_indices),
        "mean_actual_mhk_recovery": float(np.mean([row["actual_mhk_recovery"] for row in results])),
        "mean_random_direction_recovery": float(np.mean([row["random_direction_mean_recovery"] for row in results])),
        "fraction_specific": f"{sum(row['interpretation'] == 'SPECIFIC' for row in results)}/{len(results)}",
        "mean_specificity_ratio": float(
            np.mean(
                [
                    row["specificity_ratio"]
                    for row in results
                    if np.isfinite(float(row["specificity_ratio"]))
                ]
            )
        ),
        "causal_specificity_verdict": (
            "CONFIRMED"
            if sum(row["interpretation"] == "SPECIFIC" for row in results) >= 14
            else "NOT_CONFIRMED"
        ),
    }

    with (output_dir / "rdc_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "family_id",
                "original_S_lp",
                "intervention_norm",
                "actual_mhk_recovery",
                "random_direction_mean_recovery",
                "random_direction_std_recovery",
                "random_direction_p95_recovery",
                "specificity_ratio",
                "interpretation",
                "random_recoveries",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow({**row, "random_recoveries": json.dumps(row["random_recoveries"])})
    write_json(output_dir / "rdc_summary.json", summary)
    plot_comparison(results, output_dir / "rdc_comparison_plot.png")
    logger.log_event("RANDOM_DIRECTION_CONTROL_COMPLETE", **summary)


if __name__ == "__main__":
    main()
