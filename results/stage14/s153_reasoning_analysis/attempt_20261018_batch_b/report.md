# Stage 14.13 reasoning-allowed pilot analysis (descriptive)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Rule frozen in J14.13-002 before the run.
Ungraded outcomes (TRUNCATED, UNPARSEABLE, MULTIPLE_CANDIDATES, EMPTY) are NOT_EVALUATED and in no flip share.

## Qwen/Qwen2.5-7B-Instruct

Records 212; valid 212; parseable 212; no-cue anchors 20 (graded 20, correct 15); gate (at least 8 correct): met.

| Transition | graded | hits | structures | mean share [interval] |
|---|---|---|---|---|
| flip_to_wrong_given_base_correct[nonnumeric_extra] | 15 | 1 | 8 | 0.06 [0.00, 0.19] |
| rescue_to_correct_given_base_wrong[nonnumeric_extra] | 5 | 1 | 3 | 0.17 [0.00, 0.50] |
| flip_to_wrong_given_base_correct[numeric_metadata] | 15 | 0 | 8 | 0.00 [0.00, 0.00] |
| rescue_to_correct_given_base_wrong[numeric_metadata] | 5 | 0 | 3 | 0.00 [0.00, 0.00] |
| flip_to_wrong_given_base_correct[nongov_same_unit_near_high_overlap] | 14 | 2 | 8 | 0.12 [0.00, 0.31] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_near_high_overlap] | 5 | 2 | 3 | 0.33 [0.00, 1.00] |
| flip_to_wrong_given_base_correct[nongov_same_unit_near_low_overlap] | 11 | 2 | 7 | 0.14 [0.00, 0.43] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_near_low_overlap] | 2 | 1 | 2 | 0.50 [0.00, 1.00] |
| flip_to_wrong_given_base_correct[nongov_same_unit_moderate] | 15 | 1 | 8 | 0.06 [0.00, 0.19] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_moderate] | 5 | 2 | 3 | 0.33 [0.00, 0.50] |
| flip_to_wrong_given_base_correct[nongov_same_unit_far] | 15 | 1 | 8 | 0.06 [0.00, 0.19] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_far] | 5 | 1 | 3 | 0.17 [0.00, 0.50] |
| flip_to_wrong_given_base_correct[nongov_incompatible_unit_near] | 15 | 0 | 8 | 0.00 [0.00, 0.00] |
| rescue_to_correct_given_base_wrong[nongov_incompatible_unit_near] | 5 | 0 | 3 | 0.00 [0.00, 0.00] |
| flip_to_wrong_given_base_correct[nongov_same_magnitude_convertible_unit] | 15 | 2 | 8 | 0.12 [0.00, 0.38] |
| rescue_to_correct_given_base_wrong[nongov_same_magnitude_convertible_unit] | 5 | 0 | 3 | 0.00 [0.00, 0.00] |

| Cell | n | parse outcomes | graded | correct | mean generated tokens |
|---|---|---|---|---|---|
| no_cue | 20 | {'PARSED': 20} | 20 | 15 | 418 |
| nongov_incompatible_unit_near | 20 | {'PARSED': 20} | 20 | 15 | 417 |
| nongov_same_magnitude_convertible_unit | 20 | {'PARSED': 20} | 20 | 13 | 455 |
| nongov_same_unit_far | 20 | {'PARSED': 20} | 20 | 15 | 453 |
| nongov_same_unit_moderate | 20 | {'PARSED': 20} | 20 | 16 | 463 |
| nongov_same_unit_near_high_overlap | 19 | {'PARSED': 19} | 19 | 14 | 455 |
| nongov_same_unit_near_low_overlap | 13 | {'PARSED': 13} | 13 | 10 | 456 |
| nonnumeric_extra | 20 | {'PARSED': 20} | 20 | 15 | 438 |
| numeric_metadata | 20 | {'PARSED': 20} | 20 | 15 | 430 |
| relevant_edit | 20 | {'PARSED': 20} | 20 | 16 | 424 |
| role_reversal | 20 | {'PARSED': 20} | 20 | 13 | 448 |

Relevant-edit assay: 16 correct of 20 graded (20 records).

Cue numeral as the final answer: incompatible_unit_near 0/20; same_magnitude_convertible_unit 2/20; same_unit_far 0/20; same_unit_moderate 0/20; same_unit_near_high_overlap 1/19; same_unit_near_low_overlap 2/13; numeric_metadata 0/20; role_reversal 0/20

## meta-llama/Llama-3.1-8B-Instruct

