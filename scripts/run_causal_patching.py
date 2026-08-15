#!/usr/bin/env python3
# ruff: noqa: E402
"""Stage 8 causal activation patching over pre-selected sensitive PhysMon families.

Reference:
    `physmon_proposal.pdf` §9, §11 and the Stage 8 forward brief Part A.
"""

from __future__ import annotations

import argparse
import csv
import json
from contextlib import contextmanager
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.models.hooks import find_cue_token_index, set_global_seed  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402
from physmon.utils.io import write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402

from run_behavioural import format_prompt_with_chat_template, load_rendered_families  # noqa: E402


DEFAULT_STAGE = 8
DEFAULT_SEED = 42
DEFAULT_PATCH_SITE = "resid_post_last_prompt"
DEFAULT_JSONL_NAME = "run_causal_patching_events.jsonl"
DEFAULT_BEHAVIOURAL_JSONL = "results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl"
SUPPORTED_PATCH_SITES = ("resid_post_last_prompt", "resid_post_cue_token")
SUPPORTED_HOOK_SITE = "hook_resid_post"
PATCH_MODE_REPLACE = "replace"
PATCH_MODE_HEAD_KNOCKOUT = "head_knockout"
SUPPORTED_PATCH_MODES = (PATCH_MODE_REPLACE, PATCH_MODE_HEAD_KNOCKOUT)
ATTN_RESULT_HOOK_SITE = "attn.hook_result"


@contextmanager
def temporary_forward_hook(module: Any, hook_fn: Any):
    """Register one temporary forward hook and remove it on exit."""

    handle = module.register_forward_hook(hook_fn)
    try:
        yield
    finally:
        handle.remove()


@contextmanager
def temporary_forward_pre_hook(module: Any, hook_fn: Any):
    """Register one temporary forward pre-hook and remove it on exit."""

    handle = module.register_forward_pre_hook(hook_fn)
    try:
        yield
    finally:
        handle.remove()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the Stage 8 causal patching script."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", required=True, help="Registry role or key for the patched model.")
    parser.add_argument("--family-dir", required=True, help="Rendered family JSON directory.")
    parser.add_argument(
        "--patch-families",
        nargs="+",
        required=True,
        help="Ordered template ids to patch.",
    )
    parser.add_argument(
        "--patch-layers",
        nargs="+",
        type=int,
        required=True,
        help="Layer indices whose residual stream will be replaced.",
    )
    parser.add_argument(
        "--patch-site",
        default=DEFAULT_PATCH_SITE,
        choices=SUPPORTED_PATCH_SITES,
        help="Prompt-side activation site to patch.",
    )
    parser.add_argument(
        "--patch-mode",
        default=PATCH_MODE_REPLACE,
        choices=SUPPORTED_PATCH_MODES,
        help="Intervention type: residual replacement or attention-head knockout.",
    )
    parser.add_argument(
        "--head-index",
        type=int,
        default=None,
        help="Attention head index to zero when --patch-mode head_knockout is selected.",
    )
    parser.add_argument(
        "--multi-head-knockout",
        nargs="+",
        type=int,
        default=None,
        metavar="HEAD_IDX",
        help="Optional list of attention heads to zero simultaneously at attn.hook_result.",
    )
    parser.add_argument(
        "--behavioural-jsonl",
        default=DEFAULT_BEHAVIOURAL_JSONL,
        help="Variant-level behavioural JSONL providing original log-probabilities.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for Stage 8 patching artifacts.")
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE, help="Scientific stage number.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed.")
    return parser.parse_args()


def load_variant_logprob_table(path: Path, *, model_role: str) -> dict[str, dict[int, float]]:
    """Load per-family per-variant correct-answer log-probabilities for one model role."""

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


def compute_answer_logprob_from_logits(
    *,
    full_ids: torch.Tensor,
    prompt_length: int,
    logits: torch.Tensor,
) -> float:
    """Compute the continuation log-probability for answer tokens from model logits."""

    device = logits.device
    full_ids = full_ids.to(device)
    log_probs = torch.log_softmax(logits[:, :-1, :], dim=-1)
    answer_start = prompt_length - 1
    answer_end = full_ids.shape[1] - 1
    answer_targets = full_ids[:, answer_start + 1 : answer_end + 1]
    answer_token_logprobs = log_probs[:, answer_start:answer_end, :].gather(
        dim=-1,
        index=answer_targets.unsqueeze(-1),
    )
    return float(answer_token_logprobs.sum().item())


