# Analysis of the ICLR 2027 reviews of submission 50608 (withdrawn 2026-11-11)

Written 2026-11-11 after reading the full submitted paper (25 pages, `confidence_without_cause_iclr2027_submission50608.pdf`) and all four reviews with the authors' replies (`reviews_and_responses.md`).
Scope of this document: understand the reviews, check what can be checked against this repository, and record what they imply. It does **not** change the plan of record: updating `docs/proposals/PhysMon_Research_v2.pdf` is the next step and is deliberately not done here.
Provenance labels: **[V]** verified by recomputation from committed files (`results/reviews/iclr2027_submission50608/attempt_20261111/claims_check.{json,md}`, produced by `scripts/reviews/check_iclr2027_review_claims.py`), **[R]** stated by a reviewer and not checked here, **[T]** result from the teammate's Stage 14 work already in the repo, **[I]** my inference.
Data role EXPLORATION. Nothing here is a confirmation or paper-eligible evidence.

## 1. Outcome

| Reviewer | Rating | Soundness | Depth of engagement |
|---|---|---|---|
| Y9cR | 1 (clear rejection) | 1 | Re-scored released artifacts; cites files and line numbers; dozens of specific numerical claims |
| BzwY | 1 (clear rejection) | 1 | Interpretation of the label, causal reading, probe value; asks 5 questions |
| BWJ6 | 3 (weak accept) | 2 | Two concerns: knockout interpretation, template-cluster leakage |
| Bsyk | 3 (weak accept) | 2 | Cue C pooling, task scope, absence of downstream use |

All four reported confidence 2 ("broad familiarity, little or no direct research experience on this topic"). The authors withdrew on 2026-11-11 and, in every reply, accepted the specific criticisms rather than contesting them. The two accepting reviewers raised a subset of what the rejecting reviewers raised: BWJ6 criticized the causal reading and the cluster leakage; Bsyk did not address the causal claim and focused on Cue C pooling, task scope and downstream use.

## 2. What the paper claimed (for reference)

DECOY: 155 families x 4 renderings differing in one cue (A irrelevant variable 35, B unit-matched distractor 105, C equivalent units 15), certified by a SymPy free-symbol test. Label `S_lp` = largest drop of the teacher-forced log-probability of the certified answer relative to base rendering 0, threshold 0.5 nats "registered 2026-06-14". Results: Qwen 70/140 sensitive, Llama 32/140; L18 mean-state probe AUROC 0.760 (single rendering 0.747 at L16); "on par" with a fitted entropy baseline 0.727; correctness probe 0.766; frozen probe 0.820 pooled on 15 later families (0.667 / 0.6875 within cue type); four-head L16 knockout normalized recovery 1.870 on 20 Cue B families, "cancels the sensitivity", "necessary"; DeepSeek and Llama no reliable effect. Contributions (a) certified benchmark, (b) measurement, (c) pre-generation monitor, (d) paired-baseline evaluation standard, (e) causal handle.

## 3. The reviewers' specific numerical claims, checked [V]

