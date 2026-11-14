# Claude Opus 5.5 requalification run `claude_requal_v3` (prompt v3, bank v5, protocol v3)

* 8 fresh agent instances, `judge_prompt_v3.md` verbatim (sha256 55585308...) plus the assignment (`assignment.json`);
  Read/Write only. 2026-11-14.
* `transcript_audit.json`: `s180`, all 8 clean (17 tool calls each, nothing outside the batch directory, every pass 1
  saved before pass 2 was opened).
* `reviews/`: 64 reviews, copied unchanged from `/scratch/pabitra/physmon/judge/claude_requal_v3/batchNN/out/`.
* `score.json`: `s179 --bank docs/validation/v2/llm_panel/bank_v5 --split requal --protocol v3`. **QUALIFIED**: R1 22/22,
  R2 10/10, R3 3/3 for each of the four retargeted types, R4 pass, R5 6/6. One detection (F-352) rests only on the
  precision term added before the freeze; without it R1 21/22 and precision 2/3, still QUALIFIED. Journal J15.1-029.
