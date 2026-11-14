# ADOPTED 2026-11-13 as amended by `decisions_2026-11-13.md` (G1 freeze pending the items listed there): experiment cards X01-X12

Status: DRAFT, written 2026-11-13 by an agent (CPU only; nothing was run for this file). Not frozen until the user
approves it and the decision log records the G1 freeze.

Source of truth: plan of record `docs/proposals/PhysMon_Research_v2.tex`, section "Twelve decisive experiment cards"
(`sec:cards`, the cards `card:X01`..`card:X12`). Section numbers below follow the order of the `.tex` (4 = framework,
5 = execution, 7 = cards, 8 = statistics, 9 = compute); labels are given so they can be checked.
Frozen analysis code: `src/physmon/analysis/rolevalue_stats.py` (cited as `rvs.<function>`).

Conventions used in every card:

- **PLAN** = value or rule stated in the plan, with the plan's reason. **PROPOSED** = agent proposal with its reasoning,
  not decided; each is also listed in `open_questions_for_user.md`.
- The card rule kept from the October edition applies (`sec:cards`): no new estimand or panel mid-run; a card with
  zero evaluable records reports NOT_EVALUATED, never a zero effect.
- Strata are never pooled (`sec:strata`, rule 3). Every primary contrast is reported three ways: all attempted
  samples, complete-case, budget-exhausted counted wrong (`sec:statistics`, negative and missing result policy).
- SESOI values are those coded in `rvs.SESOI` (PLAN, `sec:statistics` "Effect sizes, equivalence and the language of
  null results"): F1 0.10 tracking share; F2 0.10 neglect-minus-placebo share; F3 log(1.5) per value step (odds
  ratio 1.5); lambda_D 0.10 (descriptive). Their reasons are in `rvs.SESOI_REASONS`.

---

## X01 - Authoritative reproduction

| Field | Content |
|---|---|
| Plan | `card:X01`; G0 item 3 (`sec:gates`) |
| Question | Can committed Phase-I values and the hook stack be trusted for later work? |
| Hypotheses | None of H0-H6 (integrity) |
| Data role / population | Committed Phase-I records (historical); no new items |
| Cells and sizes | PLAN: forward-pass spot check of 10 legacy families only if a Phase-I number is ever cited again; full regeneration off the critical path (D1 default) |
| Primary estimand | Equality to reported denominators, checksums and endpoint values within declared precision |
| Analysis | Done (exploratory) for committed records (J14.1-008); NOT re-run |
| Decision rule | PLAN: if extended HF-vs-TL parity fails for a model or backend, no mechanism work on it; behaviour can proceed |
| SESOI | Not applicable (reproduction to declared numerical precision) |
| Claim type | None (no causal claim) |
| Against | A mismatch localised to code or provenance blocks dependents (October no-go) |
| Gate | G0 (status: G0 NOT PASSED, extended parity outstanding; `docs/status/stage15_progress_vs_v2_plan.md` section 2) |

## X02 - Base-variant invariance challenge

| Field | Content |
|---|---|
| Plan | `card:X02` |
| Question | Does the legacy signed label depend on the arbitrary base rendering? |
| Hypotheses | None (measurement validity) |
| Data role / population | Stored Phase-I four-value arrays; historical |
| Cells and sizes | Done; no new work |
| Primary estimand | Reclassification matrix, rank concordance |
| Analysis | Done (exploratory, J14.2-006); no-go met; legacy label retired (J14.2-011) |
| Decision rule | PLAN: replacement is O1-O6 with O4 primary, not another teacher-forced label |
| SESOI | Not applicable |
| Claim type | None |
| Against | Not applicable (closed) |
| Gate | G0 (closed for this card) |

## X03 - Format/tokenization falsification

| Field | Content |
|---|---|
| Plan | `card:X03`; G4 format rule (`sec:gates`, G4) |
| Question | Does the final-answer format change the behavioural role-by-value effect? |
| Hypotheses | Alternative to every role reading (format artefact); bears on H1-H6 interpretation |
| Data role / population | G4 INTERNAL_CONFIRMATION structures, calibrated in-band population of the primary model |
| Cells and sizes | PLAN: two declared final-answer formats, each on a random half of the G4 items. PROPOSED: the half is drawn by a seeded permutation (seed 42, the project seed of `sec:statistics`) of the opened G4 structure ids, fixed before G4 opens; reason: randomisation by structure (the unit) and fixed before any output |
| Primary estimand | F1, F2, F3 estimated separately per format, each with its interval |
| Analysis | `rvs.structure_estimates` + `rvs.paired_summary` per format subset (exists); the format-dependence comparison itself NOT YET IMPLEMENTED |
| Decision rule | PLAN (planning value, G4): the reading changes if the format-specific effects differ by more than a factor of two or have opposite signs with both intervals excluding zero |
| SESOI | Same as F1-F3 (PLAN) |
| Claim type | None (behavioural) |
| Against | Format dependence under the rule above ties the effect to output elicitation (October no-go) |
| Gate | G4 (format robustness moved into G4 by the plan); format failures are O3 categories, never WRONG |

