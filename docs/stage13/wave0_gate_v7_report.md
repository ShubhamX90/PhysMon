# Stage 13 Wave 0 Gate v7

Status: `PASS`

- Gate version: 7.0
- Human pilot: `PENDING`
- Paper eligibility: `False`
- Permission for Wave 2: `False`
- Source commit: `0516a4725578dbf196de47d1a2e1e90a9e6748fc`

## Checks

### PASS `governing_document_rule_correct`

- Detail: rule names complete v1.1 plus the erratum
- Computed from: `docs/proposals/PhysMon_Part_II_governing_document_rule.md`
- Criterion: Rule must name the complete Part II v1.1 read together with the erratum.

### PASS `run_crosswalk_real_denominator`

- Detail: 182 science runs from real Slurm IDs; coverage 0.7033 (strict 0.4505)
- Computed from: `results/stage13/wave0/registry_coverage_v7.json`
- Criterion: Denominator must be jobs with real Slurm identities, not globbed filenames.

### PASS `critical_authority_zero`

- Detail: 2 critical, 0 unresolved, 0 records rejected
- Computed from: `docs/registry/artifact_authority_audit_v7.json`
- Criterion: Every critical artifact must carry a validated resolution record.

### PASS `canonical_evidence_substantive`

- Detail: 12 populated field types
- Computed from: `results/stage13/wave0/canonical_evidence_verification_v7.json`
- Criterion: Canonical evidence must span more than S_lp with source-linked values.

### PASS `claim_matrix_substantive`

- Detail: 10/10 claims cite an authoritative artifact
- Computed from: `docs/registry/claim_evidence_matrix_v7.json`
- Criterion: Every claim needs a real estimate, interval, and cited authoritative artifacts.

## Gate policy

Checks that passed on form in v6 are re-evaluated against their stricter criterion. Where a v7 artifact does not exist, the check fails rather than inheriting the v6 pass.
