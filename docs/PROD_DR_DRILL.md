# Production backup & restore drill — AcademicCheck AI

Date: 2026-09-09  
Status: **AWAITING HUMAN OPERATOR** — scripts are ready; production credentials and the live dump/restore have **not** been executed in this environment.

Database engine: **PostgreSQL**. Dump tool: `pg_dump` (custom format preferred; gzip SQL is the other supported path — do not mix restore tools).

## Absolute safety rules (read before any command)

1. **Never restore into live production.** Restore target = isolated Docker on `127.0.0.1:55433` only.
2. Backup is **read-only** against production: `pg_dump` + `SELECT` under read-only session.
3. Prefer a **read-only Postgres role** for `PROD_DATABASE_URL`.
4. Do not commit dumps, manifests with PII, or passwords.
5. If **any** check in a STOP IF box fails: **stop**, do not continue, tear down isolated target, unset env vars.

Safety contract tests (no prod creds): `backend/tests/test_prod_dr_safety.py`.

---

## Abort / rollback

| When | What to do |
| --- | --- |
| Step B dump fails or dump size is 0 | Do **not** start restore. Fix credentials. Primary is untouched. |
| Isolated Postgres does not print `ISOLATED_TARGET_READY` | `bash ops/prod_dr_restore_target.sh down`. Stop. |
| `prod_dr_restore.sh` refuses the URL | **Good** — it blocked a prod-looking host. Do not override. |
| Manifest verify FAIL | Keep isolated container for forensics; **do not** point DNS or app at it as production. Then `down`. |
| You typed a production hostname into `RESTORE_DATABASE_URL` | Unset it. Run `down`. Do not proceed. |
| Mid-drill panic | `bash ops/prod_dr_restore_target.sh down` then `unset PROD_DATABASE_URL RESTORE_DATABASE_URL PROD_DR_VERIFY_PASSWORD`. Production was not written to by these scripts. |

There is **no** production rollback because these scripts must not write production. If you used any other tool against prod, this drill is void — page incident response.

---

## HUMAN OPERATOR — exact command sequence

Run from a machine that can reach production Postgres **and** has Docker + `pg_dump`/`psql` (Linux, macOS, or WSL/Git Bash). Low-traffic window recommended. Working directory = repository root.

### Step A — Review

```bash
less ops/prod_dr_backup.sh
less ops/prod_dr_restore.sh
less ops/docker-compose.dr-restore.yml
less ops/prod_dr_guards.py
```

**STOP IF** you do not understand: backup only reads prod; restore only writes to localhost isolated DB.

### Step B — Production backup (read-only)

```bash
cd /path/to/aiessayassignmentchecker

# READ-ONLY role. Never commit this URL.
export PROD_DATABASE_URL='postgresql://READONLY_USER:PASSWORD@PROD_HOST:5432/academiccheck'
export BACKUP_DIR=./backups/prod-dr

bash ops/prod_dr_backup.sh
```

**STOP IF** the script exits non-zero.

```bash
ls -lh backups/prod-dr/academiccheck-prod-*.sql.gz
# STOP IF size is 0 or missing
cat backups/prod-dr/academiccheck-prod-*.manifest.json | head
cat backups/prod-dr/academiccheck-prod-*.timing.json
```

| Field | Value |
| --- | --- |
| Operator name | _pending_ |
| UTC start | _pending_ |
| Dump path | _pending_ |
| Dump bytes | _pending_ |
| Backup total seconds | _pending_ |
| Manifest users / payments / assignments | _pending_ |

### Step C — Isolated restore target (no prod creds)

```bash
bash ops/prod_dr_restore_target.sh up
# STOP IF output is not ISOLATED_TARGET_READY
export RESTORE_DATABASE_URL='postgresql://dr_restore:dr_restore_only@127.0.0.1:55433/academiccheck_restore'
```

**STOP IF** `RESTORE_DATABASE_URL` equals `PROD_DATABASE_URL` or contains `rds.amazonaws.com` / `neon.tech` / production hostnames.

### Step D — Restore into isolated instance

```bash
export CONFIRM_ISOLATED_RESTORE=I_UNDERSTAND_THIS_IS_NOT_PRODUCTION
# Keep RESTORE_DATABASE_URL from Step C

bash ops/prod_dr_restore.sh backups/prod-dr/academiccheck-prod-STAMP.sql.gz
```

Replace `STAMP` with the filename from Step B. **STOP IF** restore seconds are missing or the script errors.

| Field | Value |
| --- | --- |
| Restore seconds | _pending_ |
| Timing file | _pending_ |

### Step E — Verification

```bash
py -3.14 ops/prod_dr_verify.py \
  --manifest backups/prod-dr/academiccheck-prod-STAMP.manifest.json \
  --database-url "$RESTORE_DATABASE_URL" \
  --out ops/cert_prod_dr_verify.json
```

**STOP IF** the JSON `pass` is not true. Do not continue to login checks.

Optional app against isolated DB only:

```bash
# Terminal 1
bash ops/prod_dr_app_against_restore.sh
# Terminal 2
export PROD_DR_APP_BASE_URL=http://127.0.0.1:18000
export PROD_DR_VERIFY_EMAIL='you@example.com'
export PROD_DR_VERIFY_PASSWORD='...'
py -3.14 ops/prod_dr_verify.py \
  --manifest backups/prod-dr/academiccheck-prod-STAMP.manifest.json \
  --database-url "$RESTORE_DATABASE_URL" \
  --app-base-url "$PROD_DR_APP_BASE_URL" \
  --require-login \
  --out ops/cert_prod_dr_verify.json
```

| Field | Value |
| --- | --- |
| Verify verdict | **PENDING** |
| Evidence file | `ops/cert_prod_dr_verify.json` (after run) |

### Step F — Destroy isolated target

```bash
bash ops/prod_dr_restore_target.sh down
unset PROD_DATABASE_URL RESTORE_DATABASE_URL PROD_DR_VERIFY_PASSWORD CONFIRM_ISOLATED_RESTORE
```

Confirm: `docker ps` shows **no** `academiccheck-dr-restore`.

---

## RPO / RTO (fill after human run)

| Metric | Local cert (not prod) | After this prod drill |
| --- | --- | --- |
| Backup method | Host `pg_dump` custom | _pending_ |
| Local restore RTO | 43.3 s / 43.1 s (`ops/cert_host_restore.json`) | _pending_ |
| **RPO** | Last dump unless managed PITR | _pending_ |
| Adequate for paying customers? | **Not until this human drill + managed PITR** | _pending_ |

Local Docker drills are **not** a production certificate.

---

## Script inventory

| Path | Touches production? | Writes where? |
| --- | --- | --- |
| `ops/prod_dr_guards.py` | No (URL policy) | stderr |
| `ops/prod_dr_backup.sh` | Read-only `pg_dump` + SELECT | Local `BACKUP_DIR` |
| `ops/prod_dr_manifest.py` | Read-only | Local JSON |
| `ops/prod_dr_restore_target.sh` | No | Local Docker volume |
| `ops/prod_dr_restore.sh` | No (refuses prod hosts) | Isolated DB only |
| `ops/prod_dr_verify.py` | No (refuses prod hosts by default) | Local JSON |
| `ops/export_backup_host.py` | Cert Docker only | `backups/host/` |

When Steps B–E complete, paste timing JSON + verify verdict and set Status to **PASS** or **FAIL** (never soften a mismatch).
