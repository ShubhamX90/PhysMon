#!/bin/bash

#SBATCH --job-name=physmon_s12_h15_gate
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=4
#SBATCH --time=02:30:00
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

FAMILIES=(
  CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 CM_B_UM_055 CM_B_STD_013
  CM_B_UM_052 CM_B_STD_010 CM_B_STD_011 CM_B_UM_033 CM_B_UM_009
  CM_B_UM_013 TH_B_UM_006 CM_B_UM_006 TH_B_UM_008 EL_B_002
  CM_B_UM_012 CM_B_004 CM_B_STD_015 CM_B_UM_001 CM_B_STD_014
)

python -u scripts/run_h15_under_h11_knockout.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families "${FAMILIES[@]}" \
  --layer 16 \
  --gate-head 11 \
  --target-head 15 \
  --behavioural-jsonl results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl \
  --output-dir results/stage12/science/h11_h15_gating/ \
  --stage 12 \
  --seed 42
