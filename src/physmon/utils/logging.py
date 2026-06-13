"""Structured experiment logging utilities for PhysMon scripts.

Reference: Part V.3 of the implementation brief and the reproducibility plan in
`physmon_proposal.pdf` §17.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import os
import logging
import subprocess

from physmon.utils.io import append_jsonl, ensure_parent_dir


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
UTC_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
GIT_COMMIT_FALLBACK_FILENAME = ".physmon_git_commit"


def get_git_commit(repo_root: str | Path | None = None) -> str:
    """Return the current Git commit hash, or `UNKNOWN` when unavailable.

    Args:
        repo_root: Optional repository root used for the Git query.

    Returns:
        Short Git commit hash or `UNKNOWN`.
    """

    environment_commit = os.environ.get("PHYSMON_GIT_COMMIT", "").strip()
    if environment_commit:
        return environment_commit

    command = ["git", "rev-parse", "--short", "HEAD"]
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        repo_path = Path(repo_root).resolve() if repo_root is not None else Path.cwd()
        fallback_path = repo_path / GIT_COMMIT_FALLBACK_FILENAME
        if fallback_path.exists():
            fallback_commit = fallback_path.read_text(encoding="utf-8").strip()
            if fallback_commit:
                return fallback_commit
        return "UNKNOWN"
    return completed.stdout.strip() or "UNKNOWN"


@dataclass
class ExperimentLogger:
    """Small structured logger that writes both stdout and JSONL events.

    Args:
        script_name: Name of the running script.
        stage: Stage identifier such as `2`.
        jsonl_path: JSONL file path for structured event output.
        repo_root: Optional repository root for commit-hash discovery.
        model_name: Optional model name.
        model_role: Optional model role.
        git_commit: Optional precomputed Git commit hash.

    Returns:
        Mutable logger with `log_event` and `log_error` helpers.
    """

    script_name: str
    stage: int
    jsonl_path: str | Path
    repo_root: str | Path | None = None
    model_name: str | None = None
    model_role: str | None = None
    git_commit: str = field(default="")

    def __post_init__(self) -> None:
        """Configure stdout logging and initialize the commit hash."""
        if not self.git_commit:
            self.git_commit = get_git_commit(self.repo_root)
        self._logger = logging.getLogger(f"physmon.{self.script_name}")
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            self._logger.addHandler(handler)
        ensure_parent_dir(self.jsonl_path)

    def log_event(self, result: str, level: str = "INFO", **parameters: Any) -> None:
        """Write a structured event to stdout and JSONL.

        Args:
            result: High-level event result label.
            level: Logging level name.
            parameters: Additional structured metadata for the event.

        Returns:
            `None`.
        """

        payload = self._build_payload(result=result, error=None, **parameters)
        self._logger.log(getattr(logging, level.upper(), logging.INFO), str(payload))
        append_jsonl(self.jsonl_path, payload)

    def log_error(self, error: str, **parameters: Any) -> None:
        """Write a structured error event to stdout and JSONL.

        Args:
            error: Error summary string.
            parameters: Additional structured metadata for the event.

        Returns:
            `None`.
        """

        payload = self._build_payload(result="ERROR", error=error, **parameters)
        self._logger.error(str(payload))
        append_jsonl(self.jsonl_path, payload)

    def _build_payload(self, result: str, error: str | None, **parameters: Any) -> dict[str, Any]:
        """Create a JSON-serializable log payload."""
        return {
            "timestamp": datetime.now(timezone.utc).strftime(UTC_DATE_FORMAT),
            "script_name": self.script_name,
            "git_commit": self.git_commit,
            "stage": self.stage,
            "model_name": self.model_name,
            "model_role": self.model_role,
            "result": result,
            "error": error,
            "parameters": parameters,
        }
