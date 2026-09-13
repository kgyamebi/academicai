#!/usr/bin/env bash
# =============================================================================
# ops/prod_dr_restore_target.sh — START ISOLATED RESTORE DATABASE
# =============================================================================
#
# SAFETY:
#   - Creates a NEW local Postgres container (127.0.0.1:55433).
#   - Does NOT connect to production.
#   - Does NOT modify production.
#
# HUMAN or SCRIPT: Safe to run on an operator laptop / bastion without prod write access.
#
# Usage:
#   bash ops/prod_dr_restore_target.sh up
#   bash ops/prod_dr_restore_target.sh down   # destroy after drill
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE=("docker" "compose" "-f" "$ROOT/ops/docker-compose.dr-restore.yml")
ACTION="${1:-up}"

case "$ACTION" in
  up)
    "${COMPOSE[@]}" up -d
    echo "Waiting for health..."
    for i in $(seq 1 60); do
      if docker exec academiccheck-dr-restore pg_isready -U dr_restore -d academiccheck_restore >/dev/null 2>&1; then
        echo "ISOLATED_TARGET_READY"
        echo "RESTORE_DATABASE_URL=postgresql://dr_restore:dr_restore_only@127.0.0.1:55433/academiccheck_restore"
        exit 0
      fi
      sleep 1
    done
    echo "FATAL: isolated Postgres did not become ready" >&2
    exit 1
    ;;
  down)
    "${COMPOSE[@]}" down -v
    echo "ISOLATED_TARGET_DESTROYED"
    ;;
  *)
    echo "usage: $0 up|down" >&2
    exit 2
    ;;
esac
