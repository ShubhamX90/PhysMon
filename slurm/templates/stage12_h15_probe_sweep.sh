#!/bin/bash

#SBATCH --job-name=physmon_s12_h15_probe
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

python -u scripts/run_h11_output_probe.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --heads 15 14 \
  --sweep-all-layers \
  --output-dir results/stage12/science/head_output_probes/ \
  --seed 42
