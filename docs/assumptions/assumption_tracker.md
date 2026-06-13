# Assumption Tracker

This tracker records verification status for the assumptions listed in the supplementary
document.

## A1 - Sharanga Cluster Access

Status: Verified with caveats.

Evidence:
- SSH access works for user `pabitra`; home is `/home/pabitra`; scratch is
  `/scratch/pabitra`.
- `~/PhysMons` exists on Sharanga and `activations` is a symlink to
  `/scratch/pabitra/physmon/activations`.
- Slurm partitions discovered during Part I.5:
  `gpu_h200_8`, `gpu_h100_4`, `gpu_a100_8`.
- A100 smoke job `242257` completed successfully on `gpunode4` with
  `torch 2.7.1+cu126`, `torch.version.cuda == 12.6`,
  `torch.cuda.is_available() == true`, and device
  `NVIDIA A100-SXM4-80GB`.
- Part II inventory confirmed live node topology:
  `gpunode4` (A100), `gpunode5-6` (H100), `gpunode7` (H200).
- Part II queue inspection showed `gpunode6` is currently
  `DOWN+DRAIN+NOT_RESPONDING`, which explains the live H100 submission
  failures observed during Part I.5.
- Direct hardware probes recorded `Driver Version 580.126.20` and
  `CUDA Version 13.0` on A100 and H200 nodes.
- H100 smoke job submission succeeded, but runtime verification was blocked by current
  partition availability (`ReqNodeNotAvail` while one node is drained and the other is
  occupied).
- H200 smoke job submission succeeded, but runtime verification is currently blocked by
  the user's existing running H200 allocation causing `QOSMaxCpuPerUserLimit`.

## A2 - Hooking Support for Selected Models

Status: Partially verified.

Evidence:
- Sharanga `physmon` environment created successfully and exported to
  `docs/environment_lock.yml`.
- `transformer_lens` import succeeds in the Sharanga `physmon` environment when checked
  with a bounded import.
- `sympy` import succeeds in the Sharanga `physmon` environment.
- GPU-backed Part II validation on A100 confirmed live imports for:
  `torch 2.7.1+cu126`, `transformer-lens 3.4.0`, `transformers 5.11.0`,
  `sympy 1.14.0`, `scikit-learn 1.9.0`, and `baukit 0.0.1`.
- The packaging backend had to be updated to `setuptools.build_meta` for editable install
  support on Sharanga.
- `baukit` had to be installed from GitHub because no matching PyPI release was
  available.
- TransformerLens successfully began loading the local
  `Qwen2.5-7B-Instruct` checkpoint on A100, which is evidence that the local-path
  architecture conversion is working, but the full-depth load path is slow on shared
  storage.
- A direct local-path TransformerLens load attempt then showed that this
  TransformerLens version expects an official model identifier rather than the raw local
  path string.
- Corrected official-ID plus local-weights A100 jobs were launched for
  `Qwen/Qwen2.5-7B-Instruct` and a Mistral-family candidate; both progressed into active
  TransformerLens weight loading without immediate architecture errors.
- Those corrected jobs still did not complete a full dummy-forward result within the
  practical Part II inventory window.
- Candidate `PRIMARY_DENSE` models therefore remain plausible rather than fully confirmed;
  the last missing evidence is a clean Stage 2 hook-validation script that completes and
  records a dummy forward on the chosen dense candidates.

## A3 - Literature Gap Still Current

Status: Not yet verified.

Evidence: Fresh literature search required before benchmark development.

## A4 - Symbolic Invariance Certificates Are Tractable

Status: Not yet verified.

Evidence: Pending Stage 1/Stage 3 template work.

## A5 - Log-Probability Access Is Stable Across Models

Status: Not yet verified.

Evidence: Pending Stage 2 validation.

## A6 - Dual Validators Are Available

Status: Not yet verified.

Evidence: Pending validator recruitment plan.

## A7 - Bibliography IDs Are Correct Except Flagged Entries

Status: Not yet verified.

Evidence: Bibliography audit required before submission.

## A8 - Large Open Model Is Available Locally

Status: Verified.

Evidence:
- Sharanga model inventory found multiple large open-weight models already present under
  `/scratch/pabitra/rag-reason/models`.
- Large candidates include:
  `Qwen2.5-32B-Instruct`, `Qwen3-32B`, `DeepSeek-R1-Distill-Qwen-32B`,
  `Mistral-Small-4-119B-2603`, `gemma-4-31B`,
  `Qwen3.5-122B-A10B-FP8`, and `Qwen3.5-397B-A17B`.
- The model root currently occupies `1.8T`, indicating the weights are already staged
  locally on cluster storage rather than needing immediate download.

## A9 - Pilot Sensitivity Signal Exists

Status: Not yet verified.

Evidence: Pending Stage 4 pilot behavioural sweep.
