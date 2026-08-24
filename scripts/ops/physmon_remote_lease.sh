#!/usr/bin/env bash
# Coordinate deployment to the shared Sharanga repository. Run this on Sharanga.
set -euo pipefail

usage() {
  printf '%s\n' "usage: $0 {acquire|inspect|release} [--task TASK] [--commit SHA] [--token TOKEN]"
}

command_name=${1:-}
shift || true
task=""
commit=""
token=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --task) task=${2:?missing task}; shift 2 ;;
    --commit) commit=${2:?missing commit}; shift 2 ;;
    --token) token=${2:?missing token}; shift 2 ;;
    *) usage >&2; exit 64 ;;
  esac
done

case "$task$commit$token" in
  *$'\n'*|*$'\r'*) printf '%s\n' "arguments must be single-line" >&2; exit 64 ;;
esac

repo_root=${PHYSMON_ROOT:-"$HOME/PhysMons"}
state_root="$repo_root/.physmon_ops"
lock_dir="$state_root/deployment.lock"
owner_file="$lock_dir/owner.env"

show_owner() {
  if [ -f "$owner_file" ]; then
    cat "$owner_file"
  else
    printf '%s\n' "lease metadata missing"
  fi
}

case "$command_name" in
  acquire)
    [ -n "$task" ] || { printf '%s\n' "--task is required" >&2; exit 64; }
    [ -n "$commit" ] || { printf '%s\n' "--commit is required" >&2; exit 64; }
    mkdir -p "$state_root"
    if ! mkdir "$lock_dir" 2>/dev/null; then
      printf '%s\n' "deployment lease already held:" >&2
      show_owner >&2
      exit 3
    fi
    token="$(date -u +%Y%m%dT%H%M%SZ)-$(hostname)-$$"
    umask 077
    printf 'task=%s\ncommit=%s\nowner=%s\nhost=%s\ncreated_at=%s\ntoken=%s\n' \
      "$task" "$commit" "$(id -un)" "$(hostname)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$token" > "$owner_file"
    printf 'lease acquired\ntoken=%s\n' "$token"
    ;;
  inspect)
    if [ -d "$lock_dir" ]; then
      printf '%s\n' "deployment lease held:"
      show_owner
    else
      printf '%s\n' "deployment lease available"
    fi
    ;;
  release)
    [ -n "$token" ] || { printf '%s\n' "--token is required" >&2; exit 64; }
    [ -f "$owner_file" ] || { printf '%s\n' "no releasable deployment lease" >&2; exit 4; }
    recorded_token=$(sed -n 's/^token=//p' "$owner_file")
    [ "$token" = "$recorded_token" ] || { printf '%s\n' "lease token does not match" >&2; exit 5; }
    rm "$owner_file"
    rmdir "$lock_dir"
    printf '%s\n' "deployment lease released"
    ;;
  *) usage >&2; exit 64 ;;
esac
