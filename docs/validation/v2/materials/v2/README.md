# Validator qualification materials v2 (Stage 14.5)

Status: **candidate materials built by an agent.** Nothing here is a validation. A physicist must confirm the planted
bank (`planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl`) before use, and independent reviewers must do the
reviews. Plan reference: v2 B4 (p.9-10), P3.1-P3.3 (p.20).

## What to give reviewers

- Pass 1: `pass1_packets.jsonl` only. Reviewers must not see the equation, answers, model outputs, sensitivity labels,
  probe scores, or the research hypothesis.
- Pass 2: `pass2_packets.jsonl`, after Pass 1 is complete and locked.
- Review records follow the contract in `src/physmon/governance/review.py` (see the v2 handbook).

## What to keep from reviewers

`packet_key_RESTRICTED.json` (which items are planted and why), `planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl`,
`genuine_pilot_sample.csv` (its strata use model outcomes) and `summary.json`. The key is committed here for
provenance; if this repository is visible to reviewers, move the restricted files out of the copy you share.

## Contents

- 73 items: 40 genuine DECOY-v1 families and 33 planted items,
  shuffled so they cannot be told apart. Base families of planted items are disjoint from the genuine sample.
- Planted types: contradictory_distractor_statement (3), failed_transformation_identity (3), hidden_coupling (3), inconsistent_units (3), insufficient_boundary_condition (3), invalid_numerical_precision (3), invalid_parameter_domain (3), missing_assumption (3), relevant_variable_removed_from_equation (3), valid_equivalent_rewrite (6).
- Genuine strata: assumption_sensitive_isolation (6), cell_coverage (1), cue_c_frame_rendering (1), high_overlap_cluster (4), largest_gold_shift (6), negative_base_score (4), presumed_easy_stable (6), random_fill (12).
- A 20-family timing pilot (`in_timing_pilot_20` in the sample file) measures adjudication time before the full audit
  is budgeted (v2 p.43).
