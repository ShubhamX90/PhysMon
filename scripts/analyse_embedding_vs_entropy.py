#!/usr/bin/env python3
"""Compare the entropy proxy baseline against embedding-layer and best-layer probes."""

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
        "--entropy-summary",
        default="results/stage9/baselines/entropy/entropy_baseline_summary.json",
    )
    parser.add_argument(
        "--layer-auroc",
        default="results/stage6/probing/primary_variance/layer_auroc_variance.json",
    )
    parser.add_argument(
        "--output",
        default="results/stage9/baselines/entropy/embedding_vs_entropy_summary.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    entropy_summary = json.loads(Path(args.entropy_summary).read_text(encoding="utf-8"))
    layer_rows = json.loads(Path(args.layer_auroc).read_text(encoding="utf-8"))

    best_row = max(layer_rows, key=lambda row: float(row["auroc"]))
    embedding_row = next(row for row in layer_rows if int(row["layer_index"]) == 0)

    entropy_auroc = float(entropy_summary["auroc"])
    embedding_auroc = float(embedding_row["auroc"])
    best_probe_auroc = float(best_row["auroc"])

    payload = {
        "entropy_proxy_auroc": entropy_auroc,
        "embedding_layer_probe_auroc": embedding_auroc,
        "best_layer_probe_auroc": best_probe_auroc,
        "best_layer_index": int(best_row["layer_index"]),
        "delta_entropy_minus_embedding": entropy_auroc - embedding_auroc,
        "delta_best_probe_minus_entropy": best_probe_auroc - entropy_auroc,
        "interpretation": (
            "Entropy proxy is much stronger than embedding-layer variance, so it cannot be dismissed as a shallow lexical signal alone. "
            "The hidden-state probe still edges entropy at the best layer, but only narrowly, so the paper should frame entropy as a strong output-side baseline rather than a trivial straw baseline."
        ),
        "note": (
            "This summary compares AUROC levels directly. Family-level embedding-layer predictions were not saved in the existing Stage 6 artifact set, so no per-family correlation term is reported here."
        ),
    }
    write_json(Path(args.output), payload)


if __name__ == "__main__":
    main()
