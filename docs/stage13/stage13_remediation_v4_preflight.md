# Stage 13 v4 Remediation Preflight

Date: 2026-07-03

## Scope

This preflight covers the bounded CPU-only Wave 0 / Wave 1A Scientific Remediation Brief v4.0. No Sharanga, Slurm, GPU, Wave 2, Wave 3, or Wave 4 work is authorized in this cycle.

## Repository

- Repository root: `.`
- Local/Sharanga sync invariant: `make sync-up`, `make sync-check`, `make sync-down`
- Sharanga repository target from `Makefile`/`README.md`: `~/PhysMons/`
- Current branch: `master`
- Current commit: `ea914541f883f29308858346f51ec77ce73fdfb4`
- Dirty/untracked state: repository is already heavily dirty with Stage 6-13 result/doc/script artifacts. This remediation must not revert unrelated changes.

## Current Gates

- `results/stage13/wave0/wave0_gate_v3.json`: `FAIL`, `paper_eligibility=false`, `permission_for_wave2=false`, critical failure `authority_no_critical_unresolved`.
- `results/stage13/benchmark_integrity/wave1a_gate_v2.json`: `PASS`, `human_pilot_status=PENDING`, `paper_eligibility=false`, `permission_for_wave2=false`.
- v4 correction required: Wave 1A v2 PASS is scientifically invalid and must be superseded by a v3/v4 failure until content checks pass.

## Benchmark and Evidence Inputs Found

- Canonical manifest: `data/manifests/physmon_canonical_155.jsonl` and `.csv`.
- Derived manifest: `data/manifests/physmon_derived_variants.jsonl`.
- Canonical family evidence: `results/canonical/model_family_evidence.csv`.
- Canonical variant evidence: `results/canonical/model_variant_evidence.csv`.
- Original generated families: `results/stage6/generated_full_benchmark/`.
- Expansion rendered families: `results/stage10/benchmark_expansion/rendered/`.
- Variable-renaming derived families: `results/stage11/variable_renaming/rendered/`.

## Registry and Authority Inputs Found

- Registry: `docs/registry/experiment_registry.jsonl` and `.csv`.
- Authority audit v2: `docs/registry/artifact_authority_audit_v2.json` and `.md`.
- Claim matrix v2: `docs/registry/claim_evidence_matrix_v2.json` and `.md`.
- Partition freeze v2: `docs/registry/partition_freeze_v2.json` and `.md`.
- Current registry verification: `results/stage13/wave0/registry_verification_v2.json`.
- Current canonical verification: `results/stage13/wave0/canonical_evidence_verification_v2.json`.

## Validation and Wave 1A Inputs Found

- Parser candidates v2: `docs/validation/parser_audit_candidates_v2.jsonl`.
- Parser instructions: `docs/validation/parser_labeling_instructions.md`.
- Validation packets v2: `docs/validation/stage13_validation_packet_pass1_v2.jsonl`, `docs/validation/stage13_validation_packet_pass2_v2.jsonl`.
- Validator handbook v2: `docs/validation/validator_handbook_v2.md`.
- Qualification test v2: `docs/validation/qualification_test_v2.md`.
- Annotation schema v2: `docs/validation/annotation_schema_v2.json`.
- Balance audit v2: `results/stage13/benchmark_integrity/balance_audit_v2.json`.
- Mutation summary v2: `results/stage13/benchmark_integrity/mutation_test_summary_v2.json`.
- Leakage audit v2: `results/stage13/benchmark_integrity/leakage_audit_v2.json`.

## Donor-on-Renamed Evidence Inspection

The audit's urgent correction is verified locally:

- `results/stage12/science/donor_renamed/same_answer/same_answer_donor_results.csv`: 1 line total, header only, 0 evaluable rows.
- `results/stage12/science/donor_renamed/stable/stable_donor_results.csv`: 1 line total, header only, 0 evaluable rows.
- `same_answer_donor_summary.json`: `rows=0`, `mean_recovery=0.0`, `median_recovery=0.0`.
- `stable_donor_summary.json`: `rows=0`, `mean_recovery=0.0`, `median_recovery=0.0`.
- Event logs incorrectly report `SAME_ANSWER_DONOR_COMPLETE` and `STABLE_DONOR_COMPLETE`.

Interpretation: zero evaluable rows are not a measured zero effect. These runs must be reclassified as empty-panel incomplete/failed results and cannot support donor specificity or 100% specificity claims.

## Files Containing Renamed-Donor/Specificity Claims or Related Text

Search terms included `100% specificity`, `0.0 mean recovery`, `donor-on-renamed`, `same-answer donor`, `stable donor`, `68.1%`, `renamed donor`, and `specificity`.

Files requiring correction or careful supersession:

- `docs/decisions/decision_log.md`
- `docs/registry/claim_evidence_matrix_v2.json`
- `docs/registry/claim_evidence_matrix_v2.md`
- `docs/registry/artifact_authority_audit_v2.json`
- `docs/registry/artifact_authority_audit_v2.md`
- `docs/registry/experiment_registry.jsonl`
- `docs/registry/experiment_registry.csv`
- `results/stage12/science/donor_specificity/donor_specificity_summary.json`
- `scripts/analyse_donor_specificity.py`
- `scripts/run_same_answer_donor.py`
- `scripts/run_stable_donor.py`
- `results/stage12/science/donor_renamed/*/*summary.json` must be preserved but superseded, not edited.
- `results/stage12/science/donor_renamed/*/run_causal_patching_events.jsonl` must be preserved as misleading historical logs.

Prompt-brief files also contain these phrases as governance instructions and should not be edited as scientific claims.

## Slurm/Job Sources Inspected Read-Only

- Slurm templates: `slurm/templates/`.
- Submitted/log directory exists: `slurm/submitted/`.
- No `ssh`, `sbatch`, `srun`, or GPU command was run in this preflight.

## Missing or Unresolved Path Issues

- No full Slurm accounting database or cluster history is available locally in this cycle.
- Many registry rows still lack complete provenance fields such as exact job ID, command, tokenizer hash, and hardware.
- Existing generated family JSONs have only compact certificate indicators (`verifier_certified`) and not full inspectable solver certificates. v4 must generate separate pilot certificates from available template facts and mark limitations honestly.

## Planned v4 Corrections

1. Preserve v2 artifacts and create v3/v4 superseding artifacts.
2. Reclassify donor-on-renamed same-answer and stable runs as empty-panel incomplete/failed, with `raw_data_rows=0`, `summary_defaulted_zero=true`, and `scientific_null=false`.
3. Patch donor scripts so future zero-row panels produce failure status and null mean/median instead of false completion.
4. Replace the invalid balance audit with a standard-library, tie-aware, grouped-CV v3 audit.
5. Replace mutation status with representative positive/negative mutation records where supported and honest unsupported coverage where not.
6. Build balanced v3 parser candidates across Qwen, Llama, DeepSeek, and designed edge cases.
7. Create v3 certificate schema, pilot certificates, Pass 2 packets, handbook, qualification test, typed annotation schema, and agreement handling.
8. Upgrade leakage v3 to actually load and compare derived prompts.
9. Improve registry coverage and authority audit reports without claiming full historical authority.
10. Write `wave0_gate_v4` and `wave1a_gate_v4`, both with `permission_for_wave2=false`.
