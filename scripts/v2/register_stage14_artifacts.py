#!/usr/bin/env python3
"""Register and verify the Stage 14 artifacts (Research v2.0 P0.1: immutable artifact registry; §9.1 evidence records).

`--write` scans the Stage 14 result and material directories, records every file's SHA-256 with the stage, kind,
source commit, evidence class and authorization reference found in the artifact's own summary file, and appends the
new artifacts to `docs/registry/v2/artifact_register.jsonl`. It never rewrites an existing entry: if a registered
artifact has changed, it stops with an error.
`--verify` recomputes every hash and reports changed, missing and unregistered files; it exits non-zero on any
discrepancy. Registered directories are meant to be immutable: a correction is a new attempt directory.
`--add-jobs ID...` appends Slurm accounting rows (`sacct`, read-only) to `docs/registry/v2/slurm_jobs.jsonl`, with the
artifact directories that carry the job id in their name, so that failed and cancelled jobs stay on record.

Nothing here makes a result authoritative: every entry carries `paper_eligible: false` and its evidence class.
CPU only; stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_REGISTER = "docs/registry/v2/artifact_register.jsonl"
JOB_REGISTER = "docs/registry/v2/slurm_jobs.jsonl"
SUMMARY_FILES = ("run_summary.json", "plan.json", "summary.json")

# (stage, kind, glob of artifact directories relative to the root)
ARTIFACT_GLOBS = (
    ("14.1", "x01_reproduction", "results/stage14/x01_reproduction/attempt_*"),
    ("14.2", "x02_base_rotation", "results/stage14/x02_base_rotation/attempt_*"),
    ("14.3", "scoring_contract_audit", "results/stage14/s143_scoring_contract/attempt_*"),
    ("14.4", "structure_overlap", "results/stage14/s144_structure_overlap/attempt_*"),
    ("14.5", "validation_materials", "docs/validation/v2/materials/v*"),
    ("14.6", "v2_structures", "data/v2/structures/v*"),
    ("14.7", "model_smoke", "results/infrastructure/model_smoke/attempt_20261017_*"),
    ("14.7", "pilot_plan", "results/stage14/s147_pilot_plan/attempt_*"),
    ("14.7", "pilot_run", "results/stage14/s147_pilot_run/attempt_*"),
    ("14.8", "pilot_analysis", "results/stage14/s148_pilot_analysis/attempt_*"),
    ("14.9", "noise_and_anchor_analysis", "results/stage14/s149_noise_and_anchor/attempt_*"),
    ("14.13", "reasoning_run", "results/stage14/s152_reasoning_run/attempt_*"),
    ("14.13", "reasoning_analysis", "results/stage14/s153_reasoning_analysis/attempt_*"),
    ("14.12", "copying_vs_relevance", "results/stage14/s151_copying_vs_relevance/attempt_*"),
    ("14.10", "x03_plan", "results/stage14/x03_format_tokenization/plan/attempt_*"),
    ("14.10", "x03_run", "results/stage14/x03_format_tokenization/run/attempt_*"),
    ("14.10", "x03_analysis", "results/stage14/x03_format_tokenization/analysis/attempt_*"),
)
# Output directories whose names do not carry the Slurm job id.
EXTRA_JOB_LINKS = {"399217": "results/infrastructure/model_smoke/attempt_20261017_gpu_h100"}
SACCT_COLUMNS = ("JobIDRaw", "JobName", "Partition", "State", "Elapsed", "ExitCode", "NodeList", "AllocTRES")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def directory_files(directory: Path) -> dict[str, str]:
    return {str(p.relative_to(directory)): sha256_file(p) for p in sorted(directory.rglob("*")) if p.is_file()}


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def entry_for(root: Path, stage: str, kind: str, directory: Path) -> dict[str, Any]:
    files = directory_files(directory)
    meta: dict[str, Any] = {}
    for name in SUMMARY_FILES:
        if name in files:
            meta = read_json(directory / name)
            break
    relative = str(directory.relative_to(root))
    return {
        "artifact_id": f"{stage}:{kind}:{directory.name}", "stage": stage, "kind": kind, "path": relative,
        "files": files, "n_files": len(files), "bytes": sum((directory / f).stat().st_size for f in files),
        "source_commit": meta.get("source_commit"), "authorization_ref": meta.get("authorization_ref"),
        "dtype": meta.get("dtype"), "model_key": meta.get("model_key"),
        "evidence_class": meta.get("evidence_class") or "derived or preparatory; no run authority claimed",
        "data_role": meta.get("data_role", "EXPLORATION"), "paper_eligible": False,
    }


def scan(root: Path) -> list[dict[str, Any]]:
    entries = []
    for stage, kind, pattern in ARTIFACT_GLOBS:
        for directory in sorted(root.glob(pattern)):
            if directory.is_dir():
                entries.append(entry_for(root, stage, kind, directory))
    return entries


def read_register(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compare(root: Path, registered: dict[str, Any]) -> list[str]:
    """Problems for one registered artifact: missing directory, changed, missing or unregistered files."""

    directory = root / registered["path"]
    if not directory.is_dir():
        return [f"{registered['artifact_id']}: directory is missing"]
    now = directory_files(directory)
    problems = []
    for name, digest in registered["files"].items():
        if name not in now:
            problems.append(f"{registered['artifact_id']}: file removed: {name}")
        elif now[name] != digest:
            problems.append(f"{registered['artifact_id']}: file changed: {name}")
    for name in sorted(set(now) - set(registered["files"])):
        problems.append(f"{registered['artifact_id']}: unregistered file added: {name}")
    return problems


def verify(root: Path, register_path: Path) -> list[str]:
    rows = read_register(register_path)
    if not rows:
        return [f"{register_path}: the register is missing or empty (an empty register is an error, not a pass)"]
    problems: list[str] = []
    for row in rows:
        problems += compare(root, row)
    known = {row["path"] for row in rows}
    for entry in scan(root):
        if entry["path"] not in known:
            problems.append(f"{entry['artifact_id']}: artifact directory is not registered")
    return problems


def write(root: Path, register_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Append unregistered artifacts; refuse if a registered one has changed."""

    existing = read_register(register_path)
    problems = [p for row in existing for p in compare(root, row)]
    if problems:
        return [], problems
    known = {row["path"] for row in existing}
    new = [e for e in scan(root) if e["path"] not in known]
    if new:
        register_path.parent.mkdir(parents=True, exist_ok=True)
        with register_path.open("a", encoding="utf-8") as handle:
            for entry in new:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return new, []


