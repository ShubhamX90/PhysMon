# ADOPTED 2026-11-13 as amended by `decisions_2026-11-13.md` (G1 freeze pending the items listed there): open questions for the user

Status: DRAFT, 2026-11-13, agent-written. Each item is a choice the plan of record (`docs/proposals/PhysMon_Research_v2.tex`)
leaves to G1, or a gap found while drafting the other files in this folder. Format: question; options;
recommendation (R). Nothing here is decided.

## A. Statistical rules

1. **Does TRIVIAL_EFFECT count as equivalence for H0/H6?** (`sec:statistics` four outcomes; `rvs.classify` returns
   TRIVIAL_EFFECT before testing TOST, though a 95% interval inside the margin always passes TOST.)
   Options: (a) only EQUIVALENT supports H0/H6; (b) EQUIVALENT or TRIVIAL_EFFECT supports, reported as "trivial
   departure within SESOI". R: (b) for H6-RD (the SESOI defines what matters), (a) for H0 (its wording is "no effect
   beyond generic perturbation").
2. **One-sided tests vs two-sided EFFECT label.** F1/F2 are tested one-sided (sign-flip, Holm), but `rvs.classify` uses
   the two-sided 95% t-interval, so a G4 rejection can carry the label INCONCLUSIVE. Options: (a) keep; (b) classify
   F1/F2 with the one-sided 95% bound; (c) G4 decision = Holm-adjusted sign-flip rejection, label reported beside.
   R: (c) for G4 decisions, (b) for the labels; requires a code change in `rolevalue_stats.py`.
3. **"Extends beyond the margin"** is coded as "any part of the interval beyond the SESOI". Options: (a) keep; (b) the
   whole interval beyond. R: (a), plus report the point estimate's position relative to the SESOI.
4. **Minimum evaluable structures** for a scorecard status: code says 3. R: 6 (the exact sign-flip test cannot reach
   p < 0.05 two-sided below J = 6).
5. **Method agreement and drop-1-to-3 robustness** (B6.4, P4.6) are not coded. R: implement as in
   `g3_scorecard_thresholds.md` section 1 before the freeze.
6. **Phrasing disagreement**: status of a role hypothesis when phrasings disagree. R: pooled INCONCLUSIVE flagged
   WORDING_DEPENDENT, per-phrasing statuses beside.
7. **F3 "per value step"** uses the value index; study values are not equally spaced in z. Options: (a) index step
   (as coded); (b) per unit of z or log z. R: (a), stated in the card, since the SESOI was reasoned per step.

## B. Thresholds that need the user's judgement

8. **R-tracking criterion.** R: T_R >= 0.50, point estimate, at least 16 evaluable structures, absolute (not relative
   to no-cue). Options: 0.40 / 0.50 / 0.60; point estimate vs lower bound >= 0.40.
9. **Band.** R: keep [0.30, 0.85] on k_sel = 4 no-cue samples pooled over instances (J15.1-006, fixed before any
   record). Alternative: instance 0 only (matches the role cells, but only 5 possible shares).
10. **O5 SESOIs for H5**: R: length log(1.2) (20%), budget exhaustion 0.05. Alternatives: 10%/0.03 or 30%/0.10.
11. **H5 comparator**: plan says "equivalent to no-cue". R: N primary (as F1), no-cue beside.
12. **H4 trace rule**: "trace-correct" share threshold 0.50 and a frozen rule-based extractor (no LLM judge). R: accept;
    the extractor must be written and tested on synthetic traces before G3, else H4 is NOT_EVALUATED in G3.
13. **Misuse attribution**: R: M_h excludes zero + per-value rule at 2 of 3 values + not confounded in over half the
    structures; fewer than 5 total matches = INCONCLUSIVE.
