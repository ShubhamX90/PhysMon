# Stage 15 progress against the v2 plan of record

Plan of record: `docs/proposals/PhysMon_Research_v2.tex` (revision of 11 November 2026). Status as of **2026-11-13 evening IST**, main at `30d5620` (updated after the judge qualification run).
Updated at each checkpoint; the journal (`docs/journal/stage15/`) holds the detail and the evidence for every row.

Status words: **DONE** (committed and tested), **DONE (provisional)** (done, but reviewed only by the agent, pending the LLM panel or the user), **RUNNING** (GPU work in flight), **PARTIAL**, **NOT STARTED**, **NOT DUE** (gated on an earlier gate).
Nothing below is a confirmatory result; every Stage 15 number so far is EXPLORATION data, exploratory.

## 1. Execution order of the plan (appendix "Next sprint", items 1-10)

| # | Plan item | Status | Evidence |
|---|---|---|---|
| 1 | G0 status sync (Stage 14 status, ledger rows 435605/435606, journal index) | DONE | `bca487a` (merged `815f6f8`); J15.0-001..012 |
| 2 | G0 review additions (a)-(g) | DONE, with two NOT_EVALUATED parts | `bca487a`; see section 2 |
| 3 | Qwen3-32B revision identification and manifest | DONE | `docs/model_manifests/qwen3_thinking.json` (27/27 files match revision `9216db57`, identified after the fact) |
| 4 | G1 construct (strata, generator, mutation tests, contracts, analysis scripts, SESOI, cards) | PARTIAL | section 3 |
| 5 | LLM review panel (choose judges, freeze prompts, extend bank, qualify) | PARTIAL: prompt v1 frozen, bank extended (v3), first qualification run NOT QUALIFIED | section 3, rows G1-14..17; J15.1-013/015 |
| 6 | M0 pilot structures (8-12) with role-by-value cells | DONE (provisional) | 12 structures, `e0f35aa`, `15a2749`; J15.1-007 |
| 7 | Non-physics dependency control set | NOT STARTED | |
| 8 | G0 extended parity at the planned hook sites (one GPU job) | NOT STARTED | needs a GPU job; on the critical path of the G2 primary-model rule (not only G5) |
| 9 | G2 design-validation pilot on M0 (one GPU job) | DONE (GPU), sealed | both pilots complete (job 444871); `collect` refuses until the G1 freeze (J15.1-009) |
| 10 | M250 build | NOT STARTED | follows the design-validation pilot |
| 11 | G2 calibration on the 7-8B models | 3 of 4 DONE (v1 no-cue part); Qwen3-8B thinking RUNNING | J15.1-014 |

Order note: the plan runs nothing before G1. Two GPU items run early on idle queue time under the user's instruction of 2026-11-13 ("speed without compromising anything"): the design-validation pilot is sealed until the G1 freeze, and the v1 no-cue calibration has reading rules fixed before any record (J15.1-006) and disjoint selection and estimation samples (J15.1-009).

## 2. Gate G0: integrity closure

| Item | Status | Evidence / result |
|---|---|---|
| 1. Status sync | DONE | J15.0; Stage 14 status file, journal index |
| 2a. Cross-instruction label stability | DONE (part NOT_EVALUATED) | Qwen Spearman 0.043, 17/30 labels agree (16.2 by chance); Llama 0.447, 27/30 (25.4 by chance). Same-instruction control on the pilot families and Qwen first-Stage-4 recomputation NOT_EVALUATED |
| 2b. Formula-hint cell | DONE for Qwen; Llama NOT_EVALUATED | correct hint lowers gold log-prob 3.69-5.53 nats on 5/5 families (descriptive); Llama file was a copy of a Qwen run |
| 2c. Interaction rule for every intervention | DONE | `src/physmon/causal/interaction.py` (refuses raw gold scores; zero pairs NOT_EVALUATED) |
| 2d. Oracle/deployable comparator tags | DONE | `docs/registry/v2/comparator_tags.yml`: 0.7048 Wave-2 and 0.727 fitted entropy are oracle; oracle-free entropy 0.520 |
| 2e. Claim-wording check | DONE | `scripts/check_claim_wording.py`: 4 prohibited phrasings in the withdrawn paper |
| 2f. Provenance-consistency check | DONE | `scripts/check_provenance_consistency.py`: 1 conflict ("could not write physics" vs `created_by: agent`) |
| 2g. Dated threshold note | DONE | `docs/registry/v2/threshold_history.md` |
| 3. P0 narrowed + extended HF/TL parity at G5 hook sites | Smoke parity done earlier (job 399217); extended parity NOT STARTED | GPU job needed; blocks G5 only |
| 4. Phase-I closure note | DONE | `docs/reviews/iclr2027_submission50608/phase1_closure_note.md` |
| 5. Qwen3-32B revision and manifest | DONE | registry updated `2282099` |
| **Gate G0** | **NOT PASSED** (item 3 outstanding) | "behaviour can proceed" without it; mechanism work cannot |

