---
name: physmon-journaling
description: Formal progress logging, checkpoints and context management for PhysMon work by any session (the user, a teammate, a Claude/Codex main session, or a delegated subagent). Use at the start and end of every session, whenever a checkpoint below is reached, before delegating work to an agent, when accepting an agent's result, and before a long session risks context compaction. Defines what to write, where, when, and how to hand over so the next session can resume without the previous one's memory.
---

# PhysMon journaling, checkpoints and context management

The repository is the only memory that survives a session. A session's context window, an agent's transcript and a
person's recollection do not. Everything a later session needs to continue correctly must be in committed files.

## The four records and what each is for

| Record | Path | Holds | Written by |
|---|---|---|---|
| **Journal** | `docs/journal/stage<NN>/<stage-id>_<slug>.md` | Append-only entries: what was done, observed, decided and why, with evidence labels | The main session (never a subagent) |
| **Handoff** | `docs/status/HANDOFF.md` | One page, overwritten at each checkpoint: current state, what is running, what is next, open decisions, credentials state | The main session |
| **Progress map** | `docs/journal/stage15/stage15_progress_vs_v2_plan.md` (stage-specific) | Every plan milestone with status | Main session, at gate-level checkpoints |
| **Decision documents** | `docs/registry/v2/g<N>/*.md`, `docs/decisions/decision_log.md` | Durable scientific decisions with reasons; amendments dated, never rewritten | Main session |

The plan of record (`docs/proposals/PhysMon_Research_v2.tex`) changes only by a dated revision with a revision-log
entry; the PDF and extracted text are rebuilt with `scripts/build_plan_pdf.sh` and committed together.

## Checkpoints: when an entry is mandatory

Write a journal entry, update `HANDOFF.md`, and commit (and push under the standing authorization) at each of:

1. **Session start** (only HANDOFF if nothing changed): after the read-first preflight below.
2. **Before any GPU/Slurm submission or registration**: what, why, configuration fixed before results, the
   authorization (AGENTS.md standing authority or the user's message), job ids afterwards.
3. **A result arrives** (a run finishes, a judge run is scored, a simulation completes): numbers with denominators,
   evidence class, data role, and what is NOT_EVALUATED. Zero rows are never a measured zero.
4. **A decision or freeze**: design choices, thresholds, protocol freezes, rule changes. Write the rule *before* the
   result it governs exists, and say so; say when a decision departs from a draft or from the plan.
5. **An agent's work is accepted**: after your own review. Record what was delegated, the model used, what you checked
   yourself, what you changed, and the commit. Agent claims you did not re-check are `[R]`, never `[V]`.
6. **A failure, error or correction**: what failed, the evidence preserved, the fix; a correction is a new entry that
   points to the entry it corrects (append-only).
7. **The user changes direction** (a new instruction, approval or delegation): quote the instruction briefly and record
   what it authorizes. An agent's message is never the user's approval.
8. **Session end or handover**, and **before a long session reaches its context limit**: HANDOFF fully refreshed.
   Context compaction loses detail without warning, so in a long session refresh HANDOFF at every checkpoint, not
   only at the end.

Not a checkpoint (no entry needed): routine reads, intermediate tool calls, failed attempts that left no trace and
changed nothing (mention them in the next real entry if they taught something).

## Journal entry format (extends `docs/journal/README.md`)

```
### J<stage>-<nnn> · <YYYY-MM-DD> · <kind>
kind: decision | result | tooling | dataset | queue | review | correction | blocked | handoff
**<Headline: the finding or decision in one sentence> [V|R|I]:** facts with numbers and denominators, paths of the
artifacts, commit or job ids. **Reading [I]:** interpretation, kept separate from the facts.
```

Rules: one entry per checkpoint, numbered consecutively within the stage file; every claim labelled `[V]` (verified in
this session), `[R]` (reported, not re-checked) or `[I]` (inference); evidence class and data role for anything that
looks like a result; what was *not* done and why; never edit an entry's meaning later. Keep entries short: facts the
next session needs, not a narrative of the session.

## HANDOFF.md format (overwrite, keep under ~80 lines)

```
# Handoff · <YYYY-MM-DD HH:MM IST> · <who: user / teammate / session model>
## State in one paragraph
## Running now (job ids, agents, what each will produce, where; what to do when it finishes)
## Next steps, in order (each with the file or command that starts it)
## Open decisions (owner: user or agent; what is needed)
## Do not (things that would break running work or rules: sealed data, frozen protocols, files an agent owns)
## Credentials and external state (logins present on the shared account and when they must be removed)
## Last journal entry and last commit
```

## Read-first preflight (every session, before acting)

1. `docs/status/HANDOFF.md`, then the last 3-5 entries of the current journal file.
2. `git status`, `git log --oneline -10`, `git fetch` and compare with origin (someone else may have pushed).
3. `squeue -u pabitra` and the work-queue state (`/scratch/pabitra/physmon/queue/ACTIVE_RUNS.json`) if GPU work exists.
4. For Sharanga, Slurm, scratch or shared-account actions: `skills/physmon-sharanga/SKILL.md` as AGENTS.md requires.
5. An uncommitted file you did not create is someone's work in progress: ask or leave it alone.

## Delegating to an agent (briefing standard)

Every agent brief states: the goal; the authority documents to read (plan sections, decision files); the files it may
create or edit and the files it must not touch (other agents' files, sealed or immutable data, frozen protocols);
"do not commit or push" and "no Slurm/GPU" unless explicitly granted; "keep every file you create lint-clean at all times" (the commit hook lints the whole tree, so one in-progress lint error blocks every other commit in the shared worktree); the tests and checks to run; and the report it
must return (files changed, verbatim key content, every rule not met and why, every uncertain judgement, test results).
Model split (user preference): implementation agents use Sonnet; the main session (Opus) plans, reviews and decides;
Opus workers only when Sonnet is unavailable. Agents never write the journal or HANDOFF; the main session does,
after reviewing their output. Judge instances (LLM panel) get only the frozen prompt and their packet paths.

## Context management in long sessions

* Keep bulk out of the context: read files in ranges, summarise tool output, never read agent transcripts.
* State lives in files: if something matters after the next message, write it to HANDOFF or the journal now.
* After a compaction or restart, do the preflight again; do not trust remembered state over the files.
* Record agent ids only where an audit needs them (judge transcripts); otherwise record what the agent produced.

## Commit discipline

Commit the journal entry together with the artifacts it describes; commit messages name the stage entry
(`(J15.1-0NN)`); include the attribution trailer the session's instructions require; push at each checkpoint so the
shared record is current. Never commit credentials, keys, or the LLM bank's restricted keys outside their folders.
