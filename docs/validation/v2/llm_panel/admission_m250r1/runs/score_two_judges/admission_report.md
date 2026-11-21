# M250 repair round 1 re-review, Claude + GPT (5.3b guard)

Applies admission standard 5.2-5.3 (physics, qualified LLM panel) and 6.1 (naturalness) to the panel's reviews.
Judges: claude, gpt. Naturalness raters: claude. Judges required per structure: 2.

A structure is ADMITTED only if every judge calls it valid with no high flag. Missing reviews make it INCOMPLETE (a missing review is not a verdict). A sentence rated artificial must be rewritten, and so must a D sentence rated more than one level worse than its R twin (natural > slightly_artificial > artificial; standard 6.1 as amended 2026-11-15).

Structures: ADMIT 80, REJECT 32

## M250-S03: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): 'Collides head-on' for an overtaking collision is unusual wording, though the meaning (central 1D collision) is clear.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S04: REJECT

- gpt: validity is invalid
- gpt: high flag other: For T2F08 and T7685, the supplied outside-regime reference speed q*sqrt(k/m) is not generally valid: exceeding an elastic or Hookean limit requires a further constitutive model, and the limit alone does not determine the recoverable energy.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): For T2F08 and T7685, the supplied outside-regime reference speed q*sqrt(k/m) is not generally valid: exceeding an elastic or Hookean limit requires a further constitutive model, and the limit alone does not determine the recoverable energy.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N1', 'D1', 'N0']

## M250-S05: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'N0']

## M250-S06: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T7719 establishes an earlier connection but does not explicitly establish that the extra resistor is still connected during measurement, so its certified answer requires an unstated measurement configuration.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T7719 establishes an earlier connection but does not explicitly establish that the extra resistor is still connected during measurement, so its certified answer requires an unstated measurement configuration.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S09: REJECT

- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: The certified base answer and all disconnected-sentence answers are 8.24897 K, whereas the stated relations and inputs give 8.24977235 K, which rounds to 8.24977 K at the displayed precision.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): The certified base answer and all disconnected-sentence answers are 8.24897 K, whereas the stated relations and inputs give 8.24977235 K, which rounds to 8.24977 K at the displayed precision.
- naturalness: 6 sentences, rewrite ['N1'], pending 0, slightly artificial ['R1', 'D1', 'D0', 'N0']
  - REWRITE N1 (N): claude: The phrasing 'was given a further small amount of water ... for an earlier experiment only' is convoluted wording no one would ordinarily use.

## M250-S10: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D0', 'C1', 'R0', 'N1', 'D1', 'N0', 'R1']

## M250-S11: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The rendered T8720 and TB9A5 problems do not establish whether the stated 20 m/s occurs before or after the added speed gain, so their braking-onset speeds are not uniquely determined.
- gpt: high flag other: The authors explicitly define v0 as the braking-onset speed but then calculate the R answers by treating v0 as the speed before an additional acceleration, making their wiring and certified answers inconsistent with their stated input and assumption.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag insufficient_boundary_condition (high): The rendered T8720 and TB9A5 problems do not establish whether the stated 20 m/s occurs before or after the added speed gain, so their braking-onset speeds are not uniquely determined.
  - flag other (high): The authors explicitly define v0 as the braking-onset speed but then calculate the R answers by treating v0 as the speed before an additional acceleration, making their wiring and certified answers inconsistent with their stated input and assumption.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'D1', 'N0', 'N1']

## M250-S12: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The stated 50 m radius describes the road's inner edge, while the car's path radius and the road's outer boundary are unspecified, so the base problem and the D and C variants have no unique maximum speed.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The base says the 50 m radius is the inner edge of the road but does not say in so many words that the car follows the inner edge; the natural reading (car's path radius 50 m) is the one certified.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The stated 50 m radius describes the road's inner edge, while the car's path radius and the road's outer boundary are unspecified, so the base problem and the D and C variants have no unique maximum speed.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S14: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): With a box strapped onto the load (T920A, T8A2F), 'power the motor delivers to the load' admits a reading as power to the 80 kg load alone (470.4 W) rather than to the lifted assembly (540.96 W); the certified reading is the more natural one, helped by 'the mass given is that of the load alone', so this is wording only.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'D0']

## M250-S17: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T6D07 and T97D1 replace their twins' explicit 6.5 K with 'a few kelvin', violating the review instructions' requirement that variants of the same quantity preserve its stated numerical value and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T6D07 and T97D1 replace their twins' explicit 6.5 K with 'a few kelvin', violating the review instructions' requirement that variants of the same quantity preserve its stated numerical value and unit.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D1', 'D0', 'N1']

## M250-S19: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T3E32 and TFDC7 do not establish whether the stated 35° describes the direction before lowering or the actual launch direction after lowering, so they do not uniquely determine the initial velocity.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): The base states the ball is launched at 35 degrees while the R sentences lower the launch direction before launch; the intended reading (35 degrees is the initial setting) is clear but the wording is slightly in tension.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T3E32 and TFDC7 do not establish whether the stated 35° describes the direction before lowering or the actual launch direction after lowering, so they do not uniquely determine the initial velocity.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N1', 'D0', 'N0']

## M250-S202: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The base specifies that any carried cargo must be bolted on but never specifies how much bolted cargo is present, although that retained mass changes the final speed.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The base specifies that any carried cargo must be bolted on but never specifies how much bolted cargo is present, although that retained mass changes the final speed.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S203: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T9510 and T9186 specify 'a few metres per second squared' instead of 2.1 m/s², violating the review instructions' requirement that variants concerning the same quantity preserve its number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T9510 and T9186 specify 'a few metres per second squared' instead of 2.1 m/s², violating the review instructions' requirement that variants concerning the same quantity preserve its number and unit.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'D1', 'N0', 'R0', 'N1', 'R1']

## M250-S204: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['N1'], pending 0, slightly artificial ['D0', 'R1', 'D1']
  - REWRITE N1 (N): claude: The phrasing about a bag carried 'on an earlier outing only' is wording no one would naturally use and the detail is pointless.

## M250-S205: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1', 'R0', 'R1']

