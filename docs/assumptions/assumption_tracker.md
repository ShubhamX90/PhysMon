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
- The packaging backend had to be updated to `setuptools.build_meta` for editable install
  support on Sharanga.
- `baukit` had to be installed from GitHub because no matching PyPI release was
  available.
- Full model-specific hook validation is still pending Stage 2. Candidate
  `PRIMARY_DENSE` models will still need short forward-pass and hook tests before final
  selection.

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

Status: Not yet verified.

Evidence: Pending Sharanga model inventory.

## A9 - Pilot Sensitivity Signal Exists

Status: Not yet verified.

Evidence: Pending Stage 4 pilot behavioural sweep.
