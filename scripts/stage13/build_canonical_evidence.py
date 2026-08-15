#!/usr/bin/env python3
"""Build conservative canonical family/variant evidence tables.

The canonical tables are normalization aids, not claim tables. Missing values
remain blank/unknown rather than being inferred.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from governance_utils import REPO_ROOT, read_csv, read_jsonl, write_csv, write_json


FAMILY_FIELDS = [
    "canonical_family_id",
    "source_family_id",
    "domain",
    "cue_type",
    "governing_law",
    "verifier_certified",
    "pi_validated",
    "correct_answer",
    "qwen_S_lp",
    "llama_S_lp",
    "qwen_parse_ok",
    "llama_parse_ok",
    "stage6_positive_qwen",
    "source_paths",
    "paper_eligible_status",
]
VARIANT_FIELDS = [
    "canonical_family_id",
    "variant_id",
    "model_role",
    "domain",
    "cue_type",
    "cue_value",
    "correct_answer",
    "logprob_correct_answer",
    "parsed_answer",
    "parse_confident",
    "prompt_sha256",
    "source_path",
]


def load_family_jsons(generated_dirs: list[Path]) -> dict[str, dict[str, Any]]:
    families: dict[str, dict[str, Any]] = {}
    for generated_dir in generated_dirs:
        if not generated_dir.exists():
            continue
        for path in sorted(generated_dir.rglob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            fid = row.get("template_id") or path.stem
            row["_source_path"] = str(path.relative_to(REPO_ROOT))
            families[fid] = row
    return families


def load_stage6_analysis(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {row["template_id"]: row for row in read_csv(path)}


def prompt_hash(prompt: str) -> str:
    import hashlib

    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-output", default="results/canonical/model_family_evidence.csv")
    parser.add_argument("--variant-output", default="results/canonical/model_variant_evidence.csv")
    parser.add_argument("--summary-output", default="results/stage13/wave0/canonical_evidence_build.json")
    args = parser.parse_args()

    family_jsons = load_family_jsons(
        [
            REPO_ROOT / "results/stage6/generated_full_benchmark",
            REPO_ROOT / "results/stage10/benchmark_expansion/rendered",
            REPO_ROOT / "results/stage11/variable_renaming/rendered",
        ]
    )
    stage6 = load_stage6_analysis(REPO_ROOT / "results/stage6/analysis_d2/stage6_d1_per_family.csv")
    positives: set[str] = set()
    positives_path = REPO_ROOT / "results/stage6/analysis_d2/stage6_positive_families.json"
    if positives_path.exists():
        data = json.loads(positives_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            positives = {str(item) for item in data}
        elif isinstance(data, dict):
            positives = {str(item) for item in data.get("positive_families", data.get("families", []))}

    family_rows: list[dict[str, Any]] = []
    for fid, family in sorted(family_jsons.items()):
        analysis = stage6.get(fid, {})
        family_rows.append(
            {
                "canonical_family_id": fid,
                "source_family_id": fid,
                "domain": family.get("domain") or analysis.get("domain", ""),
                "cue_type": family.get("cue_type") or analysis.get("cue_type", ""),
                "governing_law": analysis.get("governing_law", ""),
                "verifier_certified": family.get("verifier_certified", ""),
                "pi_validated": analysis.get("pi_validated", ""),
                "correct_answer": family.get("correct_answer", ""),
                "qwen_S_lp": analysis.get("qwen_S_lp", ""),
                "llama_S_lp": analysis.get("llama_S_lp", ""),
                "qwen_parse_ok": analysis.get("qwen_parse_ok", ""),
                "llama_parse_ok": analysis.get("llama_parse_ok", ""),
                "stage6_positive_qwen": fid in positives,
                "source_paths": family.get("_source_path", ""),
                "paper_eligible_status": "not_eligible_until_wave0_pass",
            }
        )

    variant_rows: list[dict[str, Any]] = []
    behavioural_files = sorted((REPO_ROOT / "results/stage6/behavioural_full_rerun").glob("*.jsonl"))
    for path in behavioural_files:
        if path.name in {"run_behavioural_events.jsonl", "prompt_records.jsonl", "family_summaries.jsonl"}:
            continue
        for row in read_jsonl(path):
            if row.get("record_type") != "variant_record":
                continue
            prompt = str(row.get("prompt", ""))
            variant_rows.append(
                {
                    "canonical_family_id": row.get("template_id", ""),
                    "variant_id": row.get("variant_id", ""),
                    "model_role": row.get("model_role", ""),
                    "domain": row.get("domain", ""),
                    "cue_type": row.get("cue_type", ""),
                    "cue_value": row.get("cue_value", ""),
                    "correct_answer": row.get("correct_answer", ""),
                    "logprob_correct_answer": row.get("logprob_correct_answer", ""),
                    "parsed_answer": row.get("parsed_answer", ""),
                    "parse_confident": row.get("parse_confident", ""),
                    "prompt_sha256": prompt_hash(prompt) if prompt else "",
                    "source_path": str(path.relative_to(REPO_ROOT)),
                }
            )

    write_csv(args.family_output, family_rows, FAMILY_FIELDS)
    write_csv(args.variant_output, variant_rows, VARIANT_FIELDS)

    # Optional parquet copy if pandas+pyarrow/fastparquet is available.
    parquet_outputs: dict[str, str] = {}
    try:  # pragma: no cover - environment dependent
        import pandas as pd

        family_parquet = str(Path(args.family_output).with_suffix(".parquet"))
        variant_parquet = str(Path(args.variant_output).with_suffix(".parquet"))
        pd.DataFrame(family_rows).astype(str).to_parquet(REPO_ROOT / family_parquet, index=False)
        pd.DataFrame(variant_rows).astype(str).to_parquet(REPO_ROOT / variant_parquet, index=False)
        parquet_outputs = {"family_parquet": family_parquet, "variant_parquet": variant_parquet}
    except Exception as exc:
        parquet_outputs = {"parquet_status": f"not_written: {exc}"}

    family_counts = defaultdict(int)
    for row in family_rows:
        family_counts[str(row.get("cue_type", "unknown"))] += 1
    write_json(
        args.summary_output,
        {
            "n_family_rows": len(family_rows),
            "n_variant_rows": len(variant_rows),
            "family_output": args.family_output,
            "variant_output": args.variant_output,
            "by_cue_type": dict(sorted(family_counts.items())),
            **parquet_outputs,
        },
    )


if __name__ == "__main__":
    main()
