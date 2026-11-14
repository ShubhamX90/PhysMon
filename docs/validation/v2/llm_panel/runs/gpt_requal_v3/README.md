# GPT-6.1 Sol requalification run `gpt_requal_v3` (prompt v3, bank v5, protocol v3)

* `codex exec` on the cluster (`s182 run --model gpt-6.1-sol --reasoning-effort high --workers 3`), kit
  `/scratch/pabitra/physmon/judge_gpt/gpt_requal_v3_kit` (prompt v3 sha256 55585308...). 64 calls, all complete.
* `events_audit.json`: `s184`, all 64 event streams clean. `events/`, `reviews/`, `run_log.jsonl`, `summary.json`: unchanged.
* `score.json`: `s179 --split requal --protocol v3`. **QUALIFIED**: R1 21/22, R2 10/10, R3 pass (precision 2/3, the other
  three 3/3), R4 pass, R5 6/6. Missed: F-333 (precision flagged at `low`, called valid). **Dependence:** both precision
  detections (F-150, F-352) rest only on `failed_transformation_identity`, the term added for precision items before the
  freeze (J15.1-025 (4)); under the v2 terms precision would be 0/3 and R3 would fail. Journal J15.1-029.
