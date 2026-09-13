# Security Extended Hardening — AcademicCheck AI

Date: 2026-09-09  
Prior certified core (69 + 6 lab attacks, MFA/JWT/isolation/upload/prompt-injection/secrets) was **not re-run as new work**. This pass adds new surfaces and fixes the CI swallow bug.

## Score (honest)

Security remains **94 / 98**. This pass is code-proven. It does **not** close pentest, secret manager, live PSP, production ClamAV mandate, or live-domain TLS/SSL Labs.

## Step 0 — CI fail-closed (real bug, fixed)

`pip-audit || true` was removed from `.github/workflows/ci.yml`. Main CI now fails on any known pip-audit finding. Frontend `npm ci` is fail-closed (no `npm ci || npm install`). `npm audit --audit-level=high` is blocking. `security-scan.yml` Trivy filesystem scan exits 1 on HIGH/CRITICAL.

Evidence:

- `ops/cert_ci_security_gates.py` / `.json` — no swallowed pip-audit/npm-audit/trivy
- `ops/cert_pip_audit_failclosed.py` / `.json` — `jinja2==2.10` returns non-zero pip-audit; CI YAML no longer uses `|| true` on pip-audit
- Threshold: **any known OSV/CVE** (Python); **high+** (npm); **HIGH+** (Trivy)

`billing-reconcile.yml` still uses `|| true` on a **billing** reminder job (not a security scanner). Left as-is.

## Step 1 — SCA / SBOM / license / pins

- `backend/requirements.txt` and `frontend/package.json` are **exact pins** (`==` / no `^`).
- SBOM: `ops/generate_sbom.py` → CycloneDX-lite `ops/sbom.cdx.json`
- License allow-list: `ops/license_scan.py` (PyMuPDF AGPL called out as reviewed exception)
- Scheduled CVE check: `.github/workflows/security-scan.yml` (weekly + on lockfile changes)

## Step 2 — Malware scan (wired; mandate is a config flip)

Upload path: quarantine write → ClamAV INSTREAM → delete quarantine → reject or continue to storage.

- Compose: `ops/docker-compose.clamav.yml`
- Policy flip: `CLAMAV_REQUIRED=true` + `CLAMAV_HOST=...` (HAL-12)
- Pytest fake daemon: EICAR rejected, clean released, required-down fail-closed (`tests/test_malware_clamav.py`)
- Container drill: `ops/cert_clamav_eicar.py`

This is **fully wired**, not missing code. Making it mandatory in prod is config/ops once ClamAV is resourced.

## Step 3 — TLS / transport (app + local terminator)

- HSTS when `APP_ENV=production` (`tests/test_tls_transport.py`)
- TLS 1.2+ context: `app/core/tls.py`; local handshake `ops/cert_tls_local.py`
- Nginx modern protocols/ciphers: `ops/nginx/tls.conf` + `ops/docker-compose.tls.yml`

**Not proven:** production certificate chain, live hostname, SSL Labs. That remains the external TLS step.

## Step 4 — Container / infra

- Backend/frontend Dockerfiles: non-root `USER 10001`, slim/alpine, `npm ci`, `.dockerignore` excludes `.env`
- `docker-compose.prod.yml`: Postgres/Redis/PgBouncer **not** published to the host
- Static audit: `ops/cert_dockerfile_hardening.json`
- Trivy: CI job + `ops/cert_trivy.py`

## Step 5 — New adversarial tests (not the prior 6)

`tests/test_security_adversarial.py`: mass-assignment (`extra=forbid`), HTTP parameter pollution, no GraphQL, CSRF on cookie mutating POST, clickjacking CSP `frame-ancestors`, X-Forwarded-For rate-limit non-bypass, Hypothesis filename fuzz.

## Step 6 — Indirect prompt injection

`tests/test_prompt_injection_indirect.py`: document/citation payloads cannot skip citation verification, leak system prompt, or pull other tenants. `enhance_analysis` skips the model when untrusted corpus looks like injection.

## Step 7 — Secret rotation grace period

`FIELD_ENCRYPTION_KEY_PREVIOUS` / `BACKUP_ENCRYPTION_KEY_PREVIOUS`: decrypt old ciphertext, re-encrypt with current key (`tests/test_secret_rotation.py`). Cloud secret **manager** is still HAL-08.

## Remaining live/external items

See `docs/REMAINING_SECURITY_RISKS.md`. Only pentest, secret manager, live PSP, ClamAV **mandate**, and live-domain TLS proof still need an external party or live account. HAL-24 (CI pip-audit swallow) is **closed**.
