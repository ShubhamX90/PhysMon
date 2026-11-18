# Handoff · 2026-11-18 23:55 IST · Claude Opus 5.5 main session (user: Shubham Mishra)

Format and rules: `skills/physmon-journaling/SKILL.md`. Overwrite at every checkpoint.

## State in one paragraph
Stage 15. G1 passed and frozen (J15.1-040). The GPT judge (second qualified judge) rejected 8 of the 11 M0 v2.2 pilot
structures with mostly legitimate flags (unstated conditions; "earlier experiment" attachments that may persist; a D sentence
contradicting its scene; tense; one judge error on S72's numeral-free N), so the three G2 pilot runs were DEACTIVATED before any
record (J15.1-046) and M0 v2.3 is being built; two-judge admission is now required for M0 too. Rules 6-8 added to the five
wording rules (scratchpad `rules_6_8.md`; text in J15.1-046). M250: committed specs for 89 structures (M0 11, upgraded a 17,
b 17, c 17, d 7, new thermo 10, waves 10); new mech, em, modern, extra (S251-S262) in progress; integration builder (s198/s199)
in progress.

## Running now (Sonnet workers; agents never commit)
* M0 v2.3 (`roles_m0v23.py`, `s200_build_m0_v23.py`, `s201_m0v23_panel_packets.py`, `tests/v2/test_m0_v23.py`).
* New structures: mech S201-210, em S211-220, modern S241-250, extra S251-262 (`lib_m250_*`, `roles_m250n_*`, tests).
* Integration builder: `s198_build_m250_exploration.py`, `s199_m250_panel_packets.py`, `tests/v2/test_m250_exploration.py`.
* Slurm: nothing of ours (pilot workers 453721-6 ran 17-18 Nov and exited: runs deactivated; queue start takes < 1 day).

## Next steps, in order
1. Review and commit each worker result (re-run tests; read sentences against rules 1-8).
2. Retrofit rules 6-8 into the committed M250 spec modules (a, b, c, d, thermo, waves) before any M250 panel round.
3. M0 v2.3: build, packets, review by BOTH judges (Claude: fresh Opus instances per batch dir, `s180` audit; GPT: `s183` kit +
   `s182 run --reasoning-effort high --workers 3`, `s184` audit; score `s190b --min-judges 2`).
4. When M0 v2.3 is admitted: re-plan the G2 pilot runs on it (s170 plan, commit, register, submit workers), then the report (s197).
5. M250 build (s198), packets (s199), two-judge review in batches; then the 120 sealed structures.

## Open decisions
* None pending from the user. EPC/B5.3 public-benchmark feasibility pilot: recommended as a side track once M250 review runs;
  awaiting the user's go-ahead (asked 2026-11-16).

## Do not
* Modify files in `g1_frozen_files_sha256.json` without a dated amendment; `data/v2/dataset/*`, `data/v2/runs/*`, banks.
* Reactivate `s15_g2pilot_m0v22_*` (superseded).
* Edit files an active agent owns (listed above).

## Credentials and external state
* Codex/ChatGPT login: PRESENT in `/scratch/pabitra/physmon/codex_home` (mode 700); the user asked that it STAYS. Never copy
  `auth.json`. Codex needs `/scratch/pabitra/physmon/envs/node/bin` on PATH.

## Last journal entry and last commit
J15.1-046; commit 8e6bc1b.
