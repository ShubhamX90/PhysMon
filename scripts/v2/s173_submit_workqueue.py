#!/usr/bin/env python3
"""Stage 15: register frozen runs and submit GPU jobs to several partitions at once (standing Slurm authority of 2026-11-12).

Subcommands:

* `register`        add a checked run to the active-runs list that generic workers pull from (`s174_dispatch.py`).
* `deactivate`      mark a registered run inactive (workers skip it; nothing is deleted).
* `submit-workers`  submit generic worker jobs (`slurm/templates/stage15_dispatch.sh`) that run registered work when they start.
* `submit-run`      submit jobs bound to one run (`slurm/templates/stage15_workqueue.sh`).

Steps, each refusing on any doubt:

1. The worktree has no uncommitted tracked changes, HEAD is on origin, and the run's spec and shards are committed at HEAD.
2. An immutable snapshot of HEAD is made under /scratch/pabitra/physmon/snapshots/<sha> (git archive; read-only), so later
   edits of the worktree never change a queued job.
3. Live preflight: the account's queue (`squeue -u pabitra`), the GPU partitions (`sinfo`), and the spec's SHA-256 computed
   from the committed file.
4. Optional (`--cancel-foreign-pending`): PENDING jobs of the `pabitra` account that are not PhysMon's (name not starting
   with `physmon`) are cancelled, after `scontrol show job -dd` and `scontrol write batch_script` are saved under
   docs/registry/v2/cancelled_foreign_jobs/<job id>/ and logged, so their owners can resubmit. RUNNING jobs are never touched.
5. For every requested partition and copy: `sbatch --test-only` first, then the real submission; every submission is
   appended to docs/registry/v2/stage15_submissions.jsonl.

`--dry-run` stops after the test-only submissions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_ROOT = Path("/scratch/pabitra/physmon/snapshots")
TEMPLATE = "slurm/templates/stage15_workqueue.sh"
DISPATCH_TEMPLATE = "slurm/templates/stage15_dispatch.sh"
ACTIVE_RUNS = Path("/scratch/pabitra/physmon/queue/ACTIVE_RUNS.json")
DEFAULT_DISPATCH_PYTHON = str(Path.home() / ".conda/envs/physmon/bin/python")
SUBMISSIONS = REPO_ROOT / "docs/registry/v2/stage15_submissions.jsonl"
CANCELLED_DIR = REPO_ROOT / "docs/registry/v2/cancelled_foreign_jobs"
CANCELLED_LOG = CANCELLED_DIR / "cancelled.jsonl"
ACCOUNT_USER = "pabitra"

# Partition -> sbatch resources. gpu_rtx_pro_6000_6_csis_hyd rejects this account ("Invalid qos specification", 2026-11-12);
# V100 nodes are too small and too old for the Stage 15 models.
PARTITIONS = {
    "h100": {"partition": "gpu_h100_4", "gres": "gpu:nvidia_h100_80gb_hbm3:1", "max_time": "4-00:00:00", "blackwell": False},
    "h200": {"partition": "gpu_h200_8", "gres": "gpu:nvidia_h200_nvl:1", "max_time": "1-00:00:00", "blackwell": False},
    "a100": {"partition": "gpu_a100_8", "gres": "gpu:nvidia_a100-sxm4-80gb:1", "max_time": "5-00:00:00", "blackwell": False},
}


def run(cmd: list[str], *, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=cwd or REPO_ROOT)


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


def seconds(walltime: str) -> int:
    days = 0
    if "-" in walltime:
        d, walltime = walltime.split("-", 1)
        days = int(d)
    parts = [int(x) for x in walltime.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return days * 86400 + h * 3600 + m * 60 + s


def check_clean_pushed() -> str:
    """HEAD's sha after refusing on any uncommitted tracked change or an unpushed HEAD."""

    dirty = [line for line in git("status", "--porcelain").splitlines() if not line.startswith("??")]
    if dirty:
        raise SystemExit(f"Refusing: uncommitted tracked changes: {dirty[:5]}")
    head = git("rev-parse", "HEAD")
    run(["git", "fetch", "-q", "origin"])
    if not git("branch", "-r", "--contains", head):
        raise SystemExit("Refusing: HEAD is not on any remote branch (push first)")
    return head


