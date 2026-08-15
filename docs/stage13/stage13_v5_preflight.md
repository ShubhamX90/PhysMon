# Stage 13 v5 Preflight

Generated before v5 scientific-artifact edits.

## Repository

- Repository root: `/Users/shubhammishra/Desktop/PhysMons`
- Branch: `master`
- Commit: `ea914541f883f29308858346f51ec77ce73fdfb4`
- Dirty/untracked state: repository is already heavily dirty with Stage 10-13 artifacts, scripts, results, validation materials, and prompt briefs. Existing user/project changes must be preserved.

## Current Gates

- Wave 0 v4: `FAIL`
- Wave 1A v4: `FAIL`, reason `HUMAN_PILOT_NOT_READY`
- Human pilot: `NOT_READY`
- Permission for Wave 2: `false`

## Part II

- Located Part II PDF: `docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf`
- Located Part II LaTeX source: not found in repository.
- Local TeX engine: `pdflatex` and `tectonic` not found.
- Local PDF generation fallback: Python `reportlab` is available.
- v5 action: preserve the existing PDF, create a controlled corrective source and compiled PDF at `docs/proposals/PhysMon_Part_II_v1.2.tex` and `docs/proposals/PhysMon_Part_II_v1.2.pdf`, plus revision notes documenting that this is a corrective repository source because the v1.1 LaTeX source is absent.

## Benchmark / Template Schemas

- Canonical manifest: `data/manifests/physmon_canonical_155.jsonl`
- Canonical family count: 155.
- Source YAML templates found for all 155 canonical families under `data/raw/templates/` and `data/raw/templates/stage10_expansion/`.
- Rendered family JSONs exist under `results/stage6/generated_full_benchmark/`; these are too thin for solver-derived certificates because they omit governing equations and parameter tables.
- Template YAML fields include `template_id`, `domain`, `cue_type`, `governing_law`, `governing_equation_sympy`, `target_quantity`, `target_units`, `parameters`, `correct_answer`, `cue_slot`, `prompt_template`, `verifier`, and `validation`.

## Solver / Verifier Entry Points

- Symbolic verifier: `src/physmon/benchmark/verifier.py`
- Main callable: `physmon.benchmark.verifier.SymbolicVerifier().verify(template_yaml_path)`
- Checks available: answer correctness, cue independence, physical plausibility, correct-answer parseability.
- Verifier input schema: YAML template with governing equation, parameters, cue slot, and correct answer.
- Verifier output schema: `VerificationResult(template_id, all_passed, checks)`.
- Existing tests: `tests/test_verifier.py`.

## Current Mutation Implementation

- Current Stage 13 script: `scripts/stage13/run_solver_mutation_tests.py`
- Current validation package: `src/physmon/validation/mutation_operators.py`
- Current v3 mutation result: `results/stage13/benchmark_integrity/mutation_test_summary_v3.json`
- Problem: v3 records certificate-level assigned outcomes; they are not actual verifier calls on mutated structured objects.
- v5 action: implement `src/physmon/validation/mutation_executor.py`, revise mutation operators, and create v5 outputs using the actual `SymbolicVerifier`.

## Current Certificate Generation

- v3 draft certificates: `docs/validation/certificates/`
- v3 Pass 2 packets: `docs/validation/stage13_validation_packet_pass2_v3.jsonl`
- Problem: v3 certificates are heuristic placeholders, not solver-derived structured derivations.
- v5 action: generate certificates only from structured YAML templates through `src/physmon/validation/certificate_generator.py`; mark unsupported or failed families explicitly.

## Current Parser Candidate Distribution

- Current v3 parser status: `results/stage13/benchmark_integrity/parser_audit_status_v3.json`
- v3 total candidates: 126.
- v3 model counts: Qwen 30, Llama 30, DeepSeek 30, designed edge cases 36.
- v3 issue: model-balanced but not category/domain balanced; several required categories have very low coverage.
- v5 action: build at least 140 candidates with model, category, and domain quotas.

## Current Validation Pilot

