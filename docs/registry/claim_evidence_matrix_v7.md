# Claim-Evidence Matrix v7

- Claims: 10 | with cited artifacts: 10 | with estimates: 8
- Bootstrap: seed 42, 10000 resamples, unit = canonical family
- All estimates are discovery-tier and not paper-eligible.

| Claim | Estimate | 95% CI | Families | Status |
|---|---|---|---|---|
| C01 Behavioural counterfactual sensitivity exists on solver-ce | 0.5 | [0.4213, 0.5857] | 140 | estimated_discovery |
| C02 Prompt-side hidden states predict later counterfactual sen | 0.7596 | [0.6752, 0.8384] | 135 | estimated_discovery |
| C03 The monitor signal survives correctness residualisation | 0.7376 | [0.6504, 0.8185] | 135 | estimated_discovery |
| C04 A generic correctness probe is a strong comparator | 0.7657 | [0.6744, 0.8485] | 135 | estimated_discovery |
| C05 An entropy proxy is a strong non-activation comparator | 0.727 | [0.6385, 0.8104] | 135 | estimated_discovery |
| C06 A black-box two-query check predicts sensitivity | 0.6684 | [0.5744, 0.7567] | 135 | estimated_discovery |
| C07 The monitoring signal replicates within a second model fam | 0.7025 | [0.6014, 0.7974] | 140 | estimated_discovery |
| C08 Localized components causally modulate sensitivity in Qwen | 1.8697 | [1.5603, 2.1975] | 20 | estimated_discovery |
| C09 Localized components causally modulate sensitivity in Llam | 1.7481 | [-3.4601, 6.6532] | 20 | estimated_not_distinguishable_from_zero |
| C10 Donor-on-renamed controls establish specificity against va | unsupported | unavailable | 0 | downgraded_unsupported |

## Allowed and prohibited wording

### C01

- Allowed: The model is counterfactually sensitive on a measured fraction of families.
- Prohibited: Do not describe this as shortcut reliance; it is Level-2 behaviour only.
- Panel: Qwen sweep over the original benchmark panel; expansion families are summarised separately.
- Next: Wave 1 dual human validation of all confirmatory families.

### C02

- Allowed: Prompt-side hidden states carry information about later sensitivity.
- Prohibited: Do not claim superiority over all baselines from this number alone.
- Panel: Family-held-out LOO panel from the mean-state probe sweep.
- Next: Wave 2 combined non-activation baseline and incremental-information comparison.

### C03

- Allowed: The signal does not collapse to generic correctness variation.
- Prohibited: Do not claim independence from correctness; shared variance remains.
- Panel: Same LOO panel as the primary monitor, after residualisation.
- Next: Wave 2 deconfounding against a combined correctness-plus-entropy model.

### C04

- Allowed: Correctness prediction is a strong non-activation comparator.
- Prohibited: Do not present this as the monitor's ceiling without a paired test.
- Panel: Same LOO panel as the primary monitor.
- Next: Wave 2 paired comparison with family-bootstrap intervals on the difference.

### C05

- Allowed: Uncertainty-related signal predicts sensitivity.
- Prohibited: Do not treat the monitor's margin over entropy as established.
- Panel: Same LOO panel as the primary monitor.
- Next: Wave 2 combined non-activation baseline.

### C06

- Allowed: A practical black-box comparator carries signal.
- Prohibited: Do not describe this as equivalent to activation access.
- Panel: Directional black-box score on the monitoring panel.
- Next: Wave 2 risk-coverage and calibration comparison.

### C07

- Allowed: A within-model monitor is trainable on a reasoning-distilled model.
- Prohibited: Do not claim cross-model transfer from this within-model number.
- Panel: DeepSeek variance-probe LOO panel.
- Next: Wave 3 model-specific causal panels.

### C08

- Allowed: The component contributes causally to sensitivity under intervention.
- Prohibited: Do not claim necessity, nor a complete circuit, from this panel.
- Panel: Qwen multi-head knockout panel; family-mean recovery across tested layers.
- Next: Wave 3 necessity and sufficiency with controlled damage checks.

### C09

- Allowed: A second architecture shows a localized causal contribution.
- Prohibited: Do not claim a shared mechanism across architectures.
- Panel: Llama multi-head knockout panel at layer 21. The family-bootstrap interval spans zero, so the point estimate is not a demonstrated effect: normalized recovery divides by a near-zero original S_lp on some families and is heavy-tailed on a 20-family panel.
- Next: Wave 3 cross-model causal comparison with small-denominator exclusion.

### C10

- Allowed: The donor-on-renamed controls produced zero evaluable rows. No scientific null or specificity claim can be made from those runs.
- Prohibited: Do not claim 100% specificity, 0.0 mean recovery, or completed renamed donor controls.
- Panel: Both controls produced zero evaluable rows; the panel was never measured.
- Next: Fix run_same_answer_donor.select_donors target lookup, then run both controls as NEW registered experiments.
