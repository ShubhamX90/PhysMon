# PhysMon — Stage 6 Phase D2 Execution Brief

**Version:** 6.7  
**Date:** 2026-06-15  
**Status:** Benchmark freeze gate PASS; D2 behavioural sweep authorized.

## Purpose

This brief records the exact next execution step after the successful Stage 6
benchmark freeze. The goal is to run the repaired behavioural pipeline over the
frozen 140-family benchmark on Sharanga without introducing any new benchmark
drift or prompt-format regressions.

## Preconditions Already Satisfied

- `results/stage6/audit/stage6_freeze_gate_summary.json` reports `PASS`
- all `140/140` families are:
  - verifier-certified,
  - validated,
  - rendered,
  - parser-parseable,
  - free of manifest issues
- delegated Phase 2 B/C/E validation is recorded in:
  - `docs/validation/stage6_phase2_bce_agent_review.md`

## Execution Order

1. Assemble the frozen rendered benchmark directory:
   - `results/stage6/generated_full_benchmark/`
2. Dry-run the D2 workload structure locally (no model load).
3. `make sync-up`
4. On Sharanga, run `--print-first-prompt` once for Qwen and once for Llama to
   confirm chat-template formatting is still correct on the live tokenizer assets.
5. Submit:
   - `slurm/submitted/stage6_d2_behavioural_qwen.sh`
   - `slurm/submitted/stage6_d2_behavioural_llama.sh`
6. Record both Slurm job IDs in `docs/decisions/decision_log.md`.
7. After completion:
   - `make sync-down`
   - analyse the full D2 outputs
   - produce the Phase D2 sensitivity summary

## D2 Inputs

- frozen rendered families:
  - `data/generated/` (pilot)
  - `results/stage6/generated_phase1_full/`
  - `results/stage6/generated_phase2_ad/`
  - `results/stage6/generated_phase2_bce/`
- merged by:
  - `scripts/assemble_stage6_full_benchmark.py`

## D2 Outputs

- behavioural JSONL records:
  - `results/stage6/behavioural_full/`
- cluster logs:
  - `/scratch/pabitra/physmon/slurm_logs/stage6_d2_*`

## Guardrails

- Do not edit benchmark templates after assembly unless a new scientific issue is found.
- Do not overwrite Phase D1 outputs.
- Keep D2 outputs separate from earlier Stage 6 behavioural runs.
- If either Sharanga smoke-check shows missing chat-template markers, stop before
  job submission and repair the prompt path first.
