# PhysMon Stage 2 Handoff

Date: 2026-06-14  
Base repository commit before handoff-document additions: `db4265c76ec0a8c7f43de617bf424fad18e8ce35`  
Scope: Parts I-V complete; handoff stops before Stage 3 per the execution-order gate.

## 1. Stage 1 Gate: PASS

Source gate record: [docs/decisions/decision_log.md](/Users/shubhammishra/Desktop/PhysMons/docs/decisions/decision_log.md)

### Stage 1 Gate Section

```markdown
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
```

### `docs/construct_spec.md` Full Content

Source file: [docs/construct_spec.md](/Users/shubhammishra/Desktop/PhysMons/docs/construct_spec.md)

```markdown
# Construct Specification

Date: 2026-06-13

This document operationalizes the PhysMon Stage 1 construct per `physmon_proposal.pdf`
§3, §5.2, §9, and Stage 1 of the ordered execution plan in §11. It is the authoritative
scientific specification for how shortcut sensitivity is defined, measured, and bounded in
this repository.

## 1. Three-Level Analysis Framework

### Level 1 - Prompt condition

Level 1 concerns whether a cue condition `z_i` is present in a rendered prompt
`x_tau(r, z_i, a)`. Cue presence is determined from the benchmark template and the
rendering metadata, not from the model's output. For Cue A, this means a physically
irrelevant variable has been inserted; for Cue B, a unit-compatible but non-governing
distractor has been inserted; for Cue C, an equivalent representation has been applied.

Level 1 is not shortcut reliance. The existence of a cue in the prompt only says that the
opportunity for a shortcut-like response has been made available by construction.

### Level 2 - Observed model behaviour

Level 2 concerns observable output instability across a solver-verified invariant family
`F_tau = {x_tau(r, z_i, a)}_{i=1}^m`. The project measures instability with three
behavioural statistics:

- `S_theta(tau)`: average pairwise Jensen-Shannon divergence across output
  distributions over canonical answers.
- `hat{S}_theta(tau)`: average pairwise answer-flip rate after deterministic parsing.
- `S_theta^lp(tau)`: maximum drop in the reference-answer log-probability relative to a
  designated base prompt.

Level 2 is sensitivity-as-measured, not shortcut-as-proved. A high sensitivity score is
evidence that the model's behaviour changes under solver-preserving cue edits; it is not
by itself proof that the model relied on the cue as a reasoning shortcut.

### Level 3 - Internal representation

Level 3 concerns prompt-side hidden states extracted before generation. The probe target is
not the reasoning path, not a chain-of-thought trace, and not a claim that a mechanism has
been identified. It is a predictive monitor input: a representation `h` taken from a
prompt-side activation site and used by a probe `f_phi(h)` to predict a Level-2
sensitivity outcome.

Throughout this project, these levels are never conflated. Claim scope is
Level 3 -> predicts Level 2 -> correlated with Level 1, not Level 2 -> proves Level 1.

## 2. Formal Definitions

### Template

A canonical template is

`tau = (r, z, a, g, y*)`

where:

- `r` is the governing physical relation or law to be applied.
- `z` is the cue slot whose rendered value varies across family members.
- `a` is the set of auxiliary assumptions held fixed across the family.
- `g` is the symbolic governing equation used by the verifier.
- `y*` is the correct-answer template induced by `r`, `a`, and `g`.

Programmatically, this is represented by `physmon.formal.constructs.PhysicsTemplate`.
A valid template must specify a supported domain, one supported cue type, a SymPy-ready
governing equation string, and a family size `m >= 2`.

### Counterfactual family

Given a template `tau`, the rendered family is

`F_tau = {x_tau(r, z_i, a)}_{i=1}^m`

where each member differs only in the cue rendering and all non-cue content is fixed up to
approved representation changes. A valid family is one whose members share the same
solver-certified answer `y*_tau`.

The project keeps `m` explicit rather than hard-coding it in Stage 1. The final benchmark
value of `m` remains an unresolved study-design choice and is flagged as [Decision D5].

### Solver-verified invariance condition

The invariance requirement is

`y*_tau(r, z_i, a) = y*_tau(r, z_j, a)` for all `i != j`.

"Solver-verified" means that the project does not rely on prompt labels or human intuition
alone. Instead, a symbolic or exact executable verifier confirms that the governing
equation and the derived target quantity are invariant under the allowed cue edits.

Valid verifiers by cue family:

- Cue A: symbolic dependence analysis on the target expression to show that the inserted
  variable does not appear in the governing solution.
- Cue B: symbolic or executable confirmation that the distractor value is excluded from the
  governing law used to derive the target quantity.
- Cue C: exact equivalence check of the representation transform; if exact certification is
  unavailable, the family is excluded from v1.

### Distribution-level sensitivity

For a model `theta` and family `tau`,

`S_theta(tau) = (2 / (m(m-1))) * sum_{i<j} JSD(p_theta(. | x_i), p_theta(. | x_j))`

where `p_theta(. | x_i)` is the normalized discrete distribution over canonical answers
induced by the model's output distribution for variant `x_i`. In code, the current Stage 1
formalization expects an `answer_distribution` mapping from canonical answer strings to
probabilities or unnormalized weights.

### Answer-flip sensitivity

`hat{S}_theta(tau) = (1 / binom(m, 2)) * sum_{i<j} 1[hat{y}_theta(x_i) != hat{y}_theta(x_j)]`

where `hat{y}_theta(x_i)` is the deterministic canonical answer produced by the answer
parser. An answer flip occurs when two parseable variants in the same invariant family map
to different canonical answer strings. The answer parser is therefore part of the
measurement definition rather than a downstream convenience.

### Log-probability drop

`S_theta^lp(tau) = max_j [log p_theta(y* | x_base) - log p_theta(y* | x_j)]`

where `x_base` is the designated baseline variant in the family metadata. If no explicit
base marker is provided, the first variant index in the ordered family is treated as the
default baseline.

### Internal monitor target

The probe input is a prompt-side hidden state `h` and the probe output is a prediction of a
Level-2 sensitivity quantity or binarized sensitivity label. "Prompt-side" means token
positions that belong to the prompt prefix only, not generated tokens. Stage 1 reserves the
following extraction sites for Stage 2 validation:

- cue-token residual stream
- last-prompt-token residual stream
- attention output at cue tokens
- MLP output at cue tokens

The scientifically intended layer range is all model layers once Stage 2 instrumentation is
validated, with the Stage 1 formal module encoding the site labels but not yet constraining
the final layer subset.

## 3. Cue Types - Invariance Contracts

### Cue A - Physically Irrelevant Variable

Definition: A variable is added to the problem statement whose value does not appear in the
governing equation for the target quantity.

Invariance contract: `y*` must be derivable from `(r, a, g)` without any reference to `z`.
The verifier checks that the symbolic target expression does not depend on the cue variable.

Worked example: A constant-acceleration kinematics problem asks for final velocity after a
given time, while the statement additionally says the cart is painted red, blue, or green.
The target expression `v = v0 + a t` is independent of the color variable.

Known failure modes:

- the inserted variable appears in an intermediate expression that only later cancels
- the cue changes cognitive load or salience while remaining physically irrelevant

Required checks:

- Symbolic verifier: target expression has zero dependence on the cue variable.
- Human validation: the cue is plainly irrelevant to the governing law as written.
- Automatic artefact checks: variant text differs only at the allowed cue span and answer
  formatting remains stable.

### Cue B - Unit-Compatible Non-Governing Distractor

Definition: A quantity with units compatible with the target quantity is stated, but the
relevant governing law does not use it.

Invariance contract: the correct answer computed from the governing law is unchanged when
the distractor value is varied. The verifier checks that the distractor symbol does not
enter the governing equation used to derive the target quantity.

Worked example: A resistor-network question asks for current from Ohm's law while also
stating an irrelevant voltage drop elsewhere in the circuit whose units match the target's
dimensional family but does not govern the asked quantity under the stated assumptions.

Known failure modes:

- the prompt is ambiguous about which quantity is governing
- the distractor is actually part of an alternative valid derivation

Required checks:

- Symbolic verifier: target derivation excludes the distractor symbol.
- Human validation: the physics law required by the prompt is unambiguous.
- Automatic artefact checks: unit strings stay consistent and the distractor slot is the
  only semantic edit.

### Cue C - Representation / Frame Rendering

Definition: Equivalent renderings of the same physical setup, such as notation shifts,
coordinate-frame changes, or equivalent verbal formulations.

Invariance contract: the transform must be exactly verifiable. If exact certification is
not possible, the family is excluded from v1.

Known failure modes:

- paraphrase changes scope or introduces a hidden assumption
- a coordinate transform changes the difficulty of a sub-step in a way that is not exactly
  certifiable

Required checks:

- Symbolic verifier: exact equality of the transformed target expression.
- Human validation: the rendering preserves problem meaning exactly.
- Automatic artefact checks: the transformation is one from an approved exact catalogue,
  not a free-form paraphrase.

## 4. Shortcut Sensitivity - Binarisation Protocol

The primary planned probe target is `hat{S}_theta(tau)` because it is the most interpretable
family-level statistic and most directly expresses output instability. `S_theta(tau)`
remains the preferred continuous auxiliary target.

The binarization threshold is intentionally not fixed in Stage 1. It must be pre-registered
before any hidden-state analysis begins. This unresolved threshold choice is flagged as
[Decision D2].

Threshold policy to be decided with the PI:

- whether the threshold is universal across models and cue families
- whether it is estimated only from training families
- whether calibration is based on answer-flip rate alone or on a paired continuous summary

Until [Decision D2] is resolved and the PRE-REGISTRATION block below is filled and
committed, `SensitivityRecord.binary_sensitive` must remain unset.

## 5. Exclusion Criteria for Benchmark Families

A family is excluded from the benchmark if any of the following hold:

- the symbolic verifier cannot certify invariance for any variant
- human validators disagree on cue irrelevance strongly enough to break the pre-set
  agreement threshold
- the family is solvable by unit analysis alone rather than the intended governing law
- the answer distribution is degenerate in a way that prevents informative sensitivity
  measurement
- the problem requires numerical integration without an exact symbolic or executable
  verifier
- the family is near-duplicate relative to an existing family

Near-duplicate screening remains part of [Decision D5]. The intended comparison unit is the
family template rather than a single rendered item, and similarity should combine law,
problem structure, and cue schema rather than raw text alone.

## 6. Allowable Causal Claim Boundaries

Allowed claim:

"Localized prompt-side representations in [layer range] contribute causally to cue
sensitivity as measured by `hat{S}_theta(tau)`, as evidenced by necessity and sufficiency
tests exceeding all random-direction and random-site controls."

Disallowed claims:

- "We found the shortcut-reliance circuit."
- "We proved the model uses the cue."
- "We identified the reasoning path."

H4 is supported only if the causal intervention suite in the proposal shows a localized and
control-robust effect under prompt-side interventions. If intervention evidence is weak,
diffuse, or not stronger than controls, the claim falls back to monitorability only:
internal states predict behavioural sensitivity without a stronger causal localization
claim.

Repository language policy:

- Use: "predicts sensitivity", "tracks sensitivity", "monitor signal", "prompt-side
  contribution", "localized intervention effect".
- Avoid: mechanistic-overclaim wording that asserts a shortcut circuit was found, that a
  shortcut mechanism was conclusively isolated, or that shortcut use was proven.

## 7. Sensitivity Threshold Pre-Registration Record

## PRE-REGISTRATION

Sensitivity measure:     [TO BE FILLED before Stage 5 begins]
Binarisation threshold:  [TO BE FILLED before Stage 5 begins]
Rationale:               [TO BE FILLED before Stage 5 begins]
Date pre-registered:     [TO BE FILLED]
```

