from physmon.validation.mutation_operators import default_mutation_operators


def test_mutation_operators_declare_applicability_and_expected_outcomes():
    operators = default_mutation_operators()
    assert len(operators) >= 10
    assert all(operator.operator_id for operator in operators)
    assert all(operator.expected_outcome for operator in operators)


def test_mutation_operators_do_not_pretend_unsupported_coverage_passes():
    family = {
        "template_id": "CM_B_TEST",
        "cue_type": "nongoverning_distractor",
        "variants": [{"prompt": "A mass m is accelerated by force F while a cue value is present."}],
    }
    results = [operator.apply(family) for operator in default_mutation_operators()]
    statuses = {result.status for result in results}
    assert "coverage_not_supported" in statuses
    assert "executed_control" in statuses
    assert all(result.expected_outcome for result in results)
