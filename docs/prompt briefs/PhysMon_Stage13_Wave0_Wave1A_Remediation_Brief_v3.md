# PhysMon Stage 13 — Wave 0 / Wave 1A Remediation and Evidence-Foundation Brief

**Version:** 3.0  
**Purpose:** Repair the first Stage 13 implementation cycle so that the governance system measures scientific completion rather than file existence.  
**Governing documents:**  
1. `PhysMon Research Proposal` and supplementary documentation  
2. `PhysMon Part II — Next-Phase Scientific and Experimental Plan`, version 1.1  
3. `PhysMon Stage 13 — Controlled Part II Execution Brief`, version 2.0  
4. The latest external audit of the first Stage 13 implementation cycle  

**Scope:** Wave 0 remediation and Wave 1A remediation only.  
**Forbidden in this cycle:** Wave 2–4 confirmatory experiments, new causal-site searches, new probe selection, new thresholds, automatic follow-up jobs, and all GPU submissions.

---

# 0. Mission and current status

The first Stage 13 cycle created useful scaffolding but did **not** complete Wave 0 or Wave 1A.

The current authoritative status must be treated as:

```text
Wave 0 scientific gate: FAIL — HISTORICAL_AUTHORITY_UNRESOLVED
Wave 1A gate: FAIL — VALIDATION_AND_AUDIT_MATERIALS_INCOMPLETE
Paper eligibility: FALSE
Permission to start Wave 2: NO
```

Do not preserve or repeat the earlier `Wave 0: PASS` conclusion. The current gate passed because it checked that files existed, not that those files contained scientifically complete and internally consistent evidence.

Your job in this cycle is to repair the governance implementation so that:

1. every paper-relevant historical result is traceable;
2. every known corrected, partial, stale, or panel-mismatched result is resolved;
3. the canonical evidence tables have the correct scientific unit and benchmark accounting;
4. discovery and confirmation contamination is documented exactly;
5. the claim–evidence matrix reflects the real evidence;
6. Wave 1A materials are ready for actual human and parser annotation work;
7. gate logic fails honestly whenever substantive requirements remain unmet.

The success criterion is not “all scripts run.” The success criterion is that the resulting evidence foundation is trustworthy enough to govern later confirmatory science.

---

# 1. Mandatory execution contract

## 1.1 Read and inspect before modifying

Before editing:

1. Read the complete governing documents listed above.
2. Read the repository `README.md`.
3. Read the current Stage 13 governance configuration.
4. Read the decision logs and status reports for Stages 6–12.
5. Inspect all existing Stage 13 files and tests.
6. Inspect the Git branch, current commit, dirty state, and untracked files.
7. Inspect the local repository tree and the Sharanga sync configuration.
8. Identify which requested scripts already exist and should be corrected rather than duplicated.
9. Produce a remediation preflight report before changing scientific artifacts.

Create:

```text
docs/stage13/stage13_remediation_preflight.md
```

It must list:

- repository root;
- current branch and commit;
- dirty/untracked files;
- local results roots;
- Sharanga paths referenced by the project;
- benchmark manifests found;
- decision logs found;
- Slurm/job-history sources found;
- Stage 13 scripts and tests found;
- missing files from the previous audit package;
- schema mismatches;
- exact tasks that will modify existing files;
- unresolved questions.

If the canonical benchmark manifest, decision log, or result root cannot be identified, stop and ask for clarification.

## 1.2 No GPU or confirmatory work

Do not submit any Slurm or GPU job.

Do not:

- launch Qwen-3B, Qwen-14B, Mistral, DeepSeek, Qwen, or Llama jobs;
- rerun head sweeps;
- select new heads or layers;
- run Wave 2 monitoring confirmation;
- run Wave 3 causal confirmation;
- run Wave 4 mechanism experiments.

This cycle is CPU/file-system/governance work only.

## 1.3 No fabrication

Never invent:

- historical job IDs;
- model revisions;
- tokenizer hashes;
- Git commits;
- command lines;
- family IDs;
- source experiment IDs;
- human labels;
- parser labels;
- solver certificates;
- confirmation status.

When provenance is unavailable, record it as unresolved and make the result non-paper-eligible.

## 1.4 Preserve all evidence

Do not delete or overwrite:

- raw results;
- summaries;
- partial files;
- corrected files;
- stale summaries;
- failed outputs;
- nested archives;
- logs.

