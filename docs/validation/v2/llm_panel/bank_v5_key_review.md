# Bank v5 answer-key review (independent, before freeze)

Reviewer: Claude Opus 5.5 subagent, 2026-11-14. Read-only review; nothing under `llm_panel/runs/` was opened and
no judge output was seen. The 32 items were solved and judged first from `pass1_packets.jsonl` and
`pass2_packets.jsonl` under the admission standard of `judge_prompt_v3.md`. Only after that were
`key_RESTRICTED.json`, `scripts/v2/s187_build_requal_bank_v5.py` and `manifest.json` read.

Disclosure: `qualification_protocol_v3.md` was read before the packets, as the brief allowed. It names the six
deletions and the role-plant structures, so for those items my pass-1 view was not formed blind to their intended
type. I recomputed every one of their numbers anyway.

## Summary verdict: KEY SOUND

* **Verdicts.** I agree with all 32 expected verdicts: 22 invalid and 10 valid.
* **Answers.** Every certified answer is correct at every listed value. I recomputed each one, at 6 significant
  figures for the role items.
* **Deletions.** All six deletions remove a condition that changes the answer by more than 5% under a standard
  alternative. None repeats the R-580 error.
* **Valid controls.** All ten state every condition that decides the answer, so none repeats the F-909 error, and I
  found no false authors' claim in them.
* **Second defects.** No defective item has a second defect that is high under rule 1 or 2 and is not in the key.

There are **no blocking fixes**. Below are non-blocking risks. The first two are the labels a careful judge is most
likely to dispute.

## Item table

Key type abbreviations: CDS contradictory_distractor_statement, INP invalid_numerical_precision, IBC
insufficient_boundary_condition, MA missing_assumption, RNM rendering_not_minimal, FTI failed_transformation_identity,
HC hidden_coupling, RV relevant_variable_removed_from_equation, IU inconsistent_units, IPD invalid_parameter_domain,
VER valid_equivalent_rewrite.

