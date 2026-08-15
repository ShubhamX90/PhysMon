#!/bin/bash

#SBATCH --job-name=physmon_s12_llm_h24_31
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=3
#SBATCH --time=05:30:00
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

for HEAD in 24 25 26 27 28 29 30 31; do
  python -u scripts/run_causal_patching.py \
    --model-role llama_primary \
    --family-dir results/stage6/generated_full_benchmark/ \
    --patch-families "${FAMILIES[@]}" \
    --patch-layers 19 20 21 \
    --patch-site resid_post_last_prompt \
    --patch-mode head_knockout \
    --head-index "$HEAD" \
    --behavioural-jsonl results/stage6/behavioural_full_rerun/llama_primary_20260616T085448Z.jsonl \
    --output-dir "results/stage12/llama_full_head_sweep/head_${HEAD}/" \
    --stage 12 \
    --seed 42
done
