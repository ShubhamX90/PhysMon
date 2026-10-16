# Experiment Card X02: Base-variant invariance challenge

Experiment ID: v2_X02_base_variant_invariance_challenge

Scientific Question: Does the legacy signed, base-relative log-probability sensitivity (`S_lp` at base variant 0, threshold 0.5 nat) depend on which of the four renderings is called the base? If it does, the binary label is not invariant to variant indexing.

Discovery Or Confirmation: exploratory (diagnostic of a measurement definition on stored data; no confirmatory role opened).

Partition: The 140 original behavioural families (Stage 6 D2 rerun), Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct, four stored gold log-probabilities per family and model. Cue A, B, and C reported separately. Families with a missing log-probability are reported as NOT_EVALUATED, not dropped silently.

Primary Metric: Reclassification matrix of the 0.5-nat label under all four base choices, plus model rank concordance (Spearman) of family scores across the four bases.

Secondary Metrics: Per family and model, `max - min` of the four values (symmetric range), SD, MAD, median absolute pairwise difference, number of positive labels across the four bases, fraction of families whose label flips, pairwise rank inversions across models, stratified by cue type, domain, answer-token-length proxy, original sensitivity quantile. Both legacy definitions are reported side by side: `legacy_repo_clamped` (maximum over all four variants, never negative, as in `src/physmon/formal/sensitivity.py`) and `legacy_plan_signed` (maximum over the other three variants, can be negative, as in v2 B1.3).

Inputs: `results/stage6/behavioural_full_rerun/prompt_records.jsonl` (1,120 records = 140 families x 4 variants x 2 models). No new model calls.

Raw Outputs: `results/stage14/x02_base_rotation/<attempt-id>/base_permutation_audit.csv`.

Derived Outputs: Summary JSON with the reclassification matrix, concordance, and stratified tables; the executable unit test for the CM_B_UM_059 example (`tests/v2/test_base_rotation_x02.py`); the journal `docs/journal/stage14/14.2_*.md`; ledger update for P1A-A.

Stop Rules: No GPU, no Slurm. Do not describe any new metric as preregistered in June; preserve the threshold registration history (v2 B1.2, p.6-7).

Negative Result Policy: Report all families including those where the label is stable across bases. A family with a missing log-probability is NOT_EVALUATED. The order-independent range is absolute dispersion, not a signed risk measure, and is never presented as one (B1.3, p.8).

Paper Eligibility Rule: Not paper-eligible. This is a measurement-definition diagnostic on legacy data.

PI Approval: CPU-only work approved by the user's instruction of 2026-10-16 (journal J14.0-001).

No-Go Response: If sensitivity depends heavily on the arbitrary variant 0, retire the reference-based construct as a primary endpoint and reanalyse Phase I under a preregistered replacement while retaining the original registration history (v2 card X02, p.39).

Artifact: Per-family metric multiverse with score versions and a reclassification matrix.

v2 Reference: Card X02 (p.39); B1.2 and B1.3 (p.6-8); P1.1 (p.17); C01 and C02 (p.33); §12 item 2 (p.48).

Notes: The anchor-free and no-cue contrasts that need new model evaluations are out of scope here (P1.1 says they "do require new evaluations"); this card uses stored values only. The plan's -9.094 for CM_B_UM_059 at base 1 corresponds to `legacy_plan_signed`; under `legacy_repo_clamped` the same base gives 0.0 (journal J14.0-003).
