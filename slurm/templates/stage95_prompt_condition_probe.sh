#!/bin/bash

#SBATCH --job-name=physmon_s95_prompt_cond
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
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

python -u scripts/run_prompt_condition_probe.py \
  --activation-manifest "$SCRATCH/physmon/activations_stage6/qwen_primary/manifest.json" \
  --site resid_post_last_prompt \
  --layer 18 \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --output-dir results/stage9/prompt_condition_probe/ \
  --stage 9 \
  --seed 42
