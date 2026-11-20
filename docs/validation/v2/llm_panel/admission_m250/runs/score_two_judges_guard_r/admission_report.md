# M250 exploration admission, Claude + GPT (5.3b guard, twin-citing flags; J15.1-059)

Applies admission standard 5.2-5.3 (physics, qualified LLM panel) and 6.1 (naturalness) to the panel's reviews.
Judges: claude, gpt. Naturalness raters: claude. Judges required per structure: 2.

A structure is ADMITTED only if every judge calls it valid with no high flag. Missing reviews make it INCOMPLETE (a missing review is not a verdict). A sentence rated artificial must be rewritten, and so must a D sentence rated more than one level worse than its R twin (natural > slightly_artificial > artificial; standard 6.1 as amended 2026-11-15).

Structures: ADMIT 52, REJECT 88

## M250-S03: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: For T8516 (and less sharply T9B35) the item does not say that the loaded first cart still moves at 6 m/s; a block attached 'just before the collision' to a cart already moving at 6 m/s would, if initially at rest, slow it to 4.186 m/s, giving 2.163 m/s rather than the certified 2.825 m/s.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): For T8516 (and less sharply T9B35) the item does not say that the loaded first cart still moves at 6 m/s; a block attached 'just before the collision' to a cart already moving at 6 m/s would, if initially at rest, slow it to 4.186 m/s, giving 2.163 m/s rather than the certified 2.825 m/s.
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T1828 and T2689 replace the numerical mass and unit with 'small', violating the review instructions' requirement that variants concerning the same quantity preserve its number and unit, even though the authors identify these omissions as intentional controls.
  - flag other (low): The description calls the collision 'head-on' while explicitly specifying motion in the same direction, creating a minor terminological inconsistency.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T1828 and T2689 replace the numerical mass and unit with 'small', violating the review instructions' requirement that variants concerning the same quantity preserve its number and unit, even though the authors identify these omissions as intentional controls.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1', 'R0']

## M250-S04: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: Neither the problem nor the authors' assumptions fixes the spring's opposite end, whose motion can change the block's maximum speed.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The K sentences limit Hooke behaviour for extensions only while the block also compresses the spring by 0.15 m, and the out-of-regime reference expression q*sqrt(k/m) is not the physics beyond an elastic limit; both are uncertified side remarks and do not affect any listed answer.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): Neither the problem nor the authors' assumptions fixes the spring's opposite end, whose motion can change the block's maximum speed.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D0', 'D1', 'N0']

## M250-S05: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: TADD2 and TFEA1 omit the added disc's mass distribution, although the claimed inertia and certified accelerations require that disc to be uniform.
- gpt: high flag other: The static-friction claims incorrectly predict changed physics and zero acceleration at q = 9 N*m: the stated disc is already rotating, so a larger static-friction limit does not replace its prescribed sliding-friction torque.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The K regime 'static friction < driving torque' is not the operative reason: the problem says the disc already rotates, so kinetic friction governs regardless of the static value; the certified in-regime answers are still correct.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): TADD2 and TFEA1 omit the added disc's mass distribution, although the claimed inertia and certified accelerations require that disc to be uniform.
  - flag other (high): The static-friction claims incorrectly predict changed physics and zero acceleration at q = 9 N*m: the stated disc is already rotating, so a larger static-friction limit does not replace its prescribed sliding-friction torque.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'R1', 'N0']

## M250-S06: REJECT

- gpt: validity is invalid
- gpt: high flag other: For TA527 and T776D, the authors' outside-regime reference expression of zero current does not follow from exceeding a power rating: a rating supplies neither a failure mechanism nor a guarantee of an open circuit.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): For TA527 and T776D, the authors' outside-regime reference expression of zero current does not follow from exceeding a power rating: a rating supplies neither a failure mechanism nor a guarantee of an open circuit.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D1', 'N1']

## M250-S08: REJECT

- claude: validity is invalid
- claude: high flag other: For TF8B9 and TFF02 the certified answers (16.1905, 16.5957, 17.3333 mJ) are Ceq'V^2/2, the energy of the whole three-capacitor network, but the question asks for the energy 'stored in the two capacitors together', which literally means the 4 μF and 12 μF capacitors only (15.51 mJ at q = 7.5 μF), so the certified answer is wrong on the literal reading and at best one of two readings.
- gpt: validity is invalid
- gpt: high flag other: For TF8B9 and TFF02, every certified answer includes energy in the added capacitor, whereas the question asks for energy in the original two capacitors.
- gpt: high flag missing_assumption: The outside-regime reference energy C2*V^2/2 assumes the first capacitor fails as a short circuit, but exceeding a voltage rating does not specify that failure model.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): For TF8B9 and TFF02 the certified answers (16.1905, 16.5957, 17.3333 mJ) are Ceq'V^2/2, the energy of the whole three-capacitor network, but the question asks for the energy 'stored in the two capacitors together', which literally means the 4 μF and 12 μF capacitors only (15.51 mJ at q = 7.5 μF), so the certified answer is wrong on the literal reading and at best one of two readings.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): For TF8B9 and TFF02, every certified answer includes energy in the added capacitor, whereas the question asks for energy in the original two capacitors.
  - flag missing_assumption (high): The outside-regime reference energy C2*V^2/2 assumes the first capacitor fails as a short circuit, but exceeding a voltage rating does not specify that failure model.
- pass-1 stratum differences (claude, information only): TCCF3 authors C judge K, TE79C authors C judge K
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'D0', 'R1', 'D1', 'R0']

## M250-S09: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T128A and TC375 do not establish that water added for the earlier experiment was removed or included in the stated mass, so the authors' claim that the earlier event leaves no state behind is unsupported and the participating heat capacity is ambiguous.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T4800 ('is poured into this container') does not say whether the water is added before or after the exchange with the block; the intended reading (present during the exchange, at 293 K) is the natural one but not the only one.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T128A and TC375 do not establish that water added for the earlier experiment was removed or included in the stated mass, so the authors' claim that the earlier event leaves no state behind is unsupported and the participating heat capacity is ambiguous.
- naturalness: 6 sentences, rewrite ['N0'], pending 0, slightly artificial ['N1', 'D1', 'R0']
  - REWRITE N0 (N): claude: Pouring an unspecified extra amount of water into a separate bystander container is a pointless action, and 'the same temperature' has no clear referent.

## M250-S10: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite ['D0', 'N1', 'N0'], pending 0, slightly artificial ['C1', 'R0', 'D1', 'R1']
  - REWRITE D0 (D): claude: Placing a 'further 2.2 m stand' under a bystander table is a pointless, oddly worded action that does not belong in this scene.
  - REWRITE N1 (N): claude: A 'further small stand' placed under the platform 'for an earlier experiment only' is a contrived, oddly worded history with no place in this scene.
  - REWRITE N0 (N): claude: Placing 'a further small stand' under a table beside the platform is a pointless action with wording no one would use.

## M250-S11: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T8720/TB9A5 add a speed gain before braking to a base that says the car travels at 20 m/s and brakes; 'further' makes the intended 24.5 m/s reading clear but the wording is slightly awkward.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag rendering_not_minimal (medium): The numeral-free controls omit the number and unit preserved in the other speed-gain renderings, departing from the review instructions' general matching requirement, although the authors explicitly identify this intentional difference.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite ['D1', 'N0', 'N1'], pending 0, slightly artificial ['R0', 'D0', 'R1']
  - REWRITE D1 (D): claude: 'Gained a further 4.5 m/s on an earlier run' has no referent for 'further' and is wording no one would naturally use in this braking scenario.
  - REWRITE N0 (N): claude: The bus 'gains a further small amount' is incoherent, as it is unclear what is gained and the bus never brakes.
  - REWRITE N1 (N): claude: It is unclear what the car 'gained', so the sentence is vague to the point of incoherence.

## M250-S12: REJECT

- gpt: validity is invalid
- gpt: high flag other: TF5BA describes an outward displacement before entering the stated 50 m curve, which does not establish a new turning radius, so its claimed R classification, r + q wiring and changed certified answers are unsupported.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): TF5BA ('driven 7.5 m further from the centre of the curve before it entered the curve') is claimed R via r -> r + q, which is defensible (the car moved to an outer line before entry and keeps it), but it can also be read as a lateral position on the approach that says nothing about the radius on the curve.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): TF5BA describes an outward displacement before entering the stated 50 m curve, which does not establish a new turning radius, so its claimed R classification, r + q wiring and changed certified answers are unsupported.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): TF5BA authors R judge D
- pass-1 stratum differences (gpt, information only): TF5BA authors R judge D
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'D1', 'R1', 'R0', 'N1']

## M250-S14: REJECT

- gpt: validity is invalid
- gpt: high flag other: The K claims give q as an outside-regime reference expression for power, but a maximum below 470.4 W makes the specified lift impossible rather than establishing an alternative answer P = q.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The K claims give q as an outside-regime reference expression for power, but a maximum below 470.4 W makes the specified lift impossible rather than establishing an alternative answer P = q.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'D0', 'N0', 'R1']

## M250-S16: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D0', 'N0', 'R0', 'D1']

## M250-S17: REJECT

- claude: validity is invalid
- claude: high flag other: T9AD7 is certified R (106 W) but the problem states the steady surface temperature difference of the test as 20 K, so a warming made 'before the test began' is most naturally already included in that 20 K (80 W); the sentence admits both 80 W and 106 W and the certified R answer is not uniquely supported.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TFD0A does not specify that the colder surface remains unchanged or that the requested flow is evaluated after a new steady state is established, although its certified answers require both conditions.
- gpt: high flag failed_transformation_identity: T9AD7 describes warming before the test, so the stated test temperature difference remains 20 K; its R classification, additive wiring and certified answers incorrectly apply that historical warming again.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag other (high): T9AD7 is certified R (106 W) but the problem states the steady surface temperature difference of the test as 20 K, so a warming made 'before the test began' is most naturally already included in that 20 K (80 W); the sentence admits both 80 W and 106 W and the certified R answer is not uniquely supported.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): TFD0A does not specify that the colder surface remains unchanged or that the requested flow is evaluated after a new steady state is established, although its certified answers require both conditions.
  - flag failed_transformation_identity (high): T9AD7 describes warming before the test, so the stated test temperature difference remains 20 K; its R classification, additive wiring and certified answers incorrectly apply that historical warming again.
- pass-1 stratum differences (claude, information only): T9AD7 authors R judge D
- pass-1 stratum differences (gpt, information only): T9AD7 authors R judge D
- naturalness: 8 sentences, rewrite ['N0', 'D0'], pending 0, slightly artificial ['D1', 'R0', 'N1']
  - REWRITE N0 (N): claude: The partition has no established hotter surface or earlier warming, so warming it 'by a further few kelvin' is an incoherent, purposeless action.
  - REWRITE D0 (D): claude: Warming a bystander partition's surface 'by a further 6.5 K' has no antecedent and is a pointless action in this scene.

## M250-S18: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): TC41F and T6073 extend the expansion past the stated 2x end point without restating that the continued part is slow and isothermal; the certified p1V1 ln(q) relies on reading it as a continuation of the same process, which is the natural but not the only reading.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): The intended first-cylinder referents of 'this cylinder' in T6073 and 'the expansion' in TC41F could be stated more explicitly because the description also introduces a second expanding gas.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N1', 'R0', 'D0', 'N0', 'D1']

## M250-S19: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TFDC7 does not establish that its direction adjustment precedes the current launch; its placement after the landing description permits an adjustment after the current flight, yielding a different range.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): TFDC7 ('The launch direction is then lowered by a further 14°'), appended after 'The ball lands on the level ground', admits a reading in which the lowering happens after this flight, giving 38.3548 m instead of the certified R answer 27.3115 m.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TFDC7 does not establish that its direction adjustment precedes the current launch; its placement after the landing description permits an adjustment after the current flight, yielding a different range.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite ['D0'], pending 0, slightly artificial ['R1', 'N1', 'R0', 'D1', 'N0']
  - REWRITE D0 (D): claude: Lowering the ramp 'by a further' angle has no prior lowering to refer to and is a pointless action after the ball has already landed.

## M250-S201: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T708C says the clay 'was stuck to the block before the driving force was applied' but does not state outright that it is still on during the steady run; R is the natural reading.
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T275C and TDD8E omit the 420 g quantity retained in their numerical twins, contrary to the frozen review requirement that same-quantity variants retain the same number and unit.
  - flag other (medium): The cancellation explanation should specify a lag-shifted reference for its components: relative to cos(omega*t), the response coefficients involve phi-delta rather than phi alone.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T275C and TDD8E omit the 420 g quantity retained in their numerical twins, contrary to the frozen review requirement that same-quantity variants retain the same number and unit.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D1', 'N1', 'N0']

## M250-S202: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The problem defines the empty mass as excluding payload but never states the current payload mass or its absence, so the total initial and final masses, and consequently the final speed, are not uniquely determined.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The problem defines the empty mass as excluding payload but never states the current payload mass or its absence, so the total initial and final masses, and consequently the final speed, are not uniquely determined.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S203: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The base never fixes the platform's translational acceleration during observation, and T4B28 does not specify whether its earlier acceleration continues, so neither has a uniquely determined period.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T4B28 ('was set rising with a constant upward acceleration ... before the oscillations were observed') does not state outright that the acceleration persists during the oscillations; the authors' R reading is the natural one but a past-phase reading is possible.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The base never fixes the platform's translational acceleration during observation, and T4B28 does not specify whether its earlier acceleration continues, so neither has a uniquely determined period.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'D1', 'R0', 'N1', 'R1']
  - REWRITE N0 (N): claude: A crane hook accelerating upward at a vaguely stated constant rate during the bead's oscillations is an event that does not belong in this scene.

## M250-S204: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T081E establishes an earlier pickup but does not state that the bag remains with the skater during the collision, which determines the colliding mass and energy loss.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T081E does not say whether the stated 4 m/s holds after the bag is picked up; the authors' wiring keeps v1 = 4 m/s with mass m1+q (the natural reading of the present-tense description), but picking up a bag at rest from the ice would by momentum conservation lower the speed to 3.33 m/s and give 369.39 J.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T081E establishes an earlier pickup but does not state that the bag remains with the skater during the collision, which determines the colliding mass and energy loss.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite ['N1', 'D1'], pending 0, slightly artificial ['R1', 'R0']
  - REWRITE N1 (N): claude: The statement that the skater picked up a bag 'on an earlier outing only' is pointless and worded in a way no one would use.
  - REWRITE D1 (D): claude: The phrase 'picked up a 12 kg bag on an earlier outing only' is wording no one would use and the detail is a pointless aside to the collision.

## M250-S205: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['D1', 'N1', 'R0', 'R1'], pending 0, slightly artificial ['D0']
  - REWRITE D1 (D): claude: A 6 g price tag stuck to a coin for an earlier trial is an implausible object for this scene and heavier than the stated purpose would suggest.
  - REWRITE N1 (N): claude: Sticking a price tag on the coin 'for an earlier trial only' is a pointless action described in wording no one would use.
  - REWRITE R0 (R): claude: A price tag stuck to a coin is odd, and one weighing half as much as the coin is implausible.
  - REWRITE R1 (R): claude: A price tag weighing 6 g, half the coin's mass, stuck to a coin on a turntable is implausible.

## M250-S206: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T70B1 says the platform 'was set rising' with constant acceleration before steady rotation; the intended reading that the acceleration continues during steady rotation is the natural one but less explicit than T4A32.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T2913 and T3820 omit the numerical value and symbolic unit present in their twins, departing from the general matched-number variant format, but the authors explicitly disclose them as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D1', 'D0', 'N0', 'N1', 'C1', 'R0']

## M250-S207: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['N0'], pending 0, slightly artificial ['D1', 'N1', 'R0', 'D0']
  - REWRITE N0 (N): claude: Placing a sandbag in a toolbox on the floor is a pointless action that does not belong in this pulley scene.

