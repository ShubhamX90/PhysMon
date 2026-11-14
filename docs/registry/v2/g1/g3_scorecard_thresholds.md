# ADOPTED 2026-11-13 as amended by `decisions_2026-11-13.md` (G1 freeze pending the items listed there): G3 hypothesis scorecard thresholds (H0-H6)

Status: DRAFT, 2026-11-13, agent-written, nothing run. Implements G1 element "the scorecard criteria of G3 with numeric
thresholds" (plan `sec:gates` G1; G3 item 3) for the hypotheses of `sec:hypotheses`.

**PLAN** = stated in `docs/proposals/PhysMon_Research_v2.tex`; **PROPOSED** = agent proposal, not decided.

## 1. Common machinery

1. **Statuses (PLAN, G3 item 3):** SUPPORTED, CONTRADICTED, INCONCLUSIVE, NOT_EVALUATED. Several may be SUPPORTED at
   once; rows are not read by first match. G3 is estimation, not a test: no Holm correction in G3
   (PLAN, `sec:statistics` multiple comparisons, first bullet).
2. **Contrast outcomes (PLAN `sec:statistics`; coded in `rvs.classify`):** each contrast gets one of EFFECT (95%
   t-interval excludes zero and extends beyond the SESOI), TRIVIAL_EFFECT (excludes zero, inside the SESOI),
   EQUIVALENT (TOST at alpha 0.05 per side within the SESOI and the 95% interval includes zero), INCONCLUSIVE, or
   NOT_EVALUATED (`rvs.paired_summary`: fewer than 3 evaluable structures).
   - PROPOSED: raise the scorecard's NOT_EVALUATED floor from 3 to **6** evaluable structures per contrast. Reason: the
     exact sign-flip test, which is primary (J15.1-011), cannot reach p < 0.05 two-sided with J < 6 (minimum p = 2/2^J;
     J = 5 gives 0.0625), so with J < 6 the primary test cannot speak.
   - Direction: an EFFECT counts for a hypothesis only in the direction that hypothesis predicts (F1 > 0 loss; F2 > 0
     excess neglect; misuse excess > 0).
3. **Population (PLAN G3 item 1):** statuses are assigned on the calibrated in-band complete structures of the primary
   model; the all-validated population is reported beside with its own statuses, never substituted.
4. **Method agreement (PLAN B6.4: clustered paired tests, hierarchical models and permutation tests must agree
   qualitatively before a finding is called stable).** PROPOSED: a status that rests on an EFFECT needs the t-interval,
   the bootstrap interval (`rvs.bootstrap_ci`) and the sign-flip p (< 0.05 in the stated direction) to agree; otherwise
   the contrast is read as INCONCLUSIVE and flagged METHOD_DISAGREEMENT.
5. **Extreme-structure robustness (PLAN P4.6: effects must survive dropping the one to three most extreme
   structures).** PROPOSED operationalisation: drop the 1, 2 and 3 structures with the largest estimates in the
   direction of the effect; the 95% t-interval must still exclude zero each time; else INCONCLUSIVE, flagged
   NOT_ROBUST. NOT YET IMPLEMENTED.
6. **Phrasing agreement (PLAN `sec:rolevalue` "Difficulty and wording controls"; `rvs.phrasing_agreement`).** A role
   status (H3, H6) needs agreement on F1-F3. PROPOSED: if agreement fails, the pooled status is INCONCLUSIVE flagged
   WORDING_DEPENDENT and per-phrasing statuses are reported beside it. [amended 2026-11-14 by plan_revision_v2.2, section E: k = 24; agreement rule B; decision 21 target = EQUIVALENT or TRIVIAL: `rvs.phrasing_agreement` is rule B with three states per contrast; AGREE on F1, F2 and F3 is required; any DISAGREE (demonstrated) flags WORDING_DEPENDENT, otherwise any UNRESOLVED flags PHRASING_AGREEMENT_NOT_SHOWN; the earlier check is `rvs.phrasing_agreement_rule_a`, unused by the scorecard; k = 24 per R, D, C and K cell.]
