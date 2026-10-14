"""Download, verify, and record a registry model at a pinned Hugging Face revision.

The registry (`docs/model_registry.yml`) supplies the repo id (`name`) and the exact
local directory (`path`) the loader expects. The snapshot is downloaded into
`<path>.partial`, every file is checked against the hashes Hugging Face publishes, the
config and chat template are checked with the installed `transformers`, and only then is
the directory renamed to `<path>`. A manifest with the pinned revision and per-file
SHA-256 values is written to `docs/model_manifests/<model_key>.json`.

CPU only. Never overwrites a non-empty target directory.
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

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.utils.paths import expand_model_path  # noqa: E402
DEFAULT_REGISTRY = REPO_ROOT / "docs" / "model_registry.yml"
DEFAULT_MANIFEST_DIR = REPO_ROOT / "docs" / "model_manifests"
CHUNK_BYTES = 16 * 1024 * 1024

# Chat-template markers the Stage 4 repair showed to be essential for these families.
CHAT_MARKERS = {
    "qwen": "<|im_start|>",
    "llama": "<|start_header_id|>",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha1(path: Path) -> str:
    """Return the Git blob id of a file, which Hugging Face publishes for non-LFS files."""

    size = path.stat().st_size
    digest = hashlib.sha1(f"blob {size}\0".encode(), usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_files(
    root: Path, siblings: list[dict[str, Any]], fallback: Any = None
) -> list[dict[str, Any]]:
    """Check every published file exists with the published size and hash.

    Each sibling dict needs `path`, `size`, `blob_id`, and `lfs_sha256` (None for non-LFS).
    Returns one record per file, with `verified` True only when the content hash matched.

    `fallback(path)` may return `{"size": int, "sha256": str}` taken from the resolve
    endpoint. It is consulted only when the file listing's size disagrees with the file on
    disk (for example an LFS pointer the listing reports as a 130-byte file). The local
    content must then match the endpoint's size and SHA-256 exactly.
    """

    records = []
    for sibling in siblings:
        target = root / sibling["path"]
        record = {
            "path": sibling["path"],
            "size": sibling["size"],
            "lfs": sibling["lfs_sha256"] is not None,
            "sha256": None,
            "verified": False,
            "problem": None,
        }
        actual_size = target.stat().st_size if target.is_file() else None
        alternate = None
        if not target.is_file():
            record["problem"] = "missing"
        elif sibling["size"] is not None and actual_size != sibling["size"]:
            alternate = fallback(sibling["path"]) if fallback else None
            if alternate and alternate["size"] == actual_size and alternate["sha256"]:
                record["sha256"] = sha256_file(target)
                record["verified"] = record["sha256"] == alternate["sha256"]
                record["size"] = actual_size
                record["note"] = (
                    f"listing size {sibling['size']} disagreed with disk; verified against the "
                    "resolve endpoint's size and SHA-256"
                )
                if not record["verified"]:
                    record["problem"] = "hash mismatch"
            else:
                record["problem"] = f"size {actual_size} != {sibling['size']}"
        else:
            record["sha256"] = sha256_file(target)
            if sibling["lfs_sha256"] is not None:
                ok = record["sha256"] == sibling["lfs_sha256"]
            else:
                ok = git_blob_sha1(target) == sibling["blob_id"]
            record["verified"] = ok
            if not ok:
                record["problem"] = "hash mismatch"
        records.append(record)
    return records


def load_spec(registry_path: Path, model_key: str) -> dict[str, Any]:
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    models = registry["models"]
    if model_key not in models:
        raise SystemExit(f"Unknown model key {model_key!r}; known: {sorted(models)}")
    return models[model_key]


def resolve_siblings(repo_id: str, revision: str | None, token: Any) -> tuple[str, list[dict]]:
    from huggingface_hub import HfApi

    info = HfApi().model_info(repo_id, revision=revision, files_metadata=True, token=token)
    siblings = [
        {
            "path": item.rfilename,
            "size": item.size,
            "blob_id": item.blob_id,
            "lfs_sha256": item.lfs.sha256 if item.lfs else None,
        }
        for item in (info.siblings or [])
    ]
    return info.sha, siblings


def endpoint_metadata(repo_id: str, revision: str, path: str, token: Any) -> dict[str, Any] | None:
    """Size and SHA-256 the resolve endpoint reports for one file, or None if unavailable."""

    from huggingface_hub import get_hf_file_metadata, hf_hub_url

    try:
        meta = get_hf_file_metadata(hf_hub_url(repo_id, path, revision=revision), token=token)
    except Exception:  # network or permission problem: leave the file unverified
        return None
    etag = (meta.etag or "").strip('"')
    sha256 = etag if len(etag) == 64 and all(ch in "0123456789abcdef" for ch in etag) else None
    return {"size": meta.size, "sha256": sha256}


def compatibility_checks(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Load config and tokenizer with the installed transformers (no weights, no GPU)."""

    import transformers
    from transformers import AutoConfig, AutoTokenizer

    config = AutoConfig.from_pretrained(root, local_files_only=True)
    # Multimodal and MoE composites keep the language-model dimensions under text_config.
    text_config = config.get_text_config() if hasattr(config, "get_text_config") else config
    tokenizer = AutoTokenizer.from_pretrained(root, local_files_only=True)
    messages = [
        {"role": "system", "content": "You are a physics assistant."},
        {"role": "user", "content": "What is 2 + 2?"},
    ]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    result: dict[str, Any] = {
        "transformers_version": transformers.__version__,
        "architectures": list(getattr(config, "architectures", None) or []),
        "num_hidden_layers": getattr(text_config, "num_hidden_layers", None),
        "hidden_size": getattr(text_config, "hidden_size", None),
        "chat_template_prefix": rendered[:120],
        "problems": [],
    }
    for registry_key, config_key in (("num_layers", "num_hidden_layers"), ("hidden_dim", "hidden_size")):
        expected = spec.get(registry_key)
        if expected is not None and result[config_key] != expected:
            result["problems"].append(
                f"{config_key}={result[config_key]} but registry {registry_key}={expected}"
            )
    marker = CHAT_MARKERS.get(spec.get("family"))
    if marker is not None and marker not in rendered:
        result["problems"].append(f"chat template lacks expected marker {marker!r}")
    return result