## M250-S208: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T3181 and T1AC4 omit the number and unit retained in their respective ring variants TE735 and T7B9A, contrary to the required preservation of the quantity's number and unit across variants.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T3181 and T1AC4 omit the number and unit retained in their respective ring variants TE735 and T7B9A, contrary to the required preservation of the quantity's number and unit across variants.
- naturalness: 8 sentences, rewrite ['N0', 'N1'], pending 0, slightly artificial ['D1', 'D0']
  - REWRITE N0 (N): claude: 'A ring whose moment of inertia is a small amount' is wording no one would use for a detail of the scene.
  - REWRITE N1 (N): claude: 'A ring whose moment of inertia is a small amount' is wording no one would use, even though gluing on a ring for an earlier run is a plausible event.

## M250-S209: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The rod's initial translational and angular velocities are unspecified, although they affect the requested angular speed; T4CC0 additionally leaves the attachment time unspecified.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The rod's initial translational and angular velocities are unspecified, although they affect the requested angular speed; T4CC0 additionally leaves the attachment time unspecified.
- naturalness: 6 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['R0', 'D1', 'R1', 'N1']
  - REWRITE D0 (D): claude: Pressing a weighed piece of clay onto a vase on a shelf is a pointless action that does not belong in this collision scene.
  - REWRITE N0 (N): claude: Pressing a 'further' piece of clay onto a vase on a shelf is a pointless action that does not belong in the scene.

## M250-S21: REJECT

- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: TD410 places the tuning increase before measurement of the stated emitted frequency, so the authors incorrectly add the increase again, producing an erroneous R classification, wiring and certified answers.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T8B99 'The siren is then tuned up by a further 16 Hz' does not say whether the retuning precedes the listening asked about and sits awkwardly beside 'a steady tone of 440 Hz'; the authors' R reading (456 Hz emitted) is the most natural one but not the only one.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): TD410 places the tuning increase before measurement of the stated emitted frequency, so the authors incorrectly add the increase again, producing an erroneous R classification, wiring and certified answers.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): T4EE7 authors C judge K, TE5DD authors C judge K
- pass-1 stratum differences (gpt, information only): TD410 authors R judge D
- naturalness: 8 sentences, rewrite ['N1', 'N0', 'D0'], pending 0, slightly artificial ['R1', 'D1', 'R0']
  - REWRITE N1 (N): claude: 'Tuned up by a further small amount on an earlier run' refers to no prior tuning and is vague wording no one would use for a siren.
  - REWRITE N0 (N): claude: Tuning a parked van's horn 'by a further small amount' has no antecedent tuning and is not a plausible action in this scene.
  - REWRITE D0 (D): claude: Tuning a parked van's horn up by 'a further 16 Hz' is an implausible action with no prior tuning to be 'further' to.

## M250-S210: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T7E76 and TB3BF remove the number and unit from their damping-coefficient twins, violating the review requirement that variants of the same quantity preserve the number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T7E76 and TB3BF remove the number and unit from their damping-coefficient twins, violating the review requirement that variants of the same quantity preserve the number and unit.
- pass-1 stratum differences (gpt, information only): T9920 authors C judge K, TF11F authors C judge K
- naturalness: 8 sentences, rewrite ['N1', 'N0'], pending 0, slightly artificial ['D1', 'D0']
  - REWRITE N1 (N): claude: The phrase 'a damping coefficient of a small value' is wording no one would use, and the earlier-run aside adds to the contrivance.
  - REWRITE N0 (N): claude: An 'extra damper' on a bystander door with 'a damping coefficient of a small value' is wording no one would use and does not belong in the scene.

## M250-S211: REJECT

- gpt: validity is invalid
- gpt: high flag invalid_parameter_domain: Both cancellation explanations apply the interior-sphere field formula Qc d/(4 pi epsilon_0 a^3) at d = 6 cm even for cavity radii 3.5 cm and 5.5 cm, where that observation point is outside the removed sphere.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The C cancellation relations are written loosely ('field of the removed ball at distance d from its centre'; 'cavity field = that field') rather than as the full superposition rho(r - r')/(3 eps0), though the magnitude rho d/(3 eps0) and the a^3 cancellation are correct; the ball's permittivity is also taken as eps0 without statement (standard idealisation).
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag invalid_parameter_domain (high): Both cancellation explanations apply the interior-sphere field formula Qc d/(4 pi epsilon_0 a^3) at d = 6 cm even for cavity radii 3.5 cm and 5.5 cm, where that observation point is outside the removed sphere.
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['R0', 'N0', 'D1', 'D0', 'N1']
  - REWRITE R1 (R): claude: A plastic clip heavier than the bead being stuck to it at the instant of release inside an enclosed cavity is an implausible, contrived event.

## M250-S212: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0']

## M250-S213: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TD80D 'Each ion weighs 63 u' uses 'weighs' with a mass unit; loose but conventional wording.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D1', 'R0', 'R1', 'D0']

## M250-S214: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D1', 'N1', 'D0']

## M250-S215: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The problem supplies total inductance and capacitance without stating uniformity, so a nonuniform lossless cable can have different first-arrival transmission and load voltage.
- gpt: high flag invalid_parameter_domain: The certified 310 m length, with the fixed stated totals and uniform nondispersive line model, requires a wavefront speed of 6.2e8 m/s, exceeding the speed of light.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T2129 ('cut to a length') could suggest the stated totals no longer apply; the answer is unaffected because Z0 depends only on L/C, which is per-length invariant.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): The problem supplies total inductance and capacitance without stating uniformity, so a nonuniform lossless cable can have different first-arrival transmission and load voltage.
  - flag invalid_parameter_domain (high): The certified 310 m length, with the fixed stated totals and uniform nondispersive line model, requires a wavefront speed of 6.2e8 m/s, exceeding the speed of light.
  - flag rendering_not_minimal (medium): TBEAE and T0205 deliberately omit the numerical resistance and therefore do not satisfy the review instructions' common-number-and-unit variant format, although the authors explicitly identify them as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S216: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: Neither the problem nor the authors' assumptions explicitly connects the negative plates, although that return connection is essential to the claimed charge-transfer oscillation and maximum voltage.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): In the flash-unit sentences 'charged to the same voltage' has no clear referent; harmless because the sentence is disconnected.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): Neither the problem nor the authors' assumptions explicitly connects the negative plates, although that return connection is essential to the claimed charge-transfer oscillation and maximum voltage.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'R0', 'N0', 'N1']

## M250-S217: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'N1', 'D1']

## M250-S218: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T0373 and TD96B omit the batteries' relative polarity, so series connection permits either adding or subtracting their emfs, whereas the authors certify only the adding configuration.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T0373 and TD96B omit the batteries' relative polarity, so series connection permits either adding or subtracting their emfs, whereas the authors certify only the adding configuration.
- naturalness: 8 sentences, rewrite ['N0', 'D0'], pending 0, slightly artificial ['N1', 'D1']
  - REWRITE N0 (N): claude: Connecting a small battery in series with a wall neon sign's supply is a pointless, implausible action in this scene.
  - REWRITE D0 (D): claude: Adding a 450 V battery in series with a neon sign's supply is a pointless, implausible action in this scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)

## M250-S219: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The problem does not state nonrelativistic motion, and its unrestricted perpendicular velocity permits relativistic motion with a materially different pitch.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): The problem does not state nonrelativistic motion, and its unrestricted perpendicular velocity permits relativistic motion with a materially different pitch.
- naturalness: 8 sentences, rewrite ['R1', 'D1', 'N1'], pending 0, slightly artificial ['N0', 'D0']
  - REWRITE R1 (R): claude: A 'further' charge sitting on the bead contradicts its stated charge, and the wording is not how anyone would describe a charged bead.
  - REWRITE D1 (D): claude: 'A further 3.4 mC of charge sat on the bead for an earlier run only' is unnatural phrasing describing an irrelevant past state with no clear meaning.
  - REWRITE N1 (N): claude: 'A further small amount of charge sat on the bead for an earlier run only' is unidiomatic wording, with 'further' referring to nothing and an odd image of charge 'sitting' for a past run.

## M250-S22: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): With a second string in the scene, 'the string' and 'this string ... then increased' (TE80D) are mildly ambiguous in referent and timing, though the intended reading (first string, increase before vibration) is the natural one.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): After introducing the second string, references to 'the string' and 'this string' have an ambiguous antecedent, although the first, fully specified string is the natural intended target.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["other"]}
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R0', 'N0', 'R1', 'D0', 'N1']

## M250-S220: REJECT

- claude: validity is invalid
- claude: high flag missing_assumption: TE652 and TBFE0 say only that the further 350 V battery is 'connected in series with the battery', not that it faces the same way; the certified wiring V + q assumes aiding polarity, while an opposing battery gives V - q (150 V, 0.0675 mN).
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TBFE0 and TE652 specify a series connection without relative battery polarity, so the authors' assumed voltage V+q and the resulting certified forces are not uniquely determined.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): TE652 and TBFE0 say only that the further 350 V battery is 'connected in series with the battery', not that it faces the same way; the certified wiring V + q assumes aiding polarity, while an opposing battery gives V - q (150 V, 0.0675 mN).
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TBFE0 and TE652 specify a series connection without relative battery polarity, so the authors' assumed voltage V+q and the resulting certified forces are not uniquely determined.
- pass-1 stratum differences (claude, information only): TA3FF authors K judge C, TAC6D authors K judge C
- pass-1 stratum differences (gpt, information only): TA3FF authors K judge C, TAC6D authors K judge C
- naturalness: 8 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['R1', 'N1', 'D1']
  - REWRITE D0 (D): claude: Wiring an extra 350 V battery in series with a Geiger counter's own high-voltage supply is a pointless, implausible action in this scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)
  - REWRITE N0 (N): claude: Wiring an unspecified extra battery in series with the Geiger counter's own supply is a pointless, odd action for this scene.

## M250-S221: REJECT

- gpt: validity is invalid
- gpt: high flag other: The K annotations give 9nR(T2-T1)/2 as an outside-regime reference expression, although failure of 5T2 < theta does not imply fully excited vibration, which that expression requires.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The K annotations give 9nR(T2-T1)/2 as an outside-regime reference expression, although failure of 5T2 < theta does not imply fully excited vibration, which that expression requires.
- naturalness: 10 sentences, rewrite ['R1'], pending 0, slightly artificial ['D0', 'N1', 'D1', 'N0']
  - REWRITE R1 (R): claude: Saying the cylinder also holds a further 1.3 mol contradicts the earlier statement that it holds 2 mol of nitrogen.

## M250-S222: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T6A43 and TE45E omit the 13 kW specified by their respective twins TD41F and T5218, violating the review instructions' requirement that variants preserve the number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T6A43 and TE45E omit the 13 kW specified by their respective twins TD41F and T5218, violating the review instructions' requirement that variants preserve the number and unit.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'R1', 'D0', 'R0', 'D1']

## M250-S223: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite ['R1', 'D0'], pending 0, slightly artificial ['D1', 'N1', 'N0']
  - REWRITE R1 (R): claude: Saying the 0.2 kg block 'also includes a further 0.13 kg of ice' conflicts with the stated mass and is worded in a way no one would use.
  - REWRITE D0 (D): claude: Putting a measured mass of ice at its melting point into a corridor water dispenser before the heating is a pointless action that does not belong in this scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)

## M250-S224: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: T6DA3 admits helium after the stated initial state without specifying that the compartments regain a common temperature before mixing; equal pressures from a freely sliding partition do not establish equal temperatures, so its certified entropy changes are not determined.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The R sentences do not state that the added helium is at the common temperature; the intended reading is natural but implicit.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): T6DA3 admits helium after the stated initial state without specifying that the compartments regain a common temperature before mixing; equal pressures from a freely sliding partition do not establish equal temperatures, so its certified entropy changes are not determined.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D0', 'N0', 'D1', 'N1']

## M250-S225: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T21B1 and T15F5 do not explicitly replace the maintained 300 K condition at radius 9 cm with a condition solely at the new outer surface, so retaining or releasing the original constraint gives materially different answers.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): For the R sentences the base text still says the outer surface of the insulation (at 9 cm) is held at 300 K; the authors' wiring (outermost surface at r2+q held at 300 K) is the natural reading, but a reader could keep the 9 cm surface clamped and get 55.80 K.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T21B1 and T15F5 do not explicitly replace the maintained 300 K condition at radius 9 cm with a condition solely at the new outer surface, so retaining or releasing the original constraint gives materially different answers.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['R1', 'D1', 'D0', 'N0']
  - REWRITE N1 (N): claude: Wrapping extra insulation 'for an earlier survey only' is a contrived, hard-to-picture history phrased in wording no one would ordinarily use.

## M250-S226: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T7BAD describes ongoing warming without specifying the observation time or stating that the hot plate subsequently remains at 870 K until the shields reach a new steady state, which its certified answer requires.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Progressive 'is then warming ... by a further 70 K' (T7BAD) is slightly awkward against a steady state, and the claim metadata labels the kettle sentences' quantity as 'a further warming of the hot plate'; neither affects the answers.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T7BAD describes ongoing warming without specifying the observation time or stating that the hot plate subsequently remains at 870 K until the shields reach a new steady state, which its certified answer requires.
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'R1', 'D1', 'N1', 'R0']
  - REWRITE N0 (N): claude: 'A heater is then warming the water by a further few kelvin' has incoherent tense, refers to no earlier warming, and is a pointless event in a steady-state radiation setup.

## M250-S227: REJECT

- claude: validity is invalid
- claude: high flag other: T5974 is certified R (gas at 338 K, 1.57093 kJ/mol), but the problem states the gas 'is in thermal equilibrium at a temperature of 300 K', so heating that happened before the molecules equilibrated is naturally already included in that 300 K (1.27797 kJ/mol); read as the authors intend, the sentence contradicts the stated equilibrium temperature, so the certified R answer is not uniquely supported.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T4CBB describes ongoing heating without specifying that the requested energy is evaluated after the entire temperature increase and equilibration, so its certified answer is not uniquely determined.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag other (high): T5974 is certified R (gas at 338 K, 1.57093 kJ/mol), but the problem states the gas 'is in thermal equilibrium at a temperature of 300 K', so heating that happened before the molecules equilibrated is naturally already included in that 300 K (1.27797 kJ/mol); read as the authors intend, the sentence contradicts the stated equilibrium temperature, so the certified R answer is not uniquely supported.
  - flag inconsistent_units (low): The relation x = dE/(R*T) lists dE in kJ/mol and R in J/(mol*K) without a conversion factor; the certified numbers are right, so this is only a presentation slip in the stated relation.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T4CBB describes ongoing heating without specifying that the requested energy is evaluated after the entire temperature increase and equilibration, so its certified answer is not uniquely determined.
- pass-1 stratum differences (claude, information only): T5974 authors R judge D
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'R0', 'D1', 'D0', 'R1', 'N0']

## M250-S228: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'R0', 'N1', 'N0', 'D0']

## M250-S229: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T427C and T64CC replace their numerical twins' 17 K with 'a few kelvin', violating the review instructions' requirement that variants of the same quantity preserve its number and unit, even though the authors explicitly designate these as numeral-free controls.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T427C and T64CC replace their numerical twins' 17 K with 'a few kelvin', violating the review instructions' requirement that variants of the same quantity preserve its number and unit, even though the authors explicitly designate these as numeral-free controls.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N1', 'N0', 'R0', 'R1']

## M250-S23: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T656C could be read as describing the last stage of the heating to 360 K rather than an extra 38 K; the authors' (and the more natural) reading is the extra warming to 398 K.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): The intended reading is recoverable, but 'this piston' has an ambiguous referent and T656C does not explicitly describe its warming as additional to reaching 360 K.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["other"]}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R0', 'N1', 'D0', 'N0', 'R1', 'D1']

