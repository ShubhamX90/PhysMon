# Stage 14 status and roadmap (as of 2026-10-18)

Plan of record: `docs/proposals/PhysMon_Research_v2.pdf`. Journal index: `docs/journal/INDEX.md`. Decisions: `docs/decisions/decision_log.md`.
**Nothing in Stage 14 is a confirmation, a validated item set, or paper-eligible.** Every result below is exploratory (data role EXPLORATION).

## Done (and what it is)

| Stage | Result |
|---|---|
| 14.0 to 14.4 | Governance (ledger, contract), X01 reproduction and X02 base-rotation attack from committed records, scoring contract with seven wrappers, structure-overlap clusters (CPU) |
| 14.5 | Validator-qualification materials v2; the 33-item planted-defect bank reviewed by the user (27 defective as declared, 6 valid controls); no validator qualified |
| 14.6 | Typed generator and ten solver-certified v2 structures; approved by one open user walkthrough; certificates still UNREVIEWED |
| 14.7 | Pilot: smoke rerun passed; full two-model pilot (422 records) run; correctness rule declared (protocol 4b) |
| 14.8 to 14.9 | Descriptive pilot analysis; dtype noise floor and anchor-matched answer competition (bfloat16 reproducible; noise SD 0.09 to 0.19 nats) |
| 14.10 | X03 on the v2 structures under seven wrappers: the sign of the cue effect persists in every format, its size depends on format for Qwen, parse rates depend heavily on format |
| 14.11 | Append-only artifact registry (22 artifacts) and Slurm job register (9 jobs); five exploratory ledger rows |

Integrity check: `python3 scripts/v2/register_stage14_artifacts.py --verify` (non-zero exit on any change); `python3 scripts/v2/validate_claim_ledger.py`.

## What the evidence supports, in one paragraph

A same-unit numeral that appears in the prompt becomes a far more likely continuation as the answer (about 10 to 13 nats for Qwen, 3.5 to 5 for Llama from the no-cue prompt), about equally for near, moderate and far values, in all seven output formats; this is what in-context copying of a string predicts, and it is not evidence of a physics failure or of relevance gating. Both 7 to 8 B models are almost never correct on the ten structures when they must answer in one line, so correctness-based endpoints cannot be estimated.

## Open, and what each needs

| Open item | Needs |
|---|---|
| Correctness floor (no base-correct anchors) | A design decision: allow reasoning (a new wrapper means a new contract version and fingerprint), or use structures a 7 to 8 B model can solve. Not started. |
| Copying versus relevance | A control with the same numeral in a relevant role (the manifest has `role_reversal` and `relevant_edit` cells, not yet analysed for this) |
| P0 gate (regenerate Phase-I values through the model; hook check) | A decision to rerun legacy-stage computations on GPU; large; changes what earlier results mean |
| 40 to 60 independent structures | Generator work after review findings shape the grammar |
| Independent expert review, physicist confirmation of the bank, validator recruitment | People outside this session; the user reviewed as one non-blinded reviewer whose physics expertise was not stated |
| Legacy-family X03, first-token and value-only likelihood | Optional extensions |
| Phase-I manuscript | Not in the repository; its numbers stay SUBMITTED claims |

## Jobs and authorization

Every job needed the user's per-submission acceptance after the first block of the permission layer (J14.7-021). Jobs: COMPLETED 399217, 399539, 399969, 400932, 401287; FAILED 399511 and 399530 (git unusable on gpunode6); CANCELLED 399209 and 399215 (my own pending H200 jobs). No job is pending or running. Jobs of other projects on the shared account were not touched. See `docs/registry/v2/slurm_jobs.jsonl`.
