# History of the 0.5-nat S_lp threshold (dated note, 2026-11-12)

G0 item (g) of the plan of record (`docs/proposals/PhysMon_Research_v2.tex`, "G0. Integrity closure";
`docs/reviews/iclr2027_submission50608/analysis.md` section 5 point 2(g), issue 16). Written in Stage
15.0 (journal J15.0-006). It records what happened; it does not change any label. The legacy S_lp label
is already retired as a primary endpoint (Stage 14.2 interim rule, confirmed by the user 2026-10-17).
Labels: [V] read in the cited file in this shift; [I] inference.

## Timeline

| Date (IST) | Event | Source |
|---|---|---|
| 2026-06-14 | Policy D2 fixed before any Stage 4 output: the PRIMARY binary target is the answer-flip measure `hat{S}`; `S^lp` is a "saved tertiary cross-check"; the threshold is to be set "only after the Stage 4 pilot behavioural sweep, using training families alone and targeting roughly a 30-40% positive-class rate", and pre-registered in a Stage 5 commit [V] | `docs/decisions/decision_log.md`, entry "2026-06-14 - [PI CONFIRMED 2026-06-14] D2 Sensitivity Threshold Policy" |
| 2026-06-14, about 15:27 | Stage 4 repair run on the 30 pilot families (records `llama_primary_20260614T095723Z.jsonl`, commit 953c31e) [V] | `results/stage4_repair/behavioural/` |
| 2026-06-14, 19:36 | Parser repair v4.1 and clean re-analysis: the `hat{S}` gate FAILS (1 of 30 families flips; 6 needed); Qwen S_lp threshold candidates computed on the training split (21 families): 0.78125 for about 20% positives, **0.5 for about 30% (observed 6 of 21 = 0.286)**, 0.4375 for about 40% [V] | `results/stage4_repair/analysis_v2/stage4_sensitivity_summary.json` (`slp_threshold_candidates`, analysis events timestamped 14:06 UTC); decision-log entry "2026-06-14 - Stage 4 Parser Repair v4.1 and Clean Re-analysis" |
| 2026-06-14, 19:56 | "[PI CONFIRMED] H1 Reframing + S_lp Threshold Pre-Registration [D2]": after the `hat{S}` gate failed, the hypothesis is reframed to S_lp-primary and the threshold registered as **0.5 nats**, "round value with natural gap above (0.563) and below (0.469); 30% is centre of the 20-40% target range"; 9 of 30 pilot families positive; commit `5a7237018b25ebfa455371a3ff17107f326d2d0c` [V] | decision log, same-titled entry; `git log 5a72370` |
| 2026-06-16 | Stage 6 panel run (commit ffeeeff) under a different answer instruction (one-line "Answer: [value] [unit]" system prompt); the same 0.5 threshold labels 70 of 140 Qwen families positive [V] | `results/stage6/analysis_d2/stage6_d1_per_family.csv`; decision log "Stage 6 D2 Behavioural Sweep — Gate PASS (2026-06-16)" |
| 2026-09 (paper) | The withdrawn paper calls 0.5 nats "pre-registered" and states it "was registered on 2026-06-14, before any probe was trained, from a 30-family pilot split" [V] | `docs/reviews/iclr2027_submission50608/paper_extracted_text.txt` lines 97, 238, 264 |
| 2026-11-11 | Review check C2b: on the 30 pilot families the S_lp values of the threshold-registration run and of the panel run have Spearman 0.043 and the labels agree on 17 of 30 [V] | `results/reviews/iclr2027_submission50608/attempt_20261111/claims_check.json` |
| 2026-11-12 | G0 (a) extends C2b to both models: Qwen 0.043 / 17 of 30 (chance agreement 0.54); Llama Spearman 0.447 / 27 of 30 (chance agreement 0.85, only 2 and 3 positives); the same-instruction control (phase-D1 run vs panel run, 40 families) gives Spearman 1.0 and 40 of 40 for both models [V] | `results/g0/attempt_20261112/g0a_label_stability.{json,md}` |

## What this means [I]

1. **The threshold was chosen after the Stage 4 results, not before them.** "Registered before any probe
   was trained" is accurate, but the value was picked from candidates computed on the Stage 4 labels
   themselves, on the same day, after the pre-declared primary target (`hat{S}`) had failed its gate and
   the tertiary measure (S_lp) had been promoted. The registration fixed the threshold for later stages;
   it is not a pre-registration of the construct.
2. **Its basis is internally inconsistent.** The candidate at 0.5 gave 6 of 21 training families
   (0.286); the registration text cites 9 of 30 (all pilot families) as the positive-class rate, while
   naming the training split as its basis.
3. **It does not transfer across the answer instruction.** The labels it produces on the 30 pilot
   families under the Stage 4 prompting agree with the labels under the Stage 6 one-line instruction at
   about the chance rate for Qwen (17 of 30 against 16.2 expected from the positive rates; Spearman 0.04),
   while the same instruction reproduces exactly. For Llama the labels are almost all negative in both
   runs, so agreement (27 of 30) mostly reflects the low base rate; the rank correlation is 0.45.
4. **Wording rule from now on.** Do not call the 0.5-nat threshold or any S_lp label "pre-registered" or
   "registered before the results". Say: "a threshold chosen on 2026-06-14 from Stage 4 pilot results,
   before any probe was trained". Plan of record: no new metric is called preregistered unless it was
   frozen before the data it is applied to were seen.

## Sources

- `docs/decisions/decision_log.md`: "D2 Sensitivity Threshold Policy", "Stage 4 Parser Repair v4.1 and Clean
  Re-analysis", "[PI CONFIRMED] H1 Reframing + S_lp Threshold Pre-Registration [D2]", "Stage 4 Decision Gate
  (Revised - v2 clean analysis)".
- Commit `5a72370` ("[PRE-REGISTRATION] Qwen S_lp threshold 0.5 nats, H1 reframing to S_lp-primary").
- `results/stage4_repair/analysis_v2/stage4_sensitivity_summary.json`, `stage4_per_family.csv`.
- Review analysis: `docs/reviews/iclr2027_submission50608/analysis.md` (section 3, C2b; section 4, issue 16).
- `results/g0/attempt_20261112/g0a_label_stability.md` (G0 item a).
