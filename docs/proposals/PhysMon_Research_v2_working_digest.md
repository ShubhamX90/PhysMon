# Working digest: PhysMon Research Redesign v2.0 (14 October 2026)

**Source of truth:** `docs/proposals/PhysMon_Research_v2.pdf` (53 pages, "Physics-Counterfactual
Mechanisms: Benchmark Red-Team, DECOY-v2 Reconstruction, and a Gated Mechanistic Research
Programme"). Searchable text extraction: `docs/proposals/PhysMon_Research_v2.extracted.txt`
(page markers `######## PAGE n ########`; page numbers below are PDF pages).

This digest is a navigation aid written by the agent after reading every page. It does not replace
the PDF. When the two disagree, the PDF wins; when a task touches a gate, re-read the PDF section.

Status of the guidance (user direction, 2026-10-15): this document is the guidance for Stage 14
onwards. It replaces the June Part II plan as the plan of record (PDF p.3, "Replace, rather than
lightly revise, the June 2026 Phase-II plan"). The Part II v1.1 + erratum governing rule in
`docs/proposals/PhysMon_Part_II_governing_document_rule.md` is kept unedited because Stage 13
gate code checks its text; read it as historical context.

## 1. What the document is, and is not

- A proposed, falsifiable protocol, **not** a record of experiments performed (p.1).
- Phase-I = the submitted 25-page ICLR 2027 paper *Confidence Without Cause* (submission 50608).
  Its numbers are SUBMITTED claims "requiring reproduction", not verified facts (p.3).
  The 29-page *Proved, Not Annotated* file must not be confused with it (p.3).
- Source tags: SUBMITTED, REVIEW, LITERATURE, PROPOSAL. Numeric targets other than SUBMITTED
  values are planning choices, not results (p.3).
- The doc could not see the repository: it cannot verify raw data, jobs, code, or history (p.3).

## 2. Rules that apply at all times (from the text)

1. Separate estimands: physical-answer invariance (certificate) is not equal conditional LM
   probability; cue effects on probabilities, representations, correctness and faithful
   computation are different things (p.3). `S` = observational sensitivity only; "mechanism"
   needs controlled, specific, predictive intervention evidence; "shortcut reliance" is reserved
   for evidence that computation improperly uses the cue (p.3).
2. Do not design analyses that only accept the preferred hypothesis; all five alternative
   theses are legitimate outcomes (p.3).
3. No new unvalidated experiments smuggled into a headline claim after seeing outcomes (p.3).
4. Never silently fill missing records; a zero-row job, failed hook, timeout, parse failure,
   ineligible family or untested control is NOT_EVALUATED, not a null (p.16, p.42).
5. Semantic revision of a governing equation, assumptions, target, accepted answer or cue role
   increments the family version; no silent in-place edits. Freeze source revisions and hashes.
   Once a confirmatory panel is opened, never use it to tune generation, architecture, scoring,
   parsers, thresholds, site selection or eligibility (p.5).
6. Do not describe new metrics as preregistered in June; preserve the threshold-registration
   history; no retroactive relabeling (p.7, p.44).
7. The independent unit is the independently authored symbolic structure / template cluster,
   not a rendering, paraphrase, numeric instantiation or decoder sample (p.41).
8. Five disjoint data roles: EXPLORATION, GENERATOR_TUNING, INTERNAL_CONFIRMATION,
   EPC_CONFIRMATION, ADVERSARIAL_CHALLENGE; group by graph lineage before splitting (p.12).
   Keep a shadow test set inaccessible to all tuning scripts and agents (p.20).
9. An agent's self-review is not independent expert validation (p.42). A symbolic free-symbol
   certificate must never be called a certificate of natural-language correctness (p.13).
10. Gates are about correctness, not dates. A credible early negative result must be allowed to
    change the project (p.17, p.48).
11. Stop-pivot hierarchy: credibility of the measured effect > benchmark size; causal
    interpretation > component count; out-of-cluster prediction > peak AUROC; selective
    correctness improvement > ratio recovery (p.45).
12. Primary family of confirmatory hypotheses is small: H-B behavioral factorial, H-M single-prompt
    incremental monitoring, H-C causal head/path, optional H-R selective repair. Holm or
    hierarchical testing within; BH-FDR for prespecified secondary scans (p.41).

## 3. Map of the document

| Section | Pages | Content |
|---|---|---|
| 1 Status, scope, rules of evidence | 3 | Purpose, epistemic constraint, thesis and alternatives, source tags |
| 2 Executive judgment; 2.1 Phase-I ledger | 3-5 | Tracks M/E/R; three decisions before expensive work; ledger; audit alerts A/B/C |
| 3 Phase B (B0-B7) | 5-14 | Board decision; benchmark architecture V1-R / V2-A / V2-B / EPC / MATH-X; red-team, construct, generator, validation, external sources, pilot/power, deliverables |
| 4 Framework | 14-16 | Endpoints C_gen ... I_select; hypotheses H0-F ... H3-S; claim hierarchy C1-C6 |
| 5 Critical path P0-P11 | 16-30 | Twelve gated blocks |
| 6 Inventory A-F | 30-40 | 104 contrasts (18 A, 14 B, 18 C, 16 D, 18 E, 20 F), each R/C/X |
| 7 Cards X01-X12 | 40-42 | Minimal specs with no-go responses |
| 8 Statistics | 42-43 | Unit, estimands, multiplicity, power, missing-result policy |
| 9 Compute and data contracts | 43-45 | Escalation ladder, storage, record schema, CI checks, preflight pseudocode |
| 10 Conditional decisions | 45-46 | Gate outcome -> action -> prohibited reaction |
| 11 Literature | 46-49 | L01-L25 and four conditional novelty claims N1-N4 |
| 12 First sprint | 49-50 | Eleven ordered actions |
| 13 Paper architectures | 50-51 | A mechanism, B measurement, C repair |
| 14 Bibliography | 51-52 | Links (not independently re-verified by the agent) |
| 15 Definition of completion | 53 | Ten questions that must be answerable |

## 4. Phase B (benchmark red-team) gates

| Gate | Passes when | If it fails |
|---|---|---|
| B1 (p.8) | Phase-I labels/denominators regenerate from raw records; metric/base/wrapper robustness table published | If only a teacher-forced string effect: keep it as such; if artifacts do not reproduce, stop all dependent causal claims |
| B2 (p.9) | H-P or H-N shows reliable behavior beyond generic text/answer-string effects | Only H-T: measurement project. Only H-U: formal equivariance study. Nothing: archive as documented negative result |
| B4 (p.11) | Independent expert semantic validation + version-correct solver checks + parser criterion pass | New validation cycle, not optimistic averaging |
| B5 (p.13) | External adaptations feasible, rejection rates preserved | Restrict question types or commission expert-authored tasks; never lower certification |
| B6 (p.13) | Validated causal contrast on held-out structural units, not dominated by format/tokenization or one cue subtype | Absent on two independent sources: stop broad claim. String-only drift: calibrated likelihood/interface mechanism, no physical-reliance claim |
| Phase-B go/no-go (p.14) | GO-MECHANISM / GO-MEASUREMENT / PIVOT-GENERAL NUMERIC / REDESIGN-BENCHMARK / STOP BROAD CLAIM | Outcomes do not license retroactive relabeling |

Benchmark decision (p.5): keep DECOY-v1 immutable (V1-R, 155 families, original signed labels);
build DECOY-v2 (V2-A relevance and numeric interference; V2-B invariance/equivariance, which is
where old Cue C moves); EPC external set (EPC-D development, EPC-C locked confirmation, EPC-N
expert-authored); MATH-X non-physics controls (GSM-DC, GSM-Symbolic). Do not substitute a public
benchmark wholesale and do not call v2 novel because it is larger than v1.

## 5. Critical-path gates P0-P11

| Block | Core question | Hard gate / key rule |
|---|---|---|
| P0 reproduction and provenance (p.16) | Which Phase-I numbers follow from exact data, weights, code? | Hard stop: labels and likelihoods must regenerate independently and hooks must demonstrably affect the claimed tensors; if a headline changes, publish an erratum and rerun upstream |
| P1 measurement validity (p.17) | Is the signal the model's, or the string/scoring interface's? | Anchor-free rescoring, no-cue/nonnumeric controls, wrapper multiverse, length/tokenization, restricted-choice R_alt, free generation, reliability. If it collapses: study string scoring as the finding |
| P2 scale DECOY-v2 (p.18) | Can mechanism ingredients be varied independently on new structures? | Only after Phase B approves; 300-600 structures is a ceiling, not a quota; deconfounding cells; role-reversal controls |
| P3 validation, parser, leakage (p.20) | Are language, parser and splits trustworthy? | No confirmatory hidden-state or causal claim until every confirmatory family passes independent validation and leakage audit |
| P4 behavioral discrimination (p.21) | Which behavioral contrast is real? | Preregistered proximity x unit x relevance interaction on held-out clusters; contrast chosen here sets the mechanistic metric |
| P5 monitoring (p.21) | Does hidden-state access help? | Tasks S (single prompt), F (four-input), V (variant-local), never pooled; comparator ladder; promote only with frozen single-input spec and supported incremental gain on held-out structural cohort |
| P6 re-localize (p.23) | Is L16 H11 causal for a physical computation? | Absolute metrics before normalized recovery; multiple ablation semantics; specificity and role reversal; off-target damage and self-repair |
| P7 function (p.24) | What does the component compute? | Test F-copy / F-match / F-unit / F-role / F-position / F-answer-prior with opposing predictions |
| P8 circuit (p.26) | Upstream/downstream path? | Attribution plus true patching, path patching, knockout-rescue, faithfulness, causal abstraction, synthetic planted-shortcut check |
| P9 generalization (p.27) | Does the function recur? | Freeze function, not head index; scaling ladder; post-training; novel laws; cue composition; cross-backend |
| P10 repair (p.28) | Does a mechanism-guided edit beat cheap baselines? | Nonmechanistic baseline ladder first; strength-vs-damage curves |
| P11 closure (p.30) | Can an independent reader reproduce and attack the claim? | External cohort opened once; venue chosen after the result |

## 6. Experiment cards (p.39-42)

X01 authoritative reproduction; X02 base-variant invariance challenge (no GPU first); X03
format/tokenization falsification (60-100 families, 4-6 wrappers, both dense models); X04
physics-semantic factorial; X05 structural leakage and real OOD monitoring; X06 frozen external
behavioral replication; X07 H11 lesion/patch specificity; X08 mechanistic function
discrimination; X09 source-to-sink circuit and rescue; X10 architecture functional replication;
X11 selective mitigation challenge; X12 external audit and claim freeze. Each card fixes primary
outcome, comparators, no-go response and artifact; the agent must not invent a different
estimand or panel mid-run (p.39).

## 7. Phase-I ledger versus what the repo supports (agent verification, 2026-10-15)

Verified directly from committed data: Qwen 70/140 and Llama 32/140 at 0.5 nat; Qwen mean `S_lp`
1.4006; the exact CM_B_UM_059 numbers quoted on p.8 (gold log-probs -45.531, -55.563 [doc: -55.562],
-45.000, -46.469; legacy S at base 0 = +10.031, at base 1 = -9.094; symmetric range 10.562) from
`results/stage6/behavioural_full_rerun/prompt_records.jsonl` (1,120 prompt records = 140 x 4 x 2
models, all 140 Qwen families have 4 variants). Wave 2 numbers (0.7596, 0.727, 0.7048, paired CIs
including zero), the 147 family pairs / 34 clusters / 2,352 rendering pairs, 182 science runs with
0.703 / 0.451 coverage, and the zero-row renamed-donor control match this repo's records.

Not verifiable here (no manuscript in repo): single-rendering monitor L16 0.7465; entropy Brier
0.2140 and ECE 0.0907; FNR@FPR=0.10 0.643 vs 0.714; frozen-expansion 0.820/0.667/0.6875; clipped
four-head recovery 0.969; "71% of family-held-out tests share a cluster with training". These
need the submitted PDF (task X01).

## 8. Environment facts that constrain the plan

- Activations, checkpoints and Slurm logs from earlier runs were wiped (2026-10 scratch wipe);
  committed per-prompt JSONL records and summaries survive. Anything needing hidden states
  (X05, P5, P6, P7) first needs regenerated activations.
- Per-user GPU caps (observed 2026-10-14): H100 one GPU, 12 CPU, 300G; A100 two GPUs; H200 two
  GPUs. The doc itself says to verify GPU allocation rather than assume it (p.42) and to avoid
  committing to a 397B-class model (p.42).
- TransformerLens models keep the Hugging Face copy on CPU after `load_model`, so HF-side
  generation and log-probabilities run on CPU (observed in the model smoke test). This matters for
  P1 free-generation and tokenizer/hook parity checks (p.17, p.43).
- Eight registry models are restored under `/scratch/pabitra/models` with pinned revisions and
  hashes (`docs/model_manifests/`).

## 9. Proposed Stage 14 ordering (agent proposal for user approval)

Follows the document's first sprint (p.48-50) and its compute ladder (p.42-43). Nothing below is
started without the user's go-ahead.

14.0 Governance ingest: decision-log entry; claim-to-artifact ledger skeleton; v2 evidence
     registry schema (p.16, p.43); experiment cards X01-X03 from `docs/experiment_cards/TEMPLATE.md`.
14.1 X01 reproduction from raw per-prompt records (CPU only). Needs the submitted manuscript.
14.2 X02 base-rotation attack with an executable unit test for the CM_B_UM_059 example (CPU only).
14.3 Scoring-interface contract: prompt bytes, answer spans, chat templates, wrapper multiverse
     design for X03 (small GPU later).
14.4 Structure overlap and the five excluded stable families: adjudicate the 34 clusters, rerun
     cluster-held-out baselines that need no activations (CPU).
14.5 Validator qualification materials (human task): two-pass rubric and planted-defect bank.
14.6 Typed generator and first 10 certified v2 structures (CPU + human review).
14.7 Pilot (GPU, two dense models) only after 14.2-14.4 gates and the user's approval.
