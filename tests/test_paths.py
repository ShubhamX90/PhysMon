"""Runtime path resolution and the model registry's use of it."""

from __future__ import annotations

from pathlib import Path

import yaml

from physmon.utils import paths

REGISTRY = Path(__file__).resolve().parents[1] / "docs" / "model_registry.yml"


def _clear(monkeypatch):
    for name in ("SCRATCH", "PHYSMON_SCRATCH_ROOT", "PHYSMON_MODEL_ROOT"):
        monkeypatch.delenv(name, raising=False)


def test_defaults(monkeypatch):
    _clear(monkeypatch)
    assert paths.scratch_root() == Path("/scratch/pabitra")
    assert paths.model_root() == Path("/scratch/pabitra/models")
    assert paths.physmon_scratch_root() == Path("/scratch/pabitra/physmon")
    assert paths.physmon_scratch_path("activations_stage6", "q") == Path(
        "/scratch/pabitra/physmon/activations_stage6/q"
    )


def test_scratch_env_moves_both_roots(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("SCRATCH", "/data/alt")
    assert paths.model_root() == Path("/data/alt/models")
    assert paths.physmon_scratch_root() == Path("/data/alt/physmon")


def test_specific_overrides_win(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("SCRATCH", "/data/alt")
    monkeypatch.setenv("PHYSMON_MODEL_ROOT", "/weights")
    monkeypatch.setenv("PHYSMON_SCRATCH_ROOT", "/runs")
    assert paths.model_root() == Path("/weights")
    assert paths.physmon_scratch_root() == Path("/runs")


def test_expand_model_path(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("PHYSMON_MODEL_ROOT", "/weights")
    assert paths.expand_model_path("${PHYSMON_MODEL_ROOT}/Qwen") == "/weights/Qwen"
    assert paths.expand_model_path("/absolute/elsewhere") == "/absolute/elsewhere"


def test_registry_has_no_hardcoded_cluster_paths():
    models = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["models"]
    assert models
    for key, spec in models.items():
        assert spec["path"].startswith(paths.MODEL_ROOT_PLACEHOLDER + "/"), key
        assert "/scratch" not in spec["path"], key


def test_loader_expands_registry_paths(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("PHYSMON_MODEL_ROOT", "/weights")
    from physmon.models.loader import load_model_registry

    registry = load_model_registry(REGISTRY)
    assert registry["qwen_primary"].path == "/weights/Qwen2.5-7B-Instruct"
    assert all(spec.path.startswith("/weights/") for spec in registry.values())
