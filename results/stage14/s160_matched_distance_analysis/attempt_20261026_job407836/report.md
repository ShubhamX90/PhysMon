# Stage 14.17 plausibility-matched numeral-presence control (descriptive, precision-limited)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Adjusted presence effect = log-probability
(nats) of a numeral that appears in the prompt, as an answer with the target unit, minus the mean of matched absent numerals of the
same shape at about the same distance from the gold. Intervals are cluster bootstrap over structures (2,000 resamples, seed 42).
Reading rule: 'above plausibility' needs an interval above zero and a mean of at least 0.4 nats; otherwise 'not
distinguishable from plausibility at this precision', which is not equivalence.

## Qwen/Qwen2.5-7B-Instruct

### primary, batch A

Numerals without an effect: 46.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | 0.93 | [-1.29, 3.37] | 6 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 6 | 3.40 | [1.45, 5.57] | 6 / 0 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | -0.74 | [-2.99, 0.91] | 7 / 3 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 6.52 | [4.58, 8.58] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 4.51 | [2.24, 6.62] | 8 / 2 | above plausibility |
| relevant_input | 10 | 2.37 | [0.89, 3.78] | 8 / 2 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 3.43 | [1.29, 5.53] | 9 / 1 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -1.23 | [-3.92, 1.62] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 6 | 1.74 | [-1.80, 4.27] | 5 / 1 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -2.72 | [-6.24, 0.08] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 4.43 | [2.94, 6.05] | 10 / 0 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 2.68 | [1.17, 4.10] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 6.75 | [4.15, 9.71] | 10 / 0 | above plausibility |

### primary, batch B

Numerals without an effect: 10.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -1.22 | [-2.26, -0.10] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 8 | 5.55 | [0.80, 9.96] | 6 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | 0.07 | [-2.12, 2.28] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 5.17 | [3.45, 6.78] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 6.41 | [4.70, 8.15] | 10 / 0 | above plausibility |
| relevant_input | 10 | 4.16 | [2.80, 5.53] | 9 / 1 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 4.32 | [1.83, 6.58] | 9 / 1 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -4.49 | [-6.30, -2.43] | 1 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 8 | 0.98 | [-3.75, 5.96] | 4 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -3.18 | [-6.02, -0.56] | 2 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 0.37 | [-1.36, 2.23] | 4 / 6 | not distinguishable from plausibility at this precision |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 4.11 | [2.30, 5.82] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 3.86 | [1.22, 6.69] | 8 / 2 | above plausibility |

### primary, batch A+B (descriptive pooling)

Numerals without an effect: 56.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 20 | -0.15 | [-1.37, 1.30] | 9 / 11 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 14 | 4.63 | [1.76, 7.69] | 12 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 20 | -0.34 | [-1.84, 1.12] | 12 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 20 | 5.84 | [4.57, 7.23] | 20 / 0 | above plausibility |
| cue_relevant_reference | 20 | 5.46 | [3.89, 6.84] | 18 / 2 | above plausibility |
| relevant_input | 20 | 3.27 | [2.15, 4.38] | 17 / 3 | above plausibility |
| relevant_input[no_cue prompt only] | 20 | 3.88 | [2.27, 5.45] | 18 / 2 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 20 | -2.86 | [-4.60, -1.04] | 4 / 16 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 14 | 1.31 | [-1.74, 4.39] | 9 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 20 | -2.95 | [-5.16, -0.86] | 5 / 15 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 20 | 2.40 | [0.94, 3.87] | 14 / 6 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 20 | 3.39 | [2.26, 4.57] | 18 / 2 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 20 | 5.31 | [3.39, 7.33] | 18 / 2 | above plausibility |

### within_factor_2, batch A

Numerals without an effect: 60.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | 0.93 | [-1.30, 3.23] | 6 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 6 | 3.40 | [1.45, 5.59] | 6 / 0 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | -1.11 | [-3.69, 0.65] | 7 / 3 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 6.63 | [4.68, 8.62] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 4.51 | [2.17, 6.67] | 8 / 2 | above plausibility |
| relevant_input | 10 | 2.31 | [0.81, 3.76] | 8 / 2 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 3.34 | [1.18, 5.43] | 9 / 1 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -1.15 | [-3.74, 1.54] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 6 | 1.72 | [-1.63, 4.28] | 5 / 1 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -2.93 | [-6.99, 0.12] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 4.66 | [3.14, 6.22] | 10 / 0 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 2.65 | [1.28, 4.00] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 7.35 | [4.56, 10.53] | 10 / 0 | above plausibility |

