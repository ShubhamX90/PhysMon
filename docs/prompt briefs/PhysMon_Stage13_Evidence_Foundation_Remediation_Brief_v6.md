# PhysMon Stage 13 — Evidence Foundation Remediation Brief, Version 6.0

**Purpose:** Correct the remaining scientific, statistical, validation, provenance, and governance failures identified in the latest audit of the v5 remediation cycle.

**Scope:** CPU-only Wave 0 / Wave 1A remediation.

**Primary objective:** Produce a trustworthy evidence foundation, a genuinely pilot-ready validation package, a scientifically valid benchmark-integrity audit, and an accurate governing-document correction—without running any new model experiments.

**Governing documents:**
1. PhysMon Research Proposal and supplementary documentation
2. Complete PhysMon Part II — Next-Phase Scientific and Experimental Plan, version 1.1
3. Mandatory donor-control erratum/correction note
4. Stage 13 Controlled Execution Brief v2
5. Stage 13 Remediation Briefs v3, v4, and v5
6. Latest external audit of the Stage 13 v5 outputs

---

# 0. Authoritative current status

Treat the project status as:

```text
Wave 0:
FAIL — RUN INVENTORY, AUTHORITY, CANONICAL EVIDENCE,
AND CLAIM MAPPING INCOMPLETE

Wave 1A software/materials:
FAIL — GOVERNING-DOCUMENT CORRECTION, LABEL CONSTRUCTION,
CERTIFICATE COVERAGE, VALIDATION MATERIALS, PARSER DESIGN,
MUTATION SEMANTICS, AND LEAKAGE REVIEW INCOMPLETE

Human pilot:
NOT READY

Paper eligibility:
FALSE

Permission for Wave 2:
FALSE
```

Do not preserve the v5 `Wave 1A PASS`.

The latest audit established:

1. The zero-row donor-control correction is valid.
2. The v5 mutation system now invokes the real `SymbolicVerifier`, but several mutation names overstate what they test.
3. The current certificates are structured machine-generated drafts, not full publication-grade certificates.
4. Frame-rendering/unit-equivalence families are not independently conversion-verified.
5. The current Part II “v1.2” is a one-page correction notice, not a complete revised Part II document.
6. The balance/confound audit incorrectly treats missing expansion-family \(S^{lp}\) labels as negative labels.
7. The parser set is not truly unique or category-balanced despite satisfying superficial quotas.
8. The validator handbook, calibration bank, and qualification test are not pilot-ready.
9. Leakage detectors remain incomplete.
10. Registry coverage remains based on a weak denominator rather than a normalized run-level crosswalk.
11. The canonical evidence table remains Qwen-heavy and behaviour-heavy.
12. The claim matrix still lacks real panel counts, estimates, artifacts, and allowed wording.
13. Generated artifacts contain absolute local paths that are not portable to Sharanga.

---

# 1. Mandatory execution contract

## 1.1 Strictly forbidden

Do not run:

- `ssh`
- `sbatch`
- `srun`
- Slurm
- Sharanga jobs
- GPU jobs
- Wave 2 monitoring confirmation
- Wave 3 causal confirmation
- Wave 4 mechanistic experiments
- new head/layer/site selection
- new probe selection
- new threshold selection
- new causal panel construction
- new model inference
- new activation extraction
- any automatic follow-up job

This cycle is repository, statistics, validation-material, documentation, and evidence-integration work only.

## 1.2 Read before editing

Before modifying anything:

1. Read the complete Part II v1.1 PDF.
2. Read the one-page donor-control correction currently called v1.2.
3. Read the latest external audit in full.
4. Read the repository `README.md`.
5. Read the decision log.
6. Read all Stage 13 gate reports.
7. Inspect the current mutation implementation and verifier.
8. Inspect benchmark/template YAML schemas.
9. Inspect certificate generator and schema.
10. Inspect parser candidate generator.
11. Inspect balance/confound scripts and outputs.
12. Inspect leakage audit code and outputs.
13. Inspect registry, authority audit, canonical evidence, and claim matrix.
14. Inspect Git branch, commit, dirty state, and untracked files.
15. Inspect Sharanga sync conventions and repository-relative path expectations.

