#!/bin/bash
# Stage 6 surface baselines without Cue C families (CPU-only).

#SBATCH --job-name=physmon_s6_base_noc
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
if [ -f "$PHYSMON_ROOT/.physmon_git_commit" ]; then
  export PHYSMON_GIT_COMMIT="$(cat "$PHYSMON_ROOT/.physmon_git_commit")"
fi

echo "=== PhysMon Stage 6 Surface Baselines Start (no Cue C) ==="
echo "Job ID: ${SLURM_JOB_ID:-unknown}"
echo "Node:   $(hostname)"
echo "========================================="

cd "$PHYSMON_ROOT"

python -u scripts/run_baselines_surface.py \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --generated-dir results/stage6/generated_full_benchmark \
  --target-measure slp_binary \
  --threshold 0.5 \
  --exclude-ids CM_A_STD_018 CM_B_003 CM_B_UM_051 TH_B_UM_009 TH_B_UM_010 CM_C_001 CM_C_002 CM_C_003 CM_C_004 CM_C_005 \
  --output-dir results/stage6/baselines_no_cue_c/ \
  --stage 6 \
  --seed 42

echo "=== PhysMon Stage 6 Surface Baselines Complete (no Cue C) ==="
