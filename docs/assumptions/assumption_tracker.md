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
- Later on 2026-06-13, fresh H100 and H200 template-smoke submissions were both accepted
  by Slurm as jobs `242344` and `242345`, which confirms that the partition names,
  scratch paths, and template entrypoints are correct.
- Immediate runtime for those fresh H100/H200 smoke jobs was deferred by
  `QOSMaxCpuPerUserLimit`, so same-session execution on those partitions remains subject
  to live scheduler policy rather than a repo-side misconfiguration.

## A2 - Hooking Support for Selected Models

Status: Verified with caveats.

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
- A direct local-path TransformerLens load attempt then showed that this
  TransformerLens version expects an official model identifier rather than the raw local
  path string.
- Corrected official-ID plus local-weights A100 jobs then completed cleanly for both
  required dense candidates:
  - `242337`: `Qwen/Qwen2.5-7B-Instruct`
    - `hf_loaded` after `527.03s`
    - `tl_loaded` after `10.64s`
    - `dummy_forward_ok` with `logits_shape=[1, 33, 152064]`
  - `242338`: `meta-llama/Llama-3.1-8B-Instruct`
    - `hf_loaded` after `1257.49s`
    - `tl_loaded` after `2.90s`
    - `dummy_forward_ok` with `logits_shape=[1, 32, 128256]`
- This is sufficient to confirm that the selected Qwen and Llama dense candidates are
  compatible with the intended TransformerLens loading path for the upcoming Stage 2
  validation scripts.
- Remaining caveat: this was a deliberately narrow smoke test (`first_n_layers=2`) rather
  than the full Stage 2 hook-extraction suite, so layer-by-layer activation extraction,
  patching, and determinism still belong to Part IV rather than Part II.

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
