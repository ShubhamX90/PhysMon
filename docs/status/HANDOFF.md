# Handoff · 2026-11-21 IST · Claude Opus 5.5 main session (user: Shubham Mishra)

Format and rules: `skills/physmon-journaling/SKILL.md`. Overwrite at every checkpoint.

## State in one paragraph
Stage 15. G1 frozen (amendments A1 = check 5.3b, A2 = grader v2). M0 final = `data/v2/dataset/m0_v25` (11 structures, two-judge
ADMITTED). G2 pilot on M0 v2.5 done and reviewed (J15.1-057, `docs/registry/v2/g2/design_validation_pilot_review_m0v25.md`).
M250 exploration set `data/v2/dataset/m250_explore_v1` (151 structures, 5,586 cells) committed; two-judge review of its 140 non-M0
structures done (Claude + GPT-6.1 Sol, audits clean): **ADMIT 50, REJECT 90**; 82 structures carry 180 sentences rated artificial
(J15.1-058, `docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). Repair round 1 running.

## Running now
* Repair round 1: 12 Sonnet workers, one per spec module, each editing only `src/physmon/benchmark/v2/roles_m250r1*.py`
  (skeletons re-export the v1 modules; repaired specs go in `FIXED`, unrepairable in `DROPPED`). Instructions and briefs:
  `/scratch/pabitra/physmon/repair_m250_r1/{WORKER_INSTRUCTIONS.md,briefs/}` (briefs from `scripts/v2/s207_m250_repair_briefs.py`).
  116 structures to change (90 rejected + 26 admitted with artificial sentences).
* Builder: `s198 --round r1` builds from the r1 modules into `m250_explore_v2`; `--only` builds a subset into scratch (check builds).
  Verified: unchanged r1 build reproduces v1 cells exactly (only `dataset`, `m0_version`, `m250_source_module` differ).

## Next steps, in order
1. Review every worker's changes (read the diffs; spot-check the rendered sentences); fix or reject.
2. Full build `s198 --round r1` (systemd-run --user) -> `data/v2/dataset/m250_explore_v2`; check, commit (J15.1-059).
3. Packets for the CHANGED structures only (`s199`), two-judge re-review (Claude fresh Opus per batch + GPT kit), audits, score with
   `s190b --min-judges 2 --guard-53b`; unchanged ADMIT+natural structures keep their round-0 verdicts.
4. 120 sealed INTERNAL_CONFIRMATION structures (decide R-arithmetic parity first); G2 step 3 calibration on M250.

## Open decisions
* EPC/B5.3 public-benchmark feasibility pilot: awaiting the user's go-ahead (asked 2026-11-16).
* Generator-side R-arithmetic parity for the sealed set (pilot review section 4c).

## Do not
* Modify files in `g1_frozen_files_sha256.json` without a dated amendment; committed `data/v2/dataset/*` (incl. m250_explore_v1),
  `data/v2/runs/*`, banks; the v1 spec modules `roles_m250_*` / `roles_m250n_*` (the r1 modules override them).
* Reactivate `s15_g2pilot_m0v22_*` (superseded).
* Use `pkill -f`/`pgrep -f` waiters whose pattern appears in their own command line; run long local jobs with `systemd-run --user`.

## Credentials and external state
* Codex/ChatGPT login: PRESENT in `/scratch/pabitra/physmon/codex_home` (mode 700); the user asked that it STAYS. Never copy
  `auth.json`. Codex needs `/scratch/pabitra/physmon/envs/node/bin` on PATH.

## Last journal entry and last commit
J15.1-058; commit 4e1709f.
