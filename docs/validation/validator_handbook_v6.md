# Validator Handbook v6

Validators work in two independent passes. Pass 1 is blinded: solve all variants, identify the governing law, relevant variables, candidate non-governing variables, assumption sufficiency, answer uniqueness, answer invariance, semantic equivalence, unintended co-variation, wording naturalness, difficulty shift, verdict, confidence, and repair recommendation. Pass 2 is certificate review: inspect the solver derivation, canonical answer, unit/frame equivalence, invariance checks, limitations, and overall certificate validity.

Governing variables are variables that enter the physical law or boundary conditions required for the target quantity. Non-governing variables may be irrelevant, redundant, or correlated; only truly irrelevant variables can vary without changing the answer. A cue is valid only when all variants preserve the same target, assumptions, relevant variables, and canonical answer.

Frame and unit equivalence require numerical conversion, not visual similarity. Unit-compatible distractors are not automatically irrelevant. Borderline cases should be repaired or excluded before confirmatory use. Adjudication requires two independent annotations followed by a locked disagreement review. Repaired families must be revalidated.

Use `docs/validation/calibration_bank_v6.md` before annotation. The calibration bank contains valid, invalid, subtle, frame/unit, dimensional, semantic-drift, and solver-error examples with worked explanations.