## 2. Stage 2 Gate: PASS

Source gate record: [docs/decisions/decision_log.md](/Users/shubhammishra/Desktop/PhysMons/docs/decisions/decision_log.md)

### Stage 2 Gate Section

```markdown
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
```

## 3. Model Registry (Full YAML)

Source file: [docs/model_registry.yml](/Users/shubhammishra/Desktop/PhysMons/docs/model_registry.yml)

```yaml
models:
  qwen_primary:
    name: "Qwen/Qwen2.5-7B-Instruct"
    path: "/scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct"
    role: "PRIMARY_DENSE"
    family: "qwen"
    hook_backend: "transformer_lens"
    hook_validated: true
    logprob_validated: true
    hidden_dim: 3584
    num_layers: 28
    notes: "Validated on 2026-06-13 in Stage 2: hook job 242355 and logprob job 242356."

  llama_primary:
    name: "meta-llama/Llama-3.1-8B-Instruct"
    path: "/scratch/pabitra/rag-reason/models/Llama-3.1-8B-Instruct"
    role: "PRIMARY_DENSE"
    family: "llama"
    hook_backend: "transformer_lens"
    hook_validated: true
    logprob_validated: true
    hidden_dim: 4096
    num_layers: 32
    notes: "Validated on 2026-06-13/14 in Stage 2: hook job 242357 and logprob job 242358."

  mistral_alt:
    name: "mistralai/Mistral-7B-Instruct-v0.3"
    path: "/scratch/pabitra/rag-reason/models/Mistral-7B-Instruct-v0.3"
    role: "PRIMARY_DENSE"
    family: "mistral"
    hook_backend: "transformer_lens"
    hook_validated: false
    logprob_validated: false
    hidden_dim: null
    num_layers: null
    notes: "Documented fallback primary-dense candidate."

  reasoning_model:
    name: "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
    path: "/scratch/pabitra/rag-reason/models/DeepSeek-R1-Distill-Qwen-32B"
    role: "REASONING_TUNED"
    family: "deepseek"
    hook_backend: "transformer_lens"
    hook_validated: false
    logprob_validated: false
    hidden_dim: null
    num_layers: null
    notes: "Reasoning-tuned external-validity replication model."

  large_judge:
    name: "Qwen/Qwen2.5-32B-Instruct"
    path: "/scratch/pabitra/rag-reason/models/Qwen2.5-32B-Instruct"
    role: "LARGE_JUDGE"
    family: "qwen"
    hook_backend: "transformer_lens"
    hook_validated: false
    logprob_validated: false
    hidden_dim: null
    num_layers: null
    notes: "Primary large behavioural/judge model."
```

