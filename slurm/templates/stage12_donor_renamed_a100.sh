#!/bin/bash

#SBATCH --job-name=physmon_s12_donren_a1
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=4
#SBATCH --time=03:30:00
#SBATCH --mem=80G
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
cd "$PHYSMON_ROOT"

LATEST_JSONL=$(ls -1t results/stage11/variable_renaming/behavioural/qwen_primary_*.jsonl | head -n 1)
RENAMED_FAMILIES=$(python - <<'PY'
import json, pathlib
payload = json.loads(pathlib.Path("results/stage11/variable_renaming/rendered/renamed_manifest.json").read_text())
print(" ".join(row["renamed_template_id"] for row in payload["families"]))
PY
)

python -u scripts/run_same_answer_donor.py \
  --model-role qwen_primary \
  --family-dir results/stage11/variable_renaming/rendered/ \
  --patch-families ${RENAMED_FAMILIES} \
  --family-csv results/stage11/variable_renaming/behavioural/analysis/per_family_summary.csv \
  --donor-family-dir results/stage6/generated_full_benchmark/ \
  --donor-family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --patch-layer 16 \
  --behavioural-jsonl "$LATEST_JSONL" \
  --output-dir results/stage12/science/donor_renamed/same_answer/ \
  --stage 12 \
  --seed 42

python -u scripts/run_stable_donor.py \
  --model-role qwen_primary \
  --family-dir results/stage11/variable_renaming/rendered/ \
  --patch-families ${RENAMED_FAMILIES} \
  --family-csv results/stage11/variable_renaming/behavioural/analysis/per_family_summary.csv \
  --donor-family-dir results/stage6/generated_full_benchmark/ \
  --donor-family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --patch-layer 16 \
  --behavioural-jsonl "$LATEST_JSONL" \
  --output-dir results/stage12/science/donor_renamed/stable/ \
  --stage 12 \
  --seed 42
