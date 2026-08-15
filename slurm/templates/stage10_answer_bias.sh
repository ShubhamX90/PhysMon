#!/bin/bash

#SBATCH --job-name=physmon_s10_ans_bias
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
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

python -u scripts/run_answer_bias_check.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --negative-families-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --n-negative-families 40 \
  --knockout-heads 26 24 13 11 \
  --knockout-layer 16 \
  --output-dir results/stage10/answer_bias/ \
  --stage 10 \
  --seed 42
