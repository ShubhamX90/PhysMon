# M250 repair round 2 re-review, Claude + GPT (5.3b guard)

Applies admission standard 5.2-5.3 (physics, qualified LLM panel) and 6.1 (naturalness) to the panel's reviews.
Judges: claude, gpt. Naturalness raters: claude. Judges required per structure: 2.

A structure is ADMITTED only if every judge calls it valid with no high flag. Missing reviews make it INCOMPLETE (a missing review is not a verdict). A sentence rated artificial must be rewritten, and so must a D sentence rated more than one level worse than its R twin (natural > slightly_artificial > artificial; standard 6.1 as amended 2026-11-15).

Structures: ADMIT 46, REJECT 6

## M250-S04: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N1', 'D1', 'N0']

## M250-S06: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S09: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'D0', 'N0']

## M250-S11: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'D0', 'N1']

## M250-S12: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TF5BA is in the past tense ('On this run, the car kept') while the question is in the present; a minor wording point that does not change the reading.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial none

## M250-S19: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0']

## M250-S202: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S204: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'N1', 'D1']

## M250-S21: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: Neither tuning sentence ensures that sound emitted after retuning has reached the listener at measurement, so the authors' retuned received frequencies are not uniquely determined.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T8B99 ('tuned up soon after the tone begins') does not say explicitly that the listening occurs after the retuning, whereas TD410 does; the natural reading supports the R answer.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): Neither tuning sentence ensures that sound emitted after retuning has reached the listener at measurement, so the authors' retuned received frequencies are not uniquely determined.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N1', 'D1', 'D0', 'R0']

## M250-S211: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'N0', 'R1', 'D1', 'D0', 'N1']

## M250-S224: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'D1', 'N1']

## M250-S225: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'N1', 'R1', 'D1']

## M250-S226: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'R1', 'D1', 'N1', 'R0']

## M250-S230: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['N0'], pending 0, slightly artificial ['D1', 'N1', 'D0', 'R1']
  - REWRITE N0 (N): claude: Placing an extra piece of metal in a separate warming cabinet that plays no role is a pointless action in this scene.

## M250-S231: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1']

## M250-S232: REJECT

- claude: validity is invalid
- claude: high flag hidden_coupling: TC5E1 and T14D0 are claimed D on the ground that an earlier run 'leaves no state behind', but detergent added to the tank's water stays dissolved in it, so unless the water was replaced the reduced surface tension carries into the present run and changes the group speed (0.1713 m/s instead of 0.1859 m/s at 0.015 N/m).
- claude: high flag insufficient_boundary_condition: Neither the problem nor the sentences state that the tank was emptied, cleaned and refilled with clean water after the earlier run, which is the condition the D claim needs.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TC5E1 and T14D0 do not establish whether the detergent-treated water remains or the clean-water surface tension was restored before the current ripples.
- gpt: high flag hidden_coupling: The authors claim the earlier run leaves no state behind, but residual detergent can change the current surface tension and therefore the group speed.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag hidden_coupling (high): TC5E1 and T14D0 are claimed D on the ground that an earlier run 'leaves no state behind', but detergent added to the tank's water stays dissolved in it, so unless the water was replaced the reduced surface tension carries into the present run and changes the group speed (0.1713 m/s instead of 0.1859 m/s at 0.015 N/m).
  - flag insufficient_boundary_condition (high): Neither the problem nor the sentences state that the tank was emptied, cleaned and refilled with clean water after the earlier run, which is the condition the D claim needs.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TC5E1 and T14D0 do not establish whether the detergent-treated water remains or the clean-water surface tension was restored before the current ripples.
  - flag hidden_coupling (high): The authors claim the earlier run leaves no state behind, but residual detergent can change the current surface tension and therefore the group speed.
- pass-1 stratum differences (claude, information only): T14D0 authors N judge R, TC5E1 authors D judge R
- pass-1 stratum differences (gpt, information only): T14D0 authors N judge R, TC5E1 authors D judge R
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N1', 'N0']

## M250-S233: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['R1', 'D0', 'R0', 'D1', 'N1']
  - REWRITE N0 (N): claude: Amplifying a second, unused laser turned away from the block, timed to 'before any light reaches the block', is a pointless and incoherent action.

