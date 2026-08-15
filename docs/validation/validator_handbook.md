# PhysMon Stage 13 Validator Handbook

This handbook is for independent human validation. Validators should judge the
physics family, cue irrelevance, and answer certificate without using model
outputs or probe predictions.

## Pass 1: Blinded Prompt Review

For each packet:

1. Read the prompt text.
2. Decide whether the physics setup is valid.
3. Decide whether the cue is irrelevant to the requested answer.
4. Record uncertainty instead of guessing.

Do not infer missing solver information. Do not use model behavior as evidence.

## Pass 2: Certificate Review

After Pass 1 is complete, compare the provided correct answer/certificate against
the prompt. Mark disagreements directly. If the certificate is insufficient to
judge the problem, mark `uncertain`.

## Labels

- `yes`: supported by the prompt/certificate.
- `no`: contradicted by the prompt/certificate.
- `uncertain`: insufficient information, ambiguous wording, or validator cannot judge.

Human judgments are scientific evidence and must not be prefilled.

