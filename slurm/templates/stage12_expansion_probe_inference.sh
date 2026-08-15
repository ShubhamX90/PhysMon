#!/bin/bash

#SBATCH --job-name=physmon_s12_exp_inf
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

export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
cd "$PHYSMON_ROOT"

python -u scripts/run_trained_per_variant_probe.py \
  --source-manifest /scratch/pabitra/physmon/activations_stage6/qwen_primary/manifest.json \
  --target-manifest /scratch/pabitra/physmon/activations_stage11_expansion/qwen_primary/manifest.json \
  --site resid_post_last_prompt \
  --layer 16 \
  --source-positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --target-positive-families-file results/stage12/expansion_probe_inference/expansion_positive_families.json \
  --output-dir results/stage12/expansion_probe_inference/ \
  --seed 42
