# Sharanga deployment targets. These defaults are intentionally overridable for
# teammates whose SSH alias differs from the project default.
.PHONY: sync-up sync-down sync-check sync-plan-up sync-plan-down sync-plan-prune remote-preflight

SHARANGA_HOST ?= sharanga
SHARANGA_REPO ?= ~/PhysMons

PYTHON := $(shell if [ -x ./.venv/bin/python ]; then echo ./.venv/bin/python; else echo python3; fi)
PYTEST := $(shell if [ -x ./.venv/bin/pytest ]; then echo ./.venv/bin/pytest; else echo pytest; fi)
RUFF := $(shell if [ -x ./.venv/bin/ruff ]; then echo ./.venv/bin/ruff; else echo ruff; fi)

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

## Read-only local/remote commit, worktree, queue, and scratch preflight.
remote-preflight:
	$(PYTHON) scripts/ops/remote_preflight.py --host "$(SHARANGA_HOST)"

## Non-destructive local -> Sharanga plan. Inspect this before sync-up.
sync-plan-up:
	rsync -avzn --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  ./ $(SHARANGA_HOST):$(SHARANGA_REPO)/

## Push local -> Sharanga without deleting remote-only artifacts.
## Run remote-preflight and sync-plan-up first; this is deployment, not a merge.
sync-up:
	rsync -avz --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  ./ $(SHARANGA_HOST):$(SHARANGA_REPO)/
	commit=$$(git rev-parse HEAD); \
	ssh $(SHARANGA_HOST) "mkdir -p $(SHARANGA_REPO)/.physmon_ops && printf '%s\\n' $$commit > $(SHARANGA_REPO)/.physmon_ops/deployment_commit"

## Non-destructive Sharanga -> local plan. Ensure the local tree can accept all changes.
sync-plan-down:
	rsync -avzn --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  $(SHARANGA_HOST):$(SHARANGA_REPO)/ ./

## Pull Sharanga -> local without deleting local-only files.
sync-down:
	rsync -avz --itemize-changes \
	  $(RSYNC_EXCLUDES) \
	  $(SHARANGA_HOST):$(SHARANGA_REPO)/ ./

## Backward-compatible alias for the safe local -> remote dry-run.
sync-check: sync-plan-up

## Show what a destructive local -> remote prune would remove. This never deletes.
sync-plan-prune:
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
