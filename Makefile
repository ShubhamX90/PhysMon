# Sync targets
.PHONY: sync-up sync-down sync-check

## Push local -> Sharanga (run before every job submission)
sync-up:
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
.PHONY: test lint install

test:
	pytest tests/ -v

lint:
	ruff check src/ scripts/ tests/

install:
	pip install -e ".[dev]"
