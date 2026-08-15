#!/bin/bash

#SBATCH --job-name=physmon_s11_cue_transfer
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=01:30:00
#SBATCH --mem=32G
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

python -u scripts/run_cross_cue_probe_transfer.py \
  --activation-dir "$SCRATCH/physmon/activations_stage6/qwen_primary/" \
  --site resid_post_last_prompt \
  --layer 16 \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --output-dir results/stage11/science/cross_cue_transfer/
