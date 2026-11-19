# Handoff · 2026-11-19 20:10 IST · Claude Opus 5.5 main session (user: Shubham Mishra)

Format and rules: `skills/physmon-journaling/SKILL.md`. Overwrite at every checkpoint.

## State in one paragraph
Stage 15. G1 passed and frozen (J15.1-040; amendment A1 = check 5.3b). M0: all 11 structures are two-judge ADMITTED
(v2.3 seven unchanged + v2.4 S26, S55, S72, S92; J15.1-048, -051); two N sentences (S26 N0, S55 N1) were rated artificial and
are being rewritten as M0 v2.5 (re-rate + re-admit both judges), after which the G2 pilot runs are re-planned on M0 v2.5.
M250: spec modules committed for M0 11 + upgraded a 17, b 17, c 17, d 7 + new thermo, waves, mech, em, modern 10 each, extra 12
(131 EXPLORATION candidates before machine checks); rules 6-8 retrofitted into a, b, c, d, thermo, waves (J15.1-050, -052).

## Running now (Sonnet workers; agents never commit)
* M0 v2.5 (`roles_m0v25.py`, `s204_build_m0_v25.py`, `s205_m0v25_panel_packets.py`, `tests/v2/test_m0_v25.py`).
* Integration builder: `s198_build_m250_exploration.py`, `s199_m250_panel_packets.py`, `tests/v2/test_m250_exploration.py`.
* Slurm: nothing of ours.

## Next steps, in order
1. M0 v2.5: build, packets, Claude (fresh Opus per batch, `s180` audit) + GPT (`s183` kit, run script pattern
   `/scratch/pabitra/physmon/judge/gpt_kits/run_m0v24.sh`, `s184` audit), score `s190b --min-judges 2 --guard-53b`.
2. G2 pilot on M0 v2.5: s170 plan (k=24), commit specs, s173 register + submit workers, collect, s197 report.
3. M250: accept integration builder, build `m250_explore_v1`, packets (s199), two-judge review in batches.
4. 120 sealed INTERNAL_CONFIRMATION structures; G0 parity amendment diagnosis before G5.

## Open decisions
* EPC/B5.3 public-benchmark feasibility pilot: awaiting the user's go-ahead (asked 2026-11-16).
* M250 S08 ("energy in the two capacitors together" with a third capacitor in parallel) left for the panel.

## Do not
* Modify files in `g1_frozen_files_sha256.json` without a dated amendment; `data/v2/dataset/*`, `data/v2/runs/*`, banks.
* Reactivate `s15_g2pilot_m0v22_*` (superseded).

## Credentials and external state
* Codex/ChatGPT login: PRESENT in `/scratch/pabitra/physmon/codex_home` (mode 700); the user asked that it STAYS. Never copy
  `auth.json`. Codex needs `/scratch/pabitra/physmon/envs/node/bin` on PATH.

## Last journal entry and last commit
J15.1-052; commit a0cdaf6.
