# Validator Handbook v2 (Research v2.0, Stage 14.5)

Status: **prepared by the agent; physicist confirmation of the planted-defect bank and independent reviewer sign-off
are PENDING.** An agent's own review is not independent expert validation (v2 §9, p.43), and the agent that built
these materials is not a validator. This handbook adds the v2 requirements to the Stage 13 v6 kit
(`docs/validation/validator_handbook_v6.md`, `calibration_bank_v6.*`, `annotation_schema_v6.json`,
`pilot_selection_v6.csv`, `qualification_test_v5.md`, 12 cases); it does not replace or edit them.

Plan reference: v2 B4.1 to B4.5 (p.9-10), P3.1 to P3.3 (p.20), §9 human workload (p.43), first sprint item 5 (p.48).
Journal: `docs/journal/stage14/14.5_validator_qualification.md`.

## 1. Gap analysis: Stage 13 v6 kit against v2 B4

| v2 requirement | Stage 13 v6 kit | Stage 14.5 addition |
|---|---|---|
| Blind two-pass instrument (B4.2) | Two pass forms exist | Pass 1 shows prompts only; Pass 2 adds equation, parameters, certified answer and the authors' proof text (`pass1_packets.jsonl`, `pass2_packets.jsonl`) |
| Separate validity, clarity, difficulty, naturalness; explicit uncertainty; counterexamples (B4.2) | One `overall_verdict` plus free-text fields | Review-record contract with a separate field and vocabulary for each, `uncertain_fields`, `counterexamples`, `defect_flags`, `minutes_spent`, a blinding attestation (`src/physmon/governance/review.py`) |
| Admission categories (B4.5) | Not present | The eight categories are required in Pass 2 and adjudication |
| Qualification with boundary traps, unit conversions, misleading "isolated" claims (B4.3) | 12 one-line case descriptions (unit conversion, rpm versus Hz, mass given in seconds, a distractor that is really the spring constant, a sign error), answer key marked draft; no boundary-condition or "isolated" traps and no scoring of detection | The planted-defect bank doubles as the calibration set and is scored per defect type (section 4) |
| Planted defects with detection and false-rejection by type (B4.4) | A 16-item valid/invalid calibration bank, not typed by defect | Ten typed defect rules incl. a valid-rewrite control, each tested to make exactly its declared edit (`src/physmon/validation/defect_injection.py`) |
| Agreement: raw, kappa, Gwet AC1, structure-level CIs, category-specific defect rates (P3.2) | Raw agreement and kappa | Adds Gwet AC1, structure-cluster bootstrap, per-type detection (`review.py`); kappa is `None` when undefined, not 1.0 |
| Audit sample incl. largest gold-likelihood shifts, negative scores, easy stable, ambiguous coupled systems, high-overlap clusters (B4.1) | 30 families chosen mainly by domain and cue type; every risk flag `not_identified` | A 40-family stratified sample using those strata and the Stage 14.4 clusters (`genuine_pilot_sample.csv`) |
| 20-family timing pilot before budgeting (p.43) | Not present | `in_timing_pilot_20` in the sample file |
| Reviewers blind to outputs, labels, probe scores, hypothesis (P3.1) | Stated | Enforced in the packets (leak-scanned in tests) and attested in every record |

## 2. Independence and blinding (B4.1, B4.3, P3.1)

1. The people who wrote a family do not review it. Assignments are balanced across authors, source, cue type and
   expected difficulty. Every one of the 155 v1 families gets at least one blinded review; every family used in a
   publishable confirmatory claim gets two independent reviews and a third-party adjudicator (B4.1, P3.1).
2. Reviewers never see model outputs, sensitivity labels, probe scores, the circuit hypothesis, or which items are
   planted. The restricted files are listed in `materials/v1/README.md`.
3. Reviewers are pseudonymous in every record (`reviewer_id`); expertise is recorded by domain in a separate
   coordinator file that is not published.
4. A reviewer who learns an item's status after the fact keeps the earlier locked judgment; later changes go in an
   adjudication record, never over the original.

## 3. The two-pass instrument

**Pass 1 (blind, prompts only).** For each item, read the four renderings, solve or outline the physics yourself, then
record: the governing law and relevant variables; the assumptions you needed; the target; whether the cue could change
the target; whether the wording permits another physical reading. Judge separately:

| Field | Values | Notes |
|---|---|---|
| `validity` | `valid`, `invalid`, `uncertain` | `invalid` needs `defect_flags`; `uncertain` needs `uncertain_fields` |
| `clarity` | `clear`, `ambiguous`, `unclear` | wording, independent of physics validity |
| `difficulty` | 1 to 5 | a separate judgment, never folded into validity |
| `naturalness` | `natural`, `slightly_artificial`, `artificial` | would a textbook set this? |
| `confidence` | 1 to 5 | |
| `uncertain_fields` | list | name every judgment you are not sure of |
| `defect_flags` | list | from the defect vocabulary below, or `other` with a note |
| `counterexamples` | list | a concrete case where the claimed invariance fails |
| `minutes_spent`, `started_at`, `completed_at` | | sizes the workload |
| `blinding_attestation` | must be `true` | "I have not seen model outputs, labels, probe scores or the hypothesis" |

Defect vocabulary (matches the planted-defect types): `hidden_coupling`, `missing_assumption`,
`relevant_variable_removed_from_equation`, `failed_transformation_identity`, `inconsistent_units`,
`invalid_parameter_domain`, `insufficient_boundary_condition`, `invalid_numerical_precision`,
`contradictory_distractor_statement`, `other`.

