# PhysMon Stage 13 — Controlled Part II Execution Brief, Version 2.0

**Governing scientific document:** `PhysMon Part II — Next-Phase Scientific and Experimental Plan`, version 1.1  
**Predecessor:** `PhysMon Research Proposal` and supplementary documentation  
**Issued:** July 3, 2026  
**Status:** Active controlled-execution brief. It supersedes prior Stage 12/13 planning wherever there is a conflict.

---

## 0. Mission

Your job is not to maximize the number of experiments completed. Your job is to turn the existing PhysMon repository into a scientifically auditable evidence base and then execute only the experiments that can close, falsify, or sharply bound the central causal chain:

\[
\text{verified non-governing cue}
\rightarrow
\text{specific internal processing}
\rightarrow
\text{localized causal representation}
\rightarrow
\text{diagnostic hidden-state signature}
\rightarrow
\text{counterfactual instability}
\rightarrow
\text{selective correction}.
\]

The target is the strongest scientifically defensible paper possible. Scientific validity takes precedence over speed, positive findings, GPU utilization, or preserving earlier interpretations.

The three levels below must never be conflated:

1. **Prompt condition:** which cue, wording, value, position, or rendering appears in the prompt.
2. **Observed model behaviour:** model-specific counterfactual sensitivity across solver-certified invariant family members.
3. **Internal representation or mechanism:** a representation that predicts Level-2 behaviour, or a component whose controlled intervention changes Level-2 behaviour.

Use **shortcut sensitivity**, **counterfactual instability**, or **cue dependence** for Level-2 findings. Reserve **shortcut reliance** for cases supported by both behavioural counterfactual evidence and appropriately controlled Level-3 intervention evidence.

---

# 1. Mandatory operating contract

These rules apply to every action in this brief.

## 1.1 Read before editing

Before changing any file:

1. Read the repository `README`.
2. Read the Part I proposal and supplementary document.
3. Read the complete Part II plan.
4. Read the current decision log.
5. Inspect the repository tree, Git status, current branch, environment files, Slurm templates, and result directories.
6. Identify existing utilities before creating duplicate implementations.
7. Produce a short preflight report listing:
   - repository root;
   - current branch and commit;
   - dirty/untracked files;
   - data and results locations;
   - decision-log path;
   - available benchmark manifests;
   - known model checkpoints;
   - existing scripts relevant to each requested task;
   - unresolved path or schema ambiguities.

Do not infer paths or schemas from this prompt when the repository contains contradictory evidence. Inspect first.

## 1.2 No fabrication

Never invent or silently infer:

- job IDs;
- file paths;
- family IDs;
- model revisions;
- tokenizer hashes;
- dataset hashes;
- experiment results;
- human-validation labels;
- parser ground truth;
- confirmatory-family membership;
- missing metadata.

Use `NULL`, `unknown`, or an explicit unresolved issue. An honest missing field is preferable to false provenance.

Numbers in this brief are **prior-audit expectations**, not unquestionable ground truth. Verify every number against authoritative raw artifacts before entering it as authoritative.

## 1.3 Preserve raw evidence

Do not delete, rename in place, or overwrite raw results, logs, partial outputs, corrected outputs, or superseded artifacts.

- All new Stage 13 outputs go under versioned paths such as:
  `results/stage13/<task_id>/<run_id>/`
- Use atomic writes.
- Default to refusing overwrite unless an explicit `--overwrite` flag is passed.
- A correction creates a new artifact and a provenance link to the superseded artifact.
- Preserve both historical and corrected entries in the registry.
- Never reinterpret an empty file, one-byte marker, zero-row file, or truncated array as a scientific null result.

## 1.4 Discovery and confirmation must remain separate

A family is **discovery-consumed** if it was used to select or tune any of the following:

- sensitivity metric or threshold;
- primary probe architecture;
- activation layer or token position;
- head or circuit site;
- donor policy;
- intervention strength;
- causal metric;
- baseline feature set;
- statistical test;
- inclusion or exclusion rule;
- paper headline.

Leave-one-out prediction does not automatically make an analysis confirmatory if layer, feature, threshold, or model selection used the full dataset.

Any family changed after observing model behaviour, monitor score, or intervention effect returns to discovery status.

If no untouched internal-confirmatory families remain, state this explicitly. Do not manufacture a confirmatory partition. The remedy is a prospective internal or external confirmation set.

## 1.5 Human validation boundary

The coding agent may:

- prepare validator handbooks;
- generate blinded packets;
- generate qualification tests;
- create tracking sheets;
- compute agreement after labels are entered;
- identify missing or inconsistent annotations.

The coding agent may **not**:

- act as either independent human validator;
- fill human ground-truth labels;
- adjudicate physics disagreements;
- treat an LLM or agent review as human validation;
- mark Wave 1 complete based only on automated checks.

