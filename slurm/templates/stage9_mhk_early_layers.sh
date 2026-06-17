#!/bin/bash
#SBATCH --job-name=physmon_s9_mhk_early
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --time=04:00:00
#SBATCH --mem=80G
#SBATCH --cpus-per-task=8
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_mhk_early_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u

python scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 CM_B_UM_055 \
                   CM_B_STD_013 CM_B_UM_009 CM_B_UM_013 TH_B_UM_006 \
                   CM_B_UM_006 TH_B_UM_008 EL_B_002 CM_B_UM_012 \
                   CM_B_004 CM_B_STD_015 CM_B_UM_001 CM_B_STD_014 \
  --patch-layers 4 8 12 \
  --multi-head-knockout 26 24 13 11 \
  --patch-site resid_post_last_prompt \
  --output-dir results/stage9/mhk_early_layers/ \
  --stage 9 --seed 42

python scripts/run_damage_control.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --negative-families-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --n-negative-families 40 \
  --knockout-heads 26 24 13 11 \
  --knockout-layer 16 \
  --output-dir results/stage9/damage_control/ \
  --stage 9 --seed 42