7. **Missingness (PLAN negative and missing result policy).** Status comes from the all-attempted analysis. PROPOSED:
   if the complete-case or budget-exhausted-as-wrong analysis would give a different status, the status is kept and
   flagged MISSINGNESS_SENSITIVE.
8. **R-tracking condition (PLAN G3 gate).** If G3 R tracking is below the G1 criterion (`r_tracking_criterion.md`,
   PROPOSED 0.50), H3 and H6 are NOT_EVALUATED with reason "uninterpretable for role" (reported as a finding);
   H0, H1, H2, H5 are still scored.
9. **Self-flip floor (PLAN `sec:statistics` intervals):** any answer-change rate is read against the G2 self-flip floor,
   never against zero. F1-F3 compare against sampled controls (N, placebo), so they carry their own noise.

## 2. Estimands used by the scorecard

| Id | Definition | SESOI (reason) | Code |
|---|---|---|---|
| F1 | per structure T_N - T_D (all attempted samples, declared view) | 0.10 tracking share, PLAN (share of answers that may be lost to an irrelevant quantity before it matters) | `rvs.structure_estimates`, `rvs.primary_family` |
| F1_nocue | T_none - T_D, reported beside F1 | 0.10 (same reason) | `rvs.structure_estimates` |
| F2 | R neglect share - R placebo match rate | 0.10, PLAN (a tenth of R answers ignoring a quantity that matters) | same |
| F3 | R slope minus D slope of empirical-logit tracking per value step | log(1.5), PLAN (smaller value dependence would not change the reading of any single item) | `rvs.f3_estimate` |
| M_h | misuse excess for curve h: per structure, mean over the study values of (share of D samples matching f_h(z) - share of N samples matching f_h(z)) | 0.10, PLAN ("for the D tracking loss and misuse shares ... planning value 0.10") | per-structure rule `rvs.misuse_support` exists; M_h aggregate NOT YET IMPLEMENTED |
| A_h | attribution of curve h (see below) | n/a | NOT YET IMPLEMENTED |
| CR | copy excess in R: R share matching f_copy(z) - N share matching f_copy(z) (N is a valid comparator here because N contains no numeral) | 0.10 (PROPOSED: same reason as M_h) | NOT YET IMPLEMENTED |
| L5 | O5 length: per structure log(mean generated tokens in D / mean in N) | PROPOSED log(1.2): a 20% length rise changes cost and truncation risk at a fixed budget; it is under half of the about 45% rise seen in Stage 14.20 role-reversal cells (`sec:blockP4` status), so effects of that order are detectable | NOT YET IMPLEMENTED |
| B5 | O5 budget exhaustion: BUDGET_EXHAUSTED share D - N | PROPOSED 0.05: about a 50% relative rise over the 9-12% truncation seen for Qwen3-32B at 12,288 tokens (`sec:compute-budget` rule 4) | NOT YET IMPLEMENTED |
| TC | trace-correct share among D samples whose final answer matches an attributed misuse curve: the certified y*_D(z) is the last value stated for the target in the reasoning trace before the final-answer line, by a frozen rule-based extractor (no LLM judge in a primary analysis, PLAN `sec:outcomes`) | threshold 0.50 (PROPOSED: "readout contamination" must be the majority route of the misuse answers to be called the explanation) | NOT YET IMPLEMENTED |

**Attribution A_h (PROPOSED, implementing PLAN `sec:rolevalue`: a misuse curve is supported only when its share exceeds
the N rate at two or more of at least three values; a single match is never evidence):** curve h is attributed when
(a) M_h is EFFECT or TRIVIAL_EFFECT in the positive direction, (b) the Beta-Binomial pooled D share
(`rvs.beta_binomial_fit`) exceeds the pooled N rate at 2 or more of the 3 study values, and (c) h is not recorded as
confounded (`cell.confounded`) in more than half of the structures where it is defined (reason: a curve that cannot
be told from gold or another curve in most structures cannot be named as the route). If fewer than 5 D samples in
total match h, attribution is INCONCLUSIVE for h, not absent (reason: below 5 matches the Jeffreys interval of a
per-structure rate is dominated by the prior; Stage 14.20 had 2 wrong answers in 128 cells, so rarity is expected).

