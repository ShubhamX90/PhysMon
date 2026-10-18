# Experiment Card X03: Format and tokenization falsification

Experiment ID: v2_X03_format_tokenization_falsification

Scientific Question: Is the cue effect a property of the physics task or of the answer-string scoring interface? Does the wrapper (output format) interact with the nuisance effect on gold-versus-decoy log-odds and on reference-free dispersion?

Discovery Or Confirmation: exploratory design card (no data collected). Any later run is discovery-only on a stratified design, not confirmatory.

Partition: Stratified 60 to 100 families drawn from the 140 original families, paired wrapper variants, both primary dense models (Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct). The sampling rule and seed are frozen before any model score is seen.

Primary Metric: Within-family nuisance effect versus wrapper-by-nuisance interaction on gold-versus-decoy log-odds (R_alt, where a decoy candidate is defined) and on reference-free range `max L - min L`.

Secondary Metrics: Total and per-token gold log-likelihood, answer-token count, value-only versus value-plus-unit likelihood, first-token versus full-sequence score, chat-template and prefix variants, repeat-pass numerical reliability (P1.3, P1.4, P1.7, p.17).

Inputs: The Stage 14.3 scoring contract (prompt bytes, answer-token spans, native chat templates); 4 to 6 equal-meaning output wrappers (plain digits, `Answer: <value> <unit>`, boxed LaTeX, JSON scalar, short natural-language answer, fixed decimals or scientific notation).

Raw Outputs: `results/stage14/x03_format_tokenization/<attempt-id>/` (not created yet).

Derived Outputs: Tokenizer audit; hierarchical paired contrasts; reference to the 14.3 scoring contract.

Stop Rules: Blocked until the Stage 14.3 scoring contract passes, until Stage 14.2 (X02) is recorded, and until the user explicitly authorizes GPU work and a partition. No Slurm submission from this card as written.

Negative Result Policy: Every family and wrapper cell is reported, including failures. A failed hook, timeout, or parse failure is NOT_EVALUATED, not a null.

Paper Eligibility Rule: Not paper-eligible; exploratory design.

PI Approval: Card creation approved by the user's instruction of 2026-10-16 (journal J14.0-001). Execution requires separate approval.

No-Go Response: If the wrapper dominates, the causal interpretation must be tied to output elicitation and cannot be presented as a universal physics vulnerability (v2 card X03, p.39; §10, p.44).

Artifact: Tokenizer audit and hierarchical paired contrasts.

v2 Reference: Card X03 (p.39); P1.3 and P1.4 (p.17); B1.4 (p.7); C04 and C05 (p.33).

Notes: Designed for the small balanced GPU pilot at compute-escalation level 2 (p.43). Cost model: N_structures x N_numeric x N_cue_cells x N_models x (N_score_forward + N_generated_resamples), recorded separately per wrapper (p.42).

Stage 14.3 update (2026-10-16): the scoring contract and the seven frozen wrappers now exist (`docs/stage14/scoring_contract.md`, `src/physmon/benchmark/scoring_contract.py`, fingerprint `bb6bbec4...`). The audit found a Llama double-BOS defect and a missing-`Answer:`-prefix mismatch in the Stage 6 scoring (journal J14.3-005), so a new scorer that follows contract rules 1 to 8 is required before any X03 run. Execution still needs explicit GPU authorization.

Stage 14.10 update (2026-10-18): the plan for the ten v2 structures under all seven wrappers is committed (`results/stage14/x03_format_tokenization/plan/attempt_20261018_1ed8be2/`, 2,954 jobs, tokenizer audit clean). This is a deviation from the card: it uses v2 structures, not 60 to 100 legacy families. The analysis rule is frozen in `docs/journal/stage14/14.10_x03_wrapper_multiverse.md` J14.10-001 before any wrapper score exists. Execution requires the user's per-submission acceptance.
