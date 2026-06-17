#!/bin/bash
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=physmon_s9_corrprobe
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_corrprobe_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u
export SCRATCH=/scratch/pabitra

python scripts/run_probing.py \
  --activation-dir $SCRATCH/physmon/activations_stage6/qwen_primary/ \
  --site resid_post_last_prompt \
  --model-role qwen_primary \
  --target-measure answer_correctness \
  --probe-type variance \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --behavioural-jsonl results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl \
  --correctness-threshold 0.75 \
  --exclude-ids CM_A_STD_018 CM_B_003 CM_B_UM_051 TH_B_UM_009 TH_B_UM_010 \
  --output-dir results/stage9/baselines/correctness_probe/ \
  --stage 9 --seed 42
