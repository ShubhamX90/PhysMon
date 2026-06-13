"""Structured file I/O helpers for PhysMon.

Reference: reproducibility requirements in `physmon_proposal.pdf` §17 and the
project-wide logging and artifact rules in Part V.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import yaml


def ensure_parent_dir(path: str | Path) -> Path:
    """Create the parent directory for a target file path if needed.

    Args:
        path: File path whose parent directory should exist.

    Returns:
        Resolved `Path` object for the target file.
    """

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path


def read_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML file into a dictionary.

    Args:
        path: YAML file path.

    Returns:
        Parsed YAML content as a dictionary.
    """

    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected YAML mapping at {path}, found {type(data)!r}.")
    return data


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    """Write a JSON object to disk with stable formatting.

    Args:
        path: Output JSON path.
        payload: JSON-serializable mapping.

    Returns:
        Output `Path`.
    """

    output_path = ensure_parent_dir(path)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def append_jsonl(path: str | Path, payload: dict[str, Any]) -> Path:
    """Append one JSON object as a line to a JSONL file.

    Args:
        path: Output JSONL path.
        payload: JSON-serializable mapping.

    Returns:
        Output `Path`.
    """

    output_path = ensure_parent_dir(path)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return output_path
