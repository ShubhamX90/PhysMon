#!/bin/bash

#SBATCH --job-name=physmon_s10_llm_attn
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --time=04:00:00
#SBATCH --mem=80G
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
cd "$PHYSMON_ROOT"

FAMILIES=(
  CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 CM_B_UM_055 CM_B_STD_013
  CM_B_UM_052 CM_B_STD_010 CM_B_STD_011 CM_B_UM_033 CM_B_UM_009
  CM_B_UM_013 TH_B_UM_006 CM_B_UM_006 TH_B_UM_008 EL_B_002
  CM_B_UM_012 CM_B_004 CM_B_STD_015 CM_B_UM_001 CM_B_STD_014
)

for LAYER in 19 20 21; do
  python -u scripts/run_attention_analysis.py \
    --activation-dir "$SCRATCH/physmon/activations_stage6/llama_primary/" \
    --layer "$LAYER" \
    --families "${FAMILIES[@]}" \
    --model-key llama_primary \
    --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
    --positive-families-file results/stage6/analysis_d2/stage6_positive_families_llama.json \
    --output-dir "results/stage10/llama_attention/layer_${LAYER}/" \
    --stage 10 \
    --seed 42
done
