# Stage 14.8 pilot analysis (descriptive, precision-limited)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Ten structures are the
independent units (v2 §8.1); intervals are cluster bootstrap over structures (2,000 resamples, seed 42) and are
descriptions of precision, not tests. A contrast is a difference of raw log-probabilities (nats) of the same gold
string; cells whose gold differs from the anchor (relevant edit, role reversal) are not in these contrasts.

## Qwen/Qwen2.5-7B-Instruct

Records 212; all-valid 212; format-parseable 212; no-cue anchors 20 (parseable 20, correct 4). Model-positive stratum: NOT_EVALUATED: no sensitivity label exists for the v2 structures.

| Contrast (nats) | structures | mean | 95% cluster-bootstrap interval | structures up / down |
|---|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 10 | -0.52 | [-1.18, 0.10] | 2 / 8 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 10 | 1.27 | [-0.01, 3.07] | 6 / 4 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 10 | 2.42 | [-0.92, 6.00] | 7 / 3 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 9 | 1.86 | [-1.72, 6.93] | 5 / 4 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 10 | 0.30 | [-1.55, 2.76] | 3 / 7 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 10 | 0.46 | [-1.49, 3.22] | 3 / 7 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 10 | 2.34 | [0.36, 4.71] | 8 / 2 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 10 | -0.26 | [-2.64, 2.28] | 5 / 5 |
| gold_lp[near_high_overlap] - gold_lp[far] | 10 | 1.63 | [-1.06, 3.98] | 7 / 3 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 10 | 1.84 | [-0.25, 3.69] | 8 / 2 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 10 | 0.07 | [-1.97, 1.97] | 4 / 6 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 10 | 2.13 | [-0.35, 4.18] | 7 / 3 |
| R_alt[near_high_overlap] - R_alt[far] | 10 | -3.87 | [-7.76, 0.33] | 3 / 7 |
| R_alt[near_high_overlap] - R_alt[moderate] | 10 | -0.39 | [-3.39, 2.89] | 4 / 6 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 10 | -3.23 | [-7.34, 0.76] | 3 / 7 |

Assay response to the relevant edit: 20 evaluable instantiation pairs of 20; the generated value changed in 16, changed in the direction of the new gold in 11, moved closer to the new gold in 8.

| Cell | n | mean gold log-prob | n with R_alt | mean R_alt |
|---|---|---|---|---|
| no_cue | 20 | -12.09 | 0 | NOT_EVALUATED |
| nongov_incompatible_unit_near | 20 | -9.75 | 20 | 1.11 |
| nongov_same_magnitude_convertible_unit | 20 | -12.35 | 0 | NOT_EVALUATED |
| nongov_same_unit_far | 20 | -11.63 | 20 | 1.48 |
| nongov_same_unit_moderate | 20 | -11.79 | 20 | -2.03 |
| nongov_same_unit_near_high_overlap | 19 | -10.21 | 19 | -3.05 |
| nongov_same_unit_near_low_overlap | 13 | -10.38 | 13 | -1.57 |
| nonnumeric_extra | 20 | -12.61 | 0 | NOT_EVALUATED |
| numeric_metadata | 20 | -10.82 | 0 | NOT_EVALUATED |
| relevant_edit | 20 | -12.01 | 0 | NOT_EVALUATED |
| role_reversal | 20 | -15.59 | 0 | NOT_EVALUATED |

Copy of the cue numeral as the generated answer (descriptive): same_unit_near_high_overlap 2/19; same_unit_near_low_overlap 0/13; same_unit_moderate 0/20; same_unit_far 0/20; incompatible_unit_near 2/20

## meta-llama/Llama-3.1-8B-Instruct

Records 212; all-valid 212; format-parseable 212; no-cue anchors 20 (parseable 20, correct 1). Model-positive stratum: NOT_EVALUATED: no sensitivity label exists for the v2 structures.

| Contrast (nats) | structures | mean | 95% cluster-bootstrap interval | structures up / down |
|---|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 10 | -0.46 | [-0.99, -0.00] | 2 / 8 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 10 | 0.25 | [-0.20, 0.70] | 6 / 4 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 10 | -0.36 | [-1.68, 0.79] | 5 / 5 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 9 | -0.41 | [-2.10, 1.33] | 5 / 4 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 10 | -0.80 | [-2.42, 0.92] | 3 / 7 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 10 | -0.86 | [-2.15, 0.81] | 2 / 8 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 10 | 0.05 | [-0.66, 0.78] | 5 / 5 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 10 | -0.48 | [-2.46, 1.39] | 5 / 5 |
| gold_lp[near_high_overlap] - gold_lp[far] | 10 | 0.59 | [-0.42, 1.68] | 7 / 3 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 10 | 0.55 | [-0.44, 1.57] | 7 / 3 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 10 | -0.52 | [-2.00, 0.81] | 4 / 6 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 10 | -0.00 | [-0.83, 0.85] | 5 / 5 |
| R_alt[near_high_overlap] - R_alt[far] | 10 | 0.83 | [-1.32, 2.99] | 5 / 5 |
| R_alt[near_high_overlap] - R_alt[moderate] | 10 | 1.17 | [-0.34, 2.67] | 7 / 3 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 10 | -1.26 | [-2.49, 0.19] | 3 / 7 |

Assay response to the relevant edit: 20 evaluable instantiation pairs of 20; the generated value changed in 16, changed in the direction of the new gold in 11, moved closer to the new gold in 9.

| Cell | n | mean gold log-prob | n with R_alt | mean R_alt |
|---|---|---|---|---|
| no_cue | 20 | -9.14 | 0 | NOT_EVALUATED |
| nongov_incompatible_unit_near | 20 | -9.09 | 20 | -1.11 |
| nongov_same_magnitude_convertible_unit | 20 | -9.62 | 0 | NOT_EVALUATED |
| nongov_same_unit_far | 20 | -10.01 | 20 | -3.06 |
| nongov_same_unit_moderate | 20 | -9.95 | 20 | -3.51 |
| nongov_same_unit_near_high_overlap | 19 | -9.68 | 19 | -2.87 |
| nongov_same_unit_near_low_overlap | 13 | -10.21 | 13 | -3.83 |
| nonnumeric_extra | 20 | -9.61 | 0 | NOT_EVALUATED |
| numeric_metadata | 20 | -8.90 | 0 | NOT_EVALUATED |
| relevant_edit | 20 | -9.47 | 0 | NOT_EVALUATED |
| role_reversal | 20 | -12.90 | 0 | NOT_EVALUATED |

Copy of the cue numeral as the generated answer (descriptive): same_unit_near_high_overlap 1/19; same_unit_near_low_overlap 1/13; same_unit_moderate 2/20; same_unit_far 2/20; incompatible_unit_near 0/20

## Not evaluated

- correctness-transition endpoint (C_gen): base-correct anchors are almost empty, so no transition from correct to wrong is estimable
- presentation-noise floor (P1.7): no repeat pass or dtype variation was run; cue effects cannot be read against a noise distribution
- model-positive stratum: no sensitivity label exists for the v2 structures
- R_alt for cells without a numeric cue: no decoy candidate (v2 §4); recorded as null in the raw records
- interaction tests: not attempted: ten structures cannot support a powered interaction claim (protocol section 1)
