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

## A2_reasoning_tuned - DeepSeek Behavioural/Logprob Validation

Status: Verified with caveats on 2026-06-14.

Evidence:
- Stage 3 brief Part C.2 requires Hugging Face-only validation for
  `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`; TransformerLens support is explicitly not
  required for this role.
- Submission script prepared at
  `slurm/submitted/validate_logprob_deepseek_r1_32b.sh` with 2xH200, `device_map="auto"`,
  `torch_dtype=torch.bfloat16`, deterministic greedy generation checks, and
  reference-answer log-prob validation.
- First submission `242380` reached Python startup but failed immediately with
  `Invalid device argument ` before model loading. The validator was then patched to make
  peak-VRAM telemetry best-effort and to record full tracebacks on failure.
- Second submission `242382` completed successfully from commit `7a90f0f` on `gpunode7`
  in `00:15:25` with exit code `0:0`.
- Result artifact now exists at
  `results/stage2/logprob_validation/deepseek_r1_32b_logprob_validation.json`.
- Positive checks:
  - model load succeeded on 2xH200 with `device_map="auto"`
  - `log p(y* | x)` was finite and negative: `-14.1875`
  - altered prompt changed the reference-answer log-probability: `-14.5`
  - greedy generation was deterministic across 3 repeated runs
  - peak VRAM was approximately `30.4 GB` on GPU 0 and `32.2 GB` on GPU 1
- Caveat:
  - final successful job `242382` reported `has_think_tags: false` on the simple
    validation prompt. This is expected for trivially simple problems and is not a red
    flag for the `REASONING_TUNED` role, which requires log-probability access and
    deterministic generation. Both were confirmed.

## A3 - Literature Gap Still Current

Status: Verified on 2026-06-14.

Evidence:
- Fresh 2025-2026 literature search completed on 2026-06-14 using the Stage 3 brief
  query set:
  1. `arXiv 2025 2026 physics counterfactual LLM shortcut benchmark invariant`
  2. `"physics shortcut" language model hidden state 2025`
  3. `"invariant physics problems" LLM reasoning 2025 2026`
  4. `UGPhysics PhysReason shortcut sensitivity 2026`
  5. `physics reasoning benchmark controlled editing language model`
- Related work located includes:
  - `CounterBench` (counterfactual reasoning benchmark; not physics-specific and not a
    hidden-state monitor study)
  - `PRL-Bench` / related physics-research benchmark work (physics-oriented, but not
    solver-verified invariant family editing plus hidden-state sensitivity prediction)
  - `PhysGym`, `PHYBench`, and `ABench-Physics` style physics-reasoning benchmarks
    (physics-focused, but not combining invariant counterfactual families with internal
    monitoring of sensitivity)
  - `Are language models aware of the road not taken?`-style hidden-state work
    (internal-state/uncertainty related, but not a solver-verified physics benchmark)
- Outcome: no near-fatal scoop was found that combines BOTH
  (a) solver-verified invariant physics counterfactual families and
  (b) hidden-state prediction of shortcut sensitivity before it appears in output.
- Interpretation: the literature landscape contains adjacent work on physics reasoning,
  counterfactual evaluation, and hidden-state monitoring separately, but the exact
  PhysMon combination remains open enough to proceed.

## A4 - Symbolic Invariance Certificates Are Tractable

Status: Verified on 2026-06-14.

Evidence:
- All 30 pilot templates now pass the SymPy verifier across the classical mechanics and
  electrostatics/circuits pilot families.
- The updated Stage 3 render plus verification pass on 2026-06-14 completed with
  `verification_pass = 30/30`.
- Tractability for the larger Stage 6 expansion set remains to be confirmed separately.

## A5 - Log-Probability Access Is Stable Across Models

Status: Verified with caveats.

Evidence:
- Stage 2 log-probability validation completed successfully for both required primary
  dense models on A100:
  - `242356`: `Qwen/Qwen2.5-7B-Instruct`
    - finite `log p(y* | x)` for reference answer `10 m/s`
    - altered prompt changed the reference-answer log-probability
    - greedy generation was deterministic across repeated runs
  - `242358`: `meta-llama/Llama-3.1-8B-Instruct`
    - finite `log p(y* | x)` for reference answer `10 m/s`
    - altered prompt changed the reference-answer log-probability
    - greedy generation was deterministic across repeated runs
- Caveat: these validations use one controlled physics prompt and a short reference answer,
  so broader benchmark stability still depends on the full Stage 4 behavioural sweep.

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
