"""Interaction estimands for interventions (plan of record, Section `sec:causal`, G0 item c).

With Delta_h m_X = m(X, intervened) - m(X, clean), the effect of intervention h on prompt X:

    I_presence = Delta_h m_D - Delta_h m_N
    I_role     = Delta_h m_D - Delta_h m_R

D is the cue prompt, N the token-aligned non-numeric sentence (D and N share a gold), and R the
relevant-role twin with the same numeral, unit and position (R has a different certified answer).
`I_presence` may use any declared metric. `I_role` must use a behaviourally comparable outcome
(tracking against each world's own certified answer, answer-mode shares); raw gold-string
log-odds or log-probabilities are never subtracted across worlds, and this module refuses to.

The clean effects m(D) - m(N) and m(D) - m(R) are always returned beside the interaction, and so
are the two Delta values, so that an intervention with a large, equal effect on every prompt (a
general answer component, the head-11 lesson of the Phase-I review) is visible rather than hidden
inside a small interaction.

Inputs are per-item mappings `{item_id: value}`; items are paired by id. An item missing from any
condition, or with a non-finite value, is excluded and listed. Zero paired items give status
`NOT_EVALUATED` with `mean_interaction=None`, never 0.0 (plan of record, missing-data policy).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

EVALUATED = "EVALUATED"
NOT_EVALUATED = "NOT_EVALUATED"


class CrossWorldIncomparableError(ValueError):
    """Raised when a cross-world estimand is requested on a metric that is not comparable."""


@dataclass(frozen=True)
class MetricSpec:
    """A declared outcome metric and whether it may be differenced across worlds.

    `cross_world_comparable` is True only for outcomes defined relative to each world's own
    certified answer (or a shared answer-mode taxonomy), so that D and R values mean the same
    thing even though their golds differ.
    """

    name: str
    cross_world_comparable: bool
    description: str = ""


METRICS: dict[str, MetricSpec] = {
    spec.name: spec
    for spec in (
        MetricSpec("gold_logodds_raw", False,
                   "raw log-odds of the certified answer string against a foil; world-specific gold"),
        MetricSpec("gold_logprob_raw", False, "raw log-probability of the certified answer string"),
        MetricSpec("legacy_s_lp", False, "legacy base-relative S_lp of the bare certified string"),
        MetricSpec("tracking_own_gold", True,
                   "share of samples whose answer tracks the world's own certified answer"),
        MetricSpec("correct_own_gold", True, "semantic correctness against the world's own certified answer"),
        MetricSpec("answer_mode_share", True,
                   "share of samples in a predeclared answer mode (graph-computed foil taxonomy)"),
    )
}


def resolve_metric(metric: str | MetricSpec) -> MetricSpec:
    if isinstance(metric, MetricSpec):
        return metric
    if metric not in METRICS:
        raise ValueError(f"Unknown metric {metric!r}; declare a MetricSpec or use one of {sorted(METRICS)}")
    return METRICS[metric]


@dataclass
class InteractionResult:
    estimand: str
    metric: str
    status: str
    n_items: int
    excluded_items: dict[str, str] = field(default_factory=dict)
    per_item_interaction: dict[str, float] = field(default_factory=dict)
    mean_interaction: float | None = None
    mean_delta_cue: float | None = None
    mean_delta_comparison: float | None = None
    per_item_clean_effect: dict[str, float] = field(default_factory=dict)
    mean_clean_effect: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _interaction(estimand: str, metric: MetricSpec, cue_clean: Mapping[str, float],
                 cue_intervened: Mapping[str, float], cmp_clean: Mapping[str, float],
                 cmp_intervened: Mapping[str, float]) -> InteractionResult:
    conditions = {"cue_clean": cue_clean, "cue_intervened": cue_intervened,
                  "comparison_clean": cmp_clean, "comparison_intervened": cmp_intervened}
    ids = sorted(set().union(*(set(values) for values in conditions.values())))
    excluded: dict[str, str] = {}
    interaction: dict[str, float] = {}
    clean_effect: dict[str, float] = {}
    delta_cue: list[float] = []
    delta_cmp: list[float] = []
    for item in ids:
        missing = [name for name, values in conditions.items() if item not in values]
        if missing:
            excluded[item] = f"missing in {missing}"
            continue
        bad = [name for name, values in conditions.items() if not _finite(values[item])]
        if bad:
            excluded[item] = f"non-finite value in {bad}"
            continue
        d_cue = float(cue_intervened[item]) - float(cue_clean[item])
        d_cmp = float(cmp_intervened[item]) - float(cmp_clean[item])
        interaction[item] = d_cue - d_cmp
        clean_effect[item] = float(cue_clean[item]) - float(cmp_clean[item])
        delta_cue.append(d_cue)
        delta_cmp.append(d_cmp)
    status = EVALUATED if interaction else NOT_EVALUATED
    return InteractionResult(
        estimand=estimand, metric=metric.name, status=status, n_items=len(interaction),
        excluded_items=excluded, per_item_interaction=interaction,
        mean_interaction=_mean(list(interaction.values())),
        mean_delta_cue=_mean(delta_cue), mean_delta_comparison=_mean(delta_cmp),
        per_item_clean_effect=clean_effect, mean_clean_effect=_mean(list(clean_effect.values())),
    )


def interaction_presence(d_clean: Mapping[str, float], d_intervened: Mapping[str, float],
                         n_clean: Mapping[str, float], n_intervened: Mapping[str, float],
                         metric: str | MetricSpec) -> InteractionResult:
    """I_presence = Delta_h m_D - Delta_h m_N, with the clean effect m(D) - m(N). Any declared metric."""

    return _interaction("I_presence", resolve_metric(metric), d_clean, d_intervened, n_clean, n_intervened)


def interaction_role(d_clean: Mapping[str, float], d_intervened: Mapping[str, float],
                     r_clean: Mapping[str, float], r_intervened: Mapping[str, float],
                     metric: str | MetricSpec) -> InteractionResult:
    """I_role = Delta_h m_D - Delta_h m_R, with the clean effect m(D) - m(R).

    Raises `CrossWorldIncomparableError` for a metric not flagged cross-world comparable: D and R
    have different certified answers, so raw gold-string scores cannot be subtracted between them.
    """

    spec = resolve_metric(metric)
    if not spec.cross_world_comparable:
        raise CrossWorldIncomparableError(
            f"I_role needs a behaviourally comparable outcome; metric {spec.name!r} is world-specific "
            "(raw gold-string scores are never subtracted across worlds with different golds)")
    return _interaction("I_role", spec, d_clean, d_intervened, r_clean, r_intervened)


def cue_independence(result: InteractionResult, *, tolerance: float) -> str:
    """Descriptive reading of whether an intervention's effect is cue-independent.

    Returns `NOT_EVALUATED` without paired items; `GENERAL_COMPONENT_CANDIDATE` when both Delta
    means exceed `tolerance` in absolute value and the mean interaction is within it (a large,
    equal effect on the cue and comparison prompts); `CUE_SPECIFIC_CANDIDATE` when the mean
    interaction exceeds the tolerance; `NO_EFFECT_WITHIN_TOLERANCE` otherwise. This is a point
    reading for reports, not an inferential test.
    """

    if result.status != EVALUATED or result.mean_interaction is None:
        return NOT_EVALUATED
    if abs(result.mean_interaction) > tolerance:
        return "CUE_SPECIFIC_CANDIDATE"
    if abs(result.mean_delta_cue or 0.0) > tolerance and abs(result.mean_delta_comparison or 0.0) > tolerance:
        return "GENERAL_COMPONENT_CANDIDATE"
    return "NO_EFFECT_WITHIN_TOLERANCE"
