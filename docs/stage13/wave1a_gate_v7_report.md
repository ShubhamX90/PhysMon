# Stage 13 Wave 1A Gate v7

Status: `FAIL`

- Gate version: 7.0
- Human pilot: `PENDING`
- Paper eligibility: `False`
- Permission for Wave 2: `False`
- Source commit: `0516a4725578dbf196de47d1a2e1e90a9e6748fc`

## Checks

### FAIL `leakage_review_resolved`

- Detail: status=INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW; 2352 unresolved variant pairs = 147 family pairs in 34 clusters
- Computed from: `results/stage13/benchmark_integrity/leakage_audit_v7.json`
- Criterion: Leakage cannot pass while unresolved cross-family candidates remain.

### PASS `leakage_population_untruncated`

- Detail: 620 prompts over 155 families
- Computed from: `results/stage13/benchmark_integrity/leakage_audit_v7.json`
- Criterion: The audit must cover the whole prompt population with no truncation.

### PASS `mutation_semantics_accurate`

- Detail: carried forward unchanged from v6
- Computed from: `results/stage13/benchmark_integrity/wave1a_gate_v6.json`
- Criterion: Carried forward; not re-derived in v7.

### PASS `real_verifier_backed_operators`

- Detail: carried forward unchanged from v6
- Computed from: `results/stage13/benchmark_integrity/wave1a_gate_v6.json`
- Criterion: Carried forward; not re-derived in v7.

### PASS `certificate_status_honest`

- Detail: carried forward unchanged from v6
- Computed from: `results/stage13/benchmark_integrity/wave1a_gate_v6.json`
- Criterion: Carried forward; not re-derived in v7.

### PASS `pilot_stratified`

- Detail: carried forward unchanged from v6
- Computed from: `results/stage13/benchmark_integrity/wave1a_gate_v6.json`
- Criterion: Carried forward; not re-derived in v7.

### PASS `parser_unique_balanced`

- Detail: carried forward unchanged from v6
- Computed from: `results/stage13/benchmark_integrity/wave1a_gate_v6.json`
- Criterion: Carried forward; not re-derived in v7.

### PASS `balance_excludes_unlabeled`

- Detail: carried forward unchanged from v6
- Computed from: `results/stage13/benchmark_integrity/wave1a_gate_v6.json`
- Criterion: Carried forward; not re-derived in v7.

### PASS `portable_paths`

- Detail: carried forward unchanged from v6
- Computed from: `results/stage13/benchmark_integrity/wave1a_gate_v6.json`
- Criterion: Carried forward; not re-derived in v7.

## Gate policy

Checks that passed on form in v6 are re-evaluated against their stricter criterion. Where a v7 artifact does not exist, the check fails rather than inheriting the v6 pass.