Create:

```text
docs/stage13/stage13_v6_preflight.md
```

The preflight must list:

- repository root;
- branch and commit;
- dirty/untracked files;
- current gate states;
- complete Part II v1.1 path;
- one-page correction path;
- all files containing false or superseded Part II versioning;
- current mutation operators and their actual semantics;
- current verifier scope;
- current certificate coverage and limitations;
- current parser distribution;
- current validation-material quality;
- current leakage detector coverage;
- current run inventory logic;
- current authority scan scope;
- current canonical evidence model coverage;
- current claim matrix completeness;
- all absolute local paths embedded in generated artifacts;
- exact files to modify;
- unresolved ambiguities.

If the complete Part II v1.1 document, canonical manifest, verifier, or repository root cannot be identified, stop and request clarification.

## 1.3 No fabrication

Never invent:

- historical run identities;
- job IDs;
- model revisions;
- raw counts;
- solver equations;
- symbolic derivations;
- unit conversions;
- parser labels;
- validator labels;
- authority status;
- confirmation status;
- claim estimates.

If evidence is unavailable, mark it unavailable.

## 1.4 Preserve history

Do not overwrite or delete:

- complete Part II v1.1;
- one-page correction artifact;
- prior mutation outputs;
- prior certificates;
- prior parser sets;
- prior balance reports;
- prior leakage reports;
- old gate reports;
- stale summaries;
- zero-row donor artifacts;
- historical registry and authority files.

Create versioned corrections and explicit supersession links.

## 1.5 Scientific unit

The canonical family is the independent unit.

The benchmark contains:

```text
155 canonical families
```

Variable-renamed families remain derived variants.

## 1.6 Sharanga compatibility

Use repository-relative paths only.

Do not write:

```text
/Users/shubhammishra/...
```

or any other local absolute path into generated artifacts.

Represent artifact references as:

```text
repo://relative/path
```

or plain repository-relative paths.

Maintain compatibility with:

```text
local repository
Sharanga repository: ~/PhysMons/
```

Do not hard-code partition, account, QoS, or scratch values.

---

# 2. Correct the Part II governing-document handling

## Task V6.1 — Reclassify the one-page “v1.2”

The one-page document must not be presented as a complete revised Part II.

Rename it as an erratum:

```text
docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.tex
docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf
```

Preserve the old incorrectly named files for provenance, but mark them superseded.

## Task V6.2 — Governing-document rule

Create:

```text
docs/proposals/PhysMon_Part_II_governing_document_rule.md
```

It must state:

> The governing scientific plan remains the complete 42-page Part II v1.1 document, read together with the mandatory July 3 donor-control erratum. The erratum supersedes only the renamed donor-control statements.

Update:

- README;
- decision log;
- Stage 13 briefs;
- any “read Part II v1.2” instructions;
- governance config;
- agent onboarding notes.

## Task V6.3 — Optional full v1.2 reconstruction

Only create a genuine full v1.2 if the complete v1.1 source can be recovered or faithfully reconstructed.

If complete source is unavailable:

```text
full_v1.2_status = blocked_source_unavailable
```

Do not recreate a 42-page document from memory or parsed text.

## Task V6.4 — Verify all donor-control wording

Search the repository for:

- `100% specificity`
- `0.0 mean recovery`
- `donor-on-renamed`
- `renamed donor controls completed`
- `68.1%`
- `Part II v1.2`

Produce:

```text
docs/stage13/donor_control_statement_audit_v6.md
```

Every surviving statement must be classified as:

```text
correct_current
historical_superseded
incorrect_requires_fix
```

---

# 3. Repair mutation semantics and claims

## Task V6.5 — Mutation semantic audit

Create:

```text
docs/stage13/mutation_semantics_audit_v6.md
```

For each operator, document:

```text
operator_id
current_name
actual_code_change
verifier_property_tested
confounds
recommended_name
supported_claim
unsupported_claim
```

## Task V6.6 — Rename misleading operators

At minimum:

### Current: `dimensional_corruption`

If it only negates a parameter value, rename to:

```text
negative_parameter_value
```

