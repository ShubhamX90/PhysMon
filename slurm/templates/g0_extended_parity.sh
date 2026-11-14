#!/bin/bash
#SBATCH --job-name=physmon_g0_parity
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err
#
# G0 item 3: extended HF-versus-TransformerLens parity (scripts/v2/s185_extended_parity.py run) for qwen_primary, then
# llama_primary, on ONE GPU with 80 GB (H100 80GB, H200 or A100 80GB; not a 40 GB card). The submitter supplies --partition and
# --gres on the sbatch command line (e.g. --partition=gpu_h100_4 --gres=gpu:nvidia_h100_80gb_hbm3:1), after the live
# preflight. Protocol and pre-registered thresholds: docs/registry/v2/g0_extended_parity_protocol.md.
#
# The job runs from an immutable code snapshot of a pushed commit (e.g. the one made by
# scripts/v2/s173_submit_workqueue.py's make_snapshot under /scratch/pabitra/physmon/snapshots/<sha>), never from the live
# worktree. The snapshot must contain the frozen plans data/v2/g0_extended_parity/<model_key>/{plan.json,inputs.jsonl}.
#
# Required variables: SNAPSHOT (snapshot directory with .physmon_git_commit), AUTHORIZATION_REF (decision-log entry).
# Optional: ENV_PREFIX (default the frozen environment below), OUTPUT_DIR (default
# /scratch/pabitra/physmon/results/g0_extended_parity/<job id>; each model writes <model_key>.json there and refuses to
# overwrite), MODEL_KEYS (default "qwen_primary llama_primary").
#
# Resources (estimate): per model ~3-5 min SHA-256 of ~15-16 GB, up to ~30 min HF load from the network filesystem (job 399217
# measured 1877 s for Qwen, 1159 s for Llama), ~2 min TL build, ~5-15 min for 12 prompts x ~13 forward passes at up to ~4.4k
# tokens; ~1.5 h for both, 4 h requested. GPU memory ~16 GB HF + ~16 GB TL + < 20 GB activations and logits; the models are
# loaded one at a time, each in its own process, so memory is released between them. Host memory: HF and TL copies pass
# through host RAM while building (~35-50 GB peak).
#
# Exit code: 0 both PASS; 1 at least one model FAIL (results written; FAIL is a result, not a crash); other codes as in the
# script (2 refusal, 3 no GPU, 8 no commit, 11 model hash, 12 inputs) or 2x for a template problem. The second model runs
# even when the first FAILS.

set -uo pipefail

for name in SNAPSHOT AUTHORIZATION_REF; do
    if [ -z "${!name:-}" ]; then
        echo "missing required variable $name" >&2
        exit 20
    fi
done
ENV_PREFIX="${ENV_PREFIX:-/scratch/pabitra/physmon/envs/physmon-frozen-20261112}"
MODEL_KEYS="${MODEL_KEYS:-qwen_primary llama_primary}"
OUTPUT_DIR="${OUTPUT_DIR:-/scratch/pabitra/physmon/results/g0_extended_parity/${SLURM_JOB_ID:-local}}"
if [ ! -f "$SNAPSHOT/.physmon_git_commit" ] || [ ! -f "$SNAPSHOT/scripts/v2/s185_extended_parity.py" ]; then
    echo "snapshot $SNAPSHOT is incomplete" >&2
    exit 21
fi
for key in $MODEL_KEYS; do
    if [ ! -f "$SNAPSHOT/data/v2/g0_extended_parity/$key/plan.json" ]; then
        echo "snapshot $SNAPSHOT has no frozen plan for $key" >&2
        exit 21
    fi
done
if [ ! -x "$ENV_PREFIX/bin/python" ]; then
    echo "environment $ENV_PREFIX has no python" >&2
    exit 22
fi

CACHE=/scratch/pabitra/physmon/cache
export PHYSMON_SOURCE_COMMIT="$(cat "$SNAPSHOT/.physmon_git_commit")"
export PHYSMON_SCRATCH_ROOT=/scratch/pabitra/physmon
export PHYSMON_MODEL_ROOT=/scratch/pabitra/models
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$SNAPSHOT/src"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME="$CACHE/hf"
export DO_NOT_TRACK=1
export TRITON_CACHE_DIR="$CACHE/triton"
export TORCHINDUCTOR_CACHE_DIR="$CACHE/inductor"
export XDG_CACHE_HOME="$CACHE/xdg"
export CUDA_CACHE_PATH="$CACHE/nv"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export TMPDIR="/tmp/physmon_${SLURM_JOB_ID:-local}"  # node-local
mkdir -p "$HF_HOME" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR" "$XDG_CACHE_HOME" "$CUDA_CACHE_PATH" "$TMPDIR" "$OUTPUT_DIR"

echo "=== physmon G0 extended parity job ==="
echo "date:       $(date -Is)"
echo "host:       $(hostname)"
echo "job:        ${SLURM_JOB_ID:-} partition=${SLURM_JOB_PARTITION:-} gpus=${SLURM_JOB_GPUS:-${CUDA_VISIBLE_DEVICES:-}}"
echo "snapshot:   $SNAPSHOT commit=$PHYSMON_SOURCE_COMMIT"
echo "env:        $ENV_PREFIX ($("$ENV_PREFIX/bin/python" --version 2>&1))"
echo "models:     $MODEL_KEYS"
echo "output:     $OUTPUT_DIR"
echo "auth:       $AUTHORIZATION_REF"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader 2>&1 || true

cd "$SNAPSHOT" || exit 23
worst=0
for key in $MODEL_KEYS; do
    echo "=== $key start $(date -Is) ==="
    "$ENV_PREFIX/bin/python" scripts/v2/s185_extended_parity.py run \
        --model-key "$key" \
        --output-dir "$OUTPUT_DIR" \
        --device cuda \
        --dtype bfloat16
    rc=$?
    echo "=== $key exit $rc at $(date -Is) ==="
    if [ "$rc" -gt "$worst" ]; then
        worst=$rc
    fi
done
echo "=== exit $worst at $(date -Is) ==="
rm -rf "$TMPDIR"
exit $worst
