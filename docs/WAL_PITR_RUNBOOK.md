# WAL / PITR runbook — AcademicCheck AI

See `ops/PITR.md` for the full local engine drill and managed-provider steps.

Proven locally (2026-09-09): `ops/cert_wal_pitr.json` — two consecutive restores to a timestamp **between** two commits (row A kept, row B absent). Managed PITR remains pending a live account.
