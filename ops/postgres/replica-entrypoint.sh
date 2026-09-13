#!/bin/sh
set -eu
DATA=/var/lib/postgresql/data
export PGPASSWORD=academiccheck
if [ ! -f "$DATA/PG_VERSION" ]; then
  until pg_isready -h pg-primary -U academiccheck; do
    sleep 2
  done
  find "$DATA" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  pg_basebackup -h pg-primary -U academiccheck -D "$DATA" -Fp -Xs -P -R
  chmod 700 "$DATA"
fi
chmod 700 "$DATA" 2>/dev/null || true
exec postgres -c hot_standby=on -c max_connections=200 -c shared_buffers=256MB -c max_wal_senders=16 -c max_replication_slots=8
