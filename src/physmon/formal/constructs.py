"""Programmatic encoding of PhysMon formal constructs.

Reference: `physmon_proposal.pdf` §3 (Formal Problem Definition), §3.1
(Three-Level Analysis Framework), and §9 (Hidden-State Monitoring Methodology).

Three-Level Analysis Framework (§3.1):
  Level 1: Prompt condition — which cue z_i is present.
  Level 2: Observed model behaviour — output instability across F_tau.
  Level 3: Internal representation — hidden-state signal predicting Level 2.

These levels are never conflated in this codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
import warnings


VALID_DOMAINS = frozenset({"mechanics", "electrostatics_circuits"})
VALID_CUE_TYPES = frozenset(
    {"irrelevant_variable", "nongoverning_distractor", "frame_rendering"}
)
VALID_EXTRACTION_SITES = frozenset(
    {
        "resid_post_cue_token",
        "resid_post_last_prompt",
        "attn_out_cue_token",
        "mlp_out_cue_token",
    }
)
TEMPLATE_ID_PATTERN = re.compile(
    r"^(mechanics|electrostatics_circuits)_"
    r"(irrelevant_variable|nongoverning_distractor|frame_rendering)_\d{4}$"
)
PRE_REGISTRATION_PLACEHOLDER = "[TO BE FILLED"
DEFAULT_CONSTRUCT_SPEC_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "construct_spec.md"
)


def is_preregistration_complete(spec_path: Path | None = None) -> bool:
    """Return whether the Stage 1 pre-registration block has been completed.

    Args:
        spec_path: Optional path to `docs/construct_spec.md`. When omitted, the
            repository default is used.

    Returns:
        `True` if the pre-registration section exists and no placeholder
        markers remain, else `False`.

    Reference:
        `physmon_proposal.pdf` §11 Stage 1 deliverables and the Stage 5
        pre-registration gate described in Part III.1.
    """

    target_path = spec_path or DEFAULT_CONSTRUCT_SPEC_PATH
    if not target_path.exists():
        return False

    spec_text = target_path.read_text(encoding="utf-8")
    if "## PRE-REGISTRATION" not in spec_text:
        return False
    return PRE_REGISTRATION_PLACEHOLDER not in spec_text


@dataclass(frozen=True)
class PhysicsTemplate:
    """Canonical physics problem template τ = (r, z, a, g, y*).

    Args:
        template_id: Unique identifier with format
            `"{domain}_{cue_type}_{index:04d}"`.
        domain: Physics domain. One of `VALID_DOMAINS`.
        cue_type: Cue family. One of `VALID_CUE_TYPES`.
        governing_relation: Natural-language description of the relevant law `r`.
        cue_variable: Description of the cue condition or variable `z`.
        auxiliary_assumptions: Fixed background assumptions `a`.
        governing_equation: Symbolic governing equation `g` as a SymPy-ready string.
        correct_answer_template: Parameterized answer template `y*`.
        num_variants: Family size `m`.
        notes: Optional human-readable notes.

    Returns:
        A validated immutable `PhysicsTemplate` instance.

    Reference:
        `physmon_proposal.pdf` §3.2 and Part III.2 of the implementation brief.
    """

    template_id: str
    domain: str
    cue_type: str
    governing_relation: str
    cue_variable: str
    auxiliary_assumptions: str
    governing_equation: str
    correct_answer_template: str
    num_variants: int
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate the template against the Stage 1 formal definition."""
        if self.domain not in VALID_DOMAINS:
            raise ValueError(f"Invalid domain '{self.domain}'. Expected one of {VALID_DOMAINS}.")
        if self.cue_type not in VALID_CUE_TYPES:
            raise ValueError(
                f"Invalid cue_type '{self.cue_type}'. Expected one of {VALID_CUE_TYPES}."
            )
        if self.num_variants < 2:
            raise ValueError("Counterfactual families require at least two variants.")
        if not TEMPLATE_ID_PATTERN.match(self.template_id):
            raise ValueError(
                "template_id must match "
                "'{domain}_{cue_type}_{index:04d}' with valid domain/cue_type values."
            )