## X04 - Physics-semantic factorial (becomes the role-by-value factorial)

The plan splits this card across G3 (discovery) and G4 (one preregistered family). Two parts below.

### X04-G3 - Behavioural discovery

| Field | Content |
|---|---|
| Plan | `card:X04` Revision; G3 (`sec:gates`); `sec:rolevalue`; `sec:hypotheses`; `sec:datasetplan` |
| Question | Which of H0-H6 describes the primary model on certified role-by-value structures, and what deserves G4 and G5? |
| Hypotheses | H0-H6, scored by `g3_scorecard_thresholds.md` (not exclusive) |
| Data role / population | EXPLORATION pool of M250 (130 structures). Primary population: complete, calibrated in-band structures of the primary model; all-validated structures reported for the same cells where run (PLAN, G3 item 1) |
| Cells and sizes | PLAN: 24-40 complete calibrated structures; core cells no cue, R and D at 3 values x 2 phrasings (12 cells), the non-numeric sentence N; plus the small non-physics control. PLAN (frozen design rule, J15.1-011): N sampled n_values x n_phrasings x k = 6k times per structure, because one N cell of k samples made the one-sided F1 sign-flip test reject a true null at 0.059-0.074. PROPOSED: J = min(40, eligible), k = 8 per R/D cell [amended 2026-11-14 by plan_revision_v2.2, section E: k = 24; agreement rule B; decision 21 target = EQUIVALENT or TRIVIAL: k = 24 per R, D, C and K cell; C and K are in the core; N and no-cue 6k = 144], no-cue sampled 6k (reasons and alternatives in `sampling_and_selection_rules.md`). Targeted ablations (C, K, marking, unit and proximity, position, relevance instruction, formula hint, convertible units) only after the core result, 6 cells each (PLAN, `sec:compute-budget`) |
| Non-physics control | PROPOSED: 16 GSM-DC-style structures, same R/D x 3 values x 2 phrasings design. Reason: with an assumed per-structure SD of 0.25 (the plan's planning omega) a 95% interval half-width is about 2.13 x 0.25 / 4 = 0.13, enough to see a large effect, never enough for equivalence; the plan already makes a null here INCONCLUSIVE (G3 item 3) |
| Primary estimand | O4: F1 (T_N - T_D), F2 (neglect share - placebo rate), F3 (R minus D slope of empirical-logit tracking per value step); misuse and copy shares; lambda and Lambda descriptive with the MULTIMODAL guard. O1-O3, O5 always reported |
| Analysis | `rvs.structure_estimates`, `rvs.primary_family` (no Holm reading in G3: G3 is estimation, `sec:statistics` multiple comparisons), `rvs.phrasing_agreement`, `rvs.misuse_support`, `rvs.jeffreys`, `rvs.beta_binomial_fit`, `rvs.lambdas`. NOT YET IMPLEMENTED: population-level misuse excess, copy share in R, O5 contrasts, drop-1-to-3 robustness, scorecard assembly, C/K versions of F1/F3 |
| Decision rule | Scorecard statuses per `g3_scorecard_thresholds.md`. PLAN: the G4 primary family is fixed now, whatever G3 shows; G3 may add at most one secondary family by the rule in `sampling_and_selection_rules.md` |
| SESOI | F1 0.10, F2 0.10, F3 log(1.5), misuse shares 0.10 (PLAN); O5 PROPOSED (scorecard file) |
| Claim type | None (behavioural). The optional exploratory mechanism pilot of G3 is never confirmatory (PLAN) |
| Against | `sec:conditional-kept`: no role-by-value interaction means physical-role selection is not supported for that stratum; test H1, H2, H0 instead; never add post-hoc cue types |
| Gate | G3. If G3 R tracking is below the G1 criterion (`r_tracking_criterion.md`), the role result is uninterpretable for role (PLAN) |

### X04-G4 - Preregistered role-by-value family (internal part of X06)

| Field | Content |
|---|---|
| Plan | G4 (`sec:gates`); `sec:statistics` multiple comparisons and power; `card:X06` Revision |
| Question | Is the role-by-value pattern real beyond development data? |
| Hypotheses | Confirms or disconfirms H3 (D loss attributed to misuse), H6-RD (F1-F3 equivalent); H4 only if its trace estimand is in the family (see open questions) |
| Data role / population | Sealed INTERNAL_CONFIRMATION pool (M250 120 + M500 150 = 270), untouched template clusters, opened once; shadow set (50) never opened; calibrated in-band population of the primary model |
| Cells and sizes | PLAN: J from the power simulation (one-sided bracket J about 6.2 omega^2 / delta^2, about 17-39 at omega 0.25, delta 0.15-0.10; planning at least 50 complete and in-band per model); k = 8 [amended 2026-11-14 by plan_revision_v2.2, section E: k = 24; agreement rule B; decision 21 target = EQUIVALENT or TRIVIAL]; second answer format on half the structures. Note: joint equivalence of F1-F3 for H6-RD needs more (see open questions, item on G4 power) |
| Primary estimand | F1, F2, F3 as in G3 |
| Analysis | `rvs.primary_family`: F1 one-sided, F2 one-sided, F3 two-sided; sign-flip p primary (J15.1-011), Holm at family-wise alpha 0.05 (`rvs.holm`); TOST within SESOI for H6-RD (`rvs.tost_p`); misuse attribution as a secondary family, Holm across curves, each in its predicted direction, only after F1 passes (NOT YET IMPLEMENTED at population level); the G3-chosen secondary family after the primary family (PLAN). Second model by fixed sequence only if the primary passes (PLAN) |
| Decision rule | PLAN: G4 passes when the primary family meets its rule on the primary model; else the G3 pattern is "not replicated". "Meets its rule" is not defined numerically in the plan; PROPOSED definition in open questions |
| SESOI | F1 0.10, F2 0.10, F3 log(1.5) (PLAN) |
| Claim type | None (behavioural; CL2) |
| Against | Failure of the rule: G3 pattern reported as not replicated; never reopen the cohort |
| Gate | G4. Labelled EXPLORATORY-REPLICATION unless every G4 item is LLM_PANEL_VALIDATED by the full panel (Claude, GPT, Gemini; D2) |

## X05 - Structural leakage and real OOD monitoring

| Field | Content |
|---|---|
| Plan | `card:X05`; G7 (`sec:gates`) |
| Question | Does a monitor generalise across structure clusters? (side track) |
| Hypotheses | None of H0-H6 (CL3) |
| Data role / population | Legacy families and clusters (EXPLORATION); any new monitor targets an O1/O4 event on role-by-value cells |
| Cells and sizes | Not scheduled (D6 default) |
| Primary estimand | Paired cluster-held-out AUROC and log loss vs fitted entropy (oracle) and surface/AST baseline (deployable) |
| Analysis | NOT YET IMPLEMENTED for new monitors; legacy monitor NOT_EVALUATED (activations wiped) |
| Decision rule | PLAN: collapse under cluster folds means no out-of-structure deployment claim |
| SESOI | PROPOSED: deferred to G7 opening (estimand frozen when the card's gate opens, `sec:cards` rule) |
| Claim type | None |
| Against | Matching entropy under an adequately powered test: no deployment claim (`sec:conditional-kept`) |
| Gate | G7 (optional) |

## X06 - Frozen external behavioural replication

| Field | Content |
|---|---|
| Plan | `card:X06`; G4; G6 |
| Question | Does the role-by-value effect replicate on independent items? |
| Hypotheses | Same as X04-G4 |
| Data role / population | Internal part: X04-G4 (INTERNAL_CONFIRMATION). External part: EPC_CONFIRMATION items, each re-certified and re-validated as a new item (`sec:rolevalue` "Adapted problems") |
| Cells and sizes | Internal: see X04-G4. External: sized after G4 (PLAN, `sec:compute-budget` "G6, G7 sized after G4") |
| Primary estimand | O4 (F1-F3) with O1-O3, not a reference-free likelihood (PLAN) |
| Analysis | As X04-G4 |
| Decision rule | Internal: X04-G4. External: PROPOSED, frozen when G6 opens: the G4 family re-tested with the same estimands, one-sided in the G4 direction |
| SESOI | As F1-F3 |
| Claim type | None (behavioural) |
| Against | No effect on the external panel: narrow the thesis, investigate distribution mismatch, never cherry-pick (October no-go) |
| Gate | G4 (internal), G6 (external) |

## X07 - H11 lesion/patch specificity (retired as stated; replacement: localisation found anew)

| Field | Content |
|---|---|
| Plan | `card:X07` Revision; P6 (`sec:blockP6`); `sec:causal` |
| Question | Which components, if any, carry the role-by-value contrast that passed G4 (I_role != 0), as opposed to a numeral-cue component (I_presence only) or a general answer component? |
| Hypotheses | The G4-established one of H3, H4, H6-RD |
| Data role / population | PROPOSED: discovery screen on EXPLORATION structures (the G3 set); held-out tests on sealed INTERNAL_CONFIRMATION structures not opened by G4. Reason: P6.1 requires discovery and test on disjoint structures, and G4-opened structures were part of a confirmatory read |
| Cells and sizes | Role-by-value minimal pairs (R/D twins at the same z; same role at two values), token-aligned, several per item (PLAN P6.1). Sizes frozen when G5 opens (PLAN `sec:cards` rule; `sec:compute-budget` "card-specific") |
| Primary estimand | I_role = Delta_h m_D - Delta_h m_R under T3 (tracking against each world's own answer, or answer-mode shares) or T2; I_presence = Delta_h m_D - Delta_h m_N, any declared metric; clean effects beside both (PLAN `sec:causal`) |
| Analysis | `src/physmon/causal/interaction.py` (G0 item 2c: refuses raw gold scores across worlds); patching code NOT YET IMPLEMENTED |
| Decision rule | PLAN (Gate P6): a role component needs I_role != 0 under T2 or T3, robust across ablation semantics (resample/interchange primary, mean sensitivity), on held-out structures; I_presence alone = numeral-cue component; equal effect on D, N, R = general answer component |
| SESOI | PROPOSED: T3 I_role 0.10 in tracking share (same behavioural reason as F1: an intervention that moves role-specific tracking by less than the behavioural SESOI cannot explain the behaviour); T1/T2 log-odds 1.0 nat (reason: more than 5x the bf16 dtype noise SD of 0.09-0.19 nats measured in Stage 14, J14.9-003/004, `sec:phaseB-B6` B6.5; fixed before any data, unlike the retired post-hoc 0.5 nat, `docs/registry/v2/threshold_history.md`) |
| Claim type | T3 primary for any role claim (I_role); T1 allowed only as a readout screen for I_presence. T1 prefix type: PROPOSED (ii) the model's own trace under the N prompt, every sampled trace regardless of answer; (i) gold trace from the typed graph as sensitivity. Compatibility stratum: per-token NLL of the prefix under the recipient (D) prompt minus under the donor (N) prompt; PROPOSED tertile cutpoints computed on the discovery split and frozen before the held-out test; all prefixes reported and by stratum, none excluded (PLAN `sec:causal` T1 row) |
| Against | Effect only under zero/mean ablation; effect only on gold-string likelihood (T1); equal effect on all prompts (`sec:conditional-kept`) |
| Gate | G5; gated on G4 and on G0 extended parity in the study dtype |

## X08 - Mechanistic function discrimination

| Field | Content |
|---|---|
| Plan | `card:X08` Revision; P7 (`sec:blockP7`) |
| Question | Which function (F-copy/H1, F-match and F-unit/H2, F-role/H3, readout/H4, correct selection/H6, F-position) explains held-out intervention effects? |
| Hypotheses | H1, H2, H3, H4, H6 via the P7.2 mapping |
| Data role / population | As X07 replacement (discovery EXPLORATION; held-out unopened INTERNAL_CONFIRMATION; second model) |
| Cells and sizes | Each function needs at least two interventions with differing predictions (same digits/incompatible unit; same magnitude/digit-disjoint; tokens moved; R twin or role reversal) on a held-out grid (PLAN P7.2). Sizes frozen at G5 opening |
| Primary estimand | Sign and size of I_h per function, committed before the test (PLAN checklist item 14); effect-direction accuracy on unseen structures |
| Analysis | NOT YET IMPLEMENTED |
| Decision rule | PLAN (Gate P7): advance only if one explicit function predicts effect direction across independent manipulations and survives T2/T3 tests. PROPOSED numeric: a function "predicts" when its committed sign is correct on at least 2 of 2 discriminating interventions with the held-out 95% interval excluding zero; reason: the plan requires two discriminating interventions per function, so the minimum is both |
| SESOI | As X07 (PROPOSED) |
| Claim type | Readout function (H4): T1 at answer positions, prefix type (ii) primary, (i) sensitivity, ΔNLL tertile strata (PROPOSED as in X07). All other functions: T2 (teacher-forced prefix up to the step where q enters; C/K intermediate use not penalised) or T3. Only T2/T3 support a computation claim (PLAN) |
| Against | No simple function predicts: widen to distributed mechanism; never label from top-activating examples (October no-go) |
| Gate | G5. If G3/G4 read H1 or H2, only the unit-matching study runs (PLAN) |

## X09 - Source-to-sink circuit and rescue

| Field | Content |
|---|---|
| Plan | `card:X09` Revision; P8; `sec:causal` checklist items 5, 7, 8, 10, 11 |
| Question | Is there a validated path from the quantity's tokens to the answer, with within-structure rescue? |
| Hypotheses | The G4-established one of H3, H4, H6-RD |
| Data role / population | Discovery graph on EXPLORATION; separate causal test panel on unopened INTERNAL_CONFIRMATION (PROPOSED, as X07) |
| Cells and sizes | Rescue within structure, value-matched, R vs D twins first; cross-structure donors later (PLAN). Sizes frozen at G5 opening |
| Primary estimand | Absolute log-odds and I_h, never normalised recovery; DAS interchange-intervention accuracy on held-out pairs vs neuron and random-subspace baselines (PLAN) |
| Analysis | NOT YET IMPLEMENTED |
| Decision rule | PLAN: source path not validated means the circuit claim is removed |
| SESOI | As X07 (PROPOSED); DAS accuracy margin PROPOSED to be fixed at G5 opening (no basis yet) |
| Claim type | T2 or T3 only; T1 not used for path claims (PLAN: only T2/T3 support a computation claim). No T1 prefix needed |
| Against | Rescue fails: redefine on discovery data or fall back to localisation (`sec:conditional-kept`) |
| Gate | G5 |

## X10 - Architecture functional replication

| Field | Content |
|---|---|
| Plan | `card:X10` Revision; G6 |
| Question | Does the frozen function (not component index) recur in the second model and the reasoning variant? |
| Hypotheses | As established in G5 |
| Data role / population | Second model fixed by the G2 primary-model rule (planning Llama-3.1-8B-Instruct), searched only if its own behavioural test passed; Qwen3-8B thinking on/off; Qwen3-32B only for frozen-function transfer |
| Cells and sizes | Sized after G5 (PLAN) |
| Primary estimand | Sign-consistent intervention effects for the function |
| Analysis | NOT YET IMPLEMENTED |
| Decision rule | PLAN: non-replication means an architecture-specific account with stated scope |
| SESOI | As X07 (PROPOSED) |
| Claim type | Reasoning variant: T1 on a fixed trace, prefix type (ii) (the model's own thinking trace under N, every sampled trace), ΔNLL tertile strata (PROPOSED); T3 with on-policy resampling; never a hand-edited trace as primary evidence (PLAN checklist item 12) |
| Against | Same-layer miss is not architectural absence (`sec:conditional-kept`) |
| Gate | G6 (gated on G4 and a G5 result) |

## X11 - Selective mitigation challenge

| Field | Content |
|---|---|
| Plan | `card:X11` Revision; G7 |
| Question | Does a mechanism-guided edit beat the cheap ladder (relevance instruction, self-consistency, longer budget), solver routing and cue removal? |
| Hypotheses | Downstream of G5 |
| Data role / population | External OOD and role-reversal panels; sized after G4 |
| Cells and sizes | Sized after G4 (PLAN) |
| Primary estimand | O1 (with O2); harm on R cells as O4; cost O5; every comparator tagged oracle or deployable (PLAN) |
| Analysis | NOT YET IMPLEMENTED |
| Decision rule | PLAN: if a simpler filter wins, the edit is a causal diagnostic, not a product |
| SESOI | PROPOSED: harm SESOI on R tracking 0.10 (same reason as F2: a tenth of R answers lost to the edit matters); frozen at G7 opening |
| Claim type | T3 (generate after the edit) |
| Against | Cheap filter or relevance instruction dominates (`sec:conditional-kept`) |
| Gate | G7 (optional) |

## X12 - External audit and claim freeze

| Field | Content |
|---|---|
| Plan | `card:X12` Revision; `sec:claims` |
| Question | Do the three strongest claims survive predeclared falsifiers on an untouched final cohort? |
| Hypotheses | Whatever survived G4-G6 |
| Data role / population | External cohort (independently authored or adapted, each certified); ADVERSARIAL_CHALLENGE and G6 reserve of M500 (50) |
| Cells and sizes | Sized after G4 |
| Primary estimand | CL1-CL6 claim matrix with raw artifacts and uncertainty |
| Analysis | `scripts/check_claim_wording.py`, `scripts/check_provenance_consistency.py` (exist, G0 items 2e/2f); forbidden-phrase check |
| Decision rule | PLAN: failed claims are contracted; never tune on the external test |
| SESOI | Per claim, inherited from the card that produced it |
| Claim type | Inherited |
| Against | The claim's predeclared falsifier |
| Gate | G6 |
