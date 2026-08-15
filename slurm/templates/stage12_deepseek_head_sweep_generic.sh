#!/bin/bash

#SBATCH --job-name=physmon_s12_ds_sweep
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=2
#SBATCH --time=06:00:00
#SBATCH --mem=160G
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
cd "$PHYSMON_ROOT"

if [[ -z "${HEADS_GROUP:-}" ]]; then
  echo "HEADS_GROUP must be provided via --export=HEADS_GROUP=\"0 1 2 ...\"" >&2
  exit 1
fi

FAMILIES=$(python - <<'PY'
import json, pathlib
payload = json.loads(pathlib.Path("results/stage11/science/deepseek_single_heads/deepseek_valid_subset_summary.json").read_text())
print(" ".join(payload["valid_positive_families"]))
PY
)

for HEAD in ${HEADS_GROUP}; do
  python -u scripts/run_causal_patching.py \
    --model-role deepseek_reasoning \
    --family-dir results/stage6/generated_full_benchmark/ \
    --patch-families ${FAMILIES} \
    --patch-layers 42 43 44 45 \
    --patch-site resid_post_last_prompt \
    --patch-mode head_knockout \
    --head-index "$HEAD" \
    --behavioural-jsonl results/stage6/behavioural_deepseek/deepseek_reasoning_20260617T055830Z.jsonl \
    --output-dir "results/stage12/deepseek_full_head_sweep/head_${HEAD}/" \
    --stage 12 \
    --seed 42
done
