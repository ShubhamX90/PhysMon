#!/bin/bash

#SBATCH --job-name=physmon_s12_q14b_beh
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=4
#SBATCH --time=12:00:00
#SBATCH --mem=120G
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

python -u scripts/run_behavioural.py \
  --model-role qwen_14b \
  --family-dir results/stage6/generated_full_benchmark/ \
  --output-dir results/stage12/qwen_14b/behavioural/ \
  --seed 42
