#!/bin/sh
set -e
# Allow the replica to stream WAL from this primary.
echo "host replication academiccheck 0.0.0.0/0 md5" >> "${PGDATA}/pg_hba.conf"
echo "host replication academiccheck ::0/0 md5" >> "${PGDATA}/pg_hba.conf"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
ALTER USER academiccheck WITH REPLICATION;
SQL