### within_factor_2, batch B

Numerals without an effect: 14.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -0.92 | [-2.27, 0.83] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 8 | 5.55 | [1.01, 10.11] | 6 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | -0.36 | [-2.57, 1.90] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 5.21 | [3.71, 6.84] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 6.41 | [4.80, 8.10] | 10 / 0 | above plausibility |
| relevant_input | 10 | 4.16 | [2.77, 5.56] | 9 / 1 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 4.32 | [1.67, 6.66] | 9 / 1 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -4.19 | [-6.01, -2.19] | 1 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 8 | 0.98 | [-3.99, 6.06] | 4 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -3.18 | [-6.14, -0.29] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 0.45 | [-1.23, 2.35] | 4 / 6 | not distinguishable from plausibility at this precision |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 4.11 | [2.35, 5.80] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 3.79 | [1.06, 6.58] | 8 / 2 | above plausibility |

### within_factor_2, batch A+B (descriptive pooling)

Numerals without an effect: 74.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 20 | 0.00 | [-1.36, 1.53] | 9 / 11 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 14 | 4.63 | [1.89, 7.64] | 12 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 20 | -0.74 | [-2.50, 0.77] | 12 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 20 | 5.92 | [4.68, 7.26] | 20 / 0 | above plausibility |
| cue_relevant_reference | 20 | 5.46 | [4.01, 6.90] | 18 / 2 | above plausibility |
| relevant_input | 20 | 3.24 | [2.12, 4.31] | 17 / 3 | above plausibility |
| relevant_input[no_cue prompt only] | 20 | 3.83 | [2.13, 5.44] | 18 / 2 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 20 | -2.67 | [-4.34, -0.83] | 4 / 16 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 14 | 1.29 | [-1.76, 4.38] | 9 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 20 | -3.06 | [-5.45, -0.85] | 6 / 14 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 20 | 2.55 | [1.11, 4.05] | 14 / 6 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 20 | 3.38 | [2.22, 4.55] | 18 / 2 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 20 | 5.57 | [3.55, 7.82] | 18 / 2 | above plausibility |

### same_prefix_overlap, batch A

Numerals without an effect: 81.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | 0.89 | [-1.22, 3.25] | 6 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 3 | 3.32 | [1.66, 6.07] | 3 / 0 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | -0.65 | [-3.22, 1.04] | 7 / 3 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 6.55 | [4.65, 8.47] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 4.51 | [2.09, 6.56] | 8 / 2 | above plausibility |
| relevant_input | 10 | 2.45 | [0.90, 3.89] | 8 / 2 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 3.58 | [1.46, 5.63] | 9 / 1 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -1.37 | [-3.99, 1.36] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 3 | 3.50 | [3.03, 4.38] | 3 / 0 | above plausibility |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -2.79 | [-6.54, -0.08] | 2 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 4.46 | [2.97, 6.07] | 10 / 0 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 2.62 | [1.29, 4.05] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 6.94 | [4.61, 9.81] | 10 / 0 | above plausibility |

### same_prefix_overlap, batch B

Numerals without an effect: 42.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -1.65 | [-2.51, -0.69] | 1 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 1 | -1.03 | NOT_EVALUATED | - / - | NOT_EVALUATED |
| cue_nongoverning_isolated[incompatible] | 10 | -0.75 | [-2.33, 0.82] | 4 / 6 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 5.38 | [3.67, 7.14] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 6.41 | [4.74, 7.97] | 10 / 0 | above plausibility |
| relevant_input | 10 | 4.62 | [3.03, 6.04] | 9 / 1 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 4.93 | [2.35, 7.26] | 9 / 1 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -5.49 | [-7.46, -3.30] | 1 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 1 | -6.20 | NOT_EVALUATED | - / - | NOT_EVALUATED |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -4.58 | [-7.02, -2.22] | 0 / 10 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 0.09 | [-1.56, 1.86] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 4.18 | [2.50, 5.71] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 4.39 | [2.71, 6.59] | 10 / 0 | above plausibility |

### same_prefix_overlap, batch A+B (descriptive pooling)