| Item | Key type | My verdict | Agree | Notes (my computation) |
|---|---|---|---|---|
| F-905 | HC | invalid | AGREE | I = 6.0/3.0 = 2.0 A only if the circuit is isolated. The text says the other circuit "is electrically coupled to this one", so the authors' claim that I_B is absent is false and the answer is not determined. A judge may flag IBC/MA ("coupling unspecified"), which is not accepted (S3). |
| F-970 | MA (deletion) | invalid | AGREE | v_cm = R ω = 6.0 m/s needs rolling without slipping, which is no longer stated. At slip ratio 0.2, v_cm = 4.8 m/s (-20%). The deletion decides the answer. |
| F-500 | VER | valid | AGREE | T = 3.0 × 9.8 = 29.4 N. Hanging motionless is stated; the light rope is exempt under rule 1. |
| F-903 | VER | valid | AGREE | v = 5.0 × 2.4 = 12 m/s. No condition decides the answer. |
| F-333 | INP | invalid | AGREE | v = 6.0 × 3.0 = 18 m/s; shown 20 m/s (-11.1%). See S1 on the reading of "20". |
| R-699 | FTI | invalid | AGREE | Base asin(1.2 sin35°/1.7) = 23.8834°. At +5/10/15° the true answers are 26.9834/29.9427/32.7338°; the claims 20.6673/17.3567/13.9707° are the 35-q values. D sentences are correct; the base problem is complete. |
| F-900 | CDS | invalid | AGREE | v = 4.0 + 3.0 × 2.0 = 10.0 m/s (shown correctly). B's speed is restated at 5× its value (1.0 vs 5 m/s), which contradicts rule 2. "Accelerates at" is read as speeding up (S6). |
| F-352 | INP | invalid | AGREE | v = 3.0 + 2.0 × 4.0 = 11 m/s; shown 10 m/s (-9.1%). See S1. |
| F-779 | IBC (deletion) | invalid | AGREE | Initial speed deleted. Starting from rest gives x = 0.5 × 2.0 × 3.0² = 9.0 m; starting at 3.0 m/s gives 18.0 m (50% apart). The pass-2 parameter table still lists v0 = 3.0 m/s, which is not in the text (same defect). |
| F-113 | RV | invalid | AGREE | τ = 0.8 × 15.0 = 12.0 N·m (shown 12.0). The displayed sympy "1 * F_A" gives 15 N, which is also dimensionally a force, not a torque. A judge flagging only IU is not accepted (S3). |
| R-200 | RNM | invalid | AGREE | Base 9² × (1/5 + 1/15) = 21.6 W. With the cell added (V+q, q = 1.5/3/6 V) the answers are 29.4/38.4/60.0 W, all correct. Fuse K: 9/5 = 1.8 A < 3, 5 and 10 A, correct. D0 T5876 shows "6 V" while its claimed twin T1402 and its own value_shown say 3 V: a false minimal-pair claim. |
| F-406 | VER | valid | AGREE | f = 0.3 × 5.0 × 9.8 = 14.7 N. "Horizontal" and "slides" are stated. |
| F-933 | CDS | invalid | AGREE | Q = 2.0e-4 × 3.0 = 6.0e-4 C (correct). C2's charge is restated at 2× its value. |
| F-985 | VER | valid | AGREE | α = 9.0/1.5 = 6.0 rad/s². Reading the braking torque as the only torque is the natural reading. The key's waiver reason ("frictionless axles") does not quite fit (S8). |
| R-463 | FTI | invalid | AGREE | Base 100 + 850 × 9.8 × 20/1000 = 266.6 kPa. True R answers at q = 10/20/40 kPa: 276.6/286.6/306.6. Claimed: 256.6/246.6/226.6 (p0-q), although the wiring text says p0+q. Minor: the "flat base area" C claim is arguably D (S9). |
| R-258 | FTI | invalid | AGREE | Base sqrt(3 × 8.314 × 400/0.032) = 558.368 m/s. True at +50/100/200 K: 592.239/624.275/683.859. Claimed 522.306/483.561/394.826 are the T-q values. The C claims (n cancels) are correct. |
| F-357 | CDS | invalid | AGREE | Q = 1.0e-4 × 9.0 = 9.0e-4 C (correct). The distractor is restated at 2×. |
| F-867 | IU | invalid | AGREE | "Mass 3.0 m" (metres); the parameter table says kg. p = 12.0 kg·m/s if 3.0 kg. |
| R-592 | MA (deletion) | invalid | AGREE | Uniform disc: a = 2 × 9.8/(8 + 1) = 2.17778. Thin ring: 2 × 9.8/(8 + 2) = 1.96 (-10%). The deletion decides the answer. The frictionless axle is exempt under rule 1; the R/C/K claims are correct under the disc model (R at q = 0.4/0.8/1.2 kg: 1.66809/1.2/0.768627; string tensions 35.9 and 38.1 N < 120 N). |
| F-788 | IBC (deletion) | invalid | AGREE | From rest, v = 9.8 × 1.5 = 14.7 m/s. Thrown down at 2.0 m/s: 16.7 m/s (+13.6%). "Falls freely" does not imply starting from rest. |
| F-246 | IBC (deletion) | invalid | AGREE | 0.5 × 30 = 15.0 N·m only if the force is perpendicular. At 60°: 12.99 N·m (-13.4%). Both IBC and MA are accepted (good: either is a natural flag). The pass-2 parameter still says "perpendicular force". |
| R-273 | MA (deletion) | invalid | AGREE (most disputable) | t = 2 × 4186 × 40/1500 = 223.253 s if all 1500 W goes into the water. With 10% lost: 248.059 s (+11.1%). R answers (+0.5/1/2 kg): 279.067/334.88/446.507 s, correct. See S2. |
| R-972 | valid | valid | AGREE | a = 9.8(sin40° - 0.1 cos40°) = 5.5486 m/s², v = sqrt(2a × 5) = 7.44889 m/s. R (d+q, q = 1/2/3): 8.15985/8.81364/9.42218, correct. K: μs = 0.25/0.35/0.45 < tan40° = 0.839, correct. Mass C, correct. Minimal pairs (2 m/2 m) hold. Release from rest and kinetic friction are stated. |
| R-870 | valid | valid | AGREE | τ = 8 kΩ × 15 μF = 0.12 s, V = 9(1 - e^-1.25) = 6.42146 V. R (τ = (8+q) × 15e-3 s, q = 1/2/5): 6.03726/5.68909/4.82968, correct. K: opening at 300/500/1000 ms > 150 ms, correct. "Initially uncharged" and "in series" are stated; the ideal battery is exempt. Wording only: "a 8 kΩ", "broken again" (low). |
| F-279 | VER | valid | AGREE | F = 8.99e9 × 2e-6 × 3e-6/0.1² = 5.394 N. Point charges and the vacuum approximation are stated. |
| R-663 | RNM | invalid | AGREE | T = (1100 - 450) × 0.15³ × 9.8 = 21.4988 N (exactly 21.49875). R (ρ_l = 1150/1250/1350): 23.1525/26.46/29.7675, correct. Depth C and string-rating K (21.5 < 30 N), correct. D0 T2228 shows 1350 kg/m³ while its claimed twin T9EB4 shows 1250 (value_shown 1250): false. |
| R-697 | RNM | invalid | AGREE | di = 10 × 35/25 = 14.0 cm. R (do + 5/15/25): 13.3333/12.5/12.0, correct. D0 TF673 shows 25 cm while its claimed twin T1331 shows 15 cm. |
| F-593 | VER | valid | AGREE | K = 0.5 × 2.0 × 6.0² = 36.0 J. Non-relativistic correction negligible. |
| F-485 | IPD | invalid | AGREE | The mass is -1.0 kg. With +1.0 kg, F = 1.0 × 4.0²/2.0 = 8.0 N (the authors' value); the parameter table says +1.0. |
| R-802 | valid | valid | AGREE | λ = 1240/sqrt(2 × 511e3 × 54) nm = 166.917 pm (166.9165). R (54 + 50/100/200 eV): 120.276/98.8407/76.9625 pm, correct. Starts from rest and non-relativistic are stated (a relativistic treatment differs by 0.003%). One assumption line mentions "photon", which is harmless boilerplate (S7). |
| F-150 | INP | invalid | AGREE | P = 12.0²/6.0 = 24 W; shown 20 W (-16.7%). See S1. |
| R-836 | valid | valid | AGREE | T = 2π sqrt(1.2/9.8) = 2.19866 s. A small bob on a light string with small amplitude is stated (the F-909 error is not repeated). R (L+q, q = 0.2/0.4/0.6): 2.37482/2.53879/2.69279, correct. Mass C is correct. Minimal pairs (0.4 m/0.4 m) hold. |

Counts check: 22 invalid (CDS 3, INP 3, IBC 3, MA 3, RNM 3, FTI 3, HC/RV/IU/IPD 1 each) and 10 valid (6 VER, 4 role).
These agree with the protocol and the manifest.

## Blocking fixes

None. I found no mislabelled item, no wrong certified answer, no deletion that leaves the answer unchanged, and no
valid control that omits a condition deciding the answer or contains a false claim.

## Non-blocking suggestions, most disputable first

**S1. Numerical-precision displays "20 W", "20 m/s", "10 m/s" (F-150, F-333, F-352).**
* Each shown value is exactly the one-significant-figure rounding of the true answer: 24 to 20, 18 to 20, 11 to 10.
* Rule 3 makes "a displayed value rounded within its stated precision" medium or low. A judge who reads the trailing
  zero as not significant (1 s.f.) could argue that the display is within its own stated precision and call the item
  valid.
* The key's `accepted_terms_basis` measures precision against the *hidden* certified string ("24.0 W", ±0.05). The
  judge never sees that string.
* The planted reading is still the correct one. The inputs carry 2 to 3 significant figures (12.0 V, 6.0 Ω; 6.0 Hz,
  3.0 m; 3.0, 2.0, 4.0), so the answer should carry 2. Showing 20 for 24 is "rounded so far that it is wrong",
  which is exactly the vocabulary definition.
* No change is needed. If the bank is ever rebuilt, record this rationale (input precision) in the key, so that a
  dispute is settled by a rule decided before any run.

**S2. R-273 ("delivers 1500 W to the water" replaced by "rated at 1500 W").**
* This is the deletion a careful judge is most likely to dispute. Many textbook kettle problems take "all of the
  electrical energy heats the water" for granted.
* Under prompt v3 the label holds. "No heat losses" is not among rule 1's exempt idealisations, a 10% loss changes
  the answer by 11%, and rule 1 says a missing condition is a defect "even when [it] is the one most people would
  assume". A "rated" power is also not the power delivered to the water.
* So I keep AGREE, but expect this item to be the weakest detector. A judge who calls "no heat loss" a standard
  idealisation and flags it `medium` will be counted as a miss.
* No cleaner MA candidate is left in the builder's list: S72, CM_B_UM_007 and CM_B_UM_008 fail Safeguard A, and S15 is
  exempt. Replacing it would need a new deletion candidate. I do not think that is necessary.

**S3. Reasonable flags outside the accepted terms.** The accepted terms are frozen per type, so this is for the
record only.
* F-113: `inconsistent_units`. The displayed "1 * F_A" has units of N, while the target is N·m.
* F-905: `insufficient_boundary_condition` or `missing_assumption`. The nature of the coupling is unspecified, so
  there is no unique answer.
* F-485: `failed_transformation_identity` or `other`. The text has -1.0 kg, the parameter table +1.0 kg, and the
  certified 8.0 N would be -8.0 N with the stated mass.

A judge that flags *only* these would be scored as a miss. Most judges will also give the declared term.

**S4. Deletion items' pass-2 claims still assume the deleted condition.**
* F-246's parameter is "perpendicular force"; F-779's table lists v0 = 3.0 m/s; R-592's inputs and assumptions say
  "uniform disc"; R-273's say "all of the heater power goes into the water".
* This is consistent with the planted defect and makes it easier to see in pass 2. A judge may describe it as a false
  claim and flag `other`, so the accepted terms (IBC + MA) should stay as they are.

**S5. Deletions whose condition decides the answer** (Safeguard A rechecked):

| Item | Certified | Alternative | Change |
|---|---|---|---|
| F-788 | 14.7 m/s | 16.7 m/s | +13.6% |
| F-779 | 18.0 m | 9.0 m | -50% |
| F-246 | 15.0 N·m | 12.99 N·m | -13.4% |
| F-970 | 6.0 m/s | 4.8 m/s | -20% |
| R-592 | 2.17778 m/s² | 1.96 m/s² | -10% |
| R-273 | 223.253 s | 248.059 s | +11.1% |

All are correct. The dropped candidates are dropped for the right reasons:
* S72: relativistic answer differs by 0.0073%.
* CM_B_UM_007: the downslope weight component is unchanged.
* CM_B_UM_008: the displaced volume is stated.
* S15: the ideal battery is exempt under rule 1.

**S6. "Accelerates at" read as speeding up (F-900, F-352, F-779).**
* The screen treats `\baccelerates at \d` as stating "acceleration along the motion", while it drops CM_A_001
  ("undergoes constant acceleration").
* This matches ordinary usage, and the risk of dispute is low. Note that it is an interpretive regex, not a check of
  the physics.

**S7. R-802 assumption boilerplate.**
* "The constant hc has the stated value and is used for every photon energy and wavelength": there is no photon in
  the item.
* The line is not false, but under v3's strict rule 3 a pedantic judge could flag it as a wrong authors' claim.
  Low risk.

**S8. Key/manifest screen wording for F-985 (CM_B_STD_003).**
* The condition "the braking torque is the net torque" is waived with the reason "frictionless axles are a standard
  idealisation". The real reason is that the braking torque is the only torque the text mentions.
* This is cosmetic and does not affect the label.

**S9. Strata in defective role items that a judge might dispute.** Harmless unless a judge flags them *instead of*
the declared defect.
* R-463 TDCA5 ("flat base with an area of 2 m²"): claimed C through m = ρAh, p = p0 + mg/A. Without a uniform cross
  section this is really D (hydrostatic paradox). TDFFF ("uniform horizontal cross-sectional area") is fine as C.
* R-273 T249D/T1489 (initial temperature 293 K): claimed C. A judge may prefer K, with the regime "no boiling":
  final temperature 333 K < 373 K, and 343 K at the 303 K value.

**S10. R-836 T6565 ("small brass sphere, 0.5 kg").**
* A 0.5 kg brass sphere has radius of about 2.4 cm. Taken literally, the pivot-to-centre length would be about
  1.224 m, which raises T by about 1%.
* The problem's "small bob" sets the point-mass idealisation, and the sentence gives no radius, so the C claim (mass
  cancels) stands. Low risk; noted only because the bank is checked to 6 significant figures.

