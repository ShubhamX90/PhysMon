#!/bin/bash

#SBATCH --job-name=physmon_s12_exp_pv
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=02:30:00
#SBATCH --mem=32G
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

python -u scripts/run_per_variant_probe_sweep.py \
  --activation-manifest results/stage12/expanded_probe_training/combined_manifest.json \
  --site resid_post_last_prompt \
  --positive-families-file results/stage12/expanded_probe_training/combined_positive_families.json \
  --output-dir results/stage12/expanded_probe_training/per_variant_sweep/ \
  --stage 12 \
  --seed 42
