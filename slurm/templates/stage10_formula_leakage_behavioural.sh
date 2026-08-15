#!/bin/bash

#SBATCH --job-name=physmon_s10_formula_leak
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:30:00
#SBATCH --mem=48G
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

python scripts/run_formula_leakage_check.py \
  --emit-family-json \
  --output-dir results/appendix/formula_leakage

python scripts/run_behavioural.py \
  --model-role qwen_primary \
  --family-dir results/appendix/formula_leakage/generated_families \
  --output-dir results/appendix/formula_leakage/behavioural \
  --seed 42

QWEN_JSONL=$(ls -1t results/appendix/formula_leakage/behavioural/qwen_primary_*.jsonl | head -n 1)

python scripts/summarize_behavioural_jsonl.py \
  --jsonl "$QWEN_JSONL" \
  --output-dir results/appendix/formula_leakage/analysis \
  --model-prefix qwen \
  --threshold 0.5

python scripts/analyse_formula_leakage_results.py \
  --per-family-csv results/appendix/formula_leakage/analysis/per_family_summary.csv \
  --source-summary results/appendix/formula_leakage/formula_leakage_summary.json \
  --output-dir results/appendix/formula_leakage
