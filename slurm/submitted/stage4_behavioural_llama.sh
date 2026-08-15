#!/bin/bash
# Stage 4 pilot behavioural sweep for PRIMARY_DENSE B.
# Base template: slurm/templates/a100_single.sh
# Submit only after the Stage 3 gate is PASS or CONDITIONAL per the brief.

#SBATCH --job-name=physmon_stage4_llama
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=90G
#SBATCH --time=04:00:00
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
  --model-role llama_primary \
  --family-dir data/generated \
  --output-dir results/stage4/behavioural \
  --device cuda \
  --max-new-tokens 32 \
  --seed 42
