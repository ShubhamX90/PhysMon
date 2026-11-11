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

The plan of record for all work from Stage 14 is PhysMon Research Redesign v2, selected by the
user on 2026-10-15 and revised on 2026-11-11 (after the ICLR 2027 reviews of the withdrawn
Phase-I paper). Its canonical source is `docs/proposals/PhysMon_Research_v2.tex`; the built
`PhysMon_Research_v2.pdf` and searchable `PhysMon_Research_v2.extracted.txt` are regenerated from
it with `scripts/build_plan_pdf.sh` (edit the `.tex`, never the PDF, and commit all three
together). It replaces the June Part II plan as guidance. Before any Stage 14+ work, read its
relevant section and the navigation digest
`docs/proposals/PhysMon_Research_v2_working_digest.md`, follow its gates (G0-G7, with the October
Phase B and P0-P11 blocks kept as the requirement catalogue), its data roles, and its
negative-result and missing-data policy, and cite the section you rely on in
decision-log entries and experiment cards. If a task would contradict it, stop and ask. The
rules in the core scientific section above still apply.

Its Appendix C lists the open decisions (D1-D6) and the defaults in force until the user decides
them; the defaults only withhold actions.

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
   branches. Report every push in the handoff.
5. Standing Slurm authority (granted explicitly by the user, 2026-11-12): an agent
   may decide, submit, and monitor PhysMon jobs without asking, provided that
   it runs the live preflight first (`squeue` whole queue and `-u pabitra`,
   `sinfo`, QoS caps, `sbatch --test-only`), submits only from a clean, pushed
   commit through an immutable code snapshot, and has checked the job script,
   command, environment and inputs at least twice (a CPU dry run of the exact
   command plus an independent review) before submission, because a mistake
   costs days of queue. It may submit the same work-queue job to several
   partitions or GPU types to raise the chance of starting. It may cancel
   PENDING jobs on the shared `pabitra` account that are not PhysMon's, after
   saving `scontrol show job -dd` and `scontrol write batch_script` output to
   `docs/registry/v2/cancelled_foreign_jobs/` and logging the cancellation so
   the owner can resubmit; RUNNING jobs of other projects are never touched.
   Every submission and cancellation is recorded in
   `docs/registry/v2/slurm_jobs.jsonl` and the journal. Deleting or moving
   scratch or result data still needs explicit authorization.
6. Do not edit files that a pending or running job reads.

## Project conventions

- Keep portable paths repository-relative. Scratch/model roots belong in runtime
  configuration and the model registry, not portable source files.
- Prefer existing project scripts, model registry entries, templates, and
  provenance schemas over ad hoc substitutes.
- Use `rg` for repository search. Use `apply_patch` for deliberate source edits.
- See `docs/model_registry.yml`, `docs/decisions/decision_log.md`, and
  `docs/assumptions/assumption_tracker.md` when the task touches model identity,
  historical results, or experimental assumptions.
