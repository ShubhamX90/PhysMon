"""File verification for scripts/download_model.py must reject anything that is not exact."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "download_model.py"
spec = importlib.util.spec_from_file_location("download_model_for_test", SCRIPT)
download_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download_model)


def _sibling(path, content, lfs):
    return {
        "path": path,
        "size": len(content),
        "blob_id": hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest(),
        "lfs_sha256": hashlib.sha256(content).hexdigest() if lfs else None,
    }


def test_git_blob_sha1_matches_git(tmp_path):
    file = tmp_path / "a.txt"
    file.write_bytes(b"hello physmon\n")
    expected = subprocess.run(
        ["git", "hash-object", str(file)], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert download_model.git_blob_sha1(file) == expected


def test_verify_accepts_exact_lfs_and_non_lfs_files(tmp_path):
    (tmp_path / "config.json").write_bytes(b"{}")
    (tmp_path / "w.safetensors").write_bytes(b"weights")
    records = download_model.verify_files(
        tmp_path,
        [_sibling("config.json", b"{}", lfs=False), _sibling("w.safetensors", b"weights", lfs=True)],
    )
    assert all(record["verified"] for record in records)
    assert records[1]["sha256"] == hashlib.sha256(b"weights").hexdigest()


def test_verify_rejects_corrupt_missing_and_truncated_files(tmp_path):
    (tmp_path / "w.safetensors").write_bytes(b"weightX")  # same size, wrong bytes
    (tmp_path / "short.bin").write_bytes(b"ab")  # wrong size
    siblings = [
        _sibling("w.safetensors", b"weights", lfs=True),
        _sibling("short.bin", b"abcd", lfs=True),
        _sibling("absent.json", b"{}", lfs=False),
    ]
    records = download_model.verify_files(tmp_path, siblings)
    assert [record["verified"] for record in records] == [False, False, False]
    assert [record["problem"] for record in records] == [
        "hash mismatch",
        "size 2 != 4",
        "missing",
    ]


def test_verify_rejects_tampered_non_lfs_file(tmp_path):
    (tmp_path / "config.json").write_bytes(b"{X")
    records = download_model.verify_files(tmp_path, [_sibling("config.json", b"{}", lfs=False)])
    assert records[0]["verified"] is False
    assert records[0]["problem"] == "hash mismatch"


def _pointer_sibling(path):
    """A listing that reports a 130-byte non-LFS file, like a pointer the API mis-describes."""
    return {"path": path, "size": 130, "blob_id": "x" * 40, "lfs_sha256": None}


def test_listing_size_mismatch_is_resolved_via_endpoint_hash(tmp_path):
    content = b"real tokenizer bytes" * 10
    (tmp_path / "tokenizer.model").write_bytes(content)
    good = {"size": len(content), "sha256": hashlib.sha256(content).hexdigest()}
    records = download_model.verify_files(
        tmp_path, [_pointer_sibling("tokenizer.model")], fallback=lambda _path: good
    )
    assert records[0]["verified"] is True
    assert "resolve endpoint" in records[0]["note"]
    assert records[0]["size"] == len(content)


def test_listing_size_mismatch_still_fails_on_wrong_endpoint_hash(tmp_path):
    content = b"real tokenizer bytes" * 10
    (tmp_path / "tokenizer.model").write_bytes(content)
    wrong = {"size": len(content), "sha256": hashlib.sha256(b"other").hexdigest()}
    records = download_model.verify_files(
        tmp_path, [_pointer_sibling("tokenizer.model")], fallback=lambda _path: wrong
    )
    assert records[0]["verified"] is False
    assert records[0]["problem"] == "hash mismatch"


def test_listing_size_mismatch_fails_without_usable_fallback(tmp_path):
    (tmp_path / "tokenizer.model").write_bytes(b"abc")
    sibling = _pointer_sibling("tokenizer.model")
    no_fallback = download_model.verify_files(tmp_path, [sibling])
    unavailable = download_model.verify_files(tmp_path, [sibling], fallback=lambda _p: None)
    wrong_size = download_model.verify_files(
        tmp_path, [sibling], fallback=lambda _p: {"size": 999, "sha256": "a" * 64}
    )
    for records in (no_fallback, unavailable, wrong_size):
        assert records[0]["verified"] is False
        assert records[0]["problem"] == "size 3 != 130"


def test_fallback_is_not_consulted_when_listing_size_matches(tmp_path):
    (tmp_path / "config.json").write_bytes(b"{}")

    def explode(_path):
        raise AssertionError("fallback must not be called")

    records = download_model.verify_files(
        tmp_path, [_sibling("config.json", b"{}", lfs=False)], fallback=explode
    )
    assert records[0]["verified"] is True
