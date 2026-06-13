"""Sensitivity measures for solver-certified counterfactual families.

Reference: `physmon_proposal.pdf` §3.3 (behavioural sensitivity definitions) and
Part III.2 of the implementation brief.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import log2
import warnings

from physmon.benchmark.parser import ParseResult
from physmon.formal.constructs import CounterfactualFamily, SensitivityRecord


ANSWER_DISTRIBUTION_KEY = "answer_distribution"
PARSED_ANSWER_KEY = "parsed_answer"
REFERENCE_LOGPROB_KEY = "reference_answer_logprob"
VARIANT_INDEX_KEY = "variant_index"
IS_BASE_VARIANT_KEY = "is_base_variant"


def ensure_family_is_certified(family: CounterfactualFamily) -> None:
    """Raise when a counterfactual family lacks solver certification.

    Args:
        family: Family whose behavioural sensitivity is about to be measured.

    Returns:
        `None`.

    Reference:
        `physmon_proposal.pdf` §3.2 and Part III.2: uncertified families must
        not be used for sensitivity measurement.
    """

    if not family.verifier_certified:
        raise ValueError(
            f"Family {family.template.template_id} is not verifier-certified. "
            "Sensitivity measurement is disallowed."
        )


def compute_answer_flip_sensitivity(
    family: CounterfactualFamily,
    model_outputs: Sequence[Mapping[str, object]],
    model_name: str,
    generation_seed: int | None = None,
) -> SensitivityRecord:
    """Compute \\hat{S}_theta(τ) from parsed answers across an invariant family.

    Args:
        family: Solver-certified counterfactual family `F_tau`.
        model_outputs: Raw model output records for each rendered variant. Each
            record may contain `parsed_answer` as either a normalized string or
            a `ParseResult`.
        model_name: Name of the evaluated model.
        generation_seed: Optional deterministic generation seed.

    Returns:
        `SensitivityRecord` with `answer_flip_rate` populated.

    Reference:
        `physmon_proposal.pdf` §3.3 and Part III.2.
    """

    ensure_family_is_certified(family)
    _validate_output_length(family, model_outputs)

    parsed_answers = [_coerce_parsed_answer(output.get(PARSED_ANSWER_KEY)) for output in model_outputs]
    valid_answers = [answer for answer in parsed_answers if answer is not None]
    num_valid = len(valid_answers)
    if num_valid < family.template.num_variants:
        warnings.warn(
            (
                f"Only {num_valid} of {family.template.num_variants} variants parsed cleanly "
                f"for {family.template.template_id}."
            ),
            stacklevel=2,
        )

    if num_valid < 2:
        flip_rate = None
    else:
        flip_count = 0
        pair_count = 0
        for left_index in range(num_valid):
            for right_index in range(left_index + 1, num_valid):
                pair_count += 1
                if valid_answers[left_index] != valid_answers[right_index]:
                    flip_count += 1
        flip_rate = flip_count / pair_count

    return SensitivityRecord(
        template_id=family.template.template_id,
        model_name=model_name,
        answer_flip_rate=flip_rate,
        num_variants_used=len(model_outputs),
        num_valid_parses=num_valid,
        generation_seed=generation_seed,
    )


def compute_distribution_level_sensitivity(
    family: CounterfactualFamily,
    model_outputs: Sequence[Mapping[str, object]],
    model_name: str,
    generation_seed: int | None = None,
) -> SensitivityRecord:
    """Compute S_theta(τ) as the average pairwise Jensen-Shannon divergence.

    Args:
        family: Solver-certified counterfactual family `F_tau`.
        model_outputs: Raw model output records. Each record must include
            `answer_distribution` as a mapping from canonical answer strings to
            non-negative probabilities or unnormalized weights.
        model_name: Name of the evaluated model.
        generation_seed: Optional deterministic generation seed.

    Returns:
        `SensitivityRecord` with `jsd_sensitivity` populated.

    Reference:
        `physmon_proposal.pdf` §3.3 and Part III.2.
    """

    ensure_family_is_certified(family)
    _validate_output_length(family, model_outputs)

    normalized_distributions = [
        _normalize_distribution(output.get(ANSWER_DISTRIBUTION_KEY)) for output in model_outputs
    ]
    pairwise_jsd: list[float] = []
    for left_index in range(len(normalized_distributions)):
        for right_index in range(left_index + 1, len(normalized_distributions)):
            pairwise_jsd.append(
                _jensen_shannon_divergence(
                    normalized_distributions[left_index],
                    normalized_distributions[right_index],
                )
            )

    jsd_value = sum(pairwise_jsd) / len(pairwise_jsd) if pairwise_jsd else 0.0
    return SensitivityRecord(
        template_id=family.template.template_id,
        model_name=model_name,
        jsd_sensitivity=jsd_value,
        num_variants_used=len(model_outputs),
        num_valid_parses=_count_valid_parses(model_outputs),
        generation_seed=generation_seed,
    )


def compute_logprob_drop_sensitivity(
    family: CounterfactualFamily,
    model_outputs: Sequence[Mapping[str, object]],
    model_name: str,
    generation_seed: int | None = None,
) -> SensitivityRecord:
    """Compute S_theta^lp(τ) as the maximum reference-answer log-probability drop.

    Args:
        family: Solver-certified counterfactual family `F_tau`.
        model_outputs: Raw model output records. Each record must include
            `reference_answer_logprob` and may optionally include
            `is_base_variant=True` for the designated baseline prompt.
        model_name: Name of the evaluated model.
        generation_seed: Optional deterministic generation seed.

    Returns:
        `SensitivityRecord` with `logprob_drop` populated.

    Reference:
        `physmon_proposal.pdf` §3.3 and Part III.2.
    """

    ensure_family_is_certified(family)
    _validate_output_length(family, model_outputs)

    base_index = _resolve_base_variant_index(model_outputs)
    base_logprob = _coerce_float(model_outputs[base_index].get(REFERENCE_LOGPROB_KEY), REFERENCE_LOGPROB_KEY)
    drops = []
    for output in model_outputs:
        variant_logprob = _coerce_float(output.get(REFERENCE_LOGPROB_KEY), REFERENCE_LOGPROB_KEY)
        drops.append(base_logprob - variant_logprob)

    return SensitivityRecord(
        template_id=family.template.template_id,
        model_name=model_name,
        logprob_drop=max(drops),
        num_variants_used=len(model_outputs),
        num_valid_parses=_count_valid_parses(model_outputs),
        generation_seed=generation_seed,
    )


def compute_all_sensitivity_measures(
    family: CounterfactualFamily,
    model_outputs: Sequence[Mapping[str, object]],
    model_name: str,
    generation_seed: int | None = None,
) -> SensitivityRecord:
    """Compute all Stage 1 behavioural sensitivity measures in one record.

    Args:
        family: Solver-certified counterfactual family `F_tau`.
        model_outputs: Raw model output records containing parsed answers,
            answer distributions, and reference-answer log-probabilities.
        model_name: Name of the evaluated model.
        generation_seed: Optional deterministic generation seed.

    Returns:
        A `SensitivityRecord` populated with answer-flip, JSD, and log-prob
        sensitivity values.

    Reference:
        `physmon_proposal.pdf` §3.3 and Part III.2.
    """

    answer_flip_record = compute_answer_flip_sensitivity(
        family=family,
        model_outputs=model_outputs,
        model_name=model_name,
        generation_seed=generation_seed,
    )
    jsd_record = compute_distribution_level_sensitivity(
        family=family,
        model_outputs=model_outputs,
        model_name=model_name,
        generation_seed=generation_seed,
    )
    logprob_record = compute_logprob_drop_sensitivity(
        family=family,
        model_outputs=model_outputs,
        model_name=model_name,
        generation_seed=generation_seed,
    )

    answer_flip_record.jsd_sensitivity = jsd_record.jsd_sensitivity
    answer_flip_record.logprob_drop = logprob_record.logprob_drop
    return answer_flip_record


def _validate_output_length(
    family: CounterfactualFamily, model_outputs: Sequence[Mapping[str, object]]
) -> None:
    """Ensure the provided outputs align with the family size."""
    if len(model_outputs) != family.template.num_variants:
        raise ValueError(
            "Expected "
            f"{family.template.num_variants} model outputs but received {len(model_outputs)}."
        )


def _coerce_parsed_answer(raw_value: object) -> str | None:
    """Convert either a `ParseResult` or string into a canonical parsed answer."""
    if isinstance(raw_value, ParseResult):
        return raw_value.answer if raw_value.is_confident else None
    if raw_value is None:
        return None
    if isinstance(raw_value, str):
        normalized = raw_value.strip()
        return normalized or None
    raise TypeError(
        f"Expected '{PARSED_ANSWER_KEY}' to be a string, ParseResult, or None, "
        f"but received {type(raw_value)!r}."
    )


def _count_valid_parses(model_outputs: Sequence[Mapping[str, object]]) -> int:
    """Count confidently parsed answers present in the output records."""
    return sum(
        1 for output in model_outputs if _coerce_parsed_answer(output.get(PARSED_ANSWER_KEY)) is not None
    )


def _normalize_distribution(raw_distribution: object) -> dict[str, float]:
    """Normalize a discrete answer distribution into a probability mapping."""
    if not isinstance(raw_distribution, Mapping):
        raise TypeError(
            f"Expected '{ANSWER_DISTRIBUTION_KEY}' to be a mapping, "
            f"but received {type(raw_distribution)!r}."
        )

    normalized: dict[str, float] = {}
    total_mass = 0.0
    for key, value in raw_distribution.items():
        if not isinstance(key, str):
            raise TypeError("Distribution keys must be canonical answer strings.")
        numeric_value = _coerce_float(value, ANSWER_DISTRIBUTION_KEY)
        if numeric_value < 0:
            raise ValueError("Distribution weights must be non-negative.")
        normalized[key] = numeric_value
        total_mass += numeric_value

    if total_mass <= 0:
        raise ValueError("Distribution mass must be strictly positive.")

    return {key: value / total_mass for key, value in normalized.items()}


def _jensen_shannon_divergence(
    left_distribution: Mapping[str, float], right_distribution: Mapping[str, float]
) -> float:
    """Compute the base-2 Jensen-Shannon divergence between two distributions."""
    support = set(left_distribution) | set(right_distribution)
    midpoint = {
        key: (left_distribution.get(key, 0.0) + right_distribution.get(key, 0.0)) / 2.0
        for key in support
    }
    return (_kl_divergence(left_distribution, midpoint) + _kl_divergence(right_distribution, midpoint)) / 2.0


def _kl_divergence(
    left_distribution: Mapping[str, float], right_distribution: Mapping[str, float]
) -> float:
    """Compute the base-2 KL divergence D_KL(left || right)."""
    divergence = 0.0
    for key, left_mass in left_distribution.items():
        if left_mass == 0:
            continue
        right_mass = right_distribution.get(key, 0.0)
        if right_mass == 0:
            raise ValueError("Encountered zero mass in KL denominator; distributions must share support.")
        divergence += left_mass * log2(left_mass / right_mass)
    return divergence


def _resolve_base_variant_index(model_outputs: Sequence[Mapping[str, object]]) -> int:
    """Return the designated base-variant index, defaulting to the first variant."""
    base_indices = [
        index for index, output in enumerate(model_outputs) if bool(output.get(IS_BASE_VARIANT_KEY))
    ]
    if len(base_indices) > 1:
        raise ValueError("Multiple outputs are marked as the base variant.")
    if base_indices:
        return base_indices[0]

    indexed_outputs = sorted(
        enumerate(model_outputs),
        key=lambda item: int(item[1].get(VARIANT_INDEX_KEY, item[0])),
    )
    return indexed_outputs[0][0]


def _coerce_float(raw_value: object, field_name: str) -> float:
    """Convert a numeric field to `float` with a descriptive failure mode."""
    if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
        raise TypeError(f"Field '{field_name}' must be numeric, got {type(raw_value)!r}.")
    return float(raw_value)
