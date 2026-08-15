# PhysMon Stage 13 — Evidence Foundation Remediation Brief, Version 5.0

**Purpose:** Complete the next bounded CPU-only remediation cycle required before any Wave 2–4 scientific execution is authorized.

**Primary objective:** Replace remaining placeholder, self-confirming, or repository-incomplete checks with scientifically valid implementations, and correct the governing Part II document so that all future agents begin from an accurate factual record.

**Governing documents:**
1. PhysMon Research Proposal and supplementary documentation
2. PhysMon Part II — Next-Phase Scientific and Experimental Plan
3. PhysMon Stage 13 Controlled Execution Brief v2
4. PhysMon Stage 13 Remediation Briefs v3 and v4
5. Latest external audit of the Stage 13 v4 outputs

**Scope:** CPU-only Wave 0 / Wave 1A remediation.

**Explicitly forbidden in this cycle:**
- No Sharanga login
- No `ssh`
- No `sbatch`
- No `srun`
- No Slurm submission
- No GPU execution
- No Wave 2 monitoring confirmation
- No Wave 3 causal confirmation
- No Wave 4 mechanistic experiments
- No new head/layer/site selection
- No new threshold selection
- No new causal-panel construction
- No automatic follow-up jobs
- No promotion of exploratory evidence to confirmatory evidence

---

# 0. Authoritative current status

Treat the project status as:

```text
Wave 0:
FAIL — HISTORICAL INVENTORY AND AUTHORITY UNRESOLVED

Wave 1A software/materials:
FAIL — MUTATION, CERTIFICATE, VALIDATION, PARSER,
LEAKAGE, AND CONFOUND WORK INCOMPLETE

Human pilot:
NOT READY

Paper eligibility:
FALSE

Permission for Wave 2:
FALSE
```

Do not preserve or restate any stronger status unless every content-based gate defined in this brief is satisfied.

The most recent audit established:

1. The renamed donor-control zero-row correction is valid.
2. The current mutation “success rates” are assigned, not measured.
3. The current certificates are heuristic placeholders, not solver-derived certificates.
4. The validator handbook and qualification examples are placeholders.
5. The 25-family validation pilot is not domain/cue stratified.
6. The parser candidate set is model-balanced but not category/domain balanced.
7. The leakage review workload is inflated by within-family and expected derived-parent pairs.
8. The historical-registry coverage denominator is invalid.
9. The authority audit remains registry-linked rather than repository-wide.
10. The canonical evidence table is still mostly behavioural.
11. The claim matrix remains largely unpopulated.
12. The governing Part II document still contains the known false renamed-donor-control statement and must be corrected.

---

# 1. Mandatory execution contract

## 1.1 Read before editing

Before changing any file:

1. Read all governing documents.
2. Read the latest external audit in full.
3. Read the repository `README.md`.
4. Read the current decision log.
5. Read all Stage 13 gate reports.
6. Inspect all current Stage 13 scripts, tests, manifests, registry files, evidence tables, validation materials, and authority-audit outputs.
7. Inspect the Part II LaTeX source and build instructions.
8. Inspect the benchmark family/template schemas and solver/verifier implementation.
9. Inspect Slurm scripts and historical logs read-only.
10. Inspect Git branch, commit, dirty state, and untracked files.

Create:

```text
docs/stage13/stage13_v5_preflight.md
```

The preflight must list:

- repository root;
- branch and commit;
- dirty/untracked files;
- current Wave 0 and Wave 1A statuses;
- Part II source path and PDF path;
- benchmark/template schemas;
- solver/verifier entry points;
- current mutation implementation;
- current certificate-generation implementation;
- current parser candidate distribution;
- current validation pilot composition;
- current leakage pair categories;
- current registry expected-experiment construction;
- current authority-scan scope;
- current canonical evidence populated fields;
- current claim-matrix populated fields;
- exact files to modify;
- unresolved ambiguities.

If the Part II source, canonical manifest, solver/verifier, or repository root cannot be identified confidently, stop and ask for clarification.

## 1.2 No fabrication

Never invent:

- historical job IDs;
- model revisions;
- raw row counts;
- commands;
- hashes;
- solver equations;
- certificate derivations;
- parser labels;
- validator labels;
- experiment authority;
- confirmation status.

If a structured physics specification is missing, record the family as `certificate_generation_blocked` rather than generating a plausible-looking heuristic certificate.

