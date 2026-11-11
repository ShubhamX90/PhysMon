"""Tests for the shared-filesystem work queue (Stage 15): atomic claims, completion, release, reclaim and concurrency."""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.runtime.workqueue import WorkQueue  # noqa: E402

SHARDS = [f"shard_{i:04d}" for i in range(12)]


def test_claim_complete_and_nothing_left(tmp_path):
    q = WorkQueue(tmp_path, SHARDS[:2], worker_id="w1", alive_fn=lambda _: True)
    first = q.claim_next()
    assert first == "shard_0000"
    q.complete(first, [{"a": 1}], {"x": 1})
    done = json.loads((tmp_path / "done" / "shard_0000.json").read_text())
    assert done["n_records"] == 1 and done["worker_id"] == "w1"
    second = q.claim_next()
    q.complete(second, [], {})
    assert q.claim_next() is None and q.remaining() == [] and q.status()["n_done"] == 2


def test_a_live_claim_is_not_taken_but_a_released_one_is(tmp_path):
    a = WorkQueue(tmp_path, SHARDS[:1], worker_id="a", slurm_job_id="1", alive_fn=lambda _: True)
    b = WorkQueue(tmp_path, SHARDS[:1], worker_id="b", slurm_job_id="2", alive_fn=lambda _: True)
    shard = a.claim_next()
    assert shard and b.claim_next() is None
    a.release(shard)
    assert b.claim_next() == shard


def test_a_claim_whose_slurm_job_is_gone_is_reclaimed(tmp_path):
    a = WorkQueue(tmp_path, SHARDS[:1], worker_id="a", slurm_job_id="111", alive_fn=lambda _: True)
    a.claim_next()
    a._stop_heartbeat()
    b = WorkQueue(tmp_path, SHARDS[:1], worker_id="b", slurm_job_id="222", alive_fn=lambda job: job != "111")
    assert b.claim_next() == "shard_0000"
    assert any(p.name.startswith("shard_0000.") for p in (tmp_path / "stale").iterdir())


def test_a_claim_with_a_stale_heartbeat_is_reclaimed_when_the_owner_state_is_unknown(tmp_path):
    a = WorkQueue(tmp_path, SHARDS[:1], worker_id="a", slurm_job_id="", alive_fn=lambda _: None)
    a.claim_next()
    a._stop_heartbeat()
    old = time.time() - 10_000
    os.utime(tmp_path / "claims" / "shard_0000" / "heartbeat", (old, old))
    b = WorkQueue(tmp_path, SHARDS[:1], worker_id="b", alive_fn=lambda _: None, stale_after_s=60)
    assert b.claim_next() == "shard_0000"
    fresh = WorkQueue(tmp_path / "other", SHARDS[:1], worker_id="c", alive_fn=lambda _: None, stale_after_s=60)
    fresh.claim_next()
    fresh._stop_heartbeat()
    d = WorkQueue(tmp_path / "other", SHARDS[:1], worker_id="d", alive_fn=lambda _: None, stale_after_s=60)
    assert d.claim_next() is None


def _worker(root: str, name: str, out: str) -> None:
    q = WorkQueue(Path(root), SHARDS, worker_id=name, slurm_job_id=name, alive_fn=lambda _: True)
    taken = []
    while (shard := q.claim_next()) is not None:
        time.sleep(0.01)
        q.complete(shard, [{"shard": shard, "worker": name}], {})
        taken.append(shard)
    Path(out).write_text(json.dumps(taken))


def test_concurrent_workers_never_process_a_shard_twice(tmp_path):
    ctx = mp.get_context("fork")
    procs = [ctx.Process(target=_worker, args=(str(tmp_path / "q"), f"w{i}", str(tmp_path / f"w{i}.json"))) for i in range(4)]
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join(timeout=60)
    taken = [s for i in range(4) for s in json.loads((tmp_path / f"w{i}.json").read_text())]
    assert sorted(taken) == SHARDS
    assert len({json.loads((tmp_path / "q" / "results" / f"{s}.jsonl").read_text())["shard"] for s in SHARDS}) == 12


def test_a_live_slurm_job_beats_a_stale_heartbeat_and_complete_keeps_foreign_claims(tmp_path):
    a = WorkQueue(tmp_path, SHARDS[:1], worker_id="a", slurm_job_id="111", alive_fn=lambda _: True)
    a.claim_next()
    a._stop_heartbeat()
    old = time.time() - 10_000
    os.utime(tmp_path / "claims" / "shard_0000" / "heartbeat", (old, old))
    b = WorkQueue(tmp_path, SHARDS[:1], worker_id="b", slurm_job_id="222", alive_fn=lambda _: True, stale_after_s=60)
    assert b.claim_next() is None  # squeue says job 111 is alive: its claim stands
    b.complete("shard_0000", [], {})  # completing a shard it does not own never deletes the owner's claim
    assert (tmp_path / "claims" / "shard_0000").exists()


def _reclaimer(root: str, name: str, out: str) -> None:
    q = WorkQueue(Path(root), SHARDS[:1], worker_id=name, slurm_job_id=name, alive_fn=lambda job: job != "dead")
    Path(out).write_text(json.dumps(q.claim_next()))


def test_concurrent_reclaimers_never_both_win(tmp_path):
    for trial in range(5):
        root = tmp_path / f"q{trial}"
        dead = WorkQueue(root, SHARDS[:1], worker_id="dead", slurm_job_id="dead", alive_fn=lambda _: True)
        dead.claim_next()
        dead._stop_heartbeat()
        ctx = mp.get_context("fork")
        procs = [ctx.Process(target=_reclaimer, args=(str(root), f"r{i}", str(root / f"r{i}.json"))) for i in range(4)]
        for proc in procs:
            proc.start()
        for proc in procs:
            proc.join(timeout=60)
        winners = [i for i in range(4) if json.loads((root / f"r{i}.json").read_text()) == "shard_0000"]
        assert len(winners) <= 1
