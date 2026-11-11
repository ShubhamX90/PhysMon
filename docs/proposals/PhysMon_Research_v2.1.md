# PhysMon Research Plan v2.1: post-review revision of the v2.0 redesign

**Date:** 2026-11-11. **Status:** revision layer of the plan of record, governing work from Stage 15 onward,
written at the user's direction of 2026-11-11 ("update the v2 plan docs accordingly based on all research").
The open decisions of section 15 have defaults that only withhold an action (nothing is downloaded,
installed, run or retired irreversibly by a default); the user decides each. **Author:** the agent (Claude);
agent-written, checked by an independent agent review against the repository (section 17), not reviewed by a
person outside this session.

**Relation to v2.0.** `docs/proposals/PhysMon_Research_v2.pdf` (v2.0, 14 October 2026) stays in the repository
unchanged and remains the reference for every rule that this document does not change. This document is a
revision layer: it keeps v2.0's identifiers (B0-B7, P0-P11, X01-X12) so that the Stage 14 journal and ledger
still resolve, and states, section by section, what is kept, changed, demoted or retired (section 12). Where
the two disagree on something this document addresses explicitly, this document wins; everywhere else, v2.0
wins.

**What this revision is based on (all in the repository):**

| Input | Where | Tag used below |
|---|---|---|
| The v2.0 plan | `docs/proposals/PhysMon_Research_v2.pdf`, digest `PhysMon_Research_v2_working_digest.md` | [v2] |
| ICLR 2027 reviews of the withdrawn Phase-I paper, verified against committed data | `docs/reviews/iclr2027_submission50608/` (`analysis.md`: 23 checks, 20-issue register) | [REV] |
| Stage 14.0-14.20 results (all exploratory) | `docs/journal/stage14/`, `docs/stage14/status_and_roadmap.md` | [S14] |
| Literature search of 2026-11-11 (three search agents, venue pages opened where marked) | section 14 | [LIT] |
| Measured cluster and stack constraints | `docs/model_manifests/`, Stage 14 job records, model smoke tests | [ENV] |

Tags on statements: [V] checked in files or by computation; [I] inference or design choice; [LIT] from a
cited source. Numeric targets are planning choices, not results.

---

## 1. Why a revision

1. **The Phase-I construct is gone.** The legacy label (teacher-forced log-probability drop of the bare gold
   string, base 0, 0.5 nats) fails for three independent reasons, each reproduced from committed data [REV][V]:
   it scores a string the model was not asked to produce (no `Answer:` prefix; review check C1); it flips with
   the choice of base rendering (40-49 % of Qwen and 41-56 % of Llama base-0 positives; X02) and with the answer
   instruction (pilot labels agree at chance across two instructions; C2b); and a correct formula hint triggers
   it (3.7-5.5 nats; C3). The user retired it on 2026-10-17 (J14.2-011). The paper is withdrawn; none of its
   claims survives as stated; its numbers stay SUBMITTED.
2. **The knockout evidence was one-sided** [REV C8]. The four-head L16 knockout "recovers" more than 100 % in 17
   of 20 families (reversal, not cancellation; C8a), and head 11 alone raises the gold's first-token logit about
   equally on base and sensitive renderings (C8b). A component that boosts the answer regardless of the cue says
   nothing about cue processing. Every future intervention is read as an interaction (section 8).
3. **The "non-activation" comparators were label-derived** [REV C4][V]. The fitted entropy baseline (paper
   0.727; Wave 2 0.7048) is built from the log-probability the label is computed from; the oracle-free entropy
   baseline is 0.520. Every comparator now carries an oracle/deployable tag (section 11).
4. **What Stage 14 established** [S14][V], all exploratory:
   - A same-unit cue numeral becomes a far more probable answer continuation (Qwen2.5-7B about 10-13 nats,
     Llama-3.1-8B 3.5-5 nats from the no-cue prompt), with no detectable dependence on numeric proximity at the
     available precision (intervals of several nats on 10 structures; J14.9). Numbers the problem needs are
     boosted too, less (J14.14).
   - Matching the comparison numerals for plausibility removes about 40 % (Qwen) and 53 % (Llama) of the
     same-unit effect; the incompatible-unit and metadata effects become not distinguishable from plausibility
     (not shown equivalent to zero); the remainder depends on unit compatibility (J14.17-006).
   - The sign survives seven answer formats; size and parse rates depend on format (X03; J14.10, J14.16).
   - Without reasoning both 7-8B models are almost never correct (3/211 and 6/211; J14.7-023). With greedy
     2,048-token reasoning Qwen2.5-7B is correct on 96/211 records and Llama on 50/211, but a sentence with no
     number flips answers about as often as numeric cues, so flips could not be attributed to numerals
     (J14.13-006).
   - Qwen3-32B with thinking answered 63 of 64 graded problems correctly on one sample each (J14.19-009). On 32
     of those candidate anchors the four cue kinds gave 109 correct, 2 wrong and 17 NOT_EVALUATED of 128 cells;
     mean tokens per record were 5,632 against 4,509 without a cue, with medians from 3,849 (irrelevant text) to
     6,538 (role reversal, which also asks for an extra subtraction); truncation was 9.4 % against 11.5 % without
     a cue (J14.19-013, -014). The noise baseline (job 435606) was cancelled, so the cue contrast is
     NOT_EVALUATED (J14.19-015); these numbers support no hypothesis.
5. **The literature has moved** [LIT]. Distractor sensitivity in math (GSM-IC, GSM-Symbolic NoOp, GSM-Plus,
   MathCheck, GSM-DC), anchoring by irrelevant numbers with circuits in 7-8B Qwen and Llama (Owusu et al. 2026),
   copying of the number before the answer delimiter (Liu 2026), length inflation in reasoning models (Gema et
   al. 2025; Fan et al. 2025) and a localisation of NoOp failure to an "operation planning" band (Qu and Gomes,
   Findings of EMNLP 2026) are published. None of these is a PhysMon contribution any more (section 2).

The revision therefore makes four changes to v2.0: (a) the primary endpoint is free-generation correctness
with sampled reasoning, read against the model's own sampling noise, not a likelihood; (b) the question is
narrowed to physical role, with role varied by minimal pairs that hold numeral, unit, position and question
fixed; (c) a model-and-difficulty calibration step precedes every behavioural run, because the 7-8B models are
at the floor without reasoning and Qwen3-32B's single-sample candidate anchors leave little room for a
correctness effect; (d) mechanism work is gated on a behavioural role effect and uses an interaction estimand
with both-direction patching.

---

## 2. Research question, novelty and claim boundaries

