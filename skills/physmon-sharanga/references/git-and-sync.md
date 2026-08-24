# Git and Sync Coordination

## Purpose

Use this reference whenever a PhysMon task changes versioned code, transfers files between a workstation and Sharanga, collects results, or hands work to another person or agent.

## Current project contract

- Local clones are developer workspaces.
- GitHub `origin` is the shared source-of-truth for versioned files.
- Sharanga runs from `~/PhysMons` under the shared `pabitra` account.
- The repository Makefile provides `make sync-up`, `make sync-check`, and `make sync-down`.
- Large files are intentionally excluded from ordinary sync: activations, virtual environments, Python caches, model/checkpoint formats, `data/generated`, `slurm/submitted`, and `.git`.

`sync-up` writes the deployed full SHA to remote-only `.physmon_ops/deployment_commit` after rsync completes. That directory is excluded from ordinary sync and avoids dirtying the tracked source tree. The legacy tracked `.physmon_git_commit` may remain in historical clones; it is informational only and must not be treated as the deployment marker.

## Why `sync-up` needs a guardrail

Current `make sync-up` is non-destructive: it no longer passes `--delete`. The earlier implementation did. Treat synchronization as deployment, not as a Git merge, because an rsync transfer can still overwrite a remote file and `sync-down` can still overwrite a local file.

Before it runs, verify:

```bash
git status --short
git fetch origin
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git rev-list --left-right --count HEAD...@{upstream}
make remote-preflight
make sync-plan-up
```

Review the dry-run output. Stop for any unexplained overwrite, a dirty remote worktree, remote-only results that are not backed up, or an active job that may read changing paths. A local/remote commit disagreement is expected before deployment and forbidden before submission.

## Recommended handoff sequence

### Before a code-changing shift

```bash
git fetch origin
git switch YOUR_BRANCH
git pull --ff-only
git status --short
```

Use a feature branch when the team expects review or multiple independent changes. Do not create a second change atop unknown remote state.

### Branch and ownership rules

`main` is integration history, not a scratchpad for simultaneous agents. For a
bounded implementation task, create an attributable branch such as
`codex/<short-task>` or the project's chosen equivalent, push it, and hand off
the branch name with its full commit SHA. Merge to `main` only through the
team's chosen review/approval route. A shift may continue an existing branch
only after it has fetched, identified the branch owner, and read the handoff.

Do not solve concurrent work with `git pull --rebase`, `git reset --hard`,
force push, or a blind merge. First preserve the facts:

```bash
git fetch origin
git status --short
git log --oneline --decorate -12
git diff --name-status @{upstream}...HEAD
```

Then decide whether the work is an independent commit, a reviewed merge, or a
conflict that needs the originating teammate. Uncommitted changes in another
person's local clone are not a synchronization target.

### Before a job submission

```bash
git status --short
git rev-parse HEAD
git push
make remote-preflight
make sync-plan-up
make sync-up
python scripts/ops/remote_preflight.py --strict --expect-aligned
```

The `push` and `sync-up` steps are external state changes. Run them only with permission for the current task. The remote `activations` directory is presently untracked; do not use a broad clean/reset command there. Use `make sync-plan-prune` only to inspect a possible prune; there is intentionally no automatic destructive-prune target.

### What each sync command actually does

| Command | Direction | Mutation | Required review |
|---|---|---|---|
| `make remote-preflight` | local + read-only remote | none | local/remote status, queue, scratch |
| `make sync-plan-up` | local to remote | none | every proposed upload/overwrite |
| `make sync-up` | local to remote | overwrites matching remote versioned paths; no deletion | plan, lease, remote status |
| `make sync-plan-down` | remote to local | none | every proposed download/overwrite |
| `make sync-down` | remote to local | overwrites matching local paths; no deletion | plan and local ownership |
| `make sync-plan-prune` | local to remote | none; shows `--delete` effect | only to understand stale files; never execute a manual equivalent casually |

Neither direction is a Git merge. A file that has independently changed on both
sides is a stop condition, even if rsync would choose one side silently. Use
Git to resolve versioned source and a task-specific manifest to resolve
scratch/result artifacts.

### After a job

1. Inspect the job's Slurm state, stdout, stderr, raw output, and summary.
2. Check the observed family/variant rows against the declared panel.
3. Preserve all output, including failures and partial outputs.
4. Run `make sync-plan-down`. Ensure the local tree can accept results before `sync-down`.
5. Commit only compact, durable result artifacts plus their provenance. Do not add model weights, activation tensors, caches, or scratch checkpoints to Git.

## Collision rules

- Never edit code directly in `~/PhysMons` while another team member may synchronize or submit from it.
- Never run `make sync-up` merely because commits match: a remote result directory may still differ.
- Never re-use a result directory for a rerun. Use a new attempt path and record supersession.
- Never erase someone else's job logs or scratch tree to reclaim space without explicit owner approval.
- Never resolve a Git conflict by discarding unreviewed work. Surface the exact files and use the originating author's intent where possible.

## Remote-dirty-state decision table

| Remote observation | Safe interpretation | Action |
|---|---|---|
| clean Git status plus known `?? activations` | expected historical exception | proceed only after all other preflight checks pass |
| tracked modification | another deployment, hotfix, or accidental edit | stop; inspect diff read-only and obtain owner decision |
| untracked code/template/result file | possible active work or unsynced provenance | stop; identify owner and preserve it |
| remote `HEAD` differs before upload | normal deployment gap or unknown remote change | compare commits; do not submit yet |
| remote `HEAD` differs after upload | failed/incomplete deployment | do not submit; rerun plan and resolve |
| remote marker differs after upload | deployment marker write failed or wrong source | do not submit; inspect the exact command and lease |

## Results are not source sync

Keep three sets separate when harvesting:

1. **Versioned durable artifacts:** small manifests, compact CSV/JSON summaries,
   scripts, tests, and documentation. These can be planned, synchronized, and
   committed after review.
2. **Remote-only raw artifacts:** activations, checkpoints, model caches, and
   large arrays. Leave in scratch, then commit a manifest containing their
   repository-relative or remote operational reference and cryptographic hash
   where available.
3. **Evidence status:** an output's state (`complete`, `partial`, `failed`,
   `superseded`, `unresolved`) is determined by raw rows, provenance, and
   validation, never by its ability to copy via rsync.

Before sync-down, make a short collection manifest with job ID, source SHA,
remote output/log paths, observed versus expected rows, artifact hashes when
feasible, and any correction link. This prevents a later shift from treating a
remote directory name as a result.

## Team handoff minimum

Publish a short handoff in the project's agreed tracking surface. Include source commit, remote commit, sync status, job IDs, output roots, result status, and the next decision. Make uncertainty visible: `pending`, `partial_not_reportable`, `failed`, and `superseded` are useful states.