## 3. Per-hypothesis rules

Rules are evaluated per stratum; strata are never pooled (PLAN `sec:strata` rule 3). "Core" = no cue, R, D, N.

### H0 - No role or presence effect beyond generic perturbation
- **For (PLAN):** D tracking equals N tracking; no misuse share above its N rate; no neglect share above placebo.
- **SUPPORTED:** F1, F2, F3 each EQUIVALENT and every unconfounded M_h EQUIVALENT. (Whether TRIVIAL_EFFECT may stand in
  for EQUIVALENT is an open question; recommended no for H0.)
- **CONTRADICTED:** any of F1, F2, F3 or an M_h is EFFECT in any direction ("any reliable departure").
- **INCONCLUSIVE:** otherwise. PLAN: at G3 size H0 is normally INCONCLUSIVE (TOST at omega 0.2, Delta 0.10 needs
  about 34 structures for one contrast).
- **NOT_EVALUATED:** F1 or F2 NOT_EVALUATED.

### H1 - Numeral presence (F-copy, F-answer prior)
- **For (PLAN):** answers follow the copy curve in every role, stratum and unit. **Against:** copy absent in D, or
  confined to same-unit cells.
- **SUPPORTED:** copy attributed in D (A_copy) and CR is EFFECT or TRIVIAL_EFFECT positive; and, if the unit ablation
  ran, copy is also attributed in incompatible-unit cells.
- **CONTRADICTED:** M_copy EQUIVALENT in D; or copy attributed only in same-unit cells while EQUIVALENT in
  incompatible-unit cells (that pattern counts for H2, PLAN P4.7).
- **INCONCLUSIVE:** otherwise.
- **NOT_EVALUATED:** copy foil defined (q dimension = target dimension, `rolevalue.misuse_foils`) in fewer than 6
  evaluable structures. Note: the generator emits no digit-copy foil for incompatible-unit cells, so the unit part
  of H1 cannot be scored until it does (open question).

### H2 - Plausibility and unit (F-match, F-unit)
- **For (PLAN):** departures only for same-unit or convertible plausible values; vanish under plausibility matching.
  **Against:** departures with incompatible units or implausible values.
- Needs the unit/plausibility ablation (G3 targeted ablation). F1_s, F1_u, F1_imp = F1 computed on same-unit,
  incompatible-unit and implausible-value D cells.
- **SUPPORTED:** F1_s EFFECT and F1_u EQUIVALENT (and F1_imp EQUIVALENT where run).
- **CONTRADICTED:** F1_u EFFECT or F1_imp EFFECT.
- **INCONCLUSIVE:** otherwise. **NOT_EVALUATED:** ablation not run (expected unless the core shows a D loss).

### H3 - Relevance-selection failure (F-role); per stratum D, C, K
- **For (PLAN):** D tracking loss with answers following a prespecified misuse curve (substitute, add or subtract) in
  its predicted direction; C: wrong-law curve; K: out-of-regime curve. **Against:** invariance in D, C and K while R
  responds correctly.
- **SUPPORTED (D):** F1 EFFECT (positive) and at least one of the `replace:*`, `add:*`, `subtract:*` curves attributed.
  Attribution to `copy` alone counts for H1, not H3.
- **SUPPORTED (C / K):** F1 on C (resp. K) cells EFFECT and `wrong_law` (resp. `out_of_regime`) attributed
  (C/K versions of F1 NOT YET IMPLEMENTED; C/K only in targeted ablations).
- **CONTRADICTED (per stratum):** F1 of that stratum EQUIVALENT, F2 not EFFECT, and T_R at or above the G1 criterion.
- **INCONCLUSIVE:** e.g. F1 EFFECT without attribution (a loss of unknown route: counts against H0, not for H3).
- **NOT_EVALUATED:** R tracking below criterion (item 1.8), or stratum not run.
- Overall H3 line: each stratum reported separately; no pooled H3 status.

### H4 - Readout contamination
- **For (PLAN):** correct value in the trace, final answer moved toward the quantity; little change under the
  relevance instruction. **Against:** departures already present in the trace's computation.
