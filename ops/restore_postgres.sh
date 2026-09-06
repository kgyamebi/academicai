#!/usr/bin/env bash
set -euo pipefail
# Restore a gzipped pg_dump into a scratch database. Never run against production primary without a ticket.
if [[ -z "${1:-}" || -z "${RESTORE_DATABASE_URL:-}" ]]; then
  echo "usage: RESTORE_DATABASE_URL=postgresql://... $0 backups/academiccheck-YYYYMMDD.sql.gz" >&2
  exit 1
fi
gunzip -c "$1" | psql "$RESTORE_DATABASE_URL"
echo "restored $1"
echo "verify: SELECT count(*) FROM users; SELECT count(*) FROM payments;"
