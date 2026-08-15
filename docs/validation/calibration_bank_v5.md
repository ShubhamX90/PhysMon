# Calibration Bank v5

## CAL-V5-001 -- valid_irrelevant_variable

Problem: A cart moves with v0=2 m/s and a=3 m/s^2 for t=4 s. The cart is painted blue. What is final velocity?

Expected judgment: valid; color is irrelevant

Explanation: v=v0+at, relevant variables v0,a,t; color absent; answer invariant.

Repair: No repair.

## CAL-V5-002 -- subtly_relevant_variable

Problem: A block slides on a red surface where red indicates high friction. What is acceleration?

Expected judgment: invalid; color changes friction

Explanation: The cue is not irrelevant because it changes friction coefficient.

Repair: Rewrite so color has no physical role.

## CAL-V5-003 -- missing_assumption

Problem: A projectile is launched; find range. Air resistance is not specified.

Expected judgment: repair_required

Explanation: Without air-resistance/frame assumptions the invariant answer is under-specified.

Repair: Add no-air-resistance assumption.

## CAL-V5-004 -- ambiguous_target

Problem: A circuit has voltage and current. What is the value?

Expected judgment: invalid

Explanation: Target quantity is ambiguous.

Repair: Specify voltage, current, resistance, or power.

## CAL-V5-005 -- semantic_drift

Problem: Variant changes mass of object A while claiming cue-only edit.

Expected judgment: invalid

Explanation: Changing governing mass changes answer.

Repair: Keep governing mass fixed.

## CAL-V5-006 -- valid_frame_transform

Problem: Speed is given as 36 km/h or 10 m/s; ask for m/s.

Expected judgment: valid

Explanation: Equivalent renderings denote same speed.

Repair: No repair.

## CAL-V5-007 -- invalid_frame_transform

Problem: Treat rpm and Hz without specifying cycles/revolutions conversion.

Expected judgment: repair_required

Explanation: Frame/unit conversion is underspecified.

Repair: State exact conversion.

## CAL-V5-008 -- dimensional_inconsistency

Problem: Use F=ma but mass is given in seconds.

Expected judgment: invalid

Explanation: Units violate dimensional consistency.

Repair: Correct units.

## CAL-V5-009 -- unit_compatible_relevant

Problem: Distractor has same units and is actually the spring constant used in F=kx.

Expected judgment: invalid

Explanation: Cue is governing despite unit compatibility.

Repair: Use separate non-interacting system.

## CAL-V5-010 -- unnatural_wording

Problem: Prompt includes incoherent cue sentence.

Expected judgment: repair_required

Explanation: Naturalness/difficulty shift may invalidate human judgment.

Repair: Rewrite cue sentence.

## CAL-V5-011 -- invalid_solver_derivation

Problem: Template claims v=v0+at but computes v=v0-at.

Expected judgment: invalid

Explanation: Derivation contradicts governing law.

Repair: Fix derivation.

## CAL-V5-012 -- valid_representation_transform

Problem: Energy is rendered as 1000 J and 1 kJ, answer requested in J.

Expected judgment: valid

Explanation: Representation changes only; physical value invariant.

Repair: No repair.

## CAL-V5-013 -- parser_ambiguity

Problem: Answer text says 'about 5, maybe 6 N'.

Expected judgment: repair_required

Explanation: Final answer ambiguous for parser audit.

Repair: Require single final answer.

## CAL-V5-014 -- wrong_units

Problem: Correct number with incompatible unit.

Expected judgment: invalid

Explanation: Unit mismatch changes physical answer.

Repair: Correct unit.

## CAL-V5-015 -- borderline_nearmatch

Problem: Separate object B has value numerically close to answer but non-interacting.

Expected judgment: valid_but_high_risk

Explanation: Cue is formally irrelevant but may distract models.

Repair: Flag high risk, do not exclude solely for proximity.