`check_iclr2027_review_claims.py` recomputes each checkable claim from committed data. Result: **21 of the 23 checks reproduce the stated value** (the 21 include the paper's own Table 1 and Table 4 values and one sanity check; C7b needed an explicit unit definition), 1 was computed because the reviewer only requested it (C6b), and 1 is a code reading (C10).

| Check | Claim (reviewer) | Recomputed |
|---|---|---|
| C1a | All 560 Qwen generations start with `Answer:` (Y9cR) | 560 of 560 |
| C1b | Median gold-string log-probability -29.45 (Y9cR) | -29.45 |
| C1c | 209 renderings answered exactly `Answer: <certified string>` still score a median -27.0 (Y9cR) | n = 209, median -27.03 |
| C1d | The scorer receives the bare certified string, not the instructed format (Y9cR) | Confirmed in `scripts/run_behavioural.py` (the answer passed to `compute_reference_answer_logprob` is `family_payload["correct_answer"]`) and `src/physmon/models/logprob.py` |
| C2a | 55 of 70 stable families vary by >= 0.5 nats across renderings (Y9cR) | 55 of 70 |
| C2b | 30 pilot families: Spearman 0.04 and 17/30 label agreement between the threshold-registration run and the panel run (Y9cR) | Spearman 0.043, 17 of 30 |
| C2c | Same-instruction rerun of the 40 phase-D1 families reproduces exactly (Y9cR) | 320 of 320 records identical |
| C3 | A correct formula hint gives 3.7 to 5.5 nats on five stable families (Y9cR) | 3.69, 3.84, 3.86, 4.20, 5.53 nats; baseline `S_lp` 0.0 on all five; 0 of 5 pass the low-sensitivity check |
| C4 | The "fitted entropy" 0.727 is built from the certified answer's own log-probabilities; the genuine oracle-free token-entropy baseline is 0.520 (Y9cR) | `run_entropy_baseline.py` uses `logprob_correct_answer`; oracle-free feature `token_entropy_topk_1000_std_across_4_variants` scores 0.5204; difference to the monitor 0.7596 - 0.5204 = 0.239 (the paired CI [0.115, 0.365] was not recomputed) |
| C5b | Correctness probe scored on the sensitivity label: 0.380 (Y9cR) | 0.380 (it ranks sensitive families as more likely correct) |
| C5c | 110 families, 34 clusters, 71% (BWJ6, Y9cR) | 110 families touched by unresolved pairs, 34 clusters, 0.710 of 155; 98 of the 135 panel families touched |
| C5d | Monitor AUROC 0.649 [0.45, 0.83] on the 37 panel families with no unresolved sibling; 0.789 on the 98 clustered (Y9cR) | n = 37: 0.649 [0.46, 0.82]; n = 98: 0.789 [0.70, 0.87]. All five Cue C panel families are in the clustered group |
| C6a | Table 1 (Bsyk asked for per-cue results) | A 12/35 (mean 0.515), B 53/100 (1.330), C 5/5 (9.022) reproduce Table 1; Llama by cue: A 6/35, B 23/100, C 3/5 |
| C6b | Does the headline hold without Cue C? (Bsyk) | Monitor AUROC 0.760 (135) -> 0.743 (130 without Cue C); Cue A only 0.761 (n = 34); Cue B only 0.721 (n = 96); Cue C cannot be scored (all 5 positive) |
| C7a | Exact-match Cue B families are less often sensitive, 20/52 vs 33/48 (Y9cR) | 20/52 vs 33/48 |
| C7b | Non-unit-matched Cue B families are more often sensitive, 17/20 vs 36/80 (Y9cR) | 17/20 vs 36/80 when distractor and target units are compared as dimensions (`N*s` and `kg*m/s` count as the same, CM_B_006). The explicit `unit_matched_cue_b` template tag gives a different split (tagged 33/70, untagged 20/30), so the claim depends on the definition |
| C8a | Four-head knockout at L16: 17 of 20 families invert, +4.16 -> -3.08 nats, 7.2 nats added, correlation 0.30 (Y9cR) | 17 of 20; 4.16 -> -3.08; 7.24 added; correlation 0.30; mean recovery 1.87 |
| C8b | Removing head 11 raises the certified answer's first-token logit by 3.76 on base and 3.77 on sensitive renderings, 20/20 families each (Y9cR) | 3.76 (20/20) and 3.77 (20/20) |
| C8c | All five held-out Cue A families invert under the knockout (Y9cR) | 5 of 5 Cue A invert; 1 of 5 Cue C |
| C9 | All 155 templates `created_by: agent`; delegated agent review marks families `pi_validated: true` (Y9cR) | 155 of 155 `agent`; 140 templates have `pi_validated: true`; the agent review document is present |
| C10 | Coulomb templates pass under an absolute 1e-3 tolerance; no Cue C identity/dimension check in the verifier (Y9cR) | `COULOMB_ABSOLUTE_TOLERANCE = 1e-3` applied to `coulomb_law`/`electric_field` tags (verifier.py L22, L241-242); the absence of a Cue C check is read from the same file |

Not recomputed here [R]: the paired bootstrap CIs the reviewer quotes (+0.239 [0.115, 0.365]; +0.08 [-0.15, +0.30]), the 0.734 domain-held-out figure, the "two renderings check uses prompt-surface features only" statement, the line-number references into the paper and the decision log, and whether the formula-hint answers "stay or become correct".

**Reading:** Reviewer Y9cR's analysis of the released artifacts is accurate to the digit wherever it can be tested. The withdrawal replies are consistent with that. Treat the review as a correct audit of our own data, not as a matter of opinion.

## 4. Issue register (all four reviews, consolidated)

"Raised by" lists reviewers; "In v2?" is whether the current plan of record (`PhysMon_Research_v2.pdf`) already prescribes the check; "Stage 14" is what the teammate's committed work already shows.

| # | Issue | Raised by | Checked | In v2? | Stage 14 [T] |
|---|---|---|---|---|---|
| 1 | The label scores the bare certified string, not the instructed `Answer: <value> <unit>` format the model produces; undisclosed | Y9cR | [V] C1 | Yes: B1.4, P1.3, C04, C05 | 14.3 scoring contract with seven wrappers; 14.10 X03 under seven wrappers |
| 2 | The label is unstable: base-relative, no noise floor; pilot labels agree at chance across two answer instructions; 55/70 stable families vary >= 0.5 nats | Y9cR | [V] C2 | Yes: B1.2, P1.1, P1.7, X02 | 14.2: 40-49% (Qwen) and 41-56% (Llama) of base-0 positives flip with the base; legacy label retired as a primary endpoint (interim rule); 14.9: dtype noise floor SD 0.09-0.19 nats. **Not covered:** a cross-answer-instruction label stability test on the pilot families |
| 3 | A correct formula hint also triggers the label (3.7-5.5 nats) | Y9cR | [V] C3 | Partly: P1.2 (relevant edit), not a formula-hint cell | 14.14, 14.17: every number in a prompt, including the numbers the problem needs, gets an answer-presence boost; plausibility explains about half of the same-unit cue effect |
| 4 | Comparators mislabelled: "fitted token-entropy" is built from the label's own inputs; the oracle-free entropy baseline is 0.520; correctness probe on sensitivity is 0.380 | Y9cR, BzwY (probe vs entropy value) | [V] C4, C5b | Yes: P5.3, P5.7 | 14.4 refits "fitted entropy features" (0.729); same family of features as the paper's 0.727 |
| 5 | Knockout is one-sided and reverses (not cancels) the drop; boosts the certified answer regardless of cue; recovery > 1 is inversion | Y9cR, BzwY, BWJ6 | [V] C8 | Yes: P6.2, P6.3, E01-E12, X07 | Not started (needs activations/GPU) |
| 6 | Causal design is circular: heads chosen on the panel they are tested on; held-out panel has no Cue B | Y9cR | [R] | Yes: P6.3 (untouched structures), E12 | Not started |
| 7 | Wording exceeds evidence ("cancels", "necessary"); Appendix K claims conformance with the claim registry that prohibits the necessity wording | Y9cR | [R] (the registry prohibition itself is in `docs/registry/claim_evidence_matrix_v7.md`) | Partly: claim hierarchy C1-C6, P11 audit | Claim ledger exists (14.0) |
| 8 | Template-cluster leakage: held-out families share clusters with training (71%); monitor margin outside clusters unproven | Y9cR, BzwY, BWJ6 | [V] C5c/d | Yes: B1.6, P3.5, P3.6, X05 | 14.4: 34 clusters rebuilt; 70.4% exposure in the 135 cohort; template-only predictors lose signal under cluster-held-out folds; entropy features do not; the monitor itself under cluster-held-out folds is NOT_EVALUATED (no activations). On the 40 non-exposed families the stored monitor scores 0.685 [0.51, 0.86] against fitted entropy 0.807 |
| 9 | Cue C (equivalent units) pooled with irrelevant cues A/B | Bsyk, BzwY, Y9cR | [V] C6 | Yes: Cue C moved to V2-B (p.5) | Cue C separated in v2 structures |
| 10 | No human validation; symbolic certificate does not validate the natural-language problem; agent authorship/validation in tension with the paper's statements | BzwY, Y9cR (Q5), Bsyk | [V] C9 | Yes: B4, P3 | 14.5 materials; user walkthrough; **agent verification replaced the physicist review (user instruction, 2026-10-26)** |
| 11 | "Peaks when a distractor nearly matches the answer" overstated: exact-match families are less often sensitive; near-match tail only; Pearson 0.074; non-unit-matched Cue B more often sensitive | Y9cR | [V] C7 | Yes: P4.4, A02-A07 | 14.12, 14.17: unit compatibility modulates the boost; matched-plausibility control removes about half of the same-unit cue effect |
| 12 | Verifier scope: no Cue C identity/dimension check; loose Coulomb tolerance | Y9cR | [V] C10 | Yes: B1.5, B01-B04 | 14.6 generator with mutation tests (new structures) |
| 13 | Scope: short plug-in calculations; no formula selection, multi-step derivation or backtracking | Bsyk | [R] | Yes: B3.1 strata | 14.15/14.18/14.19: shorter and longer chains, up to 5 gold steps |
| 14 | No downstream use shown: does flagging sensitive families or suppressing heads improve accuracy, calibration or robustness? | Bsyk | [R] | Yes: P10, P5.9 | Not started |
| 15 | Interpretation gap: change in probability of one exact string is not "confidence" or "reliability" | BzwY, Y9cR | [V] via C1-C3 | Yes: B0.1, §4 endpoints (R_alt, C_gen) | 14.13/14.20: free-generation correctness endpoints with reasoning |
| 16 | The threshold's "registration date" is not a justification; it was set on a 30-family pilot whose labels are unstable across instructions | BzwY (Q1), Y9cR | [V] C2b | Partly: B1.2 says do not call new metrics preregistered | 14.2 interim rule: legacy label not used for new claims; pre-registration block left unedited |
| 17 | Similar AUROC does not show the probe and entropy capture the same information; paired single-rendering vs fitted entropy comparison requested | BzwY | [R] | Yes: P5.1 (tasks S/F/V), P5.7 | Wave 2 incremental information (CIs include zero); see section 6 caveat |
| 18 | Winner's curse in the 28-layer sweep; frozen-probe transfer inflated by cue-type base-rate skew; domain-holdout null permutes domains not labels | BzwY, Y9cR (paper's own limitations) | [R] | Yes: P5.8, B10/D07 | Not started |
| 19 | Inconsistent model/size statements (7-8B in the abstract, 7-32B in Appendix J) | BzwY | [R] | n/a (writing hygiene) | n/a |
| 20 | DeepSeek scoring position relative to the reasoning trace never confirmed | paper's Appendix D/G | [R] | Yes: P4.5 | Reasoning-model runs use their own contract (14.13, 14.19) |

