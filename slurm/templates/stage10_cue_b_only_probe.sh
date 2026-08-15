#!/bin/bash

#SBATCH --job-name=physmon_s10_cueb_probe
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
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

python -u scripts/run_probing.py \
  --activation-dir "$SCRATCH/physmon/activations_stage6/qwen_primary/" \
  --site resid_post_last_prompt \
  --model-role qwen_primary \
  --target-measure slp_binary \
  --probe-type mean \
  --cue-type nongoverning_distractor \
  --positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --exclude-ids CM_A_STD_018 CM_B_003 CM_B_UM_051 TH_B_UM_009 TH_B_UM_010 \
  --family-csv results/stage6/analysis_d2/stage6_d1_per_family.csv \
  --output-dir results/stage10/cue_b_only_probe/ \
  --stage 10 \
  --seed 42
