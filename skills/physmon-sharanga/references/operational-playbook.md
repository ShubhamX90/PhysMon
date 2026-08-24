# PhysMon Shared Operations Playbook

This is the end-to-end protocol for a person or coding agent taking a PhysMon
shift. It applies to the shared `pabitra` Sharanga account and avoids treating
the remote clone as a second collaborative editing surface.

## Roles and authority

| System | What belongs there | What must not be inferred |
|---|---|---|
| Local clone | edits, tests, review, Git commits | that it is current without fetching its upstream |
| GitHub upstream | shared versioned history | that large scratch artifacts exist or are valid |
| `~/PhysMons` | deployed source snapshot for a job | that its uncommitted files are disposable |
| `/scratch/pabitra/physmon` | job logs, models, activations, checkpoints | that contents are Git-tracked or safe to overwrite |
| Slurm accounting/logs | runtime allocation and terminal state | that a `COMPLETED` job produced valid science |

One shift owns one bounded task. The shift may prepare code, deploy it, submit
an approved job, harvest it, and write a handoff. It must not silently take
over another shift's in-progress job, remote edits, result tree, or lease.

## Shift start: read-only reality check

Run this before editing, syncing, or scheduling:

```bash
git status --short
git fetch origin
git branch --show-current
git rev-parse HEAD
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git rev-list --left-right --count HEAD...@{upstream}
make remote-preflight
```

Read the result as follows:

- local dirty files are an ownership question, not debris to remove;
- `ahead` or `behind` relative to the configured upstream must be resolved
  before a shared handoff;
- remote status must contain no unexplained changes; `?? activations` is a
  historically observed exception and still must not be removed;
- an empty personal queue does not prove the shared account is idle: inspect
  the whole current queue and consult the prior handoff if one exists.

Before altering a result root, search it and its job logs. A retry always gets
a new attempt directory. Historical, partial, corrected, and failed records
are evidence and remain preserved.

## Coordinated deployment protocol

The remote deployment lease serializes deployment, not scientific ownership.
It is stored remotely under `.physmon_ops/`, which sync excludes. Never break
an existing lease yourself: inspect it, contact its recorded owner, and obtain
an explicit handoff before any recovery action.

### 1. Prepare an immutable source snapshot locally

```bash
git status --short
git add <intended-files>
git commit -m "<bounded change>"
git push
git rev-parse HEAD
```

Use a named branch or reviewed merge according to team policy. Do not deploy
uncommitted scientific code. If a task genuinely needs an uncommitted
prototype, it is exploratory and its provenance record must say so.

### 2. Acquire and inspect the remote lease

Use the committed helper only after the same commit is deployed or execute the
already-present helper on Sharanga. Capture the returned token in the handoff
record; it is required for release.

```bash
ssh sharanga 'cd ~/PhysMons && scripts/ops/physmon_remote_lease.sh inspect'
ssh sharanga 'cd ~/PhysMons && scripts/ops/physmon_remote_lease.sh acquire \
  --task "short-task-name" --commit "FULL_LOCAL_SHA"'
```

If the helper has not reached the remote repository yet, do not work around it
by creating a competing lock manually. Coordinate the first deployment with
the person who owns the remote tree.

### 3. Plan, deploy, then verify

```bash
make remote-preflight
make sync-plan-up
make sync-up
python scripts/ops/remote_preflight.py --strict --expect-aligned
```

`sync-plan-up` is local-to-remote. `sync-plan-down` is remote-to-local. Both
are dry runs. `sync-up` and `sync-down` preserve remote/local-only files by
default; `sync-plan-prune` merely displays the effect of a dangerous
local-to-remote delete and must never be used as an execution shortcut.

After the strict check, record all of: local SHA, remote `HEAD`, and remote
`.physmon_ops/deployment_commit`. They must identify the same deployed source. Release
the deployment lease only after source deployment and any approved submission
are recorded. Do not deploy a new source snapshot while an existing job may
still read source files from the shared worktree.

### 4. Submit an approved job with durable provenance

Create a task-specific template or an immutable copy of the template in the
repository. It must declare the partition, GRES, CPU/memory/walltime,
environment, model registry role, input manifest, output root, and log root.
Use unique `--job-name`, `%j`-keyed log filenames, and an output directory
containing an attempt identifier.

```bash
ssh sharanga 'cd ~/PhysMons && sbatch --parsable slurm/templates/<template>.sh'
```

