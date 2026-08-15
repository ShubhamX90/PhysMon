#!/bin/bash

#SBATCH --job-name=physmon_s10_mhk_cue_gen
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --time=03:00:00
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
  CM_A_STD_019 CM_A_STD_005 CM_A_STD_002 CM_A_STD_004 CM_A_STD_003
  CM_C_001 CM_C_002 CM_C_003 CM_C_004 CM_C_005
)

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families "${FAMILIES[@]}" \
  --patch-layers 14 15 16 17 18 \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --multi-head-knockout 26 24 13 11 \
  --output-dir results/stage10/mhk_cue_generalization/ \
  --stage 10 \
  --seed 42
