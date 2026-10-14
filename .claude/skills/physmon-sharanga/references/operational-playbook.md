# PhysMon Shared Operations Playbook

This is the end-to-end protocol for a person or coding agent taking a PhysMon
shift when Claude Code runs directly on Sharanga (Remote SSH) in `~/PhysMons`
under the shared `pabitra` account. The worktree is the single working copy:
there is no workstation mirror, no sync step, and no deployment lease.

## Roles and authority

| System | What belongs there | What must not be inferred |
|---|---|---|
| `~/PhysMons` | edits, tests, commits, job submission | that uncommitted files are yours or disposable; that a pending job is insulated from edits |
| GitHub `origin` | shared, reviewable history | that unpushed work exists there, or that scratch artifacts exist or are valid |
| `/scratch/pabitra/physmon` | job logs, models, activations, checkpoints | that contents are Git-tracked or safe to overwrite |
| Slurm accounting/logs | runtime allocation and terminal state | that a `COMPLETED` job produced valid science |

One shift owns one bounded task. A shift may prepare code, commit it, submit an
approved job, harvest it, and write a handoff. It must not silently take over
another shift's in-progress job, uncommitted edits, branch, or result tree.
Nothing locks the tree, so ownership is established by reading Git, the queue,
and the previous handoff.

## Shift start: read-only reality check

Run this before editing or scheduling:

```bash
hostname; pwd
git status --short
git fetch origin
git branch --show-current
git rev-parse HEAD
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git rev-list --left-right --count HEAD...@{upstream}
squeue -o "%i|%u|%T|%P|%j|%M|%l|%R"
df -h /scratch/pabitra
```

Read the result as follows:

- dirty files you did not create are an ownership question, not debris;
- `ahead` means unpushed commits that exist nowhere else; `behind` or diverged
  must be understood before integrating, never forced;
- `?? activations` is a historically observed untracked path; do not remove it;
- an empty personal queue does not prove the shared account is idle: look at the
  whole current queue and consult the prior handoff if one exists.

Before altering a result root, search it and its job logs. A retry always gets a
new attempt directory. Historical, partial, corrected, and failed records are
evidence and remain preserved.

## Working in the shared tree

### 1. Make an attributable change

```bash
git switch -c claude/<short-task>   # or continue a branch you have read
# edit, then test: make test / make lint / a targeted test
git add <intended-files>
git diff --cached --stat
git commit -m "<bounded change>"
git push -u origin claude/<short-task>   # with permission
git rev-parse HEAD
```

Use a named branch and a reviewed merge according to team policy. Do not submit
uncommitted scientific code unless the run is declared exploratory and its
provenance record says so and keeps `git diff`.

### 2. Know what a job reads

Jobs execute out of the live worktree. Before changing files, identify what
pending or running jobs import or read: `src/`, the template under
`slurm/templates/`, panels or manifests under `data/`, and `configs/`. Do not
modify those while the job is pending or running. If development must continue
meanwhile, work in a separate `git worktree` directory or run the job from a
frozen checkout (see `SKILL.md`, "Editing While Jobs Are Live"). Do not switch
branches in `~/PhysMons` while such jobs exist.

### 3. Submit an approved job with durable provenance

Create a task-specific template or an immutable copy of the template in the
repository. It must declare the partition, GRES, CPU/memory/walltime,
environment, model registry role, input manifest, output root, and log root.
Use unique `--job-name`, `%j`-keyed log filenames, and an output directory
containing an attempt identifier.

```bash
cd ~/PhysMons && sbatch --parsable slurm/templates/<template>.sh
```

`--parsable` returns a job ID suitable for a manifest. Record the exact template
path, source SHA, clean/dirty state, job ID, model role/path resolution, input
panel hash, expected rows, and intended output/log paths before monitoring it.

Do not use a Slurm dependency as scientific approval. `afterok` only says a
previous batch step exited zero; a human or explicitly approved data gate must
inspect its raw output before follow-up science runs.

### 4. Monitor and harvest

```bash
squeue -j JOB_ID -o "%i|%u|%T|%P|%j|%M|%l|%R"
scontrol show job JOB_ID
sacct -X -j JOB_ID -o JobIDRaw,JobName,Partition,State,Elapsed,AllocTRES,ExitCode,MaxRSS
```

Inspect stdout, stderr, raw records, expected panel rows, and summary values.
`COMPLETED` is only scheduler success. Missing rows, an empty output, a
defaulted mean, wrong panel, or unknown source SHA makes the scientific result
partial, failed, or provenance-unresolved.

Results are already in place. Commit compact durable outputs and their metadata
(push with permission). Leave model weights, activation arrays, caches, and
bulky checkpoints in scratch unless a deliberate data-publication plan says
otherwise.

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

Never put machine-specific paths such as `/Users/...` in job artifacts or
portable code. Code uses repository-relative paths. Job scripts derive runtime
roots from `HOME`, `SCRATCH`, `PHYSMON_ROOT`, and the model registry.

## Required end-of-shift handoff

```text
Task and scientific authorization:
Branch / HEAD commit / pushed to origin (yes/no):
Uncommitted or untracked files left in ~/PhysMons and who owns them:
Job IDs, states, and Slurm exit codes:
Template, command, model role, input panel, expected/observed rows:
Result, raw-output, stdout, stderr, checkpoint, and scratch paths:
Evidence classification: authoritative / exploratory / partial / failed / superseded:
Files pending or running jobs depend on (do not edit):
Open issue, safe next action, and required approval:
```

## Recovery rules

- **Unknown dirty worktree:** stop. Inspect paths read-only and obtain owner intent.
- **Edited a file a job reads:** note the time and files; mark the affected job's
  provenance unresolved if it started after the edit; do not restore with
  `git checkout --` without checking what else changed.
- **Unpushed work at risk:** commit to a branch and, with permission, push; a
  cluster-only commit has no other copy.
- **Job ended non-zero:** preserve logs and output. Create a new attempt only
  after diagnosis and authorization.
- **Job completed with zero raw rows:** classify as failure/partial, not a null
  result. Capture target/donor or panel eligibility diagnostics.
- **Branch divergence:** resolve via Git and review, never with a force push or
  hard reset.