## M250-S207: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S208: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (low): The pair TE735/T145A differs in the verb ('fitted to' vs 'glued to') as well as the attachment; number and unit agree, so this is a minor wording difference.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N0', 'N1']

## M250-S209: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'R0', 'D1', 'N0', 'N1']

## M250-S21: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TD410 places tuning before measurement but does not establish whether it occurs before or after the initial switch-on that defines the stated 440 Hz, so its claimed R classification and certified answers are not uniquely determined.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): The R sentences rely on temporal wording ('then tuned up', 'just before the tone was measured') against a 'steady tone' of 440 Hz 'when first switched on', so the moment at which the heard frequency is asked is only implied (after retuning).
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TD410 places tuning before measurement but does not establish whether it occurs before or after the initial switch-on that defines the stated 440 Hz, so its claimed R classification and certified answers are not uniquely determined.
  - flag rendering_not_minimal (high): TEDCB and T62DC replace 16 Hz with an unspecified small amount, violating the review instructions' requirement that variants preserve the stated number and unit, although the packet explicitly identifies this as deliberate.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TEDCB and T62DC replace 16 Hz with an unspecified small amount, violating the review instructions' requirement that variants preserve the stated number and unit, although the packet explicitly identifies this as deliberate.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): T4EE7 authors C judge K, TE5DD authors C judge K
- pass-1 stratum differences (gpt, information only): TD410 authors R judge C
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N1', 'D1', 'D0', 'R0']

## M250-S210: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'R0', 'N1', 'N0']

## M250-S211: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['R1'], pending 0, slightly artificial ['N0', 'D1', 'D0', 'N1']
  - REWRITE R1 (R): claude: A plastic clip heavier than the bead riding on it inside a sealed cavity of a charged ball does not plausibly belong in this scene.

## M250-S215: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S216: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T47FC and T3A64 omit the 22 μF quantity stated in their corresponding quantitative variants, violating the review instructions' explicit requirement that variants preserve the number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T47FC and T3A64 omit the 22 μF quantity stated in their corresponding quantitative variants, violating the review instructions' explicit requirement that variants preserve the number and unit.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N0', 'N1']

## M250-S218: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D0', 'D1']

## M250-S219: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'R1', 'D1', 'N1']

## M250-S220: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- pass-1 stratum differences (claude, information only): TA3FF authors K judge C, TAC6D authors K judge C
- pass-1 stratum differences (gpt, information only): TA3FF authors K judge C, TAC6D authors K judge C
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'N1', 'D1', 'D0', 'N0']

## M250-S221: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N1', 'D1', 'N0']

## M250-S223: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N1', 'N0']

## M250-S224: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: T2667 and T6DA3 require thermal equilibration after helium admission for the certified composition-only entropy changes; equal pressures and the incoming helium temperature do not establish equal compartment temperatures after filling.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag missing_assumption (medium): The R sentences say the added helium is 'at the temperature of the gases' but do not state that the compartments remain at one common temperature after it is let in; strictly, filling a compartment of an insulated container does flow work and the sliding partition compresses the argon, so the certified answers assume (naturally but implicitly) that the common temperature is restored.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): T2667 and T6DA3 require thermal equilibration after helium admission for the certified composition-only entropy changes; equal pressures and the incoming helium temperature do not establish equal compartment temperatures after filling.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["missing_assumption"], "gpt": []}
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['R1', 'D0', 'D1', 'N1']
  - REWRITE N0 (N): claude: Letting helium into a balloon just described as having no tube to it is incoherent and a pointless action in this scene.

## M250-S225: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T6641 and T26FA do not state that the historical wrapping was removed, leaving the current outer boundary radius unresolved under the same additive-layer reading used for the relevant variants.
- gpt: high flag hidden_coupling: The authors claim that historical wrapping leaves no state behind, although retained wrapping changes the radial thermal resistance and therefore the requested temperature fall.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T6641 and T26FA do not state that the historical wrapping was removed, leaving the current outer boundary radius unresolved under the same additive-layer reading used for the relevant variants.
  - flag hidden_coupling (high): The authors claim that historical wrapping leaves no state behind, although retained wrapping changes the radial thermal resistance and therefore the requested temperature fall.
- pass-1 stratum differences (gpt, information only): T26FA authors N judge R, T6641 authors D judge R
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'R1', 'D1', 'D0', 'N0']

## M250-S226: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'R1', 'D1', 'N1', 'R0']
  - REWRITE N0 (N): claude: Timing a kettle heater to 'before the shields settle' links two unrelated things incoherently and describes a pointless action.

## M250-S227: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T9DAE and TCA07 replace the specified 38 K with an indefinite 'few kelvin', violating the review's requirement that variants of the same quantity preserve its number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T9DAE and TCA07 replace the specified 38 K with an indefinite 'few kelvin', violating the review's requirement that variants of the same quantity preserve its number and unit.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'R0', 'D1', 'D0', 'N0']

## M250-S230: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (medium): The d_rationale for T7053 and T33C5 speaks of 'metal poured into the mould', but the sentences and scene place the metal in a warming cabinet; the stratum conclusion is still right, so this is a stale rationale wording, not a wrong claim about the item.
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T33C5 and TFF07 replace 1.1 kg with 'small amount', violating the review instructions' requirement that same-quantity sentence variants preserve the number and unit, even though the authors explicitly designate these omissions as deliberate controls.
  - flag other (low): The rationales for T33C5 and T7053 describe metal poured into a mould, whereas the rendered sentences describe metal placed in the warming cabinet.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T33C5 and TFF07 replace 1.1 kg with 'small amount', violating the review instructions' requirement that same-quantity sentence variants preserve the number and unit, even though the authors explicitly designate these omissions as deliberate controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite ['D1'], pending 0, slightly artificial ['N0', 'N1', 'D0', 'R0', 'R1']
  - REWRITE D1 (D): claude: A solid block 'taking on' extra metal in an unrelated earlier run is incoherent wording that no one would use for this setup.

