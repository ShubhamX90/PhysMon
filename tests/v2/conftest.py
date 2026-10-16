"""Shared fixtures for the v2 tests: tokenizers are loaded once per session (the model store is a network filesystem)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.utils.paths import model_root  # noqa: E402

TOKENIZER_DIRS = {"llama": "Llama-3.1-8B-Instruct", "qwen": "Qwen2.5-7B-Instruct"}


def _load(kind: str):
    directory = model_root() / TOKENIZER_DIRS[kind]
    if not (directory / "tokenizer.json").exists():
        pytest.skip(f"model-store tokenizer for {kind} not present")
    transformers = pytest.importorskip("transformers")
    return transformers.AutoTokenizer.from_pretrained(str(directory), local_files_only=True,
                                                      trust_remote_code=False)


@pytest.fixture(scope="session")
def llama_tokenizer():
    return _load("llama")


@pytest.fixture(scope="session")
def qwen_tokenizer():
    return _load("qwen")


@pytest.fixture(scope="session")
def tokenizer_for(llama_tokenizer, qwen_tokenizer):
    return {"llama": llama_tokenizer, "qwen": qwen_tokenizer}
