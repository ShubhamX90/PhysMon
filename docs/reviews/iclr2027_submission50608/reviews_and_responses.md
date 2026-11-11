# ICLR 2027 submission 50608: reviews, author responses, and withdrawal (verbatim)

Paper: *Confidence Without Cause: Predicting and Localizing Physics-Shortcut Sensitivity in Language Model Hidden States* (anonymous ICLR 2027 submission, now withdrawn).
Source: the OpenReview thread text supplied by the user on 2026-11-11 (pasted into the session). Reproduced without editing; only the markdown headings and the ordering below are ours. The thread is shown here in the order it was supplied: withdrawal first, then each review followed by the authors' comment on it.

Summary of the four reviews (ratings as supplied):

| Reviewer | Date | Rating | Presentation | Informativeness | Soundness | Confidence |
|---|---|---|---|---|---|---|
| Y9cR | 02 Nov 2026, 07:03 (modified 06 Nov 2026, 18:06) | 1: Clear rejection | 2 | 2 | 1 (significant concerns, not easy to address) | 2 |
| BzwY | 30 Oct 2026, 19:18 (modified 06 Nov 2026, 18:06) | 1: Clear rejection | 1 | 1 | 1 (significant concerns, not easy to address) | 2 |
| BWJ6 | 21 Oct 2026, 10:47 (modified 06 Nov 2026, 18:06) | 3: Weak acceptance | 2 | 2 | 2 (minor or fixable concerns) | 2 |
| Bsyk | 18 Oct 2026, 22:01 (modified 06 Nov 2026, 18:06) | 3: Weak acceptance | 3 | 2 | 2 (minor or fixable concerns) | 2 |

The statements about the released code and artifacts in Reviewer Y9cR's review are checked against this repository in `docs/reviews/iclr2027_submission50608/analysis.md` and `results/reviews/iclr2027_submission50608/`.

---

## Withdrawal by Authors

Withdrawal by Authors, 11 Nov 2026, 11:16. Visible to: Program Chairs, Senior Area Chairs, Area Chairs, Reviewers, Authors.

Withdrawal Confirmation: I have read and agree with the venue's withdrawal policy on behalf of myself and my co-authors.

Comment:
After considering the reviewers' feedback and revisiting the experimental methodology, we have decided to withdraw this submission.
The reviews identified several issues concerning the measurement protocol, baseline comparisons, causal interpretation, and benchmark validation that require more substantial work than can reasonably be completed during the current review cycle. We believe it is more appropriate to address these concerns thoroughly before submitting a revised version of the work.
We thank all four reviewers for their time, careful evaluation, and constructive feedback. Their comments will inform the ongoing research and future iterations of the paper.

## Official Comment by Authors (general, on the withdrawal)

Official Comment by Authors, 11 Nov 2026, 11:15. Visible to: Everyone.

Comment:
We would like to thank all four reviewers for taking the time to evaluate our submission and for their detailed feedback. We particularly appreciate the close examination of the released code and experimental artifacts, which helped identify issues that deserve more attention than we had given them.
After considering the reviews and revisiting parts of our implementation, we have decided to withdraw this submission from ICLR 2027.
Several of the concerns raised go beyond what we believe can be adequately addressed through revisions during the current review cycle. In particular, the answer-scoring protocol and its interpretation, the characterization of the baseline comparisons, and the conclusions drawn from the head-knockout experiments need to be revisited. The reviewers also raised important questions about the benchmark's physical validation, structural overlap between evaluation families, and the distinction between irrelevant information and equivalent representations of relevant quantities.
We intend to address these issues as part of our ongoing research. This will involve re-evaluating the original measurements, revising the experimental design, strengthening the benchmark and its validation, and conducting more rigorous causal experiments before making further mechanistic claims. We also plan to extend the work beyond short calculation-based problems and investigate whether the identified effects have meaningful consequences for actual physics problem-solving behavior.
We remain interested in the underlying research question and believe there is more to investigate here, but we recognize that the current submission does not yet provide sufficiently strong evidence for several of its conclusions.
Thank you again to all the reviewers for their time, careful reading, and constructive criticism. We appreciate the effort that went into these reviews and will take their findings seriously in the next iteration of this work.

