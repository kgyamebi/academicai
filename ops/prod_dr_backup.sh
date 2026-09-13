#!/usr/bin/env bash
# =============================================================================
# ops/prod_dr_backup.sh — PRODUCTION READ-ONLY BACKUP + MANIFEST
# =============================================================================
#
# SAFETY (read this before running):
#   - Touches production ONLY via pg_dump and read-only SELECT queries.
#   - NEVER runs INSERT/UPDATE/DELETE/DDL against the source database.
#   - NEVER points at a "restore" URL. This script only WRITES local files under
#     BACKUP_DIR (default: ./backups/prod-dr/).
#   - Prefer a PostgreSQL role with SELECT + CONNECT only (no write privileges).
#
# HUMAN OPERATOR: You must supply real production credentials yourself.
#   Do NOT paste production passwords into git, CI, or chat.
#
# Usage (human, low-traffic window):
#   export PROD_DATABASE_URL='postgresql://readonly_user:...@prod-host:5432/academiccheck'
#   export BACKUP_DIR=./backups/prod-dr
#   bash ops/prod_dr_backup.sh
#
# Outputs:
#   $BACKUP_DIR/academiccheck-prod-<stamp>.sql.gz
#   $BACKUP_DIR/academiccheck-prod-<stamp>.manifest.json
#   $BACKUP_DIR/academiccheck-prod-<stamp>.timing.json
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups/prod-dr}"
mkdir -p "$BACKUP_DIR"

URL="${PROD_DATABASE_URL:-${DATABASE_URL:-}}"
if [[ -z "$URL" ]]; then
  echo "FATAL: set PROD_DATABASE_URL (preferred) or DATABASE_URL to the production DSN." >&2
  exit 2
fi
export PROD_DATABASE_URL="$URL"
# Shared guard (also unit-tested without requiring bash/WSL).
python "$ROOT/ops/prod_dr_guards.py" backup

DUMP="$BACKUP_DIR/academiccheck-prod-${STAMP}.sql.gz"
MANIFEST="$BACKUP_DIR/academiccheck-prod-${STAMP}.manifest.json"
TIMING="$BACKUP_DIR/academiccheck-prod-${STAMP}.timing.json"

echo "=== PROD DR BACKUP (read-only) ==="
echo "stamp=$STAMP"
echo "dump=$DUMP"
echo "manifest=$MANIFEST"
python - <<'PY'
import os
from urllib.parse import urlparse
u = urlparse(os.environ["PROD_DATABASE_URL"])
host = u.hostname or "unknown"
port = f":{u.port}" if u.port else ""
print(f"source_host={host}{port}/{ (u.path or '').lstrip('/') }")
PY

echo "--- capturing pre-dump manifest (SELECT only, READ ONLY session) ---"
export MANIFEST_DATABASE_URL="$URL"
export MANIFEST_OUT="$MANIFEST"
export MANIFEST_PHASE="pre_dump"
T0=$(date +%s)
(cd "$ROOT/backend" && PYTHONPATH=. python "$ROOT/ops/prod_dr_manifest.py")
T1=$(date +%s)

echo "--- pg_dump (read-only logical dump; no writes to source) ---"
T_DUMP0=$(date +%s)
pg_dump \
  --format=plain \
  --no-owner \
  --no-acl \
  --verbose \
  "$URL" | gzip -c > "$DUMP"
T_DUMP1=$(date +%s)

BYTES=$(wc -c < "$DUMP" | tr -d ' ')
echo "wrote dump bytes=$BYTES path=$DUMP"

if [[ "$BYTES" -lt 1000 ]]; then
  echo "FATAL: dump file suspiciously small ($BYTES bytes). Aborting." >&2
  exit 4
fi

export PROD_DR_STAMP="$STAMP"
export PROD_DR_DUMP="$DUMP"
export PROD_DR_MANIFEST="$MANIFEST"
export PROD_DR_TIMING="$TIMING"
export PROD_DR_BYTES="$BYTES"
export PROD_DR_T0="$T0"
export PROD_DR_T1="$T1"
export PROD_DR_DUMP0="$T_DUMP0"
export PROD_DR_DUMP1="$T_DUMP1"
python - <<'PY'
import json, os, time
from pathlib import Path
t0 = int(os.environ["PROD_DR_T0"])
t1 = int(os.environ["PROD_DR_T1"])
d0 = int(os.environ["PROD_DR_DUMP0"])
d1 = int(os.environ["PROD_DR_DUMP1"])
timing = {
  "stamp": os.environ["PROD_DR_STAMP"],
  "backup_started_unix": t0,
  "manifest_seconds": t1 - t0,
  "dump_seconds": d1 - d0,
  "backup_total_seconds": d1 - t0,
  "dump_bytes": int(os.environ["PROD_DR_BYTES"]),
  "dump_path": os.environ["PROD_DR_DUMP"],
  "manifest_path": os.environ["PROD_DR_MANIFEST"],
  "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "read_only_source": True,
  "writes_to_production": False,
}
Path(os.environ["PROD_DR_TIMING"]).write_text(json.dumps(timing, indent=2), encoding="utf-8")
print(json.dumps(timing, indent=2))
PY

echo "=== BACKUP COMPLETE — review dump size + manifest before restore ==="
echo "NEXT (human): bash ops/prod_dr_restore_target.sh up"
echo "THEN:       bash ops/prod_dr_restore.sh \"$DUMP\""
