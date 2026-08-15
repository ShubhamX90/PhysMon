#!/bin/bash
# Stage 6 variance probe on Qwen for Cue C only (CPU-only, qualitative).

#SBATCH --job-name=physmon_s6_qwen_var_cuec
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=02:00:00
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

echo "=== PhysMon Stage 6 Probe Start (Qwen variance, Cue C only) ==="
echo "Job ID: ${SLURM_JOB_ID:-unknown}"
echo "Node:   $(hostname)"
echo "========================================="

cd "$PHYSMON_ROOT"

python -u scripts/run_probing.py \
  --activation-dir "$SCRATCH/physmon/activations_stage6/qwen_primary/" \
  --site resid_post_last_prompt \
  --model-role qwen_primary \
  --target-measure slp_binary \
  --probe-type variance \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --cue-type frame_rendering \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --output-dir results/stage6/probing/variance_cue_c_only/ \
  --stage 6 \
  --seed 42

echo "=== PhysMon Stage 6 Probe Complete (Qwen variance, Cue C only) ==="
