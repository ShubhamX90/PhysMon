# LLM judge requalification protocol v3 (DRAFT pending independent key review; not frozen)

**Status: DRAFT pending independent key review.** Not frozen, and no judge may be run on bank v5 until it is. Before
freezing, an independent reviewer (who has not built the bank and does not see any judge output) recomputes every label of
`bank_v5/key_RESTRICTED.json`: each certified answer, each deletion's alternative answer, each valid control against
rule 1, and each planted defect (J15.1-025 (3)). Any correction is made to the builder (`s187`) and the bank rebuilt
before the freeze; after the freeze, labels are not changed in the light of judge output.

Why: under prompt v2 on bank v4 both judges were NOT QUALIFIED (J15.1-024). Two misses were key errors of the bank:
F-909, a "valid" pendulum rewrite that states neither "simple" nor "small amplitude" (defective under rule 1, while the
same bank planted the deletion of "small amplitude" as a defect), and R-580, the deletion of "ideal" from an rms-speed
problem, which does not decide the answer (sqrt(3RT/M) holds for any classical gas in equilibrium). Other misses were
false authors' claims about the rendering or the shown equation flagged with the right term at `medium` (R-765, F-800,
F-326). Prompt v3 (`judge_prompt_v3.md`) is prompt v2 plus one sentence in rule 3: a false claim by the authors is
`high` whatever it is about (the answers, the equation shown, a value or unit in the text, a minimal pair). Under
protocol v1 a changed prompt is requalified only on items no judge has seen.

## Bank v5 (`bank_v5/`, `scripts/v2/s187_build_requal_bank_v5.py`, seed 5151): 32 items, split "requal"
22 defective, 10 valid; no item of bank v3 or v4 (item numbers, v1 families and role (structure, type) pairs are new).
* **16 fresh legacy-style injections** (the Stage 14.5 rules, `physmon.validation.defect_injection`) on DECOY-v1
  families used neither by the 14.5 planted bank, its genuine sample, nor bank v4's fresh items (51 such families; 40
  pass the rule-1 screen below): 3 contradictory distractor statement, 3 invalid numerical precision, 1 each of hidden
  coupling, relevant variable removed from the equation, inconsistent units and invalid parameter domain; 6 valid
  equivalent rewrites. No unused family admits the failed-transformation rule; that type is covered by role plants.
* **6 condition deletions** (3 insufficient boundary condition, 3 missing assumption), none of them one of bank v4's six
  (structure, edit) pairs: on v1 family texts CM_B_UM_011 ("dropped from rest" removed), CM_A_STD_002 (initial speed
  removed), CM_B_010 ("perpendicular" removed), CM_B_UM_046 ("rolls without slipping" removed); on M0 texts S01
  ("uniform solid disc" removed) and S30 ("delivers 1500 W to the water" replaced by a 1500 W rating).
* **6 role-format plants** of the two false-claim types prompt v3 targets, each on a (structure, type) pair used in
  neither bank v3 nor v4: 3 `rendering_not_minimal` (R-200 S15, R-663 S92, R-697 S20; D0 shows 6 V / 1350 kg/m^3 /
  25 cm against its twin's 3 V / 1250 kg/m^3 / 15 cm) and 3 `failed_transformation_identity` (R-258 S55, R-463 S27,
  R-699 S26; the claimed R answers subtract q instead of adding it); **4 valid role items** (R-972 S02, R-870 S07,
  R-836 S13, R-802 S72), bases not used as valid items in bank v4.
* All ten role plants and valid role items are built on certified instance 1, which no earlier bank used (banks v3 and
  v4 use instance 0), so their pass-1 problem texts differ from every item a judge has seen (checked by the builder).
  Base answers at instance 1, recomputed by hand: S02 (40 deg, mu 0.1, 5 m) 7.44889 m/s; S07 (9 V, 8 kOhm, 15 uF,
  150 ms) 6.42146 V; S13 (1.2 m) 2.19866 s; S15 (9 V; 5 and 15 Ohm) 21.6 W; S20 (f 10 cm, object 35 cm) 14.0 cm; S26
  (n 1.2 to 1.7, 35 deg) 23.8834 deg; S27 (850 kg/m^3, 100 kPa, 20 m) 266.6 kPa; S55 (400 K, 32 g/mol) 558.368 m/s;
  S72 (54 eV) 166.917 pm; S92 (15 cm cube, 450 in 1100 kg/m^3) 21.4988 N. The builder requires every flipped
  failed-transformation answer to be finite, positive and more than 5% from the true answer on the instance used (the
  smallest gap is 7.2%, S27 at q = 10 kPa), and every rendering plant's D0 number to differ from its twin's; on instance
  1 this excludes S20, S30 and S72 as failed-transformation structures (subtracting q reaches the focal length, a
  negative mass of water, a negative kinetic energy). The two M0 deletions stay on instance 0: their edit already makes
  the problem text new. With the deletions, each of the twelve M0 structures carries exactly one item.