## 1.6 Statistical unit

The canonical physics family is the independent inference unit.

Rendered variants, repeated generations, paraphrases, and variable-renamed siblings must not be treated as independent samples. All resampling and cross-validation must be grouped by canonical family.

For model-specific analyses, the unit may be the model–family pair, but repeated variants remain clustered.

## 1.7 Reproducibility requirements

Every executable Stage 13 task must:

- expose a command-line interface;
- support `--help`;
- support `--dry-run` where practical;
- accept explicit input and output paths;
- log the full command and configuration;
- record Git commit and dirty-tree status;
- record data, manifest, model, tokenizer, and config hashes;
- record random seeds;
- use deterministic seeds where possible;
- write machine-readable summaries;
- write human-readable logs;
- include unit or integration tests;
- fail loudly on schema mismatch;
- avoid global mutable state and hard-coded personal paths.

Use existing environment and repository conventions. Do not introduce a new framework unless necessary.

## 1.8 GPU governance

Until **Wave 0 PASS** and the **Wave 1 validation pilot PASS**:

- no new experiment may be designated confirmatory;
- no new head/layer/site may become a headline claim;
- no threshold or primary metric may be changed;
- no automated follow-up job may be launched merely because an exploratory result looks positive.

Already queued jobs may finish, but ingest them as `complete_exploratory` unless they were genuinely pre-specified before launch.

Do not submit follow-up GPU jobs automatically. Prepare the experiment card, estimate cost, report the proposed job, and wait for explicit PI authorization.

## 1.9 Hard stop policy

This is a master brief, not permission to execute all waves in one uninterrupted run.

In the first implementation cycle, complete:

1. preflight;
2. Wave 0;
3. Wave 1 software and validation-material preparation;
4. Wave 0 and Wave 1-pilot reports.

Then stop and report. Do not proceed to confirmatory Wave 2–4 execution without explicit approval.

---

# 2. Repository-wide conventions to add

Create or reuse the following directories:

```text
docs/registry/
docs/validation/
docs/experiment_cards/
docs/stage13/
results/canonical/
results/stage13/
schemas/
tests/stage13/
```

Create a Stage 13 machine-readable configuration:

```text
configs/stage13/stage13_governance.yaml
```

It should define:

- canonical family ID field;
- benchmark manifests;
- result roots;
- allowed registry statuses;
- allowed experiment classes;
- split labels;
- authoritative task IDs;
- hash algorithms;
- default bootstrap repetitions;
- random seeds;
- significance and FDR settings;
- paths to proposal and decision log;
- whether a task is exploratory or confirmatory.

Do not duplicate configuration constants across scripts.

---

# 3. Preflight task — Read-only repository audit

## Task PF.1 — Stage 13 preflight report

Create:

```text
docs/stage13/stage13_preflight_report.md
```

The report must include:

1. Git branch, commit, and dirty status.
2. Repository tree summary.
3. Counts by file type under `results/`.
4. Located benchmark manifests and their family counts.
5. Located decision logs and job-history sources.
6. Located raw and summary artifacts for Stages 6–12.
7. Existing scripts that can be reused.
8. Missing dependencies or incompatible schemas.
9. A table mapping each requested Stage 13 task to:
   - existing implementation;
   - implementation needing modification;
   - missing implementation.
10. Ambiguities requiring PI resolution.

Do not modify scientific artifacts during preflight.

**Preflight stop condition:** If the repository root, canonical benchmark manifest, decision log, or authoritative results root cannot be identified confidently, stop and ask for clarification.

---

# 4. WAVE 0 — Evidence stabilization

## Wave 0 objective

Every paper-eligible result must be traceable to:

- model and revision;
- tokenizer;
- data and family manifest;
- code commit;
- configuration;
- raw output;
- summary;
- statistical unit;
- discovery/confirmation status;
- correction history.

Wave 0 may pass even if some historical jobs are irrecoverably under-documented, but only if those jobs are explicitly demoted to non-paper-eligible status. Do not fill missing provenance by guesswork.

---

## Task W0.1 — Master experiment registry

### Authoritative representation

Use:

```text
docs/registry/experiment_registry.jsonl
```

as the machine-authoritative registry.

Generate:

```text
docs/registry/experiment_registry.csv
```

as a review-friendly export.

One registry record represents one distinct run attempt. Slurm arrays require separate `array_task_id` records or a clearly normalized child-run table.

### Required fields

```text
experiment_id
parent_experiment_id
run_attempt_id
experiment_class
scientific_question
hypothesis
null_interpretation
claim_level
model_role
model_path
model_revision
tokenizer_path
tokenizer_hash
dtype
quantization
git_commit
git_dirty
command
config_file
config_hash
dataset_version
dataset_hash
family_manifest
family_manifest_hash
split_version
split_hash
sensitivity_metric
sensitivity_threshold
activation_site
token_position
patch_layer
patch_head
donor_policy
target_policy
random_seeds
job_id
array_task_id
hardware
submitted_at
completed_at
runtime_hours
status
raw_output_paths
summary_paths
stdout_path
stderr_path
supersedes_experiment_id
correction_history
paper_eligibility
claim_supported
notes
```

