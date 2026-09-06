// k6 harness. Results are only valid when pointed at a real staging URL.
// k6 run -e BASE_URL=https://staging.example ops/load_test.js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    smoke: { executor: "constant-vus", vus: 5, duration: "30s" },
  },
};

export default function () {
  const base = __ENV.BASE_URL || "http://127.0.0.1:8000";
  const live = http.get(`${base}/api/live`);
  check(live, { "live is 200": (r) => r.status === 200 });
  sleep(1);
}