## M250-S230: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T8625 does not say when the further metal is added; the natural reading (before contact, at the hotter block's initial temperature) gives the certified answer, but adding it after contact had begun would change the entropy generated.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T33C5 and TFF07 omit the numerical mass and unit present in their twins, departing from the review instructions' uniform number-and-unit requirement, although the authors explicitly identify these as intentional numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite ['N0', 'D0', 'R1'], pending 0, slightly artificial ['D1', 'N1', 'R0']
  - REWRITE N0 (N): claude: Pouring metal at 360 K into a casting mould is incoherent, since a typical metal is solid at that temperature and cannot be poured.
  - REWRITE D0 (D): claude: Pouring metal at 360 K into a casting mould is implausible since the metal would be solid, and 'a further 1.1 kg' has no prior amount to add to.
  - REWRITE R1 (R): claude: Saying the 2 kg hotter block 'also includes a further 1.1 kg' contradicts its stated mass and is wording no one would use.

## M250-S231: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T7F76 specifies that the speed increment precedes recording, but does not establish that it precedes the relevant reflection or that it is additional to the stated recording-run speed of 3 m/s.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T7F76's pluperfect 'had added 1.4 m/s ... before the echo was recorded' only implicitly says the extra speed persists during the recording, and sits slightly against the base 'constant speed of 3 m/s'; the intended reading is clear enough.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T7F76 specifies that the speed increment precedes recording, but does not establish that it precedes the relevant reflection or that it is additional to the stated recording-run speed of 3 m/s.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R0', 'R1', 'D0', 'N1', 'N0']

## M250-S232: REJECT

- gpt: validity is invalid
- gpt: high flag other: Both K claims give sqrt(g*q) as an outside-regime reference expression, but this is not the finite-depth group speed for these gravity-capillary waves and requires additional shallow-water and negligible-capillarity assumptions.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T6703 and T14D0 omit the numerical reduction and its unit, violating the review instructions' requirement that same-quantity variants retain the same number and unit, although the packet explicitly identifies these omissions as intentional controls.
  - flag other (high): Both K claims give sqrt(g*q) as an outside-regime reference expression, but this is not the finite-depth group speed for these gravity-capillary waves and requires additional shallow-water and negligible-capillarity assumptions.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T6703 and T14D0 omit the numerical reduction and its unit, violating the review instructions' requirement that same-quantity variants retain the same number and unit, although the packet explicitly identifies these omissions as intentional controls.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'N1', 'D1', 'N0']

## M250-S233: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TBC5B and TAC23 do not establish whether the stated 5 mW is before or after boosting, so the authors' increased incident powers and certified transmitted powers are not uniquely determined.
- gpt: high flag other: The cancellation claims incorrectly equate transmitted beam irradiance to incident beam irradiance times 1-R while using the same perpendicular beam cross-sectional area on both sides of a refracting interface.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The cancellation relation 'transmitted intensity I_t = I0 (1 - R) per unit area of the beam' is loose, since the refracted beam's cross-section and the transmitted intensity differ from the incident ones; the power-transmittance result 1 - R and the cancellation of area are nonetheless correct.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): TBC5B and TAC23 do not establish whether the stated 5 mW is before or after boosting, so the authors' increased incident powers and certified transmitted powers are not uniquely determined.
  - flag other (high): The cancellation claims incorrectly equate transmitted beam irradiance to incident beam irradiance times 1-R while using the same perpendicular beam cross-sectional area on both sides of a refracting interface.
- naturalness: 8 sentences, rewrite ['D0', 'R0', 'N0'], pending 0, slightly artificial ['R1', 'D1', 'N1']
  - REWRITE D0 (D): claude: A 'booster' that adds power to an idle laser pointer shining away from the block is an implausible device and detail for this scene.
  - REWRITE R0 (R): claude: An unexplained "booster" adding power to a beam already specified as 5 mW is incoherent with the setup.
  - REWRITE N0 (N): claude: A 'booster' adding a little power to an idle laser pointer lying on the bench is not a real device and reads as incoherent.

## M250-S234: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: T2524 and TB902 specify a glass coupler without its refractive index or alignment, whereas the certified answers require a straight extension made of the same n=1.8 glass.
- gpt: high flag other: The authors incorrectly identify L tan(theta_r)/d as the literal number of zigzag legs and give q*ell/c as an outside-regime reference time even though q is the surrounding liquid's index, not the glass index.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The wiring assumes the coupler is 'of the same glass' and joins without an index step, but the R sentences say only 'a glass coupler'; the intended reading is natural, so this is a minor wording gap.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): T2524 and TB902 specify a glass coupler without its refractive index or alignment, whereas the certified answers require a straight extension made of the same n=1.8 glass.
  - flag other (high): The authors incorrectly identify L tan(theta_r)/d as the literal number of zigzag legs and give q*ell/c as an outside-regime reference time even though q is the surrounding liquid's index, not the glass index.
- naturalness: 10 sentences, rewrite ['D0', 'R0', 'N0'], pending 0, slightly artificial ['R1', 'D1', 'N1']
  - REWRITE D0 (D): claude: A coupler that adds 1.3 m to a coiled cable unrelated to the rod is an implausible, pointless detail in odd wording.
  - REWRITE R0 (R): claude: A coupler that adds 1.3 m to a rod already stated to be 2 m long contradicts the setup and is not a coherent object for this scene.
  - REWRITE N0 (N): claude: Saying a coupler 'adds a little to the length' of an unrelated coiled cable is odd, pointless wording no one would use.

## M250-S235: REJECT

- claude: validity is invalid
- claude: high flag invalid_parameter_domain: Every listed radius (2.5, 4.5, 7 cm) is far below the r > 20 cm needed (r^2 > 2 d0 (h - d0) = 0.041 m^2) for a 30 cm cylinder of relative density 0.65 to float upright stably, so the C sentences contradict the authors' own assumption that the cylinder floats upright and moves only vertically.
- gpt: validity is invalid
- gpt: high flag missing_assumption: T315E and T4379 specify the added wood's length and density but omit its cross-sectional area or mass, so treating the attachment as the substitution h -> h+q and certifying a unique modified period is unjustified.
- gpt: high flag other: The outside-regime reference expression 2*pi*sqrt((d0+q)/g) is incorrect: once the cylinder becomes fully submerged or emerges, the period requires piecewise constant-acceleration and harmonic-motion segments.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag invalid_parameter_domain (high): Every listed radius (2.5, 4.5, 7 cm) is far below the r > 20 cm needed (r^2 > 2 d0 (h - d0) = 0.041 m^2) for a 30 cm cylinder of relative density 0.65 to float upright stably, so the C sentences contradict the authors' own assumption that the cylinder floats upright and moves only vertically.
  - flag missing_assumption (medium): The cylinder is never called wooden, so 'the same wood' in T315E/T4379 may refer to the raft's wood of unstated density; the R answers silently assume density 650 kg/m^3.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): T315E and T4379 specify the added wood's length and density but omit its cross-sectional area or mass, so treating the attachment as the substitution h -> h+q and certifying a unique modified period is unjustified.
  - flag other (high): The outside-regime reference expression 2*pi*sqrt((d0+q)/g) is incorrect: once the cylinder becomes fully submerged or emerges, the period requires piecewise constant-acceleration and harmonic-motion segments.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["missing_assumption"], "gpt": []}
- naturalness: 10 sentences, rewrite ['R1', 'R0'], pending 0, slightly artificial ['D1', 'N0', 'D0']
  - REWRITE R1 (R): claude: Gluing extra wood onto the cylinder contradicts the stated uniform 30 cm cylinder, and 'the same wood' refers to no wood established for the cylinder.
  - REWRITE R0 (R): claude: It refers to 'the same wood' though the cylinder was never called wooden, and gluing on extra length contradicts the stated 30 cm cylinder.

## M250-S236: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TE665 establishes that the tube was attached before measurement but does not establish that it remained attached during measurement, so its certified answer requires an unstated configuration.
- gpt: high flag other: The outside-regime reference expression c/(4*q) is not generally the resonance frequency of a flask specified only by volume and longest dimension; it requires additional geometry and acoustic boundary conditions.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): TE665 ('had been attached ... before its resonance was measured') implies but does not state outright that the tube is still on the neck during the measurement.
  - flag invalid_parameter_domain (low): For air with c = 343 m/s, densities 0.8-2.1 kg/m^3 imply pressures of about 67-176 kPa via rho c^2 = gamma P, which is atypical for a flask open to room air; the answer is unaffected because density cancels.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): TE665 establishes that the tube was attached before measurement but does not establish that it remained attached during measurement, so its certified answer requires an unstated configuration.
  - flag other (high): The outside-regime reference expression c/(4*q) is not generally the resonance frequency of a flask specified only by volume and longest dimension; it requires additional geometry and acoustic boundary conditions.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'N0', 'C1', 'N1', 'C0', 'D0']

## M250-S237: REJECT

- gpt: validity is invalid
- gpt: high flag hidden_coupling: Dredging for an earlier survey can permanently alter the target slope, so the claimed absence of a causal path for TEB36 and TF161 is false.
- gpt: high flag missing_assumption: The slope-dredging sentences do not establish that the modified seabed remains linear across the full crossing, which is necessary for the certified endpoint-substitution answers.
- gpt: high flag insufficient_boundary_condition: The earlier-survey sentences do not specify restoration of the seabed before the tsunami, and TF161 also leaves the dredged depth unspecified.
- gpt: high flag invalid_parameter_domain: The outside-regime reference expression uses deep-water phase speed, but failure of q>20*h1 does not establish deep water; the supplied example q=2 km is outside that expression's domain on this shelf.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The R sentences do not say explicitly that the slope stays uniform after dredging the landward end to 93 m; the authors' linear-profile assumption is the natural reading given 'slopes uniformly', but a local-hole reading is possible.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag hidden_coupling (high): Dredging for an earlier survey can permanently alter the target slope, so the claimed absence of a causal path for TEB36 and TF161 is false.
  - flag missing_assumption (high): The slope-dredging sentences do not establish that the modified seabed remains linear across the full crossing, which is necessary for the certified endpoint-substitution answers.
  - flag insufficient_boundary_condition (high): The earlier-survey sentences do not specify restoration of the seabed before the tsunami, and TF161 also leaves the dredged depth unspecified.
  - flag invalid_parameter_domain (high): The outside-regime reference expression uses deep-water phase speed, but failure of q>20*h1 does not establish deep water; the supplied example q=2 km is outside that expression's domain on this shelf.
- pass-1 stratum differences (gpt, information only): TEB36 authors D judge R, TF161 authors N judge R
- naturalness: 8 sentences, rewrite ['R1', 'R0', 'D1'], pending 0, slightly artificial ['N1', 'D0']
  - REWRITE R1 (R): claude: Dredging 33 m of extra depth across the landward end of a continental shelf is an implausible event for this scene.
  - REWRITE R0 (R): claude: Dredging an extra 33 m of depth on an open continental shelf is an implausible event for this natural-seabed scene.
  - REWRITE D1 (D): claude: Dredging 33 m of open continental shelf 'for an earlier survey only' is an implausible, self-undoing event in this scene.

## M250-S238: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TEF4A does not establish whether the stated 120 rpm is before or after the earlier increase, so its certified measurement power is not uniquely determined.
- gpt: high flag missing_assumption: The rendered problem omits the Newtonian constitutive model and purely azimuthal flow condition required by the certified torque law, although the auxiliary assumptions supply them.
- gpt: high flag inconsistent_units: Both density cancellation claims give tau = q*nu*d(omega)/dr, which has units Pa/m for angular velocity omega; cylindrical shear requires tau = q*nu*r*d(omega)/dr.
- gpt: high flag other: The T2F2B claim identifies a vortex-free bound as a loss-of-laminarity threshold, although Taylor vortices can themselves be laminar.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The density cancellation is presented by writing eta = rho*nu with nu = eta/rho, a circular construction; the conclusion (density does not enter the laminar Couette torque) is correct, and the relation 'omega = rot' is shorthand for the stated rpm conversion.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): TEF4A does not establish whether the stated 120 rpm is before or after the earlier increase, so its certified measurement power is not uniquely determined.
  - flag missing_assumption (high): The rendered problem omits the Newtonian constitutive model and purely azimuthal flow condition required by the certified torque law, although the auxiliary assumptions supply them.
  - flag inconsistent_units (high): Both density cancellation claims give tau = q*nu*d(omega)/dr, which has units Pa/m for angular velocity omega; cylindrical shear requires tau = q*nu*r*d(omega)/dr.
  - flag other (high): The T2F2B claim identifies a vortex-free bound as a loss-of-laminarity threshold, although Taylor vortices can themselves be laminar.
- naturalness: 10 sentences, rewrite ['N0', 'R0', 'D0', 'N1', 'R1'], pending 0, slightly artificial ['D1']
  - REWRITE N0 (N): claude: A magnetic stirrer is driven entirely by its motor, so saying a motor 'adds a little to' its rotation rate is incoherent wording no one would use.
  - REWRITE R0 (R): claude: A motor 'adding 75 rpm' to a rotor already stated to turn at 120 rpm makes the described rotation rate self-contradictory and is wording no one would use.
  - REWRITE D0 (D): claude: A separate motor 'adding 75 rpm' to a bystander magnetic stirrer is an odd, pointless action in wording no one would use.
  - REWRITE N1 (N): claude: 'A motor had added a little to the rotation rate of the rotor for an earlier run only' is vague, awkward wording no one would naturally use.
  - REWRITE R1 (R): claude: Saying a motor added 75 rpm before the power was measured conflicts with the rotor being stated to turn at 120 rpm, making the situation incoherent.

## M250-S239: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The problem never identifies 24 μm as the thickness before polishing, so the authors' subtraction d-q is not uniquely warranted, particularly for the explicitly completed event in TC0D0.
- gpt: high flag hidden_coupling: Finite coherence generally affects interference visibility continuously, so the claimed exact independence throughout q > 10 Δn d does not follow from the stated physics.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T6887/TD658 are labelled with the quantity 'a thinning of the plate' although they describe a micrometer's measurement margin, and a 6.5 um measurement margin on the same 24 um plate sits a little awkwardly beside the precisely stated thickness; T8B20's present tense leaves the timing of the thinning slightly implicit.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The problem never identifies 24 μm as the thickness before polishing, so the authors' subtraction d-q is not uniquely warranted, particularly for the explicitly completed event in TC0D0.
  - flag hidden_coupling (high): Finite coherence generally affects interference visibility continuously, so the claimed exact independence throughout q > 10 Δn d does not follow from the stated physics.
- pass-1 stratum differences (gpt, information only): TC0D0 authors R judge D
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'D1', 'N1', 'N0']

## M250-S24: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The warming variants do not establish that the stated 600 K is the temperature before warming, rather than the operating temperature after the warming described as occurring before the first cycle.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag invalid_parameter_domain (medium): TC060 warms a kettle of water by 150 K (and the listed variant 250 K), which for liquid water at ordinary pressure would pass boiling; the D classification is unaffected but the scenario is physically odd.
  - flag other (low): T82B8's 'then' leaves the timing of the reservoir warming relative to the cycle mildly ambiguous (wiring assumes before the cycles), and the kettle sentences are labelled with quantity 'a temperature rise of the hot reservoir', a metadata mislabel.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The warming variants do not establish that the stated 600 K is the temperature before warming, rather than the operating temperature after the warming described as occurring before the first cycle.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["invalid_parameter_domain"], "gpt": []}
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['R0', 'N1', 'N0', 'R1', 'D1']
  - REWRITE D0 (D): claude: Warming a kettle of water by 150 K is physically implausible since the water would boil first.

## M250-S240: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The R sentences say only the siphon liquid is replaced; a reader could wonder whether the reservoir liquid is also replaced, though the intended (and natural) reading is that the flowing liquid is the new one throughout.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite ['D0', 'R1', 'N0'], pending 0, slightly artificial ['N1', 'D1']
  - REWRITE D0 (D): claude: Replacing the contents of a garden water butt with a 1180 kg/m³ liquid is an implausible, pointless action for that scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)
  - REWRITE R1 (R): claude: Saying the siphon liquid was replaced by a denser one contradicts the stated 1000 kg/m³ liquid filling the siphon.
  - REWRITE N0 (N): claude: Replacing the water in a garden water butt with a liquid of a different density is an implausible, pointless action for that object.

