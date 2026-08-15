#!/bin/bash
# Stage 8 Qwen <-> DeepSeek cross-model transfer.

#SBATCH --job-name=physmon_stage8_xmodel_ds
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
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
if [ -f "$PHYSMON_ROOT/.physmon_git_commit" ]; then
  export PHYSMON_GIT_COMMIT="$(cat "$PHYSMON_ROOT/.physmon_git_commit")"
fi

echo "=== PhysMon Stage 8 Qwen-DeepSeek Transfer Start ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "==================================================="

cd "$PHYSMON_ROOT"

python -u scripts/run_cross_model_transfer.py \
  --source-model qwen_primary \
  --target-model deepseek_reasoning \
  --source-activation-dir /scratch/pabitra/physmon/activations_stage6/qwen_primary/ \
  --target-activation-dir /scratch/pabitra/physmon/activations_stage6/deepseek_reasoning/ \
  --source-positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --target-positive-families-file results/stage8/analysis_deepseek/stage8_positive_families_deepseek.json \
  --source-layer 18 \
  --target-layer 41 \
  --output-dir results/stage8/cross_model_deepseek/ \
  --stage 8 \
  --seed 42

echo "=== PhysMon Stage 8 Qwen-DeepSeek Transfer Complete ==="
