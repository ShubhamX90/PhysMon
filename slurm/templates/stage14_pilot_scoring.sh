#!/bin/bash

# ===========================================================================================================
# Stage 14.7 pilot scoring: PREPARED, NOT AUTHORIZED, NOT SUBMITTED, NOT VERIFIED AGAINST THE LIVE CLUSTER.
#
# Do not submit this template without (1) the user's explicit authorization in the current task, recorded in
# AUTHORIZATION_REF, (2) a live preflight (sinfo, scontrol show node, sbatch --test-only, per-user caps; the
# partition, GRES, CPU, memory and walltime below are the values last observed on 2026-10-14 and may be stale),
# (3) a clean, committed, pushed tree, and (4) the blockers in docs/stage14/pilot_protocol.md section 8.
#
# Required environment at submission:
#   PLAN_DIR           directory with plan.json and job_manifest.jsonl (from scripts/v2/s147_pilot_plan.py)
#   AUTHORIZATION_REF  a non-empty reference to the user's authorization (the runner refuses without it)
# Needed only on a node without git: SUBMIT_COMMIT (the full SHA from the submission node).
# Optional: DTYPES (default "bfloat16"; for example "bfloat16 float32" repeats the run per dtype), MODELS (default "qwen_primary llama_primary", run in sequence inside this one job because the
# per-user cap observed on 2026-10-14 was one H100 GPU), MAX_JOBS (a measured throughput test first, for example 20).
#
# The walltime is a placeholder: no throughput has been measured. Set it from a measured test, within the caps.
# ===========================================================================================================

#SBATCH --job-name=physmon_s14_pilot
#SBATCH --partition=gpu_h100_4
#SBATCH --gres=gpu:nvidia_h100_80gb_hbm3:1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=90G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err

set -eo pipefail

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
export TRANSFORMERS_CACHE="$SCRATCH/physmon/hf_cache"

cd "$PHYSMON_ROOT"

: "${PLAN_DIR:?ERROR: PLAN_DIR is not set}"
: "${AUTHORIZATION_REF:?ERROR: AUTHORIZATION_REF is not set (this pilot is not authorized by default)}"
MODELS="${MODELS:-qwen_primary llama_primary}"
DTYPES="${DTYPES:-bfloat16}"

# Some compute nodes (gpunode6 on 2026-10-17, job 399511) have no git. Then the submitter's commit is used and the
# clean-tree and pushed checks, which only git can make, are reported as NOT CHECKED. The submitter must run them
# before sbatch (`git status --short`, `git fetch`, `git status -sb`) and pass SUBMIT_COMMIT=$(git rev-parse HEAD).
if command -v git >/dev/null 2>&1; then
  GIT_ON_NODE=yes
  COMMIT="$(git rev-parse HEAD)"
else
  GIT_ON_NODE=no
  COMMIT="${SUBMIT_COMMIT:-}"
  if [ -z "${COMMIT}" ]; then
    echo "ERROR: git is not installed on $(hostname) and SUBMIT_COMMIT is not set; refusing to run without provenance." >&2
    exit 8
  fi
fi
export PHYSMON_SOURCE_COMMIT="${COMMIT}"

echo "=== PhysMon Stage 14.7 pilot scoring ==="
echo "Job ID:    ${SLURM_JOB_ID:-unknown}"
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || true)"
echo "Commit:    ${COMMIT} (git on node: ${GIT_ON_NODE})"
if [ "${GIT_ON_NODE}" = yes ]; then
  echo "Tracked dirty: $(if git diff --quiet HEAD; then echo no; else echo yes; fi)"
  echo "Untracked:     $(git ls-files --others --exclude-standard | tr '\n' ' ')"
else
  echo "Tracked dirty: NOT CHECKED on node (no git); the submitter verified before sbatch"
fi
echo "Python:    $(python --version 2>&1)"
echo "Packages:  $(python -c 'import torch, transformers; print("torch", torch.__version__, "transformers", transformers.__version__)')"
echo "Plan:      ${PLAN_DIR}"
echo "Authorization: ${AUTHORIZATION_REF}"
echo "Class:     exploratory (NOT confirmatory); data role EXPLORATION"
echo "========================================="

# A serious run starts from a clean, committed, pushed tree.
if [ "${GIT_ON_NODE}" = yes ]; then
  if ! git diff --quiet HEAD; then
    echo "ERROR: tracked files are modified; commit before running." >&2
    exit 6
  fi
  AHEAD="$(git rev-list --left-right --count HEAD...@{upstream} | cut -f1)"
  if [ "${AHEAD}" != "0" ]; then
    echo "ERROR: HEAD is ahead of its upstream by ${AHEAD} commit(s); push before running." >&2
    exit 7
  fi
fi

for MODEL in ${MODELS}; do
  for DTYPE in ${DTYPES}; do
    python -u scripts/v2/s147_pilot_run.py \
      --plan-dir "${PLAN_DIR}" \
      --model-key "${MODEL}" \
      --authorization-ref "${AUTHORIZATION_REF}" \
      --attempt-id "attempt_${SLURM_JOB_ID:-nojob}_${MODEL}_${DTYPE}" \
      --device cuda --dtype "${DTYPE}" \
      ${MAX_JOBS:+--max-jobs "${MAX_JOBS}"}
  done
done

echo "=== PhysMon Stage 14.7 pilot scoring complete ==="
