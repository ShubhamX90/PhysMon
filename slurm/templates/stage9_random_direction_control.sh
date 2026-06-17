#!/bin/bash
#SBATCH --job-name=physmon_s9_rdc
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --time=04:00:00
#SBATCH --mem=80G
#SBATCH --cpus-per-task=8
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_rdc_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u

python scripts/run_random_direction_control.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 CM_B_UM_055 \
                   CM_B_STD_013 CM_B_UM_052 CM_B_STD_010 CM_B_STD_011 \
                   CM_B_UM_033 CM_B_UM_009 CM_B_UM_013 TH_B_UM_006 \
                   CM_B_UM_006 TH_B_UM_008 EL_B_002 CM_B_UM_012 \
                   CM_B_004 CM_B_STD_015 CM_B_UM_001 CM_B_STD_014 \
  --prior-mhk-results results/stage8/multi_head_knockout/ \
  --patch-layer 16 \
  --head-indices 26 24 13 11 \
  --n-random-directions 20 \
  --output-dir results/stage9/random_direction_control/ \
  --stage 9 --seed 42