## M250-S231: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: The text defines the 3 m/s as the wall's speed relative to the trolley but never states that the trolley is at rest, yet the base answer and every D and C certified answer (7.76471 Hz) require a stationary trolley; the authors' own d_rationale ('a trolley that has no such motion') supplies this condition, which the problem does not.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The wall's specified speed is relative to its trolley, but the trolley's velocity during recording is unspecified except in T2729 and T7F76.
- gpt: high flag relevant_variable_removed_from_equation: The base Doppler and crest-timing relations use the stated relative speed v as the wall's air-frame speed, omitting the trolley velocity required to obtain that speed.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The text defines the 3 m/s as the wall's speed relative to the trolley but never states that the trolley is at rest, yet the base answer and every D and C certified answer (7.76471 Hz) require a stationary trolley; the authors' own d_rationale ('a trolley that has no such motion') supplies this condition, which the problem does not.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The wall's specified speed is relative to its trolley, but the trolley's velocity during recording is unspecified except in T2729 and T7F76.
  - flag relevant_variable_removed_from_equation (high): The base Doppler and crest-timing relations use the stated relative speed v as the wall's air-frame speed, omitting the trolley velocity required to obtain that speed.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1']

## M250-S232: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T9415 does not establish that the tank's stated surface tension is its value before the historical reduction, or explicitly identify the tank, leaving materially different surface tensions at the time of propagation possible.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T9415 ('had reduced the surface tension of the water ... before the ripples were made') does not name the tank, and the pluperfect allows the reading that the stated 0.0728 N/m already includes the reduction, which would make it D rather than R.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T9415 does not establish that the tank's stated surface tension is its value before the historical reduction, or explicitly identify the tank, leaving materially different surface tensions at the time of propagation possible.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S233: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TAC23 does not place the amplifier before the first glass surface, so its claimed incident power P0 + q and its certified transmitted powers are not uniquely established.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TAC23 does not place the amplifier before the first glass surface, so its claimed incident power P0 + q and its certified transmitted powers are not uniquely established.
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'R0', 'D1', 'N1']
  - REWRITE N0 (N): claude: Amplifying an unspecified 'small amount' of power for a second laser that is turned away from the block is a pointless, vague action that does not belong in this scene.

## M250-S234: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TF3EE can describe drawing the initially 2 m rod before transmission, but its final length or sufficient initial geometry to determine that length is not specified.
- gpt: high flag hidden_coupling: The claimed cancellation for TF3EE holds at fixed final length, whereas drawing to a specified diameter can change the rod's length and therefore its transit time.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TF3EE can describe drawing the initially 2 m rod before transmission, but its final length or sufficient initial geometry to determine that length is not specified.
  - flag hidden_coupling (high): The claimed cancellation for TF3EE holds at fixed final length, whereas drawing to a specified diameter can change the rod's length and therefore its transit time.
- pass-1 stratum differences (gpt, information only): TF3EE authors C judge R
- naturalness: 8 sentences, rewrite ['R0'], pending 0, slightly artificial ['D0', 'N0', 'R1', 'D1', 'N1']
  - REWRITE R0 (R): claude: Saying the 2 m rod 'is extended by 1.3 m' right after fixing its length reads as a self-contradictory edit rather than part of the situation.

## M250-S235: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'N1', 'D0']

## M250-S236: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): TF775 and T8378 omit the extension number and unit retained in the other extension variants, contrary to the review requirement that variants concerning the same quantity preserve both.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TF775 and T8378 omit the extension number and unit retained in the other extension variants, contrary to the review requirement that variants concerning the same quantity preserve both.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'N0', 'N1', 'D0']

## M250-S238: REJECT

- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: The K claims show P*(q/rot)^2 as an outside-regime reference expression, but changing an instability threshold does not change the imposed rotor speed, and this expression does not describe power after the onset of secondary flow.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): The K claims show P*(q/rot)^2 as an outside-regime reference expression, but changing an instability threshold does not change the imposed rotor speed, and this expression does not describe power after the onset of secondary flow.
  - flag other (medium): In the current-run speed-increase variants, 'this rate' can refer to the original 120 rpm or the updated 195 rpm.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["other"]}
- pass-1 stratum differences (claude, information only): T5A9C authors C judge K, TF420 authors C judge K
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'N1', 'D1']

## M250-S239: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T8B20's 'Polishing then thins the plate' does not fix whether the thinning precedes the light's passage; the authors' R reading (thickness d - q) is the natural one given the scene clause about thickness before polishing, but an after-the-light reading would give the base answer.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'D1', 'N1', 'N0']

## M250-S24: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The claims for TC060 and TF51D label the quantity 'a temperature rise of the hot reservoir', although these sentences warm the copper block; a metadata label only, the strata and answers are right.
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): TF51D and T77C1 replace the specified 150 K rise with 'a few kelvin', violating the review instructions' requirement that same-quantity variants preserve the number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TF51D and T77C1 replace the specified 150 K rise with 'a few kelvin', violating the review instructions' requirement that same-quantity variants preserve the number and unit.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'N1', 'D0', 'N0', 'R1', 'D1']

## M250-S240: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T5FCB/T15A1 name only the liquid in the siphon; the R answer relies on the scene clause that the reservoir holds the same liquid as the siphon, which covers it but makes the wording slightly indirect.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite ['R0'], pending 0, slightly artificial ['D0', 'N1', 'R1', 'D1', 'N0']
  - REWRITE R0 (R): claude: Replacing the liquid in the siphon alone is incoherent when the siphon is continuously fed from a reservoir said to hold the same liquid.

## M250-S241: REJECT

- gpt: validity is invalid
- gpt: high flag other: The authors' D rationales for T306C and TEB4A incorrectly identify the illuminated object as a meter dial, whereas both sentences specify a wall chart and the problem introduces no meter dial.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag invalid_numerical_precision (low): The certified answers (4.83818, 8.12814 μA, ...) use the CODATA eV-to-joule factor 1.602176634e-19 for the photon energy while the charge uses the stated e = 1.602e-19 C; with the stated constants used consistently e cancels and I = eta P / 3.1 V = 4.83871 μA (8.12903 μA at 8.4 mW), a 0.011% difference that is within any reasonable stated precision.
  - flag other (low): The D rationales for T306C and TEB4A speak of 'a lamp that lights the dial of the meter', whereas the item text names a wall chart; the physics of the claim is right but the rationale text does not match the item.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The authors' D rationales for T306C and TEB4A incorrectly identify the illuminated object as a meter dial, whereas both sentences specify a wall chart and the problem introduces no meter dial.
