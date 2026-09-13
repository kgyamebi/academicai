import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = dirname(fileURLToPath(import.meta.url));
const outDir = join(root, "artifacts");
mkdirSync(outDir, { recursive: true });

const base = process.env.LHCI_URL || process.env.A11Y_LIGHTHOUSE_URL || "";
if (!base) {
  console.log("Lighthouse skipped: set LHCI_URL to a reachable origin (deployed or local production).");
  process.exit(0);
}

const routes = (process.env.A11Y_LIGHTHOUSE_ROUTES || "/,/pricing,/login,/register,/check").split(",");
const minScore = Number(process.env.A11Y_LIGHTHOUSE_MIN || "0.98");
let failed = false;
const summary = [];

for (const route of routes) {
  const url = new URL(route, base).toString();
  const dest = join(outDir, `lighthouse${route.replaceAll("/", "_") || "_home"}.json`);
  const result = spawnSync(
    "npx",
    [
      "--yes",
      "lighthouse",
      url,
      "--only-categories=accessibility",
      "--quiet",
      "--chrome-flags=--headless --no-sandbox",
      "--output=json",
      `--output-path=${dest}`,
    ],
    { encoding: "utf8", shell: process.platform === "win32" },
  );
  if (result.status !== 0) {
    failed = true;
    console.error(`Lighthouse failed for ${url}\n${result.stderr || result.stdout}`);
    continue;
  }
  const report = JSON.parse(readFileSync(dest, "utf8"));
  const score = report.categories?.accessibility?.score ?? 0;
  summary.push({ url, score });
  console.log(`${url}: accessibility ${score}`);
  if (score < minScore) {
    failed = true;
    console.error(`  below gate ${minScore}`);
  }
}

writeFileSync(join(outDir, "lighthouse-summary.json"), JSON.stringify({ base, minScore, summary }, null, 2));
if (failed) process.exit(1);
