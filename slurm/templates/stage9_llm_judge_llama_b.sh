#!/bin/bash
#SBATCH --job-name=physmon_s9_judge_lb
#SBATCH --partition=gpu_h200_8
#SBATCH --gres=gpu:nvidia_h200_nvl:1
#SBATCH --time=04:00:00
#SBATCH --mem=80G
#SBATCH --cpus-per-task=8
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_judge_lb_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u

python scripts/run_llm_judge_baseline.py \
  --judge-model llama_primary \
  --judge-setting B \
  --family-dir results/stage6/generated_full_benchmark/ \
  --slp-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --exclude-ids CM_A_STD_018 CM_B_003 CM_B_UM_051 TH_B_UM_009 TH_B_UM_010 \
  --output-dir results/stage9/baselines/llm_judge/llama_setting_b/ \
  --stage 9 --seed 42
