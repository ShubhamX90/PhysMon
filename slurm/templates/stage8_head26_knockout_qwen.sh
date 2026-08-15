#!/bin/bash
# Stage 8 head-level causal knockout at layer-wise attention result hooks.

#SBATCH --job-name=physmon_stage8_head26_ko
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=80G
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
export HF_HOME="$SCRATCH/physmon/hf_cache"
export TRANSFORMERS_CACHE="$SCRATCH/physmon/hf_cache"
if [ -f "$PHYSMON_ROOT/.physmon_git_commit" ]; then
  export PHYSMON_GIT_COMMIT="$(cat "$PHYSMON_ROOT/.physmon_git_commit")"
fi

echo "=== PhysMon Stage 8 Head 26 Knockout Start ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "============================================="

cd "$PHYSMON_ROOT"

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage6/generated_full_benchmark/ \
  --patch-families CM_B_UM_059 CM_B_UM_032 CM_B_STD_006 CM_B_UM_055 \
                   CM_B_STD_013 CM_B_UM_052 CM_B_STD_010 CM_B_STD_011 \
                   CM_B_UM_033 CM_B_UM_009 CM_B_UM_013 TH_B_UM_006 \
                   CM_B_UM_006 TH_B_UM_008 EL_B_002 CM_B_UM_012 \
                   CM_B_004 CM_B_STD_015 CM_B_UM_001 CM_B_STD_014 \
  --patch-layers 4 8 12 14 15 16 17 18 19 20 22 25 \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --head-index 26 \
  --output-dir results/stage8/head26_knockout/ \
  --stage 8 \
  --seed 42

echo "=== PhysMon Stage 8 Head 26 Knockout Complete ==="