## 4. Hook Validation Reports (Inline JSON)

Source directory: [results/stage2/hook_validation](/Users/shubhammishra/Desktop/PhysMons/results/stage2/hook_validation)

### `llama_primary_hook_validation.json`

```json
{
  "determinism_ok": true,
  "extraction_ok": true,
  "hidden_dim": 4096,
  "hook_backend": "transformer_lens",
  "layers": 32,
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "notes": [
    "cue_token_index=34, last_prompt_index=49",
    "patch_max_logit_difference=25.718750"
  ],
  "patching_ok": true,
  "timing_seconds": {
    "extraction": 0.806,
    "forward_pass": 0.403,
    "total": 24.537
  }
}
```

### `qwen_primary_hook_validation.json`

```json
{
  "determinism_ok": true,
  "extraction_ok": true,
  "hidden_dim": 3584,
  "hook_backend": "transformer_lens",
  "layers": 28,
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "notes": [
    "cue_token_index=34, last_prompt_index=49",
    "patch_max_logit_difference=30.546875"
  ],
  "patching_ok": true,
  "timing_seconds": {
    "extraction": 0.685,
    "forward_pass": 0.343,
    "total": 21.619
  }
}
```

## 5. Compute Estimate (Inline JSON)

Source file: [results/stage2/compute_estimate.json](/Users/shubhammishra/Desktop/PhysMons/results/stage2/compute_estimate.json)

```json
{
  "estimated_full_activation_gpu_hours": 0.134,
  "estimated_pilot_gpu_hours": 0.027,
  "exceeds_80_percent_scratch_capacity": false,
  "inputs": {
    "activation_dtype": "float16",
    "full_families": 150,
    "hidden_dim": 4096,
    "num_layers": 32,
    "num_models": 2,
    "num_variants": 4,
    "pilot_families": 30,
    "prompt_positions": 2,
    "scratch_available_gb": 175000.0,
    "time_per_forward_seconds": 0.403,
    "tokens_per_problem": 2000
  },
  "stage": 2,
  "storage_per_family_per_model_mb": 4194.304,
  "total_full_storage_gb": 1258.291,
  "total_pilot_storage_gb": 251.658
}
```

## 6. Test Output (`pytest tests/ -v`, Inline)

Command rerun on 2026-06-14 after removing a host-environment import coupling in
`src/physmon/models/hooks.py`.

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.1, pytest-9.0.2, pluggy-1.6.0 -- /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
cachedir: .pytest_cache
rootdir: /Users/shubhammishra/Desktop/PhysMons
configfile: pyproject.toml
plugins: anyio-4.10.0, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ...
collected 58 items

