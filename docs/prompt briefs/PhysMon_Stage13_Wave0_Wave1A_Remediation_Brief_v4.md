# PhysMon Stage 13 — Wave 0 / Wave 1A Scientific Remediation Brief, Version 4.0

**Purpose:** Correct the remaining scientific and governance failures in the Stage 13 evidence-foundation work before any Wave 2–4 experimentation begins.

**Governing documents:**
1. PhysMon Research Proposal and supplementary documentation
2. PhysMon Part II — Next-Phase Scientific and Experimental Plan, version 1.1
3. PhysMon Stage 13 Controlled Execution Brief, version 2.0
4. PhysMon Stage 13 Wave 0 / Wave 1A Remediation Brief, version 3.0
5. The latest external audit of the Stage 13 remediation outputs

**Scope:** CPU-only Wave 0 and Wave 1A remediation.

**Forbidden in this cycle:**
- No Wave 2 monitoring confirmation
- No Wave 3 causal confirmation
- No Wave 4 mechanistic experiments
- No new head, layer, probe, or threshold selection
- No GPU jobs
- No Slurm submissions
- No automatic follow-up jobs
- No promotion of exploratory evidence to confirmatory evidence

---

# 0. Current authoritative project status

Treat the current project state as:

```text
Wave 0 scientific gate: FAIL — HISTORICAL_AUTHORITY_UNRESOLVED
Wave 1A software/materials gate: FAIL — SCIENTIFIC_CONTENT_INCOMPLETE
Human pilot: NOT READY
Paper eligibility: FALSE
Permission for Wave 2: FALSE
```

Do not preserve the earlier Wave 1A `PASS`.

The latest audit identified one urgent factual correction:

> The donor-on-renamed same-answer and stable-control runs did not produce measured zero effects. Both raw CSVs contain zero evaluable rows, and their summaries defaulted to mean recovery 0.0. These are incomplete/failed empty-panel runs, not scientific null results.

Therefore, the following statements are currently unsupported and must be removed or corrected everywhere:

- “Both renamed donor controls completed.”
- “Both renamed donor controls yielded 0.0 mean recovery.”
- “The renamed controls showed 100% specificity.”
- Any pooled specificity estimate that uses those empty runs.

The correct current interpretation is:

> The donor-on-renamed controls produced zero evaluable rows. Their summaries defaulted to zero recovery, but this is not a measured result. The controls remain incomplete and must be diagnosed and rerun later under a separate, approved experimental cycle.

---

# 1. Mandatory operating contract

## 1.1 Read before editing

Before modifying files:

1. Read all governing documents.
2. Read the latest external audit in full.
3. Read the repository `README.md`.
4. Read the current Stage 13 governance config.
5. Read the current decision logs and status reports.
6. Inspect Git branch, commit, dirty status, and untracked files.
7. Inspect all Stage 13 scripts, tests, results, manifests, and validation materials.
8. Inspect Slurm templates and historical job logs read-only.
9. Produce a remediation preflight report.

Create:

```text
docs/stage13/stage13_remediation_v4_preflight.md
```

The preflight must identify:

- repository root;
- branch and commit;
- dirty/untracked files;
- current gate files and statuses;
- current benchmark manifests;
- current canonical evidence tables;
- current registry and authority audit;
- current validation materials;
- current parser candidates;
- current mutation harness;
- current balance/confound audit;
- all files containing renamed-donor specificity claims;
- all files that must be corrected;
- missing files or unresolved path issues.

If the repository root, manifest, decision log, or results root cannot be identified reliably, stop and request clarification.

## 1.2 No fabrication

Never invent or infer missing:

- job IDs;
- model revisions;
- family IDs;
- commands;
- configuration hashes;
- raw row counts;
- solver certificates;
- parser labels;
- human labels;
- authority status;
- confirmation status.

Use explicit unresolved/null fields.

## 1.3 Preserve raw evidence

Do not delete or overwrite:

- zero-row CSVs;
- misleading summaries;
- logs claiming “COMPLETE”;
- partial files;
- stale summaries;
- corrected files;
- nested archives.

