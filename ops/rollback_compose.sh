#!/usr/bin/env bash
# Compose rollback helper. Does NOT prove blue/green or cloud LB.
# Usage: ./ops/rollback_compose.sh <previous_image_tag>
set -euo pipefail
TAG="${1:-}"
if [[ -z "$TAG" ]]; then
  echo "usage: $0 <previous_image_tag>" >&2
  exit 1
fi
if [[ ! -f docker-compose.prod.yml ]]; then
  echo "run from repository root" >&2
  exit 1
fi
export API_IMAGE_TAG="$TAG"
echo "Rolling api/worker to tag $TAG (compose recreate). Verify /api/ready afterwards."
docker compose -f docker-compose.prod.yml up -d --no-deps --force-recreate api worker
curl -fsS "${HEALTH_URL:-http://127.0.0.1:8000/api/ready}" || {
  echo "ready check failed after rollback — investigate before taking traffic" >&2
  exit 2
}
echo "rollback compose complete"
