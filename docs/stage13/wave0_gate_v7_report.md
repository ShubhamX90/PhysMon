# Stage 13 Wave 0 Gate v7

Status: `FAIL`

- Gate version: 7.0
- Human pilot: `PENDING`
- Paper eligibility: `False`
- Permission for Wave 2: `False`
- Source commit: `024c55e86a2ab1d62984207dad8b548ce9082a5a`

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

### FAIL `canonical_evidence_substantive`

- Detail: no v7 rebuild; v6 populates only ['S_lp'] across 465 rows with 185 nulls
- Computed from: `results/stage13/wave0/canonical_evidence_verification_v6.json`
- Criterion: Canonical evidence must span more than S_lp with source-linked values. The v6 pass is not inherited.

### FAIL `claim_matrix_substantive`

- Detail: no v7 rebuild; 0/10 v6 claims cite an artifact
- Computed from: `docs/registry/claim_evidence_matrix_v6.json`
- Criterion: Every claim needs a real estimate, interval, and cited authoritative artifacts. The v6 pass is not inherited.

## Gate policy

Checks that passed on form in v6 are re-evaluated against their stricter criterion. Where a v7 artifact does not exist, the check fails rather than inheriting the v6 pass.