tests/test_constructs.py::test_physics_template_validates_id_domain_and_cue_type PASSED [  1%]
tests/test_constructs.py::test_counterfactual_family_warns_when_uncertified PASSED [  3%]
tests/test_constructs.py::test_preregistration_status_and_binary_label_gate PASSED [  5%]
tests/test_constructs.py::test_probe_target_rejects_invalid_extraction_site PASSED [  6%]
tests/test_constructs.py::test_ensure_family_is_certified_raises_for_uncertified_family PASSED [  8%]
tests/test_constructs.py::test_compute_answer_flip_sensitivity_with_partial_parse_warning PASSED [ 10%]
tests/test_constructs.py::test_compute_distribution_level_sensitivity_returns_expected_jsd PASSED [ 12%]
tests/test_constructs.py::test_compute_logprob_drop_sensitivity_uses_marked_base_variant PASSED [ 13%]
tests/test_constructs.py::test_compute_all_sensitivity_measures_populates_single_record PASSED [ 15%]
tests/test_hooks.py::test_validate_prompt_side_positions_accepts_in_range_indices PASSED [ 17%]
tests/test_hooks.py::test_validate_prompt_side_positions_rejects_generated_token_indices PASSED [ 18%]
tests/test_hooks.py::test_zero_ablate_prompt_positions_zeros_only_requested_positions PASSED [ 20%]
tests/test_hooks.py::test_compare_activation_runs_detects_tensor_differences PASSED [ 22%]
tests/test_parser.py::test_parse_answer_success_cases[9.8-9.8-numeric] PASSED [ 24%]
tests/test_parser.py::test_parse_answer_success_cases[9.8 m/s^2-9.8 m/s^2-numeric] PASSED [ 25%]
tests/test_parser.py::test_parse_answer_success_cases[9.8 m s^{-2}-9.8 ms^-2-numeric] PASSED [ 27%]
tests/test_parser.py::test_parse_answer_success_cases[\u2248 9.8-9.8-numeric] PASSED [ 29%]
tests/test_parser.py::test_parse_answer_success_cases[~9.8-9.8-numeric] PASSED [ 31%]
tests/test_parser.py::test_parse_answer_success_cases[-3.20e-1 N--0.32 N-numeric] PASSED [ 32%]
tests/test_parser.py::test_parse_answer_success_cases[42.-42-numeric] PASSED [ 34%]
tests/test_parser.py::test_parse_answer_success_cases[\\boxed{9.8}-9.8-numeric] PASSED [ 36%]
tests/test_parser.py::test_parse_answer_success_cases[\\boxed{mv^2/2r}-mv^2/2r-symbolic] PASSED [ 37%]
tests/test_parser.py::test_parse_answer_success_cases[The answer is 9.8 m/s^2.-9.8 m/s^2-numeric] PASSED [ 39%]
tests/test_parser.py::test_parse_answer_success_cases[Final answer: 9.8-9.8-numeric] PASSED [ 41%]
tests/test_parser.py::test_parse_answer_success_cases[Answer = 9.8-9.8-numeric] PASSED [ 43%]
tests/test_parser.py::test_parse_answer_success_cases[Thus, 9.8 m/s^2-9.8 m/s^2-numeric] PASSED [ 44%]
tests/test_parser.py::test_parse_answer_success_cases[Therefore, mv^2/(2r)-mv^2/(2r)-symbolic] PASSED [ 46%]
tests/test_parser.py::test_parse_answer_success_cases[We compute many steps.\nFinal answer: \\boxed{9.8}-9.8-numeric] PASSED [ 48%]
tests/test_parser.py::test_parse_answer_success_cases[Some reasoning\n9.8 m/s^2-9.8 m/s^2-numeric] PASSED [ 50%]
tests/test_parser.py::test_parse_answer_success_cases[v = 9.8 m/s^2-9.8 m/s^2-numeric] PASSED [ 51%]
tests/test_parser.py::test_parse_answer_success_cases[F = ma-ma-symbolic] PASSED [ 53%]
tests/test_parser.py::test_parse_answer_success_cases[mv\xb2/2r-mv^2/2r-symbolic] PASSED [ 55%]
tests/test_parser.py::test_parse_answer_success_cases[mv^2/(2r)-mv^2/(2r)-symbolic] PASSED [ 56%]
tests/test_parser.py::test_parse_answer_success_cases[\\frac{mv^2}{2r}-(mv^2)/(2r)-symbolic] PASSED [ 58%]
tests/test_parser.py::test_parse_answer_success_cases[\\left(\\frac{mv^2}{2r}\\right)-(mv^2)/(2r)-symbolic] PASSED [ 60%]
tests/test_parser.py::test_parse_answer_success_cases[\\boxed{\\frac{1}{2}mv^2}-(1)/(2)mv^2-symbolic] PASSED [ 62%]
tests/test_parser.py::test_parse_answer_success_cases[9.8000-9.8-numeric] PASSED [ 63%]
tests/test_parser.py::test_parse_answer_success_cases[$9.8\\,\\mathrm{m/s^2}$-9.8 m/s^2-numeric] PASSED [ 65%]
tests/test_parser.py::test_parse_answer_success_cases[  '9.8 m/s^2.'  -9.8 m/s^2-numeric] PASSED [ 67%]
tests/test_parser.py::test_parse_answer_success_cases[Answer: .25 A-0.25 A-numeric] PASSED [ 68%]
tests/test_parser.py::test_parse_answer_success_cases[The final answer is 1E+03 J-1000 J-numeric] PASSED [ 70%]
tests/test_parser.py::test_parse_answer_success_cases[Reasoning...\n\n\\boxed{12 kg}-12 kg-numeric] PASSED [ 72%]
tests/test_parser.py::test_parse_answer_success_cases[There are steps here.\n\nmv^2/2r-mv^2/2r-symbolic] PASSED [ 74%]
tests/test_parser.py::test_parse_answer_success_cases[Answer: x = .5-0.5-numeric] PASSED [ 75%]
tests/test_parser.py::test_parse_answer_success_cases[Final answer: 1.23456-1.235-numeric] PASSED [ 77%]
tests/test_parser.py::test_parse_answer_failure_cases[] PASSED           [ 79%]
tests/test_parser.py::test_parse_answer_failure_cases[   ] PASSED        [ 81%]
tests/test_parser.py::test_parse_answer_failure_cases[I don't know.] PASSED [ 82%]
tests/test_parser.py::test_parse_answer_failure_cases[Cannot determine from the prompt.] PASSED [ 84%]
tests/test_parser.py::test_parse_answer_failure_cases[Sorry, I can't answer that.] PASSED [ 86%]
tests/test_parser.py::test_parse_answer_failure_cases[The values could be 9.8 or 10.1 depending on interpretation.] PASSED [ 87%]
tests/test_parser.py::test_parse_answer_failure_cases[Answers: 9.8; 10.1] PASSED [ 89%]
tests/test_parser.py::test_parse_answer_failure_cases[This problem discusses acceleration, force, and units but never commits to a final answer.] PASSED [ 91%]
tests/test_parser.py::test_parse_answer_failure_cases[Final line is a long prose summary rather than an answer to extract reliably.] PASSED [ 93%]
tests/test_parser.py::test_parse_answer_failure_cases[The quantities are 5 m and 7 s.] PASSED [ 94%]
tests/test_parser.py::test_failed_parse_logs_raw_output_snippet PASSED   [ 96%]
tests/test_parser.py::test_scientific_notation_is_not_treated_as_multi_answer PASSED [ 98%]
tests/test_parser.py::test_low_confidence_final_line_is_rejected PASSED  [100%]

=============================== warnings summary ===============================
tests/test_constructs.py::test_ensure_family_is_certified_raises_for_uncertified_family
  <string>:9: UserWarning: Family mechanics_irrelevant_variable_0001 is not solver-certified. Do not use it for sensitivity measurement until invariance is verified.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 58 passed, 1 warning in 1.35s =========================
```

Canonical repo-environment verification also remains green via `make test` (`./.venv/bin/pytest tests/ -v`).

## 7. Cluster Inventory (Full Content)

Source file: [docs/cluster_inventory.md](/Users/shubhammishra/Desktop/PhysMons/docs/cluster_inventory.md)

```markdown
# Sharanga Cluster Inventory

Date: 2026-06-13

This inventory records the live Sharanga environment discovered for PhysMon Part II.
All commands were run via `ssh sharanga`.

## II.1 - Model Inventory

Primary pre-downloaded model root:

- `/scratch/pabitra/rag-reason/models`

Current on-disk size of the model root:

- `1.8T /scratch/pabitra/rag-reason/models`

### Inventory Table

| Model family | Model name | Parameter count | Path on scratch | Size on disk | Format | Usable for PhysMon roles |
|---|---|---:|---|---:|---|---|
| Qwen | Qwen2.5-7B-Instruct | 7B | `/scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct` | 14G | safetensors | `PRIMARY_DENSE` confirmed on 2026-06-13 via A100 TransformerLens dummy-forward job `242337` (`d_model=3584`, `n_layers=2` smoke) |
| Llama | Llama-3.1-8B-Instruct | 8B | `/scratch/pabitra/rag-reason/models/Llama-3.1-8B-Instruct` | 30G | safetensors | `PRIMARY_DENSE` confirmed on 2026-06-13 via A100 TransformerLens dummy-forward job `242338` (`d_model=4096`, `n_layers=2` smoke) |
| Mistral | Mistral-7B-Instruct-v0.3 | 7B | `/scratch/pabitra/rag-reason/models/Mistral-7B-Instruct-v0.3` | 27G | safetensors | `PRIMARY_DENSE` alternate candidate; not needed because the required non-Qwen dense slot is already covered by Llama |
| Qwen | Qwen2.5-32B-Instruct | 32B | `/scratch/pabitra/rag-reason/models/Qwen2.5-32B-Instruct` | 59G | safetensors | `LARGE_JUDGE` |
| Qwen | Qwen3-32B | 32B | `/scratch/pabitra/rag-reason/models/Qwen3-32B` | 59G | safetensors | `LARGE_JUDGE` secondary candidate |
| Qwen | Qwen3.5-122B-A10B-FP8 | 122B MoE (10B active) | `/scratch/pabitra/rag-reason/models/Qwen3.5-122B-A10B-FP8` | 110G | safetensors | `LARGE_JUDGE` |
| Qwen | Qwen3.5-397B-A17B | 397B MoE (17B active) | `/scratch/pabitra/rag-reason/models/Qwen3.5-397B-A17B` | 717G | safetensors | `LARGE_JUDGE` |
| Qwen | Qwen3.5-397B-A17B-NVFP4 | 397B MoE (17B active) | `/scratch/pabitra/rag-reason/models/Qwen3.5-397B-A17B-NVFP4` | 211G | safetensors | `LARGE_JUDGE` |
| Mistral | Mistral-Small-3.2-24B-Instruct-2506 | 24B | `/scratch/pabitra/rag-reason/models/Mistral-Small-3.2-24B-Instruct-2506` | 88G | safetensors | `OTHER` |
| Mistral | Mistral-Small-4-119B-2603 | 119B | `/scratch/pabitra/rag-reason/models/Mistral-Small-4-119B-2603` | 212G | safetensors | `LARGE_JUDGE` |
| other | DeepSeek-R1-Distill-Qwen-32B | 32B | `/scratch/pabitra/rag-reason/models/DeepSeek-R1-Distill-Qwen-32B` | 59G | safetensors | `REASONING_TUNED`, `LARGE_JUDGE` |
| other | DeepSeek-V4-Flash-W4A16-FP8-MTP | unspecified in dir name | `/scratch/pabitra/rag-reason/models/DeepSeek-V4-Flash-W4A16-FP8-MTP` | 146G | safetensors | `OTHER` |
| other | DeepSeek-V4-Flash-W4A16-FP8-MTP-vllmfix | unspecified in dir name | `/scratch/pabitra/rag-reason/models/DeepSeek-V4-Flash-W4A16-FP8-MTP-vllmfix` | 146G | safetensors | `OTHER` |
| other | gemma-3-27b-it | 27B | `/scratch/pabitra/rag-reason/models/gemma-3-27b-it` | 49G | safetensors | `OTHER` |
| other | gemma-4-31B | 31B | `/scratch/pabitra/rag-reason/models/gemma-4-31B` | 55G | safetensors | `LARGE_JUDGE` |

### Role Coverage Status

- `PRIMARY_DENSE` from Qwen family: present as `Qwen2.5-7B-Instruct` candidate.
- `PRIMARY_DENSE` from Llama/Mistral family: present as `Llama-3.1-8B-Instruct` and `Mistral-7B-Instruct-v0.3` candidates.
- `REASONING_TUNED`: present as `DeepSeek-R1-Distill-Qwen-32B`.
- `LARGE_JUDGE`: present via multiple models, including `Qwen2.5-32B-Instruct`, `Mistral-Small-4-119B-2603`, `gemma-4-31B`, and the large Qwen 3.5 models.

Current verdict: no required role category is absent, and the minimum required
`PRIMARY_DENSE` coverage is now confirmed with one Qwen-family dense model
(`Qwen2.5-7B-Instruct`) and one Llama/Mistral-family dense model
(`Llama-3.1-8B-Instruct`).

## II.2 - GPU Node Assessment

### GPU Partitions

| Partition | Nodes | GPU type | GPUs per node | CPU / node | Memory / node | Default time | Max time | Notes |
|---|---:|---|---:|---:|---:|---|---|---|
| `gpu_a100_8` | 1 | `NVIDIA A100-SXM4-80GB` | 8 | 64 | 1000000M | `00:30:00` | `5-00:00:00` | `OverSubscribe=NO`, `DefMemPerGPU=96000`, node `gpunode4` |
| `gpu_h100_4` | 2 | `NVIDIA H100 80GB HBM3` | 4 | 64 | 1000000M | `00:30:00` | `2-00:00:00` | `OverSubscribe=NO`, `DefMemPerGPU=96000`, nodes `gpunode5-6` |
| `gpu_h200_8` | 1 | `NVIDIA H200 NVL` | 8 | 64 | 1000000M | `00:30:00` | `1-00:00:00` | `OverSubscribe=NO`, `DefMemPerGPU=96000`, node `gpunode7` |

### Node State Snapshot

| Node | Partition | State | GPU inventory | CPU alloc | Memory alloc | Notes |
|---|---|---|---|---:|---:|---|
| `gpunode4` | `gpu_a100_8` | `MIXED` | 8 x A100 80GB | 44 / 64 | 344G / 1000000M | A100 smoke succeeded here |
| `gpunode5` | `gpu_h100_4` | `MIXED+RESERVED` | 4 x H100 80GB HBM3 | 9 / 64 | 180G / 1000000M | current H100 work concentrated here |
| `gpunode6` | `gpu_h100_4` | `DOWN+DRAIN+NOT_RESPONDING` | 4 x H100 80GB HBM3 | 0 / 64 | 0 | reason: `Kill task failed (JobId=242225 StepId=0)` at `2026-06-13T17:35:40` |
| `gpunode7` | `gpu_h200_8` | `MIXED` | 8 x H200 NVL | 20 / 64 | 612G / 1000000M | current H200 work active here |

### Queue Depth Snapshot

Live `squeue` snapshot at inventory time:

- `gpu_a100_8`: 4 running jobs, 0 pending.
- `gpu_h100_4`: 2 running jobs, 12 pending jobs.
- `gpu_h200_8`: 4 running jobs, 0 pending jobs in the immediate snapshot, but new submissions were blocked by active resource/QoS pressure.

Representative pending reasons observed:

- `ReqNodeNotAvail, UnavailableNodes:gpunode6`
- `Resources`
- `Requested nodes are busy`

### Wait-Time Notes from Recent `sacct`

- A100 recent jobs started immediately when capacity was available. Example:
  `242257` (`physmon_smoke_a100`) submitted and started on `2026-06-13 18:50:48`.
- H100 recent jobs also started immediately when `gpunode5` was available. Example:
  `242167` submitted at `2026-06-13 13:20:57` and started at `13:20:57`.
- H200 recent jobs typically started within seconds to a few minutes when capacity was
  available. Examples:
  - `242199`: submitted `15:08:21`, started `15:08:22`
  - `242114`: submitted `11:01:35`, started `11:04:36`
  - `242107`: submitted `10:27:37`, started `10:28:39`

Interpretation: nominal wait times are low when nodes are healthy and free, but live
H100 access is currently impaired by one drained node and live H200 access is currently
tight because the single H200 node is heavily used.

### CUDA / Driver / GPU Memory

Direct measurements:

- A100 (`gpu_a100_8` on `gpunode4`):
  - `Driver Version: 580.126.20`
  - `CUDA Version: 13.0`
  - `memory.total = 81920 MiB`
- H200 (`gpu_h200_8` on `gpunode7`, measured via an `srun` step inside the user's
  running allocation `242248`):
  - `Driver Version: 580.126.20`
  - `CUDA Version: 13.0`
  - `memory.total = 143771 MiB`

H100 note:

- Direct `nvidia-smi` capture was not obtainable during this snapshot because
  `gpunode6` was down/drained and immediate one-GPU probes on `gpu_h100_4` were blocked by
  live reservation/resource state.
- Slurm GRES confirms `NVIDIA H100 80GB HBM3`.

### Proposal §6.1 Access Check

Proposal §6.1 assumes access to H200, H100, and A100 resources. This is true with
caveats:

- A100 access is directly verified.
- H100 partition access exists, but one of two nodes is currently down/drained, and the
  other is reserved/partially occupied.
- H200 partition access exists and was already used by the user, but fresh submissions
  are presently constrained by live resource/QoS pressure.
- Follow-up on 2026-06-13 23:28 IST: fresh template-smoke submissions were accepted by
  Slurm as jobs `242344` (H100) and `242345` (H200), which confirms the partition names
  and template wiring are correct, but immediate execution was deferred by
  `QOSMaxCpuPerUserLimit` rather than by an invalid partition, path, or environment
  configuration.

## II.3 - Storage Assessment

### Filesystems

- Home: `/home/pabitra`
  - filesystem size `199T`
  - used `24T`
  - available `175T`
- Scratch: `/scratch/pabitra`
  - filesystem size `274T`
  - used `100T`
  - available `175T`

### PhysMon Scratch Area

- Root: `/scratch/pabitra/physmon`
- Current usage: `182K`
- Subdirectories confirmed accessible:
  - `/scratch/pabitra/physmon/activations`
  - `/scratch/pabitra/physmon/checkpoints`
  - `/scratch/pabitra/physmon/slurm_logs`

### Activation Storage Estimate

Using the requested rough estimate for a 7B dense model:

- `80 activation sites x 2000 tokens x 4000 hidden dim x 4 bytes`
- Per problem: `2,560,000,000 bytes`
- Per problem: about `2.56 GB` decimal, or about `2.38 GiB`

Illustrative totals:

- 100 problems: about `256 GB` (`~238 GiB`)
- 500 problems: about `1.28 TB` (`~1.16 TiB`)
- 1000 problems: about `2.56 TB` (`~2.33 TiB`)

Assessment:

- Current scratch headroom (`175T` available) is easily sufficient for the pilot study and
  leaves comfortable room for activations, checkpoints, logs, and additional model caches.
- The dominant risk is not raw cluster-wide free space but local experiment discipline:
  activation retention policy and per-run cleanup will matter once larger sweeps begin.

## II.4 - Software Stack Verification

### Verified Environment

GPU-backed A100 validation job output:

- `PyTorch: 2.7.1+cu126`
- `CUDA: True`
- `GPU: NVIDIA A100-SXM4-80GB`
- `TransformerLens: 3.4.0`
- `Transformers: 5.11.0`
- `SymPy: 1.14.0`
- `sklearn: 1.9.0`
- `baukit: 0.0.1`

Interpretation:

- The Sharanga `physmon` environment imports the required stack successfully on a GPU node.
- CUDA is visible inside the environment on A100.
- `transformer_lens` and `baukit` are both installed and importable.

### Hook Support Validation

Current status:

- A direct local-path TransformerLens load attempt failed with
  `ValueError: /scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct not found`,
  which revealed that this TransformerLens version expects an official model identifier
  even when weights are supplied from a local directory.
- The corrected official-ID plus local-weights path was then validated on A100 with a
  deliberately reduced-layer smoke test (`first_n_layers=2`) and explicit stage markers:
  - `242337`: `Qwen/Qwen2.5-7B-Instruct` with local
    `/scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct`
    - `hf_loaded` after `527.03s`
    - `tl_loaded` after `10.64s`
    - `dummy_forward_ok` with `logits_shape=[1, 33, 152064]`
  - `242338`: `meta-llama/Llama-3.1-8B-Instruct` with local
    `/scratch/pabitra/rag-reason/models/Llama-3.1-8B-Instruct`
    - `hf_loaded` after `1257.49s`
    - `tl_loaded` after `2.90s`
    - `dummy_forward_ok` with `logits_shape=[1, 32, 128256]`

Conclusion:

- `Qwen2.5-7B-Instruct` is confirmed usable as the Qwen-family `PRIMARY_DENSE`
  candidate for Stage 2 instrumentation work.
- `Llama-3.1-8B-Instruct` is confirmed usable as the non-Qwen `PRIMARY_DENSE`
  candidate for Stage 2 instrumentation work.
- `Mistral-7B-Instruct-v0.3` remains a documented fallback candidate but is not required
  to satisfy the proposal minimum once Llama is confirmed.
- This completes the Part II requirement to verify that the minimum required model-role
  inventory exists locally and that the primary dense candidates are compatible with the
  intended TransformerLens loading path.
```

## 8. Assumption Tracker (Full Content)

Source file: [docs/assumptions/assumption_tracker.md](/Users/shubhammishra/Desktop/PhysMons/docs/assumptions/assumption_tracker.md)

```markdown
# Assumption Tracker

This tracker records verification status for the assumptions listed in the supplementary
document.

## A1 - Sharanga Cluster Access

Status: Verified with caveats.

Evidence:
- SSH access works for user `pabitra`; home is `/home/pabitra`; scratch is
  `/scratch/pabitra`.
- `~/PhysMons` exists on Sharanga and `activations` is a symlink to
  `/scratch/pabitra/physmon/activations`.
- Slurm partitions discovered during Part I.5:
  `gpu_h200_8`, `gpu_h100_4`, `gpu_a100_8`.
- A100 smoke job `242257` completed successfully on `gpunode4` with
  `torch 2.7.1+cu126`, `torch.version.cuda == 12.6`,
  `torch.cuda.is_available() == true`, and device
  `NVIDIA A100-SXM4-80GB`.
- Part II inventory confirmed live node topology:
  `gpunode4` (A100), `gpunode5-6` (H100), `gpunode7` (H200).
- Part II queue inspection showed `gpunode6` is currently
  `DOWN+DRAIN+NOT_RESPONDING`, which explains the live H100 submission
  failures observed during Part I.5.
- Direct hardware probes recorded `Driver Version 580.126.20` and
  `CUDA Version 13.0` on A100 and H200 nodes.
- Later on 2026-06-13, fresh H100 and H200 template-smoke submissions were both accepted
  by Slurm as jobs `242344` and `242345`, which confirms that the partition names,
  scratch paths, and template entrypoints are correct.
- Immediate runtime for those fresh H100/H200 smoke jobs was deferred by
  `QOSMaxCpuPerUserLimit`, so same-session execution on those partitions remains subject
  to live scheduler policy rather than a repo-side misconfiguration.

## A2 - Hooking Support for Selected Models

Status: Verified with caveats.

Evidence:
- Sharanga `physmon` environment created successfully and exported to
  `docs/environment_lock.yml`.
- `transformer_lens` import succeeds in the Sharanga `physmon` environment when checked
  with a bounded import.
- `sympy` import succeeds in the Sharanga `physmon` environment.
- GPU-backed Part II validation on A100 confirmed live imports for:
  `torch 2.7.1+cu126`, `transformer-lens 3.4.0`, `transformers 5.11.0`,
  `sympy 1.14.0`, `scikit-learn 1.9.0`, and `baukit 0.0.1`.
- The packaging backend had to be updated to `setuptools.build_meta` for editable install
  support on Sharanga.
- `baukit` had to be installed from GitHub because no matching PyPI release was
  available.
- A direct local-path TransformerLens load attempt then showed that this
  TransformerLens version expects an official model identifier rather than the raw local
  path string.
- Corrected official-ID plus local-weights A100 jobs then completed cleanly for both
  required dense candidates:
  - `242337`: `Qwen/Qwen2.5-7B-Instruct`
    - `hf_loaded` after `527.03s`
    - `tl_loaded` after `10.64s`
    - `dummy_forward_ok` with `logits_shape=[1, 33, 152064]`
  - `242338`: `meta-llama/Llama-3.1-8B-Instruct`
    - `hf_loaded` after `1257.49s`
    - `tl_loaded` after `2.90s`
    - `dummy_forward_ok` with `logits_shape=[1, 32, 128256]`
- This is sufficient to confirm that the selected Qwen and Llama dense candidates are
  compatible with the intended TransformerLens loading path for the upcoming Stage 2
  validation scripts.
- Remaining caveat: this was a deliberately narrow smoke test (`first_n_layers=2`) rather
  than the full Stage 2 hook-extraction suite, so layer-by-layer activation extraction,
  patching, and determinism still belong to Part IV rather than Part II.

## A3 - Literature Gap Still Current

Status: Not yet verified.

Evidence: Fresh literature search required before benchmark development.

## A4 - Symbolic Invariance Certificates Are Tractable

Status: Not yet verified.

Evidence: Pending Stage 1/Stage 3 template work.

## A5 - Log-Probability Access Is Stable Across Models

Status: Verified with caveats.

Evidence:
- Stage 2 log-probability validation completed successfully for both required primary
  dense models on A100:
  - `242356`: `Qwen/Qwen2.5-7B-Instruct`
    - finite `log p(y* | x)` for reference answer `10 m/s`
    - altered prompt changed the reference-answer log-probability
    - greedy generation was deterministic across repeated runs
  - `242358`: `meta-llama/Llama-3.1-8B-Instruct`
    - finite `log p(y* | x)` for reference answer `10 m/s`
    - altered prompt changed the reference-answer log-probability
    - greedy generation was deterministic across repeated runs
- Caveat: these validations use one controlled physics prompt and a short reference answer,
  so broader benchmark stability still depends on the full Stage 4 behavioural sweep.

## A6 - Dual Validators Are Available

Status: Not yet verified.

Evidence: Pending validator recruitment plan.

## A7 - Bibliography IDs Are Correct Except Flagged Entries

Status: Not yet verified.

Evidence: Bibliography audit required before submission.

## A8 - Large Open Model Is Available Locally

Status: Verified.

Evidence:
- Sharanga model inventory found multiple large open-weight models already present under
  `/scratch/pabitra/rag-reason/models`.
- Large candidates include:
  `Qwen2.5-32B-Instruct`, `Qwen3-32B`, `DeepSeek-R1-Distill-Qwen-32B`,
  `Mistral-Small-4-119B-2603`, `gemma-4-31B`,
  `Qwen3.5-122B-A10B-FP8`, and `Qwen3.5-397B-A17B`.
- The model root currently occupies `1.8T`, indicating the weights are already staged
  locally on cluster storage rather than needing immediate download.

## A9 - Pilot Sensitivity Signal Exists

Status: Not yet verified.

Evidence: Pending Stage 4 pilot behavioural sweep.
```

## 9. Open Decisions with Agent Recommendations

These are recommendations, not resolutions. They still require PI confirmation per the
supplementary decision log.

| Decision | Status | Agent recommendation |
|---|---|---|
| **[D1]** Specific model versions | Pending | Lock `Qwen/Qwen2.5-7B-Instruct` as Qwen `PRIMARY_DENSE`, `meta-llama/Llama-3.1-8B-Instruct` as non-Qwen `PRIMARY_DENSE`, `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` as `REASONING_TUNED`, and `Qwen/Qwen2.5-32B-Instruct` as `LARGE_JUDGE`. Keep `mistralai/Mistral-7B-Instruct-v0.3` as fallback only. |
| **[D2]** Sensitivity threshold for binarisation | Pending | Do not lock a numeric threshold yet. Use Stage 4 pilot behavioural results to inspect class balance on the training families only, then pre-register one threshold before Stage 5. If a default candidate is needed for discussion, start from `hat{S}_theta(tau) >= 0.25` as the first calibration candidate, not as a committed value. |
| **[D3]** Paraphrase generation strategy | Pending | Keep free-form paraphrase generation out of v1. For Stage 3, prefer Cue A and Cue B plus exact representation transforms only. If the PI wants Cue C beyond exact transforms, require a local model plus explicit double human review and exact-certifiability checks before inclusion. |
| **[D5]** Value of `m` (variants per family) | Pending | Start with `m = 4` fixed across cue types for the pilot, since the current compute estimate is already parameterized at `m = 4` and remains inexpensive on storage and forward-pass cost. Revisit only if pilot behaviour suggests that pairwise stability is too noisy. |
| **[D9]** Human validator recruitment | Pending | Recruit two validators with basic undergraduate-level physics competence plus a short written adjudication checklist. Require double review on pilot families, track disagreements explicitly, and lock `data/validated/` as immutable after adjudication. |

Note: no separate `[D4]` surfaced in the proposal/supplementary materials handled in this initialization pass.

## 10. Surprises / Deviations from Proposal

1. TransformerLens required official model identifiers plus local weights, not raw local
   model-directory strings. This changed the loader-validation path but not the chosen
   scientific models.
2. `baukit>=0.1` was not installable from PyPI on Sharanga; the fallback dependency had to
   be installed from GitHub.
3. `setuptools.backends.legacy:build` was not viable on Sharanga's stack; the package
   backend was switched to `setuptools.build_meta`.
4. The Mac did not have Conda available locally, so the CPU development environment was
   realized as a repo-local `.venv` while preserving the canonical GPU `environment.yml`.
5. H100 access is real but operationally noisy because one node was
   `DOWN+DRAIN+NOT_RESPONDING`; H200 access is real but can be constrained by
   `QOSMaxCpuPerUserLimit`.
6. Late in Part VI preparation, the exact host-shell command `pytest tests/ -v` exposed an
   eager import dependency on `transformer_lens` through a typing-only path in
   `src/physmon/models/hooks.py`. That coupling was fixed by moving the loader import under
   `TYPE_CHECKING`, and the exact command now passes with 58/58 tests.

## Appendix A - Log-Probability Validation Summary

Source directory: [results/stage2/logprob_validation](/Users/shubhammishra/Desktop/PhysMons/results/stage2/logprob_validation)

- `Qwen/Qwen2.5-7B-Instruct`:
  `logprob_finite=true`, `logprob_changes_with_input=true`,
  `generation_determinism_ok=true`, `reference_logprob=-15.7734375`,
  `altered_prompt_logprob=-22.28125`
- `meta-llama/Llama-3.1-8B-Instruct`:
  `logprob_finite=true`, `logprob_changes_with_input=true`,
  `generation_determinism_ok=true`, `reference_logprob=-10.703125`,
  `altered_prompt_logprob=-10.78125`

Full inline JSON remained omitted from the main body because both models passed cleanly and
no instability signal appeared in Stage 2.

## Appendix B - Sensitivity Implementation Pointer

If the construct review raises implementation questions, inspect:
[src/physmon/formal/sensitivity.py](/Users/shubhammishra/Desktop/PhysMons/src/physmon/formal/sensitivity.py)

## Appendix C - Current Session Status Snapshot

- Parts I-V complete and verified.
- Stage 1 gate: PASS.
- Stage 2 gate: PASS.
- Local repo tests: PASS.
- Local repo lint: PASS.
- Current next hard stop: wait for PI confirmation of [D1] and the Stage 3 brief before
  benchmark construction begins.
