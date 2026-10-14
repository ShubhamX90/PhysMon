# RETIRED laptop-mirror workflow. Work now happens directly on Sharanga in
# ~/PhysMons with GitHub as the shared record, so the sync-* and remote-preflight
# targets below are kept for reference only. They refuse to run unless
# PHYSMON_ALLOW_SYNC=1 is set, which should only happen when the user explicitly
# asks to sync a workstation copy. Overridable defaults follow.
.PHONY: sync-up sync-down sync-check sync-plan-up sync-plan-down sync-plan-prune remote-preflight retired-sync-guard

SHARANGA_HOST ?= sharanga
SHARANGA_REPO ?= ~/PhysMons

# Tool resolution: ./.venv, then the canonical `physmon` conda env, then PATH.
# This keeps `make lint`, `make test`, and the pre-commit hook working in
# non-interactive shells where the env is not activated. Override the env
# location with PHYSMON_ENV=/path/to/env.
PHYSMON_ENV ?= $(HOME)/.conda/envs/physmon
# The shared account's ~/.local user site holds packages from other projects
# (for example a newer huggingface-hub) that shadow the env and break
# `import transformers`. Ignore the user site for every make target.
export PYTHONNOUSERSITE := 1
find_tool = $(shell for d in ./.venv/bin $(PHYSMON_ENV)/bin; do if [ -x "$$d/$(1)" ]; then echo "$$d/$(1)"; exit 0; fi; done; echo $(1))

PYTHON := $(call find_tool,python3)
PYTEST := $(call find_tool,pytest)
RUFF := $(call find_tool,ruff)

RSYNC_EXCLUDES := \
	  --exclude='activations' \
	  --exclude='activations/' \
	  --exclude='.physmon_ops' \
	  --exclude='.physmon_ops/' \
	  --exclude='.venv/' \
	  --exclude='.pytest_cache/' \
	  --exclude='.ruff_cache/' \
	  --exclude='__pycache__/' \
	  --exclude='*.pyc' \
	  --exclude='*.egg-info/' \
	  --exclude='*.pt' \
	  --exclude='*.bin' \
	  --exclude='*.safetensors' \
	  --exclude='slurm/submitted' \
	  --exclude='slurm/submitted/' \
	  --exclude='data/generated' \
	  --exclude='data/generated/' \
	  --exclude='.git/'

retired-sync-guard:
	@if [ "$(PHYSMON_ALLOW_SYNC)" != "1" ]; then \
	  echo "ERROR: this target belongs to the retired laptop-mirror workflow." >&2; \
	  echo "Work directly in ~/PhysMons and use git. Set PHYSMON_ALLOW_SYNC=1 only if the user explicitly asks to sync a workstation copy." >&2; \
	  exit 1; \
	fi

## Read-only local/remote commit, worktree, queue, and scratch preflight.
remote-preflight: retired-sync-guard
	$(PYTHON) scripts/ops/remote_preflight.py --host "$(SHARANGA_HOST)"

## Non-destructive local -> Sharanga plan. Inspect this before sync-up.
sync-plan-up: retired-sync-guard
	rsync -avzn --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  ./ $(SHARANGA_HOST):$(SHARANGA_REPO)/

## Push local -> Sharanga without deleting remote-only artifacts.
## Run remote-preflight and sync-plan-up first; this is deployment, not a merge.
sync-up: retired-sync-guard
	rsync -avz --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  ./ $(SHARANGA_HOST):$(SHARANGA_REPO)/
	commit=$$(git rev-parse HEAD); \
	ssh $(SHARANGA_HOST) "mkdir -p $(SHARANGA_REPO)/.physmon_ops && printf '%s\\n' $$commit > $(SHARANGA_REPO)/.physmon_ops/deployment_commit"

## Non-destructive Sharanga -> local plan. Ensure the local tree can accept all changes.
sync-plan-down: retired-sync-guard
	rsync -avzn --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  $(SHARANGA_HOST):$(SHARANGA_REPO)/ ./

## Pull Sharanga -> local without deleting local-only files.
sync-down: retired-sync-guard
	rsync -avz --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  $(SHARANGA_HOST):$(SHARANGA_REPO)/ ./

## Backward-compatible alias for the safe local -> remote dry-run.
sync-check: sync-plan-up

## Show what a destructive local -> remote prune would remove. This never deletes.
sync-plan-prune: retired-sync-guard
	rsync -avzn --delete --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  ./ $(SHARANGA_HOST):$(SHARANGA_REPO)/

# Development targets
.PHONY: test lint install install-hooks

test:
	$(PYTEST) tests/ -v

lint:
	$(RUFF) check src/ scripts/ tests/
	PYTHONPATH=src $(PYTHON) scripts/check_forbidden_phrases.py

install:
	$(PYTHON) -m pip install -e ".[dev]"

install-hooks:
	git config core.hooksPath .githooks
