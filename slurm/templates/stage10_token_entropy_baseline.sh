#!/bin/bash

#SBATCH --job-name=physmon_s10_tok_ent
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --time=02:30:00
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

python -u scripts/run_token_entropy_baseline.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --topk 1000 \
  --output-dir results/stage10/baselines/token_entropy/ \
  --stage 10 \
  --seed 42