### Allowed statuses

Use exactly:

- `complete_authoritative`
- `corrected_authoritative`
- `complete_exploratory`
- `superseded`
- `partial_not_reportable`
- `failed`
- `pending`
- `diagnostic_only`

### Critical rule

The prior list of known results is a **candidate seed list**. For each candidate:

1. find the raw artifact;
2. verify the family panel and denominator;
3. regenerate or verify the summary;
4. verify the code/config association;
5. assign status only after provenance checks;
6. record discrepancies instead of forcing the expected value.

### Validation script

Create:

```text
scripts/stage13/verify_registry.py
```

Checks must include:

- unique experiment/run IDs;
- allowed statuses only;
- valid parent/supersedes references;
- all authoritative paths exist;
- hashes are populated for authoritative runs;
- authoritative runs have raw output and summary;
- no paper-eligible claim points only to a superseded, partial, failed, or missing run;
- no corrected run silently overwrites its predecessor;
- all job IDs in available job histories are either registered or explicitly excluded;
- every authoritative summary can be traced to its raw inputs.

Write:

```text
results/stage13/wave0/registry_verification.json
```

---

## Task W0.2 — Normalized evidence tables

Do not use a wide table with Qwen-, Llama-, and DeepSeek-specific columns in every row. Use normalized long-form tables.

### Family-level table

Create the authoritative machine-readable table:

```text
results/canonical/model_family_evidence.parquet
```

and a review export:

```text
results/canonical/model_family_evidence.csv
```

One row per:

```text
(model_id, canonical_family_id, benchmark_version)
```

Required groups:

**Identity**
- model_id
- model_role
- canonical_family_id
- template_id
- domain
- cue_type
- benchmark_version
- split_membership
- family_manifest_hash

**Validation**
- solver_certificate_hash
- automated_solver_status
- human_validation_status
- adjudication_status
- parser_status
- parser_issue

**Behaviour**
- n_variants_expected
- n_variants_observed
- n_variants_parsed
- family_parse_rate
- all_variants_correct
- base_variant_correct
- family_correctness_rate
- S_lp
- S_lp_binary
- answer_flip_rate
- distributional_sensitivity
- stochastic_failure_rate

**Monitoring**
- primary_monitor_score
- monitor_layer
- monitor_site
- monitor_prediction_source
- entropy_score
- confidence_score
- black_box_counterfactual_score
- cot_classifier_score
- answer_rationale_score
- correctness_probe_score

**Causal**
- causal_panel_eligible
- causal_site
- intervention_type
- normalized_effect
- raw_correct_logprob_effect
- raw_S_lp_effect
- sign_consistent
- general_damage_metric

**Eligibility**
- exclusion_flag
- exclusion_reason
- evidence_status
- paper_eligibility
- source_experiment_ids

### Variant-level table

Create:

```text
results/canonical/model_variant_evidence.parquet
```

One row per:

```text
(model_id, canonical_family_id, variant_id, generation_id)
```

This table stores variant log-probabilities, parsed answers, correctness, prompt metadata, and activation-derived predictions.

### Integrity checks

Create:

```text
scripts/stage13/build_canonical_evidence.py
scripts/stage13/verify_canonical_evidence.py
```

Checks:

- all variant rows map to exactly one family;
- no duplicate primary keys;
- family aggregates recompute from variant data;
- unexpected missingness is reported by field and model;
- structural nulls are not counted as errors;
- all source experiment IDs exist in the registry;
- no value comes from superseded artifacts.

Report `n_unexpected_nulls`, not raw null count.

---

## Task W0.3 — Artifact authority audit

Create:

```text
scripts/stage13/run_artifact_authority_audit.py
docs/registry/artifact_authority_audit.json
docs/registry/artifact_authority_audit.md
```

Audit all Stage 6–12 result directories, not only hard-coded Stage 10–12 paths.

The script must:

1. inventory raw, summary, partial, corrected, placeholder, and nested archive artifacts;
2. detect multiple summaries for the same experiment;
3. detect empty and zero-row outputs;
4. detect summaries without raw data;
5. detect raw data without summaries;
6. compare stated row counts with actual records;
7. compare summary statistics with regenerated values where feasible;
8. identify stale partial summaries;
9. identify model-panel mismatches;
10. identify contradictory prose and numerical artifacts;
11. identify nested ZIP versions that differ from extracted files;
12. write a proposed authority resolution without deleting anything.

Every resolution entry must include:

