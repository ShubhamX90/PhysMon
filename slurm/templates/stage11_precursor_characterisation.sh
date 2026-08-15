#!/bin/bash

#SBATCH --job-name=physmon_s11_precursor
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
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

python -u scripts/run_prompt_condition_probe.py \
  --activation-manifest /scratch/pabitra/physmon/activations_stage6/qwen_primary/manifest.json \
  --site resid_post_last_prompt \
  --sweep-all-layers \
  --output-dir results/stage11/science/precursor_characterisation/ \
  --stage 11 \
  --seed 42
