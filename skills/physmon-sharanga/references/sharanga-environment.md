# Sharanga Environment and Runtime Reference

This reference combines a read-only audit on 2026-08-24 with PhysMon's
repository configuration. It is operational context, not a lasting cluster
contract. Before every resource-changing action, obtain live scheduler and
account data as shown below.

## Account, repository, and storage map

| Item | Observed / configured value | Operational rule |
|---|---|---|
| SSH alias | `sharanga` | Use the local alias, not a hard-coded host name. |
| Observed login host | `hpc01.sharanga.local` | Informational only; it can change. |
| Shared Unix account | `pabitra` | Treat it as a shared operational identity. |
| Slurm account | `bits` | Let existing templates/configuration select it; re-check association. |
| Remote checkout | `~/PhysMons` | Deployed source snapshot, not a shared editor. |
| Scratch home | `/scratch/pabitra` | Large non-Git data. |
| PhysMon scratch root | `/scratch/pabitra/physmon` | Logs, caches, activations, checkpoints. |
| Model-store link | `/scratch/pabitra/physmon/models` | Symlink observed to `/scratch/pabitra/rag-reason/models`. |
| Conda environment | `physmon` | Activated by templates after conda shell setup. |

Current remote `origin` was the PhysMon GitHub repository. The remote clone had
an untracked `activations` path at audit time. This does not authorize cleanup:
read it as a pre-existing operational condition until its owner and target are
known.

## Scratch layout and ownership

| Relative path | Expected material | Rules |
|---|---|---|
| `activations/` | legacy activation products | scratch-only; do not delete or sync |
| `activations_stage6/` | Stage 6 activations | preserve, read only unless task owns an attempt |
| `activations_stage11_expansion/` | expansion activations | scratch-only |
| `activations_stage11_variable_renaming/` | derived-set activations | scratch-only |
| `checkpoints/` | resumable job state | task/attempt scoped; never reuse another run's path |
| `hf_cache/` | Hugging Face artifacts | shared cache; no purge/redownload without approval |
| `models/` | model-store link | never delete, rename, or assume every model is approved |
| `slurm_logs/` | batch stdout/stderr | durable provenance, keyed by job ID |
| `stage11_expansion_flat/` | run-local flat inputs | not canonical benchmark source data |

The audit saw roughly 279 TB total `/scratch`, 119 TB used, and 161 TB free.
This is a point-in-time observation. Check both capacity and the target tree:

```bash
ssh sharanga 'df -h /scratch/pabitra'
ssh sharanga 'du -sh /scratch/pabitra/physmon/* 2>/dev/null | sort -h'
ssh sharanga 'find /scratch/pabitra/physmon/checkpoints -maxdepth 2 -type d -print | sort'
```

Do not store a new artifact under an ambiguous existing directory. Create an
attempt-specific path, record it before submission, and retain it after an
error.

## Live resource discovery

The scheduler used Slurm 25.05.3 in the audit. It had accounting enabled,
backfill scheduling, multifactor priority with age/fairshare, cgroup job
accounting, cgroup task enforcement, and a maximum array size of 1001. This is
why queue time must be diagnosed from Slurm's live reason rather than guessed
from hardware names or QoS labels.

```bash
ssh sharanga 'scontrol --version; scontrol show config | egrep "ClusterName|SchedulerType|PriorityType|PreemptType|MaxArraySize"'
ssh sharanga 'sinfo -h -o "%P|%a|%l|%D|%G"'
ssh sharanga 'sinfo -N -h -o "%N|%P|%T|%c|%m|%G"'
ssh sharanga 'squeue -u pabitra -o "%i|%T|%P|%j|%M|%l|%R"'
ssh sharanga 'sacctmgr -n -P show assoc user=pabitra format=User,Account,Partition,QOS,MaxJobs,MaxSubmit,MaxTRESPerJob'
ssh sharanga 'sacctmgr -n -P show qos format=Name,MaxWall,MaxTRESPerUser,MaxTRESPerJob,MaxJobsPU,MaxSubmitPU,MaxTRESPU,GrpTRES'
ssh sharanga 'sshare -u pabitra -l'
```

`sinfo` reports partition capacity. `sacctmgr show assoc` reports what the
shared account can request. `squeue` and `scontrol show job` explain what is
currently schedulable. All four matter.

## Hardware snapshot

| Partition | Nodes observed | Accelerator / CPU platform | Node capacity snapshot | Partition max time |
|---|---|---|---|---|
| `gpu_a100_8` | `gpunode4` | 8 x A100 SXM4 80GB; AMD EPYC 7532 Rome | 64 CPU, about 1 TB | 5 days |
| `gpu_h100_4` | `gpunode5-6` | 4 x H100 80GB HBM3; AMD EPYC 9354 Genoa | 64 CPU, about 1 TB | 3 days |
| `gpu_h200_8` | `gpunode7` | 8 x H200 NVL; AMD EPYC 9355 Turin | 64 CPU, about 1 TB | 1 day |
| `gpu_rtx_pro_6000_6_csis_hyd` | `gpunode8` | 6 x RTX Pro 6000; AMD EPYC 9355 Turin | 64 CPU, about 1 TB | 2 days |
| `gpu_v100_2` | `gpunode2-3` | 2 x Tesla V100 PCIe 32GB | 64 CPU, 256GB | 3 days |
| `compute` | `node1-22` | CPU only | 64 CPU, 256GB | partition said infinite; QoS can be shorter |
| `big_compute` | `node23-31`, `node33-42` | CPU only | 192 CPU, 385GB | 5 days |
| `big_compute_amd_9655` | `node43-47` | CPU only | 192 CPU, 385GB | 5 days |

