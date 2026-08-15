#!/bin/bash
# Stage 8 cross-model transfer probe.

#SBATCH --job-name=physmon_stage8_xmodel
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
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
if [ -f "$PHYSMON_ROOT/.physmon_git_commit" ]; then
  export PHYSMON_GIT_COMMIT="$(cat "$PHYSMON_ROOT/.physmon_git_commit")"
fi

cd "$PHYSMON_ROOT"

python -u scripts/run_cross_model_transfer.py \
  --source-model qwen_primary \
  --target-model llama_primary \
  --source-activation-dir "$SCRATCH/physmon/activations_stage6/qwen_primary/" \
  --target-activation-dir "$SCRATCH/physmon/activations_stage6/llama_primary/" \
  --source-layer 18 \
  --target-layer 18 \
  --alignment-dims 256 \
  --output-dir results/stage8/cross_model/ \
  --stage 8
