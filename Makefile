# Sync targets
.PHONY: sync-up sync-down sync-check

PYTHON := $(shell if [ -x ./.venv/bin/python ]; then echo ./.venv/bin/python; else echo python3; fi)
PYTEST := $(shell if [ -x ./.venv/bin/pytest ]; then echo ./.venv/bin/pytest; else echo pytest; fi)
RUFF := $(shell if [ -x ./.venv/bin/ruff ]; then echo ./.venv/bin/ruff; else echo ruff; fi)

## Push local -> Sharanga (run before every job submission)
sync-up:
	git rev-parse --short HEAD > .physmon_git_commit
	rsync -avz --delete \
	  --exclude='activations' \
	  --exclude='activations/' \
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
	  --exclude='.git/' \
	  ./ sharanga:~/PhysMons/

## Pull Sharanga -> local (run after jobs complete to retrieve results)
sync-down:
	rsync -avz \
	  --exclude='activations' \
	  --exclude='activations/' \
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
	  --exclude='.git/' \
	  sharanga:~/PhysMons/ ./

## Dry-run to check what would sync
sync-check:
	rsync -avzn --delete \
	  --exclude='activations' \
	  --exclude='activations/' \
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
	  --exclude='.git/' \
	  sharanga:~/PhysMons/ ./

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
