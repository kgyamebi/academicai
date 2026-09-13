#!/usr/bin/env bash
# Single-command staging-like deploy. Gates cutover on /api/ready.
# Usage (repo root):
#   COMPOSE_FILE=docker-compose.staging.yml bash ops/deploy_compose.sh
#   IMAGE_TAG=abc123 bash ops/deploy_compose.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.staging.yml}"
if [[ ! -f "$COMPOSE_FILE" ]]; then
  COMPOSE_FILE=docker-compose.prod.yml
fi
TAG="${IMAGE_TAG:-${1:-latest}}"
export API_IMAGE_TAG="$TAG"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/ready}"
LIVE_URL="${LIVE_URL:-http://127.0.0.1:8000/api/live}"

echo "deploy: compose=$COMPOSE_FILE tag=$TAG"
docker compose -f "$COMPOSE_FILE" up -d --build
echo "waiting for ready..."
ok=0
for i in $(seq 1 60); do
  if curl -fsS "$LIVE_URL" >/dev/null 2>&1 && curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 2
done
if [[ "$ok" != "1" ]]; then
  echo "FATAL: /api/live or /api/ready failed after deploy — refusing traffic cutover" >&2
  exit 2
fi
echo "deploy complete; ready gate passed"