@dataclass
class CounterfactualFamily:
    """Rendered counterfactual family F_tau = {x_tau(r, z_i, a)}_{i=1}^m.

    Args:
        template: Source canonical template τ.
        variants: Rendered variant dictionaries, one per cue condition.
        correct_answer: Solver-verified invariant answer `y*`.
        verifier_certified: Whether invariance has been solver-certified.
        human_validated: Whether human validators have approved the family.
        validation_kappa: Optional inter-rater agreement statistic.

    Returns:
        A mutable `CounterfactualFamily` record with validation metadata.

    Reference:
        `physmon_proposal.pdf` §3.2 and Part III.2 of the implementation brief.
    """

    template: PhysicsTemplate
    variants: list[dict[str, Any]]
    correct_answer: str
    verifier_certified: bool = False
    human_validated: bool = False
    validation_kappa: float | None = None

    def __post_init__(self) -> None:
        """Validate family length and warn when the invariance certificate is absent."""
        if len(self.variants) != self.template.num_variants:
            raise ValueError(
                "Expected "
                f"{self.template.num_variants} variants but received {len(self.variants)}."
            )
        if not self.verifier_certified:
            warnings.warn(
                (
                    f"Family {self.template.template_id} is not solver-certified. "
                    "Do not use it for sensitivity measurement until invariance is verified."
                ),
                stacklevel=2,
            )


@dataclass
class SensitivityRecord:
    """Level-2 behavioural sensitivity measures for one model on one family.

    Args:
        template_id: Canonical family identifier.
        model_name: Model evaluated on the family.
        answer_flip_rate: Answer-flip sensitivity \\hat{S}_theta(τ).
        jsd_sensitivity: Distribution-level sensitivity S_theta(τ).
        logprob_drop: Log-probability drop S_theta^lp(τ).
        num_variants_used: Count of variants included in the computation.
        num_valid_parses: Count of parseable variants contributing to answer flips.
        generation_seed: Optional generation seed for reproducibility.
        binary_sensitive: Optional binary label set only after pre-registration.
        binary_threshold_used: Threshold used for binarization once allowed.

    Returns:
        A mutable record containing behavioural measurements only.

    Reference:
        `physmon_proposal.pdf` §3.3 and the Part III.2 implementation brief.
    """

    template_id: str
    model_name: str
    answer_flip_rate: float | None = None
    jsd_sensitivity: float | None = None
    logprob_drop: float | None = None
    num_variants_used: int | None = None
    num_valid_parses: int | None = None
    generation_seed: int | None = None
    binary_sensitive: bool | None = None
    binary_threshold_used: float | None = None

    def set_binary_label(
        self,
        threshold: float,
        measure: str = "answer_flip_rate",
        spec_path: Path | None = None,
    ) -> None:
        """Binarize a behavioural measure after pre-registration has been completed.

        Args:
            threshold: Pre-registered threshold used for the binary decision.
            measure: Name of the `SensitivityRecord` attribute to threshold.
            spec_path: Optional override for the construct-spec path checked for
                pre-registration completion.

        Returns:
            `None`. The record is updated in place.

        Reference:
            `physmon_proposal.pdf` §11 Stage 1 gate and Part III.1
            "Sensitivity Threshold Pre-Registration Record".
        """

        if not is_preregistration_complete(spec_path):
            raise RuntimeError(
                "Cannot set binary_sensitive before the construct specification's "
                "PRE-REGISTRATION block is completed and committed."
            )
        if not hasattr(self, measure):
            raise AttributeError(f"SensitivityRecord has no measure '{measure}'.")

        value = getattr(self, measure)
        if value is None:
            raise ValueError(f"Measure '{measure}' has not been computed yet.")

        self.binary_sensitive = bool(value >= threshold)
        self.binary_threshold_used = threshold


@dataclass(frozen=True)
class ProbeTarget:
    """Prompt-side hidden-state target used to predict Level-2 sensitivity.

    Args:
        template_id: Canonical family identifier.
        model_name: Model whose activations were extracted.
        extraction_site: Prompt-side activation site name.
        layer_index: Layer index from which the activation was extracted.
        activation_path: Scratch path to the stored activation tensor.
        variant_index: Variant index within the counterfactual family.

    Returns:
        An immutable descriptor of a prompt-side monitoring target.

    Reference:
        `physmon_proposal.pdf` §9 and Part III.2 of the implementation brief.
    """

    template_id: str
    model_name: str
    extraction_site: str
    layer_index: int
    activation_path: str
    variant_index: int

    def __post_init__(self) -> None:
        """Validate the extraction-site label and prompt-side indexing metadata."""
        if self.extraction_site not in VALID_EXTRACTION_SITES:
            raise ValueError(
                "Invalid extraction_site "
                f"'{self.extraction_site}'. Expected one of {VALID_EXTRACTION_SITES}."
            )
        if self.layer_index < 0:
            raise ValueError("layer_index must be non-negative.")
        if self.variant_index < 0:
            raise ValueError("variant_index must be non-negative.")