def current_git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
        )
        return completed.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def package_versions() -> dict[str, str]:
    from importlib import metadata

    names = ["huggingface-hub", "transformers", "tokenizers", "safetensors", "torch", "numpy"]
    versions = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "not installed"
    return versions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-key", required=True, help="Key in the model registry.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--revision", default=None, help="Pin a revision; default is current main.")
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Send no Hugging Face credentials. Use for non-gated repositories.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Resolve and report, download nothing.")
    args = parser.parse_args()

    spec = load_spec(args.registry, args.model_key)
    repo_id = spec["name"]
    target = Path(expand_model_path(spec["path"]))
    staging = target.parent / (target.name + ".partial")
    token = False if args.public_only else None

    revision, siblings = resolve_siblings(repo_id, args.revision, token)
    total_gb = sum(item["size"] or 0 for item in siblings) / 1e9
    print(f"model_key={args.model_key} repo={repo_id} revision={revision}")
    print(f"files={len(siblings)} total={total_gb:.1f} GB target={target}")
    if target.exists() and any(target.iterdir()):
        print(f"REFUSING: {target} already exists and is not empty. Nothing was changed.")
        return 2
    if args.dry_run:
        print("dry run: nothing downloaded")
        return 0

    from huggingface_hub import snapshot_download

    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading into {staging}", flush=True)
    snapshot_download(
        repo_id=repo_id, revision=revision, local_dir=str(staging), token=token, max_workers=8
    )

    print("verifying file hashes against Hugging Face", flush=True)
    records = verify_files(
        staging, siblings, fallback=lambda path: endpoint_metadata(repo_id, revision, path, token)
    )
    bad = [record for record in records if not record["verified"]]
    if bad:
        for record in bad:
            print(f"FAILED {record['path']}: {record['problem']}")
        print(f"Verification failed. Left {staging} in place for inspection; target not created.")
        return 3

    print("checking config and chat template with transformers", flush=True)
    checks = compatibility_checks(staging, spec)
    if checks["problems"]:
        for problem in checks["problems"]:
            print(f"FAILED compatibility: {problem}")
        print(f"Left {staging} in place for inspection; target not created.")
        return 4

    os.rename(staging, target)
    manifest = {
        "model_key": args.model_key,
        "repo_id": repo_id,
        "revision": revision,
        "local_path": str(target),
        "downloaded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authenticated": not args.public_only,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "host": socket.gethostname(),
        "repo_git_commit": current_git_commit(),
        "packages": package_versions(),
        "total_bytes": sum(item["size"] or 0 for item in siblings),
        "compatibility": checks,
        "files": records,
    }
    args.manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.manifest_dir / f"{args.model_key}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK: {len(records)} files verified, {target} ready, manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