## M250-S241: REJECT

- claude: validity is invalid
- claude: high flag missing_assumption: TD93A and T22AD add 3.4 mW from a second/further lamp without stating its wavelength or photon-to-electron probability; the authors' wiring (P -> P + q at 400 nm and eta = 0.003) silently assumes the extra light is identical to the beam, so the R answers are not determined by the text.
- gpt: validity is invalid
- gpt: high flag missing_assumption: TD93A and T22AD omit the additional lamp's wavelength or spectrum and applicable release probability, so the authors' replacement of P by P + q and their unique certified currents require conditions absent from the rendered problem.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): TD93A and T22AD add 3.4 mW from a second/further lamp without stating its wavelength or photon-to-electron probability; the authors' wiring (P -> P + q at 400 nm and eta = 0.003) silently assumes the extra light is identical to the beam, so the R answers are not determined by the text.
  - flag invalid_numerical_precision (medium): With the stated hc = 1240 eV nm and e = 1.602e-19 C, e cancels and I = 0.003*5 mW/3.1 V = 4.83871 uA, but the certified answers (4.83818, 8.12814, 6.48316, 10.8375 uA) are smaller by the factor 1.602/1.602176634, i.e. they mix the CODATA e (for eV to J) with the stated e (for the charge); the certified values are off in the fourth significant figure.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): TD93A and T22AD omit the additional lamp's wavelength or spectrum and applicable release probability, so the authors' replacement of P by P + q and their unique certified currents require conditions absent from the rendered problem.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["invalid_numerical_precision"], "gpt": []}
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['D1', 'R0', 'N1', 'N0']
  - REWRITE D0 (D): claude: Shining a quantified 3.4 mW of extra light onto a meter dial that is a shielded readout is a pointless action stated in unnatural wording.

## M250-S242: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: The certified wiring for T45EB assumes the extra 170 Bq batch is 'added at the moment of preparation', but the sentence ('Another 170 Bq batch of the longer-lived isotope is added to the sample') states neither when it is added nor at what moment it has 170 Bq, and a later addition gives a different crossing time.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T45EB omits the addition time, whereas its wiring and certified answers require addition at preparation.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): The certified wiring for T45EB assumes the extra 170 Bq batch is 'added at the moment of preparation', but the sentence ('Another 170 Bq batch of the longer-lived isotope is added to the sample') states neither when it is added nor at what moment it has 170 Bq, and a later addition gives a different crossing time.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T45EB omits the addition time, whereas its wiring and certified answers require addition at preparation.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'D0', 'N1', 'R0']

## M250-S243: REJECT

- gpt: validity is invalid
- gpt: high flag invalid_parameter_domain: T69BD identifies q as a charge radius, conventionally an rms radius, but its claimed sufficient regime d > q does not ensure that the trajectory lies outside the charge distribution.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag invalid_numerical_precision (low): The certified 54.9159 fm appears to convert MeV to joules with the CODATA e (1.602176634e-19) while the problem tells the solver to take e = 1.602e-19 C; using the stated e throughout gives 54.922 fm, a 0.011% difference well within the precision of the inputs.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag invalid_parameter_domain (high): T69BD identifies q as a charge radius, conventionally an rms radius, but its claimed sufficient regime d > q does not ensure that the trajectory lies outside the charge distribution.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'D1', 'D0', 'N1', 'R1', 'N0']

## M250-S244: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Tense mismatch in TEB76/TB9B8 ('gave ... before it annihilates'), and the input K is the energy on leaving the source, with no energy loss before annihilation implied rather than stated (vacuum chamber, in-flight annihilation is the clear intended reading).
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N0', 'D1', 'N1', 'D0']

## M250-S245: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TC3E2 ('adds 0.011 eV to the kinetic energy of the atoms') leaves mildly open whether the stated 0.0763 eV already includes the increment; the natural reading (K + q) is the certified one.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- pass-1 stratum differences (claude, information only): T0167 authors K judge D, T866E authors K judge D, TAB0F authors C judge D, TF60D authors C judge D
- naturalness: 10 sentences, rewrite ['D0'], pending 0, slightly artificial ['N0', 'R0', 'R1', 'N1', 'D1']
  - REWRITE D0 (D): claude: A 'faster nozzle' adding a specific eV of kinetic energy to a wall-cooling helium jet is odd wording no one would use and an unmotivated event in this scene.

## M250-S246: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['R0', 'N0', 'R1', 'D1']
  - REWRITE N1 (N): claude: The phrase 'For an earlier shield only' is garbled and makes the extra concrete's relation to the present wall incoherent.

## M250-S247: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: TE4B6 and TFEB0 do not specify the added lamp's incidence angle or irradiance measurement convention, so its normal radiation force and the final speed are not uniquely determined.
- gpt: high flag relevant_variable_removed_from_equation: The authors replace I by I + q while omitting the added light's independent incidence angle, although that angle affects its contribution to the normal radiation force.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag missing_assumption (medium): The R wiring I -> I + q requires the second lamp's light to travel along the beam at 30 degrees with q measured perpendicular to that direction, which TE4B6 and TFEB0 do not state ('illumination onto the mirror' could also be read as irradiance on the mirror surface or light from another direction).
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): TE4B6 and TFEB0 do not specify the added lamp's incidence angle or irradiance measurement convention, so its normal radiation force and the final speed are not uniquely determined.
  - flag relevant_variable_removed_from_equation (high): The authors replace I by I + q while omitting the added light's independent incidence angle, although that angle affects its contribution to the normal radiation force.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["missing_assumption"], "gpt": []}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'D0', 'N1']

## M250-S248: REJECT

- claude: validity is invalid
- claude: high flag contradictory_distractor_statement: The base text says the field at the sample is a uniform, constant 350 mT and 'no other magnetic field acts there', but the R sentences T371E ('during this measurement') and TBE19 add a second coil's 52 mT at the sample, so the problem plus either sentence contradicts itself and the certified 17.11 MHz is only one of two defensible readings.
- gpt: validity is invalid
- gpt: high flag contradictory_distractor_statement: T371E and TBE19 introduce an additional magnetic field at the sample during the measurement, contradicting the base statement that the field there is 350 mT and no other magnetic field acts there.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag contradictory_distractor_statement (high): The base text says the field at the sample is a uniform, constant 350 mT and 'no other magnetic field acts there', but the R sentences T371E ('during this measurement') and TBE19 add a second coil's 52 mT at the sample, so the problem plus either sentence contradicts itself and the certified 17.11 MHz is only one of two defensible readings.
  - flag other (low): 'Frequency' admits the angular reading (rad/s), though cyclic MHz is conventional and is the target unit.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag contradictory_distractor_statement (high): T371E and TBE19 introduce an additional magnetic field at the sample during the measurement, contradicting the base statement that the field there is 350 mT and no other magnetic field acts there.
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['D0', 'N1', 'D1', 'N0']
  - REWRITE R1 (R): claude: Adding 52 mT at the sample contradicts the earlier statement that no other magnetic field acts there.

## M250-S249: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The claimed replacement K -> K + q requires 100 MeV to describe the energy before the additional gap, whereas both the problem and the authors' input description specify it as the energy at injection.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): The claimed replacement K -> K + q requires 100 MeV to describe the energy before the additional gap, whereas both the problem and the authors' input description specify it as the energy at injection.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D1', 'R0']

## M250-S25: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The K claims give the outside-regime energy L*q^2/2 without specifying the post-saturation flux-current relation needed to obtain that expression.
- gpt: high flag other: The cancellation derivation for T1C85 asserts emf = L*I/T and average current I/2, although that sentence does not specify the zero initial current required by those assertions.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): In TA5C2 the past-tense 'Before the energy was measured, a rheostat increased the current by 2.8 A' leaves slight room to read the stated 3 A as the post-increase current.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): The K claims give the outside-regime energy L*q^2/2 without specifying the post-saturation flux-current relation needed to obtain that expression.
  - flag other (high): The cancellation derivation for T1C85 asserts emf = L*I/T and average current I/2, although that sentence does not specify the zero initial current required by those assertions.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D0', 'N1', 'D1']

## M250-S250: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The C cancellation for the film distance is a round trip (compute the ring radius r = q tan 2theta, then recover theta = atan(r/q)/2) rather than a relation the target genuinely needs, and the film is not introduced in the base text; the physics stated is true, so this is a labelling/naturalness point, not an error.
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): TC57E and TE72A replace 8.4 keV with 'a little', contrary to the review's explicit requirement that variants concerning the same quantity preserve its number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TC57E and TE72A replace 8.4 keV with 'a little', contrary to the review's explicit requirement that variants concerning the same quantity preserve its number and unit.
- pass-1 stratum differences (claude, information only): T0D3D authors C judge D, T9FF8 authors C judge D
- pass-1 stratum differences (gpt, information only): T0D3D authors C judge D, T9FF8 authors C judge D
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D0', 'R0', 'D1']

## M250-S251: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T04BD supplies the further speed before firing but does not establish the intervening motion or whether the motor sets the stated final launch speed or adds a velocity increment, so its certified launch state and height are not uniquely determined.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Minor wording issues: 'it' in TFA02/T9D2A follows the balloon sentence (D either way), 'before the firing ... speed given to the probe' in T04BD is slightly odd, and a weather balloon on an airless moon is unnatural; none changes any answer.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T04BD supplies the further speed before firing but does not establish the intervening motion or whether the motor sets the stated final launch speed or adds a velocity increment, so its certified launch state and height are not uniquely determined.
- naturalness: 8 sentences, rewrite ['N0', 'R0', 'D0', 'R1'], pending 0, slightly artificial ['D1', 'N1']
  - REWRITE N0 (N): claude: A weather balloon on an airless moon being given upward speed is implausible and incoherent for the scene.
  - REWRITE R0 (R): claude: Giving the probe 'a further' upward speed before it is fired is incoherent wording for a launch from rest on the surface.
  - REWRITE D0 (D): claude: Giving a weather balloon 'a further 210 m/s of upward speed' on an airless moon is implausible and pointless.
  - REWRITE R1 (R): claude: Saying the probe is 'also given a further 210 m/s ... for one firing only' is incoherent alongside the stated launch speed and uses unnatural wording.

## M250-S252: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The explicitly designated numeral-free controls omit the mass number and unit present in their numeric twins, departing from the general same-number-and-unit instruction, although the authors correctly disclose this difference and do not claim these controls are numeric minimal pairs.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite ['D1'], pending 0, slightly artificial ['D0', 'R1', 'N1', 'N0']
  - REWRITE D1 (D): claude: An orbiting satellite having an 'earlier flight' with extra instruments 'for one flight only' is implausible, and 'it' ambiguously follows the recovery ship.

## M250-S253: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: T9B4F and TCC99 do not specify the additional field's frequency, relative phase or coherence, and incidence direction, so the authors' substitution Ii -> Ii + q and resulting pressure amplitudes are not generally justified.
- gpt: high flag insufficient_boundary_condition: TCC99 does not establish whether the additional sound overlaps the measured wave or has already passed, permitting materially different measured amplitudes.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The R wiring adds the further intensity to the incident wave's intensity, which presumes it is part of the same plane wave (or that a single pressure amplitude is defined for the combined field); the sentences do not say so.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): T9B4F and TCC99 do not specify the additional field's frequency, relative phase or coherence, and incidence direction, so the authors' substitution Ii -> Ii + q and resulting pressure amplitudes are not generally justified.
  - flag insufficient_boundary_condition (high): TCC99 does not establish whether the additional sound overlaps the measured wave or has already passed, permitting materially different measured amplitudes.
- naturalness: 8 sentences, rewrite ['N0', 'D0'], pending 0, slightly artificial ['R1', 'R0', 'D1', 'N1']
  - REWRITE N0 (N): claude: 'A further small amount of sound intensity falls on the boathouse wall' is wording no one would use and has no coherent role in the scene.
  - REWRITE D0 (D): claude: Saying a further 0.006 W/m² of sound intensity 'falls on the boathouse wall' is incoherent, unnatural wording for this scene.

## M250-S254: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: The siren is stated to be high above the ground on a tall mast, yet the observer's position is given only as a horizontal distance from the mast with no heights, so the source-observer path length is not determined.
- claude: high flag other: The authors' input r is explicitly 'distance of the observer from the mast' but is used as the radius of the spherical wavefront from the siren, which is valid only if the observer is level with the siren; the R wiring r -> r + q likewise adds horizontal distance to a slant distance.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The observer's distance from the mast does not determine the distance from the elevated siren, and increasing the former by q does not generally increase the acoustic path by q.
- gpt: high flag other: The claimed K classification, universal regime 5*q<r, and exterior intensity expression do not follow from the stipulated isotropic point-source model; a finite-mouth replacement requires additional source and radiation specifications.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): The siren is stated to be high above the ground on a tall mast, yet the observer's position is given only as a horizontal distance from the mast with no heights, so the source-observer path length is not determined.
  - flag other (high): The authors' input r is explicitly 'distance of the observer from the mast' but is used as the radius of the spherical wavefront from the siren, which is valid only if the observer is level with the siren; the R wiring r -> r + q likewise adds horizontal distance to a slant distance.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): The observer's distance from the mast does not determine the distance from the elevated siren, and increasing the former by q does not generally increase the acoustic path by q.
  - flag other (high): The claimed K classification, universal regime 5*q<r, and exterior intensity expression do not follow from the stipulated isotropic point-source model; a finite-mouth replacement requires additional source and radiation specifications.
- pass-1 stratum differences (gpt, information only): TA1FB authors K judge C, TDDF0 authors K judge C
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['D0', 'N0', 'D1', 'R1']
  - REWRITE N1 (N): claude: The phrase 'moved away from the mast by a modest distance more' is vague, unidiomatic wording that no one would use.

## M250-S255: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Which layer is on top is not stated, so only the magnitude of the vertical deflection is unique; also the numeral-free cable sentence TC665 is labelled with quantity 'a further length of strip' although it concerns cable, a cosmetic metadata mislabel.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (low): The numerical answers specify deflection magnitudes, but the question does not explicitly request a magnitude and does not specify which layer is uppermost.
- naturalness: 8 sentences, rewrite ['N0', 'D1', 'N1'], pending 0, slightly artificial ['D0', 'R0', 'R1']
  - REWRITE N0 (N): claude: Paying out an unrelated cable from a reel just before measuring the strip is a pointless action that does not belong in the experiment.
  - REWRITE D1 (D): claude: A clamp 'letting out' more strip, with an unexplained 'also' and an earlier experiment, is incoherent wording for this setup.
  - REWRITE N1 (N): claude: The phrasing 'the clamp also let out a modest length more of the strip' in an earlier experiment is unnatural wording that no one would use and has no clear place in the scene.

## M250-S256: REJECT

- gpt: validity is invalid
- gpt: high flag invalid_parameter_domain: The supplied outside-regime reference expression is the low-temperature Debye asymptote requiring temperatures much smaller than the Debye temperature, whereas the stated complement of T1 > 2q does not establish that condition.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): For TC49F, 'cast' suggests molten lead whose temperature is left implicit; the base statement that the block is at 300 K when heated covers it on the natural reading.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T85DA and TAA2E intentionally replace 0.18 kg with an unspecified small amount, violating the review instructions' requirement that same-quantity variants preserve the number and unit.
  - flag invalid_parameter_domain (high): The supplied outside-regime reference expression is the low-temperature Debye asymptote requiring temperatures much smaller than the Debye temperature, whereas the stated complement of T1 > 2q does not establish that condition.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T85DA and TAA2E intentionally replace 0.18 kg with an unspecified small amount, violating the review instructions' requirement that same-quantity variants preserve the number and unit.
