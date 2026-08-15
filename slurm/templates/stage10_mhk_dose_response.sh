#!/bin/bash

#SBATCH --job-name=physmon_s10_mhk_dose
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --time=05:00:00
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

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families "${FAMILIES[@]}" \
  --patch-layers 14 15 16 17 18 19 20 \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --head-index 26 \
  --output-dir results/stage10/mhk_dose_response/heads_1/ \
  --stage 10 \
  --seed 42

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families "${FAMILIES[@]}" \
  --patch-layers 14 15 16 17 18 19 20 \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --multi-head-knockout 26 24 \
  --output-dir results/stage10/mhk_dose_response/heads_2/ \
  --stage 10 \
  --seed 42

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families "${FAMILIES[@]}" \
  --patch-layers 14 15 16 17 18 19 20 \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --multi-head-knockout 26 24 13 \
  --output-dir results/stage10/mhk_dose_response/heads_3/ \
  --stage 10 \
  --seed 42

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families "${FAMILIES[@]}" \
  --patch-layers 14 15 16 17 18 19 20 \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --multi-head-knockout 26 24 13 11 \
  --output-dir results/stage10/mhk_dose_response/heads_4/ \
  --stage 10 \
  --seed 42
