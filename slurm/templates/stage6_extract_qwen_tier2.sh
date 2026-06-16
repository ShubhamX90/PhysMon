#!/bin/bash
# Stage 6 full-benchmark activation extraction on Qwen (Tier 2: cue-token residuals).

#SBATCH --job-name=physmon_stage6_extract_qwen_t2
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=60G
#SBATCH --time=03:00:00
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

echo "=== PhysMon Stage 6 Extraction Start (Qwen Tier 2) ==="
echo "Reminder: run 'make sync-up' from the Mac repo before submitting jobs."
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "========================================="

cd "$PHYSMON_ROOT"

python -u scripts/extract_activations.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark \
  --output-dir "$SCRATCH/physmon/activations_stage6/" \
  --tier 2 \
  --stage 6 \
  --seed 42

echo "=== PhysMon Stage 6 Extraction Complete (Qwen Tier 2) ==="