The counts by type: contradictory distractor 3, numerical precision 3, boundary condition 3, missing assumption 3,
rendering not minimal 3, failed transformation 3, hidden coupling 1, removed variable 1, inconsistent units 1, parameter
domain 1; valid 10 (6 rewrites, 4 role items).

Caveat recorded for the reviewer: the role sentences of an M0 structure do not depend on the instance, so the sentences
of the role items (not their problem texts) were seen before.

## The two safeguards (computed by the builder; records in `manifest.json`)
* **Safeguard A (every planted under-specification).** For each candidate deletion the builder recomputes the certified
  answer by hand and computes the answer under a concrete, physically standard alternative that the edited text allows
  (thrown down at 2.0 m/s; starting from rest; force at 60 degrees to the handle; a slipping wheel with slip ratio 0.2;
  a thin-ring pulley; 10% of the heater's output lost). The alternative must change the answer by more than 5%
  relative; it and its answer are in the key (`alternative`). Candidates that failed and were dropped: S72 "treat
  non-relativistically" (relativistic answer differs by 0.007%), CM_B_UM_007 "frictionless" (the downslope weight
  component does not change), CM_B_UM_008 "fully submerged" (the displaced volume is stated); S15 "negligible internal
  resistance" was dropped because rule 1 exempts ideal batteries. A further passing candidate (CM_B_UM_004,
  "horizontal") was not needed. The builder also checks that every used deletion removes a condition its rule-1 screen
  lists as deciding the answer.
* **Safeguard B (every item; in particular every valid control).** For each v1 family and M0 structure the builder lists
  the conditions that decide the answer (from the governing relation: pendulum: simple and small amplitude; motion:
  initial state and direction of the acceleration; circular motion: uniform; collisions: elastic or not; gases: the
  model only where it decides; springs: massless where it decides; torque: the angle; and so on) and requires each to
  be stated in every rendering, or waived for a stated reason (a rule-1 standard idealisation, or no effect at the
  stated precision). A candidate that fails is used for no item, so every defective item carries its declared defect
  only. Dropped v1 families (11): CM_A_001, CM_A_002 (direction of the acceleration), CM_A_STD_008 (angle of the
  force), CM_A_STD_015 (point charges), CM_B_STD_014 (point masses / distance to the centre), CM_B_UM_013 (uniform
  motion), CM_B_UM_033 and CM_B_UM_055 (pendulums: neither simple nor small amplitude, the F-909 error), CM_B_UM_042
  (directions of the velocities), CM_B_UM_050 (massless spring), CM_B_UM_056 (both string ends fixed). Every M0
  structure passes.

## Accepted terms (frozen per type as in protocol v1/v2, one change decided before any v5 run)
A defect is detected for the declared reason when the pass-2 verdict is `invalid` and the flags contain an accepted
term. The terms are those of `s178.ACCEPTED_TERMS` (role and deletion items) and `s186.LEGACY_ACCEPTED` (fresh legacy
items), except: an `invalid_numerical_precision` item whose displayed answer is off by more than the stated precision
(half a unit in the last digit of the certified answer as written) also accepts `failed_transformation_identity`. Reason:
such a displayed answer does not follow from the shown relation and inputs either, so the second term describes the
same defect (GPT flagged F-206 this way in the v4 run; the change is made for bank v5 only, before any judge sees it, as
decided in J15.1-025 (4)). All three precision items of bank v5 meet the condition; the basis is recorded per item
(`accepted_terms_basis`).

## Judges and runs
As in protocol v2, with prompt v3: each judge is run once on all 32 items. Claude Opus 5.5 as fresh agent instances
(batches of up to four, never two items of one structure or family; transcript audit `s180`), GPT-6.1 Sol through
`codex exec` (reasoning effort high; event audit `s184`). Configuration otherwise as in q1 and gpt_q1.

## Requalification thresholds (all must hold; `s179 --split requal --protocol v3`)
| # | Criterion | Threshold | Reason |
|---|---|---|---|
| R1 | Defective items detected for the declared reason | >= 85% (>= 19 of 22) | as Q1 and protocol v2 |
| R2 | Valid items accepted with no high-severity flag | >= 85% (>= 9 of 10) | as Q3 and protocol v2 |
| R3 | Each of missing assumption, insufficient boundary condition, contradictory distractor, numerical precision | >= 2 of its 3 items detected | the types both judges failed under v1 stay fixed |
| R4 | No defect type with three or more items entirely missed | none | as Q4 |
| R5 | The false-claim role plants (rendering_not_minimal and failed_transformation_identity role items) | all but one detected (>= 5 of 6) | the change of prompt v3 targets exactly these |

A judge that passes is QUALIFIED with prompt v3 for its tier (Claude: CLAUDE_JUDGE_PROVISIONAL, EXPLORATION admissions
only; GPT: a panel member). A judge that fails is not used; any further prompt change needs another unseen set. A
verdict is reported, not overridden, and labels are not changed after seeing judge output.
