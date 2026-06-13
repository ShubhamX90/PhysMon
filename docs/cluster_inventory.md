# Sharanga Cluster Inventory

Date: 2026-06-13

This inventory records the live Sharanga environment discovered for PhysMon Part II.
All commands were run via `ssh sharanga`.

## II.1 - Model Inventory

Primary pre-downloaded model root:

- `/scratch/pabitra/rag-reason/models`

Current on-disk size of the model root:

- `1.8T /scratch/pabitra/rag-reason/models`

### Inventory Table

| Model family | Model name | Parameter count | Path on scratch | Size on disk | Format | Usable for PhysMon roles |
|---|---|---:|---|---:|---|---|
| Qwen | Qwen2.5-7B-Instruct | 7B | `/scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct` | 14G | safetensors | `PRIMARY_DENSE` confirmed on 2026-06-13 via A100 TransformerLens dummy-forward job `242337` (`d_model=3584`, `n_layers=2` smoke) |
| Llama | Llama-3.1-8B-Instruct | 8B | `/scratch/pabitra/rag-reason/models/Llama-3.1-8B-Instruct` | 30G | safetensors | `PRIMARY_DENSE` confirmed on 2026-06-13 via A100 TransformerLens dummy-forward job `242338` (`d_model=4096`, `n_layers=2` smoke) |
| Mistral | Mistral-7B-Instruct-v0.3 | 7B | `/scratch/pabitra/rag-reason/models/Mistral-7B-Instruct-v0.3` | 27G | safetensors | `PRIMARY_DENSE` alternate candidate; not needed because the required non-Qwen dense slot is already covered by Llama |
| Qwen | Qwen2.5-32B-Instruct | 32B | `/scratch/pabitra/rag-reason/models/Qwen2.5-32B-Instruct` | 59G | safetensors | `LARGE_JUDGE` |
| Qwen | Qwen3-32B | 32B | `/scratch/pabitra/rag-reason/models/Qwen3-32B` | 59G | safetensors | `LARGE_JUDGE` secondary candidate |
| Qwen | Qwen3.5-122B-A10B-FP8 | 122B MoE (10B active) | `/scratch/pabitra/rag-reason/models/Qwen3.5-122B-A10B-FP8` | 110G | safetensors | `LARGE_JUDGE` |
| Qwen | Qwen3.5-397B-A17B | 397B MoE (17B active) | `/scratch/pabitra/rag-reason/models/Qwen3.5-397B-A17B` | 717G | safetensors | `LARGE_JUDGE` |
| Qwen | Qwen3.5-397B-A17B-NVFP4 | 397B MoE (17B active) | `/scratch/pabitra/rag-reason/models/Qwen3.5-397B-A17B-NVFP4` | 211G | safetensors | `LARGE_JUDGE` |
| Mistral | Mistral-Small-3.2-24B-Instruct-2506 | 24B | `/scratch/pabitra/rag-reason/models/Mistral-Small-3.2-24B-Instruct-2506` | 88G | safetensors | `OTHER` |
| Mistral | Mistral-Small-4-119B-2603 | 119B | `/scratch/pabitra/rag-reason/models/Mistral-Small-4-119B-2603` | 212G | safetensors | `LARGE_JUDGE` |
| other | DeepSeek-R1-Distill-Qwen-32B | 32B | `/scratch/pabitra/rag-reason/models/DeepSeek-R1-Distill-Qwen-32B` | 59G | safetensors | `REASONING_TUNED`, `LARGE_JUDGE` |
| other | DeepSeek-V4-Flash-W4A16-FP8-MTP | unspecified in dir name | `/scratch/pabitra/rag-reason/models/DeepSeek-V4-Flash-W4A16-FP8-MTP` | 146G | safetensors | `OTHER` |
| other | DeepSeek-V4-Flash-W4A16-FP8-MTP-vllmfix | unspecified in dir name | `/scratch/pabitra/rag-reason/models/DeepSeek-V4-Flash-W4A16-FP8-MTP-vllmfix` | 146G | safetensors | `OTHER` |
| other | gemma-3-27b-it | 27B | `/scratch/pabitra/rag-reason/models/gemma-3-27b-it` | 49G | safetensors | `OTHER` |
| other | gemma-4-31B | 31B | `/scratch/pabitra/rag-reason/models/gemma-4-31B` | 55G | safetensors | `LARGE_JUDGE` |

### Role Coverage Status

