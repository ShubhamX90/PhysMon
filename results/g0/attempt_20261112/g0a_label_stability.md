# G0 (a): cross-instruction stability of the legacy S_lp label (30 pilot families)

Data role EXPLORATION; audit of committed Phase-I records; not evidence for any v2 claim.
Threshold 0.5 nats. Agreement is the number of the n families with the same label in both runs; `chance` is the agreement expected from the two positive rates alone.

| Model | Pair | n | Spearman | Label agreement | Chance | Positives (a / b) |
|---|---|---|---|---|---|---|
| qwen | stage4_repair__vs__stage6_panel__pilot | 30 | 0.043 | 17 of 30 | 0.54 | 9 / 12 |
| qwen | stage4_original__vs__stage4_repair__pilot | 30 | 0.309 | 17 of 30 | 0.567 | 10 / 9 |
| qwen | stage4_original__vs__stage6_panel__pilot | 30 | 0.035 | 18 of 30 | 0.533 | 10 / 12 |
| qwen | stage6_d1__vs__stage6_panel__pilot | 0 | NOT_EVALUATED | only 0 pilot families present in both runs (need >= 3) | | |
| qwen | stage6_d1__vs__stage6_panel__shared | 40 | 1.0 | 40 of 40 | 0.501 | 19 / 19 |
| llama | stage4_repair__vs__stage6_panel__pilot | 30 | 0.447 | 27 of 30 | 0.847 | 2 / 3 |
| llama | stage4_original__vs__stage4_repair__pilot | 30 | 0.364 | 27 of 30 | 0.904 | 1 / 2 |
| llama | stage4_original__vs__stage6_panel__pilot | 30 | 0.11 | 26 of 30 | 0.873 | 1 / 3 |
| llama | stage6_d1__vs__stage6_panel__pilot | 0 | NOT_EVALUATED | only 0 pilot families present in both runs (need >= 3) | | |
| llama | stage6_d1__vs__stage6_panel__shared | 40 | 1.0 | 40 of 40 | 0.625 | 10 / 10 |

## Runs

- `stage4_original` (commit 31a7857, one-line system prompt in runner: False): qwen: median 0.0 chars, 0.0 start with 'Answer:'; llama: median 126.0 chars, 0.0 start with 'Answer:'
- `stage4_repair` (commit 953c31e, one-line system prompt in runner: False): qwen: median 717.5 chars, 0.0 start with 'Answer:'; llama: median 450.0 chars, 0.0 start with 'Answer:'
- `stage6_d1` (commit 0894353, one-line system prompt in runner: True): qwen: median 14.0 chars, 1.0 start with 'Answer:'; llama: median 15.0 chars, 1.0 start with 'Answer:'
- `stage6_panel` (commit ffeeeff, one-line system prompt in runner: True): qwen: median 15.0 chars, 1.0 start with 'Answer:'; llama: median 15.0 chars, 1.0 start with 'Answer:'

## Recomputation from raw records

- qwen `stage4_original`: NOT_EVALUATED (120 (family, variant) cells have several records (several runs in one file))
- qwen `stage4_repair`: EVALUATED (recomputed from records; 30 compared with the CSV, 0 mismatches)
- qwen `stage6_d1`: EVALUATED (recomputed from records)
- qwen `stage6_panel`: EVALUATED (recomputed from records; 30 compared with the CSV, 0 mismatches)
- llama `stage4_original`: EVALUATED (recomputed from records; 30 compared with the CSV, 0 mismatches)
- llama `stage4_repair`: EVALUATED (recomputed from records; 30 compared with the CSV, 0 mismatches)
- llama `stage6_d1`: EVALUATED (recomputed from records)
- llama `stage6_panel`: EVALUATED (recomputed from records; 30 compared with the CSV, 0 mismatches)
