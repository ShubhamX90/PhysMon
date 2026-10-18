# Stage 14 status and roadmap (updated 2026-10-18, after Stage 14.16 planning)

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
| 14.12 | Copying versus relevance from the existing records: unit compatibility modulates the boost (same strings and digits); Qwen expresses it in generation, Llama almost never; no matched relevant-role control exists in these records |
| 14.13 | Reasoning-allowed contract (`reasoning-v1`, own fingerprint), runner and frozen analysis; job 401327 cancelled (512 tokens truncated most generations); rerun at 2,048 tokens (job 401357) in progress when this was written |
| 14.14 | Numeral-presence control: plan (3,924 jobs), analysis tooling, score-only runner; run pending |
| 14.15 | Second structure batch S11 to S20 (shorter chains, four domains): certified, approved by the user's open walkthrough, certificates UNREVIEWED; pilot plan for them (424 jobs) committed, run pending |
| 14.16 | Legacy-family X03 plan (60 stratified families, 4 wrappers, candidate matrix; 8,448 jobs) and frozen analysis; run pending |

Integrity check: `python3 scripts/v2/register_stage14_artifacts.py --verify` (non-zero exit on any change); `python3 scripts/v2/validate_claim_ledger.py`.

## What the evidence supports, in one paragraph

A same-unit numeral that appears in the prompt becomes a far more likely continuation as the answer (about 10 to 13 nats for Qwen, 3.5 to 5 for Llama from the no-cue prompt), about equally for near, moderate and far values, in all seven output formats; the boost depends on whether the numeral's unit matches the requested quantity (J14.9-006), so it is not explained by surface copying of the digits alone, and it is not evidence of a physics failure or of relevance gating. Both 7 to 8 B models are almost never correct on the ten structures when they must answer in one line, so correctness-based endpoints cannot be estimated.

## Open, and what each needs

| Open item | State and need |
|---|---|
| Correctness floor | Addressed by the reasoning contract: job 401357 (2,048 tokens) is running on S01 to S10; the frozen gate (at least 8 base-correct anchors of 20 per model) decides whether the correctness endpoint can be estimated. Batch B (S11 to S20) was built with shorter chains for the same purpose and has a planned pilot. |
| Copying versus relevance | The numeral-presence control (plan and analysis committed) needs one GPU run to compare the isolated cue with the numbers the problem needs. |
| Relevant-edit assay | Inconclusive under the no-reasoning answer; the reasoning run gives new data for it. |
| Legacy-family X03 | Planned and frozen; needs a GPU run (score-only). |
| P0 gate (regenerate Phase-I values through the model; hook check) | Not started; large; changes what earlier results mean; needs a decision. |
| 40 to 60 independent structures | 20 exist (S01 to S20), all with one-reviewer open walkthrough approval only. 20 to 40 more, and a certified review by someone other than the author and the walkthrough reviewer. |
| Independent expert review, physicist confirmation of the planted bank, validator recruitment | People outside this session; the user reviewed as one non-blinded reviewer whose physics expertise was not stated. |
| Phase-I manuscript | Not in the repository; its numbers stay SUBMITTED claims. |

## Jobs and authorization

Every job needed the user's per-submission acceptance after the first block of the permission layer (J14.7-021). Jobs so far: COMPLETED 399217, 399539, 399969, 400932, 401287; FAILED 399511 and 399530 (git unusable on gpunode6); CANCELLED 399209, 399215 (my own pending H200 jobs) and 401327 (reasoning, 512-token budget, at the user's choice). Job 401357 (reasoning, 2,048 tokens) was running when this was written. Jobs of other projects on the shared account were not touched. See `docs/registry/v2/slurm_jobs.jsonl`.