## 1.3 Preserve raw evidence

Do not overwrite or delete:

- old gate files;
- invalid balance-audit files;
- assigned mutation records;
- heuristic certificate drafts;
- placeholder handbook/test versions;
- zero-row donor artifacts;
- stale summaries;
- partial outputs;
- nested archives.

Create new versioned artifacts and supersession links.

## 1.4 Scientific unit

The canonical family is the independent unit.

The benchmark contains:

```text
155 canonical families
```

Variable-renaming examples remain derived variants.

## 1.5 Sharanga compatibility

This cycle is local and CPU-only.

Maintain repository-relative paths and compatibility with:

```text
local repository
Sharanga repository: ~/PhysMons/
```

Do not hard-code personal local paths or Sharanga scheduling parameters.

Do not execute sync commands automatically.

At the end, provide safe future commands:

```bash
make sync-up
make sync-check
make sync-down
```

---

# 2. Correct the governing Part II document

## Task V5.1 — Locate and version the Part II source

Identify the current Part II LaTeX source and PDF.

Create a new controlled version:

```text
PhysMon Part II version 1.2
```

Preserve version 1.1.

Update the revision record with:

```text
Version 1.2
Reason: Corrected renamed donor-control status after raw-artifact audit.
```

## Task V5.2 — Correct renamed donor-control statements

Search the complete Part II source for all statements implying:

- donor-on-renamed same-answer completed;
- donor-on-renamed stable completed;
- measured 0.0 mean recovery;
- 100% specificity;
- revised pooled specificity incorporating these runs.

Replace with:

> The renamed donor-control jobs produced zero evaluable target–donor rows. Their original summaries defaulted to zero recovery, but this is not a measured scientific null. These controls remain incomplete and are excluded from specificity claims until a valid rerun is performed.

Update:

- current evidence baseline;
- incomplete/non-authoritative evidence;
- governance notes;
- risk register if relevant;
- claim matrix examples;
- any percentage or specificity statement.

## Task V5.3 — Recompile and verify

Recompile the PDF.

Create:

```text
docs/proposals/PhysMon_Part_II_v1.2.tex
docs/proposals/PhysMon_Part_II_v1.2.pdf
docs/proposals/PhysMon_Part_II_v1.2_revision_notes.md
```

If repository conventions use other locations, follow them and document paths.

Verification:

- PDF compiles without errors;
- donor-control language is corrected everywhere;
- old version is preserved;
- current governing-document pointer is updated;
- decision log references v1.2.

---

# 3. Replace assigned mutation outcomes with actual verification

## Task V5.4 — Supersede invalid mutation results

Mark prior v3 mutation results as:

```text
superseded_assigned_outcomes_not_verified
```

Do not report:

- negative rejection rate 1.0;
- positive acceptance rate 1.0;
- 225/225 verified;

from the existing implementation.

## Task V5.5 — Identify real verifier interface

Inspect the repository to identify:

- structured family/template representation;
- symbolic answer expression;
- solver entry point;
- certificate verifier;
- invariance checker;
- dimensional checker;
- assumption representation.

Create:

```text
docs/stage13/mutation_verifier_integration.md
```

Document:

- exact callable functions;
- accepted input schemas;
- output schemas;
- mutation-safe fields;
- unsupported mutation classes.

If no reusable verifier exists, implement the smallest valid adapter around the existing solver rather than assigning outcomes.

## Task V5.6 — Implement actual mutation execution

Create or revise:

```text
src/physmon/validation/mutation_operators.py
src/physmon/validation/mutation_executor.py
scripts/stage13/run_solver_mutation_tests.py
```

A mutation counts as executed only if:

1. the original structured family/certificate is loaded;
2. a real field/expression/assumption is changed;
3. the mutated object differs from the original;
4. the relevant solver/verifier is called;
5. the actual verifier output is recorded;
6. the expected and actual outcomes are compared.

### Minimum negative mutations

Implement at least three genuine negative operators where structurally supported:

1. governing-expression sign inversion;
2. replacement of a governing variable with the cue;
3. dimensional corruption;
4. target-quantity change;
5. assumption removal/change.

### Minimum positive mutations

Implement at least three genuine positive operators:

1. algebraically equivalent expression;
2. semantics-preserving variable renaming with consistent mapping;
3. equivalent unit formatting;
4. harmless formatting change that actually changes serialization.