- naturalness: 8 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['D1', 'R0', 'N1']
  - REWRITE D0 (D): claude: A further lamp 'of the same wavelength as the light' adding power to a wall chart is a pointless detail in wording no one would use.
  - REWRITE N0 (N): claude: A further lamp matched to the photocell's wavelength just to light a wall chart is a pointless, oddly worded detail that does not belong in the scene.

## M250-S242: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The deliberately numeral-free controls T9D9A and TF3A2 do not preserve the number and unit requested by the general variant instruction, although the authors accurately identify these omissions and both explicitly claimed minimal pairs preserve 170 Bq.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'R1', 'D0', 'N1', 'R0']

## M250-S243: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The certified 54.9159 fm appears to convert MeV to joules with the exact CODATA e (1.602176634e-19) rather than the stated e = 1.602e-19 C; using the stated e throughout gives 54.922 fm, a 0.011% difference well within the four-figure precision of the given constants.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N1']

## M250-S245: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): The D rationale for T341F and T037E speaks of a nozzle that speeds up 'the helium jet', but the problem's second beam is of unspecified molecules from a second oven, so the authors' rationale misdescribes the scene (the D claim itself holds); also the sweep sentences invite deriving the velocity change from the sweep range, a reading the text does not exclude.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (claude, information only): T0167 authors K judge C, T866E authors K judge C
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N0', 'R0', 'R1', 'D0', 'N1', 'D1']

## M250-S246: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N1'], pending 0, slightly artificial ['N0', 'R1', 'D1']
  - REWRITE N1 (N): claude: The sentence is muddled: 'an earlier shield' and 'its wall' tie concrete work to an unclear object, and no one would phrase it this way.

## M250-S247: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TFEB0 says the lamp adds intensity to 'the light that reaches the mirror' without saying it enters the beam or lasts the whole exposure; the problem's clause on lamp light put into the beam makes the intended reading (along the beam, throughout) the natural one.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'D1', 'N0', 'D0', 'N1']

## M250-S248: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N1', 'D1', 'N0']

## M250-S249: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1']

## M250-S25: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['K0', 'N1', 'N0']

## M250-S251: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T9571 and T9D2A omit the number and unit, so the full speed-sentence set does not meet the requested common-number/unit format, although the authors explicitly identify these as numeral-free controls rather than numerical minimal pairs.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite ['D0'], pending 0, slightly artificial ['N0', 'R0', 'R1', 'N1']
  - REWRITE D0 (D): claude: A spring catapult giving a waiting capsule 'a further' 210 m/s is incoherent, since the capsule has no prior speed, and implausible for a spring device.

## M250-S252: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R0', 'D0', 'R1', 'D1', 'N1', 'N0']

## M250-S253: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The problem does not state the harmonic-wave assumption listed by the authors, although intensity alone determines RMS pressure and does not determine an arbitrary waveform's peak amplitude.
- gpt: high flag insufficient_boundary_condition: The rendered problem does not establish either that the second source is excluded from the measured pressure or that a source-intensity change has reached the measurement location.
- gpt: high flag hidden_coupling: Facing the boathouse wall does not establish the claimed absence of an acoustic path from the second loudspeaker to the water.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): The problem does not state the harmonic-wave assumption listed by the authors, although intensity alone determines RMS pressure and does not determine an arbitrary waveform's peak amplitude.
  - flag insufficient_boundary_condition (high): The rendered problem does not establish either that the second source is excluded from the measured pressure or that a source-intensity change has reached the measurement location.
  - flag hidden_coupling (high): Facing the boathouse wall does not establish the claimed absence of an acoustic path from the second loudspeaker to the water.
- pass-1 stratum differences (gpt, information only): TA783 authors D judge R, TF89B authors N judge R
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D0']

## M250-S254: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D0', 'N0', 'D1']

## M250-S255: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The claims for the tape sentences (TE1D7, TC665) label the quantity 'a further length of strip' although it is a length of measuring tape; a bookkeeping label only, with no effect on strata or answers.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'D1', 'N1']
  - REWRITE N0 (N): claude: Pulling a measuring tape out 'a modest distance further' is a pointless, vaguely worded action unconnected to the strip.

## M250-S256: REJECT

- claude: validity is invalid
- claude: high flag insufficient_boundary_condition: The R sentences TC49F and T6CF0 add 0.18 kg of lead without stating its temperature; the certified 4.91136 kJ requires it to start at 300 K, and the authors' own wiring describes the lead as 'cast' onto the block, which would make it hot, so the heat supplied is not uniquely determined.
- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T6CF0 and TC49F specify the added mass but not its initial temperature or that the combined block begins heating at 300 K, so their certified heat inputs require an unstated initial condition.
- claude: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The R sentences TC49F and T6CF0 add 0.18 kg of lead without stating its temperature; the certified 4.91136 kJ requires it to start at 300 K, and the authors' own wiring describes the lead as 'cast' onto the block, which would make it hot, so the heat supplied is not uniquely determined.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T6CF0 and TC49F specify the added mass but not its initial temperature or that the combined block begins heating at 300 K, so their certified heat inputs require an unstated initial condition.
- naturalness: 8 sentences, rewrite ['D1', 'D0'], pending 0, slightly artificial ['N0', 'N1', 'R0', 'R1']
  - REWRITE D1 (D): claude: Adding lead to a solid block 'for one heating only' in an earlier experiment is an implausible action described in wording no one would use.
  - REWRITE D0 (D): claude: Adding lead to a bystander weight on a hook before heating the block is a pointless action that does not belong in the scene.

## M250-S257: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'D1', 'N1', 'R1', 'R0']

## M250-S258: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'R1', 'N0']

## M250-S259: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1', 'D0', 'N0']