Consensus across reviewers: the reversal-versus-cancellation reading (#5) and the template-cluster leakage (#8) were raised by three of four, including both accepting reviewers; the probe-versus-entropy value (#4, #17), the validity of the label (#1-#3, #15), and the pooled Cue C / physical validation (#9, #10) by two or three. Only Y9cR found the scoring-format, label-stability and knockout-cue-independence problems; those are the most damaging and were found only by re-scoring the released files.

## 5. How the reviews and the v2 plan relate [I]

1. **Convergence.** Of the 20 issues, 16 are already prescribed by the v2 plan (sections B0-B7, P0-P11, cards X01-X12), 3 partly (issues 3, 7, 16) and 1 is writing hygiene (issue 19). Stage 14 already has committed evidence on issues 1, 2, 3, 8, 9, 10 and 11, mostly produced before the reviews appeared. The reviews independently confirm that the v2 redesign targeted the right weaknesses.
2. **Not in v2, or only partly.** (a) An explicit cross-answer-instruction label stability test on the pilot families (issue 2); (b) a formula-hint control cell and the observation that any in-context answer information raises the gold-string probability (issue 3; the teammate's presence control is the same phenomenon); (c) an explicit "apply every intervention to base/no-cue renderings and report whether the effect is cue-independent" gate in X07/P6 (issue 5; v2 P6.2 asks for original and intervened scores, but the review's decisive finding is that the head-11 effect is the same on base and sensitive renderings); (d) an `oracle / needs-y*` tag on every comparator and a rule that no comparator built from the label's own inputs is called "non-activation" or "one forward pass" (issue 4; P5.3 lists cost but not this failure mode); (e) a mechanical claim-wording check between a manuscript draft and the claim registry's prohibited wording (issue 7); (f) a consistency check that provenance fields (`created_by`, `pi_validated`) match what the text says about authorship and validation (issue 10); (g) honest dating of the threshold: the 0.5-nat threshold was chosen after the Stage 4 results, and the paper's own pilot shows it does not transfer across the instruction that produced it (issue 16).
3. **Tension with a v2-era decision.** Reviewer Y9cR (Q5) objected that agent-built, agent-validated families sit in tension with the paper's statements about independent validation. The Stage 14.19 gold dataset (260 samples, 80 structures) was built and verified by agents by the user's instruction of 2026-10-26 and is labelled UNREVIEWED. The same objection applies to it; the reviews are the external confirmation of why the v2 plan requires independent expert review before confirmatory claims. This is a risk to keep visible, not a decision for me to reverse.
4. **A direction that is not obvious.** Y9cR's Cue B finding (non-unit-matched Cue B families more often sensitive: 17/20 vs 36/80 under the S_lp label) points the opposite way from the story that unit compatibility drives the effect, whereas the teammate's anchor-matched presence-boost measurements show a unit-compatibility modulation. The measurements differ (legacy `S_lp` versus anchor-matched answer boost), so this is not a contradiction yet, but it is exactly the kind of disagreement that should be resolved by one frozen endpoint, not by choosing the label that supports the narrative.

## 6. Cautions about our own earlier work [I]

- **Wave 2 (2026-08-27) used the same family of "non-activation" features.** `run_combined_baseline.py` builds its entropy proxy and mean-logprob features from `logprob_correct_answer`, the quantity the label is computed from. Reviewer Y9cR's point about the paper's 0.727 therefore also applies to the Wave 2 comparator (0.7048) and to the decision-log wording that called it a strongest non-activation comparator. The oracle-free entropy baseline is 0.520. This does not change the Wave 2 finding that the intervals include zero, but it changes what that comparison means: the paper's monitor was compared against an oracle-like baseline, and against a truly oracle-free one it leads by 0.24 on the full panel. The proper reading of "the monitor's value" needs both comparators, labelled by what they need at inference (see v2 P5.3, P5.10).
- **The legacy label has three independent reasons not to be a primary endpoint:** base dependence (X02), instruction dependence (Y9cR, [V] C2b), and scoring-string mismatch (C1). The teammate's interim rule already retires it for new claims.
- **No claim from the withdrawn paper survives as stated.** What remains reproducible: the numbers in the paper (X01 and these checks), and the descriptive facts that the label is sensitive to base choice, instruction, in-context answer information and the scoring string.

## 7. What the reviewers valued (to preserve)

Open release of templates, per-rendering records, predictions, decision log and claim registry (Y9cR); family-based design with machine-checked invariance as a reference point (Y9cR, BWJ6, BzwY); the paired-bootstrap, fitted-baseline comparison standard (the standard itself, not the specific comparators); worked examples and transparent audits (BzwY); the clear line of related work (Bsyk). The benchmark and its release "keep their value whatever happens to the paper's claims" (Y9cR).

## 8. Open items for the v2 update (next step; nothing done here)

The seven additions in section 5 point 2 are the candidate edits; the decision on which to adopt, and on the authorship/validation tension in point 3, belong to the user. Also open: the monitor under cluster-held-out folds (needs regenerated activations), a correct two-sided knockout panel on untouched structures, and the propagation of the oracle-versus-deployable tag into the Wave 2 record and the claim ledger.