def check_repo(run_id: str) -> tuple[str, str]:
    """(HEAD sha, spec sha256) after refusing on any uncommitted tracked change, unpushed HEAD or uncommitted run files."""

    head = check_clean_pushed()
    spec_rel = f"data/v2/runs/{run_id}/spec.json"
    try:
        spec_bytes = run(["git", "show", f"HEAD:{spec_rel}"]).stdout.encode("utf-8")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Refusing: {spec_rel} is not committed at HEAD") from exc
    spec = json.loads(spec_bytes)
    for name in spec["shards"]:
        run(["git", "cat-file", "-e", f"HEAD:data/v2/runs/{run_id}/shards/{name}.jsonl"])
    on_disk = (REPO_ROOT / spec_rel).read_bytes()
    if on_disk != spec_bytes:
        raise SystemExit("Refusing: spec.json on disk differs from HEAD")
    return head, hashlib.sha256(spec_bytes).hexdigest()


SNAPSHOT_PATHS = ("src", "scripts", "slurm", "data/v2", "docs/model_registry.yml", "docs/model_manifests", "Makefile")


def _skip_links(member: tarfile.TarInfo, dest: str) -> tarfile.TarInfo | None:
    """The tar 'data' filter, except that links are skipped (the repo tracks a few absolute symlinks into old laptops)."""

    if member.issym() or member.islnk():
        return None
    return tarfile.data_filter(member, dest)


def make_snapshot(head: str) -> Path:
    """An immutable copy of the job-relevant paths of commit `head` under SNAPSHOT_ROOT/<head> (git archive; read-only)."""

    target = SNAPSHOT_ROOT / head
    if (target / ".physmon_git_commit").exists():
        if (target / ".physmon_git_commit").read_text().strip() != head:
            raise SystemExit(f"Refusing: snapshot {target} records another commit")
        return target
    tmp = SNAPSHOT_ROOT / f".{head}.{os.getpid()}.tmp"
    tar_path = tmp.with_suffix(".tar")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        proc = subprocess.run(["git", "archive", "--format=tar", head, "--", *SNAPSHOT_PATHS], capture_output=True,
                              check=True, cwd=REPO_ROOT)
        tar_path.write_bytes(proc.stdout)
        with tarfile.open(tar_path) as handle:
            handle.extractall(tmp, filter=_skip_links)
        (tmp / ".physmon_git_commit").write_text(head + "\n")
        for path in tmp.rglob("*"):
            if path.is_file():
                path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        try:
            os.rename(tmp, target)
        except OSError:
            if (target / ".physmon_git_commit").exists() and (target / ".physmon_git_commit").read_text().strip() == head:
                return target  # a concurrent call made the same snapshot first
            raise
    finally:
        tar_path.unlink(missing_ok=True)
        if tmp.exists():
            for path in tmp.rglob("*"):
                try:
                    path.chmod(0o700 if path.is_dir() else 0o600)
                except OSError:
                    pass
            shutil.rmtree(tmp, ignore_errors=True)
    return target


def account_queue() -> list[dict[str, str]]:
    out = run(["squeue", "-h", "-u", ACCOUNT_USER, "-o", "%i|%j|%T|%P|%r|%M"]).stdout
    rows = []
    for line in out.splitlines():
        job_id, name, state, partition, reason, elapsed = (line.split("|") + [""] * 6)[:6]
        rows.append({"job_id": job_id, "name": name, "state": state, "partition": partition, "reason": reason,
                     "elapsed": elapsed})
    return rows


