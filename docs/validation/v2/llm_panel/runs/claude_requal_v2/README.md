# Claude Opus 5.5 requalification run `claude_requal_v2` (prompt v2, bank v4, protocol v2)

* 8 fresh agent instances (batches in `assignment.json`), each given `judge_prompt_v2.md` verbatim plus its assignment;
  Read/Write only. Started and finished 2026-11-13.
* `transcript_audit.json`: `s180` over all 8 transcripts: 17 tool calls each, no access outside the batch directory, no
  forbidden text, every pass-1 review saved before the item's pass-2 packet was opened. All clean.
* `reviews/`: 64 reviews (32 items x 2 passes), copied unchanged from `/scratch/pabitra/physmon/judge/claude_requal_v2/batchNN/out/`.
* `score.json`: `s179 --bank docs/validation/v2/llm_panel/bank_v4 --split requal`. **NOT QUALIFIED**: R1 18/22 = 0.82
  (fail, needs 19); R2 9/10 (pass); R3 pass (missing assumption 2, boundary 3, contradiction 3, precision 3); R4 pass.
  Item-level reading in journal J15.1-024.
