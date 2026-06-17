#!/bin/bash
#SBATCH --job-name=physmon_s9_inject
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --time=04:00:00
#SBATCH --mem=80G
#SBATCH --cpus-per-task=8
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/s9_inject_%j.out

source ~/.bashrc
set +u; conda activate physmon; set -u
export SCRATCH=/scratch/pabitra

python scripts/run_direction_injection.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --activation-dir $SCRATCH/physmon/activations_stage6/qwen_primary/ \
  --slp-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --inject-layer 16 \
  --injection-scales 0.0 0.25 0.5 1.0 1.5 2.0 \
  --n-pos-direction-families 20 \
  --n-neg-target-families 30 \
  --output-dir results/stage9/direction_injection/ \
  --stage 9 --seed 42
