# Wave 2 comparator: oracle, not deployable (note added 2026-11-12)

Added in Stage 15.0 (G0 item d; journal J15.0-004). The Wave 2 result files in this directory are
unchanged; this note qualifies how they are read. Tags for every Phase-I and Wave 2 comparator:
`docs/registry/v2/comparator_tags.yml`.

- The "combined non-activation" comparator (`combined_baseline/combined_baseline_summary.json`,
  AUROC **0.7048**), called the strongest non-activation combination in the Wave 2 decision-log
  entry of 2026-08-27, is an **oracle** comparator. `scripts/run_combined_baseline.py` takes two of
  its nine features (`entropy_proxy`, `mean_logprob_correct`) from
  `results/stage9/baselines/entropy/entropy_per_family_scores.json`, which
  `scripts/run_entropy_baseline.py` builds from `logprob_correct_answer`, the model's
  log-probability of the certified answer on the four renderings: the quantity the S_lp label is
  computed from. A third feature (`answer_log10_magnitude`) is the certified answer's magnitude.
  None of these is available at inference without the answer, so the comparator is not
  non-activation evidence available at deployment. The same holds for `combined_plus_hidden_state`
  (0.7719) and for the leaky stacked diagnostic (0.9301, already marked diagnostic only).
- The oracle-free entropy baseline is the token-entropy feature
  `token_entropy_topk_1000_std_across_4_variants`
  (`results/stage10/baselines/token_entropy/token_entropy_summary.json`): AUROC **0.520**
  (review check C4, `results/reviews/iclr2027_submission50608/attempt_20261111/claims_check.json`).
- Reading: the Wave 2 statement that every paired interval includes zero still describes the
  comparison that was run, but that comparison was against an oracle-like comparator. Against the
  oracle-free entropy baseline the stored monitor (0.7596) is 0.24 AUROC higher on the same panel
  (the reviewer's paired interval [0.115, 0.365] was not recomputed here). Neither number is
  paper-eligible: the monitor layer, threshold and panel were selected on these families, and the
  label itself is retired as a primary endpoint (Stage 14.2 interim rule; review checks C1-C3).
