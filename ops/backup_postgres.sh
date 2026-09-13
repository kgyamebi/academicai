#!/usr/bin/env bash
set -euo pipefail
# Physical-ish logical backup. Pair with provider PITR (RDS/Neon/Cloud SQL).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
notify_fail() {
  local msg="$1"
  echo "backup failed: $msg" >&2
  if [[ -n "${ALERT_WEBHOOK_URL:-}${ALERT_SINK_FILE:-}" ]]; then
    (cd "$ROOT/backend" && ALERT_BACKUP_ERROR="$msg" PYTHONPATH=. python -c \
      'from app.core.alerting import notify_backup_failure; import os; notify_backup_failure(error=os.environ.get("ALERT_BACKUP_ERROR","backup failed"))') || true
  fi
}
trap 'notify_fail "backup_postgres.sh exited nonzero"' ERR

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT=${BACKUP_DIR:-./backups}/academiccheck-${STAMP}.sql.gz
mkdir -p "$(dirname "$OUT")"
if [[ -z "${DATABASE_URL:-}" ]]; then
  notify_fail "DATABASE_URL is not set"
  exit 1
fi
pg_dump "$DATABASE_URL" | gzip > "$OUT"
echo "wrote $OUT"
# Optional at-rest encryption (AES-256-GCM). Requires BACKUP_ENCRYPTION_KEY.
if [[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]]; then
  ENC_OUT="${OUT}.enc"
  python "$ROOT/ops/encrypt_backup_file.py" "$OUT" "$ENC_OUT"
  rm -f "$OUT"
  OUT="$ENC_OUT"
  echo "wrote $OUT"
fi
# Keep 14 daily files locally (gz or enc). Object-store copies are the recovery source of truth.
ls -1t "$(dirname "$OUT")"/academiccheck-*.sql.gz* 2>/dev/null | tail -n +15 | xargs -r rm -- || true
