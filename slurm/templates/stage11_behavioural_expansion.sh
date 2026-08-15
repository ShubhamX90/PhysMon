#!/bin/bash

#SBATCH --job-name=physmon_s11_beh_exp
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=4
#SBATCH --time=02:30:00
#SBATCH --mem=80G
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
cd "$PHYSMON_ROOT"

FLAT_DIR="$SCRATCH/physmon/stage11_expansion_flat"
rm -rf "$FLAT_DIR"
mkdir -p "$FLAT_DIR"
find results/stage10/benchmark_expansion/rendered -name '*.json' -type f -exec cp {} "$FLAT_DIR"/ \;

OUT_DIR="results/stage11/behavioural_expansion"
mkdir -p "$OUT_DIR"

python -u scripts/run_behavioural.py \
  --model-role qwen_primary \
  --family-dir "$FLAT_DIR" \
  --output-dir "$OUT_DIR" \
  --seed 42

QWEN_JSONL=$(ls -1t "$OUT_DIR"/qwen_primary_*.jsonl | head -n 1)
python -u scripts/summarize_behavioural_jsonl.py \
  --jsonl "$QWEN_JSONL" \
  --output-dir "$OUT_DIR" \
  --model-prefix qwen \
  --threshold 0.5
