# PhysMon Agent Instructions

These instructions apply to every coding agent working anywhere in this
repository. Read this file before editing, running commands, synchronizing, or
using a remote system.

## Core scientific rules

1. Read `README.md`, the applicable scientific brief, and the relevant
   decision/status record before changing experiment code, evidence, or paper
   claims.
2. Preserve raw, partial, failed, corrected, and superseded artifacts. An empty
   panel, defaulted summary, or zero-row CSV is not a measured zero effect.
3. Do not promote exploratory evidence to confirmation. Record source commit,
   model, panel, raw artifacts, and status before reporting a scientific result.
4. Do not revert, delete, or overwrite another contributor's work. Treat a
   dirty worktree or unexplained artifact as an ownership question.

## Required Sharanga routing

Before **any** task involving Sharanga, SSH, Slurm, GPU/CPU allocation, scratch
storage, models, checkpoints, activations, rsync, Git handoff, remote results,
or the shared `pabitra` account, read and follow:

```text
skills/physmon-sharanga/SKILL.md
```

Then read the referenced material needed for the action:

- `references/git-and-sync.md` for local/GitHub/Sharanga coordination;
- `references/sharanga-environment.md` before choosing environment or resources;
- `references/slurm-operations.md` before any scheduler action;
- `references/operational-playbook.md` for team handoff, deployment lease, and
  result provenance.

The skill's live-preflight and non-destructive synchronization protocol is
mandatory. Do not access Sharanga or submit a job when the current scientific
brief or user request prohibits it.

## Normal engineering workflow

1. Inspect branch, commit, and worktree status first.
2. Use a focused branch/commit for a bounded change; keep unrelated local files
   untouched.
3. Run proportional tests and report their result honestly.
4. Do not make a commit, push, remote synchronization, or Slurm submission
   unless the current task explicitly authorizes that external state change.

## Project conventions

- Keep portable paths repository-relative. Scratch/model roots belong in runtime
  configuration and the model registry, not portable source files.
- Prefer existing project scripts, model registry entries, templates, and
  provenance schemas over ad hoc substitutes.
- Use `rg` for repository search. Use `apply_patch` for deliberate source edits.
- See `docs/model_registry.yml`, `docs/decisions/decision_log.md`, and
  `docs/assumptions/assumption_tracker.md` when the task touches model identity,
  historical results, or experimental assumptions.
