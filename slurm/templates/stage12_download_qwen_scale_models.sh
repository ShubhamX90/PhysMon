#!/bin/bash
# Download the Qwen2.5 scale follow-up models (3B and 14B) via the registry-driven,
# hash-verified downloader. Targets come from docs/model_registry.yml
# (${PHYSMON_MODEL_ROOT}, default /scratch/pabitra/models). Both repositories are public.
# The original version of this script used huggingface_hub arguments that no longer
# exist in hub 1.x; see slurm/templates/download_model.sh for the general template.
#SBATCH --job-name=physmon_s12_dl_qwen
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=08:00:00
#SBATCH --mem=32G
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -euo pipefail

set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

export PYTHONNOUSERSITE=1
export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
export HF_HOME="$SCRATCH/physmon/hf_cache"
export HF_HUB_DISABLE_TELEMETRY=1
cd "$PHYSMON_ROOT"

echo "Commit: $(git rev-parse HEAD)"
git status --short || true

python -u scripts/download_model.py --model-key qwen_3b --public-only
python -u scripts/download_model.py --model-key qwen_14b --public-only