Do not call it dimensional corruption.

### Current: `target_quantity_change`

If it changes only metadata or expected answer, rename to:

```text
incorrect_canonical_answer
```

unless the prompt, target, equation, and answer are transformed consistently.

### Current: `assumption_removal`

If rejection is driven by cue leakage or another simultaneous mutation, split the operator. Do not claim assumption validation.

## Task V6.7 — Implement one genuine unit/dimension mutation

If a structured unit system exists, implement at least one real unit mutation:

Examples:

```text
kg -> s
m -> kg
V -> A
J -> C
```

The mutation must:

1. alter a structured unit field;
2. change the unit/dimension semantics;
3. invoke the available unit or dimensional checker;
4. record actual rejection.

If no dimensional checker exists, record:

```text
true_dimensional_mutation_status = unsupported_no_dimensional_checker
```

Do not fake a pass.

## Task V6.8 — Separate verifier-scope claims

Update mutation summaries so they say:

> The mutation suite tests the current symbolic verifier’s numerical-answer consistency, cue-symbol independence, structured-parameter plausibility, and parseability. It does not validate full natural-language semantics, assumption sufficiency, frame equivalence, or complete dimensional algebra.

## Task V6.9 — Mutation outputs

Create:

```text
results/stage13/benchmark_integrity/mutation_test_records_v6.jsonl
results/stage13/benchmark_integrity/mutation_test_summary_v6.json
```

Report by operator:

- actual mutation;
- changed fields;
- verifier called;
- actual checks;
- expected result;
- actual result;
- confounds;
- allowed interpretation.

---

# 4. Upgrade certificate quality and scope

## Task V6.10 — Certificate status taxonomy

Use:

```text
structured_machine_certificate_draft
structured_machine_certificate_verified
frame_equivalence_unverified
dimensional_metadata_only
certificate_generation_blocked
certificate_verification_failed
```

Do not call all generated certificates fully verified.

## Task V6.11 — Structured symbol table

Ensure every certificate’s relevant variables come only from structured template symbols.

Do not infer variables from prompt word tokens.

Each symbol entry must contain:

```text
symbol
physical_quantity
value
unit
role
source_field
```

## Task V6.12 — Explicit substituted derivation

Each certificate must include:

1. governing equation;
2. variable bindings;
3. numeric substitution;
4. intermediate calculation;
5. final answer;
6. canonical-answer comparison.

Example:

```text
v = v0 + at
v0 = 5.0 m/s
a = 2.0 m/s^2
t = 3.0 s
v = 5.0 + (2.0)(3.0)
v = 11.0 m/s
```

## Task V6.13 — Frame-rendering/unit-equivalence checker

For frame/unit-rendering families, implement a dedicated equivalence checker.

It must parse and normalize forms such as:

```text
101325 Pa
101.325 kPa
1.01325 bar
101325 N/m^2
```

and verify equivalence after conversion.

Use an existing unit library if already installed and approved by the repository. Otherwise implement a narrow, explicit conversion table for supported benchmark units.

Do not claim frame/unit equivalence from repeated evaluation of the same base value.

## Task V6.14 — Dimensional status wording

Replace:

```text
checked_from_template_units
```

with:

```text
unit_metadata_recorded_not_symbolically_verified
```

unless actual dimensional algebra is implemented.

## Task V6.15 — Portable paths

Remove absolute paths from:

- certificates;
- mutation records;
- packet files;
- manifests;
- audit files.

Add a portability test that fails on strings matching:

```text
/Users/
C:\
/home/<specific-user>/
```

## Task V6.16 — Certificate schema

Upgrade the JSON Schema with:

- explicit types;
- nested objects;
- enums;
- required fields;
- check result structure;
- allowed statuses;
- path format requirements.

Create:

```text
schemas/solver_certificate_v3.schema.json
```

---

# 5. Rebuild human-validation materials to pilot standard

## Task V6.17 — Pilot stratification

Create a 24–30 family pilot selected by deterministic stratification across:

- domain;
- cue type;
- template cluster;
- original versus expansion;
- certificate status;
- prior repair/borderline risk;
- parser risk;
- frame/unit rendering;
- assumption sensitivity.