14. **Mechanism SESOIs (G5-G7 cards)**: R: T3 I_role 0.10 tracking; T1/T2 log-odds 1.0 nat (over 5x the measured bf16
    noise SD 0.09-0.19 nats). Option: defer to G5 opening (plan allows freezing when the card's gate opens).

## C. Design and sampling

15. **Adaptive sampling in G3.** R: none (J = min(40, eligible), fixed k). Option B: two-stage 24 then 40 on interval
    width only.
16. **k in G3 and the no-cue count.** R: k = 8 per R/D cell, N 6k, no-cue 6k. Option: no-cue at k (descriptive only;
    cheaper, but its interval inherits the imbalance J15.1-011 found for N).
17. **Held-out values (m >= 5) for the dependency-curve test**: the plan assigns them to no gate. R: not run in G3;
    run in G4 as a committed prediction of answer modes at the held-out values from the G3-attributed curves.
18. **Non-physics control size.** R: 16 structures, R/D x 3 values x 2 phrasings.
19. **G4 opening rule and calibration of sealed structures.** In-band status needs no-cue selection samples on G4
    structures. R: G4 starts with a no-cue calibration pass (k_sel = 4) on structures taken in a seeded order from the
    sealed pool; in-band ones enter until J is reached; estimation and role cells use fresh samples.
20. **G4 "meets its rule"** (G4 gate) is not numeric in the plan. R: the family meets its rule if (a) at least one of
    F1-F3 is Holm-rejected in the predicted direction with label EFFECT, or (b) all three are EQUIVALENT with R tracking
    at or above the criterion (H6-RD). "Replicated" additionally requires agreement with the G3 direction for every
    contrast that was EFFECT in G3.
21. **G4 size for the H6-RD route.** Planning J = 50 powers each one-sided test, but joint TOST of F1-F3 at 80% needs
    about 11.95 omega^2/Delta^2 if the three are independent (each at about 93%): about 48 at omega 0.2 and 75 at
    omega 0.25 (Delta 0.10). R: size G4 by simulating joint TOST power from the G2 variance components; open more
    sealed structures if needed (270 available).

## D. Secondary family and testing order

22. **One secondary family**: may C and K form one "C/K extension" family? R: yes (Holm within it); otherwise
    H6-extended can never be confirmed alongside K.
23. **Priority order** of candidate families (`sampling_and_selection_rules.md` section 3). R: C/K, unit/plausibility,
    relevance instruction, cost, position, proximity.
24. **Testing order in G4**: primary F1-F3 -> misuse attribution (only after F1 passes) -> G3-chosen family. Is the
    chosen family gated on the primary family passing (fixed sequence) or tested regardless with Holm? R: fixed
    sequence after the primary family meets its rule.

## E. Hypothesis mapping

25. **F2 EFFECT (R neglect above placebo) supports no hypothesis in H1-H5.** Options: (a) add "H3-R" (selection failure
    by over-ignoring) to the scorecard; (b) report it only as evidence against H0/H6. R: (a), labelled as an addition
    to the plan's table.
26. **Copy across units**: the generator emits a copy foil only when q's dimension equals the target's, so H1's "every
    unit" and H2's incompatible-unit copy test cannot be scored. R: add a `digit_copy` foil (same digits, target unit)
    for incompatible-unit cells before the unit ablation.

## F. Causal claim types (T1 prefix)

27. **T1 prefix type per experiment.** R: type (ii) (the model's own trace under the N prompt, every sampled trace) as
    primary for X07 (readout screen), X08 (H4 readout) and X10 (Qwen3 thinking); type (i) (gold trace from the typed
    graph) as sensitivity. X09 and X11 use T2/T3 only.
28. **Compatibility strata cut-points.** Stratum variable: per-token NLL of the prefix under the D prompt minus under
    N. Options: (a) tertiles computed on the G5 discovery split, frozen before the held-out test; (b) fixed cut-points
    now (no data to justify them). R: (a).

## G. Primary-model rule

29. **Qwen3-8B mode order.** R: thinking off before thinking on.
30. **Extended parity as a G2 criterion.** The rule lists extended HF-vs-TL parity, but G0 says a parity failure blocks
    only mechanism work. Options: (a) as written (no primary model until parity has run); (b) parity required only for
    the G5 role of the primary model. R: (a) if the parity job can run before G2 ends; otherwise (b), recorded.
31. **vLLM engine parity per model** (preflight skeleton) is not listed in the rule; only Qwen2.5-7B passed (J15.1-012).
    R: add it as a criterion for any configuration whose records come from vLLM.
32. **Second model**: may it be the same weights in another thinking mode, or a Qwen model after a Qwen primary? R:
    different weights required; same vendor allowed, disclosed.
33. **G5 held-out pool.** R: unopened INTERNAL_CONFIRMATION remainder for held-out mechanism tests; shadow set and
    ADVERSARIAL/G6 reserve untouched.

## H. Inconsistencies found in the plan (for the record)

1. **Compute budget vs frozen balanced-N rule.** `sec:compute-budget` assumes 14 cells per structure with N once; the
   G1 design rule (J15.1-011) samples N 6k times, so a structure costs about 19 cell-equivalents (+36%), or 24 if the
   no-cue cell is balanced too (+71%). The G3 and G4 rows understate generations.
2. **"Presence" estimand duplicates F1.** `sec:statistics` lists an O1 difference between N and a D cell; under the
   declared view D tracking equals D O1, so it is F1.
3. **F2 has no positive hypothesis** (item 25).
4. **H0 and H6-RD nearly coincide** on the core cells; they will usually be co-scored.
5. **Joint power for H6-RD** exceeds the G4 planning J = 50 when omega >= 0.2 (item 21).
6. **One-sided tests with two-sided labels** in the frozen code (item 2).
7. **H5 comparator** is no-cue in the plan while every other D contrast uses N (item 11).
8. **Primary-model rule vs G0 parity scope** (item 30).
9. **Band timing.** The plan says the band is fixed in G1 and not changed after G2 results; J15.1-006 calls
   [0.30, 0.85] a planning band "fixed in G1 before G3", and the calibration runs are already registered. Consistent
   only if the band is frozen before any calibration record is read (item 9).
