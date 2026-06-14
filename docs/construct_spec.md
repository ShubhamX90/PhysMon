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

Sensitivity measure:     Qwen S_lp_theta(tau) - maximum log-probability drop of the
                         correct answer across solver-verified invariant family variants.
                         Formula: max_j [log p_Qwen(y* | x_base) - log p_Qwen(y* | x_j)]
                         where x_base = variant_id 0, computed via teacher-forced
                         forward pass on the repaired chat-template-formatted prompts.

Binarisation threshold:  0.5 nats

Rationale:               Targets 30% positive-class rate (9/30 pilot families) in the
                         pilot training distribution. Natural gap in the S_lp empirical
                         distribution. Determined from training-split analysis of the
                         repaired Stage 4 behavioural sweep before any probe training.

Date pre-registered:     2026-06-14

Commit:                  5a72370
