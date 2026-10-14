"""`get_git_commit` must report the live commit, not a stale marker."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from physmon.utils.logging import get_git_commit


def _init_repo(path: Path) -> str:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "PATH": "/usr/bin:/bin",
        "HOME": str(path),
    }
    for args in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "x"]):
        subprocess.run(["git", *args], cwd=path, check=True, env=env)
    out = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=path, check=True, capture_output=True,
        text=True, env=env,
    )
    return out.stdout.strip()


def test_live_git_beats_env_var_and_marker_file(tmp_path, monkeypatch):
    live = _init_repo(tmp_path)
    (tmp_path / ".physmon_git_commit").write_text("deadbee\n")
    monkeypatch.setenv("PHYSMON_GIT_COMMIT", "stale00")
    assert get_git_commit(tmp_path) == live


def test_env_var_used_only_when_git_cannot_answer(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSMON_GIT_COMMIT", "fromenv")
    monkeypatch.setattr(subprocess, "run", _raise_oserror)
    assert get_git_commit(tmp_path) == "fromenv"


def test_marker_file_then_unknown_without_git_or_env(tmp_path, monkeypatch):
    monkeypatch.delenv("PHYSMON_GIT_COMMIT", raising=False)
    monkeypatch.setattr(subprocess, "run", _raise_oserror)
    assert get_git_commit(tmp_path) == "UNKNOWN"
    (tmp_path / ".physmon_git_commit").write_text("abc1234\n")
    assert get_git_commit(tmp_path) == "abc1234"


def _raise_oserror(*_args, **_kwargs):
    raise OSError("git unavailable")


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_env_var_is_ignored(tmp_path, monkeypatch, value):
    monkeypatch.setenv("PHYSMON_GIT_COMMIT", value)
    monkeypatch.setattr(subprocess, "run", _raise_oserror)
    assert get_git_commit(tmp_path) == "UNKNOWN"
