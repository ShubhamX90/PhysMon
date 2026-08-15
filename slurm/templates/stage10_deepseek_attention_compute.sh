#!/bin/bash

#SBATCH --job-name=physmon_s10_ds_attn_cpu
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=05:00:00
#SBATCH --mem=64G
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
export HF_HOME="$SCRATCH/physmon/hf_cache"
export TRANSFORMERS_CACHE="$SCRATCH/physmon/hf_cache"
cd "$PHYSMON_ROOT"

FAMILIES=(
  CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 CM_B_UM_055 CM_B_STD_013
  CM_B_UM_052 CM_B_STD_010 CM_B_STD_011 CM_B_UM_033 CM_B_UM_009
  CM_B_UM_013 TH_B_UM_006 CM_B_UM_006 TH_B_UM_008 EL_B_002
  CM_B_UM_012 CM_B_004 CM_B_STD_015 CM_B_UM_001 CM_B_STD_014
)

for LAYER in 42 43 44 45; do
  python -u scripts/run_attention_analysis.py \
    --activation-dir "$SCRATCH/physmon/activations_stage6/deepseek_reasoning/" \
    --layer "$LAYER" \
    --families "${FAMILIES[@]}" \
    --model-key deepseek_reasoning \
    --family-csv results/stage8/analysis_deepseek/deepseek_per_family.csv \
    --positive-families-file results/stage8/analysis_deepseek/stage8_positive_families_deepseek.json \
    --output-dir "results/stage10/deepseek_attention/layer_${LAYER}/" \
    --stage 10 \
    --seed 42
done
