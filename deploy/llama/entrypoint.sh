#!/bin/sh
# Start llama.cpp OpenAI-compatible server for Cloud Run.
# Secrets: LLAMA_API_KEY (required in production).
set -eu

MODEL_PATH="${MODEL_PATH:-/models/model.gguf}"
MODEL_ALIAS="${MODEL_ALIAS:-llama-3.2-1b-instruct}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"
THREADS="${LLAMA_THREADS:-4}"
CTX_SIZE="${LLAMA_CTX_SIZE:-2048}"

if [ ! -f "$MODEL_PATH" ]; then
  echo "ERROR: model file missing at $MODEL_PATH" >&2
  exit 1
fi

if [ -z "${LLAMA_API_KEY:-}" ]; then
  echo "WARNING: LLAMA_API_KEY is empty; server will accept unauthenticated requests." >&2
fi

if command -v llama-server >/dev/null 2>&1; then
  BIN="llama-server"
elif [ -x /app/llama-server ]; then
  BIN="/app/llama-server"
elif [ -x /llama-server ]; then
  BIN="/llama-server"
else
  echo "ERROR: llama-server binary not found in image" >&2
  exit 1
fi

if [ -n "${LLAMA_API_KEY:-}" ]; then
  exec "$BIN" \
    -m "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --alias "$MODEL_ALIAS" \
    --threads "$THREADS" \
    -c "$CTX_SIZE" \
    --api-key "$LLAMA_API_KEY" \
    "$@"
fi

exec "$BIN" \
  -m "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --alias "$MODEL_ALIAS" \
  --threads "$THREADS" \
  -c "$CTX_SIZE" \
  "$@"
