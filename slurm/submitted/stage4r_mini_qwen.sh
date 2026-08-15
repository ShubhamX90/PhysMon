#!/bin/bash
# Stage 4 repair mini-validation for PRIMARY_DENSE A on A100.

#SBATCH --job-name=physmon_stage4r_mini_qwen
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=90G
#SBATCH --time=02:00:00
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

echo "Reminder: run 'make sync-up' from the Mac repo before submitting jobs."
cd "$PHYSMON_ROOT"

python scripts/run_behavioural.py \
  --model-role qwen_primary \
  --family-dir data/generated \
  --family-filter CM_A_001 CM_B_004 EL_A_002 \
  --output-dir results/stage4_repair/mini_validation \
  --device cuda \
  --max-new-tokens 512 \
  --seed 42
