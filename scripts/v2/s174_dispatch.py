#!/usr/bin/env python3
"""Stage 15: a generic GPU worker that pulls frozen runs from an active-runs list (pilot-job pattern).

Queue waits on the shared cluster are days to weeks and are set by priority, not by walltime, so generic worker jobs are
submitted early and do whatever registered work exists when they start. The active-runs list
(`/scratch/pabitra/physmon/queue/ACTIVE_RUNS.json`) is written only by `s173_submit_workqueue.py register`, after that run's
checks: spec and shards committed at a pushed commit, an immutable snapshot of that commit, the spec's SHA-256. For each
entry, in priority order, that is compatible with this node's GPU and has open shards, the dispatcher runs the entry's own
snapshot (`<snapshot>/scripts/v2/s170_sampled_run.py work`) with the entry's environment, commit and spec hash, and the time
left in this job. Records therefore carry the commit of the run's own snapshot, not of the worker's.

The dispatcher never edits the list and never runs code from the live worktree. It exits when no compatible entry has open
shards or the time budget is spent.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

DEFAULT_ACTIVE = "/scratch/pabitra/physmon/queue/ACTIVE_RUNS.json"
QUEUE_ROOT = "/scratch/pabitra/physmon/queue"
MIN_STEP_S = 900  # do not start an entry with less than this much budget left


def gpu_info() -> dict[str, Any] | None:
    """Name, memory and driver major version of this job's GPU, or None if nvidia-smi cannot be read."""

    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=60)
        name, mem, driver = [x.strip() for x in out.stdout.strip().splitlines()[0].split(",")]
        return {"name": name, "memory_gb": float(mem) / 1024.0, "driver_major": int(driver.split(".")[0]), "driver": driver}
    except Exception:
        return None


def compatible(entry: dict[str, Any], gpu: dict[str, Any]) -> bool:
    if gpu["memory_gb"] + 0.5 < float(entry.get("min_gpu_memory_gb", 0)):
        return False
    if int(gpu.get("driver_major", 0)) < int(entry.get("min_driver_major", 0)):
        return False
    return not any(s.lower() in gpu["name"].lower() for s in entry.get("exclude_gpu_substrings", []))


def open_shards(entry: dict[str, Any], queue_root: Path) -> int:
    """Shards of the entry without a done marker. Claimed shards count: the run's own worker reclaims dead claims and exits
    within seconds when every open shard is held by a live worker."""

    done = queue_root / entry["run_id"] / "done"
    return sum(not (done / f"{name}.json").exists() for name in entry["shards"])


REQUIRED_KEYS = ("run_id", "commit", "snapshot", "spec_sha256", "env_prefix", "shards", "registered_at")


def load_entries(path: Path) -> list[dict[str, Any]]:
    """Active, well-formed entries in priority order; a malformed list raises ValueError."""

    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding="utf-8")).get("entries", [])
    good = [e for e in entries if all(k in e for k in REQUIRED_KEYS) and e.get("active", True)]
    return sorted(good, key=lambda e: (int(e.get("priority", 100)), str(e["registered_at"])))


def run_entry(entry: dict[str, Any], budget_s: float, authorization_ref: str) -> int:
    snapshot = Path(entry["snapshot"])
    env = {**os.environ, "PHYSMON_SOURCE_COMMIT": entry["commit"], "PYTHONPATH": str(snapshot / "src"), "PYTHONNOUSERSITE": "1"}
    if entry.get("alloc_conf"):
        env["PYTORCH_CUDA_ALLOC_CONF"] = entry["alloc_conf"]
    else:
        env.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    cmd = [str(Path(entry["env_prefix"]) / "bin" / "python"), str(snapshot / "scripts/v2/s170_sampled_run.py"), "work",
           "--run-id", entry["run_id"], "--authorization-ref", authorization_ref, "--expect-spec-sha256", entry["spec_sha256"],
           "--time-budget-s", str(int(budget_s))]
    print(json.dumps({"event": "entry_start", "run_id": entry["run_id"], "commit": entry["commit"], "budget_s": int(budget_s),
                      "cmd": cmd}), flush=True)
    if not Path(cmd[0]).exists() or not Path(cmd[1]).exists():
        print(json.dumps({"event": "entry_unrunnable", "run_id": entry["run_id"], "missing": [c for c in cmd[:2]
                                                                                               if not Path(c).exists()]}), flush=True)
        return 30
    try:
        return subprocess.run(cmd, cwd=snapshot, env=env, timeout=budget_s + 600).returncode
    except subprocess.TimeoutExpired:
        print(json.dumps({"event": "entry_timeout", "run_id": entry["run_id"]}), flush=True)
        return 31


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--active", default=DEFAULT_ACTIVE)
    parser.add_argument("--queue-root", default=QUEUE_ROOT)
    parser.add_argument("--time-budget-s", type=float, required=True)
    parser.add_argument("--authorization-ref", required=True)
    parser.add_argument("--max-passes", type=int, default=50)
    args = parser.parse_args(argv)
    started = time.time()
    gpu = gpu_info()
    print(json.dumps({"event": "dispatcher_start", "gpu": gpu, "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
                      "budget_s": args.time_budget_s}), flush=True)
    if gpu is None:
        print(json.dumps({"event": "no_gpu_info", "error": "nvidia-smi could not be read"}), flush=True)
        return 2
    results = []
    attempted: set[str] = set()  # each entry runs at most once per job: a worker that stopped for time will not do better
    for _ in range(args.max_passes):
        left = args.time_budget_s - (time.time() - started)
        if left < MIN_STEP_S:
            break
        try:
            entries = load_entries(Path(args.active))
        except (OSError, ValueError) as exc:
            print(json.dumps({"event": "active_runs_unreadable", "error": repr(exc)}), flush=True)
            return 3
        candidates = [e for e in entries if e["run_id"] not in attempted and compatible(e, gpu)
                      and open_shards(e, Path(args.queue_root)) > 0]
        if not candidates:
            break
        entry = candidates[0]
        attempted.add(entry["run_id"])
        code = run_entry(entry, left, args.authorization_ref)
        results.append({"run_id": entry["run_id"], "exit": code, "elapsed_s": round(time.time() - started, 1)})
        print(json.dumps({"event": "entry_done", **results[-1]}), flush=True)
    print(json.dumps({"event": "dispatcher_done", "entries": results, "elapsed_s": round(time.time() - started, 1)}), flush=True)
    return 0 if all(r["exit"] == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
