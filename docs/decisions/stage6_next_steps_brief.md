# PhysMon — Stage 6 Next-Steps Brief
**Version:** 6.6  
**Date:** 2026-06-15  
**Context:** Phase 2 Parts A/D are corrected and PI-validated. Phase 2 Parts B/C/E are built,
verified, and rendered, but not yet PI-validated. The full 140-family benchmark now exists in
construction form, but the full Phase D2 behavioural sweep must remain gated behind final
validation and benchmark-freeze checks.

---

## Why This Is the Correct Next Step

The project is now in the highest-leverage but also highest-risk transition point so far:
we have enough families to make Stage 6 statistically meaningful, but we do **not** yet have a
fully human-validated frozen benchmark. Per the proposal's validation protocol and the empirical
lesson from `CM_B_UM_045`, symbolic verification is necessary but not sufficient. Before we spend
full Stage 6 behavioural compute, we must do one more rigorous validation pass over the newly
constructed families and one benchmark-wide audit over the merged 140-family pool.

This brief therefore prioritizes:
1. catching structural errors before compute is spent,
2. making PI review efficient and high-signal,
3. freezing the benchmark cleanly before the full behavioural sweep,
4. preserving the strongest design principle discovered so far: **near-match distractors**.

---

## Execution Order

```text
PART I   Agent Audit of the 140-Family Benchmark        [do now]
PART II  PI Review Package for Phase 2 B/C/E            [prepare now, PI reviews next]
PART III Apply Any PI Corrections to B/C/E              [only if needed]
PART IV  Stage 6 Benchmark Freeze Gate                  [after B/C/E PI validation]
PART V   Phase D2 Full Behavioural Sweep                [only after freeze gate PASS]
```

---

## PART I — Agent Audit of the Full Benchmark

### Goal
Produce a benchmark-wide structural audit that is broader than symbolic verification and more
useful than ad hoc spot-checking.

### Required outputs

Create these artifacts:

1. `results/stage6/audit/stage6_full_benchmark_manifest.csv`
   - one row per family across all currently constructed families
   - fields:
     - `template_id`
     - `phase_bucket` (`pilot`, `phase1_um`, `phase2_ad`, `phase2_bce`)
     - `domain`
     - `cue_type`
     - `governing_law`
     - `target_quantity`
     - `target_units`
     - `answer_value`
     - `answer_display`
     - `cue_slot_name`
     - `cue_slot_type`
     - `num_variants`
     - `verifier_certified`
     - `pi_validated`
     - `has_exact_match_distractor`
     - `min_relative_gap_to_answer`
     - `near_match_within_5pct`

2. `results/stage6/audit/stage6_phase2_bce_audit_summary.json`
   - machine-readable audit summary for the 40 B/C/E families

3. `results/stage6/audit/stage6_phase2_bce_priority_review.csv`
   - prioritized PI review list
   - families sorted so the most likely-to-be-problematic or highest-value families are reviewed first

### What the audit must check

For every family currently in the benchmark:
- schema completeness,
- exactly 4 variants,
- parser-parseable `correct_answer.display`,
- cue independence consistent with `cue_type`,
- generated JSON present when expected,
- verification report present when expected,
- validation flags internally consistent.

For numeric Cue B families:
- compute the distractor value nearest the correct answer,
- compute `min_relative_gap_to_answer = min(|d - y*| / |y*|)`,
- flag:
  - `exact_match_distractor`
  - `near_match_within_2pct`
  - `near_match_within_5pct`

For Cue C families:
- confirm each family is a pure rendering family and that all 4 variants share the same
  answer target.

### Scientific purpose
This audit is not just bookkeeping. It operationalizes the strongest empirical finding from
Phase D1: families with exact-match or near-match distractors are disproportionately likely to
produce large `S_lp`. The audit therefore creates the metadata we need later to test whether the
near-match hypothesis explains Stage 6 sensitivity better than coarse class labels alone.

---

## PART II — PI Review Package for Phase 2 B/C/E

### Goal
Make PI review of the 40 B/C/E families faster, sharper, and less error-prone than raw
family-by-family reading alone.

### Required outputs

Keep the existing validation form:
- `docs/validation/stage6_phase2_bce_validation_form.md`
- `docs/validation/stage6_phase2_bce_validation_form.csv`

Additionally create:

1. `docs/validation/stage6_phase2_bce_review_guide.md`
   - short human-readable review guide
   - must include:
     - class counts,
     - known high-risk family types,
     - families with exact-match distractors,
     - families with very small near-match gaps,
     - families with unusual framing (if any),
     - note that symbolic verification has already passed and PI review should focus on
       conceptual physics, ambiguity, and question-target alignment.

2. `results/stage6/audit/stage6_phase2_bce_priority_review.csv`
   - order families by:
     1. exact-match distractor,
     2. near-match within 2%,
     3. Cue C rendering families,
     4. thermodynamics families,
     5. remaining numeric Cue A / standard Cue B families.

### Why this matters
`CM_B_UM_045` showed that the highest-value human review catches **conceptual target mismatch**
that a numeric verifier cannot see. The review guide should explicitly remind the PI to watch for:
- asking about the wrong object,
- target quantity mismatch,
- implicit ambiguity in rendering families,
- distractor phrasing that is not truly non-governing.

---

## PART III — Apply Any PI Corrections

### Rule
Do not begin the full Phase D2 sweep until:
- any PI-flagged B/C/E corrections are applied,
- corrected families are re-verified,
- corrected families are re-rendered,
- and the validation form / audit artifacts are regenerated.

### Logging rule
Every PI correction must be recorded in `docs/decisions/decision_log.md` with:
- template ID,
- issue type,
- exact fix,
- whether the issue was symbolic-verifier-visible or human-only.

---

## PART IV — Stage 6 Benchmark Freeze Gate

### Gate question
Is the full 140-family Stage 6 benchmark ready to freeze for behavioural evaluation?

### Freeze criteria

All of the following must be true:
- [ ] All 140 templates exist and load cleanly
- [ ] All 140 pass symbolic verification
- [ ] All 140 render successfully
- [ ] All Phase 1 + Phase 2 families are PI-validated
- [ ] Benchmark manifest and audit summary are generated
- [ ] No unresolved conceptual-physics issues remain
- [ ] No unresolved duplicate-ID / malformed-schema / render-mismatch issues remain

### Output
Record a freeze-gate entry in `docs/decisions/decision_log.md` with explicit PASS / FAIL.

---

## PART V — Phase D2 Full Behavioural Sweep

### Only after the freeze gate passes
Run the full Stage 6 behavioural sweep on the complete benchmark:
- all currently validated families,
- both primary models,
- same repaired prompting and parsing stack used in Stage 4 repair.

### D2 outputs to prepare for

Expected artifacts:
- `results/stage6/behavioural_full/`
- `results/stage6/analysis_d2/`
- classwise `S_lp` and `hat_S` breakdowns,
- near-match vs non-near-match sensitivity comparison,
- model-specific divergence summary,
- refreshed positive-family pool for Stage 6 probing.

---

## What To Execute Immediately

The agent should execute **Part I** and **Part II artifact preparation** now:
- build the audit pipeline,
- generate the manifest,
- generate the priority review list,
- generate the B/C/E review guide,
- record the audit state in the decision log.

The agent should **not** run Phase D2 yet.

---

## Expected Immediate Outcome

After executing this brief, the repo should contain:
- a benchmark-wide manifest,
- a Phase 2 B/C/E audit summary,
- a prioritized PI review package,
- a clear freeze-gate definition,
- and a much sharper path from validation to compute.
