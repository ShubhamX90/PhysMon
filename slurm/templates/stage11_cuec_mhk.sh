#!/bin/bash

#SBATCH --job-name=physmon_s11_cuec_mhk
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=4
#SBATCH --time=03:00:00
#SBATCH --mem=80G
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
set -u

export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
cd "$PHYSMON_ROOT"

BEST_LAYER=$(python - <<'PY'
import json, pathlib
summary = json.loads(pathlib.Path("results/stage11/science/cue_c_circuit/cuec_probe_sweep/summary_per_variant_sweep.json").read_text())
print(int(summary["best_layer"]))
PY
)

python - <<'PY'
import json, pathlib

out_dir = pathlib.Path("results/stage11/science/cue_c_circuit/rendered_merged")
out_dir.mkdir(parents=True, exist_ok=True)

source_paths = list(pathlib.Path("results/stage6/generated_full_benchmark").glob("CM_C_*.json"))
source_paths += list(pathlib.Path("results/stage10/benchmark_expansion/rendered").rglob("CM_C_*.json"))
for path in source_paths:
    payload = json.loads(path.read_text())
    (out_dir / path.name).write_text(json.dumps(payload, indent=2))

merged_jsonl = pathlib.Path("results/stage11/science/cue_c_circuit/cuec_behavioural_merged.jsonl")
with merged_jsonl.open("w", encoding="utf-8") as handle:
    for source in [
        pathlib.Path("results/stage6/behavioural_full_rerun/qwen_primary_20260616T091228Z.jsonl"),
        sorted(pathlib.Path("results/stage11/behavioural_expansion").glob("qwen_primary_*.jsonl"))[-1],
    ]:
        with source.open("r", encoding="utf-8") as source_handle:
            for line in source_handle:
                record = json.loads(line)
                if str(record.get("template_id", "")).startswith("CM_C_"):
                    handle.write(line)
PY

POSITIVE_FAMILIES=$(python - <<'PY'
import json, pathlib
payload = json.loads(pathlib.Path("results/stage11/science/cue_c_circuit/combined_cuec_positive_families.json").read_text())
print(" ".join(payload["positive_families"]))
PY
)

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage11/science/cue_c_circuit/rendered_merged/ \
  --patch-families ${POSITIVE_FAMILIES} \
  --patch-layers "$BEST_LAYER" \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --head-index 11 \
  --behavioural-jsonl results/stage11/science/cue_c_circuit/cuec_behavioural_merged.jsonl \
  --output-dir results/stage11/science/cue_c_circuit/h11_knockout/ \
  --stage 11 \
  --seed 42

python -u scripts/run_causal_patching.py \
  --model-role qwen_primary \
  --family-dir results/stage11/science/cue_c_circuit/rendered_merged/ \
  --patch-families ${POSITIVE_FAMILIES} \
  --patch-layers "$BEST_LAYER" \
  --patch-site resid_post_last_prompt \
  --patch-mode head_knockout \
  --multi-head-knockout 11 13 \
  --behavioural-jsonl results/stage11/science/cue_c_circuit/cuec_behavioural_merged.jsonl \
  --output-dir results/stage11/science/cue_c_circuit/h11_h13_knockout/ \
  --stage 11 \
  --seed 42
