#!/usr/bin/env bash
# End-to-end smoke: Ollama + Guard from docker-compose.yml (same network as README).
# Usage (from repository root — directory containing docker-compose.yml):
#   bash scripts/smoke_compose.sh
# Keep containers running after success:
#   SMOKE_KEEP=1 bash scripts/smoke_compose.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BASE="${SMOKE_BASE:-http://127.0.0.1:8765}"
MAX_WAIT="${SMOKE_WAIT_SECS:-120}"

echo "==> docker compose up (--build)"
docker compose up -d --build

cleanup() {
  if [[ "${SMOKE_KEEP:-}" == "1" ]]; then
    echo "==> SMOKE_KEEP=1 — leaving containers up"
    return 0
  fi
  echo "==> docker compose down"
  docker compose down
}

trap cleanup EXIT

echo "==> wait for Guard /readyz (up to ${MAX_WAIT}s)"
ok=0
for ((i = 1; i <= MAX_WAIT; i++)); do
  if code="$(curl -sS -o /tmp/aegis_readyz.json -w '%{http_code}' "${BASE}/readyz" 2>/dev/null || true)"; then
    if [[ "$code" == "200" ]]; then
      echo "readyz HTTP $code"
      ok=1
      break
    fi
  fi
  sleep 1
done
if [[ "$ok" != "1" ]]; then
  echo "timeout: Guard /readyz did not return 200" >&2
  docker compose logs --tail 80
  exit 1
fi

echo "==> GET /v1/models (JSON + disclosure headers)"
curl -fsS -o /tmp/aegis_models.json -D /tmp/aegis_models.hdr "${BASE}/v1/models"
grep -qi '^X-AegisLLM-Backend:' /tmp/aegis_models.hdr
grep -qi '^X-AegisLLM-Upstream-Base:' /tmp/aegis_models.hdr
python3 -c "import json; json.load(open('/tmp/aegis_models.json'))"
echo "models JSON ok"

echo "==> POST /v1/chat/completions (stream, optional if models list non-empty)"
python3 - "$BASE" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base = sys.argv[1].rstrip("/")

try:
    with open("/tmp/aegis_models.json", encoding="utf-8") as f:
        models_doc = json.load(f)
except OSError as exc:
    print(f"stream smoke skipped: cannot read models json ({exc})")
    sys.exit(0)

rows = models_doc.get("data") or []
if not rows:
    print("stream smoke skipped: empty models data[]")
    sys.exit(0)

model = rows[0]["id"]
body = json.dumps(
    {
        "model": model,
        "messages": [{"role": "user", "content": "Say hi in a few words."}],
        "stream": True,
    }
).encode("utf-8")
req = urllib.request.Request(
    f"{base}/v1/chat/completions",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = resp.read()
except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")[:800]
    print(f"stream smoke failed: HTTP {exc.code} {detail}", file=sys.stderr)
    sys.exit(1)

text = raw.decode("utf-8", errors="replace")
if "chat.completion.chunk" not in text or "[DONE]" not in text:
    print("stream smoke failed: expected chat.completion.chunk and [DONE] in body", file=sys.stderr)
    sys.stderr.write(text[:2000])
    sys.stderr.write("\n")
    sys.exit(1)
print("stream body ok (chunk markers + [DONE])")
PY

echo "==> smoke_compose OK"
