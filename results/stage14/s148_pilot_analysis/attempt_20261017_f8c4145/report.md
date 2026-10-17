# Stage 14.8 pilot analysis (descriptive, precision-limited)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Ten structures are the
independent units (v2 §8.1); intervals are cluster bootstrap over structures (2,000 resamples, seed 42) and are
descriptions of precision, not tests. A contrast is a difference of raw log-probabilities (nats) of the same gold
string; cells whose gold differs from the anchor (relevant edit, role reversal) are not in these contrasts.

## Qwen/Qwen2.5-7B-Instruct

Records 211; all-valid 211; format-parseable 209; no-cue anchors 20 (parseable 20, correct 0). Model-positive stratum: NOT_EVALUATED: no sensitivity label exists for the v2 structures.

| Contrast (nats) | structures | mean | 95% cluster-bootstrap interval | structures up / down |
|---|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 10 | -0.52 | [-1.04, -0.07] | 3 / 7 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 10 | 0.78 | [0.15, 1.38] | 8 / 2 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 10 | 1.98 | [-0.58, 4.65] | 6 / 4 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 9 | 1.00 | [-2.85, 4.48] | 5 / 4 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 10 | 0.63 | [-2.24, 3.69] | 4 / 6 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 10 | 2.04 | [-0.75, 5.00] | 5 / 5 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 10 | 1.10 | [-1.50, 3.79] | 4 / 6 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 8 | 0.56 | [-2.59, 3.61] | 5 / 3 |
| gold_lp[near_high_overlap] - gold_lp[far] | 10 | -0.06 | [-2.21, 2.20] | 5 / 5 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 10 | 1.35 | [0.17, 2.64] | 8 / 2 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 10 | 0.88 | [-0.59, 2.62] | 5 / 5 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 8 | 0.81 | [-2.16, 4.18] | 3 / 5 |
| R_alt[near_high_overlap] - R_alt[far] | 10 | -4.38 | [-8.29, -1.01] | 3 / 7 |
| R_alt[near_high_overlap] - R_alt[moderate] | 10 | 0.66 | [-1.63, 2.87] | 5 / 5 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 10 | -8.31 | [-10.92, -5.67] | 0 / 10 |

Assay response to the relevant edit: 20 evaluable instantiation pairs of 20; the generated value changed in 15, changed in the direction of the new gold in 14, moved closer to the new gold in 7.

| Cell | n | mean gold log-prob | n with R_alt | mean R_alt |
|---|---|---|---|---|
| no_cue | 20 | -17.15 | 0 | NOT_EVALUATED |
| nongov_incompatible_unit_near | 20 | -16.05 | 20 | -2.76 |
| nongov_same_magnitude_convertible_unit | 16 | -15.98 | 0 | NOT_EVALUATED |
| nongov_same_unit_far | 20 | -15.11 | 20 | -6.69 |
| nongov_same_unit_moderate | 20 | -16.52 | 20 | -11.73 |
| nongov_same_unit_near_high_overlap | 20 | -15.17 | 20 | -11.07 |
| nongov_same_unit_near_low_overlap | 15 | -16.08 | 15 | -11.10 |
| nonnumeric_extra | 20 | -17.67 | 0 | NOT_EVALUATED |
| numeric_metadata | 20 | -16.37 | 0 | NOT_EVALUATED |
| relevant_edit | 20 | -17.07 | 0 | NOT_EVALUATED |
| role_reversal | 20 | -16.13 | 0 | NOT_EVALUATED |

Copy of the cue numeral as the generated answer (descriptive): same_unit_near_high_overlap 4/20; same_unit_near_low_overlap 3/15; same_unit_moderate 5/20; same_unit_far 3/20; incompatible_unit_near 0/20

## meta-llama/Llama-3.1-8B-Instruct

Records 211; all-valid 211; format-parseable 211; no-cue anchors 20 (parseable 20, correct 1). Model-positive stratum: NOT_EVALUATED: no sensitivity label exists for the v2 structures.

| Contrast (nats) | structures | mean | 95% cluster-bootstrap interval | structures up / down |
|---|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 10 | -0.30 | [-0.47, -0.14] | 2 / 8 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 10 | 0.14 | [-0.18, 0.59] | 4 / 6 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 10 | 0.25 | [-0.97, 1.83] | 4 / 6 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 9 | 0.64 | [-0.76, 2.56] | 4 / 5 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 10 | 0.49 | [-0.89, 2.06] | 4 / 6 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 10 | 0.61 | [-0.78, 2.24] | 6 / 4 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 10 | -0.70 | [-1.63, 0.01] | 2 / 8 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 8 | -0.29 | [-1.19, 0.40] | 3 / 5 |
| gold_lp[near_high_overlap] - gold_lp[far] | 10 | -0.35 | [-0.67, -0.01] | 2 / 8 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 10 | -0.23 | [-0.61, 0.19] | 3 / 7 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 10 | 0.95 | [-0.29, 2.34] | 7 / 3 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 8 | -0.11 | [-1.52, 1.74] | 3 / 5 |
| R_alt[near_high_overlap] - R_alt[far] | 10 | -2.04 | [-3.69, -0.64] | 1 / 9 |
| R_alt[near_high_overlap] - R_alt[moderate] | 10 | 0.29 | [-0.52, 1.23] | 3 / 7 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 10 | -2.41 | [-3.73, -1.18] | 1 / 9 |

Assay response to the relevant edit: 20 evaluable instantiation pairs of 20; the generated value changed in 16, changed in the direction of the new gold in 11, moved closer to the new gold in 10.

| Cell | n | mean gold log-prob | n with R_alt | mean R_alt |
|---|---|---|---|---|
| no_cue | 20 | -10.41 | 0 | NOT_EVALUATED |
| nongov_incompatible_unit_near | 20 | -11.11 | 20 | -1.45 |
| nongov_same_magnitude_convertible_unit | 16 | -9.67 | 0 | NOT_EVALUATED |
| nongov_same_unit_far | 20 | -9.80 | 20 | -1.82 |
| nongov_same_unit_moderate | 20 | -9.92 | 20 | -4.15 |
| nongov_same_unit_near_high_overlap | 20 | -10.16 | 20 | -3.86 |
| nongov_same_unit_near_low_overlap | 15 | -9.81 | 15 | -4.07 |
| nonnumeric_extra | 20 | -10.70 | 0 | NOT_EVALUATED |
| numeric_metadata | 20 | -10.27 | 0 | NOT_EVALUATED |
| relevant_edit | 20 | -10.13 | 0 | NOT_EVALUATED |
| role_reversal | 20 | -14.61 | 0 | NOT_EVALUATED |

Copy of the cue numeral as the generated answer (descriptive): same_unit_near_high_overlap 0/20; same_unit_near_low_overlap 2/15; same_unit_moderate 0/20; same_unit_far 0/20; incompatible_unit_near 0/20

## Not evaluated

- correctness-transition endpoint (C_gen): base-correct anchors are almost empty, so no transition from correct to wrong is estimable
- presentation-noise floor (P1.7): no repeat pass or dtype variation was run; cue effects cannot be read against a noise distribution
- model-positive stratum: no sensitivity label exists for the v2 structures
- R_alt for cells without a numeric cue: no decoy candidate (v2 §4); recorded as null in the raw records
- interaction tests: not attempted: ten structures cannot support a powered interaction claim (protocol section 1)