## 3. Gate G1: physics construct (freeze before any G2 output)

| # | G1 element | Status | Evidence |
|---|---|---|---|
| G1-1 | Strata taxonomy R/D/C/K with certificates | DONE | `src/physmon/benchmark/v2/rolevalue.py` (graph and independent-solver routes; C: zero derivative, invariance, dimension; K: regime predicate, counter value, dimension) |
| G1-2 | Role-by-value generator: >=3 values (+2 held out), >=2 phrasings per role, >=1 marker-free, misuse functions f_h(z), placebo, confounded pairs, feasibility records | DONE | `rolevalue.py`; `s177_build_m0_pilot.py` records excluded structures |
| G1-3 | Mutation tests of the generator | DONE | `tests/v2/test_rolevalue_mutations.py` (17 mutations x 12 structures; four certificate holes found and closed), J15.1-011 |
| G1-4 | Proximity conditions regenerated (exact / near-within-tolerance / tolerance-separated distinct) | NOT STARTED | |
| G1-5 | Outcome definitions O1-O3, grading views, O3 status categories | DONE | `reasoning_contract_v2.py`, `grading_views.py` (declared, convertible, 1%); O2 LaTeX recovery tested on real Stage 14.20 endings |
| G1-6 | Sampled, batched reasoning contract (prospective only) | DONE | `reasoning-v2`; `generation.py` (HF and vLLM); never pooled with greedy Stage 14 |
| G1-7 | Analysis scripts tested on synthetic records | DONE for the role-by-value family and batch-1 calibration/parity | `src/physmon/analysis/rolevalue_stats.py` (F1-F3, TOST four-way, Holm, rare rates, misuse support, lambda), `s176` |
| G1-8 | Power-simulation scripts | DONE for F1-F3; misuse-share simulator not yet | null-calibrated (F1 balanced 0.032-0.043, F2 0.022-0.054, F3 0.045-0.050); F3 power at SESOI 0.51/0.76/0.97 at J = 24/40/80; re-run from G2 variance estimates later |
| G1-9 | G3 scorecard criteria with numeric thresholds (H0-H6) | DRAFT for user review | `docs/registry/v2/g1/g3_scorecard_thresholds.md` |
| G1-10 | Minimum R-tracking criterion (checked in G2) | DRAFT (proposed >= 0.50 on >= 16 structures) | `docs/registry/v2/g1/r_tracking_criterion.md` |
| G1-11 | T1 prefix type per experiment and compatibility strata | DRAFT | in the experiment cards |
| G1-12 | Equivalence margins (SESOI) with reasons | DRAFT | planning values of the plan coded with reasons (F1 0.10, F2 0.10, F3 OR 1.5/step, lambda_D 0.10); user review pending |
| G1-13 | Experiment cards | DRAFT for user review (X01-X12) | `docs/registry/v2/g1/experiment_cards.md`; 33 open questions in `open_questions_for_user.md` |
| G1-14 | LLM panel: judges chosen (D2) | DONE | Claude sole provisional judge until GPT/Gemini credits |
| G1-15 | LLM panel: prompts frozen | DONE (v1) | `docs/validation/v2/llm_panel/judge_prompt_v1.md`, pre-freeze independent review |
| G1-16 | LLM panel: planted-defect bank extended (fresh valid items, new defects, held-out portion) | DONE (bank v3: 63 items, 10 held out) | `docs/validation/v2/llm_panel/bank_v3/` |
| G1-17 | LLM panel: qualification (>=85% defects for the declared reason, >=5/6 valid accepted) | RUN q1: NOT QUALIFIED | Q1 30/39, Q2 6/6, Q3 14/14, Q4 missed under-specification types; audit clean (J15.1-015); requalification needs a fresh planted set |
| G1-18 | M0 pilot structures | DONE (provisional) | 12 certified specs; review by the lead agent only |
| G1-19 | Dataset admission standard and data-role allocation | NOT STARTED (plan text exists) | |
| G1-20 | Adaptive-sampling rule and G3 secondary-family selection rule | DRAFT | `docs/registry/v2/g1/sampling_and_selection_rules.md` (no adaptive sampling proposed) |
| **Gate G1** | **NOT PASSED** | certificates, mutation tests and analysis tests done; panel not yet qualified; cards drafted, awaiting the user |

