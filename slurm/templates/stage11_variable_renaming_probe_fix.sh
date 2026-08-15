#!/bin/bash

#SBATCH --job-name=physmon_s11_varprobe_fix
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --mem=32G
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

rows = list(
    csv.DictReader(
        open(
            "results/stage11/variable_renaming/behavioural/analysis/per_family_summary.csv",
            "r",
            encoding="utf-8",
        )
    )
)
positives = []
for row in rows:
    slp = float(row.get("qwen_S_lp", "0") or "0")
    parse_rate = float(row.get("qwen_parse_rate_family", "1") or "1")
    if parse_rate >= 0.5 and slp >= 0.5:
        positives.append(row["template_id"])

payload = {
    "threshold": 0.5,
    "positive_families": positives,
    "source_csv": "results/stage11/variable_renaming/behavioural/analysis/per_family_summary.csv",
}
path = pathlib.Path("results/stage11/variable_renaming/renamed_positive_families.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2))
PY

PYTHONPATH=src python -u scripts/run_trained_per_variant_probe.py \
  --source-manifest "$SCRATCH/physmon/activations_stage6/qwen_primary/manifest.json" \
  --target-manifest "$SCRATCH/physmon/activations_stage11_variable_renaming/qwen_primary/manifest.json" \
  --site resid_post_last_prompt \
  --layer 16 \
  --source-positive-families-file results/stage6/analysis_d2/stage6_positive_families.json \
  --target-positive-families-file results/stage11/variable_renaming/renamed_positive_families.json \
  --output-dir results/stage11/science/variable_renaming/probe_inference/