`--parsable` returns a job ID suitable for a manifest. Record the exact
template path, deployed SHA, job ID, model role/path resolution, input panel
hash, expected rows, and intended output/log paths before monitoring it.

Do not use a Slurm dependency as scientific approval. `afterok` only says a
previous batch step exited zero; a human or explicitly approved data gate must
inspect its raw output before follow-up science runs.

### 5. Monitor, harvest, and release

For a submitted job, use the live and terminal-accounting views:

```bash
ssh sharanga 'squeue -j JOB_ID -o "%i|%u|%T|%P|%j|%M|%l|%R"'
ssh sharanga 'scontrol show job JOB_ID'
ssh sharanga 'sacct -X -j JOB_ID -o JobIDRaw,JobName,Partition,State,Elapsed,AllocTRES,ExitCode,MaxRSS'
```

Inspect stdout, stderr, raw records, expected panel rows, and summary values.
`COMPLETED` is only scheduler success. Missing rows, an empty output, a
defaulted mean, wrong panel, or unknown source SHA makes the scientific result
partial, failed, or provenance-unresolved.

When source and job handoff are complete:

```bash
ssh sharanga 'cd ~/PhysMons && scripts/ops/physmon_remote_lease.sh release --token "LEASE_TOKEN"'
make sync-plan-down
make sync-down
```

Collect compact durable outputs and their metadata only. Leave model weights,
activation arrays, caches, and bulky checkpoints in scratch unless a deliberate
data-publication plan says otherwise.

## Scheduling choices

Use the smallest approved allocation that accommodates measured model memory
and batch requirements. Live account association is authoritative. The
2026-08-24 snapshot makes several consequences concrete:

- `gpu_a100_8`: `pabitra` had a two-GPU, 16-CPU, 400G account limit. Two
  one-GPU jobs at 8 CPU/90G can fit; a third cannot.
- `gpu_h100_4`: two GPUs but only 12 CPUs and 300G were allowed. Two historic
  8-CPU single-GPU templates cannot coexist even though two GPUs are allowed.
- `gpu_h200_8`: three GPUs but only 8 CPUs and 300G were allowed, and the
  partition walltime was one day. A multi-GPU request must respect all three
  dimensions, not GPU count alone.
- `compute` is preferred for CPU-only analysis. GPU allocation for cached
  activation analysis is wasteful unless the code actually loads a model.
- RTX and legacy V100 partitions existed but had no validated PhysMon runtime
  path in the model registry snapshot. Use them only after an approved
  compatibility check.

The partition describes hardware capacity; the association/QoS constrains what
the shared account can actually consume. Historic templates can be invalid
today. Re-query before every submission.

## Shared result and scratch conventions

Use task names that survive a handoff:

```text
results/stageNN/<experiment>/<attempt-id>/
/scratch/pabitra/physmon/slurm_logs/%j_%x.out
/scratch/pabitra/physmon/slurm_logs/%j_%x.err
/scratch/pabitra/physmon/checkpoints/<experiment>/<attempt-id>/
```

An attempt ID should not be `latest`. It should encode a stable run identity,
such as a date plus short commit or explicitly assigned run ID. A corrected run
links to the prior attempt through metadata; it never overwrites it.

Never put portable code paths in job artifacts as `/Users/...`. Local code uses
repository-relative paths. Job scripts derive runtime roots from `HOME`,
`SCRATCH`, `PHYSMON_ROOT`, and the model registry.

## Required end-of-shift handoff

```text
Task and scientific authorization:
Local branch / commit / upstream relation:
Remote commit / marker / worktree status:
Deployment lease status and owner/token handoff:
Sync plan and actual direction:
Job IDs, states, and Slurm exit codes:
Template, command, model role, input panel, expected/observed rows:
Result, raw-output, stdout, stderr, checkpoint, and scratch paths:
Evidence classification: authoritative / exploratory / partial / failed / superseded:
Open issue, safe next action, and required approval:
```

## Recovery rules

- **Remote dirty worktree:** stop. Inspect paths and obtain owner intent.
- **Lease held:** stop. Do not `rm` the lock or `git clean` the remote tree.
- **Network transfer interrupted:** rerun the dry plan; rsync can resume file
  transfer but it is not a substitute for post-sync commit verification.
- **Job ended non-zero:** preserve logs and output. Create a new attempt only
  after diagnosis and authorization.
- **Job completed with zero raw rows:** classify as failure/partial, not a null
  result. Capture target/donor or panel eligibility diagnostics.
- **Remote/local divergence:** resolve via Git and review, never with an rsync
  overwrite or force reset.
