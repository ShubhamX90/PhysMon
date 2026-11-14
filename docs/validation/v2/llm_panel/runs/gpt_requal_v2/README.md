# GPT-6.1 Sol requalification run `gpt_requal_v2` (prompt v2, bank v4, protocol v2)

* `codex exec` on the cluster (`s182 run --model gpt-6.1-sol --reasoning-effort high --workers 3`), kit
  `/scratch/pabitra/physmon/judge_gpt/gpt_requal_kit` (prompt v2 sha256 082366df...). 64 calls, all complete, no rate limit.
* `events_audit.json`: `s184` over all 64 event streams: only thread/turn/agent-message events. All clean.
  `events/`: the raw event streams (as in gpt_q1).
* `reviews/`, `run_log.jsonl`, `summary.json`: copied unchanged.
* `score.json`: `s179 --split requal`. **NOT QUALIFIED**: R1 19/22 = 0.86 (pass); R2 8/10 (fail, needs 9); R3 fail
  (numerical precision 1 of 3); R4 pass. Item-level reading in journal J15.1-024.
