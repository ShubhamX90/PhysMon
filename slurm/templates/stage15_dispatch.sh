#!/bin/bash
#SBATCH --job-name=physmon_s15_worker
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err
#
# Stage 15 generic GPU worker (pilot-job pattern). Submitted early by scripts/v2/s173_submit_workqueue.py submit-workers;
# when it starts it runs scripts/v2/s174_dispatch.py from its own immutable snapshot, which pulls registered runs from
# /scratch/pabitra/physmon/queue/ACTIVE_RUNS.json and executes each run's OWN frozen snapshot with that run's environment
# and spec hash. Resources (--partition, --gres, --cpus-per-task, --mem, --time) come from the submit helper.
#
# Required variables: DISPATCH_SNAPSHOT (this job's snapshot), DISPATCH_PYTHON (a python for the dispatcher; stdlib only),
# AUTHORIZATION_REF, TIME_BUDGET_S.

set -uo pipefail

for name in DISPATCH_SNAPSHOT DISPATCH_PYTHON AUTHORIZATION_REF TIME_BUDGET_S; do
    if [ -z "${!name:-}" ]; then
        echo "missing required variable $name" >&2
        exit 20
    fi
done
if [ ! -f "$DISPATCH_SNAPSHOT/scripts/v2/s174_dispatch.py" ]; then
    echo "snapshot $DISPATCH_SNAPSHOT has no dispatcher" >&2
    exit 21
fi

CACHE=/scratch/pabitra/physmon/cache
export PHYSMON_SCRATCH_ROOT=/scratch/pabitra/physmon
export PHYSMON_MODEL_ROOT=/scratch/pabitra/models
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
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

echo "=== physmon stage15 generic worker ==="
echo "date:       $(date -Is)"
echo "host:       $(hostname)"
echo "job:        ${SLURM_JOB_ID:-} partition=${SLURM_JOB_PARTITION:-} gpus=${SLURM_JOB_GPUS:-${CUDA_VISIBLE_DEVICES:-}}"
echo "dispatcher: $DISPATCH_SNAPSHOT ($(cat "$DISPATCH_SNAPSHOT/.physmon_git_commit" 2>/dev/null))"
echo "budget s:   $TIME_BUDGET_S"
echo "auth:       $AUTHORIZATION_REF"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader 2>&1 || true

cd "$DISPATCH_SNAPSHOT" || exit 23
"$DISPATCH_PYTHON" scripts/v2/s174_dispatch.py \
    --time-budget-s "$TIME_BUDGET_S" \
    --authorization-ref "$AUTHORIZATION_REF"
rc=$?
echo "=== exit $rc at $(date -Is) ==="
rm -rf "$TMPDIR"
exit $rc
