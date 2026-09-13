import { spawn, spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..", "backend");
const port = process.env.A11Y_API_PORT || "8010";

function findPython() {
  if (process.env.A11Y_PYTHON) return { bin: process.env.A11Y_PYTHON, extra: [] };
  const options =
    process.platform === "win32"
      ? [
          { bin: "py", extra: ["-3.14"] },
          { bin: "py", extra: ["-3"] },
          { bin: "python", extra: [] },
        ]
      : [
          { bin: "python3", extra: [] },
          { bin: "python", extra: [] },
        ];
  for (const option of options) {
    const check = spawnSync(option.bin, [...option.extra, "-c", "import uvicorn"], { encoding: "utf8" });
    if (check.status === 0) return option;
  }
  throw new Error("No Python interpreter with uvicorn was found for accessibility API startup.");
}

const python = findPython();
const child = spawn(
  python.bin,
  [...python.extra, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", port],
  {
    cwd: root,
    env: {
      ...process.env,
      APP_ENV: process.env.APP_ENV || "test",
      DATABASE_URL: process.env.DATABASE_URL || "sqlite:///./a11y_playwright.db",
      JWT_SECRET_KEY: process.env.JWT_SECRET_KEY || "a11y-jwt-secret-key-32-bytes-min",
      APP_SECRET_KEY: process.env.APP_SECRET_KEY || "a11y-app-secret",
      APP_CORS_ORIGINS: process.env.APP_CORS_ORIGINS || "http://127.0.0.1:3100,http://localhost:3100",
      ADMIN_BOOTSTRAP_EMAIL: process.env.ADMIN_BOOTSTRAP_EMAIL || "a11y-admin@example.com",
      ADMIN_BOOTSTRAP_PASSWORD: process.env.ADMIN_BOOTSTRAP_PASSWORD || "A11yAdminBootstrap16",
      REQUIRE_QUEUE: "false",
    },
    stdio: "inherit",
  },
);
child.on("exit", (code) => process.exit(code ?? 1));
