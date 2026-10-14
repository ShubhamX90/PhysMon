---
name: physmon-sharanga
description: Coordinate safe PhysMon work when the repository is edited and run directly on the Sharanga HPC server (Claude Code via Remote SSH), with GitHub as the shared record. Use whenever a PhysMon task mentions Sharanga, Slurm, GPU or CPU jobs, scratch storage, model caches, job results, Git commits/pushes, the shared pabitra account, or a teammate/agent shift. Enforces a read-first preflight, provenance-aware job lifecycle, and safe in-place editing of a worktree that running jobs read.
---

# PhysMon on Sharanga

Use this skill to keep the versioned repository, the live Sharanga worktree, and non-versioned scratch data coherent. Treat the repository and cluster as a scientific workflow: every run must be attributable to a commit, an immutable input panel, a command or template, and durable outputs.

## Working Model

The normal setup is **Claude Code connected to Sharanga over Remote SSH**. The session's working directory is `~/PhysMons` on the cluster, and shell commands run on Sharanga directly. There is no workstation mirror to synchronize. Do not wrap commands in `ssh sharanga '...'` when the session is already remote; confirm with `hostname` and `pwd` first.

| Location | Purpose | Authority |
|---|---|---|
| `~/PhysMons` on Sharanga | The working repository: editing, testing, committing, and job submission | The live worktree. Its uncommitted state is real work and may be read by queued or running jobs |
| `origin` on GitHub | Shared record for viewing, review, and handoff. Reached over SSH (see "GitHub Access") | Git history and branch state. Anything not pushed exists only on the cluster |
| `/scratch/pabitra/physmon` | Models, activations, logs, checkpoints, large intermediates | Non-Git runtime data; never assume it can be reconstructed |
| Any laptop clone | Optional, read-only convenience | Never authoritative. Do not push from it or sync files to or from it unless the user asks |

The retired mirror-and-rsync workflow (`make sync-up`, `sync-down`, `sync-plan-*`, the `.physmon_ops` deployment marker and lease) is **not part of normal operation**. The Makefile targets and `scripts/ops/` helpers may still exist in the repository; do not use them unless the user explicitly asks to sync with a workstation copy. A commit that has not been pushed is not backed up anywhere else, so push deliberately (under the standing authorization) at meaningful checkpoints.

The `pabitra` account is shared. Several people or agents can operate in the same worktree, so a dirty tree, an unfamiliar branch, or an unexplained file is an ownership question, not debris.

## GitHub Access (SSH)

`origin` is reached over SSH with a repository-scoped deploy key, so fetch and push never prompt for credentials:

| Item | Value |
|---|---|
| Remote URL | `git@github-physmon:ShubhamX90/PhysMon.git` |
| Host alias | `github-physmon` in `~/.ssh/config` (`HostName github.com`, `IdentitiesOnly yes`) |
| Key | `~/.ssh/github_physmon` (ed25519, no passphrase). Deploy key `sharanga-physmon` with write access to this repository only |
| Check | `ssh -T git@github-physmon` prints `Hi ShubhamX90/PhysMon! You've successfully authenticated...` |

Rules:

- Use only this alias and key for PhysMon. `~/.ssh/github_breast_cancer_pnstage` and `~/.ssh/id_ed25519` belong to other work on the shared account. Never use them, never print or copy a private key, and never embed a token in a remote URL.
- If the check fails or a push is refused for permissions, do not improvise (no other key, no HTTPS token, no new remote). Report the exact error. Likely causes: the deploy key was removed or lacks write access in the GitHub repository settings, `origin` was reverted to an `https://` URL (`git remote -v`; restore with `git remote set-url origin git@github-physmon:ShubhamX90/PhysMon.git`), or `main` is branch-protected.
- Pushing is an external state change, but the user granted a standing authorization on 2026-10-14 (see "Edit, Commit, and Push" and `AGENTS.md`): you may commit and push your own bounded changes without asking each time, within the limits stated there.
- Recreating the key needs the user, because the public key must be added on GitHub (repository Settings, Deploy keys, "Allow write access"). Details are in [Git and Remote Workflow](references/git-and-sync.md).

