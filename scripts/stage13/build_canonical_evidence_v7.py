#!/usr/bin/env python3
"""Build the canonical model-family evidence table (v7).

The v6 table has 465 rows across three models but populates exactly one field,
``S_lp``, and carries 185 nulls whose reasons are generic.  It passed the v6
``canonical_evidence_multimodel`` check on shape alone, which is why the v7 gate
re-evaluates that check against content.

v7 ingests every family-level evidence type for which an authoritative artifact
actually exists, and records for each value:

*   the artifact it came from;
*   the registry experiment id, resolved by exact path match, then by directory
    match at lower confidence, and otherwise left explicitly unresolved.

No value is written without a source, and no missing value is given a
convenient reason.  Aggregate-only metrics such as the TF-IDF text baselines
have no family-level value at all and are recorded as ``not_applicable`` rather
than being spread across families.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_utils import REPO_ROOT, read_jsonl, write_csv, write_json  # noqa: E402


MODELS = ("qwen_primary", "llama_primary", "deepseek_reasoning")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else []


def numeric(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def from_csv(column: str, key: str = "template_id") -> Callable:
    def loader(path: Path) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for row in read_csv_rows(path):
            family = row.get(key)
            if family and row.get(column) not in (None, ""):
                value = numeric(row[column])
                out[family] = value if value is not None else row[column]
        return out

    return loader


def from_json(field: str, key: str = "template_id") -> Callable:
    def loader(path: Path) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for row in read_json_rows(path):
            family = row.get(key)
            if family is not None and row.get(field) is not None:
                out[str(family)] = row[field]
        return out

    return loader


def mean_by_family(field: str, key: str = "family_id", where: dict | None = None) -> Callable:
    """Average a per-row measure to one family-level value."""

    def loader(path: Path) -> dict[str, Any]:
        grouped: dict[str, list[float]] = defaultdict(list)
        rows = read_csv_rows(path) if path.suffix == ".csv" else read_json_rows(path)
        for row in rows:
            if where and any(str(row.get(k, "")) != str(v) for k, v in where.items()):
                continue
            family = row.get(key)
            value = numeric(row.get(field))
            if family and value is not None:
                grouped[str(family)].append(value)
        return {family: sum(v) / len(v) for family, v in grouped.items() if v}

    return loader


# (model, field, artifact path, loader)
SOURCES: list[tuple[str, str, str, Callable]] = [
    # Behavioural sensitivity and parser eligibility.
    ("qwen_primary", "S_lp", "results/stage6/analysis_d2/stage6_d1_per_family.csv", from_csv("qwen_S_lp")),
    ("qwen_primary", "hat_S", "results/stage6/analysis_d2/stage6_d1_per_family.csv", from_csv("qwen_hat_S")),
    ("qwen_primary", "parse_ok", "results/stage6/analysis_d2/stage6_d1_per_family.csv", from_csv("qwen_parse_ok")),
    ("qwen_primary", "S_lp", "results/stage11/behavioural_expansion/per_family_summary.csv", from_csv("qwen_S_lp")),
    ("qwen_primary", "hat_S", "results/stage11/behavioural_expansion/per_family_summary.csv", from_csv("qwen_hat_S")),
    ("qwen_primary", "parse_rate", "results/stage11/behavioural_expansion/per_family_summary.csv", from_csv("qwen_parse_rate_family")),
    ("qwen_primary", "correct_rate", "results/stage11/behavioural_expansion/per_family_summary.csv", from_csv("qwen_correct_rate_family")),
    ("llama_primary", "S_lp", "results/stage6/analysis_d2/stage6_d1_per_family.csv", from_csv("llama_S_lp")),
    ("llama_primary", "hat_S", "results/stage6/analysis_d2/stage6_d1_per_family.csv", from_csv("llama_hat_S")),
    ("llama_primary", "parse_ok", "results/stage6/analysis_d2/stage6_d1_per_family.csv", from_csv("llama_parse_ok")),
    ("deepseek_reasoning", "S_lp", "results/stage8/analysis_deepseek/deepseek_per_family.csv", from_csv("deepseek_S_lp")),
    ("deepseek_reasoning", "hat_S", "results/stage8/analysis_deepseek/deepseek_per_family.csv", from_csv("deepseek_hat_S")),
    ("deepseek_reasoning", "parse_rate", "results/stage8/analysis_deepseek/deepseek_per_family.csv", from_csv("deepseek_parse_rate_family")),
    ("deepseek_reasoning", "correct_rate", "results/stage8/analysis_deepseek/deepseek_per_family.csv", from_csv("deepseek_correct_rate_family")),
    # Prompt-side hidden-state monitor.
    ("qwen_primary", "monitor_score", "results/stage10/mean_probe_full_sweep_bigcompute/loo_predictions_resid_post_last_prompt.json", from_json("prediction")),
    ("qwen_primary", "monitor_layer", "results/stage10/mean_probe_full_sweep_bigcompute/loo_predictions_resid_post_last_prompt.json", from_json("layer_index")),
    ("qwen_primary", "monitor_score", "results/stage12/expansion_probe_inference/family_mean_predictions.json", from_json("mean_prediction")),
    ("deepseek_reasoning", "monitor_score", "results/stage8/probing_deepseek/loo_predictions_variance.json", from_json("prediction")),
    ("deepseek_reasoning", "monitor_layer", "results/stage8/probing_deepseek/loo_predictions_variance.json", from_json("layer_index")),
    # Non-activation comparators.
    ("qwen_primary", "entropy_score", "results/stage9/baselines/entropy/entropy_per_family_scores.json", from_json("entropy_proxy_score")),
    ("qwen_primary", "blackbox_score", "results/stage9/baselines/blackbox_counterfactual/family_scores.json", from_json("prediction_directional")),
    ("qwen_primary", "correctness_probe_score", "results/stage9/baselines/correctness_probe/loo_predictions_variance.json", from_json("prediction")),
    ("qwen_primary", "residualised_monitor_score", "results/stage9/correctness_residualisation/loo_predictions.json", from_json("prediction")),
    # Causal intervention effects (family-mean recovery over the tested panel).
    ("qwen_primary", "intervention_recovery", "results/stage8/multi_head_knockout/patching_results.csv", mean_by_family("recovery_fraction")),
    ("llama_primary", "intervention_recovery", "results/stage10/llama_mhk/patching_results.csv", mean_by_family("recovery_fraction")),
    ("deepseek_reasoning", "intervention_recovery", "results/stage10/deepseek_mhk/patching_results.csv", mean_by_family("recovery_fraction")),
]

# Metrics that exist only as a model-level aggregate, with no family-level value.
AGGREGATE_ONLY_FIELDS = {
    "cot_text_baseline": "results/stage9/baselines/cot_text/surface_tfidf_continuous.json",
    "answer_rationale_baseline": "results/stage9/baselines/answer_rationale/surface_tfidf_continuous.json",
}


def build_path_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for row in read_jsonl("docs/registry/experiment_registry.jsonl"):
        experiment_id = str(row.get("experiment_id", ""))
        for path in (row.get("raw_output_paths") or []) + (row.get("summary_paths") or []):
            index[str(path)].append(experiment_id)
    return index


def resolve_experiment(path: str, index: dict[str, list[str]]) -> tuple[str, str]:
    """Resolve an artifact to a registry experiment id, honestly reporting how."""

    if path in index:
        return ",".join(sorted(set(index[path]))), "exact_path_match"
    directory = path.rsplit("/", 1)[0]
    hits = {e for p, ids in index.items() if p.startswith(directory + "/") for e in ids}
    if hits:
        return ",".join(sorted(hits)), "directory_match"
    return "", "registry_experiment_unresolved"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifests/physmon_canonical_155.jsonl")
    parser.add_argument("--table-out", default="results/canonical/model_family_evidence_v7.csv")
    parser.add_argument(
        "--verification-out", default="results/stage13/wave0/canonical_evidence_verification_v7.json"
    )
    args = parser.parse_args()

    manifest = read_jsonl(args.manifest)
    families = [str(row.get("canonical_family_id") or row.get("template_id")) for row in manifest]
    family_meta = {
        str(row.get("canonical_family_id") or row.get("template_id")): row for row in manifest
    }

    path_index = build_path_index()

    # values[(model, family)][field] = (value, artifact, experiment_ids, resolution)
    values: dict[tuple[str, str], dict[str, tuple]] = defaultdict(dict)
    missing_sources: list[str] = []
    empty_sources: list[str] = []
    source_report: list[dict[str, Any]] = []

    for model, field, rel_path, loader in SOURCES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            missing_sources.append(rel_path)
            continue
        try:
            loaded = loader(path)
        except Exception as exc:  # a malformed artifact must not be silently skipped
            missing_sources.append(f"{rel_path} (load error: {exc})")
            continue
        experiment_ids, resolution = resolve_experiment(rel_path, path_index)
        applied = 0
        for family, value in loaded.items():
            if family not in family_meta:
                continue
            # First writer wins; SOURCES is ordered so base panels precede expansions.
            if field not in values[(model, family)]:
                values[(model, family)][field] = (value, rel_path, experiment_ids, resolution)
                applied += 1
        source_report.append(
            {
                "model": model,
                "field": field,
                "artifact": rel_path,
                "experiment_ids": experiment_ids,
                "registry_resolution": resolution,
                "families_populated": applied,
                "loaded_keys": len(loaded),
            }
        )
        if not loaded:
            # An existing artifact that yields nothing means the field name is
            # wrong. That must surface, not vanish into a null reason.
            empty_sources.append(f"{rel_path} [{model}/{field}] loaded 0 values")

    all_fields = sorted({field for _, field, _, _ in SOURCES})
    rows: list[dict[str, Any]] = []
    null_reasons: Counter = Counter()
    populated_fields: Counter = Counter()
    source_linked = 0

    for model in MODELS:
        model_has_field = {
            field for m, field, _, _ in SOURCES if m == model
        }
        for family in families:
            meta = family_meta[family]
            row: dict[str, Any] = {
                "model_id": model,
                "canonical_family_id": family,
                "domain": meta.get("domain", ""),
                "cue_type": meta.get("cue_type", ""),
                "original_or_expansion": meta.get("original_or_expansion", ""),
            }
            for field in all_fields:
                entry = values[(model, family)].get(field)
                if entry is None:
                    row[field] = ""
                    row[f"{field}__source"] = ""
                    row[f"{field}__experiment_ids"] = ""
                    reason = (
                        "not_measured"
                        if field in model_has_field
                        else "not_applicable"
                    )
                    row[f"{field}__null_reason"] = reason
                    null_reasons[f"{field}:{reason}"] += 1
                else:
                    value, artifact, experiment_ids, resolution = entry
                    row[field] = value
                    row[f"{field}__source"] = artifact
                    row[f"{field}__experiment_ids"] = experiment_ids or resolution
                    row[f"{field}__null_reason"] = ""
                    populated_fields[field] += 1
                    if experiment_ids:
                        source_linked += 1
            for field, artifact in AGGREGATE_ONLY_FIELDS.items():
                row[f"{field}__null_reason"] = "not_applicable"
                row[f"{field}__source"] = artifact
                null_reasons[f"{field}:not_applicable"] += 1
            rows.append(row)

    fieldnames = ["model_id", "canonical_family_id", "domain", "cue_type", "original_or_expansion"]
    for field in all_fields:
        fieldnames += [field, f"{field}__source", f"{field}__experiment_ids", f"{field}__null_reason"]
    for field in AGGREGATE_ONLY_FIELDS:
        fieldnames += [f"{field}__source", f"{field}__null_reason"]

    write_csv(args.table_out, rows, fieldnames)

    verification = {
        "status": (
            "PASS"
            if len(populated_fields) > 1 and source_linked > 0 and not empty_sources
            else "FAIL"
        ),
        "supersedes": "results/stage13/wave0/canonical_evidence_verification_v6.json",
        "supersession_reason": (
            "v6 populated only S_lp across 465 rows and used generic null reasons; it "
            "passed the multimodel check on shape rather than content."
        ),
        "canonical_families": len(families),
        "models": list(MODELS),
        "model_family_rows": len(rows),
        "populated_fields": dict(populated_fields),
        "n_populated_field_types": len(populated_fields),
        "source_linked_values": source_linked,
        "total_populated_values": sum(populated_fields.values()),
        "rows_by_model": {model: len(families) for model in MODELS},
        "null_reason_counts": dict(null_reasons),
        "missing_sources": missing_sources,
        "empty_sources": empty_sources,
        "source_report": source_report,
        "table": args.table_out,
        "interpretation": (
            "Every populated value cites the artifact it came from. Registry experiment "
            "ids are resolved by exact path match, then directory match, and are "
            "otherwise reported as registry_experiment_unresolved rather than invented."
        ),
    }
    write_json(args.verification_out, verification)

    print(json.dumps({k: v for k, v in verification.items() if k != "source_report"}, indent=2)[:2600])


if __name__ == "__main__":
    main()