Do not use only generic “standard” versus “expansion_or_frame” risk.

Create:

```text
docs/validation/pilot_selection_v6.csv
```

## Task V6.18 — Real calibration bank

Create at least 15 complete worked calibration examples.

Every example must contain:

```text
case_id
complete_problem_family
all_variants
governing_law
relevant_variables
designated_cue
assumptions
canonical_answer
expected_pass1_judgments
expected_pass2_judgments
valid_or_invalid
detailed_explanation
repair_or_exclusion_recommendation
```

No fields such as:

```text
governing_law = "see explanation"
relevant_variables = []
designated_cue = ""
```

are allowed.

## Task V6.19 — Qualification test

Create 12–15 complete realistic PhysMon-style cases.

Each must include:

- all variants;
- sufficient problem detail;
- questions validators must answer;
- no category label in the test prompt;
- a worked answer key explaining physics and expected annotation.

## Task V6.20 — Handbook

Write a complete handbook containing:

- purpose;
- independence;
- Pass 1 workflow;
- Pass 2 workflow;
- governing versus non-governing variables;
- irrelevant versus redundant versus correlated variables;
- assumption sufficiency;
- answer uniqueness;
- invariance;
- semantic equivalence;
- unintended co-variation;
- frame/unit equivalence;
- naturalness;
- difficulty shifts;
- borderline rules;
- repair/exclusion;
- adjudication;
- revalidation;
- worked examples from calibration bank.

## Task V6.21 — Pass 1 packet fields

Each Pass 1 packet must request:

```text
independent_solution
governing_law
relevant_variables
candidate_non_governing_variables
assumptions_sufficient
answer_unique
answer_invariant
semantic_equivalence
unintended_covariation
wording_natural
difficulty_shift
overall_verdict
confidence
repair_recommendation
notes
```

## Task V6.22 — Pass 2 packet fields

Each Pass 2 packet must include actual certificate data and request:

```text
solver_derivation_correct
certificate_valid
canonical_answer_correct
unit_or_frame_equivalence_correct
invariance_check_correct
certificate_limitations
overall_certificate_verdict
confidence
notes
```

## Task V6.23 — Pilot readiness gate

Human pilot may be `READY_FOR_PI_REVIEW` only if:

- all calibration examples are complete;
- qualification cases are complete;
- handbook is complete;
- Pass 1 and Pass 2 forms validate;
- certificate fields are nonempty and meaningful;
- pilot is stratified.

Do not mark the human pilot started.

---

# 6. Correct balance/confound analysis

## Task V6.24 — Exclude missing labels

Do not convert missing \(S^{lp}\) to zero.

Construct the labeled dataset using only rows where authoritative \(S^{lp}\) exists.

Expected current labeled count:

```text
140 Qwen families
```

unless authoritative expansion labels are ingested.

Report:

```text
n_manifest_families
n_labeled_families
n_unlabeled_families
unlabeled_family_ids
```

## Task V6.25 — Supersede invalid v5 audit

Mark:

```text
balance_audit_v5 = superseded_missing_labels_coerced_negative
```

## Task V6.26 — Template grouping

Use normalized symbolic/template identities rather than broad prefix groups.

Create a grouping field based on:

- template ID;
- normalized equation structure;
- cue insertion structure;
- domain.

Report group sizes.

## Task V6.27 — CV regimes

Run:

### A. Family-level stratified CV

For comparison only.

### B. Template-held-out CV

Use grouped folds or leave-one-template-group-out where feasible.

If there are too few template groups, report instability and do not overstate the estimate.

## Task V6.28 — Confound classes

Report separately:

- strongest numeric confound;
- strongest categorical confound;
- strongest template-structure confound.

Include:

- cue type;
- domain;
- template cluster;
- original/expansion only for labeled families;
- prompt length;
- number count;
- variable count;
- equation count;
- answer magnitude;
- available correctness;
- available entropy.

For categorical features, compute:

- chi-square or exact test;
- Cramér’s V;
- multiple-testing correction.

## Task V6.29 — Permutation and uncertainty

Use at least:

```text
1000 refitted permutations
```

