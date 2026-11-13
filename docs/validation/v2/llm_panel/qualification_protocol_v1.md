# LLM judge qualification protocol v1 (frozen 2026-11-13, before any judge has seen the bank)

Plan of record: `docs/proposals/PhysMon_Research_v2.tex`, sec:llmpanel (qualification before use) and B4.2-B4.4.
Decision D2 (2026-11-12): panel = Claude, GPT, Gemini; Claude alone for now, tier `CLAUDE_JUDGE_PROVISIONAL`
(same family as the author agent; admits items for EXPLORATION work only; never makes an item `LLM_PANEL_VALIDATED`).

## Judge
* Model: Claude Opus 5.5 (`claude-opus-5-5`), run as fresh agent instances of the session's agent tool, one instance per
  batch of up to four items, **never two items of the same base structure or legacy family in one instance** (so no
  judge can compare variants), with one file per item and pass in its directory. An instance receives only the frozen prompt `judge_prompt_v1.md`, a reviewer id and the paths
  of its packets, copied into an otherwise empty directory on scratch. It never sees the authoring context, the
  generator, the key, another instance's reviews, any model-under-test output, or the study hypotheses.
* Limitation, disclosed: the instances have file-system access; independence from the repository (which holds the key)
  is instructed, not enforced. Each review carries a `notes` field for anything seen by accident, and every judge
  transcript is kept.
* GPT and Gemini judges, when credits exist, use the same packets, prompt and scoring through an API transport.

## Bank (v3, `bank_v3/`, built by `scripts/v2/s178_build_judge_bank.py`, seed 42)
* Qualification set (53): the 33 legacy items of Stage 14.5 (27 defective of 9 types, 6 valid rewrites; labelled by the
  user, J14.5-013) and 20 role-by-value items from the 12 M0 structures (12 defective of 6 types, of which only
  `rendering_not_minimal` is new to the bank; 8 valid).
* Held-out set (10): one item of each role defect type and four valid role items. Never shown to a judge unless a
  judge or prompt must be requalified (below). Nine of the ten share a base problem with a qualification item, so the
  held-out set is unseen as items but not as structures; a fresh planted set on new structures (M250) is preferred
  for any requalification.
* Legacy question wording: all six legacy valid controls ask "Determine the X." and the defective items "What is ...?";
  every defective item with a "What is the X?" question (13 of 27) was given the equivalent "Determine the X." form,
  so "Determine" marks 6 valid of 19 items instead of 6 of 6.
* Pre-freeze review (independent agent, read-only, 2026-11-13): recomputed every role item by hand (all 12 valid items
  hold); its fixes are in this version (accepted terms, contested items, K plants made consistent, minimal pair defined
  in the prompt, flag format shown, scorer type checks, batching rule).
* The bank is not used to tune the prompt. The prompt is frozen at v1 by this commit.

## Scoring (pass-2 records are the judge's final, fully informed verdicts; `scripts/v2/s179_score_judges.py`)
* A defective item is **detected for the declared reason** when its pass-2 `validity` is `invalid` and its
  `defect_flags` contain one of the item's **accepted terms** (frozen in the key: the declared type plus the
  alternatives the pre-freeze review found defensible, for example `hidden_coupling` for a conditional value moved
  outside its regime). Detection with the exact declared term is reported beside it.
* A valid item is **accepted** when its pass-2 `validity` is `valid` and it carries no `high`-severity flag (the plan's
  admission rule: "accepts it with no high-severity defect").
* Contested items (L-Q043, L-Q048: the coupling does not change the answer; L-Q024, L-Q028, L-Q041: "ideal" deleted
  where a physicist may assume it) stay as labelled by the user and count in Q1; their outcomes are also reported
  separately. If a judge fails Q1 only through them, that is reported, not overridden.
* Every review must pass `physmon.governance.review.validate_review`; a missing or malformed review counts as a miss
  (defective) or a rejection (valid), never as excluded.

## Qualification thresholds (all must hold on the qualification set)
| # | Criterion | Threshold | Reason |
|---|---|---|---|
| Q1 | Defective items detected for the declared reason | >= 85% (>= 34 of 39) | plan of record planning value |
| Q2 | Legacy valid controls accepted | >= 5 of 6 | plan of record |
| Q3 | All valid items accepted (legacy and new) | >= 85% (>= 12 of 14) | the plan adds fresh valid items because six estimate false rejection too imprecisely; same 85% as Q1 |
| Q4 | Defect types with zero detections | none | a judge blind to a whole defect type is not qualified for it, whatever its total |

Reported beside them, not gating: per-type detection, flagged (invalid or uncertain) and attribution rates; pass-1
detection for pass-1-detectable legacy items; blind stratum agreement on the valid role items (pass-1 assignment
against the certified stratum); uncertain rates; minutes per item.

## Requalification
If a judge or the prompt changes after any bank result has been seen, the changed judge is requalified only on the
held-out set: >= 5 of 6 held-out defects detected for the declared reason and >= 3 of 4 held-out valid items accepted.
A judge that fails is not used; the failure and the change are recorded in the journal.
