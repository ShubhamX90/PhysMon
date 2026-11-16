# Handoff · 2026-11-16 14:00 IST · Claude Opus 5.5 main session (user: Shubham Mishra)

Format and rules: `skills/physmon-journaling/SKILL.md`. Overwrite at every checkpoint.

## State in one paragraph
Stage 15. G1 (physics construct) is being frozen: record `docs/registry/v2/g1/freeze/G1_FREEZE_RECORD.md` with 50 file hashes at
commit 20f9752 (`g1_frozen_files_sha256.json`); the full test suite is the last gate check (J15.1-040). M0 v2.2
(`data/v2/dataset/m0_v22/`, 11 structures, 411 cells) is fully ADMITTED by the qualified Claude judge with no sentence rated
artificial (J15.1-038/039; S02 rejected and replaced). Next: G2 design-validation pilot on M0 v2.2 (k = 24, vLLM, Qwen2.5-7B,
Llama-3.1-8B, Qwen3-8B thinking off), then M250.

## Running now
* Full test suite for the G1 gate (background, log in the session scratchpad `g1_full_tests.log`).
* M250 workers (Sonnet), all stopped on the Sonnet 5-hour limit, resume after 17:10 IST by SendMessage to the same agents:
  upgrade batches b (S24-S45, `roles_m250_b.py`) and d (S73-S95, `roles_m250_d.py`); new structures mech (S201-210), em
  (S211-220), thermo (S221-230), waves (S231-240), modern (S241-250) (`lib_m250_<domain>.py`, `roles_m250n_<domain>.py`,
  `tests/v2/test_m250n_<domain>.py`). Partial files are untracked and lint-clean. Tell them the pair-1 R wording rule (J15.1-038).
* Slurm: none of ours. 449313 (G0 extended parity) FAILED: Llama `resid_pre` from layer 8 (J15.1-039); gates mechanism work only.

## Next steps, in order
1. Gate check passes -> commit the freeze record and journal J15.1-040.
2. Plan and register the three G2 pilot runs (`s170_sampled_run.py plan --cells data/v2/dataset/m0_v22/cells.jsonl --n-samples 24`,
   run ids `s15_g2pilot_m0v22_*`), commit specs, submit workers (`s173_submit_workqueue.py`).
3. Collect the sealed October-wording M0 pilot as a pipeline check only (allowed after the freeze).
4. Review and commit M250 worker outputs; integration builder; panel review of M250 EXPLORATION (130).
5. GPT panel review when the user logs in to Codex (`CODEX_HOME=/scratch/pabitra/physmon/codex_home codex login --device-auth`; log out and delete afterwards).
6. Diagnose 449313 (TransformerLens residual mismatch on Llama).

## Open decisions
* None pending from the user.

## Do not
* Modify `data/v2/dataset/{m0_pilot,v1,m0_v2,m0_v21,m0_v22,nonphysics_v1}/`, `data/v2/runs/*`, banks v3-v5, frozen prompts or
  any file in `g1_frozen_files_sha256.json` without a dated amendment.
* Edit files an active agent owns (listed above).

## Credentials and external state
* Codex/ChatGPT login: none present (removed 2026-11-14).

## Last journal entry and last commit
J15.1-039 in `docs/journal/stage15/15.1_runner_and_batch1.md`; commit 20f9752.
