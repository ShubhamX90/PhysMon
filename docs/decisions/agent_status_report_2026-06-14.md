# PhysMon Agent Status Report
**Date/Time:** 2026-06-14
**Session summary:** Completed the Stage 4 v4.1 parser repair, executed the Stage 5 pre-registration transition, and launched the first Qwen activation-extraction job under the revised `S_lp`-primary framing.

## Completed This Session
- [x] Fixed the Stage 4 parser bugs in
  [src/physmon/benchmark/parser.py](/Users/shubhammishra/Desktop/PhysMons/src/physmon/benchmark/parser.py):
  - LaTeX-wrapped numeric answers now normalize before canonical comparison.
  - Digit-free garbage extracts such as `themagnitude` are rejected.
  - Parsed answers now distinguish display/log form from canonical comparison form.
- [x] Updated
  [scripts/run_behavioural.py](/Users/shubhammishra/Desktop/PhysMons/scripts/run_behavioural.py)
  so future behavioural JSONL records carry both `parsed_answer` and
  `parsed_answer_canonical`, while correctness remains explicitly post-analysis.
- [x] Added v4.1 parser regression tests in
  [tests/test_parser.py](/Users/shubhammishra/Desktop/PhysMons/tests/test_parser.py)
  covering:
  - LaTeX numeric wrapper normalization
  - rejection of digit-free garbage
  - LaTeX text/unit normalization with `\cdot`
- [x] Added a `--reparse` mode and clean-label logic to
  [scripts/analyse_stage4.py](/Users/shubhammishra/Desktop/PhysMons/scripts/analyse_stage4.py):
  - reparses `generated_text` directly
  - recomputes clean `hat_S`
  - preserves `S_lp`
  - flags `EL_A_004` Llama as `degraded_calculation_error`
  - flags `EL_A_005` Llama as `suspect_single_variant_anomaly`
  - verifies `S_lp` stability against the prior repair analysis
- [x] Extended
  [scripts/run_baselines_surface.py](/Users/shubhammishra/Desktop/PhysMons/scripts/run_baselines_surface.py)
  with:
  - graceful skipping when class support is too small
  - `surface_tfidf_continuous.json` for TF-IDF regression against continuous `S_lp`
- [x] Re-ran Stage 4 analysis in reparsing mode with no new GPU jobs:
  - [results/stage4_repair/analysis_v2/stage4_sensitivity_summary.json](/Users/shubhammishra/Desktop/PhysMons/results/stage4_repair/analysis_v2/stage4_sensitivity_summary.json)
  - [results/stage4_repair/analysis_v2/stage4_per_family.csv](/Users/shubhammishra/Desktop/PhysMons/results/stage4_repair/analysis_v2/stage4_per_family.csv)
  - [results/stage4_repair/analysis_v2/stage4_sensitivity_hist.png](/Users/shubhammishra/Desktop/PhysMons/results/stage4_repair/analysis_v2/stage4_sensitivity_hist.png)
- [x] Re-ran surface baselines on the clean v2 labels:
  - [results/stage5/baselines_repair_v2/surface_tfidf_logistic.json](/Users/shubhammishra/Desktop/PhysMons/results/stage5/baselines_repair_v2/surface_tfidf_logistic.json)
  - [results/stage5/baselines_repair_v2/surface_tfidf_continuous.json](/Users/shubhammishra/Desktop/PhysMons/results/stage5/baselines_repair_v2/surface_tfidf_continuous.json)
- [x] Revalidated the repo:
  - `ruff check src scripts tests` PASS
  - `pytest tests -q` PASS (`86 passed`)
- [x] Recorded the v4.1 clean-analysis outcome in
  [docs/decisions/decision_log.md](/Users/shubhammishra/Desktop/PhysMons/docs/decisions/decision_log.md)
- [x] Executed the Stage 5 pre-registration transition:
  - updated [docs/construct_spec.md](/Users/shubhammishra/Desktop/PhysMons/docs/construct_spec.md)
    with the PI-approved `Qwen S_lp_theta` measure and `0.5` nat threshold
  - updated
    [docs/decisions/decision_log.md](/Users/shubhammishra/Desktop/PhysMons/docs/decisions/decision_log.md)
    with the H1 reframing, revised Stage 4 gate, and Stage 5 kickoff
  - created the required commit: `5a72370`
- [x] Added the pre-registered Stage 5 label constants and helpers in
  [src/physmon/formal/constructs.py](/Users/shubhammishra/Desktop/PhysMons/src/physmon/formal/constructs.py)
  and covered them in
  [tests/test_constructs.py](/Users/shubhammishra/Desktop/PhysMons/tests/test_constructs.py)
- [x] Extended
  [scripts/run_baselines_surface.py](/Users/shubhammishra/Desktop/PhysMons/scripts/run_baselines_surface.py)
  to support `--target-measure slp_binary`, then generated the Stage 5 binary-`S_lp`
  surface baseline outputs in
  [results/stage5/baselines_repair_v2/](/Users/shubhammishra/Desktop/PhysMons/results/stage5/baselines_repair_v2)
