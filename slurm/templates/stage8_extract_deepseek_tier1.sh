#!/bin/bash
# Stage 8 DeepSeek-R1 tier-1 activation extraction.

#SBATCH --job-name=physmon_stage8_extract_deepseek
#SBATCH --partition=gpu_h200_8
#SBATCH --gres=gpu:nvidia_h200_nvl:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=160G
#SBATCH --time=05:00:00
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
if [ -f "$PHYSMON_ROOT/.physmon_git_commit" ]; then
  export PHYSMON_GIT_COMMIT="$(cat "$PHYSMON_ROOT/.physmon_git_commit")"
fi

echo "=== PhysMon Stage 8 DeepSeek Extraction Start ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "==============================================="

cd "$PHYSMON_ROOT"

python -u scripts/extract_activations.py \
  --model-role deepseek_reasoning \
  --family-dir results/stage6/generated_full_benchmark \
  --output-dir "$SCRATCH/physmon/activations_stage6/" \
  --tier 1 \
  --stage 8 \
  --seed 42

echo "=== PhysMon Stage 8 DeepSeek Extraction Complete ==="