Create new corrected artifacts and explicit supersession links.

## 1.4 Scientific unit

The independent unit is the canonical family.

The canonical benchmark contains exactly:

```text
155 canonical families
```

Variable-renaming examples are derived variants, not new canonical families.

## 1.5 Sharanga compatibility

This cycle is local and CPU-only.

Maintain compatibility with:

```text
local repository
Sharanga repository: ~/PhysMons/
```

Rules:

- use repository-relative paths;
- do not hard-code `/Users/...`;
- do not hard-code Sharanga partitions/accounts/QoS;
- do not run `ssh`, `sbatch`, `srun`, or GPU commands;
- do not alter Sharanga scratch;
- preserve `make sync-up`, `make sync-check`, and `make sync-down` workflow;
- provide safe sync commands only at the end.

---

# 2. Immediate factual correction: renamed donor controls

## Task R4.1 — Reclassify empty donor-control runs

Inspect:

```text
results/stage12/science/donor_renamed/same_answer/
results/stage12/science/donor_renamed/stable/
```

Verify:

- raw CSV row count;
- summary `rows`;
- event-log status;
- target/donor eligibility logic;
- why zero pairs were evaluated.

Update the experiment registry:

- these runs must not be `complete_authoritative`;
- these runs must not be `complete_exploratory`;
- classify as `partial_not_reportable` or `failed`, with an explicit reason such as `empty_result_panel`.

Add fields/notes:

```text
raw_data_rows = 0
summary_defaulted_zero = true
scientific_null = false
paper_eligibility = false
```

## Task R4.2 — Correct all derived claims

Search the full repository for:

- `100% specificity`
- `0.0 mean recovery`
- `donor-on-renamed`
- `same-answer donor`
- `stable donor`
- `68.1%`
- related claim IDs

Correct:

- Part II LaTeX/source document;
- Part II compiled PDF source references if maintained in repo;
- experiment registry;
- authority audit;
- claim–evidence matrix;
- decision log;
- project status summaries;
- paper notes;
- plots/tables if any;
- README or docs mentioning completion.

Allowed wording:

> The donor-on-renamed controls produced zero evaluable rows. Their summaries defaulted to zero recovery, so no scientific null or specificity claim can be made from these runs.

Prohibited wording:

- completed;
- 0.0 measured effect;
- 100% specificity;
- confirmed donor specificity on renamed families.

## Task R4.3 — Fix the original experiment scripts

Identify the scripts that generated the zero-row summaries.

Change behavior so that:

- `rows == 0` causes a non-zero exit or explicit failure status;
- summary fields become `null`, not `0.0`;
- event logs say `FAILED_EMPTY_RESULT_PANEL`;
- no “COMPLETE” event is emitted;
- registry ingestion maps this to `failed` or `partial_not_reportable`;
- tests cover empty panels.

Do not rerun the experiment in this cycle.

Create tests verifying:

```text
zero rows != measured zero effect
zero rows -> failure status
mean/median -> null
paper eligibility -> false
```

---

# 3. Correct the Wave 1A gate

## Task R4.4 — Replace false Wave 1A PASS

Preserve the old gate artifact.

Create:

```text
results/stage13/benchmark_integrity/wave1a_gate_v3.json
docs/stage13/wave1a_gate_v3_report.md
```

Current expected status:

```text
FAIL — SCIENTIFIC_CONTENT_INCOMPLETE
```

Human pilot status:

```text
NOT_READY
```

Permission for Wave 2:

```text
false
```

The gate must not pass merely because files exist.

## Task R4.5 — Content-based Wave 1A checks

Wave 1A software/materials may pass only when:

1. at least one genuine negative solver mutation is executed;
2. at least one genuine positive semantics-preserving mutation is executed;
3. mutation outcomes are checked against the verifier;
4. the balance audit uses valid tie-aware metrics and actual grouped CV;
5. parser candidates are balanced across target models and categories;
6. Pass 1 packets include all family variants;
7. Pass 2 packets contain actual solver-certificate content;
8. validator handbook contains worked calibration examples;
9. qualification test contains complete solvable cases;
10. annotation schema is typed and constrained;
11. agreement code computes required metrics;
12. leakage audit includes all canonical and derived data;
13. unresolved near-duplicate review is represented honestly.

