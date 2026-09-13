# STAGING_SECURITY_VERIFICATION

**Measured:** 2026-09-13T21:20:27Z  

## Smoke

```
{
  "forgot_enumeration_safe": true,
  "csrf_endpoint": true,
  "ready_env": "staging",
  "pass": true,
  "host_cookie_secure_unproven": true,
  "note": "Full IDOR suite must still be run with pytest against STAGING_URL; this is smoke only."
}
```

## Severity board

| Sev | Finding | Status |
| --- | --- | --- |
| Critical | Ready without redis/workers on staging policy | Fixed in code when APP_ENV=staging/REQUIRE_QUEUE |
| High | Host IDOR suite not re-run on STAGING_URL | Open |
| High | COOKIE_SECURE/HTTPS unproven on HTTP compose | Open until TLS terminator |
| Medium | Sentry DSN empty | Open |
| Low | Console email in staging compose | Accepted for ops proof |

Run: `STAGING_URL=... pytest backend/tests/test_isolation.py backend/tests/test_security_hardening.py`