unless runtime is prohibitive. If reduced, explain why.

Each permutation must refit the full pipeline.

Use family/group-aware bootstrap confidence intervals.

## Task V6.30 — Outputs

Create:

```text
results/stage13/benchmark_integrity/balance_audit_v6.json
results/stage13/benchmark_integrity/balance_audit_v6_family_predictions.csv
results/stage13/benchmark_integrity/balance_audit_v6_template_predictions.csv
results/stage13/benchmark_integrity/balance_audit_v6_groups.csv
```

---

# 7. Rebuild parser candidates correctly

## Task V6.31 — True uniqueness

Ensure:

```text
n_rows == n_unique_raw_outputs
```

or document deliberate duplicate cases separately.

## Task V6.32 — Manual category definitions

Do not assign `equivalent_units` merely because a unit token is present.

Define categories explicitly.

Examples:

### Equivalent units

Must contain semantically equivalent forms such as:

```text
1000 J
1 kJ
```

### Fraction

Must contain a numeric fraction pattern such as:

```text
3/4
```

not a unit slash such as:

```text
m/s
```

### Model-specific quirk

Must describe a concrete model formatting behavior, not every model output.

## Task V6.33 — Balanced quotas

Create at least 150 candidates with meaningful category and domain balance.

Minimum category counts:

- plain numeric: 15;
- scientific notation: 10;
- numeric fractions: 10;
- equivalent units: 15;
- multiple numbers: 15;
- rounding boundaries: 10;
- wrong units: 10;
- refusals/hedges: 10;
- long prose: 10;
- LaTeX: 10;
- ambiguous final answer: 10;
- concrete model-specific quirks: 10.

Domain targets:

- mechanics;
- electrostatics/circuits;
- thermodynamics or other available domains;
- designed mixed edge cases.

## Task V6.34 — Designed case grounding

Every designed case must include:

- underlying prompt or scenario;
- canonical answer;
- expected unit;
- tolerance;
- intended parser challenge;
- expected human judgment.

Do not include artificial labels such as:

```text
[edge scientific_notation 0]
```

inside raw model-output text.

## Task V6.35 — Family diversity

Report unique family count per model.

Avoid drawing most DeepSeek or Llama candidates from a tiny number of families.

## Task V6.36 — Outputs

Create:

```text
docs/validation/parser_audit_candidates_v6.jsonl
docs/validation/parser_candidate_coverage_v6.json
docs/validation/parser_labeling_instructions_v6.md
```

---

# 8. Complete leakage detector coverage

## Task V6.37 — Implement actual structural detectors

Implement and use:

1. exact prompt hash;
2. number-masked prompt hash;
3. normalized symbolic-equation hash;
4. variable-renaming-invariant structure hash;
5. cue-template hash;
6. numeric-instantiation sibling detection;
7. lexical similarity;
8. semantic/template similarity if a local approved embedding method is available.

Do not list a detector as active unless records include its output.

## Task V6.38 — Review workload taxonomy

Separate:

```text
within_same_family_expected
derived_parent_expected
cross_family_exact_duplicate
cross_family_structural_candidate
cross_family_numeric_sibling
cross_family_lexical_candidate
cross_family_semantic_candidate
cross_split_candidate
```

Only cross-family candidates should enter unresolved review.

## Task V6.39 — Gate logic

Leakage status cannot be PASS while unresolved cross-family candidates remain.

Allowed statuses:

```text
PASS
FAIL_EXACT_CROSS_SPLIT_DUPLICATE
INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW
```

---

# 9. Build a real run-level registry crosswalk

## Task V6.40 — Run candidate extraction

Build expected runs from actual evidence:

- decision-log entries;
- Slurm logs;
- Slurm job IDs;
- output directories;
- run manifests;
- raw/summary pairs;
- config files;
- experiment cards.

Do not create expected runs from:

- stage numbers;
- top-level directory names alone;
- Slurm template filenames alone;
- arbitrary numbers found in prose.

## Task V6.41 — Normalized run identity

Each expected run must have:

```text
expected_run_id
experiment_family
model_id
configuration_identity
panel_identity
job_id_if_known
result_directory
raw_artifacts
summary_artifacts
logs
config
confidence
```

