# Stage 13 Calibration Bank v6

## cal_v6_00_valid_irrelevant_variable
- Family: `CM_C_006`
- Governing law: unit_rendering_charge
- Relevant variables: q_base
- Designated cue: charge_render
- Canonical answer: 2.0 C
- Expected verdict: valid
- Explanation: Cue varies but governing expression does not use it. Governing law: unit_rendering_charge. Relevant variables: q_base. Cue: charge_render.

## cal_v6_01_subtly_relevant_variable
- Family: `CM_C_008`
- Governing law: unit_rendering_current
- Relevant variables: I_base
- Designated cue: current_render
- Canonical answer: 0.75 A
- Expected verdict: invalid
- Explanation: The changed variable would enter the governing law. Governing law: unit_rendering_current. Relevant variables: I_base. Cue: current_render.

## cal_v6_02_missing_assumption
- Family: `CM_C_004`
- Governing law: unit_rendering_power
- Relevant variables: P_base
- Designated cue: power_render
- Canonical answer: 200 W
- Expected verdict: invalid
- Explanation: The task lacks a needed physical condition. Governing law: unit_rendering_power. Relevant variables: P_base. Cue: power_render.

## cal_v6_03_ambiguous_target
- Family: `CM_A_STD_011`
- Governing law: ohms_law_voltage
- Relevant variables: I, R
- Designated cue: elapsed_switch_s
- Canonical answer: 12.0 V
- Expected verdict: invalid
- Explanation: The requested quantity is underspecified. Governing law: ohms_law_voltage. Relevant variables: I, R. Cue: elapsed_switch_s.

## cal_v6_04_semantic_drift
- Family: `CM_A_STD_012`
- Governing law: power_from_voltage_and_resistance
- Relevant variables: V, R
- Designated cue: ambient_pressure_kpa
- Canonical answer: 18.0 W
- Expected verdict: invalid
- Explanation: Variants change more than the cue. Governing law: power_from_voltage_and_resistance. Relevant variables: V, R. Cue: ambient_pressure_kpa.

## cal_v6_05_valid_frame_transformation
- Family: `CM_B_STD_010`
- Governing law: electric_field_point_charge
- Relevant variables: k_const, q_A, r_A
- Designated cue: q_B_display
- Canonical answer: 399555.6 N/C
- Expected verdict: valid
- Explanation: Equivalent unit renderings denote the same physical value. Governing law: electric_field_point_charge. Relevant variables: k_const, q_A, r_A. Cue: q_B_display.

## cal_v6_06_invalid_frame_transformation
- Family: `CM_B_STD_011`
- Governing law: electric_field_distance_distractor
- Relevant variables: k_const, q_A, r_A
- Designated cue: r_B_display
- Canonical answer: 449500 N/C
- Expected verdict: invalid
- Explanation: The rendered values are not equivalent after conversion. Governing law: electric_field_distance_distractor. Relevant variables: k_const, q_A, r_A. Cue: r_B_display.

## cal_v6_07_dimensional_inconsistency
- Family: `CM_C_012`
- Governing law: unit_rendering_momentum
- Relevant variables: p_base
- Designated cue: momentum_render
- Canonical answer: 12.0 kg*m/s
- Expected verdict: invalid
- Explanation: Units do not match the target quantity. Governing law: unit_rendering_momentum. Relevant variables: p_base. Cue: momentum_render.

## cal_v6_08_unit_compatible_relevant
- Family: `CM_C_013`
- Governing law: unit_rendering_acceleration
- Relevant variables: a_base
- Designated cue: acceleration_render
- Canonical answer: 9.8 m/s^2
- Expected verdict: invalid
- Explanation: The distractor has compatible units but is a governing variable. Governing law: unit_rendering_acceleration. Relevant variables: a_base. Cue: acceleration_render.

## cal_v6_09_unnatural_wording
- Family: `CM_C_001`
- Governing law: unit_rendering_velocity
- Relevant variables: v_base
- Designated cue: speed_render
- Canonical answer: 30.0 m/s
- Expected verdict: invalid
- Explanation: The prompt is grammatically or semantically awkward enough to change difficulty. Governing law: unit_rendering_velocity. Relevant variables: v_base. Cue: speed_render.

## cal_v6_10_invalid_solver_derivation
- Family: `CM_C_002`
- Governing law: unit_rendering_force
- Relevant variables: F_base
- Designated cue: force_render
- Canonical answer: 50.0 N
- Expected verdict: invalid
- Explanation: The derivation uses the wrong law or substituted value. Governing law: unit_rendering_force. Relevant variables: F_base. Cue: force_render.

## cal_v6_11_valid_representation_transformation
- Family: `CM_A_001`
- Governing law: kinematics_constant_acceleration_final_velocity
- Relevant variables: v_0, a, t
- Designated cue: paint_color
- Canonical answer: 11.0 m/s
- Expected verdict: valid
- Explanation: Algebraic or unit representation changes preserve the answer. Governing law: kinematics_constant_acceleration_final_velocity. Relevant variables: v_0, a, t. Cue: paint_color.

## cal_v6_12_valid_irrelevant_variable
- Family: `CM_A_002`
- Governing law: kinematics_constant_acceleration_displacement
- Relevant variables: v_0, a, t
- Designated cue: texture
- Canonical answer: 14.0 m
- Expected verdict: valid
- Explanation: Cue varies but governing expression does not use it. Governing law: kinematics_constant_acceleration_displacement. Relevant variables: v_0, a, t. Cue: texture.

## cal_v6_13_subtly_relevant_variable
- Family: `CM_B_UM_061`
- Governing law: rotational_dynamics_torque_extreme_nearmatch
- Relevant variables: r, F
- Designated cue: torque_reading_B
- Canonical answer: 6.928 N*m
- Expected verdict: invalid
- Explanation: The changed variable would enter the governing law. Governing law: rotational_dynamics_torque_extreme_nearmatch. Relevant variables: r, F. Cue: torque_reading_B.

## cal_v6_14_missing_assumption
- Family: `CM_B_UM_062`
- Governing law: hooke_force_extreme_nearmatch
- Relevant variables: k, x
- Designated cue: force_probe_B
- Canonical answer: 24.48 N
- Expected verdict: invalid
- Explanation: The task lacks a needed physical condition. Governing law: hooke_force_extreme_nearmatch. Relevant variables: k, x. Cue: force_probe_B.

## cal_v6_15_ambiguous_target
- Family: `CM_B_001`
- Governing law: newton_second_law_net_force
- Relevant variables: F_net, m_A
- Designated cue: m_B_display
- Canonical answer: 5.0 m/s^2
- Expected verdict: invalid
- Explanation: The requested quantity is underspecified. Governing law: newton_second_law_net_force. Relevant variables: F_net, m_A. Cue: m_B_display.