## M250-S260: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T8E4F (claimed R) keeps the phrase 'for one run only' from its D twin TA9C7, so a reader could take it as another run; the authors' R reading (the counted run) is the more natural one.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'N1', 'R1', 'D0']

## M250-S261: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'D0', 'N1', 'R1']

## M250-S262: REJECT

- gpt: validity is invalid
- gpt: high flag other: The authors supply tc*q/1000 as an outside-regime reference expression, but a laminar-transition threshold does not determine an alternative flow law or justify this time scaling, which produces physically impossible drainage times.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): The authors supply tc*q/1000 as an outside-regime reference expression, but a laminar-transition threshold does not determine an alternative flow law or justify this time scaling, which produces physically impossible drainage times.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'R0', 'N1', 'N0', 'D1', 'D0']

## M250-S263: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N0']

## M250-S264: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D1', 'D0', 'N1']

## M250-S265: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['R0', 'D0', 'N1', 'D1']
  - REWRITE N0 (N): claude: Raising an unrelated lamp's supply voltage by a vague 'further small amount' before measuring the load is a pointless action with odd wording.

## M250-S266: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): TA1EB and T3C5C omit the numerical value and unit retained by the other same-quantity variants, although the authors explicitly identify these as intentional numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite ['N0'], pending 0, slightly artificial ['N1', 'D0', 'D1']
  - REWRITE N0 (N): claude: Adding an unspecified 'small amount of resistive load' to an unrelated battery charger as a step before measuring transformer losses is a pointless action in odd wording.

## M250-S267: ADMIT

- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag insufficient_boundary_condition (medium): The added capacitance in TDA93/TE837 is not stated to be uncharged; the authors' wiring (C -> C+q with zero initial voltage) relies on the natural reading that the capacitance is simply increased, which I accept.
- gpt: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag rendering_not_minimal (medium): The numeral-free controls omit the numerical value and unit required by the general variant format, although the authors explicitly disclose this departure and do not claim that these controls preserve the number and unit.
  - flag other (medium): Because the description introduces two batteries, 'the battery' in T77C0 and TC55C can refer to either circuit, making their C versus D role ambiguous without changing the answer.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["insufficient_boundary_condition"], "gpt": ["other", "rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D1', 'D0', 'N1']
  - REWRITE N0 (N): claude: Wiring an unspecified 'small amount of capacitance' onto an unrelated flash unit, timed to the closing of the circuit's switch, is a pointless action in wording no one would use.

## M250-S268: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D0', 'R1', 'D1', 'N1']
  - REWRITE N0 (N): claude: Adding an 'ideal battery of small emf' in series with a doorbell's cell before closing the circuit switch is a pointless action in wording no one would use.

## M250-S270: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['N1', 'N0', 'R0', 'D0', 'D1'], pending 0, slightly artificial ['R1']
  - REWRITE N1 (N): claude: A conveyor running along a moving trolley that carried the recorder only in an earlier run is an implausible contraption, described in convoluted wording.
  - REWRITE N0 (N): claude: A conveyor belt on the trolley carrying a toolbox along it is an implausible object and pointless action in this Doppler scene.
  - REWRITE R0 (R): claude: A conveyor belt carrying the recorder along a moving trolley is an implausible contraption that does not belong in this scene.
  - REWRITE D0 (D): claude: A conveyor belt on a trolley carrying a toolbox at a set speed is an implausible, pointless contrivance in this acoustics scene.
  - REWRITE D1 (D): claude: A conveyor on a trolley carrying the recorder at a set speed in an earlier run is an implausible contrivance for this scene.

## M250-S271: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- pass-1 stratum differences (claude, information only): T94AF authors K judge C, T9574 authors K judge C
- pass-1 stratum differences (gpt, information only): T94AF authors K judge C, T9574 authors K judge C
- naturalness: 10 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['N1', 'R1', 'D1', 'R0']
  - REWRITE D0 (D): claude: Welding an extra length onto the laboratory wall railing, timed to the fitting of the rod's clamp, is a pointless action that does not belong in this experiment.
  - REWRITE N0 (N): claude: Welding an extension onto a laboratory wall railing before fitting a clamp in a Kundt's tube experiment is a pointless, implausible action for this scene.

## M250-S272: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The certified R answers require 1.5 cm/s to be the original tap's isolated contribution and require additive outlet contributions, whereas the problem specifies 1.5 cm/s as the actual water-surface speed.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (medium): The C cancellation relations fix the resonances at L + e = 13 lam/4 and 15 lam/4 (108.9 cm and 125.6 cm, end correction dropped) and set t = (L_n - q)/vw, which gives negative times for the listed initial lengths 130 cm and 190 cm, so the illustrative mode numbers are wrong for those values although the difference, and hence every certified answer, is correct.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag missing_assumption (high): The certified R answers require 1.5 cm/s to be the original tap's isolated contribution and require additive outlet contributions, whereas the problem specifies 1.5 cm/s as the actual water-surface speed.
  - flag rendering_not_minimal (high): T3D7A and TB8E5 omit the number and unit present in their numerical counterparts, contrary to the review instructions' requirement that variants preserve the number and unit.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T3D7A and TB8E5 omit the number and unit present in their numerical counterparts, contrary to the review instructions' requirement that variants preserve the number and unit.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- pass-1 stratum differences (gpt, information only): T9749 authors R judge C, TEA1B authors R judge C
- naturalness: 8 sentences, rewrite ['N1', 'N0'], pending 0, slightly artificial ['D0', 'R1', 'D1']
  - REWRITE N1 (N): claude: The sentence is garbled ('had a second outlet open that alone would lower ... for an earlier run only') in wording no one would use, and gives no rate.
  - REWRITE N0 (N): claude: Opening a pond outlet timed to the resonance experiment, phrased as one that 'alone would lower the level', is an unmotivated event in stilted wording no one would use.

## M250-S273: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'R1', 'D1']

## M250-S274: REJECT

- gpt: validity is invalid
- gpt: high flag failed_transformation_identity: The certified answers do not follow from the supplied constants and relations at their displayed precision: the base result is 27.006092 pm, and additions of 36, 55 and 83 mT give 28.950531, 29.976762 and 31.489103 pm, respectively.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag failed_transformation_identity (high): The certified answers do not follow from the supplied constants and relations at their displayed precision: the base result is 27.006092 pm, and additions of 36, 55 and 83 mT give 28.950531, 29.976762 and 31.489103 pm, respectively.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D0', 'D1', 'N0']

## M250-S275: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['D0', 'N0'], pending 0, slightly artificial ['R1', 'D1', 'N1']
  - REWRITE D0 (D): claude: Moving the edge of a metal strip on an unrelated chip by a sub-nanometre amount is a pointless, implausible action for this scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)
  - REWRITE N0 (N): claude: Nudging the edge of a metal strip on an unrelated chip sitting beside the apparatus is a pointless action with no role in the scene.