- Current Pass 1 packet: `docs/validation/stage13_validation_packet_pass1_v2.jsonl`
- Current Pass 2 packet: `docs/validation/stage13_validation_packet_pass2_v3.jsonl`
- Current issue: 25-family pilot is not explicitly stratified by domain/cue/template/risk and packet records lack domain/cue metadata.
- v5 action: deterministic stratified pilot of 24-30 families with `docs/validation/pilot_selection_v5.csv`.

## Current Leakage Pair Categories

- Current v3 leakage audit: `results/stage13/benchmark_integrity/leakage_audit_v3.json`
- v3 pair candidates: 1604.
- v3 issue: unresolved workload includes expected within-family/derived-parent relationships.
- v5 action: classify expected within-family and derived-parent pairs separately, and count only cross-family review candidates as unresolved leakage workload.

## Current Registry Expected-Experiment Construction

- Current v4 coverage: `results/stage13/wave0/registry_coverage_v4.json`
- v4 expected experiments: 202.
- v4 registered experiments: 67.
- v4 issue: denominator is still broad and partly derived from stage/result-directory heuristics rather than normalized actual runs/configurations.
- v5 action: build `expected_historical_runs_v5.jsonl` from result directories, event logs, raw/summary pairings, submitted scripts, and registry rows; reject pure stage numbers/template filenames as runs.

## Current Authority Scan Scope

- Current v4 authority audit: `docs/registry/artifact_authority_audit_v4.json`
- v4 critical unresolved: 16.
- v4 zero-row bugs detected: 2.
- v4 issue: audit remains registry-linked rather than full repository-wide artifact scan.
- v5 action: scan configured result roots for JSON/JSONL/CSV summaries/raw outputs, map orphans, detect zero-row outputs, and enforce authority rules.

## Current Canonical Evidence Populated Fields

- Current table: `results/canonical/model_family_evidence_v4.csv`
- Current rows: 295.
- Populated scientific fields such as monitor scores, entropy, black-box baseline, CoT/rationale/correctness probes, causal eligibility, site, effects, and damage metrics: 0 observed in v4 table.
- v5 action: create v5 evidence with source-linked fields where authoritative source mappings are recoverable; leave unresolved values explicitly null-reasoned.

## Current Claim Matrix Populated Fields

- Current matrix: `docs/registry/claim_evidence_matrix_v4.json`
- Current counts: 24 partial, 1 missing.
- Donor specificity claim is downgraded after v4.
- v5 action: populate estimates/panel counts where recoverable, keep human-validation/prospective-confirmation limits explicit, and preserve donor downgrade.

## Exact Files Expected To Be Modified Or Created

- `docs/proposals/PhysMon_Part_II_v1.2.tex`
- `docs/proposals/PhysMon_Part_II_v1.2.pdf`
- `docs/proposals/PhysMon_Part_II_v1.2_revision_notes.md`
- `docs/decisions/decision_log.md`
- `docs/stage13/mutation_verifier_integration.md`
- `src/physmon/validation/mutation_operators.py`
- `src/physmon/validation/mutation_executor.py`
- `src/physmon/validation/certificate_generator.py`
- `scripts/stage13/run_solver_mutation_tests.py`
- `scripts/stage13/generate_solver_certificates.py`
- `scripts/stage13/remediation_v5.py`
- v5 outputs under `results/stage13/`, `docs/registry/`, `docs/validation/`, `schemas/`, and `results/canonical/`
- tests under `tests/stage13/`

## Unresolved Ambiguities

- The original Part II v1.1 LaTeX source is not present; v5 will create a corrective v1.2 repository source and PDF rather than silently editing an unavailable source.
- Some source templates may verify under current code but still lack a fully rich human-readable derivation beyond the structured SymPy equation and substitutions; v5 certificates will state limitations rather than overclaim.
- Historical registry coverage cannot be made complete without fuller job provenance; v5 will compute a normalized denominator from recoverable run/configuration evidence and keep irrecoverable provenance explicit.
- Human validation labels do not exist; human pilot must remain pending.
