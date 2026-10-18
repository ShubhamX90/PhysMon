# Stage 14.16 legacy-family X03 analysis (descriptive, precision-limited)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Rule frozen in J14.16-003 before the run.
Presence effect (nats) = candidate numeral's log-probability under its own rendering minus the same string under renderings where
the numeral does not appear. Cluster bootstrap over template clusters (2,000 resamples, seed 42).

## Qwen/Qwen2.5-7B-Instruct

Wrappers that dominate: none; invariance: True. invariance means no interval excludes zero at this number of clusters; it is not equivalence.

| Wrapper | group | clusters | presence effect [interval] | minus answer_line [interval] | dominates |
|---|---|---|---|---|---|
| answer_line | all numeral-cue families | 35 | 2.19 [1.38, 3.20] | reference | - |
| answer_line | nongoverning_distractor | 28 | 2.80 [1.74, 4.07] | reference | - |
| answer_line | irrelevant_variable | 11 | 0.38 [-0.29, 0.97] | reference | - |
| boxed | all numeral-cue families | 35 | 2.55 [1.67, 3.67] | 0.37 [-0.39, 1.05] | False |
| boxed | nongoverning_distractor | 28 | 3.30 [2.22, 4.62] | 0.50 [-0.42, 1.32] | False |
| boxed | irrelevant_variable | 11 | 0.37 [-0.16, 0.85] | -0.01 [-0.48, 0.46] | False |
| json | all numeral-cue families | 35 | 2.18 [1.40, 3.13] | -0.01 [-0.55, 0.51] | False |
| json | nongoverning_distractor | 28 | 2.75 [1.82, 3.83] | -0.05 [-0.76, 0.58] | False |
| json | irrelevant_variable | 11 | 0.47 [-0.08, 1.09] | 0.10 [-0.71, 1.19] | False |
| plain | all numeral-cue families | 35 | 1.75 [0.99, 2.71] | -0.44 [-1.12, 0.15] | False |
| plain | nongoverning_distractor | 28 | 2.36 [1.50, 3.42] | -0.44 [-1.23, 0.31] | False |
| plain | irrelevant_variable | 11 | -0.04 [-0.65, 0.67] | -0.42 [-1.34, 0.34] | False |

| Wrapper | D_lp range mean [interval] | minus answer_line [interval] |
|---|---|---|
| answer_line | 1.98 [1.18, 3.06] | reference |
| boxed | 2.53 [1.51, 3.68] | 0.55 [-0.13, 1.33] |
| json | 1.70 [1.02, 2.52] | -0.28 [-0.90, 0.28] |
| plain | 2.25 [1.35, 3.33] | 0.27 [-0.37, 0.94] |

## meta-llama/Llama-3.1-8B-Instruct

Wrappers that dominate: none; invariance: False. invariance means no interval excludes zero at this number of clusters; it is not equivalence.

| Wrapper | group | clusters | presence effect [interval] | minus answer_line [interval] | dominates |
|---|---|---|---|---|---|
| answer_line | all numeral-cue families | 35 | 1.18 [0.73, 1.73] | reference | - |
| answer_line | nongoverning_distractor | 28 | 1.47 [0.95, 2.07] | reference | - |
| answer_line | irrelevant_variable | 11 | 0.55 [-0.14, 1.60] | reference | - |
| boxed | all numeral-cue families | 35 | 0.96 [0.52, 1.43] | -0.22 [-0.42, -0.05] | False |
| boxed | nongoverning_distractor | 28 | 1.24 [0.75, 1.82] | -0.23 [-0.47, -0.01] | False |
| boxed | irrelevant_variable | 11 | 0.35 [-0.25, 1.23] | -0.20 [-0.45, 0.02] | False |
| json | all numeral-cue families | 35 | 1.15 [0.64, 1.74] | -0.03 [-0.30, 0.28] | False |
| json | nongoverning_distractor | 28 | 1.33 [0.70, 2.11] | -0.15 [-0.48, 0.30] | False |
| json | irrelevant_variable | 11 | 1.01 [0.34, 2.06] | 0.46 [0.15, 0.81] | True |
| plain | all numeral-cue families | 35 | 1.55 [0.91, 2.31] | 0.36 [0.02, 0.75] | False |
| plain | nongoverning_distractor | 28 | 1.95 [1.13, 2.88] | 0.48 [-0.01, 1.00] | False |
| plain | irrelevant_variable | 11 | 0.84 [0.16, 1.90] | 0.29 [0.02, 0.57] | True |

| Wrapper | D_lp range mean [interval] | minus answer_line [interval] |
|---|---|---|
| answer_line | 0.90 [0.58, 1.28] | reference |
| boxed | 0.97 [0.69, 1.30] | 0.07 [-0.12, 0.24] |
| json | 0.96 [0.63, 1.33] | 0.06 [-0.25, 0.37] |
| plain | 1.62 [1.16, 2.12] | 0.72 [0.41, 1.07] |