## Task V6.42 — Crosswalk

Create:

```text
docs/registry/historical_run_crosswalk_v6.csv
results/stage13/wave0/expected_historical_runs_v6.jsonl
```

Map:

```text
expected_run_id -> registry experiment_id
```

with:

```text
matched
partially_matched
unmatched
duplicate_mapping
```

## Task V6.43 — Coverage

Compute coverage only from normalized runs.

Report:

- expected runs;
- matched;
- partial;
- unmatched;
- irrecoverable;
- coverage fraction.

---

# 10. Repository-wide authority audit

## Task V6.44 — Scan all relevant artifact types

Include:

- JSON;
- JSONL;
- CSV;
- YAML;
- logs;
- stdout/stderr;
- NPY;
- NPZ;
- PT/safetensors references where appropriate;
- config files;
- manifests;
- Slurm output files;
- summaries;
- partial summaries;
- nested archives if accessible.

## Task V6.45 — Group by run

Group raw, summary, config, log, and job artifacts by run identity.

Detect:

- orphan raw files;
- orphan summaries;
- row-count mismatch;
- zero-row results;
- partial/full pairs;
- corrected/superseded pairs;
- panel mismatch;
- stale verification;
- duplicate retries.

## Task V6.46 — Authority outputs

Create:

```text
docs/registry/artifact_authority_audit_v6.json
docs/registry/artifact_authority_audit_v6.md
results/stage13/wave0/orphan_artifacts_v6.csv
```

Do not label every orphan critical without classification.

Classify:

```text
critical
paper_relevant_noncritical
diagnostic
temporary
cache
unknown
```

---

# 11. Expand canonical evidence

## Task V6.47 — Model coverage

Extend canonical evidence to include available:

- Qwen;
- Llama;
- DeepSeek;

rows where authoritative evidence exists.

## Task V6.48 — Evidence types

Ingest resolved:

- behavioural sensitivity;
- parser eligibility;
- monitor scores;
- monitor layer/site;
- entropy/confidence;
- black-box baseline;
- CoT baseline;
- answer+rationale baseline;
- correctness probe;
- causal panel eligibility;
- causal site;
- intervention effects;
- control effects;
- damage metrics.

Every non-null value must cite source experiment IDs.

## Task V6.49 — Null reasons

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

Do not use `human_validation_pending` as a generic reason for missing monitor or causal data.

---

# 12. Populate the claim–evidence matrix

## Task V6.50 — Correct panel sizes

Use actual panel sizes, such as:

- 140-family Qwen behavioural sweep;
- 135-family monitoring panel;
- 20-family Qwen causal panel;
- 20-family Llama exploratory panel;
- 15-family expansion panel;
- approximately 10-family variable-renaming panel;
- cue-specific subsets.

Do not default to 155.

## Task V6.51 — Required fields

Populate for every claim:

```text
current_estimate
confidence_interval
family_count
model_count
experiment_ids
authoritative_artifacts
panel_caveats
discovery_or_confirmation
human_validation_dependency
allowed_wording
prohibited_wording
missing_evidence
next_required_experiment
```

## Task V6.52 — Donor specificity

Keep donor-on-renamed specificity explicitly unsupported.

---

# 13. Gate logic

## Task V6.53 — Wave 0 gate v6

Create:

```text
results/stage13/wave0/wave0_gate_v6.json
docs/stage13/wave0_gate_v6_report.md
```

Wave 0 may remain failed.

It passes only if:

- governing-document rule is correct;
- run crosswalk is substantive;
- critical authority issues are resolved;
- canonical evidence is multi-model and source-linked;
- claim matrix is populated;
- no authoritative result has partial provenance.

## Task V6.54 — Wave 1A software/materials gate v6

Create:

```text
results/stage13/benchmark_integrity/wave1a_gate_v6.json
docs/stage13/wave1a_gate_v6_report.md
```

Wave 1A passes only if:

