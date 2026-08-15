#!/bin/bash

#SBATCH --job-name=physmon_s12_q3b_a1
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=4
#SBATCH --time=10:00:00
#SBATCH --mem=80G
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
  --model-role qwen_3b \
  --family-dir results/stage6/generated_full_benchmark/ \
  --output-dir results/stage12/qwen_3b/behavioural/ \
  --seed 42