def cancel_foreign_pending(dry_run: bool) -> list[dict[str, Any]]:
    cancelled = []
    for job in account_queue():
        if job["state"] != "PENDING" or job["name"].startswith("physmon"):
            continue
        record = {**job, "cancelled_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "dry_run": dry_run,
                  "authority": "standing Slurm authority of 2026-11-12 (AGENTS.md item 5)"}
        if not dry_run:
            folder = CANCELLED_DIR / f"{job['job_id']}_{job['name']}"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "show_job.txt").write_text(run(["scontrol", "show", "job", "-dd", job["job_id"]], check=False).stdout)
            script = run(["scontrol", "write", "batch_script", job["job_id"], str(folder / "batch_script.sh")], check=False)
            record["batch_script_saved"] = script.returncode == 0 and (folder / "batch_script.sh").exists()
            # re-check the state immediately before cancelling, and let scancel itself refuse a job that has started
            state = run(["squeue", "-h", "-j", job["job_id"], "-o", "%T"], check=False).stdout.strip()
            if state != "PENDING":
                record["skipped"] = f"state is now {state or 'gone'}"
            else:
                result = run(["scancel", "--state=PENDING", job["job_id"]], check=False)
                record["scancel_rc"] = result.returncode
            CANCELLED_LOG.parent.mkdir(parents=True, exist_ok=True)
            with CANCELLED_LOG.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
        cancelled.append(record)
    return cancelled


def sbatch_command(part: dict[str, Any], *, walltime_req: str, margin_s: int, cpus: int, mem: str, job_name: str,
                   exports: dict[str, str], template: Path, test_only: bool) -> list[str]:
    walltime = walltime_req if seconds(walltime_req) <= seconds(part["max_time"]) else part["max_time"]
    budget = max(seconds(walltime) - margin_s, 600)
    exports.update(TIME_BUDGET_S=str(budget))  # the caller's dict now carries the budget; it is passed via the environment
    cmd = ["sbatch", "--parsable", f"--partition={part['partition']}", f"--gres={part['gres']}", f"--cpus-per-task={cpus}",
           f"--mem={mem}", f"--time={walltime}", f"--job-name={job_name}", "--export=ALL"]
    if test_only:
        cmd.insert(1, "--test-only")
    cmd.append(str(template))
    return cmd


def run_with_env(cmd: list[str], exports: dict[str, str]) -> subprocess.CompletedProcess:
    """Run sbatch with the job variables in its environment (--export=ALL), so values may contain commas or spaces."""

    return subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=REPO_ROOT, env={**os.environ, **exports})


def submit(partitions: list[str], args: argparse.Namespace, *, job_name: str, exports: dict[str, str], template: Path,
           record: dict[str, Any]) -> int:
    tested = {}
    for key in partitions:  # every test-only submission first: nothing is cancelled if a command would be rejected
        part = PARTITIONS[key]
        env = dict(exports)
        cmd = sbatch_command(part, walltime_req=args.time, margin_s=args.margin_s, cpus=args.cpus, mem=args.mem,
                             job_name=job_name, exports=env, template=template, test_only=True)
        test = run_with_env(cmd, env)
        tested[key] = test.returncode == 0
        print(json.dumps({"partition": key, "test_only_rc": test.returncode, "test_only": (test.stderr or test.stdout).strip()}))
    if args.dry_run or not any(tested.values()):
        return 0 if args.dry_run else 1
    if args.cancel_foreign_pending:
        print(json.dumps({"cancelled_foreign_pending": cancel_foreign_pending(False)}, indent=2))
    submitted = []
    SUBMISSIONS.parent.mkdir(parents=True, exist_ok=True)
    for key in partitions:
        if not tested[key]:
            continue
        part = PARTITIONS[key]
        for copy in range(args.copies):
            env = dict(exports)
            cmd = sbatch_command(part, walltime_req=args.time, margin_s=args.margin_s, cpus=args.cpus, mem=args.mem,
                                 job_name=job_name, exports=env, template=template, test_only=False)
            base = {**record, "partition": part["partition"], "copy": copy, "command": cmd, "exports": env}
            with SUBMISSIONS.open("a", encoding="utf-8") as handle:  # intent first, so a later failure leaves a trace
                handle.write(json.dumps({**base, "event_phase": "intent", "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")},
                                        sort_keys=True) + "\n")
            result = run_with_env(cmd, env)
            entry = {**base, "event_phase": "result", "rc": result.returncode,
                     "job_id": result.stdout.strip().split(";")[0] if result.returncode == 0 else None,
                     "stderr": result.stderr.strip(), "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            with SUBMISSIONS.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
            submitted.append(entry)
            print(json.dumps({k: entry[k] for k in ("partition", "copy", "rc", "job_id", "stderr")}))
    return 0 if all(e["rc"] == 0 for e in submitted) else 1


def _locked_update(path: Path, update) -> dict[str, Any]:
    """Read-modify-write of the active-runs list under an exclusive lock."""

    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.parent / ".ACTIVE_RUNS.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"entries": []}
        data = update(data)
        tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)
        fcntl.flock(lock, fcntl.LOCK_UN)
    return data