**Primary question.** When a physics problem contains a quantity whose irrelevance is certified by the
governing equations, does the quantity's *physical role* change a language model's answer beyond what is
explained by the numeral's presence, its value and plausibility, its unit, its position and generic
perturbation of the text; and if it does, what computation separates relevant from irrelevant quantities?

**Secondary question.** Does reasoning (thinking on versus off within the same weights, and budget) change how
role is used, and is a cue's cost paid in correctness, in length, or in failures to finish?

**Defensible novelty, stated conservatively [LIT][I].** The search of 2026-11-11 found no physics benchmark with
answer-invariant irrelevant quantities certified by the governing equations together with role-swapped
controls, and no factorial that separates physical role from value, unit, position and surface form. The
candidate contributions are:
1. a certified physics-role benchmark (DECOY-v2) whose irrelevant quantities are inert by the physics, not only
   off a dependency path (contrast GSM-DC) or judged irrelevant by an annotator (contrast ProbleMathic);
2. role minimal pairs (section 5.2) in which only the quantity's relation to the system changes, with numeral,
   unit, position and question fixed, plus a marked/unmarked x in-system/separate-system factorial;
3. a wrong-answer taxonomy computed from the typed graph (which wrong answer each misuse of the quantity
   produces; section 5.4), so cue use is read from answers rather than from a likelihood;
4. only if the behaviour warrants it, a causal account of role routing in pretrained models, framed against Qu
   and Gomes (2026), Owusu et al. (2026), Ye et al. (2025) and the binding literature;
5. a methodological record of how teacher-forced string likelihood misled (the Phase-I lesson), modest but
   supported (cf. Yuchi et al., EACL 2026).

**Not claimable as new:** that distractors hurt math or science reasoning; that numeric distractors hurt more
than non-numeric ones; that irrelevant numbers pull answers; that reasoning models write longer under
distractors; that models internally encode which quantities are necessary; that distractor failures localise
to layers or heads. A manuscript cites these as prior work.

**Claim hierarchy (v2 C1-C6, unchanged).** Observational sensitivity < behavioural role effect < causal
mediation < mechanism < generalisation. "Shortcut reliance" and "mechanism" need the evidence named in v2 p.3;
the forbidden-phrase check (`scripts/check_forbidden_phrases.py`) stays on.

---

## 3. Hypotheses and their distinguishing predictions

All six are legitimate outcomes (v2 p.3); the design must be able to support each.

| Id | Hypothesis | Predicts | Distinguishing test |
|---|---|---|---|
| H0 | No role or presence effect beyond generic perturbation | Numeric cells and role twins = matched non-numeric sentence | Equivalence on the presence and role contrasts (9.2) |
| H1 | Numeral presence: any number in context raises its own use | COPY answers for any role and unit | COPY rate equal across roles and units |
| H2 | Plausibility and unit: the cue is used when it could be the answer | Effect only for same-unit or convertible plausible values | Unit x proximity cells; plausibility-matched values |
| H3 | Relevance-selection failure: an irrelevant quantity enters the computation | Answers equal to the role twin's gold (MISUSE); larger for in-system and unmarked quantities; reduced by a relevance instruction | Role minimal pairs; 2x2 marking factorial; relevance-instruction cell |
| H4 | Readout contamination: computation right, final answer pulled to the cue | Correct value in the trace, final answer copies or moves toward the cue; little help from a relevance instruction | Trace-final mismatch audit; readout-position intervention (8.13) |
| H5 | Computational diversion: the cue costs length, not correctness | Longer traces and more truncation with correctness unchanged (shown by equivalence) | Cost endpoints against the self-noise floor; budget sweep |

At the likelihood level Stage 14 data fit H1 and H2 [S14][I]. No behavioural hypothesis has been tested: the
reasoning flips of J14.13 could not be separated from generic perturbation, and the Qwen3-32B cue contrast is
NOT_EVALUATED.

---

## 4. Endpoints

**E1, primary: free-generation correctness with sampled reasoning.** Per item i and condition c, k sampled
generations under a frozen reasoning contract; p_ic = share of the k records graded CORRECT, over all records
attempted. A NOT_EVALUATED record (TRUNCATED, UNPARSEABLE, MULTIPLE_CANDIDATES, EMPTY) is "not correct" for
p_ic but is never relabelled WRONG: the three categories CORRECT / WRONG / NOT_EVALUATED are always reported
separately, and the complete-case share (evaluable records only) is a sensitivity analysis. Rationale: cues
change length and truncation (Llama had 43 of 211 records not evaluated in J14.13), so conditioning on
evaluability would condition on a post-treatment variable. A cell with zero evaluable records is NOT_EVALUATED,
never a zero effect.

**Sampling is required.** The Stage 14 reasoning runner for Qwen2.5 and Llama (`s152`) is greedy and unbatched
(J14.13-001), so k greedy samples would be identical. G1 defines a new reasoning-contract version with sampling
at each model's published `generation_config` defaults (recorded in every record) and batched generation;
Qwen3 thinking uses T 0.6, top-p 0.95, top-k 20 (the model card forbids greedy decoding), non-thinking T 0.7,
top-p 0.8, top-k 20. Greedy runs remain as Stage 14 records and are not pooled with sampled ones.

**E2: relevant-use correctness.** On the relevant twin of each role pair (5.2.1) the endpoint is agreement with
that twin's own gold. This is the test that the model uses an *added* quantity when the physics makes it
relevant; a model that ignores every added number passes E1 cells and fails E2, so E1 without E2 is not
evidence of role sensitivity. (`relevant_edit` changes an existing input and adds no numeral, so it does not
serve this purpose; it stays as a check that inputs are read.)