## Builder and manifest notes (step 3)

* **Safeguard B is a regex screen over author-listed conditions.** It proves that the listed conditions are stated.
  It cannot find a deciding condition nobody listed. For this bank I checked every valid control by hand and found
  none missing, but the screen alone would not have caught one (S8 shows an imperfect waiver reason).
* **The screen checks a defective fresh injection on the unedited family texts**, and the valid rewrites on the
  edited texts. This is correct, because the injection is the planted defect.
* **`precision_terms` measures precision on the certified display** (`family["correct_answer"]`), not on the shown
  display (see S1). The condition is met for all three items under the input-precision reading.
* **Valid role items are screened only on the base problem text.** The role claims (strata, answers at every value,
  K regimes, minimal pairs) are inherited from the M0 certification and are not re-verified by s187. I re-verified
  all of them for R-972, R-870, R-836 and R-802 (above). All are correct.
* **Consistency.** The manifest is consistent with the protocol:
  * 51 unused families; 11 fail the screen, leaving 40; 36 remain usable after the 4 deletion families are reserved.
  * The by-type counts match.
  * The chosen structures match the protocol text: FTI S26/S27/S55, RNM S15/S20/S92, valid S02/S07/S13/S72.
  * Every role plant and valid role item is on instance 1; the two M0 deletions are on instance 0.
* **The rendering plant check** (`numbers["D0"] != numbers["R0"]`) is adequate. The failed-transformation check
  (more than 5% from the true answer, positive and finite) holds on all three plants. The smallest gap I computed is
  S27 at q = 10 kPa: 256.6 vs 276.6, a 7.2% gap.