def cmd_register(args: argparse.Namespace) -> int:
    spec = json.loads((REPO_ROOT / f"data/v2/runs/{args.run_id}/spec.json").read_text(encoding="utf-8"))
    env_prefix = Path(spec["env_prefix"])
    if not (env_prefix / "bin" / "python").exists():
        raise SystemExit(f"Refusing: no python in {env_prefix}")
    head, spec_sha = check_repo(args.run_id)
    snapshot = make_snapshot(head)
    probe = subprocess.run([str(env_prefix / "bin" / "python"), str(snapshot / "scripts/v2/s170_sampled_run.py"), "status",
                            "--run-id", args.run_id, "--queue-root", str(Path(args.active).parent / args.run_id)],
                           capture_output=True, text=True, cwd=snapshot, timeout=900,
                           env={**os.environ, "PYTHONPATH": str(snapshot / "src"), "PYTHONNOUSERSITE": "1"})
    if probe.returncode != 0:
        raise SystemExit(f"Refusing: the run's environment cannot run the snapshot's code:\n{probe.stderr[-2000:]}")
    exclude = list(args.exclude_gpu)
    if spec["backend"] != "vllm" and "RTX PRO 6000" not in exclude:
        exclude.append("RTX PRO 6000")  # the physmon torch has no Blackwell kernels
    entry = {"run_id": args.run_id, "commit": head, "snapshot": str(snapshot), "spec_sha256": spec_sha,
             "env_prefix": str(env_prefix), "shards": sorted(spec["shards"]), "priority": args.priority,
             "min_gpu_memory_gb": args.min_gpu_memory_gb, "exclude_gpu_substrings": exclude, "alloc_conf": args.alloc_conf,
             "registered_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "active": True, "model_key": spec["model_key"],
             "min_driver_major": args.min_driver_major if args.min_driver_major is not None else
             (580 if spec["backend"] == "vllm" else 0),
             "backend": spec["backend"], "purpose": spec.get("purpose")}

    def update(data: dict[str, Any]) -> dict[str, Any]:
        if any(e["run_id"] == args.run_id for e in data["entries"]):
            raise SystemExit(f"Refusing: {args.run_id} is already registered")
        data["entries"].append(entry)
        return data

    _locked_update(Path(args.active), update)
    (Path(args.active).parent / args.run_id).mkdir(parents=True, exist_ok=True)
    print(json.dumps({"registered": entry}, indent=2))
    with SUBMISSIONS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "register", **entry}, sort_keys=True) + "\n")
    return 0


def cmd_deactivate(args: argparse.Namespace) -> int:
    def update(data: dict[str, Any]) -> dict[str, Any]:
        hits = [e for e in data["entries"] if e["run_id"] == args.run_id]
        if not hits:
            raise SystemExit(f"{args.run_id} is not registered")
        for e in hits:
            e["active"] = False
        return data

    _locked_update(Path(args.active), update)
    print(json.dumps({"deactivated": args.run_id}))
    return 0


