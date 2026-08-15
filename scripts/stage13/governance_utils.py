#!/usr/bin/env python3
"""Shared utilities for Stage 13 governance scripts.

These helpers are intentionally small and dependency-light.  Stage 13 is about
provenance and auditability; scripts should prefer explicit "unknown" values to
silent inference.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE13_NOW = os.environ.get("PHYSMON_STAGE13_DATE", "2026-07-03")


def repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def ensure_parent(path: str | Path) -> Path:
    path = repo_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: str | Path) -> Any:
    with repo_path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with repo_path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL row: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: JSONL row is not an object")
            rows.append(value)
    return rows


def write_json(path: str | Path, value: Any) -> Path:
    path = ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    path = ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")
    return path


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with repo_path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: str | Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    path = ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with repo_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_record(path: str | Path) -> dict[str, Any]:
    resolved = repo_path(path)
    exists = resolved.exists()
    return {
        "path": str(resolved.relative_to(REPO_ROOT) if exists else path),
        "exists": exists,
        "size_bytes": resolved.stat().st_size if exists and resolved.is_file() else None,
        "sha256": sha256_file(resolved) if exists and resolved.is_file() else None,
    }


def git_info() -> dict[str, Any]:
    def run(args: list[str]) -> str:
        try:
            return subprocess.check_output(args, cwd=REPO_ROOT, text=True).strip()
        except Exception as exc:  # pragma: no cover - defensive in dirty envs
            return f"UNAVAILABLE: {exc}"

    status = run(["git", "status", "--short"])
    return {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "dirty": bool(status),
        "status_short": status.splitlines(),
    }


def classify_result_path(path: Path) -> str:
    name = path.name.lower()
    if "events" in name or name.endswith(".log") or name.endswith(".out"):
        return "run_log"
    if name.endswith(".jsonl") or "raw" in name or "records" in name:
        return "raw_or_record"
    if "summary" in name or "auroc" in name or "metrics" in name:
        return "summary"
    if name.endswith((".png", ".pdf", ".svg")):
        return "figure"
    if name.endswith((".zip", ".tar", ".gz")):
        return "archive"
    if path.stat().st_size == 0:
        return "empty"
    return "derived_or_unknown"


def infer_family_id(row: dict[str, Any]) -> str | None:
    for key in ("template_id", "family_id", "canonical_family_id"):
        value = row.get(key)
        if value:
            return str(value)
    return None


@dataclass(frozen=True)
class GateCheck:
    name: str
    passed: bool
    severity: str
    detail: str


def gate_json(stage: str, checks: list[GateCheck]) -> dict[str, Any]:
    blockers = [check for check in checks if not check.passed and check.severity == "blocker"]
    warnings = [check for check in checks if not check.passed and check.severity != "blocker"]
    return {
        "stage": stage,
        "date": STAGE13_NOW,
        "overall_status": "PASS" if not blockers else "FAIL",
        "paper_eligible_evidence_allowed": not blockers,
        "n_checks": len(checks),
        "n_blockers": len(blockers),
        "n_warnings": len(warnings),
        "checks": [check.__dict__ for check in checks],
    }

