# Stage 14.9 dtype noise and anchor-matched answer competition (descriptive)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Log-probabilities are raw sums in nats.

## llama_primary

**dtype noise, bfloat16 minus float32, gold log-probability per record:** n 211; mean -0.006; SD 0.085; MAD 0.048; median |difference| 0.049; 95th percentile 0.156; max 0.501.

Generations: the parsed answer is identical across dtypes in 169 of 211 records parsed in both; the correctness label agrees in 210 of 211.

**run-to-run, bfloat16 (this job against job 399969):** n 211; max |difference| 0.000; median 0.000.

| Stage 14.8 contrast | n | SD of the dtype difference | 95th percentile of its absolute value |
|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 20 | 0.106 | 0.198 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 20 | 0.078 | 0.144 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 20 | 0.129 | 0.220 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 15 | 0.116 | 0.206 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 20 | 0.176 | 0.371 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 20 | 0.107 | 0.188 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 20 | 0.101 | 0.207 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 16 | 0.111 | 0.174 |
| gold_lp[near_high_overlap] - gold_lp[far] | 20 | 0.087 | 0.145 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 20 | 0.121 | 0.225 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 20 | 0.099 | 0.196 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 16 | 0.109 | 0.179 |
| R_alt[near_high_overlap] - R_alt[far] | 20 | 0.190 | 0.405 |
| R_alt[near_high_overlap] - R_alt[moderate] | 20 | 0.140 | 0.299 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 20 | 0.127 | 0.230 |

| Anchor-matched shift from the no-cue prompt (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |
|---|---|---|---|---|
| gold_shift[nongov_same_unit_near_high_overlap] | 10 | 0.25 | [-1.07, 1.79] | 4 / 6 |
| decoy_shift[nongov_same_unit_near_high_overlap] | 10 | 4.01 | [1.28, 7.55] | 8 / 2 |
| r_alt_shift[nongov_same_unit_near_high_overlap] | 10 | -3.76 | [-5.97, -1.88] | 0 / 10 |
| gold_shift[nongov_same_unit_near_low_overlap] | 9 | 0.64 | [-0.74, 2.53] | 4 / 5 |
| decoy_shift[nongov_same_unit_near_low_overlap] | 9 | 4.03 | [1.76, 6.52] | 8 / 1 |
| r_alt_shift[nongov_same_unit_near_low_overlap] | 9 | -3.39 | [-5.32, -1.55] | 1 / 8 |
| gold_shift[nongov_same_unit_moderate] | 10 | 0.49 | [-0.85, 2.14] | 4 / 6 |
| decoy_shift[nongov_same_unit_moderate] | 10 | 3.50 | [1.50, 5.94] | 9 / 1 |
| r_alt_shift[nongov_same_unit_moderate] | 10 | -3.01 | [-4.28, -1.74] | 1 / 9 |
| gold_shift[nongov_same_unit_far] | 10 | 0.61 | [-0.77, 2.16] | 6 / 4 |
| decoy_shift[nongov_same_unit_far] | 10 | 5.26 | [3.23, 7.42] | 9 / 1 |
| r_alt_shift[nongov_same_unit_far] | 10 | -4.65 | [-7.51, -2.49] | 1 / 9 |
| gold_shift[nongov_incompatible_unit_near] | 10 | -0.70 | [-1.65, 0.03] | 2 / 8 |
| decoy_shift[nongov_incompatible_unit_near] | 10 | 0.65 | [-0.58, 2.19] | 6 / 4 |
| r_alt_shift[nongov_incompatible_unit_near] | 10 | -1.35 | [-2.29, -0.52] | 2 / 8 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_far] | 10 | 0.89 | [-2.32, 4.25] | 6 / 4 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_incompatible_unit_near] | 10 | -2.41 | [-3.71, -1.20] | 1 / 9 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_moderate] | 10 | -0.75 | [-2.00, 0.25] | 3 / 7 |

## qwen_primary

**dtype noise, bfloat16 minus float32, gold log-probability per record:** n 211; mean 0.035; SD 0.186; MAD 0.096; median |difference| 0.103; 95th percentile 0.375; max 0.648.

Generations: the parsed answer is identical across dtypes in 196 of 209 records parsed in both; the correctness label agrees in 209 of 211.

**run-to-run, bfloat16 (this job against job 399969):** n 211; max |difference| 0.000; median 0.000.

