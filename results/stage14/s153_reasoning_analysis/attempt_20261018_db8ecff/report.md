# Stage 14.13 reasoning-allowed pilot analysis (descriptive)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Rule frozen in J14.13-002 before the run.
Ungraded outcomes (TRUNCATED, UNPARSEABLE, MULTIPLE_CANDIDATES, EMPTY) are NOT_EVALUATED and in no flip share.

## Qwen/Qwen2.5-7B-Instruct

Records 211; valid 211; parseable 207; no-cue anchors 20 (graded 19, correct 11); gate (at least 8 correct): met.

| Transition | graded | hits | structures | mean share [interval] |
|---|---|---|---|---|
| flip_to_wrong_given_base_correct[nonnumeric_extra] | 11 | 4 | 7 | 0.43 [0.00, 0.71] |
| rescue_to_correct_given_base_wrong[nonnumeric_extra] | 8 | 0 | 6 | 0.00 [0.00, 0.00] |
| flip_to_wrong_given_base_correct[numeric_metadata] | 11 | 2 | 7 | 0.21 [0.00, 0.50] |
| rescue_to_correct_given_base_wrong[numeric_metadata] | 8 | 1 | 6 | 0.08 [0.00, 0.25] |
| flip_to_wrong_given_base_correct[nongov_same_unit_near_high_overlap] | 11 | 2 | 7 | 0.14 [0.00, 0.43] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_near_high_overlap] | 8 | 0 | 6 | 0.00 [0.00, 0.00] |
| flip_to_wrong_given_base_correct[nongov_same_unit_near_low_overlap] | 8 | 2 | 6 | 0.33 [0.00, 0.67] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_near_low_overlap] | 6 | 0 | 4 | 0.00 [0.00, 0.00] |
| flip_to_wrong_given_base_correct[nongov_same_unit_moderate] | 11 | 3 | 7 | 0.29 [0.00, 0.71] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_moderate] | 8 | 0 | 6 | 0.00 [0.00, 0.00] |
| flip_to_wrong_given_base_correct[nongov_same_unit_far] | 11 | 3 | 7 | 0.29 [0.00, 0.71] |
| rescue_to_correct_given_base_wrong[nongov_same_unit_far] | 8 | 1 | 6 | 0.08 [0.00, 0.25] |
| flip_to_wrong_given_base_correct[nongov_incompatible_unit_near] | 11 | 2 | 7 | 0.21 [0.00, 0.50] |
| rescue_to_correct_given_base_wrong[nongov_incompatible_unit_near] | 8 | 1 | 6 | 0.08 [0.00, 0.25] |
| flip_to_wrong_given_base_correct[nongov_same_magnitude_convertible_unit] | 9 | 3 | 6 | 0.33 [0.00, 0.67] |
| rescue_to_correct_given_base_wrong[nongov_same_magnitude_convertible_unit] | 6 | 1 | 5 | 0.20 [0.00, 0.60] |

| Cell | n | parse outcomes | graded | correct | mean generated tokens |
|---|---|---|---|---|---|
| no_cue | 20 | {'PARSED': 19, 'UNPARSEABLE': 1} | 19 | 11 | 647 |
| nongov_incompatible_unit_near | 20 | {'PARSED': 19, 'UNPARSEABLE': 1} | 19 | 10 | 661 |
| nongov_same_magnitude_convertible_unit | 16 | {'PARSED': 16} | 16 | 7 | 675 |
| nongov_same_unit_far | 20 | {'PARSED': 20} | 20 | 10 | 656 |
| nongov_same_unit_moderate | 20 | {'PARSED': 20} | 20 | 8 | 659 |
| nongov_same_unit_near_high_overlap | 20 | {'PARSED': 20} | 20 | 9 | 645 |
| nongov_same_unit_near_low_overlap | 15 | {'PARSED': 15} | 15 | 7 | 625 |
| nonnumeric_extra | 20 | {'PARSED': 20} | 20 | 7 | 669 |
| numeric_metadata | 20 | {'PARSED': 20} | 20 | 10 | 645 |
| relevant_edit | 20 | {'PARSED': 19, 'UNPARSEABLE': 1} | 19 | 6 | 693 |
| role_reversal | 20 | {'PARSED': 19, 'UNPARSEABLE': 1} | 19 | 11 | 653 |

Relevant-edit assay: 6 correct of 19 graded (20 records).

Cue numeral as the final answer: incompatible_unit_near 1/19; same_magnitude_convertible_unit 1/16; same_unit_far 0/20; same_unit_moderate 0/20; same_unit_near_high_overlap 1/20; same_unit_near_low_overlap 0/15; numeric_metadata 0/20; role_reversal 0/19

## meta-llama/Llama-3.1-8B-Instruct

Records 211; valid 211; parseable 168; no-cue anchors 20 (graded 16, correct 7); gate (at least 8 correct): NOT met.

NOT_EVALUATED: 7 of 20 no-cue anchors are correct, below the gate of 8; the correctness floor persists

| Cell | n | parse outcomes | graded | correct | mean generated tokens |
|---|---|---|---|---|---|
| no_cue | 20 | {'PARSED': 16, 'TRUNCATED': 4} | 16 | 7 | 940 |
| nongov_incompatible_unit_near | 20 | {'PARSED': 16, 'TRUNCATED': 4} | 16 | 6 | 759 |
| nongov_same_magnitude_convertible_unit | 16 | {'PARSED': 13, 'TRUNCATED': 2, 'UNPARSEABLE': 1} | 13 | 1 | 721 |
| nongov_same_unit_far | 20 | {'PARSED': 14, 'TRUNCATED': 3, 'UNPARSEABLE': 3} | 14 | 4 | 700 |
| nongov_same_unit_moderate | 20 | {'PARSED': 16, 'TRUNCATED': 1, 'UNPARSEABLE': 3} | 16 | 6 | 577 |
| nongov_same_unit_near_high_overlap | 20 | {'PARSED': 13, 'TRUNCATED': 4, 'UNPARSEABLE': 3} | 13 | 4 | 824 |
| nongov_same_unit_near_low_overlap | 15 | {'PARSED': 13, 'TRUNCATED': 1, 'UNPARSEABLE': 1} | 13 | 3 | 605 |
| nonnumeric_extra | 20 | {'PARSED': 17, 'TRUNCATED': 2, 'UNPARSEABLE': 1} | 17 | 9 | 615 |
| numeric_metadata | 20 | {'PARSED': 17, 'TRUNCATED': 2, 'UNPARSEABLE': 1} | 17 | 5 | 642 |
| relevant_edit | 20 | {'PARSED': 17, 'TRUNCATED': 2, 'UNPARSEABLE': 1} | 17 | 4 | 634 |
| role_reversal | 20 | {'PARSED': 16, 'TRUNCATED': 1, 'UNPARSEABLE': 3} | 16 | 1 | 675 |

Relevant-edit assay: 4 correct of 17 graded (20 records).

Cue numeral as the final answer: incompatible_unit_near 0/16; same_magnitude_convertible_unit 0/13; same_unit_far 0/14; same_unit_moderate 0/16; same_unit_near_high_overlap 0/13; same_unit_near_low_overlap 0/13; numeric_metadata 0/17; role_reversal 0/16
