# Deployment Certification

Date: 2026-09-07  
Artifact: `ops/cert_bluegreen_results.json`

Local edge proxy `127.0.0.1:8030` switched between blue `:8031` and green `:8032`.

| Check | Result |
| --- | --- |
| Green switch 200s | 20/20 |
| Kill green | process killed |
| Automatic rollback to blue | **true** |
| Blue 200s after rollback | 30 |
| Errors after rollback | 0 |
| Nginx / Traefik / cloud LB | **Not run** |
| Kubernetes | **Not run** |
| Canary percent | **Not run** |
| Migration rollback | **Not run** |

`pass: true` for **this workstation proxy**. It is not a production blue-green environment.

Go-live “Blue-Green Deployment = PASS” on managed infrastructure: **FAIL**.