- [x] Added cue-token indexing support in
  [src/physmon/models/hooks.py](/Users/shubhammishra/Desktop/PhysMons/src/physmon/models/hooks.py)
  and tested it in
  [tests/test_hooks.py](/Users/shubhammishra/Desktop/PhysMons/tests/test_hooks.py)
- [x] Created the Stage 5 extraction and probing entrypoints:
  - [scripts/extract_activations.py](/Users/shubhammishra/Desktop/PhysMons/scripts/extract_activations.py)
  - [scripts/run_probing.py](/Users/shubhammishra/Desktop/PhysMons/scripts/run_probing.py)
- [x] Created Stage 5 extraction Slurm scripts:
  - [slurm/submitted/stage5_extract_qwen.sh](/Users/shubhammishra/Desktop/PhysMons/slurm/submitted/stage5_extract_qwen.sh)
  - [slurm/submitted/stage5_extract_llama.sh](/Users/shubhammishra/Desktop/PhysMons/slurm/submitted/stage5_extract_llama.sh)
- [x] Synced the Stage 5 working tree to Sharanga and submitted the Qwen extraction job:
  - Qwen dry run PASS (`30 families`, `120 files`, `~22.97 MB`)
  - Slurm job id: `242554`

## In Progress
- [ ] Qwen Tier 1 activation extraction on Sharanga (`242554`) — waiting for
  manifest completion and file-count verification.
- [ ] Llama Tier 1 activation extraction — ready to submit once Qwen completes cleanly.
- [ ] Stage 5 probing execution — scaffold is implemented and locally validated, but
  awaits extracted activation tensors.

## Blocked / Flagged
- BLOCKED: Probe training cannot start until the activation manifests are present locally.
- FLAGGED: Llama extraction is intentionally deferred until Qwen extraction is verified.
- FLAGGED: The study is now running under the PI-approved `S_lp`-primary framing;
  clean `hat_S` remains a secondary measure only.

## Decisions Required from PI
- None for the current execution step. The threshold and framing decisions are now
  resolved and pre-registered.

## Assumption Checks Completed
- [A1] Sharanga access: CONFIRMED
- [A2] Behavioural measurement path after repair: CONFIRMED
- [A4] Symbolic invariance tractability for the pilot: still CONFIRMED
- [A9] Stage 4 runability: CONFIRMED; the remaining issue was resolved via the
  PI-approved `S_lp` reframing and pre-registration

## Files Modified / Created This Session
- [src/physmon/benchmark/parser.py](/Users/shubhammishra/Desktop/PhysMons/src/physmon/benchmark/parser.py)
- [scripts/run_behavioural.py](/Users/shubhammishra/Desktop/PhysMons/scripts/run_behavioural.py)
- [scripts/analyse_stage4.py](/Users/shubhammishra/Desktop/PhysMons/scripts/analyse_stage4.py)
- [scripts/run_baselines_surface.py](/Users/shubhammishra/Desktop/PhysMons/scripts/run_baselines_surface.py)
- [tests/test_parser.py](/Users/shubhammishra/Desktop/PhysMons/tests/test_parser.py)
- [tests/test_constructs.py](/Users/shubhammishra/Desktop/PhysMons/tests/test_constructs.py)
- [tests/test_hooks.py](/Users/shubhammishra/Desktop/PhysMons/tests/test_hooks.py)
- [docs/decisions/decision_log.md](/Users/shubhammishra/Desktop/PhysMons/docs/decisions/decision_log.md)
- [docs/construct_spec.md](/Users/shubhammishra/Desktop/PhysMons/docs/construct_spec.md)
- [src/physmon/formal/constructs.py](/Users/shubhammishra/Desktop/PhysMons/src/physmon/formal/constructs.py)
- [src/physmon/models/hooks.py](/Users/shubhammishra/Desktop/PhysMons/src/physmon/models/hooks.py)
- [scripts/extract_activations.py](/Users/shubhammishra/Desktop/PhysMons/scripts/extract_activations.py)
- [scripts/run_probing.py](/Users/shubhammishra/Desktop/PhysMons/scripts/run_probing.py)
- [results/stage4_repair/analysis_v2/](/Users/shubhammishra/Desktop/PhysMons/results/stage4_repair/analysis_v2)
- [results/stage5/baselines_repair_v2/](/Users/shubhammishra/Desktop/PhysMons/results/stage5/baselines_repair_v2)

## Next Actions (in order)
1. Confirm Qwen extraction job `242554` completes with a valid manifest and `120` Tier 1 files.
2. Submit the Llama Tier 1 extraction job on A100.
3. Sync activation artifacts down and run the Stage 5 probing pipeline locally.
