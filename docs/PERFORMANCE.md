# Performance certification

Status: **unproven at the requested scales**.

`ops/load_test.js` is a k6 smoke harness against `/api/live`. It is not a 100 / 1,000 / 10,000 / 50,000 user result.

Do not fill latency, CPU, memory, or queue tables until k6 (or equivalent) is pointed at a staging cluster and the raw output is attached.
