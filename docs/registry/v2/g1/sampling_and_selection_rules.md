# ADOPTED 2026-11-13 as amended by `decisions_2026-11-13.md` (G1 freeze pending the items listed there): band, sampling and selection rules

Status: DRAFT, 2026-11-13, agent-written, nothing run. Implements the G1 elements "sampling may be adaptive only by a
rule fixed in G1" (G3 item 1), "G3 can add at most one secondary family to G4, chosen by a rule fixed in G1" (G3 gate),
the calibration band (G2; `sec:populations`), and the primary-model rule (G2 item 4), all in `sec:gates`.

**PLAN** = stated in the plan; **PROPOSED** = agent proposal, not decided.

## 1. Calibration band (fixed before G3, and before any calibration record is read)

PLAN: calibrated intermediate-difficulty tasks are selected per model and budget on k_sel no-cue samples; k_est fresh
samples estimate baseline and self-flip floor; selection samples are never reused for estimation (G2 item 2;
`sec:populations`). The band is not changed after seeing G2 results (G2 gate; `sec:conditional-new`).

**PROPOSED definition (adopts the planning band already fixed before any record in J15.1-006, unchanged):**
- Configuration = model x thinking mode x token budget (Qwen2.5-7B 4,096; Llama-3.1-8B 4,096; Qwen3-8B thinking off
  4,096; Qwen3-8B thinking on 16,384, as registered in J15.1-004).
- Selection share of structure s = share of `grade_declared == correct` among all attempted no-cue samples with sample
  index 0-3 (k_sel = 4), pooled over the structure's instances; non-COMPLETE counts as not correct.
- s is **in band** iff 0.30 <= selection share <= 0.85.
- Estimation samples 4-7 give the baseline and the self-flip floor only.

Reasons for the edges (PROPOSED): the upper edge 0.85 leaves at least 0.15 of headroom, more than the 0.10 SESOI of
F1 and F2, so a loss of scientific size can show; Stage 14.20 showed near-ceiling items yield almost no errors (2 wrong
of 128 cells, `sec:blockP4` status). The lower edge 0.30 keeps base failure from dominating: below it most samples
fail the unmodified problem, so a tracking loss is bounded by a small baseline and R tracking cannot reach the
proposed 0.50 criterion. Keeping J15.1-006's value avoids any change after calibration runs have started.

Granularity note: v1 structures have 2 or 4 instances, so the selection share is over 8 or 16 samples (in band = 3-6
of 8, or 5-13 of 16). Role-by-value cells are built on instance 0 only (J15.1-007); pooling instances is PROPOSED
because the instances share one symbolic program (open question).

Model comparisons (PLAN `sec:populations`): one common item set inside every compared configuration's band
(intersection of the bands).

## 2. G3 structure selection and adaptive sampling

**Eligible:** EXPLORATION structures of M250 (130) that are complete for the primary contrast (R and D at 3 values in
2 phrasings, certified, admitted; PLAN `sec:rolevalue` "Feasibility") and in band for the primary configuration.

**Order (PROPOSED):** a seeded random permutation (seed 42) of the eligible structure ids, drawn and committed before
any G3 record. Reason: fixes which structures enter without looking at outcomes.

**Adaptive sampling rule (PROPOSED: none).** J = min(40, number eligible), the first J of the permutation; k fixed in
advance; no per-cell or per-structure top-up based on any record. Reasons: the plan's range is 24-40 (G3 item 1), and
running 40 costs under an hour more with vLLM (`sec:compute-budget`, estimate), so a stopping rule buys little and
adds a degree of freedom. Records lost to infrastructure (no record written, RECORD_ERROR from a crash) may be rerun
from the same snapshot; any written record with any O3 status is final (PLAN `sec:outcomes`: non-complete records are
outcomes).

Alternative (option B, if the user prefers to save structures for later): stage 1 = first 24; add the next 16 only if
any of F1-F3 has a 95% t-interval half-width above its SESOI. The trigger reads only interval widths, never estimates
or signs.

