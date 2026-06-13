"""Execution-gate helpers that enforce the proposal's stage ordering.

Reference: `physmon_proposal.pdf` §10 and §11, plus Part IV.5 and Part V.4 of
the implementation brief.
"""

from __future__ import annotations

from pathlib import Path


DEFAULT_DECISION_LOG_PATH = Path(__file__).resolve().parents[3] / "docs" / "decisions" / "decision_log.md"


def require_stage_gate_pass(
    stage_number: int,
    decision_log_path: str | Path = DEFAULT_DECISION_LOG_PATH,
) -> None:
    """Raise unless the requested stage decision gate is explicitly marked PASS.

    Args:
        stage_number: Ordered execution stage whose gate must have passed.
        decision_log_path: Markdown decision-log path to inspect.

    Returns:
        `None`.

    Reference:
        `physmon_proposal.pdf` §11 and Part V.4 rule 2.
    """

    decision_log = Path(decision_log_path)
    if not decision_log.exists():
        raise FileNotFoundError(f"Decision log not found at {decision_log}.")

    heading = f"## Stage {stage_number} Decision Gate"
    text = decision_log.read_text(encoding="utf-8")
    if heading not in text:
        raise RuntimeError(
            f"Stage {stage_number} decision gate is absent from {decision_log}. "
            "Do not proceed."
        )

    section = text.split(heading, maxsplit=1)[1]
    next_heading_index = section.find("\n## ")
    if next_heading_index != -1:
        section = section[:next_heading_index]

    if "[x] PASS" not in section:
        raise RuntimeError(
            f"Stage {stage_number} decision gate is not marked PASS in {decision_log}. "
            "Do not proceed."
        )
