// Authenticated k6 load. Anonymous /api/live is not this profile.
// k6 run -e BASE_URL=http://127.0.0.1:18080 -e PROFILE=100 -e EMAIL=... -e PASSWORD=... ops/load_test_auth.js
import http from "k6/http";
import { check, sleep } from "k6";

const profiles = {
  100: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "30s", target: 100 }, { duration: "1m", target: 100 }] },
  1000: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "1m", target: 1000 }, { duration: "2m", target: 1000 }] },
  5000: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "2m", target: 5000 }, { duration: "2m", target: 5000 }] },
  10000: { executor: "ramping-vus", startVUs: 0, stages: [{ duration: "2m", target: 10000 }, { duration: "2m", target: 10000 }] },
};

const chosen = __ENV.PROFILE || "100";

export const options = {
  scenarios: {
    [chosen]: profiles[chosen] || profiles[100],
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export function setup() {
  const base = __ENV.BASE_URL || "http://127.0.0.1:18080";
  const email = __ENV.EMAIL;
  const password = __ENV.PASSWORD || "password12";
  const login = http.post(
    `${base}/api/auth/login`,
    JSON.stringify({ email, password }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (login.status !== 200) {
    throw new Error(`login failed ${login.status} ${login.body}`);
  }
  const token = login.json("access_token");
  return { base, token };
}

export default function (data) {
  const headers = { Authorization: `Bearer ${data.token}` };
  const dash = http.get(`${data.base}/api/dashboard`, { headers });
  check(dash, { "dashboard 200": (r) => r.status === 200 });
  const list = http.get(`${data.base}/api/assignments?page_size=20`, { headers });
  check(list, { "assignments 200": (r) => r.status === 200 });
  const faqs = http.get(`${data.base}/api/public/faqs`);
  check(faqs, { "faqs 200": (r) => r.status === 200 });
  sleep(0.5);
}