Design rule frozen inside G1-7/8 (J15.1-011): the non-numeric control is sampled as often as all D cells of a structure together; the sign-flip test is primary.

## 4. Gate G2: measurement and calibration

| Item | Status | Evidence |
|---|---|---|
| Backend parity before vLLM records count (plan section on compute, D4) | DONE: PASS | Qwen2.5-7B greedy, 80 problems: agreement 0.90, accuracy 0.65 vs 0.65 (J15.1-012) |
| 1. Design-validation pilot (8-12 structures) | GPU DONE, sealed | both models complete; read only after the G1 freeze |
| 2. Calibration: k_sel no-cue for selection, k_est fresh for baseline and self-flip floor | 3 of 4 DONE | in band: Qwen2.5 21/80, Llama 17/80, Qwen3 no-think 32/80; Llama 22% non-complete (J15.1-014) |
| 2'. Calibration of the primary estimands' variance (R/D at three values, N) on selected items | NOT STARTED | needs M250 role cells |
| 3. R-tracking check | NOT DUE | criterion not yet fixed (G1-10) |
| 4. Primary-model rule | NOT DUE | frozen at the end of G2 |
| **Gate G2** | NOT DUE | |

## 5. Gates G3-G7

| Gate | Status |
|---|---|
| G3 behavioural discovery | NOT DUE |
| G4 independent confirmation (needs GPT and Gemini judges) | NOT DUE |
| G5 mechanism (needs G4 and extended parity) | NOT DUE |
| G6 external and functional confirmation | NOT DUE |
| G7 practical use (optional) | NOT DUE |

## 6. Dataset plan

| Stage | Target | Status |
|---|---|---|
| M0 | 8-12 pilot structures, EXPLORATION | 12 built (DONE, provisional) |
| Non-physics control set | small, GSM-DC style | NOT STARTED |
| M250 | 130 EXPLORATION (80 v1 upgraded + 50 new) + 120 sealed INTERNAL_CONFIRMATION | NOT STARTED (12 of the 80 v1 structures already have role specs through M0) |
| M500 | expansion after G3, before G4 | NOT DUE |

## 7. Open decisions D1-D6

| Id | Decision | Status |
|---|---|---|
| D1 | Full P0 regeneration off the critical path | default kept (not run) |
| D2 | Judge panel | decided 2026-11-12: Claude + GPT + Gemini; Claude alone, provisional, until credits |
| D3 | Qwen3-8B download | done: revision `b968826d` pinned and verified |
| D4 | vLLM in a separate environment with parity | done: vLLM 0.33.0 env on scratch; parity PASS on Qwen2.5-7B |
| D5 | 32-anchor no-cue resample | default kept (not resubmitted; superseded in part by the k = 8 calibration) |
| D6 | Phase-I monitor under cluster-held-out folds | default kept (not scheduled) |

## 8. Infrastructure and incidents (Stage 15)

| Item | Status | Evidence |
|---|---|---|
| Sampled runner, work queue, generic GPU workers, snapshots, register | DONE | J15.1-001/002 |
| vLLM engine start failure on five workers (CUDA in parent before fork) | FIXED and verified on GPU | J15.1-008/010; canary gate now blocks any vLLM run until its configuration has passed on a GPU |
| Foreign-job cancellation scope | narrowed to targeted GPU partitions; four CPU jobs restored | J15.1-005 |
| Home quota overflow during install | resolved; environments on scratch | J15.1-003 |
