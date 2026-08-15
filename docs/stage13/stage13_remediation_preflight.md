# Stage 13 Remediation Preflight

Date: 2026-07-03

## Scope

This preflight belongs to the bounded Wave 0 / Wave 1A remediation cycle. It
does not authorize Wave 2-4 work, Slurm submission, GPU execution, new causal
searches, new probe selection, or new thresholds.

## Repository

- Repository root: repository-relative root of this checkout.
- Branch: `master`
- Commit at preflight: `ea914541f883f29308858346f51ec77ce73fdfb4`
- Working tree: dirty before remediation. Existing dirty state includes modified
  core scripts and many untracked Stage 6-13 result/script/doc artifacts. This
  remediation works with that state and does not revert unrelated changes.

## Governing Documents Inspected

- `README.md`
- `Makefile`
- `docs/proposal/physmon_proposal.pdf`
- `docs/proposal/physmon_supplementary.pdf`
- `docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf`
- `docs/prompt briefs/PhysMon_Stage13_Controlled_Execution_Brief_v2.md`
- `docs/prompt briefs/PhysMon_Stage13_Wave0_Wave1A_Remediation_Brief_v3.md`
- External audit attachment: `f7c2e890-a7e9-46cc-a097-6dc74a5fb4c8/pasted-text.txt`
- `docs/decisions/decision_log.md`
- Stage/status reports under `docs/decisions/`

## Local Result Roots Found

- `results/stage6/`
- `results/stage8/`
- `results/stage9/`
- `results/stage10/`
- `results/stage11/`
- `results/stage12/`
- `results/stage13/`
- `results/appendix/`
- `results/canonical/`

## Sharanga Sync Configuration

The sync invariant is defined in `Makefile`:

- Local to remote: `make sync-up`
- Remote to local: `make sync-down`
- Dry-run check: `make sync-check`
- Remote repository target: `sharanga:~/PhysMons/`
- Exclusions include activations, `.venv`, caches, model/tensor files, Slurm submitted
  working files, and `data/generated`.

No Sharanga command, Slurm command, or GPU job was run during this preflight.

## Benchmark Manifests Found

- `results/stage6/audit/stage6_full_benchmark_manifest.csv`
- `results/stage6/generated_full_benchmark/` contains 141 JSON files by file count.
  This includes at least one metadata JSON (`assembly_summary.json`) and therefore
  is not itself a canonical family manifest.
- `results/stage10/benchmark_expansion/verification/` contains 15 JSON files.
- No `data/manifests/` directory existed before this remediation cycle.

## Decision Logs And Status Sources Found

- `docs/decisions/decision_log.md`
- `docs/decisions/stage6_agent_status_report.md`
- `docs/decisions/stage6_next_steps_brief.md`
- `docs/decisions/stage6_d2_execution_brief.md`
- `docs/decisions/agent_status_report_2026-06-14.md`

The decision log contains Stage 10 and Stage 11 checkpoints. A simple heading
search did not find a Stage 12 checkpoint heading.

## Slurm / Job-History Sources Found

- Submitted historical scripts under `slurm/submitted/`
- Reusable templates under `slurm/templates/`
- Run event JSONL files throughout `results/stage6/` through `results/stage12/`
- Decision-log job IDs for many Stage 6-12 runs

These sources will be treated as provenance evidence, not as authorization to
run anything.

## Existing Stage 13 Files Found

- `configs/stage13/stage13_governance.yaml`
- `docs/registry/experiment_registry.jsonl`
- `docs/registry/artifact_authority_audit.json`
- `docs/registry/claim_evidence_matrix.json`
- `docs/registry/partition_freeze.json`
- `docs/stage13/wave0_gate_report.md`
- `docs/stage13/wave1a_gate_report.md`
- `results/stage13/wave0/wave0_gate.json`
- `results/stage13/benchmark_integrity/wave1a_gate.json`
- Stage 13 scripts under `scripts/stage13/`
- Stage 13 tests under `tests/stage13/`

## Missing / Incomplete From Previous Audit Package

- `data/manifests/physmon_canonical_155.jsonl` and `.csv`
- `data/manifests/physmon_derived_variants.jsonl`
- Historical experiment discovery report
- V2 registry schema with required provenance fields
- Content-based Wave 0 gate
- Authority resolution records for known stale/corrected/panel-mismatched cases
- V2 partition freeze with exact family/choice exposure
- V2 claim-evidence matrix with experiment links
- V2 Wave 1A parser, leakage, balance, mutation, validation materials

## Schema Mismatches Observed

- Current registry uses first-cycle scaffold fields rather than the required v3
  provenance schema.
- Current status vocabulary includes `complete`, `partial`, and `planned`; v3
  requires authority-bearing statuses such as `complete_exploratory`,
  `corrected_authoritative`, `superseded`, and `partial_not_reportable`.
- Current canonical family table has one row per family with model-specific
  columns. v3 requires one row per `(model_id, canonical_family_id,
  benchmark_version)`.
- Current canonical build counted metadata and variable-renamed derivatives as
  family rows.
- Current leakage status treated unresolved near duplicates as pass.

## Files This Remediation Will Modify Or Add

- Existing Stage 13 scripts in `scripts/stage13/`
- New/updated `src/physmon/validation/mutation_operators.py`
- New/updated Stage 13 tests in `tests/stage13/`
- Versioned outputs under `docs/registry/`, `docs/stage13/`,
  `docs/validation/`, `data/manifests/`, `results/canonical/`, and
  `results/stage13/`

Existing raw historical outputs, summaries, partial files, corrected files,
archives, logs, and prior Stage 13 gate artifacts will be preserved.

## Unresolved Questions

- Some historical runs lack complete model revision, tokenizer hash, runtime,
  hardware, and command metadata. These will be recorded as partial or unresolved
  provenance rather than inferred.
- No untouched internal-confirmatory family set has yet been established; the
  partition freeze may need to record `none_available`.
- Human parser labels and independent validator labels are not present.
- Some nested archives may require deeper byte-level comparison beyond this
  first remediation pass; unresolved differences will remain critical until
  settled.

