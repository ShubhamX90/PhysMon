# LLM judge requalification protocol v2 (frozen 2026-11-13, before any judge has seen bank v4 or prompt v2)

Why: under prompt v1 neither judge qualified (Claude q1: accepted under-specified items; GPT-6.1 Sol gpt_q1: rejected
valid items on edge cases; both accepted contradictions inside a distractor; J15.1-015, J15.1-021). The user approved
three admission standards (J1-J3, `docs/registry/v2/g1/decisions_2026-11-13.md`, with J1 refined before use). They are
written into `judge_prompt_v2.md` (prompt v1 plus an "Admission standard" section; nothing else changed). Under protocol
v1 a changed prompt is requalified only on items no judge has seen.

## Bank v4 (`bank_v4/`, `scripts/v2/s186_build_requal_bank.py`, seed 4242): 32 items, split "requal", none seen by a judge
* 16 fresh legacy-style items: the Stage 14.5 injection rules on DECOY-v1 families absent from the 14.5 bank and its
  genuine sample: 3 contradictory distractor, 3 numerical precision, 2 hidden coupling (1 fresh + held-out), and the
  remaining legacy types once each where a rule applies; 6 fresh valid equivalent rewrites.
* 6 condition-deletion items on M0 problem texts (3 boundary condition: S07, S72, S02; 3 missing assumption: S55, S13,
  S01): no unused v1 family carries an answer-deciding condition the injection rules can delete.
* the 10 held-out role items of bank v3 (one per role defect type, 4 valid), with the bank-v4 K-claim wording.
22 defective, 10 valid. Accepted vocabulary terms per type as in protocol v1 (frozen in the key).

## Judges and runs
Both judges are run once each with prompt v2 on all 32 items: Claude Opus 5.5 as fresh agent instances (batches of up
to four, never two items of one structure or family; transcript audit `s180`), GPT-6.1 Sol through `codex exec`
(reasoning effort high; event audit `s184`). Configuration otherwise as in q1 and gpt_q1.

## Requalification thresholds (all must hold; `s179 --split requal`)
| # | Criterion | Threshold | Reason |
|---|---|---|---|
| R1 | Defective items detected for the declared reason | >= 85% (>= 19 of 22) | same as Q1 |
| R2 | Valid items accepted with no high-severity flag | >= 85% (>= 9 of 10) | same as Q3 |
| R3 | Each type both judges failed under v1 (missing assumption, insufficient boundary condition, contradictory distractor, numerical precision) | >= 2 of its 3 items detected | the requalification exists to show these are fixed |
| R4 | No defect type with three or more items entirely missed | none | same as Q4 |

A judge that passes is QUALIFIED with prompt v2 for its tier (Claude: CLAUDE_JUDGE_PROVISIONAL, EXPLORATION admissions
only; GPT: a panel member). A judge that fails is not used; any further prompt change needs another unseen set.
