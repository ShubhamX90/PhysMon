"""Model registry and loading helpers for PhysMon Stage 2 instrumentation.

Reference: Part IV.4 of the implementation brief and the model-selection plan in
`physmon_proposal.pdf` §6 and §11.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from physmon.utils.io import read_yaml

if TYPE_CHECKING:
    from transformer_lens import HookedTransformer


DEFAULT_MODEL_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "docs" / "model_registry.yml"
VALID_HOOK_BACKENDS = frozenset({"transformer_lens", "baukit"})


@dataclass(frozen=True)
class ModelSpec:
    """One model entry from `docs/model_registry.yml`.

    Args:
        key: Registry key.
        name: Canonical model name.
        path: Absolute local path on Sharanga scratch.
        role: PhysMon role classification.
        family: Model family label.
        hook_backend: Preferred hooking backend.
        hook_validated: Whether Stage 2 hook validation passed.
        logprob_validated: Whether Stage 2 log-prob validation passed.
        hidden_dim: Optional hidden size once confirmed.
        num_layers: Optional number of layers once confirmed.
        notes: Free-form notes.

    Returns:
        Immutable model specification.
    """

    key: str
    name: str
    path: str
    role: str
    family: str
    hook_backend: str
    hook_validated: bool
    logprob_validated: bool
    hidden_dim: int | None
    num_layers: int | None
    notes: str


@dataclass
class LoadedModelBundle:
    """Loaded model objects used by Stage 2 validation scripts.

    Args:
        spec: Registry specification.
        backend: Active hook backend.
        tokenizer: Hugging Face tokenizer.
        hf_model: Hugging Face causal LM.
        hooked_model: Optional TransformerLens model when available.

    Returns:
        Mutable bundle of loaded model objects.
    """

    spec: ModelSpec
    backend: str
    tokenizer: Any
    hf_model: Any
    hooked_model: HookedTransformer | None


def load_model_registry(path: str | Path = DEFAULT_MODEL_REGISTRY_PATH) -> dict[str, ModelSpec]:
    """Load the committed PhysMon model registry.

    Args:
        path: Registry YAML path.

    Returns:
        Mapping from registry keys to `ModelSpec` entries.
    """

    payload = read_yaml(path)
    models_section = payload.get("models", {})
    if not isinstance(models_section, dict):
        raise TypeError("`models` in model_registry.yml must be a mapping.")

    registry: dict[str, ModelSpec] = {}
    for key, value in models_section.items():
        if not isinstance(value, dict):
            raise TypeError(f"Registry entry '{key}' must be a mapping.")
        hook_backend = value.get("hook_backend", "transformer_lens")
        if hook_backend not in VALID_HOOK_BACKENDS:
            raise ValueError(
                f"Registry entry '{key}' declares invalid hook backend '{hook_backend}'."
            )
        registry[key] = ModelSpec(
            key=key,
            name=str(value["name"]),
            path=str(value["path"]),
            role=str(value["role"]),
            family=str(value["family"]),
            hook_backend=str(hook_backend),
            hook_validated=bool(value.get("hook_validated", False)),
            logprob_validated=bool(value.get("logprob_validated", False)),
            hidden_dim=int(value["hidden_dim"]) if value.get("hidden_dim") is not None else None,
            num_layers=int(value["num_layers"]) if value.get("num_layers") is not None else None,
            notes=str(value.get("notes", "")),
        )
    return registry


def resolve_model_spec(
    model_key: str | None = None,
    role: str | None = None,
    family: str | None = None,
    registry_path: str | Path = DEFAULT_MODEL_REGISTRY_PATH,
) -> ModelSpec:
    """Resolve one model spec by key or by role/family filter.

    Args:
        model_key: Optional explicit registry key.
        role: Optional role filter.
        family: Optional family filter.
        registry_path: Registry YAML path.

    Returns:
        Matching `ModelSpec`.
    """

    registry = load_model_registry(registry_path)
    if model_key is not None:
        try:
            return registry[model_key]
        except KeyError as error:
            raise KeyError(f"Unknown registry key '{model_key}'.") from error

    matches = [
        spec
        for spec in registry.values()
        if (role is None or spec.role == role) and (family is None or spec.family == family)
    ]
    if not matches:
        raise LookupError(f"No registry entry matches role={role!r}, family={family!r}.")
    if len(matches) > 1:
        raise LookupError(
            f"Registry lookup for role={role!r}, family={family!r} is ambiguous: "
            f"{[spec.key for spec in matches]}."
        )
    return matches[0]


def load_model(
    model_key: str | None = None,
    role: str | None = None,
    family: str | None = None,
    registry_path: str | Path = DEFAULT_MODEL_REGISTRY_PATH,
    device: str = "cpu",
    torch_dtype: torch.dtype | None = None,
    device_map: str | dict[str, Any] | None = None,
    first_n_layers: int | None = None,
) -> LoadedModelBundle:
    """Load a registry-backed model bundle for Stage 2 validation.

    Args:
        model_key: Optional explicit registry key.
        role: Optional role filter.
        family: Optional family filter.
        registry_path: Registry YAML path.
        device: Torch device string.
        torch_dtype: Optional torch dtype override.
        device_map: Optional Hugging Face device map such as `"auto"`.
        first_n_layers: Optional TransformerLens layer cap for smoke tests.

    Returns:
        `LoadedModelBundle` containing Hugging Face and optional TransformerLens objects.
    """

    spec = resolve_model_spec(model_key=model_key, role=role, family=family, registry_path=registry_path)
    return load_model_from_spec(
        spec=spec,
        device=device,
        torch_dtype=torch_dtype,
        device_map=device_map,
        first_n_layers=first_n_layers,
    )


def load_model_from_spec(
    spec: ModelSpec,
    device: str = "cpu",
    torch_dtype: torch.dtype | None = None,
    device_map: str | dict[str, Any] | None = None,
    first_n_layers: int | None = None,
) -> LoadedModelBundle:
    """Load model objects from one resolved registry spec.

    Args:
        spec: Resolved model specification.
        device: Torch device string.
        torch_dtype: Optional torch dtype override.
        device_map: Optional Hugging Face device map such as `"auto"`.
        first_n_layers: Optional TransformerLens layer cap for smoke tests.

    Returns:
        `LoadedModelBundle`.
    """

    resolved_dtype = torch_dtype or (torch.float16 if device.startswith("cuda") else torch.float32)
    tokenizer = AutoTokenizer.from_pretrained(spec.path, trust_remote_code=True)
    hf_model = AutoModelForCausalLM.from_pretrained(
        spec.path,
        torch_dtype=resolved_dtype,
        trust_remote_code=True,
        local_files_only=True,
        device_map=device_map,
    )
    hf_model.eval()

    if spec.hook_backend == "transformer_lens":
        from transformer_lens import HookedTransformer

        if device_map is not None:
            raise ValueError(
                "TransformerLens-backed loads do not support a Hugging Face device_map. "
                "Use a single explicit device for prompt-side hook extraction."
            )
        hooked_model = HookedTransformer.from_pretrained_no_processing(
            spec.name,
            hf_model=hf_model,
            tokenizer=tokenizer,
            device=device,
            move_to_device=True,
            dtype=resolved_dtype,
            first_n_layers=first_n_layers,
            trust_remote_code=True,
        )
        hooked_model.eval()
        return LoadedModelBundle(
            spec=spec,
            backend="transformer_lens",
            tokenizer=tokenizer,
            hf_model=hf_model,
            hooked_model=hooked_model,
        )

    if device_map is None:
        hf_model.to(device)
    return LoadedModelBundle(
        spec=spec,
        backend="baukit",
        tokenizer=tokenizer,
        hf_model=hf_model,
        hooked_model=None,
    )
