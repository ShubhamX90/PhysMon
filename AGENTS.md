# PhysMon Agent Instructions

These instructions apply to every coding agent working anywhere in this
repository. Read this file before editing, running commands, committing, or
using the cluster.

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

## Governing guidance for Stage 14 onwards

The plan of record for all work from Stage 14 is
`docs/proposals/PhysMon_Research_v2.pdf` (PhysMon Research Redesign v2.0, 14 October 2026),
selected by the user on 2026-10-15. It replaces the June Part II plan as guidance. Before any
Stage 14+ work, read its relevant section and the navigation digest
`docs/proposals/PhysMon_Research_v2_working_digest.md` (searchable text:
`docs/proposals/PhysMon_Research_v2.extracted.txt`), follow its gates (Phase B and P0-P11), its
data roles, and its negative-result and missing-data policy, and cite the section you rely on in
decision-log entries and experiment cards. If a task would contradict it, stop and ask. The
rules in the core scientific section above still apply.

## Working model

Work normally happens directly on Sharanga (Claude Code via Remote SSH) in
`~/PhysMons`. GitHub is the shared record for viewing and review. There is no
maintained laptop mirror and no sync step; do not use the `make sync-*` targets
or `scripts/ops/` lease helpers unless the user explicitly asks.

## Required Sharanga routing

Before **any** task involving Sharanga, Slurm, GPU/CPU allocation, scratch
storage, models, checkpoints, activations, Git commits/pushes, job results, or
the shared `pabitra` account, read and follow:

```text
skills/physmon-sharanga/SKILL.md
```

Then read the referenced material needed for the action (paths relative to that
skill directory):

- `references/git-and-sync.md` for Git, branches, and shared-worktree safety;
- `references/sharanga-environment.md` before choosing environment or resources;
- `references/slurm-operations.md` before any scheduler action;
- `references/operational-playbook.md` for shift start, provenance, and handoff.

The skill's live-preflight protocol is mandatory. Do not submit a job when the
current scientific brief or user request prohibits it.

## Normal engineering workflow

1. Inspect branch, commit, and worktree status first.
2. Use a focused branch/commit for a bounded change; keep unrelated files
   untouched; stage explicit paths.
3. Run proportional tests and report their result honestly.
4. Standing authorization (granted explicitly by the user, 2026-10-14): an agent
   may commit and push its own bounded changes to `origin/main` or a
   `claude/<task>` branch without asking each time, provided that it stages
   explicit paths, lint and proportionate tests pass (the pre-commit hook runs
   `make lint`), no one else's uncommitted work is swept in, no pending or
   running job reads the files it touches, and the push is a plain
   fast-forward. Never force-push, rewrite shared history, or delete remote
   branches. This does not cover Slurm submission, hold, release, or cancel,
   or deleting or moving scratch or result data; those still need explicit
   authorization in the current task. Report every push in the handoff.
5. Do not edit files that a pending or running job reads.

## Project conventions

- Keep portable paths repository-relative. Scratch/model roots belong in runtime
  configuration and the model registry, not portable source files.
- Prefer existing project scripts, model registry entries, templates, and
  provenance schemas over ad hoc substitutes.
- Use `rg` for repository search. Use `apply_patch` for deliberate source edits.
- See `docs/model_registry.yml`, `docs/decisions/decision_log.md`, and
  `docs/assumptions/assumption_tracker.md` when the task touches model identity,
  historical results, or experimental assumptions.
