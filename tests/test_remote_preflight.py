"""Regression checks for the shared Sharanga deployment preflight."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_preflight_module():
    path = Path(__file__).parents[1] / "scripts" / "ops" / "remote_preflight.py"
    specification = importlib.util.spec_from_file_location("remote_preflight", path)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def test_preflight_extracts_delimited_remote_blocks() -> None:
    module = load_preflight_module()
    output = """REMOTE_STATUS_BEGIN
 M Makefile
?? activations
REMOTE_STATUS_END
QUEUE_BEGIN
123|RUNNING|gpu_a100_8|physmon_test
QUEUE_END
SCRATCH_BEGIN
/scratch 279T 119T 161T 43% /scratch
SCRATCH_END
"""

    assert module.block(output, "REMOTE_STATUS").splitlines() == ["M Makefile", "?? activations"]
    assert module.block(output, "QUEUE") == "123|RUNNING|gpu_a100_8|physmon_test"
    assert module.block(output, "SCRATCH").endswith("/scratch")


def test_preflight_reads_deployment_marker_source() -> None:
    module = load_preflight_module()
    output = "REMOTE_MARKER_SOURCE=deployment_commit\nREMOTE_MARKER=abc123\n"

    assert module.line(output, "REMOTE_MARKER_SOURCE") == "deployment_commit"
    assert module.line(output, "REMOTE_MARKER") == "abc123"
