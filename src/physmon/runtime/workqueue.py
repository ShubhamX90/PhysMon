"""A shared-filesystem work queue so the same Slurm job can be submitted to several partitions at once (Stage 15).

Work is a fixed list of shards (JSONL files). Any worker that starts claims the next shard that is neither done nor validly
claimed, by atomically creating `claims/<shard>/` (mkdir is atomic on POSIX and on the cluster's Lustre scratch). It writes the
shard's results to a private temporary file, renames it into `results/<shard>.jsonl` and then writes `done/<shard>.json`. A worker
that finds nothing left exits at once, so a duplicate job that starts late costs seconds, not GPU hours.

A claim carries an owner record and a heartbeat file refreshed by a background thread. A claim is reclaimed only when its owner is
gone: the owner's Slurm job is no longer in the queue, or (when `squeue` cannot tell) its heartbeat is older than `stale_after_s`.
A live answer from `squeue` always wins over a stale heartbeat. Reclaiming happens under a per-shard reclaim lock (an exclusively
created file), re-checks the owner inside the lock, and renames the dead claim aside, so two reclaimers cannot both win.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def slurm_job_alive(job_id: str) -> bool | None:
    """True if the Slurm job is still pending or running, False if not, None if this cannot be told (no squeue, no job id)."""

    if not job_id:
        return None
    try:
        out = subprocess.run(["squeue", "-h", "-j", str(job_id), "-o", "%T"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        # squeue exits non-zero for an unknown (finished) job id on most Slurm versions
        return False if "Invalid job id" in (out.stderr or "") else None
    state = out.stdout.strip()
    return state in {"PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "SUSPENDED", "REQUEUED", "RESIZING"}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


class WorkQueue:
    def __init__(self, root: Path, shard_names: list[str], *, worker_id: str | None = None, slurm_job_id: str = "",
                 stale_after_s: float = 900.0, alive_fn: Callable[[str], bool | None] = slurm_job_alive,
                 heartbeat_s: float = 60.0):
        self.root = Path(root)
        self.shard_names = sorted(shard_names)
        self.slurm_job_id = slurm_job_id or os.environ.get("SLURM_JOB_ID", "")
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}:{self.slurm_job_id or 'local'}"
        self.stale_after_s = stale_after_s
        self.alive_fn = alive_fn
        self.heartbeat_s = heartbeat_s
        for sub in ("claims", "done", "results", "stale", "workers"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        self._held: str | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # --- inspection -------------------------------------------------------------------------------------------------------
    def is_done(self, shard: str) -> bool:
        return (self.root / "done" / f"{shard}.json").exists()

    def remaining(self) -> list[str]:
        return [s for s in self.shard_names if not self.is_done(s)]

    def unclaimed(self) -> list[str]:
        return [s for s in self.remaining() if not (self.root / "claims" / s).exists() or self._claim_is_dead(s)]

    def owns(self, shard: str) -> bool:
        owner = self._owner(shard)
        return owner is not None and owner.get("worker_id") == self.worker_id

    def status(self) -> dict[str, Any]:
        done = [s for s in self.shard_names if self.is_done(s)]
        claimed = [s for s in self.shard_names if not self.is_done(s) and (self.root / "claims" / s).exists()]
        return {"n_shards": len(self.shard_names), "n_done": len(done), "n_claimed": len(claimed),
                "n_open": len(self.shard_names) - len(done) - len(claimed)}

    # --- claims -----------------------------------------------------------------------------------------------------------
    def _owner(self, shard: str) -> dict[str, Any] | None:
        try:
            return json.loads((self.root / "claims" / shard / "owner.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _heartbeat_age(self, shard: str) -> float | None:
        beat = self.root / "claims" / shard / "heartbeat"
        try:
            return time.time() - beat.stat().st_mtime
        except OSError:
            return None

    def _claim_is_dead(self, shard: str) -> bool:
        owner = self._owner(shard)
        age = self._heartbeat_age(shard)
        if owner is None:
            # a claim directory without an owner record: dead only once it is older than the stale limit
            try:
                age = time.time() - (self.root / "claims" / shard).stat().st_mtime
            except OSError:
                return False
            return age > self.stale_after_s
        if owner.get("worker_id") == self.worker_id:
            return False
        alive = self.alive_fn(str(owner.get("slurm_job_id", ""))) if owner.get("slurm_job_id") else None
        if alive is True:
            return False
        if alive is False:
            return True
        return age is not None and age > self.stale_after_s

    def _try_claim(self, shard: str) -> bool:
        claim = self.root / "claims" / shard
        try:
            claim.mkdir()
        except FileExistsError:
            return False
        _atomic_write_json(claim / "owner.json", {"worker_id": self.worker_id, "slurm_job_id": self.slurm_job_id,
                                                  "host": socket.gethostname(), "claimed_at": time.time()})
        (claim / "heartbeat").touch()
        return True

    def _reclaim(self, shard: str) -> bool:
        """Under an exclusive per-shard lock: re-check that the claim is dead, move it aside, then claim afresh."""

        claim = self.root / "claims" / shard
        lock = self.root / "claims" / f".{shard}.reclaim"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:  # a reclaimer that died inside the lock leaves it behind; locks older than a minute are broken
                if time.time() - lock.stat().st_mtime > 60:
                    lock.unlink()
            except OSError:
                pass
            return False
        try:
            os.write(fd, self.worker_id.encode())
            os.close(fd)
            if not claim.exists():
                return self._try_claim(shard)
            if not self._claim_is_dead(shard):
                return False
            aside = self.root / "stale" / f"{shard}.{time.time_ns()}.{os.getpid()}"
            try:
                os.rename(claim, aside)
            except OSError:
                return False
            return self._try_claim(shard)
        finally:
            try:
                lock.unlink()
            except OSError:
                pass

    def claim_next(self) -> str | None:
        """Claim and return the next open shard, or None when every shard is done or validly claimed by a live worker."""

        for shard in self.shard_names:
            if self.is_done(shard):
                continue
            if self._try_claim(shard) or (self._claim_is_dead(shard) and self._reclaim(shard)):
                if self.is_done(shard):  # finished between our check and our claim
                    self.release(shard)
                    continue
                self._held = shard
                self._start_heartbeat(shard)
                return shard
        return None

    def _start_heartbeat(self, shard: str) -> None:
        self._stop_heartbeat()
        self._stop = threading.Event()
        beat = self.root / "claims" / shard / "heartbeat"

        def run() -> None:
            while not self._stop.wait(self.heartbeat_s):
                try:
                    beat.touch()
                except OSError:
                    pass

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def _stop_heartbeat(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def release(self, shard: str) -> None:
        """Give a claimed shard back unfinished (time budget, clean abort)."""

        self._stop_heartbeat()
        claim = self.root / "claims" / shard
        owner = self._owner(shard)
        if owner is not None and owner.get("worker_id") == self.worker_id:
            shutil.rmtree(claim, ignore_errors=True)
        self._held = None

    def complete(self, shard: str, records: list[dict[str, Any]], meta: dict[str, Any]) -> Path:
        """Write the shard's records atomically, then its done marker (with the records' hash), then drop the claim."""

        self._stop_heartbeat()
        final = self.root / "results" / f"{shard}.jsonl"
        tmp = self.root / "results" / f".{shard}.{self.worker_id.replace(':', '_')}.{time.time_ns()}.tmp"
        with tmp.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n")
        os.replace(tmp, final)
        _atomic_write_json(self.root / "done" / f"{shard}.json", {
            **meta, "shard": shard, "worker_id": self.worker_id, "slurm_job_id": self.slurm_job_id, "n_records": len(records),
            "records_sha256": sha256_file(final), "completed_at": time.time()})
        if self.owns(shard):
            shutil.rmtree(self.root / "claims" / shard, ignore_errors=True)
        self._held = None
        return final

    def log_worker(self, payload: dict[str, Any]) -> None:
        _atomic_write_json(self.root / "workers" / f"{self.worker_id.replace(':', '_')}.json",
                           {**payload, "worker_id": self.worker_id, "slurm_job_id": self.slurm_job_id, "updated_at": time.time()})
