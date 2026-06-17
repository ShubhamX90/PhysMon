#!/bin/bash
#SBATCH --job-name=physmon_s9_donor
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --time=03:00:00
#SBATCH --mem=80G
#SBATCH --cpus-per-task=8
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_donor_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u

python scripts/run_donor_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --patch-families CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 CM_B_UM_055 \
                   CM_B_STD_013 CM_B_UM_052 CM_B_STD_010 CM_B_STD_011 \
                   CM_B_UM_033 CM_B_UM_009 CM_B_UM_013 TH_B_UM_006 \
                   CM_B_UM_006 TH_B_UM_008 EL_B_002 CM_B_UM_012 \
                   CM_B_004 CM_B_STD_015 CM_B_UM_001 CM_B_STD_014 \
  --donor-families TH_B_UM_001 TH_B_UM_002 TH_B_UM_003 TH_B_UM_004 TH_B_UM_005 \
  --donor-mode unrelated_and_same_answer \
  --patch-layers 16 \
  --patch-site resid_post_last_prompt \
  --output-dir results/stage9/unrelated_donor/ \
  --stage 9 --seed 42