All corrections must produce new versioned outputs and explicit supersession links.

Use atomic writes and refuse overwrite unless `--overwrite` is explicitly supplied.

## 1.5 Canonical scientific unit

The canonical physics family is the independent unit.

The benchmark inventory is:

```text
155 canonical families
```

This consists of the original benchmark plus the 15-family expansion.

Do not count:

- `assembly_summary.json`;
- `renamed_manifest.json`;
- metadata JSON files;
- variable-renamed derivatives;

as new canonical families.

Variable-renamed examples must point to their parent canonical family through a transformation/derived-variant relation.

## 1.6 Sharanga HPC contract

This cycle is local/CPU-only, but every path and artifact must remain compatible with the Sharanga workflow.

The project uses:

```text
local Mac repository: project repository under the user's local PhysMons directory
Sharanga repository: ~/PhysMons/
```

Follow the repository sync invariant:

```bash
make sync-up
make sync-check
make sync-down
```

Rules:

1. Use repository-relative paths in code and configuration.
2. Do not hard-code `/Users/shubhammishra/...` or a specific Sharanga home path.
3. Read paths from the repository root, config, environment variables, or CLI flags.
4. Large activations, model weights, caches, and temporary tensors remain outside ordinary Git/sync paths.
5. Do not sync or overwrite Sharanga scratch data in this cycle.
6. If historical Sharanga metadata is needed, inspect existing logs/manifests read-only.
7. Do not claim a historical job ID unless it is recoverable from Slurm logs, filenames, or decision logs.
8. Prepare future scripts to record Slurm job ID, node, GPU type, CUDA version, environment, runtime, exit code, and peak memory, but do not submit jobs now.
9. Add no Sharanga-specific partition/account/QoS values unless read from existing templates or current cluster documentation.
10. At the end, provide exact safe commands for `sync-up`, `sync-check`, and later `sync-down`, but do not perform destructive sync operations automatically.

## 1.7 Stop rule

Complete the remediation deliverables and gate reports, then stop.

Do not advance to Wave 2 even if Wave 0 passes.

---

# 2. Correct the current gate status first

## Task R0.1 — Replace the false Wave 0 PASS

Before deeper remediation, update the Stage 13 gate logic and current status so that the repository no longer states that Wave 0 passed.

Create a new gate run, preserving the old file for provenance:

```text
results/stage13/wave0/wave0_gate_v2.json
docs/stage13/wave0_gate_v2_report.md
```

The current expected result is:

```text
FAIL — HISTORICAL_AUTHORITY_UNRESOLVED
```

until all mandatory content checks pass.

Do not overwrite the earlier gate artifact. Mark it superseded in the registry and authority audit.

## Task R0.2 — Content-based gate implementation

Rewrite or replace the Wave 0 gate script so that it validates substantive content.

The gate must fail if any of the following is true:

1. Known Stage 6–12 experiments are absent from the registry without an explicit exclusion record.
2. Any paper-eligible experiment lacks:
   - raw artifact;
   - summary;
   - model identity;
   - dataset/manifest identity;
   - source experiment ID;
   - provenance or correction status.
3. Any critical artifact remains `unresolved_pending_registry_link`.
4. The canonical manifest does not contain exactly 155 canonical family IDs.
5. Metadata files are represented as families.
6. Variable-renamed derivatives are represented as new canonical families.
7. Model-family rows do not have an explicit `model_id`.
8. Canonical verification was run against a different table hash from the final table.
9. The partition freeze lacks exact family IDs or an explicit `none_available`.
10. The claim matrix lacks links to experiment IDs.
11. A headline claim depends only on a superseded, partial, failed, or unresolved artifact.
12. Critical known cases remain unresolved:
    - partial versus full Llama sweep;
    - original versus corrected variable-renaming labels;
    - Qwen-selected versus DeepSeek-valid panels;
    - incomplete Qwen-3B run;
    - renamed donor controls;
    - nested Stage 6 file differences.
13. The registry uses non-approved statuses.
14. The registry contains duplicate run identities or broken supersession chains.
15. The artifact audit reports unresolved critical issues.

The gate JSON must include:

```text
gate_name
gate_version
timestamp
git_commit
git_dirty
input_hashes
checks
critical_failures
warnings
status
paper_eligibility
permission_for_wave2
```