**E3: wrong-answer class.** Every WRONG answer is classified once, in this precedence: GOLD-ADJACENT (rounding
or unit-only, by the unit-convertible view), WRONG_DIMENSION, COPY (equals the cue value within tolerance after
unit conversion), MISUSE (equals a graph-computed misuse foil, 5.4, including the role twin's gold), OTHER. E3
rates are per attempted record, so they can be compared across conditions; their power is simulated (9.4)
because Stage 14 reasoning runs gave the cue as the final answer in 0-1 of 20 cells (J14.13).

**E4: cost.** Generated tokens (mean and median, never compared across the two), TRUNCATED share and
thinking-closed share per condition, each against the same items' no-cue samples and the self-noise floor.

**E5, secondary: candidate log-odds.** Teacher-forced on the model's own completed trace, the log-odds between
the gold and the strongest foil in the instructed answer format. It is the metric of the mechanism work and a
secondary behavioural endpoint: continuous metrics carry more signal per item than accuracy (Heineman et al.
2025), but it is a two-candidate contrast after the model's own reasoning, never a single-string probability
(review issues 1 and 15), and a behavioural claim needs E1.

**Grading protocol, frozen in G1** [LIT][I]:
1. Only text after the end-of-thinking marker is graded; a missing marker is TRUNCATED (Qwen's sample parser
   treats the whole output as the answer when `</think>` is absent; that must not be copied).
2. Units are parsed and converted with a dimension check (`pint` or the existing unit module), never stripped
   (Math-Verify strips units and is not used for them).
3. Every record stores its relative error to the gold. Three views are reported: the declared
   last-printed-place rule (primary), the unit-convertible rule, and relative error <= 1 % with
   dimension-checked conversion (the field's convention: UGPhysics, PHYSICS; the declared rule failed a 0.05 %
   error in Stage A, J14.19-009).
4. **Tolerance versus cue distance.** A cue or foil that lies within a view's tolerance of the gold makes that
   cell ambiguous under that view (a COPY would be graded CORRECT): the cell is excluded from E1 and E3 for that
   view and counted. The v1 near cues lie 0.1-0.8 % from the gold (J14.17-001), so under the 1 % view they are
   ambiguous; new near cues are generated outside the loosest tolerance (planning: 2-5 % from the gold).
5. A stratified parser audit (every UNPARSEABLE record plus a random sample of graded ones) reports the
   parser's false-negative rate (rule-based graders have shown large false-negative rates elsewhere; TinyV,
   arXiv 2505.14625). No LLM judge in the primary analysis.

**Retired:** the legacy `S_lp` label and any single-string teacher-forced probability as an endpoint.
**Kept as diagnostics:** the anchor-matched presence boost (J14.9) and R_alt.

---

## 5. Items and conditions (DECOY-v2, revised)

### 5.1 What exists [S14][V]
`data/v2/dataset/v1`: 260 instantiations of 80 typed structures in 11 domains, gold traces from the typed
graph, 11 factor cells each (2,764 of 2,860 feasible). All items are `UNREVIEWED` (agent-built and
agent-verified at the user's instruction of 2026-10-26); S01-S20 also had the user's walkthrough. The
non-governing cues carry an explicit disclaimer in the text: of 1,464 feasible cells, 1,085 say the quantity is
"unrelated", 39 "not connected", 11 "takes no part", 9 "in a separate experiment", and the rest other
separating wording; so the prompt itself tells the model the cue is irrelevant. `role_reversal` reuses the
moderate cue's value in every cell and changes the question (the answer minus system B's value): it tests use
on request, not role with the question fixed. `relevant_edit` changes an existing input; it adds no numeral.

### 5.2 Cells added or redefined by this revision [I]
1. **Role minimal pairs (primary role contrast).** Two prompts identical in the numeral, its unit, its
   position, the sentence frame and the question, differing only in a relational phrase that makes the
   quantity part of the system (relevant twin; its gold is recomputed by the solver) or not (irrelevant twin;
   gold unchanged). Example frame: "The pulley hangs from a support that is [attached to the left block /
   mounted on a separate stand]" with the same quantity attached. Feasibility depends on the structure; the
   generator records infeasibility, never imputes. The irrelevant twin's MISUSE foil is the relevant twin's
   gold. Twin golds that coincide within the loosest tolerance make the pair ambiguous and it is excluded.
2. **Marking x system factorial (H3).** A 2 x 2 of {in-system inert, separate-system} x {disclaimer present,
   disclaimer removed}, matched within item on the quantity's dimension and value. *In-system inert* means a
   quantity of the same system that is physically meaningful but cancels or does not enter the governing
   equations (for example a pulley radius when the moment of inertia is given as a fraction of M R^2 and R
   cancels); certification: the solver's answer is invariant over a declared range and the symbolic program's
   derivative with respect to it is zero. Only dimension-matched variants enter this contrast, because unit
   compatibility dominated the Stage 14 likelihood effects.
3. **Formula hint (review issue 3).** A correct relevant formula or intermediate value. Expected direction:
   it *helps* (raises E1); it is the positive control for "context information is used" and the behavioural
   counterpart of review check C3.
4. **Relevance instruction.** No-cue and cue prompts with a one-line instruction to identify and ignore
   irrelevant information (I3C style, Wu et al. NAACL 2024). H3 predicts it reduces MISUSE; H4 predicts little
   change. Also the cheapest mitigation baseline (v2 P10).
5. **Cue position.** Before versus after the relevant inputs for the role pairs and the same-unit cue (v2 B3.4;
   position is fixed today; Liu 2026 shows the number nearest the answer delimiter is copied).
6. **Kept from v1:** no-cue, non-numeric matched-length sentence, same-unit near (regenerated outside the
   tolerance, 4.4) and far, incompatible unit, numeric metadata, convertible unit (v2 V2-B invariance), relevant
   edit, role reversal (use on request).

### 5.3 Item difficulty [I]
Items are useful only near the model's competence boundary. Calibration (G2) selects structures whose no-cue
correctness lies in a band fixed in G1 (planning 0.3-0.85), and adds harder variants (more steps,
upper-university levels, unit conversions) where a model is near ceiling. Comparisons *between* models or
between thinking on and off use one common item set, selected so that every compared configuration is inside
the band; per-model sets are used only for within-model contrasts.

### 5.4 Foils computed from the graph [I]
For each cell the generator emits a frozen list of foil answers, each the result of one named misuse: COPY (the
cue value, converted to the requested unit), the role twin's gold, SUBSTITUTE(slot) (the quantity replaces the
input of the same dimension), ADD-TERM (the quantity enters a sum of same-dimension terms) and, for in-system
inert quantities, the result of the most likely wrong law that keeps the quantity. Foils that coincide with the
gold or with each other within the loosest tolerance are marked ambiguous for E3. The list is frozen with the
item, before any model output.

### 5.5 Validation status and data roles [I]
v2.0's five data roles stay (EXPLORATION, GENERATOR_TUNING, INTERNAL_CONFIRMATION, EPC_CONFIRMATION,
ADVERSARIAL_CHALLENGE; v2 p.12) and so does the shadow test set (p.20). This plan maps its steps onto them: the
80 existing structures and all Stage 14 records are EXPLORATION, and G2/G3 runs on them stay EXPLORATION
(calibration and pilot are uses within that role, not new roles); new structures for G4 are
INTERNAL_CONFIRMATION, untouched by any run before G4 opens; a shadow subset of them is held back by lineage.
A structure never moves from EXPLORATION to a confirmation role. Confirmatory claims need structures that pass
v2 B4 (independent expert review, two-pass rubric, parser criterion). If no independent reviewer is available,
G4 is run but labelled EXPLORATORY-REPLICATION and no text may call it confirmatory (decision D2).

---

## 6. Models, budgets and tooling