Records 212; valid 212; parseable 184; no-cue anchors 20 (graded 18, correct 8); gate (at least 8 correct): met.

| Transition | graded | hits | structures | mean share [interval] |
|---|---|---|---|---|
| flip_to_wrong_given_base_correct[nonnumeric_extra] | 8 | 3 | 6 | 0.42 [0.08, 0.75] |
| rescue_to_correct_given_base_wrong[nonnumeric_extra] | 10 | 2 | 7 | 0.14 [0.00, 0.43] |
| flip_to_wrong_given_base_correct[numeric_metadata] | 8 | 1 | 6 | 0.17 [0.00, 0.50] |
| rescue_to_correct_given_base_wrong[numeric_metadata] | 10 | 1 | 7 | 0.07 [0.00, 0.21] |
| flip_to_wrong_given_base_correct[nongov_same_unit_near_high_overlap] | 7 | 4 | 5 | 0.50 [0.10, 0.90] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_near_high_overlap] | 8 | 1 | 6 | 0.17 [0.00, 0.50] |
| flip_to_wrong_given_base_correct[nongov_same_unit_near_low_overlap] | 5 | 2 | 4 | 0.38 [0.00, 0.75] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_near_low_overlap] | 4 | 3 | 3 | 0.67 [0.00, 1.00] |
| flip_to_wrong_given_base_correct[nongov_same_unit_moderate] | 6 | 1 | 4 | 0.12 [0.00, 0.38] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_moderate] | 9 | 2 | 6 | 0.17 [0.00, 0.50] |
| flip_to_wrong_given_base_correct[nongov_same_unit_far] | 7 | 4 | 5 | 0.60 [0.30, 0.90] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_far] | 10 | 2 | 7 | 0.14 [0.00, 0.43] |
| flip_to_wrong_given_base_correct[nongov_incompatible_unit_near] | 6 | 2 | 5 | 0.40 [0.00, 0.80] |
| rescue_to_correct_given_base_wrong[nongov_incompatible_unit_near] | 10 | 2 | 7 | 0.14 [0.00, 0.43] |
| flip_to_wrong_given_base_correct[nongov_same_magnitude_convertible_unit] | 6 | 2 | 5 | 0.30 [0.00, 0.70] |
| rescue_to_correct_given_base_wrong[nongov_same_magnitude_convertible_unit] | 9 | 2 | 7 | 0.14 [0.00, 0.43] |

| Cell | n | parse outcomes | graded | correct | mean generated tokens |
|---|---|---|---|---|---|
| no_cue | 20 | {'PARSED': 18, 'TRUNCATED': 1, 'UNPARSEABLE': 1} | 18 | 8 | 400 |
| nongov_incompatible_unit_near | 20 | {'PARSED': 16, 'TRUNCATED': 3, 'UNPARSEABLE': 1} | 16 | 6 | 563 |
| nongov_same_magnitude_convertible_unit | 20 | {'PARSED': 17, 'TRUNCATED': 2, 'UNPARSEABLE': 1} | 17 | 6 | 482 |
| nongov_same_unit_far | 20 | {'PARSED': 17, 'TRUNCATED': 1, 'UNPARSEABLE': 2} | 17 | 5 | 390 |
| nongov_same_unit_moderate | 20 | {'PARSED': 16, 'TRUNCATED': 1, 'UNPARSEABLE': 3} | 16 | 7 | 390 |
| nongov_same_unit_near_high_overlap | 19 | {'PARSED': 16, 'TRUNCATED': 1, 'UNPARSEABLE': 2} | 16 | 5 | 396 |
| nongov_same_unit_near_low_overlap | 13 | {'PARSED': 10, 'TRUNCATED': 1, 'UNPARSEABLE': 2} | 10 | 7 | 410 |
| nonnumeric_extra | 20 | {'PARSED': 20} | 20 | 8 | 316 |
| numeric_metadata | 20 | {'PARSED': 19, 'UNPARSEABLE': 1} | 19 | 8 | 315 |
| relevant_edit | 20 | {'PARSED': 19, 'TRUNCATED': 1} | 19 | 12 | 397 |
| role_reversal | 20 | {'PARSED': 16, 'TRUNCATED': 1, 'UNPARSEABLE': 3} | 16 | 1 | 495 |

Relevant-edit assay: 12 correct of 19 graded (20 records).

Cue numeral as the final answer: incompatible_unit_near 0/16; same_magnitude_convertible_unit 1/17; same_unit_far 0/17; same_unit_moderate 0/16; same_unit_near_high_overlap 2/16; same_unit_near_low_overlap 1/10; numeric_metadata 0/19; role_reversal 0/16