- naturalness: 10 sentences, rewrite ['N0', 'N1', 'R0', 'R1', 'D0'], pending 0, slightly artificial ['D1']
  - REWRITE N0 (N): claude: Casting extra lead onto an unrelated hanging weight just before the heating is a pointless, implausible action in this scene.
  - REWRITE N1 (N): claude: The phrasing 'the block also included a further small amount of lead, for one heating only' is awkward wording no one would naturally use.
  - REWRITE R0 (R): claude: Casting molten lead onto a block stated to be at 300 K just before heating is self-contradictory and an implausible step.
  - REWRITE R1 (R): claude: A block that 'also includes a further 0.18 kg of lead, for one heating only' is incoherent wording that contradicts the stated mass of the block.
  - REWRITE D0 (D): claude: Casting more lead onto a weight hanging on a hook by the bench is an implausible, pointless action in this scene.

## M250-S257: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['R1'], pending 0, slightly artificial ['D0', 'N0', 'D1', 'N1', 'R0']
  - REWRITE R1 (R): claude: Loading an extra 1300 Bq 'for one run only' at the start conflicts with the stated loading and is incoherently worded.

## M250-S258: REJECT

- gpt: validity is invalid
- gpt: high flag contradictory_distractor_statement: T5915 and TA788 increase the completed source's initial isotope inventory to 0.0067 g, contradicting the base statement that it contains 0.004 g when made.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): With T5915 or TA788 added, the base statement 'When it is made it contains 0.004 g' sits awkwardly beside 'a further 0.0027 g ... goes into the source' at making; the intended additive reading (0.0067 g) is clear from 'further', so this is a wording tension, not a contradiction.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag contradictory_distractor_statement (high): T5915 and TA788 increase the completed source's initial isotope inventory to 0.0067 g, contradicting the base statement that it contains 0.004 g when made.
- naturalness: 6 sentences, rewrite ['R1', 'R0'], pending 0, slightly artificial ['N0']
  - REWRITE R1 (R): claude: Saying that a further 0.0027 g goes into the source when it is made contradicts the stated 0.004 g content at the time it is made.
  - REWRITE R0 (R): claude: Saying a further 0.0027 g is incorporated into the source contradicts the stated 0.004 g content when it is made.

## M250-S259: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: Only the initial gas temperature is specified; without the flask's initial thermal state or a thermal boundary condition, the equilibrium measurement temperature and hence the requested amount are not determined.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The C cancellation for pressure is constructed (n_d = p/kT multiplied in and divided out) rather than a relation the solution actually uses; pressure is better described as not entering the speed distribution at fixed n and T, but the invariance claim itself is true.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): Only the initial gas temperature is specified; without the flask's initial thermal state or a thermal boundary condition, the equilibrium measurement temperature and hence the requested amount are not determined.
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['D1', 'D0', 'N0', 'R1']
  - REWRITE N1 (N): claude: 'The sunlit flask was also a modest amount warmer than at the start' in an earlier experiment is muddled wording no one would use.

## M250-S260: REJECT

- gpt: validity is invalid
- gpt: high flag other: The width claims incorrectly invoke a transition to vbar/q when wall encounters become frequent, although the target explicitly excludes wall collisions and the equilibrium intermolecular collision frequency remains determined by density, temperature and molecular cross section.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T8E4F's 'for one run only' alongside 'Before the collisions are counted' is slightly awkward, though the intended reading (the counted run has p = 113 kPa) is the natural one.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The width claims incorrectly invoke a transition to vbar/q when wall encounters become frequent, although the target explicitly excludes wall collisions and the equilibrium intermolecular collision frequency remains determined by density, temperature and molecular cross section.
- naturalness: 10 sentences, rewrite ['R1'], pending 0, slightly artificial ['D1', 'N0', 'N1', 'D0']
  - REWRITE R1 (R): claude: Saying the vessel 'also holds a further 33 kPa ... for one run only' contradicts the stated 80 kPa state and the tense and scope are incoherent.

## M250-S261: REJECT

- gpt: validity is invalid
- gpt: high flag other: Both K claims give an unjustified outside-regime speed vt/(1 + 3*q/16), substituting a stipulated validity cutoff for the actual flow Reynolds number; a validity cutoff cannot determine the corrected physical drag or terminal speed.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): Both K claims give an unjustified outside-regime speed vt/(1 + 3*q/16), substituting a stipulated validity cutoff for the actual flow Reynolds number; a validity cutoff cannot determine the corrected physical drag or terminal speed.
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['D1', 'R0', 'N0', 'D0', 'N1']
  - REWRITE R1 (R): claude: Saying the sphere is loaded with extra shot at release 'for one release only' contradicts the stated total mass and is incoherent wording.

## M250-S262: ADMIT

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (low): TD265 keeps the phrase 'for one experiment only' while being certified R; the natural reading is that the asked draining is that experiment, but the phrase invites a D reading, and the K 'for_reference_only' expression tc*q/1000 is not a meaningful turbulent-regime formula (harmless, outside the certified claim).
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['R1', 'D1'], pending 0, slightly artificial ['R0', 'N1', 'N0']
  - REWRITE R1 (R): claude: Topping up the oil 'also' but 'for one experiment only' contradicts the stated initial depth and is phrased in wording no one would use.
  - REWRITE D1 (D): claude: The redundant 'in an earlier experiment ... for one experiment only' is wording no one would use and describes a pointless past action.

## M250-S263: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: No nonzero excitation across the bridge ends is specified, so zero galvanometer current need not establish the resistance ratio used to determine resistivity.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): No nonzero excitation across the bridge ends is specified, so zero galvanometer current need not establish the resistance ratio used to determine resistivity.
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['D1', 'N1', 'D0', 'C1', 'N0']
  - REWRITE R1 (R): claude: Saying the gap contains extra resistance when the null is found yet 'for one trial only' is muddled, self-contradictory wording for the described balance.

## M250-S264: REJECT

- claude: validity is invalid
- claude: high flag contradictory_distractor_statement: The problem declares the inductor ideal, but T282F/T9559 give it a 140 kHz self-resonance, which requires parasitic capacitance an ideal inductor does not have.
- gpt: validity is invalid
- gpt: high flag missing_assumption: T0B12 does not specify the added resistance's connection, although its claimed wiring and certified answers require series insertion into the measured RLC branch.
- gpt: high flag contradictory_distractor_statement: T282F and T9559 assign finite self-resonance to an explicitly ideal lumped inductor, which has no finite self-resonance.
- gpt: high flag hidden_coupling: If the inductor is instead interpreted physically, its self-resonant frequency can affect its impedance and the phase even when q > 10*f, so that inequality establishes no exact invariance.
- gpt: high flag other: Both K claims give an outside-regime reference expression that substitutes the inductor's self-resonant frequency for the source frequency, which is physically incorrect.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag contradictory_distractor_statement (high): The problem declares the inductor ideal, but T282F/T9559 give it a 140 kHz self-resonance, which requires parasitic capacitance an ideal inductor does not have.
  - flag other (medium): The K regime's out-of-regime 'reference expression' substitutes the self-resonant frequency q for the operating frequency in atan((2 pi q L - 1/(2 pi q C))/R), which is not the physics of self-resonance (effective inductance L/(1-(f/q)^2)); the threshold q > 10 f is also loose (about 1 percent change in X_L, ~0.9 deg at q = 10 f), though all listed values are far inside.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): T0B12 does not specify the added resistance's connection, although its claimed wiring and certified answers require series insertion into the measured RLC branch.
  - flag contradictory_distractor_statement (high): T282F and T9559 assign finite self-resonance to an explicitly ideal lumped inductor, which has no finite self-resonance.
  - flag hidden_coupling (high): If the inductor is instead interpreted physically, its self-resonant frequency can affect its impedance and the phase even when q > 10*f, so that inequality establishes no exact invariance.
  - flag other (high): Both K claims give an outside-regime reference expression that substitutes the inductor's self-resonant frequency for the source frequency, which is physically incorrect.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D1', 'D0', 'R1', 'N1']

## M250-S265: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['R0', 'D0', 'N0', 'D1', 'R1']
  - REWRITE N1 (N): claude: "Higher by a further small amount" refers to no prior change and is wording no one would use.

## M250-S266: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: TEC29 and TD2EC specify the additional load's real power without specifying its power factor or that it is resistive, so their winding losses are not uniquely determined.
- gpt: high flag relevant_variable_removed_from_equation: The claimed substitution Is = (P+q)/Vs omits the additional load's possible reactive power, which affects both rms winding currents and their heating.
- gpt: high flag other: The outside-regime reference expression Ploss*(1+q^2) is not a saturation law derivable from the supplied model; predicting saturation losses requires additional magnetic and excitation information.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag missing_assumption (medium): The R sentences do not say the extra 140 W is drawn at the same 24 V, which the authors' wiring assumes; with a fixed primary supply the voltage would sag slightly, a small effect.
  - flag other (low): The K threshold q < 0.8 and the reference expression Ploss*(1+q^2) are arbitrary modelling choices, not derived physics, though they are marked reference-only and every listed value (0.42-0.68) is plausibly in the linear regime.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): TEC29 and TD2EC specify the additional load's real power without specifying its power factor or that it is resistive, so their winding losses are not uniquely determined.
  - flag relevant_variable_removed_from_equation (high): The claimed substitution Is = (P+q)/Vs omits the additional load's possible reactive power, which affects both rms winding currents and their heating.
  - flag other (high): The outside-regime reference expression Ploss*(1+q^2) is not a saturation law derivable from the supplied model; predicting saturation losses requires additional magnetic and excitation information.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["missing_assumption"], "gpt": []}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'R1', 'R0', 'D0', 'D1']

## M250-S267: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['D1', 'D0', 'N1', 'N0']
  - REWRITE R1 (R): claude: Adding extra parallel capacitance 'for one run only' in a single described run is incoherent and clashes with the stated 22 μF capacitor.

## M250-S268: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: T000E and T0F51 omit the additional source's polarity, although the certified answers require an aiding source with total emf V + q.
- gpt: high flag insufficient_boundary_condition: T0F51 does not establish that steady state is reached after inserting the additional source, so the current at opening depends on the unspecified insertion time.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (low): T000E ends 'for one run only' while saying the emf is present before the switch opens in the stated run; the R reading is the natural one but the trailing phrase invites a reader to wonder whether the extra emf belongs to another run.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): T000E and T0F51 omit the additional source's polarity, although the certified answers require an aiding source with total emf V + q.
  - flag insufficient_boundary_condition (high): T0F51 does not establish that steady state is reached after inserting the additional source, so the current at opening depends on the unspecified insertion time.
- naturalness: 8 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['R0', 'R1', 'D1', 'N1']
  - REWRITE D0 (D): claude: Inserting an extra 7.5 V of emf in series with an unrelated doorbell is a pointless action with odd wording.
  - REWRITE N0 (N): claude: 'A further small amount of emf is inserted in series with the doorbell' is wording no one would use and an odd, pointless action in this scene.

## M250-S269: REJECT

- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: The R claims for T9D97 and TFAFF replace the explicitly stated 440 Hz tuning frequency with 440 + q, although the added sentences place the adjustment before tuning and do not replace that tuning condition.
- gpt: high flag other: The out-of-regime reference expression c2/(4q) − f incorrectly substitutes displacement amplitude for effective pipe length; nonlinear acoustics does not imply this relation.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The R sentences ('before the pipe is tuned, the fork is pitched higher by a further 62 Hz') sit awkwardly beside the base text's 'exactly the frequency 440 Hz of a tuning fork'; read as an intervention on the fork it is consistent, but the wording is slightly artificial.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): The R claims for T9D97 and TFAFF replace the explicitly stated 440 Hz tuning frequency with 440 + q, although the added sentences place the adjustment before tuning and do not replace that tuning condition.
  - flag other (high): The out-of-regime reference expression c2/(4q) − f incorrectly substitutes displacement amplitude for effective pipe length; nonlinear acoustics does not imply this relation.
- pass-1 stratum differences (gpt, information only): T9D97 authors R judge D, TFAFF authors R judge D
- naturalness: 10 sentences, rewrite ['R1', 'D0', 'R0'], pending 0, slightly artificial ['D1', 'N0', 'N1']
  - REWRITE R1 (R): claude: Repitching a tuning fork by 62 Hz is implausible and contradicts the fork being stated to sound exactly 440 Hz.
  - REWRITE D0 (D): claude: Raising a leaning guitar's string 'by a further 62 Hz' has no antecedent and is a pointless, oddly worded action in this scene.
  - REWRITE R0 (R): claude: Raising a tuning fork's pitch by 'a further 62 Hz' is implausible and conflicts with the fork being stated to have exactly 440 Hz.

## M250-S270: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TA0C8 and TBF04 do not specify whether the received reflection was emitted before or after the frequency increase, so replacing f by f+q does not establish a unique answer.
- gpt: high flag contradictory_distractor_statement: TBF04 states that the siren note is 410 Hz higher during reception despite the base description specifying a steady 1500 Hz note.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TBF04/TA0C8 change the note near the time of pickup, which strictly admits a transient reading (crests picked up just after the change were emitted at the old pitch), though the intended steady reading is clear.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): TA0C8 and TBF04 do not specify whether the received reflection was emitted before or after the frequency increase, so replacing f by f+q does not establish a unique answer.
  - flag contradictory_distractor_statement (high): TBF04 states that the siren note is 410 Hz higher during reception despite the base description specifying a steady 1500 Hz note.
- pass-1 stratum differences (claude, information only): T6307 authors C judge D, TDC03 authors C judge D
- naturalness: 8 sentences, rewrite ['N1', 'N0', 'R0', 'D0', 'R1'], pending 0, slightly artificial ['D1']
  - REWRITE N1 (N): claude: 'Higher by a further small amount' in an earlier experiment is vague, refers to no prior change, and is wording no one would use.
  - REWRITE N0 (N): claude: Raising the busker's violin pitch 'by a further small amount' timed to the reflected sound is a pointless, contrived event with an unexplained 'further'.
  - REWRITE R0 (R): claude: Raising the pitch by a further 410 Hz mid-measurement contradicts the siren's stated steady note and makes the scene incoherent.
  - REWRITE D0 (D): claude: Raising a busker's violin pitch by 'a further 410 Hz' timed to the reflected sound is a pointless, oddly specified event with an unexplained 'further'.
  - REWRITE R1 (R): claude: A "further" 410 Hz rise contradicts the steady note and refers to no prior change, so it is incoherent.

## M250-S271: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The extension sentences specify the same metal but do not specify a matching cross-section, which is necessary for the claimed uniform-rod frequency after welding.
- gpt: high flag inconsistent_units: Both cancellation claims incorrectly identify Yq as stiffness per unit length: for area q, Yq has units of force and is axial rigidity, whereas a segment's axial spring stiffness is Yq divided by its length.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T3295 ('When the clamp is fitted ... for one experiment only') is awkwardly worded and the K regime's 'reference expression: q' is a vacuous placeholder; neither changes any answer.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): The extension sentences specify the same metal but do not specify a matching cross-section, which is necessary for the claimed uniform-rod frequency after welding.
  - flag inconsistent_units (high): Both cancellation claims incorrectly identify Yq as stiffness per unit length: for area q, Yq has units of force and is axial rigidity, whereas a segment's axial spring stiffness is Yq divided by its length.
  - flag rendering_not_minimal (high): TFBD6 and TFE55 replace 32 cm with an unspecified small amount, violating the review instructions' requirement that quantity variants preserve the number and unit, despite being deliberately designated numeral-free controls.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TFBD6 and TFE55 replace 32 cm with an unspecified small amount, violating the review instructions' requirement that quantity variants preserve the number and unit, despite being deliberately designated numeral-free controls.
