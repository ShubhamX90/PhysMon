# Stage 14.9 dtype noise and anchor-matched answer competition (descriptive)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Log-probabilities are raw sums in nats.

## llama_primary

**dtype noise, bfloat16 minus float32, gold log-probability per record:** n 212; mean -0.022; SD 0.102; MAD 0.053; median |difference| 0.051; 95th percentile 0.232; max 0.465.

Generations: the parsed answer is identical across dtypes in 197 of 212 records parsed in both; the correctness label agrees in 212 of 212.

| Stage 14.8 contrast | n | SD of the dtype difference | 95th percentile of its absolute value |
|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 20 | 0.130 | 0.261 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 20 | 0.081 | 0.142 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 19 | 0.085 | 0.183 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 13 | 0.116 | 0.288 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 20 | 0.101 | 0.268 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 20 | 0.101 | 0.209 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 20 | 0.102 | 0.207 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 20 | 0.104 | 0.181 |
| gold_lp[near_high_overlap] - gold_lp[far] | 19 | 0.101 | 0.171 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 19 | 0.104 | 0.167 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 19 | 0.118 | 0.229 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 19 | 0.121 | 0.215 |
| R_alt[near_high_overlap] - R_alt[far] | 19 | 0.183 | 0.364 |
| R_alt[near_high_overlap] - R_alt[moderate] | 19 | 0.207 | 0.364 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 19 | 0.122 | 0.211 |

| Anchor-matched shift from the no-cue prompt (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |
|---|---|---|---|---|
| gold_shift[nongov_same_unit_near_high_overlap] | 10 | -0.36 | [-1.70, 0.80] | 5 / 5 |
| decoy_shift[nongov_same_unit_near_high_overlap] | 10 | 3.27 | [1.89, 4.84] | 10 / 0 |
| r_alt_shift[nongov_same_unit_near_high_overlap] | 10 | -3.63 | [-4.93, -2.53] | 0 / 10 |
| gold_shift[nongov_same_unit_near_low_overlap] | 9 | -0.41 | [-2.05, 1.26] | 5 / 4 |
| decoy_shift[nongov_same_unit_near_low_overlap] | 9 | 4.38 | [2.74, 6.08] | 9 / 0 |
| r_alt_shift[nongov_same_unit_near_low_overlap] | 9 | -4.79 | [-6.43, -3.41] | 0 / 9 |
| gold_shift[nongov_same_unit_moderate] | 10 | -0.80 | [-2.50, 0.92] | 3 / 7 |
| decoy_shift[nongov_same_unit_moderate] | 10 | 3.25 | [1.37, 5.08] | 7 / 3 |
| r_alt_shift[nongov_same_unit_moderate] | 10 | -4.06 | [-5.72, -2.50] | 1 / 9 |
| gold_shift[nongov_same_unit_far] | 10 | -0.86 | [-2.15, 0.72] | 2 / 8 |
| decoy_shift[nongov_same_unit_far] | 10 | 4.67 | [1.96, 7.79] | 9 / 1 |
| r_alt_shift[nongov_same_unit_far] | 10 | -5.53 | [-9.30, -2.51] | 0 / 10 |
| gold_shift[nongov_incompatible_unit_near] | 10 | 0.05 | [-0.66, 0.80] | 5 / 5 |
| decoy_shift[nongov_incompatible_unit_near] | 10 | 2.35 | [0.79, 4.14] | 8 / 2 |
| r_alt_shift[nongov_incompatible_unit_near] | 10 | -2.29 | [-4.54, -0.43] | 2 / 8 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_far] | 10 | 1.82 | [-1.97, 5.97] | 7 / 3 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_incompatible_unit_near] | 10 | -1.26 | [-2.47, 0.21] | 3 / 7 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_moderate] | 10 | 0.38 | [-1.33, 2.32] | 5 / 5 |

## qwen_primary

**dtype noise, bfloat16 minus float32, gold log-probability per record:** n 212; mean 0.040; SD 0.201; MAD 0.094; median |difference| 0.092; 95th percentile 0.346; max 1.379.

Generations: the parsed answer is identical across dtypes in 194 of 212 records parsed in both; the correctness label agrees in 212 of 212.

| Stage 14.8 contrast | n | SD of the dtype difference | 95th percentile of its absolute value |
|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 20 | 0.214 | 0.407 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 20 | 0.252 | 0.514 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 19 | 0.200 | 0.419 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 13 | 0.259 | 0.481 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 20 | 0.215 | 0.425 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 20 | 0.303 | 0.695 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 20 | 0.229 | 0.441 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 20 | 0.256 | 0.457 |
| gold_lp[near_high_overlap] - gold_lp[far] | 19 | 0.311 | 0.507 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 19 | 0.174 | 0.258 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 19 | 0.153 | 0.314 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 19 | 0.254 | 0.528 |
| R_alt[near_high_overlap] - R_alt[far] | 19 | 0.471 | 0.908 |
| R_alt[near_high_overlap] - R_alt[moderate] | 19 | 0.286 | 0.435 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 19 | 0.255 | 0.465 |

| Anchor-matched shift from the no-cue prompt (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |
|---|---|---|---|---|
| gold_shift[nongov_same_unit_near_high_overlap] | 10 | 2.42 | [-0.77, 6.06] | 7 / 3 |
| decoy_shift[nongov_same_unit_near_high_overlap] | 10 | 7.49 | [3.95, 11.06] | 9 / 1 |
| r_alt_shift[nongov_same_unit_near_high_overlap] | 10 | -5.07 | [-9.78, -0.57] | 1 / 9 |
| gold_shift[nongov_same_unit_near_low_overlap] | 9 | 1.86 | [-1.64, 6.35] | 5 / 4 |
| decoy_shift[nongov_same_unit_near_low_overlap] | 9 | 8.06 | [3.92, 13.18] | 9 / 0 |
| r_alt_shift[nongov_same_unit_near_low_overlap] | 9 | -6.20 | [-9.90, -2.88] | 2 / 7 |
| gold_shift[nongov_same_unit_moderate] | 10 | 0.30 | [-1.52, 2.75] | 3 / 7 |
| decoy_shift[nongov_same_unit_moderate] | 10 | 7.35 | [4.88, 10.01] | 10 / 0 |
| r_alt_shift[nongov_same_unit_moderate] | 10 | -7.05 | [-9.37, -4.79] | 0 / 10 |
| gold_shift[nongov_same_unit_far] | 10 | 0.46 | [-1.57, 3.26] | 3 / 7 |
| decoy_shift[nongov_same_unit_far] | 10 | 8.02 | [3.65, 12.62] | 9 / 1 |
| r_alt_shift[nongov_same_unit_far] | 10 | -7.56 | [-12.34, -4.11] | 1 / 9 |
| gold_shift[nongov_incompatible_unit_near] | 10 | 2.34 | [0.44, 4.70] | 8 / 2 |
| decoy_shift[nongov_incompatible_unit_near] | 10 | 4.08 | [0.51, 7.76] | 8 / 2 |
| r_alt_shift[nongov_incompatible_unit_near] | 10 | -1.74 | [-6.08, 2.18] | 5 / 5 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_far] | 10 | 1.77 | [-5.36, 9.17] | 5 / 5 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_incompatible_unit_near] | 10 | -3.23 | [-7.44, 0.84] | 3 / 7 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_moderate] | 10 | 1.77 | [-2.46, 6.25] | 5 / 5 |