- `PRIMARY_DENSE` from Qwen family: present as `Qwen2.5-7B-Instruct` candidate.
- `PRIMARY_DENSE` from Llama/Mistral family: present as `Llama-3.1-8B-Instruct` and `Mistral-7B-Instruct-v0.3` candidates.
- `REASONING_TUNED`: present as `DeepSeek-R1-Distill-Qwen-32B`.
- `LARGE_JUDGE`: present via multiple models, including `Qwen2.5-32B-Instruct`, `Mistral-Small-4-119B-2603`, `gemma-4-31B`, and the large Qwen 3.5 models.

Current verdict: no required role category is absent, and the minimum required
`PRIMARY_DENSE` coverage is now confirmed with one Qwen-family dense model
(`Qwen2.5-7B-Instruct`) and one Llama/Mistral-family dense model
(`Llama-3.1-8B-Instruct`).

## II.2 - GPU Node Assessment

### GPU Partitions

| Partition | Nodes | GPU type | GPUs per node | CPU / node | Memory / node | Default time | Max time | Notes |
|---|---:|---|---:|---:|---:|---|---|---|
| `gpu_a100_8` | 1 | `NVIDIA A100-SXM4-80GB` | 8 | 64 | 1000000M | `00:30:00` | `5-00:00:00` | `OverSubscribe=NO`, `DefMemPerGPU=96000`, node `gpunode4` |
| `gpu_h100_4` | 2 | `NVIDIA H100 80GB HBM3` | 4 | 64 | 1000000M | `00:30:00` | `2-00:00:00` | `OverSubscribe=NO`, `DefMemPerGPU=96000`, nodes `gpunode5-6` |
| `gpu_h200_8` | 1 | `NVIDIA H200 NVL` | 8 | 64 | 1000000M | `00:30:00` | `1-00:00:00` | `OverSubscribe=NO`, `DefMemPerGPU=96000`, node `gpunode7` |

### Node State Snapshot

| Node | Partition | State | GPU inventory | CPU alloc | Memory alloc | Notes |
|---|---|---|---|---:|---:|---|
| `gpunode4` | `gpu_a100_8` | `MIXED` | 8 x A100 80GB | 44 / 64 | 344G / 1000000M | A100 smoke succeeded here |
| `gpunode5` | `gpu_h100_4` | `MIXED+RESERVED` | 4 x H100 80GB HBM3 | 9 / 64 | 180G / 1000000M | current H100 work concentrated here |
| `gpunode6` | `gpu_h100_4` | `DOWN+DRAIN+NOT_RESPONDING` | 4 x H100 80GB HBM3 | 0 / 64 | 0 | reason: `Kill task failed (JobId=242225 StepId=0)` at `2026-06-13T17:35:40` |
| `gpunode7` | `gpu_h200_8` | `MIXED` | 8 x H200 NVL | 20 / 64 | 612G / 1000000M | current H200 work active here |

### Queue Depth Snapshot

Live `squeue` snapshot at inventory time:

- `gpu_a100_8`: 4 running jobs, 0 pending.
- `gpu_h100_4`: 2 running jobs, 12 pending jobs.
- `gpu_h200_8`: 4 running jobs, 0 pending jobs in the immediate snapshot, but new submissions were blocked by active resource/QoS pressure.

Representative pending reasons observed:

- `ReqNodeNotAvail, UnavailableNodes:gpunode6`
- `Resources`
- `Requested nodes are busy`

### Wait-Time Notes from Recent `sacct`

- A100 recent jobs started immediately when capacity was available. Example:
  `242257` (`physmon_smoke_a100`) submitted and started on `2026-06-13 18:50:48`.
- H100 recent jobs also started immediately when `gpunode5` was available. Example:
  `242167` submitted at `2026-06-13 13:20:57` and started at `13:20:57`.
- H200 recent jobs typically started within seconds to a few minutes when capacity was
  available. Examples:
  - `242199`: submitted `15:08:21`, started `15:08:22`
  - `242114`: submitted `11:01:35`, started `11:04:36`
  - `242107`: submitted `10:27:37`, started `10:28:39`

Interpretation: nominal wait times are low when nodes are healthy and free, but live
H100 access is currently impaired by one drained node and live H200 access is currently
tight because the single H200 node is heavily used.

### CUDA / Driver / GPU Memory

Direct measurements:

- A100 (`gpu_a100_8` on `gpunode4`):
  - `Driver Version: 580.126.20`
  - `CUDA Version: 13.0`
  - `memory.total = 81920 MiB`
- H200 (`gpu_h200_8` on `gpunode7`, measured via an `srun` step inside the user's
  running allocation `242248`):
  - `Driver Version: 580.126.20`
  - `CUDA Version: 13.0`
  - `memory.total = 143771 MiB`

H100 note:

- Direct `nvidia-smi` capture was not obtainable during this snapshot because
  `gpunode6` was down/drained and immediate one-GPU probes on `gpu_h100_4` were blocked by
  live reservation/resource state.
