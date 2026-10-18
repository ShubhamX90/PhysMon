#!/bin/bash

# ===========================================================================================================
# Stage 14.13 reasoning-allowed pilot: NOT SUBMITTED BY DEFAULT; each submission needs the user's acceptance of its exact
# command, a live preflight (squeue for the whole account, scontrol show node, per-user caps counted by hand; sbatch --test-only
# does not model QoS caps), and a clean, committed, pushed tree.
#
# Required environment at submission:
#   PLAN_DIR           directory with plan.json and job_manifest.jsonl (from scripts/v2/s147_pilot_plan.py)
#   AUTHORIZATION_REF  a non-empty reference to the user's authorization (the runner refuses without it)
# Needed only on a node without git: SUBMIT_COMMIT (the full SHA from the submission node).
# Optional: OUT_ROOT (default results/stage14/s152_reasoning_run), MODELS (default "qwen_primary llama_primary", run in
# sequence inside this one job: the per-user cap is one H100), MAX_NEW_TOKENS (default 512), TIME_BUDGET_S (per model; the
# runner stops cleanly and counts the jobs it did not run), MAX_JOBS (a short test first, for example 5).
# ===========================================================================================================

#SBATCH --job-name=physmon_s14_reasoning
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
OUT_ROOT="${OUT_ROOT:-results/stage14/s152_reasoning_run}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-512}"

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

echo "=== PhysMon Stage 14.13 reasoning pilot ==="
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

STATUS=0
for MODEL in ${MODELS}; do
  python -u scripts/v2/s152_reasoning_run.py \
    --plan-dir "${PLAN_DIR}" \
    --model-key "${MODEL}" \
    --authorization-ref "${AUTHORIZATION_REF}" \
    --attempt-id "attempt_${SLURM_JOB_ID:-nojob}_${MODEL}_reasoning" \
    --device cuda --dtype bfloat16 --out-root "${OUT_ROOT}" \
    --max-new-tokens "${MAX_NEW_TOKENS}" \
    ${TIME_BUDGET_S:+--time-budget-s "${TIME_BUDGET_S}"} \
    ${MAX_JOBS:+--max-jobs "${MAX_JOBS}"} || { RC=$?; echo "run for ${MODEL} exited with ${RC}" >&2; STATUS=${RC}; }
done

echo "=== PhysMon Stage 14.13 reasoning pilot finished (worst exit status ${STATUS}) ==="
exit "${STATUS}"
