# Decision Log

All project decisions are recorded here with date, context, decision, rationale, and proposal
section references.

## Template

- Date:
- Decision:
- Rationale:
- Proposal section(s):
- Supplementary decision/assumption IDs:

## 2026-06-13 - Packaging Backend

- Date: 2026-06-13
- Decision: Use `setuptools.build_meta` instead of `setuptools.backends.legacy:build` in
  `pyproject.toml`.
- Rationale: Sharanga's Python 3.11 pip/setuptools stack could not import
  `setuptools.backends.legacy`, causing the required editable install (`-e .`) in
  `environment.yml` to fail. `setuptools.build_meta` preserves the intended editable
  package install while allowing the environment to build.
- Proposal section(s): Reproducibility and Release Plan (§17)
- Supplementary decision/assumption IDs: A2

## 2026-06-13 - Baukit Install Source

- Date: 2026-06-13
- Decision: Install Baukit from `git+https://github.com/davidbau/baukit.git` instead of
  `baukit>=0.1`.
- Rationale: No `baukit` distribution matching `baukit>=0.1` is available from PyPI in
  Sharanga's pip environment. The GitHub source preserves Baukit as the fallback hooking
  dependency required for Stage 2 if TransformerLens support is insufficient.
- Proposal section(s): Activation Extraction Tooling (§7.3), Stage 2 (§12)
- Supplementary decision/assumption IDs: A2

## 2026-06-13 - Local CPU Development Environment

- Date: 2026-06-13
- Decision: Build the local CPU-only development environment as a repo-local `uv` virtual
  environment in `.venv` instead of installing a new local Conda distribution.
- Rationale: This Mac did not have `conda`, `mamba`, or `micromamba` available. Using
  `uv` let us create a Python 3.11 CPU development environment quickly while preserving
  the canonical GPU environment specification in `environment.yml` for Sharanga.
- Proposal section(s): Environment Setup (§I.3)
- Supplementary decision/assumption IDs: A1, A2

## 2026-06-14 - [PI CONFIRMED 2026-06-14] D1 Model Lock

- Date: 2026-06-14
- Decision: Lock the Stage 3+ model assignments as:
  - `Qwen/Qwen2.5-7B-Instruct` at
    `/scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct`
    for `PRIMARY_DENSE A`
  - `meta-llama/Llama-3.1-8B-Instruct` at
    `/scratch/pabitra/rag-reason/models/Llama-3.1-8B-Instruct`
    for `PRIMARY_DENSE B`
  - `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` at
    `/scratch/pabitra/rag-reason/models/DeepSeek-R1-Distill-Qwen-32B`
    for `REASONING_TUNED`
  - `Qwen/Qwen2.5-32B-Instruct` at
    `/scratch/pabitra/rag-reason/models/Qwen2.5-32B-Instruct`
    for pilot-stage `LARGE_JUDGE`
  - `Qwen/Qwen3.5-397B-A17B-NVFP4` at
    `/scratch/pabitra/rag-reason/models/Qwen3.5-397B-A17B-NVFP4`
    as the full-study reserve `LARGE_JUDGE`
- Rationale: These assignments satisfy the required role coverage while preserving the
  already validated Qwen/Llama primary dense pair, a 32B reasoning-tuned replication
  model, and a tractable single-GPU judge for pilot stages.
- Proposal section(s): Model Selection (§6), Stage 2/3 transition (§11)
- Supplementary decision/assumption IDs: D1, A2, A8

## 2026-06-14 - [PI CONFIRMED 2026-06-14] D2 Sensitivity Threshold Policy

- Date: 2026-06-14
- Decision: Keep `hat{S}_theta(tau)` as the primary binary probe target,
  `S_theta(tau)` as the secondary continuous target, and `S_theta^lp` as a saved
  tertiary cross-check. Determine the binary threshold only after the Stage 4 pilot
  behavioural sweep, using training families alone and targeting roughly a 30-40%
  positive-class rate. Pre-register the chosen threshold in a dedicated Stage 5 commit.
- Rationale: This preserves the construct in `docs/construct_spec.md` while making the
  threshold policy concrete without leaking validation/test information into label design.
- Proposal section(s): Formal Measures (§3.3), Monitor Study (§9), Ordered Gates (§11)
- Supplementary decision/assumption IDs: D2

## 2026-06-14 - [PI CONFIRMED 2026-06-14] D3 Paraphrase Generation Timing

- Date: 2026-06-14
- Decision: Use `Qwen/Qwen2.5-32B-Instruct` for adversarial paraphrase generation and
  artefact-search prompting only, and defer all paraphrase-generation implementation to
  Stage 6. Do not use paraphrase generation in Stage 3 pilot construction.
- Rationale: The pilot benchmark should concentrate on solver-verifiable Cue A and Cue B
  families before introducing paraphrase variability that is harder to certify exactly.
- Proposal section(s): Artefact Controls (§10), Ordered Stages (§11)
- Supplementary decision/assumption IDs: D3

## 2026-06-14 - [PI CONFIRMED 2026-06-14] D5 Family Size

- Date: 2026-06-14
- Decision: Fix `m = 4` variants per family uniformly across Cue A, Cue B, and any
  future Cue C family.
