#!/bin/bash
# Stage 8 DeepSeek within-model variance probe.

#SBATCH --job-name=physmon_stage8_probe_deepseek
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
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

echo "=== PhysMon Stage 8 DeepSeek Probe Start ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "=========================================="

cd "$PHYSMON_ROOT"

python -u scripts/run_probing.py \
  --activation-dir /scratch/pabitra/physmon/activations_stage6/deepseek_reasoning/ \
  --site resid_post_last_prompt \
  --model-role deepseek_reasoning \
  --target-measure slp_binary \
  --probe-type variance \
  --family-csv results/stage8/analysis_deepseek/deepseek_per_family.csv \
  --positive-families-file results/stage8/analysis_deepseek/stage8_positive_families_deepseek.json \
  --output-dir results/stage8/probing_deepseek/ \
  --stage 8 \
  --seed 42

echo "=== PhysMon Stage 8 DeepSeek Probe Complete ==="
