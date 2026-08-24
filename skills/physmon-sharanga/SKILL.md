---
name: physmon-sharanga
description: Coordinate safe PhysMon work across a developer workstation, GitHub, and the shared Sharanga HPC environment. Use whenever a PhysMon task mentions Sharanga, Slurm, GPU or CPU jobs, scratch storage, model caches, remote results, syncing, rsync, Git handoff, the shared pabitra account, or a teammate/agent shift. Enforces a read-first preflight, provenance-aware job lifecycle, and safe local-to-remote synchronization.
---

# PhysMon on Sharanga

Use this skill to keep the versioned repository, shared remote worktree, and non-versioned scratch data coherent. Treat the repository and cluster as a scientific workflow: every run must be attributable to a commit, an immutable input panel, a command or template, and durable outputs.

Read [Git and Sync Coordination](references/git-and-sync.md) for every task that can modify code, results, or the remote worktree. Read [Sharanga Environment Snapshot](references/sharanga-environment.md) before selecting resources or a runtime environment. Read [Slurm Operations](references/slurm-operations.md) before any job action.

## Operating Model

Keep three distinct authorities separate:

| Location | Purpose | Authority |
|---|---|---|
| Personal workstation clone | Code editing, tests, review, commits | A developer's working copy only |
| `origin` on GitHub | Shared versioned source of truth | Git history and reviewed branch state |
| `~/PhysMons` on Sharanga | Operational snapshot used by jobs | Must match the intended Git commit before submission |
| `/scratch/pabitra/physmon` | Models, activations, logs, checkpoints, large intermediates | Non-Git runtime data; never assume it can be reconstructed locally |

Do not treat the shared Sharanga worktree as a collaborative editor. Edit locally, test locally, commit and push the intended change, then synchronize an audited snapshot to Sharanga. Do not use a remote result as paper evidence until its raw output, job log, source commit, panel, and summary are traceable.

## First Five Minutes

1. Read the current project's scientific-governance instructions. They can forbid remote access, jobs, or follow-up experiments even when this skill normally supports them.
2. Identify the local repository root with `git rev-parse --show-toplevel`; inspect branch, commit, and dirty files. Do not mix unrelated local changes into a job snapshot.
3. Fetch `origin` and compare the intended branch with its configured upstream. Resolve divergence before a handoff or submission.
4. Inspect Sharanga read-only: remote repository commit/status, `squeue -u pabitra`, `sinfo`, and free scratch space. Re-query live Slurm state; the dated snapshot is not a scheduler contract.
5. Before deployment, require a clean local worktree, an up-to-date upstream branch, and a remote worktree with no unexplained changes. After deployment, require the local and remote source commits plus the remote `.physmon_ops/deployment_commit` marker to match before submission.

Never bypass a project-level prohibition on `ssh`, Slurm, GPU, or remote synchronization. A live-cluster action requires explicit authorization in the current task.

## Edit, Handoff, and Sync Workflow

### Local development and GitHub

1. Start from an up-to-date local branch. Use a short-lived branch for a bounded change when the team's branch policy calls for one.
2. Make a focused change, run proportionate tests, and commit only the files belonging to the change.
3. Push the commit to `origin` before preparing a remote job. Record the commit SHA, task purpose, expected output root, model, panel, and resource request in the handoff surface already used by the project.
4. Before another teammate or agent begins, state whether the remote snapshot must be refreshed and whether active jobs depend on its current files.

### Local-to-Sharanga deployment

The repository Makefile's `sync-up` is deliberately non-destructive: it does not pass `--delete`. It can still overwrite a remote versioned file, so treat it as a controlled deployment rather than a merge. Therefore:

1. Acquire the optional shared deployment lease once the helper is present remotely. It prevents two shifts from synchronizing at the same time; it does not replace Git review or Slurm checks.
2. Run `make remote-preflight` and `make sync-plan-up`. Inspect every proposed transfer.
3. Stop if the plan includes scientific outputs, uncommitted remote edits, another shift's files, or anything not explained by the current task.
4. Only after the plan is clean and reviewed, run `make sync-up` from the intended local commit.
5. Run `python scripts/ops/remote_preflight.py --strict --expect-aligned` and verify `git rev-parse HEAD`, clean status, and `.physmon_ops/deployment_commit` agree with the planned source revision before submitting.

