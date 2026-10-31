# Stage 14.20 thinking-model run: Qwen/Qwen3-32B (descriptive)

Exploratory; data role EXPLORATION; not paper-eligible; nothing here is a confirmation. TRUNCATED and other ungraded outcomes are
NOT_EVALUATED, never wrong. The structure is the independent unit; intervals are cluster bootstrap over structures (2,000, seed 42).

Records 20; generated tokens 93638; generation time 4496.32 s; aggregate 20.8 tokens/s; tokens per record median 4983, 90th percentile 8192, maximum 8192; batch size [2].

Parse statuses {'PARSED': 15, 'TRUNCATED': 5}; correctness {'wrong': 4, 'TRUNCATED': 5, 'correct': 11}; thinking closed 0.750; truncated 0.250; correct share of graded 0.733 (11 of 15); of all records 0.550.

Problems 20: {'CONSISTENT_ANCHOR': 11, 'INCOMPLETE': 5, 'FAILED': 4}. Overall correct rate by structure 0.733 [0.4666666666666667, 0.9333333333333333].

Consistent anchors: 11 problems from 11 structures; distractor endpoint: NOT_EVALUATED: 11 anchor structures, at least 20 needed.

## Level (author-judged)

| group | problems | classes | correct rate by structure | 95% interval |
|---|---|---|---|---|
| high_school | 9 | {'CONSISTENT_ANCHOR': 5, 'INCOMPLETE': 2, 'FAILED': 2} | 0.714 | [0.286, 1.000] |
| intro_university | 10 | {'CONSISTENT_ANCHOR': 6, 'FAILED': 2, 'INCOMPLETE': 2} | 0.750 | [0.375, 1.000] |
| upper_university | 1 | {'INCOMPLETE': 1} | NOT_EVALUATED | NOT_EVALUATED |

## Domain

| group | problems | classes | correct rate by structure | 95% interval |
|---|---|---|---|---|
| acoustics | 1 | {'CONSISTENT_ANCHOR': 1} | 1.000 | NOT_EVALUATED |
| circuits | 1 | {'FAILED': 1} | 0.000 | NOT_EVALUATED |
| electromagnetism | 2 | {'FAILED': 1, 'CONSISTENT_ANCHOR': 1} | 0.500 | [0.000, 1.000] |
| fluids | 1 | {'CONSISTENT_ANCHOR': 1} | 1.000 | NOT_EVALUATED |
| mechanics | 6 | {'CONSISTENT_ANCHOR': 4, 'INCOMPLETE': 2} | 1.000 | [1.000, 1.000] |
| nuclear physics | 1 | {'FAILED': 1} | 0.000 | NOT_EVALUATED |
| optics | 1 | {'CONSISTENT_ANCHOR': 1} | 1.000 | NOT_EVALUATED |
| quantum | 3 | {'INCOMPLETE': 2, 'FAILED': 1} | 0.000 | NOT_EVALUATED |
| thermodynamics | 4 | {'CONSISTENT_ANCHOR': 3, 'INCOMPLETE': 1} | 1.000 | [1.000, 1.000] |