**Pass 2 (certificate review, after Pass 1 is locked).** With the encoded equation, parameters, certified answer and the
authors' proof text, additionally record `equation_consistent`, `units_consistent`, `answer_correct`,
`precision_adequate` and an `admission_category` (section 5). A symbolic certificate that a nuisance symbol is absent
from the equation is sound only given the equation and the assumptions; check whether the natural language actually
provides them (v2 B1.5, p.8). It does not certify the English text.

## 4. Qualification and the planted-defect bank (B4.3, B4.4)

1. **A physicist confirms the bank first.** `planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl` shows each edit next to
   the original. For every item the physicist records whether it is truly defective for the declared reason (and, for
   the control, whether it is truly valid) in `physicist_confirmation`. Items that fail are removed, not reworded
   silently. The agent cannot do this: the rules are text edits whose physical effect needs human confirmation. Two
   rules are allow-listed because deleting the idealisation changes the physics only for those templates (a frictionless
   ramp and an ideal gas); the rest of the 13 candidates give the acceleration or force directly and were excluded.
2. **Calibration.** Candidate reviewers see the bank items mixed with genuine items, in the packet format, blind.
3. **Scoring.** `review.detection_by_defect` gives, per defect type, the detection rate, the flagged-or-uncertain rate,
   the attribution rate (named the right defect) and, for the valid control, the false-rejection rate. A type is
   judged only in the pass where it is visible: Pass 1 for text defects, Pass 2 for the two equation/answer defects.
4. **Decision.** The plan sets no numeric qualification threshold and warns that no arbitrary agreement threshold
   substitutes for reviewing concrete physics defects (B4.5, Gate B4, p.10). A defect type that reviewers
   systematically miss means the checklist is revised and calibration repeated before confirmation proceeds
   (B4.4). `review.missed_defect_types` lists types with no detections, or below a floor that the coordinator declares
   in advance and records.
5. **The bank never enters the benchmark as genuine physics.**

## 5. Admission categories (B4.5)

Assigned in Pass 2 and fixed by adjudication. Report fractions before and after repair; never count a repaired item as
an untouched independent example. Store a signed reviewer record; publish aggregate outcomes without reviewers' names.

| Category | Use when |
|---|---|
| `CERTIFIED_AND_VALIDATED` | solver check correct and both reviewers judge the language valid and clear |
| `SOLVER_VALID_LANGUAGE_AMBIGUOUS` | the equation is right but the wording permits another reading |
| `SOLVER_INVALID` | the encoded equation, units or answer is wrong |
| `ANSWER_AMBIGUOUS` | more than one defensible final answer or precision |
| `NATURALNESS_FLAG` | valid but conspicuously unnatural |
| `REVISED_REVALIDATED` | edited after a defect and reviewed again |
| `EXCLUDED` | removed, with a reason code, and kept in the manifest |
| `UNREVIEWED` | no completed independent review yet (every family starts here) |

## 6. Adjudication and agreement (B4.3, P3.2)

- Disagreements go to a domain-qualified independent third reviewer, who sees both locked records.
- Report, per pair of reviewers: raw agreement, Cohen's kappa, Gwet's AC1 (use it when prevalence is severely
  imbalanced; kappa can be negative at 90% raw agreement), with bootstrap intervals that resample whole **structure
  clusters**, not renderings (`review.pairwise_agreement_report`). Report category-specific defect rates, adjudication
  edits and changed-label counts, and every unresolved ambiguity.
- A kappa of 0.80 is an aspiration, not a licence to drop difficult cases to improve agreement (P3.2).
- A missing review is NOT_EVALUATED: `review.completeness` lists the missing (reviewer, item, pass) triples; absence is
  never agreement.

## 7. Workload (v2 p.43)

For a conditional Phase-B scaling decision the plan budgets at least 2 validators x N structures independent family-level
judgments, plus calibration and adjudication, and more if each numeric or linguistic variant needs its own review. For
400 structures that is at least 800 judgments. **No time per judgment is assumed here.** The 20-family timing pilot
(`in_timing_pilot_20`) records `minutes_spent` per review and the adjudication time; reviewer-hours are then
`judgments x mean minutes / 60` with the measured spread, and the budget follows from that, not before.

## 8. Materials (`docs/validation/v2/materials/v1/`)

| File | Audience |
|---|---|
| `pass1_packets.jsonl`, `pass2_packets.jsonl` | reviewers (Pass 2 only after Pass 1 is locked) |
| `packet_key_RESTRICTED.json` | coordinator only: which items are planted, why, in which pass detectable |
| `planted_defect_bank_FOR_PHYSICIST_CONFIRMATION.jsonl` | the confirming physicist and coordinator |
| `genuine_pilot_sample.csv` | coordinator only: strata use model outcomes, as B4.1 asks |
| `summary.json`, `README.md` | coordinator |

The restricted files are committed for provenance. If this repository is visible to reviewers, move them out of the copy
that is shared.

## 9. Open items and sign-off

- Physicist confirmation of all 33 planted items (none confirmed yet).
- Recruit and qualify reviewers; none exists. Run the timing pilot; derive the workload.
- Nominate genuinely ambiguous coupled systems from physics expertise; the sample uses a proxy (families with an
  "isolated" clause in the thermodynamic and circuit domains).
- Review of the 147 unresolved family pairs from Stage 14.4 (P3.6) is separate human work.

| Role | Name | Date | Decision |
|---|---|---|---|
| Materials author (agent) | Claude Sonnet 5.5 for atharvgaur1845 | 2026-10-16 | prepared |
| Confirming physicist | | | PENDING |
| Validation coordinator | | | PENDING |