```text
artifact_path
experiment_id
issue_type
evidence
proposed_authority
resulting_status
supersedes
manual_review_required
```

Known cases to verify include:

- full versus partial Llama sweep;
- original versus corrected variable-renaming labels;
- DeepSeek results on Qwen-selected versus DeepSeek-valid panels;
- incomplete Qwen-3B output;
- empty or zero-row controls;
- nested Stage 6 files that differ from extracted versions.

---

## Task W0.4 — Discovery/confirmation freeze

Create:

```text
docs/registry/partition_freeze.md
docs/registry/partition_freeze.json
```

For every analytical choice, record:

```text
choice_id
choice
selected_value
selection_data
selection_experiment_ids
selection_date
selection_rationale
families_consumed
models_consumed
consequence_for_confirmation
```

Explicitly separate:

- direct sample leakage;
- model-selection leakage;
- layer/head/site-selection leakage;
- threshold selection;
- feature-selection leakage;
- repeated analyst exposure.

Audit the known choices:

- 0.5-nat threshold;
- primary sensitivity metric;
- L16 per-variant monitor;
- L18 mean-state monitor;
- Qwen L16H11;
- Llama L21H2;
- donor and target rules;
- primary baseline set;
- causal recovery metric.

### Important correction

A family that received a leave-one-out prediction was not directly in that fold’s probe training set, but the analysis is still discovery if the layer, representation, target, or hyperparameters were selected using the complete dataset.

If no clean internal-confirmatory set remains, write:

```text
internal_confirmatory_status: none_available
```

and specify the prospective set required. Do not force discovery families into confirmation.

---

## Task W0.5 — Claim–evidence matrix

Create:

```text
docs/registry/claim_evidence_matrix.json
docs/registry/claim_evidence_matrix.md
```

Required fields:

```text
claim_id
claim_text
claim_level
required_evidence
current_evidence_ids
current_estimate
family_count
model_count
discovery_or_confirmation
human_validation_dependency
status
allowed_wording
prohibited_wording
missing_evidence
required_next_experiment
consequence_if_null
paper_section
```

Minimum claims:

- behavioural counterfactual sensitivity exists;
- hidden states predict family-level sensitivity;
- signal is not merely prompt surface;
- signal adds information beyond output-only evidence;
- signal adds information beyond generic correctness representations;
- Qwen H11 supplies a localized sufficiency contribution;
- Qwen H11 is partially necessary;
- Llama H2 replicates on a Llama-valid prospective panel;
- variable renaming preserves sensitivity and causal effect;
- donor controls show specificity;
- Cue C constitutes a boundary or distinct mechanism;
- external natural-family transfer;
- upstream partial pathway;
- selective correction.

No current claim may be marked fully confirmed if it depends on families lacking required independent human validation.

---

## Task W0.6 — Experiment-card and gate system

Create:

```text
docs/experiment_cards/TEMPLATE.md
schemas/experiment_card.schema.json
scripts/stage13/validate_experiment_card.py
```

Every confirmatory job card must specify:

- scientific question;
- alternative and plausible null;
- claim level;
- independent unit;
- exact data and split hashes;
- model revision;
- frozen site/direction;
- inclusion and exclusion rules;
- primary and secondary outcomes;
- controls;
- statistical test;
- multiple-comparison handling;
- success, redesign, and stop thresholds;
- allowed claim if successful;
- allowed conclusion if null;
- compute estimate;
- output path;
- authorizing PI approval field.

A confirmatory Slurm script must refuse launch unless its card validates and contains approval.

---

## Wave 0 gate

Create:

```text
docs/stage13/wave0_gate_report.md
results/stage13/wave0/wave0_gate.json
```

Wave 0 passes only when:

- every paper-eligible result has traceable provenance;
- every ambiguous historical result is resolved or demoted;
- canonical family and variant tables validate;
- authority audit has no unresolved critical issue;
- discovery/confirmation status is explicit;
- claim matrix has no claim without evidence status;
- registry verification passes;
- no authoritative result relies solely on a partial, zero-row, or superseded artifact.

After Wave 0, stop and report before launching confirmatory work.

---

# 5. WAVE 1 — Benchmark integrity and human-validation preparation

Wave 1 software work may proceed in parallel with Wave 0. Final human validation remains a human process.

---

## Task W1.1 — Solver certificate audit and mutation testing

Create:

```text
scripts/stage13/run_solver_mutation_tests.py
results/stage13/benchmark_integrity/mutation_test_records.jsonl
results/stage13/benchmark_integrity/mutation_test_summary.json
```

### Do not assume every mutation is universally applicable

Define each mutation operator with:

- applicability precondition;
- intended invalidity;
- expected verifier response;
- reason it may be non-applicable;
- manual-review requirement.

Operators may include:

