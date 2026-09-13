#!/usr/bin/env node
/**
 * pa11y CLI wrapper across public routes.
 * Requires: npx pa11y (devDependency). Fails CI on any error-level issue.
 */
import { spawnSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

const base = process.env.A11Y_BASE_URL || "http://127.0.0.1:3100";
const routes = ["/", "/login", "/register", "/pricing", "/help", "/privacy", "/terms", "/forgot-password"];
const results = [];
let failed = false;

for (const route of routes) {
  const url = `${base}${route}`;
  const run = spawnSync(
    "npx",
    ["--yes", "pa11y", url, "--reporter", "json", "--standard", "WCAG2AA"],
    { encoding: "utf8", shell: true, timeout: 120000 }
  );
  let issues = [];
  try {
    issues = JSON.parse(run.stdout || "[]");
  } catch {
    issues = [{ type: "error", message: run.stderr || run.stdout || "pa11y failed to parse" }];
  }
  const errors = (Array.isArray(issues) ? issues : []).filter((i) => i.type === "error");
  results.push({ route, errorCount: errors.length, errors: errors.slice(0, 20) });
  if (errors.length) failed = true;
  console.log(`${route}: ${errors.length} error(s)`);
}

const outDir = resolve("a11y/artifacts");
mkdirSync(outDir, { recursive: true });
writeFileSync(resolve(outDir, "pa11y-summary.json"), JSON.stringify({ base, results, pass: !failed }, null, 2));
process.exit(failed ? 1 : 0);
