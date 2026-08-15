#!/bin/bash
# Stage 8 attention head contribution analysis.

#SBATCH --job-name=physmon_stage8_attention
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
export HF_HOME="$SCRATCH/physmon/hf_cache"
export TRANSFORMERS_CACHE="$SCRATCH/physmon/hf_cache"
if [ -f "$PHYSMON_ROOT/.physmon_git_commit" ]; then
  export PHYSMON_GIT_COMMIT="$(cat "$PHYSMON_ROOT/.physmon_git_commit")"
fi

cd "$PHYSMON_ROOT"

python -u scripts/run_attention_analysis.py \
  --activation-dir "$SCRATCH/physmon/activations_stage6/qwen_primary/" \
  --layer 18 \
  --families CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 EL_B_002 CM_B_UM_033 \
             CM_B_UM_009 CM_B_UM_013 TH_B_UM_008 CM_B_004 CM_B_STD_013 \
  --output-dir results/stage8/attention/ \
  --stage 8
