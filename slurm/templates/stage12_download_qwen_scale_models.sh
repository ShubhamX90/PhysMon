#!/bin/bash

#SBATCH --job-name=physmon_s12_dl_qwen
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=08:00:00
#SBATCH --mem=32G
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

export HF_HOME=/scratch/pabitra/physmon/hf_cache
export TRANSFORMERS_CACHE=/scratch/pabitra/physmon/hf_cache
MODEL_ROOT=/scratch/pabitra/rag-reason/models
mkdir -p "$MODEL_ROOT"

python - <<'PY'
from huggingface_hub import snapshot_download
from pathlib import Path

model_root = Path("/scratch/pabitra/rag-reason/models")
targets = [
    ("Qwen/Qwen2.5-3B-Instruct", model_root / "Qwen2.5-3B-Instruct"),
    ("Qwen/Qwen2.5-14B-Instruct", model_root / "Qwen2.5-14B-Instruct"),
]

for repo_id, local_dir in targets:
    if local_dir.exists() and any(local_dir.iterdir()):
        print(f"[skip] {repo_id} already present at {local_dir}")
        continue
    print(f"[download] {repo_id} -> {local_dir}")
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    print(f"[done] {repo_id}")
PY
