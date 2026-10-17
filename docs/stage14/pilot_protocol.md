# Pilot protocol (Research v2.0, Stage 14.7): prepared, not run

Status: **prepared by the agent; NOT authorized to run; blocked on the items in section 8.** No GPU job has been submitted
and no model has been scored on any v2 structure.

Plan reference: v2 B2.2-B2.5 (p.7-8), B6.1-B6.5 (p.12), P1.5-P1.7 (p.17), §8.1-§8.4 (p.41-42), §9 compute ladder level 2
(p.43), §10 (p.44), first sprint items 7 and 9 (p.50). Scoring rules: `docs/stage14/scoring_contract.md`. Journal:
`docs/journal/stage14/14.7_pilot_preparation.md`.

## 1. Purpose and what this pilot cannot do

A small balanced pilot to debug construction and estimate variance, not to prove a small effect (B6.1). With ten structures
the pilot is **precision-limited**: the independent unit is the structure (v2 §8.1), so ten structures cannot support a
powered claim about any interaction, and none is attempted. Its outputs are discovery-only: data role EXPLORATION, evidence
class `exploratory`, `paper_eligibility` false. It does not select the primary confirmatory endpoint (B2.2: that is chosen
only after reliability and incidence have been estimated, on a discovery partition, and frozen before any confirmatory data is
opened).

## 2. Design (frozen here, before any model score exists)

- **Items:** the ten structures in `data/v2/structures/v1/`, two numeric instantiations, the 211 feasible factor cells
  (`factor_cell_manifest.jsonl`). Infeasible cells are not run. Admission category: UNREVIEWED (see section 8).
- **Models:** Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct, the two primary dense models (B6.1, P4.5), loaded from
  `/scratch/pabitra/models` with their registry keys (`qwen_primary`, `llama_primary`) with pinned manifests; no third model.
- **Output grammar:** one wrapper, `answer_line` (identical to the Stage 6 instruction), so that the pilot is comparable to Phase
  I. The wrapper multiverse is card X03 and is a separate, later run.
- **Scoring:** the contract in `docs/stage14/scoring_contract.md` (BOS once; exact answer span; separate equals joint
  tokenization; the scored string is the instructed string). The legacy scripts are not used.
- **Candidate space for answer competition (R_alt, v2 §4):** fixed in advance from the cell: the gold answer string and one
  decoy-derived string, the cue numeral written with the target unit in the same wrapper. Defined only for the cells with a
  numeric cue that can be an answer (same-unit near, moderate, far; incompatible-unit near). For the other cells R_alt is
  NOT_EVALUATED, never 0.
- **Free generation:** deterministic greedy decoding, at most 40 new tokens, seed 42, parsed by the wrapper's parser. A
  generation that does not parse, or has several candidates, is recorded as such (`UNPARSEABLE`, `MULTIPLE_CANDIDATES`,
  `EMPTY`); it is never counted as wrong or correct.

## 3. Endpoints (co-endpoints; none promoted in this pilot)

| Endpoint | Definition | Cells |
|---|---|---|
| C_gen correctness transition | free-generation correctness (`correct`, `wrong`, or the parse status) relative to the no-cue anchor of the same instantiation | all |
| R_alt | log p(gold) minus log p(decoy) under the same prompt and wrapper | numeric-cue cells |
| D_lp | reference-free range of the gold log-probability across the cells of one instantiation, with SD, MAD and signed contrasts to the no-cue anchor | per instantiation |
| Presentation noise | repeat-pass and dtype variation of the same prompt (P1.7) | no-cue anchors |

The legacy base-0 `S_lp` label is not computed (journal J14.2-008).

## 4. Analysis plan (descriptive; precision-limited)

- Unit of analysis: the structure (n = 10); instantiations and cells are nested repeated measures. Report each effect per
  structure and as a structure-level summary with a cluster bootstrap over structures (2,000 resamples, seed 42); no p-values for
  interactions.
- Contrasts: each cue cell minus the no-cue anchor on R_alt where defined, on gold log-probability, and on C_gen; near minus
  far; same-unit minus incompatible-unit at the near numeral; relevant edit minus no-cue (the assay must respond to a relevant
  change); role reversal. All reported absolute and as signed contrasts, never as a ratio of a near-zero baseline.
- Eligibility strata with denominators (B2.4): all valid items; format-parseable; base-correct (no-cue anchor correct); model-positive.
  A result conditional on base correctness is labelled as such.
- Reliability first (P1.7): repeat-pass and dtype variation of the no-cue anchors; cue effects are read against this
  presentation-noise distribution.
- Missing data: a zero-row job, failed hook, timeout, parse failure, `BOUNDARY_MISMATCH` or `DUPLICATE_SPECIAL_TOKEN` record is
  NOT_EVALUATED with a reason code, reported by cell and by model; it is never replaced by zero (v2 §8.4).

## 4b. Correctness rule (declared 2026-10-17; post hoc relative to the 20-record throughput test)