| Stage 14.8 contrast | n | SD of the dtype difference | 95th percentile of its absolute value |
|---|---|---|---|
| gold_lp[nonnumeric_extra] - gold_lp[no_cue] | 20 | 0.215 | 0.369 |
| gold_lp[numeric_metadata] - gold_lp[no_cue] | 20 | 0.176 | 0.302 |
| gold_lp[nongov_same_unit_near_high_overlap] - gold_lp[no_cue] | 20 | 0.203 | 0.405 |
| gold_lp[nongov_same_unit_near_low_overlap] - gold_lp[no_cue] | 15 | 0.244 | 0.441 |
| gold_lp[nongov_same_unit_moderate] - gold_lp[no_cue] | 20 | 0.266 | 0.542 |
| gold_lp[nongov_same_unit_far] - gold_lp[no_cue] | 20 | 0.262 | 0.425 |
| gold_lp[nongov_incompatible_unit_near] - gold_lp[no_cue] | 20 | 0.198 | 0.412 |
| gold_lp[nongov_same_magnitude_convertible_unit] - gold_lp[no_cue] | 16 | 0.224 | 0.376 |
| gold_lp[near_high_overlap] - gold_lp[far] | 20 | 0.276 | 0.554 |
| gold_lp[near_high_overlap] - gold_lp[moderate] | 20 | 0.284 | 0.552 |
| gold_lp[near_high_overlap] - gold_lp[incompatible_unit_near] | 20 | 0.243 | 0.427 |
| gold_lp[near_high_overlap] - gold_lp[convertible_unit] | 16 | 0.195 | 0.327 |
| R_alt[near_high_overlap] - R_alt[far] | 20 | 0.309 | 0.540 |
| R_alt[near_high_overlap] - R_alt[moderate] | 20 | 0.257 | 0.403 |
| R_alt[near_high_overlap] - R_alt[incompatible_unit_near] | 20 | 0.235 | 0.465 |

| Anchor-matched shift from the no-cue prompt (nats) | structures | mean | 95% cluster-bootstrap interval | up / down |
|---|---|---|---|---|
| gold_shift[nongov_same_unit_near_high_overlap] | 10 | 1.98 | [-0.57, 4.74] | 6 / 4 |
| decoy_shift[nongov_same_unit_near_high_overlap] | 10 | 12.77 | [7.46, 18.32] | 9 / 1 |
| r_alt_shift[nongov_same_unit_near_high_overlap] | 10 | -10.79 | [-15.45, -6.04] | 0 / 10 |
| gold_shift[nongov_same_unit_near_low_overlap] | 9 | 1.00 | [-2.90, 4.48] | 5 / 4 |
| decoy_shift[nongov_same_unit_near_low_overlap] | 9 | 13.29 | [8.56, 18.22] | 9 / 0 |
| r_alt_shift[nongov_same_unit_near_low_overlap] | 9 | -12.29 | [-16.64, -7.55] | 1 / 8 |
| gold_shift[nongov_same_unit_moderate] | 10 | 0.63 | [-2.23, 3.60] | 4 / 6 |
| decoy_shift[nongov_same_unit_moderate] | 10 | 9.87 | [6.07, 13.93] | 10 / 0 |
| r_alt_shift[nongov_same_unit_moderate] | 10 | -9.24 | [-13.21, -5.44] | 1 / 9 |
| gold_shift[nongov_same_unit_far] | 10 | 2.04 | [-0.65, 4.97] | 5 / 5 |
| decoy_shift[nongov_same_unit_far] | 10 | 13.54 | [10.70, 16.71] | 10 / 0 |
| r_alt_shift[nongov_same_unit_far] | 10 | -11.50 | [-15.21, -8.35] | 0 / 10 |
| gold_shift[nongov_incompatible_unit_near] | 10 | 1.10 | [-1.36, 3.90] | 4 / 6 |
| decoy_shift[nongov_incompatible_unit_near] | 10 | 3.57 | [0.18, 8.02] | 8 / 2 |
| r_alt_shift[nongov_incompatible_unit_near] | 10 | -2.48 | [-5.68, 0.74] | 3 / 7 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_far] | 10 | 0.71 | [-5.43, 6.63] | 5 / 5 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_incompatible_unit_near] | 10 | -8.31 | [-10.87, -5.60] | 0 / 10 |
| r_alt_shift[nongov_same_unit_near_high_overlap] - r_alt_shift[nongov_same_unit_moderate] | 10 | -1.55 | [-6.66, 2.46] | 6 / 4 |
