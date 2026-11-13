#!/bin/bash
#SBATCH --job-name=g4s
#SBATCH --partition=gpu_h200_8
#SBATCH --gres=gpu:1
#SBATCH --time=1-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --output=/scratch/pabitra/gemma4comp/%x-%j.out
# Serves the competition checkpoint with the COMPETITION'S OWN FLAGS AND NOTHING ELSE.
#
# This replaces the rung ladders in serve{,2,3}.sbatch, which were the wrong approach: each
# appended setting (--enforce-eager, --kernel-config, VLLM_* toggles, a fake nvcc shim) hid one
# symptom and moved the failure later. The ladder's final "success" served with the gemma4
# parsers OFF, which returns
#     400 "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser
# for every tool call -- a server that looks alive and cannot run an agent.
#
# Every failure had ONE root cause: a mismatched, borrowed toolchain.
#   * `ninja` and `nvcc` resolved through the system PATH to the cluster's shared Anaconda
#     copies, which are not executable by us (the venv has had its own all along);
#   * the venv was not a coherent environment at all but a MIXED CUDA --
#       nvidia-cuda-nvcc 13.4.92, nvidia-cuda-crt 13.4.92, nvidia-cuda-cccl 13.3.4.3.1,
#       nvidia-cuda-runtime 13.0.96, torch cu130
#     and FlashInfer's cuda_toolkit.h guard exists to catch exactly that:
#     "CUDA compiler and CUDA toolkit headers are incompatible, please check your include paths"
#
# So the fix is OURS, at the root: the compiler trio pinned to 13.0.88/13.0.85 so the whole
# stack agrees with the 13.0 runtime and torch's cu130. No server flag could have fixed this;
# a flag could only route around the code path that noticed. Then the launch command is the
# competition's, unmodified.
set -u
S=/scratch/pabitra/gemma4comp
V=$S/venv
N=$V/lib/python3.11/site-packages/nvidia/cu13   # our toolchain, now pinned coherent at 13.0
H=$S/cuda_home                                  # a REAL toolkit layout built from those wheels
M=$S/model_hf
PORT=${PORT:-8000}               # override per job so two servers can share a node

export HF_HOME=$S/hf_cache TMPDIR=$S/tmp OUTLINES_CACHE_DIR=$S/outlines
export VLLM_CACHE_ROOT=$S/vllm_cache TRITON_CACHE_DIR=$S/triton_cache
export FLASHINFER_WORKSPACE_BASE=$S/flashinfer
mkdir -p "$TMPDIR" "$OUTLINES_CACHE_DIR" "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$FLASHINFER_WORKSPACE_BASE"
# pip's nvidia wheels are not a toolkit: `nvidia/cu13/lib` with versioned sonames only, so
# anything building against CUDA normally fails with `ld: cannot find -lcudart` / `-lcuda`.
# make_cuda_home.sh assembles bin/include/lib64 with the unversioned link names, and it runs
# HERE rather than at submit time because -lcuda resolves against the node's DRIVER, which
# exists on a GPU node and not on the login node.
bash "$S/make_cuda_home.sh"
# Ours first: the venv's ninja, then our pinned nvcc. Nothing borrowed from the cluster.
export PATH="$V/bin:$N/bin:$PATH"
export CUDA_HOME="$H"
export LIBRARY_PATH="$H/lib64${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="$H/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# FlashInfer caches a failed build; a stale cache from the 13.4 attempts would fail again for a
# reason that no longer exists.
rm -rf "$FLASHINFER_WORKSPACE_BASE/.cache"

echo "===== node: $(hostname)   started: $(date) ====="
nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv,noheader
echo "----- our toolchain, not the cluster's -----"
for t in ninja nvcc gcc; do printf "%-6s %s\n" "$t" "$(command -v $t || echo MISSING)"; done
nvcc --version | tail -2

