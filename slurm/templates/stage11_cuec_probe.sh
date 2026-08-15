#!/bin/bash

#SBATCH --job-name=physmon_s11_cuec_probe
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=02:30:00
#SBATCH --mem=48G
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

python - <<'PY'
import csv, json, pathlib

expansion_rows = list(csv.DictReader(open("results/stage11/behavioural_expansion/per_family_summary.csv", "r", encoding="utf-8")))
valid_new_cuec = [
    row["template_id"]
    for row in expansion_rows
    if row["template_id"].startswith("CM_C_") and float(row["qwen_parse_rate_family"]) >= 0.5
]
new_cuec_positive = [
    row["template_id"]
    for row in expansion_rows
    if row["template_id"] in valid_new_cuec and float(row["qwen_S_lp"]) >= 0.5
]
old_cuec_positive = [f"CM_C_{idx:03d}" for idx in range(1, 6)]
out_dir = pathlib.Path("results/stage11/science/cue_c_circuit")
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "valid_new_cuec_families.json").write_text(
    json.dumps({"families": valid_new_cuec}, indent=2)
)
(out_dir / "expansion_cuec_positive_families.json").write_text(
    json.dumps({"threshold": 0.5, "positive_families": new_cuec_positive}, indent=2)
)
(out_dir / "combined_cuec_positive_families.json").write_text(
    json.dumps({"threshold": 0.5, "positive_families": old_cuec_positive + new_cuec_positive}, indent=2)
)
PY

VALID_NEW_CUEC=$(python - <<'PY'
import json, pathlib
payload = json.loads(pathlib.Path("results/stage11/science/cue_c_circuit/valid_new_cuec_families.json").read_text())
print(" ".join(payload["families"]))
PY
)

PYTHONPATH=src python -u scripts/build_activation_manifest_subset.py \
  --input-manifests "$SCRATCH/physmon/activations_stage11_expansion/qwen_primary/manifest.json" \
  --family-ids ${VALID_NEW_CUEC} \
  --site resid_post_last_prompt \
  --output-manifest results/stage11/science/cue_c_circuit/expansion_cuec_manifest.json

PYTHONPATH=src python -u scripts/build_activation_manifest_subset.py \
  --input-manifests "$SCRATCH/physmon/activations_stage6/qwen_primary/manifest.json" "$SCRATCH/physmon/activations_stage11_expansion/qwen_primary/manifest.json" \
  --family-ids CM_C_001 CM_C_002 CM_C_003 CM_C_004 CM_C_005 ${VALID_NEW_CUEC} \
  --site resid_post_last_prompt \
  --output-manifest results/stage11/science/cue_c_circuit/combined_cuec_manifest.json

PYTHONPATH=src python -u scripts/run_trained_per_variant_probe.py \
  --source-manifest "$SCRATCH/physmon/activations_stage6/qwen_primary/manifest.json" \
  --target-manifest results/stage11/science/cue_c_circuit/expansion_cuec_manifest.json \
  --site resid_post_last_prompt \
  --layer 16 \
  --source-positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --target-positive-families-file results/stage11/science/cue_c_circuit/expansion_cuec_positive_families.json \
  --output-dir results/stage11/science/cue_c_circuit/heldout_inference/

PYTHONPATH=src python -u scripts/run_per_variant_probe_sweep.py \
  --activation-manifest results/stage11/science/cue_c_circuit/combined_cuec_manifest.json \
  --site resid_post_last_prompt \
  --positive-families-file results/stage11/science/cue_c_circuit/combined_cuec_positive_families.json \
  --output-dir results/stage11/science/cue_c_circuit/cuec_probe_sweep/ \
  --stage 11 \
  --seed 42