- pass-1 stratum differences (claude, information only): T94AF authors K judge C, T9574 authors K judge C
- pass-1 stratum differences (gpt, information only): T94AF authors K judge C, T9574 authors K judge C
- naturalness: 10 sentences, rewrite ['D0', 'N0', 'R1', 'D1'], pending 0, slightly artificial ['K1', 'N1', 'R0']
  - REWRITE D0 (D): claude: Welding 'a further' 32 cm of metal onto a wall railing before fitting the clamp is a pointless action that does not belong in a Kundt's tube scene.
  - REWRITE N0 (N): claude: Welding metal onto the laboratory railing before fitting the rod's clamp is a pointless action unconnected to the experiment.
  - REWRITE R1 (R): claude: Welding 32 cm onto the rod 'when the clamp is fitted ... for one experiment only' is incoherent with the stated rod and unnaturally worded.
  - REWRITE D1 (D): claude: The redundant 'in an earlier experiment ... for one experiment only' phrasing is wording no one would use.

## M250-S272: REJECT

- claude: validity is invalid
- claude: high flag other: The C cancellation relations for TBEDA/TFF60 state that the air column length is q - vw t and resonates at 5 lam/4 then 3 lam/4, i.e. that the column shortens as the water falls; in fact the column between the open top and a falling water surface lengthens (L = q + vw t), and from 130 cm the next resonances are at 9 lam/4 and 11 lam/4 (less end correction), so the shown relation is physically false even though the cancelled answer is right.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T9749 specifies an increased speed before the first resonance without specifying its continuation afterward, so its certified interval is not uniquely determined.
- gpt: high flag other: The cancellation claims incorrectly make the air column shrink as the water falls, and the radius claims assert conditional dependence and an outside-regime expression that do not follow from the stipulated fixed-end-correction resonance model.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The C cancellation relations for TBEDA/TFF60 state that the air column length is q - vw t and resonates at 5 lam/4 then 3 lam/4, i.e. that the column shortens as the water falls; in fact the column between the open top and a falling water surface lengthens (L = q + vw t), and from 130 cm the next resonances are at 9 lam/4 and 11 lam/4 (less end correction), so the shown relation is physically false even though the cancelled answer is right.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): T9749 specifies an increased speed before the first resonance without specifying its continuation afterward, so its certified interval is not uniquely determined.
  - flag rendering_not_minimal (high): T3D7A and TB8E5 omit the number and unit present in their numerical twins, contrary to the review instructions' requirement that same-quantity variants preserve the number and unit, although the packet explicitly identifies these omissions as intentional controls.
  - flag other (high): The cancellation claims incorrectly make the air column shrink as the water falls, and the radius claims assert conditional dependence and an outside-regime expression that do not follow from the stipulated fixed-end-correction resonance model.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T3D7A and TB8E5 omit the number and unit present in their numerical twins, contrary to the review instructions' requirement that same-quantity variants preserve the number and unit, although the packet explicitly identifies these omissions as intentional controls.
- pass-1 stratum differences (claude, information only): T0685 authors K judge C, T0899 authors K judge C
- pass-1 stratum differences (gpt, information only): T0685 authors K judge C, T0899 authors K judge C, T9749 authors R judge D
- naturalness: 10 sentences, rewrite ['N0', 'D0', 'R0', 'R1'], pending 0, slightly artificial ['N1', 'D1']
  - REWRITE N0 (N): claude: 'Drawn down at a rate raised by a further small amount' is garbled wording that no one would use, tying the pond to the tube's resonance timing for no reason.
  - REWRITE D0 (D): claude: Drawing down an unrelated garden pond 'at a rate raised by a further 0.9 cm/s' before a resonance is heard is an out-of-place event in wording no one would use.
  - REWRITE R0 (R): claude: The phrase 'drawn down at a rate raised by a further 0.9 cm/s' is convoluted wording and conflicts with the stated constant fall rate.
  - REWRITE R1 (R): claude: The sentence contradicts the stated constant 1.5 cm/s fall rate, making the scenario self-contradictory.

## M250-S273: REJECT

- gpt: validity is invalid
- gpt: high flag other: The claimed outside-regime reference expression substitutes the nuclear radius for the Bohr orbital radius without physical justification; failure of 10*q < r does not itself change the binding energy.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The nuclear radii 1.9-2.5 fm are unrealistic for a Z=1, 1836.15 m_e nucleus (a proton, ~0.84 fm), and the out-of-regime reference expression hc/(K + Z ke2/(2q)) is not the correct finite-size physics; neither affects the certified in-regime answers.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T2E00 and T4CEB omit the 116 eV in their quantitative twins, contrary to the review instructions' same-number-and-unit requirement, even though the authors disclose this deliberate control design.
  - flag other (high): The claimed outside-regime reference expression substitutes the nuclear radius for the Bohr orbital radius without physical justification; failure of 10*q < r does not itself change the binding energy.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T2E00 and T4CEB omit the 116 eV in their quantitative twins, contrary to the review instructions' same-number-and-unit requirement, even though the authors disclose this deliberate control design.
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['K0', 'N0', 'R1', 'D1', 'R0', 'D0']
  - REWRITE N1 (N): claude: An 'earlier capture' of the single muon being captured is incoherent, and the accelerating-gap wording is contrived.

## M250-S274: REJECT

- gpt: validity is invalid
- gpt: high flag other: The alkali principal-doublet P3/2 to S1/2 transition is the shorter-wavelength member, contradicting its identification as the longer-wavelength member.
- gpt: high flag inconsistent_units: The supplied relations produce Eb and dE in joules but divide by hc specified in eV nm, omitting the joule-to-electronvolt conversion and the final conversion to pm.
- gpt: high flag hidden_coupling: A coil producing a field at the compass can also produce a field at the vapour, so the claimed absence of a causal path does not follow from the sentences or the compass location.
- gpt: high flag missing_assumption: The compass-coil variants require an explicit condition that the coil's additional field at the vapour is negligible at the required precision.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The fine-structure values (0.0018-0.004 eV) do not match the real 589 nm sodium doublet (~0.0021 eV is within range, 0.0036 eV shown is not), and a coil adding field 'at the compass' is physically plausible to also leak some field to the vapour; neither alters the answer as the sentences are worded.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The alkali principal-doublet P3/2 to S1/2 transition is the shorter-wavelength member, contradicting its identification as the longer-wavelength member.
  - flag inconsistent_units (high): The supplied relations produce Eb and dE in joules but divide by hc specified in eV nm, omitting the joule-to-electronvolt conversion and the final conversion to pm.
  - flag hidden_coupling (high): A coil producing a field at the compass can also produce a field at the vapour, so the claimed absence of a causal path does not follow from the sentences or the compass location.
  - flag missing_assumption (high): The compass-coil variants require an explicit condition that the coil's additional field at the vapour is negligible at the required precision.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'R1', 'D0', 'D1', 'N0']

## M250-S275: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: T3E63 does not say at which edge the slice is widened; the certified answers (0.350678, 0.359585, 0.476585) assume the right edge with the left edge fixed at 0.6 nm, but widening at the left edge or symmetrically gives different probabilities (q = 0.24: 0.4594 left, 0.4137 symmetric), so the answer is not unique.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T3E63 specifies the increase in slice width without identifying which edge remains fixed, so its certified probabilities require an unstated choice of the final interval.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T3E63 does not say at which edge the slice is widened; the certified answers (0.350678, 0.359585, 0.476585) assume the right edge with the left edge fixed at 0.6 nm, but widening at the left edge or symmetrically gives different probabilities (q = 0.24: 0.4594 left, 0.4137 symmetric), so the answer is not unique.
  - flag other (low): 'The coating ... is widened' is an odd way to say thickened, and the base text introduces 'a second chip' with no first chip mentioned; wording only.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T3E63 specifies the increase in slice width without identifying which edge remains fixed, so its certified probabilities require an unstated choice of the final interval.
- naturalness: 6 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'R1', 'D1', 'R0', 'N1']
  - REWRITE N0 (N): claude: Widening a coating 'by a little more' on an unrelated chip is a pointless action in wording no one would use.

## M250-S276: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The thermal sentences do not specify how thermal motion relates to the prescribed incident kinetic energy or provide the energy distribution needed to calculate averaged transmitted currents.
- gpt: high flag hidden_coupling: The claimed exact thermal invariance under 8*q < V has no basis in the transmission law: thermal changes to incident normal energies change the exponentially energy-dependent transmissions even within that inequality.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The K regime predicate '8*q < V' is an unexplained heuristic threshold and the out-of-regime 'reference expression' sqrt(md/mp) has no evident physical meaning as a current ratio; both are outside the certified in-regime claim, which holds.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): The thermal sentences do not specify how thermal motion relates to the prescribed incident kinetic energy or provide the energy distribution needed to calculate averaged transmitted currents.
  - flag hidden_coupling (high): The claimed exact thermal invariance under 8*q < V has no basis in the transmission law: thermal changes to incident normal energies change the exponentially energy-dependent transmissions even within that inequality.
- pass-1 stratum differences (gpt, information only): T2708 authors K judge R, TAEE0 authors K judge R
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'K0', 'N1', 'N0', 'R0']

## M250-S277: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['D0', 'N0', 'R0'], pending 0, slightly artificial ['D1', 'N1', 'R1']
  - REWRITE D0 (D): claude: The cooling line abruptly 'getting 34 m more pipe' is pointless in this scene and phrased in wording no one would use.
  - REWRITE N0 (N): claude: 'The cooling-water line gets a little more pipe' is vague, pointless and phrased in a way no one would write.
  - REWRITE R0 (R): claude: 'The flight path of the pions gets 34 m more pipe' is wording no one would use and sits oddly against the stated 100 m tube.

## M250-S278: REJECT

- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: The certified base and sentence answers do not follow from the supplied relations and inputs, with discrepancies exceeding rounding to their displayed 0.001 MeV precision.
- gpt: high flag other: TCCEF does not specify the reference for 'more rest energy', so the authors' asserted increment Q → Q + q is not uniquely established by the sentence.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag invalid_numerical_precision (low): The certified answers (279.669, 508.394 MeV) follow from Q = 134.98 MeV, not the displayed 135 MeV, which gives 279.712 and 508.44 MeV; the 0.015% gap is within the precision of the displayed 135 MeV.
  - flag other (medium): TCCEF ('in this reaction, the final particles carry 104 MeV more rest energy') can also be read as an excess of 104 MeV, which would contradict the stated 135 MeV. Separately, the D rationale for TE22F/TB459 speaks of a particle created at the second station, while the sentences speak of that station's beam energy; D still holds.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): The certified base and sentence answers do not follow from the supplied relations and inputs, with discrepancies exceeding rounding to their displayed 0.001 MeV precision.
  - flag other (high): TCCEF does not specify the reference for 'more rest energy', so the authors' asserted increment Q → Q + q is not uniquely established by the sentence.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite ['D0', 'D1', 'R0', 'N0', 'R1'], pending 0, slightly artificial ['N1']
  - REWRITE D0 (D): claude: The phrase "gets 104 MeV more" has no stated reference, so the sentence is vague and worded in a way no one would write.
  - REWRITE D1 (D): claude: Saying the final particles 'carried 104 MeV more rest energy' in an earlier reaction only is odd, unexplained wording that no one would use for a threshold reaction.
  - REWRITE R0 (R): claude: 'The rest energy of the final particles gets 104 MeV more' is incoherent wording no physicist would use and conflicts with the stated reaction.
  - REWRITE N0 (N): claude: The phrasing 'gets a little more' is ungrammatical and vague, wording no one would use.
  - REWRITE R1 (R): claude: The sentence contradicts the earlier statement that the excess rest energy is 135 MeV, making the description self-contradictory.

## M250-S279: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Wording 'has grown by 3.7 cm more in rim radius' and 'gets 3.7 cm more' is awkward, and the problem says 'leading order in v/c' where the first nonvanishing order is (v/c)^2; both are wording issues only.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['D1', 'R1', 'D0', 'N1', 'R0', 'N0'], pending 0, slightly artificial none
  - REWRITE D1 (D): claude: A rotor that 'had grown by 3.7 cm more in rim radius' for an earlier run only is incoherent wording describing an implausible event.
  - REWRITE R1 (R): claude: A rigid rotor 'growing by 3.7 cm more in rim radius' is incoherent wording and an implausible event.
  - REWRITE D0 (D): claude: The pulley radius that 'gets 3.7 cm more' is ungrammatical wording and a pointless, unexplained change to a bystander pump.
  - REWRITE N1 (N): claude: A rotor that 'had grown by a little more in rim radius' for an earlier run is incoherent wording no one would use.
  - REWRITE R0 (R): claude: 'The radius ... gets 3.7 cm more' is ungrammatical wording no one would use, and changing a spinning rotor's radius is not a coherent event here.
  - REWRITE N0 (N): claude: 'The radius of the pulley of the vacuum pump gets a little more' is ungrammatical wording describing a pointless, vague change.

## M250-S28: REJECT

- gpt: validity is invalid
- gpt: high flag contradictory_distractor_statement: T56E0 and T5651 impose a speed cap reached before catch-up, contradicting the stated constant acceleration unless that acceleration law is explicitly qualified.
- gpt: high flag missing_assumption: TE8F1 and TEA52 do not establish whether the stated running acceleration of 2 m/s² excludes or already includes the kit's contribution, so the certified modified answers require an unstated interpretation.
- gpt: high flag other: The authors' first assumption incorrectly says the initially stationary car passes the truck at launch, whereas the problem states that the moving truck passes the stationary car.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): The base text states the car 'accelerates at a constant 2 m/s^2', so the R kit sentences (especially TE8F1, 'Before the start, a tuning kit added ...') admit a reading in which 2 m/s^2 is already the kit-inclusive acceleration (answer 15 s) rather than 3.3 m/s^2 (9.09 s).
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag contradictory_distractor_statement (high): T56E0 and T5651 impose a speed cap reached before catch-up, contradicting the stated constant acceleration unless that acceleration law is explicitly qualified.
  - flag missing_assumption (high): TE8F1 and TEA52 do not establish whether the stated running acceleration of 2 m/s² excludes or already includes the kit's contribution, so the certified modified answers require an unstated interpretation.
  - flag other (high): The authors' first assumption incorrectly says the initially stationary car passes the truck at launch, whereas the problem states that the moving truck passes the stationary car.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 10 sentences, rewrite ['R1'], pending 0, slightly artificial ['N1', 'R0', 'D1', 'N0', 'D0']
  - REWRITE R1 (R): claude: A tuning kit 'adding 1.3 m/s^2' to an acceleration already stated as a constant 2 m/s^2 is confusing, near self-contradictory wording no one would use.

## M250-S280: REJECT

- gpt: validity is invalid
- gpt: high flag other: The K claims present dv + v1**2/r1*q as an outside-regime reference expression, but finite-duration orbital burns have no universal additive correction equal to initial gravitational acceleration times burn duration.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The K claims present dv + v1**2/r1*q as an outside-regime reference expression, but finite-duration orbital burns have no universal additive correction equal to initial gravitational acceleration times burn duration.
- naturalness: 10 sentences, rewrite ['R1', 'N0', 'D0', 'R0'], pending 0, slightly artificial ['D1', 'N1', 'C1']
  - REWRITE R1 (R): claude: An orbit being 'placed 470 km higher still' is wording no one would use and contradicts the altitude already given for the initial orbit.
  - REWRITE N0 (N): claude: The vague phrase 'gets a little more' about the relay satellite's altitude is wording no one would use and has no coherent role in the scene.
  - REWRITE D0 (D): claude: "Gets 470 km more" is ungrammatical and the unexplained change in a bystander satellite's altitude is incoherent.
  - REWRITE R0 (R): claude: The ungrammatical 'gets 470 km more' contradicts the stated initial altitude and is wording no one would use.

