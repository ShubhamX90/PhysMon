# Mutation Semantics Audit v6

The mutation suite tests the current symbolic verifier's numerical-answer consistency, cue-symbol independence, structured-parameter plausibility, and parseability. It does not validate full natural-language semantics, assumption sufficiency, frame equivalence, or complete dimensional algebra.

## `algebraically_equivalent_expression`
- current_name: `algebraically_equivalent_expression`
- actual_code_change: adds algebraic zero
- verifier_property_tested: acceptance of numerically equivalent expression
- confounds: not NL semantics
- recommended_name: `algebraically_equivalent_expression`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `cue_leakage_after_assumption_text_removal`
- current_name: `cue_leakage_after_assumption_text_removal`
- actual_code_change: removes proof text and leaks cue into equation
- verifier_property_tested: cue leakage detection
- confounds: does not validate assumption sufficiency
- recommended_name: `cue_leakage_after_assumption_text_removal`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `equivalent_unit_formatting`
- current_name: `equivalent_unit_formatting`
- actual_code_change: rewrites answer display with same value/unit
- verifier_property_tested: parser/display stability
- confounds: not unit conversion equivalence
- recommended_name: `equivalent_unit_formatting_display_only`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `exact_noop_control`
- current_name: `exact_noop_control`
- actual_code_change: metadata-only copy
- verifier_property_tested: serialization control
- confounds: not substantive mutation evidence
- recommended_name: `exact_noop_control`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `harmless_serialization_formatting`
- current_name: `harmless_serialization_formatting`
- actual_code_change: changes prompt serialization when possible
- verifier_property_tested: serialization robustness
- confounds: may not alter rendered task semantics
- recommended_name: `harmless_serialization_formatting`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `incorrect_canonical_answer`
- current_name: `incorrect_canonical_answer`
- actual_code_change: corrupts stored correct_answer fields
- verifier_property_tested: incorrect canonical answer detection
- confounds: not target quantity semantics
- recommended_name: `incorrect_canonical_answer`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `negative_parameter_value`
- current_name: `negative_parameter_value`
- actual_code_change: negates one structured parameter value
- verifier_property_tested: numeric consistency and basic physical plausibility
- confounds: not dimensional corruption
- recommended_name: `negative_parameter_value`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `replace_governing_variable_with_cue`
- current_name: `replace_governing_variable_with_cue`
- actual_code_change: substitutes a cue symbol into governing_equation_sympy
- verifier_property_tested: cue-symbol independence and numeric consistency
- confounds: does not test semantic relevance in prose
- recommended_name: `replace_governing_variable_with_cue`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `semantics_preserving_variable_renaming`
- current_name: `semantics_preserving_variable_renaming`
- actual_code_change: renames one structured symbol consistently
- verifier_property_tested: symbol-table consistency and numeric equivalence
- confounds: limited to structured symbols
- recommended_name: `semantics_preserving_variable_renaming`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `sign_inversion_governing_expression`
- current_name: `sign_inversion_governing_expression`
- actual_code_change: negates governing_equation_sympy
- verifier_property_tested: numeric answer consistency
- confounds: does not test natural-language prompt alignment
- recommended_name: `sign_inversion_governing_expression`
- supported_claim: Evidence about current SymbolicVerifier behaviour on structured YAML fields only.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.

## `true_unit_metadata_corruption`
- current_name: `true_unit_metadata_corruption`
- actual_code_change: would change structured unit metadata
- verifier_property_tested: unsupported because SymbolicVerifier has no dimensional algebra checker
- confounds: no measured unit rejection
- recommended_name: `true_unit_metadata_corruption`
- supported_claim: No measured result; true dimensional mutation unsupported by current verifier.
- unsupported_claim: full natural-language, dimensional, assumption-sufficiency, or frame-equivalence validation.
