#!/bin/bash
#SBATCH --job-name=physmon_s9_selfcon_r
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --time=10:00:00
#SBATCH --mem=80G
#SBATCH --cpus-per-task=8
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_selfcon_r_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u

python scripts/run_self_consistency_baseline.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --exclude-ids CM_A_STD_018 CM_B_003 CM_B_UM_051 TH_B_UM_009 TH_B_UM_010 \
  --n-samples 5 \
  --temperature 0.7 \
  --top-p 0.9 \
  --output-dir results/stage9/baselines/self_consistency/ \
  --stage 9 --seed 42