- Slurm GRES confirms `NVIDIA H100 80GB HBM3`.

### Proposal §6.1 Access Check

Proposal §6.1 assumes access to H200, H100, and A100 resources. This is true with
caveats:

- A100 access is directly verified.
- H100 partition access exists, but one of two nodes is currently down/drained, and the
  other is reserved/partially occupied.
- H200 partition access exists and was already used by the user, but fresh submissions
  are presently constrained by live resource/QoS pressure.
- Follow-up on 2026-06-13 23:28 IST: fresh template-smoke submissions were accepted by
  Slurm as jobs `242344` (H100) and `242345` (H200), which confirms the partition names
  and template wiring are correct, but immediate execution was deferred by
  `QOSMaxCpuPerUserLimit` rather than by an invalid partition, path, or environment
  configuration.

## II.3 - Storage Assessment

### Filesystems

- Home: `/home/pabitra`
  - filesystem size `199T`
  - used `24T`
  - available `175T`
- Scratch: `/scratch/pabitra`
  - filesystem size `274T`
  - used `100T`
  - available `175T`

### PhysMon Scratch Area

- Root: `/scratch/pabitra/physmon`
- Current usage: `182K`
- Subdirectories confirmed accessible:
  - `/scratch/pabitra/physmon/activations`
  - `/scratch/pabitra/physmon/checkpoints`
  - `/scratch/pabitra/physmon/slurm_logs`

### Activation Storage Estimate

Using the requested rough estimate for a 7B dense model:

- `80 activation sites x 2000 tokens x 4000 hidden dim x 4 bytes`
- Per problem: `2,560,000,000 bytes`
- Per problem: about `2.56 GB` decimal, or about `2.38 GiB`

Illustrative totals:

- 100 problems: about `256 GB` (`~238 GiB`)
- 500 problems: about `1.28 TB` (`~1.16 TiB`)
- 1000 problems: about `2.56 TB` (`~2.33 TiB`)

Assessment:

- Current scratch headroom (`175T` available) is easily sufficient for the pilot study and
  leaves comfortable room for activations, checkpoints, logs, and additional model caches.
- The dominant risk is not raw cluster-wide free space but local experiment discipline:
  activation retention policy and per-run cleanup will matter once larger sweeps begin.

## II.4 - Software Stack Verification

### Verified Environment

GPU-backed A100 validation job output:

- `PyTorch: 2.7.1+cu126`
- `CUDA: True`
- `GPU: NVIDIA A100-SXM4-80GB`
- `TransformerLens: 3.4.0`
- `Transformers: 5.11.0`
- `SymPy: 1.14.0`
- `sklearn: 1.9.0`
- `baukit: 0.0.1`

Interpretation:

- The Sharanga `physmon` environment imports the required stack successfully on a GPU node.
- CUDA is visible inside the environment on A100.
- `transformer_lens` and `baukit` are both installed and importable.

### Hook Support Validation

Current status:

- A direct local-path TransformerLens load attempt failed with
  `ValueError: /scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct not found`,
  which revealed that this TransformerLens version expects an official model identifier
  even when weights are supplied from a local directory.
- The corrected official-ID plus local-weights path was then validated on A100 with a
  deliberately reduced-layer smoke test (`first_n_layers=2`) and explicit stage markers:
  - `242337`: `Qwen/Qwen2.5-7B-Instruct` with local
    `/scratch/pabitra/rag-reason/models/Qwen2.5-7B-Instruct`
    - `hf_loaded` after `527.03s`
    - `tl_loaded` after `10.64s`
    - `dummy_forward_ok` with `logits_shape=[1, 33, 152064]`
  - `242338`: `meta-llama/Llama-3.1-8B-Instruct` with local
    `/scratch/pabitra/rag-reason/models/Llama-3.1-8B-Instruct`
    - `hf_loaded` after `1257.49s`
    - `tl_loaded` after `2.90s`
    - `dummy_forward_ok` with `logits_shape=[1, 32, 128256]`

Conclusion:

- `Qwen2.5-7B-Instruct` is confirmed usable as the Qwen-family `PRIMARY_DENSE`
  candidate for Stage 2 instrumentation work.
- `Llama-3.1-8B-Instruct` is confirmed usable as the non-Qwen `PRIMARY_DENSE`
  candidate for Stage 2 instrumentation work.
- `Mistral-7B-Instruct-v0.3` remains a documented fallback candidate but is not required
  to satisfy the proposal minimum once Llama is confirmed.
- This completes the Part II requirement to verify that the minimum required model-role
  inventory exists locally and that the primary dense candidates are compatible with the
  intended TransformerLens loading path.