---

# 4. Fix the balance/confound audit

## Task R4.6 — Supersede the invalid audit

The current balance audit is invalid because:

- it labels a maximum single-feature AUROC as a combined grouped-CV result;
- its custom AUROC does not handle ties correctly;
- it does not perform grouped cross-validation;
- it omits required confounds and corrections.

Mark the current artifact:

```text
superseded_invalid_auc_implementation
```

Update registry and authority audit.

## Task R4.7 — Implement a valid audit

Rewrite:

```text
scripts/stage13/run_balance_audit.py
```

Use standard libraries:

- `sklearn.metrics.roc_auc_score`
- `StratifiedGroupKFold` or another valid family-grouped split
- `Pipeline`
- fold-local preprocessing
- `LogisticRegression`
- appropriate encoders/scalers

Do not implement custom AUROC unless independently tested against sklearn.

### Features

At family level:

- domain;
- cue type;
- answer sign;
- answer magnitude;
- prompt length;
- token count;
- number count;
- variable count;
- equation count;
- unit-token count;
- base correctness;
- entropy;
- answer format;
- template cluster.

### Analyses

1. Descriptive distributions by sensitivity label.
2. Standardized effect sizes.
3. Pearson/Spearman correlations for continuous features.
4. Tie-aware single-feature AUROC.
5. Orientation-independent discrimination where useful.
6. Grouped-CV combined surface-feature classifier.
7. Confidence intervals from family bootstrap.
8. Permutation test.
9. Benjamini–Hochberg correction for multiple univariate tests.
10. Exact fold assignments saved.

### Outputs

```text
results/stage13/benchmark_integrity/balance_audit_v3.json
results/stage13/benchmark_integrity/balance_audit_v3_folds.csv
results/stage13/benchmark_integrity/balance_audit_v3_predictions.csv
```

The report must clearly distinguish:

- single-feature AUROC;
- combined grouped-CV AUROC;
- in-sample descriptive statistics;
- out-of-fold predictions.

Add tests for ties and compare against sklearn.

---

# 5. Implement real solver mutation testing

## Task R4.8 — Replace no-op-only mutation status

The current mutation harness has not tested negative mutations.

Change status to:

```text
MUTATION_FRAMEWORK_SCAFFOLDED
NEGATIVE_MUTATION_EXECUTION_NOT_IMPLEMENTED
```

until real mutations run.

## Task R4.9 — Implement representative real mutations

Inspect the actual family/template/solver architecture.

Implement at least:

### Genuine negative mutations

1. Sign inversion in a governing expression.
2. Replace a governing variable with the designated cue.
3. Dimensional corruption.
4. Remove or alter one required assumption where represented structurally.
5. Change target quantity so the original certificate is no longer valid.

### Genuine positive mutations

1. Whitespace/formatting change that genuinely changes the text representation but preserves semantics.
2. Variable renaming that preserves the symbolic mapping.
3. Algebraically equivalent expression.
4. Unit formatting normalization where supported.

Each operator must declare:

```text
operator_id
applicability
mutation_applied
expected_verifier_result
actual_verifier_result
coverage_status
```

Run on a representative stratified subset across domains and cue types.

Do not fake unsupported natural-language verification. Mark unsupported cases honestly.

Outputs:

```text
results/stage13/benchmark_integrity/mutation_test_records_v3.jsonl
results/stage13/benchmark_integrity/mutation_test_summary_v3.json
```

The summary must report:

- applicable count;
- executed count;
- negative rejection rate;
- positive acceptance rate;
- unsupported count;
- failures by operator.

---

# 6. Rebuild parser audit candidates

## Task R4.10 — Supersede the current candidate set

The current candidate set is not sufficiently stratified.

Mark it as draft/superseded for final parser-audit use.

## Task R4.11 — Build a balanced set

Create at least 120 unique candidates:

