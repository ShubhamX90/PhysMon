# DRAFT for user review (G1 freeze): minimum R-tracking criterion

Status: DRAFT, 2026-11-13, agent-written, nothing run. Implements G1 element "the minimum R-tracking criterion checked
in G2" (plan `sec:gates` G1; G2 item 3; G3 gate; H6 row of `sec:hypotheses`).

## 1. What the plan fixes (PLAN)
- G2 item 3: "A minimum tracking share on R cells, fixed numerically in G1, is checked here: a model or budget below it
  does not use added relevant quantities reliably enough for any role reading, and is changed or dropped at this gate,
  never after G3."
- G2 gate: passes only if the R-tracking check passes; "the band and the R criterion are not changed after seeing G2
  results".
- G2 item 4: the R-tracking criterion is one of the primary-model criteria.
- G3 gate: if R tracking in G3 falls below the criterion, the G3 role result is uninterpretable for role (itself a
  finding); items and band are not changed on the same data.
- H6 (both scopes) requires R tracking at or above the criterion.
- The plan gives no number.

## 2. Proposed value

**PROPOSED: T_R >= 0.50**, where T_R is the mean over structures of the structure-level R tracking share (definition in
section 3), assessed on the point estimate, per configuration (model x thinking mode x token budget).

Reasons:
1. **Majority rule.** At 0.50 the modal R sample tracks the certified response y*_R(z). Below it, "R responds
   correctly", the condition that separates H3's evidence against (invariance in D *while R responds correctly*) and
   H6 from a model that ignores or fumbles every added quantity, does not describe the model's typical answer.
2. **Absolute, not relative to no-cue.** A relative rule (T_R vs no-cue accuracy) would measure the cost of adding a
   relevant quantity, which is close to a cue effect; the primary-model rule must "never depend on observed cue
   effects" (G2 item 4). An absolute capability floor avoids selecting models on the effect under study.
3. **Compatible with the band.** The proposed band is no-cue selection share 0.30-0.85
   (`sampling_and_selection_rules.md`), midpoint about 0.575. A model whose R cells cost no more than a few points over
   its no-cue accuracy passes; one whose R cells lose much more is exactly the model the plan says cannot support a
   role reading.
4. **Room for the neglect contrast.** With T_R >= 0.50, an F2 neglect excess at its SESOI (0.10) is a minority mode and
   is not confounded with general failure.

Point estimate rather than an interval bound (PROPOSED): G2 measures R tracking on about 20 structures in one phrasing
(PLAN G2 item 2 and `sec:compute-budget`); with a per-structure SD near 0.25 the 95% half-width is about 0.12, so a
lower-bound rule (e.g. lower bound >= 0.40) would reject most models that truly sit at 0.50-0.55. The interval is
reported beside the decision.

Minimum evidence (PROPOSED): at least **16 evaluable structures**, each with R cells at 3 values; fewer means the
check is NOT_EVALUATED and G2 does not pass on it. Reason: the plan's G2 subset is "about 20 structures" and its power
protocol assumes 20-40% loss to infeasible cells, parse failures and budget exhaustion (`sec:statistics` power);
20 x 0.8 = 16.

## 3. How it is computed from records
1. Records: G2 calibration records of the R cells (3 study values, 1 phrasing, a few samples each; PLAN G2 item 2),
   on in-band structures selected by the selection samples only.
2. Per sample: T = `rvs.tracking(record)` = 1 if `completion_status == COMPLETE` and `grade_declared == correct`
   against the cell's own certified y*_R(z), else 0, over all attempted samples (non-COMPLETE counts 0; PLAN
   `sec:rolevalue` estimand 1). Held-out values are excluded.
3. Per structure: T_R(s) = `rvs.structure_estimates(records, cells)[s]["T"]["R"]` (mean over values, phrasings and
   samples).
4. Per configuration: T_R = unweighted mean of T_R(s) over evaluable structures (the structure is the unit,
   `sec:statistics`), with `rvs.bootstrap_ci` (2,000 resamples, seed 42).
5. Reported beside (not used for the decision): complete-case T_R; T_R under the convertible and 1% views; T_R by
   value and by phrasing; O3 composition of R records; no-cue estimation-sample accuracy on the same structures.
6. NOT YET IMPLEMENTED: a function that applies the criterion and writes the verdict (steps 2-4 use existing
   functions).

In G3 the same computation runs on the G3 R cells (both phrasings, all G3 structures); in G4 on the G4 structures
(needed for H6-RD there).

## 4. What happens below it (PLAN)
- **G2:** the configuration is changed (budget, thinking mode, harder or easier variants) or dropped at G2, never after
  G3; G2 is repeated. A model that cannot be brought to the criterion and the band is reported on the all-validated
  population only, and its band-based discovery is not run.
- **Primary-model rule:** a configuration below the criterion cannot be primary or second.
- **G3:** below the criterion, the G3 role result (H3, H6) is NOT_EVALUATED, reason "uninterpretable for role",
  reported as a finding; band and items are not changed on the same data.
- **H6:** never SUPPORTED below the criterion, in G3 or G4.
- The value 0.50 is not changed after any G2 R-cell record is read.
