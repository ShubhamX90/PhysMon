# Stage 14.12 copying versus relevance, from the existing pilot records (descriptive)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. bfloat16, answer_line, ten structures.

## Qwen/Qwen2.5-7B-Instruct

**Unit modulation** (same-unit near cell minus incompatible-unit near cell; same gold string, decoy string and cue digits; only the prompt's unit differs):

| measure (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |
|---|---|---|---|---|
| decoy_shift | 10 | 9.19 | [5.75, 13.21] | 10 / 0 |
| gold_shift | 10 | 0.88 | [-0.60, 2.66] | 5 / 5 |
| r_alt_shift | 10 | -8.31 | [-10.99, -5.59] | 0 / 10 |

Items excluded because the two cue numerals differ: 0.

**Generations equal to the cue numeral** (parsed generations; Wilson 95% interval):

| cell | parsed | equal to cue numeral | interval |
|---|---|---|---|
| nongov_incompatible_unit_near | 20 | 0 | [0.00, 0.16] |
| nongov_same_magnitude_convertible_unit | 16 | 0 | [0.00, 0.19] |
| nongov_same_unit_far | 20 | 3 | [0.05, 0.36] |
| nongov_same_unit_moderate | 20 | 5 | [0.11, 0.47] |
| nongov_same_unit_near_high_overlap | 20 | 4 | [0.08, 0.42] |
| nongov_same_unit_near_low_overlap | 15 | 3 | [0.07, 0.45] |
| numeric_metadata | 20 | 0 | [0.00, 0.16] |
| role_reversal | 18 | 0 | [0.00, 0.18] |

**Role reversal** (the cue quantity is relevant; the question asks for a difference): 18 parsed of 20; 0 equal to the cue numeral; 1 correct; 15 with the sign of the gold (the gold is negative in 20). the question asks for a difference, so these rates are not comparable with the isolated cells.

## meta-llama/Llama-3.1-8B-Instruct

**Unit modulation** (same-unit near cell minus incompatible-unit near cell; same gold string, decoy string and cue digits; only the prompt's unit differs):

| measure (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |
|---|---|---|---|---|
| decoy_shift | 10 | 3.36 | [1.21, 5.85] | 9 / 1 |
| gold_shift | 10 | 0.95 | [-0.31, 2.34] | 7 / 3 |
| r_alt_shift | 10 | -2.41 | [-3.76, -1.20] | 1 / 9 |

Items excluded because the two cue numerals differ: 0.

**Generations equal to the cue numeral** (parsed generations; Wilson 95% interval):

| cell | parsed | equal to cue numeral | interval |
|---|---|---|---|
| nongov_incompatible_unit_near | 20 | 0 | [0.00, 0.16] |
| nongov_same_magnitude_convertible_unit | 16 | 2 | [0.03, 0.36] |
| nongov_same_unit_far | 20 | 0 | [0.00, 0.16] |
| nongov_same_unit_moderate | 20 | 0 | [0.00, 0.16] |
| nongov_same_unit_near_high_overlap | 20 | 0 | [0.00, 0.16] |
| nongov_same_unit_near_low_overlap | 15 | 2 | [0.04, 0.38] |
| numeric_metadata | 20 | 0 | [0.00, 0.16] |
| role_reversal | 20 | 3 | [0.05, 0.36] |

**Role reversal** (the cue quantity is relevant; the question asks for a difference): 20 parsed of 20; 3 equal to the cue numeral; 0 correct; 0 with the sign of the gold (the gold is negative in 20). the question asks for a difference, so these rates are not comparable with the isolated cells.