- mutation semantics are accurate;
- real verifier-backed operators exist;
- certificate status is honest;
- frame/unit equivalence is actually checked or marked unsupported;
- pilot is stratified;
- calibration examples are complete;
- qualification cases are complete;
- parser set is unique and meaningfully balanced;
- balance audit excludes unlabeled families;
- leakage detectors are implemented and unresolved candidates are honestly tracked;
- all generated paths are portable.

Human pilot remains:

```text
PENDING
```

Wave 2 permission remains:

```text
false
```

---

# 14. Tests

Add substantive tests:

1. one-page erratum cannot be treated as full Part II;
2. governing rule references complete v1.1 plus erratum;
3. misleading mutation names are removed;
4. negative-parameter mutation is not called dimensional corruption;
5. target-answer corruption is not called target-quantity change;
6. verifier-scope statement is present;
7. certificate variables come from symbol table;
8. derivation contains actual substitution values;
9. frame-unit conversions are numerically checked;
10. dimensional metadata status is not overclaimed;
11. no generated artifact contains `/Users/`;
12. pilot contains all required strata;
13. calibration examples have complete fields;
14. qualification cases contain full prompts;
15. Pass 1 schema includes all required judgments;
16. missing \(S^{lp}\) labels are excluded;
17. template-held-out grouping is normalized;
18. permutation refits the full model;
19. parser raw outputs are truly unique;
20. equivalent-unit category requires actual equivalent forms;
21. fraction category ignores unit slashes;
22. designed cases include canonical answer and scenario;
23. all leakage detectors produce fields;
24. expected same-family and derived-parent relations are excluded from unresolved review;
25. run inventory rejects directory/stage placeholders as runs;
26. authority audit scans logs/configs, not just tabular files;
27. canonical non-null values cite source experiments;
28. claim panel counts match source experiments;
29. Wave 1A cannot pass with incomplete calibration or parser materials.

Run:

```bash
.venv/bin/ruff check scripts/stage13 src/physmon tests/stage13
PYTHONPATH=src python3 -m pytest tests/stage13
PYTHONPATH=src python3 -m pytest
```

---

# 15. Required report-back

## A. Scope
- confirm no Sharanga, Slurm, GPU, or Wave 2–4 work.

## B. Governing document
- complete Part II path;
- erratum path;
- governing rule;
- whether full v1.2 was blocked.

## C. Mutation semantics
- renamed operators;
- verifier properties tested;
- unsupported claims;
- actual results.

## D. Certificates
- status counts;
- substituted derivations;
- frame/unit conversion checks;
- dimensional limitations;
- portable paths.

## E. Human validation
- pilot strata;
- calibration examples;
- qualification cases;
- packet counts;
- readiness status.

## F. Balance/confound
- labeled/unlabeled family counts;
- numeric confounds;
- categorical confounds;
- template confounds;
- family-CV;
- template-held-out CV;
- permutation p-values;
- CIs.

## G. Parser
- total rows;
- unique outputs;
- counts by model;
- counts by category;
- counts by domain;
- unique families per model;
- human-label status.

## H. Leakage
- detector coverage;
- expected relations;
- cross-family candidates;
- cross-split candidates;
- unresolved components.

## I. Run crosswalk
- expected runs;
- matched;
- partial;
- unmatched;
- irrecoverable;
- coverage.

## J. Authority
- artifacts scanned by type;
- orphan classes;
- critical unresolved;
- zero-row issues;
- resolved corrections.

## K. Canonical evidence
- rows by model;
- populated fields;
- source-linked values;
- null reasons.

## L. Claims
- populated claims;
- real panel counts;
- downgraded claims;
- missing evidence.

## M. Gates
- Wave 0;
- Wave 1A software/materials;
- human pilot;
- Wave 2 permission.

## N. Tests
- exact commands and results.

## O. Sharanga readiness
- no jobs run;
- no absolute local paths;
- safe sync commands.

Stop after reporting.

---

# 16. Final instruction

Do not optimize for a green gate.

A one-page erratum is not a full revised proposal.

A mutation name must describe the actual code change.

Missing labels must remain missing.

A parser category must reflect the actual phenomenon.

A calibration case must be complete enough for a human validator to solve.

A coverage denominator must represent real runs.

A truthful failure is scientifically preferable to a false pass.