## M250-S234: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T97AD and TACC7 omit the number and unit retained by the other extension sentences, departing from the review instructions' general numerical-matching requirement, although the authors explicitly identify them as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['R0', 'R1', 'D1', 'N1']
  - REWRITE D0 (D): claude: Lengthening a coiled optical cable by splicing on a piece of the rod's bulk glass in line is an implausible, pointless action in this scene.
  - REWRITE N0 (N): claude: Splicing a length of glass onto an idle coil of optical cable lying on the bench before the pulse is sent is a pointless, implausible action in this scene.

## M250-S238: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The problem explicitly identifies 120 rpm as the initial rate but does not specify the final rate for the base problem and the disconnected or density additions.
- gpt: high flag inconsistent_units: The displayed relation omega = rot omits the factor 2*pi/60 required when rot is supplied in rpm, contradicting the correctly stated conversion assumption and the certified calculations.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The density C-cancellation is shown through a contrived route (nu = eta/rho then rho*nu), whereas the physically real role of density is in the radial pressure balance and in the laminar-regime (Taylor/Reynolds) condition; the invariance itself is correct.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): The problem explicitly identifies 120 rpm as the initial rate but does not specify the final rate for the base problem and the disconnected or density additions.
  - flag inconsistent_units (high): The displayed relation omega = rot omits the factor 2*pi/60 required when rot is supplied in rpm, contradicting the correctly stated conversion assumption and the certified calculations.
- pass-1 stratum differences (claude, information only): T5A9C authors C judge K, TF420 authors C judge K
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S240: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (low): The intentional numeral-free controls TCBA8 and T2061 omit their twins' number and unit, departing from the review prompt's matching-number convention, although the authors explicitly disclose this and do not claim these controls as minimal pairs.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N1', 'R1', 'D1', 'N0']

## M250-S241: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag invalid_numerical_precision (low): With the stated constants the current is exactly eta*P/(3.1 V) = 4.83871 μA (e cancels), but the certified 4.83818 μA (and 6.48316, 8.12814, 10.8375) is 0.011% low, consistent with converting eV to J with the exact 1.602176634e-19 while using the stated e = 1.602e-19 for charge; the discrepancy is far below the precision of the inputs.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T306C and TE41A omit the numerical power and unit required by the general rendering instruction, although the authors explicitly identify them as intentional numeral-free controls and do not claim they are numerical minimal pairs.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N1', 'N0']

## M250-S246: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The claims label the quantity of the shed-roof sentences TCC3C/TC013 as 'a further layer of concrete', though the sentences do not say the roof layer is concrete; a metadata label only, with no effect on any answer.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D1', 'N1']

## M250-S251: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (low): The claimed pair TFA02/T9791 differs by the word 'also' in T9791 as well as by the time attachment and tense; this is harmless, and the number and unit (210 m/s) match.
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T9571 and T9D2A replace the numerical speed and its unit with 'a small amount', violating the required preservation of number and unit across variants of the same quantity.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T9571 and T9D2A replace the numerical speed and its unit with 'a small amount', violating the required preservation of number and unit across variants of the same quantity.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D1', 'N1']

## M250-S253: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'N1', 'D0']

## M250-S255: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Which layer is on top is not stated, so only the magnitude of the deflection is fixed; also the quantity label for TE1D7/TC665 ('a further length of strip') actually describes tape length, a metadata mislabel that does not affect any answer.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'R1']

## M250-S256: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D1', 'R1']

## M250-S262: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T75EB and T7A3F replace 13 cm with an unspecified increase, violating the review instructions' requirement that sentence variants preserve the numerical quantity and unit, despite being deliberately designated numeral-free controls.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T75EB and T7A3F replace 13 cm with an unspecified increase, violating the review instructions' requirement that sentence variants preserve the numerical quantity and unit, despite being deliberately designated numeral-free controls.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'D1']

## M250-S265: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T4891 says the mains was 14 V above its nominal value at the measurement, which presupposes that the problem's 'mains supply of 230 V rms' is the nominal rating; the problem never says 'nominal', a minor wording point rather than a contradiction.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'D0', 'N1', 'N0', 'D1']

## M250-S266: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'R1', 'D0', 'D1']

## M250-S267: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Typo in the scene clause: 'charged from a its own small cell'.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N1', 'N0']

## M250-S268: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['N0', 'D1', 'N1']
  - REWRITE D0 (D): claude: Wiring an ideal 7.5 V battery in series with a doorbell's cell before closing an unrelated switch is a pointless action no one would describe.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)