# A previous tenant's dying process can still hold the card. vLLM then fails with
# "Free memory on device cuda:0 (10.94/139.8 GiB) ... less than desired GPU memory
# utilization", which is what made rung 2 of job 392756 fail for a reason that had nothing to
# do with its own configuration. Wait for the card instead of misreading the result.
for i in $(seq 1 60); do
  # The card THIS server will use: under serve_train.sbatch a second server runs on GPU 1 while
  # GPU 0 is busy serving, and checking "the first GPU" made it wait 10 minutes for nothing.
  used=$(nvidia-smi -i "${CUDA_VISIBLE_DEVICES%%,*}" --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null \
         || nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  [ "$used" -lt 2000 ] && break
  echo "waiting for the GPU: ${used} MiB still in use (${i}/60)"; sleep 10
done

# The beacon carries the JOB ID. An unstamped one outlived its cancelled job and a poller
# read it as "this job is up" while this job was still PENDING -- a readiness file that
# reports the wrong job is worse than none, which is the same lesson as the rest of this file.
READY=$S/serve_ready_${SLURM_JOB_ID}.txt
rm -f "$READY"
echo "$(hostname) $PORT" > "$S/serve_endpoint.txt"

# The competition's configuration, verbatim from HARNESS_README:198 -- tool_call_parser=gemma4,
# reasoning_parser=gemma4, enable_auto_tool_choice, max_model_len=32768, the model alias, and
# default_chat_template_kwargs={'enable_thinking': True}. That last one was missing from the
# first clean launch, and it is not cosmetic: without it the server defaults thinking OFF while
# the grader's defaults ON, and ADK never sends thinking_config, so every local run measured a
# different model behaviour from the one Kaggle scores.
# enable_lora / max_loras 8 / max_lora_rank 128 are the grader's too (README 3.1): LoRA-enabled
# serving takes a different kernel path even with no adapter loaded, and our own adapters are
# served exactly as the grader would, via LORA_MODULES="name=/path/to/adapter ...". Several adapters
# may be joined with "+" (a=/p/a+b=/p/b): the keeper passes LORA_MODULES inside one sbatch --export word.
# tensor-parallel-size is 1 rather than their 4 because the 23 GB W4A16 checkpoint fits one
# card; that divergence is recorded in localeval/README.md.
"$V/bin/vllm" serve \
    --model "$M" --served-model-name gemma-4-31b-it-qat-w4a16-ct \
    --host 0.0.0.0 --port $PORT \
    --max-model-len 32768 --tensor-parallel-size 1 --trust-remote-code \
    --enable-auto-tool-choice --tool-call-parser gemma4 --reasoning-parser gemma4 \
    --default-chat-template-kwargs '{"enable_thinking": true}' \
    --enable-lora --max-loras 8 --max-lora-rank 128 \
    ${LORA_MODULES:+--lora-modules ${LORA_MODULES//+/ }} &
PID=$!

# READINESS IS NOT LIVENESS. Job 391172 answered /v1/models for twenty minutes and then died
# on its first real generation, and the beacon had already declared it up. The gate is a tool
# call, because that is what the agent actually needs and what the parsers-off rung could not do.
for i in $(seq 1 150); do
  kill -0 $PID 2>/dev/null || { echo "!!! server exited during startup"; wait $PID; exit 1; }
  curl -sf "http://127.0.0.1:$PORT/v1/models" -o /dev/null 2>/dev/null && break
  sleep 10
done
echo "--- /v1/models answers; gating on a real TOOL CALL ---"
BODY=$(curl -s --max-time 300 "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"model":"gemma-4-31b-it-qat-w4a16-ct",
       "messages":[{"role":"user","content":"Read the file app/main.py using the read_file tool."}],
       "tools":[{"type":"function","function":{"name":"read_file","description":"Read a file",
         "parameters":{"type":"object","properties":{"filepath":{"type":"string"}},"required":["filepath"]}}}],
       "tool_choice":"auto","max_tokens":128,"temperature":0}')
echo "$BODY" | head -c 900; echo
if ! echo "$BODY" | grep -q '"choices"'; then
  echo "!!! tool-calling generation FAILED -- not a usable server"
  kill $PID 2>/dev/null; wait $PID 2>/dev/null; exit 1
fi
echo "$(hostname) $PORT $(date)" > "$READY"
echo "===== ACCEPTED: tool-calling generation works. serving. ====="
wait $PID