def cmd_submit_workers(args: argparse.Namespace) -> int:
    head = check_clean_pushed()
    snapshot = make_snapshot(head)
    if not (snapshot / "scripts/v2/s174_dispatch.py").exists():
        raise SystemExit("Refusing: the snapshot has no dispatcher")
    print(json.dumps({"head": head, "snapshot": str(snapshot), "account_queue": account_queue()}, indent=2))
    exports = {"DISPATCH_SNAPSHOT": str(snapshot), "DISPATCH_PYTHON": args.dispatch_python,
               "AUTHORIZATION_REF": args.authorization_ref}
    return submit(args.partitions, args, job_name="physmon_s15_worker", exports=exports,
                  template=snapshot / DISPATCH_TEMPLATE, record={"event": "submit-workers", "source_commit": head})


def cmd_submit_run(args: argparse.Namespace) -> int:
    spec = json.loads((REPO_ROOT / f"data/v2/runs/{args.run_id}/spec.json").read_text(encoding="utf-8"))
    env_prefix = Path(spec["env_prefix"])
    if spec["backend"] != "vllm" and any(PARTITIONS[p]["blackwell"] for p in args.partitions):
        raise SystemExit("Refusing: Blackwell partitions only for the CUDA 13 vLLM environment")
    head, spec_sha = check_repo(args.run_id)
    snapshot = make_snapshot(head)
    print(json.dumps({"head": head, "snapshot": str(snapshot), "spec_sha256": spec_sha, "account_queue": account_queue()},
                     indent=2))
    exports = {"RUN_ID": args.run_id, "SNAPSHOT": str(snapshot), "ENV_PREFIX": str(env_prefix), "SPEC_SHA256": spec_sha,
               "AUTHORIZATION_REF": args.authorization_ref, "ALLOC_CONF": args.alloc_conf}
    return submit(args.partitions, args, job_name=f"physmon_s15_{args.run_id[:24]}", exports=exports,
                  template=snapshot / TEMPLATE, record={"event": "submit-run", "run_id": args.run_id, "source_commit": head,
                                                        "spec_sha256": spec_sha})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    reg = sub.add_parser("register")
    reg.add_argument("--run-id", required=True)
    reg.add_argument("--priority", type=int, default=100, help="lower runs first")
    reg.add_argument("--min-gpu-memory-gb", type=float, default=70.0)
    reg.add_argument("--exclude-gpu", nargs="*", default=["V100"])
    reg.add_argument("--alloc-conf", default="")
    reg.add_argument("--min-driver-major", type=int, default=None, help="default 580 for vLLM (CUDA 13 wheels), else 0")
    reg.add_argument("--active", default=str(ACTIVE_RUNS))
    de = sub.add_parser("deactivate")
    de.add_argument("--run-id", required=True)
    de.add_argument("--active", default=str(ACTIVE_RUNS))
    for name in ("submit-workers", "submit-run"):
        s = sub.add_parser(name)
        if name == "submit-run":
            s.add_argument("--run-id", required=True)
            s.add_argument("--alloc-conf", default="")
        else:
            s.add_argument("--dispatch-python", default=DEFAULT_DISPATCH_PYTHON)
        s.add_argument("--partitions", nargs="+", default=["h100", "h200", "a100"], choices=sorted(PARTITIONS))
        s.add_argument("--copies", type=int, default=1, help="copies per partition")
        s.add_argument("--time", default="1-00:00:00")
        s.add_argument("--margin-s", type=int, default=1800, help="walltime minus this is the worker's time budget")
        s.add_argument("--cpus", type=int, default=6)
        s.add_argument("--mem", default="120G")
        s.add_argument("--authorization-ref", default="standing-slurm-authority-2026-11-12")
        s.add_argument("--cancel-foreign-pending", action="store_true")
        s.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    return {"register": cmd_register, "deactivate": cmd_deactivate, "submit-workers": cmd_submit_workers,
            "submit-run": cmd_submit_run}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
