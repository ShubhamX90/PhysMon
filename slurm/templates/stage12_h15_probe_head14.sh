#!/bin/bash

#SBATCH --job-name=physmon_s12_h15_h14
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=4
#SBATCH --time=03:30:00
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

python -u scripts/run_h11_output_probe.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --heads 14 \
  --sweep-all-layers \
  --output-dir results/stage12/science/head_output_probes/head14/ \
  --seed 42