## M250-S270: REJECT

- gpt: validity is invalid
- gpt: high flag contradictory_distractor_statement: TA134 and T4BE2 say the toolbox is carried along the trolley from departure, conflicting with the unqualified base description that it stands on the trolley beside the recorder.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The scene_clause_note refers to 'a belt that moves' the toolbox, which appears nowhere in the item (the sentences use a walking technician); a stale explanatory note that does not affect any answer or stratum.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag contradictory_distractor_statement (high): TA134 and T4BE2 say the toolbox is carried along the trolley from departure, conflicting with the unqualified base description that it stands on the trolley beside the recorder.
- pass-1 stratum differences (claude, information only): T6307 authors C judge D, TDC03 authors C judge D
- naturalness: 8 sentences, rewrite ['N1', 'R0', 'D1'], pending 0, slightly artificial ['N0', 'D0', 'R1']
  - REWRITE N1 (N): claude: The sentence is redundantly worded ('walking steadily ... at a steady pace') and the tacked-on 'for an earlier run only' makes it a contrived aside no one would naturally write.
  - REWRITE R0 (R): claude: A technician walking steadily along a trolley moving at 9 m/s while carrying the recorder is an implausible scenario for a roadside acoustics setup.
  - REWRITE D1 (D): claude: A technician walking along a trolley moving at 9 m/s while carrying the recorder, and only 'for an earlier run', is an odd scenario in contrived wording.

## M250-S271: REJECT

- claude: validity is invalid
- claude: high flag other: The d_rationale for T2604 and its numeral-free twin TFBD6 says 'Metal welded onto the railing lengthens the railing only', but the item has no railing: the sentences and the scene clause concern a metal wire hanging from a hook, so the authors' stated rationale is false of this item.
- gpt: validity is invalid
- gpt: high flag other: The authors' rationales for T2604 and TFBD6 falsely describe metal welded onto a railing, whereas the rendered sentences extend the hanging wire; these claims misidentify the physical object and operation.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The d_rationale for T2604 and its numeral-free twin TFBD6 says 'Metal welded onto the railing lengthens the railing only', but the item has no railing: the sentences and the scene clause concern a metal wire hanging from a hook, so the authors' stated rationale is false of this item.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The authors' rationales for T2604 and TFBD6 falsely describe metal welded onto a railing, whereas the rendered sentences extend the hanging wire; these claims misidentify the physical object and operation.
- pass-1 stratum differences (claude, information only): T94AF authors K judge C, T9574 authors K judge C
- pass-1 stratum differences (gpt, information only): T94AF authors K judge C, T9574 authors K judge C
- naturalness: 10 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['N1', 'R1', 'D1', 'R0']
  - REWRITE D0 (D): claude: Splicing extra metal onto a wire hanging idle beside the bench, timed by fitting the rod's clamp, is a pointless action that does not fit the scene.
  - REWRITE N0 (N): claude: Splicing extra metal onto an unrelated hanging wire before the rod is clamped is a pointless action with no place in a Kundt's tube setup.

## M250-S272: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The C cancellation names the 13 lam/4 and 15 lam/4 resonances as 'the' successive pair, but for an initial length of 85 or 130 cm earlier resonances (7 lam/4 = 117 cm, 9 lam/4 = 151 cm, minus e) come first; the spacing and the invariance are unaffected.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['N1', 'N0', 'R0', 'R1', 'D1']
  - REWRITE D0 (D): claude: Opening a tap on a garden pond timed to the first resonance of a lab tube is a pointless, out-of-place event in this scene.

## M250-S274: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T664D and T3EF7 omit the number and unit retained by their quantified twins, departing from the general matching convention, although the authors explicitly designate them as numeral-free controls rather than claiming they are minimal pairs.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D0', 'D1', 'N0']

## M250-S275: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The full sentence set does not satisfy the requested uniform number-and-unit convention because T0018 and TE382 replace 0.24 nm with 'a little', although the authors explicitly identify these as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D1', 'N1', 'N0']

## M250-S279: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T6166 and TA7FF replace the numerical twins' 3.7 cm with 'a little', violating the review's stipulated preservation of the same number and unit across sentence variants, even though the authors explicitly identify these omissions as intentional controls.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T6166 and TA7FF replace the numerical twins' 3.7 cm with 'a little', violating the review's stipulated preservation of the same number and unit across sentence variants, even though the authors explicitly identify these omissions as intentional controls.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'D0', 'N1', 'R0', 'N0']

