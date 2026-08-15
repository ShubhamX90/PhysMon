# Stage 10 Failure-Case Taxonomy

This note summarises the dominant error modes of the Stage 9.5 mean probe at
layer 18, using the highest-confidence false positives and false negatives from
`results/stage9/mean_probe_stage6/loo_predictions_resid_post_last_prompt.json`.

## Overview

The mean probe's strongest mistakes do not look random. They cluster into a few
repeated structural patterns:

1. Near-match-style geometry without behavioural manifestation.
2. Clean physics families whose answers are simple and reliable despite using a
   sensitive cue template.
3. Cue A numerical coincidence families that behave like weak shortcut cases but
   do not consistently cross the 0.5-nat threshold.
4. Families with very large true S_lp where the hidden-state signal seems to
   disperse across a different subspace than the mean probe captures.

## Category 1 — "Looks like a positive" false positives

These are families where the prompt structure resembles a sensitive family even
though the measured `S_lp` stays below threshold.

- `CM_B_UM_041` (`pred=0.998`, `S_lp=0.203`): momentum-to-velocity with a
  disconnected 6.0 m/s distractor. The surface form is almost identical to the
  high-sensitivity velocity/velocity families, so the probe treats it as a
  strong Cue B case even though Qwen remains behaviourally stable.
- `CM_B_UM_018` (`pred=0.966`, `S_lp=0.000`): Ohm's-law current family with an
  isolated branch-current distractor. This has the same local "answer unit ==
  distractor unit" pattern as the positive current families, but the model
  apparently rejects the distractor cleanly.
- `CM_B_STD_001` (`pred=0.848`, `S_lp=0.000`) and `CM_B_STD_004`
  (`pred=0.865`, `S_lp=0.297`): standard Cue B rotational/fluid prompts. Both
  instantiate the right distractor template, but the nuisance value is not
  numerically confusable enough to trigger a full positive.

Interpretation: the mean probe is sensitive to *template geometry* even when the
behavioural threshold is not crossed. These are "latent-positive" errors rather
than arbitrary misses.

## Category 2 — Stable negatives with the right shell

Several high-confidence false positives are families already known from the
benchmark analysis to have physically recognizable, behaviourally stable
distractors.

- `CM_B_UM_035` (pendulum with 0.5 Hz distractor) and `CM_B_UM_053`
  (spring-mass with 0.8 Hz distractor): both are frequency/frequency templates,
  but the distractors are still far enough away that the model resists them.
- `CM_B_007` and `CM_B_STD_008`: same cue type, same disconnected-system
  narrative, but little or no measured instability.

Interpretation: these cases reinforce the "near-match principle." The probe
sometimes assigns high sensitivity because the family belongs to a dangerous
template class, while the actual family stays negative because the distractor is
not close enough numerically.

## Category 3 — Weak positives the probe underestimates

These false negatives usually have real `S_lp > 0.5`, but the cue is either
small in magnitude or numerically subtle.

- `CM_B_UM_015` (`pred=0.125`, `S_lp=0.578`) and `CM_B_UM_027`
  (`pred=0.131`, `S_lp=0.719`): modest current/torque positives whose cue values
  are not especially close to the answer. They clear the binary threshold, but
  the mean representation does not look like an extreme-sensitive family.
- `CM_A_005` and `CM_A_STD_004`: Cue A positives driven by numerical
  coincidence. The cue is irrelevant by type, so the family-level mean signal is
  weaker than in Cue B even though the measured `S_lp` is above threshold.

Interpretation: the mean probe is strongest on robust Cue B structure and can
miss low-amplitude positives that are real but only mildly unstable.

## Category 4 — Strong positives with dispersed internal signatures

Some of the most interesting false negatives are genuine high-S_lp families.

- `CM_B_001` (`pred=0.203`, `S_lp=2.000`) and `CM_B_004`
  (`pred=0.213`, `S_lp=2.672`): classic pilot positives that clearly behave as
  sensitive families, but the mean probe assigns them low scores.
- `CM_B_UM_009` (`pred=0.309`, `S_lp=4.375`): an exact-match Cue B family where
  the behavioural effect is very strong, but the layer-18 mean feature still
  underestimates it.
- `CM_A_STD_019` (`pred=0.365`, `S_lp=3.156`): thermodynamics Cue A family with
  high sensitivity despite a very different physical mechanism from the typical
  mechanics Cue B families.

Interpretation: these errors suggest that a single layer-18 mean feature is not
  enough to capture every route to high sensitivity. They are consistent with
  the broader Stage 10 motivation for full layer sweeps, per-variant probes, and
  cue-specific analyses.

## Takeaway

The probe's errors mostly track *structured ambiguity* rather than generic
failure. False positives often sit in risky cue templates that stay just below
threshold, while false negatives are either weak positives or high-sensitivity
families whose internal signal appears to live in a different representation
than the layer-18 mean summary captures. This supports using the Stage 10 full
mean/per-variant sweeps and cue-specific analyses as the next refinement step,
rather than treating the current probe as exhausted.
