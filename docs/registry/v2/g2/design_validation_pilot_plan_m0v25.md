# G2 step 1: design-validation pilot, re-planned on M0 v2.5 · fixed before any record (2026-11-19)

Supersedes the dataset choice of `design_validation_pilot_plan.md` (2026-11-16), whose runs on M0 v2.2 were deactivated before any
record existed (J15.1-046). Everything in that document applies unchanged (runs, k = 24, token limits, the four design questions,
decision rules, "not done here"), with only these substitutions:

* Dataset: `data/v2/dataset/m0_v25/cells.jsonl` (11 structures, 411 cells), the final M0: every structure two-judge ADMITTED
  (Claude Opus 5.5 + GPT-6.1 Sol, prompt v3, amendment A1 guard) and every role sentence natural (J15.1-048, -051, -053).
* Run ids: `s15_g2pilot_m0v25_qwen25_7b`, `s15_g2pilot_m0v25_llama31_8b`, `s15_g2pilot_m0v25_qwen3_8b_nothink` (same models,
  thinking settings and parity basis).
* Medium-flag sentences reported separately under design question 3: S26 R1 and S55 R1 (minority before/after reading noted by the
  Claude judge on M0 v2.4/v2.5).

Written after the panel reviews and before any model output on any M0 v2.x cell. Journal J15.1-054.
