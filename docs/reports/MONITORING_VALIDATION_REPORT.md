# MONITORING_VALIDATION_REPORT

**Measured:** 2026-09-13T21:20:27Z  

## Sentry probe

```
{
  "probe": {
    "ok": true,
    "status": 200,
    "json": {
      "ok": false,
      "sentry_armed": false,
      "detail": "SENTRY_DSN is empty."
    },
    "error": null
  },
  "dsn_configured": false,
  "pass": false,
  "note": "Pass requires SENTRY_DSN on the staging API and visible Issue in Sentry UI (manual confirm)."
}
```

## Pass criteria

1. `SENTRY_DSN` set on API + worker  
2. `NEXT_PUBLIC_SENTRY_DSN` set on web  
3. Probe returns `sentry_armed: true`  
4. Issue visible in Sentry project (manual evidence)

**Pass this run:** False
