#!/usr/bin/env bash
# =============================================================================
# ops/prod_dr_restore.sh — RESTORE DUMP INTO ISOLATED INSTANCE ONLY
# =============================================================================
#
# SAFETY (hard refusals):
#   - NEVER restores into production.
#   - Refuses managed-looking hosts (rds, neon, supabase, azure, cloudsql) always.
#   - Requires RESTORE_DATABASE_URL to be localhost/127.0.0.1 by default
#     (I_CONFIRM_NONLOCAL_ISOLATED=1 only for a dedicated non-prod offsite box
#     that is still NOT a managed prod hostname).
#   - Requires CONFIRM_ISOLATED_RESTORE=I_UNDERSTAND_THIS_IS_NOT_PRODUCTION
#   - Refuses if RESTORE_DATABASE_URL == PROD_DATABASE_URL.
#   - Does not open any connection to production.
#
# HUMAN OPERATOR:
#   export CONFIRM_ISOLATED_RESTORE=I_UNDERSTAND_THIS_IS_NOT_PRODUCTION
#   export RESTORE_DATABASE_URL=postgresql://dr_restore:dr_restore_only@127.0.0.1:55433/academiccheck_restore
#   bash ops/prod_dr_restore.sh backups/prod-dr/academiccheck-prod-XXXX.sql.gz
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DUMP="${1:-}"

if [[ -z "$DUMP" || -z "${RESTORE_DATABASE_URL:-}" ]]; then
  echo "usage: RESTORE_DATABASE_URL=... CONFIRM_ISOLATED_RESTORE=I_UNDERSTAND_THIS_IS_NOT_PRODUCTION $0 <dump.sql.gz>" >&2
  exit 2
fi

if [[ ! -f "$DUMP" ]]; then
  echo "FATAL: dump not found: $DUMP" >&2
  exit 2
fi

# Shared guard (also unit-tested without requiring bash/WSL).
python "$ROOT/ops/prod_dr_guards.py" restore

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TIMING_DIR="${BACKUP_DIR:-$(dirname "$DUMP")}"
TIMING="$TIMING_DIR/restore-timing-${STAMP}.json"
mkdir -p "$TIMING_DIR"

echo "=== PROD DR RESTORE (isolated only) ==="
echo "dump=$DUMP"
SAFE_URL=$(python -c "from urllib.parse import urlparse; u=urlparse('''$RESTORE_DATABASE_URL'''); print((u.hostname or '')+(':'+str(u.port) if u.port else ''))" 2>/dev/null || echo "redacted")
echo "target_host=$SAFE_URL"

T0=$(date +%s)
# Drop/recreate public schema objects via plain SQL dump replay.
# For a fresh empty DB this is enough; for reuse we wipe public first (isolated only).
psql "$RESTORE_DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO PUBLIC;
SQL

gunzip -c "$DUMP" | psql "$RESTORE_DATABASE_URL" -v ON_ERROR_STOP=1
T1=$(date +%s)

python - <<PY
import json, time
from pathlib import Path
timing = {
  "stamp": "$STAMP",
  "restore_seconds": $T1 - $T0,
  "dump_path": r"""$DUMP""",
  "target_host": """$SAFE_URL""",
  "writes_to_production": False,
  "isolated_target": True,
  "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
Path(r"""$TIMING""").write_text(json.dumps(timing, indent=2), encoding="utf-8")
print(json.dumps(timing, indent=2))
PY

echo "=== RESTORE COMPLETE ==="
echo "NEXT: py -3 ops/prod_dr_verify.py --manifest <pre.dump.manifest.json> --database-url \$RESTORE_DATABASE_URL"