## M250-S276: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N1', 'N0', 'R0']

## M250-S277: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1', 'D0', 'R1', 'N0']

## M250-S278: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N1', 'D1', 'R0', 'N0']

## M250-S279: REJECT

- gpt: validity is invalid
- gpt: high flag invalid_numerical_precision: For both relevant sentences at q = 3.7 cm, the certified 6.7855 MHz does not correctly round the calculated 6.7855928 MHz; at the displayed precision it should be 6.7856 MHz.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): T1355 does not repeat 'at the same rotation frequency', and the authors' quantity label and wiring speak of 'a further ring', which no sentence mentions; neither changes the answer under the natural reading that the stated 600 Hz still holds.
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag invalid_numerical_precision (high): For both relevant sentences at q = 3.7 cm, the certified 6.7855 MHz does not correctly round the calculated 6.7855928 MHz; at the displayed precision it should be 6.7856 MHz.
- note: 5.3 rounding guard: gpt flags precision high while a Claude judge accepts it; the status above is not changed, the standard's owner decides
- naturalness: 6 sentences, rewrite ['D0', 'R0'], pending 0, slightly artificial ['D1', 'R1', 'N1', 'N0']
  - REWRITE D0 (D): claude: Enlarging the pump's pulley is a pointless, unexplained action stated in odd wording that does not belong in the scene.
  - REWRITE R0 (R): claude: Enlarging the radius of a source fixed to the rotor rim, with no stated timing, contradicts the setup just given and is incoherent in place.

## M250-S28: REJECT

- gpt: validity is invalid
- gpt: high flag missing_assumption: The problem explicitly allows an unspecified top speed without ensuring it exceeds 30 m/s, and it does not specify motion after reaching a binding cap, so the base, disconnected-sentence and tuning-kit certified answers require unstated modelling conditions.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag missing_assumption (high): The problem explicitly allows an unspecified top speed without ensuring it exceeds 30 m/s, and it does not specify motion after reaching a binding cap, so the base, disconnected-sentence and tuning-kit certified answers require unstated modelling conditions.
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N1', 'R1', 'R0', 'D1', 'N0', 'D0']

## M250-S280: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['R1', 'R0'], pending 0, slightly artificial ['D1', 'N1', 'N0', 'D0']
  - REWRITE R1 (R): claude: Raising the initial orbit by 470 km before the first burn, with no stated means, contradicts a transfer said to be done by exactly two burns and reads as an incoherent change to the scenario.
  - REWRITE R0 (R): claude: Saying the initial orbit's altitude 'is increased by 470 km' right after fixing it at 100 km reads as a self-contradictory edit rather than part of the situation.

## M250-S281: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite ['R0', 'R1', 'N0', 'D0'], pending 0, slightly artificial ['D1', 'N1']
  - REWRITE R0 (R): claude: A planet accreting enough rock to grow by 310 km in radius is an implausible event that does not belong in a launch scenario.
  - REWRITE R1 (R): claude: A planet accreting 310 km of radius shortly before a probe launch is a physically implausible event for this scene.
  - REWRITE N0 (N): claude: A moon accreting rock and 'gaining a small amount of radius' during a probe launch is an implausible event with wording no one would use.
  - REWRITE D0 (D): claude: A moon accreting enough rock to gain 310 km of radius is an implausible event for this launch scenario.

## M250-S282: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T37E0 specifies an expansion without specifying the final surface temperature or preserving the peak wavelength, so its certified luminosities require an unstated thermal condition.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T37E0 specifies an expansion without specifying the final surface temperature or preserving the peak wavelength, so its certified luminosities require an unstated thermal condition.
- naturalness: 6 sentences, rewrite ['D1', 'N0', 'D0', 'R1', 'R0', 'N1'], pending 0, slightly artificial none
  - REWRITE D1 (D): claude: A star's radius cannot be increased for one observation, so the sentence describes an implausible, incoherent event.
  - REWRITE N0 (N): claude: Increasing the radius of a star's dust disc rim is not an action anyone can perform, and 'a small part of the radius of the Sun' is unnatural wording.
  - REWRITE D0 (D): claude: A circumstellar dust disc's rim being 'increased' by a stated amount is not a plausible event, and the wording is unnatural.
  - REWRITE R1 (R): claude: Increasing a star's radius before evaluating its luminosity is an impossible action that no one would describe this way.
  - REWRITE R0 (R): claude: A star's radius simply being increased by a stated amount is not a plausible event in this scene, and the wording is unnatural.
  - REWRITE N1 (N): claude: A star's radius cannot be increased for one observation only, so the sentence describes an implausible action.

## M250-S29: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N0', 'R1', 'N1', 'D0']

## M250-S31: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R0', 'N0', 'D1', 'D0', 'C1', 'R1', 'N1']

## M250-S32: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The claims for the trolley sentences (TFBC0, TDC1D) label the quantity 'a weight fixed to the block' although the weight is fixed to the trolley; a metadata label slip that does not affect any answer or stratum.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'N0', 'K0', 'D0', 'K1']

