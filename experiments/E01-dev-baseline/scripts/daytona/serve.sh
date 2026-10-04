#!/usr/bin/env bash
# serve.sh NAME   vLLM 0.30.0 for /workspace/models/NAME, served as NAME, with the flags `zendo_bench serve-plan`
# gives for a Qwen 27B FP8 model on one H100 (prefix caching off, KV in the model dtype, 73,728-token context).
# Log: /workspace/e01/logs/vllm-serve.log
set -uo pipefail
NAME=${1:?NAME}
cd /workspace/e01
export OMP_NUM_THREADS=8
# FlashInfer JIT (FP8 block-scale GEMM, GDN prefill) runs ninja and nvcc: the venv's bin and CUDA on PATH.
export PATH=/workspace/venv/bin:/usr/local/cuda/bin:$PATH CUDA_HOME=/usr/local/cuda MAX_JOBS=16
echo "[$(date -u +%FT%TZ)] serve start $NAME" >> logs/vllm-serve.log
exec /workspace/venv/bin/vllm serve /workspace/models/$NAME \
  --served-model-name $NAME \
  --language-model-only \
  --kv-cache-dtype auto \
  --max-model-len 73728 \
  --max-num-seqs 32 \
  --max-cudagraph-capture-size 32 \
  --max-num-batched-tokens 8192 \
  --gpu-memory-utilization 0.92 \
  --no-enable-prefix-caching \
  --reasoning-parser qwen3 \
  --port 8000 >> logs/vllm-serve.log 2>&1
