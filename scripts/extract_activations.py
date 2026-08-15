#!/usr/bin/env python3
# ruff: noqa: E402
"""Extract pre-registered Stage 5 prompt-side activations from primary models.

Reference:
    `physmon_proposal.pdf` §9, §11 and the Stage 5 brief Part C.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import torch
from transformers import AutoConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.models.hooks import extract_targeted_activations, find_cue_token_index, set_global_seed  # noqa: E402
from physmon.models.loader import load_model, resolve_model_spec  # noqa: E402
from physmon.utils.io import ensure_parent_dir, write_json  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402

from run_behavioural import format_prompt_with_chat_template, load_rendered_families  # noqa: E402


DEFAULT_STAGE = 5
DEFAULT_SEED = 42
DEFAULT_JSONL_NAME = "extract_activations_events.jsonl"
DEFAULT_TIER = 1
SUPPORTED_TIERS = (1, 2)
RESID_SITE = "resid_post"


def parse_args() -> argparse.Namespace:
    """Parse Stage 5 extraction CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-role", required=True, help="Registry key or model role to extract.")
    parser.add_argument("--family-dir", required=True, help="Rendered family JSON directory.")
    parser.add_argument("--output-dir", required=True, help="Scratch activation root directory.")
    parser.add_argument("--tier", type=int, default=DEFAULT_TIER, choices=SUPPORTED_TIERS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE, help="Scientific stage number for logging.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_registry_selection(model_role: str) -> tuple[str, str]:
    """Resolve the requested extraction target to one registry key and one role."""

    try:
        spec = resolve_model_spec(model_key=model_role)
        return spec.key, spec.role
    except KeyError:
        spec = resolve_model_spec(role=model_role)
        return spec.key, spec.role


def estimated_storage_bytes(
    *,
    family_count: int,
    variants_per_family: int,
    n_layers: int,
    d_model: int,
    tier: int,
    bytes_per_value: int = 2,
) -> int:
    """Estimate extraction storage for one model under the requested tier."""

    site_count = 1 if tier == 1 else 2
    return family_count * variants_per_family * site_count * n_layers * d_model * bytes_per_value


def bytes_to_megabytes(value: int) -> float:
    """Convert bytes to megabytes for operator-friendly dry-run output."""

    return value / (1024 ** 2)


def infer_model_dims_from_config(model_path: str) -> tuple[list[int], int]:
    """Infer layer count and hidden size from a local model config."""

    config = AutoConfig.from_pretrained(
        model_path,
        local_files_only=True,
        trust_remote_code=True,
    )
    num_layers = int(
        getattr(config, "num_hidden_layers", None)
        or getattr(config, "n_layer", None)
    )
    hidden_size = int(
        getattr(config, "hidden_size", None)
        or getattr(config, "d_model", None)
    )
    if num_layers <= 0 or hidden_size <= 0:
        raise ValueError(f"Could not infer num_layers/hidden_size from config at {model_path}.")
    return list(range(num_layers)), hidden_size


def build_site_tensor(
    extracted: dict[str, torch.Tensor],
    *,
    prefix: str,
    layer_indices: list[int],
) -> torch.Tensor:
    """Stack per-layer extracted vectors back into one `(n_layers, d_model)` tensor."""

    return torch.stack([extracted[f"{prefix}_layer{layer_index}"] for layer_index in layer_indices], dim=0)


def save_activation_tensor(path: Path, tensor: torch.Tensor) -> str:
    """Persist one float16 activation tensor and return its absolute path."""

    output_path = ensure_parent_dir(path)
    torch.save(tensor.cpu(), output_path)
    return str(output_path.resolve())


def extract_hidden_states_fallback(
    *,
    hf_model: Any,
    tokenizer: Any,
    formatted_prompt: str,
    cue_token_index: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Fallback extraction for models loaded without TransformerLens support.

    Returns:
        Tuple of `(last_prompt_tensor, cue_tensor)` each shaped `(n_layers, d_model)`.
    """

    first_parameter = next(hf_model.parameters())
    encoded = tokenizer(
        formatted_prompt,
        return_tensors="pt",
        add_special_tokens=False,
    )
    encoded = {key: value.to(first_parameter.device) for key, value in encoded.items()}
    with torch.no_grad():
        outputs = hf_model(
            **encoded,
            output_hidden_states=True,
            use_cache=False,
        )
    hidden_states = outputs.hidden_states
    if hidden_states is None:
        raise RuntimeError("HF fallback extraction expected output_hidden_states=True to return hidden states.")
    layer_states = hidden_states[1:]
    last_prompt_index = int(encoded["input_ids"].shape[1] - 1)
    last_prompt_tensor = torch.stack(
        [state[0, last_prompt_index, :].detach().cpu().to(dtype=torch.float16) for state in layer_states],
        dim=0,
    )
    cue_tensor = torch.stack(
        [state[0, cue_token_index, :].detach().cpu().to(dtype=torch.float16) for state in layer_states],
        dim=0,
    )
    return last_prompt_tensor, cue_tensor


def main() -> None:
    """Run Stage 5 activation extraction or dry-run planning."""

    args = parse_args()
    set_global_seed(args.seed)
    resolved_model_key, resolved_role = resolve_registry_selection(args.model_role)
    model_spec = resolve_model_spec(model_key=resolved_model_key)
    family_payloads = load_rendered_families(args.family_dir)

    output_root = Path(args.output_dir) / resolved_model_key
    logger = ExperimentLogger(
        script_name="extract_activations.py",
        stage=args.stage,
        jsonl_path=output_root / DEFAULT_JSONL_NAME,
        repo_root=Path(__file__).resolve().parents[1],
        model_name=model_spec.name,
        model_role=resolved_role,
    )

    bundle = None
    if args.dry_run:
        if model_spec.num_layers is None or model_spec.hidden_dim is None:
            layer_indices, d_model = infer_model_dims_from_config(model_spec.path)
        else:
            layer_indices = list(range(model_spec.num_layers))
            d_model = int(model_spec.hidden_dim)
    else:
        device_map = "auto" if model_spec.hook_backend != "transformer_lens" else None
        bundle = load_model(model_key=resolved_model_key, device="cuda", device_map=device_map)
        if bundle.hooked_model is not None:
            layer_indices = list(range(bundle.hooked_model.cfg.n_layers))
            d_model = int(bundle.hooked_model.cfg.d_model)
        else:
            layer_indices, d_model = infer_model_dims_from_config(model_spec.path)
    variants_per_family = max(len(payload["variants"]) for payload in family_payloads)
    estimate_mb = bytes_to_megabytes(
        estimated_storage_bytes(
            family_count=len(family_payloads),
            variants_per_family=variants_per_family,
            n_layers=len(layer_indices),
            d_model=d_model,
            tier=args.tier,
        )
    )

    logger.log_event(
        "ACTIVATION_EXTRACTION_START",
        model_key=resolved_model_key,
        tier=args.tier,
        dry_run=args.dry_run,
        family_count=len(family_payloads),
        n_layers=len(layer_indices),
        d_model=d_model,
        estimated_storage_mb=estimate_mb,
    )

    site_names = ["resid_post_last_prompt"] if args.tier == 1 else [
        "resid_post_last_prompt",
        "resid_post_cue_token",
    ]

    manifest_entries: list[dict[str, Any]] = []
    for family_payload in family_payloads:
        for variant_payload in sorted(family_payload["variants"], key=lambda item: int(item["variant_id"])):
            family_dir = output_root / family_payload["template_id"]
            file_plan = {
                site_name: family_dir / f"v{variant_payload['variant_id']}_{site_name}.pt"
                for site_name in site_names
            }

            if args.dry_run:
                for site_name, planned_path in file_plan.items():
                    manifest_entries.append(
                        {
                            "template_id": family_payload["template_id"],
                            "variant_id": int(variant_payload["variant_id"]),
                            "site": site_name,
                            "tensor_path": str(planned_path.resolve()),
                            "shape": [len(layer_indices), d_model],
                            "dry_run": True,
                        }
                    )
                continue

            assert bundle is not None
            formatted_prompt = format_prompt_with_chat_template(variant_payload["prompt"], bundle.tokenizer)
            prompt_token_ids = bundle.tokenizer(
                formatted_prompt,
                add_special_tokens=False,
            ).input_ids
            cue_token_index = find_cue_token_index(
                formatted_prompt,
                str(variant_payload["cue_sentence"]),
                bundle.tokenizer,
            )

            if bundle.hooked_model is not None:
                extracted = extract_targeted_activations(
                    model=bundle.hooked_model,
                    prompt=formatted_prompt,
                    prompt_token_ids=prompt_token_ids,
                    cue_span_token_ids=[cue_token_index],
                    layers=layer_indices,
                    sites=[RESID_SITE],
                    dtype="float16",
                )
                last_prompt_tensor = build_site_tensor(
                    extracted,
                    prefix="resid_post_last_prompt",
                    layer_indices=layer_indices,
                )
                cue_tensor = None
                if args.tier == 2:
                    cue_tensor = build_site_tensor(
                        extracted,
                        prefix="resid_post_cue_token0",
                        layer_indices=layer_indices,
                    )
            else:
                last_prompt_tensor, cue_tensor = extract_hidden_states_fallback(
                    hf_model=bundle.hf_model,
                    tokenizer=bundle.tokenizer,
                    formatted_prompt=formatted_prompt,
                    cue_token_index=cue_token_index,
                )
            saved_last_prompt = save_activation_tensor(
                file_plan["resid_post_last_prompt"],
                last_prompt_tensor,
            )
            manifest_entries.append(
                {
                    "template_id": family_payload["template_id"],
                    "variant_id": int(variant_payload["variant_id"]),
                    "site": "resid_post_last_prompt",
                    "tensor_path": saved_last_prompt,
                    "shape": list(last_prompt_tensor.shape),
                    "cue_token_index": cue_token_index,
                    "last_prompt_token_index": len(prompt_token_ids) - 1,
                    "seed": args.seed,
                    "git_commit": logger.git_commit,
                }
            )

            if args.tier == 2:
                assert cue_tensor is not None
                saved_cue = save_activation_tensor(
                    file_plan["resid_post_cue_token"],
                    cue_tensor,
                )
                manifest_entries.append(
                    {
                        "template_id": family_payload["template_id"],
                        "variant_id": int(variant_payload["variant_id"]),
                        "site": "resid_post_cue_token",
                        "tensor_path": saved_cue,
                        "shape": list(cue_tensor.shape),
                        "cue_token_index": cue_token_index,
                        "last_prompt_token_index": len(prompt_token_ids) - 1,
                        "seed": args.seed,
                        "git_commit": logger.git_commit,
                    }
                )

            logger.log_event(
                "ACTIVATION_EXTRACTED",
                template_id=family_payload["template_id"],
                variant_id=int(variant_payload["variant_id"]),
                tier=args.tier,
                cue_token_index=cue_token_index,
                last_prompt_token_index=len(prompt_token_ids) - 1,
            )

    manifest_payload = {
        "model_key": resolved_model_key,
        "model_role": resolved_role,
        "model_name": model_spec.name,
        "tier": args.tier,
        "dry_run": args.dry_run,
        "family_count": len(family_payloads),
        "files": manifest_entries,
        "estimated_storage_mb": estimate_mb,
    }
    write_json(output_root / "manifest.json", manifest_payload)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "model_key": resolved_model_key,
                    "tier": args.tier,
                    "family_count": len(family_payloads),
                    "planned_files": len(manifest_entries),
                    "estimated_storage_mb": round(estimate_mb, 3),
                },
                indent=2,
            )
        )

    logger.log_event(
        "ACTIVATION_EXTRACTION_COMPLETE",
        model_key=resolved_model_key,
        tier=args.tier,
        dry_run=args.dry_run,
        extracted_files=len(manifest_entries),
        manifest_path=str((output_root / "manifest.json").resolve()),
    )


if __name__ == "__main__":
    main()