- **SUPPORTED:** F1 EFFECT, some curve attributed, TC Jeffreys 95% lower bound > 0.50, and, if the relevance
  instruction ablation ran, the change in F1 with vs without the instruction is EQUIVALENT within 0.10 (PROPOSED:
  "little change" = within the F1 SESOI).
- **CONTRADICTED:** TC 95% upper bound < 0.50 (misuse values already computed in the trace).
- **INCONCLUSIVE:** otherwise (expected when misuse answers are rare).
- **NOT_EVALUATED:** no attributed curve, no reasoning trace (non-reasoning output), or trace extractor not frozen.

### H5 - Computational diversion
- **For (PLAN):** O5 rises (length, budget exhaustion) while O1 and O4 are equivalent to no-cue. **Against:** O1 or O4
  departures.
- PROPOSED comparator: N primary (so a generic added sentence is not counted as diversion, as for F1), no-cue beside;
  the plan names no-cue (open question). Under the declared view, D O1 equals D tracking, so "O1 equivalent" is F1.
- **SUPPORTED:** (L5 EFFECT positive or B5 EFFECT positive) and F1, F2 EQUIVALENT.
- **CONTRADICTED:** L5 and B5 both EQUIVALENT; or F1 or F2 EFFECT (departures in O1/O4; H5 as "cost only" fails,
  though a cost rise may still be reported).
- **INCONCLUSIVE:** otherwise.

### H6 - Correct selection (H6-RD and H6-extended)
- **For (PLAN):** F1, F2, F3 each EQUIVALENT within SESOI by TOST, R tracking at or above the G1 criterion, across
  values and phrasings. H6-extended adds the same for C and K. **Against:** departures in any stratum; an underpowered
  null is INCONCLUSIVE.
- **SUPPORTED (H6-RD):** F1, F2, F3 each EQUIVALENT (TOST alpha 0.05 each; no multiplicity correction because all three
  must pass, an intersection-union test), T_R >= criterion, phrasing agreement on F1-F3. [amended 2026-11-14 by plan_revision_v2.2, section E: k = 24; agreement rule B; decision 21 target = EQUIVALENT or TRIVIAL: the joint power target of decision 21 applies to the rate of F1-F3 all EQUIVALENT or TRIVIAL_EFFECT, the H6-RD criterion under decision 1.]
- **SUPPORTED (H6-extended):** H6-RD plus F1 on C and on K EQUIVALENT and the C and K tracking slopes across values
  EQUIVALENT within log(1.5) (PROPOSED: R-minus-C slope is meaningless because C's quantity differs from R's, so the
  C/K analogue of F3 is the stratum's own slope, target 0; NOT YET IMPLEMENTED).
- **CONTRADICTED:** any of F1, F2, F3 EFFECT (or the C/K analogues for H6-extended).
- **INCONCLUSIVE:** otherwise. PLAN: normally INCONCLUSIVE at G3 size.
- **NOT_EVALUATED:** R tracking below criterion; for H6-extended, C or K not run.

## 4. Non-physics dependency control (PLAN G3 item 3; `sec:conditional-new`)
F1-F3 on the control set are scored with the same outcome rules. A null is INCONCLUSIVE unless powered and is not
evidence of physics-specificity. If the control shows F1 EFFECT in the same direction as the physics core, the
phenomenon is flagged GENERAL_NUMERIC_OR_DEPENDENCY and no physics-specific wording is allowed; this flag does not
change the H0-H6 statuses.

## 5. Notes on the plan found while drafting
- H0's predictions and H6-RD's nearly coincide on the core cells (both need F1, F2 equivalent); they will usually be
  co-SUPPORTED or co-INCONCLUSIVE. They differ by F3 and the R criterion (H6) and the misuse shares (H0).
- An F2 EFFECT (R neglect above placebo) contradicts H0 and H6 but supports no hypothesis in H1-H5 (open question).
- `rvs.classify` uses the two-sided 95% t-interval for EFFECT while F1/F2 are one-sided tests; a one-sided
  rejection with a two-sided interval touching zero is INCONCLUSIVE here (open question).
