#!/usr/bin/env python3
"""Read-only deployment preflight for the shared PhysMon Sharanga worktree."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


ALLOWED_REMOTE_UNTRACKED = {"?? activations"}


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def run(command: list[str], *, cwd: Path | None = None, input_text: str | None = None) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(command, completed.returncode, completed.stdout, completed.stderr)


def git_output(root: Path, *arguments: str) -> str:
    result = run(["git", *arguments], cwd=root)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def remote_probe(host: str, remote_repo: str) -> CommandResult:
    remote_repo_expression = "$HOME/PhysMons" if remote_repo == "~/PhysMons" else shlex.quote(remote_repo)
    script = """set -u
repo=$1
printf 'REMOTE_HEAD='; git -C "$repo" rev-parse HEAD
printf 'REMOTE_MARKER_SOURCE='; if [ -f "$repo/.physmon_ops/deployment_commit" ]; then printf 'deployment_commit'; elif [ -f "$repo/.physmon_git_commit" ]; then printf 'legacy_tracked_marker'; else printf 'MISSING'; fi; printf '\\n'
printf 'REMOTE_MARKER='; if [ -f "$repo/.physmon_ops/deployment_commit" ]; then cat "$repo/.physmon_ops/deployment_commit"; elif [ -f "$repo/.physmon_git_commit" ]; then cat "$repo/.physmon_git_commit"; else printf 'MISSING'; fi; printf '\\n'
printf 'REMOTE_STATUS_BEGIN\\n'; git -C "$repo" status --porcelain=v1; printf 'REMOTE_STATUS_END\\n'
printf 'QUEUE_BEGIN\\n'; squeue -u "$(id -un)" -h -o '%i|%T|%P|%j|%M|%l|%R'; printf 'QUEUE_END\\n'
printf 'SCRATCH_BEGIN\\n'; df -h "${SCRATCH:-/scratch/$(id -un)}" | tail -n 1; printf 'SCRATCH_END\\n'
"""
    return run(["ssh", host, f"sh -s -- {remote_repo_expression}"], input_text=script)


def block(text: str, name: str) -> str:
    match = re.search(rf"{name}_BEGIN\n(.*?){name}_END", text, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def line(text: str, name: str) -> str | None:
    match = re.search(rf"^{name}=(.*)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="sharanga")
    parser.add_argument("--remote-repo", default="~/PhysMons")
    parser.add_argument("--allow-remote-untracked", action="append", default=[])
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--expect-aligned",
        action="store_true",
        help="Require the remote commit marker and Git commit to match the local commit. Use after sync-up.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when the selected preflight checks fail.",
    )
    args = parser.parse_args()

    root = Path(git_output(Path.cwd(), "rev-parse", "--show-toplevel"))
    local_commit = git_output(root, "rev-parse", "HEAD")
    local_status = git_output(root, "status", "--porcelain=v1").splitlines()
    upstream_result = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd=root)
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    divergence = git_output(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}").split() if upstream else None
    remote = remote_probe(args.host, args.remote_repo)
    if remote.returncode:
        raise RuntimeError(remote.stderr.strip() or "remote preflight failed")

    allowed = ALLOWED_REMOTE_UNTRACKED | set(args.allow_remote_untracked)
    remote_status = block(remote.stdout, "REMOTE_STATUS").splitlines()
    remote_unexpected = [entry for entry in remote_status if entry not in allowed]
    remote_head = line(remote.stdout, "REMOTE_HEAD")
    remote_marker = line(remote.stdout, "REMOTE_MARKER")
    remote_marker_source = line(remote.stdout, "REMOTE_MARKER_SOURCE")
    checks = {
        "local_worktree_clean": not local_status,
        "local_branch_has_upstream": upstream is not None,
        "local_branch_matches_upstream": divergence == ["0", "0"] if divergence else False,
        "remote_worktree_has_no_unexpected_changes": not remote_unexpected,
    }
    alignment_checks = {
        "remote_commit_matches_local": remote_head == local_commit,
        "remote_marker_matches_local": remote_marker is not None and local_commit.startswith(remote_marker),
    }
    if args.expect_aligned:
        checks.update(alignment_checks)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "repository_root": str(root),
        "host": args.host,
        "remote_repo": args.remote_repo,
        "local": {
            "commit": local_commit,
            "status": local_status,
            "upstream": upstream,
            "ahead_behind_upstream": (
                {"ahead": int(divergence[0]), "behind": int(divergence[1])} if divergence else None
            ),
        },
        "remote": {
            "commit": remote_head,
            "commit_marker": remote_marker,
            "commit_marker_source": remote_marker_source,
            "status": remote_status,
            "queue": block(remote.stdout, "QUEUE").splitlines(),
            "scratch": block(remote.stdout, "SCRATCH"),
        },
        "checks": checks,
        "alignment_checks": alignment_checks,
        "allowed_remote_untracked": sorted(allowed),
        "unexpected_remote_status": remote_unexpected,
        "remote_command": asdict(remote),
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if not args.strict or all(checks.values()) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"remote preflight error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