def resolve_patch_position(
    *,
    formatted_prompt: str,
    prompt_token_ids: list[int],
    cue_sentence: str,
    tokenizer: Any,
    patch_site: str,
) -> int:
    """Resolve the patch position for one prompt."""

    if patch_site == "resid_post_last_prompt":
        return len(prompt_token_ids) - 1
    if patch_site == "resid_post_cue_token":
        return find_cue_token_index(formatted_prompt, cue_sentence, tokenizer)
    raise ValueError(f"Unsupported patch site '{patch_site}'.")


def build_patch_hook(base_resid: torch.Tensor, *, position: int):
    """Create a TransformerLens hook that replaces one prompt-side residual vector."""

    def hook(value: torch.Tensor, hook: Any | None = None) -> torch.Tensor:
        del hook
        patched = value.clone()
        patched[:, position, :] = base_resid.unsqueeze(0)
        return patched

    return hook


def build_head_knockout_hook(*, position: int, head_indices: list[int]):
    """Create a TransformerLens hook that zeroes one or more head outputs at one position."""

    def hook(value: torch.Tensor, hook: Any | None = None) -> torch.Tensor:
        del hook
        patched = value.clone()
        for head_index in head_indices:
            patched[:, position, head_index, :] = 0.0
        return patched

    return hook


def build_hf_residual_replace_hook(base_resid: torch.Tensor, *, position: int):
    """Create a HF forward hook that replaces one block output vector."""

    def hook(module: Any, inputs: tuple[Any, ...], output: Any) -> Any:
        del module, inputs
        if isinstance(output, tuple):
            hidden = output[0].clone()
            hidden[:, position, :] = base_resid.unsqueeze(0)
            return (hidden, *output[1:])
        hidden = output.clone()
        hidden[:, position, :] = base_resid.unsqueeze(0)
        return hidden

    return hook


def build_hf_head_knockout_pre_hook(*, position: int, head_indices: list[int], d_head: int):
    """Create a HF pre-hook that zeroes selected head slices before o_proj."""

    def hook(module: Any, inputs: tuple[Any, ...]) -> tuple[Any, ...]:
        del module
        attn_output = inputs[0].clone()
        for head_index in head_indices:
            start = int(head_index) * d_head
            stop = start + d_head
            attn_output[:, position, start:stop] = 0.0
        if len(inputs) == 1:
            return (attn_output,)
        return (attn_output, *inputs[1:])

    return hook


def compute_hf_logits(*, model: Any, input_ids: torch.Tensor) -> torch.Tensor:
    """Run one HF forward pass and return logits."""

    with torch.no_grad():
        outputs = model(input_ids=input_ids, use_cache=False)
    return outputs.logits


def capture_hf_layer_residual(
    *,
    model: Any,
    input_ids: torch.Tensor,
    layer_index: int,
    position: int,
) -> torch.Tensor:
    """Capture one HF transformer block output vector at one position."""

    layer_module = model.model.layers[layer_index]
    captured: list[torch.Tensor] = []

    def hook(module: Any, inputs: tuple[Any, ...], output: Any) -> Any:
        del module, inputs
        hidden = output[0] if isinstance(output, tuple) else output
        captured.append(hidden[0, position, :].detach().clone())
        return output

    with temporary_forward_hook(layer_module, hook):
        _ = compute_hf_logits(model=model, input_ids=input_ids)
    if not captured:
        raise RuntimeError(f"Failed to capture residual from HF layer {layer_index}.")
    return captured[-1]


def locate_sensitive_variant(variant_logprobs: dict[int, float]) -> tuple[int, int, float]:
    """Pick base variant 0 and the most-sensitive variant by maximal logprob drop."""

    if 0 not in variant_logprobs:
        raise KeyError("Expected behavioural log-probabilities for base variant_id 0.")
    base_variant_id = 0
    base_logprob = variant_logprobs[0]
    sensitive_variant_id = max(
        (variant_id for variant_id in variant_logprobs if variant_id != 0),
        key=lambda variant_id: base_logprob - variant_logprobs[variant_id],
    )
    original_slp = base_logprob - variant_logprobs[sensitive_variant_id]
    return base_variant_id, sensitive_variant_id, float(original_slp)


