#!/bin/bash

#SBATCH --job-name=physmon_s12_llm_h2mx
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=4
#SBATCH --time=04:00:00
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

SUBSETS=(
  "2"
  "2 10"
  "2 23"
  "2 10 23"
  "2 10 23 9"
)

for SPEC in "${SUBSETS[@]}"; do
  read -r -a HEADS <<< "$SPEC"
  NAME=$(printf '%s_' "${HEADS[@]}")
  NAME=${NAME%_}
  OUTDIR="results/stage12/llama_head2_combos/subset_${NAME}"
  python -u scripts/run_causal_patching.py \
    --model-role llama_primary \
    --family-dir results/stage6/generated_full_benchmark/ \
    --patch-families "${FAMILIES[@]}" \
    --patch-layers 21 \
    --patch-site resid_post_last_prompt \
    --patch-mode head_knockout \
    --multi-head-knockout "${HEADS[@]}" \
    --behavioural-jsonl results/stage6/behavioural_full_rerun/llama_primary_20260616T085448Z.jsonl \
    --output-dir "$OUTDIR" \
    --stage 12 \
    --seed 42
done
