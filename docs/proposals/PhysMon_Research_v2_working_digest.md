# Working digest: PhysMon Research Redesign v2 (revised edition, 11 November 2026)

**Source of truth:** `docs/proposals/PhysMon_Research_v2.tex` (canonical LaTeX source, 73 pages when built).
Built output: `PhysMon_Research_v2.pdf`; searchable text: `PhysMon_Research_v2.extracted.txt` (page markers
`######## PAGE n ########`). Rebuild both with `scripts/build_plan_pdf.sh` (tectonic and pypdf in the separate
conda environment `texbuild`; see the script header). Edit the `.tex`, never the PDF; rebuild and commit all three
together.

This digest is a navigation aid regenerated from the revised source. It does not replace it; when they disagree,
the `.tex` wins. Page numbers below are PDF pages of the 11 November build (73 pages).

## 1. What the document is

- The single plan of record for PhysMon from Stage 14 onward (user direction 2026-10-15; revised edition at the
  user's direction of 2026-11-11, consolidated into one LaTeX source at the user's choice the same day).
- The revised edition replaces the edition of 14 October 2026 (preserved in Git history, e.g. commit `2cf08e2`)
  and the short-lived Markdown revision layer `PhysMon_Research_v2.1.md` (commit `2cf08e2`, removed).
- It keeps the October identifiers (B0-B7, P0-P11, A01-F20, X01-X12) so the Stage 14 journal, ledger and decision
  log still resolve; Appendix C gives the disposition of every October element.
- Inputs: the four ICLR 2027 reviews of the withdrawn Phase-I paper (verified, `docs/reviews/iclr2027_submission50608/`),
  Stages 14.0-14.20, a literature update of 2026-11-11, and four independent reviews of the drafts (Appendix D).
- A proposed, falsifiable protocol, not a record of results. Agent-written; not reviewed by a person outside the
  project.

## 2. Rules that apply at all times (Section 1, p. 4)

1. Separate estimands: probabilities, representations, correct answers and faithful computation are different
   things. `S` is observational only; "mechanism" needs controlled, specific, predictive intervention evidence;
   "shortcut reliance" needs evidence that the computation improperly uses a quantity.
2. A quantity that cancels algebraically or is irrelevant only within a regime may legitimately enter intermediate
   reasoning; that use is never an error (Section 4.2).
3. All alternative theses (string/format effects, difficulty, copying, context sensitivity, several mechanisms,
   correct selection) are legitimate outcomes.
4. Disjoint data roles (EXPLORATION, GENERATOR_TUNING, INTERNAL_CONFIRMATION, EPC_CONFIRMATION,
   ADVERSARIAL_CHALLENGE) by graph lineage; a shadow set; a structure never moves from EXPLORATION into confirmation.
5. The independent unit is the structure or template cluster, never a rendering, value, phrasing or sample.
6. `NOT_EVALUATED` is neither a null nor `WRONG`; zero evaluable rows are not a zero effect.
7. Validation tiers: the authoring agent's self-review is not validation; a qualified panel of independent LLM
   reviewers (Phase B, B4) is the interim tier for confirmation, disclosed as such; human expert review is the
   strongest tier and is never claimed when only the panel ran.
8. Thresholds record when they were fixed; no retroactive relabelling; no "preregistered" after the fact.
9. Every comparator is tagged `oracle` or `deployable`.
10. Every intervention is read as an interaction against a control prompt.
11. Every GPU job needs the user's acceptance of its exact command.

## 3. The construct (Section 4, pp. 19-25)

- **Question (4.1):** does the answer depend on a quantity the way its certified physical role requires, beyond
  presence, value, plausibility, unit, position, marker wording and generic perturbation; and what computation
  produces or prevents departures? Novelty is scoped against PRISM-Physics, GSM-DC, Qu and Gomes, Owusu et al. and
  Liu (Section 11).
- **Role strata (4.2):** R relevant; D structurally disconnected; C algebraically cancelling; K conditionally
  irrelevant. Each has its own certificate and correct behaviour; never pooled.
- **Role-by-value design (4.3):** R and D (C, K where feasible) at three or more values in two or more validated
  phrasings (one without marker words). Primary estimands: per-sample tracking `T` and the D tracking loss against the
  non-numeric sentence (which catches a departure of either sign); misuse shares for prespecified, signed misuse
  curves across values; the R neglect share against a placebo match rate. Descriptive only, with a multimodality guard: response fractions `lambda_r` and the index
  `Lambda = lambda_R - lambda_D`. All matches kept. A structure is complete only with R and D at three values in two
  phrasings.
- **Outcomes (4.5):** O1 usable-answer success (all attempts), O2 semantic physics correctness (adjudicated), O3
  completion and grading status (`BUDGET_EXHAUSTED` only when the token limit was hit; a missing end-of-thinking
  marker otherwise is `FORMAT_INVALID`), O4 role-by-value response, O5 cost, O6 candidate log-odds (only inside a
  causal claim type). Sampling is required; Stage 14 greedy records are never pooled with sampled ones.
