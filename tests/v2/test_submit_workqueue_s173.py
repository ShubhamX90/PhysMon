"""Tests for the Stage 15 submit helper with the scheduler mocked: walltime arithmetic, the sbatch command, and the rule that
only PENDING non-PhysMon jobs are cancelled, after their details are saved. Nothing is submitted or cancelled."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("s173", REPO_ROOT / "scripts/v2/s173_submit_workqueue.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s173 = _load()


def test_walltime_seconds():
    assert s173.seconds("12:00:00") == 43200
    assert s173.seconds("1-00:00:00") == 86400
    assert s173.seconds("4-02:30:00") == 4 * 86400 + 2 * 3600 + 1800
    assert s173.seconds("30:00") == 1800


def test_sbatch_command_caps_walltime_at_the_partition_limit_and_sets_the_budget(tmp_path):
    common = {"walltime_req": "2-00:00:00", "margin_s": 1800, "cpus": 6, "mem": "120G", "job_name": "physmon_s15_worker",
              "exports": {"DISPATCH_SNAPSHOT": "/snap", "AUTHORIZATION_REF": "auth"}, "template": tmp_path / "t.sh"}
    cmd = s173.sbatch_command(s173.PARTITIONS["h200"], **common, test_only=True)
    assert cmd[0] == "sbatch" and cmd[1] == "--test-only" and "--partition=gpu_h200_8" in cmd
    assert "--time=1-00:00:00" in cmd  # capped at the H200 limit
    assert "--export=ALL" in cmd and common["exports"]["TIME_BUDGET_S"] == "84600"  # variables travel in the environment
    real = s173.sbatch_command(s173.PARTITIONS["h100"], **common, test_only=False)
    assert "--test-only" not in real and "--time=2-00:00:00" in real and "--gres=gpu:nvidia_h100_80gb_hbm3:1" in real
    assert set(s173.PARTITIONS) == {"h100", "h200", "a100"}


def test_register_writes_one_entry_and_refuses_a_duplicate(tmp_path, monkeypatch):
    run_dir = tmp_path / "repo" / "data/v2/runs/r1"
    run_dir.mkdir(parents=True)
    env = tmp_path / "env"
    (env / "bin").mkdir(parents=True)
    (env / "bin" / "python").write_text("")
    (run_dir / "spec.json").write_text(json.dumps({"env_prefix": str(env), "shards": {"shard_0001": "x", "shard_0000": "y"},
                                                   "backend": "hf", "model_key": "qwen_primary", "purpose": "t"}))
    monkeypatch.setattr(s173, "REPO_ROOT", tmp_path / "repo")
    monkeypatch.setattr(s173, "SUBMISSIONS", tmp_path / "subs.jsonl")
    monkeypatch.setattr(s173, "check_repo", lambda run_id: ("c0ffee", "s" * 64))
    monkeypatch.setattr(s173, "make_snapshot", lambda head: tmp_path / "snap" / head)
    real_run = s173.subprocess.run

    def fake_subprocess_run(cmd, *a, **k):
        if "status" in cmd:  # the import probe of the run's environment
            return s173.subprocess.CompletedProcess(cmd, 0, "{}", "")
        if "work" in cmd and "--check-only" in cmd:  # the worker pre-flight
            return s173.subprocess.CompletedProcess(cmd, 0, '{"event": "self_test", "code": 0}', "")
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(s173.subprocess, "run", fake_subprocess_run)
    active = tmp_path / "queue" / "ACTIVE_RUNS.json"
    assert s173.main(["register", "--run-id", "r1", "--priority", "10", "--active", str(active)]) == 0
    data = json.loads(active.read_text())
    entry = data["entries"][0]
    assert entry["shards"] == ["shard_0000", "shard_0001"] and entry["commit"] == "c0ffee" and entry["priority"] == 10
    assert "RTX PRO 6000" in entry["exclude_gpu_substrings"] and "V100" in entry["exclude_gpu_substrings"]
    assert entry["min_driver_major"] == 0  # HF backend; vLLM entries default to 580
    try:
        s173.main(["register", "--run-id", "r1", "--active", str(active)])
        raise AssertionError("duplicate registration must be refused")
    except SystemExit:
        pass
    try:
        s173.main(["register", "--run-id", "r1", "--replace", "--active", str(active)])
        raise AssertionError("replacing an active entry must be refused")
    except SystemExit:
        pass
    assert s173.main(["deactivate", "--run-id", "r1", "--active", str(active)]) == 0
    assert json.loads(active.read_text())["entries"][0]["active"] is False
    try:
        s173.main(["register", "--run-id", "r1", "--replace", "--requires", "nope", "--active", str(active)])
        raise AssertionError("an unregistered canary must be refused")
    except SystemExit:
        pass
    monkeypatch.setattr(s173, "check_repo", lambda run_id: ("beef", "s" * 64))
    assert s173.main(["register", "--run-id", "r1", "--replace", "--active", str(active)]) == 0
    entries = json.loads(active.read_text())["entries"]
    assert len(entries) == 1 and entries[0]["commit"] == "beef" and entries[0]["replaces"][0]["commit"] == "c0ffee"
    (active.parent / "r1" / "done").mkdir(parents=True)
    (active.parent / "r1" / "done" / "shard_0000.json").write_text("{}")
    s173.main(["deactivate", "--run-id", "r1", "--active", str(active)])
    try:
        s173.main(["register", "--run-id", "r1", "--replace", "--active", str(active)])
        raise AssertionError("a run with records must never be re-pointed at another commit")
    except SystemExit:
        pass


def test_only_pending_non_physmon_jobs_are_cancelled_after_saving(tmp_path, monkeypatch):
    monkeypatch.setattr(s173, "CANCELLED_DIR", tmp_path / "cancelled")
    monkeypatch.setattr(s173, "CANCELLED_LOG", tmp_path / "cancelled" / "cancelled.jsonl")
    queue = "1|g4a|PENDING|gpu_a100_8|JobHeldUser|0:00\n2|ap_w_h200c|RUNNING|gpu_h200_8|None|7:54\n" \
            "3|physmon_s15_x|PENDING|gpu_h100_4|Priority|0:00\n4|ap_w_a100|PENDING|gpu_a100_8|Priority|0:00\n" \
            "5|g2_m111|PENDING|compute|Priority|0:00\n"
    calls: list[list[str]] = []

    def fake_run(cmd, *, check=True, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["squeue", "-h"] and "-u" in cmd:
            return subprocess.CompletedProcess(cmd, 0, queue, "")
        if cmd[:2] == ["squeue", "-h"] and "-j" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "PENDING\n" if cmd[3] == "1" else "RUNNING\n", "")
        if cmd[:3] == ["scontrol", "write", "batch_script"]:
            Path(cmd[4]).write_text("#!/bin/bash\n")
        return subprocess.CompletedProcess(cmd, 0, "details", "")

    monkeypatch.setattr(s173, "run", fake_run)
    done = s173.cancel_foreign_pending(dry_run=False, partitions={"gpu_a100_8", "gpu_h100_4", "gpu_h200_8"})
    assert [d["job_id"] for d in done] == ["1", "4"]  # never RUNNING job 2, PhysMon job 3, or CPU job 5 on another partition
    scancels = [c for c in calls if c[0] == "scancel"]
    assert scancels == [["scancel", "--state=PENDING", "1"]]  # job 4 started between listing and cancelling: skipped
    log = [json.loads(line) for line in (tmp_path / "cancelled" / "cancelled.jsonl").read_text().splitlines()]
    assert log[0]["batch_script_saved"] and log[1]["skipped"].startswith("state is now")
    assert (tmp_path / "cancelled" / "1_g4a" / "show_job.txt").read_text() == "details"


def test_dry_run_cancels_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(s173, "CANCELLED_DIR", tmp_path / "c")
    monkeypatch.setattr(s173, "CANCELLED_LOG", tmp_path / "c" / "log.jsonl")
    calls = []

    def fake_run(cmd, *, check=True, cwd=None):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "1|g4a|PENDING|gpu_a100_8|JobHeldUser|0:00\n", "")

    monkeypatch.setattr(s173, "run", fake_run)
    assert [d["job_id"] for d in s173.cancel_foreign_pending(dry_run=True, partitions={"gpu_a100_8"})] == ["1"]
    assert s173.cancel_foreign_pending(dry_run=True, partitions={"gpu_h100_4"}) == []
    assert not any(c[0] in ("scancel", "scontrol") for c in calls) and not (tmp_path / "c").exists()


if __name__ == "__main__":
    sys.exit(0)


def test_snapshot_of_the_real_repository_extracts_without_links_and_is_read_only(tmp_path, monkeypatch):
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip()
    monkeypatch.setattr(s173, "SNAPSHOT_ROOT", tmp_path / "snapshots")
    snap = s173.make_snapshot(head)
    assert (snap / ".physmon_git_commit").read_text().strip() == head
    assert (snap / "src/physmon/benchmark/v2/graph.py").exists() and (snap / "docs/model_registry.yml").exists()
    assert not any(p.is_symlink() for p in snap.rglob("*"))
    assert not (snap / "src/physmon/benchmark/v2/graph.py").stat().st_mode & 0o222
    assert s173.make_snapshot(head) == snap  # idempotent
    assert not list((tmp_path / "snapshots").glob(".*tmp*"))


def test_the_helpers_own_registers_do_not_block_the_clean_tree_check(monkeypatch):
    status = " M docs/registry/v2/stage15_submissions.jsonl\n?? scratch.txt\n"
    monkeypatch.setattr(s173, "git", lambda *a: status if a[0] == "status" else "abc" if a[0] == "rev-parse" else "origin/main")
    monkeypatch.setattr(s173, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, "", ""))
    assert s173.check_clean_pushed() == "abc"
    status = " M scripts/v2/s170_sampled_run.py\n"
    try:
        s173.check_clean_pushed()
        raise AssertionError("a modified job input must be refused")
    except SystemExit:
        pass