Numerals without an effect: 123.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 20 | -0.38 | [-1.69, 1.02] | 7 / 13 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 4 | 2.23 | [-0.22, 4.96] | 3 / 1 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] | 20 | -0.70 | [-2.34, 0.54] | 11 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 20 | 5.97 | [4.71, 7.36] | 20 / 0 | above plausibility |
| cue_relevant_reference | 20 | 5.46 | [3.98, 6.91] | 18 / 2 | above plausibility |
| relevant_input | 20 | 3.54 | [2.33, 4.68] | 17 / 3 | above plausibility |
| relevant_input[no_cue prompt only] | 20 | 4.25 | [2.56, 5.86] | 18 / 2 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 20 | -3.43 | [-5.41, -1.41] | 4 / 16 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 4 | 1.08 | [-3.88, 4.04] | 3 / 1 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 20 | -3.68 | [-5.84, -1.85] | 2 / 18 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 20 | 2.27 | [0.82, 3.76] | 15 / 5 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 20 | 3.40 | [2.24, 4.51] | 18 / 2 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 20 | 5.67 | [4.03, 7.45] | 20 / 0 | above plausibility |

### Unadjusted (Stage 14.14 control) and adjusted effects of the same batch-A numerals

| Role | unadjusted | adjusted | difference |
|---|---|---|---|
| cue_irrelevant_metadata | 5.23 | 0.93 | 4.30 |
| cue_nongoverning_isolated[equivalent] | 9.43 | 3.40 | 6.03 |
| cue_nongoverning_isolated[incompatible] | 3.05 | -0.74 | 3.79 |
| cue_nongoverning_isolated[same] | 10.86 | 6.52 | 4.34 |
| cue_relevant_reference | 6.27 | 4.51 | 1.76 |
| relevant_input | 2.68 | 2.37 | 0.31 |
| relevant_input[no_cue prompt only] | 3.30 | 3.43 | -0.13 |

Reproducibility of the present-numeral scores against the Stage 14.14 run: {'n': 981, 'max_abs_difference': 0.0, 'mean_abs_difference': 0.0, 'n_exactly_equal': 981}.

## meta-llama/Llama-3.1-8B-Instruct

### primary, batch A

Numerals without an effect: 46.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -0.45 | [-1.06, 0.06] | 4 / 6 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 6 | 2.24 | [1.07, 3.29] | 6 / 0 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | -0.22 | [-0.62, 0.14] | 6 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 2.34 | [1.38, 3.38] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 2.65 | [2.06, 3.18] | 10 / 0 | above plausibility |
| relevant_input | 10 | 0.71 | [0.37, 1.08] | 9 / 1 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 0.60 | [0.22, 1.01] | 9 / 1 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -0.91 | [-1.46, -0.41] | 1 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 6 | 1.76 | [0.20, 3.16] | 5 / 1 | above plausibility |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -0.85 | [-1.83, 0.01] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 1.42 | [0.40, 2.45] | 8 / 2 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 1.38 | [0.52, 2.16] | 8 / 2 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 2.05 | [0.96, 3.22] | 10 / 0 | above plausibility |

### primary, batch B

Numerals without an effect: 10.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -0.15 | [-0.68, 0.33] | 6 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 8 | 4.85 | [1.14, 9.40] | 6 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | 0.74 | [0.18, 1.53] | 8 / 2 | above plausibility |
| cue_nongoverning_isolated[same] | 10 | 2.92 | [1.71, 4.02] | 9 / 1 | above plausibility |
| cue_relevant_reference | 10 | 4.56 | [3.15, 6.23] | 10 / 0 | above plausibility |
| relevant_input | 10 | 1.22 | [0.43, 2.01] | 8 / 2 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 1.42 | [0.22, 2.43] | 8 / 2 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -1.14 | [-2.11, -0.17] | 2 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 8 | 3.63 | [0.10, 8.33] | 6 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -0.29 | [-1.34, 0.83] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 1.88 | [0.72, 3.17] | 7 / 3 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 2.93 | [1.52, 4.42] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 0.72 | [-0.36, 1.71] | 7 / 3 | not distinguishable from plausibility at this precision |

### primary, batch A+B (descriptive pooling)

