#!/bin/bash
#SBATCH --job-name=physmon_logprob_qwen
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon

export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT=/home/pabitra/PhysMons
export PYTHONPATH=$PHYSMON_ROOT/src:$PYTHONPATH
export HF_HOME=$SCRATCH/hf_cache
export TRANSFORMERS_CACHE=$SCRATCH/hf_cache

echo "Reminder: run make sync-up before manual submission."
cd "$PHYSMON_ROOT"

python scripts/validate_logprob.py \
  --model-key qwen_primary \
  --model-role PRIMARY_DENSE \
  --model-family qwen \
  --hook-backend transformer_lens \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --model-path /scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct \
  --output-dir results/stage2/logprob_validation \
  --device cuda \
  --seed 42
