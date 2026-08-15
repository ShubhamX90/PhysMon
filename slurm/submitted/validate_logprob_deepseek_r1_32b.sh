#!/bin/bash
# Stage 3 brief Part C.2: REASONING_TUNED validation on 2xH200 via Hugging Face only.
# Base template: slurm/templates/h200_multi.sh
# IMPORTANT: run `make sync-up` before submission.

#SBATCH --job-name=physmon_ds_r1_validate
#SBATCH --partition=gpu_h200_8
#SBATCH --gres=gpu:nvidia_h200_nvl:2
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=90G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

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

echo "=== PhysMon DeepSeek Validation Start ==="
echo "Reminder: run 'make sync-up' from the Mac repo before submitting jobs."
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "========================================="

cd "$PHYSMON_ROOT"

python scripts/validate_logprob.py \
  --model-key deepseek_r1_32b \
  --model-role REASONING_TUNED \
  --model-family deepseek \
  --hook-backend baukit \
  --model-name deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
  --model-path /scratch/pabitra/rag-reason/models/DeepSeek-R1-Distill-Qwen-32B \
  --output-dir results/stage2/logprob_validation \
  --device cuda \
  --device-map auto \
  --prompt "A block of mass 2.0 kg is pushed along a frictionless surface by a net horizontal force of 10.0 N. What is the acceleration of the block?" \
  --altered-prompt "A block of mass 3.0 kg is pushed along a frictionless surface by a net horizontal force of 10.0 N. What is the acceleration of the block?" \
  --reference-answer "5.0 m/s²" \
  --expect-think-tags \
  --determinism-runs 3 \
  --seed 42

echo "=== PhysMon DeepSeek Validation Complete ==="