---

## Official Review of Submission 50608 by Reviewer Y9cR

Official Review by Reviewer Y9cR, 02 Nov 2026, 07:03 (modified: 06 Nov 2026, 18:06). Visible to: Everyone. Revisions: https://openreview.net/revisions?id=3PZGrVWeps

**Paper Summary:**
The paper introduces DECOY: 155 physics problem families of four renderings that differ in one cue of three types; a SymPy check certifies that the cue symbol is absent from the governing expression. Sensitivity is the largest drop, relative to a fixed base rendering, in the teacher-forced log-probability of the certified answer, thresholded at 0.5 nats. Qwen2.5-7B-Instruct is sensitive on 70 of 140 families and Llama-3.1-8B-Instruct on 32. A probe on Qwen's layer-18 last-prompt-token state, averaged over renderings, predicts the label at leave-one-family-out AUROC 0.760, reported as on par with a fitted token-entropy baseline (0.727). Knocking out four layer-16 heads gives a mean normalised recovery of 1.870 on 20 Cue B families, against 0.021 for random perturbations, with no reliable effect in Llama or DeepSeek.

Presentation: 2: Generally understandable, but requires substantial effort in places.
Informativeness: 2: I learned something interesting or useful.
Soundness: 1: I have significant concerns about the paper's soundness that do not appear easy to address.

**Critical Strengths:**
Paths are in the supplementary material unless they name a repository script (footnote 1).