The historical `docs/cluster_inventory.md` is valuable for validated model
loads and prior failures, but it is dated. Its H100 walltime observation, for
example, differed from this live audit. Prefer live Slurm facts.

## Shared-account limits observed

These are association/QoS snapshot values, not requests to copy blindly.

| Resource | Account-facing limit that governed PhysMon use | Consequence |
|---|---|---|
| `compute` / `cpulimit` | 1024 CPU, 5 nodes, 7 jobs per user, QoS `MaxWall=4 days` | use for CPU analysis; check memory/node request separately |
| `big_compute` | 5 nodes per job, 8 jobs per user | reserve for justified high-CPU/high-memory work |
| `big_compute_amd_9655` | 2 nodes per job, 2 jobs per user | limited shared resource |
| `gpu_a100_8` | 2 GPU per user; 16 CPU, 400G per job; 2 jobs per user | at most two typical one-GPU jobs, subject to queue |
| `gpu_h100_4` | 2 generic GPU / 1 named H100; 12 CPU, 300G; 3 jobs per user | two 8-CPU one-GPU jobs exceed CPU allowance |
| `gpu_h200_8` | 3 GPU, 8 CPU, 300G; 2 jobs per user | GPU count alone can be misleading; 1-day walltime |
| `gpu_v100_2` | generic GPU group limit 4 | legacy path; verify runtime support first |

The audit also saw `gpu_v100_1` requiring a special QoS and no explicit
project association for it. Do not presume it is usable. The RTX partition had
no PhysMon model-backend validation at audit time. Neither is a default
fallback.

## Runtime and software environment

Existing current generic templates initialize the environment this way:

```bash
set -eo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate physmon
export SCRATCH=/scratch/pabitra
export PHYSMON_ROOT="$HOME/PhysMons"
export PYTHONPATH="$PHYSMON_ROOT/src:${PYTHONPATH:-}"
export HF_HOME="$SCRATCH/physmon/hf_cache"
export TRANSFORMERS_CACHE="$SCRATCH/physmon/hf_cache"
cd "$PHYSMON_ROOT"
```

An interactive audit loaded no environment modules. The observed environment
had Python 3.11.15, Torch 2.7.1, PyTorch CUDA 12.1, TransformerLens 3.4,
Transformers 5.11, Accelerate 1.14, Baukit 0.0.1, SymPy 1.14, scikit-learn
1.9, and Ruff 0.15.17. That records a working snapshot, not an invariant.

Do not add `module load cuda` only because a GPU partition is selected. It may
conflict with the conda runtime. First inspect the current template and test
environment compatibility in an explicitly approved small run. Snapshot the
actual environment in every serious job:

```bash
python --version
python - <<'PY'
import torch, transformers
print("torch", torch.__version__, "cuda", torch.version.cuda)
print("transformers", transformers.__version__)
print("cuda_available", torch.cuda.is_available())
PY
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
```

## Models and loader boundary

`docs/model_registry.yml` is the authority for logical roles, checkpoints,
backends, and validation status. The shared store contains many downloaded
models, including Qwen 2.5 3B/7B/14B/32B, Llama 3.1 8B, Mistral 7B and larger,
DeepSeek-R1-Distill-Qwen-32B, Gemma variants, and Qwen 3/3.5 variants. Presence
in that directory does not mean a model is approved, compatible, or validated.

| Registry role | Model | Backend | Current registry status |
|---|---|---|---|
| `qwen_primary` | Qwen2.5-7B-Instruct | TransformerLens | hooks and logprob validated |
| `llama_primary` | Llama-3.1-8B-Instruct | TransformerLens | hooks and logprob validated |
| `qwen_3b`, `qwen_14b` | Qwen2.5 scale followups | TransformerLens | not validated |
| `mistral_alt` | Mistral-7B-Instruct-v0.3 | Baukit | not validated |
| `deepseek_reasoning` | DeepSeek-R1-Distill-Qwen-32B | Baukit | logprob validated only |
| large judge roles | Qwen 32B / Qwen3.5 397B reserve | Baukit | not validated |

Use `src/physmon/models/loader.py` and the registry, not an ad hoc direct
checkpoint load. TransformerLens has model-name and local-weight constraints
that previous work already handled through the project loader. Record model
role, registry revision, resolved local path, tokenizer identity, backend, and
hook validation status in a run manifest.

## Before handing a job to Slurm

Confirm the following in the job's own stdout or metadata:

```text
deployed Git SHA and .physmon_ops/deployment_commit
Slurm job ID, node, partition, GRES, CPU, memory, walltime
hostname and GPU driver/runtime snapshot
conda environment and key package versions
model registry key/backend and resolved checkpoint/tokenizer path
input family manifest path, hash, expected rows and panel policy
output root, stdout/stderr root, checkpoint root, attempt ID
```

This transforms cluster execution from a one-off shell interaction into an
auditable experiment.
