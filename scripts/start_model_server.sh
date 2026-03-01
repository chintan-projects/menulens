#!/usr/bin/env bash
# Start llama-server with LFM2-8B-A1B for MenuLens extraction.
#
# Usage:
#   ./scripts/start_model_server.sh              # defaults
#   ./scripts/start_model_server.sh --port 8081  # custom port
#
# The server exposes an OpenAI-compatible API at http://localhost:8081/v1
# which the MenuLens extraction service connects to.

set -euo pipefail

# Resolve model path via shared MODELS_DIR (see ~/Projects/_models/config.yaml).
# Never store model binaries inside the project — use the workspace-level registry.
MODELS_DIR="${MODELS_DIR:-$HOME/Projects/_models}"
MODEL_PATH="${MODEL_PATH:-$MODELS_DIR/LFM2-8B-A1B-Q4_K_M.gguf}"
PORT="${PORT:-8081}"
HOST="${HOST:-127.0.0.1}"
CTX_SIZE="${CTX_SIZE:-8192}"
GPU_LAYERS="${GPU_LAYERS:-auto}"

if [ ! -f "$MODEL_PATH" ]; then
    echo "ERROR: Model file not found at $MODEL_PATH"
    echo ""
    echo "Download it to the shared model registry:"
    echo "  python -c \"from huggingface_hub import hf_hub_download; hf_hub_download('LiquidAI/LFM2-8B-A1B-GGUF', filename='LFM2-8B-A1B-Q4_K_M.gguf', local_dir='$MODELS_DIR')\""
    echo ""
    echo "Or set MODELS_DIR to point at your model directory:"
    echo "  MODELS_DIR=/path/to/models ./scripts/start_model_server.sh"
    exit 1
fi

echo "Starting llama-server..."
echo "  Model:      $MODEL_PATH"
echo "  Port:       $PORT"
echo "  Context:    $CTX_SIZE tokens"
echo "  GPU layers: $GPU_LAYERS"
echo ""
echo "API endpoint: http://$HOST:$PORT/v1/chat/completions"
echo ""

exec llama-server \
    --model "$MODEL_PATH" \
    --alias "lfm2-8b-a1b" \
    --host "$HOST" \
    --port "$PORT" \
    --ctx-size "$CTX_SIZE" \
    --n-gpu-layers "$GPU_LAYERS" \
    "$@"
