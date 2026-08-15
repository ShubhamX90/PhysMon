#!/usr/bin/env python3
"""Prepare Appendix A formula-leakage sanity-check artifacts.

This script selects a small set of low-sensitivity families, constructs explicit
formula-hint prompt variants for each, records the existing baseline
behaviour/probe scores for those families, and emits compact rendered-family
JSON payloads that can be evaluated directly by `scripts/run_behavioural.py`.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from physmon.utils.io import write_json  # noqa: E402


DEFAULT_FAMILIES = (
    "TH_B_UM_001",
    "TH_B_UM_003",
    "CM_B_010",
    "CM_B_UM_028",
    "CM_A_STD_009",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-csv", default="results/stage6/analysis_d2/stage6_d1_per_family.csv")
    parser.add_argument("--variance-preds", default="results/stage6/probing/primary_variance/loo_predictions_variance.json")
    parser.add_argument("--family-dir", default="results/stage6/generated_full_benchmark")
    parser.add_argument("--families", nargs="*", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--output-dir", default="results/appendix/formula_leakage")
    parser.add_argument(
        "--emit-family-json",
        action="store_true",
        help="Also emit rendered family JSON payloads for direct behavioural evaluation.",
    )
    return parser.parse_args()


def load_family_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["template_id"]: row for row in csv.DictReader(handle)}


def load_predictions(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["template_id"]: float(row["prediction"]) for row in payload}


def derive_formula_hint(prompt: str, correct_answer: str) -> str:
    """Infer a compact governing-law hint from the prompt text."""

    prompt_lower = prompt.lower()
    if "specific heat capacity" in prompt_lower and "warms by" in prompt_lower:
        return "Use the governing relation Q = m c ΔT."
    if "torque" in prompt_lower and ("wrench" in prompt_lower or "lever arm" in prompt_lower):
        return "Use the governing relation τ = rF for a perpendicular force."
    if "spring constant" in prompt_lower and "stretched" in prompt_lower:
        return "Use Hooke's law: F = kx."
    if "kinetic energy" in prompt_lower:
        return "Use the governing relation K = (1/2)mv^2."
    if "potential energy" in prompt_lower:
        return "Use the governing relation U = mgh."
    if "acceleration" in prompt_lower and "net force" in prompt_lower:
        return "Use Newton's second law: F = ma."
    if "work is done" in prompt_lower or "how much work" in prompt_lower:
        return "Use the governing relation W = Fd for a constant parallel force."
    return f"Use the governing physics relation needed to compute {correct_answer} directly."


def inject_formula_hint(prompt: str, formula_hint: str) -> str:
    """Insert a formula hint before the final question block."""

    if "\n\n" in prompt:
        stem, question = prompt.rsplit("\n\n", 1)
        return f"{stem}\n{formula_hint}\n\n{question}"
    return f"{formula_hint}\n\n{prompt}"


def build_formula_leakage_family(
    family_payload: dict[str, Any],
    base_prompt: str,
    formula_prompt: str,
    formula_hint: str,
) -> dict[str, Any]:
    """Construct a minimal rendered-family payload for behavioural execution."""

    template_id = str(family_payload["template_id"])
    correct_answer = str(family_payload["correct_answer"])
    return {
        "template_id": f"{template_id}_FORMULA",
        "domain": family_payload.get("domain"),
        "cue_type": "formula_leakage_sanity",
        "correct_answer": correct_answer,
        "verifier_certified": True,
        "variants": [
            {
                "variant_id": 0,
                "correct_answer": correct_answer,
                "cue_value": "none",
                "cue_sentence": "",
                "prompt": base_prompt,
                "variant_label": "base",
            },
            {
                "variant_id": 1,
                "correct_answer": correct_answer,
                "cue_value": formula_hint,
                "cue_sentence": formula_hint,
                "prompt": formula_prompt,
                "variant_label": "formula_hint",
            },
        ],
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    family_rows = load_family_rows(Path(args.family_csv))
    preds = load_predictions(Path(args.variance_preds))

    selected = []
    behavioural_payloads: list[dict[str, Any]] = []
    for family_id in args.families:
        payload_path = Path(args.family_dir) / f"{family_id}.json"
        if not payload_path.exists():
            continue
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        base_variant = next(variant for variant in payload["variants"] if int(variant["variant_id"]) == 0)
        formula_hint = derive_formula_hint(str(base_variant["prompt"]), str(payload["correct_answer"]))
        formula_prompt = inject_formula_hint(str(base_variant["prompt"]), formula_hint)
        row = family_rows.get(family_id, {})
        selected.append(
            {
                "template_id": family_id,
                "domain": payload.get("domain"),
                "cue_type": payload.get("cue_type"),
                "correct_answer": payload.get("correct_answer"),
                "baseline_qwen_slp": float(row.get("qwen_S_lp", "0") or "0"),
                "baseline_variance_probe_prediction": float(preds.get(family_id, 0.0)),
                "formula_hint": formula_hint,
                "base_prompt": base_variant["prompt"],
                "formula_prompt": formula_prompt,
            }
        )
        if args.emit_family_json:
            behavioural_payloads.append(
                build_formula_leakage_family(
                    family_payload=payload,
                    base_prompt=str(base_variant["prompt"]),
                    formula_prompt=formula_prompt,
                    formula_hint=formula_hint,
                )
            )

    write_json(
        output_dir / "formula_leakage_prompt_pairs.json",
        {
            "families": selected,
            "note": (
                "Prompt pairs prepared for the Appendix A formula-leakage sanity check. "
                "Each pair contains the original low-sensitivity base prompt and a "
                "formula-hint variant that makes the governing law explicit."
            ),
        },
    )
    write_json(
        output_dir / "formula_leakage_summary.json",
        {
            "execution_status": "behavioural_payloads_prepared" if args.emit_family_json else "prompt_pairs_prepared",
            "n_families": len(selected),
            "families": [
                {
                    "template_id": row["template_id"],
                    "baseline_qwen_slp": row["baseline_qwen_slp"],
                    "baseline_variance_probe_prediction": row["baseline_variance_probe_prediction"],
                    "formula_hint": row["formula_hint"],
                }
                for row in selected
            ],
            "next_step": (
                "Run behavioural inference on the generated rendered-family payloads and verify that "
                "formula-hint variants remain low-sensitivity and do not trigger elevated probe scores."
            ),
        },
    )

    if args.emit_family_json:
        family_dir = output_dir / "generated_families"
        family_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows = []
        for payload in behavioural_payloads:
            family_path = family_dir / f"{payload['template_id']}.json"
            write_json(family_path, payload)
            manifest_rows.append(
                {
                    "template_id": payload["template_id"],
                    "source_family": payload["template_id"].removesuffix("_FORMULA"),
                    "n_variants": len(payload["variants"]),
                    "cue_type": payload["cue_type"],
                }
            )
        write_json(
            output_dir / "generated_families_manifest.json",
            {
                "n_families": len(behavioural_payloads),
                "family_dir": str(family_dir),
                "families": manifest_rows,
            },
        )


if __name__ == "__main__":
    main()
