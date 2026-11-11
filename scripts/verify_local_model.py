"""Identify the revision of a model directory already on disk and write its manifest.

For a directory that was downloaded with `huggingface_hub` into a local directory (so that
`<model_dir>/.cache/huggingface/download/<file>.metadata` exists), this script:

1. reads every `.metadata` file (line 1: commit, line 2: etag, line 3: download timestamp);
2. checks that all metadata files name one commit, and the expected one if given;
3. hashes every file: SHA-256 for every file, compared with the etag when the etag is a
   64-hex LFS SHA-256, and the Git blob SHA-1 compared with the etag when it is 40-hex;
4. optionally (`--hub-check`, network) compares the local file set, sizes and hashes with the
   file list Hugging Face publishes for that commit, so a file that was never downloaded is
   caught even if it left no metadata;
5. lists `.incomplete` partial downloads in the cache and maps each to the file whose etag it
   carries; a partial whose file did not verify is a problem;
6. writes a manifest in the schema of `scripts/download_model.py` only if every expected file
   is present and matches; otherwise writes a report and no manifest.

The manifest carries `identified_after_the_fact: true`: the weights were not downloaded
through `scripts/download_model.py`, so their identity is established from the files as they
are now, not from a record made at download time. Read only on the model directory.

Usage:
    python3 scripts/verify_local_model.py --model-key qwen3_thinking \
        --model-dir /scratch/pabitra/models/Qwen3-32B --repo-id Qwen/Qwen3-32B \
        --expected-commit 9216db5781bf21249d130ec9da846c4624c16137 --hub-check \
        --report results/g0/attempt_20261112/qwen3_thinking_verification.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_DIR = REPO_ROOT / "docs" / "model_manifests"
CHUNK_BYTES = 16 * 1024 * 1024
DOWNLOAD_CACHE = Path(".cache") / "huggingface" / "download"
HEX = set("0123456789abcdef")


def sha256_and_blob_sha1(path: Path) -> tuple[str, str]:
    """Return (SHA-256, Git blob SHA-1) of a file in one pass."""

    size = path.stat().st_size
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(f"blob {size}\0".encode(), usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            sha256.update(chunk)
            blob.update(chunk)
    return sha256.hexdigest(), blob.hexdigest()


def _is_hex(value: str, length: int) -> bool:
    return len(value) == length and set(value) <= HEX


def read_cache_metadata(model_dir: Path) -> dict[str, dict[str, Any]]:
    """Map each relative file path to its cached commit, etag and timestamp."""

    download_dir = model_dir / DOWNLOAD_CACHE
    entries: dict[str, dict[str, Any]] = {}
    if not download_dir.is_dir():
        return entries
    for meta_path in sorted(download_dir.rglob("*.metadata")):
        relative = meta_path.relative_to(download_dir).as_posix()[: -len(".metadata")]
        lines = meta_path.read_text(encoding="utf-8").splitlines()
        entry: dict[str, Any] = {
            "commit": lines[0].strip() if len(lines) > 0 else None,
            "etag": lines[1].strip().strip('"') if len(lines) > 1 else None,
            "timestamp": None,
            "problem": None,
        }
        try:
            entry["timestamp"] = float(lines[2]) if len(lines) > 2 else None
        except ValueError:
            entry["problem"] = f"unreadable timestamp {lines[2]!r}"
        if not entry["commit"] or not entry["etag"]:
            entry["problem"] = "metadata file lacks a commit or an etag"
        entries[relative] = entry
    return entries


def scan_partials(model_dir: Path) -> list[dict[str, Any]]:
    """List `.incomplete` partial downloads with the etag encoded in their names."""

    download_dir = model_dir / DOWNLOAD_CACHE
    partials = []
    if not download_dir.is_dir():
        return partials
    for path in sorted(download_dir.rglob("*.incomplete")):
        parts = path.name.split(".")
        etag = next((part for part in parts if _is_hex(part, 64) or _is_hex(part, 40)), None)
        partials.append({"name": path.relative_to(download_dir).as_posix(), "etag": etag,
                         "size": path.stat().st_size})
    return partials


def local_files(model_dir: Path) -> list[str]:
    """Every regular file under the model directory, excluding the download cache."""

    files = []
    for path in sorted(model_dir.rglob("*")):
        relative = path.relative_to(model_dir)
        if relative.parts[:1] == (".cache",) or not path.is_file():
            continue
        files.append(relative.as_posix())
    return files


def verify_against_metadata(model_dir: Path, metadata: dict[str, dict[str, Any]],
                            hasher=sha256_and_blob_sha1) -> list[dict[str, Any]]:
    """One record per expected file, in the `download_model.py` manifest record schema."""

    records = []
    for relative, entry in sorted(metadata.items()):
        etag = entry["etag"] or ""
        is_lfs = _is_hex(etag, 64)
        record: dict[str, Any] = {"path": relative, "size": None, "lfs": is_lfs, "sha256": None,
                                  "verified": False, "problem": entry["problem"],
                                  "expected_etag": etag, "verified_by": None}
        target = model_dir / relative
        if record["problem"]:
            pass
        elif not target.is_file():
            record["problem"] = "missing"
        elif not (is_lfs or _is_hex(etag, 40)):
            record["problem"] = f"etag {etag!r} is neither a SHA-256 nor a Git blob id"
        else:
            record["size"] = target.stat().st_size
            sha256, blob_sha1 = hasher(target)
            record["sha256"] = sha256
            if is_lfs:
                record["verified"] = sha256 == etag
                record["verified_by"] = "sha256 == LFS etag"
            else:
                record["verified"] = blob_sha1 == etag
                record["verified_by"] = "git blob sha1 == etag"
                record["git_blob_sha1"] = blob_sha1
            if not record["verified"]:
                record["problem"] = "hash mismatch"
        records.append(record)
    return records


def compare_with_hub(records: list[dict[str, Any]], hub_files: list[dict[str, Any]]) -> list[str]:
    """Problems found when the local verified set is compared with the published file list."""

    problems = []
    local = {record["path"]: record for record in records}
    for item in hub_files:
        record = local.get(item["path"])
        if record is None:
            problems.append(f"{item['path']}: published at this revision but absent from the cache metadata")
            continue
        if item.get("size") is not None and record["size"] is not None and item["size"] != record["size"]:
            problems.append(f"{item['path']}: size {record['size']} != published {item['size']}")
        expected = item.get("lfs_sha256") or item.get("blob_id")
        if expected and expected != record["expected_etag"]:
            problems.append(f"{item['path']}: cached etag differs from the published hash")
    published = {item["path"] for item in hub_files}
    for path in local:
        if path not in published:
            problems.append(f"{path}: in the cache metadata but not published at this revision")
    return problems


def fetch_hub_files(repo_id: str, revision: str) -> tuple[str, list[dict[str, Any]]]:
    """Published file list at a revision (public request, no credentials sent)."""

    from huggingface_hub import HfApi

    info = HfApi().model_info(repo_id, revision=revision, files_metadata=True, token=False)
    files = [{"path": item.rfilename, "size": item.size, "blob_id": item.blob_id,
              "lfs_sha256": item.lfs.sha256 if item.lfs else None} for item in (info.siblings or [])]
    return info.sha, files


def index_shards(model_dir: Path) -> list[str]:
    index = model_dir / "model.safetensors.index.json"
    if not index.is_file():
        return []
    weight_map = json.loads(index.read_text(encoding="utf-8")).get("weight_map", {})
    return sorted(set(weight_map.values()))


def assess(model_dir: Path, *, expected_commit: str | None,
           hub: tuple[str, list[dict[str, Any]]] | None = None,
           hasher=sha256_and_blob_sha1) -> dict[str, Any]:
    """Run every check and return a report; `report['ok']` is True only if nothing is wrong."""

    metadata = read_cache_metadata(model_dir)
    problems: list[str] = []
    if not metadata:
        problems.append(f"no Hugging Face cache metadata under {model_dir / DOWNLOAD_CACHE}")
    commits = sorted({entry["commit"] for entry in metadata.values() if entry["commit"]})
    if len(commits) > 1:
        problems.append(f"cache metadata names several commits: {commits}")
    commit = commits[0] if len(commits) == 1 else None
    if expected_commit and commit != expected_commit:
        problems.append(f"cache commit {commit} != expected {expected_commit}")

    records = verify_against_metadata(model_dir, metadata, hasher=hasher)
    problems.extend(f"{r['path']}: {r['problem']}" for r in records if not r["verified"])

    on_disk = local_files(model_dir)
    extra = [path for path in on_disk if path not in metadata]
    problems.extend(f"{path}: on disk without cache metadata (unverifiable)" for path in extra)
    missing_shards = [shard for shard in index_shards(model_dir) if shard not in metadata]
    problems.extend(f"{shard}: listed in the safetensors index but has no cache metadata"
                    for shard in missing_shards)

    by_etag = {r["expected_etag"]: r for r in records}
    partials = scan_partials(model_dir)
    for partial in partials:
        owner = by_etag.get(partial["etag"])
        partial["file"] = owner["path"] if owner else None
        partial["file_verified"] = bool(owner and owner["verified"])
        if not partial["file_verified"]:
            problems.append(f"partial download {partial['name']} has no verified complete file")

    hub_report: dict[str, Any] = {"checked": False}
    if hub is not None:
        hub_sha, hub_files = hub
        hub_problems = compare_with_hub(records, hub_files)
        if commit and hub_sha != commit:
            hub_problems.append(f"Hub resolved {hub_sha}, cache commit {commit}")
        hub_report = {"checked": True, "resolved_sha": hub_sha, "n_published_files": len(hub_files),
                      "problems": hub_problems}
        problems.extend(hub_problems)

    timestamps = [entry["timestamp"] for entry in metadata.values() if entry["timestamp"]]
    mtimes = [(model_dir / path).stat().st_mtime for path in on_disk]
    return {
        "model_dir": str(model_dir),
        "commit": commit,
        "n_expected_files": len(metadata),
        "n_verified": sum(1 for r in records if r["verified"]),
        "files": records,
        "extra_files_without_metadata": extra,
        "index_shards_without_metadata": missing_shards,
        "cache_partials": partials,
        "cache_download_window_utc": [_utc(min(timestamps)), _utc(max(timestamps))] if timestamps else None,
        "latest_file_mtime_utc": _utc(max(mtimes)) if mtimes else None,
        "hub": hub_report,
        "problems": problems,
        "ok": not problems,
    }


def _utc(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _packages() -> dict[str, str]:
    from importlib import metadata as importlib_metadata

    versions = {}
    for name in ("huggingface-hub", "transformers", "tokenizers", "safetensors", "torch", "numpy"):
        try:
            versions[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            versions[name] = "not installed"
    return versions


def build_manifest(report: dict[str, Any], *, model_key: str, repo_id: str, note: str,
                   compatibility: dict[str, Any]) -> dict[str, Any]:
    """Manifest in the `download_model.py` schema plus the after-the-fact identification."""

    files = [{key: record[key] for key in ("path", "size", "lfs", "sha256", "verified", "problem")}
             for record in report["files"]]
    return {
        "model_key": model_key,
        "repo_id": repo_id,
        "revision": report["commit"],
        "local_path": report["model_dir"],
        "downloaded_at_utc": report["cache_download_window_utc"][1]
        if report["cache_download_window_utc"] else None,
        "authenticated": None,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "host": socket.gethostname(),
        "repo_git_commit": _git_head(),
        "packages": _packages(),
        "total_bytes": sum(record["size"] or 0 for record in report["files"]),
        "compatibility": compatibility,
        "files": files,
        "identified_after_the_fact": True,
        "identification": {
            "verified_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "method": "local SHA-256 and Git blob SHA-1 of every file compared with the etags in "
                      "<model_dir>/.cache/huggingface/download/*.metadata"
                      + ("; file list, sizes and hashes compared with the Hugging Face API at the "
                         "same commit" if report["hub"]["checked"] else ""),
            "cache_download_window_utc": report["cache_download_window_utc"],
            "cache_partials": report["cache_partials"],
            "note": note,
        },
    }


def compatibility_check(model_dir: Path) -> dict[str, Any]:
    """Load config and tokenizer offline; never fails the identification, only records."""

    try:
        import transformers
        from transformers import AutoConfig, AutoTokenizer

        config = AutoConfig.from_pretrained(model_dir, local_files_only=True)
        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": "What is 2 + 2?"}], tokenize=False, add_generation_prompt=True)
        return {"transformers_version": transformers.__version__,
                "architectures": list(getattr(config, "architectures", None) or []),
                "num_hidden_layers": getattr(config, "num_hidden_layers", None),
                "hidden_size": getattr(config, "hidden_size", None),
                "chat_template_prefix": rendered[:120], "problems": []}
    except Exception as error:  # noqa: BLE001 -- recorded, not hidden
        return {"problems": [f"compatibility check not completed: {type(error).__name__}: {error}"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--expected-commit", default=None)
    parser.add_argument("--hub-check", action="store_true",
                        help="Also compare with the Hugging Face file list at the commit (network).")
    parser.add_argument("--compat", action="store_true",
                        help="Load config and tokenizer offline with transformers and record the result.")
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--report", type=Path, required=True, help="Verification report (JSON).")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)

    hub = None
    if args.hub_check:
        revision = args.expected_commit or "main"
        try:
            hub = fetch_hub_files(args.repo_id, revision)
        except Exception as error:  # noqa: BLE001 -- a failed check is reported, not skipped
            hub = None
            hub_error = f"{type(error).__name__}: {error}"
        else:
            hub_error = None
    report = assess(args.model_dir, expected_commit=args.expected_commit, hub=hub)
    if args.hub_check and hub is None:
        report["hub"] = {"checked": False, "error": hub_error}
        report["problems"].append(f"hub check requested but failed: {hub_error}")
        report["ok"] = False
    report["model_key"] = args.model_key
    report["repo_id"] = args.repo_id

    manifest_path = args.manifest_dir / f"{args.model_key}.json"
    if report["ok"]:
        compatibility = compatibility_check(args.model_dir) if args.compat else {
            "problems": [], "not_run": "offline transformers check not requested"}
        manifest = build_manifest(report, model_key=args.model_key, repo_id=args.repo_id,
                                  note=args.note, compatibility=compatibility)
        args.manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        resolved = manifest_path.resolve()
        report["manifest_written"] = (resolved.relative_to(REPO_ROOT).as_posix()
                                      if resolved.is_relative_to(REPO_ROOT) else str(manifest_path))
    else:
        report["manifest_written"] = None
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    status = "OK" if report["ok"] else "NOT IDENTIFIED"
    print(f"{status}: {report['n_verified']} of {report['n_expected_files']} files verified at "
          f"commit {report['commit']}; {len(report['problems'])} problems; "
          f"{len(report['cache_partials'])} cache partials; report {args.report}")
    for problem in report["problems"]:
        print(f"  problem: {problem}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
