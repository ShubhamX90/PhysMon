# PhysMon Stage Journal

This directory is the running, stage-by-stage journal of work done under the plan of record,
`docs/proposals/PhysMon_Research_v2.pdf` (PhysMon Research Redesign v2.0, 14 October 2026;
navigation digest `docs/proposals/PhysMon_Research_v2_working_digest.md`).

It complements, and does not replace, `docs/decisions/decision_log.md`. The decision log carries the
durable scientific decisions and corrections. The journal carries everything behind them: what was
read, what was observed, what was decided and why, which alternatives were rejected, which commands
were run, what each change touched, and what is still open.

## Rules

1. **Append-only.** A journal entry is never edited to change its meaning. A correction is a new
   entry that points at the entry it corrects. Typo-level fixes are allowed within the same shift.
2. **Every decision and every change gets an entry**, at the time it is made, not reconstructed
   later. This includes decisions not to do something.
3. **Cite the v2 section** (page and section number of the PDF) for every decision that rests on the
   plan. If a decision would contradict the plan, stop and ask the user before acting.
4. **Separate observation from inference.** Mark each statement as `[V]` (verified by reading or
   running it in this shift), `[R]` (reported by a reader or tool and not re-checked), or `[I]`
   (inference).
5. **Never convert a missing or zero-row result into a measured null.** Use `NOT_EVALUATED` (v2 §8.4,
   p.42) and say why.
6. **Record the evidence class** of anything that looks like a result: `exploratory`,
   `confirmatory`, `diagnostic_only`, `partial_not_reportable`, `failed`, `superseded`, or
   `NOT_EVALUATED`. Nothing from Stage 14 is paper-eligible by default.
7. **Record provenance** for every produced artifact: source commit, the command, input paths and
   hashes where practical, and output paths.
8. **Record what was not done** and the reason (for example: no Slurm submission, no GPU work).

## Layout

- `INDEX.md`: stage table with status and links.
- `stage14/<stage-id>_<slug>.md`: one journal file per stage (for example `14.0_governance_ingest.md`).

## Entry template

```
### J<stage>-<nnn> · <ISO timestamp, +05:30> · <kind>
kind: decision | change | observation | read | command | correction | blocked | handoff
**What:** ...
**Why:** ...
**v2 reference:** section / page
**Alternatives considered:** ...
**Files touched:** ...
**Commands run:** ...
**Result / evidence class:** ...
**Open:** ...
```

Not every field applies to every entry; omit fields that are empty rather than writing "n/a".

## Identity and pushing

During the 2026-10-16 session the user asked that commits and pushes made by the agent carry the
user's own identity (`atharvgaur1845 <atharvgaur591@gmail.com>`). This is applied per command with
`git -c user.name=... -c user.email=...`; the shared `~/.gitconfig` and the repository config are not
changed. Commits keep the `Co-Authored-By: Claude Sonnet 5.5` trailer.
