# Second Validator Instructions

This document is the handoff for the independent second validator for the 30-family
PhysMon pilot benchmark. It is written for a reviewer with undergraduate-level physics
training and does not assume any knowledge of the internal project machinery.

## Your Task

You will review 30 short physics problem families. Each family contains 4 variants of
the same core problem. In each family, one sentence changes across variants. Your job is
to judge whether that changing sentence is genuinely irrelevant to the target quantity
and whether the problem family is clear and scientifically sound.

Please complete the form in:

- `docs/validation/pilot_validation_form.md`

Do not discuss your answers with anyone else until both validators have completed their
forms independently.

## The Four Questions

For each family, answer these four questions:

1. `Q1` — Is the varying cue clearly irrelevant (Cue A) or clearly non-governing
   (Cue B) for the stated target quantity?
2. `Q2` — Do all 4 variants represent the same physics problem with the same correct
   answer?
3. `Q3` — Is the stated correct answer unambiguously correct under the governing law?
4. `Q4` — Is the wording clear and unambiguous to a competent undergraduate physics
   reader?

Use `Y` for yes and `N` for no. Add a short note whenever a family is borderline,
ambiguous, or fails any question.

## Worked PASS Example

Suggested reference family: `CM_A_001`.

Why it passes:

- The changing sentence only names the paint color of the particle.
- Paint color does not enter the constant-acceleration kinematics relation
  `v = v_0 + a t`.
- All variants preserve the same values of `v_0`, `a`, and `t`.
- The stated answer remains identical across variants.
- The wording is straightforward and does not create a competing physical interpretation.

This should be marked `Y` on Q1-Q4.

## Worked FAIL Example

Hypothetical example:

> Variant 1 says a block slides on a frictionless surface.
> Variant 2 changes the cue sentence to say the surface is rough and does not explicitly
> preserve the frictionless override.

Why that would fail:

- The changed sentence could alter whether friction belongs in the governing law.
- The correct answer might then differ across variants.
- A reviewer could no longer certify that the cue is irrelevant or non-governing.

This would likely be marked `N` on Q1 and `N` on Q2, with an explanatory note.

## Submission Instructions

Please return your completed form by email to:

- `shubham.mishra@research.local`

If you are unsure about a family, record your best judgment and explain the uncertainty
briefly in the notes column rather than leaving the item blank.
