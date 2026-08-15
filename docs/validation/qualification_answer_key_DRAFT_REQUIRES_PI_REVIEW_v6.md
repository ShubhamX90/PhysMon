# Qualification Answer Key v6

## Case 1
- Variant: A charge standard is labelled as {charge_render}.

What is that charge in coulombs?
- Variant: A charge standard is labelled as {charge_render}.

What is that charge in coulombs?
- Variant: A charge standard is labelled as {charge_render}.

What is that charge in coulombs?
- Variant: A charge standard is labelled as {charge_render}.

What is that charge in coulombs?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: valid
- Explanation: Cue varies but governing expression does not use it. Governing law: unit_rendering_charge. Relevant variables: q_base. Cue: charge_render.

## Case 2
- Variant: Meter A displays the current as {current_render}.

What is that current in amperes?
- Variant: Meter A displays the current as {current_render}.

What is that current in amperes?
- Variant: Meter A displays the current as {current_render}.

What is that current in amperes?
- Variant: Meter A displays the current as {current_render}.

What is that current in amperes?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: The changed variable would enter the governing law. Governing law: unit_rendering_current. Relevant variables: I_base. Cue: current_render.

## Case 3
- Variant: Meter A reports the power as 200 W.

What is that power in watts?
- Variant: Meter A reports the power as 0.2 kW.

What is that power in watts?
- Variant: Meter A reports the power as 200 J/s.

What is that power in watts?
- Variant: Meter A reports the power as 200000 mW.

What is that power in watts?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: The task lacks a needed physical condition. Governing law: unit_rendering_power. Relevant variables: P_base. Cue: power_render.

## Case 4
- Variant: A resistor carries current 2.0 A and has resistance 6.0 ohm. The room light switch was toggled 3 s ago.

What voltage is across the resistor?
- Variant: A resistor carries current 2.0 A and has resistance 6.0 ohm. The room light switch was toggled 6 s ago.

What voltage is across the resistor?
- Variant: A resistor carries current 2.0 A and has resistance 6.0 ohm. The room light switch was toggled 12 s ago.

What voltage is across the resistor?
- Variant: A resistor carries current 2.0 A and has resistance 6.0 ohm. The room light switch was toggled 24 s ago.

What voltage is across the resistor?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: The requested quantity is underspecified. Governing law: ohms_law_voltage. Relevant variables: I, R. Cue: elapsed_switch_s.

## Case 5
- Variant: A resistor has voltage 12.0 V across it and resistance 8.0 ohm. The ambient pressure near the bench is 18 kPa.

What power does the resistor dissipate?
- Variant: A resistor has voltage 12.0 V across it and resistance 8.0 ohm. The ambient pressure near the bench is 36 kPa.

What power does the resistor dissipate?
- Variant: A resistor has voltage 12.0 V across it and resistance 8.0 ohm. The ambient pressure near the bench is 72 kPa.

What power does the resistor dissipate?
- Variant: A resistor has voltage 12.0 V across it and resistance 8.0 ohm. The ambient pressure near the bench is 144 kPa.

What power does the resistor dissipate?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: Variants change more than the cue. Governing law: power_from_voltage_and_resistance. Relevant variables: V, R. Cue: ambient_pressure_kpa.

## Case 6
- Variant: Charge A has magnitude 4e-06 C and the field point is 0.3 m away. Use k = 8990000000.0 N·m²/C². A separate source B carries charge 1.0e-6 C, but source B never interacts with charge A or the field point.

What is the electric field magnitude due to charge A at the field point?
- Variant: Charge A has magnitude 4e-06 C and the field point is 0.3 m away. Use k = 8990000000.0 N·m²/C². A separate source B carries charge 3.8e-6 C, but source B never interacts with charge A or the field point.

What is the electric field magnitude due to charge A at the field point?
- Variant: Charge A has magnitude 4e-06 C and the field point is 0.3 m away. Use k = 8990000000.0 N·m²/C². A separate source B carries charge 4.0e-6 C, but source B never interacts with charge A or the field point.

What is the electric field magnitude due to charge A at the field point?
- Variant: Charge A has magnitude 4e-06 C and the field point is 0.3 m away. Use k = 8990000000.0 N·m²/C². A separate source B carries charge 6.0e-6 C, but source B never interacts with charge A or the field point.

What is the electric field magnitude due to charge A at the field point?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: valid
- Explanation: Equivalent unit renderings denote the same physical value. Governing law: electric_field_point_charge. Relevant variables: k_const, q_A, r_A. Cue: q_B_display.

