# Slurm Operations for PhysMon

Use this reference only when the current task explicitly authorizes job
execution. Commands are written for a session running on Sharanga itself (Claude
Code via Remote SSH); run them directly. If you ever work from a machine that is
not Sharanga, prefix each with `ssh sharanga '...'`. A scientific brief can
prohibit jobs even if the account has idle GPU capacity. Never submit, alter,
hold, release, or cancel a job merely to make the queue look tidy.

## Inspection ladder

Use the narrowest read-only command that answers the question.

```bash
# Cluster and capacity
sinfo -h -o "%P|%a|%l|%D|%G"
sinfo -N -h -o "%N|%P|%T|%c|%m|%G"
scontrol show partition gpu_a100_8
scontrol show partition gpu_h100_4
scontrol show partition gpu_h200_8

# Shared-account policy and current queue
sacctmgr -n -P show assoc user=pabitra format=User,Account,Partition,QOS,MaxJobs,MaxSubmit,MaxTRESPerJob
sacctmgr -n -P show qos format=Name,MaxWall,MaxTRESPerUser,MaxTRESPerJob,MaxJobsPU,MaxSubmitPU,MaxTRESPU,GrpTRES
sshare -u pabitra -l
squeue -u pabitra -o "%i|%u|%T|%P|%j|%M|%l|%D|%R"

# A selected job
scontrol show job JOB_ID
squeue -j JOB_ID -o "%i|%u|%T|%P|%j|%M|%l|%R"
sacct -X -j JOB_ID -o JobIDRaw,JobName,Partition,State,Elapsed,Start,End,AllocTRES,ExitCode,MaxRSS
```

For a pending job, `%R` and `scontrol show job` are the source of truth. Common
reasons include `Resources`, `Priority`, `QOSMax*`, `AssocMax*`, `ReqNodeNotAvail`,
and dependency waits. Do not respond to `Priority` by randomly changing QoS or
increasing resources; the audited scheduler used fairshare/age multifactor
priority and did not assign QoS priority weight.

## Resource request anatomy

Specify all resources explicitly in a submitted template:

```bash
#SBATCH --job-name=physmon_<task>_<attempt>
#SBATCH --partition=gpu_a100_8
#SBATCH --gres=gpu:nvidia_a100-sxm4-80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=90G
#SBATCH --time=12:00:00
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%j_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%j_%x.err
```

Use the live `sinfo` GRES text exactly. The current generic templates use
A100/H100/H200 GRES names as documented in the environment reference. Do not
combine `--mem` with `--mem-per-cpu` or `--mem-per-gpu` in one request. Avoid
requesting a whole node unless that is truly required. Request a walltime with
enough diagnostic margin, but keep within the live partition maximum and
account QoS maximum.

The request must fit **three** constraints: node capacity, partition policy,
and the shared account's association/QoS. For example, H100's observed
two-GPU allowance did not make two 8-CPU jobs valid, because the same shared
account allowed only 12 CPUs. Check aggregate current jobs before submitting a
second one.

## CPU, GPU, and array decisions

| Work | Default choice | Escalate only when |
|---|---|---|
| CSV/JSON analysis, integrity audits, plotting | `compute` | memory or parallelism is measured to exceed ordinary nodes |
| cached activation analysis that does not load a model | `compute` | code truly needs CUDA operations |
| model inference / hooks / patching | smallest compatible GPU request | model/backend profile proves a larger allocation is needed |
| long high-memory CPU preprocessing | `big_compute*` | task is approved and resource requirement is documented |
| independent homogeneous shards | array | each task has distinct inputs, logs, outputs, and an aggregation plan |

Slurm's observed maximum array size was 1001. Arrays multiply failure modes:
give each task `%A_%a` logs and an attempt-specific output directory, record
the task-to-family mapping, and validate every shard before aggregate summary.

```bash
# Example only: use after approved panel/mapping creation.
#SBATCH --array=0-19%2
#SBATCH --output=/scratch/pabitra/physmon/slurm_logs/%A_%a_%x.out
#SBATCH --error=/scratch/pabitra/physmon/slurm_logs/%A_%a_%x.err
```

The `%2` cap must also respect account job/GPU limits. It does not make a
panel scientifically independent or authorize chained follow-up experiments.

## Template and runtime contract

Start from a current generic template in `slurm/templates/`, not an old copy in
`slurm/submitted/` or an historical Stage directory. Submitted scripts are
provenance artifacts; modifying them destroys the record.

Every template should establish the project environment, then emit a compact
runtime manifest before launching the science script:

