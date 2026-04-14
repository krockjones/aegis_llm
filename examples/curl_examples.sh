#!/usr/bin/env bash
# Examples: AegisLLM Guard on http://127.0.0.1:8765 with Ollama behind it.
set -euo pipefail
BASE="${AEGISLLM_EXAMPLE_BASE:-http://127.0.0.1:8765}"

curl -sS "${BASE}/healthz" | jq .
curl -sS "${BASE}/readyz" | jq .
curl -sS "${BASE}/v1/models" | jq .
curl -sS "${BASE}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","messages":[{"role":"user","content":"Say hi in one word."}],"stream":false}' | jq .

EMBED_MODEL="${AEGISLLM_EXAMPLE_EMBED_MODEL:-nomic-embed-text}"
curl -sS "${BASE}/v1/embeddings" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${EMBED_MODEL}\",\"input\":\"hello embeddings\"}" | jq .
