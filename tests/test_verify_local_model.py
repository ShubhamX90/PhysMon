"""scripts/verify_local_model.py identifies a revision only when every file matches."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_local_model.py"
spec = importlib.util.spec_from_file_location("verify_local_model_for_test", SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

COMMIT = "a" * 40


def _blob(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()


def _fake_model(tmp_path: Path, files: dict[str, tuple[bytes, bool]]) -> Path:
    """files: name -> (content, is_lfs). Writes the files and matching cache metadata."""

    model = tmp_path / "model"
    cache = model / ".cache" / "huggingface" / "download"
    cache.mkdir(parents=True)
    for name, (content, lfs) in files.items():
        (model / name).write_bytes(content)
        etag = hashlib.sha256(content).hexdigest() if lfs else _blob(content)
        (cache / f"{name}.metadata").write_text(f"{COMMIT}\n{etag}\n1792060383.7\n", encoding="utf-8")
    return model


FILES = {"config.json": (b"{}", False), "model-00001-of-00001.safetensors": (b"weights", True),
         ".gitattributes": (b"*.safetensors filter=lfs\n", False)}


def test_all_files_match_gives_ok_and_reports_partials(tmp_path):
    model = _fake_model(tmp_path, FILES)
    lfs_etag = hashlib.sha256(b"weights").hexdigest()
    cache = model / ".cache" / "huggingface" / "download"
    (cache / f"abc=.{lfs_etag}.1234.incomplete").write_bytes(b"wei")
    report = verify.assess(model, expected_commit=COMMIT)
    assert report["ok"], report["problems"]
    assert report["n_verified"] == 3
    assert report["cache_partials"][0]["file"] == "model-00001-of-00001.safetensors"
    assert report["cache_partials"][0]["file_verified"] is True


def test_missing_file_blocks_identification(tmp_path):
    model = _fake_model(tmp_path, FILES)
    (model / "config.json").unlink()
    report = verify.assess(model, expected_commit=COMMIT)
    assert not report["ok"] and any("config.json: missing" in p for p in report["problems"])


def test_hash_mismatch_and_wrong_commit_block_identification(tmp_path):
    model = _fake_model(tmp_path, FILES)
    (model / "model-00001-of-00001.safetensors").write_bytes(b"tampered")
    report = verify.assess(model, expected_commit="b" * 40)
    assert not report["ok"]
    assert any("hash mismatch" in p for p in report["problems"])
    assert any("expected" in p for p in report["problems"])


def test_partial_without_complete_file_and_extra_file_are_problems(tmp_path):
    model = _fake_model(tmp_path, FILES)
    cache = model / ".cache" / "huggingface" / "download"
    (cache / f"zz=.{'c' * 64}.99.incomplete").write_bytes(b"")
    (model / "tokenizer.json").write_bytes(b"{}")
    report = verify.assess(model, expected_commit=COMMIT)
    assert not report["ok"]
    assert any("partial download" in p for p in report["problems"])
    assert any("tokenizer.json: on disk without cache metadata" in p for p in report["problems"])


def test_hub_comparison_catches_a_file_never_downloaded(tmp_path):
    model = _fake_model(tmp_path, FILES)
    hub_files = [{"path": name, "size": len(content),
                  "blob_id": _blob(content), "lfs_sha256": hashlib.sha256(content).hexdigest() if lfs else None}
                 for name, (content, lfs) in FILES.items()]
    hub_files.append({"path": "vocab.json", "size": 2, "blob_id": "d" * 40, "lfs_sha256": None})
    report = verify.assess(model, expected_commit=COMMIT, hub=(COMMIT, hub_files))
    assert not report["ok"]
    assert any("vocab.json: published at this revision but absent" in p for p in report["problems"])
    report_ok = verify.assess(model, expected_commit=COMMIT, hub=(COMMIT, hub_files[:-1]))
    assert report_ok["ok"], report_ok["problems"]


def test_cli_writes_manifest_only_when_ok(tmp_path):
    model = _fake_model(tmp_path, FILES)
    manifests = tmp_path / "manifests"
    report_path = tmp_path / "report.json"
    args = ["--model-key", "fake", "--model-dir", str(model), "--repo-id", "org/fake",
            "--expected-commit", COMMIT, "--manifest-dir", str(manifests), "--report", str(report_path),
            "--note", "test"]
    assert verify.main(args) == 0
    manifest = json.loads((manifests / "fake.json").read_text(encoding="utf-8"))
    assert manifest["identified_after_the_fact"] is True and manifest["revision"] == COMMIT
    assert {"path", "size", "lfs", "sha256", "verified", "problem"} == set(manifest["files"][0])
    (manifests / "fake.json").unlink()
    (model / "config.json").write_bytes(b"{changed}")
    assert verify.main(args) == 1
    assert not (manifests / "fake.json").exists()
    assert json.loads(report_path.read_text(encoding="utf-8"))["manifest_written"] is None