def plot_recovery_curve(layer_means: list[dict[str, float]], output_path: Path) -> None:
    """Plot mean recovery versus patch layer."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    layers = [row["patch_layer"] for row in layer_means]
    recovery = [row["mean_recovery_fraction"] for row in layer_means]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(layers, recovery, marker="o")
    axis.set_xlabel("Patch layer")
    axis.set_ylabel("Mean recovery fraction")
    axis.set_title("Stage 8 Causal Patching Recovery by Layer")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def plot_family_heatmap(
    families: list[str],
    patch_layers: list[int],
    recovery_by_family_layer: dict[str, dict[int, float]],
    output_path: Path,
) -> None:
    """Render a family x layer heatmap of recovery fractions."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matrix = np.asarray(
        [
            [recovery_by_family_layer[family_id].get(layer_index, np.nan) for layer_index in patch_layers]
            for family_id in families
        ],
        dtype=float,
    )
    figure, axis = plt.subplots(figsize=(10, max(4.5, len(families) * 0.35)))
    image = axis.imshow(matrix, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    axis.set_xticks(range(len(patch_layers)), [str(layer) for layer in patch_layers], rotation=45, ha="right")
    axis.set_yticks(range(len(families)), families)
    axis.set_xlabel("Patch layer")
    axis.set_ylabel("Family")
    axis.set_title("Stage 8 Causal Patching Recovery Heatmap")
    figure.colorbar(image, ax=axis, label="Recovery fraction")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def save_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write one CSV artifact with stable field ordering."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Run Stage 8 causal patching over one selected set of sensitive families."""

    args = parse_args()
    set_global_seed(args.seed)
    if args.multi_head_knockout is not None:
        args.patch_mode = PATCH_MODE_HEAD_KNOCKOUT
    if args.patch_mode == PATCH_MODE_HEAD_KNOCKOUT and args.head_index is None and args.multi_head_knockout is None:
        raise ValueError(
            "Provide --head-index or --multi-head-knockout when --patch-mode head_knockout is selected."
        )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_spec = resolve_model_spec(model_key=args.model_role) if args.model_role else resolve_model_spec(role=args.model_role)
    logger = ExperimentLogger(
        script_name="run_causal_patching.py",
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
    behavioural_table = load_variant_logprob_table(
        Path(args.behavioural_jsonl),
        model_role=resolved_spec.role,
    )

    bundle = load_model(
        model_key=resolved_spec.key,
        device="cuda",
        device_map="auto" if resolved_spec.hook_backend != "transformer_lens" else None,
    )
    active_head_indices = None
    if args.patch_mode == PATCH_MODE_HEAD_KNOCKOUT:
        active_head_indices = (
            list(args.multi_head_knockout)
            if args.multi_head_knockout is not None
            else [int(args.head_index)]
        )
        if bundle.hooked_model is not None:
            bundle.hooked_model.set_use_attn_result(True)
            n_heads = int(bundle.hooked_model.cfg.n_heads)
            d_head = int(bundle.hooked_model.cfg.d_head)
        else:
            config = bundle.hf_model.config
            n_heads = int(getattr(config, "num_attention_heads"))
            hidden_size = int(getattr(config, "hidden_size"))
            d_head = hidden_size // n_heads
        invalid_heads = [head_index for head_index in active_head_indices if head_index < 0 or head_index >= n_heads]
        if invalid_heads:
            raise ValueError(
                f"Head indices {invalid_heads} are out of range for model with {n_heads} heads."
            )
    if bundle.hooked_model is not None:
        model_device = next(bundle.hooked_model.parameters()).device
    else:
        model_device = next(bundle.hf_model.parameters()).device

    logger.log_event(
        "CAUSAL_PATCHING_START",
        model_role=resolved_spec.role,
        family_count=len(args.patch_families),
        patch_layers=list(args.patch_layers),
        patch_site=args.patch_site,
        patch_mode=args.patch_mode,
        head_index=args.head_index,
        multi_head_knockout=active_head_indices,
    )

    hook_site_name = SUPPORTED_HOOK_SITE if args.patch_mode == PATCH_MODE_REPLACE else ATTN_RESULT_HOOK_SITE
    candidate_hook_names = {f"blocks.{layer}.{hook_site_name}" for layer in args.patch_layers}

    results_rows: list[dict[str, Any]] = []
    recovery_grid: dict[str, dict[int, float]] = {family_id: {} for family_id in args.patch_families}
    for family_id in args.patch_families:
        family_payload = family_payloads[family_id]
        variant_logprobs = behavioural_table[family_id]
        base_variant_id, sensitive_variant_id, original_slp = locate_sensitive_variant(variant_logprobs)

        variants_by_id = {
            int(variant_payload["variant_id"]): variant_payload for variant_payload in family_payload["variants"]
        }
        base_variant = variants_by_id[base_variant_id]
        sensitive_variant = variants_by_id[sensitive_variant_id]

        answer_ids = bundle.tokenizer(
            str(family_payload["correct_answer"]),
            return_tensors="pt",
            add_special_tokens=False,
        ).input_ids.to(model_device)

        base_prompt = format_prompt_with_chat_template(str(base_variant["prompt"]), bundle.tokenizer)
        sensitive_prompt = format_prompt_with_chat_template(str(sensitive_variant["prompt"]), bundle.tokenizer)
        base_prompt_ids = bundle.tokenizer(base_prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(
            model_device
        )
        sensitive_prompt_ids = bundle.tokenizer(
            sensitive_prompt,
            return_tensors="pt",
            add_special_tokens=True,
        ).input_ids.to(model_device)
        base_full_ids = torch.cat([base_prompt_ids, answer_ids], dim=1)
        sensitive_full_ids = torch.cat([sensitive_prompt_ids, answer_ids], dim=1)

        base_patch_position = resolve_patch_position(
            formatted_prompt=base_prompt,
            prompt_token_ids=base_prompt_ids[0].tolist(),
            cue_sentence=str(base_variant["cue_sentence"]),
            tokenizer=bundle.tokenizer,
            patch_site=args.patch_site,
        )
        sensitive_patch_position = resolve_patch_position(
            formatted_prompt=sensitive_prompt,
            prompt_token_ids=sensitive_prompt_ids[0].tolist(),
            cue_sentence=str(sensitive_variant["cue_sentence"]),
            tokenizer=bundle.tokenizer,
            patch_site=args.patch_site,
        )

        base_cache = None
        if bundle.hooked_model is not None and args.patch_mode == PATCH_MODE_REPLACE:
            _, base_cache = bundle.hooked_model.run_with_cache(
                base_full_ids,
                names_filter=lambda name: name in candidate_hook_names,
            )

        for patch_layer in args.patch_layers:
            if bundle.hooked_model is not None:
                hook_name = f"blocks.{patch_layer}.{hook_site_name}"
                hook_fn = None
                if args.patch_mode == PATCH_MODE_REPLACE:
                    assert base_cache is not None
                    base_resid = base_cache[hook_name][0, base_patch_position, :].detach().clone()
                    hook_fn = build_patch_hook(base_resid, position=sensitive_patch_position)
                else:
                    hook_fn = build_head_knockout_hook(
                        position=sensitive_patch_position,
                        head_indices=list(active_head_indices),
                    )
                patched_logits = bundle.hooked_model.run_with_hooks(
                    sensitive_full_ids,
                    fwd_hooks=[(hook_name, hook_fn)],
                )
            else:
                if args.patch_mode == PATCH_MODE_REPLACE:
                    base_resid = capture_hf_layer_residual(
                        model=bundle.hf_model,
                        input_ids=base_full_ids,
                        layer_index=int(patch_layer),
                        position=base_patch_position,
                    )
                    layer_module = bundle.hf_model.model.layers[int(patch_layer)]
                    hook_fn = build_hf_residual_replace_hook(base_resid, position=sensitive_patch_position)
                    with temporary_forward_hook(layer_module, hook_fn):
                        patched_logits = compute_hf_logits(model=bundle.hf_model, input_ids=sensitive_full_ids)
                else:
                    o_proj_module = bundle.hf_model.model.layers[int(patch_layer)].self_attn.o_proj
                    hook_fn = build_hf_head_knockout_pre_hook(
                        position=sensitive_patch_position,
                        head_indices=list(active_head_indices),
                        d_head=d_head,
                    )
                    with temporary_forward_pre_hook(o_proj_module, hook_fn):
                        patched_logits = compute_hf_logits(model=bundle.hf_model, input_ids=sensitive_full_ids)
            patched_logprob = compute_answer_logprob_from_logits(
                full_ids=sensitive_full_ids,
                prompt_length=int(sensitive_prompt_ids.shape[1]),
                logits=patched_logits,
            )
            patched_slp = variant_logprobs[base_variant_id] - patched_logprob
            recovery_fraction = 1.0 if original_slp == 0.0 else 1.0 - (patched_slp / original_slp)
            row = {
                "family_id": family_id,
                "base_variant_id": base_variant_id,
                "sensitive_variant_id": sensitive_variant_id,
                "patch_layer": int(patch_layer),
                "patch_site": args.patch_site,
                "patch_mode": args.patch_mode,
                "head_index": args.head_index,
                "multi_head_knockout": "" if active_head_indices is None else ",".join(map(str, active_head_indices)),
                "original_S_lp": float(original_slp),
                "patched_S_lp": float(patched_slp),
                "recovery_fraction": float(recovery_fraction),
            }
            results_rows.append(row)
            recovery_grid[family_id][int(patch_layer)] = float(recovery_fraction)

        logger.log_event(
            "CAUSAL_PATCHING_FAMILY_COMPLETE",
            family_id=family_id,
            base_variant_id=base_variant_id,
            sensitive_variant_id=sensitive_variant_id,
            original_slp=original_slp,
        )

    patch_layers_sorted = sorted(set(int(layer) for layer in args.patch_layers))
    layer_summary_rows: list[dict[str, float]] = []
    for patch_layer in patch_layers_sorted:
        layer_values = [
            row["recovery_fraction"] for row in results_rows if int(row["patch_layer"]) == int(patch_layer)
        ]
        layer_summary_rows.append(
            {
                "patch_layer": int(patch_layer),
                "mean_recovery_fraction": float(np.mean(layer_values)),
                "median_recovery_fraction": float(np.median(layer_values)),
            }
        )

    best_layer = max(layer_summary_rows, key=lambda row: row["mean_recovery_fraction"])
    summary_payload = {
        "model_role": resolved_spec.role,
        "patch_site": args.patch_site,
        "patch_mode": args.patch_mode,
        "head_index": args.head_index,
        "multi_head_knockout": active_head_indices,
        "families": list(args.patch_families),
        "patch_layers": patch_layers_sorted,
        "best_causal_layer": int(best_layer["patch_layer"]),
        "best_mean_recovery_fraction": float(best_layer["mean_recovery_fraction"]),
        "layer_means": layer_summary_rows,
        "families_with_gt_50pct_recovery": sorted(
            {
                row["family_id"]
                for row in results_rows
                if int(row["patch_layer"]) == int(best_layer["patch_layer"])
                and float(row["recovery_fraction"]) >= 0.50
            }
        ),
        "families_with_lt_10pct_recovery": sorted(
            {
                row["family_id"]
                for row in results_rows
                if int(row["patch_layer"]) == int(best_layer["patch_layer"])
                and float(row["recovery_fraction"]) < 0.10
            }
        ),
    }

    save_csv(
        output_dir / "patching_results.csv",
        results_rows,
        [
            "family_id",
            "base_variant_id",
            "sensitive_variant_id",
            "patch_layer",
            "patch_site",
            "patch_mode",
            "head_index",
            "multi_head_knockout",
            "original_S_lp",
            "patched_S_lp",
            "recovery_fraction",
        ],
    )
    write_json(output_dir / "patching_summary.json", summary_payload)
    plot_recovery_curve(layer_summary_rows, output_dir / "patching_layer_curve.png")
    plot_family_heatmap(list(args.patch_families), patch_layers_sorted, recovery_grid, output_dir / "patching_family_heatmap.png")

    logger.log_event(
        "CAUSAL_PATCHING_COMPLETE",
        best_causal_layer=int(best_layer["patch_layer"]),
        best_mean_recovery_fraction=float(best_layer["mean_recovery_fraction"]),
        family_count=len(args.patch_families),
        patch_mode=args.patch_mode,
        head_index=args.head_index,
        multi_head_knockout=active_head_indices,
    )


if __name__ == "__main__":
    main()
