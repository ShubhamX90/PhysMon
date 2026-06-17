#!/bin/bash
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --job-name=physmon_s9_ansrat
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_ansrat_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u

python scripts/run_baselines_surface.py \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --generated-dir results/stage6/generated_full_benchmark/ \
  --behavioural-jsonl results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl \
  --target-measure slp_binary \
  --threshold 0.5 \
  --baseline-type answer_rationale_classifier \
  --exclude-ids CM_A_STD_018 CM_B_003 CM_B_UM_051 TH_B_UM_009 TH_B_UM_010 \
  --output-dir results/stage9/baselines/answer_rationale/ \
  --stage 9 --seed 42
