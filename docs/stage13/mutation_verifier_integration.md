# Mutation Verifier Integration v5

Callable verifier: `physmon.benchmark.verifier.SymbolicVerifier().verify(template_yaml_path)`.

Accepted input: structured YAML templates with `governing_equation_sympy`, `parameters`, `correct_answer`, and `cue_slot`.

Output: `VerificationResult` with `template_id`, `all_passed`, and structured checks.

Mutation-safe fields: governing equation, parameter values, cue-slot proof fields, target quantity, correct answer display/value, prompt serialization.

Unsupported classes: natural-language-only semantic drift and full dimensional algebra when no structured unit algebra is available. These are recorded as coverage limitations rather than fabricated passes.