- Rationale: `m = 4` yields 6 pairwise comparisons for answer-flip/JSD estimates while
  keeping the 30-family pilot at 120 prompts per model, which is compatible with the
  single-load batched behavioural-job design.
- Proposal section(s): Counterfactual Families (§3.2), Pilot Stage Design (§11)
- Supplementary decision/assumption IDs: D5

## Stage 1 Decision Gate

**Gate question:** Can shortcut sensitivity be defined and measured
objectively without reliance on prompt-condition labels alone?

**Evidence:**
- [x] `construct_spec.md` exists and covers all 7 required sections
- [x] `constructs.py` implements all formal definitions with docstrings
- [x] `sensitivity.py` computes all three measures from raw outputs
- [x] `parser.py` passes all 30+ unit tests
- [x] `test_constructs.py` passes
- [x] No function in `formal/` takes prompt condition as a required input
- [x] `SensitivityRecord.binary_sensitive` is gated behind pre-registration

**Gate result:** [x] PASS - reason: Stage 1 now defines shortcut sensitivity through
solver-certified family invariance plus Level-2 behavioural measurements
(`hat{S}_theta`, `S_theta`, `S_theta^lp`) rather than prompt-condition labels, and the
formal layer enforces that separation in code.

**Verification run:**
- `pytest tests/ -v` -> PASS on 2026-06-13
- `./.venv/bin/ruff check src scripts tests` -> PASS on 2026-06-13

**Decisions flagged to PI for confirmation:**
- [D2] Sensitivity threshold for binarisation: open; deferred to the Stage 5
  pre-registration block in `docs/construct_spec.md`
- [D5] Value of `m` (variants per family): open; Stage 1 keeps `m` explicit in the
  formal layer without prematurely fixing the benchmark-wide family size

## Stage 2 Decision Gate

**Gate question:** Is activation extraction and intervention hook support
stable on both primary models?

**Evidence:**
- [x] `qwen_primary`: hook_validation -> PASS, logprob_validation -> PASS
- [x] `llama_primary`: hook_validation -> PASS, logprob_validation -> PASS
- [x] compute estimate completed; scratch capacity confirmed adequate
- [x] `model_registry.yml` updated with confirmed paths and validated flags
- [x] Slurm templates tested on live Sharanga resources with caveat: A100 executed
  successfully end to end for Stage 2, while H100/H200 template submission paths were
  accepted by Slurm but same-session runtime remained constrained by `QOSMaxCpuPerUserLimit`
  as recorded under A1

**Gate result:** [x] PASS - reason: both required primary dense models completed the Stage 2
hook and log-prob validation suites on A100 with successful extraction, successful
zero-ablation perturbation, deterministic repeated extraction, finite reference-answer
log-probabilities, prompt-sensitive log-prob changes, and deterministic greedy generation.

**Artifact summary:**
- `results/stage2/hook_validation/qwen_primary_hook_validation.json`
- `results/stage2/hook_validation/llama_primary_hook_validation.json`
- `results/stage2/logprob_validation/qwen_primary_logprob_validation.json`
- `results/stage2/logprob_validation/llama_primary_logprob_validation.json`
- `results/stage2/compute_estimate.json`

**Primary-model lock ready for PI confirmation:**
- [D1] Proposed locked primary models:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `meta-llama/Llama-3.1-8B-Instruct`

Per Part IV.5, no work beyond Stage 2 should be treated as authorized until [D1] is
explicitly confirmed by the PI.

## 2026-06-14 - PI Self-Validation Complete

- Date: 2026-06-14
- Decision: PI self-validation of all 30 pilot families complete. 26 families pass
  Q1-Q4 without qualification. 4 families received required fixes (`CM_A_010` grammar,
  `EL_A_005` conductor cue values, `EL_B_003`/`EL_B_004`/`EL_B_005` notation). 2
  families received design notes (`CM_A_002`, `EL_A_003`). All fixes applied and
  verified before Stage 4 job submission.
- Proposal section(s): Validation Protocol (§7), Stage 3 (§11)
- Supplementary decision/assumption IDs: A4, A6

## Stage 3 Decision Gate

Gate question: Does the pilot benchmark satisfy invariance, agreement,
and surface-artefact requirements?

Evidence:
- [x] All 30 templates written and verified (`data/raw/templates/`)
- [x] All 30 families pass SymPy verifier (`results/stage3/verification/`)
- [x] Artefact Checks 1, 2, 4, 5 all PASS for all 30 families
- [x] Pilot validation form generated (`docs/validation/pilot_validation_form.md`)
- [x] PI self-validation completed: 26 clean pass, 4 fixed, 2 design notes
- [x] `run_behavioural.py` implemented and dry-run tested
- [x] Literature gap check (A3) VERIFIED - no near-fatal scoop found
- [x] DeepSeek validation PASS with caveats (logprob+determinism confirmed;
      `has_think_tags` caveat noted and accepted)
- [x] D1/D2/D3/D5 all recorded in `decision_log.md`
- [x] Compute estimate revised (targeted extraction added to `results/stage2/`)
- [ ] Second validator (D9): still pending - not blocking CONDITIONAL PASS

Gate result: [x] CONDITIONAL PASS
  Reason: All 30 templates verifier-certified + PI validation complete + parser 100%
  coverage. Second validator is pending per decision D9, which was never blocking Stage
  4 job submission per the Stage 3 brief.
