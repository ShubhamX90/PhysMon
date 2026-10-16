# Experiment Card X05: Structural leakage and real OOD monitoring (partly executed)

Experiment ID: v2_X05_structure_leakage_and_ood_monitoring

Scientific Question: Does the Phase-I monitor read the editing grammar or template identity rather than a general property of the model? Compare family-held-out with structure-cluster-held-out evaluation, against fitted entropy and a surface baseline.

Discovery Or Confirmation: exploratory (legacy data, legacy label as the historical Phase-I target). The final frozen external test is not run.

Partition: The 135-family monitoring cohort and the 34 adjudication-pending structure clusters (110 families; 45 singletons) rebuilt from the Stage 13 unresolved review; all 140 behavioural families for the inclusion-agnostic re-analysis.

Primary Metric: Paired cluster-held-out AUROC and log loss of the monitor versus fitted entropy and a surface/AST baseline, with intervals corrected for selection.

Secondary Metrics: Leave-one-family-out minus leave-one-cluster-out AUROC with a cluster bootstrap; AUROC split by whether a held-out family has a cluster mate in training.

Inputs: `results/stage13/benchmark_integrity/leakage_review_v7.csv`, `data/manifests/physmon_canonical_155.jsonl`, the stored out-of-fold predictions, rendered Stage 6 families. Not available: activation tensors (lost in the 2026-10 scratch wipe).

Raw Outputs: `results/stage14/s144_structure_overlap/<attempt-id>/`.

Derived Outputs: `clusters.csv` (lineage graph), `summary.json`, ledger rows S144-R1 to S144-R4.

Stop Rules: The monitor under cluster-held-out folds needs regenerated activations (GPU) and explicit authorization; it is NOT_EVALUATED, not substituted. No confirmatory claim before the independent validation and leakage-firewall gate P3 (p.20).

Negative Result Policy: Every predictor and both cohorts are reported, including intervals that include zero and below-chance leave-out AUROCs. A missing activation is NOT_EVALUATED, never a zero.

Paper Eligibility Rule: Not paper-eligible.

PI Approval: CPU-only work approved by the user's instruction of 2026-10-16 (journal J14.0-001).

No-Go Response: If the monitor collapses under cluster-held-out folds, it reads the template or editing grammar and no out-of-structure deployment claim is made; quoting the best family-LOOCV AUROC as an out-of-distribution score is prohibited (v2 card X05, p.40; §10, p.44).

Artifact: Exact fold manifest (`clusters.csv`), predictions and the fairness and cost table (cost table still open).

v2 Reference: Card X05 (p.40); B1.6 (p.8); P3.5 and P3.6 (p.20); B05 and B08 (p.32).

Notes: Executed so far: cluster reconstruction, the 71% reconciliation, family-held-out versus cluster-held-out for non-activation predictors, exposure split of stored predictions, the five exclusions (journal `docs/journal/stage14/14.4_structure_overlap.md`). Still open: the monitor under cluster-held-out folds, human adjudication of the 147 pairs, law-class and source-held-out splits, cost accounting (P5.11).