def parse_sacct(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    header = lines[0].split("|")
    return [dict(zip(header, line.split("|"), strict=False)) for line in lines[1:]]


def sacct_rows(job_ids: list[str]) -> list[dict[str, str]]:
    result = subprocess.run(["sacct", "-X", "-P", "-j", ",".join(job_ids), "-o", ",".join(SACCT_COLUMNS)],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"sacct failed: {result.stderr.strip()}")
    return parse_sacct(result.stdout)


def add_jobs(root: Path, job_path: Path, job_ids: list[str], rows: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    rows = rows if rows is not None else sacct_rows(job_ids)
    present = {json.loads(line)["job_id"] for line in job_path.read_text(encoding="utf-8").splitlines()
               if line.strip()} if job_path.exists() else set()
    added = []
    for row in rows:
        job_id = row["JobIDRaw"]
        if job_id in present:
            continue
        artifacts = sorted(str(p.relative_to(root)) for _, _, pattern in ARTIFACT_GLOBS for p in root.glob(pattern)
                           if f"attempt_{job_id}_" in p.name)
        extra = EXTRA_JOB_LINKS.get(job_id)
        if extra and (root / extra).is_dir():
            artifacts = sorted({*artifacts, extra})
        added.append({"job_id": job_id, "job_name": row["JobName"], "partition": row["Partition"], "state": row["State"],
                      "elapsed": row["Elapsed"], "exit_code": row["ExitCode"], "node": row["NodeList"],
                      "alloc_tres": row["AllocTRES"], "artifact_dirs": artifacts, "source": "sacct, read-only"})
    if added:
        job_path.parent.mkdir(parents=True, exist_ok=True)
        with job_path.open("a", encoding="utf-8") as handle:
            for row in added:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--add-jobs", nargs="+", metavar="JOB_ID")
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--register", default=ARTIFACT_REGISTER)
    parser.add_argument("--job-register", default=JOB_REGISTER)
    args = parser.parse_args()
    root = Path(args.root)
    if args.verify:
        problems = verify(root, root / args.register)
        for problem in problems:
            print(problem, file=sys.stderr)
        print(json.dumps({"verified": not problems, "n_problems": len(problems)}))
        return 1 if problems else 0
    if args.write:
        new, problems = write(root, root / args.register)
        for problem in problems:
            print(f"refusing to register: {problem}", file=sys.stderr)
        print(json.dumps({"registered_new": [e["artifact_id"] for e in new], "n_problems": len(problems)}))
        return 1 if problems else 0
    added = add_jobs(root, root / args.job_register, args.add_jobs)
    print(json.dumps({"jobs_added": [r["job_id"] for r in added]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