- **Populations (4.6):** all validated tasks (always reported), calibrated band, reliably solved tasks.
- **Hypotheses (4.7):** H0 none; H1 presence; H2 plausibility and unit; H3 relevance-selection failure (with C and
  K wrong-law curves); H4 readout contamination; H5 diversion (cost only); H6 correct selection, split into H6-RD
  (R and D) and H6-extended (adds C and K), each needing equivalence. Scored, not exclusive.
- **Causal standard (4.8):** claim types T1 readout (prompts sharing a gold; certified answer vs a predeclared
  alternative on one explicitly identified prefix; no prefix excluded), T2 intermediate computation, T3 total
  effect. Two interactions: `I_presence` (vs the non-numeric sentence) and `I_role` (vs the relevant twin with the
  same numeral, on a behaviourally comparable outcome); only `I_role` supports a role-routing claim. A 14-item
  protocol checklist.
- **Claim levels (4.9):** CL1 benchmark, CL2 behavioural, CL3 monitor, CL4 causal localisation, CL5 mechanism,
  CL6 repair; promotion one level at a time (the October C1-C6).

## 4. Critical path (Section 5, pp. 25-39)

| Gate | Deliverable | Passes when |
|---|---|---|
| G0 integrity closure | Status sync, seven review-derived checks, narrowed P0 (extended parity), Phase-I closure note, Qwen3-32B manifest | Items committed; failed parity blocks mechanism work on that model only |
| G1 physics construct | Strata certificates, role-by-value generator, outcomes, sampled contract, analysis and power scripts, thresholds, SESOI | Tests pass; cards committed; nothing run before |
| G2 measurement and calibration | 8-12-structure design-validation pilot; calibration with fresh baseline samples; R-tracking check; primary-model rule frozen | Enough complete structures in band (planning 24+), R criterion met, cost fits |
| G3 behavioural discovery | Core run (24-40 structures, 14 cells each), staged ablations, non-physics control, hypothesis scorecard | Estimation only; G4 family is fixed in advance |
| G4 confirmation | Role-by-value family (F1 D tracking loss against the non-numeric sentence, F2 R neglect against a placebo rate, F3 role x value interaction on tracking; Holm) on untouched clusters validated by the qualified LLM panel, two formats | Primary model meets the family rule |
| G5 mechanism | T1/T2/T3 experiments with both interactions | After G4 establishes H3, H4 or H6-RD (H6-extended only if G4 covered C and K) |
| G6 external and functional confirmation | Re-certified external physics, non-physics transfer, second model | Required for broad claims |
| G7 practical use | Monitoring, repair | Optional |

Section 5.2 keeps P0-P11 as the requirement catalogue, each with a status line and its gate.

## 5. Other sections

- Section 2 (p. 5): tracks M/E/R; the final Phase-I ledger after the reviews; what Stage 14 established.
- Section 3 (pp. 7-18): Phase B (B0-B7) with status lines; benchmark architecture (V1-R, V2-A, V2-B, EPC, MATH-X).
- Section 6 (pp. 39-47): all 104 inventory items with gate and status; contrasts added by the revision.
- Section 7 (pp. 48-52): cards X01-X12 with status and revision (X07 retired as stated; X04 becomes the
  role-by-value factorial).
- Section 8 (p. 53): statistics (structure-level paired analysis, SESOI with reasons, four-way result language,
  rare categories, power by simulation including null data).
- Section 9 (p. 55): environment, models, measured rates, staged budget, human effort, data contracts, preflight.
- Sections 10-15: contingencies, literature and novelty, next sprint, paper architectures, bibliography,
  completion.
- Appendices: A Stage 14 evidence; B review issues and answers; C disposition and open decisions; D revision log.

## 6. Open decisions (Appendix C, p. 71)

D1 keep the full P0 regeneration off the critical path (default: not run); D2 which 2-3 judge models form the LLM
review panel (the user decided on 2026-11-11 to use a qualified LLM panel now and human review later; until the
models are chosen and qualified on the planted-defect bank, G4 would be EXPLORATORY-REPLICATION); D3 download Qwen3-8B (default: no); D4 install vLLM in a separate
environment (default: no); D5 resubmit the 32-anchor resample (default: no); D6 Phase-I monitor side track
(default: not scheduled). Defaults only withhold actions.

## 7. Environment facts that constrain the plan

- Activations, checkpoints and earlier Slurm logs were wiped in the 2026-10 scratch wipe; committed records survive.
- Per-user QoS limits (live `sacctmgr`, 2026-11-11): H100 12 CPU, 2 GPUs of which 1 named H100, 300G, 2 jobs;
  H200 12 CPU, 2 GPUs, 300G, 2 jobs; A100 2 GPUs, 2 jobs. Shared with other projects on the account.
- HF-versus-TransformerLens parity passed for Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct on one smoke prompt in
  float16 (job 399217); extended parity in the study dtype is a G0 item.
- Qwen3-32B: about 20 tokens/s on plain Hugging Face; revision not pinned, no manifest.
- Eight registry models are restored under `/scratch/pabitra/models` with pinned revisions (`docs/model_manifests/`).
