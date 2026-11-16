# G1 freeze record (physics construct) · 2026-11-16

Authority: plan of record v2.2 (`docs/proposals/PhysMon_Research_v2.tex`, section 5.1 "G1. Physics construct" and "Gate G1"),
the user's delegation of every G1 decision (2026-11-13, 2026-11-14) and the instruction of 2026-11-16 ("make best decisions of
your own keeping good project and also speed of progress in mind"). Written by the main session (Claude Opus 5.5) before any G2
output on the frozen dataset exists. Journal entry J15.1-040.

## What is frozen

Every file listed in `g1_frozen_files_sha256.json` (50 files), hashed at commit `20f9752` (the worktree was clean for all of
them). A later change to any of them is a dated amendment with a new version, never an edit in place; analysis code changed after
a G2 or G3 record exists is labelled as such in every result that uses it.

| Plan G1 element | Frozen as | Evidence |
|---|---|---|
| Strata taxonomy R/D/C/K, certificates | `rolevalue.py`, `rolevalue_v2.py`, `certify.py`, `graph.py`, `dimensions.py` | J15.1-011 (mutation tests), J15.1-032, J15.1-036 |
| Role-by-value generator: >= 2 validated phrasings per role relation, misuse functions, feasibility records | `rolevalue_v2.py` (v2.1 rules: two phrasing pairs, d0 co-present in the scene, d1 other event without lasting state, no undone events) | plan revision v2.2 sections A, G |
| Proximity conditions as distinct conditions | `supporting_v2.py` (exact, near-within-tolerance and tolerance-separated cells with `tolerance_status` per grading view; exact-match cells `source_ambiguous`) | J15.1-032 |
| Outcome definitions, grading views, O3 status | `reasoning_contract_v2.py` (reasoning-v2), `grading_views.py`, `unit_convertible.py` (count and money units) | grading dry run 0 unexpected failures on m0_v2, m0_v21, nonphysics_v1 (J15.1-036) |
| Sampled, batched reasoning contract | reasoning-v2, `generation.py` (HF, vLLM); never pooled with greedy Stage 14 records | vLLM-vs-HF parity PASS for Qwen2.5-7B, Llama-3.1-8B, Qwen3-8B thinking off (J15.1-030) |
| Analysis and power scripts tested on synthetic records | `rolevalue_stats.py` (F1-F3, TOST four-way, Holm, method agreement, min J = 6, rule B), `s189` power simulation | J15.1-026; `results/stage15/g1_power/attempt_20261114/` |
| G3 scorecard with numeric thresholds | `g3_scorecard_thresholds.md` as amended by `decisions_2026-11-13.md`; `scorecard.py` | J15.1-026 |
| Minimum R-tracking criterion (checked in G2) | T_R >= 0.40 (point estimate) on >= 16 evaluable structures (decision 8) | `r_tracking_criterion.md`, decisions file |
| Samples per cell k and agreement rule | k = 24 per R, D, C and K cell; N and no-cue balanced; phrasing-agreement rule B | plan revision v2.2 section E |
| D kinds, paired phrasings, consequence lexicon, C familiarity, value hygiene, gold traces | `rolevalue_v2.py` (lexicons and `PRIOR_MARKERS` inside), `traces_v2.py`, admission standard 3.1-3.6, 6.2 | |
| T1 prefix type and compatibility strata | decision 27 (type ii primary, gold trace as sensitivity), decision 28 (tertiles on the G5 discovery split) | decisions file |
| Equivalence margins with reasons | F1 0.10, F2 0.10, F3 odds ratio 1.5 per value-index step, lambda_D 0.10, H5 log 1.2 and 0.05; mechanism SESOIs deferred to their gates (decision 14) | decisions 1-3, 7, 10, 14 |
| Experiment cards | `experiment_cards.md` as amended by the decisions file | |
| LLM review panel | Claude Opus 5.5 and GPT-6.1 Sol QUALIFIED, judge prompt v3, protocol v3, bank v5; naturalness prompt v2 | J15.1-029 |
| H4 trace extractor | `trace_extractor.py`, version h4-v1 (fingerprint pinned by its test) | J15.1-031 |
| M0 pilot structures | `data/v2/dataset/m0_v22/` (11 structures, 411 cells), all ADMITTED by the qualified Claude judge with no sentence rated artificial | J15.1-038, J15.1-039 |
| Dataset admission standard and data-role allocation | `dataset_admission_standard.md`; milestones and roles of plan section 5.2 (M250: 130 EXPLORATION, 120 sealed INTERNAL_CONFIRMATION) | |
| Non-physics control set | `data/v2/dataset/nonphysics_v1/` (16 structures, 240 cells); admission review before its first use in G3 | J15.1-035 |

## Gate G1 conditions (plan: "passes when certificates, mutation tests and analysis tests pass, the LLM panel is qualified and the cards are committed")

* Certificates and mutation tests, analysis tests: the full committed test suite at the freeze commit (result in J15.1-040).
* LLM panel qualified: yes (two judges; Gemini unavailable, recorded).
* Cards committed: yes.

## Known limits carried into G2 (not hidden by the freeze)

* M0 v2.2 is admitted on one qualified judge (Claude). The admission standard allows this for M0 only; the GPT review is done
  when the user logs in to Codex again, and its verdicts are reported beside, never used to drop a structure after a model output.
* Two medium flags on admitted structures (S26 R1, S55 R1: tense leaves a minority reading); their cells are analysed as is and
  flagged in the G2 report.
* Extended HF-vs-TransformerLens parity failed for Llama-3.1-8B in `resid_pre` from layer 8 (job 449313). It gates mechanism work
  (G5 onward) on that model, not G2 behaviour runs (plan: "If extended parity fails for a model or backend: no mechanism work on
  it; behaviour can proceed").
* The sealed October-wording M0 pilot (`data/v2/runs/s15_m0pilot_*`) may now be collected, as a pipeline and grading check only;
  its wording is superseded and its numbers are never pooled with M0 v2.2 records.
