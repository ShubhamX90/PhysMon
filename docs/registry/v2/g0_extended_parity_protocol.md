# G0 item 3: extended HF-versus-TransformerLens parity (protocol, pre-registered)

Status: PRE-REGISTERED, written before any GPU result of this check (2026-11-13). Plan of record:
`docs/proposals/PhysMon_Research_v2.tex`, G0 item 3 ("P0, narrowed"), P0.3(a) and Gate P0, G5, and Section
`sec:causal` (claim types T1-T3). Script: `scripts/v2/s185_extended_parity.py`; job template:
`slurm/templates/g0_extended_parity.sh`; tests: `tests/v2/test_extended_parity_s185.py`. The thresholds below are the
constants of the script; `plan.json` stores their SHA-256 fingerprint (`design_fingerprint`), and `run` refuses to
start if the script's constants no longer match the frozen plan.

Design fingerprint at pre-registration: `e5cd6023eeeb5725c055841314ea42664851857756a51c9412a3e0f94035bb66`
(frozen plans: `data/v2/g0_extended_parity/{qwen_primary,llama_primary}/plan.json`; inputs 417-1,088 tokens for Qwen,
392-4,292 for Llama).

## Why this check

The earlier parity (job 399217, J14.7-011) compared final-position logits on one short smoke prompt, in float16 with
parameters on CPU. G5 will intervene in bfloat16 on CUDA at residual, attention, per-head and MLP sites, at positions
spread over a prompt plus the model's own reasoning trace (hundreds to thousands of tokens). Errors that a short prompt
cannot reveal grow with position: rotary-embedding scaling (Llama 3.1 uses NTK-by-parts "llama3" scaling), rotary base,
bf16 attention-score precision over long contexts, grouped-query head mapping, Qwen2's q/k/v biases. Gate P0 asks that
"the intervention hooks demonstrably affect the claimed tensors and token positions"; reading parity alone does not show
that, so two interventions are also checked.

## Inputs (frozen by `s185 plan`, committed before the job)

- Models: `qwen_primary` (Qwen2.5-7B-Instruct, revision a09a3545...) and `llama_primary` (Llama-3.1-8B-Instruct, revision
  0e9e39f2...), weights verified file by file against `docs/model_manifests/<key>.json` (SHA-256 and size) by the job.
- N = 12 sequences per model. Each is a chat-templated user turn built exactly as the Stage 15 runner builds it
  (`reasoning_contract_v2.user_turn` with the unit stated + `generation.chat_prompt_ids`, BOS once), followed by a
  sampled reasoning trace of the SAME model from its G2 calibration run (`results/stage15/s15_cal_qwen25_7b`,
  `s15_cal_llama31_8b`, field `generated_answer_raw`, re-tokenized without special tokens).
- Lengths: target trace lengths are the quantiles 0.05, 0.13, ..., 0.95 (12 evenly spaced) of that model's own
  calibration length distribution (all 2,080 records, any completion status), so short, median and long (95th
  percentile) cases are all present. For Llama the 95th percentile is the 4,096-token budget (226 of 2,080 traces hit
  the budget), so its longest case is ~4.3k tokens; for Qwen it is ~930 tokens.
- Prompt: if one of the 12 M0 pilot structures (`data/v2/dataset/m0_pilot/cells.jsonl`, instance 0) has a trace within
  15% of the target, a role cell of that structure is the prompt (types cycle no_cue, N, R, D, C, K), and the trace is
  the model's own trace under the no-cue control prompt: exactly T1 prefix type (ii). Otherwise the closest trace of any
  unused structure is taken with its own calibration prompt (the M0 traces do not reach the long tail). Each structure is
  used once. Traces are chosen by length only, never by answer, correctness or status.
- The job re-tokenizes every input and refuses (exit 12) unless it reproduces the frozen token ids.

## What is compared

HF: `AutoModelForCausalLM`, bfloat16 (the study dtype), CUDA, default SDPA attention (the path the study's HF runners
use). TransformerLens 3.4.0 `HookedTransformer`, bfloat16, built from the same in-memory HF weights and the local
`config.json` (no hub access), with every weight-processing option off, so that its activations are HF's activations and
not a reparameterisation:

| TL option | Value | Why |
|---|---|---|
| `fold_ln` | False | folding RMSNorm weights into the next matrices changes resid-adjacent tensors |
| `center_writing_weights` | False | subtracts a per-position mean from every residual write; HF has none |
| `center_unembed` | False | shifts logits by a per-position constant; keep HF logits |
| `fold_value_biases` | False | Qwen2 has value biases; folding them into b_O changes `hook_z` |
| `refactor_factored_attn_matrices` | False | re-bases W_Q/W_K and W_V/W_O, so q, k, v, z would differ from HF |
| `default_prepend_bos` | False | inputs are token ids; the chat template already contains the BOS |
| `n_ctx` | max(2048, longest input) | TL caps both models at 2,048 by default; longer inputs need it raised |
| `use_attn_result` | False | per-head d_model results are not materialised (memory); z and attn_out are compared |

Sites, at every layer, every position (TL hook name; HF tensor captured with module hooks, never with
`output_hidden_states`, whose last entry is final-normed in transformers 5; the hidden states are checked to equal the
hooked `resid_pre` exactly):

| Site | TL | HF |
|---|---|---|
| resid_pre | `blocks.l.hook_resid_pre` | input of decoder layer l (= `hidden_states[l]`) |
| resid_mid | `blocks.l.hook_resid_mid` | resid_pre + self_attn output (HF's own bf16 add) |
| resid_post | `blocks.l.hook_resid_post` | output of decoder layer l (= `hidden_states[l+1]` for l < L-1) |
| attn_out | `blocks.l.hook_attn_out` | output of `self_attn` |
| z (per head) | `blocks.l.attn.hook_z` | input of `self_attn.o_proj`, reshaped to heads |
| mlp_out | `blocks.l.hook_mlp_out` | output of `mlp` |
| logits | model output | model output |

Metrics per site, pooled over the 12 sequences: cosine per position (per position and head for z), its minimum (with
prompt and position) and mean; relative L2 error ||TL - HF|| / ||HF|| over the sequence, worst sequence; max abs error.
Logits: top-1 agreement over all positions, mean and max KL(HF || TL) over positions, max abs difference, and the largest
HF top-1/top-2 margin at a disagreeing position (disagreements at near-ties are noise).

Noise references, on the same inputs: (1) a second HF SDPA pass (`rerun`: run-to-run determinism; expected zero), and
(2) an HF pass with eager attention (`floor`: two correct HF bf16 implementations of the same model; eager computes
attention scores in bf16 like TL, SDPA keeps them in fp32). Because a bit-identical rerun gives a floor of zero, the
eager pass is the floor the thresholds use; both are reported.

## Interventions (Gate P0: hooks affect the claimed tensors and positions)

Applied identically in HF (module hooks) and TL (hook points), at layer L = n_layers // 2; directions are fixed seeded
random unit vectors, scales come from the HF clean pass.

1. `resid_add` (stands for a T3 intervention at a quantity's prompt tokens): add 1.0 x the median residual norm along a
   fixed direction to `resid_post[L]` at 4 positions starting at the prompt midpoint.
2. `head_z_add` (stands for a T1 head intervention at answer positions): add 20 x the head's median z norm along a fixed
   direction to `z[L, head n_heads // 2]` at the first 16 trace positions.

Checks per intervention, per sequence, both backends: (a) the downstream tensor (`resid_post[L]` as read after the hook, i.e. what layer L+1 receives, resp. `attn_out[L]`)
changes only inside the window (outside: <= 2 x the backend's rerun difference, i.e. exactly zero when deterministic);
(b) inside the window the change points where the perturbation predicts (cosine >= 0.99 with the added vector, resp. with
the vector mapped through that head's W_O); (c) logits before the window do not change (<= max(2 x rerun noise, 0.05));
(d) the HF effect is informative (it moves some next-token log-probability by >= 1 nat; otherwise UNINFORMATIVE, which
fails); (e) effect parity: the change in the log-probability of each observed next token over [window start, window end
+ 64), TL against HF, relative error judged by the rule below with the HF-eager effect as floor (allowance 0.10,
ceiling 0.50).

## Thresholds and the rule (pre-registered)

Every metric is an error (larger is worse). It PASSES if `value <= allowance`, or if `value <= 3 x floor` AND
`value <= ceiling`, where floor is the same metric between HF SDPA and HF eager on the same inputs. NaN or inf fails.

| Class | Metric | Allowance | Ceiling |
|---|---|---|---|
| residual (resid_pre, resid_mid, resid_post) | 1 - min cosine | 1e-3 (cos >= 0.999) | 1e-2 (cos >= 0.99) |
| | 1 - mean cosine | 1e-4 | 1e-3 |
| | relative L2 (worst sequence) | 0.02 | 0.05 |
| component (attn_out, z, mlp_out) | 1 - min cosine | 1e-2 | 0.10 |
| | 1 - mean cosine | 1e-3 | 1e-2 |
| | relative L2 (worst sequence) | 0.05 | 0.15 |
| logits | 1 - top-1 agreement | 0.01 | 0.03 |
| | mean KL(HF‖TL), nats | 0.01 | 0.05 |
| intervention effect | relative error of the effect | 0.10 | 0.50 |

Reasons:

- Allowance: a level at which no mechanism conclusion could change. Residual cosine 0.999 at every position means the
  TL state differs from HF's by at most ~4.5% of its norm in the worst position; mean cosine 0.9999 and a sequence-level
  relative error of 2% are about two to five bf16 unit roundoffs (2^-8 ~ 0.4%) accumulated over 28-32 layers. A mean
  KL of 0.01 nats and 99% top-1 agreement are far below the effects G5 reports (G4's SESOI is in tens of percentage points
  of answer share; Phase-I effects were > 0.5 nats).
- Component sites are looser: per-position attention, head and MLP outputs can have small norms that arise from
  cancellation of large terms, where bf16 relative error is large without any implementation difference.
- Floor clause (3 x HF-eager-versus-SDPA): a TL path that is no further from HF-SDPA than about three times HF's own
  alternative kernel is noise-equivalent for mechanism work; TL computes attention scores and softmax inputs in bf16
  like HF eager, so the eager floor is the relevant one. A factor of 3 allows the different op ordering (einsum, scale
  after the product) without excusing systematic error.
- Ceiling: no floor can excuse an error at which a real defect is the likely cause. A rotary-scaling, rotary-base,
  head-mapping or missing-bias bug drives residual cosines at long positions well below 0.99 and top-1 agreement well
  below 97%; a wrong hook position or head makes the intervention effects nearly uncorrelated (relative error > 1).
- Intervention locality is exact by construction (position-wise operations and causal masking), so any change outside
  the window above run-to-run noise is a defect.

## What PASS and FAIL imply

A model PASSES only if every site at every layer, the logits, both interventions on every sequence, and the
hidden-states consistency pass, with all 12 sequences evaluated. A failing site fails parity for that model and backend
(Gate G0/P0): no mechanism work on it with TransformerLens; behaviour may proceed. A crashed or skipped sequence is a
FAIL, never a pass on fewer inputs. The result is valid only for this TL version (3.4.0), this transformers/torch stack
(the frozen environment), bf16 on CUDA with HF SDPA as reference, and sequence lengths up to
`parity_valid_up_to_tokens` in the result file; G5 work outside that range needs a new check. PASS is infrastructure
evidence, not scientific evidence. Not covered: attention patterns (`hook_pattern`; HF SDPA does not expose them),
q/k/v hooks, other models (Qwen3-8B needs its own run before mechanism work), multi-GPU or batched/padded inputs.

## Outputs

`<OUTPUT_DIR>/<model_key>.json` (exclusive create, never overwritten): model revision, manifest hash and file
verification, source commit, Slurm job, GPU, versions, dtype, TL options and config, plan and input hashes, thresholds
and design fingerprint, per site and layer the pooled TL, floor and rerun metrics with the judgement, logits,
interventions, per-sequence records (lengths, prompt source, token-id hash, timings, errors), `failures` and `overall`.
