# G1 decisions, 2026-11-13

Authority: the user delegated every open G1 question to the agent on 2026-11-13 ("make the best possible decisions on your
own, ensuring highest research quality ... whilst also ensuring a steady speed of work"). Each decision below answers the
numbered question in `open_questions_for_user.md` (same numbering) and gives its reason. Where the decision departs from
the draft recommendation, the row says so. The drafts in this folder (`experiment_cards.md`, `g3_scorecard_thresholds.md`,
`r_tracking_criterion.md`, `sampling_and_selection_rules.md`) are adopted as amended here; where they conflict, this file
governs. Status of each item in the G1 freeze: DECIDED (no work needed), DECIDED + CODE (needs implementation before the
freeze), DEFERRED (frozen later at a stated point, as the plan allows).

## LLM judge standards (user-approved recommendations, 2026-11-13)

| # | Standard | Decision | Reason |
|---|---|---|---|
| J1 | An answer that depends on an assumption the item does not state (ideal gas, starting from rest) | The item is **invalid** (`missing_assumption` or `insufficient_boundary_condition`, severity high) unless the assumption is a stated or universal constant convention (e.g. g given in the text) | Matches the user's bank labels; a benchmark item must determine its answer from its own text; the GPT judge already applies it (6/6) |
| J2 | A contradiction inside a distractor statement that cannot affect the target | The item is **invalid** (`contradictory_distractor_statement`, high) | The distractor's number is the manipulated variable of this benchmark; a self-contradicting distractor makes the cue ill-defined |
| J3 | Severity | `high` only when a certified answer or a physics claim is wrong, or the item fails J1/J2; wording, boundary-convention and unit-display nitpicks are `medium` or `low` and do not make an item invalid | GPT rejected 5 of 14 valid items on edge cases; Claude accepted every valid item; both directions miss the intended standard |

These go into judge prompt v2; both judges are requalified on a fresh planted set (protocol: a changed prompt is
requalified only on unseen items).

## A. Statistical rules

| # | Decision | Status | Reason |
|---|---|---|---|
| 1 | TRIVIAL_EFFECT supports H6-RD (reported as "trivial departure within SESOI"); only EQUIVALENT supports H0 | DECIDED | the SESOI defines what matters for correct selection; H0 is worded as "no effect" |
| 2 | G4 decision = Holm-adjusted sign-flip rejection; labels from the one-sided bound for F1/F2 (already in code: the 90% two-sided interval) | DECIDED (code done, J15.1-013) | a label can no longer contradict its test |
| 3 | "Extends beyond the margin" = any part of the interval beyond the SESOI; the point estimate's position is reported beside | DECIDED | conventional reading of the four-outcome language |
| 4 | Minimum evaluable structures for any status: **6** | DECIDED + CODE | below J = 6 the exact two-sided sign-flip test cannot reach p < 0.05 (2/2^5 = 0.0625) |
| 5 | Method agreement (t, sign-flip, bootstrap, mixed model) and drop-1-to-3-structures robustness implemented before the freeze | DECIDED + CODE | required by the plan (B6.4, P4.6); cheap |
| 6 | Phrasings disagree: pooled status INCONCLUSIVE flagged WORDING_DEPENDENT, per-phrasing statuses beside | DECIDED | a role claim needs agreement across phrasings (plan) |
| 7 | F3 per value **index** step, stated in the card | DECIDED | the SESOI was reasoned per step; values are not equally spaced |

## B. Thresholds

| # | Decision | Status | Reason |
|---|---|---|---|
| 8 | R-tracking criterion: T_R >= **0.40** (point estimate) on >= 16 evaluable structures, absolute | DECIDED (**departs from draft 0.50**) | in-band no-cue estimation shares are 0.53-0.60 (J15.1-014/022); a 0.50 floor sits inside sampling noise of the expected level and would pass or fail a model by chance; 0.40 rejects only clear failure to use relevant quantities. No R-cell data was seen (the pilot is sealed) |
| 9 | Band [0.30, 0.85] on k_sel = 4 no-cue samples pooled over instances | DECIDED | fixed before any record (J15.1-006) |
| 10 | H5 SESOIs: response length log(1.2), budget exhaustion 0.05 | DECIDED | a fifth longer response or five more exhausted budgets per hundred is a practical cost |
| 11 | H5 comparator: N primary, no-cue beside | DECIDED | same comparator as every other D contrast (inconsistency H7) |
| 12 | H4 trace rule: trace-correct share >= 0.50, frozen rule-based extractor tested on synthetic traces before G3; otherwise H4 is NOT_EVALUATED in G3 | DECIDED + CODE (before G3) | no LLM judge in the outcome path |
| 13 | Misuse attribution: share above N's at >= 2 of 3 values, excludes zero, not confounded in more than half the structures; fewer than 5 matches = INCONCLUSIVE | DECIDED | rare categories (plan) |
| 14 | Mechanism SESOIs (G5-G7 cards): planning values T3 I_role 0.10, T1/T2 1.0 nat recorded; frozen when each card's gate opens | DEFERRED (**departs from draft**) | the plan allows freezing a card at its gate; freezing now has no data behind it and G5 is gated on G4 |

## C. Design and sampling

| # | Decision | Status | Reason |
|---|---|---|---|
| 15 | No adaptive sampling in G3: J = min(40, eligible), fixed k | DECIDED | adaptive rules add researcher degrees of freedom for little gain |
| 16 | k = 8 per R/D cell; N **and** no-cue sampled 6k each (fully balanced) | DECIDED (**draft offered a cheaper no-cue**) | vLLM made generation cheap (2,080 samples in minutes); balance keeps every interval free of the J15.1-011 skew |
| 17 | Held-out values (m >= 5) not run in G3; run in G4 as a committed prediction from the G3-attributed curves | DECIDED | a true out-of-sample test of the misuse curves |
| 18 | Non-physics control: 16 structures, R/D x 3 values x 2 phrasings | DECIDED | enough to estimate, explicitly not powered (plan: a null there is INCONCLUSIVE) |
| 19 | G4 opens with a no-cue calibration pass (k_sel = 4) on sealed structures in a seeded order; in-band ones enter until J is reached; estimation and role cells use fresh samples | DECIDED | in-band status needs selection samples; selection and estimation stay disjoint |
| 20 | G4 meets its rule if (a) at least one of F1-F3 is Holm-rejected in its predicted direction with label EFFECT, or (b) all three are EQUIVALENT/TRIVIAL with R tracking >= the criterion (H6-RD); "replicated" also needs the G3 direction for every contrast that was EFFECT in G3 | DECIDED | makes the G4 gate numeric |
| 21 | G4 size from a simulation of joint TOST power (F1-F3) using G2 variance components; more sealed structures opened if needed (270 available) | DECIDED + CODE (before G4) | planning J = 50 does not power joint equivalence at omega >= 0.2 |

## D. Secondary family and order

| # | Decision | Status | Reason |
|---|---|---|---|
| 22 | C and K together form one "C/K extension" family (Holm within it) | DECIDED | otherwise H6-extended could never be confirmed |
| 23 | Priority: C/K, unit/plausibility, relevance instruction, cost, position, proximity | DECIDED | order of scientific importance; fixed now, not chosen from G3 estimates |
| 24 | Fixed sequence: primary F1-F3, then misuse attribution (only after F1 passes), then the G3-chosen family only after the primary family meets its rule | DECIDED | controls family-wise error without spending alpha on secondaries |

## E. Hypothesis mapping

| # | Decision | Status | Reason |
|---|---|---|---|
| 25 | Add **H3-R** (selection failure by over-ignoring relevant quantities) to the scorecard, scored by F2 EFFECT; labelled as an addition to the plan's table | DECIDED | otherwise an F2 effect supports no hypothesis (inconsistency H3) |
| 26 | Add a `digit_copy` foil (same digits, target unit) for incompatible-unit cells before the unit ablation | DECIDED + CODE | lets H1's "every unit" and H2's copy test be scored |

## F. Causal claim types

| # | Decision | Status | Reason |
|---|---|---|---|
| 27 | T1 prefix type (ii) primary (the model's own trace under N), type (i) gold trace as sensitivity, for X07, X08, X10; X09 and X11 T2/T3 only | DECIDED | the model's own trace is the realistic state; the gold trace isolates the readout |
| 28 | Compatibility strata: tertiles of the prefix NLL difference computed on the G5 discovery split, frozen before the held-out test | DECIDED | no data justify fixed cut-points now |

## G. Primary-model rule

| # | Decision | Status | Reason |
|---|---|---|---|
| 29 | Qwen3-8B thinking off before thinking on | DECIDED | thinking on currently ends 35% non-complete (J15.1-022) |
| 30 | Extended HF-vs-TL parity is a G2 criterion (option a); the parity job is scheduled now so it runs before G2 ends | DECIDED + GPU | the queue starts workers within a day; option (b) is the recorded fallback only if the job cannot run in time |
| 31 | Every model configuration whose records come from vLLM needs its own vLLM-vs-HF greedy parity (rule of J15.1-006) | DECIDED + GPU | only Qwen2.5-7B passed so far; Llama-3.1-8B and Qwen3-8B (thinking off) parity runs are scheduled |
| 32 | The second model must have different weights; same vendor allowed, disclosed | DECIDED | a thinking toggle of the same weights is not a second model |
| 33 | G5 held-out pool: the unopened INTERNAL_CONFIRMATION remainder; shadow set and ADVERSARIAL/G6 reserve untouched | DECIDED | keeps G4 and G6 reserves clean |

## H. Plan inconsistencies (resolved)

| # | Resolution |
|---|---|
| 1 | Compute rows understate generations under the balanced design (+71% with no-cue balanced); moot in practice under vLLM; the compute section is updated at the next plan revision |
| 2 | The "presence" estimand duplicates F1 under the declared view; reported under F1, not as a separate estimand |
| 3 | Resolved by decision 25 (H3-R) |
| 4 | H0 and H6-RD are co-scored on the core cells; both statuses are reported |
| 5 | Resolved by decision 21 |
| 6 | Resolved by decision 2 (code already changed) |
| 7 | Resolved by decision 11 |
| 8 | Resolved by decision 30 |
| 9 | Consistent: the band was committed in J15.1-006 before any calibration record existed, and calibration was read only through that frozen rule |

## What still stands between this and the G1 freeze

1. Code: decisions 4, 5 (statistics), 12 (H4 extractor, before G3), 21 (joint power, before G4), 26 (digit_copy foil); the
   G3 scorecard as code (currently a document).
2. LLM panel: judge prompt v2 (J1-J3), a fresh planted set, requalification of both judges.
3. GPU: extended HF-vs-TL parity (30); vLLM parity for Llama-3.1-8B and Qwen3-8B (31).
The sealed M0 pilot stays sealed until items 1 (scorecard and statistics code) and the cards are frozen.
