# M0 v2 admission report

Applies admission standard 5.2-5.3 (physics, qualified LLM panel) and 6.1 (naturalness) to the panel's reviews.
Judges: claude, gpt. Naturalness raters: claude. Judges required per structure: 2.

A structure is ADMITTED only if every judge calls it valid with no high flag. Missing reviews make it INCOMPLETE (a missing review is not a verdict). A sentence rated artificial must be rewritten, and so must a D sentence rated more than one level worse than its R twin (natural > slightly_artificial > artificial; standard 6.1 as amended 2026-11-15).

Structures: ADMIT 14, REJECT 1

## M250-S21: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N1', 'D1', 'D0', 'R0']

## M250-S230: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1', 'R0', 'R1']

## M250-S232: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The deliberately numeral-free controls T6703 and T14D0 omit the number and unit required by the general rendering instructions, although the authors explicitly identify this difference and do not claim these controls are numerical minimal pairs.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R0']

## M250-S233: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TAC23's 'Before the experiment starts' phrasing is mildly open to a reading in which the amplification is not part of the run; the present tense 'adds' and the R claim make the intended reading the natural one.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['R1', 'R0', 'D1', 'N1', 'N0']
  - REWRITE D0 (D): claude: An optical amplifier 'adding 3.4 mW to the power' of a laser that is turned away and unused is odd wording and a pointless action in this scene.

## M250-S234: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The authors' scene_clause_note speaks of 'a coil of optical cable on the bench' whereas the item text has a glass tube; this is a metadata slip that does not affect the item text or answers.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'R0', 'N0', 'R1', 'D1', 'N1']

## M250-S238: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The density cancellation exhibit is circular (it writes eta as rho*(eta/rho)); the relations are true and the C label is defensible because rho appears in the Navier-Stokes momentum balance and drops out of the azimuthal balance for purely circular flow, but the exhibit does not show that physical mechanism.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- pass-1 stratum differences (claude, information only): T5A9C authors C judge K, TF420 authors C judge K
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S268: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'D1', 'N1']

## M250-S270: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N1', 'D1'], pending 0, slightly artificial ['N0', 'R0', 'D0', 'R1']
  - REWRITE N1 (N): claude: A technician walking along a moving trolley carrying the recorder, described as 'carried along the trolley ... for an earlier run only', is an odd scenario in wording no one would naturally use.
  - REWRITE D1 (D): claude: A technician walking along a moving trolley carrying the recorder, mentioned only for some earlier run, is convoluted wording and an odd action no one would include.

## M250-S271: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TFBD6/T2604 attach the timing clause 'Before the clamp is fitted' to the bar on the rack, which has no clamp; the wording is slightly odd though the rod/bar distinction is clear.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): TFBD6 and TFE55 omit the number and unit of their numerical counterparts, departing from the review instructions' common-number/unit variant format, although the packet explicitly identifies them as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- pass-1 stratum differences (claude, information only): T94AF authors K judge C, T9574 authors K judge C
- pass-1 stratum differences (gpt, information only): T94AF authors K judge C, T9574 authors K judge C
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'N1', 'R1', 'D1', 'R0']

## M250-S272: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The C cancellation expression omits the end correction and picks the 13/4 and 15/4 resonances, which are not the first ones after the start for q = 85 cm (7 lam/4 = 117 cm comes first) or q = 130 cm; both points cancel and do not affect the certified interval.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'R1', 'D1']

## M250-S281: REJECT

- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: For both relevant sentences at q = 310 km, the stated relation gives 5.48812 km/s, whereas the certified answer is 5.48839 km/s, a discrepancy beyond rounding at the displayed precision.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The scene note calls the moon 'small', which the problem does not state; harmless because the problem says the pull of any other body is ignored.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): For both relevant sentences at q = 310 km, the stated relation gives 5.48812 km/s, whereas the certified answer is 5.48839 km/s, a discrepancy beyond rounding at the displayed precision.
- naturalness: 8 sentences, rewrite ['R1', 'D0'], pending 0, slightly artificial ['R0', 'D1', 'N1', 'N0']
  - REWRITE R1 (R): claude: A rock layer covering an entire planet and adding 310 km to its radius before a probe launch is not a plausible event in this scenario.
  - REWRITE D0 (D): claude: A rock layer that 'covers the moon and adds 310 km to its radius' is a bizarre, unnatural description of a moon, given without any stated size for the moon.

## M250-S35: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T3E4C and T0789 omit the numerical extension and its unit, departing from the review instructions' uniform-number requirement, although the authors explicitly identify these as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'D1', 'D0', 'R1']

## M250-S41: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- pass-1 stratum differences (claude, information only): T81A0 authors C judge K, TAA47 authors C judge K
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D0', 'D1']

## M250-S54: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'R0', 'R1', 'N1', 'D1', 'D0']

## M250-S82: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R0', 'D0', 'R1']

