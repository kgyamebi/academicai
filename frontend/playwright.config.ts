import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./a11y",
  testMatch: /.*\.spec\.ts/,
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "off",
  },
  webServer: [
    {
      command: "node a11y/start-api.mjs",
      url: "http://127.0.0.1:8010/api/live",
      reuseExistingServer: false,
      timeout: 180_000,
    },
    {
      command: "npx next dev --hostname 127.0.0.1 --port 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
      timeout: 180_000,
      env: {
        ...process.env,
        API_INTERNAL_URL: "http://127.0.0.1:8010",
        NEXT_PUBLIC_API_URL: "http://127.0.0.1:8010",
        NEXT_TELEMETRY_DISABLED: "1",
      },
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
