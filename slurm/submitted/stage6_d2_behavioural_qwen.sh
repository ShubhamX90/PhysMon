#!/bin/bash
# Stage 6 Phase D2 full-benchmark behavioural sweep on Qwen.

#SBATCH --job-name=physmon_stage6_d2_qwen
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=90G
#SBATCH --time=08:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/stage6_d2_qwen_%j.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/stage6_d2_qwen_%j.err

set -eo pipefail
set -x

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
mkdir -p results/stage6/behavioural_full
echo "pwd=$(pwd)"
which python
python --version
echo "starting_run_behavioural_qwen_stage6_d2"

python -u scripts/run_behavioural.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark \
  --output-dir results/stage6/behavioural_full \
  --device cuda \
  --max-new-tokens 128 \
  --seed 42