## M250-S28: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'R1', 'R0', 'D1', 'N0', 'D0']

## M250-S281: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['R1', 'N0'], pending 0, slightly artificial ['R0', 'D1', 'N1', 'D0']
  - REWRITE R1 (R): claude: A 310 km layer of rock covering a planet before a probe launch is not a plausible event in this scene.
  - REWRITE N0 (N): claude: A rock layer 'of the same density' (with no clear referent) that 'covers the moon and adds a small amount to its radius' is wording no one would use to describe a moon.

## M250-S34: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T1332 and T741D replace the numerical angle with 'a few degrees', departing from the review instructions' requested matching of numbers and units across renderings, although the authors explicitly and accurately identify these as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0']

## M250-S35: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): In T5418/T0789 'before the bob is set moving' is slightly ambiguous about which bob, since the second bob hangs at rest; the answer is unaffected.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['N1', 'N0', 'D1', 'R1']
  - REWRITE D0 (D): claude: Letting out the string of a bob that hangs at rest is pointless, and 'before the bob is set moving' muddles which bob is meant.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)

## M250-S36: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N0', 'D0']

## M250-S38: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'D0', 'N0', 'R0', 'N1']

## M250-S41: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- pass-1 stratum differences (claude, information only): T81A0 authors C judge K, TAA47 authors C judge K
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['N0', 'D1']
  - REWRITE D0 (D): claude: Moving a pair of uncharged glass rods 26 cm further apart is a pointless action with no role in the scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)

## M250-S52: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T96AB (and its twin T32CB) say 'the water' without naming the container while the scene has warm water in two containers; the context makes the first container the natural reading.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D0', 'D1', 'R0', 'N1', 'N0']

## M250-S53: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The D rationale for T3307/TA69F refers to an 'earlier survey' while the sentences say 'earlier test'; a wording mismatch in the authors' rationale only, not in the item.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T91A5's 'this wall' has a competing shed-wall antecedent, while TFB61's 'Just before' suggests a possible transient despite the explicit steady-flow condition.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["other"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D1', 'D0']

## M250-S54: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag missing_assumption (low): For the R sentences the cast layer is taken to have the stated common emissivity; the text says the spheres share an emissivity and that the layer is the same metal, but does not say the new surface has the same finish (minor, the natural reading).
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T298E and TDB9C omit the thickness number and unit supplied in their quantified twins, violating the review instructions' requirement that variants state the same number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T298E and TDB9C omit the thickness number and unit supplied in their quantified twins, violating the review instructions' requirement that variants state the same number and unit.
- naturalness: 6 sentences, rewrite ['D0'], pending 0, slightly artificial ['N0', 'R0', 'R1', 'N1', 'D1']
  - REWRITE D0 (D): claude: Casting a thick layer of metal around a bracket hanging on a frame is a pointless, implausible action in a radiation-comparison scene.

## M250-S56: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): The base sentence 'the refrigerator must remove heat from it at a steady rate of 200 W' reads as the total removal rate, which the R lamp sentences make 255 W; the later clause fixing 200 W as the wall leak resolves it, but the wording is strained (also, the scene_clause_note speaks of a lamp inside the freezer while the sentences put it above the freezer).
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): T0E77 authors C judge D, T2BAE authors C judge D
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D0', 'D1', 'R0', 'R1', 'N1']

## M250-S65: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The explicitly numeral-free controls T5FB3 and T38EB omit the value required by the general same-number variant instruction, although the authors accurately disclose this construction and do not designate these controls as numerical minimal pairs.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'D1', 'N0', 'N1']

## M250-S67: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): In T60FB and T9EF0, 'before the transmitted power was measured' can suggest the current measurement despite the intended attachment to a separate earlier experiment.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["other"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D1', 'N1', 'K0', 'D0', 'N0']

## M250-S77: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'R0', 'N1', 'D1']

## M250-S82: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The base does not specify the second star's observation state, and TF04F establishes only that an outburst began before recording, so its certified answers require an unstated condition that the outburst remains underway at observation.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The base does not specify the second star's observation state, and TF04F establishes only that an outburst began before recording, so its certified answers require an unstated condition that the outburst remains underway at observation.
- pass-1 stratum differences (gpt, information only): T099E authors D judge K, TFD41 authors N judge K
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N1']