Read [Git and Remote Workflow](references/git-and-sync.md) for every task that can modify code, results, or Git state. Read [Sharanga Environment Snapshot](references/sharanga-environment.md) before selecting resources or a runtime environment. Read [Slurm Operations](references/slurm-operations.md) before any job action. Read [Operational Playbook](references/operational-playbook.md) for shift start, job provenance, and handoff.

## First Five Minutes

1. Read the project's scientific-governance instructions (`README.md`, the applicable brief, decision log). They can forbid jobs, follow-up experiments, or paper claims even when this skill normally supports them.
2. Confirm where you are: `hostname`, `pwd`, `git rev-parse --show-toplevel`. Inspect branch, HEAD commit, and `git status --short`. Do not touch dirty files you did not create.
3. `git fetch origin` and compare the branch with its upstream. Resolve divergence by reading it, never by reset or force. If the fetch fails on authentication, see "GitHub Access".
4. Inspect the cluster read-only: `squeue` (whole queue, not just your jobs), `sinfo`, `df -h /scratch/pabitra`, and the previous handoff if one exists. Live Slurm output outranks the dated snapshot. Also confirm the scratch roots exist: `ls -ld /scratch/pabitra/physmon /scratch/pabitra/models`. If they are missing (as on 2026-10-14, which left the repo's `activations` symlink dangling), model, GPU, and activation work is blocked. Do not recreate or re-download anything without the user's approval.
5. Check whether any queued or running job reads files in the worktree (see "Editing While Jobs Are Live" below) before changing source, templates, panels, or configs.

A live-cluster action (submitting, holding, or cancelling a job; deleting or moving scratch data) needs explicit authorization in the current task. Read-only inspection does not.

## Edit, Commit, and Push

1. Work on an attributable branch for any bounded change (for example `claude/<short-task>`); keep `main` as integration history. Continue an existing branch only after reading its history and handoff.
2. Make a focused change and run proportionate tests (`make test`, `make lint`, or the specific test file). Report results honestly. The Makefile finds `ruff`, `pytest`, and `python3` itself (`./.venv`, then the `physmon` conda env, then PATH), so no environment activation is needed. The pre-commit hook runs `make lint`; if it fails, fix the finding. Never bypass it with `--no-verify`.
3. Stage only the files belonging to the change (`git add <paths>`), never `git add -A` in a shared tree. Commit with a message that states what and why.
4. Standing authorization (granted explicitly by the user, 2026-10-14, and recorded in `AGENTS.md`): you may commit and push your own bounded changes to `origin/main` or a `claude/<task>` branch without asking each time. Conditions: explicit-path staging; lint and proportionate tests pass; no one else's uncommitted work is swept in; no pending or running job reads the files you touch (otherwise use a branch or wait); a plain fast-forward push. Not covered, so still ask: force-push, history rewrite, deleting remote branches, merging someone else's branch, Slurm submit/hold/release/cancel, and deleting or moving scratch or result data. GitHub is where teammates and the user read the code, so unpushed work is invisible to them; report every push in the handoff.
5. Never use `git reset --hard`, `git checkout -- <path>`, `git clean`, `git stash drop`, a force push, or a blind `git pull --rebase` to resolve a shared worktree. Preserve facts first (`git status`, `git log`, `git diff`), then decide.

## Editing While Jobs Are Live

Because jobs run from `~/PhysMons`, editing the worktree can change what a pending job executes. A job queued earlier reads whatever is on disk when it starts, and a running Python job may import modules lazily.

- Before editing a file, check `squeue` and the submitted templates for jobs that could read it (`src/`, `slurm/templates/`, panels or manifests under `data/`, `configs/`).
- While a job is **pending or running**, do not modify source it imports, the panel or manifest it reads, or its template. Work on a branch for unrelated files, or wait.
- For a serious run, submit from a **clean, committed, pushed** state, record the full SHA, and keep the tree unchanged for those files until the job reaches a terminal state. If concurrent development must continue, run the job from a frozen checkout:

  ```bash
  git worktree add /scratch/pabitra/physmon/snapshots/<attempt-id> <full-sha>
  ```

  Templates currently set `PHYSMON_ROOT="$HOME/PhysMons"`; verify or parameterize that before relying on a snapshot, and record the snapshot path in the manifest.
- An exploratory run from uncommitted code is allowed only if its provenance record says so (and includes `git diff` saved beside the outputs).

## Job Lifecycle

Use existing templates in `slurm/templates/` as the starting point. Do not invent a partition, account, QoS, resource type, model path, or scratch root. The standard template establishes the `physmon` conda environment, `PYTHONPATH`, `PHYSMON_ROOT`, `HF_HOME`, and `TRANSFORMERS_CACHE`.

1. Choose a resource from live partition/QoS information and the model registry. Request the smallest defensible allocation and walltime.
2. Make output and error logs unique under the approved scratch log root. Never share an output filename between jobs.
3. Submit only from a clean, committed state (or with the exploratory caveat recorded). Capture the job ID immediately (`sbatch --parsable`).
4. Monitor with `squeue`, diagnose with `scontrol show job` and the log files, and query terminal accounting with `sacct`.
5. Cancel only a job that belongs to the current task and whose ID you verified immediately before. Preserve failed output and record the reason.

For command syntax, request patterns, quotas, and triage, read [Slurm Operations](references/slurm-operations.md).

## Result Collection

Results are produced in place; there is nothing to download.

1. Wait for a terminal Slurm state and inspect stdout, stderr, and the raw records.
2. Verify expected versus observed row/family counts before declaring a run complete. An empty file or defaulted aggregate is not a measured null result.
3. Commit small durable artifacts (manifests, compact CSV/JSON summaries, provenance, docs) and push under the standing authorization. Keep activations, model weights, caches, and bulky intermediates on scratch and reference them from a manifest.
4. Hand off the exact job ID, exit state, source commit, output paths, raw-row count, and any failure or caveat.

## Scratch and Model Rules

Use repository-relative paths in code and derive runtime roots from environment variables in job scripts. Scratch paths belong in templates or configuration, not in portable source code. Keep the following separate:

- `~/PhysMons`: the working repository.
- `/scratch/pabitra/physmon/activations*`: large model-derived artifacts; do not delete or move casually.
- `/scratch/pabitra/physmon/slurm_logs`: stdout/stderr provenance.
- `/scratch/pabitra/physmon/hf_cache`: shared Hugging Face cache; do not purge or redownload without coordination.
- `/scratch/pabitra/models` (`PHYSMON_MODEL_ROOT`): model weights at the locations in `docs/model_registry.yml`. Re-create missing weights only with `scripts/download_model.py` (registry-driven, pinned revision, hash-verified, manifest in `docs/model_manifests/`). Never delete or overwrite a model directory.
- `/scratch/pabitra/physmon/checkpoints`: run state; never overwrite another task's checkpoint.

Read [Sharanga Environment Snapshot](references/sharanga-environment.md) for the verified layout, model registry, and a refresh procedure.

## Multi-Agent and Team Safety

- Shifts are not serialized by any lock now. Check Git and the whole Slurm queue; never infer that an empty queue means nobody is preparing a run.
- Use a task-specific result directory and job name. Do not reuse generic `latest`, `output`, or another task's checkpoint directory.
- Do not change a submitted script in place after submission. Preserve the exact script and the commit the job used.
- Do not promote partial, corrected, panel-mismatched, or zero-row outputs to completed evidence. Register correction and supersession relationships explicitly.
- When raw data is too large to commit, commit a compact manifest pointing to the scratch location, not a copied or invented summary.
- If the user's Remote SSH session ends, uncommitted edits remain in the worktree. State what is uncommitted at the end of every shift.

## Required Handoff Record

At the end of a shift involving Sharanga, report:

```text
Branch and HEAD commit (and whether pushed to origin):
Uncommitted or untracked files left in the worktree, and why:
Job IDs and terminal/pending states:
Template/script and exact command:
Model registry key and scratch inputs:
Family panel/manifest and expected versus observed rows:
Output, stdout, and stderr paths:
What is authoritative, partial, failed, or pending:
Files that pending/running jobs depend on (do not edit):
Next safe action and any required approval:
```

## Refresh Requirement

The environment reference is a verified snapshot from 2026-08-24. Before submitting or changing resource policy, re-query the cluster and account association. Treat live `scontrol`, `sinfo`, `squeue`, `sacctmgr`, `df`, and Git output as authoritative over the snapshot.
