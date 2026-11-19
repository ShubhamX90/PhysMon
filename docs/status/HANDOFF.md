# Handoff · 2026-11-20 03:00 IST · Claude Opus 5.5 main session (user: Shubham Mishra)

Format and rules: `skills/physmon-journaling/SKILL.md`. Overwrite at every checkpoint.

## State in one paragraph
Stage 15. G1 passed and frozen (J15.1-040; amendment A1 = check 5.3b). M0 final = `data/v2/dataset/m0_v25` (all 11 structures
two-judge ADMITTED and natural; J15.1-053). G2 pilot on M0 v2.5 registered (J15.1-055); its four workers are PENDING (all GPU
nodes fully allocated). M250: 151 structures machine-admitted, 0 rejected, in a first build of `m250_explore_v1`; that build was
discarded uncommitted because 9 structures had ungrammatical N fills ("by a further a few kelvin"), fixed in 4e8de96 with a
cross-module fill-grammar test (`tests/v2/test_m250_n_fill_grammar.py`); a rebuild from a clean worktree at 4e8de96 is running.

## Running now
* M250 rebuild: worktree `/scratch/pabitra/physmon/worktrees/m250_build_4e8de96`, log `/scratch/pabitra/physmon/worktrees/m250_build.log`,
  output `data/v2/dataset/m250_explore_v1/` (uncommitted until checked; builder refuses to overwrite).
* Slurm: G2 pilot workers 460225, 460226 (gpu_h100_4), 460227, 460228 (gpu_a100_8), PENDING (Priority).

## Next steps, in order
1. Check the rebuild (README admitted/REJECTED, composition, prompt-text scan), commit with journal J15.1-056, remove the worktree.
2. `s199` packets -> two-judge M250 review: Claude (fresh Opus per batch; admission batches of 4, naturalness up to 24; `s180`
   audit) + GPT (`s183` kit, run-script pattern `/scratch/pabitra/physmon/judge/gpt_kits/run_m0v25.sh`, `s184` audit); score
   `s190b --min-judges 2 --guard-53b`; repair rounds for rejected/artificial items.
3. G2 pilot: when workers finish, collect and run `s197` report + audit sample per the pilot plan.
4. 120 sealed INTERNAL_CONFIRMATION structures; G0 parity amendment diagnosis before G5.

## Open decisions
* EPC/B5.3 public-benchmark feasibility pilot: awaiting the user's go-ahead (asked 2026-11-16).
* M250 S08 ("energy in the two capacitors together" with a third capacitor in parallel) left for the panel.

## Do not
* Modify files in `g1_frozen_files_sha256.json` without a dated amendment; committed `data/v2/dataset/*`, `data/v2/runs/*`, banks.
* Reactivate `s15_g2pilot_m0v22_*` (superseded).
* Use `pkill -f`/`pgrep -f` waiters whose pattern appears in their own command line (they match themselves).

## Credentials and external state
* Codex/ChatGPT login: PRESENT in `/scratch/pabitra/physmon/codex_home` (mode 700); the user asked that it STAYS. Never copy
  `auth.json`. Codex needs `/scratch/pabitra/physmon/envs/node/bin` on PATH.

## Last journal entry and last commit
J15.1-055; commit 4e8de96.
