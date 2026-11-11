"""G0 item (c): interaction estimands refuse cross-world raw scores and never default to zero."""

from __future__ import annotations

import pytest

from physmon.causal.interaction import (
    NOT_EVALUATED,
    CrossWorldIncomparableError,
    MetricSpec,
    cue_independence,
    interaction_presence,
    interaction_role,
)


def test_presence_interaction_and_clean_effect_are_computed_per_item():
    result = interaction_presence(
        d_clean={"a": 1.0, "b": 2.0}, d_intervened={"a": 4.0, "b": 2.0},
        n_clean={"a": 0.5, "b": 1.0}, n_intervened={"a": 1.5, "b": 1.0},
        metric="gold_logodds_raw",
    )
    assert result.status == "EVALUATED"
    assert result.per_item_interaction == {"a": 2.0, "b": 0.0}
    assert result.mean_interaction == 1.0
    assert result.per_item_clean_effect == {"a": 0.5, "b": 1.0}
    assert result.mean_clean_effect == 0.75
    assert result.mean_delta_cue == 1.5 and result.mean_delta_comparison == 0.5


def test_role_interaction_refuses_raw_gold_scores():
    values = {"a": 0.0}
    for metric in ("gold_logodds_raw", "gold_logprob_raw", "legacy_s_lp",
                   MetricSpec("custom_raw", cross_world_comparable=False)):
        with pytest.raises(CrossWorldIncomparableError):
            interaction_role(values, values, values, values, metric=metric)


def test_role_interaction_on_tracking_outcome():
    result = interaction_role(
        d_clean={"s1": 0.9}, d_intervened={"s1": 0.5}, r_clean={"s1": 0.95}, r_intervened={"s1": 0.9},
        metric="tracking_own_gold",
    )
    assert result.estimand == "I_role"
    assert result.per_item_interaction["s1"] == pytest.approx(-0.35)
    assert result.per_item_clean_effect["s1"] == pytest.approx(-0.05)


def test_missing_and_non_finite_items_are_excluded_and_listed():
    result = interaction_presence(
        d_clean={"a": 1.0, "b": 1.0, "c": float("nan")}, d_intervened={"a": 2.0, "b": 1.0, "c": 1.0},
        n_clean={"a": 1.0, "c": 1.0}, n_intervened={"a": 1.0, "c": 1.0}, metric="correct_own_gold",
    )
    assert result.n_items == 1
    assert set(result.excluded_items) == {"b", "c"}


def test_zero_paired_items_is_not_evaluated_not_zero():
    result = interaction_presence({"a": 1.0}, {"a": 1.0}, {"b": 1.0}, {"b": 1.0}, metric="correct_own_gold")
    assert result.status == NOT_EVALUATED
    assert result.mean_interaction is None and result.mean_clean_effect is None
    assert cue_independence(result, tolerance=0.1) == NOT_EVALUATED


def test_equal_large_effect_reads_as_general_component():
    # The head-11 pattern: the intervention moves cue and comparison prompts by the same amount.
    result = interaction_presence(
        d_clean={"a": 0.0, "b": 0.0}, d_intervened={"a": 3.76, "b": 3.77},
        n_clean={"a": 0.0, "b": 0.0}, n_intervened={"a": 3.77, "b": 3.76}, metric="gold_logodds_raw",
    )
    assert abs(result.mean_interaction) < 1e-9
    assert cue_independence(result, tolerance=0.5) == "GENERAL_COMPONENT_CANDIDATE"


def test_unknown_metric_name_is_rejected():
    with pytest.raises(ValueError):
        interaction_presence({}, {}, {}, {}, metric="probability")
