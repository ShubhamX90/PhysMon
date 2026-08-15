#!/bin/bash
#SBATCH --job-name=physmon_stage5_probe_qwen_pca
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=90G
#SBATCH --time=08:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
export HF_HOME="$SCRATCH/physmon/hf_cache"
export TRANSFORMERS_CACHE="$SCRATCH/physmon/hf_cache"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

echo "=== PhysMon Stage 5 PCA Probing Start ==="
echo "Reminder: run 'make sync-up' from the Mac repo before submitting jobs."
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "========================================="

cd "$PHYSMON_ROOT"
mkdir -p results/stage5/probing

for PCA_DIMS in 10 20 50; do
  python scripts/run_probing.py \
    --activation-dir /scratch/pabitra/physmon/activations/qwen_primary \
    --site resid_post_last_prompt \
    --model-role qwen_primary \
    --target-measure slp_binary \
    --output-dir results/stage5/probing \
    --layer-filter 15 \
    --pca-dims "$PCA_DIMS" \
    --seed 42
done

echo "=== PhysMon Stage 5 PCA Probing Complete ==="
