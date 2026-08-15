#!/usr/bin/env python3
"""Approximate Stage 8 attention-head contribution analysis at one probe layer.

This script reconstructs the layer-18 variance probe direction from extracted
Stage 6 activations, then decomposes that direction into per-head output
subspaces using the attention output projection matrix.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from safetensors import safe_open
from sklearn.linear_model import LogisticRegression
import torch
from transformers import AutoConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.models.loader import resolve_model_spec  # noqa: E402
from physmon.utils.logging import ExperimentLogger  # noqa: E402
from run_probing import (  # noqa: E402
    build_family_feature_tensors,
    infer_positive_families,
    load_per_family_rows,
    load_site_tensors,
)


DEFAULT_STAGE = 8
DEFAULT_SITE = "resid_post_last_prompt"
DEFAULT_JSONL_NAME = "run_attention_analysis_events.jsonl"
DEFAULT_FAMILY_CSV = "results/stage6/analysis_d2/stage6_d1_per_family.csv"


def slp_column_for_model(model_key: str) -> str:
    """Resolve the per-family S_lp column for one model."""

    if "deepseek" in model_key:
        return "deepseek_S_lp"
    if "llama" in model_key:
        return "llama_S_lp"
    return "qwen_S_lp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation-dir", required=True)
    parser.add_argument("--layer", type=int, required=True)
    parser.add_argument("--families", nargs="+", required=True)
    parser.add_argument("--model-key", default="qwen_primary")
    parser.add_argument("--family-csv", default=DEFAULT_FAMILY_CSV)
    parser.add_argument(
        "--positive-families-file",
        default="results/stage6/analysis_d2/stage6_positive_families.json",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage", type=int, default=DEFAULT_STAGE)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_o_proj_weight(model_path: Path, layer_index: int) -> np.ndarray:
    """Load one Qwen attention output projection matrix from safetensors."""

    index_path = model_path / "model.safetensors.index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Missing safetensors index at {index_path}.")
    weight_map = json.loads(index_path.read_text(encoding="utf-8"))["weight_map"]
    tensor_name = f"model.layers.{layer_index}.self_attn.o_proj.weight"
    shard_name = weight_map[tensor_name]
    # Some checkpoint shards store bf16 weights; load through Torch first so the
    # cast to float32 is explicit and NumPy never has to interpret bf16 directly.
    with safe_open(model_path / shard_name, framework="pt", device="cpu") as handle:
        tensor = handle.get_tensor(tensor_name)
    return tensor.to(dtype=torch.float32).cpu().numpy()


def project_into_head_subspace(vector: np.ndarray, submatrix: np.ndarray) -> np.ndarray:
    """Project a residual-space vector into one head output subspace."""

    basis = submatrix
    gram = basis.T @ basis
    gram_pinv = np.linalg.pinv(gram)
    coefficients = gram_pinv @ basis.T @ vector
    return basis @ coefficients


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ExperimentLogger(
        script_name="run_attention_analysis.py",
        stage=args.stage,
        jsonl_path=output_dir / DEFAULT_JSONL_NAME,
        repo_root=REPO_ROOT,
        model_role=args.model_key,
    )

    family_rows = load_per_family_rows(Path(args.family_csv))
    slp_column = slp_column_for_model(args.model_key)
    positive_families, _ = infer_positive_families(
        family_csv=Path(args.family_csv),
        positive_families_file=Path(args.positive_families_file),
    )
    entries, tensors = load_site_tensors(Path(args.activation_dir), DEFAULT_SITE)
    family_ids, feature_tensors = build_family_feature_tensors(tensors, entries, reducer="variance")
    family_index = {family_id: idx for idx, family_id in enumerate(family_ids)}
    selected_indices = [family_index[family_id] for family_id in args.families]
    selected_vectors = feature_tensors[selected_indices, args.layer, :]

    labels = np.asarray([int(family_id in positive_families) for family_id in family_ids], dtype=int)
    layer_features = feature_tensors[:, args.layer, :]
    model = LogisticRegression(
        C=10.0,
        class_weight="balanced",
        max_iter=2000,
        solver="liblinear",
        random_state=args.seed,
    )
    model.fit(layer_features, labels)
    probe_weight = model.coef_[0].astype(np.float32)
    np.save(output_dir / f"probe_weights_layer{args.layer}.npy", probe_weight)

    spec = resolve_model_spec(model_key=args.model_key)
    config = AutoConfig.from_pretrained(spec.path, local_files_only=True, trust_remote_code=True)
    num_heads = int(config.num_attention_heads)
    hidden_size = int(config.hidden_size)
    d_head = hidden_size // num_heads
    o_proj = load_o_proj_weight(Path(spec.path), args.layer)

    head_rows: list[dict[str, Any]] = []
    family_rows_out: list[dict[str, Any]] = []
    aggregated_scores: list[float] = []
    for head_index in range(num_heads):
        start = head_index * d_head
        stop = start + d_head
        head_matrix = o_proj[:, start:stop]
        alignment = float(np.linalg.norm(probe_weight @ head_matrix) ** 2)
        family_scores: list[float] = []
        for family_id, variance_vector in zip(args.families, selected_vectors, strict=True):
            projected = project_into_head_subspace(variance_vector, head_matrix)
            contribution = float(abs(probe_weight @ projected))
            family_scores.append(contribution)
            family_rows_out.append(
                {
                    "family_id": family_id,
                    "head_index": head_index,
                    "contribution": contribution,
                    "alignment_strength": alignment,
                    "family_slp": float(family_rows[family_id].get(slp_column, "0") or "0"),
                }
            )
        mean_contribution = float(np.mean(family_scores))
        aggregated_scores.append(mean_contribution)
        head_rows.append(
            {
                "head_index": head_index,
                "alignment_strength": alignment,
                "mean_contribution": mean_contribution,
                "max_contribution": float(np.max(family_scores)),
            }
        )

    head_rows.sort(key=lambda row: row["mean_contribution"], reverse=True)
    save_json(output_dir / "head_sensitivity_scores.json", head_rows)
    save_json(output_dir / "family_head_contributions.json", family_rows_out)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        matrix = np.zeros((len(args.families), num_heads), dtype=np.float32)
        family_position = {family_id: idx for idx, family_id in enumerate(args.families)}
        for row in family_rows_out:
            matrix[family_position[row["family_id"]], int(row["head_index"])] = float(row["contribution"])
        figure, axis = plt.subplots(figsize=(12, max(4.0, len(args.families) * 0.35)))
        image = axis.imshow(matrix, aspect="auto", cmap="magma")
        axis.set_xticks(range(num_heads))
        axis.set_xticklabels([str(i) for i in range(num_heads)], rotation=90)
        axis.set_yticks(range(len(args.families)))
        axis.set_yticklabels(args.families)
        axis.set_xlabel("Attention head")
        axis.set_ylabel("Family")
        axis.set_title(f"Stage 8 attention contributions at layer {args.layer}")
        figure.colorbar(image, ax=axis, label="Approximate contribution")
        figure.tight_layout()
        figure.savefig(output_dir / "head_sensitivity_heatmap.png", dpi=200)
        plt.close(figure)
    except Exception as exc:  # pragma: no cover
        logger.log_event("ATTENTION_HEATMAP_SKIPPED", reason=str(exc))

    logger.log_event(
        "ATTENTION_ANALYSIS_COMPLETE",
        layer=args.layer,
        family_count=len(args.families),
        top_head=int(head_rows[0]["head_index"]) if head_rows else None,
    )


if __name__ == "__main__":
    main()