**k (PROPOSED default, to be replaced by the pre-G3 power simulation, PLAN `sec:statistics` power):** k = 8 per R/D
cell (the G4 planning k, so G3 variance components are measured at G4's k); N sampled 6k = 48 (PLAN design rule
J15.1-011: N as often as all D cells together); no-cue sampled 6k = 48 (PROPOSED: the F1-vs-no-cue contrast has the
same imbalance that made the one-sided sign-flip over-reject; open question). Per structure about 96 + 48 + 48 = 192
generations; at J = 40 about 7,700, against the plan's 1,008-4,480 for the core (see inconsistency 1 in
`open_questions_for_user.md`).

## 3. Rule for G3 adding at most one secondary family to G4

PLAN: the G4 primary family (F1-F3) is fixed now; G3 may add at most one secondary family, chosen by a rule fixed in
G1, labelled as chosen on EXPLORATION data; it is tested after the primary family, Holm-corrected
(`sec:statistics` multiple comparisons). The misuse-attribution family (Holm across curves, after F1 passes) is
already prespecified and is not this choice.

**Candidate families (PROPOSED, closed list, in priority order):**
1. **C/K extension:** F1 and the value slope on C and on K cells (needed for H6-extended and the C/K forms of H3;
   PLAN G5: mechanism of correctness covers only strata in G4's family).
2. **Unit/plausibility (H2):** F1 on same-unit vs incompatible-unit vs implausible-value D cells.
3. **Relevance instruction:** F1 with vs without the instruction (discriminates H3 from H4).
4. **Cost (H5):** L5 and B5 of `g3_scorecard_thresholds.md`.
5. **Position:** F1 at cue before vs after the relevant inputs.
6. **Proximity:** F1 across the three proximity levels.
Excluded: formula hint (PLAN: a diagnostic, never a gate); non-physics control (G6 transfer).

**Eligibility (PROPOSED):** a candidate is eligible only if all hold:
- (a) its key contrast was run in G3 and is EFFECT on the calibrated population, with method agreement, phrasing
  agreement and the drop-1-to-3 robustness of the scorecard; for family 1 also eligible when the scorecard points to
  H6-RD (F1, F2, F3 not EFFECT and R tracking at or above criterion), because confirming correct selection in C/K
  needs an equivalence test, not an effect;
- (b) the pre-G4 power simulation, run **at the SESOI, not at the G3 estimate** (reason: avoids the winner's curse of
  sizing on the largest G3 estimate), gives at least 80% power on the G4 pool structures where the family is feasible;
- (c) its cells can be added without changing the primary family's cells.

**Choice:** the first eligible family in the priority order, never the one with the largest G3 estimate (PLAN G3
gate: "not chosen from G3's largest estimate", applied here by analogy). Reason for the order: families that decide
G5 eligibility and the main competing explanation come first; moderators last. If none is eligible, G4 has no
secondary family. The choice and its EXPLORATION label are recorded in the decision log before the G4 preregistration.

## 4. Primary-model rule, operational (PLAN G2 item 4)

Frozen at the end of G2 and before any G3 output; never depends on observed cue effects.

1. Order: Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct, Qwen3-8B (D3: downloaded, revision `b968826d` pinned).
   PROPOSED for Qwen3-8B: thinking off before thinking on (open question).
2. A configuration **meets the G2 criteria** iff all hold:
   - (a) at least 24 complete role-by-value structures in its band (PLAN G2 gate, planning), or the number the pre-G3
     power simulation requires if larger;
   - (b) R tracking T_R >= 0.50 on at least 16 evaluable structures (`r_tracking_criterion.md`, PROPOSED);
   - (c) extended HF-vs-TransformerLens parity at the G5 hook sites in the study dtype passed (PLAN, G0 item 3; not
     yet run);
   - (d) PROPOSED, from the plan's preflight skeleton (`sec:preflight`): engine parity against the pinned HF stack
     passed for this model if its G3 records come from vLLM (so far only Qwen2.5-7B greedy, J15.1-012);
   - (e) its G3 cost fits `sec:compute` (jobs under 10 hours).
3. The primary model is the first configuration in the order that meets them; the second model is the next one that
   meets them (PROPOSED: a different set of weights, so the two thinking modes of Qwen3-8B cannot be primary and
   second together).
4. Recorded in the decision log with the G2 evidence for each criterion; no D-cell, N-cell or F1-F3 output is read
   for this decision.