1. A reusable benchmark with an unusually open release. Each family passes a machine-checked free-symbol test on its structured equation (p.4 L192-203; structured certificates for 30, docs/validation/certificates_v6/). Templates, per-rendering records, predictions, the decision log and the claim registry are released, so labels and most comparisons can be re-scored; activations are not, so probes cannot be refit. The test does not cover the rendered prompt (docs/stage13/stage13_v6_preflight.md L71-78). This matters because the resource keeps its value whatever happens to the paper's claims.
2. The monitor beats oracle-free baselines on the full panel; outside template clusters its margin is not shown. Against the oracle-free next-token-entropy baseline the paper omits (AUROC 0.520; results/stage10/baselines/token_entropy/), the layer-18 probe wins by +0.239 (paired bootstrap, 95% [0.115, 0.365]), and it scores 0.734 with whole domains held out (Table 4 L1035; App. H(d)'s null permutes domains, not labels). On the 37 panel families with no unresolved leakage sibling (results/stage13/benchmark_integrity/leakage_review_v7.csv), however, it scores 0.649 [0.45, 0.83], only +0.08 [-0.15, +0.30] above entropy, against 0.789 on the 98 clustered families, which include all five Cue C families. This matters because the monitor is what survives the comparator problem (Question 4).

**Critical Weaknesses:**

1. The measured quantity and its main comparator are not what the paper says.
   * The label scores a string the model does not produce. It scores the bare certified string ("36.0 J") straight after the assistant turn, while the system prompt asks for "Answer: [value] [unit]" and all 560 Qwen generations start with "Answer:" (run_behavioural.py L41-46, L531-535; logprob.py L35-50; results/stage6/behavioural_full_rerun/). Neither the paper nor the supplement discloses this. Scores have a median of -29.45 nats; the 209 renderings answered exactly "Answer: <certified string>" still score a median of -27.0.
   * The label is not stable. It is signed against one fixed base with no noise floor (55 of the 70 stable families vary by at least 0.5 nats across renderings). On the 30 pilot families, with identical problem text and scored strings, S_lp under the instruction used to register the threshold and under the panel's instruction correlate at Spearman 0.04 and agree on 17 of 30 labels, the chance level, while a same-instruction rerun of 40 other families reproduces exactly (results/stage4_repair/behavioural/; results/stage6/behavioural_full_rerun/; rerun: results/stage6/behavioural/). A correct formula hint gives 3.7 to 5.5 nats on five stable families whose answers stay or become correct (results/appendix/formula_leakage/). A confident answer that "silently track[s] task-irrelevant detail" (abstract L37-38) is not shown.
   * The comparators are mislabelled. The "fitted token-entropy" baseline, described as next-token entropy from one forward pass (p.6 L292-293; Table 5; p.9 L433-434), is a regression on the standard deviation and mean of the four teacher-forced log-probabilities of the certified answer, the label's own inputs, which the decision log calls "NOT deployable" (docs/decisions/decision_log.md L1696-1698). The "two renderings" check (p.6 L294-295) uses prompt-surface features only.
This matters because contribution (d), the deployment advice (p.7 L376-378) and the "confidence" reading of contributions (b) and (c) rest on these.
2. The causal claim is unsupported.
   * One-sided knockout. Only the sensitive rendering is knocked out, and it is compared with the intact base (run_causal_patching.py L485-499, L527-528). The knockout adds 7.2 nats on average, largely regardless of the drop (correlation 0.30; results/stage8/multi_head_knockout/patching_results.csv), so 17 of 20 families invert (-3.08 nats against +4.16 before), the recovery interval [1.560, 2.198] lies above 1 (p.8 L400-403), and all five held-out Cue A families invert (results/stage10/mhk_cue_generalization/). That is a reversal, not a cancellation.
   * Cue-independent effect. No run recomputes S_lp with the knockout on base renderings; the damage control on 40 stable families records only accuracy (results/stage9/damage_control/). Removing head 11 raises the certified answer's first-token logit by 3.76 on base and 3.77 on sensitive renderings, in 20 of 20 families each (results/stage12/science/h11_h15_gating/gating_test_per_family.json).
   * Design. The four heads are the top layer-18 probe contributors on 10 panel families, knocked out at layer 16 after a layer sweep on the same panel (decision_log.md L1194-1211, L1508-1520). The held-out panel has no Cue B family.
   * Wording. The paper keeps "cancels" (abstract L35-36) and "necessary" (p.8 L417; p.9 L444-445). The authors' registry prohibits the necessity wording and rates every estimate "discovery-tier and not paper-eligible" (docs/registry/claim_evidence_matrix_v7.md), yet App. K claims conformance (p.25 L1320-1321).
This matters because contribution (e) and the title's "localizing" fail as stated.

**Questions For Authors:**
Clarification requests (answers could change my assessment):

1. Please relabel the 0.727 baseline and add to Table 5 the oracle-free entropy row (0.520), the correctness probe scored on sensitivity (0.380; Fig. 3a's 0.7657 is on its own target; results/stage9/baselines/correctness_probe/) and the combined model without the certified-answer features (App. E L1077).
2. Do the 50.0% rate and the probe AUROC survive each of these?
   * Scoring the instructed format ("Answer: 36 J") after its prefix, under two answer instructions.
   * A base-free statistic (maximum minus minimum across renderings).
   * Restricting to families answered correctly on all four renderings.
What is the noise floor for content-free edits?
3. What are log p(y*) and S_lp under the four-head knockout in the damage-control run (all renderings of 40 stable families) and on the panel's base renderings?
4. What is the probe's AUROC with whole template clusters held out and the layer chosen inside training folds (p.9 L481-483)? Please name the grouping, e.g. the 34 leakage clusters (results/stage13/benchmark_integrity/leakage_audit_v7.json) rather than App. K's 9-level "template cluster".
5. All 155 templates carry `created_by: agent` (p.14 L712; data/raw/templates/). The supplement records that a coding agent built templates and that a "Codex agent" validated 40 families in place of the PI pass, which are marked `pi_validated: true` (docs/decisions/stage6_agent_status_report.md; docs/validation/stage6_phase2_bce_agent_review.md). How does this square with p.3 L126-128, p.4 L209-210 and the AI-use statement (p.10 L494-497)?

**Suggestions:**

* Contribution (b). Exact-match Cue B families are less often sensitive (20/52 against 33/48; results/stage6/audit/stage6_full_benchmark_manifest.csv), so "peaks when a distractor nearly matches" (p.2 L92-93) overstates.
* Cue B. 20 of the 100 labelled Cue B families are not unit-matched (cf. Table 1; p.4 L205-207), and they are more often sensitive (17/20 against 36/80).
* Verifier. The admission verifier runs no Cue C identity or dimensional check (results/stage13/benchmark_integrity/mutation_test_summary_v6.json), and Coulomb templates pass under an absolute 1e-3 tolerance, against p.4 L197-200 and App. C L943.

To move above a clear rejection I would need labels re-scored in the instructed format that stay stable across answer instructions and benign edits, S_lp under the knockout on all renderings and stable families, and a cluster-held-out AUROC clearly above the paper's 0.651 surface baseline (p.9 L436).

Rating rationale.
The benchmark and its release are valuable, and on the full panel the monitor beats oracle-free baselines. But the paper's three empirical claims fail against its own released artefacts. The label tracks the scoring set-up, not confidence: it does not reproduce across answer instructions, and a correct formula hint triggers it. The comparator behind contribution (d) is an oracle, and the monitor's margin is not shown outside template clusters. The knockout boosts the certified answer whatever the cue. Repairing this needs new labels, probes and knockouts: a new study, not a revision.

Flag For Ethics Review: No
Rating: 1: Clear rejection
Confidence: 2: I have broad familiarity with this field but little or no direct research experience on this topic.

### Official Comment by Authors (response to Reviewer Y9cR)

Official Comment by Authors, 11 Nov 2026, 11:12. Visible to: Everyone.

Comment:
Thank you for taking the time to examine not just the paper but also the released code, experiment records, and validation artifacts in such detail. Your review brought several important issues to our attention, particularly concerning the answer-scoring protocol, the interpretation of the entropy baseline, and the design of the causal interventions.
We acknowledge that the mismatch between the instructed answer format and the scored reference string needs to be corrected, and that the sensitivity labels must be re-evaluated under a consistent scoring protocol. The distinction you pointed out between the fitted likelihood-based comparator and an actual oracle-free entropy baseline is also important, and the existing presentation does not make that distinction correctly. Similarly, the one-sided head-knockout experiments do not support the stronger claims about cancellation or necessity made in the paper. These conclusions need to be revisited using interventions on both base and sensitive renderings, along with appropriate controls.
Your concerns regarding template-cluster leakage, benchmark certification, and the provenance of agent-assisted construction and validation are equally important. We will address these explicitly in the ongoing work, including a clearer separation between automated checks and independent human validation.
Given the extent of the methodological changes required, we have decided to withdraw this submission rather than attempt to address them through a limited revision during the current review cycle. We intend to rework the measurement and experimental foundations before making further claims.
Thank you again for the detailed review. The specific issues you identified will be valuable in guiding the next iteration of this research.

---

## Official Review of Submission 50608 by Reviewer BzwY

Official Review by Reviewer BzwY, 30 Oct 2026, 19:18 (modified: 06 Nov 2026, 18:06). Visible to: Everyone. Revisions: https://openreview.net/revisions?id=GtfFD4sIfN

**Paper Summary:**
The paper investigates whether language models are influenced by information that should not affect the solution to a physics problem. The authors introduce DECOY, a benchmark comprising 155 families, each with four prompt variants, and use symbolic verification to establish that the correct answer remains unchanged. They measure sensitivity by the change in the log-probability assigned to the correct reference answer and train hidden-state probes to predict this sensitivity before generation. The experiments mainly focus on Qwen and Llama, with additional analyses on DeepSeek. The authors also investigate whether removing specific attention heads reduces the measured sensitivity.

Presentation: 1: Difficult to follow despite careful reading.
Informativeness: 1: I learned little or nothing new from this paper.
Soundness: 1: I have significant concerns about the paper's soundness that do not appear easy to address.

**Critical Strengths:**
The motivation and overall goal of the paper are interesting and relevant. I think constructing physics problems with symbolically verified invariance of the answer is a promising starting point for a benchmark. The authors also provide considerable experimental detail, including worked examples, intervention controls, and benchmark audits.

**Critical Weaknesses:**

1. The interpretation of sensitivity needs further validation Sec. 3.3 measures changes in the probability of one exact correct-answer string. In Tab. 2, Llama consistently produces the same incorrect answer while being classified as sensitive. The authors distinguish sensitivity from correctness, but it remains unclear how changes in the probability of one exact answer string relate to the broader claims about confidence and reliability. The benchmark also combines irrelevant distractors with equivalent representations of relevant quantities, which test somewhat different phenomena. The human validation described in Appendix K has not yet been completed, and symbolic verification alone does not validate the natural-language problems. This concern about interpretation also applies to the causal results. Sec. 5.4 reports a mean recovery of 1.870, where values above 1 correspond to reversing the measured drop. Reversing the effect does not establish that the model has become insensitive to the cue. The paper is also very inconsistent about what models and sizes are tested. The abstract says 7-8B, the appendix J says 7-32B. This should be clarified.
2. The probe's added value and generalization remain unclear The probe achieves 0.76 AUROC, compared to 0.727 for entropy, with no statistically significant difference (Sec. 5.3). The main probe also requires four prompt variants. The single-rendering result of 0.747 is helpful, but its practical advantage over the simpler baseline remains unclear. Generalization is similarly difficult to assess. Sec. 7 states that 71% of held-out families share template clusters with training families. The transfer result of 0.820 is based on only 15 families. It partly reflects differences between cue types, as acknowledged in Sec. 5.2. Sec. 7 also states that generalization to unseen domains is not established, as the domain-holdout result does not significantly outperform the permutation baseline (). This further limits the evidence for the probe's usefulness beyond the evaluated settings. The discussion in Sec. 5.5 largely repeats the experimental findings without discussing what they mean in enough detail. For example, similar AUROC does not establish that the probe and entropy baseline capture the same information. I think a clearer discussion of what the results establish about confidence and reliability is needed.

**Questions For Authors:**

* Why is the registration date of the sensitivity threshold relevant?
* What justifies connecting changes in the probability of one exact answer string to the broader claims about confidence and reliability?
* Why is the intervention described as canceling sensitivity when recovery above 1 reflects a reversal of the measured drop?
* Why is similar AUROC taken as evidence that the probe and entropy baseline capture similar information in Sec. 5.5?
* Could the authors provide a paired comparison between the single-rendering probe and the fitted entropy baseline on the same held-out families? What practical benefit does the probe provide that justifies access to hidden states?

Flag For Ethics Review: No
Rating: 1: Clear rejection
Confidence: 2: I have broad familiarity with this field but little or no direct research experience on this topic.

### Official Comment by Authors (response to Reviewer BzwY)

Official Comment by Authors, 11 Nov 2026, 11:13. Visible to: Everyone.

Comment:
Thank you for your review and for raising these concerns. We agree that the interpretation of sensitivity needs stronger justification, particularly the connection between changes in the likelihood of a specific reference-answer string and broader claims about confidence and reliability. This distinction was not established sufficiently in the submitted work.
Your points about the probe's added value and generalization are also well taken. In particular, the comparison with simpler baselines needs to be made on matched evaluation settings, and performance on held-out families is not enough when substantial template overlap remains. We also agree that similar AUROC values alone do not establish that two predictors capture the same information.
Regarding the causal experiments, the reported recovery values should not have been interpreted as cancellation when the intervention could reverse the original effect. This will require a different experimental design and more careful interpretation.
We have decided to withdraw the submission and continue working on these issues rather than attempt a limited revision at this stage. The next iteration will place greater emphasis on validating the behavioral measure, establishing meaningful generalization, and connecting the internal measurements to actual model behavior.
Thank you again for taking the time to review our work. Your comments will be taken into account as we revise the study.

---

## Official Review of Submission 50608 by Reviewer BWJ6

Official Review by Reviewer BWJ6, 21 Oct 2026, 10:47 (modified: 06 Nov 2026, 18:06). Visible to: Everyone. Revisions: https://openreview.net/revisions?id=ZKONGDHTJd

**Paper Summary:**
When answering physics problems, language models may be influenced by task-irrelevant details, causing their confidence to change even when their answers remain correct. This paper investigates whether such sensitivity can be detected before generation from the model's hidden states and attempts to localise the relevant internal mechanisms. The authors construct physics problem families whose correct answers remain invariant across renderings, evaluate confidence changes across several models, and train linear probes to predict sensitivity, comparing them with baselines such as token entropy. They also conduct attention-head knockout experiments and associated controls to examine the contribution of specific internal components.

Presentation: 2: Generally understandable, but requires substantial effort in places.
Informativeness: 2: I learned something interesting or useful.
Soundness: 2: I have minor or fixable concerns about the paper's soundness.

**Critical Strengths:**

* The paper addresses the problem of models relying on task-irrelevant features when solving physics problems, a form of shortcut learning that can coexist with high accuracy. This is an interesting research question, and the examples are concise and easy to understand.
* The benchmark construction is well controlled. The authors adopt a family-based design, varying a designated cue while keeping the physically relevant conditions and the correct answer unchanged. Answer invariance is verified by a symbolic solver. Compared with perturbation tests based solely on manual or heuristic rewriting, this design provides a clearer reference for interpreting behavioural changes.

**Critical Weaknesses:**

* The interpretation of the head-knockout experiments may require stronger validation. The reported metric measures the drop in the log-probability of the certified answer relative to the base rendering. However, reversing a drop into an increase does not establish that the model is no longer influenced by irrelevant details. The current results support a causal effect of the attention heads on this directional metric, but do not yet establish that the intervention eliminates the influence of task-irrelevant cues.
* The probe's generalisation ability may not be sufficiently validated. Although the evaluation holds out entire families, approximately 71% of held-out families share a template cluster with families in the training set. The probe may therefore have learned which problem templates tend to be sensitive, rather than identifying the actual sensitivity of individual instances. The current results demonstrate some predictive ability on problems with similar template structure, but do not sufficiently establish generalisation to unseen templates. An evaluation that holds out entire template clusters would help address this concern.

**Questions For Authors:**
see the weaknesses.

Flag For Ethics Review: No
Rating: 3: Weak acceptance
Confidence: 2: I have broad familiarity with this field but little or no direct research experience on this topic.

### Official Comment by Authors (response to Reviewer BWJ6)

Official Comment by Authors, 11 Nov 2026, 11:13. Visible to: Everyone.

Comment:
Thank you for your review and for recognizing the motivation behind the benchmark and the use of symbolically verified counterfactual problems.
We agree with both of your main concerns. The current head-knockout results establish an effect on the measured likelihood difference, but they do not demonstrate that the model has become insensitive to the irrelevant cue. In particular, reversing the original drop is not equivalent to eliminating the dependence. We will revisit these experiments with paired interventions and controls that can distinguish a cue-specific effect from a general change in answer likelihood.
Your point about generalization beyond familiar templates is also important. Although we held out entire problem families, the structural overlap between training and evaluation families limits what can be concluded. We intend to use stricter template-cluster holdouts and independently constructed problems in future evaluations.
We have decided to withdraw the current submission and continue developing the work with these limitations addressed more directly.
Thank you again for the constructive review and for identifying the areas where the evidence needs to be strengthened.

---

## Official Review of Submission 50608 by Reviewer Bsyk

Official Review by Reviewer Bsyk, 18 Oct 2026, 22:01 (modified: 06 Nov 2026, 18:06). Visible to: Everyone. Revisions: https://openreview.net/revisions?id=NMONyo5PwZ

**Paper Summary:**
This paper introduces DECOY, which consists of 155 families of four physics prompts that differ only in a single cue. A symbolic solver certifies that the cue cannot change the answer, and each family is labelled by the largest drop in the teacher-forced log-probability of the certified answer. On these families, Qwen2.5-7B-Instruct is sensitive on 50% and Llama-3.1-8B-Instruct on 23%. A linear probe on Qwen's hidden state predicts this sensitivity before generation, and knocking out a small set of attention heads at layer 16 cancels the effect on a Qwen panel. The contributions are a certified measure of confidence shifts under answer-preserving edits, a pre-generation monitor for that sensitivity, and a causal localisation of the effect in one model.

Presentation: 3: Clear and easy to follow.
Informativeness: 2: I learned something interesting or useful.
Soundness: 2: I have minor or fixable concerns about the paper's soundness.

**Critical Strengths:**
The line of the work is clear. The core idea is that sensitivity to irrelevant conditions corresponds to unstable confidence. The related work shows that each dimension is grounded and reflects the authors' own improvements: every paragraph first states prior practice, then points to a specific gap, and that gap is exactly a step addressed later in the paper. The paper also sets up many experiments to rule out confounds and to probe the problem in depth, and the logic is tight.

**Critical Weaknesses:**
One issue in the methodology is that Cue C is not the same as Cue A and Cue B. A and B are irrelevant information, whereas C is more about the model's unit conversion, and in some cases different conventions may correspond to different units. This is completely different from A and B, and C should not be pooled with A and B in the later analysis. In addition, the 155 DECOY families are mainly short calculations that can be symbolically certified, covering mechanics, circuits, and thermodynamics, but they do not include problems that require formula selection, multi-step derivation, or backtracking, which are more closely tied to confidence. The paper shows that simple formula-evaluation items make it clear whether irrelevant information interferes, but these plug-in-the-numbers questions may also be less susceptible to irrelevant information than real theoretical physics derivations, so using only short calculations is somewhat limited. A further point is that the contribution currently stops at certified measurement. The paper does not show how what it proves and measures can be used back in physics problem solving, for example whether it can improve accuracy, calibration, or robustness during calculation or reasoning.

**Questions For Authors:**
Please report sensitivity rates, mean drops, and probe results separately for Cue A, Cue B, and Cue C. Do the headline claims still hold if Cue C is excluded from the aggregate? The current families are short, symbolically certified calculations. Can answer invariance still be certified for items that require formula selection, multi-step derivation, or backtracking? If so, do you have any such results, or is this left to future work? Beyond measurement, does flagging sensitive families or suppressing the localised heads improve accuracy, calibration, or robustness on physics calculations? If this was not tested, which of these uses do the authors see as the immediate next step?

Flag For Ethics Review: No
Rating: 3: Weak acceptance
Confidence: 2: I have broad familiarity with this field but little or no direct research experience on this topic.

### Official Comment by Authors (response to Reviewer Bsyk)

Official Comment by Authors, 11 Nov 2026, 11:13. Visible to: Everyone.

Comment:
Thank you for your review and for your comments on the benchmark design and the broader direction of the work.
We agree that Cue C should not be treated as the same phenomenon as Cues A and B. Equivalent representations of a relevant physical quantity raise different questions from genuinely irrelevant information, and combining them in the same analysis makes the interpretation less clear. We plan to separate these cases and study them under distinct evaluation protocols.
Your observation about the limited complexity of the current physics problems is also important. The short calculation-based families gave us a controlled starting point, but they do not adequately represent problems involving formula selection, multistep derivations, or more involved physical reasoning. Extending the benchmark in these directions, while retaining reliable verification of the underlying physics, is a major part of our ongoing work.
We also agree that the study should go beyond detecting sensitivity. Whether the identified behavior can be used to improve actual problem-solving accuracy, calibration, or robustness remains an open question, and we intend to investigate this rather than assume that better sensitivity measurements will translate into practical improvements.
We have decided to withdraw this submission and continue the research with these extensions and corrections in mind.
Thank you again for the encouraging and constructive feedback. Your suggestions are closely aligned with several of the directions we want to pursue next.
