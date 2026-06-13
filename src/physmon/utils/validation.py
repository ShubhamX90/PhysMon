"""Human-validation utilities for Stage 3 pilot review.

Reference: the Stage 3 brief Part D.7 and the validation plan in
`physmon_proposal.pdf` §11.
"""

from __future__ import annotations

from collections import Counter


def compute_kappa(
    rater1_responses: dict[str, dict[str, str]],
    rater2_responses: dict[str, dict[str, str]],
    question: str = "Q1",
) -> float:
    """Compute Cohen's kappa for one validation question across templates.

    Args:
        rater1_responses: Mapping from template id to question responses for rater 1.
        rater2_responses: Mapping from template id to question responses for rater 2.
        question: Validation question key such as `Q1`.

    Returns:
        Cohen's kappa score in `[-1, 1]`.

    Raises:
        ValueError: If the raters do not cover the same template set or contain invalid labels.
    """

    template_ids = sorted(set(rater1_responses) & set(rater2_responses))
    if not template_ids:
        raise ValueError("No overlapping template ids available for kappa computation.")
    if set(rater1_responses) != set(rater2_responses):
        raise ValueError("Raters must cover the same template ids for kappa computation.")

    valid_labels = {"Y", "N"}
    paired_labels: list[tuple[str, str]] = []
    for template_id in template_ids:
        left_label = str(rater1_responses[template_id][question]).upper()
        right_label = str(rater2_responses[template_id][question]).upper()
        if left_label not in valid_labels or right_label not in valid_labels:
            raise ValueError(f"Invalid labels for {template_id}: {left_label}, {right_label}")
        paired_labels.append((left_label, right_label))

    observed_agreement = sum(1 for left, right in paired_labels if left == right) / len(paired_labels)
    left_counts = Counter(left for left, _ in paired_labels)
    right_counts = Counter(right for _, right in paired_labels)
    expected_agreement = sum(
        (left_counts[label] / len(paired_labels)) * (right_counts[label] / len(paired_labels))
        for label in valid_labels
    )
    if expected_agreement == 1.0:
        return 1.0
    return (observed_agreement - expected_agreement) / (1.0 - expected_agreement)
