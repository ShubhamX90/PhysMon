#!/bin/bash
# Stage 9 correctness residualisation: regress out correctness direction at layer 18.

#SBATCH --job-name=physmon_s9_corr_resid
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:30:00
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

python -u scripts/run_correctness_residualisation.py \
  --activation-manifest "$SCRATCH/physmon/activations_stage6/qwen_primary/manifest.json" \
  --site resid_post_last_prompt \
  --layer 18 \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --behavioural-jsonl results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl \
  --correctness-threshold 0.75 \
  --output-dir results/stage9/correctness_residualisation/ \
  --stage 9 \
  --seed 42
