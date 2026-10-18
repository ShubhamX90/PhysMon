# Stage 14.14 numeral-presence control (descriptive, precision-limited)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. Presence effect = log-probability (nats) of a
numeral that appears in the prompt, as an answer with the target unit, minus that of a matched absent numeral under the same prompt.
Ten structures; intervals are cluster bootstrap (2,000 resamples, seed 42).

## Qwen/Qwen2.5-7B-Instruct

Numerals 981; NOT_EVALUATED 0.

| Role | structures | mean presence effect | 95% interval | up / down |
|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | 5.23 | [1.10, 9.24] | 8 / 2 |
| cue_nongoverning_isolated[equivalent] | 8 | 8.81 | [5.96, 11.77] | 8 / 0 |
| cue_nongoverning_isolated[incompatible] | 10 | 4.04 | [0.18, 8.06] | 7 / 3 |
| cue_nongoverning_isolated[same] | 10 | 10.86 | [7.36, 14.24] | 10 / 0 |
| cue_relevant_reference | 10 | 6.27 | [2.42, 9.91] | 9 / 1 |
| relevant_input | 10 | 2.80 | [0.66, 4.77] | 8 / 2 |
| relevant_input[no_cue prompt only] | 10 | 3.36 | [0.48, 6.16] | 9 / 1 |
| *paired within a prompt* | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | 2.92 | [-1.78, 7.83] | 7 / 3 |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 8 | 6.58 | [4.05, 9.43] | 8 / 0 |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | 1.52 | [-3.12, 6.25] | 6 / 4 |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 8.25 | [5.07, 11.60] | 9 / 1 |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 3.20 | [0.03, 6.43] | 6 / 4 |
| same-unit near cue minus incompatible-unit near cue | 10 | 8.26 | [4.25, 12.81] | 9 / 1 |

## meta-llama/Llama-3.1-8B-Instruct

Numerals 981; NOT_EVALUATED 0.

| Role | structures | mean presence effect | 95% interval | up / down |
|---|---|---|---|---|
| cue_irrelevant_metadata | 10 | 2.24 | [1.07, 3.50] | 8 / 2 |
| cue_nongoverning_isolated[equivalent] | 8 | 4.93 | [3.27, 6.82] | 8 / 0 |
| cue_nongoverning_isolated[incompatible] | 10 | 3.04 | [1.23, 5.07] | 9 / 1 |
| cue_nongoverning_isolated[same] | 10 | 4.97 | [3.23, 6.68] | 9 / 1 |
| cue_relevant_reference | 10 | 4.81 | [3.67, 5.95] | 10 / 0 |
| relevant_input | 10 | 1.24 | [0.36, 2.15] | 8 / 2 |
| relevant_input[no_cue prompt only] | 10 | 1.22 | [0.10, 2.32] | 8 / 2 |
| *paired within a prompt* | | | | |
| cue_irrelevant_metadata minus relevant_input (same prompt) | 10 | 1.19 | [0.14, 2.38] | 8 / 2 |
| cue_nongoverning_isolated[equivalent] minus relevant_input (same prompt) | 8 | 3.81 | [1.73, 5.94] | 7 / 1 |
| cue_nongoverning_isolated[incompatible] minus relevant_input (same prompt) | 10 | 1.55 | [-0.40, 3.46] | 8 / 2 |
| cue_nongoverning_isolated[same] minus relevant_input (same prompt) | 10 | 3.58 | [2.22, 4.91] | 10 / 0 |
| cue_relevant_reference minus relevant_input (same prompt) | 10 | 2.97 | [1.92, 3.96] | 9 / 1 |
| same-unit near cue minus incompatible-unit near cue | 10 | 2.07 | [0.26, 3.94] | 7 / 3 |
