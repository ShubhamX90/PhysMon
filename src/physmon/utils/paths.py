"""Runtime scratch and model locations, resolved from the environment.

Portable source and the model registry must not hardcode cluster paths. Everything that
lives outside the repository is located through the helpers here, so a relocated or
rebuilt scratch tree needs one environment variable, not an edit across many files.

Environment variables (all optional):
    SCRATCH                Per-account scratch root. Default: /scratch/pabitra.
    PHYSMON_SCRATCH_ROOT   PhysMon run data (activations, logs, checkpoints, caches).
                           Default: $SCRATCH/physmon.
    PHYSMON_MODEL_ROOT     Model weight directories. Default: $SCRATCH/models.

The model registry writes model locations as `${PHYSMON_MODEL_ROOT}/<directory>`;
`expand_model_path` substitutes the resolved root.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_SCRATCH_ROOT = "/scratch/pabitra"
MODEL_ROOT_PLACEHOLDER = "${PHYSMON_MODEL_ROOT}"


def scratch_root() -> Path:
    return Path(os.environ.get("SCRATCH") or DEFAULT_SCRATCH_ROOT)


def physmon_scratch_root() -> Path:
    override = os.environ.get("PHYSMON_SCRATCH_ROOT")
    return Path(override) if override else scratch_root() / "physmon"


def model_root() -> Path:
    override = os.environ.get("PHYSMON_MODEL_ROOT")
    return Path(override) if override else scratch_root() / "models"


def physmon_scratch_path(*parts: str) -> Path:
    """Return a path under the PhysMon scratch root, for example activations or logs."""

    return physmon_scratch_root().joinpath(*parts)


def expand_model_path(value: str) -> str:
    """Substitute `${PHYSMON_MODEL_ROOT}` in a registry path. Other values pass through."""

    return value.replace(MODEL_ROOT_PLACEHOLDER, str(model_root()))
