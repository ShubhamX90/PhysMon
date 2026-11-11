"""Tests for the Stage 15 generic-worker dispatcher with stub runs: priority order, GPU compatibility, one attempt per entry
per job, open-shard counting, and that each entry runs its own snapshot with its own commit and spec hash."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("s174", REPO_ROOT / "scripts/v2/s174_dispatch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s174 = _load()

STUB = """import json, os, sys
from pathlib import Path
args = sys.argv[1:]
run_id = args[args.index('--run-id') + 1]
queue = Path(os.environ['STUB_QUEUE']) / run_id
(queue / 'done').mkdir(parents=True, exist_ok=True)
for shard in json.loads(os.environ['STUB_SHARDS_' + run_id]):
    (queue / 'done' / (shard + '.json')).write_text('{}')
log = Path(os.environ['STUB_LOG'])
with log.open('a') as h:
    h.write(json.dumps({'run_id': run_id, 'commit': os.environ['PHYSMON_SOURCE_COMMIT'],
                        'spec': args[args.index('--expect-spec-sha256') + 1], 'cwd': os.getcwd()}) + '\\n')
sys.exit(int(os.environ.get('STUB_EXIT_' + run_id, '0')))
"""


def make_entry(tmp_path: Path, run_id: str, priority: int, **extra):
    snap = tmp_path / f"snap_{run_id}"
    (snap / "scripts/v2").mkdir(parents=True)
    (snap / "scripts/v2/s170_sampled_run.py").write_text(STUB)
    return {"run_id": run_id, "commit": f"commit_{run_id}", "snapshot": str(snap), "spec_sha256": f"sha_{run_id}",
            "env_prefix": str(Path(sys.executable).parent.parent), "shards": ["shard_0000", "shard_0001"], "priority": priority,
            "registered_at": f"2026-11-12T00:00:0{priority % 10}", "active": True, "min_gpu_memory_gb": 70,
            "exclude_gpu_substrings": ["V100"], **extra}


def test_dispatcher_runs_compatible_entries_in_priority_order_each_once(tmp_path, monkeypatch):
    entries = [make_entry(tmp_path, "late", 50), make_entry(tmp_path, "first", 10),
               make_entry(tmp_path, "needs_more_memory", 5, min_gpu_memory_gb=140),
               make_entry(tmp_path, "inactive", 1, active=False), make_entry(tmp_path, "fails", 20)]
    active = tmp_path / "ACTIVE_RUNS.json"
    active.write_text(json.dumps({"entries": entries}))
    log = tmp_path / "log.jsonl"
    monkeypatch.setenv("STUB_QUEUE", str(tmp_path / "queue"))
    monkeypatch.setenv("STUB_LOG", str(log))
    for e in entries:
        monkeypatch.setenv(f"STUB_SHARDS_{e['run_id']}", json.dumps(e["shards"]))
    monkeypatch.setenv("STUB_EXIT_fails", "11")
    monkeypatch.setattr(s174, "gpu_info", lambda: {"name": "NVIDIA H100 80GB HBM3", "memory_gb": 79.6, "driver_major": 580})
    code = s174.main(["--active", str(active), "--queue-root", str(tmp_path / "queue"), "--time-budget-s", "100000",
                      "--authorization-ref", "test"])
    ran = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["run_id"] for r in ran] == ["first", "fails", "late"]
    assert ran[0]["commit"] == "commit_first" and ran[0]["spec"] == "sha_first" and ran[0]["cwd"].endswith("snap_first")
    assert code == 1  # one entry failed; it was not retried


def test_open_shards_and_compatibility(tmp_path):
    entry = make_entry(tmp_path, "r", 1)
    assert s174.open_shards(entry, tmp_path / "queue") == 2
    (tmp_path / "queue" / "r" / "done").mkdir(parents=True)
    (tmp_path / "queue" / "r" / "done" / "shard_0000.json").write_text("{}")
    (tmp_path / "queue" / "r" / "claims" / "shard_0001").mkdir(parents=True)
    assert s174.open_shards(entry, tmp_path / "queue") == 1  # a claimed shard still counts; the run's worker judges the claim
    assert not s174.compatible(entry, {"name": "Tesla V100-PCIE-32GB", "memory_gb": 32, "driver_major": 580})
    assert s174.compatible(entry, {"name": "NVIDIA A100-SXM4-80GB", "memory_gb": 79.2, "driver_major": 580})
    cu13 = dict(entry, min_driver_major=580)
    assert not s174.compatible(cu13, {"name": "NVIDIA A100-SXM4-80GB", "memory_gb": 79.2, "driver_major": 550})


def test_unreadable_gpu_or_run_list_exit_nonzero(tmp_path, monkeypatch):
    monkeypatch.setattr(s174, "gpu_info", lambda: None)
    assert s174.main(["--active", str(tmp_path / "x.json"), "--time-budget-s", "100000", "--authorization-ref", "t"]) == 2
    monkeypatch.setattr(s174, "gpu_info", lambda: {"name": "H100", "memory_gb": 80, "driver_major": 580})
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert s174.main(["--active", str(bad), "--time-budget-s", "100000", "--authorization-ref", "t"]) == 3
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"entries": [{"run_id": "only_an_id"}]}))
    assert s174.load_entries(partial) == []


def test_nothing_registered_exits_cleanly(tmp_path, monkeypatch):
    monkeypatch.setattr(s174, "gpu_info", lambda: {"name": "x", "memory_gb": 80, "driver_major": 580})
    assert s174.main(["--active", str(tmp_path / "none.json"), "--time-budget-s", "100000", "--authorization-ref", "t"]) == 0
