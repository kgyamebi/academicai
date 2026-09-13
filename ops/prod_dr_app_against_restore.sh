#!/usr/bin/env bash
# Optional: run API against the ISOLATED restore DB for functional read checks.
# NEVER point this at production.
#
# Usage (after restore):
#   export RESTORE_DATABASE_URL=postgresql://dr_restore:dr_restore_only@127.0.0.1:55433/academiccheck_restore
#   bash ops/prod_dr_app_against_restore.sh
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -z "${RESTORE_DATABASE_URL:-}" ]]; then
  echo "FATAL: RESTORE_DATABASE_URL required" >&2
  exit 2
fi
case "$RESTORE_DATABASE_URL" in
  *127.0.0.1*|*localhost*) ;;
  *)
    echo "FATAL: app-against-restore only allows localhost restore targets" >&2
    exit 3
    ;;
esac

# Convert to SQLAlchemy URL if needed
DB_URL="$RESTORE_DATABASE_URL"
if [[ "$DB_URL" == postgresql://* ]]; then
  DB_URL="postgresql+psycopg://${DB_URL#postgresql://}"
fi

export DATABASE_URL="$DB_URL"
export APP_ENV="${APP_ENV:-development}"
export REQUIRE_QUEUE="${REQUIRE_QUEUE:-false}"
export COOKIE_SECURE="${COOKIE_SECURE:-false}"
PORT="${PROD_DR_APP_PORT:-18000}"

echo "Starting API on 127.0.0.1:$PORT against ISOLATED restore DB only"
cd "$ROOT/backend"
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
