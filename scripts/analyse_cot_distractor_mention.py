#!/usr/bin/env python3
"""Analyse whether generated text explicitly mentions distractor values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from collections import defaultdict

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--behavioural-jsonl", default="results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl")
    parser.add_argument("--generated-dir", default="results/stage6/generated_full_benchmark")
    parser.add_argument("--family-csv", default="results/stage6/analysis_d2/stage6_d1_per_family.csv")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--output", default="results/stage10/cot_distractor_mention/cot_mention_summary.json")
    return parser.parse_args()


def normalize_value(text: str) -> str:
    text = text.strip().lower()
    return re.sub(r"\s+", "", text)


def main() -> None:
    args = parse_args()
    import csv

    with Path(args.family_csv).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    top_rows = sorted(rows, key=lambda r: float(r.get("qwen_S_lp", "0") or "0"), reverse=True)[: args.top_k]
    selected = {row["template_id"]: float(row["qwen_S_lp"]) for row in top_rows}

    cue_value_by_variant: dict[tuple[str, int], str] = {}
    for path in Path(args.generated_dir).glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        tid = payload.get("template_id")
        if tid not in selected:
            continue
        for variant in payload.get("variants", []):
            cue_value_by_variant[(tid, int(variant["variant_id"]))] = str(variant.get("cue_value", ""))

    family_stats: dict[str, dict[str, float | int | list[dict[str, str | int | bool]]]] = {}
    mention_rows = []
    with Path(args.behavioural_jsonl).open("r", encoding="utf-8") as handle:
        for line in handle:
            rec = json.loads(line)
            if rec.get("record_type") != "variant_record":
                continue
            tid = rec["template_id"]
            if tid not in selected:
                continue
            vid = int(rec["variant_id"])
            generated = str(rec.get("generated_text", "") or "")
            cue_value = cue_value_by_variant.get((tid, vid), "")
            norm_generated = normalize_value(generated)
            norm_cue = normalize_value(cue_value)
            mentions = bool(norm_cue) and norm_cue in norm_generated
            row = {
                "template_id": tid,
                "variant_id": vid,
                "cue_value": cue_value,
                "mentions_distractor": mentions,
                "generated_text_excerpt": generated[:240],
            }
            mention_rows.append(row)
            stats = family_stats.setdefault(tid, {"slp": selected[tid], "mentions": 0, "total": 0, "variants": []})
            stats["mentions"] += int(mentions)
            stats["total"] += 1
            stats["variants"].append(row)

    summary_rows = []
    for tid, stats in sorted(family_stats.items(), key=lambda item: item[1]["slp"], reverse=True):
        mention_rate = stats["mentions"] / max(stats["total"], 1)
        summary_rows.append(
            {
                "template_id": tid,
                "qwen_S_lp": float(stats["slp"]),
                "mention_rate": mention_rate,
                "mentions": int(stats["mentions"]),
                "total": int(stats["total"]),
            }
        )

    slps = np.asarray([row["qwen_S_lp"] for row in summary_rows], dtype=float)
    mention_rates = np.asarray([row["mention_rate"] for row in summary_rows], dtype=float)
    corr = float(np.corrcoef(slps, mention_rates)[0, 1]) if len(summary_rows) > 1 else None
    payload = {
        "n_families": len(summary_rows),
        "n_variant_records": len(mention_rows),
        "family_level_slp_vs_mention_rate_pearson": corr,
        "families": summary_rows,
        "variant_rows": mention_rows,
        "interpretation": (
            "high-S_lp sensitivity often manifests without explicit distractor mention"
            if corr is not None and corr < 0.3
            else "distractor mention tracks sensitivity for many families"
        ),
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
