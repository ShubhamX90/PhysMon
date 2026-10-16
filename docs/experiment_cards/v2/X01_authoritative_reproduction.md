# Experiment Card X01: Authoritative reproduction

Experiment ID: v2_X01_authoritative_reproduction

Scientific Question: Which Phase-I numbers follow from exact committed per-prompt records, manifests, and code in this repository, and which cannot be reproduced from it? Every value copied from the submitted manuscript is labelled verified, different but explained, unreproducible, or not enough source data (v2 P0.2, p.16).

Discovery Or Confirmation: reproduction_audit (exploratory; no confirmatory data role is opened and nothing here is tuned).

Partition: Legacy Phase-I data with data role UNASSIGNED_LEGACY: 155 canonical families, 140 original behavioural families, 135-family monitoring cohort. No family is assigned to a v2 data role by this card.

Primary Metric: Equality of recomputed panel denominators, labels, and endpoint values to the reported values within a declared numerical precision, one label per ledger row in `docs/registry/v2/claim_ledger.jsonl`.

Secondary Metrics: Reproduction of the paired 10,000-resample bootstrap distributions (not only intervals); inclusion-flow counts 155 to 140 to 135; per-cue and per-domain rates; Qwen, Llama and DeepSeek label overlaps.

Inputs: Committed raw per-prompt records (`results/stage6/behavioural_full_rerun/prompt_records.jsonl`, `family_summaries.jsonl`), `data/manifests/physmon_canonical_155.jsonl`, committed out-of-fold prediction files, the Wave 2 summaries, and the Stage 13 v7 audit artifacts. Not available: the submitted manuscript PDF, and activation tensors (lost in the October 2026 scratch wipe).

Raw Outputs: `results/stage14/x01_reproduction/<attempt-id>/` (new attempt path per run; never reused).

Derived Outputs: Updated `verification_label`, `verified_in_stage` and `journal_ref` on ledger rows; a reconciliation table and a discrepancy log under the attempt path; journal entries in `docs/journal/stage14/14.1_*.md`.

Stop Rules: If a headline denominator or label does not regenerate from raw records, stop every dependent experiment (P0 hard stop, p.16), localise the discrepancy, and record it. No GPU or Slurm work in this card. A re-run of 10 or more hand-selected families through the model (P0.3) needs separate explicit authorization.

Negative Result Policy: An unreproducible value keeps the label `unreproducible` with an explanation. A value with no committed source keeps `not_enough_source_data`. Missing records are never filled and a zero-row output is NOT_EVALUATED, not a null (v2 §8.4, p.42).

Paper Eligibility Rule: No value becomes paper-eligible from this card. Reproduction only.

PI Approval: CPU-only work approved by the user's instruction of 2026-10-16 (journal J14.0-001). GPU work not approved.

No-Go Response: If reproduction fails, block every dependent experiment, fix code or provenance, and rerun the minimal upstream chain; publish an erratum in the internal ledger (v2 P0, p.16; §10, p.44).

Artifact: A signed reconciliation ledger and replayable tests.

v2 Reference: Card X01 (p.39); P0.1 to P0.5 (p.16); B1.1 (p.6); §8.4 (p.42).

Notes: Known limits at card creation: the single-rendering L16 monitor (0.7465), the entropy Brier and ECE values, FNR@FPR values, the frozen-expansion pooled AUROC, and the 71% family-held-out cluster-sharing figure have no committed source and are expected to be `not_enough_source_data` unless the manuscript is supplied (working digest section 7).
