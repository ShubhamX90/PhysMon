#!/bin/bash
# Download, verify, and record one registry model (CPU only).
#
# Submit with the model key exported and a unique job name, for example:
#   sbatch --parsable --job-name=physmon_dl_qwen_primary \
#     --export=ALL,MODEL_KEY=qwen_primary,DOWNLOAD_ARGS=--public-only \
#     slurm/templates/download_model.sh
# Use --public-only for non-gated repositories so no credentials are sent.
# The registry (docs/model_registry.yml) decides the repo id and target directory.
#SBATCH --job-name=physmon_download_model
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -euo pipefail

set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

# Ignore ~/.local user-site packages from other projects on this shared account.
export PYTHONNOUSERSITE=1
export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
export HF_HOME="$SCRATCH/physmon/hf_cache"
export HF_HUB_DISABLE_TELEMETRY=1
cd "$PHYSMON_ROOT"

echo "=== PhysMon model download ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "Model key: ${MODEL_KEY:?'ERROR: MODEL_KEY not set'}"
echo "Args:      ${DOWNLOAD_ARGS:-none}"
echo "Commit:    $(git rev-parse HEAD)"
echo "Python:    $(python --version 2>&1)"
python - <<'PY'
from importlib import metadata
for name in ("huggingface-hub", "transformers", "tokenizers", "safetensors", "torch"):
    print(f"{name:16s}", metadata.version(name))
PY
echo "Git status (short):"
git status --short || true
echo "=============================="

# shellcheck disable=SC2086
python -u scripts/download_model.py --model-key "$MODEL_KEY" ${DOWNLOAD_ARGS:-}

echo "=== PhysMon model download complete ==="
