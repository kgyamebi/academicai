# Performance certification

Status: **partially measured; unproven at the requested scales.**  
Scalability score: **60 / 100.** Gate 98. **Fail.**

Measured on this host:

- SQLite assignment list at 100k rows: p95 0.886 ms
- SQLite findings page at 500k rows: p95 1.0 ms
- Live uvicorn `GET /api/live`: p95 7.6 ms sequential; **281.7 ms** at 50 in-flight (under 500 ms); **1208.4 ms** at 100 in-flight (over 500 ms)

`ops/load_test.js` is a k6 harness with profiles `smoke`, `100`, `1000`, `5000`, `10000` and a `p(95)<500` threshold. It is not a 100 / 1,000 / 10,000 user result until `k6 run` is pointed at a staging cluster and the raw output is attached to `docs/LOAD_TEST_RESULTS.md`.

Full certificate: `docs/SCALABILITY_CERTIFICATION.md`.
