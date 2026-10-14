# Git and Remote Workflow

## Purpose

Use this reference whenever a PhysMon task changes versioned code, commits or pushes, collects results, or hands work to another person or agent. The filename is historical; there is no longer a workstation-to-cluster sync step.

## Current project contract

- Claude Code runs on Sharanga via Remote SSH. The working repository is `~/PhysMons` under the shared `pabitra` account.
- GitHub `origin` is where the user and teammates read the code and review work. It is the shared record, but it only contains what has been pushed.
- There is no maintained mirror on a laptop. The old `make sync-up`, `sync-down`, `sync-plan-*`, `sync-check`, the `.physmon_ops/deployment_commit` marker, `scripts/ops/physmon_remote_lease.sh`, and `scripts/ops/remote_preflight.py --expect-aligned` belonged to that workflow. They may remain in the repository; do not run them unless the user explicitly asks to sync a workstation copy.
- Large files stay out of Git: activations, virtual environments, Python caches, model/checkpoint formats, `data/generated`, `slurm/submitted`. Keep them on scratch and reference them from manifests.

Because the worktree is both the editing surface and the thing jobs run from, the two main hazards are (1) another person's or agent's uncommitted work in the same tree, and (2) editing files that a pending or running job will read. Everything below addresses those.

## Shift-start inspection

```bash
hostname; pwd
git status --short
git fetch origin
git branch --show-current
git rev-parse HEAD
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git rev-list --left-right --count HEAD...@{upstream}
git log --oneline --decorate -12
```

Interpret:

- Dirty or untracked files you did not create belong to someone else until proven otherwise. Leave them untouched and tell the user.
- `behind` means upstream has commits you lack; read them (`git log HEAD..@{upstream}`) before integrating. `ahead` means unpushed local commits that exist nowhere else.
- No upstream configured: ask which branch to track before pushing.

## Branch and ownership rules

`main` is integration history, not a scratchpad for simultaneous agents. For a bounded task, create an attributable branch such as `claude/<short-task>` (or the project's chosen equivalent), commit there, and hand off the branch name with its full SHA. Merge to `main` only through the team's chosen review route (GitHub pull request or an explicit user instruction). Continue an existing branch only after fetching, identifying its owner, and reading the handoff.

```bash
git fetch origin
git switch -c claude/<short-task>      # new branch from the current commit
# ... edit, test ...
git add <specific-paths>
git commit -m "<what and why>"
git push -u origin claude/<short-task> # only with permission
```

Switching branches in the shared worktree changes the files every running job and every other session sees. Check `squeue` and `git status` first, and prefer not to switch branches while jobs that read the tree are pending or running. If you need a second branch checked out at the same time, use `git worktree add` into a separate directory instead.

Do not resolve concurrent work with `git pull --rebase`, `git reset --hard`, a force push, or a blind merge. Preserve the facts first:

```bash
git fetch origin
git status --short
git log --oneline --decorate -12
git diff --name-status @{upstream}...HEAD
```

Then decide whether it is an independent commit, a reviewed merge, or a conflict that needs the originating author. Use `git pull --ff-only` for the simple fast-forward case.

## Commit and push discipline

- Stage explicit paths. `git add -A` and `git commit -a` can sweep in another session's files in a shared tree.
- Check `git diff --cached --stat` before committing.
- Commit and push are external state changes; do them only when the current task authorizes them. Because no mirror exists, ask the user at natural checkpoints (end of a working change, before a long job) whether to push, so work is backed up on GitHub.
- Never commit model weights, activation tensors, caches, or scratch checkpoints. Check `git status` for large untracked paths before staging.
- The untracked `activations` path observed at the repo root is a known pre-existing condition. Do not delete, stage, or `git clean` it.

## Before a job submission

```bash
git status --short                 # tree state; know what is uncommitted
git rev-parse HEAD                 # the SHA the job will record
git log -1 --oneline
git rev-list --left-right --count HEAD...@{upstream}   # is the SHA on GitHub?
squeue                             # what else is queued or running
```

Preferred: the tree is clean, HEAD is pushed, and the job's template and inputs are committed. The job's stdout must print the SHA and `git status --short` so provenance survives. If the tree is dirty for a reason relevant to the job, either commit it first or label the run exploratory and save `git diff` beside its outputs. Dirty files unrelated to the job (someone else's notes, scratch edits) must be named in the record, not committed.

Submitting does not freeze the tree. See "Editing While Jobs Are Live" in `SKILL.md` before touching files a queued or running job uses.

## After a job

1. Inspect the job's Slurm state, stdout, stderr, raw output, and summary.
2. Check observed family/variant rows against the declared panel.
3. Preserve all output, including failures and partial outputs.
4. Make a short collection manifest (see below) and commit only compact, durable result artifacts plus their provenance.
5. Push with permission so the results are visible on GitHub.

## Collision rules

- Never revert or overwrite another contributor's uncommitted change. Surface the exact files and ask.
- Never edit a template, panel, or source file that a pending or running job reads.
- Never re-use a result directory for a rerun. Use a new attempt path and record supersession.
- Never erase someone else's job logs or scratch tree to reclaim space without explicit owner approval.
- Never resolve a Git conflict by discarding unreviewed work.

## Dirty-state decision table

| Observation | Safe interpretation | Action |
|---|---|---|
| clean status plus known untracked `activations` | expected historical exception | proceed after other checks |
| tracked modification you did not make | another session, hotfix, or accidental edit | stop; inspect `git diff` read-only; ask the owner or user |
| untracked code/template/result file you did not create | possible active work or unrecorded provenance | stop; identify the owner and preserve it |
| tracked modification you made | normal in-progress work | commit with explicit paths, or report it in the handoff |
| `HEAD` ahead of upstream | local commits not on GitHub | report; push with permission |
| `HEAD` behind upstream | newer work exists on GitHub | read it; fast-forward only when safe and no live job is affected |
| `HEAD` and upstream diverged | concurrent history | stop; do not rebase or force; surface both sides |
| HEAD at job-submission time differs from SHA in the job's recorded provenance | tree changed after submission | mark provenance unresolved; do not retrofit metadata |

## Results are not source

Keep three sets separate when finishing a run:

1. **Versioned durable artifacts:** small manifests, compact CSV/JSON summaries, scripts, tests, documentation. Commit after review.
2. **Scratch-only raw artifacts:** activations, checkpoints, model caches, large arrays. Leave in scratch and commit a manifest containing their path under `/scratch/pabitra/physmon` and a cryptographic hash where feasible.
3. **Evidence status:** `complete`, `partial`, `failed`, `superseded`, or `unresolved`, determined by raw rows, provenance, and validation, never by whether a file exists or was committed.

A collection manifest records job ID, source SHA (plus dirty/exploratory flag), output/log paths, observed versus expected rows, artifact hashes when feasible, and any correction link. This prevents a later shift from treating a directory name as a result.

## Team handoff minimum

Publish a short handoff in the project's agreed tracking surface (and say it in the final message of the session). Include branch, HEAD SHA, whether it is pushed, uncommitted files, job IDs, output roots, result status, files that live jobs depend on, and the next decision. Make uncertainty visible: `pending`, `partial_not_reportable`, `failed`, and `superseded` are useful states.
