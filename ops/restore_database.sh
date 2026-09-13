#!/usr/bin/env bash
set -euo pipefail
# restore_database.sh — operator entrypoint for logical restore into a SCRATCH DB only.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DUMP="${1:-}"
if [[ -z "$DUMP" || -z "${RESTORE_DATABASE_URL:-}" ]]; then
  echo "usage: RESTORE_DATABASE_URL=postgresql://... CONFIRM_ISOLATED_RESTORE=I_UNDERSTAND_THIS_IS_NOT_PRODUCTION $0 path/to/dump.sql.gz" >&2
  exit 1
fi
python "$ROOT/ops/prod_dr_guards.py" restore
exec "$ROOT/ops/restore_postgres.sh" "$DUMP"