`permission_for_wave2` must remain `false` throughout this remediation cycle.

---

# 3. Build the actual historical experiment registry

## Task R1.1 — Correct the registry schema

Use the machine-authoritative file:

```text
docs/registry/experiment_registry.jsonl
```

and generate:

```text
docs/registry/experiment_registry.csv
```

The registry must use exactly these statuses:

```text
complete_authoritative
corrected_authoritative
complete_exploratory
superseded
partial_not_reportable
failed
pending
diagnostic_only
```

Add a separate provenance field:

```text
provenance_status = complete | partial | unresolved
```

Required fields:

```text
experiment_id
parent_experiment_id
run_attempt_id
stage
task_id
experiment_class
scientific_question
hypothesis
null_interpretation
claim_level
model_id
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
provenance_status
raw_output_paths
summary_paths
stdout_path
stderr_path
supersedes_experiment_id
correction_history
paper_eligibility
discovery_or_confirmation
claim_supported
notes
```

## Task R1.2 — Discover historical experiments

Do not create one registry row per artifact. Discover experiments/runs using:

- decision logs;
- stage status reports;
- Slurm scripts;
- job output logs;
- summary JSON;
- raw JSON/JSONL/CSV/NPY outputs;
- directory names;
- nested archives;
- correction notes;
- known result anchors.

Build an intermediate discovery report:

```text
docs/registry/historical_experiment_discovery.md
results/stage13/wave0/historical_experiment_candidates.jsonl
```

Each candidate record should include:

```text
candidate_id
stage
probable_experiment_name
evidence_paths
probable_job_ids
probable_model
probable_panel
confidence
ambiguities
recommended_registry_action
```

## Task R1.3 — Minimum required historical coverage

At minimum, register and resolve all experiments associated with:

### Monitoring
- Qwen mean-state full sweep;
- Qwen per-variant probe sweep;
- variance probe;
- ensemble probe;
- MLP probe;
- earliest-layer/embedding baseline;
- held-out-domain evaluation;
- no-Cue-C result;
- expansion inference;
- expanded retrain;
- variable-renaming probe original and corrected;
- Cue C probe sweep and held-out inference;
- multi-site probe;
- H14/H15 output probes;
- generic correctness probe;
- residualized correctness analysis;
- entropy, black-box, CoT, answer+rationale baselines.

### Qwen causal
- full L16 single-head sweep;
- H11 layer sweep;
- H24 layer sweep;
- pairwise/multi-head interactions;
- H15 gating;
- random direction;
- random site;
- nearby layer;
- unrelated-family donor;
- same-answer donor;
- stable donor;
- general damage;
- variable-renaming H11;
- donor-on-renamed same-answer;
- donor-on-renamed stable;
- Cue C H11/H13 intervention.

### Llama
- stale partial head summary;
- full 32-head sweep;
- old MHK;
- corrected MHK v2;
- any combination sweep;
- panel eligibility information.

### DeepSeek
- within-model monitoring;
- Qwen-to-DeepSeek transfer;
- DeepSeek-to-Qwen transfer;
- H20/H26 exploratory runs;
- top-4 MHK;
- valid-panel rerun;
- pending/absent full head sweep.

### Scaling and pending
- Qwen2.5-3B incomplete behavioural run;
- Qwen2.5-14B;
- Mistral-7B;
- any reasoning-model scale runs;
- formula leakage;
- latent family geometry;
- precursor characterization;
- cross-cue layer sweep.

### Benchmark/data
- original 140-family generation;
- 15-family expansion;
- variable-renaming derived set;
- parser fixes;
- benchmark repairs;
- nested Stage 6 archive differences.

## Task R1.4 — Irrecoverable provenance policy

If a historical experiment is complete but lacks sufficient provenance:

- do not mark it authoritative;
- mark `paper_eligibility=false`;
- use `complete_exploratory` only if the output is complete and interpretable;
- set `provenance_status=partial` or `unresolved`;
- document exactly what is missing.

If the output is incomplete, use `partial_not_reportable`.

If a result is contradicted by a corrected run, mark it `superseded`.

## Task R1.5 — Registry verification

Upgrade:

```text
scripts/stage13/verify_registry.py
```

It must check:

- exact status vocabulary;
- unique run IDs;
- valid parent and supersession links;
- no circular supersession;
- authoritative paths exist;
- authoritative records have raw and summary artifacts;
- authoritative records have explicit model and family panel;
- all known historical candidates are registered or explicitly excluded;
- all claim-matrix experiment IDs exist;
- all canonical evidence source experiment IDs exist;
- no paper-eligible experiment has unresolved provenance;
- no paper-eligible experiment depends on stale/partial artifacts.

Write:

```text
results/stage13/wave0/registry_verification_v2.json
```

---

# 4. Resolve artifact authority, not merely inventory it

## Task R2.1 — Upgrade the authority audit

Modify:

```text
scripts/stage13/run_artifact_authority_audit.py
```

Produce:

```text
docs/registry/artifact_authority_audit_v2.json
docs/registry/artifact_authority_audit_v2.md
```

For each experiment, identify:

- raw artifact set;
- generated summary;
- partial summary;
- corrected summary;
- stale summary;
- nested archive version;
- prose report;
- decision-log statement.

Regenerate summary values from raw outputs where feasible.

Each resolution record must include:

```text
experiment_id
artifact_paths
issue_type
raw_record_count
stated_record_count
regenerated_statistics
reported_statistics
panel_identity
authority_decision
authoritative_paths
superseded_paths
reason
criticality
manual_review_required
status
```

## Task R2.2 — Mandatory known-case resolutions

Resolve explicitly:

1. **Llama sweep**
   - partial summary versus full 32-head summary;
   - identify the authoritative file;
   - register the partial file as superseded.

2. **Variable-renaming probe**
   - original all-positive/wrong-label result;
   - corrected labels and corrected AUROC;
   - preserve both;
   - corrected run must explicitly supersede the original.

3. **DeepSeek**
   - distinguish Qwen-selected panel from DeepSeek-positive valid panel;
   - prevent panel-mismatched results from supporting a clean DeepSeek causal claim.

4. **Qwen2.5-3B**
   - validate the exact number of completed families and variants;
   - mark partial and not paper-reportable.

5. **Donor-on-renamed controls**
   - verify raw row counts;
   - verify both reported 0.0 means;
   - identify exact family panel;
   - classify as completed controls if raw evidence supports this.

6. **Nested Stage 6 files**
   - compare extracted and nested versions;
   - identify changed files;
   - mark the authoritative extracted versions;
   - preserve nested versions as historical.

7. **Stale canonical verification**
   - identify which table the 649-row verification used;
   - mark that verification artifact superseded;
   - regenerate after final evidence-table build.

8. **Formula leakage**
   - verify family count and mixed verdict;
   - ensure it is not described as pending.

9. **Empty/placeholder outputs**
   - distinguish placeholders from actual result files;
   - never classify them as scientific nulls.

## Task R2.3 — Critical unresolved count

The authority report must calculate:

```text
n_artifacts_scanned
n_experiments_resolved
n_experiments_partially_resolved
n_critical_unresolved
n_noncritical_unresolved
```

Wave 0 cannot pass if `n_critical_unresolved > 0`.

---

# 5. Rebuild canonical evidence correctly

## Task R3.1 — Freeze the 155-family manifest

Create:

```text
data/manifests/physmon_canonical_155.jsonl
data/manifests/physmon_canonical_155.csv
```

Each row:

```text
canonical_family_id
benchmark_source
template_id
domain
cue_type
original_or_expansion
source_family_path
solver_certificate_path
parent_family_id
is_canonical
```

Rules:

- exactly 155 rows have `is_canonical=true`;
- metadata files are excluded;
- the 15 expansion families are identified;
- variable-renamed examples are not canonical rows;
- no duplicate canonical IDs;
- every source family file exists.

Create a separate transformation manifest:

```text
data/manifests/physmon_derived_variants.jsonl
```

Fields:

```text
derived_id
parent_canonical_family_id
transformation_type
source_path
rendering_ids
notes
```

Variable-renaming examples belong here.

## Task R3.2 — Use normalized long-form evidence

Create:

```text
results/canonical/model_family_evidence.parquet
results/canonical/model_family_evidence.csv
results/canonical/model_variant_evidence.parquet
results/canonical/model_variant_evidence.csv
```

### Family table

One row per:

```text
(model_id, canonical_family_id, benchmark_version)
```

Do not use model-specific columns such as `qwen_S_lp` and `llama_S_lp`.

Required fields:

```text
model_id
model_role
model_revision
canonical_family_id
template_id
domain
cue_type
benchmark_version
split_membership
family_manifest_hash
solver_certificate_hash
automated_solver_status
human_validation_status
adjudication_status
n_variants_expected
n_variants_observed
n_variants_parsed
family_parse_rate
base_variant_correct
all_variants_correct
family_correctness_rate
S_lp
S_lp_binary
answer_flip_rate
distributional_sensitivity
primary_monitor_score
monitor_layer
monitor_site
entropy_score
confidence_score
black_box_counterfactual_score
cot_classifier_score
answer_rationale_score
correctness_probe_score
causal_panel_eligible
causal_site
intervention_type
normalized_effect
raw_correct_logprob_effect
raw_S_lp_effect
sign_consistent
general_damage_metric
exclusion_flag
exclusion_reason
evidence_status
paper_eligibility
source_experiment_ids
```

### Variant table

One row per:

```text
(model_id, canonical_family_id, derived_id_or_null, variant_id, generation_id)
```

Required fields include:

```text
model_id
canonical_family_id
derived_id
variant_id
generation_id
prompt_hash
prompt_text_or_path
parsed_answer
canonical_answer
correct
correct_answer_logprob
entropy
monitor_score
source_experiment_ids
```

Do not use generic `PRIMARY_DENSE` as the only model identifier.

## Task R3.3 — Build only from authoritative source mappings

Every populated scientific value must link to one or more registry experiment IDs.

Do not populate from a prose report if a raw artifact is unavailable.

Do not carry a value from a superseded run.

Leave structural nulls as null and record why.

## Task R3.4 — Verification and hash binding

Upgrade:

```text
scripts/stage13/verify_canonical_evidence.py
```

Checks:

- canonical manifest has exactly 155 canonical IDs;
- no metadata file appears as a family;
- derived variants map to valid parents;
- model IDs are explicit;
- no duplicate table primary keys;
- every family aggregate recomputes from variant rows where data exist;
- every source experiment ID exists;
- no value comes from a superseded or partial experiment;
- nulls are classified as structural or unexpected;
- table hashes match the gate input hashes;
- verification ran after the final build.

Write:

```text
results/stage13/wave0/canonical_evidence_verification_v2.json
```

Include:

```text
family_table_hash
variant_table_hash
manifest_hash
n_canonical_families
n_model_family_rows
n_variant_rows
n_derived_variants
n_unexpected_nulls
unexpected_nulls_by_field
```

---

# 6. Complete the discovery/confirmation freeze

## Task R4.1 — Exact analytical-choice ledger

Replace the placeholder partition document with:

```text
docs/registry/partition_freeze_v2.md
docs/registry/partition_freeze_v2.json
```

For every analytical choice:

```text
choice_id
choice
selected_value
selection_experiment_ids
selection_family_ids
selection_models
date_or_stage
direct_sample_exposure
indirect_selection_exposure
consequence_for_confirmation
```

Mandatory choices:

- answer-flip to `S_lp` metric change;
- 0.5-nat threshold;
- primary probe architecture;
- L16 per-variant site;
- L18 mean-state site;
- variance monitor;
- baseline selection;
- Qwen L16H11;
- Qwen donor policy;
- Llama L21H2;
- multi-head combinations;
- normalized recovery metric;
- Cue C site;
- variable-renaming analysis choices.

## Task R4.2 — Exact family classification

For each of the 155 canonical families, assign:

```text
discovery
internal_confirmatory
external_confirmatory
unassigned
```

with a reason.

If no untouched internal-confirmatory set remains, state:

```text
internal_confirmatory_status: none_available
```

and list the prospective confirmation set that must be built.

Do not treat leave-one-out prediction as untouched confirmation when the layer or representation was selected globally.

## Task R4.3 — Causal panel contamination audit

For every family used in the Qwen and Llama causal panels, report whether it participated in:

- sensitivity metric selection;
- threshold selection;
- probe training;
- layer selection;
- head selection;
- donor selection;
- recovery-metric development;
- multi-head selection.

This report determines whether a result is discovery, internal replication, or prospective confirmation.

---

# 7. Rebuild the claim–evidence matrix

## Task R5.1 — Full matrix

Create:

```text
docs/registry/claim_evidence_matrix_v2.json
docs/registry/claim_evidence_matrix_v2.md
```

Required fields:

```text
claim_id
claim_text
claim_level
required_evidence
experiment_ids
authoritative_artifacts
family_count
model_count
discovery_or_confirmation
human_validation_dependency
current_estimate
confidence_interval
status
allowed_wording
prohibited_wording
missing_evidence
next_required_experiment
consequence_if_null
paper_section
```

## Task R5.2 — Minimum claims

Include at least:

1. Solver-certified family invariance.
2. Qwen behavioural sensitivity exists.
3. Hidden states predict sensitivity above surface text.
4. Hidden states add information beyond entropy/output evidence.
5. Hidden states add information beyond generic correctness activations.
6. Residualized sensitivity signal remains.
7. Qwen H11 has a localized sufficiency effect.
8. Qwen H11 partial necessity.
9. Qwen causal effect exceeds random and unrelated controls.
10. Donor specificity.
11. Variable-renaming behavioural robustness.
12. Variable-renaming monitor transfer.
13. Variable-renaming causal robustness.
14. Llama H2 replication.
15. DeepSeek monitoring transfer.
16. DeepSeek causal boundary.
17. Cue A/B partial transfer.
18. Cue C distinct/boundary behavior.
19. Expansion-family monitor generalization.
20. H15 gating null.
21. No universal shared shortcut direction.
22. External natural-family transfer.
23. Diagnostic versus causal subspace relationship.
24. Upstream partial pathway.
25. Selective correction.

Claims 4, 8, 14, 22, 23, 24, and 25 may remain missing/partial. The matrix must say so.

## Task R5.3 — Human-validation dependency

No claim depending on benchmark construct validity may be marked fully confirmed while required independent human validation is incomplete.

---

# 8. Repair Wave 1A benchmark-integrity work

## Task R6.1 — Leakage audit remediation

Upgrade:

```text
scripts/stage13/run_leakage_audit.py
```

Use:

- exact prompt hashes;
- canonical symbolic hashes;
- variable-renaming-invariant structural hashes;
- masked rendering skeletons;
- cue-insertion template hashes;
- numeric-sibling detection;
- lexical similarity;
- semantic/template similarity candidate generation.

Include original, expansion, and derived-variant manifests.

Create:

```text
results/stage13/benchmark_integrity/leakage_audit_v2.json
results/stage13/benchmark_integrity/leakage_review_v2.csv
```

The 300 prior near-duplicate pairs must be:

- deduplicated into equivalence clusters;
- classified by detector;
- prioritized for human review;
- marked cross-split or within-split;
- linked to canonical family IDs.

Do not return `PASS` while cross-split near duplicates remain unresolved.

Allowed statuses:

```text
PASS
FAIL_EXACT_CROSS_SPLIT_DUPLICATE
INCOMPLETE_PENDING_NEAR_DUPLICATE_REVIEW
```

## Task R6.2 — Balance and confound audit remediation

Upgrade:

```text
scripts/stage13/run_balance_audit.py
```

At the family level, compute:

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

Report:

- distributions by sensitivity label;
- standardized effect sizes;
- Pearson and Spearman correlations;
- grouped-CV single-feature AUROC;
- grouped-CV combined surface-feature AUROC;
- chi-square or appropriate association tests;
- multiple-comparison correction;
- strongest confound;
- required mitigation.

Create:

```text
results/stage13/benchmark_integrity/balance_audit_v2.json
```

Do not label a descriptive-only audit as PASS.

## Task R6.3 — Solver mutation adapter

Inspect the existing benchmark and solver code.

Create an applicability-aware adapter rather than an empty scaffold.

Files:

```text
scripts/stage13/run_solver_mutation_tests.py
src/physmon/validation/mutation_operators.py
tests/stage13/test_mutation_operators.py
```

Operators should include, where applicable:

- insert cue into governing expression;
- remove a necessary assumption;
- sign inversion;
- replace a governing variable with cue;
- change target quantity;
- introduce a relevance-changing constraint;
- dimensional corruption;
- frame-assumption change;
- boundary-condition change.

Also include:

- semantics-preserving positive controls;
- exact no-op controls.

Each operator must declare applicability and expected outcome.

If the existing solver architecture cannot test a mutation class, record `coverage_not_supported` rather than pretending a pass.

Output:

```text
results/stage13/benchmark_integrity/mutation_test_records_v2.jsonl
results/stage13/benchmark_integrity/mutation_test_summary_v2.json
```

