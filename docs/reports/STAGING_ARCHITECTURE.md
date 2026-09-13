# Staging architecture

```
                 STAGING_WEB_URL (:3000)
                         |
                      [web/Next]
                         |
                 STAGING_URL (:8000)
                    [api/uvicorn]
                   /      |      \
            [postgres] [redis] [worker/RQ]
                 |         |
              volume     AOF volume
                         |
                   [storage volume]
```

Optional TLS: `ops/docker-compose.tls.yml` terminates HTTPS on `:8443` to host API.

## Environment inventory

| Service | Image / build | Port | Persistence |
| --- | --- | --- | --- |
| postgres | postgres:16 | 55434 | staging_pg |
| redis | redis:7-alpine AOF | 56380 | staging_redis |
| api | backend Dockerfile | 8000 | — |
| worker | backend Dockerfile | — | shared storage |
| web | frontend Dockerfile | 3000 | — |

## Validation checklist

1. `docker compose -f docker-compose.staging.yml up -d --build`
2. `curl -sf $STAGING_URL/api/live`
3. `curl -sf $STAGING_URL/api/ready` → database, redis true, workers≥1
4. Set `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN`; run probe
5. `python ops/validate_public_launch.py`