Numerals without an effect: 56.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 20 | -0.30 | [-0.72, 0.06] | 10 / 10 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 14 | 3.73 | [1.64, 6.55] | 12 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 20 | 0.26 | [-0.13, 0.72] | 14 / 6 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 20 | 2.63 | [1.89, 3.36] | 19 / 1 | above plausibility |
| cue_relevant_reference | 20 | 3.61 | [2.78, 4.59] | 20 / 0 | above plausibility |
| relevant_input | 20 | 0.96 | [0.53, 1.42] | 17 / 3 | above plausibility |
| relevant_input[no_cue prompt only] | 20 | 1.01 | [0.41, 1.60] | 17 / 3 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 20 | -1.02 | [-1.60, -0.50] | 3 / 17 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 14 | 2.83 | [0.76, 5.64] | 11 / 3 | above plausibility |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 20 | -0.57 | [-1.29, 0.16] | 8 / 12 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 20 | 1.65 | [0.85, 2.48] | 15 / 5 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 20 | 2.16 | [1.24, 3.11] | 17 / 3 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 20 | 1.38 | [0.55, 2.18] | 17 / 3 | above plausibility |

### within_factor_2, batch A

Numerals without an effect: 60.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -0.45 | [-1.06, 0.07] | 4 / 6 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 6 | 2.24 | [1.07, 3.41] | 6 / 0 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | -0.38 | [-0.82, 0.02] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 2.39 | [1.43, 3.43] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 2.65 | [2.08, 3.20] | 10 / 0 | above plausibility |
| relevant_input | 10 | 0.65 | [0.31, 0.99] | 9 / 1 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 0.54 | [0.17, 1.00] | 8 / 2 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -0.85 | [-1.40, -0.38] | 1 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 6 | 1.86 | [0.37, 3.19] | 5 / 1 | above plausibility |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -0.87 | [-1.71, -0.15] | 4 / 6 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 1.56 | [0.55, 2.56] | 8 / 2 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 1.35 | [0.48, 2.11] | 8 / 2 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 2.16 | [1.17, 3.34] | 10 / 0 | above plausibility |

### within_factor_2, batch B

Numerals without an effect: 14.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -0.13 | [-0.71, 0.36] | 6 / 4 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 8 | 4.85 | [1.29, 9.40] | 6 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | 0.75 | [0.27, 1.41] | 9 / 1 | above plausibility |
| cue_nongoverning_isolated[same] | 10 | 3.00 | [1.85, 4.11] | 9 / 1 | above plausibility |
| cue_relevant_reference | 10 | 4.56 | [3.14, 6.20] | 10 / 0 | above plausibility |
| relevant_input | 10 | 1.22 | [0.39, 2.00] | 8 / 2 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 1.42 | [0.19, 2.45] | 8 / 2 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -1.13 | [-2.13, -0.14] | 2 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 8 | 3.63 | [0.29, 8.22] | 6 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -0.34 | [-1.45, 0.82] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 1.94 | [0.70, 3.16] | 7 / 3 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 2.93 | [1.54, 4.50] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 0.76 | [-0.37, 1.72] | 8 / 2 | not distinguishable from plausibility at this precision |

### within_factor_2, batch A+B (descriptive pooling)

Numerals without an effect: 74.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 20 | -0.29 | [-0.71, 0.08] | 10 / 10 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 14 | 3.73 | [1.62, 6.66] | 12 / 2 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 20 | 0.19 | [-0.24, 0.67] | 14 / 6 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 20 | 2.70 | [1.95, 3.42] | 19 / 1 | above plausibility |
| cue_relevant_reference | 20 | 3.61 | [2.81, 4.56] | 20 / 0 | above plausibility |
| relevant_input | 20 | 0.94 | [0.50, 1.40] | 17 / 3 | above plausibility |
| relevant_input[no_cue prompt only] | 20 | 0.98 | [0.32, 1.57] | 16 / 4 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 20 | -0.99 | [-1.57, -0.44] | 3 / 17 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 14 | 2.87 | [0.79, 5.70] | 11 / 3 | above plausibility |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 20 | -0.61 | [-1.33, 0.15] | 7 / 13 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 20 | 1.75 | [0.89, 2.58] | 15 / 5 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 20 | 2.14 | [1.24, 3.08] | 17 / 3 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 20 | 1.46 | [0.69, 2.27] | 18 / 2 | above plausibility |

### same_prefix_overlap, batch A

