#!/bin/bash
#SBATCH --job-name=physmon_s15_wq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err
#
# Stage 15 work-queue worker (scripts/v2/s170_sampled_run.py work). Submitted by scripts/v2/s173_submit_workqueue.py, which
# supplies --partition, --gres, --cpus-per-task, --mem, --time and the variables below. The same job may be submitted to several
# partitions: shards are claimed atomically from /scratch/pabitra/physmon/queue/$RUN_ID, so a late duplicate finds nothing to do
# and exits within seconds. The job runs from an immutable code snapshot of a pushed commit, never from the live worktree.
#
# Required variables: RUN_ID, SNAPSHOT (snapshot directory), ENV_PREFIX (conda environment prefix), SPEC_SHA256 (sha256 of
# the committed spec.json), AUTHORIZATION_REF, TIME_BUDGET_S (seconds of work before the worker stops claiming shards).
# Optional: ALLOC_CONF (PYTORCH_CUDA_ALLOC_CONF for the Hugging Face backend; leave empty for vLLM).

set -uo pipefail

for name in RUN_ID SNAPSHOT ENV_PREFIX SPEC_SHA256 AUTHORIZATION_REF TIME_BUDGET_S; do
    if [ -z "${!name:-}" ]; then
        echo "missing required variable $name" >&2
        exit 20
    fi
done
if [ ! -f "$SNAPSHOT/.physmon_git_commit" ] || [ ! -f "$SNAPSHOT/scripts/v2/s170_sampled_run.py" ]; then
    echo "snapshot $SNAPSHOT is incomplete" >&2
    exit 21
fi
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
export VLLM_CACHE_ROOT="$CACHE/vllm"
export VLLM_NO_USAGE_STATS=1
export DO_NOT_TRACK=1
export TRITON_CACHE_DIR="$CACHE/triton"
export TORCHINDUCTOR_CACHE_DIR="$CACHE/inductor"
export XDG_CACHE_HOME="$CACHE/xdg"
export FLASHINFER_WORKSPACE_BASE="$CACHE/flashinfer"
export CUDA_CACHE_PATH="$CACHE/nv"
# vLLM 0.33 defaults to the FlashInfer sampler, which JIT-compiles with whatever nvcc it finds (CUDA 12.3 on these nodes,
# against torch built for CUDA 13); the PyTorch sampler needs no compilation.
export VLLM_USE_FLASHINFER_SAMPLER=0
export TMPDIR="/tmp/physmon_${SLURM_JOB_ID:-local}"  # node-local: short socket paths, no Lustre leak on a walltime kill
mkdir -p "$HF_HOME" "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR" "$XDG_CACHE_HOME" "$FLASHINFER_WORKSPACE_BASE" "$CUDA_CACHE_PATH" "$TMPDIR"
if [ -n "${ALLOC_CONF:-}" ]; then
    export PYTORCH_CUDA_ALLOC_CONF="$ALLOC_CONF"
fi

echo "=== physmon stage15 work-queue job ==="
echo "date:       $(date -Is)"
echo "host:       $(hostname)"
echo "job:        ${SLURM_JOB_ID:-} partition=${SLURM_JOB_PARTITION:-} gpus=${SLURM_JOB_GPUS:-${CUDA_VISIBLE_DEVICES:-}}"
echo "run:        $RUN_ID"
echo "snapshot:   $SNAPSHOT commit=$PHYSMON_SOURCE_COMMIT"
echo "env:        $ENV_PREFIX ($("$ENV_PREFIX/bin/python" --version 2>&1))"
echo "spec sha:   $SPEC_SHA256"
echo "budget s:   $TIME_BUDGET_S"
echo "auth:       $AUTHORIZATION_REF"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader 2>&1 || true

cd "$SNAPSHOT" || exit 23
"$ENV_PREFIX/bin/python" scripts/v2/s170_sampled_run.py work \
    --run-id "$RUN_ID" \
    --authorization-ref "$AUTHORIZATION_REF" \
    --expect-spec-sha256 "$SPEC_SHA256" \
    --time-budget-s "$TIME_BUDGET_S"
rc=$?
echo "=== exit $rc at $(date -Is) ==="
rm -rf "$TMPDIR"
exit $rc
