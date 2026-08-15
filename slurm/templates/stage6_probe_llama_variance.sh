#!/bin/bash
# Stage 6 last-prompt variance probe on Llama with Llama-specific labels (CPU-only).

#SBATCH --job-name=physmon_s6_llama_var
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

echo "=== PhysMon Stage 6 Probe Start (Llama variance) ==="
echo "Job ID: ${SLURM_JOB_ID:-unknown}"
echo "Node:   $(hostname)"
echo "========================================="

cd "$PHYSMON_ROOT"

python -u scripts/run_probing.py \
  --activation-dir "$SCRATCH/physmon/activations_stage6/llama_primary/" \
  --site resid_post_last_prompt \
  --model-role llama_primary \
  --target-measure slp_binary \
  --probe-type variance \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families_llama.json \
  --exclude-ids CM_A_STD_018 CM_B_003 CM_B_UM_051 TH_B_UM_009 TH_B_UM_010 \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --output-dir results/stage6/probing/llama_variance/ \
  --stage 6 \
  --seed 42

echo "=== PhysMon Stage 6 Probe Complete (Llama variance) ==="