Numerals without an effect: 81.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -0.34 | [-1.07, 0.23] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 3 | 1.14 | [0.36, 2.64] | 3 / 0 | above plausibility |
| cue_nongoverning_isolated[incompatible] | 10 | -0.24 | [-0.70, 0.20] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 10 | 2.23 | [1.23, 3.37] | 10 / 0 | above plausibility |
| cue_relevant_reference | 10 | 2.65 | [2.04, 3.19] | 10 / 0 | above plausibility |
| relevant_input | 10 | 0.69 | [0.33, 1.08] | 9 / 1 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 0.58 | [0.18, 1.07] | 7 / 3 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -0.81 | [-1.39, -0.24] | 1 / 9 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 3 | 0.68 | [-1.53, 3.12] | 2 / 1 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -0.93 | [-1.87, -0.15] | 3 / 7 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 1.39 | [0.29, 2.53] | 8 / 2 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 1.44 | [0.53, 2.25] | 8 / 2 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 2.10 | [1.05, 3.21] | 10 / 0 | above plausibility |

### same_prefix_overlap, batch B

Numerals without an effect: 42.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | -0.29 | [-0.97, 0.26] | 5 / 5 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 1 | -2.98 | NOT_EVALUATED | - / - | NOT_EVALUATED |
| cue_nongoverning_isolated[incompatible] | 10 | 0.70 | [0.06, 1.45] | 7 / 3 | above plausibility |
| cue_nongoverning_isolated[same] | 10 | 2.84 | [1.71, 3.90] | 9 / 1 | above plausibility |
| cue_relevant_reference | 10 | 4.56 | [3.10, 6.13] | 10 / 0 | above plausibility |
| relevant_input | 10 | 1.41 | [0.52, 2.21] | 8 / 2 | above plausibility |
| relevant_input[no_cue prompt only] | 10 | 1.68 | [0.33, 2.78] | 8 / 2 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | -1.47 | [-2.64, -0.41] | 2 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 1 | -3.31 | NOT_EVALUATED | - / - | NOT_EVALUATED |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | -0.53 | [-1.58, 0.52] | 4 / 6 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 1.60 | [0.38, 2.88] | 7 / 3 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 2.79 | [1.44, 4.14] | 9 / 1 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 10 | 0.80 | [-0.33, 1.85] | 7 / 3 | not distinguishable from plausibility at this precision |

### same_prefix_overlap, batch A+B (descriptive pooling)

Numerals without an effect: 123.

| Role | structures | mean adjusted effect | 95% interval | up / down | reading |
|---|---|---|---|---|---|
| cue_irrelevant_metadata | 20 | -0.32 | [-0.78, 0.10] | 10 / 10 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] | 4 | 0.11 | [-2.13, 2.09] | 3 / 1 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] | 20 | 0.23 | [-0.21, 0.72] | 12 / 8 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] | 20 | 2.53 | [1.75, 3.35] | 19 / 1 | above plausibility |
| cue_relevant_reference | 20 | 3.61 | [2.75, 4.58] | 20 / 0 | above plausibility |
| relevant_input | 20 | 1.05 | [0.58, 1.54] | 17 / 3 | above plausibility |
| relevant_input[no_cue prompt only] | 20 | 1.13 | [0.42, 1.82] | 15 / 5 | above plausibility |
| *paired within a prompt* | | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 20 | -1.14 | [-1.82, -0.48] | 3 / 17 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 4 | -0.32 | [-2.42, 1.96] | 2 / 2 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 20 | -0.73 | [-1.43, -0.06] | 7 / 13 | not distinguishable from plausibility at this precision |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 20 | 1.49 | [0.68, 2.33] | 15 / 5 | above plausibility |
| cue_relevant_reference minus relevant_input (same prompt) | 20 | 2.11 | [1.25, 3.00] | 17 / 3 | above plausibility |
| same-unit near cue minus incompatible-unit near cue | 20 | 1.45 | [0.62, 2.29] | 17 / 3 | above plausibility |

### Unadjusted (Stage 14.14 control) and adjusted effects of the same batch-A numerals

| Role | unadjusted | adjusted | difference |
|---|---|---|---|
| cue_irrelevant_metadata | 2.24 | -0.45 | 2.69 |
| cue_nongoverning_isolated[equivalent] | 5.58 | 2.24 | 3.34 |
| cue_nongoverning_isolated[incompatible] | 2.87 | -0.22 | 3.08 |
| cue_nongoverning_isolated[same] | 4.96 | 2.34 | 2.62 |
| cue_relevant_reference | 4.81 | 2.65 | 2.16 |
| relevant_input | 1.30 | 0.71 | 0.59 |
| relevant_input[no_cue prompt only] | 1.31 | 0.60 | 0.71 |

Reproducibility of the present-numeral scores against the Stage 14.14 run: {'n': 981, 'max_abs_difference': 0.0, 'mean_abs_difference': 0.0, 'n_exactly_equal': 981}.
