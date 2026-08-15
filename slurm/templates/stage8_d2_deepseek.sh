#!/bin/bash
# Stage 8 full DeepSeek-R1 behavioural sweep.

#SBATCH --job-name=physmon_stage8_deepseek_d2
#SBATCH --partition=gpu_h200_8
#SBATCH --gres=gpu:nvidia_h200_nvl:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=120G
#SBATCH --time=16:00:00
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

echo "=== PhysMon Stage 8 DeepSeek D2 Start ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "========================================="

cd "$PHYSMON_ROOT"

python -u scripts/run_behavioural.py \
  --model-role deepseek_reasoning \
  --family-dir results/stage6/generated_full_benchmark/ \
  --output-dir results/stage6/behavioural_deepseek/ \
  --device cuda \
  --device-map auto \
  --max-new-tokens 512 \
  --seed 42

echo "=== PhysMon Stage 8 DeepSeek D2 Complete ==="
