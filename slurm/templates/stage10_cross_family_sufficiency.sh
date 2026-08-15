#!/bin/bash

#SBATCH --job-name=physmon_s10_xfam_suf
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --time=03:00:00
#SBATCH --mem=80G
#SBATCH --cpus-per-task=4
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

python -u scripts/run_cross_family_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --patch-layer 16 \
  --output-dir results/stage10/cross_family_sufficiency/ \
  --stage 10 \
  --seed 42
