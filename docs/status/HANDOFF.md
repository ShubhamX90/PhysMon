# Handoff · 2026-11-23 IST · Claude Opus 5.5 main session (user: Shubham Mishra)

Format and rules: `skills/physmon-journaling/SKILL.md`. Overwrite at every checkpoint.

## State in one paragraph
Stage 15. G1 frozen (amendments A1 = check 5.3b, A2 = grader v2). M0 final = `data/v2/dataset/m0_v25` (11 structures). M250
exploration set after three repair rounds: `data/v2/dataset/m250_explore_v4` (146 machine-admitted, 5,232 cells). Two-judge panel
(Claude Opus + GPT-6.1 Sol, all audits clean), latest verdict per structure across `docs/validation/v2/llm_panel/admission_m250`
(`score_two_judges_guard_r`), `admission_m250r1`, `admission_m250r2`, `admission_m250r3` (`score_two_judges`): **143 ready
(M0 11 + 132 admitted and natural), 5,122 cells**; not ready: S233, S270 (admitted, artificial sentences), S281 (GPT arithmetic-error
reject; certified gold verified 5.48839 km/s; held for human adjudication). Dropped across rounds: S08, S237, S269, S280, S282.
Journal J15.1-064.

## Running now
Nothing.

## Next steps, in order
1. Write ~107 new structures toward 250 (new `roles_m250n2_*` modules; keep C/K shares, domain balance; K share is 0.19 vs 0.30
   target). Sonnet workers, at most 3 at a time (`/scratch/pabitra/physmon/repair_m250_r*/WORKER_INSTRUCTIONS.md` has the rules).
2. Two-judge review of the new structures (s199 packets, Claude fresh Opus batches <=3 concurrent, GPT kit via systemd + retry timer).
3. 120 sealed INTERNAL_CONFIRMATION structures (decide R-arithmetic parity first); G2 step 3 calibration on M250.

## Open decisions
* EPC/B5.3 public-benchmark feasibility pilot: awaiting the user's go-ahead (asked 2026-11-16).
* Generator-side R-arithmetic parity for the sealed set (pilot review section 4c).
* S281: human adjudication of GPT's arithmetic-error reject.

## Do not
* Modify files in `g1_frozen_files_sha256.json` without a dated amendment; committed `data/v2/dataset/*` (incl. m250_explore_v1..v4),
  `data/v2/runs/*`, banks; earlier-round spec modules `roles_m250_*`, `roles_m250n_*`, `roles_m250r{1,2,3}*` (new rounds override).
* Reactivate `s15_g2pilot_m0v22_*` (superseded).
* Run more than 3 subagents at once (5-hour usage limit).
* Use `pkill -f`/`pgrep -f` waiters whose pattern appears in their own command line; run long local jobs with `systemd-run --user`.

## Credentials and external state
* Codex/ChatGPT login: PRESENT in `/scratch/pabitra/physmon/codex_home` (mode 700); the user asked that it STAYS. Never copy
  `auth.json`. Codex needs `/scratch/pabitra/physmon/envs/node/bin` on PATH.

## Last journal entry and last commit
J15.1-064; see `git log -1`.