### Stratified execution set

Use at least 30 canonical families stratified across:

- mechanics;
- electrostatics/circuits;
- available cue types;
- original and expansion families;
- multiple template classes.

If a mutation operator is unsupported for a family, record:

```text
coverage_not_supported
```

Do not coerce applicability.

## Task V5.7 — Mutation outputs

Create:

```text
results/stage13/benchmark_integrity/mutation_test_records_v5.jsonl
results/stage13/benchmark_integrity/mutation_test_summary_v5.json
```

Summary fields:

```text
operator_id
operator_type
n_considered
n_applicable
n_executed
n_verified
n_expected_reject
n_actual_reject
n_expected_accept
n_actual_accept
rejection_rate
acceptance_rate
n_unsupported
n_execution_failures
```

A gate may pass only if at least one genuine negative and one genuine positive operator are actually verified.

---

# 4. Build solver-derived certificate infrastructure

## Task V5.8 — Define structured physics specification

Inspect the benchmark family schema.

Where possible, create or normalize a structured specification containing:

```text
family_id
domain
template_id
governing_law_id
governing_equations
symbol_table
relevant_variables
designated_cue
assumptions
target_quantity
symbolic_answer
canonical_answer
units
variant_bindings
```

Do not infer relevant variables from generic word-token extraction.

## Task V5.9 — Certificate generator

Create:

```text
src/physmon/validation/certificate_generator.py
scripts/stage13/generate_solver_certificates.py
schemas/solver_certificate_v2.schema.json
```

A valid certificate must contain:

- governing law;
- structured governing equations;
- symbol table;
- relevant variables;
- designated cue;
- stated assumptions;
- substituted values;
- explicit symbolic derivation;
- computed canonical answer;
- dimensional check;
- invariance proof/check across variants;
- numeric spot checks;
- generator version;
- source template;
- verification result;
- limitations.

### Example quality standard

A valid constant-acceleration certificate must show something like:

```text
v = v0 + at
v0 = 5.0 m/s
a = 2.0 m/s^2
t = 3.0 s
v = 5.0 + 2.0 * 3.0 = 11.0 m/s
```

It must not merely say “apply the law.”

## Task V5.10 — Pilot certificate eligibility

Generate certificates only for families with sufficient structured information.

For each selected family, classify:

```text
certificate_generated
certificate_generation_blocked
certificate_verification_failed
```

Do not fill missing equations heuristically from prompt keywords.

## Task V5.11 — Pass 2 packets

Generate Pass 2 packets only from verified certificates.

Create:

```text
docs/validation/stage13_validation_packet_pass2_v5.jsonl
docs/validation/certificates_v5/<family_id>.json
```

Each Pass 2 packet must expose the actual certificate fields.

---

# 5. Rebuild the human-validation pilot properly

## Task V5.12 — Stratified pilot selection

Do not use the first 25 manifest rows.

Create a deterministic stratified pilot of 24–30 families covering:

- mechanics;
- electrostatics/circuits;
- each cue type represented in the benchmark;
- original and expansion sets;
- multiple template clusters;
- easy and difficult cases;
- known borderline/repair candidates;
- representation/frame cases where available.

Create:

```text
docs/validation/pilot_selection_v5.csv
```

Fields:

```text
family_id
domain
cue_type
template_cluster
original_or_expansion
difficulty_or_risk_stratum
selection_reason
certificate_status
```

## Task V5.13 — Pass 1 packets

Generate all natural-language variants for each selected family.

Do not show:

- designated cue;
- governing law;
- canonical answer;
- solver derivation;
- model outputs;
- sensitivity labels;
- monitor or causal results.

Create:

```text
docs/validation/stage13_validation_packet_pass1_v5.jsonl
```

## Task V5.14 — Real calibration bank

Create a dedicated calibration bank separate from confirmatory families.

It must include at least 15 worked examples with:

- complete problem text;
- all relevant variants;
- expected physics judgment;
- governing law;
- relevant variables;
- designated cue;
- answer invariance;
- why the case is valid or invalid;
- borderline reasoning;
- repair recommendation where applicable.

Include:

- valid irrelevant variable;
- subtly relevant variable;
- missing assumption;
- ambiguous target;
- semantic drift;
- valid/invalid frame transformation;
- dimensional inconsistency;
- unit-compatible but relevant variable;
- unnatural wording;
- invalid solver derivation;
- valid representation transformation.

Create:

```text
docs/validation/calibration_bank_v5.md
docs/validation/calibration_bank_v5.jsonl
```

## Task V5.15 — Real qualification test

Create 12–15 complete cases with actual prompts and questions.

Create:

```text
docs/validation/qualification_test_v5.md
docs/validation/qualification_answer_key_DRAFT_REQUIRES_PI_REVIEW_v5.md
```

Each answer-key entry must explain the physics and expected judgment.

## Task V5.16 — Validator handbook

Create:

```text
docs/validation/validator_handbook_v5.md
```

The handbook must reference the actual calibration bank and explain:

- pass 1;
- pass 2;
- independence;
- relevance;
- invariance;
- assumptions;
- semantic equivalence;
- naturalness;
- difficulty shifts;
- repair/exclusion;
- adjudication;
- revalidation.

## Task V5.17 — Typed annotation schema and forms

Create:

```text
docs/validation/annotation_schema_v5.json
docs/validation/annotation_form_pass1_v5.md
docs/validation/annotation_form_pass2_v5.md
```

Define types, enums, required fields, confidence scales, verdict options, and missingness rules.

---

# 6. Repair the balance/confound audit

## Task V5.18 — Missingness handling

Do not convert missing correctness to false/zero.

For every feature, record:

```text
n_available
n_missing
missing_reason
included_in_model
```

If entropy or correctness is unavailable, exclude it from that model and report it as unavailable.

## Task V5.19 — Separate confound classes

Report:

- strongest numeric confound;
- strongest categorical confound;
- strongest template-structure confound.

Include:

- cue type;
- domain;
- template cluster;
- original/expansion;
- prompt length;
- number/variable/equation counts;
- answer magnitude;
- available correctness;
- available entropy.

For categorical associations, compute:

- chi-square or appropriate exact test;
- Cramér’s V;
- corrected p-values.

## Task V5.20 — Two grouped-CV regimes

Run:

### Regime A — family-row stratified CV

Useful as a baseline because rows are family-level.

### Regime B — template-held-out/grouped CV

Group by normalized template/symbolic cluster so template siblings do not cross folds.

All preprocessing must be fold-local.

Report both.

## Task V5.21 — Proper permutation test

For each permutation:

1. permute labels;
2. recreate folds under the fixed grouping rule;
3. refit preprocessing;
4. refit classifier;
5. regenerate OOF predictions;
6. calculate AUROC.

Do not permute labels against fixed predictions only.

## Task V5.22 — Outputs

Create:

```text
results/stage13/benchmark_integrity/balance_audit_v5.json
results/stage13/benchmark_integrity/balance_audit_v5_family_folds.csv
results/stage13/benchmark_integrity/balance_audit_v5_template_folds.csv
results/stage13/benchmark_integrity/balance_audit_v5_predictions.csv
```

---

# 7. Rebuild the parser candidate set

## Task V5.23 — Category and domain quotas

Create at least 140 unique candidates.

Target:

- Qwen: at least 35;
- Llama: at least 35;
- DeepSeek: at least 35;
- designed edge cases: at least 35.

Use multiple unique families per model.

Category minimums:

- integers/decimals: 15;
- scientific notation: 10;
- fractions: 10;
- equivalent units: 15;
- multiple numbers: 15;
- rounding boundaries: 10;
- wrong units: 10;
- refusals/hedges: 10;
- long prose: 10;
- LaTeX: 10;
- ambiguous final answer: 10;
- model-specific quirks: 10.

A candidate may carry multiple categories, but report unique category coverage.

Domain quotas:

- mechanics;
- electrostatics/circuits;
- any available additional physics domains;
- synthetic mixed edge cases.

## Task V5.24 — Grounding fields

Every candidate must include:

```text
candidate_id
model_id
family_id_or_edge_case_id
domain
raw_output
canonical_answer
expected_unit
tolerance_rule
acceptable_equivalent_forms
categories
human_extracted_answer
human_normalized_answer
human_correctness
human_ambiguity
notes
```

Human fields remain blank.

Designed edge cases must have explicit reference answers and units where applicable.

## Task V5.25 — Outputs

Create:

```text
docs/validation/parser_audit_candidates_v5.jsonl
docs/validation/parser_candidate_coverage_v5.json
docs/validation/parser_labeling_instructions_v5.md
```

---

# 8. Refine leakage auditing

## Task V5.26 — Remove expected relations from unresolved workload

Classify pairs as:

```text
within_same_canonical_family_expected
derived_parent_expected
exact_cross_family_duplicate
masked_structural_cross_family_candidate
lexical_cross_family_candidate
semantic_template_candidate
cross_split_candidate
```

Do not count:

- within-family variant pairs;
- known derived-parent relations;

as unresolved leakage candidates.

## Task V5.27 — Implement all declared detectors

Actually compute:

- exact prompt hash;
- number-masked hash;
- symbolic expression hash;
- variable-renaming-invariant structural hash;
- cue-template hash;
- numeric sibling relation;
- lexical similarity;
- semantic/template similarity if an existing local embedding method is available.

Do not claim a detector was used unless its output contributes to the record.

## Task V5.28 — Connected components

Construct connected components only over cross-family candidate edges requiring review.

Report:

- expected within-family pairs;
- expected derived-parent pairs;
- cross-family candidate pairs;
- cross-split pairs;
- connected components requiring review.

Create:

```text
results/stage13/benchmark_integrity/leakage_audit_v5.json
results/stage13/benchmark_integrity/leakage_review_v5.csv
```

---

# 9. Repair registry coverage and authority discovery

## Task V5.29 — Build normalized expected-run inventory

Do not use:

- stage numbers;
- Slurm template filenames;
- numeric strings in prose;

as experiments.

Create:

```text
results/stage13/wave0/expected_historical_runs_v5.jsonl
docs/registry/expected_historical_runs_v5.md
```

Each expected item must correspond to one actual or intended run/configuration and include:

```text
expected_run_id
source
stage
experiment_family
model
panel
config_or_script
job_id_if_known
result_directory_if_known
evidence_paths
confidence
```

Sources:

- decision-log entries;
- actual Slurm output logs;
- result directories;
- summary/raw artifacts;
- run manifests;
- known experiment cards.

## Task V5.30 — Recompute coverage

Compute:

```text
n_expected_runs
n_registered_runs
n_unregistered_runs
n_irrecoverable_runs
coverage_fraction
```

Only after deduplication and normalization.

## Task V5.31 — Repository-wide artifact scan

Scan the full configured results roots, not only paths already in the registry.

For every candidate artifact:

- hash;
- classify;
- map to experiment/run;
- detect orphan;
- detect summary/raw relationships;
- detect zero-row outputs;
- detect partial/full/corrected variants.

Create:

```text
docs/registry/artifact_authority_audit_v5.json
docs/registry/artifact_authority_audit_v5.md
results/stage13/wave0/orphan_artifacts_v5.csv
```

## Task V5.32 — Authority rules

A result cannot be authoritative when:

- provenance is partial;
- raw data are missing;
- row count is zero;
- panel is ambiguous;
- corrected/superseded relationship is unresolved;
- summary cannot be traced.

---

# 10. Populate canonical evidence and claim matrix

## Task V5.33 — Ingest existing authoritative evidence

Populate available fields from resolved experiments:

- primary monitor scores;
- monitor site/layer;
- entropy/confidence if available;
- black-box baseline;
- CoT baseline;
- rationale baseline;
- correctness probe;
- causal-panel eligibility;
- causal site;
- intervention effects;
- control effects;
- damage metrics.

Every non-null value must cite source experiment IDs.

## Task V5.34 — Null-reason taxonomy

Use:

```text
not_applicable
not_measured
source_not_ingested
source_unresolved
source_missing
excluded_ineligible
parser_invalid
human_validation_pending
unexpected_missing
```

Verification must report counts by field and null reason.

## Task V5.35 — Populate claim matrix

For each claim, populate:

- current estimate;
- CI if available;
- family count;
- model count;
- experiment IDs;
- artifacts;
- panel caveat;
- discovery/confirmation status;
- allowed wording;
- prohibited wording;
- missing evidence;
- next required experiment.

Do not assign 155 families to claims using 20-, 15-, or 10-family panels.

---

# 11. Gate logic

## Task V5.36 — Wave 0 gate v5

Create:

```text
results/stage13/wave0/wave0_gate_v5.json
docs/stage13/wave0_gate_v5_report.md
```