| Role | Model | Why | Status [ENV][V] |
|---|---|---|---|
| Primary behaviour and mechanism | Qwen2.5-7B-Instruct, sampled reasoning, 2,048 tokens (budget sweep in G2) | Mid-range accuracy with reasoning on v2 items; TransformerLens 3.4 "full verification"; HF-versus-TL parity passed on 2026-10-17 (job 399217) | Restored, revision pinned, manifest |
| Second family | Llama-3.1-8B-Instruct | As above, lower accuracy | Restored, pinned; parity passed (399217) |
| Thinking on/off within one model | Qwen3-8B (optionally Qwen3-14B) | Same weights with and without thinking separate reasoning from model identity; TL 3.4 "core verification" for 8B | Not downloaded (D3) |
| Scale and ceiling check | Qwen3-32B, thinking | Hard subset only | Present on scratch (not re-downloaded); **revision not pinned, no manifest**; TL unverified |
| Not planned | DeepSeek-R1-distill, Mistral, Qwen2.5-32B judge, 397B NVFP4 judge | Not needed for the primary question; v2 p.42 advises against committing to the 397B model | Kept on scratch |

Tooling [I][LIT]:
- **Generation engine (D4).** Plain Hugging Face `generate` gave Qwen3-32B about 20 tokens/s aggregate with no
  gain from batch 2 to 3, far below the memory-bandwidth bound (J14.19-007, -009). KV memory does not explain
  this: at about 256 KiB per token, the 10-18 GB left after the bf16 weights hold roughly 40,000-70,000 tokens,
  several 6,000-token sequences. A faster engine is therefore expected to help. If vLLM is adopted: a fresh
  `uv` environment (vLLM wheels bundle their own torch and conflict with conda torch; current release 0.33.0,
  2026-11-02; check the cluster's CUDA driver first), a logit and greedy-output parity check against the pinned
  Hugging Face stack on fixed prompts, and a short timing job before any study run. Generation and analysis
  are split: vLLM generates and saves token ids; activations and E5 come from a Hugging Face teacher-forced
  forward pass over the saved sequences, so hooks never run inside vLLM. Without vLLM the plan runs on the
  7-8B models (section 10).
- **Parity.** HF-versus-TransformerLens parity passed for Qwen2.5-7B and Llama-3.1-8B on the smoke prompt
  (top-1 equal, cosine 0.99998 and 0.99999; job 399217, `results/infrastructure/model_smoke/attempt_20261017_gpu_h100/`).
  G0 adds what that check does not cover: parity at the hook sites G5 will use, on traces of the planned length,
  and for any further model.
- **Mechanism tools.** TransformerLens 3.4 (pinned) for the 7-8B models; pyvene for DAS; Qwen3-32B only in bf16
  (TL 3.4 `boot()` defaults to float32) through the TransformerBridge or plain forward hooks, exact patching
  only, after a parity test.
- **Qwen3-32B provenance.** Pin its revision and write its manifest before any further run. Runs 417416, 425243
  and 435605 stay `model_commit NOT_RECORDED` unless the file hashes on scratch match a published revision, in
  which case the match is recorded as an after-the-fact identification, not as a pin at run time.
- **Budget.** The thinking budget is part of the contract; 12,288 tokens truncated 9-12 % of Qwen3-32B records.

---

## 7. Critical path (gates G0-G6)

Each gate names its passing condition and what happens otherwise; each needs a committed gate report. The v2
blocks it implements are in brackets.

### G0. Closure and repair (CPU, plus one short GPU check) [v2 P0, B1; reviews]
1. **Status sync:** update `docs/stage14/status_and_roadmap.md` through 14.20; ledger rows and a decision-log
   entry for job 435605 and the 435606 cancellation; fix the stale INDEX rows.
2. **The seven review-derived additions** (`analysis.md` section 5 point 2), each as a concrete artifact:
   (a) cross-instruction stability of any label on the pilot families (CPU recomputation where records allow,
   otherwise NOT_EVALUATED); (b) the formula-hint cell (5.2.3); (c) the interaction rule for every intervention
   (section 8.1); (d) the oracle/deployable tag on every comparator, propagated to the Wave 2 record and the
   claim ledger; (e) a mechanical claim-wording check between any manuscript draft and the claim registry; (f) a
   provenance-consistency check that `created_by` and validation fields match any text about authorship and
   validation; (g) a dated note that the 0.5-nat threshold was chosen after the Stage 4 results and does not
   transfer across instructions.
3. **P0, narrowed (D1).** v2's full regeneration of Phase-I values is not on the critical path, because the
   paper is withdrawn and no new claim rests on its numbers. What stays: the extended parity check of section 6,
   and a forward-pass spot check of 10 legacy families' stored log-probabilities if a Phase-I number is ever
   cited again. If the user keeps the full P0 (D1), it runs as a side track; it does not block G1-G4.
4. **Phase-I closure note:** which Phase-I statements survive (descriptive: the label moves with base,
   instruction, in-context answer information and the scoring string) and which do not (every causal and
   monitoring claim as stated).

*Passes when* the items above are committed. *If the extended parity check fails* for a model or backend: no
mechanism work on it; behaviour can proceed.

### G1. Construct freeze (CPU) [v2 B2, B3, P1, P4.1]
Freeze, before any G2 output: the endpoints and grading protocol of section 4; the sampled reasoning-contract
version (also parsing a LaTeX-wrapped final line, which cost 5 of 78 Stage A records; prospective only, never
applied to old records); the foil generator (5.4); the cells of 5.2 with certificates and mutation tests; the
analysis scripts with tests on synthetic records; the G3 decision rules (below) with their numeric thresholds;
the equivalence margin (9.2); experiment cards for G2-G4 from `docs/experiment_cards/TEMPLATE.md`.

*Passes when* the tests pass and the cards are committed. Nothing is run before.

### G2. Model and difficulty calibration (GPU, small) [v2 B6, P1]
Per candidate model and budget: k_sel = 4 no-cue samples on every structure to select items in the band, then
k_est = 4 fresh no-cue samples on the selected items to estimate the baseline and the self-flip floor (never the
selection samples: the 14.20 preliminary analysis is the worked example of that bias, J14.19-014). On the
selected items, also k = 4 samples of one same-unit cue cell and of the non-numeric sentence, so that the
variance of a *cue difference* (omega in 9.4) can be estimated, not only the no-cue variance. Also measured:
tokens per record, truncation, parse failures. Output: per model, the item set, baseline correctness, omega and
run cost; and the common item set for cross-configuration comparisons (5.3).

*Passes when* at least 40 structures per model fall in the band (the number the power and equivalence
arithmetic of section 9 assumes) with a cost that fits section 10. *If not:* add harder or easier variants
(5.3) or change the budget; a model that stays outside the band is reported as such and dropped from E1, not
forced. The band is not changed after seeing G2 results.

### G3. Pilot of the role factorial (GPU, medium) [v2 B6, P4, X04]
Primary model first (Qwen2.5-7B-Instruct); the second model (Llama-3.1-8B-Instruct) runs only if it passed G2.
Conditions on the calibrated items (one instance each): no-cue; non-numeric sentence; role pair (relevant and
irrelevant twin); the 2 x 2 marking factorial (four cells); same-unit near and far; incompatible unit;
convertible unit; formula hint; relevance instruction (with the irrelevant twin and with no cue); cue position
(irrelevant twin moved). That is 16 conditions where all are feasible; infeasible cells are recorded. G3 is
EXPLORATION: its intervals estimate effects and select at most one primary contrast for G4; it confirms nothing.

**Decision rules (thresholds fixed numerically in G1; planning values given).** Contrasts are structure-level
paired differences with 95 % intervals (9.2); "positive" = interval excludes 0 in the stated direction;
"equivalent" = TOST within the G1 margin.

| Order | Rule (estimand: interval condition) | Reading | Action |
|---|---|---|---|
| 0 | E2 on relevant twins below a floor (planning 0.5) or formula hint does not help | The model does not use added inputs at this band | Recalibrate; no role reading |
| 1 | Too few evaluable or unambiguous pairs for the power target | NOT_EVALUATED | Never read as a zero effect; resize or stop |
| 2 | MISUSE rate (irrelevant twin) minus its no-cue rate positive, and larger for unmarked and in-system cells | H3 | Primary contrast for G4; G5 after G4 |
| 3 | Correct value in trace but COPY or cue-directed final answer, rate positive against no-cue; relevance instruction does not reduce it | H4 | Primary contrast for G4; G5 at readout positions after G4 |
| 4 | E1 (non-numeric minus same-unit cue) positive, COPY share positive, no difference between role twins | H1 or H2 (H2 if confined to same-unit/convertible plausible cells) | Behavioural report; G5 optional, only for the unit-matching computation, framed against Liu 2026 and Owusu et al. 2026 |
| 5 | E1 contrasts equivalent within the margin, E4 tokens or truncation positive against the self-noise floor | H5 | Cost report; budget sweep; no G5 |
| 6 | All presence and role contrasts equivalent within the margin, E4 not positive | H0 at this band | Try the other band once; if H0 again, write up as a certified null with its power |
| 7 | A cue *raises* E1 (other than the formula hint) | Unexpected help | Report; check for leakage of the answer into the cue |
| 8 | None of the above (mixed or undetermined) | Unclassified | Report as undetermined; no G4 on this model and band |

Rules are applied in order; the first that matches decides. More than one hypothesis can be true; rows 2 and
3 are both recorded if both match, and G4 then preregisters the one with the larger effect on G3 data, stating
that the choice was made on EXPLORATION data.

### G4. Behavioural replication on held-out structures (GPU, medium) [v2 B4, B6, P3, P4, X06]
Preregister the one contrast G3 selected, its estimand, decision rule and the sample size from the power
simulation, on new structures in template clusters no earlier run has touched (INTERNAL_CONFIRMATION, 5.5),
validated under B4 or labelled EXPLORATORY-REPLICATION (D2). Primary model: Qwen2.5-7B-Instruct, one-sided
test at alpha 0.05; secondary: Llama-3.1-8B-Instruct, tested only if the primary passes (fixed sequence). Format
robustness (v2 B6): the final-answer line is run in two declared formats on a random half of items, and the
contrast must keep its sign in both. Opened once.

*Passes when* the primary model meets the rule; "replicates on the second model" means its own one-sided test
passes. *If not:* the G3 effect is reported as not replicated.

### G5. Mechanism (GPU) [v2 P6-P9, X07-X09]
Gated on G4 passing for H3 or H4; under H1/H2 only the optional unit-matching study of rule 4. Protocol in
section 8. Starts on Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct; Qwen3-8B with thinking after that; Qwen3-32B
only for a frozen-function transfer test (v2 P9: freeze the function, not the head index).

### G6. Optional extensions [v2 B5, P5, P9, P10]
EPC external physics sets (v2 B5; used for P11's external cohort); non-physics transfer (GSM-DC or GSM-Symbolic
NoOp with the same factorial where it maps); monitoring (demoted, section 12); repair (mechanism-guided edit
against the cheap ladder: relevance instruction, self-consistency, longer budget); scaling ladder.

---

## 8. Causal protocol for G5 [LIT][REV]

Built so that a cue-independent effect cannot be read as cue processing (the head-11 lesson).

1. **Estimand: paired interaction.** For metric m (E5 on the model's own trace), item i, cue prompt S_i
   (irrelevant twin) and control prompt B_i (no cue, and separately the relevant twin):
   I_h(i) = [m(S_i, intervened) - m(S_i, clean)] - [m(B_i, intervened) - m(B_i, clean)].
   The cue effect m(S_i, clean) - m(B_i, clean) is reported beside it. A component matters for cue processing
   only if I_h is non-zero; a large equal effect on both prompts marks a general answer component.
2. **Both directions.** Noising (tests necessity) and denoising (tests sufficiency), reported separately; they
   are not complements (Heimersheim and Nanda 2024).
3. **Counterfactuals in distribution.** The role minimal pairs are the primary counterfactual (token-aligned,
   only the relational phrase differs); several corruptions per item (Zhang and Nanda, ICLR 2024). No Gaussian
   noise; no zero ablation as evidence.
4. **Metric:** log-odds or logit difference with each candidate's logit shown; never probability; never
   normalised recovery (values above 1 come from negative components, not cancellation).
5. **Ablation semantics:** resample or interchange from matched counterfactuals as primary, mean ablation as a
   sensitivity; the conclusion reported under both (Miller et al. 2024; Li and Janson 2024).
6. **Direct and total effects** with a frozen-final-LayerNorm control for self-repair (Rushing and Nanda 2024;
   McGrath et al. 2023).
7. **Divergence check:** patched activations compared with the natural distribution at that site, and KL on
   neutral control prompts (Grant et al., ICLR 2026).
8. **Screen, then confirm:** attribution patching only as a screen; every reported component confirmed by
   exact patching (Kramár et al. 2024).
9. **Selection stability:** components re-selected on bootstrap subsamples with inclusion frequency reported;
   selection on a discovery split of EXPLORATION structures, tests on held-out structures only (Certified
   Circuits, ICML 2026; review issue 6).
10. **Nulls and multiplicity:** matched random components of the same layer and type; family-wise correction over
    the components tested.
11. **Rescue:** knock out the candidate set on S, restore it from a different item with the same role (should
    rescue) and from one with the opposite role (should not).
12. **Variable claims need causal abstraction:** a binary relevance variable localised by DAS (pyvene), with
    interchange-intervention accuracy on held-out pairs against neuron and random-subspace baselines (MIB, ICML
    2025), plus the subspace-illusion check (Makelov et al., ICLR 2024).
13. **Reasoning models:** (i) readout effect: teacher-force the model's own trace and intervene only at the answer
    positions; (ii) total effect: intervene at the cue tokens and resample N traces per condition (Thought
    Branches, 2025); never a hand-edited trace as primary evidence; no conclusion from one sample.
14. **Probes are diagnostic only** (Hidden Error Awareness, 2026).
15. **Held-out prediction:** before the test, the predicted sign and size of I_h on held-out structures and the
    second model are committed.

---

## 9. Statistics

### 9.1 Unit and estimands
The structure is the unit of inference (template cluster where structures share one); instances and samples are
nested in it. Per contrast: the mean over structures of the within-structure difference in p (E1) or in the E3
rate. Primary contrasts by hypothesis: presence, p(non-numeric sentence) - p(same-unit cue); role, MISUSE rate
of the irrelevant twin minus the no-cue rate of the same foil, and p(relevant twin correct) for E2; marking,
the interaction in the 2 x 2 of 5.2.2. NOT_EVALUATED handling as in E1.

### 9.2 Intervals and tests
Average samples and instances within structure first, then a paired analysis of the J structure-level
differences: t-interval with J - 1 degrees of freedom and a sign-flip randomisation test. Never pool the k x N
draws as independent (Miller 2024). At J of a few dozen, CLT and bootstrap intervals under-cover (Bowyer et al.,
ICML 2025), so the Stage 14 cluster bootstrap (2,000 resamples, seed 42) becomes a sensitivity analysis together
with a clustered Bayesian interval. Secondary model: mixed-effects logistic regression with structure and
instance random effects, simplified when the fit is singular (Matuschek et al. 2017), reporting the marginal
risk difference. Cue-induced flips are read against the self-flip floor measured in G2, never against zero.

**Equivalence margin:** fixed numerically in G1 at 0.10 in p (planning value), with no data-dependent
adjustment. TOST at 80 % power with a true effect of zero needs about 8.6 omega^2 / Delta^2 structures (omega =
standard deviation of the per-structure difference), so with 40 structures a 0.10 margin is supportable only if
omega is about 0.22 or less; if G2's omega is larger, G1's sample size (not the margin) is revised before G3,
and equivalence is not claimed where the sample cannot support it. Delta = 0.05 is not supportable at this scale
(about 137 structures at omega = 0.2).

**Multiplicity:** G3 is estimation; G4 tests one preregistered contrast with a fixed sequence across models.
If queue delays force batches in G4, one interim analysis at half the sample with Lan-DeMets O'Brien-Fleming
spending may be preregistered.

**Truncation:** reported three ways for every contrast: all records with NOT_EVALUATED as not correct (primary,
E1), evaluable records only, and truncated counted as wrong (a bound; answers at the length limit are almost
always wrong in published reasoning evaluations, Hochlehnert et al. 2025). Truncation share and length are
outcomes of their own (E4).

### 9.3 Selection bias
Items are selected on samples that are never reused to estimate the baseline (G2); every analysis reports the
selection rule; the 14.20 preliminary contrast (baseline 1.000 by construction, J14.19-014) is the worked
example.

### 9.4 Power
Simulated before G3 and G4 from the G2 estimates (structure and instance variance components, omega of the cue
difference, within-item Bernoulli variance, which more samples reduce and between-structure variance does not;
Wang 2026), for J in {24, 40, 60, 80} and k in {3, 5, 8}, at least 1,000 simulated datasets each analysed
exactly as planned, for E1 and for the E3 MISUSE and COPY rates (which may be rare). Analytic bracket [LIT]: for
80 % power at alpha 0.05, J is about 7.85 omega^2 / delta^2 (Miller 2024). With omega = 0.25, delta = 0.10 needs
about 49 structures and delta = 0.15 about 22; with J = 40 the minimum detectable difference is about 0.44 omega.

---

## 10. Compute and effort budget [ENV][I]

Measured: Qwen2.5-7B and Llama-3.1-8B greedy, unbatched reasoning at 2,048 tokens took 12.6 s and 14.7 s per
record (job 401357; sampling and batching will change this); Qwen3-32B thinking 19.8-20.8 tokens/s aggregate
with 4,983-5,242 median and 5,632 mean tokens per record (jobs 417416, 425243, 435605), about 14 records per
hour; hard items truncate more (5 of the 7 upper-university Stage A problems). H100 queue waits on the shared
account were 38 hours to 6 days.

| Step | Generations (planning) | 7-8B, HF at the measured rate (per model) | 7-8B, vLLM (estimate) | Qwen3-32B thinking |
|---|---|---|---|---|
| G2: 80 structures x 1 instance x k_sel 4, then about 40 x (k_est 4 + 2 cue conditions x 4) | about 800 | about 3 h | under 0.5 h | not planned |
| G3: 40 structures x 16 conditions x k 8 | 5,120 | about 19 h, run as 2-3 jobs | about 1 h | excluded |
| G4: J from 9.4 (planning 50) x 2 paired conditions x 2 formats on half x k 8 | about 1,200 | about 5 h | under 0.5 h | hard subset only |
| Qwen3-32B hard subset: 20 structures x 4 conditions x k 4 | 320, at 8,000-12,000 tokens each (2.6-3.8 M tokens) | - | - | HF 35-55 h; vLLM bf16 several hours (estimate) |
| G5 mechanism | items x sites x pairs | hours on 7-8B (HF teacher forcing) | n/a | exact patching, small set |

vLLM figures are estimates from published single-H100 benchmarks (thousands of output tokens per second for 7-8B
models, hundreds for 32B in bf16), not measurements here; the timing job replaces them. Jobs are sized to finish
in under 10 hours with a clean time budget (as `s164` does), because 1-6-day queue waits make many short jobs
costly; G3 at HF speed is therefore split into 2-3 jobs by condition block, all from one frozen commit.

**Human effort (not GPU):** G4 needs about 50 new structures. Generating and certifying them is agent and CPU
work; independent B4 review is about 15-20 minutes per structure per reviewer (planning), i.e. about 12-17 hours
per reviewer for two-pass review of 50, plus adjudication. Without reviewers, G4 is EXPLORATORY-REPLICATION.

Each job still needs the user's acceptance of its exact command (AGENTS.md, skill).

---

## 11. Governance additions (review-derived)

1. **Comparator tags.** Every comparator is labelled `oracle` (needs y* or the label's inputs at inference) or
   `deployable`; no `oracle` comparator is called "non-activation", "one forward pass" or "cheap" (review issue
   4; the Wave 2 record annotated in G0).
2. **Wording check.** Before any manuscript or external summary, a script compares its claim sentences with the
   claim registry's prohibited wording and the ledger's evidence level (review issue 7).
3. **Provenance consistency.** `created_by`, `verified_by` and `admission_category` must match any statement
   about authorship and validation; agent authorship and agent verification are disclosed (review issue 10;
   Y9cR Q5).
4. **Threshold honesty.** Every threshold records when it was fixed relative to the data it is applied to
   (review issue 16).
5. **Interventions read as interactions** (8.1) in every card that intervenes (review issue 5).
6. **NOT_EVALUATED is not a null and not WRONG.** Unchanged from v2; restated because Stage 14 thinking runs
   had 10-25 % NOT_EVALUATED records, and because the primary E1 now counts them as "not correct" while keeping
   them a separate category.
7. **Data roles** as in 5.5 (v2's five roles and the shadow set, unchanged).

---

## 12. Disposition of v2.0, section by section

| v2.0 section | Disposition | Note |
|---|---|---|
| Rules of p.3 (estimands, alternative theses, source tags) | Keep | Restated in 2 and 3 |
| Data roles (p.12) and shadow set (p.20) | Keep unchanged | 5.5 maps G2-G4 onto them |
| B0 threat model, novelty audit | Keep; partly done here | Sections 2 and 14 |
| B1 reproduce and break v1 | Close | Reviews and Stage 14 broke v1; B1.5 verifier audit only if v1 is reused |
| B2 construct choice | Decided here | E1 primary; H-T and H-N of v2 become H1/H2; H-P becomes H3/H4 |
| B3 typed generator | Keep, extend | Cells 5.2, foils 5.4, position, difficulty variants |
| B4 human validation | Keep, unresolved | Required for G4 to be confirmatory (D2) |
| B5 external sets (EPC physics; MATH-X) | Demote to G6 | EPC remains the source of P11's external cohort; it is needed only after G4 |
| B6 pilot, power, roles; "not dominated by format" | Keep, restructured | G2 + G3 with simulation; G4 runs two final-answer formats |
| B7 Phase-B go/no-go | Replace | By the G3 decision rules |
| V2-A relevance cells | Keep, extended | 5.2 |
| V2-B invariance/equivariance (ex-Cue C) | Keep | The convertible-unit cell is in G3 |
| P0 full reproduction | Narrow (D1) | Extended parity kept; full regeneration a side track if the user keeps it |
| P1 measurement validity | Close | Its likelihood findings are diagnostics now |
| P2 scale DECOY-v2 to 300-600 | Demote | Only the structures G3/G4 need |
| P3 validation, parser, leakage | Keep | Parser audit now includes LaTeX final lines |
| P4 behavioural discrimination | Keep, central | G3/G4 |
| P5 monitoring | Demote to G6 | The Phase-I monitor under cluster-held-out folds is a side track; needs activations |
| P6-P8 relocalisation, function, circuit | Keep, gated | Section 8 replaces recovery-based reading; H11 is not the starting point |
| P9 generalisation | Keep, gated | Function-level transfer to Qwen3 |
| P10 repair | Keep in G6 | Cheap ladder includes the relevance instruction |
| P11 closure | Keep | External cohort from EPC; venue after the result |
| X01-X03 | Done (exploratory) | |
| X04 physics-semantic factorial | Becomes G3/G4 | |
| X05 leakage and OOD monitor | Side track (G6) | |
| X06 frozen external replication | Partly folded into G4 (internal); external part stays with EPC in G6 | |
| X07 H11 lesion | Retire as stated | Replaced by section 8 on components found anew |
| X08-X12 | Keep, gated on G4 | |

---

## 13. Contingencies

- **Outside the band** after harder or easier variants: report the model as uninformative at that budget; the
  band is not changed after seeing results.
- **No independent reviewer:** results stay exploratory; any manuscript presents them as such, with the
  agent-authorship and agent-verification disclosure.
- **vLLM not approved:** 7-8B only; Qwen3-32B only for a small hard-subset check, if at all.
- **Role pairs infeasible for many structures:** the role contrast is run on the feasible subset with its count
  stated; structures are not edited to force feasibility after G1.
- **Queue starvation:** CPU work (G0, G1, foils, cards, new structures) continues; jobs are sized under 10 hours.
- **H0 or H5:** a certified null with equivalence bounds, or a cost finding, is a result; it is written up as
  such, not rescued by new endpoints.

---

## 14. Literature basis (searched 2026-11-11)

[R] = the venue or arXiv page was opened by a search agent and the entry confirmed; "per arXiv" = only the arXiv
comment claims the venue. The two entries closest to the novelty boundary (Qu and Gomes; Owusu et al.) were
re-opened by the planning agent.

**Closest-work matrix**

| Work | Role control | Invariance certified | Reasoning models | Causal analysis | Physics |
|---|---|---|---|---|---|
| GSM-IC (Shi et al., ICML 2023) [R] | No | Manual | No | No | No |
| GSM-Symbolic NoOp (Mirzadeh et al., ICLR 2025 per arXiv) [R] | No | Template | Yes | No | No |
| GSM-Plus (Li et al., ACL 2024) [R] | No | Manual | No | No | No |
| MathCheck (Zhou et al., ICLR 2025) [R] | No | By design | Partly | No | No |
| GSM-DC (Yang et al., EMNLP 2025) [R] | Off-path nodes | Graph | Limited | No | No |
| ProbleMathic (Anantheswaran et al., ICLR 2025 workshop) [R] | Relevance taxonomy; "no shared unit" construction rule | LLM + human | No | No | No |
| Numerical sensitivity (Sun et al., arXiv 2511.08022) [R] | Numeric vs non-numeric | Not stated | Not stated | No | No |
| Inverse scaling in test-time compute (Gema et al., TMLR 2025 per arXiv) [R] | No | Trivial | Yes (Qwen3-32B scaled positively on controlled Misleading Math) | No | No |
| Physics of LMs 2.1 (Ye et al., ICLR 2025) [R] | Necessary vs unnecessary parameters | Synthetic | No | Probing | No |
| Four-stage decomposition (Qu and Gomes, Findings of EMNLP 2026) [R, re-opened] | Filler vs NoOp | Manual | No | Patching, ablation | No |
| Anchoring pathways (Owusu, Wiegreffe, Feldman, arXiv 2606.12818) [R, re-opened] | No | Multiple choice | No | Circuits (7-8B Qwen, Llama) | No |
| The Readout Shortcut (Liu, arXiv 2605.22870) [R] | Position and framing | - | No | Patching-style | No |
| Premise removal (Meadows et al., Findings of EMNLP 2024 per arXiv) [R] | Premise removal | - | No | No | Yes |

Physics benchmarks found without irrelevant-quantity tests (per their abstracts): UGPhysics (ICML 2025),
PhysReason (ACL 2025), PHYSICS (Findings of ACL 2025), SciBench (ICML 2024), PhySense, PhysicsEval, SeePhys.

**Methodology (section 8):** Zhang and Nanda (ICLR 2024); Heimersheim and Nanda (arXiv 2404.15255); Kramár et al.,
AtP* (arXiv 2403.00745); Syed et al. (BlackboxNLP 2024); Rushing and Nanda (ICML 2024); McGrath et al. (arXiv
2307.15771); Li and Janson (NeurIPS 2024); Miller, Chughtai and Saunders (COLM 2024); Grant et al., divergent
representations (ICLR 2026); Anani et al., Certified Circuits (ICML 2026); Mueller et al., MIB (ICML 2025); Geiger
et al., causal abstraction (JMLR 2025) and DAS (CLeaR 2024); Makelov et al. (ICLR 2024); Bogdan et al., Thought
Anchors (arXiv 2506.19143); Macar et al., Thought Branches (arXiv 2510.27484); Yuan et al., Hidden Error
Awareness (arXiv 2605.09502); Shi et al., hypothesis testing the circuit hypothesis (arXiv 2410.13032); Méloux et
al. (arXiv 2510.00845, 2512.18792).

**Binding and number representation (framing for G5):** Feng and Steinhardt (ICLR 2024); Prakash et al. (ICLR
2024 per arXiv); Gur-Arieh, Geva and Geiger (ICLR 2026 per arXiv); Wu, Geiger and Millière (ICML 2025 per arXiv);
McDougall et al., copy suppression (arXiv 2310.04625); Ortu et al. (ACL 2024 per arXiv); Levy and Geva (NAACL
2025 per arXiv); Yuchi, Du and Eisner (EACL 2026); Nikankin et al. (ICLR 2025); Wu, Shen and Jiang, I3C (NAACL
2024).

**Statistics and evaluation:** Miller, "Adding error bars to evals" (arXiv 2411.00640); Bowyer, Aitchison and
Ivanova (ICML 2025, position paper on small-N intervals); Wang, "Measuring all the noises of LLM evals" (arXiv
2512.21326); Heineman et al., signal and noise (arXiv 2508.13144); Hochlehnert et al., "A sober look at progress in
LM reasoning" (arXiv 2504.07086); Matuschek et al. (J. Mem. Lang. 2017); Mancl and DeRouen (Biometrics 2001);
Lakens, Scheel and Isager (AMPPS 2018, TOST); Lan-DeMets group-sequential spending (gsDesign). Grading: UGPhysics
(arXiv 2502.00334), PHYSICS (Findings of ACL 2025), PhysReason (arXiv 2502.12054), Math-Verify, TinyV (arXiv
2505.14625), pint 0.26. Models and inference: Qwen3 technical report (arXiv 2505.09388) and model cards (sampling;
licences: Qwen3 and Qwen2.5 Apache-2.0, Llama 3.1 community licence); vLLM installation documentation and PyPI
(0.33.0); vLLM quantized KV-cache documentation.

**Tooling facts:** TransformerLens 3.4.0 (2026-06-09; the version in `docs/environment_lock.yml`) lists
Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct as fully verified on the TransformerBridge, Qwen3-8B as
core-verified, and Qwen3-14B and Qwen3-32B as skipped by its memory-limited harness (unverified, not known
broken); Qwen3-32B is not in the HookedTransformer list; `boot()` defaults to float32. Latest TransformerLens is
4.3.0 (2026-10-23); upgrading is a separate decision. circuit-tracer offers transcoders for Qwen3 0.6B-14B and
Llama-3.1-8B-Instruct, none for Qwen2.5 or Qwen3-32B.

---

## 15. Open decisions for the user

Defaults only withhold an action; none is irreversible.

| Id | Decision | Default until decided |
|---|---|---|
| D1 | Drop the full P0 regeneration of Phase-I values from the critical path (extended parity kept) | Not run; can be run later as a side track |
| D2 | Who performs independent physics review for G4 (v2 B4) | Nobody yet: G4 would be EXPLORATORY-REPLICATION |
| D3 | Download Qwen3-8B (optionally Qwen3-14B) with pinned revisions | Not downloaded; G2 on Qwen2.5-7B and Llama-3.1-8B |
| D4 | Install vLLM in a separate environment with a parity check | Not installed; 7-8B with Hugging Face only |
| D5 | Resubmit the 32-anchor no-cue resample (435606 design) | Not resubmitted. Its question (the Qwen3-32B cue effect on single-sample candidate anchors) is lower priority than calibration; whether those anchors are reliable is exactly what it would measure, so no ceiling is assumed |
| D6 | Run the Phase-I monitor under cluster-held-out folds as a side track | Not scheduled |

## 16. First sprint (all CPU unless marked; nothing submitted without acceptance)

1. G0.1 status sync; ledger rows for 435605 and 435606.
2. G0.2 the seven review additions, as scripts or notes, with tests where code is involved.
3. Qwen3-32B revision identification and manifest (CPU, read-only on scratch).
4. G1: role minimal pairs and the marking factorial in the generator (certificates, mutation tests,
   feasibility counts); regenerated near cues outside the loosest tolerance; foil generator with tests; sampled
   and batched reasoning-contract version with the LaTeX final-line parse (prospective only); frozen G2/G3
   analysis and power-simulation scripts tested on synthetic records; G3 thresholds and the equivalence margin;
   experiment cards.
5. G0.3 extended parity at the planned hook sites and trace lengths for Qwen2.5-7B and Llama-3.1-8B (one short
   GPU job, on acceptance).
6. G2 calibration on the two 7-8B models (one GPU job each, on acceptance).

## 17. Review of this document

An independent agent review (2026-11-11, read-only, against the repository) checked the factual statements and
the design. It confirmed the review-derived numbers, the Stage 14 counts and rates, the model and manifest
status and the power and equivalence arithmetic; it found ten factual errors in the first draft (among them:
HF-versus-TL parity had in fact passed in job 399217; the Stage 14 reasoning runner is greedy, so sampling is a
new contract; the cue disclaimer wording; a wrong KV-memory explanation; overstated Stage 14 readings) and twelve
design flaws (among them: no cell varied role alone; the in-system contrast was confounded with unit; E1 was
conditioned on a post-treatment variable; near cues fell inside the 1 % tolerance; a data-dependent equivalence
margin; undefined gate thresholds). This version corrects all of them; the corrections are visible in sections
1, 4, 5, 6, 7, 9, 10, 12 and 15.