- insert cue into governing expression;
- remove a necessary assumption;
- sign inversion;
- replace a governing variable with cue;
- ask for a different target quantity;
- introduce a genuinely relevance-changing constraint;
- dimensional corruption;
- alter a frame assumption;
- change a boundary condition.

Do not treat “same units” alone as making a variable physically relevant.

### Controls

Include:

- **negative mutations:** scientifically invalid changes that should be rejected;
- **positive mutations:** semantics-preserving changes that should remain accepted;
- **no-op controls:** exact semantic equivalents.

Measure mutation score by operator and applicable-family count.

A failed natural-language assumption mutation may indicate that the symbolic verifier is not designed to validate prose semantics, not necessarily that the solver is broken. Record verifier coverage boundaries honestly.

---

## Task W1.2 — Answer parser audit

The coding agent must not create “manual ground truth” labels itself.

### Step A — Candidate set generation

Create:

```text
docs/validation/parser_audit_candidates.jsonl
```

Sample actual Qwen, Llama, and DeepSeek outputs, plus carefully designed edge cases, covering:

- integers and decimals;
- scientific notation;
- fractions;
- equivalent units;
- multiple numbers;
- rounding boundaries;
- correct number with wrong units;
- refusals;
- long prose;
- LaTeX;
- ambiguous final answers;
- model-specific formats.

Include raw output, canonical answer, expected unit, model, family, and blank human-label fields.

### Step B — Human labeling

Create instructions and a label schema. Do not fill the labels.

### Step C — Audit after labels exist

Create:

```text
scripts/stage13/run_parser_audit.py
```

Report:

- extraction accuracy;
- normalized-answer accuracy;
- false-accept rate;
- false-reject rate;
- unit error rate;
- ambiguity rate;
- per-format and per-model results;
- bootstrap intervals.

All tolerance rules must be explicit and versioned.

Flag affected families in the canonical evidence table.

---

## Task W1.3 — Leakage and split audit

Create:

```text
scripts/stage13/run_leakage_audit.py
results/stage13/benchmark_integrity/leakage_audit.json
results/stage13/benchmark_integrity/leakage_review.csv
```

Use multiple detectors:

1. canonical symbolic-expression hash;
2. variable-renaming-invariant AST/graph hash;
3. masked rendering-skeleton hash;
4. cue-insertion-template hash;
5. numerical-instantiation sibling detection;
6. lexical near-duplicate similarity;
7. semantic/template similarity for human review.

Report exact duplicates separately from near-duplicate candidates.

Do not hard-code expansion IDs when a manifest can identify them.

Any cross-split near duplicate must be reviewed and resolved before confirmatory use.

---

## Task W1.4 — Balance and confound audit

Create:

```text
scripts/stage13/run_balance_audit.py
results/stage13/benchmark_integrity/balance_audit.json
```

At family level, evaluate associations between sensitivity and:

- domain;
- cue type;
- answer sign and magnitude;
- prompt length;
- token count;
- number count;
- variable count;
- equation count;
- unit-token count;
- base correctness;
- entropy;
- answer format;
- source/template cluster.

Use:

- descriptive distributions;
- standardized effect sizes;
- Pearson and Spearman correlations where appropriate;
- grouped cross-validated single-feature AUROC;
- grouped cross-validated combined surface baseline;
- corrected significance tests for multiple confounds.

A high confound AUROC is not solved merely by mentioning it. It requires matching, conditioning, split redesign, or claim narrowing.

---

## Task W1.5 — Human-validation package

### Critical blinding correction

The first-pass validator packet must **not** reveal:

- the designated cue;
- the intended governing law;
- the solver derivation;
- the canonical answer;
- model outputs;
- sensitivity labels;
- probe or causal results.

Showing these before independent judgment would bias validators.

### Two-pass validation design

**Pass 1 — Independent physics judgment**
Validators see all natural-language family members and independently:

- solve the problem;
- identify governing law;
- identify relevant variables;
- identify any non-governing variable;
- assess assumptions;
- assess answer invariance;
- assess semantic equivalence;
- flag ambiguity.

**Pass 2 — Certificate verification**
After Pass 1 is submitted and locked, validators see the proposed cue, solver derivation, and certificate, then assess whether the certificate is correct.

### Deliverables

Create:

```text
docs/validation/validator_handbook.md
docs/validation/qualification_test.md
docs/validation/qualification_answer_key_PRIVATE.md
docs/validation/annotation_schema.json
docs/validation/validation_status.csv
scripts/stage13/generate_validation_packets.py
scripts/stage13/compute_validation_agreement.py
```

Calibration examples should come from a dedicated calibration bank, not confirmatory benchmark families. Include valid and deliberately invalid examples.

Generate separate blinded packets for each validator. The second validator must not see the first validator’s responses.

The tracking system must include:

```text
family_id
packet_version
validator_1_id
validator_1_assigned
validator_1_completed
validator_2_id
validator_2_assigned
validator_2_completed
critical_disagreement
adjudicator_id
adjudication_completed
repair_required
revalidation_required
final_verdict
notes
```

### Agreement outputs

After labels exist, compute:

- raw agreement;
- Cohen’s kappa or an appropriate alternative;
- agreement on cue relevance;
- agreement on invariance;
- agreement on assumption sufficiency;
- agreement by cue and domain;
- adjudication rate.

The coding agent must not mark a family valid until required human fields are present.

---

## Wave 1A pilot gate

Wave 1A passes when:

- handbook and qualification test are complete;
- 20–25 calibration/pilot families are assigned;
- the first-pass and second-pass blinding workflow works;
- agreement code is tested;
- parser candidate set is ready for human labeling;
- mutation and leakage tools run successfully.

This gate allows the PI to authorize carefully defined retrospective Wave 2 analyses. It does not mean the confirmatory benchmark is fully validated.

## Wave 1B final gate

Wave 1B passes only when:

- every confirmatory family has two independent completed reviews;
- all critical disagreements are adjudicated;
- repaired families are revalidated;
- no unresolved invariance or relevance dispute remains;
- final benchmark manifest and annotations are frozen.

Final paper claims and prospective confirmatory experiments require Wave 1B.

---

# 6. WAVE 2 — Monitoring confirmation specification

Do not execute until authorized after Wave 0 PASS and Wave 1A PASS.

Separate two products:

1. **Retrospective nested re-analysis:** quantifies what current data support without pretending it is untouched confirmation.
2. **Prospective frozen evaluation:** uses internal or external families not used for selection.

---

## Task W2.1 — Baseline taxonomy and incremental-value analysis

### Correct baseline categories

Do not call a generic correctness probe “non-activation.” It is activation-based.

Evaluate:

**A. Surface/output-only single-pass**
- TF–IDF/n-grams;
- prompt statistics;
- answer confidence;
- entropy;
- output-text or rationale classifier.

**B. Black-box multi-query**
- counterfactual two-query sensitivity;
- self-consistency;
- reflection/critic if available.

**C. Generic activation baseline**
- correctness probe;
- difficulty/error probe.

**D. PhysMon sensitivity activation monitor**
- frozen primary hidden-state monitor.

**E. Combined models**
- A only;
- A+B;
- A+B+C;
- A+B+C+D.

Report resource requirements so that a two-query oracle is not presented as equivalent to a single-pass pre-generation monitor.

### Cross-fitting requirements

All text vectorizers, dimensionality reduction, calibration, imputation, feature selection, regularization, and stacking must be fitted only inside training folds.

Use grouped nested cross-validation for retrospective analysis. For prospective evaluation, freeze all components before test evaluation.

### Family aggregation

Do not treat variant predictions as independent. Pre-specify a family-level aggregation, such as mean, maximum, or a multi-instance model, and select it only on discovery data.

### Metrics

Report:

- AUROC;
- AUPRC;
- log loss;
- Brier score;
- ECE with uncertainty;
- fixed-FPR sensitivity;
- fixed-recall precision;
- risk–coverage;
- paired family-bootstrap differences.

The key comparison is whether adding D improves A+B+C on held-out families.

---

## Task W2.2 — Silent-sensitivity analysis

Use precise strata:

- **Silent-correct sensitive:** all parsed variants correct, no answer flip, \(S^{lp}\ge 0.5\).
- **Stable-correct:** all parsed variants correct, no answer flip, \(S^{lp}<0.5\).
- **Correct-to-incorrect failure:** at least one cue edit changes a correct answer to incorrect.
- **Other visible flip:** answer changes but does not fit the above.
- **Stable-incorrect:** all parsed variants incorrect and \(S^{lp}<0.5\).
- **Unclassifiable:** insufficient parsed variants.

Compare silent-correct sensitive versus stable-correct only if both groups have adequate family counts. Report CIs and class counts. Do not use arbitrary AUROC thresholds without uncertainty.

---

## Task W2.3 — Correctness and entropy deconfounding

Use statistically valid cross-fitted methods:

1. conditional logistic or regression models;
2. residual prediction with nuisance models trained only on training folds;
3. matched analyses;
4. orthogonalization of hidden representations or probe directions using training-fold correctness directions;
5. silent-correct analysis;
6. combined predictive models.

Do not “subtract a direction from a scalar score.”

If using representation projection:

- estimate the correctness direction on training folds;
- project training and test activations using that frozen direction;
- train the sensitivity probe on projected training activations;
- evaluate on projected test activations.

---

## Task W2.4 — Prompt-position emergence

Use template metadata to define semantically aligned checkpoints.

At minimum:

- pre-cue;
- immediately post-cue;
- after governing information;
- question onset;
- final prompt token.