- 30+ Qwen;
- 30+ Llama;
- 30+ DeepSeek;
- 30+ designed edge cases.

Cover:

- mechanics;
- electrostatics/circuits;
- Cue A/B/C where available;
- integers;
- decimals;
- scientific notation;
- fractions;
- equivalent units;
- multiple numbers;
- rounding boundaries;
- wrong units;
- refusals;
- long prose;
- LaTeX;
- ambiguous outputs;
- model-specific quirks.

Do not classify fractions using a raw `/` substring.

Use regex or parsing logic that distinguishes:

- numeric fractions such as `3/4`;
- unit slashes such as `m/s`.

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
category
human_extracted_answer
human_normalized_answer
human_correctness
human_ambiguity
notes
```

Human fields remain blank.

Create:

```text
docs/validation/parser_audit_candidates_v3.jsonl
docs/validation/parser_labeling_instructions_v3.md
```

Add a coverage summary and uniqueness test.

---

# 7. Build actual Pass 2 certificates

## Task R4.12 — Define a certificate schema

Create:

```text
schemas/solver_certificate.schema.json
```

Required fields:

```text
family_id
governing_law
governing_equations
relevant_variables
designated_cue
stated_assumptions
symbolic_derivation
canonical_answer
dimensional_checks
invariance_claim
invariance_checks
numeric_spot_checks
certificate_generator
certificate_version
source_template
verification_status
limitations
```

## Task R4.13 — Populate real certificates

For each of the 25 pilot families:

- extract existing symbolic/template information;
- generate a real inspectable certificate;
- do not leave governing equation, derivation, assumptions, or checks empty;
- do not use `verifier_certified: true` as a substitute for evidence.

If a real certificate cannot be generated for a family, exclude it from the pilot and record why.

Create:

```text
docs/validation/certificates/<family_id>.json
docs/validation/stage13_validation_packet_pass2_v3.jsonl
```

Pass 2 packet records must embed or reference actual certificate fields.

---

# 8. Make validator materials pilot-ready

## Task R4.14 — Expand the validator handbook

Create:

```text
docs/validation/validator_handbook_v3.md
```

Include:

1. Purpose and independence rules.
2. Three-level project distinction.
3. Definition of governing and non-governing variables.
4. Difference between irrelevant, redundant, correlated, and relevant variables.
5. Answer invariance.
6. Assumption sufficiency.
7. Semantic equivalence.
8. Frame/coordinate transformation guidance.
9. Unit-compatible distractor guidance.
10. Naturalness and difficulty-shift rules.
11. Borderline decision rules.
12. Repair versus exclusion.
13. Pass 1 workflow.
14. Pass 2 certificate verification.
15. Adjudication.
16. Revalidation after repair.
17. At least 15–20 worked calibration examples:
    - valid;
    - invalid;
    - subtle;
    - domain-diverse.

Calibration examples must not be confirmatory families.

## Task R4.15 — Build a real qualification test

Create 12–15 complete cases, each with actual problem text and questions.

Create:

```text
docs/validation/qualification_test_v3.md
docs/validation/qualification_answer_key_DRAFT_REQUIRES_PI_REVIEW_v3.md
```

The test must include:

- valid irrelevant variable;
- subtly relevant variable;
- missing assumption;
- ambiguous target;
- invalid frame equivalence;
- valid coordinate transformation;
- dimensional inconsistency;
- semantic drift;
- solver error;
- parser ambiguity;
- unit-compatible but governing variable;
- natural versus unnatural rendering.

## Task R4.16 — Type the annotation schema

Create:

```text
docs/validation/annotation_schema_v3.json
```

Define:

- field types;
- enums;
- required fields by pass;
- confidence scale;
- verdict options;
- allowed missingness;
- date/time formats;
- validator ID constraints.

## Task R4.17 — Agreement implementation

Upgrade:

```text
scripts/stage13/compute_validation_agreement.py
```

Compute:

- raw agreement;
- Cohen’s kappa or appropriate alternative;
- cue-relevance agreement;
- invariance agreement;
- assumption-sufficiency agreement;
- semantic-equivalence agreement;
- domain/cue breakdown;
- adjudication rate;
- missing-field rate.

Do not return final agreement metrics when human labels are absent.

---

# 9. Upgrade leakage auditing

## Task R4.18 — Complete detector coverage

Upgrade leakage audit to use:

- exact prompt hash;
- symbolic expression hash;
- variable-renaming-invariant structural hash;
- masked rendering skeleton;
- cue-template hash;
- numeric sibling detection;
- lexical similarity;
- semantic/template candidate similarity;
- derived variant prompts.

Do not claim `derived_variants_included=true` unless derived prompts were actually loaded and compared.

Outputs:

```text
results/stage13/benchmark_integrity/leakage_audit_v3.json
results/stage13/benchmark_integrity/leakage_review_v3.csv
```

Distinguish:

- pair count;
- connected-component cluster count;
- exact duplicates;
- cross-split duplicates;
- within-split siblings;
- derived-parent relations;
- unresolved near-duplicate candidates.

Do not return PASS while cross-split candidates remain unresolved.

---

# 10. Improve registry coverage and authority audit

## Task R4.19 — Replace row-count coverage

Do not treat `registry_rows >= 50` as historical coverage.

Compute coverage against:

- decision-log experiment references;
- Slurm scripts;
- Slurm output/job logs;
- result directories;
- known headline claims;
- known failed/partial experiments.

Report:

```text
n_expected_experiments
n_registered_experiments
n_unregistered_experiments
coverage_fraction
unregistered_list
```

If Slurm history cannot be fully recovered, distinguish:

- discovered expected experiments;
- recoverable jobs;
- irrecoverable provenance.

## Task R4.20 — Status/provenance consistency

A run may not be `complete_authoritative` or `corrected_authoritative` unless provenance is complete.

If provenance remains partial:

- downgrade to `complete_exploratory`;
- or introduce a clearly documented `corrected_exploratory` status only if the governing vocabulary is formally revised everywhere.

Prefer the existing allowed vocabulary and use notes/correction links.

## Task R4.21 — Generic authority audit

The audit must not resolve only hard-coded cases.

Implement generic grouping using:

- directory structure;
- filenames;
- registry experiment IDs;
- summary/raw links;
- job/log references;
- config hashes;
- family panels.

For every experiment:

- count raw data rows;
- read summary-reported rows;
- compare them;
- detect zero-row completion bugs;
- regenerate basic statistics where possible;
- identify partial/full/corrected artifacts;
- resolve authority or mark unresolved.

Special rule:

```text
raw_data_rows == 0
```

can never support a measured null effect.

---

# 11. Improve canonical evidence and null taxonomy

## Task R4.22 — Populate authoritative fields

Ingest available authoritative:

- monitor scores;
- monitor layer/site;
- entropy/confidence;
- black-box scores;
- CoT and rationale scores;
- correctness-probe scores;
- causal panel eligibility;
- causal site;
- intervention effects;
- damage controls.

Every value must cite source experiment IDs.

## Task R4.23 — Null classification

Add a field-level null-reason system:

```text
not_applicable
not_measured
source_missing
source_unresolved
excluded_ineligible
parser_invalid
human_validation_pending
unexpected_missing
```

Verification must report counts by reason.

Do not report `unexpected_nulls=0` merely because only identity columns were checked.

---

# 12. Improve partition freeze and claim matrix

## Task R4.24 — Historical selection accuracy

Update selection ledgers with exact historical subsets where recoverable.

Do not say all 155 families selected a decision that was made before expansion.

Distinguish:

- direct selection set;
- later reuse;
- analyst exposure;
- prospective eligibility.

## Task R4.25 — Populate claim matrix

For every claim, add:

- current estimate;
- family count;
- model count;
- experiment IDs;
- authoritative artifacts;
- panel caveats;
- discovery/confirmation status;
- human-validation dependency;
- allowed wording;
- prohibited wording;
- missing evidence.

Immediately downgrade donor-specificity claims because renamed donor controls are empty.

---

# 13. Tests

Add tests for:

1. zero rows produce failure, not zero effect;
2. donor summaries use null mean/median on empty panels;
3. Wave 1A fails with empty certificate fields;
4. Wave 1A fails with no genuine negative mutation;
5. Wave 1A fails with invalid balance audit;
6. tie-aware AUROC matches sklearn;
7. grouped CV is actually executed;
8. combined surface model differs from max single-feature AUROC;
9. parser categories distinguish fractions from unit slashes;
10. parser candidate model/category balance;
11. Pass 2 contains non-empty equations, derivation, assumptions, and checks;
12. qualification test contains full cases;
13. annotation schema types/enums validate;
14. agreement code handles missing labels;
15. derived prompts are actually included in leakage;
16. registry coverage compares against discovered experiment references;
17. authoritative status requires complete provenance;
18. zero-row raw data cannot be authority-resolved as complete;
19. canonical null reasons are valid;
20. gate reports bind final artifact hashes.

Run:

```bash
.venv/bin/ruff check scripts/stage13 src/physmon tests/stage13
PYTHONPATH=src python3 -m pytest tests/stage13
PYTHONPATH=src python3 -m pytest
```

---

# 14. Corrected gate reports

Create:

```text
results/stage13/wave0/wave0_gate_v4.json
docs/stage13/wave0_gate_v4_report.md
results/stage13/benchmark_integrity/wave1a_gate_v4.json
docs/stage13/wave1a_gate_v4_report.md
```

## Wave 0

Wave 0 may remain failed. That is acceptable.

It passes only if:

- critical authority issues are zero;
- registry coverage is substantive;
- canonical evidence is traceable;
- claim matrix is populated;
- selection ledger is accurate;
- no paper-eligible result has unresolved provenance.

## Wave 1A

Wave 1A software/materials passes only if:

- valid balance audit;
- real mutation execution;
- balanced parser set;
- real Pass 2 certificates;
- complete handbook;
- real qualification test;
- typed annotation schema;
- agreement code ready;
- leakage audit honestly scoped.

Human pilot remains pending until real validators are recruited and labels exist.

Always set:

```text
permission_for_wave2 = false
```

for this cycle.

---

# 15. Report-back format

At completion report:

## A. Factual corrections
- renamed donor-control row counts;
- old status;
- corrected status;
- all documents corrected;
- whether any specificity claim remains.

## B. Gates
- Wave 0 status;
- Wave 1A software/materials status;
- human pilot status;
- Wave 2 permission.

## C. Balance audit
- implementation;
- grouped folds;
- single-feature AUROCs;
- combined grouped-CV AUROC;
- CIs;
- strongest confound;
- correction method.

## D. Mutation testing
- negative operators executed;
- positive operators executed;
- applicable counts;
- rejection/acceptance rates;
- unsupported coverage.

## E. Parser set
- total unique candidates;
- counts by model;
- counts by category;
- counts by domain;
- human-label status.

## F. Human validation
- Pass 1 count;
- Pass 2 count;
- real certificate count;
- handbook calibration examples;
- qualification cases;
- schema status;
- pilot readiness.

## G. Leakage
- exact duplicates;
- cross-split duplicates;
- pair candidates;
- connected clusters;
- derived variants actually evaluated;
- unresolved review.

## H. Registry/authority
- expected experiments;
- registered;
- coverage;
- complete provenance;
- partial provenance;
- critical unresolved;
- zero-row bugs detected.

## I. Canonical evidence
- canonical families;
- derived variants;
- model-family rows;
- populated scientific fields;
- null reasons.

## J. Claims
- confirmed;
- partial;
- missing;
- downgraded;
- donor-specificity correction.

## K. Tests
- exact commands;
- exact outputs.

## L. Sharanga
- confirmation that no jobs ran;
- repository-relative path status;
- safe future sync commands.

Stop after reporting. Do not start Wave 2–4.

---

# 16. Final instruction

Do not optimize for a passing gate.

The most important scientific correction in this cycle is:

```text
zero evaluable rows are not a zero effect
```

Any code, summary, status, claim, or document that violates this rule must be corrected.

A truthful FAIL is a successful outcome.
