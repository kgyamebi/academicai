// k6 harness. Results are only valid when pointed at a real staging URL.
// k6 run -e BASE_URL=https://staging.example -e PROFILE=100 ops/load_test.js
import http from "k6/http";
import { check, sleep } from "k6";

const profiles = {
  smoke: { executor: "constant-vus", vus: 5, duration: "30s" },
  100: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "1m", target: 100 }, { duration: "2m", target: 100 }] },
  1000: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "2m", target: 1000 }, { duration: "3m", target: 1000 }] },
  5000: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "3m", target: 5000 }, { duration: "3m", target: 5000 }] },
  10000: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "4m", target: 10000 }, { duration: "3m", target: 10000 }] },
};

const chosen = __ENV.PROFILE || "smoke";

export const options = {
  scenarios: {
    [chosen]: profiles[chosen] || profiles.smoke,
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export default function () {
  const base = __ENV.BASE_URL || "http://127.0.0.1:8000";
  const live = http.get(`${base}/api/live`);
  check(live, { "live is 200": (r) => r.status === 200 });
  const ready = http.get(`${base}/api/ready`);
  check(ready, { "ready is 200 or 503": (r) => r.status === 200 || r.status === 503 });
  sleep(1);
}