Run:

1. position-specific sensitivity probes;
2. frozen final-position direction applied across positions;
3. cue-identity probes;
4. correctness probes.

Interpret pre-cue prediction as possible family-structure or difficulty information, not impossible “future cue reading.”

Treat this as exploratory unless checkpoint definitions and probe selection were frozen prospectively.

---

# 7. WAVE 3 — Core causal confirmation specification

Do not execute without validated experiment cards and PI approval.

---

## Task W3.1 — Qwen H11 necessity

Define the receiver site and token positions exactly. Match the current sufficiency setup.

Test:

- mean replacement;
- stable-family replacement;
- zero ablation as an OOD stress control;
- low-rank direction removal learned on discovery data;
- random norm-matched subspaces;
- nearby heads and layers;
- stable families;
- unrelated tasks;
- general capability damage.

Use raw changes in \(S^{lp}\), correct-answer log-probability, answer accuracy, and normalized effects.

Do not call a component “necessary” based on an arbitrary 30% reduction. Use:

- effect direction;
- confidence interval;
- separation from controls;
- low collateral damage;
- replication on a frozen panel.

The allowed claim may be “partially necessary contributor.”

---

## Task W3.2 — Corrected bidirectional dose-response

The previous draft contained a donor/target direction ambiguity. Use the following definitions.

**Mitigation direction**
- target: naturally sensitive run;
- donor: matched stable or low-sensitivity run;
- increasing \(\alpha\) should reduce \(S^{lp}\), if the representation mitigates sensitivity.

**Induction direction**
- target: naturally stable run;
- donor: matched sensitive run;
- increasing \(\alpha\) should increase \(S^{lp}\), if the representation induces sensitivity.

Use:

\[
h(\alpha)=h_{\text{target}}+\alpha(h_{\text{donor}}-h_{\text{target}})
\]

with pre-specified \(\alpha\) values.

Report individual-family curves, monotonic trend tests, raw effects, accuracy, and overshoot. Do not rely only on normalized recovery.

---

## Task W3.3 — Llama-valid causal panel

The earlier H2 site was selected on a panel not cleanly Llama-confirmatory.

Build or identify a prospective Llama-positive panel that:

- is Llama-sensitive;
- has valid parsing;
- is independently validated;
- was not used to select H2;
- uses Llama-positive donor policies.

Keep knockout, ablation, and donor patching conceptually distinct. Name the exact intervention.

If fewer than a defensible number of eligible families exist, report insufficiency and construct new prospective families rather than making a strong replication claim.

---

## Task W3.4 — Llama miss analysis

Classify apparent misses into:

- not Llama-sensitive;
- parser/alignment failure;
- unstable denominator;
- Cue C or another subtype;
- genuine H2 miss;
- distributed effect.

Any alternate-head search on the original misses is exploratory. A secondary head must be confirmed on newly constructed and independently validated matched families.

---

# 8. WAVE 4 — Mechanistic deepening specification

---

## Task W4.1 — Diagnostic versus causal subspace

Do not define a “causal subspace” by optimizing reduction in the existing probe score. That would recover another diagnostic subspace.

Estimate:

- diagnostic probe direction;
- sensitive–stable contrast direction;
- actual causal subspace optimized using intervention effects on model outputs or behavioural sensitivity on discovery families.

Evaluate on held-out families.

Cross-ablation must include:

- remove diagnostic direction;
- remove causal subspace;
- random matched subspace;
- retain-only interventions only if they do not catastrophically destroy the residual stream;
- general-damage controls.

Report geometry and behavioural effects separately.

---

## Task W4.2 — Upstream circuit tracing

First localize the receiver precisely:

- layer;
- head;
- query position;
- attention pattern, value result, or projected output.

Use attribution methods only for candidate discovery. Verify top candidates with exact path or receiver-conditioned interventions.

Search both attention heads and MLPs, and do not assume the sender lies only at the cue token.

Required controls:

- random sender;
- nearby sender;
- unrelated-family patch;
- position-matched control;
- direct sender-to-output path check;
- knockout and rescue;
- joint intervention.

Use “partial causal pathway” only if the path explains a substantial, stable fraction of the receiver-mediated effect on held-out families. Because effects are nonlinear, define the coverage metric explicitly.

---

## Task W4.3 — Cue-factorial functional characterization

Five families are insufficient for a paper-level functional claim. Use a larger, stratified set across cue types and domains, subject to power and construction feasibility.

Manipulate factors orthogonally where possible:

- physical relevance;
- unit compatibility;
- magnitude;
- numerical proximity;
- position;
- syntactic prominence;
- lexical emphasis;
- repetition;
- variable naming;
- answer correlation.

Length-match deletions with neutral filler. Human-validate the resulting families.

