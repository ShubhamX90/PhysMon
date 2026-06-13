#!/bin/bash
#SBATCH --job-name=physmon_job
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

echo "=== PhysMon Job Start ==="
echo "Reminder: run 'make sync-up' from the Mac repo before submitting jobs."
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "Script:    ${SCRIPT:?'ERROR: SCRIPT variable not set'}"
echo "Args:      ${ARGS:-none}"
echo "========================================="

cd "$PHYSMON_ROOT"

python "$SCRIPT" ${ARGS:-}

echo "=== PhysMon Job Complete ==="