## Task R6.4 — Parser audit candidate remediation

Create a stratified set of at least 100 **unique** candidate outputs using actual model outputs where possible, supplemented by designed edge cases.

Cover:

- Qwen, Llama, and DeepSeek;
- multiple domains;
- integers/decimals;
- scientific notation;
- fractions;
- equivalent units;
- multiple numbers;
- rounding boundaries;
- wrong units;
- refusals;
- long prose;
- LaTeX;
- ambiguous final answers;
- model-specific quirks.

Create:

```text
docs/validation/parser_audit_candidates_v2.jsonl
docs/validation/parser_labeling_instructions.md
```

Human labels must remain blank.

Add a duplicate-text check so the set is not dominated by repeated outputs.

The parser audit script should refuse to compute final metrics while labels are missing.

---

# 9. Rebuild the human-validation package

## Task R7.1 — Two-pass blinded packets

### Pass 1

Each packet must show **all natural-language variants in the canonical family**.

Do not show:

- designated cue;
- intended governing law;
- solver derivation;
- canonical answer;
- sensitivity;
- model outputs;
- probe/causal results.

Validators independently record:

- their solution;
- governing law;
- relevant variables;
- candidate non-governing variables;
- whether assumptions are sufficient;
- whether answer is unique;
- whether all variants are semantically equivalent;
- whether answer should be invariant;
- wording naturalness;
- difficulty shifts;
- uncertainty.

### Pass 2

After Pass 1 is locked, show:

- proposed cue;
- stated assumptions;
- governing equation;
- symbolic derivation;
- canonical answer;
- executable/symbolic certificate;
- dimensional checks;
- invariance checks.

Validators assess the certificate.

Create:

```text
docs/validation/stage13_validation_packet_pass1_v2.jsonl
docs/validation/stage13_validation_packet_pass2_v2.jsonl
```

## Task R7.2 — Handbook

Expand:

```text
docs/validation/validator_handbook_v2.md
```

It must include:

- formal cue-irrelevance definition;
- answer-invariance definition;
- distinction between irrelevant, redundant, and relevant variables;
- assumption-sufficiency rules;
- frame and coordinate transformation guidance;
- unit-compatible distractor guidance;
- semantic-drift examples;
- naturalness/difficulty rules;
- borderline-case policy;
- repair versus exclusion policy;
- independence rules;
- adjudication protocol;
- revalidation rules.

Use a dedicated calibration bank, not confirmatory families.

## Task R7.3 — Qualification test

Create a 12–15 case qualification test with:

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

Create:

```text
docs/validation/qualification_test_v2.md
docs/validation/qualification_answer_key_DRAFT_REQUIRES_PI_REVIEW.md
```

The answer key is a draft for PI/domain-expert review, not an independent human validation result.

## Task R7.4 — Annotation schema

Expand:

```text
docs/validation/annotation_schema_v2.json
```

Include:

```text
validator_id
family_id
packet_version
pass_number
started_at
completed_at
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
solver_derivation_correct
certificate_valid
canonical_answer_correct
overall_verdict
confidence
repair_recommendation
notes
```

## Task R7.5 — Validation tracking and agreement

Upgrade:

```text
docs/validation/validation_status_v2.csv
scripts/stage13/compute_validation_agreement.py
```

The agreement script must compute:

- raw agreement;
- Cohen’s kappa or appropriate alternative;
- cue-relevance agreement;
- answer-invariance agreement;
- assumption-sufficiency agreement;
- semantic-equivalence agreement;
- agreement by cue type;
- agreement by domain;
- adjudication rate;
- missing-field rate.

It must not mark any family valid until required human fields exist.

---

# 10. Tests

Add or correct tests for:

- gate fails when critical artifacts unresolved;
- gate fails when registry lacks historical experiments;
- gate fails when canonical manifest count is not 155;
- metadata files excluded from manifest;
- renamed variants map to parents;
- explicit model IDs required;
- final-table hash matches verification hash;
- exact status vocabulary;
- supersession chain validation;
- authority audit known cases;
- partition freeze requires exact IDs or `none_available`;
- claim matrix requires experiment links;
- leakage audit includes expansion and derived variants;
- near-duplicate unresolved status is not PASS;
- grouped CV prevents sibling leakage;
- mutation-operator applicability;
- positive and negative mutation controls;
- parser candidate uniqueness and stratification;
- Pass 1 packets contain all variants and no certificate information;
- Pass 2 packets contain actual certificate fields;
- agreement metrics;
- no overwrite without explicit flag;
- repository-relative path behavior;
- Sharanga-safe path/config behavior.

