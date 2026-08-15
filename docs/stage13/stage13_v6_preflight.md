# Stage 13 v6 Remediation Preflight

Date: 2026-07-03

## Scope Guard

This preflight is for the bounded CPU-only Wave 0 / Wave 1A remediation cycle. No Sharanga access, Slurm commands, GPU execution, model inference, activation extraction, Wave 2-4 experiments, or new scientific site/threshold/panel selection are authorized.

## Repository State

- Repository root: `repo://.`
- Git branch: `master`
- Git commit: `ea914541f883f29308858346f51ec77ce73fdfb4`
- Dirty tracked files observed before v6 edits: `docs/decisions/decision_log.md`, `docs/model_registry.yml`, several scripts under `scripts/`, `slurm/templates/stage9_llm_judge.sh`, and `src/physmon/formal/constructs.py`.
- Untracked Stage 6-13 data, docs, results, schemas, validation materials, and scripts are present. These are treated as existing project artifacts and must be preserved.

## Current Gate States

- `results/stage13/wave0/wave0_gate_v5.json`: `FAIL`, `permission_for_wave2=false`.
- `results/stage13/benchmark_integrity/wave1a_gate_v5.json`: `PASS`, `permission_for_wave2=false`. This v5 pass is scientifically superseded by the v6 audit and must not be preserved.

## Governing Documents

- Complete Part II v1.1 PDF: `docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf`
  - `pdfinfo` reports 42 pages and file size 544250 bytes.
  - `pdftotext` extraction produced 2564 text lines.
- Current one-page correction incorrectly named v1.2:
  - `docs/proposals/PhysMon_Part_II_v1.2.tex`
  - `docs/proposals/PhysMon_Part_II_v1.2.pdf`
  - `docs/proposals/PhysMon_Part_II_v1.2_revision_notes.md`
- Complete v1.1 LaTeX source: not found in repository preflight. A complete v1.2 reconstruction is therefore blocked unless that source is later recovered.

## Files Containing False or Superseded Part II Versioning / Donor-Control Wording

Preflight search terms included `Part II v1.2`, `100% specificity`, `0.0 mean recovery`, `donor-on-renamed`, `renamed donor controls completed`, and `68.1%`.

Known files requiring v6 classification or correction:

- `docs/proposals/PhysMon_Part_II_v1.2.tex`
- `docs/proposals/PhysMon_Part_II_v1.2_revision_notes.md`
- `scripts/stage13/remediation_v5.py`
- `docs/registry/claim_evidence_matrix_v5.json`
- `docs/registry/claim_evidence_matrix_v5.md`
- `docs/decisions/decision_log.md`
- prior Stage 13 briefs and reports that quote the correction terms as historical instructions.

The corrected current wording is: the donor-on-renamed controls produced zero evaluable rows; their summaries defaulted to zero recovery, so no measured null or specificity claim can be made from those runs.

## Current Mutation Operators and Actual Semantics

Current implementation: `src/physmon/validation/mutation_operators.py` plus `src/physmon/validation/mutation_executor.py`.

- `sign_inversion_governing_expression`: genuinely negates the governing expression and tests numerical-answer consistency.
- `replace_governing_variable_with_cue`: genuinely introduces the cue symbol into the governing expression and tests cue-symbol independence plus answer consistency.
- `dimensional_corruption`: actually negates a structured parameter value. It is not dimensional corruption.
- `target_quantity_change`: changes target metadata and the stored canonical answer, but not the prompt/equation. It tests incorrect answer detection, not target semantics.
- `assumption_removal`: removes proof text and also leaks cue into the equation. Rejection is confounded by cue leakage, not evidence of assumption-sufficiency checking.
- Positive operators include algebraic `+ 0`, symbol renaming, answer-display formatting, prompt serialization, and no-op metadata control.

## Current Verifier Scope

Verifier: `physmon.benchmark.verifier.SymbolicVerifier`.

It checks:

- numerical answer correctness by evaluating `governing_equation_sympy`;
- cue-symbol absence from free symbols;
- finite/basic positive parameter plausibility;
- parseability of `correct_answer.display`.

It does not check:

- full natural-language semantics;
- assumption sufficiency;
- prompt/equation target consistency;
- full dimensional algebra;
- coordinate-frame equivalence;
- rendered unit equivalence.

## Current Certificate Coverage and Limitations

Current generator: `src/physmon/validation/certificate_generator.py`.

v5 certificates are structured drafts from YAML fields. Known limitations:

- status wording overstates verification (`certificate_generated`);
- `checked_from_template_units` overclaims dimensional checking;
- frame/unit rendering variants are not independently conversion-verified;
- source paths can contain absolute local paths;
- schema v2 is a shallow required-field list.

## Current Parser Distribution

`docs/validation/parser_candidate_coverage_v5.json` reports:

- `n_candidates=225`;
- `n_unique_raw_outputs=223`, so raw outputs are not truly unique;
- category counts are inflated by heuristic `equivalent_units` and broad `model_specific_quirks`.

## Current Validation-Material Quality

v5 materials improved stratification but are not pilot-ready:

- calibration examples are skeletal in the latest audit;
- qualification cases are too fragmentary;
- handbook is not operationally complete;
- pass-1/pass-2 requested fields are incomplete.

## Current Leakage Detector Coverage

`results/stage13/benchmark_integrity/leakage_audit_v5.json` separates expected within-family and derived-parent relations, but active detectors remain limited and `cross_family_candidate_pairs=456` remain unresolved.

## Current Run Inventory and Authority Scope

- `results/stage13/wave0/registry_coverage_v5.json`: `n_expected_runs=143`, `n_registered_runs=0`, `coverage_fraction=0.0`; the denominator is directory-derived and not a normalized run-level crosswalk.
- `docs/registry/artifact_authority_audit_v5.json`: `n_artifacts_scanned=1431`, `critical_unresolved=1334`, `n_zero_row_outputs=2`; audit is broader than v4 but still requires normalized run grouping and orphan classification.

## Current Canonical Evidence and Claim Matrix

- `results/stage13/wave0/canonical_evidence_verification_v5.json`: 155 canonical families, 155 model-family rows, mostly Qwen/behavioural evidence.
- `docs/registry/claim_evidence_matrix_v5.json`: 24 partial claims and 1 missing claim; panel counts and allowed wording require v6 correction.

## Absolute Local Paths

Preflight `rg` found many historical local absolute paths in old results, decision logs, and v5 mutation records. v6 generated artifacts must not introduce new absolute local paths. Old historical artifacts are preserved rather than rewritten.

## Exact Files Planned for Modification or Creation

Shared code:

- `src/physmon/validation/mutation_operators.py`
- `src/physmon/validation/mutation_executor.py`
- `src/physmon/validation/certificate_generator.py`
- `scripts/stage13/remediation_v6.py`
- `tests/stage13/test_stage13_v6_remediation.py`

Versioned outputs:

- `docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.tex`
- `docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf`
- `docs/proposals/PhysMon_Part_II_governing_document_rule.md`
- `docs/stage13/donor_control_statement_audit_v6.md`
- `docs/stage13/mutation_semantics_audit_v6.md`
- `schemas/solver_certificate_v3.schema.json`
- v6 validation, mutation, balance, parser, leakage, run-crosswalk, authority, canonical-evidence, claim-matrix, and gate artifacts under `docs/`, `results/`, and `schemas/`.

## Unresolved Ambiguities

- Complete Part II v1.1 LaTeX source is not present; full v1.2 reconstruction is blocked.
- No full dimensional algebra checker is evident in the current verifier.
- Semantic/template embedding leakage detection is unavailable unless an approved local embedding method is discovered; v6 should mark it unavailable rather than active.
- Historical run IDs remain incomplete where logs/manifests do not expose Slurm/job metadata.
