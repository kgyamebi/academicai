#!/usr/bin/env bash
set -euo pipefail
# Physical-ish logical backup. Pair with provider PITR (RDS/Neon/Cloud SQL).
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT=${BACKUP_DIR:-./backups}/academiccheck-${STAMP}.sql.gz
mkdir -p "$(dirname "$OUT")"
pg_dump "$DATABASE_URL" | gzip > "$OUT"
echo "wrote $OUT"
# Keep 14 daily files locally; object-store copies are the recovery source of truth.
ls -1t "$(dirname "$OUT")"/academiccheck-*.sql.gz | tail -n +15 | xargs -r rm --