## M250-S281: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag invalid_numerical_precision (low): Earth's stated radius and density with G = 6.674e-11 give 11.18 km/s, not the stated 11.19 km/s; the certified answers follow the stated 11.19 consistently, so the effect is a 0.07% difference from a direct G calculation.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['R0', 'R1', 'N0', 'D0'], pending 0, slightly artificial ['D1', 'N1']
  - REWRITE R0 (R): claude: A rock layer adding 310 km to a planet's radius is physically implausible and conflicts with the radius just given.
  - REWRITE R1 (R): claude: Giving a planet 310 km more radius of rock is physically impossible as an event and contradicts the stated radius.
  - REWRITE N0 (N): claude: A layer of rock being added to a moon's radius is not a plausible event or ordinary description of a moon.
  - REWRITE D0 (D): claude: A layer of rock being added to a moon's radius is an implausible event phrased in wording no one would use.

## M250-S282: REJECT

- gpt: validity is invalid
- gpt: high flag other: Both numeral-free twin_note claims falsely state that the number and unit were replaced by a nonnumeric phrase: the actual sentences replace only the number and retain 'in solar radii'.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): Wording 'gets 0.74 more, in solar radii' / 'swollen by 0.74 more' is awkward, though the intended additive reading is clear enough.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): Both numeral-free twin_note claims falsely state that the number and unit were replaced by a nonnumeric phrase: the actual sentences replace only the number and retain 'in solar radii'.
- naturalness: 6 sentences, rewrite ['D1', 'N0', 'D0', 'R1', 'R0', 'N1'], pending 0, slightly artificial none
  - REWRITE D1 (D): claude: The phrasing 'swollen by 0.74 more, in solar radii' is wording no one would use, and a star changing radius between observations is an odd, contrived detail.
  - REWRITE N0 (N): claude: 'The radius of the dust disc rim gets a little more, in solar radii' is incoherent wording that no one would use.
  - REWRITE D0 (D): claude: "Gets 0.74 more, in solar radii" is ungrammatical and a dust disc rim suddenly growing is implausible.
  - REWRITE R1 (R): claude: A star swelling 'by 0.74 more, in solar radii' just before its luminosity is evaluated is implausible and awkwardly worded.
  - REWRITE R0 (R): claude: The phrasing 'gets 0.74 more, in solar radii' is wording no one would use, and an abrupt change in the star's radius conflicts with the radius already given.
  - REWRITE N1 (N): claude: 'Swollen by a little more, in solar radii' for an earlier observation is vague, garbled wording that no one would use.

## M250-S29: ADMIT

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag missing_assumption (medium): The R sentences do not say the tension (40 N) and speed (3 m/s) are unchanged after the rope is tilted; the authors' wiring assumes so, which is the literal reading, but physically a sled held at constant speed against friction would generally need a different tension at 47 degrees.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["missing_assumption"], "gpt": []}
- naturalness: 10 sentences, rewrite ['D0'], pending 0, slightly artificial ['D1', 'N0', 'R1', 'N1', 'R0']
  - REWRITE D0 (D): claude: Tilting the jib of an unrelated crane beside a sled being pulled is a pointless action that does not belong in this scene.

## M250-S31: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: T1E37 ('The thrower then climbs onto a platform 14 m above the cliff edge'), appended after the throw has been described, most naturally places the climb after the throw (exactly as 'The surveyor then climbs' in its minimal pair T4ABD is read), so it does not fix that the stone is launched from the platform and the certified R answer 39.51 m is not uniquely determined; the D answer 30.30 m is equally or more defensible.
- gpt: validity is invalid
- gpt: high flag other: The R classifications, launch-height wiring and certified answers for T1E37 and TA432 incorrectly infer a launch from the platform, although neither sentence replaces the explicitly stated launch from the cliff edge.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T1E37 ('The thrower then climbs onto a platform 14 m above the cliff edge'), appended after the throw has been described, most naturally places the climb after the throw (exactly as 'The surveyor then climbs' in its minimal pair T4ABD is read), so it does not fix that the stone is launched from the platform and the certified R answer 39.51 m is not uniquely determined; the D answer 30.30 m is equally or more defensible.
  - flag contradictory_distractor_statement (medium): The R sentences require a launch 14 m above the cliff edge, while the problem says the stone is thrown from the edge of a cliff 20 m above the ground; for TA432 the launch from the platform is only implied (the thrower climbed up before the throw), so the tension is real but mild.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The R classifications, launch-height wiring and certified answers for T1E37 and TA432 incorrectly infer a launch from the platform, although neither sentence replaces the explicitly stated launch from the cliff edge.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["contradictory_distractor_statement"], "gpt": []}
- pass-1 stratum differences (claude, information only): T1E37 authors R judge D
- pass-1 stratum differences (gpt, information only): T1E37 authors R judge D, TA432 authors R judge D
- naturalness: 8 sentences, rewrite ['R0', 'N1'], pending 0, slightly artificial ['N0', 'D1', 'D0', 'C1', 'R1']
  - REWRITE R0 (R): claude: The thrower climbing onto a 14 m platform above the cliff edge after the throw is a pointless, implausible action in this scene.
  - REWRITE N1 (N): claude: Mentioning that the thrower climbed a platform 'in an earlier experiment' is a pointless aside about a past event that does not belong in this scene.

## M250-S32: REJECT

- gpt: validity is invalid
- gpt: high flag rendering_not_minimal: The numeral-free controls omit the mass and unit retained in their numbered twins, contrary to the review instructions' requirement that quantity variants preserve the same number and unit, although the packet explicitly identifies this difference as intentional.
- gpt: high flag other: The outside-regime reference expression k*q^2/(2*mu*m*g) does not follow from a Hooke's-law or elastic limit q: exceeding that limit requires an additional force and unloading model to determine the recoverable energy.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The claims for TFBC0 and TDC1D label the quantity 'a weight fixed to the block' although the sentences attach the weight to the trolley; this is a metadata label only and does not affect the answers.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): The numeral-free controls omit the mass and unit retained in their numbered twins, contrary to the review instructions' requirement that quantity variants preserve the same number and unit, although the packet explicitly identifies this difference as intentional.
  - flag other (high): The outside-regime reference expression k*q^2/(2*mu*m*g) does not follow from a Hooke's-law or elastic limit q: exceeding that limit requires an additional force and unloading model to determine the recoverable energy.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R0']

## M250-S33: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'R1', 'N1', 'D0', 'D1', 'R0']

## M250-S34: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T96D5 does not establish that the adjustment finishes before launch or specify the support motion if it occurs during the ascent, so replacing θ by θ + q does not determine a unique answer.
- gpt: high flag missing_assumption: The authors' outside-regime reference expression uses the static friction coefficient as the sliding friction coefficient without specifying a kinetic friction law or assuming equality of the two coefficients.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The out-of-regime reference expression for friction uses the static coefficient in a slipping formula and ignores that a slipping sphere would regain rolling; it is marked reference-only, and the sentence timing ('is then tilted') is slightly loose, so this is low severity.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): T96D5 does not establish that the adjustment finishes before launch or specify the support motion if it occurs during the ascent, so replacing θ by θ + q does not determine a unique answer.
  - flag missing_assumption (high): The authors' outside-regime reference expression uses the static friction coefficient as the sliding friction coefficient without specifying a kinetic friction law or assuming equality of the two coefficients.
- naturalness: 10 sentences, rewrite ['R1', 'R0'], pending 0, slightly artificial ['D1', 'N0', 'N1', 'D0', 'C1']
  - REWRITE R1 (R): claude: Retilting an incline described as fixed at 25 degrees contradicts the stated setup and reads incoherently.
  - REWRITE R0 (R): claude: Tilting the incline 'then' contradicts its description as fixed and leaves the scenario's timing incoherent.

## M250-S35: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: For T41B5 the string is lengthened 'then', i.e. after the stated steady motion at 30 degrees; nothing states that the subsequent motion is again a steady cone at 30 degrees, yet the certified R answers (2.36/2.57/2.83 s) assume the angle is unchanged, and the question could equally refer to the stated (pre-lengthening) motion, giving 2.046 s.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The lengthening variants do not uniquely identify the operative length and steady-motion state for the requested revolution, so their certified answers require additional conditions.
- claude: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): For T41B5 the string is lengthened 'then', i.e. after the stated steady motion at 30 degrees; nothing states that the subsequent motion is again a steady cone at 30 degrees, yet the certified R answers (2.36/2.57/2.83 s) assume the angle is unchanged, and the question could equally refer to the stated (pre-lengthening) motion, giving 2.046 s.
  - flag other (medium): For TC5DB, the base's 'attached to a light string of length 1.2 m' could be read as the length after the earlier lengthening, which would leave the answer at 2.046 s; the intended reading (1.9 m) is the more natural one.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The lengthening variants do not uniquely identify the operative length and steady-motion state for the requested revolution, so their certified answers require additional conditions.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['N1', 'D1', 'D0']
  - REWRITE N0 (N): claude: Lengthening the line on a reel that lies apart from the pendulum is a pointless action, and 'lengthened by a little' is wording no one would use.

## M250-S36: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N0', 'D0'], pending 0, slightly artificial ['N1', 'D1']
  - REWRITE N0 (N): claude: Moving the pivot of an unrelated nearby see-saw is a pointless action that does not belong in the scene.
  - REWRITE D0 (D): claude: Moving the pivot of a nearby see-saw by a precise 20.5 cm is a pointless action that does not belong in this lab scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)

## M250-S37: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TDE51 and T2454 specify an orbital rise without explicitly specifying the final circularity or semimajor axis, which is needed to determine the measured period uniquely.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (low): TDE51 ('is then raised') does not say explicitly that the asked period is the one after the raise, unlike T2454; the R reading is the natural one but the base-orbit period is also a defensible reading.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TDE51 and T2454 specify an orbital rise without explicitly specifying the final circularity or semimajor axis, which is needed to determine the measured period uniquely.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'D1', 'R1']

## M250-S38: REJECT

- claude: validity is invalid
- claude: high flag contradictory_distractor_statement: TCE71 is certified R (angle 44 degrees while the person stands), but the problem states in the present tense that the ladder, with the person standing still on it, makes 62 degrees with the ground; under the certified reading the item contradicts itself, and under the consistent reading (the tilt preceded the stated 62-degree configuration) the answer is the base 841.6 N, so the certified 939.7 N is not uniquely implied.
- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: TCE71 describes a tilt before the person stood on the ladder, so subtracting it from the explicitly stated current occupied angle of 62 degrees is not justified and its certified answers are not uniquely supported.
- gpt: high flag other: The claimed outside-regime reference expression incorrectly treats a coefficient of static friction as determining the actual friction force and retains N=(m+M)g after static equilibrium becomes impossible.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag contradictory_distractor_statement (high): TCE71 is certified R (angle 44 degrees while the person stands), but the problem states in the present tense that the ladder, with the person standing still on it, makes 62 degrees with the ground; under the certified reading the item contradicts itself, and under the consistent reading (the tilt preceded the stated 62-degree configuration) the answer is the base 841.6 N, so the certified 939.7 N is not uniquely implied.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): TCE71 describes a tilt before the person stood on the ladder, so subtracting it from the explicitly stated current occupied angle of 62 degrees is not justified and its certified answers are not uniquely supported.
  - flag other (high): The claimed outside-regime reference expression incorrectly treats a coefficient of static friction as determining the actual friction force and retains N=(m+M)g after static equilibrium becomes impossible.
- pass-1 stratum differences (claude, information only): TCE71 authors R judge D
- pass-1 stratum differences (gpt, information only): TCE71 authors R judge D
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'D0', 'N0', 'N1']

## M250-S41: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TFAEF leaves the additional displacement's position in the experimental sequence ambiguous, so the authors' final separation and certified answers are not uniquely established.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): TFAEF ('Before the force was measured, ...') can be read as referring to the 80 mN measurement, where the 30 cm separation is stated, making it irrelevant history (16 mN) rather than the claimed R (7.788 mN).
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TFAEF leaves the additional displacement's position in the experimental sequence ambiguous, so the authors' final separation and certified answers are not uniquely established.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): T81A0 authors C judge K, TAA47 authors C judge K
- pass-1 stratum differences (gpt, information only): TFAEF authors R judge D
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['R1', 'N1', 'D0', 'D1']
  - REWRITE N0 (N): claude: Moving unrelated bar magnets slightly apart is a pointless action that does not belong to this electrostatics scene.

## M250-S42: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TC461 and T4B85 refer to 'the battery' after two batteries have been introduced, leaving the added cell's circuit unspecified and permitting different powers for the wire.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T4B85 'Before the power was measured, ... was connected' relies on the reader inferring the cell is still in place during the measurement; the intended R reading is the natural one but the wording is slightly less explicit than TC461.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TC461 and T4B85 refer to 'the battery' after two batteries have been introduced, leaving the added cell's circuit unspecified and permitting different powers for the wire.
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'D1']
  - REWRITE N0 (N): claude: Adding a cell to the separate battery of an unrelated bystander lamp is a pointless action that does not belong in this circuit scenario.

## M250-S43: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The relevant additions do not specify whether additional charge excludes charging caused by connecting the extra cell after the explicitly described initial 12 V charged state.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T9341 ('Before the slab was inserted, a 7.5 V cell ... was connected') does not state that the cell remains connected during the insertion, which the R certification (1.17 nC) requires; a reader could take it as removed, giving 0.72 nC.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The relevant additions do not specify whether additional charge excludes charging caused by connecting the extra cell after the explicitly described initial 12 V charged state.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'N1', 'R0', 'D1']

## M250-S44: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The problem says only that the compass is 'nearby'; the D rationale for TF1C5 (the compass field is a region of its own) and the R wiring B + q (coil field parallel to the main field) rest on natural but unstated readings.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1', 'D0', 'R1', 'N0', 'R0']

## M250-S45: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TD3A9 does not establish whether the extra voltage applied before release remains across the gap during acceleration, so its certified radius is conditional on an unstated temporal boundary condition.
- gpt: high flag inconsistent_units: The relevant-sentence wiring uses q simultaneously as bead charge and additional voltage in q(V+q), making V+q dimensionally invalid with the packet's defined charge variable q.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): 'The gap'/'the accelerating gap' is not introduced explicitly, an added voltage of the same polarity is implicit, and the authors' wiring uses q for both the charge and the added potential; all are wording/notation issues only.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): TD3A9 does not establish whether the extra voltage applied before release remains across the gap during acceleration, so its certified radius is conditional on an unstated temporal boundary condition.
  - flag inconsistent_units (high): The relevant-sentence wiring uses q simultaneously as bead charge and additional voltage in q(V+q), making V+q dimensionally invalid with the packet's defined charge variable q.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'R1', 'N1', 'D1', 'R0', 'D0']

## M250-S46: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S47: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S48: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The question says 'frequency' without naming cycles per second versus angular frequency; the certified Hz answer is the standard reading.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): In T0F33, 'this circuit' can refer to the recently introduced second circuit, whereas the certified answer assumes it refers to the first circuit.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["other"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'D1']

## M250-S51: REJECT

- claude: validity is invalid
- claude: high flag contradictory_distractor_statement: T6655 'The piston stops at a compression ratio of 15' plainly states the piston comes to rest at ratio 15, contradicting the stated compression ratio 8; only T75C2's wording ('can be pushed in only until') expresses the intended limit.
- gpt: validity is invalid
- gpt: high flag contradictory_distractor_statement: T6655 states an actual stopping compression ratio of 15, contradicting the base problem's final compression ratio of 8.
- gpt: high flag hidden_coupling: The authors classify T6655 as an inactive mechanical limit, although its stated stopping ratio describes an endpoint that directly determines the work.
- claude: pass-2 FAIL, validity invalid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag contradictory_distractor_statement (high): T6655 'The piston stops at a compression ratio of 15' plainly states the piston comes to rest at ratio 15, contradicting the stated compression ratio 8; only T75C2's wording ('can be pushed in only until') expresses the intended limit.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag contradictory_distractor_statement (high): T6655 states an actual stopping compression ratio of 15, contradicting the base problem's final compression ratio of 8.
  - flag hidden_coupling (high): The authors classify T6655 as an inactive mechanical limit, although its stated stopping ratio describes an endpoint that directly determines the work.
