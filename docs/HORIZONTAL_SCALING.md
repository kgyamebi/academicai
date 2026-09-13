# Horizontal Scaling Report

Date: 2026-09-06  
Instances measured: **1** uvicorn (`127.0.0.1:8011`)  
Load balancer: **none**

## Instance matrix

| Instances | Throughput | p95 | Error rate | Status |
| ---: | --- | --- | --- | --- |
| 1 | `/api/live` only | see `docs/LOAD_TEST_RESULTS.md` | 0% on health | Measured |
| 2 | — | — | — | **Not run** |
| 5 | — | — | — | **Not run** |
| 10 | — | — | — | **Not run** |
| 50 | — | — | — | **Not run** |

## Stateless audit (source)

| Dependency | Local state? | Risk |
| --- | --- | --- |
| JWT / cookies | No (shared secret) | Secret must be identical on every replica |
| SQLAlchemy session | Per-request | OK if all replicas share Postgres |
| Prompt cache | **Yes — process memory** | Duplicate LLM calls across replicas |
| `/api/metrics` histogram | **Yes — process memory** | Must scrape every replica |
| Uploads | Local disk if S3 unset | Hidden sticky-node dependency |
| RQ job id | Redis | OK if all replicas share Redis |

Hidden local-state dependencies that remain: in-process AI cache, in-process metrics, optional local storage. They do not break correctness if every replica can reach Postgres + Redis + object storage, but they prevent a single-process cache-hit or metric from representing the cluster.

## Verdict

Horizontal scaling is **not demonstrated**. One process was measured. Compose `--workers 4` and replica counts are configuration, not a 2/5/10/50-instance result.
