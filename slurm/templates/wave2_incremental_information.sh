#!/bin/bash

#SBATCH --job-name=physmon_w2_incinfo
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
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
cd "$PHYSMON_ROOT"

echo "=== PhysMon Wave 2 incremental information ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "Commit:    $(git rev-parse HEAD)"
# Report tracked-file dirtiness separately: `git status --porcelain` counts the
# expected untracked `activations` directory and would always say "yes",
# making the provenance field useless.
echo "Tracked dirty: $(if git diff --quiet HEAD; then echo no; else echo yes; fi)"
echo "Untracked:     $(git ls-files --others --exclude-standard | tr '\n' ' ')"
echo "Class:     exploratory_unfrozen (NOT confirmatory)"
echo "=============================================="

# No GPU, no model loading, no activation extraction: this reuses per-family
# artifacts already on disk. CPU partition is the smallest defensible request.
python -u scripts/run_combined_baseline.py \
  --outer-folds 5 --inner-folds 4 --seed 42 \
  --output-dir results/wave2/combined_baseline

python -u scripts/run_incremental_information.py \
  --outer-folds 5 --inner-folds 4 --seed 42 --bootstrap-reps 10000 \
  --output-dir results/wave2/incremental_information

echo "=== PhysMon Wave 2 Complete ==="