## M250-S34: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T96D5 does not explicitly place the tilt before launch and final clamping, so its certified distance requires an additional timing condition.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): T96D5 'The incline is then tilted 13 degrees more steeply' does not fix when the tilt happens relative to the launch, and following the scene clause's 'clamped before the sphere is launched' it can be read as occurring after the clamping/launch, so the certified R reading (tilt before the roll) is the intended but not the only reading.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T96D5 does not explicitly place the tilt before launch and final clamping, so its certified distance requires an additional timing condition.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['D1', 'D0']
  - REWRITE N0 (N): claude: Tilting a bystander solar panel during a rolling-sphere experiment is a pointless action that does not belong in this scene.

## M250-S35: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The numeral-free controls T3E4C and T0789 do not preserve the number and unit requested for sentence variants, although the authors explicitly disclose this departure and do not claim that these controls preserve them.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 8 sentences, rewrite ['N0'], pending 0, slightly artificial ['N1', 'D1', 'D0']
  - REWRITE N0 (N): claude: Letting out line on a fishing reel that lies apart from the pendulum is a pointless action unconnected to the scene, and the 'then' sequencing is incoherent.

## M250-S36: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TFE49 does not establish whether the stated 0.3 m pivot offset applies before or after the movement preceding the oscillations, allowing materially different periods.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (low): T1D34 moves the pivot of the rod while it is described as swinging, and TFE49 revises the stated 0.3 m pivot position, so the reader must infer that the period asked is the one after the move; the natural reading gives the certified answer.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TFE49 does not establish whether the stated 0.3 m pivot offset applies before or after the movement preceding the oscillations, allowing materially different periods.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'N0', 'D0']

## M250-S37: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'D1', 'D0']

## M250-S38: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The problem explicitly identifies 62 degrees as the initial setup angle but does not specify the final equilibrium angle or state that it remains unchanged, although the requested force depends on that final angle.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The problem explicitly identifies 62 degrees as the initial setup angle but does not specify the final equilibrium angle or state that it remains unchanged, although the requested force depends on that final angle.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R1', 'D0', 'N0', 'N1']

## M250-S41: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: TFAEF does not specify whether its displacement precedes the initial 80 mN measurement or follows the stated 60 cm separation, so its claimed final separation and certified answer are not uniquely determined.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): TFAEF's 'Before the force was measured' could in principle be read as preceding the initial 80 mN state rather than the asked force; the base clause 'the force asked for is the one at the final separation, after all their moves' and the fact that the 80 mN is not described as a measurement make the R reading the natural one.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): TFAEF does not specify whether its displacement precedes the initial 80 mN measurement or follows the stated 60 cm separation, so its claimed final separation and certified answer are not uniquely determined.
- pass-1 stratum differences (claude, information only): T81A0 authors C judge K, TAA47 authors C judge K
- pass-1 stratum differences (gpt, information only): TFAEF authors R judge D
- naturalness: 8 sentences, rewrite ['N0', 'D0'], pending 0, slightly artificial ['N1', 'D1']
  - REWRITE N0 (N): claude: Moving unrelated bar magnets a few centimetres apart is a pointless action with no place in this electrostatics scene.
  - REWRITE D0 (D): claude: Moving bystander bar magnets a precise 26 cm further apart is a pointless action that does not belong in this electrostatics scene.
  - REWRITE D0 (D): claude: rated artificial while its R twin R0 is natural (more than one level worse)

## M250-S42: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D0', 'N1', 'D1']

## M250-S43: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): T27DA and T0DBA omit the numerical emf and unit present in their twins, departing from the review instructions' general same-number requirement, although the authors explicitly identify these as numeral-free controls.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'N0', 'N1', 'R1', 'R0']

## M250-S45: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['N0', 'R1', 'N1', 'R0', 'D0']

## M250-S51: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['N0', 'D1', 'R0', 'R1', 'N1', 'D0']

## M250-S52: REJECT

- gpt: validity is invalid
- gpt: high flag inconsistent_units: For T2F5B and T162D, the authors report unit=null and claim that the unit was replaced, although both rendered sentences explicitly retain the unit kelvin.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T2F5B and T162D replace the specified 17 K with an unspecified 'few kelvin', violating the review requirement that variants preserve the same numerical quantity.
  - flag inconsistent_units (high): For T2F5B and T162D, the authors report unit=null and claim that the unit was replaced, although both rendered sentences explicitly retain the unit kelvin.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T2F5B and T162D replace the specified 17 K with an unspecified 'few kelvin', violating the review requirement that variants preserve the same numerical quantity.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R1', 'D0', 'D1', 'N1', 'N0']

## M250-S53: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): TA69F and TC890 replace their numerical twins' specified 13 K with an unspecified 'few kelvin', violating the review instructions' requirement that variants of the same quantity preserve its number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TA69F and TC890 replace their numerical twins' specified 13 K with an unspecified 'few kelvin', violating the review instructions' requirement that variants of the same quantity preserve its number and unit.
- naturalness: 10 sentences, rewrite ['K1'], pending 0, slightly artificial ['N0', 'N1', 'K0', 'R1', 'D0']
  - REWRITE K1 (K): claude: Foam insulation burning away completely merely because the temperature difference exceeds 75 K is physically implausible for a building wall.

## M250-S54: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T298E and TDB9C replace the specified 4.5 cm thickness with 'thin', violating the review instructions' requirement that variants concerning the same quantity preserve its number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T298E and TDB9C replace the specified 4.5 cm thickness with 'thin', violating the review instructions' requirement that variants concerning the same quantity preserve its number and unit.
- naturalness: 6 sentences, rewrite ['N0', 'D0'], pending 0, slightly artificial ['R0', 'R1', 'N1', 'D1']
  - REWRITE N0 (N): claude: Casting a metal layer around an unrelated hanging bracket is a pointless action that does not belong in this radiation scene.
  - REWRITE D0 (D): claude: Casting a layer of metal around a bracket hanging nearby is a pointless, out-of-place action in a scene about measuring radiated power.

