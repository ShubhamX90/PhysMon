#!/bin/bash

#SBATCH --job-name=physmon_s11_varname
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=4
#SBATCH --time=05:00:00
#SBATCH --mem=80G
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
cd "$PHYSMON_ROOT"

python -u scripts/run_behavioural.py \
  --model-role qwen_primary \
  --family-dir results/stage11/variable_renaming/rendered/ \
  --output-dir results/stage11/variable_renaming/behavioural/ \
  --seed 42

LATEST_JSONL=$(ls -1t results/stage11/variable_renaming/behavioural/qwen_primary_*.jsonl | head -n 1)
PYTHONPATH=src python -u scripts/summarize_behavioural_jsonl.py \
  --jsonl "$LATEST_JSONL" \
  --output-dir results/stage11/variable_renaming/behavioural/analysis/ \
  --model-prefix qwen \
  --threshold 0.5

python - <<'PY'
import csv, json, pathlib

rows = list(
    csv.DictReader(
        open(
            "results/stage11/variable_renaming/behavioural/analysis/per_family_summary.csv",
            "r",
            encoding="utf-8",
        )
    )
)
positives = []
for row in rows:
    slp = float(row.get("qwen_S_lp", "0") or "0")
    parse_rate = float(row.get("qwen_parse_rate_family", "1") or "1")
    if parse_rate >= 0.5 and slp >= 0.5:
        positives.append(row["template_id"])

payload = {
    "threshold": 0.5,
    "positive_families": positives,
    "source_csv": "results/stage11/variable_renaming/behavioural/analysis/per_family_summary.csv",
}
path = pathlib.Path("results/stage11/variable_renaming/renamed_positive_families.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2))
PY

python -u scripts/extract_activations.py \
  --model-role qwen_primary \
  --family-dir results/stage11/variable_renaming/rendered/ \
  --output-dir "$SCRATCH/physmon/activations_stage11_variable_renaming/" \
  --tier 1 \
  --stage 11 \
  --seed 42

PYTHONPATH=src python -u scripts/run_trained_per_variant_probe.py \
  --source-manifest "$SCRATCH/physmon/activations_stage6/qwen_primary/manifest.json" \
  --target-manifest "$SCRATCH/physmon/activations_stage11_variable_renaming/qwen_primary/manifest.json" \
  --site resid_post_last_prompt \
  --layer 16 \
  --source-positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --target-positive-families-file results/stage11/variable_renaming/renamed_positive_families.json \
  --output-dir results/stage11/science/variable_renaming/probe_inference/

RENAMED_FAMILIES=$(python - <<'PY'
import json, pathlib
renamed = json.loads(pathlib.Path("results/stage11/variable_renaming/rendered/renamed_manifest.json").read_text())
print(" ".join(row["renamed_template_id"] for row in renamed["families"]))
PY
)

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage11/variable_renaming/rendered/ \
  --patch-families ${RENAMED_FAMILIES} \
  --patch-layers 16 \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --head-index 11 \
  --behavioural-jsonl "$LATEST_JSONL" \
  --output-dir results/stage11/science/variable_renaming/h11_knockout/ \
  --stage 11 \
  --seed 42