## Case 7
- Variant: Charge A has magnitude 2e-06 C and the field point is 0.2 m away. Use k = 8990000000.0 N·m²/C². In a separate setup B, another field point is 0.10 m from its own charge, but setup B is isolated.

What is the electric field magnitude due to charge A at the field point?
- Variant: Charge A has magnitude 2e-06 C and the field point is 0.2 m away. Use k = 8990000000.0 N·m²/C². In a separate setup B, another field point is 0.19 m from its own charge, but setup B is isolated.

What is the electric field magnitude due to charge A at the field point?
- Variant: Charge A has magnitude 2e-06 C and the field point is 0.2 m away. Use k = 8990000000.0 N·m²/C². In a separate setup B, another field point is 0.20 m from its own charge, but setup B is isolated.

What is the electric field magnitude due to charge A at the field point?
- Variant: Charge A has magnitude 2e-06 C and the field point is 0.2 m away. Use k = 8990000000.0 N·m²/C². In a separate setup B, another field point is 0.30 m from its own charge, but setup B is isolated.

What is the electric field magnitude due to charge A at the field point?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: The rendered values are not equivalent after conversion. Governing law: electric_field_distance_distractor. Relevant variables: k_const, q_A, r_A. Cue: r_B_display.

## Case 8
- Variant: The trolley momentum is recorded as {momentum_render}.

What is that momentum in kg*m/s?
- Variant: The trolley momentum is recorded as {momentum_render}.

What is that momentum in kg*m/s?
- Variant: The trolley momentum is recorded as {momentum_render}.

What is that momentum in kg*m/s?
- Variant: The trolley momentum is recorded as {momentum_render}.

What is that momentum in kg*m/s?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: Units do not match the target quantity. Governing law: unit_rendering_momentum. Relevant variables: p_base. Cue: momentum_render.

## Case 9
- Variant: An inertial sensor reports the acceleration as {acceleration_render}.

What is that acceleration in m/s^2?
- Variant: An inertial sensor reports the acceleration as {acceleration_render}.

What is that acceleration in m/s^2?
- Variant: An inertial sensor reports the acceleration as {acceleration_render}.

What is that acceleration in m/s^2?
- Variant: An inertial sensor reports the acceleration as {acceleration_render}.

What is that acceleration in m/s^2?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: The distractor has compatible units but is a governing variable. Governing law: unit_rendering_acceleration. Relevant variables: a_base. Cue: acceleration_render.

## Case 10
- Variant: A motion sensor reports the cart's speed as 30 m/s.

What is that speed in m/s?
- Variant: A motion sensor reports the cart's speed as 3000 cm/s.

What is that speed in m/s?
- Variant: A motion sensor reports the cart's speed as 108 km/h.

What is that speed in m/s?
- Variant: A motion sensor reports the cart's speed as 30000 mm/s.

What is that speed in m/s?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: The prompt is grammatically or semantically awkward enough to change difficulty. Governing law: unit_rendering_velocity. Relevant variables: v_base. Cue: speed_render.

## Case 11
- Variant: Instrument A reports the applied force as 50 N.

What is that force in newtons?
- Variant: Instrument A reports the applied force as 0.05 kN.

What is that force in newtons?
- Variant: Instrument A reports the applied force as 50000 mN.

What is that force in newtons?
- Variant: Instrument A reports the applied force as 5×10^1 N.

What is that force in newtons?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: invalid
- Explanation: The derivation uses the wrong law or substituted value. Governing law: unit_rendering_force. Relevant variables: F_base. Cue: force_render.

## Case 12
- Variant: A particle initially moving at 5.0 m/s undergoes constant acceleration
of 2.0 m/s² for a duration of 3.0 s. The particle is painted red.

What is the velocity of the particle at the end of this interval?
- Variant: A particle initially moving at 5.0 m/s undergoes constant acceleration
of 2.0 m/s² for a duration of 3.0 s. The particle is painted blue.

What is the velocity of the particle at the end of this interval?
- Variant: A particle initially moving at 5.0 m/s undergoes constant acceleration
of 2.0 m/s² for a duration of 3.0 s. The particle is painted green.

What is the velocity of the particle at the end of this interval?
- Variant: A particle initially moving at 5.0 m/s undergoes constant acceleration
of 2.0 m/s² for a duration of 3.0 s. The particle is painted yellow.

What is the velocity of the particle at the end of this interval?
- Questions: identify governing law, relevant variables, cue relevance, invariance, assumptions, and final verdict.
- Expected verdict: valid
- Explanation: Algebraic or unit representation changes preserve the answer. Governing law: kinematics_constant_acceleration_final_velocity. Relevant variables: v_0, a, t. Cue: paint_color.
