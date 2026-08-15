#!/bin/bash

#SBATCH --job-name=physmon_s12_multisite
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

python -u scripts/run_multi_site_probe.py \
  --activation-manifest /scratch/pabitra/physmon/activations_stage6/qwen_primary/manifest.json \
  --layer 16 \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --output-dir results/stage12/science/multi_site_probe/ \
  --stage 12 \
  --seed 42