A parsed generation is `correct` if its unit matches the gold unit, it equals the gold at the answer's own printed precision (|answer - gold| at most
half a unit in the last printed place), and it is within 0.5% of the gold; otherwise `wrong`. An unparseable, empty or multi-candidate generation keeps
that status and is never `wrong` by default. Why not a plain relative tolerance: 0.1% rejects a correctly rounded three-figure answer, and 0.5% accepts a
copy of the near-match cue (2.17 for a gold of 2.1778), which is the construct under study. Every record also stores `relative_error` and the strict 0.1%
label, so any other rule can be applied later and a sensitivity analysis needs no re-run. This rule was chosen after seeing the 20 throughput records (one record changes: "2.18" for 2.1778 becomes correct),
so it is post hoc relative to them; the full pilot is graded under it as written here, before its outcomes exist.

## 5. Decision rules (what each outcome would do; B2 Gate, §10)

| Observation | Interpretation | Action | Prohibited reaction |
|---|---|---|---|
| Assay does not respond to the relevant edit | the measurement does not track physics | stop; debug scoring and grammar | proceed to cue comparisons |
| Cue effects within presentation noise | no detectable effect at this precision | report as precision-limited; do not call it null | claim equivalence |
| Effects only on gold log-probability, not on C_gen or R_alt | likelihood-only phenomenon | restrict to a likelihood-interface account | claim physics reasoning failure |
| Near-match effect equals the incompatible-unit effect | numeral copying or lexical priming | test the copying account (P4) | claim relevance gating |
| Effect tied to one structure | structure-specific | report per structure | pool to a headline |

Nothing from this pilot may be described as a confirmation, and no cell may be added after seeing outcomes (v2 p.3).

## 6. Cost model (v2 §9, p.42)

N_structures x N_instances x N_cells x N_models x (N_score_forward + N_generated_resamples), per candidate. For the committed
manifest this is 10 structures x 2 instantiations x 11 cells = 220 cells, of which 211 are feasible, x 2 models = 422 jobs.
`scripts/v2/s147_pilot_plan.py` (a dry run: tokenizers only) computes the exact counts and token totals; the committed plan is
`results/stage14/s147_pilot_plan/attempt_20261016_d22a65d/`: 306 scoring forward passes and 211 generations per model, with 95
decoy-defined jobs per model, and 0 tokenization failures under either tokenizer. **GPU time is not estimated here**: no throughput has been measured on the current stack, and the
2026-10-14 smoke job spent most of its 4 h 42 min loading weights from the network filesystem. Step 1 of any approved run is a
short, measured throughput test.

## 7. Provenance and execution rules

Submit only from a clean, committed, pushed tree; record the full SHA; use a new attempt directory per run (the runner refuses a
non-empty one); unique `%j` logs; `PYTHONNOUSERSITE=1`; print SHA, `git status --short`, hostname, GPU and package versions at job
start; record the contract fingerprint and tokenizer file hashes; write raw per-record JSONL before any aggregation; keep
activations out (this pilot needs no hooks and stores none). Partition, GRES, CPU, memory and walltime come from a live preflight
(`sinfo`, `scontrol show node`, `sbatch --test-only`, per-user caps), not from this document. The template
`slurm/templates/stage14_pilot_scoring.sh` is unverified against the live cluster.

## 8. Blockers and what must be authorized

| # | Blocker | Why it matters | Owner |
|---|---|---|---|
| 1 | Independent expert review of the ten structures (all UNREVIEWED) | v2 B4 gate: no claim on items whose English is unreviewed | physicist and reviewers (Stage 14.5 materials) |
|   | Update 2026-10-17: the user approved all ten in one open walkthrough (`docs/validation/v2/structure_review_2026-10-17.json`). One reviewer, not blinded, expertise not stated; the certificates still say UNREVIEWED. Partly addressed, not cleared. | | |
| 2 | Ten structures, not 40 to 60 | B6.1 asks for roughly 40 to 60 independent discovery structures | user / further generator work after review |
| 3 | P0 gate open: values recomputed, not regenerated through the model; hook check needs activations | v2 P0 hard stop (p.16) | needs this pilot's models on GPU under an approved run |
| 4 | Post-wipe GPU validation of the two models is incomplete (4 of 7 smoke results predate the fix, no rerun) | the loader and hooks are unproven on the restored weights | needs a short approved GPU job |
|   | Update 2026-10-17 (later): job 399539 ran the real runner for 20 S01 jobs on Qwen2.5-7B through the direct HF path; all records OK. Throughput measured (see J14.7-018). Remaining: the correctness-tolerance rule is undeclared (code uses 1e-3), Llama untested on this path, P0 regeneration open. | | |
|   | Update 2026-10-17: job 399217 reran the smoke for the two pilot models; all checks pass (TransformerLens loader and hooks). The direct Hugging Face scoring path used by the runner is still untested on real weights. Partly addressed. | | |
| 5 | Explicit user authorization to submit Slurm jobs, with partition and resource limits chosen from a live preflight | AGENTS.md and the Sharanga skill | user |

Per v2 p.50 the pilot follows the Phase-B gates; running it on unreviewed items would be exploratory only and must say so.

## 9. Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Protocol author (agent) | Claude Sonnet 5.5 for atharvgaur1845 | 2026-10-16 | prepared |
| Approving investigator | | | PENDING |
