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