Run:

```bash
.venv/bin/ruff check scripts/stage13 src/physmon tests/stage13
python3 -m pytest tests/stage13
python3 -m pytest
```

Report exact results.

---

# 11. Final gate reports for this cycle

Create:

```text
results/stage13/wave0/wave0_gate_v3.json
docs/stage13/wave0_gate_v3_report.md
results/stage13/benchmark_integrity/wave1a_gate_v2.json
docs/stage13/wave1a_gate_v2_report.md
```

## Wave 0 PASS criteria

Wave 0 may pass only if:

- all paper-relevant historical experiments are registered;
- all critical known artifact conflicts are resolved;
- `n_critical_unresolved == 0`;
- the 155-family manifest validates;
- canonical tables use explicit model IDs;
- derived variants are not counted as canonical families;
- final table hashes match verification;
- partition freeze contains exact IDs or `none_available`;
- claim matrix contains experiment links and evidence status;
- no paper-eligible result has unresolved provenance;
- all Wave 0 tests pass.

## Wave 1A PASS criteria

Wave 1A may pass only if:

- mutation adapter executes supported operators and reports coverage;
- leakage audit has no unresolved exact cross-split duplicates;
- near-duplicate review workflow is operational;
- balance/confound audit is substantive, not descriptive only;
- parser candidate set is stratified and ready for human labels;
- two-pass validation packets are correct and blinded;
- handbook and qualification test are complete;
- agreement code is ready;
- at least the pilot assignment package is ready for actual humans.

Human agreement and parser metrics may remain unavailable before humans label the data. In that case distinguish:

```text
Wave 1A software/materials gate: PASS
Wave 1A human pilot gate: PENDING
```

Do not collapse these into one false pass.

Even if Wave 0 and Wave 1A software pass, set:

```text
permission_for_wave2: false
```

until the PI explicitly approves the next cycle.

---

# 12. Required report-back format

At completion, report:

## A. Summary

- what was fixed;
- what remains unresolved;
- whether Wave 0 passed;
- whether Wave 1A software/materials passed;
- whether human pilot remains pending;
- confirmation that no GPU or Slurm jobs ran.

## B. File changes

List every created or modified file.

## C. Registry

- total experiment records;
- authoritative;
- corrected;
- exploratory;
- superseded;
- partial;
- pending;
- unresolved provenance;
- historical-job coverage percentage.

## D. Artifact authority

- artifacts scanned;
- experiments resolved;
- critical unresolved;
- known cases resolved;
- regenerated summary discrepancies.

## E. Canonical evidence

- canonical family count;
- derived-variant count;
- model-family row count;
- variant row count;
- explicit model IDs;
- unexpected nulls;
- table and manifest hashes.

## F. Discovery/confirmation

- discovery family count;
- internal-confirmatory family count;
- external-confirmatory family count;
- whether `none_available` applies;
- major selection-contamination findings.

## G. Claim matrix

- confirmed;
- partial;
- missing;
- blocked by human validation;
- blocked by prospective confirmation.

## H. Wave 1A

- mutation coverage;
- leakage flags;
- near-duplicate clusters;
- strongest confound;
- parser candidate coverage;
- validation packet counts;
- handbook/qualification readiness;
- human-label status.

## I. Tests

Exact commands and outputs.

## J. Sharanga readiness

- repository-relative paths confirmed;
- sync commands;
- no hard-coded local path;
- no job submitted;
- any missing Sharanga metadata.

## K. Next approval request

Propose the next bounded cycle, but do not execute it.

---

# 13. Final instruction

Do not optimize for a green gate. Optimize for a truthful gate.

A FAIL caused by unresolved historical provenance is scientifically better than a PASS produced by placeholder files.

The cycle is successful when the repository can answer, for every headline number:

1. Which exact experiment produced it?
2. Which model and checkpoint?
3. Which family panel?
4. Which raw records?
5. Which summary script?
6. Which code/config revision?
7. Was it discovery or confirmation?
8. Has it been superseded?
9. Is it independently validated?
10. What wording is scientifically allowed?

Stop after delivering the corrected Wave 0 and Wave 1A remediation reports.