- pass-1 stratum differences (gpt, information only): T6655 authors K judge R
- naturalness: 10 sentences, rewrite ['K0', 'R1'], pending 0, slightly artificial ['N0', 'D1', 'N1', 'D0']
  - REWRITE K0 (K): claude: Saying the piston stops at a compression ratio of 15 directly contradicts the stated compression ratio of 8.
  - REWRITE R1 (R): claude: Saying the cylinder also held a further 1.3 mol contradicts the stated 0.5 mol content, and the phrase 'in this run' is incoherent with the single described compression.

## M250-S52: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The current-run heating statements do not specify whether the stated 40 K excess applies before heating or when ice is added, and T5D2A additionally leaves which container is heated ambiguous.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): With T96AB or T5D2A added, 'starts 40 K above the melting point' could be read as the temperature at the moment the ice is added (after heating) rather than before heating; the certified answers take the latter reading, and T5D2A's 'the container' is slightly ambiguous beside the second container.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The current-run heating statements do not specify whether the stated 40 K excess applies before heating or when ice is added, and T5D2A additionally leaves which container is heated ambiguous.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D0', 'N1', 'N0']

## M250-S53: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The authors' outside-regime reference P = dT/R1 requires the foam to contribute zero thermal resistance after exceeding its limit, whereas loss of shape or exceeding a rating does not specify removal or any post-failure conduction model.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TFB61's past tense 'For this survey, the temperature difference ... was raised by 13 K' could be read as already reflected in the stated 20 K, a mild wording ambiguity; T91A5 ('is then raised') is unambiguous.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): The authors' outside-regime reference P = dT/R1 requires the foam to contribute zero thermal resistance after exceeding its limit, whereas loss of shape or exceeding a rating does not specify removal or any post-failure conduction model.
- pass-1 stratum differences (claude, information only): T0538 authors C judge K, T2BD1 authors C judge K
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'K0', 'R0', 'D1', 'R1', 'D0']

## M250-S54: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: With T6222 ('A 4.5 cm layer ... was plated onto the second sphere') the text never says whether the present-tense stated radius of 10 cm is the radius before or after the completed plating; the reading that it already includes the layer gives 12.44 kW, not the certified 26.16 kW.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The coating renderings do not establish whether the stated 10 cm radius precedes or includes plating, especially when T6222 says the layer 'was plated', so the authors' required initial radius is unspecified.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): With T6222 ('A 4.5 cm layer ... was plated onto the second sphere') the text never says whether the present-tense stated radius of 10 cm is the radius before or after the completed plating; the reading that it already includes the layer gives 12.44 kW, not the certified 26.16 kW.
  - flag other (low): A 4.5 cm (and up to 7.5 cm) 'plated layer' is physically implausible for plating, making the R sentences artificial.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The coating renderings do not establish whether the stated 10 cm radius precedes or includes plating, especially when T6222 says the layer 'was plated', so the authors' required initial radius is unspecified.
- naturalness: 6 sentences, rewrite ['R0', 'R1', 'D1', 'D0'], pending 0, slightly artificial ['N0', 'N1']
  - REWRITE R0 (R): claude: Plating a 4.5 cm thick layer onto a 10 cm sphere is implausible, since plating produces thin coatings.
  - REWRITE R1 (R): claude: A 4.5 cm plated layer is implausible since plating is thin, and it conflicts with the sphere's stated 10 cm radius description.
  - REWRITE D1 (D): claude: A 4.5 cm plated layer is implausibly thick for plating and the detail about an unrelated disc is pointless.
  - REWRITE D0 (D): claude: A 4.5 cm thick plated layer is not a realistic plating, and plating a bystander bracket is a pointless action in this scene.

## M250-S56: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The rendered problem does not specify that the requested refrigerator electrical input excludes the operating interior lamp's own consumption, which changes the answer by 55 W.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T5F2C and the authors' rationale speak of 'this test' although the base problem never calls the steady run a test; the meaning is still recoverable.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): The rendered problem does not specify that the requested refrigerator electrical input excludes the operating interior lamp's own consumption, which changes the answer by 55 W.
- pass-1 stratum differences (claude, information only): T0E77 authors C judge D, T2BAE authors C judge D
- pass-1 stratum differences (gpt, information only): T2BAE authors C judge D
- naturalness: 10 sentences, rewrite ['D0'], pending 0, slightly artificial ['D1', 'R0', 'C0', 'N0', 'R1', 'N1']
  - REWRITE D0 (D): claude: Keeping a 55 W lamp lit inside a chest freezer is a pointless, implausible action for this scene.

## M250-S57: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['R1'], pending 0, slightly artificial ['D1', 'D0', 'N0', 'N1']
  - REWRITE R1 (R): claude: Saying the tank 'also held' a further 1.4 kg contradicts the stated 2 kg content, and 'the tank' is ambiguous next to an empty second tank.

## M250-S61: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The claims for TC70F and T68D0 label the quantity 'a shift of the screen' although those sentences describe a shift of the camera; a metadata label only, the physics and answers are right.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D0', 'D1']

## M250-S62: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (medium): T2171 ('is then increased by 35 mW') does not say the increase precedes the measurement the question asks about, so a reader could answer for the original 40 mW; the certified after-increase reading is the natural one.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): T86DB authors C judge D, TAD42 authors C judge D
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'D0', 'R0', 'N0', 'R1']

## M250-S63: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D0', 'D1', 'N1', 'K1']

## M250-S64: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1']

## M250-S65: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The problem specifies a flat entrance face but does not specify that it is perpendicular to the fibre axis, which is necessary for the claimed acceptance angle and governing relations.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T55EF says the fibre end 'was dipped' into the liquid for this experiment without saying the liquid replaces the stated air, so the reader must infer that it overrides 'enters from air'; T494E states this explicitly.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag rendering_not_minimal (high): T5FB3 and T38EB omit the numerical index preserved by their counterparts, violating the required matching of numbers and units across variants even though the authors identify these omissions as deliberate controls.
  - flag missing_assumption (high): The problem specifies a flat entrance face but does not specify that it is perpendicular to the fibre axis, which is necessary for the claimed acceptance angle and governing relations.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T5FB3 and T38EB omit the numerical index preserved by their counterparts, violating the required matching of numbers and units across variants even though the authors identify these omissions as deliberate controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite ['N1'], pending 0, slightly artificial ['D0', 'D1', 'N0']
  - REWRITE N1 (N): claude: "A liquid whose refractive index is a known value" is wording no one would use, and the reference to an earlier experiment is pointless.

## M250-S66: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The screen sentences use 'the screen' although no screen is introduced, and the question does not state that the angle is wanted in degrees (target unit deg is conventional but not written).
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- pass-1 stratum differences (claude, information only): T2E60 authors C judge D, TBC0D authors C judge D
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['N1', 'D1', 'R1', 'R0']
  - REWRITE N0 (N): claude: "Light of a certain wavelength" is vague, and its entering the unrelated second spectrometer is a pointless event that no one would write this way.

## M250-S67: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TBD30 does not establish that the stated 50 mW precedes the historical increase, so the authors' 85 mW incident power and 78.4615 mW transmitted power are not uniquely determined by the wording.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TBD30 ('increased by 35 mW before the beam reached the plate') reads slightly awkwardly against the base statement that a 50 mW beam falls on the plate; the intended reading (incident power 85 mW) is the natural one.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TBD30 does not establish that the stated 50 mW precedes the historical increase, so the authors' 85 mW incident power and 78.4615 mW transmitted power are not uniquely determined by the wording.
- pass-1 stratum differences (gpt, information only): TBD30 authors R judge D
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['D1', 'N1', 'D0', 'N0']
  - REWRITE R1 (R): claude: Saying the source output was raised by 35 mW before reaching the plate conflicts with the stated 50 mW incident beam and reads incoherently.

## M250-S71: REJECT

- gpt: validity is invalid
- gpt: high flag other: The T860D claim subtracts the shift from the explicitly stated incident wavelength, whereas its sentence places the shortening before arrival and does not establish that 250 nm is the wavelength before shortening.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T860D ('shortened by 55 nm before it reached the metal surface') can be read as the 250 nm in the problem already being the wavelength arriving at the surface, in which case the answer would not change; the authors' R reading (250 nm is the original wavelength) is the more natural one but not the only one.
  - flag inconsistent_units (low): The displayed relation v = c*sqrt(2*Kmax/mc2) lists Kmax in eV and mc2 in keV; numerically the certified answers use a consistent conversion, so this is only a presentation issue.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): TA8F1 and TCF8E omit the number and unit retained by the other wavelength variants, contrary to the review's stipulated matching requirement, although the authors explicitly identify these omissions as deliberate controls.
  - flag other (high): The T860D claim subtracts the shift from the explicitly stated incident wavelength, whereas its sentence places the shortening before arrival and does not establish that 250 nm is the wavelength before shortening.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TA8F1 and TCF8E omit the number and unit retained by the other wavelength variants, contrary to the review's stipulated matching requirement, although the authors explicitly identify these omissions as deliberate controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): T5707 authors C judge K, TB26A authors C judge K
- pass-1 stratum differences (gpt, information only): T5707 authors C judge K, T860D authors R judge D, TB26A authors C judge K
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['N1', 'D1', 'D0', 'N0']
  - REWRITE R1 (R): claude: Light's wavelength being "shortened by 55 nm" on the way to the surface is not a coherent physical event, and the wording is unnatural.

## M250-S73: ADMIT

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): TEDF7/T6BE7 ('The well was widened ... in an earlier experiment on it') do not say the widening was reversed, and widening is a lasting structural change, so a reader could take the present width as 2.9 nm (answer 1848 nm); the authors' 'leaves no state behind' reading relies on the stated 0.5 nm width taking precedence.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T425C and T6BE7 omit the numerical widening and its unit, departing from the review instructions' uniform-number requirement, although the authors explicitly identify these as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite ['N0', 'D1', 'R0'], pending 0, slightly artificial ['D0', 'R1', 'N1']
  - REWRITE N0 (N): claude: Widening an already-grown quantum dot just before a transition is not a physically plausible action, and the dot is otherwise unrelated to the well.
  - REWRITE D1 (D): claude: Widening a 0.5 nm infinite well by 2.4 nm in an earlier experiment is physically odd and does not fit the stated width, so the sentence reads as incoherent.
  - REWRITE R0 (R): claude: Widening the well by 2.4 nm before the transition contradicts the stated 0.5 nm width and is an implausible event for this setup.

## M250-S77: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T9848/T6F0D phrase 'was then replaced ... for an earlier experiment only' combines 'then' with 'earlier experiment', which reads awkwardly although the intended reading is recoverable.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['N0', 'R1', 'D0', 'R0', 'N1', 'D1'], pending 0, slightly artificial none
  - REWRITE N0 (N): claude: Replacing the step 'by one whose height is known' before the electron arrives is incoherent wording and a pointless action.
  - REWRITE R1 (R): claude: The sentence says the barrier 'was then replaced' yet 'before the electron approached it', a muddled, self-contradictory sequence no one would write.
  - REWRITE D0 (D): claude: Replacing a separate on-chip potential step 'before the electron arrives' is an incoherent action for this tunneling scenario, and the wording is awkward.
  - REWRITE R0 (R): claude: Replacing a chip's barrier 'before the electron arrives', with the clumsy 'Before ... then' wording, is implausible and not how anyone would phrase it.
  - REWRITE N1 (N): claude: Replacing the barrier with one 'whose height is known for an earlier experiment only' is incoherent wording no one would use.
  - REWRITE D1 (D): claude: 'Was then replaced ... for an earlier experiment only' is self-contradictory in time and wording no one would use.

## M250-S82: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The stellar-history sentences do not establish the observed temperature relative to the stated 2900 K or specify that the star returns to that temperature after its earlier outburst.
- gpt: high flag hidden_coupling: The claimed disconnection of T099E and TFD41 is unsupported because an earlier outburst can leave a temperature change that affects the observed blackbody peak.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): The stellar-history sentences do not establish the observed temperature relative to the stated 2900 K or specify that the star returns to that temperature after its earlier outburst.
  - flag hidden_coupling (high): The claimed disconnection of T099E and TFD41 is unsupported because an earlier outburst can leave a temperature change that affects the observed blackbody peak.
- pass-1 stratum differences (gpt, information only): T099E authors D judge R, TFD41 authors N judge R
- naturalness: 6 sentences, rewrite ['R0', 'R1'], pending 0, slightly artificial ['N0', 'D0', 'N1']
  - REWRITE R0 (R): claude: A star's surface temperature rising by 950 K before spectra are compared is physically implausible for this situation.
  - REWRITE R1 (R): claude: A star's surface temperature rising by 950 K shortly before observation is implausible and contradicts the stated temperature.

## M250-S91: REJECT

- gpt: validity is invalid
- gpt: high flag other: The K claims incorrectly turn an absolute-pressure feasibility constraint into a different flow law outside q > dp, replacing the measured pressure difference by q without physical justification.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The K regime 'q > dp' only keeps the throat pressure positive, not above the liquid's vapour pressure (the true cavitation bound), and the out-of-regime reference expression substitutes q for dp, which is not the physics of a cavitating Venturi; all listed values (170-350 kPa vs dp = 14.8 kPa) are far inside any sensible regime, so no certified answer is affected.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The K claims incorrectly turn an absolute-pressure feasibility constraint into a different flow law outside q > dp, replacing the measured pressure difference by q without physical justification.
- pass-1 stratum differences (claude, information only): T2A08 authors K judge C, T6339 authors K judge C
- pass-1 stratum differences (gpt, information only): T2A08 authors K judge C, T6339 authors K judge C
- naturalness: 10 sentences, rewrite ['D0', 'N0', 'R1'], pending 0, slightly artificial ['D1', 'N1', 'R0']
  - REWRITE D0 (D): claude: Replacing the liquid in a wall barometer just before reading the manometer is a pointless, implausible action in this scene.
  - REWRITE N0 (N): claude: Replacing the liquid in a wall-mounted mercury barometer before reading the manometer is a pointless, implausible action in this scene.
  - REWRITE R1 (R): claude: Saying the U-tube liquid was replaced by a 2500 kg/m³ liquid before reading contradicts the earlier statement that it contains a 13600 kg/m³ liquid.

## M250-S93: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): A water density of 962 kg/m^3 (water near 90 C) is unusual and slightly artificial, and 'its hole' in the scene clause follows the barrel sentence; neither affects the answer.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['N0', 'R1', 'C1', 'C0', 'R0', 'D1', 'D0']
  - REWRITE N1 (N): claude: Widening the hole 'by a further small amount' after the timing ended is a pointless action in wording no one would use.

## M250-S94: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The authors require a Newtonian incompressible liquid, but the rendered problem does not state that constitutive model; a viscosity value alone does not explicitly establish it under the admission standard.
- gpt: high flag insufficient_boundary_condition: For TF825 and T0FF6, the question does not identify whether the pressure-drop endpoints bound the original 2 m pipe or the complete pipe-and-tubing assembly, which gives materially different powers.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): For the R sentences, 'the pressure drop along the pipe' could be read as along the original 2 m section only (unchanged answer) rather than along the extended pipe; the extended reading the authors certify is the more natural one.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): The authors require a Newtonian incompressible liquid, but the rendered problem does not state that constitutive model; a viscosity value alone does not explicitly establish it under the admission standard.
  - flag insufficient_boundary_condition (high): For TF825 and T0FF6, the question does not identify whether the pressure-drop endpoints bound the original 2 m pipe or the complete pipe-and-tubing assembly, which gives materially different powers.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'D0', 'N0', 'R0', 'N1']

## M250-S95: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The C cancellation relations call p_L the absolute pressure (p_atm + mg/A2) while the main relations list uses pL = mg/A2 as a gauge pressure; the notation is mixed but the physics and expression are correct.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The numeral-free controls omit the 560 kg quantity required by the general variant-format instruction, although the authors explicitly disclose this intended difference and do not claim these controls preserve the numerical value.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'R1', 'N1', 'N0', 'D1']