## M250-S56: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: T5F2C describes a lamp operating during a past steady run without establishing that it operates during the run being evaluated, leaving the present cooling load and requested power undetermined.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (medium): For TC1B7 and T5F2C the base clause 'must remove heat from it at a steady rate of 200 W' can be read as the total removal rate, which would leave the answer at 60.6 W; the 'Heat leaks into the interior, so' wording supports the authors' leak-only reading and wiring Pc + q.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): T5F2C describes a lamp operating during a past steady run without establishing that it operates during the run being evaluated, leaving the present cooling load and requested power undetermined.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": ["other"], "gpt": []}
- naturalness: 10 sentences, rewrite none, pending 0, slightly artificial ['D1', 'R0', 'R1', 'N1']

## M250-S57: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The scene_clause_note calls the second tank 'empty', whereas the problem says it holds some water of its own; the note's conclusion (the second tank is not connected to the engine) still holds, and 'the same temperature' in the second-tank sentences has a slightly vague referent, neither of which affects any answer.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N0', 'N1']

## M250-S65: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 6 sentences, rewrite ['R1'], pending 0, slightly artificial ['D0', 'D1', 'N0', 'N1']
  - REWRITE R1 (R): claude: Saying the fibre end was held in a liquid contradicts the opening statement that light enters the fibre from air, making the scene self-contradictory.

## M250-S66: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag other (low): The screen sentences say 'the screen' although the problem introduces no screen; this does not affect the angular answer.
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N0', 'N1', 'D1', 'R1', 'D0']

## M250-S67: REJECT

- gpt: validity is invalid
- gpt: high flag other: For T146E, the authors incorrectly identify an operating power rating as a physical damage threshold and assert changed physics outside that rating, neither of which follows from the sentence.
- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 FAIL, validity invalid, category SOLVER_INVALID
  - flag other (high): For T146E, the authors incorrectly identify an operating power rating as a physical damage threshold and assert changed physics outside that rating, neither of which follows from the sentence.
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['R1', 'K1', 'D1', 'N1', 'D0', 'N0']

## M250-S71: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): TA8F1 and TCF8E omit the 55 nm value carried by the other wavelength-shift sentences, violating the review instructions' numerical-matching requirement even though the packet explicitly identifies these omissions as intentional numeral-free controls.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: TA8F1 and TCF8E omit the 55 nm value carried by the other wavelength-shift sentences, violating the review instructions' numerical-matching requirement even though the packet explicitly identifies these omissions as intentional numeral-free controls.
- pass-1 stratum differences (claude, information only): T5707 authors C judge K, TB26A authors C judge K
- pass-1 stratum differences (gpt, information only): T5707 authors C judge K, TB26A authors C judge K
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'D1', 'D0', 'N0']

## M250-S73: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag inconsistent_units (low): The relation E1 = hc**2/(8*mc2*L**2) mixes hc in eV nm with mc2 in keV, so a keV-to-eV conversion is implicit; the certified numbers use it correctly.
- gpt: pass-2 PASS, validity invalid, category SOLVER_INVALID
  - flag rendering_not_minimal (high): T425C and T6BE7 omit the number and unit present in their numerical twins, contrary to the assignment's explicit requirement that variants of a quantity retain the same number and unit.
  - warning: validity invalid rests only on 5.3b-guarded flags; the other judge decides
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T425C and T6BE7 omit the number and unit present in their numerical twins, contrary to the assignment's explicit requirement that variants of a quantity retain the same number and unit.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['D0', 'R1', 'N0', 'D1', 'R0']

## M250-S77: ADMIT

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
  - flag rendering_not_minimal (medium): The numeral-free controls omit the number and unit carried by their twins, so they depart from the general same-number-and-unit requirement for sentence variants; this departure is explicitly disclosed rather than falsely claimed to be a numerical minimal pair.
- note: judges disagree on medium flags (recorded, not a rejection): {"claude": [], "gpt": ["rendering_not_minimal"]}
- naturalness: 6 sentences, rewrite ['N0', 'R1', 'D0'], pending 0, slightly artificial ['R0', 'N1', 'D1']
  - REWRITE N0 (N): claude: Rebuilding a barrier on a chip from a different material 'before the electron arrives' is an implausible event on the timescale of a single electron's approach.
  - REWRITE R1 (R): claude: Rebuilding the barrier from a different material just before the electron approaches is an implausible action that contradicts the stated 8 eV height, with an ambiguous 'it'.
  - REWRITE D0 (D): claude: Rebuilding a barrier from a different material in the time before a single electron arrives is an incoherent action for this scene.

## M250-S82: REJECT

- gpt: validity is invalid
- gpt: high flag insufficient_boundary_condition: The question does not identify the target epoch as recording, and a temperature increase before recording does not specify the temperature remaining at recording, so the temporal variants do not determine unique answers.
- claude: pass-2 PASS, validity valid, category SOLVER_VALID_LANGUAGE_AMBIGUOUS
  - flag other (low): With T099E/TFD41 the question asks for the peak of 'the second star' in the present tense without tying it to the recorded spectrum, so a reader could take the star's post-outburst temperature (3850 K, 1.646 eV) rather than the recorded 2900 K.
- gpt: pass-2 FAIL, validity invalid, category ANSWER_AMBIGUOUS
  - flag insufficient_boundary_condition (high): The question does not identify the target epoch as recording, and a temperature increase before recording does not specify the temperature remaining at recording, so the temporal variants do not determine unique answers.
  - flag rendering_not_minimal (high): T2C66 and TFD41 replace 950 K with an unspecified small amount, contrary to the review instructions' requirement that variants of the same quantity preserve its number and unit.
  - warning: 5.3b judge error (not counted): high flag rendering_not_minimal: T2C66 and TFD41 replace 950 K with an unspecified small amount, contrary to the review instructions' requirement that variants of the same quantity preserve its number and unit.
- naturalness: 6 sentences, rewrite none, pending 0, slightly artificial ['R0', 'N0', 'D0']

## M250-S91: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'N1', 'D0', 'N0']

## M250-S93: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['N1', 'N0', 'C1', 'C0', 'D0']

## M250-S94: ADMIT  (ready: admitted and natural)

- claude: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- gpt: pass-2 PASS, validity valid, category CERTIFIED_AND_VALIDATED
- naturalness: 8 sentences, rewrite none, pending 0, slightly artificial ['D1', 'D0', 'N0']

