#!/usr/bin/env python3
"""Collect a run-level inventory of PhysMon Slurm jobs from Sharanga.

This script runs *on Sharanga*, where the scratch Slurm log root and the Slurm
accounting database are visible.  It emits a compact JSONL manifest that points
at the remote raw logs rather than copying them, per the project rule that bulky
runtime data stays on scratch while provenance is versioned.

Two facts about this evidence source matter scientifically:

1.  Log filenames carry the real Slurm job ID under two historical conventions
    (``<jobid>_<name>.out`` and ``<name>_<jobid>.out``).  Both are parsed; a file
    matching neither is recorded as ``job_id_parse_failed`` rather than guessed.
2.  ``sacct`` is authoritative for terminal state.  A job present in the logs but
    absent from accounting is recorded as ``accounting_unavailable``; it is never
    assumed to have succeeded.

Nothing here infers scientific validity.  A ``COMPLETED`` Slurm state is a
scheduler outcome, not evidence that a run produced valid science.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# `<jobid>_<jobname>.out` -- the `%j_%x` convention in slurm/templates/*.sh
LEADING_JOB_ID = re.compile(r"^(?P<job_id>\d+)_(?P<job_name>.+)\.(?P<stream>out|err)$")
# `<jobname>_<jobid>.out` -- the older convention still present in the log root
TRAILING_JOB_ID = re.compile(r"^(?P<job_name>.+)_(?P<job_id>\d+)\.(?P<stream>out|err)$")

# Header lines emitted by the standard job template.
HEADER_FIELDS = {
    "Job ID:": "template_job_id",
    "Node:": "node",
    "GPU:": "gpu",
    "Script:": "script",
    "Args:": "args",
}

SACCT_FIELDS = [
    "JobID",
    "JobName",
    "Partition",
    "State",
    "Elapsed",
    "ExitCode",
    "Submit",
    "Start",
    "End",
    "ReqTRES",
    "NodeList",
]

HEADER_SCAN_LINES = 40


def parse_log_name(name: str) -> tuple[str | None, str | None, str | None]:
    """Return ``(job_id, job_name, stream)`` for a Slurm log filename.

    Returns ``(None, None, None)`` when neither historical convention matches, so
    the caller can record a parse failure instead of inventing an identity.
    """

    for pattern in (LEADING_JOB_ID, TRAILING_JOB_ID):
        match = pattern.match(name)
        if match:
            return match["job_id"], match["job_name"], match["stream"]
    return None, None, None


def read_header(path: Path) -> dict[str, str]:
    """Extract template header fields from the first lines of a job log."""

    found: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for _, line in zip(range(HEADER_SCAN_LINES), handle):
                for prefix, key in HEADER_FIELDS.items():
                    if line.startswith(prefix):
                        found[key] = line[len(prefix) :].strip()
    except OSError as exc:
        found["header_read_error"] = str(exc)
    return found


def collect_sacct(start_time: str) -> dict[str, dict[str, str]]:
    """Return authoritative accounting rows keyed by job ID.

    Only top-level job rows are kept; ``.batch`` and ``.extern`` steps are folded
    away because they duplicate the parent job's identity.
    """

    command = [
        "sacct",
        "--user",
        os.environ.get("USER", ""),
        "--starttime",
        start_time,
        "--format",
        ",".join(SACCT_FIELDS),
        "--parsable2",
        "--noheader",
    ]
    try:
        raw = subprocess.run(
            command, capture_output=True, text=True, timeout=300, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"warning: sacct unavailable: {exc}", file=sys.stderr)
        return {}
    if raw.returncode != 0:
        print(f"warning: sacct exit {raw.returncode}: {raw.stderr.strip()}", file=sys.stderr)
        return {}

    rows: dict[str, dict[str, str]] = {}
    for line in raw.stdout.splitlines():
        parts = line.split("|")
        if len(parts) != len(SACCT_FIELDS):
            continue
        record = dict(zip(SACCT_FIELDS, parts))
        job_id = record["JobID"]
        if "." in job_id:  # a step row, not the job itself
            continue
        rows[job_id] = record
    return rows


def build_inventory(log_root: Path, sacct_rows: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Group log files by job ID and join them with accounting state."""

    jobs: dict[str, dict[str, Any]] = {}
    parse_failures: list[dict[str, Any]] = []

    for path in sorted(log_root.iterdir()):
        if not path.is_file() or path.suffix not in {".out", ".err"}:
            continue
        job_id, job_name, stream = parse_log_name(path.name)
        if job_id is None:
            parse_failures.append(
                {
                    "job_id": None,
                    "job_id_source": "job_id_parse_failed",
                    "log_filename": path.name,
                    "log_root": str(log_root),
                }
            )
            continue

        job = jobs.setdefault(
            job_id,
            {
                "job_id": job_id,
                "job_id_source": "slurm_log_filename",
                "job_name_from_log": job_name,
                "log_root": str(log_root),
                "stdout_path": "",
                "stderr_path": "",
                "stdout_bytes": None,
                "stderr_bytes": None,
                "header": {},
            },
        )
        size = path.stat().st_size
        if stream == "out":
            job["stdout_path"] = str(path)
            job["stdout_bytes"] = size
            job["header"].update(read_header(path))
        else:
            job["stderr_path"] = str(path)
            job["stderr_bytes"] = size

    records = []
    for job_id, job in sorted(jobs.items(), key=lambda item: int(item[0])):
        accounting = sacct_rows.get(job_id)
        job["accounting_status"] = "sacct" if accounting else "accounting_unavailable"
        job["accounting"] = accounting or {}
        job["terminal_state"] = accounting.get("State", "unknown") if accounting else "unknown"
        job["partition"] = accounting.get("Partition", "") if accounting else ""
        job["exit_code"] = accounting.get("ExitCode", "") if accounting else ""
        job["elapsed"] = accounting.get("Elapsed", "") if accounting else ""
        job["submit"] = accounting.get("Submit", "") if accounting else ""
        job["start"] = accounting.get("Start", "") if accounting else ""
        job["end"] = accounting.get("End", "") if accounting else ""
        job["req_tres"] = accounting.get("ReqTRES", "") if accounting else ""
        job["node_list"] = accounting.get("NodeList", "") if accounting else ""
        # A scheduler outcome is not a scientific outcome. Say so in the record.
        job["scientific_validity"] = "not_assessed_by_this_collector"
        records.append(job)

    records.extend(parse_failures)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-root",
        default=os.environ.get("PHYSMON_SLURM_LOG_ROOT", ""),
        help="Slurm log directory on scratch. Defaults to $PHYSMON_SLURM_LOG_ROOT, "
        "else $SCRATCH/physmon/slurm_logs.",
    )
    parser.add_argument(
        "--sacct-start",
        default="2026-05-01",
        help="Earliest submit date passed to sacct.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination JSONL path for the run inventory manifest.",
    )
    args = parser.parse_args()

    log_root = args.log_root
    if not log_root:
        scratch = os.environ.get("SCRATCH")
        if not scratch:
            parser.error(
                "--log-root not given and neither PHYSMON_SLURM_LOG_ROOT nor SCRATCH is set."
            )
        log_root = str(Path(scratch) / "physmon" / "slurm_logs")

    root = Path(log_root)
    if not root.is_dir():
        parser.error(f"log root does not exist or is not a directory: {root}")

    sacct_rows = collect_sacct(args.sacct_start)
    records = build_inventory(root, sacct_rows)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")

    resolved = sum(1 for r in records if r.get("job_id"))
    accounted = sum(1 for r in records if r.get("accounting_status") == "sacct")
    print(
        f"jobs_with_resolved_id={resolved} "
        f"jobs_with_accounting={accounted} "
        f"parse_failures={len(records) - resolved} "
        f"output={output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