```bash
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
export HF_HOME="$SCRATCH/physmon/hf_cache"
export TRANSFORMERS_CACHE="$SCRATCH/physmon/hf_cache"
cd "$PHYSMON_ROOT"

git rev-parse HEAD
git status --short
hostname
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || true
python --version
```

Use `set -euo pipefail` for new templates. Existing templates using only
`set -eo pipefail` are historical context, not a reason to omit unset-variable
checks in a new job. Make input/output directories before writing, and reject
an existing nonempty attempt directory unless the task explicitly supports a
restart.

## Submission, capture, and dependencies

After the Git preflight (clean or explicitly labeled tree, known HEAD SHA) and explicit scientific authorization:

```bash
cd ~/PhysMons && sbatch --parsable slurm/templates/<template>.sh
```

Capture the returned job ID before doing anything else. Create a run manifest
that joins it to SHA, template, command, model role, input panel/hash, expected
rows, and output/log roots.

`srun` is useful for an approved, bounded interactive allocation or debugging
session, but it consumes scheduler resources and must use explicit partition,
time, CPU, memory, and GRES. It is not a way to bypass batch provenance.

```bash
# Only with explicit approval for an interactive diagnostic. `--pty` needs a
# real terminal; from an agent shell prefer a short batch job or `srun ... <cmd>`.
srun --partition=compute --cpus-per-task=4 --mem=16G --time=00:30:00 --pty bash -l
```

Use `--dependency=afterok:JOB_ID` only for mechanically dependent work whose
scientific decision does not rely on interpreting the first result. It must
not automate a causal follow-up, threshold decision, or result-dependent
experiment. `afterok` verifies exit status, not artifact integrity.

## Live monitoring and terminal harvest

```bash
# Queue state and pending cause
squeue -j JOB_ID -o "%i|%T|%P|%j|%M|%l|%R"
scontrol show job JOB_ID

# For running jobs where enabled
sstat -j JOB_ID.batch --format=JobID,AveCPU,AveRSS,MaxRSS

# Read logs without mutating them
tail -n 160 /scratch/pabitra/physmon/slurm_logs/JOBID_NAME.out
tail -n 160 /scratch/pabitra/physmon/slurm_logs/JOBID_NAME.err

# Terminal accounting
sacct -X -j JOB_ID -o JobIDRaw,JobName,Partition,State,Elapsed,Start,End,AllocTRES,ExitCode,MaxRSS
```

Interpret terminal states carefully:

| State | Meaning for science | Required response |
|---|---|---|
| `COMPLETED` | scheduler process exited zero | verify raw row counts, panel, summary, logs, and source SHA |
| `FAILED` | process failed | preserve and diagnose; new attempt only after approval |
| `OUT_OF_MEMORY` | allocation inadequate or code leaked memory | preserve MaxRSS/logs; do not erase partials |
| `TIMEOUT` | time limit reached | preserve partials; only resume if design supports it |
| `CANCELLED` | user/admin cancellation | record initiator/reason and retain all logs |
| `PREEMPTED` / node failure | infrastructure interruption | preserve attempt; classify separately from scientific null |

A zero raw-row result, a missing panel, or a defaulted aggregate is neither
success nor a measured zero. Its status is failed, partial, or unresolved.

## Failure diagnosis map

| Observation | Check | Safe response |
|---|---|---|
| `PD (QOSMax...)` or `AssocMax...` | association, QoS, aggregate current TRES | wait or reduce within approved design; do not resubmit blindly |
| `PD (Resources)` | requested GRES/memory versus `sinfo` and queue | wait; do not change partition simply because it is shorter |
| immediate Python/import error | stderr, `which python`, package snapshot, deployed SHA | repair locally, test, make a new attempt |
| CUDA OOM | stderr, batch size, `sacct MaxRSS`, GPU memory logs | record failure, then obtain approval for any changed allocation/config |
| output path absent | stdout/stderr, parent path, script `cd`, permissions | preserve failed attempt and correct path handling |
| panel unexpectedly empty | panel manifest, eligibility filters, parser diagnostics | report empty panel; never emit a zero effect |
| source differs from what the job should have run | job stdout SHA/`git status` versus current `git log`; files edited after submission | mark provenance unresolved; do not retrofit metadata |

## Holds, cancellation, and ownership

`scontrol hold`, `scontrol release`, and `scancel` change shared state. Use
them only for a verified job owned by the current task and only when the action
is authorized. Confirm the job identity immediately before mutation:

```bash
squeue -j JOB_ID -o "%i|%u|%j|%T|%P"
scancel JOB_ID
```

Editing the worktree while a job is pending or running can change what it
executes; see "Editing While Jobs Are Live" in `SKILL.md`.

Never cancel by job-name glob and never touch a colleague's job. Record why a
job was held, released, or cancelled in the handoff.