Wave 0 may remain failed.

It passes only if:

- governing Part II is corrected;
- expected-run inventory is normalized;
- registry coverage is substantive;
- critical authority issues are zero;
- canonical evidence links to source experiments;
- claim matrix is populated;
- no authoritative result has partial provenance.

## Task V5.37 — Wave 1A software/materials gate v5

Create:

```text
results/stage13/benchmark_integrity/wave1a_gate_v5.json
docs/stage13/wave1a_gate_v5_report.md
```

Wave 1A software/materials passes only if:

- actual mutation verification occurred;
- actual certificates exist;
- pilot is stratified;
- calibration examples are worked examples;
- qualification cases are complete;
- parser set meets model/category/domain quotas;
- balance audit has valid missingness handling and template-held-out CV;
- leakage workload excludes expected relations;
- annotation schema/forms are usable.

Human pilot remains:

```text
PENDING
```

until actual humans are recruited and assigned.

Always set:

```text
permission_for_wave2 = false
```

---

# 12. Tests

Add tests that verify scientific substance, not only field presence.

Minimum tests:

1. mutation object differs from original;
2. verifier is actually invoked;
3. assigned `actual=expected` logic is impossible;
4. negative mutation can fail verification;
5. positive mutation can pass verification;
6. certificate relevant variables come from structured symbol table;
7. certificate contains substituted numeric derivation;
8. invariance checks recompute rather than repeat stored answers;
9. pilot contains multiple domains and cue types;
10. calibration examples include full problem and explanation;
11. qualification cases include full prompts;
12. missing correctness remains missing, not false;
13. template-held-out groups do not cross folds;
14. permutation test refits the pipeline;
15. parser quotas are enforced;
16. designed parser cases include canonical answers;
17. within-family leakage pairs excluded from review count;
18. derived-parent pairs excluded from unresolved count;
19. expected-run inventory rejects stage numbers/template names as runs;
20. authority scan finds orphan artifacts;
21. canonical non-null fields cite experiment IDs;
22. claim family counts match source panels;
23. Part II v1.2 no longer contains false donor-control wording.

Run:

```bash
.venv/bin/ruff check scripts/stage13 src/physmon tests/stage13
PYTHONPATH=src python3 -m pytest tests/stage13
PYTHONPATH=src python3 -m pytest
```

---

# 13. Report-back format

## A. Scope
- confirm no Sharanga, Slurm, GPU, or Wave 2–4 work.

## B. Part II correction
- source path;
- PDF path;
- version;
- all corrected statements.

## C. Mutation verification
- operators;
- families;
- actual verifier calls;
- measured rates;
- unsupported classes.

## D. Certificates
- generated;
- blocked;
- failed;
- example derivation;
- verification method.

## E. Human-validation materials
- pilot composition by domain/cue/template;
- calibration examples;
- qualification cases;
- Pass 1 and Pass 2 counts;
- pilot readiness.

## F. Balance/confound
- missingness;
- numeric confounds;
- categorical confounds;
- template confounds;
- family-CV result;
- template-held-out result;
- refitted permutation p-value.

## G. Parser set
- counts by model;
- category;
- domain;
- unique families;
- label status.

## H. Leakage
- expected within-family pairs;
- expected derived-parent pairs;
- cross-family candidates;
- cross-split candidates;
- connected review clusters.

## I. Registry/authority
- expected runs;
- registered;
- coverage;
- orphans;
- critical unresolved;
- zero-row findings.

## J. Canonical evidence
- populated fields;
- null reasons;
- source links.

## K. Claims
- estimates populated;
- panel counts;
- downgraded claims;
- missing claims.

## L. Gates
- Wave 0;
- Wave 1A software/materials;
- human pilot;
- Wave 2 permission.

## M. Tests
- exact commands and results.

## N. Sharanga readiness
- repository-relative paths;
- no jobs run;
- safe future sync commands.

Stop after reporting.

---

# 14. Final instruction

Do not optimize for a green gate.

A mutation is not verified unless a real mutated object is passed through a real verifier.

A certificate is not real unless it contains a structured derivation and independently recomputed checks.

A calibration example is not real unless it contains a complete case and explanation.

A coverage percentage is not meaningful unless the denominator represents actual runs.

A truthful failure is scientifically preferable to a fabricated success.