Never use `git reset --hard`, `git checkout --`, `git clean`, or a force push to reconcile a shared environment. Do not run `make sync-up` while another person's job might be reading paths it will change.

### Result collection

1. Wait for a terminal Slurm state and inspect both stdout and stderr plus the produced raw records.
2. Verify expected row/family counts and output completeness before declaring the run complete. An empty file or defaulted aggregate is not a measured null result.
3. Run `make sync-plan-down`, then `make sync-down` only when the local tree can receive the results without overwriting work.
4. Commit small durable results, manifests, provenance, and documentation locally. Keep activations, model weights, caches, and bulky intermediates on scratch.
5. Hand off the exact job ID, exit state, source commit, output paths, raw-row count, and any failure or caveat.

## Job Lifecycle

Use existing templates in `slurm/templates/` as the starting point. Do not invent a partition, account, QoS, resource type, model path, or scratch root. The standard template establishes the `physmon` conda environment, `PYTHONPATH`, `PHYSMON_ROOT`, `HF_HOME`, and `TRANSFORMERS_CACHE`. Read [Operational Playbook](references/operational-playbook.md) for resource-selection rules, the lease protocol, and exact job lifecycle checkpoints.

1. Choose a resource from the live partition/QoS information and the model registry. Request the smallest defensible allocation and walltime.
2. Make output and error logs unique under the approved scratch log root. Do not share an output filename between jobs.
3. Submit only after source/sync preflight passes. Capture the job ID immediately.
4. Monitor with `squeue`, diagnose with `scontrol show job` and the log files, and query terminal accounting with `sacct`.
5. Cancel only a job that belongs to the current task and whose ID has been verified. Preserve failed output and record the reason.

For command syntax, request patterns, quotas, and triage, read [Slurm Operations](references/slurm-operations.md).

## Scratch and Model Rules

Use repository-relative paths in code and derive runtime roots from environment variables in job scripts. Scratch paths belong in templates or configuration, not in portable source code. Keep the following separate:

- `~/PhysMons`: the operational repository copy.
- `/scratch/pabitra/physmon/activations*`: large model-derived artifacts; do not sync or delete casually.
- `/scratch/pabitra/physmon/slurm_logs`: stdout/stderr provenance.
- `/scratch/pabitra/physmon/hf_cache` and the `models` symlink: shared model/cache storage; do not purge or redownload without coordination.
- `/scratch/pabitra/physmon/checkpoints`: run state; never overwrite another task's checkpoint.

Read [Sharanga Environment Snapshot](references/sharanga-environment.md) for the verified layout, model registry, and a refresh procedure.

## Multi-Agent and Team Safety

- Assume shifts are serialized only after checking Git and Slurm; never infer that because a queue is empty no one is preparing a run.
- Use a task-specific result directory and job name. Do not reuse generic `latest`, `output`, or another task's checkpoint directory.
- Do not change a submitted script in place after submission. Preserve the exact rendered script or commit that a job used.
- Do not promote partial, corrected, panel-mismatched, or zero-row outputs to completed evidence. Register correction and supersession relationships explicitly.
- When a result is not safely synchronizable, create a compact manifest pointing to the remote raw data, not a copied or invented summary.

## Required Handoff Record

At the end of a shift involving Sharanga, report:

```text
Local branch and commit:
Remote branch and commit:
Sync direction and outcome:
Job IDs and terminal/pending states:
Template/script and exact command:
Model registry key and scratch inputs:
Family panel/manifest and expected versus observed rows:
Output, stdout, and stderr paths:
What is authoritative, partial, failed, or pending:
Next safe action and any required approval:
```

## Refresh Requirement

The environment reference is a verified snapshot from 2026-08-24. Before submitting or changing resource policy, re-query the cluster and account association. Treat live `scontrol`, `sinfo`, `squeue`, `sacctmgr`, `df`, and Git output as authoritative over the snapshot.
