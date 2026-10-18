# Stage 14.10 X03 wrapper analysis (descriptive, precision-limited)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Quantities are anchor-matched shifts of R_alt
(nats) from the no-cue prompt, by structure (n = 10); intervals are cluster bootstrap over structures (2,000 resamples, seed 42).
Criteria were frozen in J14.10-001 before the run. Raw sums are compared within a wrapper only.

## Qwen/Qwen2.5-7B-Instruct

Wrappers that dominate the near-cell shift: ['scientific']; invariance (no interval excludes zero): False. invariance means no interval excludes zero at ten structures; it is not equivalence.

| Wrapper | records | parsed | correct | mean gold tokens | near-cell shift (mean [interval]) | minus answer_line [interval] | excludes zero | dominates | D_lp range mean |
|---|---|---|---|---|---|---|---|---|---|
| answer_line | 211 | 209 | 3 | 9.1 | -10.79 [-15.30, -6.13] | reference | - | - | 9.52 |
| boxed | 211 | 162 | 3 | 10.1 | -11.42 [-16.20, -6.84] | -0.63 [-2.25, 0.79] | False | False | 9.54 |
| decimal_plain | 211 | 168 | 2 | 9.1 | -10.09 [-13.86, -6.02] | 0.70 [-0.86, 2.39] | False | False | 9.08 |
| json | 211 | 210 | 1 | 16.1 | -10.52 [-15.05, -5.92] | 0.27 [-1.03, 1.73] | False | False | 8.09 |
| plain | 211 | 208 | 6 | 6.2 | -8.73 [-12.65, -4.74] | 2.06 [0.66, 3.55] | True | False | 9.40 |
| scientific | 211 | 211 | 2 | 11.1 | -3.95 [-7.56, -0.64] | 6.84 [3.99, 9.95] | True | True | 9.40 |
| sentence | 211 | 201 | 3 | 11.1 | -11.05 [-15.66, -6.31] | -0.27 [-1.55, 1.32] | False | False | 9.38 |

## meta-llama/Llama-3.1-8B-Instruct

Wrappers that dominate the near-cell shift: none; invariance (no interval excludes zero): False. invariance means no interval excludes zero at ten structures; it is not equivalence.

| Wrapper | records | parsed | correct | mean gold tokens | near-cell shift (mean [interval]) | minus answer_line [interval] | excludes zero | dominates | D_lp range mean |
|---|---|---|---|---|---|---|---|---|---|
| answer_line | 211 | 211 | 6 | 7.5 | -3.76 [-5.80, -1.94] | reference | - | - | 3.34 |
| boxed | 211 | 211 | 9 | 8.5 | -3.11 [-5.02, -1.62] | 0.64 [0.24, 1.12] | True | False | 3.39 |
| decimal_plain | 211 | 206 | 4 | 7.5 | -2.96 [-6.04, -0.57] | 0.79 [-1.85, 2.65] | False | False | 5.26 |
| json | 211 | 210 | 4 | 14.5 | -3.56 [-5.27, -2.07] | 0.20 [-0.42, 0.83] | False | False | 3.44 |
| plain | 211 | 211 | 9 | 4.6 | -2.68 [-4.66, -0.98] | 1.08 [-0.01, 2.03] | False | False | 2.80 |
| scientific | 211 | 193 | 0 | 9.6 | -2.60 [-3.94, -1.55] | 1.16 [-0.67, 3.41] | False | False | 4.27 |
| sentence | 211 | 211 | 7 | 9.5 | -3.74 [-6.03, -1.79] | 0.02 [-0.33, 0.46] | False | False | 3.26 |