Analyze with family-level mixed-effects or hierarchical models. A single manipulation does not prove a function. Compare competing hypotheses and report which are supported, falsified, or unresolved.

---

# 9. Running-job harvest policy

When pending jobs finish:

1. sync without overwriting prior artifacts;
2. register the exact job and array tasks;
3. validate row counts and completeness;
4. summarize on the correct model-positive panel;
5. mark as exploratory unless pre-authorized as confirmatory;
6. update claim matrix;
7. do not launch automatic follow-ups.

Do not claim:

- depth universality from two Qwen sizes;
- cross-architecture universality from a single Mistral site;
- DeepSeek mechanistic failure from an invalid or tiny panel.

Allowed wording should remain bounded, such as:

- “consistent relative-depth localization within tested Qwen checkpoints”;
- “no reliable single-head localization under the tested intervention and panel”;
- “reasoning-tuned model boundary remains unresolved.”

---

# 10. Documentation tasks

## DOC.1 — Decision-log synthesis

Regenerate every quoted number from authoritative raw artifacts before writing it.

Include:

- exact experiment IDs;
- family denominators;
- discovery/confirmation status;
- panel caveats;
- superseded interpretations;
- failed and null results.

Do not describe inhibitory heads as “mirrors” across architectures without direct functional evidence.

## DOC.2 — Confirmatory experiment cards

Cards must be committed and validated before job submission.

## DOC.3 — Checkpoint report

After Wave 0 and Wave 1A:

- report completed deliverables;
- list unresolved provenance;
- list unexpected nulls;
- list whether internal confirmation exists;
- propose the next authorized tasks;
- stop for review.

---

# 11. Required tests

At minimum, add tests for:

- registry schema validation;
- hash reproducibility;
- authority resolution;
- family/variant aggregation;
- no cross-split family leakage;
- grouped CV behavior;
- no vectorizer fit on test folds;
- parser edge cases;
- mutation-operator applicability;
- validation-packet blinding;
- experiment-card launch guard;
- no overwrite without flag;
- deterministic summary regeneration.

Use small fixtures rather than full model runs for unit tests.

---

# 12. Report-back format

Every report-back must include:

```text
task_id
status
git_commit
git_dirty
data_hash
family_manifest_hash
experiment_ids
n_families
n_variants
discovery_or_confirmation
human_validation_status
primary_estimate
95_percent_CI
control_estimates
unexpected_missingness
exclusions
output_paths
scientific_interpretation
claim_level
allowed_wording
prohibited_wording
next_gate
```

The Wave 0/1 checkpoint must report:

### Wave 0
- registry entries;
- authoritative entries;
- exploratory entries;
- superseded entries;
- unresolved provenance;
- canonical family rows;
- canonical variant rows;
- unexpected nulls;
- internal-confirmatory family count;
- claims confirmed/partial/missing.

### Wave 1
- applicable mutation counts and rejection rates by operator;
- positive-control acceptance rates;
- parser candidate count and human-label status;
- exact and near-duplicate leakage flags;
- strongest confound and grouped-CV estimate;
- validation packets generated;
- human pilot assignment and completion status.

Do not report a scientific number without its denominator, CI, experiment ID, and evidence status.

---

# 13. Prior-audit candidate anchors to verify

The following are not instructions to force the registry to match. They are expected anchors requiring raw-artifact verification:

- Qwen L16H11 full single-head sweep near 1.848 normalized recovery on a 20-family discovery panel.
- Qwen mean-state monitor near 0.760 at L18.
- Qwen per-variant monitor near 0.747 at L16.
- Llama L21H2 near 1.847 on a Qwen-selected 20-family panel, with 14/20 above the stated recovery threshold.
- Corrected variable-renaming monitor near 0.667 family-level and 0.688 variant-level.
- Donor-on-renamed same-answer and stable controls reported as 0.0 mean recovery.
- Expansion inference near 0.820 family-level on 15 families.
- Cue C probe and causal results materially weaker than Cue A/B.
- H15 gating reported null.
- Qwen-3B, Qwen-14B, Mistral, and DeepSeek full-sweep work may be incomplete or pending.

If any anchor disagrees with authoritative artifacts, record the discrepancy and follow the authority hierarchy.

---

# 14. Final instruction for the first coding-agent session

Implement only:

1. PF.1;
2. W0.1–W0.6;
3. W1.1–W1.5 software and materials;
4. tests;
5. Wave 0 and Wave 1A reports.

Do not execute W2–W4 confirmatory experiments in the same session.

At completion, provide:

- concise summary of changes;
- files created or modified;
- tests run and results;
- unresolved questions;
- registry/gate status;
- exact commands for the PI to review;
- proposed next tasks requiring approval.

Scientific honesty is the success criterion. A negative, incomplete, or contaminated result must be preserved and labeled correctly rather than repaired into a positive finding.
